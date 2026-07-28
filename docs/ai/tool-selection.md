# Tool Selection Strategy

## Priority Order

The tool selection strategy follows a configurable priority:

1. **Local Tool** — Execute locally when practical (fastest, cheapest)
2. **Cached Result** — Return cached content if available (zero-cost)
3. **Internal Service** — Use internal microservices if available
4. **Provider Native Tool** — Use LLM provider tools only when they provide clear advantage
5. **Manual User Input** — Last resort, require user intervention

## Implementation

The `ToolRegistry` implements priority-based selection:

```python
from ai.infrastructure.tools.registry import get_tool_registry, ToolCategory, ToolPriority

registry = get_tool_registry()

# Register tools with priorities
registry.register(
    WebFetchTool(),
    category=ToolCategory.FETCH,
    priority=ToolPriority.LOCAL,
    capabilities=["http", "url"],
)

# Select best tool for a capability
tool = registry.select_tool("http")  # Returns WebFetchTool (LOCAL priority)
```

## When to Use Provider-Native Tools

Provider-native tools should only be used when:

| Capability | Local | Provider | Rationale |
|------------|-------|----------|-----------|
| URL Fetching | ✅ | ❌ | Local is faster and cheaper |
| HTML Cleaning | ✅ | ❌ | Deterministic, no tokens |
| Text Extraction | ✅ | ❌ | Deterministic regex |
| Code Generation | ❌ | ✅ | Requires LLM intelligence |
| Complex Analysis | ❌ | ✅ | Requires reasoning |
| Structured Extraction | ❌ | ✅ | When schema is complex |
| Summarization | ❌ | ✅ | Requires understanding |

## Configuration

Priority is configurable per-tool:

```python
from ai.infrastructure.tools.registry import ToolPriority

# Override default priority
registry.register(
    MyTool(),
    category=ToolCategory.EXTRACT,
    priority=ToolPriority.CACHED,  # Prefer cache over local
)
```

## Observability

The registry tracks:

- Tool execution count
- Total execution time
- Cache hit/miss ratio
- Provider calls avoided (estimated tokens saved)

```python
stats = registry.stats
print(f"Total executions: {stats['total_executions']}")
print(f"Total time: {stats['total_time_ms']}ms")
```
