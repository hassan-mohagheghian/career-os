from __future__ import annotations

from typing import Any, Optional

from .base import PromptSpec, PromptType, PromptVersion
from .template import PromptTemplate
from .observability import get_prompt_logger


class PromptRegistry:
    _prompts: dict[str, dict[str, PromptTemplate]]

    def __init__(self):
        self._prompts: dict[str, dict[str, PromptTemplate]] = {}

    def register(self, prompt: PromptTemplate) -> None:
        ident = prompt.identifier
        ver = prompt.version
        if ident not in self._prompts:
            self._prompts[ident] = {}
        self._prompts[ident][ver] = prompt

    def get(
        self,
        identifier: str,
        version: str = "latest",
    ) -> PromptTemplate:
        versions = self._prompts.get(identifier)
        if not versions:
            msg = f"Prompt '{identifier}' not found in registry"
            raise KeyError(msg)

        if version == "latest":
            sorted_vers = sorted(versions.keys())
            return versions[sorted_vers[-1]]

        if version not in versions:
            msg = f"Prompt '{identifier}' version '{version}' not found"
            raise KeyError(msg)

        return versions[version]

    def get_spec(self, identifier: str, version: str = "latest") -> PromptSpec:
        return self.get(identifier, version).spec

    def exists(self, identifier: str, version: str = "latest") -> bool:
        try:
            self.get(identifier, version)
            return True
        except KeyError:
            return False

    def list_identifiers(self) -> list[str]:
        return sorted(self._prompts.keys())

    def list_versions(self, identifier: str) -> list[str]:
        versions = self._prompts.get(identifier)
        if not versions:
            return []
        return sorted(versions.keys())

    def list_by_owner(self, owner: str) -> list[PromptSpec]:
        result: list[PromptSpec] = []
        for ident, versions in self._prompts.items():
            latest = versions[sorted(versions.keys())[-1]]
            if latest.spec.owner == owner:
                result.append(latest.spec)
        return result

    def list_by_tags(self, tags: list[str]) -> list[PromptSpec]:
        result: list[PromptSpec] = []
        tag_set = set(tags)
        for ident, versions in self._prompts.items():
            latest = versions[sorted(versions.keys())[-1]]
            if tag_set.intersection(latest.spec.tags):
                result.append(latest.spec)
        return result

    def all_specs(self) -> list[PromptSpec]:
        result: list[PromptSpec] = []
        for ident, versions in self._prompts.items():
            latest = versions[sorted(versions.keys())[-1]]
            result.append(latest.spec)
        return result

    def deregister(self, identifier: str, version: Optional[str] = None) -> None:
        if identifier not in self._prompts:
            return
        if version:
            self._prompts[identifier].pop(version, None)
            if not self._prompts[identifier]:
                del self._prompts[identifier]
        else:
            del self._prompts[identifier]

    def render(
        self,
        identifier: str,
        version: str = "latest",
        **kwargs: Any,
    ) -> str:
        prompt = self.get(identifier, version)
        logger = get_prompt_logger()
        result = prompt.render(**kwargs)
        logger.log_render(identifier, prompt.version, len(result))
        return result

    def create_prompt(
        self,
        identifier: str,
        template: str,
        owner: str,
        version: str = "1.0.0",
        prompt_type: PromptType = PromptType.SYSTEM,
        description: str = "",
        **kwargs: Any,
    ) -> PromptTemplate:
        prompt = PromptTemplate.from_string(
            template=template,
            identifier=identifier,
            owner=owner,
            version=version,
            prompt_type=prompt_type,
            description=description,
            **kwargs,
        )
        self.register(prompt)
        return prompt

    def create_version(
        self,
        identifier: str,
        template: str,
        version: str,
        description: str = "",
        **kwargs: Any,
    ) -> PromptTemplate:
        base = self.get(identifier)
        spec = base.spec.model_copy()
        spec.version = version
        spec.description = description
        spec.changelog.append(
            PromptVersion(version=version, description=description)
        )
        prompt = PromptTemplate.from_string(
            template=template,
            identifier=identifier,
            owner=spec.owner,
            version=version,
            prompt_type=spec.prompt_type,
            description=description,
            **kwargs,
        )
        self.register(prompt)
        return prompt


_registry: Optional[PromptRegistry] = None


def get_registry() -> PromptRegistry:
    global _registry
    if _registry is None:
        _registry = PromptRegistry()
    return _registry


def reset_registry() -> None:
    global _registry
    _registry = None


def register_prompt(
    identifier: str,
    template: str,
    owner: str,
    version: str = "1.0.0",
    prompt_type: PromptType = PromptType.SYSTEM,
    description: str = "",
    **kwargs: Any,
) -> PromptTemplate:
    return get_registry().create_prompt(
        identifier=identifier,
        template=template,
        owner=owner,
        version=version,
        prompt_type=prompt_type,
        description=description,
        **kwargs,
    )


def get_prompt(
    identifier: str,
    version: str = "latest",
    **kwargs: Any,
) -> str:
    return get_registry().render(identifier, version, **kwargs)
