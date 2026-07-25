"""Agent tools — domain services wrapping existing business logic.

Tools are thin adapters over existing services. They do NOT duplicate logic.
Each tool follows SRP and depends on abstractions (DIP).
"""

from .base import BaseTool, ToolResult

__all__ = ["BaseTool", "ToolResult"]
