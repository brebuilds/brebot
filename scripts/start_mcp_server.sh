#!/bin/bash

# Brebot MCP Server Startup Script
# This script starts the MCP server for external LLM control

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🚀 Starting Brebot MCP Server...${NC}"

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Please run setup first.${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}📦 Activating virtual environment...${NC}"
source "$PROJECT_ROOT/venv/bin/activate"

# Check if MCP dependencies are installed
echo -e "${YELLOW}🔍 Checking MCP dependencies...${NC}"
python -c "import mcp, mcpadapt" 2>/dev/null || {
    echo -e "${RED}❌ MCP dependencies not found. Installing...${NC}"
    pip install mcp mcpadapt
}

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/logs"

# Set environment variables
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
export MCP_LOG_LEVEL="INFO"
export MCP_LOG_FILE="$PROJECT_ROOT/logs/mcp_server.log"

# Start the MCP server
echo -e "${GREEN}🎯 Starting MCP server...${NC}"
echo -e "${BLUE}📡 Server will be available via stdio transport${NC}"
echo -e "${BLUE}🔧 Available tools: bot management, file operations, content creation${NC}"
echo -e "${YELLOW}💡 Use Ctrl+C to stop the server${NC}"
echo ""

cd "$PROJECT_ROOT"
python src/mcp/brebot_mcp_server.py
