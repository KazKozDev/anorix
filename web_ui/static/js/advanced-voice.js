/**
 * Advanced Voice Handler with WebRTC Streaming and Wake Word Detection
 * Integrates with existing Local Friend interface
 */

class AdvancedVoiceHandler {
    constructor(app) {
        this.app = app; // Reference to main FriendApp
        
        // Connection
        this.socket = null;
        this.peerConnection = null;
        this.voiceSession = null;
        
        // Audio streams
        this.localStream = null;
        this.remoteStream = null;
        this.audioContext = null;
        
        // Wake word detection
        this.wakeWordDetector = null;
        this.wakeWordEnabled = false;
        this.isAwake = false;
        
        // State
        this.isConnected = false;
        this.isStreaming = false;
        this.isProcessing = false;
        
        // Settings
        this.sampleRate = 16000;
        this.language = 'en-US';
        
        console.log('🎙️ Advanced Voice Handler initialized');
    }
    
    async initialize() {
        /* Initialize advanced voice system */
        try {
            // Connect to Socket.IO
            await this.connectSocket();
            
            // Initialize audio context
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Setup WebRTC
            await this.setupWebRTC();
            
            // Initialize wake word detector - TEMPORARILY DISABLED
            // await this.initializeWakeWordDetector();
            
            console.log('✅ Advanced voice system ready');
            return true;
            
        } catch (error) {
            console.error('❌ Failed to initialize advanced voice:', error);
            return false;
        }
    }
    
    connectSocket() {
        return new Promise((resolve, reject) => {
            // Connect to Socket.IO server
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('🔗 Connected to voice server');
                this.isConnected = true;
                resolve();
            });
            
            this.socket.on('disconnect', () => {
                console.log('🔌 Disconnected from voice server');
                this.isConnected = false;
            });
            
            this.socket.on('status', (data) => {
                console.log('📊 Server status:', data);
                if (!data.voice_available) {
                    console.warn('⚠️ Voice features not available on server');
                }
            });
            
            // WebRTC signaling
            this.socket.on('voice_session_created', (data) => {
                this.voiceSession = data.session_id;
                console.log('🎙️ Voice session created:', this.voiceSession);
            });
            
            this.socket.on('webrtc_answer', (data) => {
                this.handleWebRTCAnswer(data);
            });
            
            this.socket.on('webrtc_error', (error) => {
                console.error('WebRTC Error:', error);
            });
            
            this.socket.on('tts_success', (data) => {
                console.log('🗣️ TTS Success:', data);
            });
            
            // STT results
            this.socket.on('stt_result', (data) => {
                console.log('🎤 STT Result:', data.text);
                if (data.text && data.text.trim()) {
                    this.handleTranscribedText(data.text.trim());
                }
            });
            
            // STT errors
            this.socket.on('stt_error', (error) => {
                console.error('❌ STT Error:', error);
                this.updateVoiceUI('error', 'Speech recognition error');
            });
            
            // Connection timeout
            setTimeout(() => {
                if (!this.isConnected) {
                    reject(new Error('Connection timeout'));
                }
            }, 5000);
        });
    }
    
    async setupWebRTC() {
        /* Setup WebRTC peer connection */
        this.peerConnection = new RTCPeerConnection({
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' }
            ]
        });
        
        // Handle remote stream
        this.peerConnection.ontrack = (event) => {
            console.log('📺 Received remote track');
            this.remoteStream = event.streams[0];
            this.playRemoteAudio();
        };
        
        // Handle ICE candidates
        this.peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                console.log('🧊 ICE candidate generated');
                // Send to signaling server if needed
            }
        };
        
        // Connection state monitoring
        this.peerConnection.onconnectionstatechange = () => {
            console.log('🔗 WebRTC connection state:', this.peerConnection.connectionState);
        };
    }
    
    async startVoiceSession() {
        /* Start new voice communication session */
        try {
            if (!this.isConnected) {
                throw new Error('Not connected to server');
            }
            
            // Create voice session on server
            this.socket.emit('create_voice_session', {
                config: {
                    whisper_model: 'base',
                    bark_voice: 'v2/en_speaker_6'
                }
            });
            
            // Wait for session creation
            await this.waitForSession();
            
            // Get user media
            this.localStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: this.sampleRate,
                    channelCount: 1,
                    autoGainControl: true,
                    noiseSuppression: true,
                    echoCancellation: true
                },
                video: false
            });
            
            console.log('🎤 Microphone access granted');
            
            // Add audio track to peer connection
            this.localStream.getTracks().forEach(track => {
                this.peerConnection.addTrack(track, this.localStream);
            });
            
            // Create offer
            const offer = await this.peerConnection.createOffer();
            await this.peerConnection.setLocalDescription(offer);
            
            // Send offer to server
            this.socket.emit('webrtc_offer', {
                session_id: this.voiceSession,
                offer: offer.sdp
            });
            
            this.isStreaming = true;
            console.log('📡 Voice streaming started');
            
            // Update UI
            this.updateVoiceUI('streaming', 'Voice connection active');
            
        } catch (error) {
            console.error('❌ Failed to start voice session:', error);
            this.updateVoiceUI('error', 'Failed to start voice connection');
            throw error;
        }
    }
    
    async handleWebRTCAnswer(data) {
        /* Handle WebRTC answer from server */
        try {
            const answer = new RTCSessionDescription({
                type: 'answer',
                sdp: data.answer
            });
            
            await this.peerConnection.setRemoteDescription(answer);
            console.log('📞 WebRTC connection established');
            
        } catch (error) {
            console.error('Error handling WebRTC answer:', error);
        }
    }
    
    waitForSession(timeout = 5000) {
        /* Wait for voice session to be created */
        return new Promise((resolve, reject) => {
            const checkSession = () => {
                if (this.voiceSession) {
                    resolve();
                } else {
                    setTimeout(checkSession, 100);
                }
            };
            
            setTimeout(() => reject(new Error('Session creation timeout')), timeout);
            checkSession();
        });
    }
    
    playRemoteAudio() {
        /* Play audio received from server */
        if (this.remoteStream) {
            // Create audio element for playback
            const audioElement = document.createElement('audio');
            audioElement.srcObject = this.remoteStream;
            audioElement.autoplay = true;
            audioElement.style.display = 'none';
            
            document.body.appendChild(audioElement);
            
            // Remove after playback
            audioElement.onended = () => {
                document.body.removeChild(audioElement);
            };
            
            console.log('🔊 Playing remote audio');
        }
    }
    
    async stopVoiceSession() {
        /* Stop voice communication session */
        try {
            this.isStreaming = false;
            
            // Stop local stream
            if (this.localStream) {
                this.localStream.getTracks().forEach(track => track.stop());
                this.localStream = null;
            }
            
            // Close peer connection
            if (this.peerConnection) {
                this.peerConnection.close();
                await this.setupWebRTC(); // Reset for next session
            }
            
            // Clear session
            this.voiceSession = null;
            
            console.log('🔇 Voice session stopped');
            this.updateVoiceUI('ready', 'Ready for voice communication');
            
        } catch (error) {
            console.error('Error stopping voice session:', error);
        }
    }
    
    async toggleVoiceMode(enabled) {
        /* Toggle voice mode on/off */
        try {
            if (enabled) {
                await this.initialize();
                await this.startVoiceSession();
                return true;
            } else {
                await this.stopVoiceSession();
                return false;
            }
        } catch (error) {
            console.error('Error toggling voice mode:', error);
            return false;
        }
    }
    
    // Wake word detection methods
    async initializeWakeWordDetector() {
        /* Initialize wake word detection with Porcupine */
        try {
            if (!window.WakeWordDetector) {
                console.warn('⚠️ WakeWordDetector not available');
                return false;
            }
            
            this.wakeWordDetector = new window.WakeWordDetector();
            
            // Setup callbacks
            this.wakeWordDetector.onWakeWordDetected = () => {
                this.onWakeWordDetected();
            };
            
            this.wakeWordDetector.onError = (error) => {
                console.error('Wake word detection error:', error);
                this.updateVoiceUI('error', 'Wake word detection error');
            };
            
            this.wakeWordDetector.onStatusChange = (status) => {
                console.log('Wake word status:', status);
                this.updateWakeWordUI(status);
            };
            
            // Initialize detector
            const success = await this.wakeWordDetector.initialize();
            
            if (success) {
                console.log('✅ Wake word detector initialized');
                return true;
            } else {
                console.warn('⚠️ Wake word detector using fallback mode');
                return false;
            }
            
        } catch (error) {
            console.error('❌ Failed to initialize wake word detector:', error);
            return false;
        }
    }
    
    async enableWakeWord(enabled = true) {
        /* Enable/disable wake word detection - TEMPORARILY DISABLED */
        console.log('⚠️ Wake word detection temporarily disabled');
        return false;
        
        /* COMMENTED CODE - RESTORE IF NEEDED
        try {
            if (!this.wakeWordDetector) {
                console.warn('⚠️ Wake word detector not available');
                return false;
            }
            
            this.wakeWordEnabled = enabled;
            
            if (enabled) {
                console.log('👂 Starting wake word detection');
                const success = await this.wakeWordDetector.startListening();
                
                if (success) {
                    this.updateVoiceUI('wake-word', 'Listening for "Start"...');
                    console.log('✅ Wake word detection started');
                } else {
                    console.error('❌ Failed to start wake word detection');
                }
                
                return success;
                
            } else {
                console.log('🔇 Stopping wake word detection');
                await this.wakeWordDetector.stopListening();
                this.updateVoiceUI('ready', 'Ready for voice communication');
                return true;
            }
            
        } catch (error) {
            console.error('Error toggling wake word:', error);
            return false;
        }
        */
    }
    
    onWakeWordDetected() {
        /* Handle wake word detection */
        console.log('👋 Wake word detected: "Start"');
        this.isAwake = true;
        
        // Visual feedback
        this.updateVoiceUI('activated', 'Wake word "Start" detected!');
        
        // Auto-activate voice mode if not already active
        if (!this.isStreaming) {
            console.log('🚀 Auto-activating voice mode...');
            
            // Toggle the voice mode switch
            if (this.app.voiceModeToggle) {
                this.app.voiceModeToggle.checked = true;
            }
            
            // Start voice session
            this.toggleVoiceMode(true).then(() => {
                console.log('✅ Voice mode activated by wake word');
                
                // Continue listening for speech after activation
                setTimeout(() => {
                    this.startListeningForSpeech();
                }, 1000);
                
            }).catch(error => {
                console.error('❌ Failed to activate voice mode:', error);
            });
        }
        
        // Brief timeout before returning to listening
        setTimeout(() => {
            this.isAwake = false;
            if (this.wakeWordEnabled && !this.isStreaming) {
                this.updateVoiceUI('wake-word', 'Listening for "Start"...');
            }
        }, 3000);
    }
    
    updateWakeWordUI(status) {
        /* Update UI based on wake word status */
        const statusMessages = {
            'initialized': 'Wake word ready',
            'fallback': 'Wake word (fallback mode)',
            'listening': 'Listening for "Start"...',
            'stopped': 'Wake word stopped'
        };
        
        const message = statusMessages[status] || `Wake word: ${status}`;
        
        // Update status in UI if wake word is primary mode
        if (this.wakeWordEnabled && !this.isStreaming) {
            this.updateVoiceUI('wake-word', message);
        }
    }
    
    handleTranscribedText(text) {
        /* Handle transcribed speech text */
        console.log(`🗨️ Transcribed: "${text}"`);
        
        // Show transcribed text in chat immediately
        this.displayUserMessage(text);
        
        // Send to virtual friend via main app
        if (this.app && this.app.sendMessage) {
            this.app.sendMessage(text);
        } else {
            console.error('❌ Cannot send message - app.sendMessage not available');
        }
        
        // Update voice UI
        this.updateVoiceUI('processing', 'Processing...');
    }
    
    displayUserMessage(text) {
        /* Display user message in chat */
        if (this.app && this.app.addMessage) {
            this.app.addMessage(text, 'user');
        } else {
            // Fallback - directly add to chat
            const chatMessages = document.getElementById('chatMessages');
            if (chatMessages) {
                const messageEl = document.createElement('div');
                messageEl.className = 'message user-message';
                messageEl.innerHTML = `
                    <div class="message-content">
                        <div class="message-text">${text}</div>
                        <div class="message-time">${new Date().toLocaleTimeString()}</div>
                    </div>
                `;
                chatMessages.appendChild(messageEl);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }
    }
    
    startListeningForSpeech() {
        /* Start listening for speech after wake word activation */
        console.log('🎤 Starting speech listening...');
        
        if (!this.isStreaming || !this.voiceSession) {
            console.error('❌ Cannot start speech listening - no active session');
            return;
        }
        
        // Update UI to show listening state
        this.updateVoiceUI('listening', 'Listening...');
        
        // The WebRTC connection should already be streaming audio to the server
        // Server will process the audio and send back STT results via socket
        console.log('📡 WebRTC audio streaming is active, waiting for transcription...');
    }
    
    // UI Integration methods
    updateVoiceUI(state, message) {
        /* Update voice UI elements */
        const voiceStatus = document.getElementById('voiceStatus');
        const voiceVisualizer = document.getElementById('voiceVisualizer');
        
        if (voiceStatus) {
            voiceStatus.textContent = message;
            voiceStatus.className = `voice-status ${state}`;
        }
        
        // Update visualizer
        this.updateVoiceVisualizer(state);
        
        // Update friend status
        if (this.app.friendStatusText) {
            this.app.friendStatusText.textContent = message;
        }
    }
    
    updateVoiceVisualizer(state) {
        /* Update voice visualizer animation */
        const visualizer = document.getElementById('voiceVisualizer');
        const waveBars = visualizer?.querySelectorAll('.wave-bar');
        
        if (!waveBars) return;
        
        // Reset animations
        waveBars.forEach(bar => {
            bar.style.animation = '';
        });
        
        // Apply state-specific animations
        switch (state) {
            case 'streaming':
                waveBars.forEach((bar, index) => {
                    bar.style.animation = `wave 1s ease-in-out infinite ${index * 0.1}s`;
                });
                break;
            case 'processing':
                waveBars.forEach((bar, index) => {
                    bar.style.animation = `wave 0.6s ease-in-out infinite ${index * 0.05}s`;
                });
                break;
            case 'error':
                visualizer.style.display = 'none';
                break;
        }
    }
    
    // Compatibility methods with existing VoiceHandler
    isSupported() {
        /* Check if advanced voice is supported */
        return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && 
                 window.RTCPeerConnection && window.io);
    }
    
    // Test methods
    async testVoiceConnection() {
        /* Test voice connection */
        try {
            console.log('🧪 Testing voice connection...');
            
            await this.initialize();
            console.log('✅ Socket connection: OK');
            
            // Test microphone access
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop());
            console.log('✅ Microphone access: OK');
            
            console.log('✅ Voice system test completed');
            return true;
            
        } catch (error) {
            console.error('❌ Voice system test failed:', error);
            return false;
        }
    }
    
    // Cleanup
    async disconnect() {
        /* Disconnect and cleanup resources */
        // Stop wake word detection
        if (this.wakeWordDetector) {
            await this.wakeWordDetector.cleanup();
            this.wakeWordDetector = null;
        }
        
        if (this.socket) {
            this.socket.disconnect();
        }
        
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => track.stop());
        }
        
        if (this.peerConnection) {
            this.peerConnection.close();
        }
        
        if (this.audioContext) {
            this.audioContext.close();
        }
        
        console.log('🔌 Advanced voice handler disconnected');
    }
}

// Export for use in main app
window.AdvancedVoiceHandler = AdvancedVoiceHandler;