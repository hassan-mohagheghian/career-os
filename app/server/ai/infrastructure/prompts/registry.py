"""Prompt Registry — centralized prompt management.

SRP: Only manages prompt loading and versioning.
OCP: New prompt sources can be added without modifying the registry.
"""

from __future__ import annotations

import os
from typing import Optional


class PromptRegistry:
    """Centralized prompt registry with versioning support.

    Delegates to existing load_prompt() for template rendering.
    Adds agent-specific namespace lookup.
    """

    def __init__(self, prompts_dir: Optional[str] = None):
        if prompts_dir is None:
            # Default to the project's prompts directory
            _file_dir = os.path.dirname(os.path.abspath(__file__))
            prompts_dir = os.path.join(_file_dir, '..', '..', 'server', 'prompts')
        self._prompts_dir = os.path.abspath(prompts_dir)

    def get_prompt(self, name: str, **kwargs) -> str:
        """Load and render a prompt template.

        Args:
            name: Prompt name (e.g., 'job_processing/step8_score').
                  Supports nested paths like 'company/company_extract'.
            **kwargs: Template variables to fill in.

        Returns:
            Rendered prompt string.
        """
        try:
            import sys
            sys.path.insert(0, os.path.join(self._prompts_dir, '..'))
            from prompts import load_prompt
            return load_prompt(name, **kwargs)
        except (ImportError, FileNotFoundError):
            # Fallback: try direct file read
            return self._fallback_load(name, **kwargs)

    def _fallback_load(self, name: str, **kwargs) -> str:
        """Fallback prompt loading via direct file read."""
        path = os.path.join(self._prompts_dir, f'{name}.txt')
        if os.path.exists(path):
            with open(path) as f:
                template = f.read()
            try:
                return template.format(**kwargs)
            except KeyError:
                return template
        raise FileNotFoundError(f"Prompt not found: {name}.txt (searched {self._prompts_dir})")

    def list_prompts(self) -> list[str]:
        """List all available prompt names."""
        prompts = []
        for root, dirs, files in os.walk(self._prompts_dir):
            for f in files:
                if f.endswith('.txt'):
                    rel = os.path.relpath(os.path.join(root, f), self._prompts_dir)
                    prompts.append(rel.replace('.txt', ''))
        return sorted(prompts)


# Module-level convenience function
_registry: Optional[PromptRegistry] = None


def get_prompt(name: str, **kwargs) -> str:
    """Load a prompt using the default registry.

    Module-level convenience function following the Singleton pattern.
    """
    global _registry
    if _registry is None:
        _registry = PromptRegistry()
    return _registry.get_prompt(name, **kwargs)
