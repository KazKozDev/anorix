#!/usr/bin/env python3
"""
Simple Desktop UI for Local Friend using Tkinter
Connects to the existing Flask backend at http://127.0.0.1:5000
"""
import threading
import queue
import time
import asyncio
import requests
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

# Voice dependencies
try:
    import socketio  # python-socketio client
    from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
    import numpy as np
    import sounddevice as sd
    import av
    VOICE_DEPS = True
except Exception:
    VOICE_DEPS = False

# Whisper for local dictation
try:
    from faster_whisper import WhisperModel
    import io
    import wave
    import tempfile
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

API_BASE = "http://127.0.0.1:5000/api"

# =====================
# Local Whisper Dictation (ChatGPT-style)
# =====================

class LocalDictation:
    """Local dictation with Whisper to insert text into input field"""
    
    def __init__(self, device=None):
        self.device = device
        self.whisper_model = None
        self.is_recording = False
        self._audio_buffer = bytearray()
        self.sample_rate = 16000
        
    def _load_whisper(self):
        """Load Whisper model (lazy init)"""
        if self.whisper_model is None and WHISPER_AVAILABLE:
            try:
                # Use a faster model for dictation
                self.whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
                return True
            except Exception as e:
                print(f"Whisper load error: {e}")
                return False
        return self.whisper_model is not None
    
    def start_recording(self):
        """Start voice recording"""
        if not WHISPER_AVAILABLE:
            raise Exception("Whisper is not installed. Install: pip install faster-whisper")
        
        if not self._load_whisper():
            raise Exception("Failed to load Whisper model")
            
        self.is_recording = True
        self._audio_buffer = bytearray()
        
        def audio_callback(indata, frames, time, status):
            if self.is_recording:
                # Convert to int16 for Whisper compatibility
                audio_int16 = (indata[:, 0] * 32767).astype(np.int16)
                self._audio_buffer.extend(audio_int16.tobytes())
        
        # Start recording
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32',
            callback=audio_callback,
            device=self.device
        )
        self.stream.start()
    
    def stop_recording_and_transcribe(self):
        """Stop recording and return transcription"""
        if not self.is_recording:
            return ""
            
        self.is_recording = False
        
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        
        if not self._audio_buffer:
            return ""
        
        try:
            # Convert to numpy array
            audio_np = np.frombuffer(bytes(self._audio_buffer), dtype=np.int16)
            
            # Save to a temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                with wave.open(temp_file.name, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(self.sample_rate)
                    wav_file.writeframes(audio_np.tobytes())
                
                # Transcribe with Whisper
                segments, _ = self.whisper_model.transcribe(
                    temp_file.name,
                    language="ru",  # Russian
                    beam_size=5,
                    best_of=5,
                    temperature=0.0
                )
                
                # Aggregate text
                text_parts = []
                for segment in segments:
                    text_parts.append(segment.text.strip())
                
                result = " ".join(text_parts).strip()
                
                # Remove temporary file
                try:
                    import os
                    os.unlink(temp_file.name)
                except:
                    pass
                
                return result
                
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""

# =====================
# Voice/WebRTC Client (defined early to be available before mainloop)
# =====================

class MicAudioTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self, input_samplerate=48000, blocksize=960, device=None):
        super().__init__()
        self.sample_rate = input_samplerate
        self.blocksize = blocksize  # samples per chunk
        self.queue = asyncio.Queue(maxsize=10)
        self._stream = None
        self._closed = False
        self.device = device  # sounddevice device index or None for default

        def audio_callback(indata, frames, time_info, status):
            try:
                # indata is float32 -1..1, convert to int16 bytes
                data = np.clip(indata[:, 0], -1.0, 1.0)
                int16 = (data * 32767).astype(np.int16).tobytes()
                # Put into asyncio queue from non-async thread callback
                asyncio.run_coroutine_threadsafe(self.queue.put(int16), self._loop)
            except Exception:
                pass

        # Create InputStream but start later when loop is set
        self._stream_factory = lambda: sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32',
            blocksize=self.blocksize,
            callback=audio_callback,
            device=self.device
        )

    def attach_loop(self, loop):
        self._loop = loop
        if self._stream is None:
            self._stream = self._stream_factory()
            self._stream.start()

    async def recv(self):
        # Try to get audio chunk quickly; if not available, send brief silence to keep pipeline alive
        try:
            audio_bytes = await asyncio.wait_for(self.queue.get(), timeout=0.1)
            samples = max(1, len(audio_bytes) // 2)
            frame = av.AudioFrame(format='s16', layout='mono', samples=samples)
            frame.sample_rate = self.sample_rate
            for plane in frame.planes:
                plane.update(audio_bytes)
            return frame
        except asyncio.TimeoutError:
            # Generate ~20ms of silence at current sample_rate
            samples = max(1, int(self.sample_rate * 0.02))
            frame = av.AudioFrame(format='s16', layout='mono', samples=samples)
            frame.sample_rate = self.sample_rate
            for plane in frame.planes:
                plane.update(b"\x00" * plane.buffer_size)
            return frame

    async def stop_stream(self):
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        self._closed = True


class VoiceClient:
    def __init__(self, ui_queue: queue.Queue, server_url: str = "http://127.0.0.1:5000", input_device: int | None = None):
        self.ui_queue = ui_queue
        self.server_url = server_url
        self.sio = socketio.Client()
        self.pc = None
        self.session_id = None
        self.loop = None
        self.thread = None
        self._stopping = threading.Event()
        self.mic_track = None
        self.input_device = input_device

        # Socket.IO event handlers
        self.sio.on('connect', self._on_connect)
        self.sio.on('disconnect', self._on_disconnect)
        self.sio.on('voice_session_created', self._on_voice_session_created)
        self.sio.on('webrtc_answer', self._on_webrtc_answer)
        self.sio.on('stt_result', self._on_stt_result)

    # -------------- Public API --------------
    def start(self):
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self._stopping.set()
        if self.loop:
            asyncio.run_coroutine_threadsafe(self._async_stop(), self.loop)
        if self.thread:
            self.thread.join(timeout=2)

    # -------------- Internals --------------
    def _run_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._async_start())
            # Keep loop running while not stopping
            while not self._stopping.is_set():
                self.loop.run_until_complete(asyncio.sleep(0.1))
        finally:
            try:
                self.loop.run_until_complete(self._async_stop())
            except Exception:
                pass
            self.loop.stop()
            self.loop.close()

    async def _async_start(self):
        # Connect socket
        try:
            self.sio.connect(self.server_url, transports=['websocket', 'polling'])
        except Exception as e:
            self.ui_queue.put(("chat_err", f"Socket connect error: {e}"))
            return

        # Prepare RTCPeerConnection
        self.pc = RTCPeerConnection()
        
        # Setup microphone track
        self.ui_queue.put(("system", f"Microphone: {'default' if self.input_device is None else f'index={self.input_device}'}"))
        self.mic_track = MicAudioTrack(input_samplerate=48000, blocksize=960, device=self.input_device)
        self.mic_track.attach_loop(self.loop)
        self.pc.addTrack(self.mic_track)

        # Handle remote tracks (TODO: playback)
        @self.pc.on("track")
        def on_track(track):
            # Could implement TTS playback here by reading frames from track
            pass

        # Ask server to create voice session
        self.sio.emit('create_voice_session', {
            'config': {
                'whisper_model': 'base',
                'bark_voice': 'v2/en_speaker_6'
            }
        })

    async def _async_stop(self):
        try:
            if self.pc:
                await self.pc.close()
        except Exception:
            pass
        try:
            if self.mic_track:
                await self.mic_track.stop_stream()
        except Exception:
            pass
        try:
            if self.sio.connected:
                self.sio.disconnect()
        except Exception:
            pass

    # ------ Socket.IO callbacks ------
    def _on_connect(self):
        self.ui_queue.put(("system", "Voice: connected to server"))

    def _on_disconnect(self):
        self.ui_queue.put(("system", "Voice: disconnected from server"))

    def _on_voice_session_created(self, data):
        self.session_id = data.get('session_id')
        self.ui_queue.put(("system", f"Voice: session created {self.session_id}"))
        # Create and send offer
        asyncio.run_coroutine_threadsafe(self._send_offer(), self.loop)

    async def _send_offer(self):
        if not self.pc or not self.session_id:
            return
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)
        # Send via Socket.IO
        self.sio.emit('webrtc_offer', {
            'session_id': self.session_id,
            'offer': offer.sdp
        })

    def _on_webrtc_answer(self, data):
        if not self.pc:
            return
        answer_sdp = data.get('answer')
        if not answer_sdp:
            return
        desc = RTCSessionDescription(sdp=answer_sdp, type='answer')
        asyncio.run_coroutine_threadsafe(self.pc.setRemoteDescription(desc), self.loop)
        self.ui_queue.put(("system", "Voice: WebRTC connection established"))

    def _on_stt_result(self, data):
        text = (data or {}).get('text')
        if text:
            # Push transcribed text to UI as if user said it; app can forward to friend if desired
            self.ui_queue.put(("stt_text", text))

class DesktopFriendUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Local Friend - Desktop UI")
        self.geometry("720x640")
        self.minsize(600, 500)

        self.voice_mode = tk.BooleanVar(value=False)
        self.dark_mode = tk.BooleanVar(value=False)
        self.selected_device = tk.StringVar(value="(default)")
        self._device_name_to_index = {}

        self._build_ui()
        self.network_queue = queue.Queue()
        self.after(100, self._process_network_queue)
        self._load_status_async()

        # Voice/WebRTC client (runs in background thread with its own asyncio loop)
        self.voice = None
        
        # Local dictation system (ChatGPT-style)
        self.dictation = None
        self.is_dictating = False

    def _build_ui(self):
        # Top bar
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=10, pady=10)

        self.friend_name = ttk.Label(top, text="Anorix", font=("Inter", 16, "bold"))
        self.friend_name.pack(side=tk.LEFT)

        self.status_label = ttk.Label(top, text="Connecting...", foreground="#888")
        self.status_label.pack(side=tk.RIGHT)

        # Chat area
        chat_frame = ttk.Frame(self)
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))

        self.chat_text = tk.Text(chat_frame, wrap=tk.WORD, state=tk.DISABLED, font=("Inter", 11))
        self.chat_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(chat_frame, command=self.chat_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_text["yscrollcommand"] = scrollbar.set

        # Input area
        input_frame = ttk.Frame(self)
        input_frame.pack(fill=tk.X, padx=10, pady=(0,10))

        self.message_entry = tk.Text(input_frame, height=3, wrap=tk.WORD, font=("Inter", 11))
        self.message_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.message_entry.bind("<Shift-Return>", lambda e: None)
        self.message_entry.bind("<Return>", self._on_enter_send)
        
        # Add global Escape key to stop dictation
        self.bind("<Escape>", self._on_escape_pressed)

        # Dictation button (microphone)
        self.dictation_btn = ttk.Button(input_frame, text="🎤", width=3, command=self._toggle_dictation)
        self.dictation_btn.pack(side=tk.LEFT, padx=(4,0))
        
        # File upload button
        self.file_btn = ttk.Button(input_frame, text="📎", width=3, command=self._upload_file)
        self.file_btn.pack(side=tk.LEFT, padx=(4,0))

        send_btn = ttk.Button(input_frame, text="Send", command=self._send_clicked)
        send_btn.pack(side=tk.LEFT, padx=(4,0))

        # Controls
        controls = ttk.Frame(self)
        controls.pack(fill=tk.X, padx=10, pady=(0,10))

        self.voice_check = ttk.Checkbutton(controls, text="Voice mode (WebRTC)", variable=self.voice_mode, command=self._toggle_voice_mode)
        self.voice_check.pack(side=tk.LEFT)

        self.dark_check = ttk.Checkbutton(controls, text="Dark theme", variable=self.dark_mode, command=self._toggle_dark_mode)
        self.dark_check.pack(side=tk.RIGHT)

        # Microphone selector with refresh
        mic_frame = ttk.Frame(self)
        mic_frame.pack(fill=tk.X, padx=10, pady=(0,10))
        ttk.Label(mic_frame, text="Microphone:").pack(side=tk.LEFT)
        self.mic_combo = ttk.Combobox(mic_frame, textvariable=self.selected_device, state="readonly", width=45)
        self.mic_combo.pack(side=tk.LEFT, padx=(6,6))
        self.mic_combo.bind('<<ComboboxSelected>>', self._on_device_selected)
        ttk.Button(mic_frame, text="Refresh", command=self._refresh_devices).pack(side=tk.LEFT)
        self._refresh_devices(init=True)

        # Setup styles for dictation button
        self._setup_dictation_styles()
        
        # Welcome message
        self._append_message("friend", "Hi! I'm Anorix, your virtual friend! Type a message below or use dictation (🎤). Press the button again or Escape to stop dictation.")

    def _setup_dictation_styles(self):
        """Setup styles for the dictation button"""
        style = ttk.Style()
        # Style for recording button (red background)
        style.configure("Recording.TButton", 
                       foreground="white", 
                       background="red",
                       focuscolor="none")

    def _toggle_dark_mode(self):
        if self.dark_mode.get():
            self._apply_dark_theme()
        else:
            self._apply_light_theme()

    def _apply_dark_theme(self):
        self.configure(bg="#111")
        for widget in self.winfo_children():
            try:
                widget.configure(style="Dark.TFrame")
            except Exception:
                pass
        self.chat_text.configure(bg="#111", fg="#eee", insertbackground="#eee")
        self.message_entry.configure(bg="#111", fg="#eee", insertbackground="#eee")

    def _apply_light_theme(self):
        self.configure(bg="")
        self.chat_text.configure(bg="white", fg="black", insertbackground="black")
        self.message_entry.configure(bg="white", fg="black", insertbackground="black")

    def _on_enter_send(self, event):
        self._send_clicked()
        return "break"
    
    def _on_escape_pressed(self, event):
        """Handle Escape key - stop dictation"""
        if self.is_dictating:
            self._stop_dictation()
        return "break"

    def _send_clicked(self):
        text = self.message_entry.get("1.0", tk.END).strip()
        if not text:
            return
        self.message_entry.delete("1.0", tk.END)
        self._append_message("user", text)
        self._send_to_backend_async(text, self.voice_mode.get())

    def _append_message(self, sender, text):
        timestamp = datetime.now().strftime("%H:%M")
        prefix = "You: " if sender == "user" else "Anorix: "
        color = "#1f6feb" if sender == "user" else "#16a34a"
        self.chat_text.configure(state=tk.NORMAL)
        self.chat_text.insert(tk.END, f"[{timestamp}] ", ("timestamp",))
        self.chat_text.insert(tk.END, prefix, ("sender", sender))
        self.chat_text.insert(tk.END, text + "\n")
        self.chat_text.configure(state=tk.DISABLED)
        self.chat_text.see(tk.END)
        # Tag styles
        self.chat_text.tag_config("timestamp", foreground="#888")
        self.chat_text.tag_config("sender", foreground=color, font=("Inter", 11, "bold"))

    def _append_system(self, text):
        self.chat_text.configure(state=tk.NORMAL)
        self.chat_text.insert(tk.END, text + "\n", ("system",))
        self.chat_text.configure(state=tk.DISABLED)
        self.chat_text.tag_config("system", foreground="#888", font=("Inter", 10, "italic"))
        self.chat_text.see(tk.END)

    # ---- Microphone devices ----
    def _refresh_devices(self, init: bool = False):
        try:
            devices = sd.query_devices()
            input_devices = []
            self._device_name_to_index.clear()

            # Default input device
            default_in = None
            try:
                default_in = sd.default.device[0]
            except Exception:
                default_in = None

            for idx, dev in enumerate(devices):
                if dev.get('max_input_channels', 0) > 0:
                    name = f"[{idx}] {dev.get('name', 'Unknown')} — {dev.get('hostapi', '')}"
                    input_devices.append(name)
                    self._device_name_to_index[name] = idx

            if not input_devices:
                input_devices = ["(no input devices)"]

            self.mic_combo['values'] = ["(default)"] + input_devices

            # Select default
            if default_in is not None and default_in >= 0:
                # Try to find default_in in our list
                def_name = next((name for name, i in self._device_name_to_index.items() if i == default_in), None)
                if def_name:
                    self.selected_device.set(def_name)
                else:
                    self.selected_device.set("(default)")
            else:
                self.selected_device.set("(default)")

            # Log devices to UI
            if not init:
                self._append_system("Microphone list updated:")
            for name in self.mic_combo['values']:
                self._append_system(f"  • {name}")
        except Exception as e:
            self._append_system(f"Error getting device list: {e}")

    def _on_device_selected(self, event=None):
        choice = self.selected_device.get()
        if choice == "(default)":
            self._append_system("Selected microphone: default")
        else:
            idx = self._device_name_to_index.get(choice)
            self._append_system(f"Selected microphone: {choice} (index={idx})")

    def _send_to_backend_async(self, message, voice_mode):
        def worker():
            try:
                resp = requests.post(
                    f"{API_BASE}/chat",
                    json={"message": message, "voice_mode": bool(voice_mode)},
                    timeout=60
                )
                if resp.ok:
                    data = resp.json()
                    self.network_queue.put(("chat_ok", data))
                else:
                    self.network_queue.put(("chat_err", f"HTTP {resp.status_code}"))
            except Exception as e:
                self.network_queue.put(("chat_err", str(e)))
        threading.Thread(target=worker, daemon=True).start()
        self._append_system("Sending...")

    def _load_status_async(self):
        def worker():
            try:
                resp = requests.get(f"{API_BASE}/status", timeout=10)
                if resp.ok:
                    data = resp.json()
                    self.network_queue.put(("status_ok", data))
                else:
                    self.network_queue.put(("status_err", f"HTTP {resp.status_code}"))
            except Exception as e:
                self.network_queue.put(("status_err", str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _process_network_queue(self):
        try:
            while True:
                kind, payload = self.network_queue.get_nowait()
                if kind == "status_ok":
                    online = payload.get("online", False)
                    name = payload.get("friend_name") or "Anorix"
                    self.friend_name.configure(text=name)
                    self.status_label.configure(text="Online" if online else "Offline", foreground=("#22c55e" if online else "#ef4444"))
                elif kind == "status_err":
                    self.status_label.configure(text=f"Status: error ({payload})", foreground="#ef4444")
                elif kind == "chat_ok":
                    self._append_system("Sent.")
                    msg = payload.get("message") or "(empty response)"
                    self._append_message("friend", msg)
                elif kind == "chat_err":
                    self._append_system(f"Send error: {payload}")
                elif kind == "system":
                    self._append_system(str(payload))
                elif kind == "stt_text":
                    text = str(payload).strip()
                    if text:
                        # Show as user message and forward to backend
                        self._append_message("user", text)
                        self._send_to_backend_async(text, True)
                elif kind == "dictation_result":
                    text = str(payload).strip()
                    if text:
                        # Insert transcribed text into the input field
                        current_text = self.message_entry.get("1.0", tk.END).strip()
                        if current_text:
                            # Add a space if there is already text
                            new_text = current_text + " " + text
                        else:
                            new_text = text
                        
                        self.message_entry.delete("1.0", tk.END)
                        self.message_entry.insert("1.0", new_text)
                        self.message_entry.see(tk.END)
                        self._append_system(f"Dictation finished: added text '{text}'")
                    else:
                        self._append_system("Dictation finished: no text recognized")
                elif kind == "dictation_error":
                    self._append_system(f"Dictation error: {payload}")
                else:
                    pass
        except queue.Empty:
            pass
        finally:
            self.after(100, self._process_network_queue)

    def _toggle_voice_mode(self):
        enabled = self.voice_mode.get()
        if enabled:
            if not VOICE_DEPS:
                messagebox.showerror(
                    "Voice dependencies",
                    "Voice mode requires packages: python-socketio, aiortc, av, sounddevice, numpy"
                )
                self.voice_mode.set(False)
                return
            self._start_voice_client()
        else:
            self._stop_voice_client()
        
    def _start_voice_client(self):
        if self.voice is not None:
            return
        self._append_system("Initializing voice mode…")
        # Map selected device to index (or None for default)
        dev_choice = self.selected_device.get()
        input_device = self._device_name_to_index.get(dev_choice) if dev_choice != "(default)" else None
        self.voice = VoiceClient(self.network_queue, input_device=input_device)
        self.voice.start()

    def _stop_voice_client(self):
        if self.voice is None:
            self._append_system("Voice mode is already off.")
            return
        self._append_system("Turning off voice mode…")
        self.voice.stop()
        self.voice = None

    # ---- Local Dictation (ChatGPT-style) ----
    
    def _toggle_dictation(self):
        """Toggle dictation (press and hold / release)"""
        if not WHISPER_AVAILABLE:
            messagebox.showerror(
                "Whisper unavailable",
                "Dictation requires: pip install faster-whisper"
            )
            return
            
        if not self.is_dictating:
            self._start_dictation()
        else:
            self._stop_dictation()
    
    def _start_dictation(self):
        """Start dictation"""
        try:
            # Get selected device
            dev_choice = self.selected_device.get()
            input_device = self._device_name_to_index.get(dev_choice) if dev_choice != "(default)" else None
            
            # Create dictation object
            self.dictation = LocalDictation(device=input_device)
            self.dictation.start_recording()
            
            # Update UI
            self.is_dictating = True
            self.dictation_btn.configure(text="⏹️", style="Recording.TButton")  # Red stop button
            self._append_system("Dictation: starting recording... Press the button again to stop.")
            
        except Exception as e:
            self._append_system(f"Dictation start error: {e}")
            messagebox.showerror("Dictation error", str(e))
    
    def _stop_dictation(self):
        """Stop dictation and process result"""
        if not self.is_dictating or not self.dictation:
            return
            
        try:
            # Stop recording and get transcription
            self._append_system("Dictation: processing recording...")
            
            # Run transcription in a separate thread to avoid freezing the UI
            def transcribe_async():
                try:
                    text = self.dictation.stop_recording_and_transcribe()
                    # Send result to the main thread
                    self.network_queue.put(("dictation_result", text))
                except Exception as e:
                    self.network_queue.put(("dictation_error", str(e)))
            
            threading.Thread(target=transcribe_async, daemon=True).start()
            
        except Exception as e:
            self._append_system(f"Dictation processing error: {e}")
        finally:
            # Reset state
            self.is_dictating = False
            self.dictation_btn.configure(text="🎤", style="TButton")
            self.dictation = None

    def _upload_file(self):
        """Open file chooser and send read request"""
        try:
            # Open file chooser dialog
            file_path = filedialog.askopenfilename(
                title="Select a file to read",
                filetypes=[
                    ("All supported", ("*.txt", "*.md", "*.pdf", "*.docx", "*.xlsx", "*.xls", "*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp", "*.webp", "*.tiff")),
                    ("Text files", ("*.txt", "*.md", "*.py", "*.js", "*.css", "*.html", "*.json", "*.xml", "*.csv")),
                    ("PDF documents", "*.pdf"),
                    ("Word documents", "*.docx"),
                    ("Excel files", ("*.xlsx", "*.xls")),
                    ("Images", ("*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp", "*.webp", "*.tiff")),
                    ("All files", "*.*")
                ]
            )
            
            if file_path:
                # Show loading indicator
                self.file_btn.configure(text="⏳")
                self.update()
                
                # Prepare request to agent to read file
                message = f"Read file: {file_path}"
                
                # Add a chat message from user
                self._append_message("user", f"📎 Uploaded file: {file_path.split('/')[-1]}")
                
                # Put the request into input field and send
                self.message_entry.delete("1.0", tk.END)
                self.message_entry.insert("1.0", message)
                self._send_clicked()
                
        except Exception as e:
            self._append_system(f"File upload error: {e}")
            messagebox.showerror("Error", f"Failed to upload file: {e}")
        finally:
            # Restore button
            self.file_btn.configure(text="📎")


def main():
    try:
        app = DesktopFriendUI()
        app.mainloop()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
