"""
Memory Service for Brebot.
Handles memory storage, updates, and retrieval.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, Any, List
from models.actions import MemoryAction
from utils.logger import brebot_logger


class MemoryService:
    """Service for managing memory/knowledge storage."""
    
    def __init__(self):
        self.memories = {}  # In-memory storage for now
        brebot_logger.log_agent_action("MemoryService", "initialized")
    
    async def add(self, action: MemoryAction) -> Dict[str, Any]:
        """Add a new memory."""
        memory_id = f"memory_{len(self.memories) + 1}"
        memory = {
            "id": memory_id,
            "summary": action.summary,
            "tags": action.tags or [],
            "created_at": "2025-01-01T00:00:00Z"
        }
        self.memories[memory_id] = memory
        
        brebot_logger.log_agent_action("MemoryService", "memory_added", {"memory_id": memory_id})
        return {"status": "success", "memory_id": memory_id, "memory": memory}
    
    async def update(self, action: MemoryAction) -> Dict[str, Any]:
        """Update an existing memory."""
        if not action.id or action.id not in self.memories:
            return {"status": "error", "message": "Memory not found"}
        
        memory = self.memories[action.id]
        if action.summary:
            memory["summary"] = action.summary
        if action.tags:
            memory["tags"] = action.tags
        
        brebot_logger.log_agent_action("MemoryService", "memory_updated", {"memory_id": action.id})
        return {"status": "success", "memory": memory}
    
    async def delete(self, memory_id: str) -> Dict[str, Any]:
        """Delete a memory."""
        if memory_id not in self.memories:
            return {"status": "error", "message": "Memory not found"}
        
        del self.memories[memory_id]
        brebot_logger.log_agent_action("MemoryService", "memory_deleted", {"memory_id": memory_id})
        return {"status": "success", "message": "Memory deleted"}
    
    async def search(self, query: str) -> Dict[str, Any]:
        """Search memories by query."""
        # Simple text search for now
        results = []
        for memory in self.memories.values():
            if query.lower() in memory["summary"].lower():
                results.append(memory)
        
        brebot_logger.log_agent_action("MemoryService", "memory_searched", {"query": query, "results_count": len(results)})
        return {"status": "success", "results": results}


# Global instance
memoryService = MemoryService()
