use anyhow::Result;

use crate::config::Config;
use crate::process::ManagedProcess;
use crate::ui::format;

pub async fn run(config: Config) -> Result<()> {
    format::log("Starting backend server...");

    let python = config.python()?;
    format::log(&format!("Using Python: {}", python));

    let alembic = config.alembic();
    if let Ok(alembic_path) = alembic {
        if std::path::Path::new(&alembic_path).exists() {
            format::log("Running database migrations...");
            let migrate_output = std::process::Command::new(&alembic_path)
                .args(["upgrade", "head"])
                .current_dir(&config.repo_root)
                .output();

            match migrate_output {
                Ok(output) => {
                    if !output.status.success() {
                        format::warn("Alembic migration warning (non-fatal)");
                    }
                }
                Err(_) => {
                    format::warn("Alembic migration warning (non-fatal)");
                }
            }
        }
    }

    let port_str = config.backend_port.to_string();
    let child = std::process::Command::new(&python)
        .args([
            "-m", "uvicorn", "app.server.entrypoints.api:app",
            "--host", "0.0.0.0", "--port", &port_str, "--reload",
        ])
        .current_dir(&config.repo_root)
        .spawn()?;

    let pid = child.id();
    let backend = ManagedProcess::new("backend", config.pid_file.clone());
    backend.save_pid(pid)?;
    format::ok(&format!(
        "Backend started (PID: {}) on http://localhost:{}",
        pid, config.backend_port
    ));

    tokio::signal::ctrl_c().await?;
    format::log("Shutting down backend...");
    backend.stop()?;
    crate::process::kill_by_pattern("mimo run")?;
    format::ok("Backend stopped.");

    Ok(())
}
