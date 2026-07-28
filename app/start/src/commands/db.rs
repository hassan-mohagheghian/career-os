use anyhow::Result;

use crate::config::Config;
use crate::DbCommands;
use crate::ui::format;

pub async fn run(action: Option<DbCommands>) -> Result<()> {
    let config = Config::load()?;
    let alembic = config.alembic()?;

    match action {
        Some(DbCommands::Up) => {
            format::log("Running migrations up...");
            let status = std::process::Command::new(&alembic)
                .args(["upgrade", "head"])
                .current_dir(&config.repo_root)
                .status()?;
            if status.success() {
                format::ok("Migrations applied.");
            } else {
                anyhow::bail!("Migrations failed");
            }
        }
        Some(DbCommands::Down) => {
            format::log("Rolling back last migration...");
            let status = std::process::Command::new(&alembic)
                .args(["downgrade", "-1"])
                .current_dir(&config.repo_root)
                .status()?;
            if status.success() {
                format::ok("Migration rolled back.");
            } else {
                anyhow::bail!("Rollback failed");
            }
        }
        Some(DbCommands::New { name }) => {
            format::log(&format!("Creating migration: {}", name));
            let status = std::process::Command::new(&alembic)
                .args(["revision", "--autogenerate", "-m", &name])
                .current_dir(&config.repo_root)
                .status()?;
            if status.success() {
                format::ok(&format!("Migration '{}' created.", name));
            } else {
                anyhow::bail!("Migration creation failed");
            }
        }
        None => {
            format::log("Usage: start db <up|down|new <name>>");
        }
    }

    Ok(())
}
