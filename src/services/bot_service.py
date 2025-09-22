"""
Bot Service for Brebot.
Handles bot creation, updates, and management.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, Any
from models.actions import BotAction
from utils.logger import brebot_logger


class BotService:
    """Service for managing bots."""
    
    def __init__(self):
        self.bots = {}
        brebot_logger.log_agent_action("BotService", "initialized")
    
    async def create(self, action: BotAction) -> Dict[str, Any]:
        """Create a new bot."""
        bot_id = action.id or f"bot_{len(self.bots) + 1}"
        bot = {
            "id": bot_id,
            "name": action.name,
            "role": action.role,
            "responsibilities": action.responsibilities or [],
            "voice_id": action.voice_id,
            "provider": action.provider,
            "created_at": "2025-01-01T00:00:00Z"
        }
        self.bots[bot_id] = bot
        return {"status": "success", "bot_id": bot_id, "bot": bot}
    
    async def update(self, action: BotAction) -> Dict[str, Any]:
        """Update a bot."""
        if not action.id or action.id not in self.bots:
            return {"status": "error", "message": "Bot not found"}
        
        bot = self.bots[action.id]
        if action.name:
            bot["name"] = action.name
        if action.role:
            bot["role"] = action.role
        if action.responsibilities:
            bot["responsibilities"] = action.responsibilities
        if action.voice_id:
            bot["voice_id"] = action.voice_id
        if action.provider:
            bot["provider"] = action.provider
        
        return {"status": "success", "bot": bot}
    
    async def delete(self, bot_id: str) -> Dict[str, Any]:
        """Delete a bot."""
        if bot_id in self.bots:
            del self.bots[bot_id]
        return {"status": "success", "message": "Bot deleted"}
    
    async def train(self, action: BotAction) -> Dict[str, Any]:
        """Train a bot."""
        return {"status": "success", "message": "Bot training started"}
    
    async def assign_task(self, action: BotAction) -> Dict[str, Any]:
        """Assign a task to a bot."""
        return {"status": "success", "message": f"Task assigned to bot {action.id}"}
    
    async def list(self) -> Dict[str, Any]:
        """List all bots."""
        return {"status": "success", "bots": list(self.bots.values())}


# Global instance
botService = BotService()
