# ADR-011: LangGraph Native State Management

## Status

Accepted

## Context

AI workflows used temporary files (JSON, TXT, MD) for inter-node communication. This caused:
- Unnecessary I/O overhead
- Synchronization issues
- Cleanup problems
- Race conditions
- Reduced performance

## Decision

Migrate all AI workflows to LangGraph's native state management:

1. **Strongly Typed State Models**: Each workflow uses a TypedDict extending `BaseState`
2. **In-Memory Data Flow**: Nodes communicate exclusively through LangGraph State
3. **Built-in Checkpointing**: Use LangGraph's native checkpointer (`MemorySaver`, `SqliteSaver`, `PostgresSaver`)
4. **No Temporary Files**: All intermediate data stays in State; only final business artifacts are persisted

## Consequences

### Positive
- Eliminates file I/O between nodes
- Built-in retry and recovery via checkpointing
- Strong typing prevents data inconsistencies
- Future migration to PostgreSQL requires no architecture changes

### Negative
- Prompts still reference file paths (backward compatibility with LLM providers)
- Some file I/O remains at the LLM provider level (transparent to workflows)

## Compliance

- Every workflow uses LangGraph State
- Temporary files eliminated from workflow code
- Nodes communicate only through State
- Checkpointing uses native LangGraph mechanisms
- State models are strongly typed
