# BreBot Platform Integrations Setup Guide

BreBot now supports comprehensive integrations with all your favorite platforms, giving you and your AI agents long-term access to your digital ecosystem with complete activity tracking.

## 🎯 Overview

BreBot can now access and manage:
- **Dropbox** - File storage and synchronization
- **Airtable** - Database management and automation
- **Etsy** - Marketplace management and listings
- **Printify** - Print-on-demand product management
- **n8n** - Workflow automation
- **Shopify** - E-commerce platform (planned)
- **Notion** - Workspace and documentation (planned)
- **Canva** - Design automation (planned)
- **Figma** - Design collaboration (planned)
- **Desktop Files** - Local file system access
- **Browser Automation** - Web automation (planned)
- **Email Accounts** - Email management (planned)

## 🔧 Environment Configuration

Set these environment variables to enable platform integrations:

### Dropbox Integration
```bash
export DROPBOX_ACCESS_TOKEN="your_dropbox_token_here"
```

**Setup Steps:**
1. Go to https://www.dropbox.com/developers/apps
2. Create a new app with "Full Dropbox" access
3. Generate an access token
4. Set the token as DROPBOX_ACCESS_TOKEN

### Airtable Integration
```bash
export AIRTABLE_API_KEY="your_airtable_key_here"
```

**Setup Steps:**
1. Go to https://airtable.com/create/tokens
2. Create a personal access token
3. Grant access to your bases
4. Set the token as AIRTABLE_API_KEY

### Etsy Integration
```bash
export ETSY_API_KEY="your_etsy_api_key_here"
export ETSY_SHOP_ID="your_shop_id_here"
```

**Setup Steps:**
1. Go to https://www.etsy.com/developers/register
2. Create a new app
3. Get your API key from the app dashboard
4. Find your shop ID in your shop settings

### Printify Integration
```bash
export PRINTIFY_API_TOKEN="your_printify_token_here"
export PRINTIFY_SHOP_ID="your_shop_id_here"
```

**Setup Steps:**
1. Go to https://printify.com/app/account/api
2. Generate a new API token
3. Find your shop ID in your shop settings
4. Set the credentials

### n8n Integration
```bash
export N8N_BASE_URL="https://your-n8n.hostinger.com"
export N8N_API_KEY="your_n8n_api_key_here"
```

**Setup Steps:**
1. Access your n8n instance
2. Go to Settings → API Keys
3. Create a new API key
4. Set your instance URL and API key

## 🚀 Initialization

BreBot automatically initializes all configured integrations when starting:

```bash
# Start BreBot with all integrations
source venv/bin/activate
python3 src/main.py web --port 8002
```

## 📊 Activity Logging

Every platform interaction is comprehensively logged:

### What's Logged
- **Platform**: Which service was accessed
- **Activity Type**: Read, write, create, update, delete, etc.
- **Agent Name**: Which BreBot agent performed the action
- **Timestamp**: When the action occurred
- **Resource Path**: What file/record was accessed
- **Data Size**: Amount of data transferred
- **Success/Failure**: Whether the action succeeded
- **Error Details**: Any error messages
- **Session Tracking**: Links related activities

### Log Storage
- **Database**: SQLite database for queryable logs
- **Files**: Detailed JSON logs organized by platform and date
- **Exports**: CSV/JSON exports for analysis

## 🔍 Available MCP Tools

BreBot exposes all platform capabilities through MCP tools for external LLMs:

### Dropbox Tools
- `list_dropbox_files` - Browse files and folders
- `download_dropbox_file` - Download files locally
- `upload_dropbox_file` - Upload files to Dropbox
- `create_dropbox_folder` - Create new folders
- `delete_dropbox_file` - Delete files/folders
- `search_dropbox_files` - Search for files
- `create_dropbox_shared_link` - Create sharing links

### Airtable Tools
- `list_airtable_bases` - List accessible bases
- `get_airtable_schema` - Get table structures
- `list_airtable_records` - Query records
- `create_airtable_record` - Add new records
- `update_airtable_record` - Modify records
- `delete_airtable_record` - Remove records
- `search_airtable_records` - Search within tables
- `export_airtable_data` - Export table data

### Etsy Tools
- `get_etsy_shop_info` - Shop information
- `list_etsy_listings` - Browse products
- `create_etsy_listing` - Add new products
- `update_etsy_listing` - Modify listings
- `delete_etsy_listing` - Remove products
- `get_etsy_orders` - View orders
- `search_etsy_listings` - Search marketplace
- `get_etsy_shop_stats` - Analytics

### Printify Tools
- `list_printify_shops` - List connected shops
- `list_printify_products` - Browse products
- `create_printify_product` - Design new products
- `update_printify_product` - Modify products
- `publish_printify_product` - Publish to sales channels
- `list_printify_orders` - Order management
- `get_printify_blueprints` - Available product types

### n8n Tools
- `list_n8n_workflows` - Browse workflows
- `execute_n8n_workflow` - Run automations
- `create_n8n_workflow` - Build new workflows
- `update_n8n_workflow` - Modify workflows
- `activate_n8n_workflow` - Enable workflows
- `get_n8n_health` - System status

### System Tools
- `get_integration_health` - Check all platform status
- `export_activity_logs` - Download activity logs
- `get_integration_summary` - Platform overview

## 🎮 Usage Examples

### File Management with Dropbox
```python
# External LLM through MCP can:
list_dropbox_files(path="/Projects")
download_dropbox_file(dropbox_path="/Projects/design.psd", local_path="./downloads/")
upload_dropbox_file(local_path="./output.pdf", dropbox_path="/Completed/output.pdf")
```

### E-commerce Management
```python
# Manage Etsy listings
create_etsy_listing(
    title="Custom Art Print",
    description="Beautiful handmade art",
    price=25.00,
    tags=["art", "print", "custom"]
)

# Sync with Printify
create_printify_product(
    title="Custom T-Shirt",
    blueprint_id=5,
    print_provider_id=1
)
```

### Data Management
```python
# Create Airtable records
create_airtable_record(
    base_id="appXXX",
    table_id="tblYYY",
    fields={"Name": "New Customer", "Email": "test@example.com"}
)

# Export data
export_airtable_data(base_id="appXXX", table_id="tblYYY", format="csv")
```

## 🔒 Security & Privacy

### Data Protection
- API keys stored as environment variables only
- No hardcoded credentials in code
- Secure HTTPS connections to all platforms
- Activity logs stored locally

### Access Control
- Each integration can be individually enabled/disabled
- Comprehensive audit trail of all actions
- Error logging without exposing sensitive data
- Session tracking for accountability

### Activity Monitoring
- Real-time logging of all platform interactions
- Exportable logs for compliance
- Health monitoring for all integrations
- Automatic error detection and reporting

## 📈 Monitoring & Health

### Health Checks
BreBot automatically monitors all integrations:
- Connection status
- API quota usage
- Error rates
- Response times

### Activity Analytics
- Platform usage statistics
- Agent activity patterns
- Error frequency analysis
- Data transfer volumes

### Exports & Reports
- Activity logs in CSV/JSON format
- Integration health reports
- Usage analytics
- Compliance documentation

## 🛠 Troubleshooting

### Common Issues

**Integration Not Working**
1. Check environment variables are set
2. Verify API credentials are valid
3. Check platform-specific permissions
4. Review activity logs for errors

**Health Check Failures**
1. Verify internet connectivity
2. Check API key permissions
3. Confirm platform service status
4. Review rate limiting

**Missing Activity Logs**
1. Ensure activity logger is initialized
2. Check database permissions
3. Verify log directory exists
4. Review error messages

### Getting Help
- Check activity logs: `export_activity_logs(hours=24)`
- Run health check: `get_integration_health()`
- View integration summary: `get_integration_summary()`

## 🚀 Next Steps

1. **Set up your API credentials** for desired platforms
2. **Restart BreBot** to initialize integrations
3. **Run health checks** to verify connections
4. **Start automating** with your AI agents!

Your BreBot agents now have comprehensive access to your digital ecosystem with complete transparency and logging! 🎉