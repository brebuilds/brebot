#!/bin/bash

# Brebot Simple Launcher
# This creates a simple launcher that opens the web interface

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BREBOT_DIR="$(dirname "$SCRIPT_DIR")"

# Function to show notification
show_notification() {
    local title="$1"
    local message="$2"
    osascript -e "display notification \"$message\" with title \"$title\"" 2>/dev/null || true
}

# Function to open URL
open_url() {
    local url="$1"
    open "$url" 2>/dev/null || true
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        return 1
    fi
    return 0
}

# Main function
main() {
    # Change to the Brebot directory
    cd "$BREBOT_DIR"
    
    # Show welcome message
    echo "🤖 Brebot AI System Starting..."
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        show_notification "Brebot Error" "Docker is not installed. Please install Docker Desktop first."
        exit 1
    fi
    
    # Check if Docker is running
    if ! check_docker; then
        show_notification "Brebot Error" "Docker is not running. Please start Docker Desktop first."
        exit 1
    fi
    
    # Start Docker services
    echo "🐳 Starting Docker services..."
    cd docker
    if docker-compose up -d; then
        show_notification "Brebot" "Docker services started!"
        
        # Wait for services to be ready
        echo "⏳ Waiting for services to be ready..."
        sleep 10
        
        # Start web interface
        echo "🌐 Starting web interface..."
        cd "$BREBOT_DIR"
        
        # Activate virtual environment if it exists
        if [ -d "venv" ]; then
            source venv/bin/activate
        fi
        
        # Start the web interface
        python src/main.py web &
        WEB_PID=$!
        
        # Wait for web server to start
        sleep 5
        
        # Open browser
        open_url "http://localhost:8000"
        
        show_notification "Brebot" "Web interface started! Opening browser..."
        
        echo "🎉 Brebot is now running!"
        echo "📍 Web Interface: http://localhost:8000"
        echo "📍 OpenWebUI: http://localhost:3000"
        echo "📍 Ollama API: http://localhost:11434"
        echo ""
        echo "Press Ctrl+C to stop all services"
        
        # Keep the web server running
        wait $WEB_PID
    else
        show_notification "Brebot Error" "Failed to start Docker services"
        exit 1
    fi
}

# Run main function
main "$@"
