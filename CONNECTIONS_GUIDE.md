# Brebot Connections Guide

This guide covers Brebot's external service integration capabilities, including OAuth connections, secure token storage, and N8N automation integration.

## 🔌 **Connections Overview**

### **Supported Services**
- **Dropbox**: File storage and synchronization
- **Google Drive**: Cloud file management
- **Notion**: Workspace and page management
- **Airtable**: Database and record management
- **Slack**: Team communication and file sharing

### **Key Features**
- **OAuth Integration**: Secure authentication with external services
- **Token Management**: Encrypted storage of API tokens
- **Ingestion Control**: Toggle which connections are available to Brebot
- **N8N Integration**: Automatic webhook creation for automation workflows
- **Health Monitoring**: Real-time connection status and health checks
- **Scope Management**: Granular permission control per connection

## 🚀 **Getting Started**

### **1. Access Connections**
1. Open the Brebot dashboard
2. Click the **"Connections"** button in the Knowledge Hub panel
3. View all available integrations and their status

### **2. Connect a Service**
1. Click **"Connect"** on any service card
2. Complete OAuth authorization in the popup window
3. Grant necessary permissions
4. Connection status will update automatically

### **3. Enable Ingestion**
1. Once connected, click **"Enable Ingestion"**
2. This creates an N8N webhook for automation
3. Brebot can now automatically ingest content from this service

## 🔐 **OAuth Flow**

### **Authentication Process**
```
User clicks "Connect" 
    ↓
Brebot generates OAuth URL with state parameter
    ↓
User completes authorization in popup window
    ↓
Service redirects with authorization code
    ↓
Brebot exchanges code for access token
    ↓
Token is encrypted and stored securely
    ↓
Connection status updated to "connected"
```

### **Security Features**
- **State Parameter**: Prevents CSRF attacks
- **Token Encryption**: All tokens encrypted with Fernet
- **Secure Storage**: Tokens stored in encrypted format
- **Automatic Refresh**: Refresh tokens handled automatically
- **Scope Validation**: Only requested permissions granted

## 🎯 **Service-Specific Configuration**

### **Dropbox**
- **Scopes**: `files.metadata.read`, `files.content.read`, `files.metadata.write`, `files.content.write`
- **Use Cases**: File synchronization, document processing
- **Events**: File created, file updated, file deleted

### **Google Drive**
- **Scopes**: `https://www.googleapis.com/auth/drive.readonly`, `https://www.googleapis.com/auth/drive.file`
- **Use Cases**: Document collaboration, file sharing
- **Events**: File shared, file modified, new uploads

### **Notion**
- **Scopes**: `read`, `write`
- **Use Cases**: Knowledge management, note taking
- **Events**: Page created, page updated, database changes

### **Airtable**
- **Scopes**: `data.records:read`, `data.records:write`
- **Use Cases**: Data management, record tracking
- **Events**: Record created, record updated, field changes

### **Slack**
- **Scopes**: `channels:read`, `files:read`, `chat:read`
- **Use Cases**: Team communication, file sharing
- **Events**: New messages, file uploads, channel updates

## 🔄 **N8N Integration**

### **Automatic Webhook Creation**
When you enable ingestion for a connection, Brebot automatically:
1. Creates a unique webhook URL for the connection
2. Registers the webhook with N8N
3. Sets up event routing for the service
4. Configures the workflow trigger

### **Webhook URL Format**
```
https://your-n8n-instance.com/webhook/brebot_{service}_{connection_id}
```

### **Event Flow Example**
```
New file in Dropbox
    ↓
Dropbox webhook triggers
    ↓
N8N workflow processes event
    ↓
File content extracted
    ↓
Content sent to Brebot memory
    ↓
Notification sent to Inbox
```

### **N8N Workflow Templates**
Brebot provides pre-built N8N workflows for common automation scenarios:

#### **File Processing Workflow**
- **Trigger**: New file in connected service
- **Actions**: 
  - Extract file content
  - Process with AI
  - Store in Brebot memory
  - Send notification

#### **Data Sync Workflow**
- **Trigger**: Record update in Airtable
- **Actions**:
  - Fetch updated data
  - Update Brebot knowledge base
  - Notify relevant bots

#### **Communication Workflow**
- **Trigger**: New message in Slack
- **Actions**:
  - Analyze message content
  - Route to appropriate bot
  - Generate response
  - Post back to Slack

## 🎛️ **Connection Management**

### **Connection Status**
- **Disconnected**: No active connection
- **Connecting**: OAuth flow in progress
- **Connected**: Active connection with valid token
- **Error**: Connection failed or token expired
- **Expired**: Token needs refresh

### **Connection Actions**

#### **Connect/Disconnect**
- **Connect**: Initiates OAuth flow
- **Disconnect**: Revokes token and removes connection

#### **Toggle Ingestion**
- **Enable**: Creates N8N webhook and enables automation
- **Disable**: Removes webhook and disables automation

#### **Health Check**
- **Test Connection**: Verifies API connectivity
- **Response Time**: Measures connection latency
- **Error Details**: Shows specific error messages

### **Connection Statistics**
- **Total Connections**: Number of configured services
- **Connected**: Number of active connections
- **Ingestion Enabled**: Number of connections with automation
- **N8N Webhooks**: Number of active webhooks

## 🔧 **API Endpoints**

### **Connection Management**
```http
GET /api/connections
POST /api/connections/{connection_id}/connect
POST /api/connections/{connection_id}/disconnect
POST /api/connections/{connection_id}/toggle-ingestion
GET /api/connections/{connection_id}/health
```

### **Event Processing**
```http
POST /api/connections/events
GET /api/connections/{connection_id}/events
```

### **Example API Usage**
```javascript
// Get all connections
const response = await fetch('/api/connections');
const data = await response.json();

// Connect a service
const connectResponse = await fetch('/api/connections/dropbox_default/connect', {
    method: 'POST'
});

// Toggle ingestion
const toggleResponse = await fetch('/api/connections/dropbox_default/toggle-ingestion', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ enabled: true })
});
```

## 🛡️ **Security & Privacy**

### **Token Security**
- **Encryption**: All tokens encrypted with Fernet
- **Key Management**: Encryption keys stored securely
- **Token Rotation**: Automatic refresh token handling
- **Access Control**: Tokens only accessible by authorized services

### **Data Privacy**
- **Minimal Scope**: Only request necessary permissions
- **Data Retention**: Configurable retention policies
- **Audit Logging**: All connection events logged
- **User Control**: Users can revoke access anytime

### **Network Security**
- **HTTPS Only**: All connections use encrypted transport
- **Certificate Validation**: Proper SSL/TLS validation
- **Rate Limiting**: API rate limits respected
- **Error Handling**: Secure error messages

## 📊 **Monitoring & Analytics**

### **Connection Health**
- **Real-time Status**: Live connection monitoring
- **Response Times**: Performance metrics
- **Error Rates**: Failure tracking
- **Usage Statistics**: Connection utilization

### **Event Analytics**
- **Event Volume**: Number of events processed
- **Processing Time**: Event handling performance
- **Success Rates**: Event processing success
- **Error Analysis**: Failure pattern analysis

### **N8N Integration Metrics**
- **Webhook Activity**: Webhook trigger frequency
- **Workflow Execution**: N8N workflow performance
- **Automation Success**: End-to-end automation success
- **Data Flow**: Content ingestion statistics

## 🔍 **Troubleshooting**

### **Common Issues**

#### **OAuth Authorization Failed**
1. **Check Client ID**: Verify OAuth app configuration
2. **Check Redirect URI**: Ensure correct callback URL
3. **Check Permissions**: Verify requested scopes
4. **Check Network**: Ensure internet connectivity

#### **Token Expired**
1. **Automatic Refresh**: System attempts automatic refresh
2. **Manual Reconnect**: User can reconnect if refresh fails
3. **Check Permissions**: Verify refresh token scope
4. **Check Service Status**: Verify external service availability

#### **N8N Webhook Issues**
1. **Check N8N Status**: Verify N8N instance is running
2. **Check Webhook URL**: Verify webhook URL is accessible
3. **Check Workflow**: Verify N8N workflow is active
4. **Check Permissions**: Verify webhook permissions

#### **Connection Health Issues**
1. **Run Health Check**: Use built-in health check
2. **Check API Limits**: Verify service API limits
3. **Check Network**: Test network connectivity
4. **Check Credentials**: Verify token validity

### **Debug Mode**
Enable debug logging for detailed troubleshooting:

```javascript
// Enable connection debug mode
localStorage.setItem('connectionDebug', 'true');

// Check connection status
console.log('Connections:', window.dashboardApp.connections);

// Check connection health
window.dashboardApp.connections.forEach(conn => {
    window.dashboardApp.checkConnectionHealth(conn.connection_id);
});
```

## 🚀 **Advanced Configuration**

### **Custom OAuth Apps**
To use your own OAuth applications:

1. **Create OAuth App**: Register with each service
2. **Configure Redirect URI**: Set to your Brebot instance
3. **Update Client IDs**: Replace default client IDs
4. **Test Connection**: Verify OAuth flow works

### **Custom N8N Workflows**
Create custom automation workflows:

1. **Design Workflow**: Plan your automation logic
2. **Create Webhook**: Set up webhook trigger
3. **Configure Actions**: Add processing steps
4. **Test Workflow**: Verify end-to-end functionality

### **Custom Event Handlers**
Extend event processing:

```python
# Custom event handler
async def handle_custom_event(event: ConnectionEvent):
    if event.event_type == "custom_event":
        # Custom processing logic
        await process_custom_event(event.event_data)
```

## 📚 **Best Practices**

### **Connection Management**
- **Regular Health Checks**: Monitor connection status
- **Token Rotation**: Use refresh tokens when available
- **Scope Minimization**: Request only necessary permissions
- **Error Handling**: Implement robust error handling

### **N8N Integration**
- **Workflow Testing**: Test workflows thoroughly
- **Error Handling**: Handle webhook failures gracefully
- **Performance Monitoring**: Monitor workflow execution
- **Backup Strategies**: Implement fallback mechanisms

### **Security**
- **Regular Audits**: Review connection permissions
- **Token Monitoring**: Monitor token usage
- **Access Logging**: Log all connection activities
- **Incident Response**: Have response plans ready

## 🎉 **What This Enables**

Your Brebot system now has **comprehensive external service integration**! You can:

- **Connect to all major services** with secure OAuth authentication
- **Automatically ingest content** from connected services
- **Create powerful automations** with N8N integration
- **Monitor connection health** in real-time
- **Control data flow** with granular permissions
- **Scale integrations** as your needs grow

This transforms Brebot from a standalone system into a **connected automation platform** that can seamlessly integrate with your entire digital workflow.

---

**Ready to connect your services?** Click the **"Connections"** button in the Knowledge Hub and start building your connected automation ecosystem! 🔌🤖
