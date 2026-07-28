use anyhow::Result;

use crate::config::Config;
use crate::ui::format;

pub async fn run() -> Result<()> {
    let config = Config::load()?;
    format::log("Running database migrations...");

    let alembic = config.alembic()?;
    let output = std::process::Command::new(&alembic)
        .args(["upgrade", "head"])
        .current_dir(&config.repo_root)
        .status()?;

    if output.success() {
        format::ok("Migrations applied successfully.");
    } else {
        anyhow::bail!("Migrations failed");
    }

    Ok(())
}
