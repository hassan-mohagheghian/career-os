# Architecture Sessions Index

This folder contains session-by-session architecture investigation notes.
Each session file documents: goals, findings, changes made, bugs fixed, and pending work.

## Sessions

| # | Date | Focus | File |
|---|---|---|---|
| 001 | — | AI provider registration (opencode) | *(pre-dates this practice)* |
| 002 | — | Skill roadmap generation + WebSocket progress | *(pre-dates this practice)* |
| 003 | 2026-07-27 | Generation history, persistence, duplicate fix, session ID, roadmap actions in drawer | [003-generation-history-persistence.md](003-generation-history-persistence.md) |
| 004 | 2026-07-27 | Generation system unification — OOP/SOLID/TDD for all generation types | [2026-07-27_generation-unification.md](2026-07-27_generation-unification.md) |
| 005 | 2026-07-28 | Documentation cleanup (v1 removal), GenerationHistoryDrawer auto-refresh, pending_generations history fix | [005-docs-cleanup-history-fixes.md](005-docs-cleanup-history-fixes.md) |

## How to Use

1. **At session start**: Read the latest session file for context
2. **During session**: Note findings, changes, and decisions
3. **At session end**: Write a new session file with full details
4. **Update this index**: Add the new session row

## Conventions

- Session files are named `NNN-topic-slug.md`
- Each file has sections: Goals, Findings, Changes, Bugs, Pending, File Reference
- Findings include DB schemas, API contracts, and data flow diagrams
- Changes include before/after comparisons with reasoning
