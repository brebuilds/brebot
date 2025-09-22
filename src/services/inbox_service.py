"""
Inbox Service for Brebot.
Handles inbox notifications and management.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, Any
from models.actions import InboxAction
from utils.logger import brebot_logger


class InboxService:
    """Service for managing inbox notifications."""
    
    def __init__(self):
        self.notifications = {}
        brebot_logger.log_agent_action("InboxService", "initialized")
    
    async def notify(self, action: InboxAction) -> Dict[str, Any]:
        """Create a new notification."""
        notification_id = f"notif_{len(self.notifications) + 1}"
        notification = {
            "id": notification_id,
            "message": action.message,
            "severity": action.severity or "info",
            "created_at": "2025-01-01T00:00:00Z"
        }
        self.notifications[notification_id] = notification
        return {"status": "success", "notification_id": notification_id}
    
    async def mark_read(self, notification_id: str) -> Dict[str, Any]:
        """Mark notification as read."""
        if notification_id in self.notifications:
            self.notifications[notification_id]["read"] = True
        return {"status": "success"}
    
    async def mark_unread(self, notification_id: str) -> Dict[str, Any]:
        """Mark notification as unread."""
        if notification_id in self.notifications:
            self.notifications[notification_id]["read"] = False
        return {"status": "success"}
    
    async def pin(self, notification_id: str) -> Dict[str, Any]:
        """Pin a notification."""
        if notification_id in self.notifications:
            self.notifications[notification_id]["pinned"] = True
        return {"status": "success"}


# Global instance
inboxService = InboxService()
