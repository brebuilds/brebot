/**
 * Voice Widget for Brebot
 * Handles realtime voice communication with OpenAI Realtime API
 */

class VoiceWidget {
    constructor() {
        this.isVisible = false;
        this.isListening = false;
        this.isConnected = false;
        this.websocket = null;
        this.mediaRecorder = null;
        this.audioStream = null;
        this.sessionId = null;
        this.audioContext = null;
        this.audioQueue = [];
        this.isPlaying = false;
        
        this.createWidget();
        this.setupKeyboardShortcut();
        this.setupEventListeners();
    }
    
    createWidget() {
        // Create the floating widget
        this.widget = document.createElement('div');
        this.widget.id = 'voice-widget';
        this.widget.className = 'voice-widget hidden';
        this.widget.innerHTML = `
            <div class="voice-widget-header">
                <div class="voice-widget-title">
                    <i class="fas fa-microphone"></i>
                    Brebot Voice
                </div>
                <div class="voice-widget-controls">
                    <button id="voice-mute-btn" class="voice-btn" title="Mute/Unmute">
                        <i class="fas fa-volume-up"></i>
                    </button>
                    <button id="voice-close-btn" class="voice-btn" title="Close">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
            
            <div class="voice-widget-content">
                <div class="voice-status">
                    <div id="voice-status-indicator" class="status-indicator">
                        <div class="status-dot"></div>
                        <span id="voice-status-text">Ready</span>
                    </div>
                </div>
                
                <div class="voice-transcript">
                    <div class="transcript-label">Your Speech:</div>
                    <div id="voice-user-transcript" class="transcript-text"></div>
                </div>
                
                <div class="voice-response">
                    <div class="response-label">Brebot:</div>
                    <div id="voice-bot-response" class="response-text"></div>
                </div>
                
                <div class="voice-audio-visualizer">
                    <canvas id="voice-waveform" width="200" height="40"></canvas>
                </div>
                
                <div class="voice-controls">
                    <button id="voice-mic-btn" class="voice-mic-btn">
                        <i class="fas fa-microphone"></i>
                    </button>
                    <div class="voice-mode-toggle">
                        <label>
                            <input type="checkbox" id="voice-mode-toggle" checked>
                            <span class="toggle-slider"></span>
                            Voice Mode
                        </label>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(this.widget);
        
        // Add CSS styles
        this.addStyles();
    }
    
    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .voice-widget {
                position: fixed;
                top: 20px;
                right: 20px;
                width: 350px;
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 16px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                z-index: 10000;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                transition: all 0.3s ease;
            }
            
            .voice-widget.hidden {
                opacity: 0;
                transform: translateY(-20px);
                pointer-events: none;
            }
            
            .voice-widget-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 16px 20px;
                border-bottom: 1px solid rgba(0, 0, 0, 0.1);
            }
            
            .voice-widget-title {
                display: flex;
                align-items: center;
                font-weight: 600;
                color: #1f2937;
            }
            
            .voice-widget-title i {
                margin-right: 8px;
                color: #3b82f6;
            }
            
            .voice-widget-controls {
                display: flex;
                gap: 8px;
            }
            
            .voice-btn {
                width: 32px;
                height: 32px;
                border: none;
                background: rgba(0, 0, 0, 0.05);
                border-radius: 8px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s ease;
            }
            
            .voice-btn:hover {
                background: rgba(0, 0, 0, 0.1);
            }
            
            .voice-widget-content {
                padding: 20px;
            }
            
            .voice-status {
                margin-bottom: 16px;
            }
            
            .status-indicator {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .status-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #10b981;
                animation: pulse 2s infinite;
            }
            
            .status-dot.listening {
                background: #f59e0b;
                animation: pulse-fast 0.5s infinite;
            }
            
            .status-dot.speaking {
                background: #3b82f6;
                animation: pulse-fast 0.3s infinite;
            }
            
            .status-dot.error {
                background: #ef4444;
                animation: none;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            
            @keyframes pulse-fast {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.3; }
            }
            
            .voice-transcript, .voice-response {
                margin-bottom: 16px;
            }
            
            .transcript-label, .response-label {
                font-size: 12px;
                font-weight: 600;
                color: #6b7280;
                margin-bottom: 4px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .transcript-text, .response-text {
                min-height: 20px;
                padding: 8px 12px;
                background: rgba(0, 0, 0, 0.05);
                border-radius: 8px;
                font-size: 14px;
                line-height: 1.4;
                color: #374151;
            }
            
            .voice-audio-visualizer {
                margin-bottom: 16px;
                text-align: center;
            }
            
            #voice-waveform {
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 8px;
                background: rgba(0, 0, 0, 0.02);
            }
            
            .voice-controls {
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            
            .voice-mic-btn {
                width: 60px;
                height: 60px;
                border: none;
                background: linear-gradient(135deg, #3b82f6, #1d4ed8);
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 24px;
                transition: all 0.3s ease;
                box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
            }
            
            .voice-mic-btn:hover {
                transform: scale(1.05);
                box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
            }
            
            .voice-mic-btn.listening {
                background: linear-gradient(135deg, #ef4444, #dc2626);
                animation: pulse-mic 1s infinite;
            }
            
            @keyframes pulse-mic {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.1); }
            }
            
            .voice-mode-toggle {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 14px;
                color: #6b7280;
            }
            
            .voice-mode-toggle input[type="checkbox"] {
                display: none;
            }
            
            .toggle-slider {
                width: 40px;
                height: 20px;
                background: #d1d5db;
                border-radius: 20px;
                position: relative;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .toggle-slider::before {
                content: '';
                position: absolute;
                width: 16px;
                height: 16px;
                background: white;
                border-radius: 50%;
                top: 2px;
                left: 2px;
                transition: all 0.3s ease;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            }
            
            .voice-mode-toggle input[type="checkbox"]:checked + .toggle-slider {
                background: #3b82f6;
            }
            
            .voice-mode-toggle input[type="checkbox"]:checked + .toggle-slider::before {
                transform: translateX(20px);
            }
            
            /* Dark mode support */
            @media (prefers-color-scheme: dark) {
                .voice-widget {
                    background: rgba(31, 41, 55, 0.95);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }
                
                .voice-widget-title {
                    color: #f9fafb;
                }
                
                .transcript-text, .response-text {
                    background: rgba(255, 255, 255, 0.05);
                    color: #e5e7eb;
                }
                
                .transcript-label, .response-label {
                    color: #9ca3af;
                }
                
                .voice-mode-toggle {
                    color: #9ca3af;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    setupKeyboardShortcut() {
        document.addEventListener('keydown', (e) => {
            // Cmd+Shift+B on Mac, Ctrl+Shift+B on Windows/Linux
            if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'B') {
                e.preventDefault();
                this.toggle();
            }
        });
    }
    
    setupEventListeners() {
        // Mic button
        document.getElementById('voice-mic-btn').addEventListener('click', () => {
            this.toggleListening();
        });
        
        // Close button
        document.getElementById('voice-close-btn').addEventListener('click', () => {
            this.hide();
        });
        
        // Mute button
        document.getElementById('voice-mute-btn').addEventListener('click', () => {
            this.toggleMute();
        });
        
        // Voice mode toggle
        document.getElementById('voice-mode-toggle').addEventListener('change', (e) => {
            this.setVoiceMode(e.target.checked);
        });
    }
    
    show() {
        this.widget.classList.remove('hidden');
        this.isVisible = true;
        this.connect();
    }
    
    hide() {
        this.widget.classList.add('hidden');
        this.isVisible = false;
        this.disconnect();
    }
    
    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }
    
    async connect() {
        if (this.isConnected) return;
        
        try {
            this.updateStatus('Connecting...', 'connecting');
            
            // Connect to WebSocket
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/voice`;
            
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                this.isConnected = true;
                this.updateStatus('Connected', 'connected');
                this.initializeAudio();
            };
            
            this.websocket.onmessage = (event) => {
                this.handleWebSocketMessage(JSON.parse(event.data));
            };
            
            this.websocket.onclose = () => {
                this.isConnected = false;
                this.updateStatus('Disconnected', 'error');
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateStatus('Connection Error', 'error');
            };
            
        } catch (error) {
            console.error('Error connecting to voice service:', error);
            this.updateStatus('Connection Failed', 'error');
        }
    }
    
    disconnect() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
        
        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
            this.audioStream = null;
        }
        
        if (this.mediaRecorder) {
            this.mediaRecorder.stop();
            this.mediaRecorder = null;
        }
        
        this.isConnected = false;
        this.isListening = false;
        this.updateStatus('Disconnected', 'error');
    }
    
    async initializeAudio() {
        try {
            this.audioStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });
            
            this.mediaRecorder = new MediaRecorder(this.audioStream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0 && this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                    const reader = new FileReader();
                    reader.onload = () => {
                        const base64Audio = btoa(String.fromCharCode(...new Uint8Array(reader.result)));
                        this.websocket.send(JSON.stringify({
                            type: 'audio_input',
                            audio: base64Audio
                        }));
                    };
                    reader.readAsArrayBuffer(event.data);
                }
            };
            
            this.updateStatus('Ready', 'ready');
            
        } catch (error) {
            console.error('Error initializing audio:', error);
            this.updateStatus('Microphone Access Denied', 'error');
        }
    }
    
    toggleListening() {
        if (!this.isConnected || !this.mediaRecorder) return;
        
        if (this.isListening) {
            this.stopListening();
        } else {
            this.startListening();
        }
    }
    
    startListening() {
        if (this.isListening) return;
        
        this.isListening = true;
        this.mediaRecorder.start(100); // Send data every 100ms
        
        document.getElementById('voice-mic-btn').classList.add('listening');
        this.updateStatus('Listening...', 'listening');
        
        // Send start listening message
        if (this.websocket) {
            this.websocket.send(JSON.stringify({
                type: 'start_listening'
            }));
        }
    }
    
    stopListening() {
        if (!this.isListening) return;
        
        this.isListening = false;
        this.mediaRecorder.stop();
        
        document.getElementById('voice-mic-btn').classList.remove('listening');
        this.updateStatus('Processing...', 'processing');
        
        // Send stop listening message
        if (this.websocket) {
            this.websocket.send(JSON.stringify({
                type: 'stop_listening'
            }));
        }
    }
    
    toggleMute() {
        const muteBtn = document.getElementById('voice-mute-btn');
        const icon = muteBtn.querySelector('i');
        
        if (icon.classList.contains('fa-volume-up')) {
            icon.classList.remove('fa-volume-up');
            icon.classList.add('fa-volume-mute');
            this.isMuted = true;
        } else {
            icon.classList.remove('fa-volume-mute');
            icon.classList.add('fa-volume-up');
            this.isMuted = false;
        }
    }
    
    setVoiceMode(enabled) {
        this.voiceMode = enabled;
        // Update UI or behavior based on voice mode
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'session_created':
                this.sessionId = data.session_id;
                break;
                
            case 'transcript':
                this.updateUserTranscript(data.text);
                break;
                
            case 'text_output':
                this.updateBotResponse(data.text, false);
                break;
                
            case 'text_complete':
                this.updateBotResponse(data.text, true);
                break;
                
            case 'audio_output':
                if (!this.isMuted) {
                    this.playAudio(data.audio);
                }
                break;
                
            case 'tool_call':
                this.handleToolCall(data.tool_call);
                break;
                
            case 'error':
                this.updateStatus('Error: ' + data.message, 'error');
                break;
        }
    }
    
    updateStatus(text, status) {
        document.getElementById('voice-status-text').textContent = text;
        const statusDot = document.querySelector('.status-dot');
        statusDot.className = `status-dot ${status}`;
    }
    
    updateUserTranscript(text) {
        const transcriptEl = document.getElementById('voice-user-transcript');
        transcriptEl.textContent = text;
    }
    
    updateBotResponse(text, isComplete) {
        const responseEl = document.getElementById('voice-bot-response');
        
        if (isComplete) {
            responseEl.textContent = text;
            this.updateStatus('Ready', 'ready');
        } else {
            responseEl.textContent = text;
            this.updateStatus('Speaking...', 'speaking');
        }
    }
    
    async playAudio(base64Audio) {
        try {
            const audioData = atob(base64Audio);
            const audioBuffer = new Uint8Array(audioData.length);
            for (let i = 0; i < audioData.length; i++) {
                audioBuffer[i] = audioData.charCodeAt(i);
            }
            
            const blob = new Blob([audioBuffer], { type: 'audio/wav' });
            const audioUrl = URL.createObjectURL(blob);
            
            const audio = new Audio(audioUrl);
            audio.onended = () => {
                URL.revokeObjectURL(audioUrl);
                this.isPlaying = false;
            };
            
            this.isPlaying = true;
            await audio.play();
            
        } catch (error) {
            console.error('Error playing audio:', error);
        }
    }
    
    handleToolCall(toolCall) {
        // Handle tool calls from the voice system
        console.log('Tool call:', toolCall);
        
        // You can integrate this with your existing task/memory system
        if (toolCall.name === 'create_task') {
            // Create task in your system
            this.showNotification('Task created: ' + toolCall.parameters.title);
        } else if (toolCall.name === 'add_to_memory') {
            // Add to memory system
            this.showNotification('Added to memory: ' + toolCall.parameters.content);
        }
    }
    
    showNotification(message) {
        // Show a notification (you can integrate with your existing notification system)
        console.log('Notification:', message);
    }
    
    drawWaveform() {
        const canvas = document.getElementById('voice-waveform');
        const ctx = canvas.getContext('2d');
        
        // Simple waveform visualization
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        if (this.isListening || this.isPlaying) {
            ctx.fillStyle = '#3b82f6';
            const bars = 20;
            const barWidth = canvas.width / bars;
            
            for (let i = 0; i < bars; i++) {
                const height = Math.random() * canvas.height * 0.8;
                ctx.fillRect(i * barWidth, canvas.height - height, barWidth - 2, height);
            }
        }
        
        requestAnimationFrame(() => this.drawWaveform());
    }
}

// Initialize the voice widget when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.voiceWidget = new VoiceWidget();
    
    // Start waveform animation
    if (window.voiceWidget) {
        window.voiceWidget.drawWaveform();
    }
});
