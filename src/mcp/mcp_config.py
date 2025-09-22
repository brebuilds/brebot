"""
MCP Server Configuration
Configuration settings for the Brebot MCP server.
"""

import os
from typing import Dict, Any
from pydantic import BaseSettings

class MCPSettings(BaseSettings):
    """MCP Server configuration settings."""
    
    # Server Configuration
    server_name: str = "brebot-mcp-server"
    server_version: str = "1.0.0"
    server_description: str = "Brebot MCP Server for external LLM control"
    
    # Transport Configuration
    transport_type: str = "stdio"  # stdio, sse, or http
    host: str = "localhost"
    port: int = 8001
    
    # Authentication
    enable_auth: bool = False
    auth_token: str = ""
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/mcp_server.log"
    
    # Bot Management
    max_concurrent_tasks: int = 10
    task_timeout: int = 300  # 5 minutes
    health_check_interval: int = 30  # seconds
    
    # Tool Configuration
    enable_file_operations: bool = True
    enable_marketing_tools: bool = True
    enable_web_design_tools: bool = True
    enable_system_management: bool = True
    
    class Config:
        env_prefix = "MCP_"
        env_file = ".env"

# Global settings instance
mcp_settings = MCPSettings()

# Tool categories and their configurations
TOOL_CATEGORIES = {
    "file_management": {
        "enabled": True,
        "tools": [
            "get_bot_status",
            "organize_files",
            "list_available_tools"
        ]
    },
    "content_creation": {
        "enabled": True,
        "tools": [
            "create_marketing_content",
            "design_web_element"
        ]
    },
    "bot_management": {
        "enabled": True,
        "tools": [
            "create_bot",
            "assign_task",
            "update_bot_configuration",
            "get_task_history"
        ]
    },
    "system_monitoring": {
        "enabled": True,
        "tools": [
            "get_system_health"
        ]
    }
}

# Available bot types
AVAILABLE_BOT_TYPES = [
    "file_organizer",
    "marketing",
    "web_design",
    "data_processor",
    "content_creator",
    "api_integration",
    "custom"
]

# Task types
TASK_TYPES = [
    "file_organization",
    "content_creation",
    "web_design",
    "data_processing",
    "api_integration",
    "system_maintenance",
    "custom"
]

# Priority levels
PRIORITY_LEVELS = ["low", "medium", "high", "critical"]

# Bot statuses
BOT_STATUSES = ["online", "offline", "busy", "maintenance", "error"]

def get_tool_config() -> Dict[str, Any]:
    """Get the current tool configuration."""
    return {
        "categories": TOOL_CATEGORIES,
        "bot_types": AVAILABLE_BOT_TYPES,
        "task_types": TASK_TYPES,
        "priority_levels": PRIORITY_LEVELS,
        "bot_statuses": BOT_STATUSES
    }

def is_tool_enabled(tool_name: str) -> bool:
    """Check if a specific tool is enabled."""
    for category in TOOL_CATEGORIES.values():
        if category["enabled"] and tool_name in category["tools"]:
            return True
    return False

def get_enabled_tools() -> list:
    """Get list of all enabled tools."""
    enabled_tools = []
    for category in TOOL_CATEGORIES.values():
        if category["enabled"]:
            enabled_tools.extend(category["tools"])
    return enabled_tools
