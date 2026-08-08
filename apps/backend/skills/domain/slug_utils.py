"""Slug helpers for canonical skill and category names.

A slug is the canonical, case/format-insensitive key for a name. It makes
"NoSQL" and "nosql" (or "Data Engineering" and "data engineering") resolve to
the same skill/category, and it is the equality key used during extraction and
breakdown. Keeps useful punctuation (`+ . # -`) so `C#` and `React.js` stay
readable.
"""

from __future__ import annotations

import re

_SEPARATORS = re.compile(r"[^\w+#.\-]+", flags=re.UNICODE)


def slugify(name: str | None) -> str:
    """Build the canonical slug for ``name``.

    Lowercases, trims, collapses whitespace/separators to a single ``-`` and
    keeps ``+ . # -``. Returns an empty string for blank input.

    Examples:
        "NoSQL"           -> "nosql"
        "NoSQL / SQL"     -> "nosql-sql"
        "React.js"        -> "react.js"
        "C#"              -> "c#"
        "Data Engineering" -> "data-engineering"
    """
    if not name:
        return ""
    cleaned = _SEPARATORS.sub("-", name.strip().lower())
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    return cleaned
