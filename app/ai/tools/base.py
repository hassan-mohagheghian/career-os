"""Base tool interface — contracts for all agent tools.

DDD: Tools are domain services that encapsulate a single capability.
SOLID:
- SRP: Each tool has one responsibility.
- OCP: New tools extend BaseTool without modifying it.
- LSP: Any BaseTool subclass can be used anywhere a BaseTool is expected.
- ISP: Tools expose only the run() method and input_schema property.
- DIP: Tools depend on abstractions, not on concrete services.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToolResult:
    """Value object — standardized tool execution result.

    DDD: Carries the result of a domain operation.
    """
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseTool(abc.ABC):
    """Abstract base class for all agent tools.

    Each tool:
    - Has a unique name and description
    - Defines an input schema for validation
    - Executes via run() method
    - Returns a ToolResult

    Design Pattern: Command Pattern — each tool encapsulates an action.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Unique tool name for agent registration."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def description(self) -> str:
        """Human-readable description of what the tool does."""
        raise NotImplementedError

    @property
    def input_schema(self) -> dict:
        """JSON Schema for tool input. Override for custom validation."""
        return {"type": "object", "properties": {}}

    @abc.abstractmethod
    def run(self, **kwargs) -> ToolResult:
        """Execute the tool with the given arguments.

        Returns:
            ToolResult with success/failure status and data.
        """
        raise NotImplementedError

    def to_langchain_tool(self):
        """Convert to a LangChain-compatible tool.

        Adapter Pattern: bridges our tool interface to LangChain's.
        """
        try:
            from langchain_core.tools import StructuredTool

            def _run(**kwargs):
                result = self.run(**kwargs)
                if result.success:
                    return result.data
                raise RuntimeError(result.error or "Tool failed")

            return StructuredTool(
                name=self.name,
                description=self.description,
                func=_run,
                args_schema=None,  # Could map input_schema to Pydantic
            )
        except ImportError:
            return self
