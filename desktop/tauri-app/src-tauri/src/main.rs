#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::path::Path;
use std::process::Command;
use tauri::{AppHandle, Manager};

fn repo_root() -> Result<std::path::PathBuf, String> {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    std::fs::canonicalize(root).map_err(|e| e.to_string())
}

#[tauri::command]
async fn open_backend(app: AppHandle) -> Result<(), String> {
    let url = "http://localhost:8000";
    tauri::api::shell::open(&app.shell_scope(), url, None).map_err(|e| e.to_string())
}

#[tauri::command]
async fn open_pwa_in_chrome() -> Result<(), String> {
    let url = "http://127.0.0.1:8000";
    
    // Try to open in Chrome specifically
    let chrome_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser"
    ];
    
    for chrome_path in &chrome_paths {
        if std::path::Path::new(chrome_path).exists() {
            let mut cmd = Command::new(chrome_path);
            cmd.arg("--new-window")
               .arg("--app")
               .arg("--user-data-dir=/tmp/brebot-chrome")
               .arg("--no-first-run")
               .arg("--no-default-browser-check")
               .arg(url);
            
            match cmd.spawn() {
                Ok(_) => return Ok(()),
                Err(e) => println!("Failed to launch Chrome at {}: {}", chrome_path, e),
            }
        }
    }
    
    // Fallback to default browser
    let mut cmd = Command::new("open");
    cmd.arg(url);
    cmd.spawn()
        .map_err(|e| format!("Failed to open browser: {e}"))?;
    Ok(())
}

#[tauri::command]
async fn navigate_to_dashboard(app: AppHandle) -> Result<(), String> {
    let url = "http://127.0.0.1:8000";
    
    // Get the main window
    if let Some(window) = app.get_window("main") {
        window.eval(&format!("window.location.href = '{}';", url))
            .map_err(|e| format!("Failed to navigate: {e}"))?;
    } else {
        return Err("Main window not found".to_string());
    }
    
    Ok(())
}

#[tauri::command]
async fn start_backend() -> Result<(), String> {
    let root = repo_root()?;
    println!("Repo root: {:?}", root);

    let venv_python = root.join("venv/bin/python3");
    println!("Venv python path: {:?}", venv_python);
    println!("Venv python exists: {}", venv_python.exists());
    
    let interpreter = if venv_python.exists() {
        venv_python
    } else {
        Path::new("python3").to_path_buf()
    };
    println!("Using interpreter: {:?}", interpreter);

    let mut cmd = Command::new(&interpreter);
    cmd.current_dir(&root)
        .args(["src/main.py", "web"]);
    
    println!("Running command: {:?}", cmd);
    
    cmd.spawn()
        .map_err(|e| format!("Failed to launch backend: {e}"))?;
    Ok(())
}

#[tauri::command]
async fn start_services() -> Result<(), String> {
    let root = repo_root()?;
    println!("Starting services from: {:?}", root);
    
    let mut cmd = Command::new("docker");
    cmd.current_dir(&root)
        .args([
            "compose",
            "-f",
            "docker/docker-compose.yml",
            "up",
            "-d",
            "chromadb",
            "redis",
        ]);
    
    println!("Running Docker command: {:?}", cmd);
    
    cmd.spawn()
        .map_err(|e| format!("Failed to start Docker services: {e}"))?;
    Ok(())
}

#[tauri::command]
async fn check_backend_health() -> Result<String, String> {
    let client = reqwest::Client::new();
    match client.get("http://127.0.0.1:8000/api/health").send().await {
        Ok(response) => {
            if response.status().is_success() {
                match response.text().await {
                    Ok(body) => Ok(body),
                    Err(e) => Err(format!("Failed to read response: {e}")),
                }
            } else {
                Err(format!("Backend responded with status: {}", response.status()))
            }
        }
        Err(e) => Err(format!("Failed to connect to backend: {e}")),
    }
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![open_backend, open_pwa_in_chrome, navigate_to_dashboard, start_backend, start_services, check_backend_health])
        .run(tauri::generate_context!())
        .expect("error while running Brebot Desktop");
}
