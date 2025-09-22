#!/bin/bash

# Enhanced Brebot System Launcher
# Launches the complete system with Docker Compose

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BREBOT_DIR="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$BREBOT_DIR/docker"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to show macOS notification
show_notification() {
    osascript -e "display notification \"$2\" with title \"$1\""
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running. Please start Docker Desktop first.${NC}"
        show_notification "Brebot Error" "Docker is not running. Please start Docker Desktop first."
        exit 1
    fi
    echo -e "${GREEN}✅ Docker is running${NC}"
}

# Function to check if Ollama is running natively
check_ollama() {
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Ollama is running natively${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️ Ollama is not running natively. Will use Docker version.${NC}"
        return 1
    fi
}

# Function to start services
start_services() {
    echo -e "${BLUE}🐳 Starting Brebot Enhanced Services...${NC}"
    
    cd "$DOCKER_DIR" || exit 1
    
    # Check if we should use native Ollama or Docker Ollama
    if check_ollama; then
        echo -e "${YELLOW}Using native Ollama, starting services without Ollama container...${NC}"
        # Start services without Ollama (assuming it's running natively)
        docker-compose -f docker-compose.yml up -d openwebui chromadb redis brebot-web mocktopus-bot airtable-logger shopify-publisher prometheus grafana
    else
        echo -e "${YELLOW}Starting all services including Ollama container...${NC}"
        # Start all services
        docker-compose -f docker-compose.yml up -d
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Services started successfully${NC}"
        show_notification "Brebot" "Enhanced services are starting up..."
    else
        echo -e "${RED}❌ Failed to start services${NC}"
        show_notification "Brebot Error" "Failed to start services. Check Docker logs."
        exit 1
    fi
}

# Function to wait for services to be ready
wait_for_services() {
    echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"
    
    # Wait for ChromaDB
    echo "Waiting for ChromaDB..."
    for i in {1..30}; do
        if curl -s http://localhost:8001/api/v1/heartbeat >/dev/null 2>&1; then
            echo -e "${GREEN}✅ ChromaDB is ready${NC}"
            break
        fi
        sleep 2
    done
    
    # Wait for OpenWebUI
    echo "Waiting for OpenWebUI..."
    for i in {1..30}; do
        if curl -s http://localhost:3000/health >/dev/null 2>&1; then
            echo -e "${GREEN}✅ OpenWebUI is ready${NC}"
            break
        fi
        sleep 2
    done
    
    # Wait for Brebot Web Interface
    echo "Waiting for Brebot Web Interface..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/api/health >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Brebot Web Interface is ready${NC}"
            break
        fi
        sleep 2
    done
}

# Function to open browser
open_browser() {
    echo -e "${BLUE}🌍 Opening Brebot Enhanced Dashboard...${NC}"
    open http://localhost:8000
    show_notification "Brebot Enhanced" "Dashboard is ready at http://localhost:8000"
}

# Function to show service URLs
show_urls() {
    echo -e "${BLUE}
╔══════════════════════════════════════════════════════════════╗
║                    🤖 Brebot Enhanced System                ║
║                  All services are running!                  ║
╚══════════════════════════════════════════════════════════════╝
${NC}"
    
    echo -e "${GREEN}📍 Service URLs:${NC}"
    echo -e "   🖥️  Brebot Dashboard:    http://localhost:8000"
    echo -e "   💬 OpenWebUI Chat:      http://localhost:3000"
    echo -e "   🧠 ChromaDB:            http://localhost:8001"
    echo -e "   📊 Grafana:             http://localhost:3001"
    echo -e "   📈 Prometheus:          http://localhost:9090"
    echo -e "   🔴 Redis:               localhost:6379"
    echo ""
    echo -e "${GREEN}🤖 Bot Services:${NC}"
    echo -e "   🎨 MockTopus:           Image processing & mockups"
    echo -e "   📋 Airtable Logger:     Data management & logging"
    echo -e "   🛒 Shopify Publisher:   E-commerce integration"
    echo ""
    echo -e "${YELLOW}💡 Tips:${NC}"
    echo -e "   • Use the three-panel dashboard for full control"
    echo -e "   • Chat with Brebot for AI assistance"
    echo -e "   • Monitor bot status in the right panel"
    echo -e "   • Upload files in the left panel to start pipelines"
    echo ""
    echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"
}

# Function to stop services
stop_services() {
    echo -e "${YELLOW}🛑 Stopping Brebot Enhanced Services...${NC}"
    cd "$DOCKER_DIR" || exit 1
    docker-compose -f docker-compose.yml down
    echo -e "${GREEN}✅ Services stopped${NC}"
    show_notification "Brebot" "All services have been stopped"
}

# Main function
main() {
    echo -e "${BLUE}
╔══════════════════════════════════════════════════════════════╗
║                    🤖 Brebot Enhanced System                ║
║              Autonomous AI Agent Platform v2.0              ║
╚══════════════════════════════════════════════════════════════╝
${NC}"
    
    # Check prerequisites
    check_docker
    
    # Start services
    start_services
    
    # Wait for services to be ready
    wait_for_services
    
    # Open browser
    open_browser
    
    # Show service URLs
    show_urls
    
    # Set up signal handler for graceful shutdown
    trap stop_services SIGINT SIGTERM
    
    # Keep script running
    while true; do
        sleep 60
        # Optional: Check service health periodically
        if ! curl -s http://localhost:8000/api/health >/dev/null 2>&1; then
            echo -e "${YELLOW}⚠️ Brebot web interface appears to be down. Attempting restart...${NC}"
            # Could add restart logic here
        fi
    done
}

# Handle command line arguments
case "${1:-}" in
    "stop")
        stop_services
        ;;
    "restart")
        stop_services
        sleep 5
        main
        ;;
    "status")
        echo -e "${BLUE}🔍 Checking service status...${NC}"
        curl -s http://localhost:8000/api/health | python3 -m json.tool 2>/dev/null || echo "Services not running"
        ;;
    *)
        main
        ;;
esac
