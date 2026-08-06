"""Context budget — size caps for text fed into LLM analysis prompts.

Each extracted source is trimmed independently so a single oversized page
cannot crowd out the others, and the combined context is capped so the total
prompt stays well inside the provider output window (the models used truncate
or malform JSON when the input is too large).
"""

from __future__ import annotations

MAX_SOURCE_CHARS = 8_000
MAX_COMBINED_CHARS = 48_000
_TRIM_SUFFIX = "\n\n[truncated]"


def trim_text(text: str, *, max_chars: int, keep_head: bool = True) -> str:
    """Trim ``text`` to at most ``max_chars`` characters.

    By default the head of the text is kept (title/hero/meta are the most
    informative part of a page); ``keep_head=False`` keeps the tail instead.
    A marker is appended so callers know content was dropped.
    """
    text = text.strip()
    if len(text) <= max_chars:
        return text
    if keep_head:
        return text[: max_chars - len(_TRIM_SUFFIX)].rstrip() + _TRIM_SUFFIX
    return _TRIM_SUFFIX + text[-(max_chars - len(_TRIM_SUFFIX)) :].lstrip()
