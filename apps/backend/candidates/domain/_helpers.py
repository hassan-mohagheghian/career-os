"""Shared helpers for candidate domain entities."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def parse_datetime(value: Any) -> datetime | None:
    """Parse a datetime or ISO-8601 string into a ``datetime`` (or None)."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))
