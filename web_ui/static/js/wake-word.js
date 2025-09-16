/**
 * Wake Word Detection using Porcupine
 * Activated by "Start" (demo uses a close built-in keyword)
 */

class WakeWordDetector {
    constructor() {
        this.porcupine = null;
        this.isListening = false;
        this.isInitialized = false;
        this.mediaStream = null;
        this.audioContext = null;
        this.processor = null;
        
        // Callbacks
        this.onWakeWordDetected = null;
        this.onError = null;
        this.onStatusChange = null;
        
        // Porcupine Access Key - demo placeholder; get your key at https://picovoice.ai/
        this.accessKey = 'YOUR_ACCESS_KEY_HERE';
        
        this.log('WakeWordDetector initialized');
    }
    
    /**
     * Initialize Porcupine
     */
    async initialize() {
        try {
            if (this.isInitialized) {
                this.log('Already initialized');
                return true;
            }
            
            // Check Porcupine availability
            if (!window.PorcupineWeb) {
                throw new Error('Porcupine WASM not loaded');
            }
            
            this.log('Initializing Porcupine...');
            
            // For demo we use the built-in "hey siri" (close to "Start").
            // In production, use a custom model for "Start".
            const porcupineWorker = await window.PorcupineWeb.PorcupineWorker.create({
                accessKey: this.accessKey,
                keywords: [window.PorcupineWeb.BuiltinKeyword.HEY_SIRI], // Temporary instead of Start
                start: false
            });
            
            this.porcupine = porcupineWorker;
            
            // Wake word detection handler
            this.porcupine.onmessage = (event) => {
                if (event.data.command === 'keyword') {
                    this.log('Wake word detected!');
                    if (this.onWakeWordDetected) {
                        this.onWakeWordDetected();
                    }
                }
            };
            
            this.isInitialized = true;
            this.log('Porcupine initialized successfully');
            
            if (this.onStatusChange) {
                this.onStatusChange('initialized');
            }
            
            return true;
            
        } catch (error) {
            this.logError('Failed to initialize Porcupine:', error);
            
            // Fallback - use simple microphone activity detection
            await this.initializeFallback();
            
            if (this.onError) {
                this.onError(error);
            }
            
            return false;
        }
    }
    
    /**
     * Fallback mode - simple microphone activity detection
     */
    async initializeFallback() {
        this.log('Initializing fallback wake word detection...');
        
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: { 
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 16000
                } 
            });
            
            this.mediaStream = stream;
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            const source = this.audioContext.createMediaStreamSource(stream);
            const analyser = this.audioContext.createAnalyser();
            analyser.fftSize = 256;
            
            source.connect(analyser);
            
            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            
            // Simple activity check to approximate "Start"
            let silenceStart = Date.now();
            let speaking = false;
            
            const checkAudioLevel = () => {
                if (!this.isListening) return;
                
                analyser.getByteFrequencyData(dataArray);
                
                const average = dataArray.reduce((sum, value) => sum + value, 0) / bufferLength;
                
                if (average > 30) { // Activity threshold
                    if (!speaking) {
                        speaking = true;
                        silenceStart = Date.now();
                    }
                } else {
                    if (speaking && Date.now() - silenceStart > 500) {
                        // Detected speech activity - treat as "Start"
                        speaking = false;
                        this.log('Wake word "Start" detected (fallback mode)');
                        if (this.onWakeWordDetected) {
                            this.onWakeWordDetected();
                        }
                    }
                }
                
                if (this.isListening) {
                    requestAnimationFrame(checkAudioLevel);
                }
            };
            
            this.fallbackChecker = checkAudioLevel;
            this.isInitialized = true;
            this.log('Fallback wake word detection initialized');
            
            if (this.onStatusChange) {
                this.onStatusChange('fallback');
            }
            
        } catch (error) {
            this.logError('Fallback initialization failed:', error);
            throw error;
        }
    }
    
    /**
     * Start wake word detection
     */
    async startListening() {
        try {
            if (!this.isInitialized) {
                await this.initialize();
            }
            
            if (this.isListening) {
                this.log('Already listening');
                return true;
            }
            
            this.log('Starting wake word detection...');
            
            if (this.porcupine) {
                // Use Porcupine
                if (!this.mediaStream) {
                    this.mediaStream = await navigator.mediaDevices.getUserMedia({ 
                        audio: { 
                            sampleRate: 16000,
                            channelCount: 1,
                            echoCancellation: true,
                            noiseSuppression: true
                        } 
                    });
                }
                
                this.porcupine.postMessage({
                    command: 'start',
                    inputStream: this.mediaStream
                });
                
            } else if (this.fallbackChecker) {
                // Use fallback
                this.fallbackChecker();
            }
            
            this.isListening = true;
            this.log('Wake word detection started');
            
            if (this.onStatusChange) {
                this.onStatusChange('listening');
            }
            
            return true;
            
        } catch (error) {
            this.logError('Failed to start listening:', error);
            
            if (this.onError) {
                this.onError(error);
            }
            
            return false;
        }
    }
    
    /**
     * Stop wake word detection
     */
    async stopListening() {
        try {
            if (!this.isListening) {
                this.log('Not listening');
                return;
            }
            
            this.log('Stopping wake word detection...');
            
            if (this.porcupine) {
                this.porcupine.postMessage({ command: 'pause' });
            }
            
            this.isListening = false;
            
            if (this.onStatusChange) {
                this.onStatusChange('stopped');
            }
            
            this.log('Wake word detection stopped');
            
        } catch (error) {
            this.logError('Failed to stop listening:', error);
        }
    }
    
    /**
     * Full cleanup of resources
     */
    async cleanup() {
        try {
            this.log('Cleaning up wake word detector...');
            
            await this.stopListening();
            
            if (this.porcupine) {
                this.porcupine.postMessage({ command: 'release' });
                this.porcupine = null;
            }
            
            if (this.mediaStream) {
                this.mediaStream.getTracks().forEach(track => track.stop());
                this.mediaStream = null;
            }
            
            if (this.audioContext) {
                await this.audioContext.close();
                this.audioContext = null;
            }
            
            this.isInitialized = false;
            this.isListening = false;
            
            this.log('Wake word detector cleaned up');
            
        } catch (error) {
            this.logError('Cleanup failed:', error);
        }
    }
    
    /**
     * Get detector status
     */
    getStatus() {
        return {
            isInitialized: this.isInitialized,
            isListening: this.isListening,
            hasPorcupine: !!this.porcupine,
            isFallback: !this.porcupine && this.isInitialized
        };
    }
    
    /**
     * Set access key for Porcupine
     */
    setAccessKey(accessKey) {
        this.accessKey = accessKey;
        this.log('Access key updated');
    }
    
    /**
     * Logging helpers
     */
    log(message, ...args) {
        console.log(`🔊 [WakeWord] ${message}`, ...args);
    }
    
    logError(message, error) {
        console.error(`❌ [WakeWord] ${message}`, error);
    }
}

// Global export
window.WakeWordDetector = WakeWordDetector;