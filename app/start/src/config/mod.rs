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

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;

    #[test]
    fn test_load_port_from_env_file() {
        let dir = std::env::temp_dir().join("config_test_env");
        std::fs::create_dir_all(&dir).unwrap();
        let env_path = dir.join(".env");
        let mut f = std::fs::File::create(&env_path).unwrap();
        writeln!(f, "BACKEND_PORT=8080").unwrap();
        writeln!(f, "FRONTEND_PORT=3000").unwrap();

        let port = load_port_from_env(&dir, "BACKEND_PORT", 5000);
        assert_eq!(port, 8080);

        let port = load_port_from_env(&dir, "FRONTEND_PORT", 5173);
        assert_eq!(port, 3000);

        let port = load_port_from_env(&dir, "OTHER_PORT", 9999);
        assert_eq!(port, 9999);

        std::fs::remove_dir_all(&dir).unwrap();
    }

    #[test]
    fn test_load_port_from_env_ignores_comments_and_empty() {
        let dir = std::env::temp_dir().join("config_test_comments");
        std::fs::create_dir_all(&dir).unwrap();
        let env_path = dir.join(".env");
        let mut f = std::fs::File::create(&env_path).unwrap();
        writeln!(f, "").unwrap();
        writeln!(f, "# This is a comment").unwrap();
        writeln!(f, "  ").unwrap();
        writeln!(f, "PORT=1234").unwrap();

        let port = load_port_from_env(&dir, "PORT", 5000);
        assert_eq!(port, 1234);

        std::fs::remove_dir_all(&dir).unwrap();
    }

    #[test]
    fn test_load_port_from_env_no_file() {
        let dir = std::env::temp_dir().join("config_test_no_file");
        std::fs::create_dir_all(&dir).unwrap();

        let port = load_port_from_env(&dir, "BACKEND_PORT", 5000);
        assert_eq!(port, 5000);

        std::fs::remove_dir_all(&dir).unwrap();
    }

    #[test]
    fn test_load_port_from_env_invalid_value() {
        let dir = std::env::temp_dir().join("config_test_invalid");
        std::fs::create_dir_all(&dir).unwrap();
        let env_path = dir.join(".env");
        let mut f = std::fs::File::create(&env_path).unwrap();
        writeln!(f, "BACKEND_PORT=not_a_number").unwrap();

        let port = load_port_from_env(&dir, "BACKEND_PORT", 5000);
        assert_eq!(port, 5000);

        std::fs::remove_dir_all(&dir).unwrap();
    }

    #[test]
    fn test_config_with_backend_port() {
        let dir = std::env::temp_dir().join("config_test_with_port");
        std::fs::create_dir_all(&dir).unwrap();
        std::env::set_current_dir(&dir).unwrap();

        let config = Config {
            repo_root: dir.clone(),
            server_dir: dir.join("app").join("server"),
            client_dir: dir.join("app").join("client"),
            pid_file: dir.join(".server.pid"),
            client_pid_file: dir.join(".client.pid"),
            venv_dir: dir.join(".venv"),
            backend_port: 5000,
            frontend_port: 5173,
        };

        let updated = config.with_backend_port(9000);
        assert_eq!(updated.backend_port, 9000);
        assert_eq!(updated.frontend_port, 5173);

        std::fs::remove_dir_all(&dir).unwrap();
    }

    #[test]
    fn test_config_with_frontend_port() {
        let dir = std::env::temp_dir().join("config_test_with_fport");
        std::fs::create_dir_all(&dir).unwrap();
        std::env::set_current_dir(&dir).unwrap();

        let config = Config {
            repo_root: dir.clone(),
            server_dir: dir.join("app").join("server"),
            client_dir: dir.join("app").join("client"),
            pid_file: dir.join(".server.pid"),
            client_pid_file: dir.join(".client.pid"),
            venv_dir: dir.join(".venv"),
            backend_port: 5000,
            frontend_port: 5173,
        };

        let updated = config.with_frontend_port(3000);
        assert_eq!(updated.backend_port, 5000);
        assert_eq!(updated.frontend_port, 3000);

        std::fs::remove_dir_all(&dir).unwrap();
    }

    #[test]
    fn test_python_from_venv() {
        let dir = std::env::temp_dir().join("config_test_python");
        std::fs::create_dir_all(&dir).unwrap();
        std::env::set_current_dir(&dir).unwrap();

        let config = Config {
            repo_root: dir.clone(),
            server_dir: dir.join("app").join("server"),
            client_dir: dir.join("app").join("client"),
            pid_file: dir.join(".server.pid"),
            client_pid_file: dir.join(".client.pid"),
            venv_dir: dir.join(".venv"),
            backend_port: 5000,
            frontend_port: 5173,
        };

        let python = config.python().unwrap();
        assert_eq!(python, "python3");

        std::fs::remove_dir_all(&dir).unwrap();
    }

    #[test]
    fn test_alembic_falls_back() {
        let dir = std::env::temp_dir().join("config_test_alembic");
        std::fs::create_dir_all(&dir).unwrap();
        std::env::set_current_dir(&dir).unwrap();

        let config = Config {
            repo_root: dir.clone(),
            server_dir: dir.join("app").join("server"),
            client_dir: dir.join("app").join("client"),
            pid_file: dir.join(".server.pid"),
            client_pid_file: dir.join(".client.pid"),
            venv_dir: dir.join(".venv"),
            backend_port: 5000,
            frontend_port: 5173,
        };

        let alembic = config.alembic().unwrap();
        assert_eq!(alembic, "alembic");

        std::fs::remove_dir_all(&dir).unwrap();
    }
}
