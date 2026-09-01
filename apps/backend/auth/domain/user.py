"""Auth domain: User entity."""

from __future__ import annotations

import uuid
from datetime import datetime, UTC


class User:
    """User domain entity.

    Attributes:
        id: UUID v4 identifier
        username: unique login name
        display_name: human-readable name
        password_hash: bcrypt-hashed password (never exposed in API responses)
        created_at: account creation timestamp
        updated_at: last modification timestamp
    """

    def __init__(
        self,
        username: str,
        display_name: str,
        password_hash: str,
        id: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self._id = id or str(uuid.uuid4())
        self._username = username
        self._display_name = display_name
        self._password_hash = password_hash
        self._created_at = created_at or datetime.now(UTC)
        self._updated_at = updated_at or datetime.now(UTC)

    @property
    def id(self) -> str:
        return self._id

    @property
    def username(self) -> str:
        return self._username

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def password_hash(self) -> str:
        return self._password_hash

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)

    def __repr__(self) -> str:
        return f"User(id={self._id!r}, username={self._username!r})"
