"""Auth domain: User repository interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from auth.domain.user import User


class UserRepositoryInterface(ABC):
    """Abstract repository for User aggregate."""

    @abstractmethod
    def get_by_id(self, user_id: str) -> User | None: ...

    @abstractmethod
    def get_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    def create(self, user: User) -> User: ...

    @abstractmethod
    def update(self, user: User) -> User: ...

    @abstractmethod
    def delete(self, user_id: str) -> None: ...
