pub mod format;

use tracing_subscriber::{fmt, EnvFilter};

pub fn init_logging() {
    let _ = fmt()
        .with_env_filter(
            EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info")),
        )
        .with_target(false)
        .with_file(false)
        .with_line_number(false)
        .try_init();
}
