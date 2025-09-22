# Brebot MCP Integration

This document describes how to use the Model Context Protocol (MCP) integration with Brebot, allowing external LLMs to control and manage your Brebot agents.

## 🎯 What is MCP?

Model Context Protocol (MCP) is a standard that enables AI assistants to securely connect to data sources and tools. With MCP, you can have another LLM (like Claude, GPT-4, or any MCP-compatible AI) control your Brebot system.

## 🚀 Quick Start

### 1. Start the MCP Server

```bash
# Make the script executable (if not already done)
chmod +x scripts/start_mcp_server.sh

# Start the MCP server
./scripts/start_mcp_server.sh
```

The server will start and be available via stdio transport, ready to accept connections from MCP clients.

### 2. Connect with an MCP Client

You can connect to the Brebot MCP server using any MCP-compatible client. Here are some examples:

#### Using Claude Desktop
Add this to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "brebot": {
      "command": "python",
      "args": ["/path/to/brebot/src/mcp/brebot_mcp_server.py"],
      "env": {
        "PYTHONPATH": "/path/to/brebot/src"
      }
    }
  }
}
```

#### Using the Example Client
```bash
cd /Users/bre/brebot
source venv/bin/activate
python src/mcp/mcp_client_example.py
```

## 🔧 Available MCP Tools

The Brebot MCP server provides the following tools for external LLM control:

### Bot Management
- **`get_bot_status`** - Get status of all bots or a specific bot
- **`create_bot`** - Create a new bot with specified configuration
- **`update_bot_configuration`** - Update bot settings and tools
- **`assign_task`** - Assign tasks to specific bots

### File Operations
- **`organize_files`** - Organize files using the file organizer bot
- **`list_available_tools`** - List all available tools by category

### Content Creation
- **`create_marketing_content`** - Create marketing content using the marketing bot
- **`design_web_element`** - Design web elements using the web design bot

### System Monitoring
- **`get_system_health`** - Get overall system health and metrics
- **`get_task_history`** - Get history of completed tasks

## 📋 Tool Usage Examples

### Get Bot Status
```json
{
  "name": "get_bot_status",
  "arguments": {
    "bot_id": "all"
  }
}
```

### Create a New Bot
```json
{
  "name": "create_bot",
  "arguments": {
    "bot_id": "content-writer",
    "bot_type": "content_creator",
    "description": "AI bot for creating blog posts and articles",
    "tools": ["TextGeneratorTool", "MarkdownTool", "APICallTool"]
  }
}
```

### Assign a Task
```json
{
  "name": "assign_task",
  "arguments": {
    "bot_id": "file_organizer",
    "task_type": "file_organization",
    "description": "Organize all files in the Downloads folder by type",
    "parameters": {
      "directory": "/Users/bre/Downloads",
      "organization_type": "by_extension"
    },
    "priority": "high"
  }
}
```

### Organize Files
```json
{
  "name": "organize_files",
  "arguments": {
    "directory_path": "/Users/bre/Documents",
    "organization_type": "by_date",
    "create_backup": true
  }
}
```

### Create Marketing Content
```json
{
  "name": "create_marketing_content",
  "arguments": {
    "content_type": "blog_post",
    "topic": "AI Automation Benefits",
    "target_audience": "small business owners",
    "tone": "professional",
    "length": "medium"
  }
}
```

## 🔌 Integration with Popular AI Assistants

### Claude Desktop
1. Open Claude Desktop settings
2. Add the Brebot MCP server configuration
3. Restart Claude Desktop
4. You can now ask Claude to control your Brebot system!

Example prompts:
- "Check the status of all my Brebot agents"
- "Create a new bot for social media management"
- "Organize files in my Documents folder"
- "Create a blog post about AI automation"

### Cline (VS Code Extension)
1. Install the Cline extension
2. Configure MCP servers in settings
3. Use natural language to control Brebot

### Custom MCP Clients
You can build custom MCP clients using the MCP SDK:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def control_brebot():
    server_params = StdioServerParameters(
        command="python",
        args=["src/mcp/brebot_mcp_server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Use Brebot tools
            result = await session.call_tool("get_bot_status", {"bot_id": "all"})
            print(result)
```

## 🛠️ Configuration

### Environment Variables
You can configure the MCP server using environment variables:

```bash
export MCP_LOG_LEVEL="DEBUG"
export MCP_LOG_FILE="/path/to/logs/mcp_server.log"
export MCP_MAX_CONCURRENT_TASKS=10
export MCP_TASK_TIMEOUT=300
```

### Tool Categories
The MCP server organizes tools into categories:

- **File Management**: File operations and organization
- **Content Creation**: Marketing and web design tools
- **Bot Management**: Bot creation and task assignment
- **System Monitoring**: Health checks and task history

## 🔒 Security Considerations

- The MCP server runs with the same permissions as the user
- File operations are restricted to configured directories
- All tool calls are logged for audit purposes
- Authentication can be enabled for production use

## 🐛 Troubleshooting

### Common Issues

1. **"MCP dependencies not found"**
   ```bash
   pip install mcp mcpadapt
   ```

2. **"Import errors"**
   ```bash
   export PYTHONPATH="/path/to/brebot/src:$PYTHONPATH"
   ```

3. **"Server not responding"**
   - Check if the server is running
   - Verify the stdio transport is working
   - Check logs in `logs/mcp_server.log`

### Debug Mode
Enable debug logging:
```bash
export MCP_LOG_LEVEL="DEBUG"
./scripts/start_mcp_server.sh
```

## 📚 Advanced Usage

### Custom Tool Development
You can extend the MCP server with custom tools by modifying `brebot_mcp_server.py`:

1. Add new tool definitions in `list_tools()`
2. Implement tool handlers in `call_tool()`
3. Add corresponding async handler functions

### Integration with Other Systems
The MCP server can be integrated with:
- CI/CD pipelines
- Monitoring systems
- Custom automation workflows
- Third-party AI platforms

## 🤝 Contributing

To contribute to the MCP integration:

1. Fork the repository
2. Create a feature branch
3. Add your MCP tools or improvements
4. Test with the example client
5. Submit a pull request

## 📄 License

This MCP integration is part of the Brebot project and follows the same license terms.

---

**Need help?** Check the logs in `logs/mcp_server.log` or open an issue on GitHub.
