use anyhow::Result;

use crate::config::Config;
use crate::ui::format;

pub async fn run() -> Result<()> {
    let config = Config::load()?;
    format::log("Running tests...");

    let python = config.python()?;
    let output = std::process::Command::new(&python)
        .args(["-m", "pytest", "app/server/tests", "-v", "--tb=short"])
        .current_dir(&config.repo_root)
        .status()?;

    if output.success() {
        format::ok("All tests passed.");
    } else {
        anyhow::bail!("Tests failed");
    }

    Ok(())
}
