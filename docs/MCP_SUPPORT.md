# Brebot MCP Support

Brebot ships with an experimental **Model Context Protocol (MCP)** server, letting external LLM clients (Claude Desktop, VS Code Copilot MCP, etc.) drive Brebot’s core tools. The implementation lives under `src/mcp/` and exposes the same agent actions you get through the CLI or REST API.

## 📦 Available Servers

```
src/mcp/brebot_mcp_server.py       # full server with task + bot tooling
src/mcp/working_mcp_server.py      # trimmed version used for local testing
src/mcp/brebot_mcp_server_simple.py# minimal demonstrator
```

All three register the same MCP metadata (`@server.list_tools` and `@server.call_tool`) but target different demo scopes. `brebot_mcp_server.py` is the one to extend for production.

## 🛠️ Tools Exposed

The MCP server surfaces Brebot operations as tools. The current list (see `list_tools()` in `brebot_mcp_server.py`) includes:

- `get_bot_status` – returns health and workload info for all bots or a specific bot.
- `create_bot` – creates a new bot entry with role, description, and tool assignments.
- `assign_task` – asks an existing bot to perform a task (file organization, content creation, etc.).
- `design_bot` – drafts a bot blueprint (department, tools, checklist) and can auto-create the bot.
- `organize_files` – invokes the file organizer workflow with optional strategy and backup options.
- `create_marketing_content` – drafts marketing assets via the marketing agent.
- `design_web_element` – (continues in file) hands layout/asset requests to the web design agent.
- `list_tasks`, `list_memories`, `ingest_files`, and other helpers in `working_mcp_server.py` for experimentation.

Each tool uses the same underlying services that the FastAPI and CLI routes call, so MCP clients see real system state.

## 🚀 Running the MCP Server

Launch with standard IO (works for Claude Desktop / cursors):

```bash
source venv/bin/activate
python -m src.mcp.brebot_mcp_server
```

This starts an MCP stdio server named `brebot-mcp-server`. Tools are advertised via `list_tools`, and requests are handled by `@server.call_tool` handlers.

For quick sanity checks you can run the included client demos:

```bash
# Simple command-line client showing tool discovery
python -m src.mcp.simple_client_test

# Example of programmatic tool invocation
python -m src.mcp.mcp_client_example
```

## 🔌 Integrating with Claude Desktop

Claude uses a `claude_desktop_config.json`. Add an entry that points to the Brebot server script, for example:

```json
{
  "brebot": {
    "command": ["python", "-m", "src.mcp.brebot_mcp_server"],
    "working_directory": "/Users/bre/brebot"
  }
}
```

Restart Claude Desktop and you’ll see the Brebot tool bundle available to the AI assistant.

## 🧩 Extending MCP Support

- Add new tools by defining a handler in the MCP server module and returning a `Tool` schema entry.
- Reuse the FastAPI services or `BrebotCrew` methods inside the handler’s `call_tool` implementation to execute actions.
- Keep schemas simple: MCP expects JSON-serializable dicts and basic validation (the pydantic models in the server provide the shape).

With MCP enabled, Brebot becomes a controllable agent platform for any MCP-aware LLM client.
