"""Builders that turn company data (prepared context, rules) into prompt text."""

from __future__ import annotations

from typing import Any

# Company type → rule scope used to select the applicable scoring rules.
# Parity with the legacy company worker scope map.
COMPANY_TYPE_SCOPE_MAP: dict[str, str] = {
    "PRODUCT_COMPANY": "COMPANY_PRODUCT",
    "RECRUITING_AGENCY": "COMPANY_RECRUITING",
    "STAFFING_COMPANY": "COMPANY_RECRUITING",
    "CONSULTING_COMPANY": "COMPANY_PRODUCT",
    "UNKNOWN": "COMPANY_PRODUCT",
}

DEFAULT_COMPANY_SCOPE = "COMPANY_PRODUCT"


def scope_for_company_type(company_type: Any) -> str:
    """Resolve the scoring-rule scope for a company type value."""
    if not isinstance(company_type, str):
        return DEFAULT_COMPANY_SCOPE
    return COMPANY_TYPE_SCOPE_MAP.get(company_type.upper(), DEFAULT_COMPANY_SCOPE)


def build_scoring_rules_text(rules: list[dict[str, Any]]) -> str:
    """Format enabled scoring rules (SHARED + COMPANY scopes) for the prompt."""
    if not rules:
        return "(no scoring rules set)"
    lines = []
    for r in rules:
        weight = r["priority"]
        lines.append(f"  #{r.get('priority')}  {r.get('key')} (weight:{weight}): {r.get('value')}")
    return "\n".join(lines)


def build_company_type_line(company_type: Any) -> str:
    if not isinstance(company_type, str) or not company_type.strip():
        return "UNKNOWN"
    return company_type.strip().upper()
