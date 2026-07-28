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

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;

    #[test]
    fn test_managed_process_new() {
        let pid_file = std::env::temp_dir().join("test_new.pid");
        let mp = ManagedProcess::new("test-proc", pid_file.clone());
        assert_eq!(mp.name, "test-proc");
        assert_eq!(mp.pid_file, pid_file);
    }

    #[test]
    fn test_save_and_read_pid() {
        let dir = std::env::temp_dir().join("process_test_save_read");
        std::fs::create_dir_all(&dir).unwrap();
        let pid_file = dir.join("test.pid");

        let mp = ManagedProcess::new("test-proc", pid_file.clone());
        mp.save_pid(12345).unwrap();

        assert!(pid_file.exists());
        let content = std::fs::read_to_string(&pid_file).unwrap();
        assert_eq!(content.trim(), "12345");

        let pid = mp.read_pid();
        assert_eq!(pid, Some(12345));

        std::fs::remove_dir_all(&dir).unwrap();
    }

    #[test]
    fn test_read_pid_nonexistent_file() {
        let pid_file = std::env::temp_dir().join("nonexistent_file_xyz.pid");
        let mp = ManagedProcess::new("test", pid_file);
        assert!(mp.read_pid().is_none());
    }

    #[test]
    fn test_read_pid_invalid_content() {
        let dir = std::env::temp_dir().join("process_test_invalid_pid");
        std::fs::create_dir_all(&dir).unwrap();
        let pid_file = dir.join("invalid.pid");
        let mut f = std::fs::File::create(&pid_file).unwrap();
        writeln!(f, "not_a_number").unwrap();

        let mp = ManagedProcess::new("test", pid_file.clone());
        assert!(mp.read_pid().is_none());

        std::fs::remove_dir_all(&dir).unwrap();
    }

    #[test]
    fn test_save_pid_overwrites() {
        let dir = std::env::temp_dir().join("process_test_overwrite");
        std::fs::create_dir_all(&dir).unwrap();
        let pid_file = dir.join("overwrite.pid");

        let mp = ManagedProcess::new("test", pid_file.clone());
        mp.save_pid(111).unwrap();
        mp.save_pid(222).unwrap();

        let pid = mp.read_pid();
        assert_eq!(pid, Some(222));

        std::fs::remove_dir_all(&dir).unwrap();
    }

    #[test]
    fn test_is_running_no_pid_file() {
        let pid_file = std::env::temp_dir().join("no_pid.pid");
        let mp = ManagedProcess::new("test", pid_file);
        assert!(!mp.is_running());
    }

    #[test]
    fn test_kill_by_pattern_silent_on_missing_pkill() {
        let result = kill_by_pattern("nonexistent_pattern_xyz_abc");
        assert!(result.is_ok());
    }

    #[test]
    fn test_stop_removes_pid_file() {
        let dir = std::env::temp_dir().join("process_test_stop_remove");
        std::fs::create_dir_all(&dir).unwrap();
        let pid_file = dir.join("stop_remove.pid");

        let mp = ManagedProcess::new("test", pid_file.clone());
        mp.save_pid(99999).unwrap();
        assert!(pid_file.exists());

        mp.stop().unwrap();
        assert!(!pid_file.exists());

        std::fs::remove_dir_all(&dir).unwrap();
    }

    #[test]
    fn test_stop_no_pid_file_does_not_error() {
        let pid_file = std::env::temp_dir().join("stop_nonexistent.pid");
        let mp = ManagedProcess::new("test", pid_file);
        let result = mp.stop();
        assert!(result.is_ok());
    }
}
