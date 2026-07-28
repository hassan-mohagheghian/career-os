use anyhow::Result;

use crate::config::Config;
use crate::ui::format;

pub async fn run() -> Result<()> {
    let config = Config::load()?;
    format::log("Running linters...");

    let mut failed = false;

    format::log("Linting backend (ruff)...");
    let python = config.python()?;
    let ruff_status = std::process::Command::new(&python)
        .args(["-m", "ruff", "check", "app/server"])
        .current_dir(&config.repo_root)
        .status();
    match ruff_status {
        Ok(s) if !s.success() => {
            format::warn("Ruff lint issues found");
            failed = true;
        }
        Ok(_) => format::ok("Ruff: OK"),
        Err(_) => format::warn("Ruff not available, skipping"),
    }

    format::log("Linting frontend (eslint)...");
    let eslint_status = std::process::Command::new("npm")
        .args(["run", "lint"])
        .current_dir(&config.client_dir)
        .status();
    match eslint_status {
        Ok(s) if !s.success() => {
            format::warn("ESLint issues found");
            failed = true;
        }
        Ok(_) => format::ok("ESLint: OK"),
        Err(_) => format::warn("ESLint not available, skipping"),
    }

    if failed {
        anyhow::bail!("Linting found issues");
    }

    format::ok("All linters passed.");
    Ok(())
}
