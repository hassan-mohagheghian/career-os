# Workflow Progress Tracking

## LangGraph Node Execution

The job processing pipeline is implemented as a LangGraph with 13 nodes:

```
load_context
    ↓
validate_input
    ↓
fetch_url
    ↓
fallback_to_notes
    ↓
extract_raw_content
    ↓
clean_content
    ↓
extract_structured_data
    ↓
analyze_job
    ↓
extract_skills
    ↓
score_job
    ↓
generate_summary
    ↓
persist_results
    ↓
completion_event
```

## Progress State

Each node execution updates the `progress` dict in the LangGraph state:

```python
state["progress"] = {
    "current_node": "fetch_url",           # Currently executing node
    "progress_pct": 28.6,                  # Percentage complete (0-100)
    "message": "Fetching URL content...",   # Human-readable status
    "started_at": "2026-07-29T10:30:00",   # ISO timestamp of start
    "completed_nodes": [                    # Nodes that finished
        "load_context",
        "validate_input",
    ],
    "node_timings": {                       # Per-node duration in ms
        "load_context": 234.5,
        "validate_input": 12.3,
    },
}
```

## Per-Node Status Mapping

| LangGraph Node       | JobStatus    | WorkflowStep |
|----------------------|-------------|--------------|
| load_context         | starting    | validate     |
| validate_input       | starting    | validate     |
| fetch_url            | fetching    | fetch        |
| fallback_to_notes    | fetching    | fetch        |
| extract_raw_content  | analyzing   | extract      |
| clean_content        | analyzing   | extract      |
| extract_structured   | analyzing   | extract      |
| analyze_job          | analyzing   | analyze      |
| extract_skills       | analyzing   | analyze      |
| score_job            | generating  | score        |
| generate_summary     | generating  | summarize    |
| persist_results      | finalizing  | persist      |
| completion_event     | finalizing  | complete     |

## Retry Logic

Certain nodes have retry configured:
- `extract_raw_content`: max 2 retries, 1s delay
- `score_job`: max 2 retries, 1s delay

Each retry attempt increments `retry_count` in the pending_jobs record.

## WebSocket Progress Events

During execution, the worker emits `pending:progress` events with:
- Current node name
- Progress percentage
- Completion message with timing
- List of completed nodes with their durations

## Frontend Display

The frontend `ProcessingItem` component shows:
- Current status label (from `pending:update` status field)
- Progress bar (from progress_pct)
- Current step description (from message)
- Workflow log entries (from `pending:log` events)
