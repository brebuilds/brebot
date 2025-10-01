"""
Comprehensive Activity Logging Service for BreBot Platform Integrations
Tracks all interactions across platforms with detailed audit trails
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import aiofiles
import hashlib
from pathlib import Path

from utils.logger import brebot_logger


class ActivityType(Enum):
    """Types of activities that can be logged."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    CREATE = "create"
    UPDATE = "update"
    EXECUTE = "execute"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    BROWSE = "browse"
    EMAIL_SEND = "email_send"
    EMAIL_READ = "email_read"
    API_CALL = "api_call"
    FILE_ACCESS = "file_access"
    AUTOMATION = "automation"


class Platform(Enum):
    """Supported platforms."""
    DROPBOX = "dropbox"
    ETSY = "etsy"
    SHOPIFY = "shopify"
    AIRTABLE = "airtable"
    NOTION = "notion"
    CANVA = "canva"
    FIGMA = "figma"
    DESKTOP = "desktop"
    BROWSER = "browser"
    EMAIL = "email"
    N8N = "n8n"
    SYSTEM = "system"


@dataclass
class ActivityRecord:
    """Individual activity record."""
    id: str
    timestamp: str
    platform: str
    activity_type: str
    agent_name: str
    description: str
    details: Dict[str, Any]
    resource_path: Optional[str] = None
    resource_id: Optional[str] = None
    data_size: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    session_id: Optional[str] = None
    user_context: Optional[str] = None


class ActivityLogger:
    """Comprehensive activity logging service."""
    
    def __init__(self, db_path: str = "data/activity_logs.db", log_dir: str = "data/activity_logs"):
        """Initialize activity logger."""
        self.db_path = Path(db_path)
        self.log_dir = Path(log_dir)
        self.session_id = self._generate_session_id()
        
        # Ensure directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        brebot_logger.log_agent_action(
            agent_name="ActivityLogger",
            action="initialized",
            details={
                "db_path": str(self.db_path),
                "log_dir": str(self.log_dir),
                "session_id": self.session_id
            }
        )
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        timestamp = datetime.now(timezone.utc).isoformat()
        return hashlib.md5(f"brebot_session_{timestamp}".encode()).hexdigest()[:12]
    
    def _init_database(self):
        """Initialize SQLite database for activity logs."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS activities (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    activity_type TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    details TEXT NOT NULL,
                    resource_path TEXT,
                    resource_id TEXT,
                    data_size INTEGER,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    session_id TEXT,
                    user_context TEXT
                )
            """)
            
            # Create indexes for common queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON activities(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_platform ON activities(platform)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_agent ON activities(agent_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON activities(session_id)")
            
            conn.commit()
    
    async def log_activity(
        self,
        platform: Union[Platform, str],
        activity_type: Union[ActivityType, str],
        agent_name: str,
        description: str,
        details: Dict[str, Any] = None,
        resource_path: Optional[str] = None,
        resource_id: Optional[str] = None,
        data_size: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        user_context: Optional[str] = None
    ) -> str:
        """Log an activity to database and file system."""
        
        # Generate unique activity ID
        timestamp = datetime.now(timezone.utc)
        activity_id = hashlib.md5(
            f"{timestamp.isoformat()}_{platform}_{activity_type}_{agent_name}".encode()
        ).hexdigest()
        
        # Create activity record
        record = ActivityRecord(
            id=activity_id,
            timestamp=timestamp.isoformat(),
            platform=platform.value if isinstance(platform, Platform) else platform,
            activity_type=activity_type.value if isinstance(activity_type, ActivityType) else activity_type,
            agent_name=agent_name,
            description=description,
            details=details or {},
            resource_path=resource_path,
            resource_id=resource_id,
            data_size=data_size,
            success=success,
            error_message=error_message,
            session_id=self.session_id,
            user_context=user_context
        )
        
        # Store in database
        await self._store_in_database(record)
        
        # Store detailed log file
        await self._store_log_file(record)
        
        # Log to BreBot logger as well
        brebot_logger.log_agent_action(
            agent_name=agent_name,
            action=f"{platform}_{activity_type}",
            details={
                "activity_id": activity_id,
                "platform": record.platform,
                "description": description,
                "success": success,
                "resource_path": resource_path,
                "data_size": data_size
            }
        )
        
        return activity_id
    
    async def _store_in_database(self, record: ActivityRecord):
        """Store activity record in SQLite database."""
        def _insert_record():
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO activities (
                        id, timestamp, platform, activity_type, agent_name,
                        description, details, resource_path, resource_id,
                        data_size, success, error_message, session_id, user_context
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.id, record.timestamp, record.platform, record.activity_type,
                    record.agent_name, record.description, json.dumps(record.details),
                    record.resource_path, record.resource_id, record.data_size,
                    record.success, record.error_message, record.session_id, record.user_context
                ))
                conn.commit()
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _insert_record)
    
    async def _store_log_file(self, record: ActivityRecord):
        """Store detailed activity log in JSON file."""
        # Organize logs by date and platform
        date_str = datetime.fromisoformat(record.timestamp.replace('Z', '+00:00')).strftime('%Y-%m-%d')
        platform_dir = self.log_dir / record.platform / date_str
        platform_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = platform_dir / f"{record.id}.json"
        
        async with aiofiles.open(log_file, 'w') as f:
            await f.write(json.dumps(asdict(record), indent=2, default=str))
    
    async def get_activities(
        self,
        platform: Optional[str] = None,
        agent_name: Optional[str] = None,
        activity_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ActivityRecord]:
        """Query activities with filters."""
        
        def _query_activities():
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                query = "SELECT * FROM activities WHERE 1=1"
                params = []
                
                if platform:
                    query += " AND platform = ?"
                    params.append(platform)
                
                if agent_name:
                    query += " AND agent_name = ?"
                    params.append(agent_name)
                
                if activity_type:
                    query += " AND activity_type = ?"
                    params.append(activity_type)
                
                if start_time:
                    query += " AND timestamp >= ?"
                    params.append(start_time.isoformat())
                
                if end_time:
                    query += " AND timestamp <= ?"
                    params.append(end_time.isoformat())
                
                query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                rows = conn.execute(query, params).fetchall()
                
                activities = []
                for row in rows:
                    activity = ActivityRecord(
                        id=row['id'],
                        timestamp=row['timestamp'],
                        platform=row['platform'],
                        activity_type=row['activity_type'],
                        agent_name=row['agent_name'],
                        description=row['description'],
                        details=json.loads(row['details']) if row['details'] else {},
                        resource_path=row['resource_path'],
                        resource_id=row['resource_id'],
                        data_size=row['data_size'],
                        success=bool(row['success']),
                        error_message=row['error_message'],
                        session_id=row['session_id'],
                        user_context=row['user_context']
                    )
                    activities.append(activity)
                
                return activities
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _query_activities)
    
    async def get_activity_summary(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get summary statistics of activities."""
        
        def _get_summary():
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        platform,
                        activity_type,
                        agent_name,
                        COUNT(*) as count,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                        SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed,
                        SUM(COALESCE(data_size, 0)) as total_data_size
                    FROM activities 
                    WHERE 1=1
                """
                params = []
                
                if start_time:
                    query += " AND timestamp >= ?"
                    params.append(start_time.isoformat())
                
                if end_time:
                    query += " AND timestamp <= ?"
                    params.append(end_time.isoformat())
                
                query += " GROUP BY platform, activity_type, agent_name"
                
                rows = conn.execute(query, params).fetchall()
                
                summary = {
                    "total_activities": 0,
                    "platforms": {},
                    "activity_types": {},
                    "agents": {},
                    "success_rate": 0,
                    "total_data_processed": 0
                }
                
                total_count = 0
                total_successful = 0
                
                for row in rows:
                    platform, activity_type, agent_name, count, successful, failed, data_size = row
                    
                    total_count += count
                    total_successful += successful
                    summary["total_data_processed"] += data_size or 0
                    
                    # Platform stats
                    if platform not in summary["platforms"]:
                        summary["platforms"][platform] = {"count": 0, "successful": 0, "failed": 0}
                    summary["platforms"][platform]["count"] += count
                    summary["platforms"][platform]["successful"] += successful
                    summary["platforms"][platform]["failed"] += failed
                    
                    # Activity type stats
                    if activity_type not in summary["activity_types"]:
                        summary["activity_types"][activity_type] = {"count": 0, "successful": 0, "failed": 0}
                    summary["activity_types"][activity_type]["count"] += count
                    summary["activity_types"][activity_type]["successful"] += successful
                    summary["activity_types"][activity_type]["failed"] += failed
                    
                    # Agent stats
                    if agent_name not in summary["agents"]:
                        summary["agents"][agent_name] = {"count": 0, "successful": 0, "failed": 0}
                    summary["agents"][agent_name]["count"] += count
                    summary["agents"][agent_name]["successful"] += successful
                    summary["agents"][agent_name]["failed"] += failed
                
                summary["total_activities"] = total_count
                summary["success_rate"] = (total_successful / total_count * 100) if total_count > 0 else 0
                
                return summary
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get_summary)
    
    async def export_activities(
        self,
        format_type: str = "json",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        platform: Optional[str] = None
    ) -> str:
        """Export activities to file."""
        
        activities = await self.get_activities(
            platform=platform,
            start_time=start_time,
            end_time=end_time,
            limit=10000  # Large limit for export
        )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"activity_export_{timestamp}.{format_type}"
        export_path = self.log_dir / "exports" / filename
        export_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format_type == "json":
            export_data = [asdict(activity) for activity in activities]
            async with aiofiles.open(export_path, 'w') as f:
                await f.write(json.dumps(export_data, indent=2, default=str))
        elif format_type == "csv":
            import csv
            import io
            
            output = io.StringIO()
            if activities:
                fieldnames = list(asdict(activities[0]).keys())
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                for activity in activities:
                    row = asdict(activity)
                    # Convert complex fields to JSON strings
                    row['details'] = json.dumps(row['details'])
                    writer.writerow(row)
            
            async with aiofiles.open(export_path, 'w') as f:
                await f.write(output.getvalue())
        
        return str(export_path)


# Global activity logger instance
activity_logger: Optional[ActivityLogger] = None

def initialize_activity_logger(db_path: str = "data/activity_logs.db", log_dir: str = "data/activity_logs") -> ActivityLogger:
    """Initialize the global activity logger instance."""
    global activity_logger
    activity_logger = ActivityLogger(db_path, log_dir)
    return activity_logger

def get_activity_logger() -> Optional[ActivityLogger]:
    """Get the global activity logger instance."""
    return activity_logger

async def log_platform_activity(
    platform: Union[Platform, str],
    activity_type: Union[ActivityType, str],
    agent_name: str,
    description: str,
    **kwargs
) -> Optional[str]:
    """Convenience function to log platform activity."""
    logger = get_activity_logger()
    if logger:
        return await logger.log_activity(
            platform=platform,
            activity_type=activity_type,
            agent_name=agent_name,
            description=description,
            **kwargs
        )
    return None