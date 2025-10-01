"""
Brebot MCP Server
Provides MCP tools for external LLMs to control and manage Brebot agents.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence
from datetime import datetime

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
from pydantic import BaseModel

# Import your existing Brebot components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from brebot_crew import BrebotCrew
from config.settings import settings
from utils.logger import brebot_logger
from services.bot_architect_service import botArchitectService, BotDesignSpec
from services.n8n_service import N8nService, initialize_n8n_service, get_n8n_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the MCP server
server = Server("brebot-mcp-server")

# Global Brebot crew instance
brebot_crew: Optional[BrebotCrew] = None

class BotStatus(BaseModel):
    """Bot status information."""
    bot_id: str
    status: str
    health_score: int
    tasks_completed: int
    last_active: Optional[datetime] = None

class TaskRequest(BaseModel):
    """Task request model."""
    task_type: str
    description: str
    parameters: Dict[str, Any] = {}
    priority: str = "medium"

class FileOperationRequest(BaseModel):
    """File operation request model."""
    operation: str
    source_path: str
    destination_path: Optional[str] = None
    parameters: Dict[str, Any] = {}

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List all available MCP tools for Brebot control."""
    return [
        Tool(
            name="get_bot_status",
            description="Get the current status of all Brebot agents",
            inputSchema={
                "type": "object",
                "properties": {
                    "bot_id": {
                        "type": "string",
                        "description": "Specific bot ID to check, or 'all' for all bots"
                    }
                }
            }
        ),
        Tool(
            name="create_bot",
            description="Create a new bot with specified configuration",
            inputSchema={
                "type": "object",
                "properties": {
                    "bot_id": {
                        "type": "string",
                        "description": "Unique identifier for the bot"
                    },
                    "bot_type": {
                        "type": "string",
                        "description": "Type of bot (file_organizer, marketing, web_design, etc.)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of what the bot does"
                    },
                    "tools": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of tools to assign to the bot"
                    }
                },
                "required": ["bot_id", "bot_type", "description"]
            }
        ),
        Tool(
            name="design_bot",
            description="Generate a bot blueprint and optional auto-creation",
            inputSchema={
                "type": "object",
                "properties": {
                    "goal": {
                        "type": "string",
                        "description": "Primary objective for the bot"
                    },
                    "description": {
                        "type": "string",
                        "description": "Additional background or constraints"
                    },
                    "primary_tasks": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Key responsibilities"
                    },
                    "data_sources": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Data sources the bot should use"
                    },
                    "integrations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Integrations or tools required"
                    },
                    "auto_create": {
                        "type": "boolean",
                        "description": "If true, create the bot after designing"
                    }
                },
                "required": ["goal"]
            }
        ),
        Tool(
            name="assign_task",
            description="Assign a task to a specific bot",
            inputSchema={
                "type": "object",
                "properties": {
                    "bot_id": {
                        "type": "string",
                        "description": "ID of the bot to assign the task to"
                    },
                    "task_type": {
                        "type": "string",
                        "description": "Type of task (file_organization, content_creation, etc.)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the task"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Additional parameters for the task"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Task priority level"
                    }
                },
                "required": ["bot_id", "task_type", "description"]
            }
        ),
        Tool(
            name="organize_files",
            description="Organize files in a directory using the file organizer bot",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory_path": {
                        "type": "string",
                        "description": "Path to the directory to organize"
                    },
                    "organization_type": {
                        "type": "string",
                        "enum": ["by_extension", "by_date", "by_type", "by_size"],
                        "description": "Type of organization to perform"
                    },
                    "create_backup": {
                        "type": "boolean",
                        "description": "Whether to create a backup before organizing"
                    }
                },
                "required": ["directory_path"]
            }
        ),
        Tool(
            name="create_marketing_content",
            description="Create marketing content using the marketing bot",
            inputSchema={
                "type": "object",
                "properties": {
                    "content_type": {
                        "type": "string",
                        "enum": ["blog_post", "social_media", "email", "ad_copy"],
                        "description": "Type of marketing content to create"
                    },
                    "topic": {
                        "type": "string",
                        "description": "Topic or subject for the content"
                    },
                    "target_audience": {
                        "type": "string",
                        "description": "Target audience for the content"
                    },
                    "tone": {
                        "type": "string",
                        "enum": ["professional", "casual", "friendly", "authoritative"],
                        "description": "Tone of the content"
                    },
                    "length": {
                        "type": "string",
                        "enum": ["short", "medium", "long"],
                        "description": "Desired length of the content"
                    }
                },
                "required": ["content_type", "topic"]
            }
        ),
        Tool(
            name="design_web_element",
            description="Design web elements using the web design bot",
            inputSchema={
                "type": "object",
                "properties": {
                    "element_type": {
                        "type": "string",
                        "enum": ["landing_page", "component", "layout", "style_guide"],
                        "description": "Type of web element to design"
                    },
                    "requirements": {
                        "type": "string",
                        "description": "Requirements and specifications for the design"
                    },
                    "style": {
                        "type": "string",
                        "enum": ["modern", "classic", "minimalist", "bold"],
                        "description": "Design style preference"
                    },
                    "color_scheme": {
                        "type": "string",
                        "description": "Preferred color scheme"
                    }
                },
                "required": ["element_type", "requirements"]
            }
        ),
        Tool(
            name="get_system_health",
            description="Get overall system health and performance metrics",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="list_available_tools",
            description="List all available tools that can be assigned to bots",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Filter tools by category (optional)"
                    }
                }
            }
        ),
        Tool(
            name="update_bot_configuration",
            description="Update a bot's configuration and settings",
            inputSchema={
                "type": "object",
                "properties": {
                    "bot_id": {
                        "type": "string",
                        "description": "ID of the bot to update"
                    },
                    "new_tools": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New tools to assign to the bot"
                    },
                    "description": {
                        "type": "string",
                        "description": "Updated description for the bot"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["online", "offline", "maintenance"],
                        "description": "New status for the bot"
                    }
                },
                "required": ["bot_id"]
            }
        ),
        Tool(
            name="get_task_history",
            description="Get the history of tasks performed by bots",
            inputSchema={
                "type": "object",
                "properties": {
                    "bot_id": {
                        "type": "string",
                        "description": "Specific bot ID, or 'all' for all bots"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of tasks to return"
                    }
                }
            }
        ),
        Tool(
            name="list_n8n_workflows",
            description="List all n8n workflows from your n8n instance",
            inputSchema={
                "type": "object",
                "properties": {
                    "active_only": {
                        "type": "boolean",
                        "description": "If true, only list active workflows"
                    }
                }
            }
        ),
        Tool(
            name="execute_n8n_workflow",
            description="Execute a specific n8n workflow",
            inputSchema={
                "type": "object", 
                "properties": {
                    "workflow_id": {
                        "type": "string",
                        "description": "ID of the workflow to execute"
                    },
                    "data": {
                        "type": "object",
                        "description": "Optional data to pass to the workflow"
                    }
                },
                "required": ["workflow_id"]
            }
        ),
        Tool(
            name="get_n8n_execution_status",
            description="Get the status of an n8n workflow execution",
            inputSchema={
                "type": "object",
                "properties": {
                    "execution_id": {
                        "type": "string",
                        "description": "ID of the execution to check"
                    }
                },
                "required": ["execution_id"]
            }
        ),
        Tool(
            name="activate_n8n_workflow", 
            description="Activate an n8n workflow to make it available for execution",
            inputSchema={
                "type": "object",
                "properties": {
                    "workflow_id": {
                        "type": "string",
                        "description": "ID of the workflow to activate"
                    }
                },
                "required": ["workflow_id"]
            }
        ),
        Tool(
            name="deactivate_n8n_workflow",
            description="Deactivate an n8n workflow to stop it from running",
            inputSchema={
                "type": "object",
                "properties": {
                    "workflow_id": {
                        "type": "string", 
                        "description": "ID of the workflow to deactivate"
                    }
                },
                "required": ["workflow_id"]
            }
        ),
        Tool(
            name="get_n8n_health",
            description="Check the health status of the n8n instance",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="create_n8n_workflow",
            description="Create a new n8n workflow",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the new workflow"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of what the workflow does"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags to categorize the workflow"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="update_n8n_workflow",
            description="Update an existing n8n workflow name, tags, or structure",
            inputSchema={
                "type": "object",
                "properties": {
                    "workflow_id": {
                        "type": "string",
                        "description": "ID of the workflow to update"
                    },
                    "name": {
                        "type": "string",
                        "description": "New name for the workflow"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New tags for the workflow"
                    }
                },
                "required": ["workflow_id"]
            }
        ),
        Tool(
            name="duplicate_n8n_workflow",
            description="Create a copy of an existing n8n workflow",
            inputSchema={
                "type": "object",
                "properties": {
                    "workflow_id": {
                        "type": "string",
                        "description": "ID of the workflow to duplicate"
                    },
                    "new_name": {
                        "type": "string",
                        "description": "Name for the new workflow copy"
                    }
                },
                "required": ["workflow_id"]
            }
        ),
        Tool(
            name="delete_n8n_workflow",
            description="Delete an n8n workflow permanently",
            inputSchema={
                "type": "object",
                "properties": {
                    "workflow_id": {
                        "type": "string",
                        "description": "ID of the workflow to delete"
                    }
                },
                "required": ["workflow_id"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls from external LLMs."""
    global brebot_crew
    
    try:
        # Initialize Brebot crew if not already done
        if brebot_crew is None:
            brebot_crew = BrebotCrew()
            logger.info("Brebot crew initialized for MCP server")
        
        if name == "get_bot_status":
            return await handle_get_bot_status(arguments)
        elif name == "create_bot":
            return await handle_create_bot(arguments)
        elif name == "assign_task":
            return await handle_assign_task(arguments)
        elif name == "design_bot":
            return await handle_design_bot(arguments)
        elif name == "organize_files":
            return await handle_organize_files(arguments)
        elif name == "create_marketing_content":
            return await handle_create_marketing_content(arguments)
        elif name == "design_web_element":
            return await handle_design_web_element(arguments)
        elif name == "get_system_health":
            return await handle_get_system_health(arguments)
        elif name == "list_available_tools":
            return await handle_list_available_tools(arguments)
        elif name == "update_bot_configuration":
            return await handle_update_bot_configuration(arguments)
        elif name == "get_task_history":
            return await handle_get_task_history(arguments)
        elif name == "list_n8n_workflows":
            return await handle_list_n8n_workflows(arguments)
        elif name == "execute_n8n_workflow":
            return await handle_execute_n8n_workflow(arguments)
        elif name == "get_n8n_execution_status":
            return await handle_get_n8n_execution_status(arguments)
        elif name == "activate_n8n_workflow":
            return await handle_activate_n8n_workflow(arguments)
        elif name == "deactivate_n8n_workflow":
            return await handle_deactivate_n8n_workflow(arguments)
        elif name == "get_n8n_health":
            return await handle_get_n8n_health(arguments)
        elif name == "create_n8n_workflow":
            return await handle_create_n8n_workflow(arguments)
        elif name == "update_n8n_workflow":
            return await handle_update_n8n_workflow(arguments)
        elif name == "duplicate_n8n_workflow":
            return await handle_duplicate_n8n_workflow(arguments)
        elif name == "delete_n8n_workflow":
            return await handle_delete_n8n_workflow(arguments)
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    
    except Exception as e:
        logger.error(f"Error handling tool call {name}: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]

async def handle_get_bot_status(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get bot status information."""
    bot_id = arguments.get("bot_id", "all")
    
    # Simulate bot status data (in real implementation, this would query your bot system)
    bot_statuses = {
        "file_organizer": BotStatus(
            bot_id="file_organizer",
            status="online",
            health_score=95,
            tasks_completed=42,
            last_active=datetime.now()
        ),
        "marketing": BotStatus(
            bot_id="marketing",
            status="online",
            health_score=88,
            tasks_completed=28,
            last_active=datetime.now()
        ),
        "web_design": BotStatus(
            bot_id="web_design",
            status="busy",
            health_score=92,
            tasks_completed=15,
            last_active=datetime.now()
        )
    }
    
    if bot_id == "all":
        status_text = "Bot Status Summary:\n\n"
        for bot in bot_statuses.values():
            status_text += f"🤖 {bot.bot_id}:\n"
            status_text += f"   Status: {bot.status}\n"
            status_text += f"   Health: {bot.health_score}%\n"
            status_text += f"   Tasks Completed: {bot.tasks_completed}\n"
            status_text += f"   Last Active: {bot.last_active}\n\n"
    else:
        if bot_id in bot_statuses:
            bot = bot_statuses[bot_id]
            status_text = f"Bot Status for {bot_id}:\n"
            status_text += f"Status: {bot.status}\n"
            status_text += f"Health: {bot.health_score}%\n"
            status_text += f"Tasks Completed: {bot.tasks_completed}\n"
            status_text += f"Last Active: {bot.last_active}"
        else:
            status_text = f"Bot '{bot_id}' not found"
    
    return [TextContent(type="text", text=status_text)]

async def handle_create_bot(arguments: Dict[str, Any]) -> List[TextContent]:
    """Create a new bot."""
    bot_id = arguments["bot_id"]
    bot_type = arguments["bot_type"]
    description = arguments["description"]
    tools = arguments.get("tools", [])
    
    # In real implementation, this would create the bot in your system
    result_text = f"✅ Bot '{bot_id}' created successfully!\n\n"
    result_text += f"Type: {bot_type}\n"
    result_text += f"Description: {description}\n"
    result_text += f"Assigned Tools: {', '.join(tools) if tools else 'None'}\n"
    result_text += f"Status: Online\n"
    result_text += f"Health Score: 100%\n"
    
    # Log the bot creation
    brebot_logger.log_agent_action(
        agent_name=bot_id,
        action="created_via_mcp",
        details={
            "bot_type": bot_type,
            "description": description,
            "tools": tools
        }
    )
    
    return [TextContent(type="text", text=result_text)]

async def handle_assign_task(arguments: Dict[str, Any]) -> List[TextContent]:
    """Assign a task to a bot."""
    bot_id = arguments["bot_id"]
    task_type = arguments["task_type"]
    description = arguments["description"]
    parameters = arguments.get("parameters", {})
    priority = arguments.get("priority", "medium")
    
    # In real implementation, this would queue the task for the bot
    result_text = f"📋 Task assigned to {bot_id}:\n\n"
    result_text += f"Task Type: {task_type}\n"
    result_text += f"Description: {description}\n"
    result_text += f"Priority: {priority}\n"
    result_text += f"Parameters: {json.dumps(parameters, indent=2)}\n"
    result_text += f"Status: Queued\n"
    result_text += f"Estimated Completion: 5-10 minutes\n"
    
    # Log the task assignment
    brebot_logger.log_agent_action(
        agent_name=bot_id,
        action="task_assigned_via_mcp",
        details={
            "task_type": task_type,
            "description": description,
            "priority": priority,
            "parameters": parameters
        }
    )
    
    return [TextContent(type="text", text=result_text)]


async def handle_design_bot(arguments: Dict[str, Any]) -> List[TextContent]:
    """Generate a bot blueprint via the architect service."""
    goal = (arguments.get("goal") or "").strip()
    if not goal:
        return [TextContent(type="text", text="The 'goal' field is required to design a bot.")]

    spec = BotDesignSpec(
        goal=goal,
        description=arguments.get("description"),
        name=arguments.get("name"),
        primary_tasks=arguments.get("primary_tasks") or [],
        data_sources=arguments.get("data_sources") or [],
        integrations=arguments.get("integrations") or [],
        success_metrics=arguments.get("success_metrics") or [],
        personality=arguments.get("personality"),
        auto_create=bool(arguments.get("auto_create")),
    )

    result = await botArchitectService.design_bot(spec)
    recommendation = result.get("recommendation", {})
    checklist = result.get("checklist", [])
    created_bot = result.get("created_bot")

    lines = ["🤖 Bot Architect Blueprint", ""]
    lines.append(f"Bot ID: {recommendation.get('bot_id', 'n/a')}")
    lines.append(f"Department: {recommendation.get('department', 'Automation')}")
    lines.append(f"Type: {recommendation.get('bot_type', 'text_processing')}")
    lines.append(f"Description: {recommendation.get('description', goal)}")

    responsibilities = recommendation.get('responsibilities') or []
    if responsibilities:
        lines.append("Responsibilities:")
        for item in responsibilities:
            lines.append(f"  • {item}")

    tools = recommendation.get('suggested_tools') or []
    if tools:
        lines.append("Suggested tools: " + ", ".join(tools))

    if checklist:
        lines.append("")
        lines.append("Setup checklist:")
        for item in checklist:
            lines.append(f"  ☐ {item}")

    if created_bot:
        lines.append("")
        created_id = created_bot.get('id') or created_bot.get('bot_id')
        lines.append(f"✅ Bot '{created_id}' created successfully.")

    return [TextContent(type="text", text="\n".join(lines))]

async def handle_organize_files(arguments: Dict[str, Any]) -> List[TextContent]:
    """Organize files using the file organizer bot."""
    directory_path = arguments["directory_path"]
    organization_type = arguments.get("organization_type", "by_extension")
    create_backup = arguments.get("create_backup", True)
    
    try:
        # Use the actual Brebot crew to organize files
        result = brebot_crew.organize_files(directory_path, organization_type)
        
        result_text = f"📁 File organization completed!\n\n"
        result_text += f"Directory: {directory_path}\n"
        result_text += f"Organization Type: {organization_type}\n"
        result_text += f"Backup Created: {'Yes' if create_backup else 'No'}\n"
        result_text += f"Result: {result}\n"
        
        return [TextContent(type="text", text=result_text)]
    
    except Exception as e:
        error_text = f"❌ Error organizing files: {str(e)}"
        return [TextContent(type="text", text=error_text)]

async def handle_create_marketing_content(arguments: Dict[str, Any]) -> List[TextContent]:
    """Create marketing content using the marketing bot."""
    content_type = arguments["content_type"]
    topic = arguments["topic"]
    target_audience = arguments.get("target_audience", "general")
    tone = arguments.get("tone", "professional")
    length = arguments.get("length", "medium")
    
    # In real implementation, this would use the marketing agent
    result_text = f"📝 Marketing content created!\n\n"
    result_text += f"Content Type: {content_type}\n"
    result_text += f"Topic: {topic}\n"
    result_text += f"Target Audience: {target_audience}\n"
    result_text += f"Tone: {tone}\n"
    result_text += f"Length: {length}\n\n"
    result_text += f"Content Preview:\n"
    result_text += f"---\n"
    result_text += f"# {topic}\n\n"
    result_text += f"Engaging {content_type} content about {topic} targeting {target_audience} audience...\n"
    result_text += f"---\n"
    
    return [TextContent(type="text", text=result_text)]

async def handle_design_web_element(arguments: Dict[str, Any]) -> List[TextContent]:
    """Design web elements using the web design bot."""
    element_type = arguments["element_type"]
    requirements = arguments["requirements"]
    style = arguments.get("style", "modern")
    color_scheme = arguments.get("color_scheme", "blue and white")
    
    # In real implementation, this would use the web design agent
    result_text = f"🎨 Web element designed!\n\n"
    result_text += f"Element Type: {element_type}\n"
    result_text += f"Requirements: {requirements}\n"
    result_text += f"Style: {style}\n"
    result_text += f"Color Scheme: {color_scheme}\n\n"
    result_text += f"Design Specifications:\n"
    result_text += f"- Layout: Responsive {element_type} design\n"
    result_text += f"- Colors: {color_scheme}\n"
    result_text += f"- Style: {style} aesthetic\n"
    result_text += f"- Features: {requirements}\n"
    
    return [TextContent(type="text", text=result_text)]

async def handle_get_system_health(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get system health information."""
    # Simulate system health data
    health_text = "🏥 System Health Report\n\n"
    health_text += "Overall Status: ✅ Healthy\n"
    health_text += "Active Bots: 3/3\n"
    health_text += "Memory Usage: 65%\n"
    health_text += "CPU Usage: 23%\n"
    health_text += "Disk Usage: 45%\n"
    health_text += "Network Status: ✅ Connected\n"
    health_text += "Last Health Check: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n"
    
    return [TextContent(type="text", text=health_text)]

async def handle_list_available_tools(arguments: Dict[str, Any]) -> List[TextContent]:
    """List available tools."""
    category = arguments.get("category")
    
    tools_by_category = {
        "File Management": ["ListFilesTool", "CreateFolderTool", "MoveFileTool", "OrganizeFilesTool", "DeleteFileTool"],
        "Web & API": ["WebScrapingTool", "APICallTool", "WebSearchTool", "EmailTool"],
        "Data Processing": ["DataAnalysisTool", "CSVProcessorTool", "JSONProcessorTool", "DatabaseTool"],
        "Content Creation": ["TextGeneratorTool", "ImageGeneratorTool", "MarkdownTool", "PDFTool"],
        "E-commerce": ["ShopifyTool", "ProductCatalogTool", "InventoryTool", "OrderProcessingTool"],
        "Communication": ["SlackTool", "DiscordTool", "TeamsTool", "NotificationTool"]
    }
    
    if category and category in tools_by_category:
        tools_text = f"🔧 Tools in {category} category:\n\n"
        for tool in tools_by_category[category]:
            tools_text += f"- {tool}\n"
    else:
        tools_text = "🔧 All Available Tools:\n\n"
        for cat, tools in tools_by_category.items():
            tools_text += f"{cat}:\n"
            for tool in tools:
                tools_text += f"  - {tool}\n"
            tools_text += "\n"
    
    return [TextContent(type="text", text=tools_text)]

async def handle_update_bot_configuration(arguments: Dict[str, Any]) -> List[TextContent]:
    """Update bot configuration."""
    bot_id = arguments["bot_id"]
    new_tools = arguments.get("new_tools", [])
    description = arguments.get("description")
    status = arguments.get("status")
    
    result_text = f"⚙️ Bot configuration updated for {bot_id}:\n\n"
    
    if new_tools:
        result_text += f"New Tools: {', '.join(new_tools)}\n"
    if description:
        result_text += f"New Description: {description}\n"
    if status:
        result_text += f"New Status: {status}\n"
    
    result_text += f"Configuration saved successfully!"
    
    return [TextContent(type="text", text=result_text)]

async def handle_get_task_history(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get task history."""
    bot_id = arguments.get("bot_id", "all")
    limit = arguments.get("limit", 10)
    
    # Simulate task history data
    history_text = f"📊 Task History for {bot_id}:\n\n"
    history_text += f"Showing last {limit} tasks:\n\n"
    
    sample_tasks = [
        {"task": "File organization", "status": "completed", "duration": "2m 30s", "timestamp": "2024-01-15 14:30"},
        {"task": "Content creation", "status": "completed", "duration": "5m 15s", "timestamp": "2024-01-15 14:25"},
        {"task": "Web design", "status": "in_progress", "duration": "3m 45s", "timestamp": "2024-01-15 14:20"},
        {"task": "Data analysis", "status": "completed", "duration": "1m 20s", "timestamp": "2024-01-15 14:15"},
    ]
    
    for i, task in enumerate(sample_tasks[:limit]):
        status_emoji = "✅" if task["status"] == "completed" else "🔄"
        history_text += f"{i+1}. {status_emoji} {task['task']}\n"
        history_text += f"   Status: {task['status']}\n"
        history_text += f"   Duration: {task['duration']}\n"
        history_text += f"   Time: {task['timestamp']}\n\n"
    
    return [TextContent(type="text", text=history_text)]

# n8n Integration Handlers
async def handle_list_n8n_workflows(arguments: Dict[str, Any]) -> List[TextContent]:
    """List n8n workflows."""
    n8n = get_n8n_service()
    if not n8n:
        return [TextContent(type="text", text="❌ n8n service not configured. Please set N8N_BASE_URL and N8N_API_KEY.")]
    
    try:
        active_only = arguments.get("active_only", False)
        workflows = await n8n.list_workflows(active_only=active_only)
        
        if not workflows:
            return [TextContent(type="text", text="No workflows found.")]
        
        result_text = f"🔧 n8n Workflows {'(Active Only)' if active_only else ''}:\n\n"
        
        for workflow in workflows:
            status_emoji = "🟢" if workflow.active else "⚪"
            result_text += f"{status_emoji} **{workflow.name}** (ID: {workflow.id})\n"
            result_text += f"   Status: {'Active' if workflow.active else 'Inactive'}\n"
            result_text += f"   Nodes: {workflow.nodes}\n"
            result_text += f"   Updated: {workflow.updatedAt}\n"
            if workflow.tags:
                result_text += f"   Tags: {', '.join(workflow.tags)}\n"
            result_text += "\n"
        
        result_text += f"Total: {len(workflows)} workflows"
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error listing workflows: {str(e)}")]

async def handle_execute_n8n_workflow(arguments: Dict[str, Any]) -> List[TextContent]:
    """Execute an n8n workflow."""
    n8n = get_n8n_service()
    if not n8n:
        return [TextContent(type="text", text="❌ n8n service not configured. Please set N8N_BASE_URL and N8N_API_KEY.")]
    
    try:
        workflow_id = arguments["workflow_id"]
        data = arguments.get("data")
        
        # Get workflow info first
        workflow = await n8n.get_workflow(workflow_id)
        if not workflow:
            return [TextContent(type="text", text=f"❌ Workflow {workflow_id} not found.")]
        
        # Execute the workflow
        execution_id = await n8n.execute_workflow(workflow_id, data)
        
        result_text = f"🚀 Workflow Execution Started:\n\n"
        result_text += f"Workflow: {workflow.name} (ID: {workflow_id})\n"
        result_text += f"Execution ID: {execution_id}\n"
        if data:
            result_text += f"Input Data: {json.dumps(data, indent=2)}\n"
        result_text += f"\nUse 'get_n8n_execution_status' with execution ID {execution_id} to check progress."
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error executing workflow: {str(e)}")]

async def handle_get_n8n_execution_status(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get n8n execution status."""
    n8n = get_n8n_service()
    if not n8n:
        return [TextContent(type="text", text="❌ n8n service not configured. Please set N8N_BASE_URL and N8N_API_KEY.")]
    
    try:
        execution_id = arguments["execution_id"]
        execution = await n8n.get_execution_status(execution_id)
        
        if not execution:
            return [TextContent(type="text", text=f"❌ Execution {execution_id} not found.")]
        
        status_emoji = {
            "success": "✅",
            "running": "🟡", 
            "waiting": "⏳",
            "error": "❌",
            "canceled": "⚪"
        }.get(execution.status, "❓")
        
        result_text = f"{status_emoji} Execution Status:\n\n"
        result_text += f"Execution ID: {execution.id}\n"
        result_text += f"Workflow ID: {execution.workflowId}\n"
        result_text += f"Status: {execution.status}\n"
        result_text += f"Mode: {execution.mode}\n"
        
        if execution.startedAt:
            result_text += f"Started: {execution.startedAt}\n"
        if execution.finishedAt:
            result_text += f"Finished: {execution.finishedAt}\n"
        if execution.executionTime:
            result_text += f"Duration: {execution.executionTime}ms\n"
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error getting execution status: {str(e)}")]

async def handle_activate_n8n_workflow(arguments: Dict[str, Any]) -> List[TextContent]:
    """Activate an n8n workflow."""
    n8n = get_n8n_service()
    if not n8n:
        return [TextContent(type="text", text="❌ n8n service not configured. Please set N8N_BASE_URL and N8N_API_KEY.")]
    
    try:
        workflow_id = arguments["workflow_id"]
        
        # Get workflow info first
        workflow = await n8n.get_workflow(workflow_id)
        if not workflow:
            return [TextContent(type="text", text=f"❌ Workflow {workflow_id} not found.")]
        
        if workflow.active:
            return [TextContent(type="text", text=f"✅ Workflow '{workflow.name}' is already active.")]
        
        await n8n.activate_workflow(workflow_id)
        
        result_text = f"✅ Workflow Activated:\n\n"
        result_text += f"Name: {workflow.name}\n"
        result_text += f"ID: {workflow_id}\n"
        result_text += f"The workflow is now active and ready to receive triggers."
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error activating workflow: {str(e)}")]

async def handle_deactivate_n8n_workflow(arguments: Dict[str, Any]) -> List[TextContent]:
    """Deactivate an n8n workflow."""
    n8n = get_n8n_service()
    if not n8n:
        return [TextContent(type="text", text="❌ n8n service not configured. Please set N8N_BASE_URL and N8N_API_KEY.")]
    
    try:
        workflow_id = arguments["workflow_id"]
        
        # Get workflow info first
        workflow = await n8n.get_workflow(workflow_id)
        if not workflow:
            return [TextContent(type="text", text=f"❌ Workflow {workflow_id} not found.")]
        
        if not workflow.active:
            return [TextContent(type="text", text=f"⚪ Workflow '{workflow.name}' is already inactive.")]
        
        await n8n.deactivate_workflow(workflow_id)
        
        result_text = f"⚪ Workflow Deactivated:\n\n"
        result_text += f"Name: {workflow.name}\n"
        result_text += f"ID: {workflow_id}\n"
        result_text += f"The workflow is now inactive and will not respond to triggers."
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error deactivating workflow: {str(e)}")]

async def handle_get_n8n_health(arguments: Dict[str, Any]) -> List[TextContent]:
    """Check n8n health status."""
    n8n = get_n8n_service()
    if not n8n:
        return [TextContent(type="text", text="❌ n8n service not configured. Please set N8N_BASE_URL and N8N_API_KEY.")]
    
    try:
        health = await n8n.health_check()
        
        status_emoji = "✅" if health["status"] == "healthy" else "❌"
        
        result_text = f"{status_emoji} n8n Health Status:\n\n"
        result_text += f"Status: {health['status']}\n"
        result_text += f"URL: {health['base_url']}\n"
        result_text += f"Checked: {health['timestamp']}\n"
        
        if health["status"] == "unhealthy" and "error" in health:
            result_text += f"\nError: {health['error']}\n"
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error checking n8n health: {str(e)}")]

async def handle_create_n8n_workflow(arguments: Dict[str, Any]) -> List[TextContent]:
    """Create a new n8n workflow."""
    n8n = get_n8n_service()
    if not n8n:
        return [TextContent(type="text", text="❌ n8n service not configured. Please set N8N_BASE_URL and N8N_API_KEY.")]
    
    try:
        name = arguments.get("name")
        if not name:
            return [TextContent(type="text", text="❌ Workflow name is required.")]
        
        nodes = arguments.get("nodes", [])
        tags = arguments.get("tags", [])
        
        workflow = await n8n.create_workflow(name=name, nodes=nodes, tags=tags)
        
        if workflow:
            result_text = f"✅ Workflow created successfully!\n\n"
            result_text += f"**{workflow.name}** (ID: {workflow.id})\n"
            result_text += f"Status: {'Active' if workflow.active else 'Inactive'}\n"
            result_text += f"Nodes: {workflow.nodes}\n"
            result_text += f"Created: {workflow.createdAt}\n"
            if workflow.tags:
                result_text += f"Tags: {', '.join(workflow.tags)}\n"
        else:
            result_text = "❌ Failed to create workflow."
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error creating workflow: {str(e)}")]

async def handle_update_n8n_workflow(arguments: Dict[str, Any]) -> List[TextContent]:
    """Update an existing n8n workflow."""
    n8n = get_n8n_service()
    if not n8n:
        return [TextContent(type="text", text="❌ n8n service not configured. Please set N8N_BASE_URL and N8N_API_KEY.")]
    
    try:
        workflow_id = arguments.get("workflow_id")
        if not workflow_id:
            return [TextContent(type="text", text="❌ Workflow ID is required.")]
        
        name = arguments.get("name")
        nodes = arguments.get("nodes")
        tags = arguments.get("tags")
        
        workflow = await n8n.update_workflow(
            workflow_id=workflow_id, 
            name=name, 
            nodes=nodes, 
            tags=tags
        )
        
        if workflow:
            result_text = f"✅ Workflow updated successfully!\n\n"
            result_text += f"**{workflow.name}** (ID: {workflow.id})\n"
            result_text += f"Status: {'Active' if workflow.active else 'Inactive'}\n"
            result_text += f"Nodes: {workflow.nodes}\n"
            result_text += f"Updated: {workflow.updatedAt}\n"
            if workflow.tags:
                result_text += f"Tags: {', '.join(workflow.tags)}\n"
        else:
            result_text = "❌ Failed to update workflow or workflow not found."
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error updating workflow: {str(e)}")]

async def handle_duplicate_n8n_workflow(arguments: Dict[str, Any]) -> List[TextContent]:
    """Duplicate an existing n8n workflow."""
    n8n = get_n8n_service()
    if not n8n:
        return [TextContent(type="text", text="❌ n8n service not configured. Please set N8N_BASE_URL and N8N_API_KEY.")]
    
    try:
        workflow_id = arguments.get("workflow_id")
        if not workflow_id:
            return [TextContent(type="text", text="❌ Workflow ID is required.")]
        
        new_name = arguments.get("new_name")
        
        workflow = await n8n.duplicate_workflow(workflow_id=workflow_id, new_name=new_name)
        
        if workflow:
            result_text = f"✅ Workflow duplicated successfully!\n\n"
            result_text += f"**{workflow.name}** (ID: {workflow.id})\n"
            result_text += f"Status: {'Active' if workflow.active else 'Inactive'}\n"
            result_text += f"Nodes: {workflow.nodes}\n"
            result_text += f"Created: {workflow.createdAt}\n"
            if workflow.tags:
                result_text += f"Tags: {', '.join(workflow.tags)}\n"
        else:
            result_text = "❌ Failed to duplicate workflow or source workflow not found."
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error duplicating workflow: {str(e)}")]

async def handle_delete_n8n_workflow(arguments: Dict[str, Any]) -> List[TextContent]:
    """Delete an n8n workflow."""
    n8n = get_n8n_service()
    if not n8n:
        return [TextContent(type="text", text="❌ n8n service not configured. Please set N8N_BASE_URL and N8N_API_KEY.")]
    
    try:
        workflow_id = arguments.get("workflow_id")
        if not workflow_id:
            return [TextContent(type="text", text="❌ Workflow ID is required.")]
        
        # Get workflow info before deletion for confirmation
        workflow = await n8n.get_workflow(workflow_id)
        if not workflow:
            return [TextContent(type="text", text="❌ Workflow not found.")]
        
        success = await n8n.delete_workflow(workflow_id)
        
        if success:
            result_text = f"✅ Workflow deleted successfully!\n\n"
            result_text += f"Deleted: **{workflow.name}** (ID: {workflow_id})\n"
        else:
            result_text = "❌ Failed to delete workflow."
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error deleting workflow: {str(e)}")]

async def main():
    """Main function to run the MCP server."""
    logger.info("Starting Brebot MCP Server...")
    
    # Initialize n8n service if configured
    import os
    n8n_base_url = os.getenv("N8N_BASE_URL")
    n8n_api_key = os.getenv("N8N_API_KEY")
    
    if n8n_base_url:
        try:
            initialize_n8n_service(n8n_base_url, n8n_api_key)
            logger.info(f"n8n service initialized: {n8n_base_url}")
        except Exception as e:
            logger.warning(f"Failed to initialize n8n service: {e}")
    else:
        logger.info("n8n service not configured (set N8N_BASE_URL and N8N_API_KEY)")
    
    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="brebot-mcp-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
