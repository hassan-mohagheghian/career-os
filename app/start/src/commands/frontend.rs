use anyhow::Result;

use crate::config::Config;
use crate::process::ManagedProcess;
use crate::ui::format;

pub async fn run(config: Config) -> Result<()> {
    format::log("Starting frontend dev server...");

    let port_str = config.frontend_port.to_string();
    let child = std::process::Command::new("npm")
        .args(["run", "dev", "--", "--port", &port_str])
        .current_dir(&config.client_dir)
        .spawn()?;

    let pid = child.id();
    let frontend = ManagedProcess::new("frontend", config.client_pid_file.clone());
    frontend.save_pid(pid)?;
    format::ok(&format!(
        "Frontend started (PID: {}) on http://localhost:{}",
        pid, config.frontend_port
    ));

    tokio::signal::ctrl_c().await?;
    format::log("Shutting down frontend...");
    frontend.stop()?;
    format::ok("Frontend stopped.");

    Ok(())
}
