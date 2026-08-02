"""PromptManager — manages prompt templates per graph node.

SRP: Each prompt template is owned by its graph node.
Template Method: Prompts can be loaded from files or strings.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional


class PromptTemplate:
    """A prompt template with variable substitution."""

    def __init__(self, template: str, name: str = ""):
        self._template = template
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def render(self, **kwargs: Any) -> str:
        """Render the template with the given variables.

        Args:
            **kwargs: Variables to substitute in the template.

        Returns:
            Rendered prompt string.
        """
        result = self._template
        for key, value in kwargs.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    def __str__(self) -> str:
        return self._template


class PromptManager:
    """Manages prompt templates for graph nodes.

    Each graph node owns its prompts. Avoid global prompt folders.
    """

    def __init__(self, base_dir: Optional[str] = None):
        self._base_dir = base_dir or os.path.join(
            os.path.dirname(__file__), "prompts"
        )
        self._templates: dict[str, PromptTemplate] = {}

    def load_prompt(
        self,
        node_name: str,
        prompt_name: str,
        subdirectory: str = "",
    ) -> PromptTemplate:
        """Load a prompt template from a file.

        Args:
            node_name: The graph node name.
            prompt_name: The prompt file name (without extension).
            subdirectory: Optional subdirectory within the prompts folder.

        Returns:
            Loaded PromptTemplate.
        """
        cache_key = f"{node_name}/{subdirectory}/{prompt_name}"
        if cache_key in self._templates:
            return self._templates[cache_key]

        # Build file path
        path_parts = [self._base_dir, node_name]
        if subdirectory:
            path_parts.append(subdirectory)
        path_parts.append(f"{prompt_name}.md")

        file_path = os.path.join(*path_parts)

        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                content = f.read()
            template = PromptTemplate(content, name=cache_key)
        else:
            # Return empty template if file not found
            template = PromptTemplate("", name=cache_key)

        self._templates[cache_key] = template
        return template

    def register_prompt(
        self,
        node_name: str,
        prompt_name: str,
        template: str,
    ) -> None:
        """Register a prompt template programmatically.

        Args:
            node_name: The graph node name.
            prompt_name: The prompt name.
            template: The prompt template string.
        """
        cache_key = f"{node_name}/{prompt_name}"
        self._templates[cache_key] = PromptTemplate(template, name=cache_key)

    def get_prompt(
        self,
        node_name: str,
        prompt_name: str,
    ) -> Optional[PromptTemplate]:
        """Get a registered prompt template."""
        cache_key = f"{node_name}/{prompt_name}"
        return self._templates.get(cache_key)

    def list_prompts(self, node_name: str) -> list[str]:
        """List all prompts for a node."""
        return [
            key.split("/", 1)[1]
            for key in self._templates
            if key.startswith(f"{node_name}/")
        ]
