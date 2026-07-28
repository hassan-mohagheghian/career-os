use anyhow::{Context, Result};
use std::path::PathBuf;

pub struct Config {
    pub repo_root: PathBuf,
    pub server_dir: PathBuf,
    pub client_dir: PathBuf,
    pub pid_file: PathBuf,
    pub client_pid_file: PathBuf,
    pub venv_dir: PathBuf,
    pub backend_port: u16,
    pub frontend_port: u16,
}

impl Config {
    pub fn load() -> Result<Self> {
        let exe_path = std::env::current_exe().context("Failed to get current exe path")?;
        let exe_dir = exe_path
            .parent()
            .context("Failed to get exe parent directory")?;

        let repo_root = if exe_dir.join("app").exists() {
            exe_dir.to_path_buf()
        } else {
            std::env::current_dir().context("Failed to get current directory")?
        };

        let server_dir = repo_root.join("app").join("server");
        let client_dir = repo_root.join("app").join("client");
        let pid_file = repo_root.join(".server.pid");
        let client_pid_file = repo_root.join(".client.pid");
        let venv_dir = repo_root.join(".venv");

        let backend_port = load_port_from_env(&repo_root, "BACKEND_PORT", 5000);
        let frontend_port = load_port_from_env(&repo_root, "FRONTEND_PORT", 5173);

        Ok(Config {
            repo_root,
            server_dir,
            client_dir,
            pid_file,
            client_pid_file,
            venv_dir,
            backend_port,
            frontend_port,
        })
    }

    pub fn with_backend_port(mut self, port: u16) -> Self {
        self.backend_port = port;
        self
    }

    pub fn with_frontend_port(mut self, port: u16) -> Self {
        self.frontend_port = port;
        self
    }

    pub fn python(&self) -> Result<String> {
        let venv_python = self.venv_dir.join("bin").join("python");
        if venv_python.exists() {
            return Ok(venv_python.to_string_lossy().to_string());
        }
        Ok("python3".to_string())
    }

    pub fn alembic(&self) -> Result<String> {
        let venv_alembic = self.venv_dir.join("bin").join("alembic");
        if venv_alembic.exists() {
            return Ok(venv_alembic.to_string_lossy().to_string());
        }
        Ok("alembic".to_string())
    }
}

fn load_port_from_env(repo_root: &PathBuf, key: &str, default: u16) -> u16 {
    let env_file = repo_root.join(".env");
    if let Ok(content) = std::fs::read_to_string(env_file) {
        for line in content.lines() {
            let line = line.trim();
            if line.starts_with('#') || line.is_empty() {
                continue;
            }
            if let Some((k, v)) = line.split_once('=') {
                if k.trim() == key {
                    if let Ok(port) = v.trim().parse::<u16>() {
                        return port;
                    }
                }
            }
        }
    }

    std::env::var(key)
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(default)
}
