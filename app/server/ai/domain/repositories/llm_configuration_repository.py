from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..entities.llm_configuration import LLMConfiguration


class ILLMConfigurationRepository(ABC):
    @abstractmethod
    def get_by_id(self, config_id: str) -> Optional[LLMConfiguration]:
        ...

    @abstractmethod
    def get_all(self) -> list[LLMConfiguration]:
        ...

    @abstractmethod
    def save(self, config: LLMConfiguration) -> str:
        ...

    @abstractmethod
    def update(self, config: LLMConfiguration) -> str:
        ...

    @abstractmethod
    def delete(self, config_id: str) -> bool:
        ...

    @abstractmethod
    def get_enabled(self) -> list[LLMConfiguration]:
        ...
