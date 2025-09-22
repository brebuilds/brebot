# Brebot Voice Communication Guide

This guide covers Brebot's realtime voice communication capabilities, including voice input/output, bot voice assignment, and integration with the existing chat/task system.

## 🎤 **Voice Features Overview**

### **Core Capabilities**
- **Push-to-Talk**: Global keyboard shortcut (Cmd+Shift+B / Ctrl+Shift+B)
- **Live Transcription**: Real-time speech-to-text using OpenAI Whisper
- **Voice Responses**: Text-to-speech with bot-specific voices
- **Bot Voice Assignment**: Each bot can have its own voice personality
- **Command Processing**: Voice commands create tasks, add to memory, etc.
- **Integration**: Seamless integration with existing chat and task systems

## 🚀 **Getting Started**

### **1. Enable Voice Features**
The voice widget is automatically loaded with the dashboard. Press **Cmd+Shift+B** (Mac) or **Ctrl+Shift+B** (Windows/Linux) to open the voice widget.

### **2. First-Time Setup**
1. **Grant Microphone Permission**: Browser will prompt for microphone access
2. **Configure OpenAI API**: Ensure your OpenAI API key is set in settings
3. **Test Connection**: The widget will show connection status

### **3. Basic Usage**
1. **Open Voice Widget**: Use keyboard shortcut or click the mic button
2. **Start Speaking**: Click and hold the mic button or use push-to-talk
3. **Get Responses**: Brebot will respond with both text and voice
4. **View Transcripts**: All conversations are logged in the chat system

## 🎯 **Voice Commands**

### **Task Management**
- *"Create a task to review the quarterly report"*
- *"Add a task for tomorrow to call the client"*
- *"Assign the marketing task to Glen-o-matic"*

### **Memory Management**
- *"Remember that the client prefers morning meetings"*
- *"Add to memory that the project deadline is next Friday"*
- *"Save this information: the new API endpoint is ready"*

### **General Conversation**
- *"What's the status of the current projects?"*
- *"Who's available to help with the design work?"*
- *"Show me the latest updates"*

### **System Commands**
- *"Start a meeting"*
- *"Open the file manager"*
- *"Show me the bot status"*

## 🤖 **Bot Voice Configuration**

### **Voice Providers**

#### **OpenAI Voices**
- **Alloy**: Neutral, professional
- **Echo**: Warm, friendly
- **Fable**: Energetic, enthusiastic
- **Onyx**: Deep, authoritative
- **Nova**: Clear, articulate
- **Shimmer**: Soft, gentle

#### **ElevenLabs Voices**
- **Rachel**: Professional, clear
- **Domi**: Confident, strong
- **Bella**: Warm, approachable
- **Antoni**: Smooth, sophisticated
- **Elli**: Young, energetic
- **Josh**: Casual, friendly
- **Arnold**: Deep, commanding
- **Adam**: Neutral, reliable
- **Sam**: Cheerful, upbeat

### **Voice Settings**
- **Speed**: 0.5x to 2.0x (default: 1.0x)
- **Pitch**: 0.5x to 2.0x (default: 1.0x)
- **Provider**: OpenAI or ElevenLabs

### **Configuring Bot Voices**

#### **During Bot Creation**
1. Open the "Create Bot" modal
2. Fill in bot details
3. In the "Voice Configuration" section:
   - Select voice provider
   - Choose voice ID
   - Adjust speed and pitch
4. Create the bot

#### **For Existing Bots**
```javascript
// Configure voice via API
fetch('/api/voice/configure?bot_id=my-bot', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        provider: 'openai',
        voice_id: 'nova',
        speed: 1.2,
        pitch: 1.0
    })
});
```

## 🎛️ **Voice Widget Interface**

### **Widget Controls**
- **Microphone Button**: Click to start/stop recording
- **Mute Button**: Toggle audio output
- **Close Button**: Hide the widget
- **Voice Mode Toggle**: Enable/disable voice responses

### **Status Indicators**
- **Ready**: Green dot - Ready to listen
- **Listening**: Orange pulsing dot - Recording audio
- **Speaking**: Blue pulsing dot - Playing response
- **Processing**: Yellow dot - Analyzing speech
- **Error**: Red dot - Connection or permission issue

### **Display Areas**
- **Your Speech**: Shows live transcription
- **Brebot Response**: Shows text response
- **Audio Visualizer**: Waveform display during recording/playback

## 🔧 **Technical Implementation**

### **Architecture**
```
Frontend (Voice Widget) 
    ↓ WebSocket
Backend (Voice Service)
    ↓ OpenAI Realtime API
OpenAI GPT-4o Realtime
    ↓ Tool Calls
Brebot Backend (Tasks/Memory)
```

### **WebSocket Endpoints**
- **`/ws/voice`**: Main voice communication endpoint
- **`/ws`**: General WebSocket for other features

### **API Endpoints**
- **`POST /api/voice/configure`**: Configure bot voice settings
- **`GET /api/voice/config/{bot_id}`**: Get bot voice configuration
- **`POST /api/voice/process`**: Process voice commands

### **Voice Service Features**
- **Real-time Audio Streaming**: Low-latency audio processing
- **Automatic Transcription**: OpenAI Whisper integration
- **Tool Call Processing**: Convert voice to actions
- **Multi-bot Support**: Different voices per bot
- **Error Handling**: Robust error recovery

## 📝 **System Prompt**

The voice system uses this specialized prompt:

```
You are Brebot, my AI office assistant.
- If the user is brainstorming, capture text as a note or sticky note.
- If the user gives a command (e.g. "create a task", "assign to [bot]", "add to memory", "start meeting"), create the correct object and send it to the backend.
- If the user asks a direct question, answer conversationally in voice and show text in the chat log.
- Always confirm actions out loud (e.g. "Task assigned to Glen-o-matic.").
- Route voice responses based on the bot's assigned voice property if available.
- End with a short follow-up ("Want me to add that to the calendar?").
```

## 🔄 **Event Flow**

### **Voice Input Flow**
1. **User presses shortcut** → Voice widget opens
2. **User clicks mic** → Audio recording starts
3. **Audio streams** → WebSocket to backend
4. **Backend processes** → OpenAI Realtime API
5. **Transcription** → Live text display
6. **Command parsing** → Tool calls or conversation
7. **Response generation** → Text and audio response

### **Voice Output Flow**
1. **Response generated** → Text response
2. **Voice synthesis** → OpenAI or ElevenLabs TTS
3. **Audio streaming** → WebSocket to frontend
4. **Audio playback** → Browser audio system
5. **Chat logging** → Response saved to chat history

## 🛠️ **Configuration**

### **Environment Variables**
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# ElevenLabs Configuration (optional)
ELEVENLABS_API_KEY=your_elevenlabs_api_key

# Voice Settings
VOICE_DEFAULT_PROVIDER=openai
VOICE_DEFAULT_VOICE_ID=alloy
VOICE_DEFAULT_SPEED=1.0
VOICE_DEFAULT_PITCH=1.0
```

### **Browser Requirements**
- **Microphone Access**: Required for voice input
- **WebSocket Support**: For real-time communication
- **Audio Playback**: For voice responses
- **Modern Browser**: Chrome, Firefox, Safari, Edge

### **Network Requirements**
- **WebSocket Connection**: For real-time communication
- **HTTPS**: Required for microphone access in production
- **OpenAI API Access**: For transcription and responses

## 🎨 **Customization**

### **Voice Widget Styling**
The voice widget uses CSS custom properties for easy theming:

```css
.voice-widget {
    --voice-primary: #3b82f6;
    --voice-success: #10b981;
    --voice-warning: #f59e0b;
    --voice-error: #ef4444;
    --voice-bg: rgba(255, 255, 255, 0.95);
    --voice-border: rgba(255, 255, 255, 0.2);
}
```

### **Keyboard Shortcuts**
Customize the global shortcut by modifying the voice widget:

```javascript
// Change from Cmd+Shift+B to Cmd+Shift+V
document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'V') {
        e.preventDefault();
        window.voiceWidget.toggle();
    }
});
```

### **Voice Commands**
Add custom voice commands by extending the voice service:

```python
# In voice_service.py
async def process_voice_command(self, command: str, bot_id: str = "brebot"):
    # Add your custom command processing
    if "custom command" in command.lower():
        return {
            "action": "custom_action",
            "parameters": {"data": "custom_data"}
        }
    # ... existing processing
```

## 🔍 **Troubleshooting**

### **Common Issues**

#### **Microphone Not Working**
1. **Check Permissions**: Ensure browser has microphone access
2. **Test Microphone**: Use browser's microphone test
3. **Check Hardware**: Verify microphone is working
4. **Browser Compatibility**: Try different browser

#### **No Voice Response**
1. **Check Audio Output**: Ensure speakers/headphones work
2. **Check Mute Status**: Verify widget is not muted
3. **Check Connection**: Ensure WebSocket connection is active
4. **Check API Keys**: Verify OpenAI API key is valid

#### **Poor Transcription Quality**
1. **Speak Clearly**: Enunciate words clearly
2. **Reduce Background Noise**: Use quiet environment
3. **Check Microphone Quality**: Use good quality microphone
4. **Adjust Distance**: Speak 6-12 inches from microphone

#### **Connection Issues**
1. **Check Network**: Ensure stable internet connection
2. **Check Firewall**: Allow WebSocket connections
3. **Check Server**: Verify backend is running
4. **Check API Limits**: Ensure OpenAI API limits not exceeded

### **Debug Mode**
Enable debug logging in the browser console:

```javascript
// Enable voice widget debug mode
window.voiceWidget.debug = true;

// Check connection status
console.log('Voice widget connected:', window.voiceWidget.isConnected);

// Check microphone status
console.log('Microphone available:', window.voiceWidget.audioStream !== null);
```

## 📊 **Performance Optimization**

### **Audio Quality Settings**
- **Sample Rate**: 16kHz (optimal for speech)
- **Bit Depth**: 16-bit (sufficient for voice)
- **Channels**: Mono (reduces bandwidth)
- **Codec**: Opus (efficient compression)

### **Latency Optimization**
- **Chunk Size**: 100ms audio chunks
- **Buffer Size**: Minimal buffering
- **Connection**: WebSocket for low latency
- **Processing**: Stream processing for real-time

### **Resource Management**
- **Memory**: Automatic cleanup of audio buffers
- **CPU**: Efficient audio processing
- **Network**: Compressed audio streams
- **Storage**: Minimal local storage usage

## 🔒 **Security & Privacy**

### **Data Handling**
- **Audio Processing**: Real-time, not stored locally
- **Transcriptions**: Logged for chat history
- **API Calls**: Secure HTTPS connections
- **Voice Data**: Not permanently stored

### **Privacy Considerations**
- **Microphone Access**: Only when widget is active
- **Audio Streaming**: Encrypted WebSocket connections
- **API Usage**: OpenAI's privacy policies apply
- **Local Storage**: Minimal, temporary data only

### **Access Control**
- **Authentication**: Integrate with existing auth system
- **Authorization**: Role-based voice access
- **Audit Logging**: Track voice interactions
- **Data Retention**: Configurable retention policies

## 🚀 **Advanced Features**

### **Multi-Language Support**
```python
# Configure language in voice service
session = await self.openai_client.beta.realtime.sessions.create(
    model="gpt-4o-realtime-preview-2024-12-17",
    voice="alloy",
    instructions=self.system_prompt,
    input_audio_transcription={
        "model": "whisper-1",
        "language": "en"  # or "es", "fr", "de", etc.
    }
)
```

### **Custom Voice Models**
```python
# Use custom ElevenLabs voice
voice_config = VoiceConfig(
    provider="elevenlabs",
    voice_id="custom_voice_id",
    speed=1.0,
    pitch=1.0
)
```

### **Voice Cloning**
```python
# Clone user's voice for personalized responses
voice_config = VoiceConfig(
    provider="elevenlabs",
    voice_id="cloned_voice_id",
    speed=1.0,
    pitch=1.0
)
```

## 📚 **API Reference**

### **Voice Service Methods**
```python
# Configure bot voice
voice_service.set_bot_voice(bot_id, voice_config)

# Get bot voice configuration
config = voice_service.get_bot_voice(bot_id)

# Process voice command
result = await voice_service.process_voice_command(command, bot_id)

# Start realtime session
await voice_service.start_realtime_session(session_id, websocket)
```

### **Voice Widget Methods**
```javascript
// Show/hide widget
window.voiceWidget.show();
window.voiceWidget.hide();
window.voiceWidget.toggle();

// Control recording
window.voiceWidget.startListening();
window.voiceWidget.stopListening();

// Control audio
window.voiceWidget.toggleMute();
window.voiceWidget.setVoiceMode(enabled);
```

## 🎉 **What This Enables**

Your Brebot system now has **true voice interaction capabilities**! Users can:

- **Talk to Brebot naturally** using voice commands
- **Get spoken responses** with bot-specific voices
- **Create tasks and manage memory** through voice
- **Have conversations** that feel natural and intuitive
- **Use push-to-talk** for hands-free operation
- **Integrate voice** with existing workflows

This transforms Brebot from a text-based system into a **conversational AI assistant** that can interact naturally through voice while maintaining all the powerful automation and management capabilities you've built.

---

**Ready to start talking to Brebot?** Press **Cmd+Shift+B** (Mac) or **Ctrl+Shift+B** (Windows/Linux) to open the voice widget and start your first voice conversation!
