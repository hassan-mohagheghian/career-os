# ADR-010: Prompt Management Platform

## Status

Accepted (Sprint 10)

## Context

Prompt engineering has become a first-class architectural concern. Previously, prompts were:
- Embedded as raw strings in workflow code
- Loaded from flat `.txt` files in bounded context `infrastructure/ai/prompts/` directories
- Rendered via simple string substitution (`str.format()`)
- Not versioned, not typed, not testable

## Decision

Build a centralized Prompt Platform with the following characteristics:

1. **ChatPromptTemplate**: All prompts use LangChain's `ChatPromptTemplate` instead of manual string formatting.
2. **Prompt Registry**: Centralized `PromptRegistry` that resolves prompts by identifier (e.g. `job.extract`, `company.analyze`).
3. **Versioning**: Every prompt has an explicit semantic version. Multiple versions coexist. Workflows request by identifier, registry resolves the version.
4. **Typed Input Models**: Every prompt has a corresponding Pydantic input model (`JobExtractionInput`, `JobScoreInput`, etc.) instead of raw dictionaries.
5. **Structured Output**: Prompts instruct the LLM to return structured JSON.
6. **Provider Independence**: Templates contain no provider-specific syntax.
7. **Reusable Components**: Tone instructions, formatting rules, JSON rules, safety instructions are defined as reusable `SystemMessagePromptTemplate` components.
8. **Ownership**: Each bounded context owns its prompts. The `owner` field on `PromptSpec` tracks which context owns a prompt.
9. **Observability**: A `PromptLogger` tracks render counts, execution times, and failures.
10. **Testing**: Every prompt has tests for rendering, variables, missing inputs, structured output, regression, and golden output.

## Consequences

### Positive
- Prompts are modular, versioned, testable, reusable, and maintainable
- Adding new prompts follows a consistent pattern
- Provider-specific logic is isolated to adapter layer
- Migration to external prompt registries (LangSmith, LangFuse, PromptLayer) is possible without modifying workflows
- Backward compatible — existing `.md` files and `PromptManager` still work

### Negative
- Additional abstraction layer to maintain
- All existing graph nodes and tools need to migrate from legacy `load_prompt()` to the new registry

## Future Work

- Migrate all graph nodes to use `PromptRegistry.get()` instead of legacy `load_prompt()`
- Add LangChain Hub integration as an external provider
- Add prompt editing UI
- Add A/B testing for prompt versions
