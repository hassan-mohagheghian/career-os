"""CompanyMatchingService — resolves an extracted company (name + website) to an
existing company or creates a minimal one.

Used by the Job Analysis workflow (LinkCompanyNode) so a processed job is
connected to a company record instead of producing near-duplicate companies:

  1. Resolve any matched alias to its main company (parent_company_id).
  2. Match by exact website domain (and root-domain + loose name fallback).
  3. Match by normalized company name (legal suffixes stripped).
  4. Conservative fuzzy match (difflib ratio >= FUZZY_THRESHOLD).
  5. Otherwise create a minimal company with ``status="created"``.

Matching is deliberately conservative to avoid false-positive links; a wrong
link can be un-related manually from the Companies page later.
"""

from __future__ import annotations

import difflib
import re
from typing import Any

# Legal-form suffixes stripped before name comparison. Keep to unambiguous
# legal forms only — meaningful tokens like "Group"/"Systems" are preserved.
LEGAL_SUFFIXES: tuple[str, ...] = (
    "& co kg",
    "b v",
    "s a",
    "s a r l",
    "s r l",
    "gmbh",
    "ltd",
    "llc",
    "inc",
    "corp",
    "limited",
    "corporation",
    "company",
    "sarl",
    "srl",
    "plc",
    "ag",
    "oy",
    "ab",
    "nv",
    "as",
    "sa",
    "bv",
    "co",
)

FUZZY_THRESHOLD = 0.88
ROOT_DOMAIN_NAME_THRESHOLD = 0.6


def normalize_company_name(name: str) -> str:
    """Lowercase, replace non-alphanumerics with spaces, strip a trailing
    legal-form suffix, and collapse whitespace."""
    raw = re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()
    tokens = raw.split()
    if not tokens:
        return ""
    for suffix in sorted(LEGAL_SUFFIXES, key=lambda s: len(s.split()), reverse=True):
        parts = re.sub(r"[^a-z0-9]+", " ", suffix.lower()).strip().split()
        if len(tokens) >= len(parts) and tokens[-len(parts):] == parts:
            tokens = tokens[:-len(parts)]
            break
    return " ".join(tokens).strip()


def extract_domain(website: str | None) -> str | None:
    """Extract the bare registered hostname (no scheme/path/port/www)."""
    if not website:
        return None
    url = (website or "").strip().lower()
    if "://" in url:
        url = url.split("://", 1)[1]
    url = url.split("/")[0].split("?")[0].split("#")[0]
    url = url.split(":")[0]
    url = url.lstrip("www.")
    return url or None


def _root_domain(domain: str) -> str:
    """Last two labels of a domain (rough eTLD+1 for matching)."""
    parts = domain.split(".")
    if len(parts) <= 2:
        return domain
    return ".".join(parts[-2:])


def _fuzzy_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


class CompanyMatchingService:
    """Find-or-create a company from a job's extracted company data."""

    def __init__(self, repository: Any):
        self._repo = repository

    def find_or_create(self, name: str | None, website: str | None) -> tuple[str, bool]:
        """Return (company_id, created). ``created`` is True when a new company row was inserted.

        An empty/None name raises ValueError (the caller should skip instead of
        creating a company without a name).
        """
        company_name = (name or "").strip()
        if not company_name:
            raise ValueError("company name is required to find or create a company")

        candidates = self._repo.list_for_matching()
        matched = self._match(company_name, website, candidates)
        if matched is not None:
            return self._resolve_main(matched), False

        company = self._repo.insert({
            "name": company_name,
            "website": website or None,
            "domain": extract_domain(website),
            "status": "created",
            "source": "job",
        })
        return company["id"], True

    # ── Matching helpers ─────────────────────────────────────────────

    def _match(self, name: str, website: str | None, candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
        domain = extract_domain(website)
        norm = normalize_company_name(name)

        if domain:
            exact = next(
                (c for c in candidates if (c.get("domain") or extract_domain(c.get("website"))) == domain),
                None,
            )
            if exact is not None:
                return exact

            root = _root_domain(domain)
            for c in candidates:
                c_domain = c.get("domain") or extract_domain(c.get("website"))
                if c_domain and _root_domain(c_domain) == root and len(root) >= 4:
                    if _fuzzy_similarity(norm, normalize_company_name(c.get("name") or "")) >= ROOT_DOMAIN_NAME_THRESHOLD:
                        return c

        if norm:
            exact_name = next(
                (c for c in candidates if normalize_company_name(c.get("name") or "") == norm),
                None,
            )
            if exact_name is not None:
                return exact_name

        best: dict[str, Any] | None = None
        best_score = 0.0
        for c in candidates:
            c_norm = normalize_company_name(c.get("name") or "")
            if not c_norm:
                continue
            score = _fuzzy_similarity(norm, c_norm)
            if score > best_score:
                best, best_score = c, score
        if best is not None and best_score >= FUZZY_THRESHOLD:
            return best
        return None

    def _resolve_main(self, company: dict[str, Any]) -> str:
        """Return the ultimate main company id for a company (walking parents)."""
        company_id = company.get("parent_company_id")
        if company_id:
            return company_id
        return company["id"]
