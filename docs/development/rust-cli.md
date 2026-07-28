# Rust Developer CLI

## Overview

The `start` binary is a Rust CLI application that replaces the former `start.sh` shell script. It serves as the single developer entry point for the entire Job Search monorepo.

## Installation

```bash
cargo build --release --manifest-path app/start/Cargo.toml
cp app/start/target/release/start ./start
```

## Usage

```bash
./start              # Start backend + frontend (default: dev command)
./start dev          # Start backend + frontend
./start backend      # Start only backend
./start frontend     # Start only frontend
./start test         # Run all tests
./start lint         # Run all linters
./start format       # Run all formatters
./start stop         # Stop all running processes
./start status       # Show status of running processes
./start doctor       # Validate development environment
./start migrate      # Run database migrations
./start db up        # Run migrations up
./start db down      # Rollback last migration
./start db new NAME  # Create new migration
./start docker up    # Start docker containers
./start docker down  # Stop docker containers
./start clean        # Remove build artifacts
./start logs         # Stream logs
./start version      # Show version
```

## Architecture

```
app/start/
  src/
    main.rs           # CLI entry point with clap parsing
    commands/         # Command implementations (one module per command)
      mod.rs          # Module declarations
      dev.rs          # Start all services
      backend.rs      # Backend only
      frontend.rs     # Frontend only
      test.rs         # Run tests
      lint.rs         # Run linters
      format_cmd.rs   # Run formatters
      migrate.rs      # Database migrations
      db.rs           # Database operations
      docker.rs       # Docker operations
      clean.rs        # Clean artifacts
      doctor.rs       # Environment validation
      logs.rs         # Log streaming
      version.rs      # Version info
      stop.rs         # Stop processes
      status.rs       # Process status
    config/           # Configuration and path resolution
    process/          # Process management (PID files, signals, cleanup)
    ui/               # Terminal output formatting
    utils/            # Shared utilities
```

## Adding a New Command

1. Create a new file in `src/commands/your_command.rs`
2. Add a variant to the `Commands` enum in `main.rs`
3. Add a module declaration in `src/commands/mod.rs`
4. Implement the command in the new module

## Build

```bash
cargo build --release --manifest-path app/start/Cargo.toml
```

The build script copies the binary to the repository root automatically.
