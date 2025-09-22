#!/bin/bash

# Test script to debug the Mac app

echo "🧪 Testing Mac App Functionality"
echo "================================="

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BREBOT_DIR="$SCRIPT_DIR"

echo "📍 Brebot directory: $BREBOT_DIR"

# Check if Docker is running
echo "🐳 Checking Docker..."
if docker info >/dev/null 2>&1; then
    echo "✅ Docker is running"
else
    echo "❌ Docker is not running"
    exit 1
fi

# Check if virtual environment exists
echo "🐍 Checking virtual environment..."
if [ -d "$BREBOT_DIR/venv" ]; then
    echo "✅ Virtual environment exists"
else
    echo "❌ Virtual environment not found"
    exit 1
fi

# Check if Python dependencies are installed
echo "📦 Checking Python dependencies..."
cd "$BREBOT_DIR"
source venv/bin/activate

if python -c "import fastapi, uvicorn" 2>/dev/null; then
    echo "✅ FastAPI and Uvicorn are installed"
else
    echo "❌ FastAPI and Uvicorn are not installed"
    exit 1
fi

# Test the web app import
echo "🌐 Testing web app import..."
if python -c "from src.web.app_simple import app" 2>/dev/null; then
    echo "✅ Web app imports successfully"
else
    echo "❌ Web app import failed"
    exit 1
fi

# Test starting the web server
echo "🚀 Testing web server startup..."
echo "Starting web server for 5 seconds..."

# Start the web server in background
python src/main_simple.py &
WEB_PID=$!

# Wait for it to start
sleep 5

# Test if it's responding
if curl -s http://localhost:8000/api/health >/dev/null 2>&1; then
    echo "✅ Web server is responding"
else
    echo "❌ Web server is not responding"
fi

# Stop the web server
kill $WEB_PID 2>/dev/null

echo ""
echo "🎉 Mac app test completed!"
echo ""
echo "If all tests passed, the Mac app should work when you click the dock icon."
