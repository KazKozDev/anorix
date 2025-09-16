/**
 * Voice Handler for Local Friend - Speech Recognition and Synthesis
 */

class VoiceHandler {
    constructor() {
        this.recognition = null;
        this.synthesis = null;
        this.isListening = false;
        this.language = 'ru-RU';
        this.speechRate = 1.0;
        this.speechPitch = 1.0;
        this.speechVolume = 1.0;
        
        this.init();
    }
    
    init() {
        this.setupSpeechRecognition();
        this.setupSpeechSynthesis();
        console.log('🎤 Voice Handler initialized');
    }
    
    setupSpeechRecognition() {
        // Check for speech recognition support
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            console.warn('Speech recognition not supported');
            return;
        }
        
        // Create recognition instance
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        // Configure recognition
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.lang = this.language;
        
        // Event listeners
        this.recognition.onstart = () => {
            console.log('🎤 Speech recognition started');
            this.isListening = true;
            this.onRecognitionStart();
        };
        
        this.recognition.onresult = (event) => {
            let finalTranscript = '';
            let interimTranscript = '';
            
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                
                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                } else {
                    interimTranscript += transcript;
                }
            }
            
            this.onRecognitionResult(finalTranscript, interimTranscript);
        };
        
        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.isListening = false;
            this.onRecognitionError(event.error);
        };
        
        this.recognition.onend = () => {
            console.log('🎤 Speech recognition ended');
            this.isListening = false;
            this.onRecognitionEnd();
        };
    }
    
    setupSpeechSynthesis() {
        if (!('speechSynthesis' in window)) {
            console.warn('Speech synthesis not supported');
            return;
        }
        
        this.synthesis = window.speechSynthesis;
        
        // Load available voices
        this.loadVoices();
        
        // Update voices when they change
        this.synthesis.onvoiceschanged = () => {
            this.loadVoices();
        };
    }
    
    loadVoices() {
        this.voices = this.synthesis.getVoices();
        console.log('🔊 Available voices:', this.voices.length);
        
        // Find best Russian voice
        this.russianVoice = this.voices.find(voice => 
            voice.lang.startsWith('ru') && voice.localService
        ) || this.voices.find(voice => voice.lang.startsWith('ru'));
        
        // Find best English voice as fallback
        this.englishVoice = this.voices.find(voice => 
            voice.lang.startsWith('en') && voice.localService
        ) || this.voices.find(voice => voice.lang.startsWith('en'));
    }
    
    // Speech Recognition Methods
    startRecording() {
        return new Promise((resolve, reject) => {
            if (!this.recognition) {
                reject(new Error('Speech recognition not available'));
                return;
            }
            
            if (this.isListening) {
                reject(new Error('Already listening'));
                return;
            }
            
            this.recordingPromise = { resolve, reject };
            
            try {
                this.recognition.start();
            } catch (error) {
                reject(error);
            }
        });
    }
    
    stopRecording() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
        return Promise.resolve();
    }
    
    // Speech Synthesis Methods
    speak(text, options = {}) {
        return new Promise((resolve, reject) => {
            if (!this.synthesis) {
                reject(new Error('Speech synthesis not available'));
                return;
            }
            
            // Stop any current speech
            this.synthesis.cancel();
            
            // Create utterance
            const utterance = new SpeechSynthesisUtterance(text);
            
            // Set voice based on language
            let selectedVoice;
            if (this.language.startsWith('ru')) {
                selectedVoice = this.russianVoice;
            } else if (this.language.startsWith('en')) {
                selectedVoice = this.englishVoice;
            }
            
            if (selectedVoice) {
                utterance.voice = selectedVoice;
            }
            
            // Set speech parameters
            utterance.rate = options.rate || this.speechRate;
            utterance.pitch = options.pitch || this.speechPitch;
            utterance.volume = options.volume || this.speechVolume;
            utterance.lang = this.language;
            
            // Event listeners
            utterance.onstart = () => {
                console.log('🔊 Speech started');
                this.onSpeechStart();
            };
            
            utterance.onend = () => {
                console.log('🔊 Speech ended');
                this.onSpeechEnd();
                resolve();
            };
            
            utterance.onerror = (event) => {
                console.error('Speech synthesis error:', event.error);
                this.onSpeechError(event.error);
                reject(new Error(event.error));
            };
            
            // Speak
            this.synthesis.speak(utterance);
        });
    }
    
    stopSpeech() {
        if (this.synthesis) {
            this.synthesis.cancel();
        }
    }
    
    // Configuration Methods
    setLanguage(language) {
        this.language = language;
        if (this.recognition) {
            this.recognition.lang = language;
        }
        console.log('🌐 Language set to:', language);
    }
    
    setSpeechRate(rate) {
        this.speechRate = Math.max(0.1, Math.min(10, rate));
        console.log('⚡ Speech rate set to:', this.speechRate);
    }
    
    setSpeechPitch(pitch) {
        this.speechPitch = Math.max(0, Math.min(2, pitch));
        console.log('🎵 Speech pitch set to:', this.speechPitch);
    }
    
    setSpeechVolume(volume) {
        this.speechVolume = Math.max(0, Math.min(1, volume));
        console.log('🔊 Speech volume set to:', this.speechVolume);
    }
    
    // Event Handlers (can be overridden)
    onRecognitionStart() {
        // Update UI to show listening state
        this.updateVoiceStatus('Listening...', 'listening');
    }
    
    onRecognitionResult(finalTranscript, interimTranscript) {
        // Update UI with recognition results
        if (interimTranscript) {
            this.updateVoiceStatus(`Recognizing: "${interimTranscript}"`, 'recognizing');
        }
        
        if (finalTranscript && this.recordingPromise) {
            console.log('🎤 Final transcript:', finalTranscript);
            this.recordingPromise.resolve(finalTranscript);
            this.recordingPromise = null;
        }
    }
    
    onRecognitionError(error) {
        console.error('Recognition error:', error);
        
        let errorMessage = 'Speech recognition error';
        switch (error) {
            case 'no-speech':
                errorMessage = 'No speech detected';
                break;
            case 'audio-capture':
                errorMessage = 'Microphone not available';
                break;
            case 'not-allowed':
                errorMessage = 'Microphone access denied';
                break;
            case 'network':
                errorMessage = 'Network error';
                break;
        }
        
        this.updateVoiceStatus(errorMessage, 'error');
        
        if (this.recordingPromise) {
            this.recordingPromise.reject(new Error(errorMessage));
            this.recordingPromise = null;
        }
    }
    
    onRecognitionEnd() {
        // Recognition ended - could be natural or forced
        this.updateVoiceStatus('Press and speak', 'ready');
        
        if (this.recordingPromise) {
            // If we have a promise waiting, resolve with empty string
            this.recordingPromise.resolve('');
            this.recordingPromise = null;
        }
    }
    
    onSpeechStart() {
        // Update UI to show speaking state
        this.updateVoiceStatus('Speaking...', 'speaking');
        
        // Update friend status
        if (window.friendApp) {
            const statusEl = document.getElementById('friendStatusText');
            if (statusEl) {
                statusEl.textContent = 'Speaking...';
            }
        }
    }
    
    onSpeechEnd() {
        // Update UI when speech ends
        this.updateVoiceStatus('Ready to chat', 'ready');
        
        // Update friend status
        if (window.friendApp) {
            const statusEl = document.getElementById('friendStatusText');
            if (statusEl) {
                statusEl.textContent = 'Voice mode active';
            }
        }
    }
    
    onSpeechError(error) {
        console.error('Speech error:', error);
        this.updateVoiceStatus('Speech synthesis error', 'error');
    }
    
    updateVoiceStatus(message, state) {
        const voiceStatus = document.getElementById('voiceStatus');
        if (voiceStatus) {
            voiceStatus.textContent = message;
            voiceStatus.className = `voice-status ${state}`;
        }
        
        // Update voice visualizer based on state
        this.updateVoiceVisualizer(state);
    }
    
    updateVoiceVisualizer(state) {
        const visualizer = document.getElementById('voiceVisualizer');
        const waveBars = visualizer?.querySelectorAll('.wave-bar');
        
        if (!waveBars) return;
        
        // Reset all animations
        waveBars.forEach(bar => {
            bar.style.animation = '';
        });
        
        // Apply state-specific animations
        switch (state) {
            case 'listening':
                waveBars.forEach((bar, index) => {
                    bar.style.animation = `wave 1.2s ease-in-out infinite ${index * 0.1}s`;
                });
                break;
            case 'recognizing':
                waveBars.forEach((bar, index) => {
                    bar.style.animation = `wave 0.8s ease-in-out infinite ${index * 0.05}s`;
                });
                break;
            case 'speaking':
                waveBars.forEach((bar, index) => {
                    bar.style.animation = `wave 1.5s ease-in-out infinite ${index * 0.2}s`;
                });
                break;
        }
    }
    
    // Utility Methods
    isSupported() {
        return !!(this.recognition && this.synthesis);
    }
    
    getAvailableLanguages() {
        if (!this.voices) return [];
        
        const languages = [...new Set(this.voices.map(voice => voice.lang))];
        return languages.sort();
    }
    
    getVoicesForLanguage(language) {
        if (!this.voices) return [];
        
        return this.voices.filter(voice => voice.lang.startsWith(language.split('-')[0]));
    }
    
    // Test Methods
    testRecognition() {
        console.log('🧪 Testing speech recognition...');
        
        this.startRecording()
            .then(text => {
                console.log('✅ Recognition test result:', text);
                alert(`Recognized text: "${text}"`);
            })
            .catch(error => {
                console.error('❌ Recognition test failed:', error);
                alert(`Test error: ${error.message}`);
            });
    }
    
    testSynthesis(text = 'Hello! This is a speech synthesis test.') {
        console.log('🧪 Testing speech synthesis...');
        
        this.speak(text)
            .then(() => {
                console.log('✅ Synthesis test completed');
            })
            .catch(error => {
                console.error('❌ Synthesis test failed:', error);
                alert(`Synthesis error: ${error.message}`);
            });
    }
}

// Initialize voice handler
window.VoiceHandler = new VoiceHandler();

// Add debugging methods to global scope in development
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    window.testVoice = () => {
        console.log('🧪 Voice tests available:');
        console.log('- VoiceHandler.testRecognition()');
        console.log('- VoiceHandler.testSynthesis()');
        console.log('- VoiceHandler.getAvailableLanguages()');
        console.log('- VoiceHandler.isSupported()');
    };
    
    // Auto-test on load (commented out for production)
    // setTimeout(() => {
    //     if (VoiceHandler.isSupported()) {
    //         console.log('✅ Voice features supported');
    //         testVoice();
    //     } else {
    //         console.warn('⚠️ Voice features not fully supported');
    //     }
    // }, 1000);
}