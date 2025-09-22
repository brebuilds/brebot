"""
Brebot MCP Client Example
Example client showing how to connect to and use the Brebot MCP server.
"""

import asyncio
import json
from typing import Dict, Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    """Example client that connects to the Brebot MCP server."""
    
    # Configure the MCP server connection
    server_params = StdioServerParameters(
        command="python",
        args=["src/mcp/brebot_mcp_server.py"],
        env=None
    )
    
    print("🔌 Connecting to Brebot MCP Server...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            print("✅ Connected to Brebot MCP Server!")
            print("📋 Available tools:")
            
            # List available tools
            tools_result = await session.list_tools()
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description}")
            
            print("\n" + "="*50)
            print("🎯 Example Tool Calls")
            print("="*50)
            
            # Example 1: Get bot status
            print("\n1. Getting bot status...")
            status_result = await session.call_tool(
                "get_bot_status",
                {"bot_id": "all"}
            )
            print("Bot Status Result:")
            for content in status_result.content:
                if hasattr(content, 'text'):
                    print(content.text)
            
            # Example 2: Get system health
            print("\n2. Getting system health...")
            health_result = await session.call_tool(
                "get_system_health",
                {}
            )
            print("System Health Result:")
            for content in health_result.content:
                if hasattr(content, 'text'):
                    print(content.text)
            
            # Example 3: List available tools
            print("\n3. Listing available tools...")
            tools_result = await session.call_tool(
                "list_available_tools",
                {}
            )
            print("Available Tools Result:")
            for content in tools_result.content:
                if hasattr(content, 'text'):
                    print(content.text)
            
            # Example 4: Create a new bot
            print("\n4. Creating a new bot...")
            create_result = await session.call_tool(
                "create_bot",
                {
                    "bot_id": "test-bot-mcp",
                    "bot_type": "custom",
                    "description": "Test bot created via MCP",
                    "tools": ["ListFilesTool", "APICallTool"]
                }
            )
            print("Create Bot Result:")
            for content in create_result.content:
                if hasattr(content, 'text'):
                    print(content.text)
            
            # Example 5: Assign a task
            print("\n5. Assigning a task...")
            task_result = await session.call_tool(
                "assign_task",
                {
                    "bot_id": "test-bot-mcp",
                    "task_type": "file_organization",
                    "description": "Organize files in the Documents folder",
                    "parameters": {"folder": "/Users/bre/Documents"},
                    "priority": "medium"
                }
            )
            print("Task Assignment Result:")
            for content in task_result.content:
                if hasattr(content, 'text'):
                    print(content.text)
            
            print("\n" + "="*50)
            print("🎉 MCP Client Example Complete!")
            print("="*50)

if __name__ == "__main__":
    asyncio.run(main())
