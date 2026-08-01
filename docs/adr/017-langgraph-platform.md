# ADR: LangGraph Platform Migration

## Status

Accepted

## Context

The project needed to migrate all AI generation workflows to a unified LangGraph-based architecture. Previously, workflows were implemented as ad-hoc Python functions with inconsistent patterns for error handling, state management, and output formatting.

## Decision

We adopt LangGraph as the primary workflow orchestration engine with the following architecture:

### 1. Graph-Based Workflows

Every AI generation process becomes an independent LangGraph workflow:
- `job_processing`: Job posting analysis
- `company_processing`: Company intelligence
- `resume_generation`: Tailored resume creation
- `cover_letter_generation`: Cover letter creation
- `skill_extraction`: Skill extraction from jobs
- `skill_roadmap`: Learning roadmap generation
- `insights`: Career intelligence (6 child graphs)
- `generate_all`: Parent orchestrator

### 2. Typed State and Outputs

- State: `BaseState` TypedDict flowing through all nodes
- Outputs: Strongly typed Pydantic models for each graph
- No free-text parsing; all structured data via models

### 3. Provider Abstraction

- All LLM calls go through `LLMProvider` interface
- Graphs never call providers directly
- Provider selection via `AI_PROVIDER` env var
- Future providers supported without changing workflows

### 4. Composable Architecture

- Career Insights uses 6 independent child graphs
- Each child graph is independently executable
- Parent orchestrator composes children in sequence
- Generate All orchestrates all workflow graphs

### 5. Common Features

- **Retry**: Per-node configurable retry with delay
- **Checkpointing**: Via LangGraph's MemorySaver
- **Streaming**: Step-by-step execution streaming
- **Error Recovery**: Partial failure support in insights
- **Progress Events**: Via ProgressEmitter

## Consequences

### Positive

- Unified workflow pattern across all AI features
- Strongly typed outputs reduce runtime errors
- Composable graphs enable flexible execution
- Provider abstraction supports future LLM providers
- Comprehensive test coverage for all graphs

### Negative

- Increased complexity vs. simple function calls
- LangGraph dependency adds to package size
- Learning curve for developers unfamiliar with state machines

### Neutral

- Existing `LLMService` remains as the unified entry point
- Old agent classes (e.g., `JobExtractorAgent`) are preserved for backward compatibility
- Prompts are organized per-graph in `prompts/` directory

## Alternatives Considered

1. **Simple function chains**: Rejected due to lack of checkpointing, streaming, and retry support
2. **Celery workflows**: Rejected as overkill for synchronous AI processing
3. **Custom state machine**: Rejected due to maintenance burden; LangGraph provides battle-tested infrastructure

## References

- LangGraph documentation: https://langchain-ai.github.io/langgraph/
- Project architecture: DDD + Hexagonal Architecture
- Existing patterns: GraphBuilder, AgentExecutor, AgentRegistry
