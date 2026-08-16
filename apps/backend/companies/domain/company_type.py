"""Company type fixed vocabulary.

The ``company_type`` column must always hold one of the fixed values below.
Anything else (inaccurate LLM extraction, free-text manual entry) is coerced to
``UNKNOWN`` at the storage layer so a company reprocess with more resources
re-detects and persists a fixed type.
"""

from __future__ import annotations

VALID_COMPANY_TYPES: tuple[str, ...] = (
    "PRODUCT_COMPANY",
    "RECRUITING_AGENCY",
    "STAFFING_COMPANY",
    "CONSULTING_COMPANY",
    "UNKNOWN",
)


def normalize_company_type(value: str | None) -> str | None:
    """Coerce a company_type value to the fixed vocabulary.

    Empty/None → ``None`` (not classified). A recognized value is uppercased.
    Anything else → ``UNKNOWN``.
    """
    if value is None or str(value).strip() == "":
        return None
    normalized = str(value).strip().upper()
    if normalized not in VALID_COMPANY_TYPES:
        return "UNKNOWN"
    return normalized