# Brebot Docker Setup

This directory contains Docker configuration files for running Brebot with Ollama and OpenWebUI.

## Quick Start

1. **Start the services:**
   ```bash
   cd docker
   docker-compose up -d
   ```

2. **Setup models (first time only):**
   ```bash
   docker-compose exec ollama bash /scripts/setup_models.sh
   ```

3. **Access the services:**
   - Brebot API: http://localhost:8000
   - OpenWebUI: http://localhost:3000
   - Ollama API: http://localhost:11434

## Services

### Ollama
- **Purpose**: Runs local LLM models
- **Port**: 11434
- **Models**: llama3.1:8b, nomic-embed-text, codellama:7b, mistral:7b
- **GPU Support**: Configured for NVIDIA GPUs (optional)

### OpenWebUI
- **Purpose**: Web interface for managing Ollama models
- **Port**: 3000
- **Features**: Chat interface, model management, API access

### Brebot
- **Purpose**: Main application
- **Port**: 8000
- **Features**: File organization, agent orchestration

## Configuration

### Environment Variables
- `OLLAMA_BASE_URL`: Ollama service URL
- `OLLAMA_MODEL`: Default LLM model
- `OLLAMA_EMBEDDING_MODEL`: Default embedding model
- `LOG_LEVEL`: Logging level
- `DEFAULT_WORK_DIR`: Default workspace directory

### Volumes
- `ollama_data`: Ollama model storage
- `openwebui_data`: OpenWebUI data
- `/Users/bre/Desktop:/app/workspace`: Your workspace (modify as needed)

## GPU Support

To enable GPU support, ensure you have:
1. NVIDIA Docker runtime installed
2. NVIDIA drivers installed
3. Uncomment the GPU configuration in docker-compose.yml

## Troubleshooting

### Models not loading
```bash
# Check if Ollama is running
docker-compose ps

# Check Ollama logs
docker-compose logs ollama

# Manually pull models
docker-compose exec ollama ollama pull llama3.1:8b
```

### Permission issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER /Users/bre/Desktop
```

### Memory issues
- Reduce model size or use CPU-only mode
- Increase Docker memory limits
- Close other applications

## Development

### Rebuild after code changes
```bash
docker-compose build brebot
docker-compose up -d brebot
```

### View logs
```bash
docker-compose logs -f brebot
```

### Access container shell
```bash
docker-compose exec brebot bash
```
