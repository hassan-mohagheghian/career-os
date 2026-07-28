use anyhow::Result;

use crate::ui::format;

pub async fn run() -> Result<()> {
    format::header("Job Search Developer CLI");
    println!("  Version: {}", env!("CARGO_PKG_VERSION"));
    println!("  Binary:  start");
    println!();
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_version_run_does_not_panic() {
        let result = run().await;
        assert!(result.is_ok());
    }

    #[test]
    fn test_cargo_pkg_version_compiles() {
        let _ = env!("CARGO_PKG_VERSION");
    }
}
