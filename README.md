# Brebot Enhanced - Autonomous AI Agent Platform v2.0

A comprehensive AI agent system with a three-panel dashboard, ChromaDB integration, and modular bot architecture for marketing and web design agencies.

## 🚀 Quick Start

### Prerequisites
- Docker Desktop running
- Python 3.11+ (for local development)
- 8GB+ RAM recommended

### Local Setup (CLI + API)
```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install Brebot dependencies
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# 3. Install Playwright browsers (needed for web automation tools)
python3 -m playwright install

# 4. Verify the CLI and services
python3 src/main.py init      # prepares the crew
python3 src/main.py health    # runs aggregated health checks

# 5. Launch the FastAPI dashboard (optional)
python3 src/main.py web --host 0.0.0.0 --port 8000
```

You can run the automated helper instead of the manual steps above:

```bash
chmod +x setup.sh
./setup.sh
```

### Start Backing Services with Docker (optional, recommended for full feature set)
```bash
docker compose -f docker/docker-compose.yml up -d chromadb redis

# once services are up you can launch the dashboard or CLI commands
python3 src/main.py health
```

This docker compose file also includes optional services (Ollama, OpenWebUI, bot workers, Grafana/Prometheus). Start them when you are ready:

```bash
docker compose -f docker/docker-compose.yml up -d
```

## 🎯 System Architecture

### Three-Panel Dashboard

#### **Left Panel: File Explorer**
- **File Sources**: Dropbox, Google Drive, Notion integration
- **Recent Files**: Quick access to recently uploaded files
- **Quick Actions**: Start pipelines, organize files, content creation
- **Upload Interface**: Drag-and-drop file uploads

#### **Middle Panel: Chat with Brebot**
- **Context Switching**: Chat with different bots (MockTopus, Airtable Logger, etc.)
- **RAG Integration**: Uses ChromaDB knowledge base for intelligent responses
- **Real-time Updates**: WebSocket-powered live chat
- **Pipeline Integration**: Start and monitor workflows through chat

#### **Right Panel: Bot Staff**
- **Bot Status**: Real-time health monitoring of all agents
- **Current Tasks**: Live progress tracking
- **Active Pipelines**: Monitor running workflows
- **Performance Metrics**: Task completion rates, health scores

### Bot Services

#### **MockTopus Bot** 🎨
- **Purpose**: Image processing and mockup generation
- **Input**: Design files from Dropbox/Drive
- **Process**: Photopea API integration for product mockups
- **Output**: High-quality mockups for t-shirts, hoodies, etc.

#### **Bot Architect Assistant** 🧠
- **Purpose**: Guides you through new bot creation, suggesting departments, tools, and checklists
- **Interface**: Available in the dashboard (Bot Architect modal) and via MCP tool `design_bot`
- **Auto-Creation**: Can deploy the recommended bot instantly, preventing decision paralysis

#### **Airtable Logger** 📋
- **Purpose**: Data management and pipeline tracking
- **Input**: Bot outputs and pipeline state
- **Process**: Logs results, updates pipeline status
- **Output**: Structured data in Airtable

#### **Shopify Publisher** 🛒
- **Purpose**: E-commerce integration
- **Input**: Approved mockups and product data
- **Process**: Creates draft listings
- **Output**: Shopify product drafts

## 🔄 Pipeline Flow

### Design → Shopify Pipeline
```
Dropbox Design File → MockTopus Bot → Photopea API → Airtable Log → Shopify Draft
```

1. **File Upload**: Design file uploaded to Dropbox
2. **Mockup Generation**: MockTopus processes file and generates product mockups
3. **Data Logging**: Airtable Logger records results and updates pipeline status
4. **E-commerce Publishing**: Shopify Publisher creates draft product listings

## 🛠️ Development Setup

### Local Development
```bash
git clone <repo>
cd brebot

python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m playwright install

# Run unit tests
pytest

# Launch the FastAPI app locally
python3 -m uvicorn src.web.app:app --reload --port 8000
```

### Docker Development
```bash
# Bring up core dependencies only
docker compose -f docker/docker-compose.yml up -d chromadb redis

# Bring up everything including optional bots/monitoring
docker compose -f docker/docker-compose.yml up -d
```

## 🤖 MCP Integration (Claude Desktop, VS Code MCP, etc.)

Brebot includes a Model Context Protocol server so external LLM clients can drive bots, ingestion, and automation directly.

- See `docs/MCP_SUPPORT.md` for the tool list and setup instructions.
- Start the server when you need it:
  ```bash
  source venv/bin/activate
  python -m src.mcp.brebot_mcp_server
  ```
- Add the command to your `claude_desktop_config.json` (example in the doc) to give Claude Desktop hands-on control of Brebot.

## 📊 Monitoring & Observability

### Service Health
- **Health Checks**: All services expose `/health` endpoints
- **Real-time Status**: Dashboard shows live service status
- **Automatic Recovery**: Services restart on failure

### Metrics & Logging
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization dashboards
- **Structured Logs**: JSON-formatted logs for all operations
- **Performance Tracking**: Response times, success rates, error rates

### Bot Performance
- **Task Completion Rates**: Track bot efficiency
- **Health Scores**: Monitor bot reliability
- **Processing Times**: Optimize performance
- **Error Tracking**: Identify and resolve issues

## 🔧 Configuration

### Environment Variables
Create `.env` file:
```bash
# AI Services
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Vector Storage
CHROMA_URL=http://localhost:8001

# Message Queue
REDIS_URL=redis://localhost:6379

# External APIs
AIRTABLE_TOKEN=your_airtable_token
AIRTABLE_BASE_ID=your_base_id
DROPBOX_TOKEN=your_dropbox_token
SHOPIFY_TOKEN=your_shopify_token
SHOPIFY_SHOP_DOMAIN=your_shop.myshopify.com

# Logging
LOG_LEVEL=INFO
```

### Airtable Setup
Create two tables:

**Pipelines Table:**
- Pipeline ID (Single line text)
- Status (Single select: pending, in_progress, completed, failed)
- Current Step (Single select)
- Input Data (Long text)
- Results (Long text)
- Created At (Date)
- Completed At (Date)

**Bot Logs Table:**
- Log ID (Single line text)
- Bot ID (Single line text)
- Pipeline ID (Single line text)
- Task Type (Single select)
- Input (Long text)
- Output (Long text)
- Status (Single select: success, failed, retry)
- Duration (Number)
- Timestamp (Date)

## 🚀 Usage Examples

### Starting a Design Pipeline
1. **Upload File**: Drag design file to left panel
2. **Start Pipeline**: Click "Design → Shopify" quick action
3. **Monitor Progress**: Watch real-time updates in right panel
4. **Chat Integration**: Ask Brebot about pipeline status

### Chat with Specific Bot
1. **Select Bot**: Choose bot from dropdown in chat panel
2. **Ask Question**: "MockTopus, can you generate mockups for this design?"
3. **Get Response**: Bot responds with context-aware information
4. **View Results**: See generated mockups and metadata

### File Organization
1. **Select Files**: Choose files in left panel
2. **Organize**: Click "Organize Files" quick action
3. **Monitor**: Watch progress in right panel
4. **Review**: Check organized structure

## 🔌 API Endpoints

### Health & Status
- `GET /api/health` - System health check
- `GET /api/bots` - Bot statuses
- `GET /api/bots/{bot_id}/health` - Specific bot health

### Chat & AI
- `POST /api/chat` - Chat with Brebot
- `GET /api/chat/{task_id}` - Get chat result

### File Operations
- `GET /api/files` - File explorer data
- `POST /api/files/operation` - File operations

### Pipeline Management
- `POST /api/pipeline/start` - Start new pipeline
- `GET /api/pipeline/{pipeline_id}` - Pipeline status

### WebSocket
- `WS /ws` - Real-time updates and bot commands

## 🎨 Customization

### Adding New Bots
1. **Create Bot Directory**: `bots/new-bot/`
2. **Implement Interface**: Extend `BotInterface` class
3. **Add Dockerfile**: Container configuration
4. **Update Compose**: Add to docker-compose-complete.yml
5. **Register Bot**: Add to dashboard bot list

### Custom Pipelines
1. **Define Pipeline**: Create pipeline configuration
2. **Implement Steps**: Add bot tasks for each step
3. **Add UI**: Create pipeline starter in dashboard
4. **Monitor**: Add pipeline tracking

### Dashboard Themes
- **CSS Variables**: Modify colors and styling
- **Layout**: Adjust panel sizes and arrangement
- **Components**: Add new UI components

## 🐛 Troubleshooting

### Common Issues

**Services Not Starting:**
```bash
# Check Docker status
docker info

# Check service logs
docker-compose -f docker/docker-compose-complete.yml logs [service_name]

# Restart specific service
docker-compose -f docker/docker-compose-complete.yml restart [service_name]
```

**ChromaDB Connection Issues:**
```bash
# Check ChromaDB health
curl http://localhost:8001/api/v1/heartbeat

# Reset ChromaDB data
docker-compose -f docker/docker-compose-complete.yml down
rm -rf docker/chroma_data
docker-compose -f docker/docker-compose-complete.yml up -d chromadb
```

**Bot Communication Issues:**
```bash
# Check Redis connection
redis-cli ping

# Check bot logs
docker-compose -f docker/docker-compose-complete.yml logs mocktopus-bot
```

### Performance Optimization

**Memory Usage:**
- Monitor with `docker stats`
- Adjust service memory limits
- Use smaller models for development

**Response Times:**
- Check service health endpoints
- Monitor Prometheus metrics
- Optimize bot processing logic

## 🔮 Future Roadmap

### Phase 2: Advanced Features
- **BreBot Manager**: AI supervisor for bot coordination
- **Advanced Pipelines**: Multi-step workflows with conditional logic
- **Custom Bot Builder**: Visual bot creation interface
- **API Marketplace**: Third-party bot integrations

### Phase 3: Enterprise Features
- **Multi-tenant Support**: Separate workspaces for different clients
- **Advanced Analytics**: Business intelligence and reporting
- **Workflow Automation**: Trigger pipelines from external events
- **Custom Integrations**: Connect to any API or service

## 📞 Support

### Getting Help
- **Documentation**: Check this README and inline comments
- **Logs**: Review service logs for error details
- **Health Checks**: Use `/api/health` endpoint
- **Community**: Join our Discord for support

### Contributing
- **Bug Reports**: Use GitHub issues
- **Feature Requests**: Submit enhancement proposals
- **Code Contributions**: Follow our development guidelines
- **Documentation**: Help improve our docs

---

**Brebot Enhanced** - Doubling your productivity with AI agents! 🚀
# brebot
