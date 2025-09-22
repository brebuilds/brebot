"""
Note Service for Brebot.
Handles note creation, updates, and management.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, Any, List
from models.actions import NoteAction
from utils.logger import brebot_logger


class NoteService:
    """Service for managing notes."""
    
    def __init__(self):
        self.notes = {}  # In-memory storage for now
        brebot_logger.log_agent_action("NoteService", "initialized")
    
    async def create(self, action: NoteAction) -> Dict[str, Any]:
        """Create a new note."""
        note_id = f"note_{len(self.notes) + 1}"
        note = {
            "id": note_id,
            "text": action.text,
            "tags": action.tags or [],
            "created_at": "2025-01-01T00:00:00Z"
        }
        self.notes[note_id] = note
        
        brebot_logger.log_agent_action("NoteService", "note_created", {"note_id": note_id})
        return {"status": "success", "note_id": note_id, "note": note}
    
    async def update(self, action: NoteAction) -> Dict[str, Any]:
        """Update an existing note."""
        if not action.id or action.id not in self.notes:
            return {"status": "error", "message": "Note not found"}
        
        note = self.notes[action.id]
        if action.text:
            note["text"] = action.text
        if action.tags:
            note["tags"] = action.tags
        
        brebot_logger.log_agent_action("NoteService", "note_updated", {"note_id": action.id})
        return {"status": "success", "note": note}
    
    async def delete(self, note_id: str) -> Dict[str, Any]:
        """Delete a note."""
        if note_id not in self.notes:
            return {"status": "error", "message": "Note not found"}
        
        del self.notes[note_id]
        brebot_logger.log_agent_action("NoteService", "note_deleted", {"note_id": note_id})
        return {"status": "success", "message": "Note deleted"}
    
    async def list(self) -> Dict[str, Any]:
        """List all notes."""
        return {"status": "success", "notes": list(self.notes.values())}


# Global instance
noteService = NoteService()
