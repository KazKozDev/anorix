"""
Advanced Voice Engine for Virtual Friend

This module provides:
- WebRTC streaming audio processing
- Whisper-based speech-to-text
- Bark-based text-to-speech
- Real-time voice communication
"""

from .voice_processor import VoiceProcessor
from .webrtc_server import WebRTCVoiceServer, VoiceSession

__version__ = "1.0.0"
__all__ = ["VoiceProcessor", "WebRTCVoiceServer", "VoiceSession"]