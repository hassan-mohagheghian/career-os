use anyhow::Result;

use crate::config::Config;
use crate::process::ManagedProcess;
use crate::ui::format;

pub async fn run() -> Result<()> {
    let config = Config::load()?;

    format::header("Job Search App Status");

    let backend = ManagedProcess::new("backend", config.pid_file.clone());
    if backend.is_running() {
        let pid = backend.read_pid().unwrap_or(0);
        format::ok(&format!(
            "Backend:  Running (PID: {}) — http://localhost:{}",
            pid, config.backend_port
        ));
    } else {
        format::warn("Backend:  Not running");
    }

    let frontend = ManagedProcess::new("frontend", config.client_pid_file.clone());
    if frontend.is_running() {
        let pid = frontend.read_pid().unwrap_or(0);
        format::ok(&format!(
            "Frontend: Running (PID: {}) — http://localhost:{}",
            pid, config.frontend_port
        ));
    } else {
        format::warn("Frontend: Not running");
    }

    let output = std::process::Command::new("pgrep")
        .args(["-f", "mimo run"])
        .output();
    match output {
        Ok(o) => {
            let count = String::from_utf8_lossy(&o.stdout)
                .lines()
                .filter(|l| !l.is_empty())
                .count();
            if count > 0 {
                format::warn(&format!("Mimo AI:  {} process(es) running", count));
            } else {
                format::ok("Mimo AI:  No processes running");
            }
        }
        Err(_) => {
            format::ok("Mimo AI:  No processes running");
        }
    }

    if config.repo_root.join(".env").exists() {
        let env_content = std::fs::read_to_string(config.repo_root.join(".env")).unwrap_or_default();
        let ai_provider = env_content
            .lines()
            .find(|l| l.starts_with("AI_PROVIDER="))
            .and_then(|l| l.split('=').nth(1))
            .unwrap_or("mimo");
        format::ok(&format!("AI Provider: {}", ai_provider));
    }

    println!();
    Ok(())
}
