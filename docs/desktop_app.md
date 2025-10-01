# Brebot Desktop Wrapper

A lightweight Tauri application lives in `desktop/tauri-app/`. It wraps the FastAPI dashboard so you have a dedicated desktop window on macOS (and later Windows/Linux if needed).

## Prerequisites
- Node.js 18+
- Rust toolchain (install via `rustup`)
- Docker (optional, for starting supporting services)
- Python environment ready for `python3 src/main.py web`

## Usage
```bash
cd desktop/tauri-app
npm install
npm run dev     # launches Brebot Desktop in development

# When you're ready to bundle a native app
npm run build   # produces .app/.dmg under src-tauri/target/release
```

The window polls `http://localhost:8000/api/health`. Once the backend reports healthy, the PWA dashboard opens in Chrome in app mode.

### Launch workflow from the desktop app
Buttons inside the wrapper do the heavy lifting:
- **Start Chroma & Redis** runs `docker compose -f docker/docker-compose.yml up -d chromadb redis` from the repo root.
- **Launch Brebot Backend** spawns `python3 src/main.py web` in the repo root (make sure your virtualenv is active or Python dependencies are global).
- **Check Status** re-runs the health probe.
- **Open PWA Dashboard** launches the dashboard in Chrome in app mode.

If services are already running, the commands simply return immediately.

### Icons
Brebot ships with a generated icon set under `desktop/tauri-app/src-tauri/icons/`. Replace `icon-1024.png` with your own artwork and rerun the resize step if you want different branding.

## Customising
- `static/index.html` – UI shell that hosts the launcher interface and status log
- `static/style.css` – styling for the launcher interface
- `tauri.conf.json` – tweak window defaults, bundle identifier, etc.

The desktop app now acts as a smart launcher that opens the PWA dashboard in Chrome in app mode, providing a native desktop experience with web technology.
