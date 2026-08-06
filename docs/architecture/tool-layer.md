# Tool Layer Architecture

## Overview

The Tool Layer provides a unified abstraction for all tool executions across AI workflows. It implements the **local-first philosophy**: always prefer executing tools locally before delegating to LLM provider-native tools.

## Design Principles

1. **Local-First**: Execute locally whenever practical
2. **Provider-Independence**: No workflow contains provider-specific logic
3. **Typed Outputs**: All tools return structured, validated models
4. **Observable**: All executions are logged with timing
5. **Cacheable**: Redundant operations are cached
6. **Configurable**: Tool selection priority is configurable

## Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    AI Workflows                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │   Job    │  │ Company  │  │  Resume  │  │ Skills │  │
│  │Processing│  │Processing│  │Generation│  │Extrac. │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───┬────┘  │
│       │              │              │             │       │
│  ┌────▼──────────────▼──────────────▼─────────────▼───┐  │
│  │              Tool Registry                          │  │
│  │  • Registration  • Selection  • Execution Logging  │  │
│  └────┬───────────────────────────────────────────────┘  │
│       │                                                   │
│  ┌────▼───────────────────────────────────────────────┐  │
│  │              Tool Implementations                   │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │  │
│  │  │   Web    │  │  LLM     │  │   Database       │ │  │
│  │  │  Tools   │  │  Tools   │  │   Tools          │ │  │
│  │  └────┬─────┘  └──────────┘  └──────────────────┘ │  │
│  │       │                                              │  │
│  │  ┌────▼──────────────────────────────────────────┐  │  │
│  │  │           Content Cache                        │  │  │
│  │  │  • File-based  • SHA256 keys  • TTL support   │  │  │
│  │  └────┬──────────────────────────────────────────┘  │  │
│  │       │                                              │  │
│  │  ┌────▼──────────────────────────────────────────┐  │  │
│  │  │        Local Fetch Pipeline                    │  │  │
│  │  │  HTTP → Retry → Encoding → Clean → Extract    │  │  │
│  │  └───────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

### URL Fetching

```
Workflow Node
    │
    ▼
ToolRegistry.select_tool("http")
    │
    ▼
WebFetchTool.run(url=...)
    │
    ├──▶ Cache.get(url) ──▶ Return cached FetchedPage
    │
    ▼
fetch_page(url)
    │
    ├──▶ HTTP Request
    ├──▶ Retry Logic
    ├──▶ HTML Cleaning
    ├──▶ Content Extraction
    └──▶ Text Normalization
    │
    ▼
Cache.set(url, page)
    │
    ▼
FetchedPage (structured result)
```

## File Structure

```
ai/infrastructure/tools/
├── __init__.py          # Public API exports
├── base.py              # BaseTool, ToolResult
├── models.py            # FetchedPage, ContentExtraction, etc.
├── fetch.py             # Local HTTP fetching pipeline
├── cache.py             # Content caching layer
├── web.py               # WebFetchTool, CompanyFetchTool
├── registry.py          # Tool registration and selection
├── job_tools.py         # Job-specific tools
├── company_tools.py     # Company-specific tools
├── skill_tools.py       # Skill-specific tools
├── resume_tools.py      # Resume-specific tools
└── database.py          # Database query tools
```

## Key Files Modified

| File | Change |
|------|--------|
| `worker.py` | `_fetch_url` now uses `fetch_page()` |
| `backfill_raw.py` | `fetch_url` now uses `fetch_page()` |
| `stream_server.py` | `fetch_url` now uses `fetch_page()` |
| `job/graph.py` | `fetch_url` node uses `WebFetchTool` |
| `job_processing.py` | `fetch_url` node uses `fetch_page()` |
| `job_tools.py` | `FetchJobTool` uses `WebFetchTool` |
| `company_tools.py` | `FetchCompanyTool` uses `CompanyFetchTool` |
