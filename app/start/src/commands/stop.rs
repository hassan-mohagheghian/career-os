use anyhow::Result;

use crate::config::Config;
use crate::process::ManagedProcess;
use crate::ui::format;

pub async fn run() -> Result<()> {
    let config = Config::load()?;
    format::log("Stopping all processes...");

    let backend = ManagedProcess::new("backend", config.pid_file.clone());
    let frontend = ManagedProcess::new("frontend", config.client_pid_file.clone());

    backend.stop()?;
    frontend.stop()?;
    crate::process::kill_by_pattern("mimo run")?;

    format::ok("All processes stopped.");
    Ok(())
}
