mod commands;
mod config;
mod process;
mod ui;
mod utils;

use anyhow::Result;
use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(
    name = "start",
    about = "Job Search Application — Developer CLI",
    version,
    propagate_version = true
)]
struct Cli {
    #[command(subcommand)]
    command: Option<Commands>,
}

#[derive(Subcommand)]
enum Commands {
    /// Start backend + frontend (default)
    Dev {
        /// Backend port (default: 5000 or BACKEND_PORT from .env)
        #[arg(long)]
        backend_port: Option<u16>,
        /// Frontend port (default: 5173 or FRONTEND_PORT from .env)
        #[arg(long)]
        frontend_port: Option<u16>,
    },
    /// Start only the FastAPI backend
    Backend {
        /// Backend port (default: 5000 or BACKEND_PORT from .env)
        #[arg(long)]
        port: Option<u16>,
    },
    /// Start only the frontend dev server
    Frontend {
        /// Frontend port (default: 5173 or FRONTEND_PORT from .env)
        #[arg(long)]
        port: Option<u16>,
    },
    /// Run all project tests
    Test,
    /// Run all linters
    Lint,
    /// Run all formatters
    Format,
    /// Run database migrations
    Migrate,
    /// Database operations
    Db {
        #[command(subcommand)]
        action: Option<DbCommands>,
    },
    /// Docker operations
    Docker {
        #[command(subcommand)]
        action: Option<DockerCommands>,
    },
    /// Remove build artifacts and caches
    Clean,
    /// Validate development environment
    Doctor,
    /// Stream logs from running services
    Logs,
    /// Show version information
    Version,
    /// Stop all running processes
    Stop,
    /// Show status of running processes
    Status,
}

#[derive(Subcommand)]
enum DbCommands {
    /// Run pending migrations up
    Up,
    /// Rollback last migration
    Down,
    /// Create a new migration
    New {
        /// Migration name
        name: String,
    },
}

#[derive(Subcommand)]
enum DockerCommands {
    /// Start docker containers
    Up,
    /// Stop docker containers
    Down,
    /// Show docker container status
    Status,
}

#[tokio::main]
async fn main() -> Result<()> {
    ui::init_logging();

    let cli = Cli::parse();

    match cli.command {
        Some(Commands::Dev {
            backend_port,
            frontend_port,
        }) => {
            let mut config = config::Config::load()?;
            if let Some(p) = backend_port {
                config = config.with_backend_port(p);
            }
            if let Some(p) = frontend_port {
                config = config.with_frontend_port(p);
            }
            commands::dev::run(config).await
        }
        Some(Commands::Backend { port }) => {
            let mut config = config::Config::load()?;
            if let Some(p) = port {
                config = config.with_backend_port(p);
            }
            commands::backend::run(config).await
        }
        Some(Commands::Frontend { port }) => {
            let mut config = config::Config::load()?;
            if let Some(p) = port {
                config = config.with_frontend_port(p);
            }
            commands::frontend::run(config).await
        }
        Some(Commands::Test) => commands::test::run().await,
        Some(Commands::Lint) => commands::lint::run().await,
        Some(Commands::Format) => commands::format_cmd::run().await,
        Some(Commands::Migrate) => commands::migrate::run().await,
        Some(Commands::Db { action }) => commands::db::run(action).await,
        Some(Commands::Docker { action }) => commands::docker::run(action).await,
        Some(Commands::Clean) => commands::clean::run().await,
        Some(Commands::Doctor) => commands::doctor::run().await,
        Some(Commands::Logs) => commands::logs::run().await,
        Some(Commands::Version) => commands::version::run().await,
        Some(Commands::Stop) => commands::stop::run().await,
        Some(Commands::Status) => commands::status::run().await,
        None => {
            let config = config::Config::load()?;
            commands::dev::run(config).await
        }
    }
}
