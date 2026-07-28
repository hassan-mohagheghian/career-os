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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_command_exists_known() {
        assert!(command_exists("sh"));
        assert!(command_exists("echo"));
    }

    #[test]
    fn test_command_exists_unknown() {
        assert!(!command_exists("this_command_should_not_exist_xyz123"));
    }

    #[test]
    fn test_get_command_version() {
        let version = get_command_version("echo", &["hello"]);
        assert!(version.is_ok());
        assert_eq!(version.unwrap(), "hello");
    }

    #[test]
    fn test_get_command_version_nonexistent() {
        let version = get_command_version("nonexistent_cmd_xyz", &["--version"]);
        assert!(version.is_err());
    }

    #[test]
    fn test_check_tool_found() {
        let (ok, msg) = check_tool("echo", &["hello"]);
        assert!(ok);
        assert!(msg.contains("echo"));
    }

    #[test]
    fn test_check_tool_not_found() {
        let (ok, msg) = check_tool("nonexistent_tool_abc", &["--version"]);
        assert!(!ok);
        assert!(msg.contains("not found"));
    }

    #[test]
    fn test_path_exists_true() {
        let dir = std::env::temp_dir().join("utils_test_exists");
        std::fs::create_dir_all(&dir).unwrap();
        assert!(path_exists(&dir));
        std::fs::remove_dir_all(&dir).unwrap();
    }

    #[test]
    fn test_path_exists_false() {
        let p = Path::new("/tmp/should_not_exist_xyz_12345");
        assert!(!path_exists(p));
    }
}
