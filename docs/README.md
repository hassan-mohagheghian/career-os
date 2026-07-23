# Documentation

## Structure

```
docs/
├── README.md                    — This file
├── PROJECT_CONTEXT.md           — Architecture overview, modules, design decisions
├── ROADMAP.md                   — Completed features and future plans
├── CHANGELOG.md                 — Version history
├── architecture/
│   └── ARCHITECTURE.md          — System design, entities, data flows, modules
├── features/
│   └── career_intelligence.md   — Career Intelligence feature spec
└── agent/
    ├── CURRENT_STATE.md         — Environment, privacy rules, constraints
    ├── ACTIVE_TASKS.md          — Current session work
    ├── KNOWN_ISSUES.md          — Known limitations
    └── NEXT_STEPS.md            — Future work
```

## Quick Start

```bash
./app/start.sh  # Starts Flask + WebSocket + React dev server
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python Flask, SQLite (raw SQL), Typer CLI |
| Frontend | React 18 (JSX), Vite, shadcn/ui, Tailwind CSS |
| AI | Mimo CLI subprocess |
| Realtime | WebSocket (8765) + SSE |
