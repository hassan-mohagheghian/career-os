use anyhow::Result;
use tokio::signal;

use crate::config::Config;
use crate::process::ManagedProcess;
use crate::ui::format;

pub async fn run(config: Config) -> Result<()> {
    format::log("Starting all services...");
    println!();

    start_backend_inner(&config).await?;
    tokio::time::sleep(std::time::Duration::from_secs(2)).await;
    start_frontend_inner(&config).await?;

    println!();
    format::ok("All services started!");
    println!();
    println!("  Backend:  http://localhost:{}", config.backend_port);
    println!("  Frontend: http://localhost:{}", config.frontend_port);
    println!();
    println!("  Press Ctrl+C to stop all services");
    println!();

    signal::ctrl_c().await?;
    println!();
    format::log("Shutting down...");

    let backend = ManagedProcess::new("backend", config.pid_file.clone());
    let frontend = ManagedProcess::new("frontend", config.client_pid_file.clone());

    backend.stop()?;
    frontend.stop()?;
    crate::process::kill_by_pattern("mimo run")?;

    format::ok("All processes stopped.");
    Ok(())
}

pub async fn start_backend_inner(config: &Config) -> Result<()> {
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
    let output = std::process::Command::new(&python)
        .args([
            "-m", "uvicorn", "app.server.entrypoints.api:app",
            "--host", "0.0.0.0", "--port", &port_str, "--reload",
        ])
        .current_dir(&config.repo_root)
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::piped())
        .spawn()?;

    let pid = output.id();
    let backend = ManagedProcess::new("backend", config.pid_file.clone());
    backend.save_pid(pid)?;
    format::ok(&format!(
        "Backend started (PID: {}) on http://localhost:{}",
        pid, config.backend_port
    ));

    Ok(())
}

async fn start_frontend_inner(config: &Config) -> Result<()> {
    format::log("Starting frontend dev server...");

    let port_str = config.frontend_port.to_string();
    let output = std::process::Command::new("npm")
        .args(["run", "dev", "--", "--port", &port_str])
        .current_dir(&config.client_dir)
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::piped())
        .spawn()?;

    let pid = output.id();
    let frontend = ManagedProcess::new("frontend", config.client_pid_file.clone());
    frontend.save_pid(pid)?;
    format::ok(&format!(
        "Frontend started (PID: {}) on http://localhost:{}",
        pid, config.frontend_port
    ));

    Ok(())
}
