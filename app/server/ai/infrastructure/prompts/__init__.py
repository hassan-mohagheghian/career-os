"""Centralized prompt management for AI agents.

Delegates to existing load_prompt() for template rendering.
Adds versioning support and agent-specific prompt lookup.
"""

from .registry import PromptRegistry, get_prompt

__all__ = ["PromptRegistry", "get_prompt"]
