# ADR-004: AI Agent Orchestration Layer

## Status

Accepted

## Context

The project evolved from direct Mimo CLI subprocess calls to a multi-provider agent system. All 15 AI call sites were migrated to LLMService, and the architecture now supports swapping providers via environment variable.

## Decision

Introduce an AI Agent Orchestration Layer with:
- **LLMService**: Unified entry point for all AI calls (Facade Pattern)
- **Provider Abstraction**: Swap LLM providers without changing agent code (Strategy Pattern)
- **Agent Runtime**: LangGraph-based workflow orchestration (Builder Pattern)
- **Tool System**: Domain services wrapping existing business logic (Command Pattern)
- **Workflow Graphs**: Composable, stateful processing pipelines

## Alternatives Considered

- **Direct MimoRunner calls**: Rejected — tight coupling, no provider flexibility
- **LangChain agents**: Rejected — too heavy for simple prompt→response workflows
- **Custom framework**: Rejected — unnecessary abstraction for this scale

## Consequences

**Positive:**
- Provider swap via `AI_PROVIDER` env var (zero code changes)
- All AI calls go through single entry point (LLMService)
- Tests mock LLMService instead of MimoRunner
- New agents/tools follow consistent patterns
- Workflow graphs enable complex multi-step pipelines

**Negative:**
- Additional abstraction layer (3 files: service.py, base.py, mimo/adapter.py)
- Must import from `ai_compat` in server code (path bridging)
- LangGraph adds dependency (optional, graceful fallback)

## Migration Summary

| Component | Before | After |
|-----------|--------|-------|
| AI calls | Direct `MimoRunner.run()` | `LLMService.generate_structured()` |
| Provider | Hardcoded Mimo | `AI_PROVIDER` env var |
| Progress | Synchronous/blocking | WebSocket events |
| Tests | Mock `MimoRunner` | Mock `get_llm_service` |
