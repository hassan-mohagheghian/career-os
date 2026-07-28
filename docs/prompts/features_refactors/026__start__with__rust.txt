# Sprint 05 — Replace start.sh with a Rust Developer CLI

## ROLE

You are a Principal Rust Engineer, Software Architect, DevOps Engineer, and Monorepo Architect.

Your task is to replace the current `start.sh` script with a production-quality Rust CLI application.

This CLI will become the single developer entry point for the entire project.

The existing shell script is only the starting point.

The new CLI must be extensible and become the foundation for future developer tooling.

--------------------------------------------------
PROJECT CONTEXT
--------------------------------------------------

[PASTE CURRENT PROJECT CONTEXT HERE]

--------------------------------------------------
CURRENT PROJECT STRUCTURE
--------------------------------------------------

The repository is organized as a monorepo.

Example:

apps/

    frontend/

    backend/

The backend is already organized using:

- DDD
- Hexagonal Architecture
- Bounded Contexts

There is currently a shell script located at:

start.sh

This script is responsible for various development tasks.

It must be completely replaced.

--------------------------------------------------
OBJECTIVE
--------------------------------------------------

Create a brand-new Rust application named:

apps/start/

This project becomes the developer CLI for the entire repository.

After compilation, the generated executable must be copied automatically to:

/start

at the repository root.

This executable replaces start.sh forever.

No shell script should remain responsible for developer workflows.

--------------------------------------------------
TECH STACK
--------------------------------------------------

Use modern Rust.

Recommended crates:

- clap
- tokio
- anyhow
- tracing
- tracing-subscriber
- indicatif
- dialoguer (optional)
- serde
- serde_json

Use only stable Rust.

--------------------------------------------------
CLI DESIGN
--------------------------------------------------

Design the CLI to be extensible.

Example:

start

    dev

    backend

    frontend

    test

    lint

    format

    migrate

    db

    docker

    clean

    doctor

    logs

    version

Future commands should be easy to add.

Every command should live in its own module.

--------------------------------------------------
FIRST GOAL
--------------------------------------------------

Analyze the existing start.sh.

Reimplement every feature.

Behavior must remain compatible.

Nothing should be lost.

--------------------------------------------------
COMMANDS
--------------------------------------------------

Implement commands equivalent to everything currently supported by start.sh.

Examples:

start dev

Starts frontend

Starts backend

Opens browser (if current script does)

Streams logs

Supports Ctrl+C shutdown

--------------------------------

start backend

Only backend

--------------------------------

start frontend

Only frontend

--------------------------------

start test

Run every project test

Backend

Frontend

Future Rust tests

--------------------------------

start lint

Run every linter

--------------------------------

start format

Run every formatter

--------------------------------

start doctor

Validate environment

Rust

Python

Node

pnpm

uv

Docker

PostgreSQL

Everything required for development.

--------------------------------------------------
PROCESS MANAGEMENT
--------------------------------------------------

The CLI should properly manage child processes.

Support:

Ctrl+C

Graceful shutdown

Parallel execution

Exit code propagation

Colored output

Streaming logs

--------------------------------------------------
CONFIGURATION
--------------------------------------------------

Avoid hardcoded paths.

Use configuration where appropriate.

--------------------------------------------------
OUTPUT
--------------------------------------------------

Provide beautiful terminal output.

Use:

Progress bars

Spinners

Colors

Clear status messages

Readable errors

--------------------------------------------------
ERROR HANDLING
--------------------------------------------------

Use proper Rust error handling.

Never panic for expected errors.

Return meaningful exit codes.

--------------------------------------------------
PROJECT STRUCTURE
--------------------------------------------------

Design a clean Rust project.

Example:

apps/

    start/

        src/

            commands/

            process/

            config/

            ui/

            utils/

            main.rs

The architecture should remain maintainable.

--------------------------------------------------
BUILD
--------------------------------------------------

Configure Cargo so that:

cargo build --release

produces

target/release/start

and automatically copies it to

/start

at the repository root.

The repository should always contain the latest executable after release builds.

--------------------------------------------------
QUALITY
--------------------------------------------------

The code should follow:

Rust best practices

SOLID

Clean Code

Modular architecture

Extensibility

Maintainability

--------------------------------------------------
DOCUMENTATION
--------------------------------------------------

Create or update:

docs/development/rust-cli.md

docs/development/developer-workflow.md

docs/architecture/developer-cli.md

docs/adr/006-rust-developer-cli.md

Include:

Architecture

Commands

Extending the CLI

Build process

Developer guide

--------------------------------------------------
IMPLEMENTATION PLAN
--------------------------------------------------

Before writing code:

1. Analyze the current start.sh completely.
2. Produce a feature parity checklist.
3. Design the Rust CLI architecture.
4. Implement incrementally.
5. Verify every existing feature still works.
6. Remove dependency on start.sh.

--------------------------------------------------
ACCEPTANCE CRITERIA
--------------------------------------------------

The project must:

✔ Replace start.sh completely.

✔ Preserve all existing functionality.

✔ Be modular.

✔ Be extensible.

✔ Follow Rust best practices.

✔ Produce a single executable named "start".

✔ Place the executable in the repository root after release builds.

✔ Serve as the permanent developer entry point for the project.
