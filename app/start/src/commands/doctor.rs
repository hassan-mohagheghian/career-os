use anyhow::Result;

use crate::config::Config;
use crate::ui::format;
use crate::utils::check_tool;

pub async fn run() -> Result<()> {
    let config = Config::load()?;
    format::header("Environment Check");

    let mut all_ok = true;

    let tools: Vec<(&str, &[&str])> = vec![
        ("rustc", &["--version"]),
        ("cargo", &["--version"]),
        ("python3", &["--version"]),
        ("node", &["--version"]),
        ("npm", &["--version"]),
        ("docker", &["--version"]),
        ("git", &["--version"]),
    ];

    for (tool, args) in tools {
        let (ok, msg) = check_tool(tool, args);
        if ok {
            format::ok(&msg);
        } else {
            format::err(&msg);
            all_ok = false;
        }
    }

    if config.venv_dir.exists() {
        format::ok(&format!("Python venv: {}", config.venv_dir.display()));
    } else {
        format::warn("Python venv not found (expected at .venv/)");
    }

    if config.server_dir.exists() {
        format::ok(&format!("Server dir: {}", config.server_dir.display()));
    } else {
        format::err("Server directory not found");
        all_ok = false;
    }

    if config.client_dir.exists() {
        format::ok(&format!("Client dir: {}", config.client_dir.display()));
    } else {
        format::err("Client directory not found");
        all_ok = false;
    }

    if config.repo_root.join(".env").exists() {
        format::ok(".env file found");
    } else {
        format::warn(".env file not found");
    }

    println!();
    if all_ok {
        format::ok("All checks passed! Environment is ready.");
    } else {
        format::warn("Some checks failed. Please fix the issues above.");
    }

    Ok(())
}
