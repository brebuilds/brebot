"""Storage client helpers for Brebot.

Provides centralized access to ChromaDB, Redis, and Airtable instances with
lazy initialization and basic error handling.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional, Dict
from urllib.parse import urlparse

import chromadb
from chromadb.config import Settings as ChromaSettings

from config.settings import settings
from utils import brebot_logger

try:
    import redis  # type: ignore
except ImportError:  # pragma: no cover - handled in requirements
    redis = None  # type: ignore

try:
    from pyairtable import Api
    from pyairtable.api.table import Table
except ImportError:  # pragma: no cover - handled in requirements
    Api = None  # type: ignore
    Table = None  # type: ignore

__all__ = [
    "get_chroma_client",
    "get_redis_client",
    "get_airtable_api",
    "get_airtable_table",
    "airtable_available",
]


_chroma_client: Optional[chromadb.HttpClient] = None
_redis_client: Optional["redis.Redis"] = None
_airtable_api: Optional[Api] = None
_airtable_tables: Dict[str, Table] = {}


def _parse_chroma_url(url: str) -> Dict[str, object]:
    """Parse the configured Chroma URL into connection parameters."""
    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 8000
    scheme = parsed.scheme or "http"
    return {
        "host": host,
        "port": port,
        "ssl": scheme == "https",
    }


def get_chroma_client() -> chromadb.HttpClient:
    """Return a shared ChromaDB HTTP client instance."""
    global _chroma_client
    if _chroma_client is not None:
        return _chroma_client

    try:
        params = _parse_chroma_url(settings.chroma_url)
        _chroma_client = chromadb.HttpClient(
            host=params["host"],
            port=params["port"],
            ssl=params["ssl"],
            settings=ChromaSettings(allow_reset=True, anonymized_telemetry=False),
        )
        brebot_logger.log_crew_activity(
            crew_name="Storage",
            activity="chroma_connected",
            details={"url": settings.chroma_url},
        )
    except Exception as exc:  # pragma: no cover - network failures
        brebot_logger.log_error(exc, "storage.get_chroma_client")
        raise

    return _chroma_client


def get_redis_client() -> Optional["redis.Redis"]:
    """Return a shared Redis client if configured."""
    if redis is None:
        brebot_logger.log_error(
            ImportError("redis package not installed"),
            "storage.get_redis_client",
        )
        return None

    if not settings.redis_url:
        return None

    global _redis_client
    if _redis_client is not None:
        return _redis_client

    try:
        _redis_client = redis.from_url(  # type: ignore[attr-defined]
            settings.redis_url,
            decode_responses=True,
        )
        # Perform lightweight ping to confirm connectivity
        _redis_client.ping()
        brebot_logger.log_crew_activity(
            crew_name="Storage",
            activity="redis_connected",
            details={"url": settings.redis_url},
        )
    except Exception as exc:  # pragma: no cover - connection failures
        brebot_logger.log_error(exc, "storage.get_redis_client")
        _redis_client = None

    return _redis_client


def airtable_available() -> bool:
    """Return True if Airtable credentials are present and client available."""
    return bool(Api and settings.airtable_api_key and settings.airtable_base_id)


def get_airtable_api() -> Optional[Api]:
    """Return a shared Airtable API client if configured."""
    if not airtable_available():
        return None

    global _airtable_api
    if _airtable_api is not None:
        return _airtable_api

    try:
        _airtable_api = Api(settings.airtable_api_key)  # type: ignore[arg-type]
        brebot_logger.log_crew_activity(
            crew_name="Storage",
            activity="airtable_connected",
            details={"base_id": settings.airtable_base_id},
        )
    except Exception as exc:  # pragma: no cover - auth failures
        brebot_logger.log_error(exc, "storage.get_airtable_api")
        _airtable_api = None

    return _airtable_api


def get_airtable_table(table_name: str) -> Optional[Table]:
    """Return an Airtable table client with caching."""
    api = get_airtable_api()
    if api is None or settings.airtable_base_id is None:
        return None

    cache_key = f"{settings.airtable_base_id}:{table_name}"
    if cache_key in _airtable_tables:
        return _airtable_tables[cache_key]

    if Table is None:  # pragma: no cover - import guard
        return None

    try:
        table = api.table(settings.airtable_base_id, table_name)  # type: ignore[arg-type]
        _airtable_tables[cache_key] = table
        return table
    except Exception as exc:  # pragma: no cover - runtime failures
        brebot_logger.log_error(exc, f"storage.get_airtable_table({table_name})")
        return None


@lru_cache(maxsize=None)
def get_default_airtable_task_table() -> Optional[Table]:
    """Convenience accessor for the configured Tasks table."""
    return get_airtable_table(settings.airtable_tasks_table)


@lru_cache(maxsize=None)
def get_default_airtable_events_table() -> Optional[Table]:
    """Convenience accessor for the configured SystemEvents table."""
    return get_airtable_table(settings.airtable_system_events_table)


@lru_cache(maxsize=None)
def get_default_airtable_ingestion_table() -> Optional[Table]:
    """Convenience accessor for the configured IngestionRuns table."""
    return get_airtable_table(settings.airtable_ingestion_runs_table)
