# n8n Integration for BreBot

BreBot now has full MCP integration with self-hosted n8n instances, allowing external LLMs to manage n8n workflows through BreBot's MCP server.

## Setup

### Environment Variables
Set these environment variables to configure n8n integration:

```bash
export N8N_BASE_URL="https://your-n8n.hostinger.com"
export N8N_API_KEY="your_api_key_here"
```

### n8n API Key Setup
1. Log into your n8n instance
2. Go to Settings → API Keys
3. Create a new API key
4. Copy the key and set it as N8N_API_KEY

## Available MCP Tools

### Workflow Management
- `list_n8n_workflows` - List all workflows (with optional active_only filter)
- `execute_n8n_workflow` - Execute a workflow with optional data payload
- `get_n8n_execution_status` - Check execution status by ID
- `activate_n8n_workflow` - Activate a workflow
- `deactivate_n8n_workflow` - Deactivate a workflow

### Workflow Creation & Editing
- `create_n8n_workflow` - Create new workflows with nodes and tags
- `update_n8n_workflow` - Update existing workflow name, nodes, or tags
- `duplicate_n8n_workflow` - Duplicate a workflow with optional new name
- `delete_n8n_workflow` - Delete a workflow (with confirmation)

### Health & Status
- `get_n8n_health` - Check n8n instance connectivity and health

## Example Usage

### Create a Simple Workflow
```python
# External LLM can call this through MCP
create_n8n_workflow(
    name="Email Notification Workflow",
    nodes=[
        {
            "name": "Start",
            "type": "n8n-nodes-base.start",
            "position": [250, 300],
            "parameters": {}
        },
        {
            "name": "Send Email", 
            "type": "n8n-nodes-base.emailSend",
            "position": [450, 300],
            "parameters": {
                "to": "admin@example.com",
                "subject": "Notification",
                "text": "Hello from n8n!"
            }
        }
    ],
    tags=["notifications", "email"]
)
```

### Execute a Workflow
```python
# Execute workflow with data
execute_n8n_workflow(
    workflow_id="123",
    data={"user_id": "456", "action": "signup"}
)
```

## Integration Benefits

1. **Full Workflow Control**: Create, edit, execute, and manage workflows programmatically
2. **Real-time Monitoring**: Check execution status and workflow health
3. **Automation**: External LLMs can automate workflow management tasks
4. **Flexibility**: Support for complex node configurations and data passing

## Security Notes

- API keys are handled securely through environment variables
- All n8n operations are logged through BreBot's logging system
- Error handling prevents sensitive information exposure
- Workflow deletion requires confirmation to prevent accidents

## Files Modified

- `src/services/n8n_service.py` - Complete n8n API integration service
- `src/mcp/brebot_mcp_server.py` - MCP tools and handlers for n8n operations

The integration is now ready for use with your self-hosted n8n instance on Hostinger!