"""Persistent Memory Service for Brebot."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from chromadb.api import Collection

from config import get_chroma_client
from utils import brebot_logger
from models.actions import MemoryAction


class MemoryService:
    """Service for managing knowledge storage backed by ChromaDB with graceful fallback."""

    COLLECTION_NAME = "brebot_memories"

    def __init__(self):
        self.client: Optional[object] = None
        self.collection: Optional[Collection] = None
        self._fallback_store: Dict[str, Dict[str, Any]] = {}
        self._fallback_reason: Optional[str] = None
        self._initialise_backend()
        brebot_logger.log_agent_action(
            "MemoryService",
            "initialized",
            {"backend": "chroma" if self.collection else "in-memory"},
        )

    def _initialise_backend(self) -> bool:
        """Attempt to connect to ChromaDB, falling back to in-memory storage on failure."""
        if self.collection is not None:
            return True

        try:
            self.client = get_chroma_client()
            self.collection = self.client.get_or_create_collection(name=self.COLLECTION_NAME)
            self._fallback_reason = None
            return True
        except Exception as exc:  # pragma: no cover - connection failure
            if self._fallback_reason is None:
                # Only log the first failure loudly to avoid log spam when offline
                brebot_logger.log_error(exc, "MemoryService._initialise_backend")
            self.collection = None
            self.client = None
            self._fallback_reason = str(exc)
            return False

    def _build_memory_payload(self, memory_id: str, summary: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"id": memory_id, "summary": summary}
        payload.update(metadata)
        return payload

    def _use_fallback(self) -> bool:
        return not self._initialise_backend()

    async def add(self, action: MemoryAction) -> Dict[str, Any]:
        """Add a new memory to the knowledge store."""
        if not action.summary:
            return {"status": "error", "message": "Summary is required"}

        memory_id = action.id or f"memory_{uuid4().hex}"
        metadata = {
            "tags": action.tags or [],
            "domain": action.domain,
            "project": action.project,
            "source_type": action.source_type,
            "source_path": action.source_path,
            "created_at": datetime.utcnow().isoformat(),
        }
        if action.metadata:
            metadata.update(action.metadata)

        if self._use_fallback():
            payload = self._build_memory_payload(memory_id, action.summary, metadata)
            self._fallback_store[memory_id] = payload
            brebot_logger.log_agent_action(
                "MemoryService",
                "memory_added_fallback",
                {"memory_id": memory_id},
            )
            return {"status": "success", "memory_id": memory_id, "memory": payload, "storage": "memory"}

        try:
            assert self.collection is not None  # for type checkers
            self.collection.add(
                ids=[memory_id],
                documents=[action.summary],
                metadatas=[metadata],
            )
            brebot_logger.log_agent_action(
                "MemoryService",
                "memory_added",
                {"memory_id": memory_id, "tags": metadata["tags"]},
            )
            return {
                "status": "success",
                "memory_id": memory_id,
                "memory": self._build_memory_payload(memory_id, action.summary, metadata),
            }
        except Exception as exc:  # pragma: no cover - storage failure
            brebot_logger.log_error(exc, "MemoryService.add")
            return {"status": "error", "message": str(exc)}

    async def update(self, action: MemoryAction) -> Dict[str, Any]:
        """Update an existing memory."""
        if not action.id:
            return {"status": "error", "message": "Memory ID is required"}

        if self._use_fallback():
            memory = self._fallback_store.get(action.id)
            if not memory:
                return {"status": "error", "message": "Memory not found"}

            if action.summary:
                memory["summary"] = action.summary
            if action.tags is not None:
                memory["tags"] = action.tags
            if action.domain is not None:
                memory["domain"] = action.domain
            if action.project is not None:
                memory["project"] = action.project
            if action.source_type is not None:
                memory["source_type"] = action.source_type
            if action.source_path is not None:
                memory["source_path"] = action.source_path
            if action.metadata:
                memory.update(action.metadata)
            memory["updated_at"] = datetime.utcnow().isoformat()
            brebot_logger.log_agent_action(
                "MemoryService",
                "memory_updated_fallback",
                {"memory_id": action.id},
            )
            return {"status": "success", "memory": memory}

        try:
            assert self.collection is not None
            existing = self.collection.get(ids=[action.id], include=["documents", "metadatas"])
            if not existing.get("ids"):
                return {"status": "error", "message": "Memory not found"}

            document = existing["documents"][0]
            metadata = existing["metadatas"][0] or {}

            if action.summary:
                document = action.summary
            if action.tags is not None:
                metadata["tags"] = action.tags
            if action.domain is not None:
                metadata["domain"] = action.domain
            if action.project is not None:
                metadata["project"] = action.project
            if action.source_type is not None:
                metadata["source_type"] = action.source_type
            if action.source_path is not None:
                metadata["source_path"] = action.source_path
            if action.metadata:
                metadata.update(action.metadata)
            metadata["updated_at"] = datetime.utcnow().isoformat()

            self.collection.update(
                ids=[action.id],
                documents=[document],
                metadatas=[metadata],
            )

            brebot_logger.log_agent_action(
                "MemoryService",
                "memory_updated",
                {"memory_id": action.id},
            )
            return {
                "status": "success",
                "memory": self._build_memory_payload(action.id, document, metadata),
            }
        except Exception as exc:  # pragma: no cover - storage failure
            brebot_logger.log_error(exc, "MemoryService.update")
            return {"status": "error", "message": str(exc)}

    async def delete(self, memory_id: str) -> Dict[str, Any]:
        """Delete a memory from the collection."""
        if not memory_id:
            return {"status": "error", "message": "Memory ID is required"}

        if self._use_fallback():
            removed = self._fallback_store.pop(memory_id, None)
            if not removed:
                return {"status": "error", "message": "Memory not found"}
            brebot_logger.log_agent_action(
                "MemoryService",
                "memory_deleted_fallback",
                {"memory_id": memory_id},
            )
            return {"status": "success", "message": "Memory deleted"}

        try:
            assert self.collection is not None
            self.collection.delete(ids=[memory_id])
            brebot_logger.log_agent_action(
                "MemoryService",
                "memory_deleted",
                {"memory_id": memory_id},
            )
            return {"status": "success", "message": "Memory deleted"}
        except Exception as exc:  # pragma: no cover - storage failure
            brebot_logger.log_error(exc, "MemoryService.delete")
            return {"status": "error", "message": str(exc)}

    async def search(
        self,
        query: str,
        k: int = 5,
        tags: Optional[List[str]] = None,
        domain: Optional[str] = None,
        project: Optional[str] = None,
        source_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Search memories using semantic similarity."""
        if not query:
            return {"status": "error", "message": "Query is required"}

        where: Dict[str, Any] = {}
        if tags:
            where = {"tags": {"$contains": tags}}
        if domain:
            where.setdefault("domain", domain)
        if project:
            where.setdefault("project", project)
        if source_type:
            where.setdefault("source_type", source_type)

        if self._use_fallback():
            results = []
            query_lower = query.lower()
            required_tags = tags or []
            for memory in self._fallback_store.values():
                summary = memory.get("summary", "")
                memory_tags = memory.get("tags", []) or []
                domain_match = (not domain) or memory.get("domain") == domain
                project_match = (not project) or memory.get("project") == project
                source_type_match = (not source_type) or memory.get("source_type") == source_type
                tag_match = (not required_tags) or all(tag in memory_tags for tag in required_tags)
                if not (domain_match and project_match and source_type_match and tag_match):
                    continue
                if query_lower in summary.lower():
                    meta = {
                        key: value
                        for key, value in memory.items()
                        if key not in {"id", "summary"}
                    }
                    results.append(
                        {
                            "id": memory["id"],
                            "summary": summary,
                            "metadata": meta,
                            "score": None,
                        }
                    )
            brebot_logger.log_agent_action(
                "MemoryService",
                "memory_searched_fallback",
                {"query": query, "results_count": len(results)},
            )
            return {"status": "success", "results": results[:k], "storage": "memory"}

        try:
            assert self.collection is not None
            results = self.collection.query(
                query_texts=[query],
                n_results=k,
                where=where or None,
                include=["documents", "metadatas", "distances"],
            )

            formatted = []
            ids = results.get("ids", [[]])[0]
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            for idx, memory_id in enumerate(ids):
                formatted.append(
                    {
                        "id": memory_id,
                        "summary": documents[idx] if idx < len(documents) else "",
                        "metadata": metadatas[idx] if idx < len(metadatas) else {},
                        "score": distances[idx] if idx < len(distances) else None,
                    }
                )

            brebot_logger.log_agent_action(
                "MemoryService",
                "memory_searched",
                {"query": query, "results_count": len(formatted)},
            )
            return {"status": "success", "results": formatted}
        except Exception as exc:  # pragma: no cover - storage failure
            brebot_logger.log_error(exc, "MemoryService.search")
            return {"status": "error", "message": str(exc)}


# Global instance
memoryService = MemoryService()
