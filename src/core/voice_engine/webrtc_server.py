#!/usr/bin/env python3
"""
WebRTC Audio Streaming Server for Real-time Voice Processing
"""

import asyncio
import logging
import json
import uuid
from typing import Dict, Optional
from dataclasses import dataclass

try:
    from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
    from aiortc.contrib.media import MediaRecorder, MediaPlayer
    from aiortc.rtcrtpsender import RTCRtpSender
    import av
    WEBRTC_AVAILABLE = True
except ImportError:
    logging.warning("WebRTC dependencies not available")
    WEBRTC_AVAILABLE = False

from .voice_processor import VoiceProcessor


@dataclass
class VoiceSession:
    """Voice processing session."""
    session_id: str
    peer_connection: 'RTCPeerConnection'
    voice_processor: VoiceProcessor
    is_active: bool = False
    text_callback: Optional[callable] = None
    audio_callback: Optional[callable] = None


class AudioStreamTrack(MediaStreamTrack):
    """Custom audio track for streaming processed audio back to client."""
    
    kind = "audio"
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.audio_queue = asyncio.Queue(maxsize=8)
        self.sample_rate = 24000  # Bark's sample rate
        
    async def add_audio_data(self, audio_bytes: bytes):
        """Add audio data to be streamed."""
        try:
            self.audio_queue.put_nowait(audio_bytes)
        except asyncio.QueueFull:
            # Drop the oldest frame to make space to avoid unbounded growth
            try:
                _ = self.audio_queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            try:
                self.audio_queue.put_nowait(audio_bytes)
            except asyncio.QueueFull:
                if self.logger.isEnabledFor(logging.DEBUG):
                    self.logger.debug("Dropping audio frame due to sustained backpressure")
    
    async def recv(self):
        """Receive next audio frame."""
        try:
            # Get audio data from queue
            audio_bytes = await asyncio.wait_for(self.audio_queue.get(), timeout=0.1)
            
            # Convert to av.AudioFrame
            frame = av.AudioFrame.from_bytes(
                audio_bytes,
                format='s16',
                layout='mono',
                sample_rate=self.sample_rate
            )
            
            return frame
            
        except asyncio.TimeoutError:
            # Return silence if no audio available
            samples = 480  # 20ms at 24kHz
            frame = av.AudioFrame(format='s16', layout='mono', samples=samples)
            frame.sample_rate = self.sample_rate
            
            # Fill with zeros (silence)
            for plane in frame.planes:
                plane.update(b'\x00' * plane.buffer_size)
            
            return frame


class WebRTCVoiceServer:
    """WebRTC server for real-time voice communication."""
    
    def __init__(self, friend_instance=None, socketio_instance=None, verbose: bool = True):
        """
        Initialize WebRTC voice server.
        
        Args:
            friend_instance: Virtual friend instance for processing
            socketio_instance: Flask-SocketIO instance for real-time communication
            verbose: Enable verbose logging
        """
        if not WEBRTC_AVAILABLE:
            raise ImportError("WebRTC dependencies not available. Install aiortc and av.")
        
        self.logger = logging.getLogger(__name__)
        self.verbose = verbose
        self.friend_instance = friend_instance
        self.socketio = socketio_instance
        
        # Active sessions
        self.sessions: Dict[str, VoiceSession] = {}
        
        # Default voice processor settings
        self.default_voice_settings = {
            "whisper_model": "base",
            "bark_voice": "v2/en_speaker_6",
            "device": "auto"
        }
        
        self.logger.info("🌐 WebRTC Voice Server initialized")
    
    async def create_session(self, session_config: dict = None) -> str:
        """
        Create new voice session.
        
        Args:
            session_config: Configuration for the session
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        try:
            # Create peer connection
            pc = RTCPeerConnection()
            
            # Create voice processor
            config = {**self.default_voice_settings, **(session_config or {})}
            voice_processor = VoiceProcessor(**config)
            
            # Initialize models
            await voice_processor.initialize_models()
            
            # Create session
            session = VoiceSession(
                session_id=session_id,
                peer_connection=pc,
                voice_processor=voice_processor
            )
            
            # Setup audio track for outgoing audio
            audio_track = AudioStreamTrack()
            pc.addTrack(audio_track)
            
            # Set up callbacks
            session.text_callback = lambda text: self._handle_transcribed_text(session_id, text)
            session.audio_callback = lambda audio: audio_track.add_audio_data(audio)
            
            voice_processor.set_callbacks(
                text_callback=session.text_callback,
                audio_callback=session.audio_callback
            )
            
            # Handle incoming audio tracks
            @pc.on("track")
            async def on_track(track):
                self.logger.info(f"📺 Received {track.kind} track for session {session_id}")
                
                if track.kind == "audio":
                    session.is_active = True
                    await self._process_incoming_audio(session, track)
            
            @pc.on("connectionstatechange")
            async def on_connection_state_change():
                self.logger.info(f"🔗 Connection state: {pc.connectionState} for session {session_id}")
                
                if pc.connectionState == "closed":
                    await self.close_session(session_id)
            
            # Store session
            self.sessions[session_id] = session
            
            self.logger.info(f"✅ Created voice session: {session_id}")
            return session_id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create session: {e}")
            raise
    
    async def handle_offer(self, session_id: str, offer_sdp: str) -> str:
        """
        Handle WebRTC offer and return answer.
        
        Args:
            session_id: Session identifier
            offer_sdp: Offer SDP from client
            
        Returns:
            Answer SDP
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        
        try:
            # Set remote description
            offer = RTCSessionDescription(sdp=offer_sdp, type="offer")
            await session.peer_connection.setRemoteDescription(offer)
            
            # Create answer
            answer = await session.peer_connection.createAnswer()
            await session.peer_connection.setLocalDescription(answer)
            
            self.logger.info(f"📞 Handled WebRTC offer for session {session_id}")
            return session.peer_connection.localDescription.sdp
            
        except Exception as e:
            self.logger.error(f"❌ Error handling offer for session {session_id}: {e}")
            raise
    
    async def _process_incoming_audio(self, session: VoiceSession, track: MediaStreamTrack):
        """Process incoming audio stream."""
        self.logger.info(f"🎤 Processing audio stream for session {session.session_id}")
        
        try:
            while True:
                frame = await track.recv()
                
                if frame is None:
                    break
                
                # Extract PCM16 bytes from frame regardless of input format
                try:
                    # Convert to signed 16-bit mono ndarray to avoid channel ambiguity
                    pcm_nd = frame.to_ndarray(format='s16', layout='mono')
                    channels = 1
                    audio_bytes = pcm_nd.tobytes()
                except Exception:
                    # Fallback to raw bytes; processor will attempt to interpret as int16
                    audio_bytes = frame.to_bytes()
                    channels = 1

                # Detect sample rate and channels; fall back to typical WebRTC defaults
                input_sample_rate = getattr(frame, 'sample_rate', 48000) or 48000
                # Log for diagnostics
                try:
                    self.logger.debug(f"Frame sample_rate={input_sample_rate}, channels={channels}, bytes={len(audio_bytes)}")
                except Exception:
                    pass

                # Process with voice processor using resampling-aware method
                text = await session.voice_processor.process_audio_stream_raw(
                    audio_bytes,
                    input_sample_rate=input_sample_rate,
                    channels=channels
                )
                
                # If we have transcribed text, send it to client immediately
                if text and text.strip():
                    await self._send_stt_result(session.session_id, text.strip())
                
        except Exception as e:
            self.logger.error(f"Error processing incoming audio: {e}")
        finally:
            session.is_active = False
    
    async def _handle_transcribed_text(self, session_id: str, text: str):
        """Handle transcribed text from audio."""
        self.logger.info(f"📝 Transcribed text for {session_id}: {text[:50]}...")
        
        try:
            if self.friend_instance:
                # Send to virtual friend for processing
                response = await asyncio.to_thread(
                    self.friend_instance.process_query, 
                    text
                )
                
                self.logger.info(f"🤖 Friend response: {response[:50]}...")
                
                # Generate speech from response
                if session_id in self.sessions:
                    session = self.sessions[session_id]
                    await session.voice_processor.generate_speech(response)
                else:
                    # Echo back for testing
                    echo_response = f"You said: {text}"
                    if session_id in self.sessions:
                        session = self.sessions[session_id]
                        await session.voice_processor.generate_speech(echo_response)
                    
        except Exception as e:
            self.logger.error(f"Error handling transcribed text: {e}")
    
    async def send_text_to_session(self, session_id: str, text: str):
        """
        Send text to session for speech synthesis.
        
        Args:
            session_id: Session identifier
            text: Text to convert to speech
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        await session.voice_processor.generate_speech(text)
    
    async def close_session(self, session_id: str):
        """Close voice session."""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        
        try:
            await session.peer_connection.close()
            await session.voice_processor.close()
            
            del self.sessions[session_id]
            
            self.logger.info(f"🔌 Closed session: {session_id}")
            
        except Exception as e:
            self.logger.error(f"Error closing session {session_id}: {e}")
    
    async def get_session_info(self, session_id: str) -> dict:
        """Get session information."""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        session = self.sessions[session_id]
        
        return {
            "session_id": session_id,
            "connection_state": session.peer_connection.connectionState,
            "is_active": session.is_active,
            "has_voice_processor": session.voice_processor is not None
        }
    
    async def list_sessions(self) -> dict:
        """List all active sessions."""
        sessions_info = {}
        
        for session_id, session in self.sessions.items():
            sessions_info[session_id] = await self.get_session_info(session_id)
        
        return {
            "total_sessions": len(self.sessions),
            "sessions": sessions_info
        }
    
    async def close_all_sessions(self):
        """Close all active sessions."""
        session_ids = list(self.sessions.keys())
        
        for session_id in session_ids:
            await self.close_session(session_id)
        
        self.logger.info("🔌 All sessions closed")
    
    async def _send_stt_result(self, session_id: str, text: str):
        """Send STT result to client via Socket.IO."""
        if self.socketio:
            try:
                self.logger.info(f"📤 Sending STT result: {text[:50]}...")
                self.socketio.emit('stt_result', {
                    'session_id': session_id,
                    'text': text,
                    'timestamp': asyncio.get_event_loop().time()
                }, broadcast=True, namespace='/')
            except Exception as e:
                self.logger.error(f"Error sending STT result via socket: {e}")
        else:
            self.logger.warning("No SocketIO instance available for STT results")


# Test function
async def test_webrtc_server():
    """Test WebRTC voice server."""
    server = WebRTCVoiceServer(verbose=True)
    
    # Create test session
    session_id = await server.create_session()
    print(f"Created session: {session_id}")
    
    # Get session info
    info = await server.get_session_info(session_id)
    print(f"Session info: {info}")
    
    # Test text-to-speech
    await server.send_text_to_session(session_id, "Hello! This is a test of the WebRTC server.")
    
    # Close session
    await server.close_session(session_id)
    print("Session closed")


if __name__ == "__main__":
    asyncio.run(test_webrtc_server())
