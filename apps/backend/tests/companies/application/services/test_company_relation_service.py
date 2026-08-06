"""Tests for CompanyRelationService — main/alias relations."""

import pytest

from companies.application.services.company_relation_service import CompanyRelationService
from shared.application.exceptions import ConflictError, NotFoundError


class FakeCompanyRepo:
    def __init__(self, companies=None):
        self.companies = companies or []
        self.updated = []

    def get_by_id(self, company_id):
        return next((c for c in self.companies if c["id"] == company_id), None)

    def list_for_matching(self):
        return [
            {
                "id": c["id"],
                "name": c.get("name"),
                "website": c.get("website"),
                "domain": c.get("domain"),
                "parent_company_id": c.get("parent_company_id"),
            }
            for c in self.companies
        ]

    def update_fields(self, company_id, **fields):
        self.updated.append((company_id, fields))
        for c in self.companies:
            if c["id"] == company_id:
                c.update(fields)
        return True


def _company(cid: str, parent=None) -> dict:
    return {"id": cid, "name": cid, "website": None, "domain": None, "parent_company_id": parent}


class TestRelate:
    def test_relate_sets_parent_and_returns_subtree(self):
        repo = FakeCompanyRepo([_company("alias"), _company("main")])
        result = CompanyRelationService(repo).relate("alias", "main")
        assert repo.updated == [("alias", {"parent_company_id": "main"})]
        assert result == {"main_company_id": "main", "affected_company_ids": ["alias"]}

    def test_relate_includes_descendant_aliases_in_subtree(self):
        repo = FakeCompanyRepo([_company("middle"), _company("leaf", parent="middle"), _company("main")])
        result = CompanyRelationService(repo).relate("middle", "main")
        assert result["main_company_id"] == "main"
        assert set(result["affected_company_ids"]) == {"middle", "leaf"}

    def test_self_link_rejected(self):
        repo = FakeCompanyRepo([_company("a")])
        with pytest.raises(ConflictError):
            CompanyRelationService(repo).relate("a", "a")

    def test_missing_company_rejected(self):
        repo = FakeCompanyRepo([_company("main")])
        with pytest.raises(NotFoundError):
            CompanyRelationService(repo).relate("ghost", "main")
        with pytest.raises(NotFoundError):
            CompanyRelationService(repo).relate("main", "ghost")

    def test_main_that_is_itself_alias_rejected(self):
        # a is an alias of top, so it cannot serve as another company's main
        repo = FakeCompanyRepo([_company("top"), _company("a", parent="top"), _company("b")])
        with pytest.raises(ConflictError):
            CompanyRelationService(repo).relate("b", "a")

    def test_cycle_rejected(self):
        # a is already an alias of b; relating b to a would cycle
        repo = FakeCompanyRepo([_company("a", parent="b"), _company("b")])
        with pytest.raises(ConflictError):
            CompanyRelationService(repo).relate("b", "a")


class TestUnrelate:
    def test_unrelate_clears_parent(self):
        repo = FakeCompanyRepo([_company("alias", parent="main")])
        result = CompanyRelationService(repo).unrelate("alias")
        assert repo.updated == [("alias", {"parent_company_id": None})]
        assert result == {"main_company_id": "alias", "affected_company_ids": ["alias"]}

    def test_unrelate_missing_company_rejected(self):
        repo = FakeCompanyRepo([])
        with pytest.raises(NotFoundError):
            CompanyRelationService(repo).unrelate("ghost")
