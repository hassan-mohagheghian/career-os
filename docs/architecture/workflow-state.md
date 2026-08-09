# Workflow State Architecture

## Overview

All AI workflows follow the same pattern:

1. **Input** is loaded into LangGraph State
2. **Nodes** read from State, process, write back to State
3. **Checkpointing** captures state after each node
4. **Output** is read from final State

## State Flow

```
┌─────────────┐
│   Input     │
└──────┬──────┘
       ↓
┌─────────────┐
│  State      │  ← TypedDict with workflow-specific fields
└──────┬──────┘
       ↓
┌─────────────┐     ┌──────────────┐
│  Node A     │────→│  Updated     │
│  (process)  │     │  State       │
└─────────────┘     └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │  Node B      │
                    │  (process)   │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │  Final       │
                    │  Output      │
                    └──────────────┘
```

## Checkpoint Architecture

```
┌─────────────┐    Optional    ┌──────────────┐
│  Graph      │───────────────→│  Checkpointer │
│  Execution  │                │  (Memory/DB)  │
└─────────────┘                └──────────────┘
```

## File I/O Elimination

- Worker code no longer writes to or reads from temp files
- LLM provider may still use temporary files internally (transparent)
- `TempFileManager` is deprecated
- Only final business artifacts (job analysis, company intelligence, skills, insights) are persisted
