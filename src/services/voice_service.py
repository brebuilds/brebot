"""
Voice Communication Service for Brebot.
Handles realtime voice input/output with OpenAI Realtime API and ElevenLabs.
"""

import asyncio
import json
import base64
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import websockets
import openai
from openai import AsyncOpenAI
import requests
from pydantic import BaseModel

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config.settings import settings
from config.system_prompts import get_voice_prompt
from utils.logger import brebot_logger


class VoiceConfig(BaseModel):
    """Voice configuration for bots."""
    provider: str = "openai"  # "openai" or "elevenlabs"
    voice_id: str = "alloy"  # OpenAI voice or ElevenLabs voice ID
    speed: float = 1.0
    pitch: float = 1.0


class VoiceEvent(BaseModel):
    """Voice event model."""
    type: str  # "voice_command", "voice_reply", "voice_transcript"
    transcript: Optional[str] = None
    text: Optional[str] = None
    audio_url: Optional[str] = None
    bot_id: Optional[str] = None
    action: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.now()


class VoiceService:
    """Service for handling voice communication."""
    
    def __init__(self):
        """Initialize the voice service."""
        self.openai_api_key = getattr(settings, 'openai_api_key', None)
        self.openai_client = AsyncOpenAI(api_key=self.openai_api_key) if self.openai_api_key else None
        self.elevenlabs_api_key = getattr(settings, 'elevenlabs_api_key', None)
        self.active_connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.voice_configs: Dict[str, VoiceConfig] = {}
        self.event_handlers: List[Callable[[VoiceEvent], None]] = []
        
        # System prompt for voice mode
        self.system_prompt = get_voice_prompt()
        
        brebot_logger.log_agent_action(
            agent_name="VoiceService",
            action="initialized",
            details={"openai_configured": bool(settings.openai_api_key)}
        )
    
    def add_event_handler(self, handler: Callable[[VoiceEvent], None]):
        """Add an event handler for voice events."""
        self.event_handlers.append(handler)
    
    def remove_event_handler(self, handler: Callable[[VoiceEvent], None]):
        """Remove an event handler."""
        if handler in self.event_handlers:
            self.event_handlers.remove(handler)
    
    def _emit_event(self, event: VoiceEvent):
        """Emit a voice event to all handlers."""
        for handler in self.event_handlers:
            try:
                handler(event)
            except Exception as e:
                logging.error(f"Error in voice event handler: {e}")
    
    def set_bot_voice(self, bot_id: str, voice_config: VoiceConfig):
        """Set voice configuration for a bot."""
        self.voice_configs[bot_id] = voice_config
        brebot_logger.log_agent_action(
            agent_name="VoiceService",
            action="bot_voice_configured",
            details={"bot_id": bot_id, "provider": voice_config.provider, "voice_id": voice_config.voice_id}
        )
    
    def get_bot_voice(self, bot_id: str) -> VoiceConfig:
        """Get voice configuration for a bot."""
        return self.voice_configs.get(bot_id, VoiceConfig())
    
    async def start_realtime_session(self, session_id: str, websocket: websockets.WebSocketServerProtocol):
        """Start a realtime voice session."""
        self.active_connections[session_id] = websocket
        
        if not self.openai_client:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
            }))
            return
        
        try:
            # Create OpenAI Realtime API session
            session = await self.openai_client.beta.realtime.sessions.create(
                model="gpt-4o-realtime-preview-2024-12-17",
                voice="alloy",
                instructions=self.system_prompt,
                input_audio_format="pcm16",
                output_audio_format="pcm16",
                input_audio_transcription={
                    "model": "whisper-1"
                },
                turn_detection={
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                },
                tools=[{
                    "type": "function",
                    "name": "create_task",
                    "description": "Create a new task",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "bot_id": {"type": "string"}
                        },
                        "required": ["title"]
                    }
                }, {
                    "type": "function",
                    "name": "add_to_memory",
                    "description": "Add information to memory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "category": {"type": "string"}
                        },
                        "required": ["content"]
                    }
                }, {
                    "type": "function",
                    "name": "assign_to_bot",
                    "description": "Assign a task to a specific bot",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "string"},
                            "bot_id": {"type": "string"}
                        },
                        "required": ["task_id", "bot_id"]
                    }
                }]
            )
            
            # Send session info to client
            await websocket.send(json.dumps({
                "type": "session_created",
                "session_id": session.id,
                "expires_at": session.expires_at
            }))
            
            # Handle realtime communication
            await self._handle_realtime_communication(session_id, session, websocket)
            
        except Exception as e:
            logging.error(f"Error in realtime session {session_id}: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": str(e)
            }))
        finally:
            if session_id in self.active_connections:
                del self.active_connections[session_id]
    
    async def _handle_realtime_communication(self, session_id: str, session, websocket: websockets.WebSocketServerProtocol):
        """Handle realtime communication with OpenAI."""
        try:
            # Connect to OpenAI Realtime API
            async with self.openai_client.beta.realtime.sessions.connect(session.id) as stream:
                
                # Handle messages from client
                async def handle_client_message():
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            
                            if data["type"] == "audio_input":
                                # Forward audio to OpenAI
                                audio_data = base64.b64decode(data["audio"])
                                await stream.send({
                                    "type": "input_audio_buffer.append",
                                    "audio": audio_data
                                })
                            
                            elif data["type"] == "start_listening":
                                await stream.send({"type": "conversation.item.create"})
                                await stream.send({"type": "input_audio_buffer.commit"})
                            
                            elif data["type"] == "stop_listening":
                                await stream.send({"type": "input_audio_buffer.commit"})
                            
                        except Exception as e:
                            logging.error(f"Error handling client message: {e}")
                
                # Handle messages from OpenAI
                async def handle_openai_message():
                    async for event in stream:
                        try:
                            if event.type == "conversation.item.input_audio_transcription.completed":
                                # Handle transcription
                                transcript = event.transcript
                                voice_event = VoiceEvent(
                                    type="voice_transcript",
                                    transcript=transcript
                                )
                                self._emit_event(voice_event)
                                
                                await websocket.send(json.dumps({
                                    "type": "transcript",
                                    "text": transcript
                                }))
                            
                            elif event.type == "conversation.item.output_audio.delta":
                                # Handle audio output
                                audio_data = event.delta
                                await websocket.send(json.dumps({
                                    "type": "audio_output",
                                    "audio": base64.b64encode(audio_data).decode()
                                }))
                            
                            elif event.type == "conversation.item.output_text.delta":
                                # Handle text output
                                text = event.delta
                                await websocket.send(json.dumps({
                                    "type": "text_output",
                                    "text": text
                                }))
                            
                            elif event.type == "conversation.item.output_text.done":
                                # Handle completed text
                                full_text = event.text
                                voice_event = VoiceEvent(
                                    type="voice_reply",
                                    text=full_text,
                                    bot_id="brebot"
                                )
                                self._emit_event(voice_event)
                                
                                await websocket.send(json.dumps({
                                    "type": "text_complete",
                                    "text": full_text
                                }))
                            
                            elif event.type == "conversation.item.tool_call.delta":
                                # Handle tool calls
                                tool_call = event.tool_call
                                await websocket.send(json.dumps({
                                    "type": "tool_call",
                                    "tool_call": tool_call
                                }))
                            
                            elif event.type == "conversation.item.tool_call.done":
                                # Handle completed tool calls
                                tool_call = event.tool_call
                                voice_event = VoiceEvent(
                                    type="voice_command",
                                    action={
                                        "tool": tool_call.name,
                                        "parameters": tool_call.parameters
                                    }
                                )
                                self._emit_event(voice_event)
                                
                                await websocket.send(json.dumps({
                                    "type": "tool_call_complete",
                                    "tool_call": tool_call
                                }))
                        
                        except Exception as e:
                            logging.error(f"Error handling OpenAI message: {e}")
                
                # Run both handlers concurrently
                await asyncio.gather(
                    handle_client_message(),
                    handle_openai_message()
                )
        
        except Exception as e:
            logging.error(f"Error in realtime communication: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": str(e)
            }))
    
    async def generate_elevenlabs_audio(self, text: str, voice_id: str) -> Optional[bytes]:
        """Generate audio using ElevenLabs API."""
        if not self.elevenlabs_api_key:
            return None
        
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.elevenlabs_api_key
            }
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            
            return response.content
        
        except Exception as e:
            logging.error(f"Error generating ElevenLabs audio: {e}")
            return None
    
    async def process_voice_command(self, command: str, bot_id: str = "brebot") -> Dict[str, Any]:
        """Process a voice command and return response."""
        try:
            # Parse command and determine action
            command_lower = command.lower()
            
            if "create task" in command_lower or "add task" in command_lower:
                # Extract task details
                task_title = self._extract_task_title(command)
                return {
                    "action": "create_task",
                    "parameters": {
                        "title": task_title,
                        "description": command,
                        "bot_id": bot_id
                    }
                }
            
            elif "add to memory" in command_lower or "remember" in command_lower:
                return {
                    "action": "add_to_memory",
                    "parameters": {
                        "content": command,
                        "category": "voice_input"
                    }
                }
            
            elif "assign to" in command_lower:
                # Extract bot name and task
                parts = command_lower.split("assign to")
                if len(parts) > 1:
                    bot_name = parts[1].strip().split()[0]
                    return {
                        "action": "assign_to_bot",
                        "parameters": {
                            "bot_name": bot_name,
                            "task_description": command
                        }
                    }
            
            else:
                # General conversation
                return {
                    "action": "conversation",
                    "parameters": {
                        "message": command
                    }
                }
        
        except Exception as e:
            logging.error(f"Error processing voice command: {e}")
            return {
                "action": "error",
                "parameters": {
                    "error": str(e)
                }
            }
    
    def _extract_task_title(self, command: str) -> str:
        """Extract task title from voice command."""
        # Simple extraction - look for text after "create task" or "add task"
        command_lower = command.lower()
        
        if "create task" in command_lower:
            parts = command_lower.split("create task")
            if len(parts) > 1:
                return parts[1].strip()
        
        elif "add task" in command_lower:
            parts = command_lower.split("add task")
            if len(parts) > 1:
                return parts[1].strip()
        
        return command
    
    async def close_session(self, session_id: str):
        """Close a voice session."""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.close()
            del self.active_connections[session_id]
            
            brebot_logger.log_agent_action(
                agent_name="VoiceService",
                action="session_closed",
                details={"session_id": session_id}
            )


# Global voice service instance
voice_service = VoiceService()
