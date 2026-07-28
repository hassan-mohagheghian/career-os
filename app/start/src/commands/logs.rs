use anyhow::Result;

use crate::config::Config;
use crate::ui::format;

pub async fn run() -> Result<()> {
    let config = Config::load()?;
    format::log("Streaming logs...");

    let log_file = config.repo_root.join("tmp").join("app.log");
    if log_file.exists() {
        let _output = std::process::Command::new("tail")
            .args(["-f", log_file.to_str().unwrap()])
            .status()?;
    } else {
        format::warn("No log file found at tmp/app.log");
        format::log("Starting log tail from journalctl...");
        let _ = std::process::Command::new("journalctl")
            .args(["-f", "-u", "job-search"])
            .status();
    }

    Ok(())
}
