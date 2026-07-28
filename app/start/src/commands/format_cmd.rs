use anyhow::Result;

use crate::config::Config;
use crate::ui::format;

pub async fn run() -> Result<()> {
    let config = Config::load()?;
    format::log("Running formatters...");

    let mut failed = false;

    format::log("Formatting backend (ruff)...");
    let python = config.python()?;
    let ruff_status = std::process::Command::new(&python)
        .args(["-m", "ruff", "format", "app/server"])
        .current_dir(&config.repo_root)
        .status();
    match ruff_status {
        Ok(s) if !s.success() => {
            format::warn("Ruff format issues");
            failed = true;
        }
        Ok(_) => format::ok("Ruff format: OK"),
        Err(_) => format::warn("Ruff not available, skipping"),
    }

    format::log("Formatting frontend (prettier)...");
    let prettier_status = std::process::Command::new("npm")
        .args(["run", "format"])
        .current_dir(&config.client_dir)
        .status();
    match prettier_status {
        Ok(s) if !s.success() => {
            format::warn("Prettier format issues");
            failed = true;
        }
        Ok(_) => format::ok("Prettier: OK"),
        Err(_) => format::warn("Prettier not available, skipping"),
    }

    if failed {
        anyhow::bail!("Formatting found issues");
    }

    format::ok("All formatters passed.");
    Ok(())
}
