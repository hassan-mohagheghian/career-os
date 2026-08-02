"""Tool Registry and Selection Strategy.

Manages tool registration, capability discovery, and selection.
Implements the configurable priority: Local → Cached → Internal → Provider → Manual.

Design: Registry Pattern + Strategy Pattern.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from shared.infrastructure.process.logging_config import get_logger
from .base import BaseTool, ToolResult
from .models import ToolExecutionLog
log = get_logger("ai.tools.registry")


class ToolCategory(str, Enum):
    FETCH = "fetch"
    EXTRACT = "extract"
    ANALYZE = "analyze"
    SEARCH = "search"
    TRANSFORM = "transform"
    PERSIST = "persist"


class ToolPriority(int, Enum):
    LOCAL = 1
    CACHED = 2
    INTERNAL_SERVICE = 3
    PROVIDER_NATIVE = 4
    MANUAL = 5


class ToolRegistration:
    """Metadata for a registered tool."""

    def __init__(
        self,
        tool: BaseTool,
        category: ToolCategory,
        priority: ToolPriority = ToolPriority.LOCAL,
        capabilities: Optional[list[str]] = None,
    ):
        self.tool = tool
        self.category = category
        self.priority = priority
        self.capabilities = capabilities or []
        self.execution_count = 0
        self.total_time_ms = 0.0


class ToolRegistry:
    """Central registry for all available tools.

    Supports:
    - Registration by category and capability
    - Priority-based selection
    - Execution logging and observability
    """

    def __init__(self):
        self._tools: dict[str, ToolRegistration] = {}
        self._execution_log: list[ToolExecutionLog] = []

    def register(
        self,
        tool: BaseTool,
        category: ToolCategory,
        priority: ToolPriority = ToolPriority.LOCAL,
        capabilities: Optional[list[str]] = None,
    ) -> None:
        """Register a tool in the registry."""
        reg = ToolRegistration(
            tool=tool,
            category=category,
            priority=priority,
            capabilities=capabilities or [],
        )
        self._tools[tool.name] = reg
        log.debug("tool.registered", name=tool.name, category=category.value)

    def get(self, name: str) -> Optional[ToolRegistration]:
        """Get a tool by name."""
        return self._tools.get(name)

    def find_by_capability(
        self,
        capability: str,
        category: Optional[ToolCategory] = None,
    ) -> list[ToolRegistration]:
        """Find tools that declare a specific capability, sorted by priority."""
        results = []
        for reg in self._tools.values():
            if capability in reg.capabilities:
                if category is None or reg.category == category:
                    results.append(reg)
        results.sort(key=lambda r: r.priority.value)
        return results

    def find_by_category(self, category: ToolCategory) -> list[ToolRegistration]:
        """Find all tools in a category, sorted by priority."""
        results = [r for r in self._tools.values() if r.category == category]
        results.sort(key=lambda r: r.priority.value)
        return results

    def select_tool(
        self,
        capability: str,
        category: Optional[ToolCategory] = None,
    ) -> Optional[BaseTool]:
        """Select the best tool for a capability using priority ordering."""
        candidates = self.find_by_capability(capability, category)
        if candidates:
            return candidates[0].tool
        return None

    def execute(
        self,
        tool_name: str,
        **kwargs,
    ) -> ToolResult:
        """Execute a registered tool with observability logging."""
        import time

        reg = self._tools.get(tool_name)
        if not reg:
            return ToolResult(
                success=False,
                error=f"Tool not found: {tool_name}",
            )

        start = time.time()
        try:
            result = reg.tool.run(**kwargs)
            duration_ms = (time.time() - start) * 1000
            reg.execution_count += 1
            reg.total_time_ms += duration_ms

            log_entry = ToolExecutionLog(
                tool_name=tool_name,
                execution_time_ms=round(duration_ms, 2),
                success=result.success,
                input_size=_estimate_size(kwargs),
                output_size=_estimate_size(result.data) if result.success else 0,
                error=result.error,
            )
            self._execution_log.append(log_entry)

            log.info(
                "tool.executed",
                name=tool_name,
                success=result.success,
                duration_ms=round(duration_ms, 2),
            )
            return result
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            log_entry = ToolExecutionLog(
                tool_name=tool_name,
                execution_time_ms=round(duration_ms, 2),
                success=False,
                error=str(e),
            )
            self._execution_log.append(log_entry)
            return ToolResult(success=False, error=f"Tool execution failed: {e}")

    @property
    def execution_log(self) -> list[ToolExecutionLog]:
        return list(self._execution_log)

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "total_tools": len(self._tools),
            "total_executions": sum(r.execution_count for r in self._tools.values()),
            "total_time_ms": round(sum(r.total_time_ms for r in self._tools.values()), 2),
            "by_category": {
                cat.value: len([r for r in self._tools.values() if r.category == cat])
                for cat in ToolCategory
            },
        }


def _estimate_size(obj: Any) -> int:
    """Estimate the size of an object in characters."""
    if obj is None:
        return 0
    if isinstance(obj, str):
        return len(obj)
    if isinstance(obj, (dict, list)):
        return len(str(obj))
    return len(str(obj))


_global_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get or create the global tool registry singleton."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def reset_tool_registry() -> None:
    """Reset the global registry (for testing)."""
    global _global_registry
    _global_registry = None
