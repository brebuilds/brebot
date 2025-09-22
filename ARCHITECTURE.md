# Brebot Modular Bot Architecture

## System Overview

Brebot is designed as a modular AI agent system where each bot is a specialized container/service with clear input/output interfaces. Bots communicate via Airtable rows and message queues.

## Architecture Layers

### 1. **Bot Layer** (Individual Services)
Each bot is a Docker container with:
- **Single Responsibility**: One specific task (e.g., image processing, content generation)
- **Clear I/O**: Standardized input/output formats
- **Health Monitoring**: Built-in health checks and logging
- **Queue Integration**: Connects to message queue for task assignment

### 2. **Communication Layer**
- **Message Queue**: Redis/RabbitMQ for task distribution
- **Airtable Integration**: Central data store for pipeline state
- **API Gateway**: Standardized communication between bots

### 3. **BreBot Manager Layer** (Future)
- **Digital Clone**: AI manager that reads logs, approves/rejects outputs
- **Task Assignment**: Distributes work from backlog
- **Quality Control**: Monitors bot performance and outputs

## Phase 1 Pipeline: Design → Mockups → Airtable → Shopify

### Pipeline Flow
```
Dropbox Design File → MockTopus Bot → Photopea API → Airtable Log → Shopify Draft
```

### Bot Services

#### **MockTopus Bot** (Image Processing)
- **Input**: Design file URL from Dropbox
- **Process**: Generate Photopea mockups
- **Output**: Mockup images + metadata
- **Container**: `mocktopus-bot:latest`

#### **Airtable Logger** (Data Management)
- **Input**: Bot outputs and pipeline state
- **Process**: Log results, update pipeline status
- **Output**: Updated Airtable records
- **Container**: `airtable-logger:latest`

#### **Shopify Publisher** (E-commerce)
- **Input**: Approved mockups and product data
- **Process**: Create draft listings
- **Output**: Shopify product drafts
- **Container**: `shopify-publisher:latest`

## Data Flow

### 1. **Task Initiation**
```json
{
  "pipeline_id": "design_001",
  "trigger": "dropbox_file_added",
  "input": {
    "file_url": "https://dropbox.com/design.png",
    "product_name": "Summer Collection T-Shirt",
    "target_market": "fashion"
  },
  "status": "pending"
}
```

### 2. **Bot Communication**
```json
{
  "bot_id": "mocktopus",
  "task_id": "design_001",
  "input": {
    "source_file": "https://dropbox.com/design.png",
    "mockup_templates": ["t-shirt", "hoodie", "tank-top"]
  },
  "output": {
    "mockups": [
      {
        "template": "t-shirt",
        "image_url": "https://cdn.example.com/mockup1.jpg",
        "confidence": 0.95
      }
    ],
    "status": "completed"
  }
}
```

### 3. **Pipeline State**
```json
{
  "pipeline_id": "design_001",
  "status": "in_progress",
  "current_step": "shopify_publish",
  "completed_steps": ["mockup_generation", "airtable_log"],
  "results": {
    "mockups": [...],
    "airtable_record_id": "rec123456",
    "shopify_draft_id": "draft_789"
  }
}
```

## Container Structure

### Base Bot Container
```dockerfile
FROM python:3.11-slim

# Standard bot interface
COPY bot_interface.py /app/
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Bot-specific implementation
COPY bot_logic.py /app/
COPY config.py /app/

# Health check and monitoring
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python /app/health_check.py

CMD ["python", "/app/bot_interface.py"]
```

### Bot Interface Standard
```python
class BotInterface:
    def __init__(self, bot_id: str, queue_url: str, airtable_token: str):
        self.bot_id = bot_id
        self.queue = MessageQueue(queue_url)
        self.airtable = AirtableClient(airtable_token)
    
    def process_task(self, task: dict) -> dict:
        """Main processing logic - implemented by each bot"""
        pass
    
    def run(self):
        """Main bot loop"""
        while True:
            task = self.queue.get_next_task(self.bot_id)
            if task:
                result = self.process_task(task)
                self.queue.complete_task(task['id'], result)
                self.airtable.log_result(task, result)
```

## Message Queue Design

### Task Types
- `mockup_generation`: Generate product mockups
- `content_creation`: Create marketing content
- `shopify_publish`: Publish to Shopify
- `quality_check`: Review bot outputs

### Queue Structure
```json
{
  "queue_name": "bot_tasks",
  "message": {
    "task_id": "uuid",
    "bot_type": "mocktopus",
    "pipeline_id": "design_001",
    "input_data": {...},
    "priority": "high",
    "created_at": "2025-01-01T00:00:00Z",
    "retry_count": 0
  }
}
```

## Airtable Schema

### Pipelines Table
| Field | Type | Description |
|-------|------|-------------|
| Pipeline ID | Single line text | Unique identifier |
| Status | Single select | pending, in_progress, completed, failed |
| Current Step | Single select | Current bot in pipeline |
| Input Data | Long text | JSON of input parameters |
| Results | Long text | JSON of all bot outputs |
| Created At | Date | Pipeline start time |
| Completed At | Date | Pipeline completion time |

### Bot Logs Table
| Field | Type | Description |
|-------|------|-------------|
| Log ID | Single line text | Unique identifier |
| Bot ID | Single line text | Bot that performed task |
| Pipeline ID | Single line text | Associated pipeline |
| Task Type | Single select | Type of task performed |
| Input | Long text | JSON of input data |
| Output | Long text | JSON of output data |
| Status | Single select | success, failed, retry |
| Duration | Number | Task duration in seconds |
| Timestamp | Date | When task was completed |

## Future Bot Expansion

### Planned Bots
- **ThreadMaster**: Social media content generation
- **PromoPiper**: Email marketing campaigns
- **CodeCraft**: Web development tasks
- **DataDigger**: Analytics and reporting
- **CustomerCare**: Support ticket handling

### Bot Template
```python
# New bot implementation
class NewBot(BotInterface):
    def process_task(self, task: dict) -> dict:
        # Bot-specific logic here
        input_data = task['input_data']
        
        # Process the task
        result = self.do_specific_work(input_data)
        
        return {
            'status': 'completed',
            'output': result,
            'metadata': {
                'processing_time': 30,
                'confidence': 0.95
            }
        }
```

## Deployment Strategy

### Docker Compose Structure
```yaml
version: '3.8'
services:
  # Core services
  redis:
    image: redis:alpine
    ports: ["6379:6379"]
  
  # Bot services
  mocktopus-bot:
    build: ./bots/mocktopus
    environment:
      - REDIS_URL=redis://redis:6379
      - AIRTABLE_TOKEN=${AIRTABLE_TOKEN}
  
  airtable-logger:
    build: ./bots/airtable-logger
    environment:
      - AIRTABLE_TOKEN=${AIRTABLE_TOKEN}
  
  shopify-publisher:
    build: ./bots/shopify-publisher
    environment:
      - SHOPIFY_TOKEN=${SHOPIFY_TOKEN}
  
  # Manager layer (future)
  brebot-manager:
    build: ./manager
    environment:
      - REDIS_URL=redis://redis:6379
      - AIRTABLE_TOKEN=${AIRTABLE_TOKEN}
```

## Monitoring & Observability

### Health Checks
- Each bot exposes `/health` endpoint
- Centralized health monitoring
- Automatic restart on failure

### Logging
- Structured JSON logs
- Centralized log aggregation
- Performance metrics

### Metrics
- Task completion rates
- Bot response times
- Pipeline success rates
- Error rates by bot type

## Security

### Authentication
- API keys for external services
- Service-to-service authentication
- Secure credential management

### Data Privacy
- Local processing where possible
- Encrypted data transmission
- Audit trails for all operations

---

This architecture provides a solid foundation for building a scalable AI agent system that can grow from one working pipeline to a full digital workforce.
