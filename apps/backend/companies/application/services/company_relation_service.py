"""CompanyRelationService — relate a near-duplicate company as an alias of a
main company, or un-relate it.

The main company is the single reference for display and further processing.
Relating a company re-points the jobs of the company (and of its own aliases,
transitively) onto the main company. Only the companies repository is used
here; the jobs re-pointing is orchestrated by the presentation layer to keep
context boundaries intact.
"""

from __future__ import annotations

from typing import Any

from shared.application.exceptions import ConflictError, NotFoundError


class CompanyRelationService:
    """Main/alias relations for companies."""

    def __init__(self, company_repo: Any):
        self._repo = company_repo

    def relate(self, company_id: str, main_company_id: str) -> dict[str, Any]:
        """Set ``company_id`` as an alias of ``main_company_id``.

        Returns ``{"main_company_id": ..., "affected_company_ids": [...]}``
        where affected ids include the related company and every company that
        (transitively) already pointed at it as an alias.
        """
        company = self._repo.get_by_id(company_id)
        if not company:
            raise NotFoundError(f"Company {company_id} not found")
        main = self._repo.get_by_id(main_company_id)
        if not main:
            raise NotFoundError(f"Company {main_company_id} not found")

        if company_id == main_company_id:
            raise ConflictError("A company cannot be related to itself")

        if main.get("parent_company_id"):
            raise ConflictError(
                "The target company is itself an alias of another company; "
                "relate to its main company instead"
            )

        subtree = self._collect_subtree(company_id)
        if main_company_id in subtree:
            raise ConflictError("A company cannot be related to one of its own aliases (cycle)")

        self._repo.update_fields(company_id, parent_company_id=main_company_id)
        affected = [company_id] + [c["id"] for c in subtree]
        return {"main_company_id": main_company_id, "affected_company_ids": affected}

    def unrelate(self, company_id: str) -> dict[str, Any]:
        """Clear the alias relation on ``company_id`` (it becomes a standalone company)."""
        company = self._repo.get_by_id(company_id)
        if not company:
            raise NotFoundError(f"Company {company_id} not found")
        self._repo.update_fields(company_id, parent_company_id=None)
        return {"main_company_id": company_id, "affected_company_ids": [company_id]}

    def _collect_subtree(self, company_id: str) -> list[dict[str, Any]]:
        """All companies (transitively) related to ``company_id`` as an alias."""
        by_parent: dict[str, list[dict[str, Any]]] = {}
        for c in self._repo.list_for_matching():
            parent = c.get("parent_company_id")
            if parent:
                by_parent.setdefault(parent, []).append(c)

        found: list[dict[str, Any]] = []
        stack = [company_id]
        while stack:
            parent = stack.pop()
            for child in by_parent.get(parent, []):
                found.append(child)
                stack.append(child["id"])
        return found
