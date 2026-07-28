# Developer Workflow

## Quick Start

```bash
# Validate environment
./start doctor

# Start development (backend + frontend)
./start

# Run tests
./start test

# Run linters
./start lint

# Stop everything
./start stop
```

## Commands

| Command | Description |
|---------|-------------|
| `./start` | Start all services (default) |
| `./start dev` | Start backend + frontend |
| `./start backend` | Start backend only |
| `./start frontend` | Start frontend only |
| `./start test` | Run all tests |
| `./start lint` | Run all linters |
| `./start format` | Run all formatters |
| `./start stop` | Stop all processes |
| `./start status` | Show process status |
| `./start doctor` | Validate environment |
| `./start migrate` | Run database migrations |
| `./start db up` | Migrate up |
| `./start db down` | Migrate down |
| `./start db new NAME` | Create migration |
| `./start docker up` | Start Docker containers |
| `./start docker down` | Stop Docker containers |
| `./start clean` | Remove build artifacts |
| `./start logs` | Stream logs |
| `./start version` | Show version |

## Services

- **Backend**: FastAPI on http://localhost:5000
- **Frontend**: Vite on http://localhost:5173

## Database

```bash
./start db up          # Run pending migrations
./start db down        # Rollback last migration
./start db new add_users  # Create new migration
```
