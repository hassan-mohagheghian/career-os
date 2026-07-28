use anyhow::{Context, Result};
use std::fs;
use std::path::PathBuf;
use tokio::process::Command;

pub struct ManagedProcess {
    pub name: String,
    pub pid_file: PathBuf,
}

impl ManagedProcess {
    pub fn new(name: &str, pid_file: PathBuf) -> Self {
        Self {
            name: name.to_string(),
            pid_file,
        }
    }

    pub fn save_pid(&self, pid: u32) -> Result<()> {
        fs::write(&self.pid_file, pid.to_string())
            .with_context(|| format!("Failed to write PID file for {}", self.name))?;
        Ok(())
    }

    pub fn read_pid(&self) -> Option<u32> {
        fs::read_to_string(&self.pid_file)
            .ok()
            .and_then(|s| s.trim().parse().ok())
    }

    pub fn is_running(&self) -> bool {
        self.read_pid()
            .map(|pid| is_process_alive(pid))
            .unwrap_or(false)
    }

    pub fn stop(&self) -> Result<()> {
        if let Some(pid) = self.read_pid() {
            if is_process_alive(pid) {
                tracing::info!("Stopping {} (PID: {})", self.name, pid);
                kill_process(pid)?;
            }
        }
        let _ = fs::remove_file(&self.pid_file);
        Ok(())
    }
}

pub fn is_process_alive(pid: u32) -> bool {
    unsafe { libc::kill(pid as i32, 0) == 0 }
}

pub fn kill_process(pid: u32) -> Result<()> {
    unsafe {
        libc::kill(pid as i32, libc::SIGTERM);
    }
    std::thread::sleep(std::time::Duration::from_millis(500));
    if is_process_alive(pid) {
        unsafe {
            libc::kill(pid as i32, libc::SIGKILL);
        }
    }
    Ok(())
}

pub async fn run_command(name: &str, command: &mut Command) -> Result<()> {
    let mut child = command
        .spawn()
        .with_context(|| format!("Failed to spawn {}", name))?;

    let status = child
        .wait()
        .await
        .with_context(|| format!("Failed to wait for {}", name))?;

    if !status.success() {
        anyhow::bail!("{} exited with status: {}", name, status);
    }
    Ok(())
}

pub fn kill_by_pattern(pattern: &str) -> Result<()> {
    let output = std::process::Command::new("pkill")
        .args(["-f", pattern])
        .output();

    match output {
        Ok(_) => Ok(()),
        Err(_) => Ok(()),
    }
}
