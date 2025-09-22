# Brebot Mac Application Setup

Yes! You can absolutely have a nice icon in your Mac dock to launch Brebot with a single click. I've created a complete Mac application bundle for you.

## 🚀 Quick Setup

### Option 1: Full Mac App (Recommended)

```bash
# Navigate to the mac-app directory
cd mac-app

# Run the installer
./install-app.sh
```

This will:
- Create a proper Mac application bundle
- Generate application icons
- Install Brebot.app to your Applications folder
- Create a desktop shortcut
- Optionally add it to your Dock

### Option 2: Simple Launcher Script

```bash
# Make the launcher executable (if not already)
chmod +x launch-brebot.sh

# Run the launcher
./launch-brebot.sh
```

## 🎯 What You Get

### Mac Application Bundle
- **Brebot.app** in your Applications folder
- **Custom robot icon** in your dock
- **Native Mac integration** with notifications
- **Spotlight search** support (Cmd+Space, type "Brebot")

### Features
- **One-click launch** from dock or Applications
- **Interactive menu** with options:
  - Start Web Interface
  - Start Docker Services
  - Check System Status
  - Open File Organizer
  - View Logs
  - Stop All Services
- **Native notifications** for status updates
- **Automatic browser opening** for web interface

## 🎨 Application Features

### Main Menu Options
1. **Start Web Interface**: Launches the full web interface
2. **Start Docker Services**: Starts all Docker containers
3. **Check System Status**: Shows health of all services
4. **Open File Organizer**: Interactive file organization
5. **View Logs**: Opens system logs in Console
6. **Stop All Services**: Cleanly stops everything

### Smart Features
- **Docker Detection**: Checks if Docker is running
- **Service Health**: Monitors all Brebot services
- **Auto-Open Browser**: Opens web interface automatically
- **Native Notifications**: Mac-style notifications
- **Error Handling**: Clear error messages and recovery

## 📱 How to Use

### After Installation
1. **Find Brebot.app** in your Applications folder
2. **Drag to Dock** for easy access
3. **Double-click** to launch
4. **Choose your action** from the menu
5. **Enjoy** your AI-powered file organization!

### Dock Integration
- **Right-click** the dock icon for quick actions
- **Badge notifications** for system status
- **Bounce animation** when starting services
- **Native Mac look and feel**

## 🔧 Customization

### Icon Customization
The app includes a custom robot icon, but you can replace it:
1. Replace `mac-app/brebot-icon.svg` with your own
2. Run `./install-app.sh` again
3. The new icon will be applied

### Menu Customization
Edit `mac-app/Brebot.app/Contents/MacOS/brebot` to:
- Add new menu options
- Change default actions
- Modify notifications
- Customize the interface

## 🛠️ Troubleshooting

### App Won't Launch
```bash
# Check permissions
chmod +x mac-app/Brebot.app/Contents/MacOS/brebot

# Reinstall the app
cd mac-app
./install-app.sh
```

### Icon Not Showing
```bash
# Clear icon cache
sudo rm -rfv /Library/Caches/com.apple.iconservices.store
killall Finder
```

### Services Not Starting
- Ensure Docker Desktop is running
- Check if ports 8000, 3000, 11434 are available
- Run the status check from the app menu

## 🎉 Benefits

### User Experience
- **Professional appearance** with native Mac integration
- **One-click access** to all Brebot features
- **Visual feedback** with notifications and status
- **Familiar interface** that feels like a native Mac app

### Productivity
- **Quick launch** from dock or Spotlight
- **No command-line** knowledge required
- **Visual status** of all services
- **Easy management** of AI agents

### Integration
- **Dock integration** with custom icon
- **Spotlight search** support
- **Native notifications** for status updates
- **System integration** with proper app bundle

## 📋 System Requirements

- **macOS 10.15** (Catalina) or later
- **Docker Desktop** installed and running
- **Python 3.11+** (handled by the app)
- **8GB+ RAM** for local LLM

## 🚀 Advanced Usage

### Command Line Integration
You can still use the command line:
```bash
# Direct CLI access
python src/main.py web

# Or use the launcher script
./launch-brebot.sh
```

### Automation
The app can be integrated with:
- **Automator** workflows
- **Shortcuts** app
- **AppleScript** automation
- **Cron jobs** for scheduled tasks

## 🎨 Customization Examples

### Adding Custom Menu Items
Edit the `brebot` script to add new options:
```bash
# Add to the menu
"Custom Command"|"custom_command")
    # Your custom code here
    ;;
```

### Custom Notifications
Modify notification messages:
```bash
show_notification "Custom Title" "Your custom message"
```

### Custom Icons
Replace the SVG icon with your own design and reinstall.

---

**Your Brebot system now has a professional Mac application that integrates seamlessly with your workflow! 🚀**

**Install it now:**
```bash
cd mac-app
./install-app.sh
```

Then drag Brebot.app to your dock and enjoy one-click access to your AI agent system!
