"""Agent tools — unified AI Tool Layer for all workflows.

Tools follow the local-first philosophy: always prefer executing tools
locally before delegating to LLM provider-native tools.

Architecture:
- base: ToolResult and BaseTool abstract interface
- models: Structured output models (FetchedPage, ContentExtraction, etc.)
- fetch: Local HTTP fetching with preprocessing pipeline
- cache: Content caching layer
- web: Unified web fetch tools (WebFetchTool, CompanyFetchTool, MultiSourceFetchTool)
- registry: Tool registration and priority-based selection
"""

from .base import BaseTool, ToolResult
from .models import FetchedPage, FetchStatus, FetchError, ContentExtraction, ToolExecutionLog
from .fetch import fetch_page, extract_content
from .cache import get_content_cache, ContentCache
from .web import WebFetchTool, CompanyFetchTool, MultiSourceFetchTool
from .registry import get_tool_registry, ToolRegistry, ToolCategory, ToolPriority

__all__ = [
    "BaseTool",
    "ToolResult",
    "FetchedPage",
    "FetchStatus",
    "FetchError",
    "ContentExtraction",
    "ToolExecutionLog",
    "fetch_page",
    "extract_content",
    "get_content_cache",
    "ContentCache",
    "WebFetchTool",
    "CompanyFetchTool",
    "MultiSourceFetchTool",
    "get_tool_registry",
    "ToolRegistry",
    "ToolCategory",
    "ToolPriority",
]
