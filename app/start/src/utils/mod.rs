use anyhow::Result;
use std::path::Path;
use std::process::Command;

pub fn command_exists(name: &str) -> bool {
    Command::new("which")
        .arg(name)
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false)
}

pub fn get_command_version(cmd: &str, args: &[&str]) -> Result<String> {
    let output = Command::new(cmd).args(args).output()?;
    Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
}

pub fn check_tool(name: &str, version_args: &[&str]) -> (bool, String) {
    if !command_exists(name) {
        return (false, format!("{} not found", name));
    }
    match get_command_version(name, version_args) {
        Ok(v) => (true, format!("{} {}", name, v)),
        Err(_) => (true, format!("{} (version unknown)", name)),
    }
}

pub fn path_exists(path: &Path) -> bool {
    path.exists()
}
