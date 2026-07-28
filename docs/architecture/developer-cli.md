# Developer CLI Architecture

## Overview

The developer CLI (`start`) is a Rust binary that provides a unified interface for all development tasks in the Job Search monorepo.

## Design Principles

1. **Extensibility**: New commands are added by creating a module and registering it in the CLI enum.
2. **Modularity**: Each command lives in its own module under `src/commands/`.
3. **Process Management**: Proper PID tracking, signal handling, and graceful shutdown.
4. **Cross-platform**: Uses `libc` for Unix signal handling.

## Modules

- **config**: Resolves paths (repo root, server dir, client dir, venv, PID files).
- **process**: Manages child processes (spawn, PID tracking, kill, cleanup).
- **ui/format**: Colored terminal output with consistent branding.
- **utils**: Shared helpers (command existence checks, version detection).

## Process Lifecycle

1. Commands spawn child processes.
2. PIDs are written to `.server.pid` / `.client.pid`.
3. On Ctrl+C or `stop`, processes receive SIGTERM then SIGKILL.
4. PID files are cleaned up on exit.

## Adding Commands

```rust
// 1. Add variant to Commands enum in main.rs
#[derive(Subcommand)]
enum Commands {
    // ...existing commands...
    MyNewCommand,
}

// 2. Create src/commands/my_new_command.rs
pub async fn run() -> Result<()> {
    // implementation
    Ok(())
}

// 3. Add module declaration in src/commands/mod.rs
pub mod my_new_command;

// 4. Handle in main.rs match
Some(Commands::MyNewCommand) => commands::my_new_command::run().await,
```
