# Checkpointing

Uses LangGraph's native checkpointing mechanism.

## Default Checkpointer

All graphs use `MemorySaver` by default:

```python
from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)
```

## When to Persist

Persist state only when necessary:

- Long-running workflows
- Human-in-the-loop
- Workflow resume after failure
- Retry after crash
- Workflow history

Short-lived workflows remain entirely in memory.

## Configuration

```python
config = {
    "configurable": {
        "thread_id": "workflow_123",
        "checkpoint_id": "ckpt_456",
    }
}
state = graph.invoke(my_state, config=config)
```

## Resume After Failure

```python
saved_state = graph.get_state(config)
if saved_state:
    graph.update_state(config, {"retry": True})
    result = graph.invoke(None, config=config)
```

## Database-Backed Checkpointing

For PostgreSQL:

```python
from langgraph.checkpoint.postgres import PostgresSaver
checkpointer = PostgresSaver.from_conn_string(DB_URL)
```

For SQLite:

```python
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
conn = sqlite3.connect("checkpoints.db")
checkpointer = SqliteSaver(conn)
```
