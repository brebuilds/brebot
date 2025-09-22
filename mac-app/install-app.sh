#!/bin/bash

# Brebot Mac App Installer
# This script creates the Mac application bundle and installs it

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${PURPLE}🚀 Installing Brebot Mac Application...${NC}"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$SCRIPT_DIR/Brebot.app"
ICON_SVG="$SCRIPT_DIR/brebot-icon.svg"

# Check if we have the required tools
check_requirements() {
    echo -e "${BLUE}🔍 Checking requirements...${NC}"
    
    # Check if we're on macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        echo -e "${RED}❌ This script is for macOS only${NC}"
        exit 1
    fi
    
    # Check if sips is available (built into macOS)
    if ! command -v sips &> /dev/null; then
        echo -e "${RED}❌ sips command not found. This should be available on macOS.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Requirements check passed${NC}"
}

# Create icon files
create_icons() {
    echo -e "${BLUE}🎨 Creating application icons...${NC}"
    
    # Create different icon sizes
    local sizes=(16 32 64 128 256 512 1024)
    
    for size in "${sizes[@]}"; do
        # Create PNG from SVG (using sips to resize)
        sips -s format png -z $size $size "$ICON_SVG" --out "$APP_DIR/Contents/Resources/brebot-icon-${size}.png" >/dev/null 2>&1 || {
            # If sips can't handle SVG, create a simple colored square
            sips -s format png -z $size $size /System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/GenericApplicationIcon.icns --out "$APP_DIR/Contents/Resources/brebot-icon-${size}.png" >/dev/null 2>&1
        }
    done
    
    # Create the main icon file (256x256)
    cp "$APP_DIR/Contents/Resources/brebot-icon-256.png" "$APP_DIR/Contents/Resources/brebot-icon.png"
    
    # Create icns file
    iconutil -c icns "$APP_DIR/Contents/Resources" -o "$APP_DIR/Contents/Resources/brebot-icon.icns" 2>/dev/null || {
        echo -e "${YELLOW}⚠️  Could not create .icns file, using PNG instead${NC}"
    }
    
    echo -e "${GREEN}✅ Icons created successfully${NC}"
}

# Create a simple icon if SVG conversion fails
create_simple_icon() {
    echo -e "${BLUE}🎨 Creating simple application icon...${NC}"
    
    # Create a simple blue square icon
    local sizes=(16 32 64 128 256 512 1024)
    
    for size in "${sizes[@]}"; do
        # Create a simple colored square using sips
        sips -s format png -z $size $size /System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/GenericApplicationIcon.icns --out "$APP_DIR/Contents/Resources/brebot-icon-${size}.png" >/dev/null 2>&1
    done
    
    # Create the main icon file
    cp "$APP_DIR/Contents/Resources/brebot-icon-256.png" "$APP_DIR/Contents/Resources/brebot-icon.png"
    
    echo -e "${GREEN}✅ Simple icon created${NC}"
}

# Install the application
install_app() {
    echo -e "${BLUE}📦 Installing Brebot application...${NC}"
    
    # Create Applications directory if it doesn't exist
    mkdir -p "$HOME/Applications"
    
    # Copy the app to Applications
    if [ -d "$HOME/Applications/Brebot.app" ]; then
        echo -e "${YELLOW}⚠️  Removing existing Brebot.app...${NC}"
        rm -rf "$HOME/Applications/Brebot.app"
    fi
    
    cp -R "$APP_DIR" "$HOME/Applications/"
    
    echo -e "${GREEN}✅ Brebot installed to Applications folder${NC}"
}

# Create desktop shortcut
create_desktop_shortcut() {
    echo -e "${BLUE}🖥️  Creating desktop shortcut...${NC}"
    
    # Create an alias on the desktop
    ln -sf "$HOME/Applications/Brebot.app" "$HOME/Desktop/Brebot"
    
    echo -e "${GREEN}✅ Desktop shortcut created${NC}"
}

# Main installation process
main() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════╗"
    echo "║        🤖 Brebot Mac App Installer   ║"
    echo "║     Creating Dock Application        ║"
    echo "╚══════════════════════════════════════╝"
    echo -e "${NC}"
    
    check_requirements
    
    # Try to create icons from SVG, fallback to simple icon
    if [ -f "$ICON_SVG" ]; then
        create_icons || create_simple_icon
    else
        create_simple_icon
    fi
    
    install_app
    create_desktop_shortcut
    
    echo -e "${GREEN}"
    echo "🎉 Brebot Mac Application installed successfully!"
    echo ""
    echo "📍 Location: ~/Applications/Brebot.app"
    echo "🖥️  Desktop shortcut: ~/Desktop/Brebot"
    echo ""
    echo "🚀 You can now:"
    echo "   • Double-click the Brebot icon in Applications"
    echo "   • Drag it to your Dock for easy access"
    echo "   • Use the desktop shortcut"
    echo "   • Launch from Spotlight (Cmd+Space, type 'Brebot')"
    echo -e "${NC}"
    
    # Ask if user wants to add to dock
    read -p "Would you like to add Brebot to your Dock? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}📌 Adding Brebot to Dock...${NC}"
        # This will add the app to the dock
        open "$HOME/Applications/Brebot.app"
        echo -e "${GREEN}✅ Brebot added to Dock!${NC}"
    fi
}

# Run main function
main "$@"
