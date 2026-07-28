# ADR 006: Rust Developer CLI

## Status

Accepted

## Context

The project used a shell script (`start.sh`) as the developer entry point. This script was functional but lacked:
- Type safety
- Proper error handling
- Extensibility
- Cross-platform support
- Rich terminal output

## Decision

Replace `start.sh` with a Rust CLI application named `start` built with:
- **clap**: Argument parsing with derive macros
- **tokio**: Async runtime for signal handling
- **anyhow**: Error handling
- **tracing**: Structured logging

## Consequences

### Positive
- Type-safe command definitions
- Proper error handling and exit codes
- Easy to extend with new commands
- Beautiful terminal output
- Single binary distribution
- Native async signal handling (Ctrl+C)

### Negative
- Build requires Rust toolchain
- Slightly longer initial build time
- Binary size (~3MB vs ~5KB script)

### Mitigations
- Build script auto-copies binary to repo root
- Release builds are cached
- Binary is small enough to commit

## Alternatives Considered

1. **Python CLI (click/typer)**: Would require Python runtime, slower startup.
2. **Go CLI**: Good option but Rust chosen for consistency with future tooling goals.
3. **Enhanced bash**: Would not solve extensibility or type safety issues.
