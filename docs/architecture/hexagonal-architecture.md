# Hexagonal Architecture

## Ports and Adapters

The backend follows hexagonal (ports and adapters) architecture:

```
                    ┌─────────────────────────┐
                    │     Domain Layer        │
                    │  (Entities, Value Obj,  │
                    │   Repository Interfaces)│
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │   Application Layer     │
                    │  (Use Cases, DTOs)      │
                    └───────────┬─────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
    ┌───────▼──────┐   ┌───────▼──────┐   ┌───────▼──────┐
    │  API (In)    │   │  DB (Out)    │   │  Worker (Out)│
    │  FastAPI     │   │  SQLAlchemy  │   │  Background  │
    │  Routers     │   │  Repos       │   │  Threads     │
    └──────────────┘   └──────────────┘   └──────────────┘
```

## Ports

### Inbound (Driving) Ports
- **API Port**: FastAPI routers accept HTTP requests
- **CLI Port**: Typer commands accept terminal input

### Outbound (Driven) Ports
- **Repository Port**: `IJobRepository`, `ICompanyRepository`, etc.
- **LLM Port**: `LLMProvider` ABC
- **Broadcaster Port**: WebSocket broadcaster interface

## Adapters

### Inbound Adapters
- `presentation/api/*.py` — FastAPI routers
- `cli.py` — Typer CLI

### Outbound Adapters
- `infrastructure/repositories/*.py` — SQLAlchemy implementations
- `ai/providers/*.py` — LLM provider implementations
- `infrastructure/websocket/*.py` — SocketIO broadcaster

## Dependency Rule

Dependencies point inward: Presentation → Application → Domain.
The domain layer has zero outward dependencies.
