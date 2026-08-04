# Sprint 09 — Optimize AI Tooling: Prefer Local Tools Before LLM Provider Tools

## ROLE

You are a Principal AI Systems Architect, LangChain Expert, LangGraph Expert, LLM Infrastructure Engineer, and Software Performance Engineer.

Your task is to redesign the AI tool execution strategy to minimize LLM cost, latency, and unnecessary provider-side tool usage.

The project already uses:

- LangChain
- LangGraph
- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- ARQ

The objective is to ensure that every workflow intelligently chooses between local tools and provider-native tools.

Business behavior must remain unchanged.

---

# OBJECTIVES

Create a unified AI Tool Layer that all LangGraph workflows use.

The AI workflows should not directly depend on OpenAI tools (or any provider's built-in tools).

Instead, every tool invocation must go through a common abstraction layer.

---

# TOOL EXECUTION PHILOSOPHY

Always prefer executing tools locally whenever doing so is practical.

LLM provider tools should only be used when they provide a clear advantage that cannot reasonably be achieved locally.

Optimize for:

- Lower latency
- Lower token usage
- Lower API cost
- Deterministic behavior
- Easier testing
- Provider independence

---

# TOOL ABSTRACTION

Design a generic Tool Provider interface.

Example responsibilities:

- Fetch Web Page
- Search
- Download URL
- Parse HTML
- Extract Metadata
- Read PDF
- Read Markdown
- Read DOCX
- Read Images
- OCR
- Extract Structured Data
- Execute Python Utilities
- File Processing

Every LangGraph workflow should use this abstraction rather than directly invoking provider-specific capabilities.

---

# WEB FETCHING

Review every workflow that consumes URLs.

Examples:

- Job Processing
- Company Processing
- Resume Processing
- Career Insights
- Site Generation

For every URL:

Prefer:

Local HTTP fetching

↓

HTML parsing

↓

Readability extraction

↓

Structured cleaning

↓

Markdown conversion (optional)

↓

Send only the cleaned content to the LLM.

Do NOT send URLs directly to the LLM when the application can retrieve and preprocess the content itself.

---

# CONTENT EXTRACTION

Implement a reusable content extraction pipeline.

Examples:

HTTP Request

↓

Redirect Handling

↓

Retry

↓

Encoding Detection

↓

HTML Cleaning

↓

Remove Navigation

↓

Remove Ads

↓

Remove Scripts

↓

Extract Main Content

↓

Normalize Text

↓

Return Structured Result

The LLM should receive clean, focused content instead of noisy raw HTML whenever possible.

---

# PROVIDER TOOL EVALUATION

Review every supported AI provider.

Examples:

- OpenAI
- Anthropic
- Google Gemini
- OpenRouter
- Future providers

Determine for each provider:

- Which native tools exist
- Whether they improve accuracy
- Whether they increase cost
- Whether they reduce latency
- Whether they consume additional tokens
- Whether they require additional API calls
- Whether they return deterministic results

Document the findings.

---

# TOOL SELECTION STRATEGY

Implement a configurable strategy.

Preferred order:

1. Local Tool
2. Cached Result
3. Internal Service
4. Provider Native Tool
5. Manual User Input (if required)

This priority should be configurable.

---

# CACHING

Avoid fetching identical URLs repeatedly.

Introduce caching where appropriate.

Examples:

- Web Pages
- Robots Metadata
- Parsed Documents
- PDFs
- Markdown

Cache invalidation policy should be configurable.

---

# STRUCTURED OUTPUTS

Local tools should return structured models instead of raw strings.

Example:

FetchedPage

- url
- title
- canonical_url
- markdown
- plain_text
- language
- metadata
- fetched_at
- status_code

LangGraph nodes should consume these typed objects.

---

# ERROR HANDLING

Handle failures gracefully.

Examples:

404

403

429

Timeout

Redirect Loop

Invalid SSL

Unsupported Content

Large Documents

Rate Limiting

Return typed errors rather than throwing unexpected exceptions.

---

# PROVIDER INDEPENDENCE

No workflow should contain provider-specific logic.

Avoid code like:

if provider == OpenAI

Instead:

Use dependency injection and capability discovery.

---

# OBSERVABILITY

Log:

- Tool selected
- Tool execution time
- Cache hit/miss
- Tokens saved (estimated)
- Provider calls avoided
- Fetch failures
- Retry attempts

---

# PERFORMANCE

Optimize for:

- Minimal token usage
- Minimal latency
- Reduced network requests
- Streaming where appropriate
- Parallel execution when safe

Only invoke the LLM after all deterministic preprocessing has completed.

---

# TESTING

Create tests for:

- Web Fetch
- HTML Cleaning
- Markdown Extraction
- Cache Behavior
- Retry Logic
- Provider Fallback
- Tool Selection
- Error Handling

---

# DOCUMENTATION

Create:

docs/ai/tooling.md

docs/ai/tool-selection.md

docs/ai/web-fetching.md

docs/ai/provider-capabilities.md

docs/architecture/tool-layer.md

docs/adr/009-ai-tool-platform.md

Document:

- Tool architecture
- Selection strategy
- Provider capability matrix
- Local vs provider trade-offs
- Caching strategy
- Error recovery strategy

---

# ACCEPTANCE CRITERIA

✔ Every AI workflow uses the shared Tool Layer.

✔ URLs are fetched and preprocessed locally whenever practical.

✔ The LLM receives clean, structured content instead of raw web pages whenever possible.

✔ Provider-native tools are only used when they offer a measurable benefit.

✔ Tool selection is configurable and provider-independent.

✔ Tool outputs are strongly typed.

✔ Redundant network requests are minimized through caching.

✔ Existing business behavior remains unchanged.

✔ The architecture is ready to support additional AI providers without modifying workflows.
