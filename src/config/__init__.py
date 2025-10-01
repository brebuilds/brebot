"""
Configuration package for Brebot.
"""

from .settings import (
    Settings,
    load_settings,
    get_llm_config,
    get_embedding_config,
    settings,
)
from .system_prompts import (
    SystemPrompts,
    get_chat_prompt,
    get_voice_prompt,
    get_agent_prompt,
    get_system_prompt,
    get_tool_prompt,
    get_response_template,
)
from .storage import (
    get_chroma_client,
    get_redis_client,
    get_airtable_api,
    get_airtable_table,
    airtable_available,
    get_default_airtable_task_table,
    get_default_airtable_events_table,
    get_default_airtable_ingestion_table,
)

__all__ = [
    "Settings",
    "load_settings", 
    "get_llm_config",
    "get_embedding_config",
    "settings",
    "get_chroma_client",
    "get_redis_client",
    "get_airtable_api",
    "get_airtable_table",
    "airtable_available",
    "get_default_airtable_task_table",
    "get_default_airtable_events_table",
    "get_default_airtable_ingestion_table",
    "SystemPrompts",
    "get_chat_prompt",
    "get_voice_prompt", 
    "get_agent_prompt",
    "get_system_prompt",
    "get_tool_prompt",
    "get_response_template"
]
