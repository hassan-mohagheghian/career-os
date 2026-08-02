from __future__ import annotations

from typing import Any, Optional

from langchain_core.prompts import (
    ChatPromptTemplate as LangChainChatPromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.prompts.chat import (
    ChatPromptValue,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

from .base import PromptSpec, PromptType


class PromptTemplate:
    def __init__(
        self,
        template: LangChainChatPromptTemplate,
        spec: PromptSpec,
    ):
        self._template = template
        self._spec = spec

    @property
    def spec(self) -> PromptSpec:
        return self._spec

    @property
    def identifier(self) -> str:
        return self._spec.identifier

    @property
    def version(self) -> str:
        return self._spec.version

    @property
    def input_variables(self) -> list[str]:
        return list(self._template.input_variables)

    def _fill_kwargs(self, **kwargs: Any) -> dict[str, Any]:
        filled = dict(kwargs)
        for var in self._template.input_variables:
            if var not in filled:
                filled[var] = ""
        return filled

    def render(self, **kwargs: Any) -> str:
        filled = self._fill_kwargs(**kwargs)
        messages = self._template.format_messages(**filled)
        lines: list[str] = []
        for msg in messages:
            prefix = msg.type.upper() if msg.type else "SYSTEM"
            lines.append(f"<{prefix}>")
            lines.append(str(msg.content))
            lines.append(f"</{prefix}>")
        return "\n".join(lines)

    def render_messages(self, **kwargs: Any) -> list[dict[str, str]]:
        filled = self._fill_kwargs(**kwargs)
        messages = self._template.format_messages(**filled)
        return [{"role": m.type, "content": str(m.content)} for m in messages]

    def render_prompt_value(self, **kwargs: Any) -> ChatPromptValue:
        return self._template.format_prompt(**kwargs)

    @classmethod
    def from_string(
        cls,
        template: str,
        identifier: str,
        owner: str,
        version: str = "1.0.0",
        prompt_type: PromptType = PromptType.SYSTEM,
        description: str = "",
        **kwargs: Any,
    ) -> PromptTemplate:
        langchain_template = LangChainChatPromptTemplate.from_template(template)
        spec = PromptSpec(
            identifier=identifier,
            version=version,
            description=description,
            owner=owner,
            prompt_type=prompt_type,
            **kwargs,
        )
        return cls(langchain_template, spec)

    @classmethod
    def from_messages(
        cls,
        messages: list[tuple[str, str]],
        identifier: str,
        owner: str,
        version: str = "1.0.0",
        prompt_type: PromptType = PromptType.SYSTEM,
        description: str = "",
        **kwargs: Any,
    ) -> PromptTemplate:
        langchain_template = LangChainChatPromptTemplate.from_messages(messages)
        spec = PromptSpec(
            identifier=identifier,
            version=version,
            description=description,
            owner=owner,
            prompt_type=prompt_type,
            **kwargs,
        )
        return cls(langchain_template, spec)


def system_template(template: str) -> SystemMessagePromptTemplate:
    return SystemMessagePromptTemplate.from_template(template)


def human_template(template: str) -> HumanMessagePromptTemplate:
    return HumanMessagePromptTemplate.from_template(template)


def placeholder(name: str) -> MessagesPlaceholder:
    return MessagesPlaceholder(variable_name=name)
