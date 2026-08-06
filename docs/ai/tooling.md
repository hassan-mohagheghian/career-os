# AI Tooling

## Overview

The AI Tool Layer provides a unified abstraction for all tool executions across LangGraph workflows. It follows a **local-first philosophy**: always prefer executing tools locally before delegating to LLM provider-native tools.

## Architecture

```
┌─────────────────────────────────────────────────┐
│               LangGraph Workflows               │
│  (job_processing, resume_generation, ...)       │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│              Tool Registry                       │
│  - Tool registration by category/capability      │
│  - Priority-based selection                      │
│  - Execution logging & observability             │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│            Web Tools Layer                       │
│  WebFetchTool │ CompanyFetchTool │ MultiSource   │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│          Content Cache (file-based)              │
│  - SHA256 URL keys                               │
│  - Configurable TTL (default 6h)                 │
│  - Cache hit/miss tracking                       │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│         Local Fetch Pipeline                     │
│  HTTP → Retry → Encoding → HTML Clean →          │
│  Content Extract → Text Normalize                │
└─────────────────────────────────────────────────┘
```

## Key Modules

| Module | Path | Purpose |
|--------|------|---------|
| `models.py` | `ai/infrastructure/tools/models.py` | Structured output models (FetchedPage, ContentExtraction, etc.) |
| `fetch.py` | `ai/infrastructure/tools/fetch.py` | Local HTTP fetching with preprocessing pipeline |
| `cache.py` | `ai/infrastructure/tools/cache.py` | File-based content caching with configurable TTL |
| `web.py` | `ai/infrastructure/tools/web.py` | Web fetch tools (WebFetchTool, CompanyFetchTool, MultiSourceFetchTool) |
| `registry.py` | `ai/infrastructure/tools/registry.py` | Tool registration and priority-based selection |
| `base.py` | `ai/infrastructure/tools/base.py` | BaseTool abstract interface and ToolResult |

## Usage

### Direct Fetch

```python
from ai.infrastructure.tools.fetch import fetch_page

page = fetch_page("https://example.com/job/123")
if page.is_ok:
    print(page.plain_text)  # Cleaned, structured content
```

### Using WebFetchTool

```python
from ai.infrastructure.tools.web import WebFetchTool

tool = WebFetchTool()
result = tool.run(url="https://example.com/job/123")
if result.success:
    content = result.data["plain_text"]
```

### Multi-Source Fetching

```python
from ai.infrastructure.tools.web import MultiSourceFetchTool

tool = MultiSourceFetchTool()
result = tool.run(
    url="https://example.com/job",
    notes=[{"type": "text", "content": "Additional context"}],
    links=[{"url": "https://linkedin.com/jobs/123", "title": "LinkedIn"}],
)
```

## Benefits

- **Lower latency**: Local HTTP fetch is faster than LLM provider tools
- **Lower cost**: No tokens consumed for URL fetching
- **Deterministic**: Same URL always returns same content
- **Cached**: Redundant fetches are avoided
- **Provider-independent**: No dependency on OpenAI/Anthropic tools
- **Typed outputs**: FetchedPage provides structured, validated results
