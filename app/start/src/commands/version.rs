use anyhow::Result;

use crate::ui::format;

pub async fn run() -> Result<()> {
    format::header("Job Search Developer CLI");
    println!("  Version: {}", env!("CARGO_PKG_VERSION"));
    println!("  Binary:  start");
    println!();
    Ok(())
}
