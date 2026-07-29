# Developer CLI

## Overview

The `start.py` script is the single developer entry point for the entire Job Search monorepo. It replaces the former Rust CLI (`app/start/`).

## Usage

```bash
python start.py              # Start backend + frontend (default: dev command)
python start.py dev          # Start backend + frontend
python start.py backend      # Start only backend
python start.py frontend     # Start only frontend
python start.py test         # Run all tests
python start.py lint         # Run all linters
python start.py format       # Run all formatters
python start.py stop         # Stop all running processes
python start.py status       # Show status of running processes
python start.py doctor       # Validate development environment
python start.py migrate      # Run database migrations
python start.py db up        # Run migrations up
python start.py db down      # Rollback last migration
python start.py db new NAME  # Create new migration
python start.py docker up    # Start docker containers
python start.py docker down  # Stop docker containers
python start.py clean        # Remove build artifacts
python start.py logs         # Stream logs
python start.py version      # Show version
```

## Architecture

The CLI is implemented in `start.py` using `typer`. It provides all commands natively without needing a compiled binary.
