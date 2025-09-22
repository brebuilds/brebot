#!/bin/bash

# Brebot Menu Bar Launcher
# This creates a persistent menu bar item for Brebot

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

# Function to start everything
start_everything() {
    echo "🚀 Starting Brebot services..."
    
    # Check Docker
    if ! check_docker; then
        show_notification "Brebot Error" "Docker is not running. Please start Docker Desktop first."
        return 1
    fi
    
    # Start Docker services
    cd "$BREBOT_DIR/docker"
    if docker-compose up -d; then
        show_notification "Brebot" "Docker services started!"
        
        # Wait for services to be ready
        sleep 10
        
        # Start web interface
        cd "$BREBOT_DIR"
        if [ -d "venv" ]; then
            source venv/bin/activate
        fi
        
        python src/main.py web &
        WEB_PID=$!
        
        # Wait for web server to start
        sleep 5
        
        # Open browser
        open_url "http://localhost:8000"
        
        show_notification "Brebot" "Web interface started! Opening browser..."
        
        # Keep the web server running
        wait $WEB_PID
    else
        show_notification "Brebot Error" "Failed to start Docker services"
    fi
}

# Function to show menu
show_menu() {
    choice=$(osascript -e "
    set menuItems to {\"🚀 Start Everything\", \"🌐 Web Interface Only\", \"🐳 Docker Services Only\", \"📊 Check Status\", \"🛑 Stop All Services\", \"❌ Quit\"}
    set selectedItem to choose from list menuItems with title \"Brebot Menu\" with prompt \"Choose an option:\" default items {\"🚀 Start Everything\"}
    if selectedItem is false then
        return \"❌ Quit\"
    else
        return item 1 of selectedItem
    end
    " 2>/dev/null)
    
    case "$choice" in
        "🚀 Start Everything")
            start_everything
            ;;
        "🌐 Web Interface Only")
            cd "$BREBOT_DIR"
            if [ -d "venv" ]; then
                source venv/bin/activate
            fi
            python src/main.py web &
            sleep 3
            open_url "http://localhost:8000"
            show_notification "Brebot" "Web interface started!"
            ;;
        "🐳 Docker Services Only")
            cd "$BREBOT_DIR/docker"
            docker-compose up -d
            show_notification "Brebot" "Docker services started!"
            ;;
        "📊 Check Status")
            if check_docker; then
                show_notification "Brebot Status" "Docker is running"
            else
                show_notification "Brebot Status" "Docker is not running"
            fi
            ;;
        "🛑 Stop All Services")
            cd "$BREBOT_DIR/docker"
            docker-compose down
            pkill -f "python src/main.py"
            show_notification "Brebot" "All services stopped"
            ;;
        "❌ Quit"|"")
            exit 0
            ;;
    esac
}

# Main loop
while true; do
    show_menu
    sleep 1
done
