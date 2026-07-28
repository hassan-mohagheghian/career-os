# LangGraph Integration

## Overview

This project uses LangGraph as the primary workflow orchestration engine. LangGraph provides state machine semantics, checkpointing, and streaming for AI workflows.

## Key Concepts

### StateGraph

LangGraph's `StateGraph` is the core abstraction. Each graph is a directed acyclic graph (DAG) of nodes connected by edges.

```python
from langgraph.graph import StateGraph, END

graph = StateGraph(BaseState)
graph.add_node("step1", step1_fn)
graph.add_node("step2", step2_fn)
graph.add_edge("step1", "step2")
graph.add_edge("step2", END)
graph.set_entry_point("step1")
compiled = graph.compile()
```

### State

State is a TypedDict that flows through all nodes. Each node reads from state and returns updated state.

```python
from typing import TypedDict

class BaseState(TypedDict, total=False):
    input: str
    output: str
    context: dict
    errors: list[str]
    metadata: dict
    node_history: list[str]
```

### Conditional Edges

Graphs can branch based on state:

```python
def route(state):
    if state["metadata"]["has_data"]:
        return "process"
    return "skip"

graph.add_conditional_edges("fetch", route, {
    "process": "process_node",
    "skip": "skip_node",
})
```

### Checkpointing

Enable checkpointing for state persistence:

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
compiled = graph.compile(checkpointer=checkpointer)

# Invoke with config for checkpointing
config = {"configurable": {"thread_id": "session-123"}}
result = compiled.invoke(state, config=config)
```

### Streaming

Stream execution step by step:

```python
for event in compiled.stream(state):
    print(event)  # {"node_name": updated_state}
```

## GraphBuilder Wrapper

Our `GraphBuilder` wraps LangGraph with additional features:

```python
from ai.infrastructure.graphs.runtime.graph import GraphBuilder

builder = GraphBuilder("my_workflow")
builder.add_node("step1", step1_fn)
builder.add_node("step2", step2_fn)
builder.add_edge("step1", "step2")
builder.set_entry("step1")
builder.set_finish("step2")
builder.set_retry("step2", max_retries=3, delay=1.0)

compiled = builder.compile()
result = compiled.invoke(state)
```

## Retry Configuration

Per-node retry with exponential backoff:

```python
builder.set_retry("flaky_node", max_retries=3, delay=1.0)
```

## Error Handling

- Nodes that fail are marked as `"{name}:FAILED"` in `node_history`
- Errors are appended to `state["errors"]`
- Retry logic handles transient failures
- Insights graph supports partial failure (one section failing doesn't stop others)

## Provider Integration

All LLM calls go through the `LLMProvider` abstraction:

```python
provider = get_provider()  # From env AI_PROVIDER
llm = provider.as_langchain_llm()  # LangChain-compatible
```

This ensures provider-agnostic code that works with Mimo, OpenAI, Anthropic, etc.
