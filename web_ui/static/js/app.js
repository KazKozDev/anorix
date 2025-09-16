/**
 * Local Friend Web UI - Main Application Logic
 */

class LocalFriendApp {
    constructor() {
        this.voiceMode = false;
        this.isRecording = false;
        this.isProcessing = false;
        this.conversationCount = 0;
        this.memoryCount = 0;
        this.panelUpdateInterval = null;
        
        // Voice systems
        this.legacyVoiceHandler = null;
        this.advancedVoiceHandler = null;
        this.useAdvancedVoice = true; // Prefer advanced voice
        
        // API endpoints
        this.API_BASE = '/api';
        
        // Initialize app
        this.init();
    }
    
    async init() {
        this.initElements();
        this.initEventListeners();
        await this.initVoiceSystem();
        this.loadSettings();
        this.checkFriendStatus();
        
        // Auto-scroll to bottom
        this.scrollToBottom();
        
        console.log('🤖 Local Friend App initialized');
    }
    
    async initVoiceSystem() {
        /* Initialize voice system (advanced or legacy fallback) */
        try {
            // Check if advanced voice is available
            if (window.AdvancedVoiceHandler) {
                this.advancedVoiceHandler = new AdvancedVoiceHandler(this);
                
                // Test advanced voice support
                const isSupported = this.advancedVoiceHandler.isSupported();
                console.log(`🎙️ Advanced voice supported: ${isSupported}`);
                
                if (isSupported) {
                    this.useAdvancedVoice = true;
                    console.log('✅ Using Advanced Voice System');
                } else {
                    this.useAdvancedVoice = false;
                    this.advancedVoiceHandler = null;
                }
            }
            
            // Fallback to legacy voice handler
            if (!this.useAdvancedVoice && window.VoiceHandler) {
                this.legacyVoiceHandler = window.VoiceHandler;
                console.log('⚠️ Using Legacy Voice System');
            }
            
            // Show voice capability status
            this.updateVoiceCapabilityUI();
            
        } catch (error) {
            console.error('Error initializing voice system:', error);
            this.useAdvancedVoice = false;
        }
    }
    
    updateVoiceCapabilityUI() {
        /* Update UI to show voice capabilities */
        const voiceToggleContainer = document.querySelector('.voice-toggle-container');
        const toggleLabel = voiceToggleContainer?.querySelector('.toggle-label');
        
        if (toggleLabel) {
            if (this.useAdvancedVoice) {
                toggleLabel.innerHTML = 'Voice mode <span style="color: #cdaa3d; font-size: 0.8em;">(WebRTC)</span>';
            } else if (this.legacyVoiceHandler) {
                toggleLabel.innerHTML = 'Voice mode <span style="color: #8b7355; font-size: 0.8em;">(Legacy)</span>';
            } else {
                toggleLabel.innerHTML = 'Voice mode <span style="color: #ef4444; font-size: 0.8em;">(Unavailable)</span>';
                if (this.voiceModeToggle) {
                    this.voiceModeToggle.disabled = true;
                }
            }
        }
    }
    
    initElements() {
        // Voice elements
        this.voiceModeToggle = document.getElementById('voiceMode');
        this.wakeWordModeToggle = document.getElementById('wakeWordMode');
        this.textInputArea = document.getElementById('textInputArea');
        this.voiceInputArea = document.getElementById('voiceInputArea');
        this.voiceBtn = document.getElementById('voiceBtn');
        this.voiceVisualizer = document.getElementById('voiceVisualizer');
        this.voiceStatus = document.getElementById('voiceStatus');
        
        // Chat elements
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.typingIndicator = document.getElementById('typingIndicator');
        
        // File upload elements
        this.fileBtn = document.getElementById('fileBtn');
        this.fileInput = document.getElementById('fileInput');
        
        // Status elements
        this.friendStatus = document.getElementById('friendStatus');
        this.friendStatusText = document.getElementById('friendStatusText');
        
        // Panel elements
        this.infoBtn = document.getElementById('infoBtn');
        this.sidePanel = document.getElementById('sidePanel');
        this.panelClose = document.getElementById('panelClose');
        
        // Modal elements
        this.settingsBtn = document.getElementById('settingsBtn');
        this.settingsModal = document.getElementById('settingsModal');
        this.modalClose = document.getElementById('modalClose');
        
        // Info elements
        this.friendMood = document.getElementById('friendMood');
        this.conversationCountEl = document.getElementById('conversationCount');
        this.memoryCountEl = document.getElementById('memoryCount');
        this.memoryList = document.getElementById('memoryList');
        this.moodChart = document.getElementById('moodChart');
    }
    
    initEventListeners() {
        // Voice mode toggle
        this.voiceModeToggle.addEventListener('change', (e) => {
            this.toggleVoiceMode(e.target.checked);
        });
        
        // Wake word mode toggle - TEMPORARILY DISABLED
        /*
        if (this.wakeWordModeToggle) {
            this.wakeWordModeToggle.addEventListener('change', (e) => {
                this.toggleWakeWordMode(e.target.checked);
            });
        }
        */
        
        // Text input
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        this.messageInput.addEventListener('input', () => {
            this.adjustTextareaHeight();
        });
        
        this.sendBtn.addEventListener('click', () => {
            this.sendMessage();
        });
        
        // File upload button click
        this.fileBtn.addEventListener('click', () => {
            this.fileInput.click();
        });
        
        // File input change
        this.fileInput.addEventListener('change', (e) => {
            this.handleFileUpload(e);
        });
        
        // Voice input
        this.voiceBtn.addEventListener('mousedown', () => {
            if (!this.isProcessing) {
                this.startVoiceRecording();
            }
        });
        
        this.voiceBtn.addEventListener('mouseup', () => {
            if (this.isRecording) {
                this.stopVoiceRecording();
            }
        });
        
        this.voiceBtn.addEventListener('mouseleave', () => {
            if (this.isRecording) {
                this.stopVoiceRecording();
            }
        });
        
        // Touch events for mobile
        this.voiceBtn.addEventListener('touchstart', (e) => {
            e.preventDefault();
            if (!this.isProcessing) {
                this.startVoiceRecording();
            }
        });
        
        this.voiceBtn.addEventListener('touchend', (e) => {
            e.preventDefault();
            if (this.isRecording) {
                this.stopVoiceRecording();
            }
        });
        
        // Panel controls
        this.infoBtn.addEventListener('click', () => {
            this.toggleSidePanel();
        });
        
        this.panelClose.addEventListener('click', () => {
            this.closeSidePanel();
        });
        
        // Settings modal
        this.settingsBtn.addEventListener('click', () => {
            this.openSettings();
        });
        
        this.modalClose.addEventListener('click', () => {
            this.closeSettings();
        });
        
        // Click outside modal to close
        this.settingsModal.addEventListener('click', (e) => {
            if (e.target === this.settingsModal) {
                this.closeSettings();
            }
        });
        
        // Save settings
        document.getElementById('saveSettings').addEventListener('click', () => {
            this.saveSettings();
        });
        
        // Reset memory
        document.getElementById('resetMemory').addEventListener('click', () => {
            this.resetMemory();
        });
        
        // Dark mode toggle
        document.getElementById('darkMode').addEventListener('change', (e) => {
            this.toggleDarkMode(e.target.checked);
        });
    }
    
    async toggleVoiceMode(enabled) {
        this.voiceMode = enabled;
        
        try {
            if (enabled) {
                // Show voice UI
                this.textInputArea.style.display = 'none';
                this.voiceInputArea.style.display = 'flex';
                this.voiceVisualizer.style.display = 'block';
                
                // Initialize voice system
                if (this.useAdvancedVoice && this.advancedVoiceHandler) {
                    console.log('🎙️ Starting advanced voice mode...');
                    const success = await this.advancedVoiceHandler.toggleVoiceMode(true);
                    
                    if (success) {
                        this.friendStatusText.textContent = 'WebRTC voice channel active';
                        this.updateVoiceStatus('Voice connection established', 'streaming');
                        // Begin listening flow for advanced mode UI right away
                        this.advancedVoiceHandler.startListeningForSpeech();
                    } else {
                        throw new Error('Failed to start advanced voice');
                    }
                    
                } else if (this.legacyVoiceHandler) {
                    console.log('🎤 Starting legacy voice mode...');
                    this.legacyVoiceHandler.init();
                    this.friendStatusText.textContent = 'Voice mode active';
                    this.updateVoiceStatus('Press and speak', 'ready');
                } else {
                    throw new Error('No voice system available');
                }
                
            } else {
                // Hide voice UI
                this.textInputArea.style.display = 'flex';
                this.voiceInputArea.style.display = 'none';
                this.voiceVisualizer.style.display = 'none';
                
                // Stop voice system
                if (this.useAdvancedVoice && this.advancedVoiceHandler) {
                    await this.advancedVoiceHandler.toggleVoiceMode(false);
                }
                
                this.friendStatusText.textContent = 'Ready to chat';
            }
            
            // Save setting
            localStorage.setItem('voiceMode', enabled);
            
        } catch (error) {
            console.error('Error toggling voice mode:', error);
            
            // Fallback - disable voice mode
            this.voiceModeToggle.checked = false;
            this.voiceMode = false;
            this.textInputArea.style.display = 'flex';
            this.voiceInputArea.style.display = 'none';
            this.voiceVisualizer.style.display = 'none';
            
            this.showError('Failed to enable voice mode');
            this.friendStatusText.textContent = 'Voice mode error';
        }
    }
    
    async toggleWakeWordMode(enabled) {
        /* Toggle wake word detection mode - TEMPORARILY DISABLED */
        console.log('⚠️ Wake word mode is temporarily disabled. Use the button to activate voice mode.');
        this.showNotification('Wake word mode is temporarily disabled. Use the button.', 'info');
        return;
        
        /* COMMENTED CODE - RESTORE IF NEEDED
        try {
            console.log(`🔊 Wake word mode: ${enabled ? 'ON' : 'OFF'}`);
            
            if (!this.useAdvancedVoice || !this.advancedVoiceHandler) {
                console.warn('⚠️ Wake word requires advanced voice system');
                this.wakeWordModeToggle.checked = false;
                this.showNotification('Wake word requires advanced voice system', 'warning');
                return;
            }
            
            if (enabled) {
                // Request microphone permission first
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    stream.getTracks().forEach(track => track.stop()); // Just test permission
                    
                    console.log('✅ Microphone permission granted for wake word');
                } catch (error) {
                    console.error('❌ Microphone permission denied:', error);
                    this.wakeWordModeToggle.checked = false;
                    this.showNotification('Allow microphone access for wake word detection', 'error');
                    return;
                }
                
                // Enable wake word detection
                const success = await this.advancedVoiceHandler.enableWakeWord(true);
                
                if (success) {
                    console.log('✅ Wake word detection started');
                    this.updateWakeWordUI('listening');
                    this.showNotification('Wake word detection active. Say "Start"', 'success');
                } else {
                    console.error('❌ Failed to start wake word detection');
                    this.wakeWordModeToggle.checked = false;
                    this.showNotification('Failed to start wake word detection', 'error');
                }
                
            } else {
                // Disable wake word detection
                await this.advancedVoiceHandler.enableWakeWord(false);
                this.updateWakeWordUI('stopped');
                console.log('🔇 Wake word detection stopped');
            }
            
            // Save setting
            localStorage.setItem('wakeWordMode', enabled);
            
        } catch (error) {
            console.error('Error toggling wake word mode:', error);
            
            // Fallback - disable wake word mode
            this.wakeWordModeToggle.checked = false;
            this.updateWakeWordUI('error');
            this.showNotification('Wake word detection error', 'error');
        }
        */
    }
    
    updateWakeWordUI(state) {
        /* Update wake word UI visual state */
        const wakeWordToggle = document.querySelector('.wake-word-toggle');
        
        if (!wakeWordToggle) return;
        
        // Remove all state classes
        wakeWordToggle.classList.remove('active', 'error', 'listening', 'stopped');
        
        // Add current state class
        wakeWordToggle.classList.add(state);
        
        // Update friend status if wake word is active
        if (state === 'listening' && this.friendStatusText) {
            this.friendStatusText.textContent = 'Listening for "Start"...';
        }
        
        console.log(`🔊 Wake word UI updated: ${state}`);
    }
    
    updateVoiceStatus(message, state) {
        /* Update voice status display */
        const voiceStatus = document.getElementById('voiceStatus');
        if (voiceStatus) {
            voiceStatus.textContent = message;
            voiceStatus.className = `voice-status ${state}`;
        }
        
        // Update voice visualizer
        this.updateVoiceVisualizer(state);
    }
    
    updateVoiceVisualizer(state) {
        /* Update voice visualizer animation */
        const visualizer = document.getElementById('voiceVisualizer');
        const waveBars = visualizer?.querySelectorAll('.wave-bar');
        
        if (!waveBars) return;
        
        // Reset all animations
        waveBars.forEach(bar => {
            bar.style.animation = '';
        });
        
        // Apply state-specific animations
        switch (state) {
            case 'streaming':
                waveBars.forEach((bar, index) => {
                    bar.style.animation = `wave 1.2s ease-in-out infinite ${index * 0.1}s`;
                });
                break;
            case 'processing':
                waveBars.forEach((bar, index) => {
                    bar.style.animation = `wave 0.8s ease-in-out infinite ${index * 0.05}s`;
                });
                break;
            case 'ready':
                // Subtle idle animation
                waveBars.forEach((bar, index) => {
                    bar.style.animation = `wave 2s ease-in-out infinite ${index * 0.2}s`;
                });
                break;
        }
    }
    
    async sendMessage(text = null) {
        const message = text || this.messageInput.value.trim();
        if (!message) return;
        
        // Clear input
        if (!text) {
            this.messageInput.value = '';
            this.adjustTextareaHeight();
        }
        
        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Show typing indicator
        this.showTypingIndicator();
        
        // Send to backend
        try {
            const response = await this.sendToFriend(message);
            
            // Hide typing indicator
            this.hideTypingIndicator();
            
            // Add friend response
            this.addMessage(response.message, 'friend');
            
            // Update stats if provided
            if (response.stats) {
                this.updateStats(response.stats);
            }
            
            // Speak response if voice mode is enabled
            if (this.voiceMode && window.VoiceHandler) {
                window.VoiceHandler.speak(response.message);
            }
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            this.addMessage('Sorry, an error occurred while processing the message.', 'friend', true);
        }
        
        this.conversationCount++;
        this.updateConversationCount();
    }
    
    async sendToFriend(message) {
        const response = await fetch(`${this.API_BASE}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                voice_mode: this.voiceMode
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    addMessage(text, sender, isError = false) {
        const messageEl = document.createElement('div');
        messageEl.className = `message ${sender}-message`;
        
        if (isError) {
            messageEl.classList.add('error');
        }
        
        const avatarEl = document.createElement('div');
        avatarEl.className = 'message-avatar';
        avatarEl.innerHTML = sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        
        const contentEl = document.createElement('div');
        contentEl.className = 'message-content';
        
        const textEl = document.createElement('div');
        textEl.className = 'message-text';
        textEl.innerHTML = this.formatMessage(text);
        
        const timeEl = document.createElement('div');
        timeEl.className = 'message-time';
        timeEl.textContent = new Date().toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        contentEl.appendChild(textEl);
        contentEl.appendChild(timeEl);
        messageEl.appendChild(avatarEl);
        messageEl.appendChild(contentEl);
        
        this.chatMessages.appendChild(messageEl);
        this.scrollToBottom();
        
        // Animate message appearance
        setTimeout(() => {
            messageEl.style.opacity = '1';
            messageEl.style.transform = 'translateY(0)';
        }, 10);
    }
    
    formatMessage(text) {
        // Convert emojis (basic support) prior to markdown
        const emojiMap = {
            ':)': '😊',
            ':(': '😢',
            ':D': '😃',
            ';)': '😉',
            ':P': '😛',
            '<3': '❤️'
        };
        Object.keys(emojiMap).forEach(emoticon => {
            const regex = new RegExp(emoticon.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g');
            text = text.replace(regex, emojiMap[emoticon]);
        });

        // Prefer Markdown rendering with sanitization if libraries are available
        try {
            if (window.marked && window.DOMPurify) {
                // Configure marked
                marked.setOptions({
                    breaks: true,
                    gfm: true
                });
                // Custom renderer to force safe links opening in new tab
                const renderer = new marked.Renderer();
                renderer.link = function(href, title, text) {
                    const t = title ? ` title="${title}"` : '';
                    return `<a href="${href}" target="_blank" rel="noopener noreferrer"${t}>${text}</a>`;
                };
                const rawHtml = marked.parse(text, { renderer });
                const safeHtml = DOMPurify.sanitize(rawHtml, {
                    ALLOWED_ATTR: ['href','title','target','rel','class','id','src','alt','lang'],
                    // Allow common markdown tags
                    ALLOWED_TAGS: ['a','b','strong','i','em','p','br','ul','ol','li','code','pre','blockquote','hr','h1','h2','h3','h4','h5','h6','img','span']
                });
                return safeHtml;
            }
        } catch (e) {
            console.warn('Markdown rendering failed, falling back to plain formatting:', e);
        }

        // Fallback: linkify URLs and keep newlines
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        let html = text.replace(urlRegex, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');
        html = html.replace(/\n/g, '<br>');
        return html;
    }
    
    showTypingIndicator() {
        this.typingIndicator.style.display = 'block';
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        this.typingIndicator.style.display = 'none';
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }
    
    adjustTextareaHeight() {
        const textarea = this.messageInput;
        textarea.style.height = 'auto';
        const newHeight = Math.min(textarea.scrollHeight, 120);
        textarea.style.height = newHeight + 'px';
    }
    
    // Voice Recording
    startVoiceRecording() {
        // In advanced (WebRTC) mode, pressing the button should just (re)enter listening state
        if (this.useAdvancedVoice && this.advancedVoiceHandler) {
            this.isRecording = true;
            this.voiceBtn.classList.add('recording');
            this.voiceBtn.querySelector('.voice-btn-text').textContent = 'Listening...';
            this.showVoiceVisualizer();
            this.advancedVoiceHandler.startListeningForSpeech();
            return;
        }
        
        // Legacy fallback (Web Speech API)
        if (!window.VoiceHandler) {
            this.showError('Voice input is unavailable');
            return;
        }
        
        this.isRecording = true;
        this.voiceBtn.classList.add('recording');
        this.voiceBtn.querySelector('.voice-btn-text').textContent = 'Speak...';
        
        this.showVoiceVisualizer();
        
        window.VoiceHandler.startRecording()
            .then(() => {
                console.log('🎤 Recording started');
            })
            .catch(error => {
                console.error('Error starting recording:', error);
                this.showError('Failed to start recording');
                this.stopVoiceRecording();
            });
    }
    
    stopVoiceRecording() {
        // In advanced (WebRTC) mode, releasing the button should not invoke legacy flow
        if (this.useAdvancedVoice && this.advancedVoiceHandler) {
            if (!this.isRecording) return;
            this.isRecording = false;
            this.voiceBtn.classList.remove('recording');
            this.voiceBtn.querySelector('.voice-btn-text').textContent = 'Ready for voice input';
            this.hideVoiceVisualizer();
            return;
        }
        
        if (!window.VoiceHandler || !this.isRecording) return;
        
        this.isRecording = false;
        this.isProcessing = true;
        
        this.voiceBtn.classList.remove('recording');
        this.voiceBtn.classList.add('processing');
        this.voiceBtn.querySelector('.voice-btn-text').textContent = 'Processing...';
        
        window.VoiceHandler.stopRecording();
        
        // Wait for the recognition result
        if (window.VoiceHandler.recordingPromise) {
            window.VoiceHandler.recordingPromise.resolve = (text) => {
                console.log('🎤 Recording stopped, text:', text);
                this.isProcessing = false;
                this.voiceBtn.classList.remove('processing');
                this.voiceBtn.querySelector('.voice-btn-text').textContent = 'Press and speak';
                this.hideVoiceVisualizer();
                
                if (text && text.trim()) {
                    this.sendMessage(text);
                }
            };
            
            window.VoiceHandler.recordingPromise.reject = (error) => {
                console.error('Error stopping recording:', error);
                this.isProcessing = false;
                this.voiceBtn.classList.remove('processing');
                this.voiceBtn.querySelector('.voice-btn-text').textContent = 'Press and speak';
                this.hideVoiceVisualizer();
                this.showError('Voice processing error');
            };
        }
    }
    
    showVoiceVisualizer() {
        this.voiceVisualizer.style.display = 'block';
        this.voiceStatus.textContent = 'Listening...';
    }
    
    hideVoiceVisualizer() {
        this.voiceVisualizer.style.display = 'none';
    }
    
    // Side Panel
    toggleSidePanel() {
        if (this.sidePanel.classList.contains('open')) {
            this.closeSidePanel();
        } else {
            this.openSidePanel();
        }
    }
    
    openSidePanel() {
        this.sidePanel.classList.add('open');
        this.loadPanelData();
    }
    
    closeSidePanel() {
        this.sidePanel.classList.remove('open');
    }
    
    async loadPanelData() {
        try {
            // Load friend status
            const statusResponse = await fetch(`${this.API_BASE}/status`);
            const status = await statusResponse.json();
            
            this.updatePanelInfo(status);
            
        } catch (error) {
            console.error('Error loading panel data:', error);
        }
    }
    
    updatePanelInfo(data) {
        if (data.mood) {
            this.friendMood.textContent = data.mood;
        }
        
        if (data.memory_count !== undefined) {
            this.memoryCount = data.memory_count;
            this.memoryCountEl.textContent = this.memoryCount;
        }
        
        if (data.memories && data.memories.length > 0) {
            this.displayMemories(data.memories);
        }
        
        if (data.mood_history) {
            this.displayMoodHistory(data.mood_history);
        }
    }
    
    displayMemories(memories) {
        this.memoryList.innerHTML = '';
        
        if (memories.length === 0) {
            this.memoryList.innerHTML = '<p class="no-memory">No saved information yet</p>';
            return;
        }
        
        memories.forEach(memory => {
            const memoryEl = document.createElement('div');
            memoryEl.className = 'memory-item';
            memoryEl.innerHTML = `
                <div class="memory-text">${memory.content}</div>
                <div class="memory-meta">
                    <span class="memory-importance">Importance: ${memory.importance}/10</span>
                    <span class="memory-date">${new Date(memory.timestamp).toLocaleDateString('en-US')}</span>
                </div>
            `;
            this.memoryList.appendChild(memoryEl);
        });
    }
    
    displayMoodHistory(moodHistory) {
        // Simple text display for now, could be enhanced with charts
        this.moodChart.innerHTML = '';
        
        if (moodHistory.length === 0) {
            this.moodChart.innerHTML = '<p class="no-data">No mood data</p>';
            return;
        }
        
        const recent = moodHistory.slice(-5);
        recent.forEach(mood => {
            const moodEl = document.createElement('div');
            moodEl.className = 'mood-item';
            moodEl.innerHTML = `
                <span class="mood-emotion">${mood.emotion}</span>
                <span class="mood-date">${new Date(mood.timestamp).toLocaleDateString('en-US')}</span>
            `;
            this.moodChart.appendChild(moodEl);
        });
    }
    
    // Settings
    openSettings() {
        this.settingsModal.style.display = 'flex';
        this.loadCurrentSettings();
    }
    
    closeSettings() {
        this.settingsModal.style.display = 'none';
    }
    
    loadCurrentSettings() {
        const friendName = localStorage.getItem('friendName') || 'Anorix';
        const voiceLanguage = localStorage.getItem('voiceLanguage') || 'ru-RU';
        const speechRate = localStorage.getItem('speechRate') || '1';
        const darkMode = localStorage.getItem('darkMode') === 'true';
        
        document.getElementById('friendNameInput').value = friendName;
        document.getElementById('voiceSelect').value = voiceLanguage;
        document.getElementById('speechRate').value = speechRate;
        document.getElementById('darkMode').checked = darkMode;
    }
    
    saveSettings() {
        const friendName = document.getElementById('friendNameInput').value;
        const voiceLanguage = document.getElementById('voiceSelect').value;
        const speechRate = document.getElementById('speechRate').value;
        const darkMode = document.getElementById('darkMode').checked;
        
        // Save to localStorage
        localStorage.setItem('friendName', friendName);
        localStorage.setItem('voiceLanguage', voiceLanguage);
        localStorage.setItem('speechRate', speechRate);
        localStorage.setItem('darkMode', darkMode);
        
        // Apply settings
        document.querySelector('.friend-name').textContent = friendName;
        
        if (window.VoiceHandler) {
            window.VoiceHandler.setLanguage(voiceLanguage);
            window.VoiceHandler.setSpeechRate(parseFloat(speechRate));
        }
        
        this.toggleDarkMode(darkMode);
        
        this.closeSettings();
        this.showSuccess('Settings saved!');
    }
    
    async resetMemory() {
        if (!confirm('Are you sure you want to clear all friend memory? This action cannot be undone.')) {
            return;
        }
        
        try {
            const response = await fetch(`${this.API_BASE}/reset-memory`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.showSuccess('Memory cleared successfully!');
                this.memoryCount = 0;
                this.updateStats({ memory_count: 0 });
                this.loadPanelData();
            } else {
                throw new Error('Failed to reset memory');
            }
        } catch (error) {
            console.error('Error resetting memory:', error);
            this.showError('Error clearing memory');
        }
    }
    
    loadSettings() {
        // Load saved settings
        const voiceMode = localStorage.getItem('voiceMode') === 'true';
        const wakeWordMode = localStorage.getItem('wakeWordMode') === 'true';
        const darkMode = localStorage.getItem('darkMode') === 'true';
        const friendName = localStorage.getItem('friendName') || 'Anorix';
        
        this.voiceModeToggle.checked = voiceMode;
        this.toggleVoiceMode(voiceMode);
        
        // WAKE WORD TEMPORARILY DISABLED
        /*
        if (this.wakeWordModeToggle) {
            this.wakeWordModeToggle.checked = wakeWordMode;
            // Delay wake word activation to ensure advanced voice is ready
            setTimeout(() => {
                if (wakeWordMode && this.useAdvancedVoice) {
                    this.toggleWakeWordMode(wakeWordMode);
                }
            }, 1000);
        }
        */
        
        this.toggleDarkMode(darkMode);
        document.querySelector('.friend-name').textContent = friendName;
    }
    
    toggleDarkMode(enabled) {
        if (enabled) {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.documentElement.removeAttribute('data-theme');
        }
    }
    
    // Status Updates
    async checkFriendStatus() {
        try {
            const response = await fetch(`${this.API_BASE}/status`);
            if (response.ok) {
                const status = await response.json();
                this.updateFriendStatus(status);
            }
        } catch (error) {
            console.error('Error checking friend status:', error);
            this.updateFriendStatus({ online: false });
        }
    }
    
    updateFriendStatus(status) {
        if (status.online) {
            this.friendStatus.className = 'status-indicator online';
            this.friendStatusText.textContent = status.status_text || 'Ready to chat';
        } else {
            this.friendStatus.className = 'status-indicator offline';
            this.friendStatusText.textContent = 'Offline';
        }
    }
    
    updateStats(stats) {
        if (stats.conversation_count !== undefined) {
            this.conversationCount = stats.conversation_count;
        }
        
        if (stats.memory_count !== undefined) {
            this.memoryCount = stats.memory_count;
            this.memoryCountEl.textContent = this.memoryCount;
        }
        
        this.updateConversationCount();
    }
    
    updateConversationCount() {
        this.conversationCountEl.textContent = this.conversationCount;
    }
    
    // Utility methods
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Style the notification
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '1rem 1.5rem',
            borderRadius: '0.5rem',
            color: 'white',
            fontSize: '0.9rem',
            zIndex: '1000',
            opacity: '0',
            transform: 'translateY(-20px)',
            transition: 'all 0.3s ease'
        });
        
        // Set background color based on type
        const colors = {
            error: '#ef4444',
            success: '#10b981',
            info: '#6366f1'
        };
        notification.style.background = colors[type] || colors.info;
        
        // Add to DOM
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateY(0)';
        }, 10);
        
        // Remove after delay
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(-20px)';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
    
    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        try {
            // Show uploading state
            this.fileBtn.classList.add('uploading');
            this.fileBtn.innerHTML = '<i class="fas fa-spinner"></i>';
            
            // Check file size (10MB limit)
            const maxSize = 10 * 1024 * 1024;
            if (file.size > maxSize) {
                throw new Error('File is too large (max 10MB)');
            }
            
            // Show file upload message in chat
            this.addMessage('user', `📎 Uploaded file: ${file.name} (${this.formatFileSize(file.size)})`);
            
            // For text files, we can read content directly
            if (this.isTextFile(file)) {
                const content = await this.readFileAsText(file);
                const message = `Read the contents of the file "${file.name}":\n\n${content}`;
                this.sendMessage(message);
            } else {
                // For other files, ask the agent to read them via file path
                // We need to upload the file to server first
                await this.uploadFileToServer(file);
                const message = `Read file: ${file.name}`;
                this.sendMessage(message);
            }
            
        } catch (error) {
            console.error('File upload error:', error);
            this.addMessage('system', `❌ File upload error: ${error.message}`);
        } finally {
            // Reset button state
            this.fileBtn.classList.remove('uploading');
            this.fileBtn.innerHTML = '<i class="fas fa-paperclip"></i>';
            
            // Clear file input
            this.fileInput.value = '';
        }
    }
    
    isTextFile(file) {
        const textTypes = [
            'text/plain', 'text/markdown', 'text/csv', 'text/html', 'text/css', 'text/javascript',
            'application/json', 'application/xml', 'text/xml'
        ];
        const textExtensions = ['.txt', '.md', '.py', '.js', '.css', '.html', '.json', '.xml', '.csv'];
        
        return textTypes.includes(file.type) || 
               textExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
    }
    
    readFileAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = reject;
            reader.readAsText(file);
        });
    }
    
    async uploadFileToServer(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${this.API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Server upload error: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.friendApp = new LocalFriendApp();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && window.friendApp) {
        window.friendApp.checkFriendStatus();
    }
});