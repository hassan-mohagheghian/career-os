# Sprint 11 — Migrate All AI Workflows to Native LangGraph State Management

## ROLE

You are a Principal AI Architect, LangGraph Expert, LangChain Expert, and Distributed Systems Engineer.

Your task is to redesign the state management of every AI workflow.

The project already uses:

- FastAPI
- LangChain
- LangGraph
- PostgreSQL / SQLite (current database)
- SQLAlchemy
- Redis
- ARQ
- DDD
- Hexagonal Architecture

Business behavior must remain unchanged.

Do NOT redesign prompts.

Do NOT redesign workflows.

Do NOT redesign business logic.

This sprint is ONLY about state management.

--------------------------------------------------
OBJECTIVE
--------------------------------------------------

Every workflow must use LangGraph's native state management.

Eliminate manual state persistence through files.

The graph itself should own the execution state.

--------------------------------------------------
CURRENT PROBLEM
--------------------------------------------------

Some workflows currently:

- write intermediate JSON files
- save temporary text files
- persist temporary markdown
- create intermediate artifacts only to be consumed by the next step

This introduces:

- unnecessary I/O
- synchronization issues
- cleanup problems
- race conditions
- reduced performance

These temporary artifacts should disappear.

--------------------------------------------------
TARGET ARCHITECTURE
--------------------------------------------------

Every workflow should follow:

Input

↓

LangGraph State

↓

Node A

↓

Updated State

↓

Node B

↓

Updated State

↓

Node C

↓

Final Output

Nodes communicate ONLY through LangGraph State.

Never through temporary files.

--------------------------------------------------
STATE DESIGN
--------------------------------------------------

Review every workflow.

Design strongly typed State models.

Use TypedDict or Pydantic models where appropriate.

Avoid dictionaries with arbitrary keys.

State should contain only information required by downstream nodes.

--------------------------------------------------
CHECKPOINTING
--------------------------------------------------

Use LangGraph checkpointing when persistence is required.

Prefer the built-in checkpoint mechanism.

If checkpoint persistence is needed:

Use the current project database.

(Currently SQLite; future databases should work without architectural changes.)

Do NOT implement custom file-based checkpoint systems.

--------------------------------------------------
WHEN TO PERSIST
--------------------------------------------------

Persist state only when necessary.

Examples:

- Long-running workflows
- Human-in-the-loop
- Workflow resume
- Retry after failure
- Crash recovery
- Workflow history

Short-lived workflows should remain entirely in memory.

--------------------------------------------------
REMOVE FILE STORAGE
--------------------------------------------------

Remove every temporary storage pattern such as:

temp.json

output.json

context.json

prompt_output.txt

intermediate.md

workflow_cache.*

Any similar temporary artifacts.

--------------------------------------------------
FINAL OUTPUTS
--------------------------------------------------

Only final business artifacts may be persisted.

Examples:

Generated Resume

Generated Cover Letter

Generated Roadmap

Generated Insights

Generated Website

Intermediate artifacts should remain inside State.

--------------------------------------------------
NODE COMMUNICATION
--------------------------------------------------

Nodes must never communicate through files.

They must read/write only from LangGraph State.

--------------------------------------------------
ERROR RECOVERY
--------------------------------------------------

Ensure failed workflows can resume from checkpoints when appropriate.

Avoid restarting the entire workflow unnecessarily.

--------------------------------------------------
OBSERVABILITY
--------------------------------------------------

Track:

Workflow ID

Execution ID

Current Node

Current State Version

Checkpoint Count

Resume Events

Completion Time

Failure Events

--------------------------------------------------
TESTING
--------------------------------------------------

Create tests for:

State transitions

Checkpoint recovery

Resume after failure

State validation

Node communication

Memory-only execution

Persistent execution

--------------------------------------------------
DOCUMENTATION
--------------------------------------------------

Create:

docs/ai/state-management.md

docs/ai/langgraph-state.md

docs/ai/checkpointing.md

docs/architecture/workflow-state.md

docs/adr/011-langgraph-state.md

Document:

- State lifecycle
- Checkpoint strategy
- Memory vs persistent state
- Resume strategy
- Recovery strategy

--------------------------------------------------
ACCEPTANCE CRITERIA
--------------------------------------------------

✔ Every workflow uses LangGraph State.

✔ Temporary files are eliminated.

✔ Nodes communicate only through State.

✔ Checkpointing uses LangGraph's native mechanisms.

✔ Persistent checkpoints use the existing database when needed.

✔ Existing workflow behavior remains unchanged.

✔ State models are strongly typed.

✔ Workflows are ready for future migration to PostgreSQL without changing the state architecture.
