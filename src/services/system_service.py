"""Persistent System Service for Brebot."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from config import get_redis_client, get_default_airtable_events_table
from models.actions import SystemAction
from utils import brebot_logger


class SystemService:
    """Service for system operations backed by Redis and Airtable."""

    REDIS_CONNECTION_PREFIX = "brebot:connection:"
    REDIS_INGESTION_PREFIX = "brebot:ingestion:"
    REDIS_ALERT_LIST = "brebot:alerts"
    REDIS_CALENDAR_PREFIX = "brebot:calendar:"
    REDIS_CALENDAR_INDEX = "brebot:calendar:index"

    def __init__(self):
        self.redis = get_redis_client()
        self.events_table = get_default_airtable_events_table()
        brebot_logger.log_agent_action("SystemService", "initialized")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _log_event(self, event_type: str, details: Dict[str, Any], actor: str = "Brebot") -> None:
        if not self.events_table:
            return
        try:
            self.events_table.create(
                {
                    "Event ID": f"event_{uuid4().hex}",
                    "Type": event_type,
                    "Actor": actor,
                    "Details": json.dumps(details),
                    "Timestamp": datetime.utcnow().isoformat(),
                }
            )
        except Exception as exc:  # pragma: no cover - network failure
            brebot_logger.log_error(exc, "SystemService._log_event")

    def _set_connection_status(self, service: str, status: str) -> None:
        if not self.redis:
            return
        self.redis.set(f"{self.REDIS_CONNECTION_PREFIX}{service}", status)

    def _get_connection_status(self, service: str) -> str:
        if self.redis:
            status = self.redis.get(f"{self.REDIS_CONNECTION_PREFIX}{service}")
            if status:
                return status
        return "unknown"

    def _toggle_ingestion_state(self, service: str) -> str:
        if not self.redis:
            return "unknown"
        key = f"{self.REDIS_INGESTION_PREFIX}{service}"
        current = self.redis.get(key)
        new_state = "enabled" if current != "enabled" else "disabled"
        self.redis.set(key, new_state)
        return new_state

    def _record_alert(self, alert: Dict[str, Any]) -> None:
        if self.redis:
            self.redis.lpush(self.REDIS_ALERT_LIST, json.dumps(alert))

    def _store_calendar_event(self, event: Dict[str, Any]) -> None:
        if not self.redis:
            return
        key = f"{self.REDIS_CALENDAR_PREFIX}{event['id']}"
        self.redis.set(key, json.dumps(event))
        self.redis.sadd(self.REDIS_CALENDAR_INDEX, event["id"])

    def _delete_calendar_event(self, event_id: str) -> None:
        if not self.redis:
            return
        key = f"{self.REDIS_CALENDAR_PREFIX}{event_id}"
        self.redis.delete(key)
        self.redis.srem(self.REDIS_CALENDAR_INDEX, event_id)

    def _list_calendar_events(self) -> List[Dict[str, Any]]:
        if not self.redis:
            return []
        events: List[Dict[str, Any]] = []
        for event_id in self.redis.smembers(self.REDIS_CALENDAR_INDEX):
            raw = self.redis.get(f"{self.REDIS_CALENDAR_PREFIX}{event_id}")
            if raw:
                events.append(json.loads(raw))
        return events

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def enable_connection(self, service: str) -> Dict[str, Any]:
        if not service:
            return {"status": "error", "message": "Service name is required"}
        self._set_connection_status(service, "enabled")
        self._log_event("connection_toggle", {"service": service, "status": "enabled"})
        return {"status": "success", "message": f"Connection {service} enabled"}

    async def disable_connection(self, service: str) -> Dict[str, Any]:
        if not service:
            return {"status": "error", "message": "Service name is required"}
        self._set_connection_status(service, "disabled")
        self._log_event("connection_toggle", {"service": service, "status": "disabled"})
        return {"status": "success", "message": f"Connection {service} disabled"}

    async def health_check(self, service: str) -> Dict[str, Any]:
        status = self._get_connection_status(service)
        return {"status": "success", "health": status}

    async def toggle_ingestion(self, service: str) -> Dict[str, Any]:
        if not service:
            return {"status": "error", "message": "Service name is required"}
        state = self._toggle_ingestion_state(service)
        self._log_event("connection_toggle", {"service": service, "ingestion": state})
        return {"status": "success", "message": f"Ingestion {state} for {service}"}

    async def add_calendar_event(self, action: SystemAction) -> Dict[str, Any]:
        event_id = action.id or f"calendar_{uuid4().hex}"
        event = {
            "id": event_id,
            "service": action.service,
            "message": action.message,
            "time": action.query,
            "created_at": datetime.utcnow().isoformat(),
        }
        self._store_calendar_event(event)
        self._log_event("calendar_update", {"action": "add", "event": event})
        return {"status": "success", "event_id": event_id}

    async def update_calendar_event(self, action: SystemAction) -> Dict[str, Any]:
        if not action.id:
            return {"status": "error", "message": "Event ID is required"}
        events = {event["id"]: event for event in self._list_calendar_events()}
        event = events.get(action.id)
        if not event:
            return {"status": "error", "message": "Event not found"}

        if action.message is not None:
            event["message"] = action.message
        if action.query is not None:
            event["time"] = action.query
        event["updated_at"] = datetime.utcnow().isoformat()
        self._store_calendar_event(event)
        self._log_event("calendar_update", {"action": "update", "event": event})
        return {"status": "success", "message": "Event updated"}

    async def delete_calendar_event(self, event_id: str) -> Dict[str, Any]:
        self._delete_calendar_event(event_id)
        self._log_event("calendar_update", {"action": "delete", "event_id": event_id})
        return {"status": "success", "message": "Event deleted"}

    async def check_calendar(self, query: Optional[str] = None) -> Dict[str, Any]:
        events = self._list_calendar_events()
        if query:
            events = [event for event in events if query.lower() in (event.get("message") or "").lower()]
        return {"status": "success", "events": events}

    async def create_alert(self, action: SystemAction) -> Dict[str, Any]:
        alert_id = action.id or f"alert_{uuid4().hex}"
        alert = {
            "id": alert_id,
            "service": action.service,
            "severity": action.severity or "info",
            "message": action.message,
            "created_at": datetime.utcnow().isoformat(),
        }
        self._record_alert(alert)
        self._log_event("system_alert", {"action": "create", "alert": alert})
        return {"status": "success", "alert_id": alert_id}

    async def resolve_alert(self, alert_id: str) -> Dict[str, Any]:
        self._log_event("system_alert", {"action": "resolve", "alert_id": alert_id})
        return {"status": "success", "message": "Alert resolved"}

    async def cancel_subscription(self, action: SystemAction) -> Dict[str, Any]:
        self._log_event("system_alert", {"action": "cancel_subscription", "service": action.service})
        return {"status": "success", "message": "Subscription cancelled"}

    async def diagnose(self, action: SystemAction) -> Dict[str, Any]:
        connections: Dict[str, str] = {}
        ingestions: Dict[str, str] = {}
        if self.redis:
            for key in self.redis.scan_iter(f"{self.REDIS_CONNECTION_PREFIX}*"):
                service = key.decode().split(self.REDIS_CONNECTION_PREFIX, 1)[1] if isinstance(key, bytes) else key.split(self.REDIS_CONNECTION_PREFIX, 1)[1]
                connections[service] = self.redis.get(key)
            for key in self.redis.scan_iter(f"{self.REDIS_INGESTION_PREFIX}*"):
                service = key.decode().split(self.REDIS_INGESTION_PREFIX, 1)[1] if isinstance(key, bytes) else key.split(self.REDIS_INGESTION_PREFIX, 1)[1]
                ingestions[service] = self.redis.get(key)

        diagnosis = {
            "connections": connections,
            "ingestion": ingestions,
            "alerts_pending": self.redis.llen(self.REDIS_ALERT_LIST) if self.redis else 0,
        }

        return {"status": "success", "diagnosis": diagnosis}

    async def assist_project(self, action: SystemAction) -> Dict[str, Any]:
        self._log_event("project_assist", {"query": action.query, "service": action.service})
        return {
            "status": "success",
            "assistance": "Project assistance recorded. Detailed automation to be implemented.",
        }

    async def list_projects(self) -> Dict[str, Any]:
        return {"status": "success", "projects": []}


# Global instance
systemService = SystemService()
