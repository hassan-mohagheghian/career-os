use anyhow::Result;

use crate::config::Config;
use crate::DockerCommands;
use crate::ui::format;

pub async fn run(action: Option<DockerCommands>) -> Result<()> {
    let config = Config::load()?;

    match action {
        Some(DockerCommands::Up) => {
            format::log("Starting docker containers...");
            let status = std::process::Command::new("docker")
                .args(["compose", "up", "-d"])
                .current_dir(&config.repo_root)
                .status()?;
            if status.success() {
                format::ok("Docker containers started.");
            } else {
                anyhow::bail!("Docker compose up failed");
            }
        }
        Some(DockerCommands::Down) => {
            format::log("Stopping docker containers...");
            let status = std::process::Command::new("docker")
                .args(["compose", "down"])
                .current_dir(&config.repo_root)
                .status()?;
            if status.success() {
                format::ok("Docker containers stopped.");
            } else {
                anyhow::bail!("Docker compose down failed");
            }
        }
        Some(DockerCommands::Status) => {
            format::log("Docker container status:");
            let status = std::process::Command::new("docker")
                .args(["compose", "ps"])
                .current_dir(&config.repo_root)
                .status()?;
            if !status.success() {
                anyhow::bail!("Docker compose ps failed");
            }
        }
        None => {
            format::log("Usage: start docker <up|down|status>");
        }
    }

    Ok(())
}
