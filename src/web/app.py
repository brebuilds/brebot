"""
Enhanced Brebot Web Interface with Three-Panel Dashboard
Integrates ChromaDB, Airtable, and Bot Management
"""

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import json
import uuid
import os
import subprocess
from pathlib import Path
import httpx
import chromadb
from chromadb.config import Settings

# Import voice service
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from services.voice_service import voice_service, VoiceEvent
from services.connection_service import connection_service
from models.connections import ConnectionEvent
from config.system_prompts import get_chat_prompt

# Enhanced app with full integration
app = FastAPI(
    title="Brebot Enhanced Dashboard",
    description="Three-panel dashboard with ChromaDB, Airtable, and Bot Management",
    version="2.0.0",
)

# Mount static files
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

# Templates configuration
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# Global clients
chroma_client = None
airtable_client = None
redis_client = None

# In-memory storage for active tasks and bot status
class TaskStatus(BaseModel):
    task_id: str
    status: str  # pending, running, completed, failed
    message: str
    progress: int = 0
    result: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    bot_id: Optional[str] = None
    pipeline_id: Optional[str] = None

class BotStatus(BaseModel):
    bot_id: str
    bot_type: str
    status: str  # online, offline, busy, error
    current_task: Optional[str] = None
    last_activity: datetime
    health_score: float = 1.0
    tasks_completed: int = 0
    tasks_failed: int = 0

active_tasks: Dict[str, TaskStatus] = {}
bot_statuses: Dict[str, BotStatus] = {}
file_explorer_cache: Dict[str, Any] = {}

# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove dead connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Pydantic Models
class ChatMessage(BaseModel):
    message: str
    context: Optional[str] = None  # bot_id for context switching
    use_rag: bool = True

class FileOperation(BaseModel):
    operation: str  # upload, download, organize, search
    path: str
    parameters: Dict[str, Any] = {}

class BotCommand(BaseModel):
    bot_id: str
    command: str
    parameters: Dict[str, Any] = {}

class PipelineRequest(BaseModel):
    pipeline_type: str  # design-to-shopify, content-creation, etc.
    input_data: Dict[str, Any]
    priority: str = "normal"

# Initialize services
async def initialize_services():
    """Initialize ChromaDB, Airtable, and Redis connections"""
    global chroma_client, airtable_client, redis_client
    
    try:
        # Initialize ChromaDB
        chroma_client = chromadb.HttpClient(
            host="localhost",
            port=8001,
            settings=Settings(allow_reset=True)
        )
        print("✅ ChromaDB connected")
    except Exception as e:
        print(f"⚠️ ChromaDB connection failed: {e}")
    
    try:
        # Initialize Redis (for message queue)
        import redis
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        redis_client.ping()
        print("✅ Redis connected")
    except Exception as e:
        print(f"⚠️ Redis connection failed: {e}")
    
    # Initialize bot statuses
    bot_statuses.update({
        "mocktopus": BotStatus(
            bot_id="mocktopus",
            bot_type="image_processing",
            status="online",
            last_activity=datetime.now(),
            health_score=1.0
        ),
        "airtable-logger": BotStatus(
            bot_id="airtable-logger",
            bot_type="data_management",
            status="online",
            last_activity=datetime.now(),
            health_score=1.0
        ),
        "shopify-publisher": BotStatus(
            bot_id="shopify-publisher",
            bot_type="ecommerce",
            status="online",
            last_activity=datetime.now(),
            health_score=1.0
        )
    })

# Startup event
@app.on_event("startup")
async def startup_event():
    await initialize_services()

# Routes
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the enhanced three-panel dashboard"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "title": "Brebot Enhanced Dashboard"
    })

@app.get("/api/health")
async def health_check():
    """Comprehensive health check for all services"""
    services = {
        "web_interface": "running",
        "ollama": await check_service("http://localhost:11434/api/tags"),
        "openwebui": await check_service("http://localhost:3000/health"),
        "chromadb": await check_service("http://localhost:8001/api/v1/heartbeat"),
        "redis": await check_redis_health(),
        "docker": await check_docker_health()
    }
    
    overall_status = "healthy" if all(
        status in ["running", "healthy"] for status in services.values()
    ) else "degraded"
    
    return {
        "status": overall_status,
        "message": "Brebot Enhanced System Status",
        "timestamp": datetime.now(),
        "services": services,
        "bots": {bot_id: bot.dict() for bot_id, bot in bot_statuses.items()}
    }

@app.get("/api/bots")
async def get_bots():
    """Get all bot statuses"""
    return {"bots": {bot_id: bot.dict() for bot_id, bot in bot_statuses.items()}}

@app.get("/api/bots/{bot_id}/health")
async def get_bot_health(bot_id: str):
    """Get specific bot health"""
    if bot_id not in bot_statuses:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # In a real implementation, this would ping the actual bot
    bot = bot_statuses[bot_id]
    return bot.dict()

@app.post("/api/voice/configure")
async def configure_bot_voice(bot_id: str, voice_config: dict):
    """Configure voice settings for a bot."""
    try:
        from services.voice_service import VoiceConfig
        config = VoiceConfig(**voice_config)
        voice_service.set_bot_voice(bot_id, config)
        return {"status": "success", "message": f"Voice configured for bot {bot_id}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/voice/config/{bot_id}")
async def get_bot_voice_config(bot_id: str):
    """Get voice configuration for a bot."""
    config = voice_service.get_bot_voice(bot_id)
    return {
        "bot_id": bot_id,
        "voice_config": {
            "provider": config.provider,
            "voice_id": config.voice_id,
            "speed": config.speed,
            "pitch": config.pitch
        }
    }

@app.post("/api/voice/process")
async def process_voice_command(command: str, bot_id: str = "brebot"):
    """Process a voice command."""
    try:
        result = await voice_service.process_voice_command(command, bot_id)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Connection Management API
@app.get("/api/connections")
async def get_connections():
    """Get all connection configurations."""
    connections = connection_service.get_all_connections()
    return {
        "connections": [
            {
                "connection_id": conn.connection_id,
                "connection_type": conn.connection_type,
                "name": conn.name,
                "status": conn.status,
                "scopes": [scope.dict() for scope in conn.scopes],
                "enabled_for_ingestion": conn.enabled_for_ingestion,
                "n8n_webhook_url": conn.n8n_webhook_url,
                "n8n_workflow_id": conn.n8n_workflow_id,
                "last_sync": conn.last_sync.isoformat() if conn.last_sync else None,
                "error_message": conn.error_message,
                "metadata": conn.metadata,
                "created_at": conn.created_at.isoformat(),
                "updated_at": conn.updated_at.isoformat()
            }
            for conn in connections
        ]
    }

@app.get("/api/connections/{connection_id}")
async def get_connection(connection_id: str):
    """Get a specific connection configuration."""
    connection = connection_service.get_connection(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    return {
        "connection_id": connection.connection_id,
        "connection_type": connection.connection_type,
        "name": connection.name,
        "status": connection.status,
        "scopes": [scope.dict() for scope in connection.scopes],
        "enabled_for_ingestion": connection.enabled_for_ingestion,
        "n8n_webhook_url": connection.n8n_webhook_url,
        "n8n_workflow_id": connection.n8n_workflow_id,
        "last_sync": connection.last_sync.isoformat() if connection.last_sync else None,
        "error_message": connection.error_message,
        "metadata": connection.metadata,
        "created_at": connection.created_at.isoformat(),
        "updated_at": connection.updated_at.isoformat()
    }

@app.post("/api/connections/{connection_id}/connect")
async def connect_connection(connection_id: str, redirect_uri: str = "http://localhost:8000/connections/callback"):
    """Initiate OAuth connection for a service."""
    oauth_url = connection_service.create_oauth_url(connection_id, redirect_uri)
    if not oauth_url:
        raise HTTPException(status_code=400, detail="Failed to create OAuth URL")
    
    return {"oauth_url": oauth_url}

@app.post("/api/connections/{connection_id}/callback")
async def handle_oauth_callback(connection_id: str, code: str, state: str):
    """Handle OAuth callback."""
    success = await connection_service.handle_oauth_callback(connection_id, code, state)
    if not success:
        raise HTTPException(status_code=400, detail="OAuth callback failed")
    
    return {"status": "success", "message": "Connection established successfully"}

@app.post("/api/connections/{connection_id}/disconnect")
async def disconnect_connection(connection_id: str):
    """Disconnect a connection."""
    success = connection_service.disconnect_connection(connection_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to disconnect")
    
    return {"status": "success", "message": "Connection disconnected"}

@app.post("/api/connections/{connection_id}/toggle-ingestion")
async def toggle_ingestion(connection_id: str, enabled: bool):
    """Toggle ingestion availability for a connection."""
    success = connection_service.toggle_ingestion(connection_id, enabled)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to toggle ingestion")
    
    return {"status": "success", "message": f"Ingestion {'enabled' if enabled else 'disabled'}"}

@app.get("/api/connections/{connection_id}/health")
async def check_connection_health(connection_id: str):
    """Check connection health."""
    health = await connection_service.check_connection_health(connection_id)
    return {
        "connection_id": health.connection_id,
        "is_healthy": health.is_healthy,
        "response_time_ms": health.response_time_ms,
        "last_check": health.last_check.isoformat(),
        "error_details": health.error_details
    }

@app.post("/api/connections/events")
async def process_connection_event(event: dict):
    """Process a connection event from n8n webhook."""
    try:
        connection_event = ConnectionEvent(
            event_id=event.get("event_id", "unknown"),
            connection_id=event.get("connection_id"),
            event_type=event.get("event_type"),
            event_data=event.get("event_data", {}),
            timestamp=datetime.now()
        )
        
        await connection_service.process_connection_event(connection_event)
        
        return {"status": "success", "message": "Event processed"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/connections/{connection_id}/events")
async def get_connection_events(connection_id: str):
    """Get events for a specific connection."""
    events = connection_service.get_connection_events(connection_id)
    return {
        "events": [
            {
                "event_id": event.event_id,
                "connection_id": event.connection_id,
                "event_type": event.event_type,
                "event_data": event.event_data,
                "timestamp": event.timestamp.isoformat(),
                "processed": event.processed
            }
            for event in events
        ]
    }

@app.post("/api/chat")
async def chat_with_brebot(message: ChatMessage, background_tasks: BackgroundTasks):
    """Chat with Brebot using RAG from ChromaDB"""
    task_id = str(uuid.uuid4())
    
    # Add to background tasks
    background_tasks.add_task(process_chat_task, task_id, message)
    
    return {"task_id": task_id, "status": "processing"}

@app.get("/api/chat/{task_id}")
async def get_chat_result(task_id: str):
    """Get chat result"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return active_tasks[task_id]

@app.get("/api/files")
async def get_file_explorer():
    """Get file explorer data"""
    # In a real implementation, this would connect to Dropbox/Drive APIs
    return {
        "files": [
            {
                "name": "design_001.png",
                "type": "image",
                "size": "2.3 MB",
                "modified": "2024-01-01T10:00:00Z",
                "path": "/designs/design_001.png",
                "source": "dropbox"
            },
            {
                "name": "product_catalog.xlsx",
                "type": "spreadsheet",
                "size": "1.1 MB",
                "modified": "2024-01-01T09:30:00Z",
                "path": "/data/product_catalog.xlsx",
                "source": "google_drive"
            }
        ],
        "folders": [
            {
                "name": "Designs",
                "path": "/designs",
                "file_count": 15,
                "source": "dropbox"
            },
            {
                "name": "Marketing Assets",
                "path": "/marketing",
                "file_count": 8,
                "source": "google_drive"
            }
        ]
    }

@app.post("/api/files/operation")
async def file_operation(operation: FileOperation, background_tasks: BackgroundTasks):
    """Perform file operations"""
    task_id = str(uuid.uuid4())
    background_tasks.add_task(process_file_operation, task_id, operation)
    
    return {"task_id": task_id, "status": "processing"}

@app.post("/api/pipeline/start")
async def start_pipeline(pipeline: PipelineRequest, background_tasks: BackgroundTasks):
    """Start a new pipeline"""
    task_id = str(uuid.uuid4())
    background_tasks.add_task(process_pipeline, task_id, pipeline)
    
    return {"task_id": task_id, "pipeline_id": str(uuid.uuid4()), "status": "started"}

@app.get("/api/pipeline/{pipeline_id}")
async def get_pipeline_status(pipeline_id: str):
    """Get pipeline status"""
    # In a real implementation, this would query Airtable
    return {
        "pipeline_id": pipeline_id,
        "status": "in_progress",
        "current_step": "mockup_generation",
        "progress": 45,
        "steps": [
            {"name": "file_upload", "status": "completed", "duration": 2.3},
            {"name": "mockup_generation", "status": "running", "duration": 15.7},
            {"name": "airtable_log", "status": "pending", "duration": 0},
            {"name": "shopify_publish", "status": "pending", "duration": 0}
        ],
        "results": {
            "mockups_generated": 3,
            "airtable_record_id": "rec123456",
            "shopify_draft_id": None
        }
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await manager.send_personal_message(
                    json.dumps({"type": "pong", "timestamp": datetime.now().isoformat()}),
                    websocket
                )
            elif message.get("type") == "bot_command":
                # Handle bot commands
                await handle_bot_command(message, websocket)
            else:
                # Echo other messages
                await manager.send_personal_message(f"Echo: {data}", websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.websocket("/ws/voice")
async def voice_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for voice communication."""
    await websocket.accept()
    
    session_id = str(uuid.uuid4())
    
    try:
        # Start voice session
        await voice_service.start_realtime_session(session_id, websocket)
    except WebSocketDisconnect:
        await voice_service.close_session(session_id)
    except Exception as e:
        logging.error(f"Error in voice WebSocket: {e}")
        await websocket.close()

# Voice event handler
def handle_voice_event(event: VoiceEvent):
    """Handle voice events and integrate with existing systems."""
    if event.type == "voice_command":
        # Handle voice commands
        if event.action:
            # Process the action (create task, add to memory, etc.)
            print(f"Voice command: {event.action}")
    elif event.type == "voice_reply":
        # Log voice replies to chat
        print(f"Voice reply: {event.text}")
    elif event.type == "voice_transcript":
        # Log transcripts
        print(f"Voice transcript: {event.transcript}")

# Register voice event handler
voice_service.add_event_handler(handle_voice_event)

# Background task processors
async def process_chat_task(task_id: str, message: ChatMessage):
    """Process chat with RAG"""
    task = TaskStatus(
        task_id=task_id,
        status="running",
        message="Processing chat with Brebot...",
        progress=0,
        created_at=datetime.now()
    )
    active_tasks[task_id] = task
    
    try:
        # Get the system prompt for chat
        system_prompt = get_chat_prompt()
        
        # Simulate RAG processing
        await asyncio.sleep(2)
        
        # In a real implementation, this would:
        # 1. Query ChromaDB for relevant context
        # 2. Send to Ollama with context and system prompt
        # 3. Return response
        
        task.progress = 50
        task.message = "Retrieving relevant context..."
        await manager.broadcast(json.dumps({
            "type": "task_update",
            "task_id": task_id,
            "task": task.dict()
        }))
        
        await asyncio.sleep(2)
        
        task.progress = 100
        task.status = "completed"
        task.message = "Chat response generated"
        task.result = {
            "response": f"Based on your query '{message.message}', here's what I found in the knowledge base...",
            "sources": ["design_guidelines.pdf", "brand_standards.docx"],
            "confidence": 0.92
        }
        task.completed_at = datetime.now()
        
        await manager.broadcast(json.dumps({
            "type": "task_update",
            "task_id": task_id,
            "task": task.dict()
        }))
        
    except Exception as e:
        task.status = "failed"
        task.message = f"Error: {str(e)}"
        task.completed_at = datetime.now()
        
        await manager.broadcast(json.dumps({
            "type": "task_update",
            "task_id": task_id,
            "task": task.dict()
        }))

async def process_file_operation(task_id: str, operation: FileOperation):
    """Process file operations"""
    task = TaskStatus(
        task_id=task_id,
        status="running",
        message=f"Processing {operation.operation}...",
        progress=0,
        created_at=datetime.now()
    )
    active_tasks[task_id] = task
    
    try:
        # Simulate file operation
        await asyncio.sleep(3)
        
        task.progress = 100
        task.status = "completed"
        task.message = f"{operation.operation} completed successfully"
        task.result = {
            "operation": operation.operation,
            "path": operation.path,
            "files_processed": 5,
            "success": True
        }
        task.completed_at = datetime.now()
        
        await manager.broadcast(json.dumps({
            "type": "task_update",
            "task_id": task_id,
            "task": task.dict()
        }))
        
    except Exception as e:
        task.status = "failed"
        task.message = f"Error: {str(e)}"
        task.completed_at = datetime.now()
        
        await manager.broadcast(json.dumps({
            "type": "task_update",
            "task_id": task_id,
            "task": task.dict()
        }))

async def process_pipeline(task_id: str, pipeline: PipelineRequest):
    """Process pipeline execution"""
    task = TaskStatus(
        task_id=task_id,
        status="running",
        message=f"Starting {pipeline.pipeline_type} pipeline...",
        progress=0,
        created_at=datetime.now()
    )
    active_tasks[task_id] = task
    
    try:
        # Simulate pipeline processing
        steps = ["file_processing", "mockup_generation", "airtable_log", "shopify_publish"]
        
        for i, step in enumerate(steps):
            task.message = f"Executing {step}..."
            task.progress = int((i + 1) / len(steps) * 100)
            
            await manager.broadcast(json.dumps({
                "type": "task_update",
                "task_id": task_id,
                "task": task.dict()
            }))
            
            await asyncio.sleep(2)
        
        task.status = "completed"
        task.message = "Pipeline completed successfully"
        task.result = {
            "pipeline_type": pipeline.pipeline_type,
            "steps_completed": len(steps),
            "total_duration": 8.5,
            "success": True
        }
        task.completed_at = datetime.now()
        
        await manager.broadcast(json.dumps({
            "type": "task_update",
            "task_id": task_id,
            "task": task.dict()
        }))
        
    except Exception as e:
        task.status = "failed"
        task.message = f"Pipeline error: {str(e)}"
        task.completed_at = datetime.now()
        
        await manager.broadcast(json.dumps({
            "type": "task_update",
            "task_id": task_id,
            "task": task.dict()
        }))

async def handle_bot_command(message: dict, websocket: WebSocket):
    """Handle bot commands via WebSocket"""
    try:
        bot_id = message.get("bot_id")
        command = message.get("command")
        
        if bot_id in bot_statuses:
            bot = bot_statuses[bot_id]
            bot.last_activity = datetime.now()
            
            # Simulate command execution
            response = {
                "type": "bot_response",
                "bot_id": bot_id,
                "command": command,
                "result": f"Command '{command}' executed successfully",
                "timestamp": datetime.now().isoformat()
            }
            
            await manager.send_personal_message(json.dumps(response), websocket)
        else:
            error_response = {
                "type": "bot_error",
                "bot_id": bot_id,
                "error": "Bot not found",
                "timestamp": datetime.now().isoformat()
            }
            await manager.send_personal_message(json.dumps(error_response), websocket)
            
    except Exception as e:
        error_response = {
            "type": "bot_error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        await manager.send_personal_message(json.dumps(error_response), websocket)

# Helper functions
async def check_service(url: str) -> str:
    """Check if a service is running"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5)
            return "healthy" if response.status_code == 200 else "unhealthy"
    except:
        return "unreachable"

async def check_redis_health() -> str:
    """Check Redis health"""
    try:
        if redis_client:
            redis_client.ping()
            return "healthy"
        return "unreachable"
    except:
        return "unreachable"

async def check_docker_health() -> str:
    """Check Docker health"""
    try:
        result = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=5)
        return "healthy" if result.returncode == 0 else "unhealthy"
    except:
        return "unreachable"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
