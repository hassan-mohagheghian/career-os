use anyhow::Result;
use std::fs;

use crate::config::Config;
use crate::ui::format;

pub async fn run() -> Result<()> {
    let config = Config::load()?;
    format::log("Cleaning build artifacts...");

    let dirs_to_clean = vec![
        config.repo_root.join("app").join("server").join("__pycache__"),
        config.repo_root.join("app").join("client").join("node_modules").join(".cache"),
        config.repo_root.join("target"),
        config.repo_root.join("app").join("start").join("target"),
        config.repo_root.join("tmp"),
        config.repo_root.join(".pytest_cache"),
    ];

    for dir in &dirs_to_clean {
        if dir.exists() {
            fs::remove_dir_all(dir).ok();
            format::ok(&format!("Removed: {}", dir.display()));
        }
    }

    format::ok("Clean completed.");
    Ok(())
}
