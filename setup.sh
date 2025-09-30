#!/bin/bash

# Brebot Setup Script
# This script sets up the entire Brebot system

set -e  # Exit on any error

echo "🚀 Welcome to Brebot Setup!"
echo "=========================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3.11+ is installed
check_python() {
    print_status "Checking Python installation..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        print_success "Python $PYTHON_VERSION found"
        
        # Check if version is 3.11 or higher
        if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 11) else 1)'; then
            print_success "Python version is compatible (3.11+)"
        else
            print_error "Python 3.11+ is required. Current version: $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 is not installed. Please install Python 3.11+ first."
        exit 1
    fi
}

# Check if Docker is installed
check_docker() {
    print_status "Checking Docker installation..."
    
    if command -v docker &> /dev/null; then
        print_success "Docker found"
        
        if command -v docker-compose &> /dev/null; then
            print_success "Docker Compose found"
        else
            print_warning "Docker Compose not found. Trying 'docker compose'..."
            if docker compose version &> /dev/null; then
                print_success "Docker Compose (new version) found"
            else
                print_error "Docker Compose is required but not found."
                exit 1
            fi
        fi
    else
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
}

# Create virtual environment
setup_venv() {
    print_status "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    print_success "Virtual environment activated"
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Upgrade pip
    python -m pip install --upgrade pip
    
    # Install requirements
    python -m pip install -r requirements.txt

    # Install Playwright browsers if Playwright is available
    if python -c "import importlib, sys; sys.exit(0 if importlib.util.find_spec('playwright') else 1)"; then
        print_status "Installing Playwright browsers..."
        if python -m playwright install; then
            print_success "Playwright browsers installed"
        else
            print_warning "Playwright browser install failed. Run 'python -m playwright install' manually."
        fi
    else
        print_warning "Playwright package not installed; skipping browser setup."
    fi
    
    print_success "Python dependencies installed"
}

# Setup environment file
setup_env() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        cp env.example .env
        print_success "Environment file created from template"
        print_warning "Please edit .env file with your specific settings"
    else
        print_warning "Environment file already exists"
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p logs
    mkdir -p data/vector_store
    mkdir -p backups
    
    print_success "Directories created"
}

# Setup Docker services
setup_docker() {
    print_status "Setting up Docker services..."
    
    cd docker
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    # Start services
    print_status "Starting Docker services..."
    docker-compose up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Setup models
    print_status "Setting up Ollama models..."
    docker-compose exec ollama bash /scripts/setup_models.sh
    
    cd ..
    
    print_success "Docker services are running"
}

# Test the installation
test_installation() {
    print_status "Testing Brebot installation..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Test health check
    if python src/main.py health; then
        print_success "Health check passed"
    else
        print_warning "Health check failed - this might be normal if services are still starting"
    fi
    
    # Test initialization
    if python src/main.py init; then
        print_success "Brebot initialization successful"
    else
        print_warning "Brebot initialization failed - check your configuration"
    fi
}

# Main setup function
main() {
    echo "Starting Brebot setup process..."
    echo ""
    
    # Run all setup steps
    check_python
    check_docker
    setup_venv
    install_dependencies
    setup_env
    create_directories
    setup_docker
    test_installation
    
    echo ""
    echo "🎉 Brebot setup completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Edit .env file with your specific settings"
    echo "2. Activate virtual environment: source venv/bin/activate"
    echo "3. Test the system: python src/main.py health"
    echo "4. Start organizing files: python src/main.py organize /path/to/files"
    echo ""
    echo "🌐 Access points:"
    echo "- Brebot CLI: python src/main.py --help"
    echo "- OpenWebUI: http://localhost:3000"
    echo "- Ollama API: http://localhost:11434"
    echo ""
    echo "📚 Documentation: README.md"
    echo "🐛 Troubleshooting: docker/README.md"
    echo ""
    print_success "Happy organizing with Brebot! 🚀"
}

# Run main function
main "$@"
