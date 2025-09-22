# Getting Started with Brebot

Welcome to **Brebot** - your autonomous AI agent system for marketing and web design agencies! This guide will help you get up and running quickly.

## 🚀 Quick Setup (5 minutes)

### Option 1: Automated Setup (Recommended)

```bash
# Run the automated setup script
./setup.sh
```

This script will:
- Check system requirements
- Set up Python virtual environment
- Install all dependencies
- Configure Docker services
- Download and setup Ollama models
- Test the installation

### Option 2: Manual Setup

If you prefer manual setup or the automated script fails:

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup environment
cp env.example .env
# Edit .env with your settings

# 4. Start Docker services
cd docker
docker-compose up -d

# 5. Setup models
docker-compose exec ollama bash /scripts/setup_models.sh
```

## 🎯 Your First File Organization

Once setup is complete, try organizing your files:

```bash
# Activate virtual environment
source venv/bin/activate

# Initialize Brebot
python src/main.py init

# Organize files by extension
python src/main.py organize /Users/bre/Desktop

# Check system health
python src/main.py health
```

## 📁 What Gets Created

Brebot will organize your files like this:

```
Your Directory/
├── PDF_Files/          # All PDF documents
├── IMAGE_Files/        # All images (jpg, png, gif, etc.)
├── DOC_Files/          # Word documents
├── XLSX_Files/         # Excel spreadsheets
├── CODE_Files/         # Code files (py, js, html, etc.)
└── Other_Files/        # Files with uncommon extensions
```

## 🔧 Configuration

### Key Settings in `.env`

```bash
# Your workspace directory
DEFAULT_WORK_DIR=/Users/bre/Desktop

# Whether to create backups before moving files
CREATE_BACKUP=True

# Whether to run in dry-run mode (see what would happen)
DRY_RUN=False

# LLM model to use
OLLAMA_MODEL=llama3.1:8b
```

### Docker Services

- **Ollama**: http://localhost:11434 (LLM API)
- **OpenWebUI**: http://localhost:3000 (Model management interface)
- **Brebot**: http://localhost:8000 (Main application)

## 🎮 Available Commands

```bash
# System commands
python src/main.py init          # Initialize the system
python src/main.py health        # Check system health
python src/main.py status        # Get system status

# File organization
python src/main.py organize /path/to/files                    # Organize by extension
python src/main.py organize /path/to/files --type by_date     # Organize by date
python src/main.py organize /path/to/files --type by_project  # Organize by project

# Folder management
python src/main.py create-structure /base/path "Projects/2024/Client_A"
python src/main.py move /source/files /organized/destination
```

## 🛠️ Troubleshooting

### Common Issues

1. **"Crew not initialized"**
   ```bash
   python src/main.py init
   ```

2. **"Ollama not responding"**
   ```bash
   cd docker
   docker-compose restart ollama
   ```

3. **"Permission denied"**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER /path/to/your/files
   ```

4. **"Models not found"**
   ```bash
   cd docker
   docker-compose exec ollama ollama pull llama3.1:8b
   ```

### Debug Mode

Enable detailed logging:

```bash
# Edit .env file
LOG_LEVEL=DEBUG

# Or run with verbose output
python src/main.py organize /path --verbose
```

## 📊 Monitoring

### Log Files

- `logs/brebot.log` - General application logs
- `logs/brebot_errors.log` - Error-specific logs

### Health Monitoring

```bash
# Check system health
python src/main.py health

# View Docker service status
cd docker && docker-compose ps

# Check Ollama models
docker-compose exec ollama ollama list
```

## 🚀 Next Steps

1. **Customize Organization Rules**: Edit the agent's behavior in `src/agents/file_organizer_agent.py`

2. **Add New Tools**: Create custom tools in `src/tools/`

3. **Create New Agents**: Add specialized agents for marketing or web design tasks

4. **Integrate with APIs**: Connect to your existing tools and services

5. **Scale Up**: Add more agents for different aspects of your agency workflow

## 💡 Tips for Success

- **Start Small**: Test with a small directory first
- **Use Backups**: Always keep `CREATE_BACKUP=True` initially
- **Monitor Logs**: Check logs if something doesn't work as expected
- **Dry Run**: Use `DRY_RUN=True` to see what would happen without making changes
- **Regular Maintenance**: Run health checks periodically

## 🆘 Getting Help

- **Documentation**: Check `README.md` for detailed information
- **Docker Issues**: See `docker/README.md` for Docker-specific help
- **Logs**: Check `logs/` directory for error details
- **Community**: Create an issue for bugs or feature requests

---

**Ready to double your productivity? Let Brebot handle the file organization while you focus on what matters most! 🎉**
