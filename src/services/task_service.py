"""
Task Service for Brebot.
Handles task creation, updates, and management.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, Any, List
from models.actions import TaskAction
from utils.logger import brebot_logger


class TaskService:
    """Service for managing tasks."""
    
    def __init__(self):
        self.tasks = {}  # In-memory storage for now
        brebot_logger.log_agent_action("TaskService", "initialized")
    
    async def create(self, action: TaskAction) -> Dict[str, Any]:
        """Create a new task."""
        task_id = f"task_{len(self.tasks) + 1}"
        task = {
            "id": task_id,
            "title": action.title,
            "description": action.description,
            "due_date": action.due_date,
            "assigned_bot": action.assigned_bot,
            "priority": action.priority or "medium",
            "status": action.status or "not_started",
            "created_at": "2025-01-01T00:00:00Z"
        }
        self.tasks[task_id] = task
        
        brebot_logger.log_agent_action("TaskService", "task_created", {"task_id": task_id})
        return {"status": "success", "task_id": task_id, "task": task}
    
    async def update(self, action: TaskAction) -> Dict[str, Any]:
        """Update an existing task."""
        if not action.id or action.id not in self.tasks:
            return {"status": "error", "message": "Task not found"}
        
        task = self.tasks[action.id]
        if action.title:
            task["title"] = action.title
        if action.description:
            task["description"] = action.description
        if action.due_date:
            task["due_date"] = action.due_date
        if action.assigned_bot:
            task["assigned_bot"] = action.assigned_bot
        if action.priority:
            task["priority"] = action.priority
        if action.status:
            task["status"] = action.status
        
        brebot_logger.log_agent_action("TaskService", "task_updated", {"task_id": action.id})
        return {"status": "success", "task": task}
    
    async def delete(self, task_id: str) -> Dict[str, Any]:
        """Delete a task."""
        if task_id not in self.tasks:
            return {"status": "error", "message": "Task not found"}
        
        del self.tasks[task_id]
        brebot_logger.log_agent_action("TaskService", "task_deleted", {"task_id": task_id})
        return {"status": "success", "message": "Task deleted"}
    
    async def list(self) -> Dict[str, Any]:
        """List all tasks."""
        return {"status": "success", "tasks": list(self.tasks.values())}


# Global instance
taskService = TaskService()
