#!/usr/bin/env python3
"""
Advanced Voice Processing Engine for Virtual Friend
Handles WebRTC streaming, Whisper STT, and Bark TTS
"""

import asyncio
import logging
import numpy as np
import io
import wave
import tempfile
from collections import deque
from threading import Lock
from typing import AsyncGenerator, Optional, Callable
from pathlib import Path

try:
    from faster_whisper import WhisperModel
    import torch
    from bark import SAMPLE_RATE, generate_audio, preload_models
    try:
        from bark.generation import set_seed
    except ImportError:
        # Fallback for older bark versions
        def set_seed(seed):
            import random
            import numpy as np
            random.seed(seed)
            np.random.seed(seed)
            torch.manual_seed(seed)
    import soundfile as sf
    import scipy.io.wavfile as wavfile
    VOICE_DEPS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Voice dependencies not available: {e}")
    VOICE_DEPS_AVAILABLE = False


class VoiceProcessor:
    """Advanced voice processor with streaming capabilities."""

    # Shared caches so multiple sessions reuse heavy model weights
    _whisper_cache = {}
    _bark_loaded = False
    _torch_patch_lock = Lock()
    
    def __init__(
        self,
        whisper_model: str = "base",
        bark_voice: str = "v2/en_speaker_6",  # High quality English voice
        device: str = "auto",
        verbose: bool = True
    ):
        """
        Initialize voice processor.
        
        Args:
            whisper_model: Whisper model size (tiny, base, small, medium, large)
            bark_voice: Bark voice preset
            device: Device to use (auto, cpu, cuda)
            verbose: Enable verbose logging
        """
        self.logger = logging.getLogger(__name__)
        self.verbose = verbose
        
        if not VOICE_DEPS_AVAILABLE:
            raise ImportError("Voice dependencies not installed. Run: pip install -r requirements_voice.txt")
        
        # Configuration
        self.whisper_model_name = whisper_model
        self.bark_voice = bark_voice
        self.device = self._get_device(device)
        
        # Models (loaded lazily / via shared cache)
        self.whisper_model: Optional[WhisperModel] = None
        self.bark_loaded = bool(self._bark_loaded)
        
        # Audio processing settings
        self.sample_rate = 16000  # Standard for speech processing
        self.chunk_duration = 0.25  # Process audio in 0.25-second chunks for higher responsiveness
        self.chunk_size = int(self.sample_rate * self.chunk_duration)
        
        # Streaming buffers (deque of numpy arrays keeps memory footprint small)
        self.audio_buffer: deque[np.ndarray] = deque()
        self._buffered_samples = 0
        self.text_callback: Optional[Callable] = None
        self.audio_callback: Optional[Callable] = None
        
        self.logger.info(f"🎙️ VoiceProcessor initialized (Whisper: {whisper_model}, Device: {self.device})")
    
    def _get_device(self, device: str) -> str:
        """Determine the best device to use."""
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            # Skip MPS for now due to compatibility issues with faster-whisper
            # elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            #     return "mps" 
            else:
                return "cpu"
        elif device == "mps":
            # Force CPU if MPS is requested but causing issues
            self.logger.warning("⚠️ MPS device requested but using CPU for compatibility")
            return "cpu"
        return device
    
    async def initialize_models(self):
        """Initialize AI models asynchronously."""
        try:
            # Initialize Whisper
            cache_key = (self.whisper_model_name, self.device)
            if cache_key in self._whisper_cache:
                self.whisper_model = self._whisper_cache[cache_key]
                self.logger.info("✅ Whisper model reused from cache")
            else:
                self.logger.info(f"🔄 Loading Whisper model: {self.whisper_model_name}")
                self.whisper_model = WhisperModel(
                    self.whisper_model_name,
                    device=self.device,
                    compute_type="float16" if self.device == "cuda" else "int8"
                )
                self._whisper_cache[cache_key] = self.whisper_model
                self.logger.info("✅ Whisper model loaded")
            
            # Initialize Bark with PyTorch 2.6 compatibility
            self.logger.info("🔄 Loading Bark TTS models...")
            
            # Fix for PyTorch 2.6+ weights_only issue
            # Try to add safe globals, but fall back to weights_only=False if needed
            try:
                import torch.serialization
                import numpy
                
                # Add commonly needed numpy types for Bark compatibility
                safe_globals = [
                    numpy.dtype,
                    numpy.ndarray,
                    numpy.core.multiarray.scalar,
                ]
                
                # Add numpy dtypes that might be needed
                try:
                    safe_globals.extend([
                        numpy.dtypes.Float64DType,
                        numpy.dtypes.Float32DType,
                        numpy.dtypes.Int64DType,
                        numpy.dtypes.Int32DType,
                    ])
                except AttributeError:
                    # Older numpy versions might not have these
                    pass
                
                torch.serialization.add_safe_globals(safe_globals)
                self.logger.info("✅ Added safe globals for PyTorch 2.6+ compatibility")
                
            except (ImportError, AttributeError) as e:
                self.logger.warning(f"⚠️ Could not set safe globals for PyTorch: {e}")
            
            # Patch torch.load temporarily if weights_only issues persist
            import torch
            if not self._bark_loaded:
                with self._torch_patch_lock:
                    if not self._bark_loaded:
                        original_load = torch.load

                        def patched_load(*args, **kwargs):
                            if 'weights_only' not in kwargs:
                                kwargs['weights_only'] = False
                                self.logger.info("🔧 Using weights_only=False for Bark model loading")
                            return original_load(*args, **kwargs)

                        torch.load = patched_load
                        try:
                            await asyncio.to_thread(preload_models)
                            set_seed(42)  # For consistent voice quality
                            self.__class__._bark_loaded = True
                            self.logger.info("✅ Bark TTS models loaded")
                        finally:
                            torch.load = original_load

            self.bark_loaded = bool(type(self)._bark_loaded)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize models: {e}")
            return False
    
    def set_callbacks(self, text_callback: Callable = None, audio_callback: Callable = None):
        """Set callbacks for real-time processing."""
        self.text_callback = text_callback
        self.audio_callback = audio_callback
    
    async def process_audio_stream(self, audio_data: bytes) -> Optional[str]:
        """
        Process streaming audio data and return transcribed text.
        
        Args:
            audio_data: Raw audio bytes (16kHz, 16-bit PCM)
            
        Returns:
            Transcribed text or None if not enough audio
        """
        if not self.whisper_model:
            await self.initialize_models()
        
        try:
            # Convert bytes to numpy array
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

            # Add to buffer
            self._append_audio(audio_np)
            
            # Process if we have enough audio
            if self._buffered_samples >= self.chunk_size:
                # Extract chunk
                chunk = self._pop_chunk()
                
                # Transcribe
                text = await self._transcribe_chunk(chunk)
                
                if text and self.text_callback:
                    await self.text_callback(text)
                
                return text
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error processing audio stream: {e}")
            return None

    async def process_audio_stream_raw(self, audio_data: bytes, input_sample_rate: int = 48000, channels: int = 1) -> Optional[str]:
        """Process raw streaming audio at arbitrary sample rate and resample to 16kHz mono.

        Args:
            audio_data: Raw PCM16 bytes (typically 48kHz from WebRTC)
            input_sample_rate: Sample rate of incoming audio
            channels: Number of channels (we expect mono from getUserMedia, but handle >1 by taking first channel)

        Returns:
            Transcribed text or None
        """
        if not self.whisper_model:
            await self.initialize_models()

        try:
            # Convert bytes to numpy int16
            audio_int16 = np.frombuffer(audio_data, dtype=np.int16)

            # If multichannel, take the first channel
            if channels and channels > 1:
                audio_int16 = audio_int16.reshape(-1, channels)[:, 0]

            # Convert to float32 -1..1
            audio_float = audio_int16.astype(np.float32) / 32768.0

            # Resample to 16kHz if needed
            if input_sample_rate != self.sample_rate:
                try:
                    # Prefer high-quality polyphase resampling if SciPy is available
                    from scipy.signal import resample_poly  # type: ignore
                    # Compute up/down factors approximately
                    up = self.sample_rate
                    down = input_sample_rate
                    # Reduce fraction to avoid huge numbers
                    from math import gcd
                    g = gcd(up, down)
                    up //= g
                    down //= g
                    audio_resampled = resample_poly(audio_float, up, down)
                except Exception:
                    # Fallback to simple linear interpolation
                    ratio = self.sample_rate / float(input_sample_rate)
                    new_len = int(len(audio_float) * ratio)
                    if new_len <= 1:
                        return None
                    x_old = np.linspace(0, 1, num=len(audio_float), endpoint=False, dtype=np.float32)
                    x_new = np.linspace(0, 1, num=new_len, endpoint=False, dtype=np.float32)
                    audio_resampled = np.interp(x_new, x_old, audio_float).astype(np.float32)
            else:
                audio_resampled = audio_float

            # Buffer handling (same as process_audio_stream)
            self._append_audio(audio_resampled)
            try:
                if self.verbose:
                    self.logger.debug(f"Buffer samples: {self._buffered_samples} / chunk_size: {self.chunk_size}")
            except Exception:
                pass

            if self._buffered_samples >= self.chunk_size:
                chunk = self._pop_chunk()

                self.logger.debug("Transcribing chunk...")
                text = await self._transcribe_chunk(chunk)
                if text and self.text_callback:
                    await self.text_callback(text)
                return text

            return None

        except Exception as e:
            self.logger.error(f"Error processing raw audio stream: {e}")
            return None

    def _append_audio(self, samples: np.ndarray):
        """Store incoming samples without creating millions of Python objects."""
        if samples is None or samples.size == 0:
            return
        if samples.dtype != np.float32:
            samples = samples.astype(np.float32)
        self.audio_buffer.append(samples)
        self._buffered_samples += len(samples)

    def _pop_chunk(self) -> np.ndarray:
        """Collect exactly chunk_size samples from the deque."""
        remaining = self.chunk_size
        chunks = []

        while remaining > 0 and self.audio_buffer:
            block = self.audio_buffer[0]
            block_len = len(block)
            if block_len <= remaining:
                chunks.append(block)
                self.audio_buffer.popleft()
                self._buffered_samples -= block_len
                remaining -= block_len
            else:
                chunks.append(block[:remaining])
                self.audio_buffer[0] = block[remaining:]
                self._buffered_samples -= remaining
                remaining = 0

        if not chunks:
            return np.zeros(self.chunk_size, dtype=np.float32)

        if len(chunks) == 1:
            return np.asarray(chunks[0], dtype=np.float32)

        return np.concatenate(chunks).astype(np.float32, copy=False)
    
    async def _transcribe_chunk(self, audio_chunk: np.ndarray) -> Optional[str]:
        """Transcribe audio chunk using Whisper."""
        try:
            # Run Whisper in thread to avoid blocking
            segments, info = await asyncio.to_thread(
                self.whisper_model.transcribe,
                audio_chunk,
                language="en",  # English by default
                beam_size=1,    # Fast decoding
                best_of=1,      # Fast decoding
                temperature=0.0,
                condition_on_previous_text=False,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=300)
            )
            
            # Extract text from segments
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())
            
            full_text = " ".join(text_parts).strip()
            
            if full_text and len(full_text) > 3:  # Filter out very short transcriptions
                self.logger.info(f"🎙️ Transcribed: {full_text[:50]}...")
                return full_text
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error transcribing audio: {e}")
            return None
    
    async def generate_speech(self, text: str) -> Optional[bytes]:
        """
        Generate speech from text using Bark TTS.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Audio data as bytes or None if failed
        """
        if not self.bark_loaded:
            await self.initialize_models()
        
        try:
            self.logger.info(f"🗣️ Generating speech: {text[:50]}...")
            
            # Generate audio using Bark
            audio_array = await asyncio.to_thread(
                generate_audio,
                text,
                history_prompt=self.bark_voice,
                text_temp=0.7,
                waveform_temp=0.7
            )
            
            # Convert to bytes
            audio_bytes = self._array_to_bytes(audio_array)
            
            if self.audio_callback:
                await self.audio_callback(audio_bytes)
            
            self.logger.info("✅ Speech generated successfully")
            return audio_bytes
            
        except Exception as e:
            self.logger.error(f"Error generating speech: {e}")
            return None
    
    def _array_to_bytes(self, audio_array: np.ndarray) -> bytes:
        """Convert numpy array to audio bytes."""
        try:
            # Normalize and convert to 16-bit PCM
            audio_int16 = (audio_array * 32767).astype(np.int16)
            
            # Create WAV file in memory
            with io.BytesIO() as wav_io:
                with wave.open(wav_io, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(SAMPLE_RATE)
                    wav_file.writeframes(audio_int16.tobytes())
                
                return wav_io.getvalue()
                
        except Exception as e:
            self.logger.error(f"Error converting audio array to bytes: {e}")
            return b""
    
    def save_audio_file(self, audio_bytes: bytes, filepath: str):
        """Save audio bytes to file."""
        try:
            with open(filepath, 'wb') as f:
                f.write(audio_bytes)
            self.logger.info(f"💾 Audio saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving audio file: {e}")
    
    async def process_complete_audio(self, audio_data: bytes) -> Optional[str]:
        """
        Process complete audio file (not streaming).
        
        Args:
            audio_data: Complete audio file bytes
            
        Returns:
            Full transcription
        """
        if not self.whisper_model:
            await self.initialize_models()
        
        try:
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            # Transcribe entire file
            segments, info = await asyncio.to_thread(
                self.whisper_model.transcribe,
                temp_path,
                language="en",
                beam_size=5,
                best_of=5,
                temperature=0.0
            )
            
            # Extract full text
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())
            
            full_text = " ".join(text_parts).strip()
            
            # Cleanup
            Path(temp_path).unlink(missing_ok=True)
            
            self.logger.info(f"🎙️ Complete transcription: {full_text[:100]}...")
            return full_text
            
        except Exception as e:
            self.logger.error(f"Error processing complete audio: {e}")
            return None
    
    async def close(self):
        """Clean up resources."""
        self.audio_buffer.clear()
        self._buffered_samples = 0
        self.logger.info("🔌 VoiceProcessor closed")


# Test function
async def test_voice_processor():
    """Test the voice processor."""
    processor = VoiceProcessor(whisper_model="tiny", verbose=True)
    
    # Test initialization
    success = await processor.initialize_models()
    print(f"Models loaded: {success}")
    
    # Test TTS
    if success:
        audio_bytes = await processor.generate_speech("Hello! I am your virtual friend Ajax!")
        if audio_bytes:
            processor.save_audio_file(audio_bytes, "test_output.wav")
            print("Test audio saved to test_output.wav")
    
    await processor.close()


if __name__ == "__main__":
    asyncio.run(test_voice_processor())
