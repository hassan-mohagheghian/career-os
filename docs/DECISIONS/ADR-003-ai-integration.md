# ADR-003: AI Integration (Mimo CLI Subprocess)

## Context

Need AI capabilities for job analysis, company intelligence, skill insights, and resume generation without paying for API services.

## Decision

Use Mimo CLI as a subprocess — spawn `mimo run <prompt>` and parse JSON output.

## Alternatives

- **OpenAI API**: Rejected — costs money, user has no budget
- **Anthropic API**: Rejected — costs money
- **Local LLM**: Rejected — requires GPU, setup complexity
- **LangChain**: Rejected — unnecessary abstraction for simple prompt→response

## Consequences

**Positive:**
- Zero cost for AI operations
- Full control over prompts and output parsing
- Session-based conversation continuity via `--session` flag
- Cancellation support via process management

**Negative:**
- Depends on Mimo CLI being installed
- Subprocess management complexity (timeouts, cleanup)
- JSON parsing from streaming output requires careful error handling
- No streaming response to UI during generation (only progress events)
