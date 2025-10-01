"""
Enhanced Brebot Web Interface with Three-Panel Dashboard
Integrates ChromaDB, Airtable, and Bot Management
"""

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import asyncio
import json
import uuid
import os
import subprocess
from pathlib import Path
import httpx
import chromadb
from chromadb.config import Settings

# Shared utilities
from utils import brebot_logger

# Integration management
from services.integration_manager import get_integration_manager, initialize_all_integrations

# Import voice service (optional)
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

voice_service = None
VoiceEvent = None
VoiceConfig = None
VOICE_SERVICE_ERROR: Optional[str] = None

try:
    from services.voice_service import voice_service as _voice_service, VoiceEvent as _VoiceEvent, VoiceConfig as _VoiceConfig

    voice_service = _voice_service
    VoiceEvent = _VoiceEvent
    VoiceConfig = _VoiceConfig
except Exception as exc:  # pragma: no cover - optional dependency failures
    class VoiceEvent(BaseModel):  # type: ignore[no-redef]
        type: str = "error"
        transcript: Optional[str] = None
        text: Optional[str] = None
        audio_url: Optional[str] = None
        bot_id: Optional[str] = None
        action: Optional[Dict[str, Any]] = None

    VOICE_SERVICE_ERROR = str(exc)
    brebot_logger.log_error(exc, "web.app.voice_service_import")

from services.connection_service import connection_service
from services.memory_service import memoryService
from services.bot_architect_service import botArchitectService, BotDesignSpec
from models.connections import ConnectionEvent
from config.system_prompts import get_chat_prompt
from config import get_chroma_client, get_redis_client, airtable_available
from services.ingestion_service import ingest_path, log_ingestion_run
from services.workspace_service import ensure_workspace
from config import settings

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
ingestion_runs: List[Dict[str, Any]] = []  # legacy in-memory fallback

INGESTION_REDIS_KEY = "brebot:ingestion:runs"
MAX_INGESTION_RUNS = 100

VOICE_SERVICE_AVAILABLE = voice_service is not None


_redis_ingestion_error_logged = False


def get_redis_connection():
    """Return a cached Redis connection if available."""
    global redis_client, _redis_ingestion_error_logged
    if redis_client is not None:
        return redis_client

    try:
        redis_client = get_redis_client()
    except Exception as exc:  # pragma: no cover - connection failure
        if not _redis_ingestion_error_logged:
            brebot_logger.log_error(exc, "web.get_redis_connection")
            _redis_ingestion_error_logged = True
        redis_client = None

    if redis_client is None:
        _redis_ingestion_error_logged = True

    return redis_client


def persist_ingestion_run(entry: Dict[str, Any]) -> None:
    """Persist a run record to Redis or fall back to in-memory storage."""
    client = get_redis_connection()
    if client is not None:
        try:
            client.lpush(INGESTION_REDIS_KEY, json.dumps(entry))
            client.ltrim(INGESTION_REDIS_KEY, 0, MAX_INGESTION_RUNS - 1)
            return
        except Exception as exc:  # pragma: no cover - redis failure
            brebot_logger.log_error(exc, "web.persist_ingestion_run")

    ingestion_runs.insert(0, entry)
    del ingestion_runs[MAX_INGESTION_RUNS:]


def load_recent_ingestion_runs(limit: int = 25) -> List[Dict[str, Any]]:
    """Retrieve recent ingestion runs from Redis or fallback storage."""
    client = get_redis_connection()
    if client is not None:
        try:
            raw_runs = client.lrange(INGESTION_REDIS_KEY, 0, limit - 1)
            runs: List[Dict[str, Any]] = []
            for raw in raw_runs:
                try:
                    runs.append(json.loads(raw))
                except (TypeError, json.JSONDecodeError):
                    continue
            if runs:
                return runs
        except Exception as exc:  # pragma: no cover - redis failure
            brebot_logger.log_error(exc, "web.load_recent_ingestion_runs")

    return ingestion_runs[:limit]


def ensure_voice_service_ready() -> None:
    """Ensure voice service is available before handling voice endpoints."""
    if voice_service is None:
        detail = "Voice service is currently unavailable"
        if VOICE_SERVICE_ERROR:
            detail = f"Voice service unavailable: {VOICE_SERVICE_ERROR}"
        raise HTTPException(status_code=503, detail=detail)

WORKSPACE_ROOT = Path.home() / "BrebotWorkspace"
INGEST_DROP_PATH = WORKSPACE_ROOT / "Inbox" / "ingest"

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


async def broadcast_task_update(task_id: str, task: TaskStatus) -> None:
    await manager.broadcast(
        json.dumps(
            {
                "type": "task_update",
                "task_id": task_id,
                "task": task.model_dump(mode="json"),
            }
        )
    )


async def broadcast_ingestion_runs() -> None:
    runs = load_recent_ingestion_runs()
    await manager.broadcast(json.dumps({"type": "ingestion_runs", "runs": runs}))

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


class IngestionRequest(BaseModel):
    path: Optional[str] = None
    domain: Optional[str] = None
    project: Optional[str] = None
    source_type: str = "chat_history"
    tags: List[str] = []
    dry_run: bool = False
    no_archive: bool = False


class BotDesignRequest(BaseModel):
    goal: str
    description: Optional[str] = None
    name: Optional[str] = None
    primary_tasks: List[str] = []
    data_sources: List[str] = []
    integrations: List[str] = []
    success_metrics: List[str] = []
    personality: Optional[str] = None
    auto_create: bool = False

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
    import asyncio
    
    # Run all health checks in parallel for faster response
    services_tasks = {
        "web_interface": asyncio.create_task(asyncio.sleep(0, "running")),
        "ollama": asyncio.create_task(check_service("http://localhost:11434/api/tags")),
        "openwebui": asyncio.create_task(check_service("http://localhost:3000/health")),
        "chromadb": asyncio.create_task(check_service("http://localhost:8001/api/v1/heartbeat")),
        "redis": asyncio.create_task(check_redis_health()),
        "docker": asyncio.create_task(check_docker_health()),
        "voice_service": asyncio.create_task(asyncio.sleep(0, "running" if VOICE_SERVICE_AVAILABLE else "unavailable")),
    }
    
    # Wait for all tasks to complete
    services = {}
    for name, task in services_tasks.items():
        try:
            services[name] = await task
        except Exception as e:
            services[name] = "error"
    
    overall_status = "healthy" if all(
        status in ["running", "healthy"] for status in services.values()
    ) else "degraded"
    
    return {
        "status": overall_status,
        "message": "Brebot Enhanced System Status",
        "timestamp": datetime.now(),
        "services": services,
        "bots": {bot_id: bot.dict() for bot_id, bot in bot_statuses.items()},
        "voice_error": VOICE_SERVICE_ERROR,
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


@app.post("/api/bots/architect")
async def design_bot(request: BotDesignRequest):
    """Generate a bot design recommendation and optionally create it."""
    spec = BotDesignSpec(
        goal=request.goal,
        description=request.description,
        name=request.name,
        primary_tasks=request.primary_tasks,
        data_sources=request.data_sources,
        integrations=request.integrations,
        success_metrics=request.success_metrics,
        personality=request.personality,
        auto_create=request.auto_create,
    )

    result = await botArchitectService.design_bot(spec)
    return result

@app.post("/api/voice/configure")
async def configure_bot_voice(bot_id: str, voice_config: dict):
    """Configure voice settings for a bot."""
    ensure_voice_service_ready()
    try:
        if VoiceConfig is None or voice_service is None:
            raise RuntimeError("Voice configuration unavailable")
        config = VoiceConfig(**voice_config)
        voice_service.set_bot_voice(bot_id, config)
        return {"status": "success", "message": f"Voice configured for bot {bot_id}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/voice/config/{bot_id}")
async def get_bot_voice_config(bot_id: str):
    """Get voice configuration for a bot."""
    ensure_voice_service_ready()
    if voice_service is None:
        raise HTTPException(status_code=503, detail="Voice service unavailable")
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
        ensure_voice_service_ready()
        if voice_service is None:
            raise RuntimeError("Voice service unavailable")
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


@app.post("/api/system/power-up")
async def system_power_up():
    """Initiate system checks and ensure workspace structure exists."""
    response = {
        "timestamp": datetime.utcnow().isoformat(),
        "workspace": {},
        "chroma": {},
        "redis": {},
        "airtable": {},
    }

    try:
        ensure_workspace(WORKSPACE_ROOT)
        response["workspace"] = {"status": "ready", "path": str(WORKSPACE_ROOT)}
    except Exception as exc:
        response["workspace"] = {"status": "error", "message": str(exc)}

    try:
        client = get_chroma_client()
        client.list_collections()
        response["chroma"] = {"status": "ready"}
    except Exception as exc:
        response["chroma"] = {"status": "error", "message": str(exc)}

    try:
        redis_client = get_redis_client()
        if redis_client:
            redis_client.ping()
            response["redis"] = {"status": "ready"}
        else:
            response["redis"] = {"status": "unknown", "message": "Redis client not configured"}
    except Exception as exc:
        response["redis"] = {"status": "error", "message": str(exc)}

    response["airtable"] = {
        "status": "ready" if airtable_available() else "not_configured"
    }

    return response


@app.post("/api/ingest/upload")
async def upload_ingestion_files(files: List[UploadFile] = File(...)):
    """Upload files into the inbox drop zone and start ingestion."""
    ensure_workspace(WORKSPACE_ROOT)
    drop_path = INGEST_DROP_PATH
    drop_path.mkdir(parents=True, exist_ok=True)

    saved_files = []
    for upload in files:
        content = await upload.read()
        destination = drop_path / upload.filename
        destination.write_bytes(content)
        saved_files.append(upload.filename)

    job_id = str(uuid.uuid4())
    request = IngestionRequest(path=str(drop_path))
    asyncio.create_task(execute_ingestion_job(job_id, request))

    return {
        "task_id": job_id,
        "saved_files": saved_files,
    }


@app.post("/api/ingest/run")
async def run_ingestion(request: IngestionRequest):
    """Trigger ingestion for the specified path (defaults to inbox)."""
    job_id = str(uuid.uuid4())
    asyncio.create_task(execute_ingestion_job(job_id, request))
    return {"task_id": job_id}


@app.get("/api/ingest/runs")
async def get_ingestion_runs():
    """Return recent ingestion runs."""
    return {"runs": load_recent_ingestion_runs()}

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

# New Code Editor APIs
class CodeFile(BaseModel):
    path: str
    content: str
    language: str = "python"

@app.get("/api/code/browse")
async def browse_code_files():
    """Browse code files in the project"""
    project_root = Path(__file__).parent.parent
    code_files = []
    
    # Get Python files
    for py_file in project_root.rglob("*.py"):
        if "__pycache__" not in str(py_file) and "venv" not in str(py_file):
            rel_path = py_file.relative_to(project_root)
            code_files.append({
                "path": str(rel_path),
                "name": py_file.name,
                "type": "python",
                "size": py_file.stat().st_size,
                "modified": datetime.fromtimestamp(py_file.stat().st_mtime).isoformat()
            })
    
    return {"files": code_files[:50]}  # Limit to 50 files for performance

@app.get("/api/code/read/{file_path:path}")
async def read_code_file(file_path: str):
    """Read a code file for editing"""
    project_root = Path(__file__).parent.parent
    full_path = project_root / file_path
    
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Security check - only allow files within project
    if not str(full_path.resolve()).startswith(str(project_root.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        content = full_path.read_text(encoding='utf-8')
        language = "python" if file_path.endswith('.py') else "text"
        
        return {
            "path": file_path,
            "content": content,
            "language": language,
            "size": len(content),
            "lines": len(content.split('\n'))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

@app.post("/api/code/save")
async def save_code_file(code_file: CodeFile):
    """Save a code file with live editing"""
    project_root = Path(__file__).parent.parent
    full_path = project_root / code_file.path
    
    # Security check - only allow files within project
    if not str(full_path.resolve()).startswith(str(project_root.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Create backup
        if full_path.exists():
            backup_path = full_path.with_suffix(f"{full_path.suffix}.backup")
            backup_path.write_text(full_path.read_text(encoding='utf-8'), encoding='utf-8')
        
        # Save new content
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(code_file.content, encoding='utf-8')
        
        brebot_logger.log_agent_action(
            agent_name="CodeEditor",
            action="file_saved",
            details={"file": code_file.path, "size": len(code_file.content)}
        )
        
        return {
            "success": True,
            "message": f"File {code_file.path} saved successfully",
            "backup_created": full_path.exists()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

@app.post("/api/agents/create")
async def create_new_agent(agent_spec: BotDesignSpec):
    """Create a new agent dynamically"""
    try:
        # Use the bot architect service to create the agent
        result = await botArchitectService.design_bot(agent_spec)
        
        if result.get("success"):
            # Deploy the agent
            deployment_result = await botArchitectService.deploy_bot(result["bot_config"])
            
            brebot_logger.log_agent_action(
                agent_name="BotArchitect",
                action="agent_created",
                details={"agent_name": agent_spec.name, "department": agent_spec.department}
            )
            
            return {
                "success": True,
                "agent_id": deployment_result.get("agent_id"),
                "message": f"Agent {agent_spec.name} created successfully",
                "config": result["bot_config"]
            }
        else:
            return {"success": False, "error": result.get("error", "Unknown error")}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating agent: {str(e)}")

@app.get("/api/agents/templates")
async def get_agent_templates():
    """Get available agent templates"""
    return {
        "templates": [
            {
                "id": "file_organizer",
                "name": "File Organizer",
                "description": "Organizes files and directories",
                "category": "productivity",
                "tools": ["file_operations", "folder_creation"],
                "example_config": {
                    "role": "File Organization Specialist",
                    "goal": "Organize files efficiently",
                    "backstory": "Expert in file management"
                }
            },
            {
                "id": "data_analyst", 
                "name": "Data Analyst",
                "description": "Analyzes data and creates reports",
                "category": "analytics",
                "tools": ["data_processing", "visualization"],
                "example_config": {
                    "role": "Data Analysis Expert",
                    "goal": "Extract insights from data",
                    "backstory": "Experienced data scientist"
                }
            },
            {
                "id": "social_media_manager",
                "name": "Social Media Manager", 
                "description": "Manages social media content and engagement",
                "category": "marketing",
                "tools": ["content_creation", "social_posting"],
                "example_config": {
                    "role": "Social Media Specialist",
                    "goal": "Increase social media engagement",
                    "backstory": "Marketing expert with social media focus"
                }
            }
        ]
    }

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
    if voice_service is None:
        await websocket.close(code=1011, reason="Voice service unavailable")
        return

    await websocket.accept()
    
    session_id = str(uuid.uuid4())
    
    try:
        # Start voice session
        await voice_service.start_realtime_session(session_id, websocket)
    except WebSocketDisconnect:
        if voice_service:
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

# Register voice event handler if voice service available
if voice_service:
    voice_service.add_event_handler(handle_voice_event)


async def execute_ingestion_job(job_id: str, request: IngestionRequest) -> None:
    ensure_workspace(WORKSPACE_ROOT)
    drop_path = Path(request.path).expanduser().resolve() if request.path else INGEST_DROP_PATH
    drop_path.mkdir(parents=True, exist_ok=True)

    task = TaskStatus(
        task_id=job_id,
        status="running",
        message="Embedding files into Brebot's memory...",
        progress=0,
        created_at=datetime.now(),
        bot_id="ingestion",
    )
    active_tasks[job_id] = task
    await broadcast_task_update(job_id, task)

    run_id = f"ingest_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    try:
        task.message = "Scanning files..."
        await broadcast_task_update(job_id, task)

        result = await ingest_path(
            target=drop_path,
            workspace=WORKSPACE_ROOT,
            domain=request.domain,
            project=request.project,
            source_type=request.source_type,
            extra_tags=request.tags,
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
            dry_run=request.dry_run,
            no_archive=request.no_archive,
        )

        if result.get("status") != "empty" and not request.dry_run:
            log_ingestion_run(run_id, result, request.source_type)

        entry = {
            "run_id": run_id,
            "timestamp": datetime.utcnow().isoformat(),
            "domain": result.get("domain"),
            "project": result.get("project"),
            "status": result.get("status"),
            "files_processed": result.get("files_processed"),
            "chunks": result.get("chunks"),
            "dry_run": result.get("dry_run"),
        }
        persist_ingestion_run(entry)

        task.progress = 100
        task.status = "completed" if result.get("status") == "success" else "not_found"
        task.message = (
            "Ingestion completed" if result.get("status") == "success" else "No files found to ingest"
        )
        task.result = {"run_id": run_id, **result}
        task.completed_at = datetime.now()
    except Exception as exc:
        brebot_logger.log_error(exc, "web.execute_ingestion_job")
        task.status = "failed"
        task.message = f"Error: {exc}"
        task.completed_at = datetime.now()
        task.result = {"error": str(exc)}
        persist_ingestion_run(
            {
                "run_id": run_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "failed",
                "files_processed": 0,
                "chunks": 0,
                "domain": request.domain,
                "project": request.project,
                "dry_run": request.dry_run,
                "error": str(exc),
            }
        )
    finally:
        await broadcast_task_update(job_id, task)
        await broadcast_ingestion_runs()

def parse_chat_context(context: Optional[str]) -> tuple[Optional[str], Optional[str], List[str]]:
    """Parse chat context string into domain/project/tag hints."""
    domain: Optional[str] = None
    project: Optional[str] = None
    tags: List[str] = []

    if not context:
        return domain, project, tags

    separators = ["|", ","]
    tokens = [context]
    for sep in separators:
        tokens = [subtoken for token in tokens for subtoken in token.split(sep)]

    for token in tokens:
        token = token.strip()
        if not token:
            continue
        if "=" in token:
            key, value = [part.strip() for part in token.split("=", 1)]
            key_lower = key.lower()
            if key_lower == "domain":
                domain = value or domain
            elif key_lower == "project":
                project = value or project
            elif key_lower in {"tag", "tags"}:
                tags.extend(v.strip() for v in value.split("/") if v.strip())
            else:
                tags.append(value)
        elif "/" in token:
            parts = [part.strip() for part in token.split("/", 1)]
            if len(parts) == 2:
                domain = domain or parts[0]
                project = project or parts[1]
        else:
            tags.append(token)

    # Deduplicate tags while preserving order
    seen: set[str] = set()
    unique_tags: List[str] = []
    for tag in tags:
        if tag and tag not in seen:
            unique_tags.append(tag)
            seen.add(tag)

    return domain, project, unique_tags

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
        
        # Retrieve context from memory service if enabled
        context_domain, context_project, context_tags = parse_chat_context(message.context)
        rag_results: List[Dict[str, Any]] = []
        if message.use_rag:
            try:
                search_response = await memoryService.search(
                    query=message.message,
                    k=settings.top_k_results,
                    tags=context_tags or None,
                    domain=context_domain,
                    project=context_project,
                )
                if search_response.get("status") == "success":
                    rag_results = search_response.get("results", [])
            except Exception as exc:  # pragma: no cover - runtime safety
                brebot_logger.log_error(exc, "web.process_chat_task.rag")

        task.progress = 50 if message.use_rag else 20
        task.message = "Retrieving relevant context..." if message.use_rag else "Drafting response..."
        await manager.broadcast(json.dumps({
            "type": "task_update",
            "task_id": task_id,
            "task": task.model_dump(mode="json"),
        }))

        # Generate response using Ollama with BreBot v2.0
        try:
            import httpx
            
            # Prepare context from RAG results
            context_text = ""
            if rag_results:
                context_text = "\n\nRelevant context from your knowledge base:\n"
                for idx, result in enumerate(rag_results[:3], start=1):
                    summary = result.get("summary", "")
                    snippet = summary[:200] + ("…" if len(summary) > 200 else "")
                    source_meta = result.get("metadata", {}) or {}
                    label = source_meta.get("source_path") or source_meta.get("project") or f"memory_{idx}"
                    context_text += f"{idx}. {label}: {snippet}\n"
            
            # Prepare the full prompt
            full_prompt = f"{system_prompt}\n\nUser message: {message.message}{context_text}"
            
            # Call Ollama API
            async with httpx.AsyncClient() as client:
                ollama_response = await client.post(
                    f"{settings.ollama_base_url}/api/generate",
                    json={
                        "model": settings.ollama_model,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "max_tokens": 1000
                        }
                    },
                    timeout=60.0
                )
                
                if ollama_response.status_code == 200:
                    ollama_data = ollama_response.json()
                    response_text = ollama_data.get("response", "I'm having trouble generating a response right now.")
                else:
                    response_text = "I'm having trouble connecting to my AI brain right now. Let me try again!"
                    
        except Exception as e:
            brebot_logger.log_error(e, "web.process_chat_task.ollama")
            response_text = "I'm having a bit of a brain freeze right now, but I'm still here to help! What else can I do for you?"

        task.progress = 100
        task.status = "completed"
        task.message = "Chat response generated"
        task.result = {
            "response": response_text,
            "sources": rag_results,
            "context_filters": {
                "domain": context_domain,
                "project": context_project,
                "tags": context_tags,
            },
            "confidence": 0.85 if rag_results else 0.4,
            "model_used": settings.ollama_model,
            "rag_enabled": message.use_rag,
        }
        task.completed_at = datetime.now()
        
        await manager.broadcast(json.dumps({
            "type": "task_update",
            "task_id": task_id,
            "task": task.model_dump(mode="json"),
        }))

    except Exception as e:
        task.status = "failed"
        task.message = f"Error: {str(e)}"
        task.completed_at = datetime.now()
        
        await manager.broadcast(json.dumps({
            "type": "task_update",
            "task_id": task_id,
            "task": task.model_dump(mode="json"),
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
            "task": task.model_dump(mode="json"),
        }))
        
    except Exception as e:
        task.status = "failed"
        task.message = f"Error: {str(e)}"
        task.completed_at = datetime.now()
        
        await manager.broadcast(json.dumps({
            "type": "task_update",
            "task_id": task_id,
            "task": task.model_dump(mode="json"),
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
                "task": task.model_dump(mode="json"),
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
            "task": task.model_dump(mode="json"),
        }))
        
    except Exception as e:
        task.status = "failed"
        task.message = f"Pipeline error: {str(e)}"
        task.completed_at = datetime.now()
        
        await manager.broadcast(json.dumps({
            "type": "task_update",
            "task_id": task_id,
            "task": task.model_dump(mode="json"),
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
            response = await client.get(url, timeout=2)
            return "healthy" if response.status_code == 200 else "unhealthy"
    except:
        return "unreachable"

# ===============================
# INTEGRATIONS API ENDPOINTS
# ===============================

class IntegrationConfigRequest(BaseModel):
    platform: str
    api_key: Optional[str] = None
    additional_config: Optional[Dict[str, Any]] = None
    enabled: bool = True

@app.get("/api/integrations")
async def get_integrations():
    """Get all platform integrations with their status."""
    try:
        manager = get_integration_manager()
        summary = await manager.get_integration_summary()
        
        return {
            "integrations": summary["platforms"],
            "health_details": summary["health_details"],
            "summary": {
                "total": summary["total_integrations"],
                "enabled": summary["enabled_integrations"],
                "healthy": summary["healthy_integrations"]
            },
            "activity_summary": summary.get("activity_summary", {}),
            "generated_at": summary["generated_at"]
        }
    except Exception as e:
        brebot_logger.log_error(e, context="web.get_integrations")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/integrations/{platform}/configure")
async def configure_integration(platform: str, config: IntegrationConfigRequest):
    """Configure a platform integration."""
    try:
        manager = get_integration_manager()
        
        # Update platform configuration
        manager.update_platform_config(
            platform=platform,
            enabled=config.enabled,
            api_key=config.api_key,
            additional_config=config.additional_config
        )
        
        # Re-initialize services
        await manager.initialize_services()
        
        # Get updated status
        platform_config = manager.get_platform_config(platform)
        
        return {
            "platform": platform,
            "status": "configured",
            "enabled": platform_config.enabled if platform_config else False,
            "health_status": platform_config.health_status if platform_config else "unknown"
        }
        
    except Exception as e:
        brebot_logger.log_error(e, context=f"web.configure_integration.{platform}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/integrations/{platform}/enable")
async def enable_integration(platform: str):
    """Enable a platform integration."""
    try:
        manager = get_integration_manager()
        manager.update_platform_config(platform=platform, enabled=True)
        await manager.initialize_services()
        
        return {"platform": platform, "status": "enabled"}
        
    except Exception as e:
        brebot_logger.log_error(e, context=f"web.enable_integration.{platform}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/integrations/{platform}/disable")
async def disable_integration(platform: str):
    """Disable a platform integration."""
    try:
        manager = get_integration_manager()
        manager.update_platform_config(platform=platform, enabled=False)
        
        return {"platform": platform, "status": "disabled"}
        
    except Exception as e:
        brebot_logger.log_error(e, context=f"web.disable_integration.{platform}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/integrations/{platform}/health")
async def check_integration_health(platform: str):
    """Check health of a specific platform integration."""
    try:
        manager = get_integration_manager()
        health_results = await manager.health_check_all()
        
        if platform not in health_results:
            raise HTTPException(status_code=404, detail=f"Platform {platform} not found")
        
        return {
            "platform": platform,
            "health": health_results[platform]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        brebot_logger.log_error(e, context=f"web.check_integration_health.{platform}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/integrations/health-check")
async def run_health_check_all():
    """Run health check on all integrations."""
    try:
        manager = get_integration_manager()
        health_results = await manager.health_check_all()
        
        healthy_count = sum(1 for result in health_results.values() if result["status"] == "healthy")
        
        return {
            "health_results": health_results,
            "summary": {
                "total_platforms": len(health_results),
                "healthy_platforms": healthy_count,
                "unhealthy_platforms": len(health_results) - healthy_count
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        brebot_logger.log_error(e, context="web.run_health_check_all")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/integrations/activity/export")
async def export_integration_activity(
    platform: Optional[str] = None,
    hours: int = 24,
    format_type: str = "json"
):
    """Export integration activity logs."""
    try:
        manager = get_integration_manager()
        export_path = await manager.export_activity_logs(
            platform=platform,
            hours=hours,
            format_type=format_type
        )
        
        return {
            "export_path": export_path,
            "platform": platform,
            "hours": hours,
            "format": format_type,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        brebot_logger.log_error(e, context="web.export_integration_activity")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/integrations/initialize")
async def initialize_integrations():
    """Initialize all platform integrations."""
    try:
        manager = await initialize_all_integrations()
        initialized_services = await manager.initialize_services()
        
        return {
            "status": "initialized",
            "initialized_services": initialized_services,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        brebot_logger.log_error(e, context="web.initialize_integrations")
        raise HTTPException(status_code=500, detail=str(e))

# ===============================
# HEALTH CHECK FUNCTIONS
# ===============================

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
        result = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=2)
        return "healthy" if result.returncode == 0 else "unhealthy"
    except:
        return "unreachable"


# Theme Management APIs
class ThemeConfig(BaseModel):
    name: str
    primary_color: str
    secondary_color: str
    accent_color: str
    background_color: str
    text_color: str
    font_family: str
    logo_url: Optional[str] = None
    custom_css: Optional[str] = None

@app.get("/api/themes")
async def get_available_themes():
    """Get available theme presets"""
    themes = {
        "default": {
            "name": "Default",
            "primary_color": "#3b82f6",
            "secondary_color": "#64748b",
            "accent_color": "#10b981",
            "background_color": "#ffffff",
            "text_color": "#1f2937",
            "font_family": "Inter, system-ui, sans-serif"
        },
        "glassmorphism": {
            "name": "Glass Morphism",
            "primary_color": "#8b5cf6",
            "secondary_color": "#a78bfa",
            "accent_color": "#06b6d4",
            "background_color": "rgba(255, 255, 255, 0.1)",
            "text_color": "#1f2937",
            "font_family": "SF Pro Display, -apple-system, sans-serif"
        },
        "neon_brutalism": {
            "name": "Neon Brutalism",
            "primary_color": "#ff0080",
            "secondary_color": "#00ff80",
            "accent_color": "#ffff00",
            "background_color": "#000000",
            "text_color": "#ffffff",
            "font_family": "JetBrains Mono, Courier New, monospace"
        },
        "luxury_clean": {
            "name": "Luxury Clean White",
            "primary_color": "#d4af37",
            "secondary_color": "#c9b037",
            "accent_color": "#f5f5dc",
            "background_color": "#fafafa",
            "text_color": "#2c2c2c",
            "font_family": "Playfair Display, Georgia, serif"
        },
        "dark_techy": {
            "name": "Dark Techy Glow",
            "primary_color": "#00ff41",
            "secondary_color": "#00d4aa",
            "accent_color": "#0099cc",
            "background_color": "#0a0a0a",
            "text_color": "#00ff41",
            "font_family": "Fira Code, Monaco, monospace"
        },
        "coastal_surf": {
            "name": "Coastal Surf Zine",
            "primary_color": "#00a8cc",
            "secondary_color": "#ffa500",
            "accent_color": "#ff6b6b",
            "background_color": "#f0f8ff",
            "text_color": "#2c3e50",
            "font_family": "Surfer, Comic Sans MS, cursive"
        }
    }
    return themes

@app.get("/api/themes/current")
async def get_current_theme():
    """Get current theme configuration"""
    theme_file = Path("src/web/static/user_theme.json")
    if theme_file.exists():
        try:
            return json.loads(theme_file.read_text())
        except:
            pass
    # Return default theme
    themes = await get_available_themes()
    return themes["default"]

@app.post("/api/themes/apply")
async def apply_theme(theme_config: ThemeConfig):
    """Apply a theme configuration"""
    try:
        theme_file = Path("src/web/static/user_theme.json")
        theme_file.parent.mkdir(parents=True, exist_ok=True)
        theme_file.write_text(json.dumps(theme_config.dict(), indent=2))
        
        # Generate CSS file
        css_content = generate_theme_css(theme_config)
        css_file = Path("src/web/static/user_theme.css")
        css_file.write_text(css_content)
        
        return {"status": "success", "message": "Theme applied successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/themes/upload-logo")
async def upload_logo(file: UploadFile = File(...)):
    """Upload custom logo"""
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Save uploaded logo
        logo_dir = Path("src/web/static/uploads")
        logo_dir.mkdir(parents=True, exist_ok=True)
        
        logo_path = logo_dir / f"logo_{uuid.uuid4().hex[:8]}.{file.filename.split('.')[-1]}"
        with open(logo_path, "wb") as buffer:
            buffer.write(await file.read())
        
        logo_url = f"/static/uploads/{logo_path.name}"
        return {"status": "success", "logo_url": logo_url}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def generate_theme_css(theme: ThemeConfig) -> str:
    """Generate CSS from theme configuration"""
    css = f"""
/* User Theme CSS - Generated automatically */
:root {{
    --primary-color: {theme.primary_color};
    --secondary-color: {theme.secondary_color};
    --accent-color: {theme.accent_color};
    --background-color: {theme.background_color};
    --text-color: {theme.text_color};
    --font-family: {theme.font_family};
}}

body {{
    background-color: var(--background-color);
    color: var(--text-color);
    font-family: var(--font-family);
}}

/* Apply theme colors to common elements */
.btn-primary, .bg-blue-500 {{
    background-color: var(--primary-color) !important;
}}

.text-blue-500, .text-blue-600 {{
    color: var(--primary-color) !important;
}}

.border-blue-500 {{
    border-color: var(--primary-color) !important;
}}

.bg-gray-500 {{
    background-color: var(--secondary-color) !important;
}}

.text-green-500, .text-green-600 {{
    color: var(--accent-color) !important;
}}

.bg-green-500 {{
    background-color: var(--accent-color) !important;
}}
"""
    
    # Add glassmorphism effects
    if "glassmorphism" in theme.name.lower():
        css += """
/* Glassmorphism Effects */
.modal-content, .card, .sidebar {{
    backdrop-filter: blur(20px) saturate(180%);
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
}}
"""
    
    # Add neon effects for brutalism
    if "neon" in theme.name.lower():
        css += """
/* Neon Brutalism Effects */
.btn, .card, .modal-content {{
    border: 2px solid var(--primary-color);
    box-shadow: 0 0 20px var(--primary-color);
    text-shadow: 0 0 10px var(--primary-color);
}}

.btn:hover {{
    box-shadow: 0 0 30px var(--primary-color), inset 0 0 20px var(--primary-color);
}}
"""
    
    # Add luxury styling
    if "luxury" in theme.name.lower():
        css += """
/* Luxury Clean Styling */
.card, .modal-content {{
    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
    border: 1px solid #e5e5e5;
}}

.btn {{
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}}
"""
    
    # Add techy glow effects
    if "techy" in theme.name.lower():
        css += """
/* Dark Techy Glow Effects */
.card, .modal-content, .btn {{
    background: rgba(0, 255, 65, 0.05);
    border: 1px solid var(--primary-color);
    box-shadow: 0 0 15px rgba(0, 255, 65, 0.3);
}}

.text-primary {{
    text-shadow: 0 0 10px var(--primary-color);
}}
"""
    
    # Add surf zine styling
    if "surf" in theme.name.lower():
        css += """
/* Coastal Surf Zine Styling */
.card, .btn {{
    border-radius: 15px;
    transform: rotate(-1deg);
    box-shadow: 3px 3px 0px var(--accent-color);
}}

.card:nth-child(even) {{
    transform: rotate(1deg);
}}

.btn {{
    font-weight: bold;
    text-transform: lowercase;
}}
"""
    
    if theme.custom_css:
        css += f"\n/* Custom CSS */\n{theme.custom_css}"
    
    return css

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
