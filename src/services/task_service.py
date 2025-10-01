"""Persistent Task Service for Brebot."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from config import (
    get_redis_client,
    get_default_airtable_task_table,
    get_default_airtable_events_table,
)
from models.actions import TaskAction
from utils import brebot_logger


class TaskService:
    """Service for managing tasks with Redis + Airtable persistence."""

    REDIS_TASK_PREFIX = "brebot:task:"
    REDIS_TASK_INDEX = "brebot:task_index"

    def __init__(self):
        self.redis = get_redis_client()
        self.tasks_table = get_default_airtable_task_table()
        self.events_table = get_default_airtable_events_table()
        self._fallback_tasks: Dict[str, Dict[str, Any]] = {}
        brebot_logger.log_agent_action("TaskService", "initialized")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _redis_key(self, task_id: str) -> str:
        return f"{self.REDIS_TASK_PREFIX}{task_id}"

    def _load_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        if self.redis:
            raw = self.redis.get(self._redis_key(task_id))
            if raw:
                return json.loads(raw)
        return self._fallback_tasks.get(task_id)

    def _store_task(self, task: Dict[str, Any]) -> None:
        task_id = task["id"]
        if self.redis:
            self.redis.set(self._redis_key(task_id), json.dumps(task))
            self.redis.sadd(self.REDIS_TASK_INDEX, task_id)
        else:
            self._fallback_tasks[task_id] = task

    def _remove_task(self, task_id: str) -> None:
        if self.redis:
            self.redis.delete(self._redis_key(task_id))
            self.redis.srem(self.REDIS_TASK_INDEX, task_id)
        self._fallback_tasks.pop(task_id, None)

    def _list_task_ids(self) -> List[str]:
        if self.redis:
            return list(self.redis.smembers(self.REDIS_TASK_INDEX))
        return list(self._fallback_tasks.keys())

    def _normalise_status(self, status: Optional[str]) -> str:
        if not status:
            return "not_started"
        mapping = {"done": "completed"}
        return mapping.get(status, status)

    def _normalise_priority(self, priority: Optional[str]) -> str:
        return priority or "medium"

    def _normalise_project(self, project: Optional[str]) -> str:
        return project or "Unspecified"

    def _sync_task_to_airtable(self, task: Dict[str, Any]) -> None:
        if not self.tasks_table:
            return

        fields = {
            "Task ID": task["id"],
            "Title": task.get("title") or "Untitled Task",
            "Project": self._normalise_project(task.get("project")),
            "Status": task.get("status"),
            "Priority": task.get("priority"),
            "Assigned Bot": task.get("assigned_bot"),
            "Due Date": task.get("due_date"),
            "Context": task.get("description"),
            "Result": task.get("result"),
        }

        try:
            record = self.tasks_table.first(formula=f"{{Task ID}} = '{task['id']}'")
            if record:
                self.tasks_table.update(record["id"], fields)
            else:
                self.tasks_table.create(fields)
        except Exception as exc:  # pragma: no cover - network failure
            brebot_logger.log_error(exc, "TaskService._sync_task_to_airtable")

    def _log_event(self, event_type: str, details: Dict[str, Any]) -> None:
        if not self.events_table:
            return
        try:
            self.events_table.create(
                {
                    "Event ID": f"event_{uuid4().hex}",
                    "Type": event_type,
                    "Actor": "Brebot",
                    "Details": json.dumps(details),
                    "Timestamp": datetime.utcnow().isoformat(),
                }
            )
        except Exception as exc:  # pragma: no cover - network failure
            brebot_logger.log_error(exc, "TaskService._log_event")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def create(self, action: TaskAction) -> Dict[str, Any]:
        """Create a new task."""
        task_id = action.id or f"task_{uuid4().hex}"
        now = datetime.utcnow().isoformat()

        task = {
            "id": task_id,
            "title": action.title or "Untitled Task",
            "description": action.description or "",
            "project": self._normalise_project(action.project),
            "due_date": action.due_date,
            "assigned_bot": action.assigned_bot,
            "priority": self._normalise_priority(action.priority),
            "status": self._normalise_status(action.status),
            "created_at": now,
            "updated_at": now,
            "comments": [],
            "result": None,
        }

        self._store_task(task)
        self._sync_task_to_airtable(task)
        self._log_event("task_update", {"action": "create", "task_id": task_id})

        brebot_logger.log_agent_action("TaskService", "task_created", {"task_id": task_id})
        return {"status": "success", "task_id": task_id, "task": task}

    async def update(self, action: TaskAction) -> Dict[str, Any]:
        """Update an existing task."""
        if not action.id:
            return {"status": "error", "message": "Task ID is required"}

        task = self._load_task(action.id)
        if not task:
            return {"status": "error", "message": "Task not found"}

        if action.title:
            task["title"] = action.title
        if action.description is not None:
            task["description"] = action.description
        if action.project is not None:
            task["project"] = self._normalise_project(action.project)
        if action.due_date is not None:
            task["due_date"] = action.due_date
        if action.assigned_bot is not None:
            task["assigned_bot"] = action.assigned_bot
        if action.priority is not None:
            task["priority"] = self._normalise_priority(action.priority)
        if action.status is not None:
            task["status"] = self._normalise_status(action.status)
        if action.comment:
            task.setdefault("comments", []).append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "comment": action.comment,
                }
            )
        task["updated_at"] = datetime.utcnow().isoformat()

        self._store_task(task)
        self._sync_task_to_airtable(task)
        self._log_event("task_update", {"action": "update", "task_id": action.id})

        brebot_logger.log_agent_action("TaskService", "task_updated", {"task_id": action.id})
        return {"status": "success", "task": task}

    async def delete(self, task_id: str) -> Dict[str, Any]:
        """Delete a task."""
        task = self._load_task(task_id)
        if not task:
            return {"status": "error", "message": "Task not found"}

        task["status"] = "cancelled"
        task["result"] = task.get("result") or "Task cancelled"
        self._sync_task_to_airtable(task)
        self._remove_task(task_id)
        self._log_event("task_update", {"action": "delete", "task_id": task_id})

        brebot_logger.log_agent_action("TaskService", "task_deleted", {"task_id": task_id})
        return {"status": "success", "message": "Task deleted"}

    async def list(self) -> Dict[str, Any]:
        """List all tasks currently tracked."""
        tasks: List[Dict[str, Any]] = []
        for task_id in self._list_task_ids():
            task = self._load_task(task_id)
            if task:
                tasks.append(task)
        return {"status": "success", "tasks": tasks}


# Global instance
taskService = TaskService()
