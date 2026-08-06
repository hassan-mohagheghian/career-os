"""Tests for CompanyMatchingService — find-or-create from extracted job data."""

import pytest

from companies.application.services.company_matching_service import (
    CompanyMatchingService,
    extract_domain,
    normalize_company_name,
)


class FakeCompanyRepo:
    def __init__(self, companies=None):
        self.companies = companies or []
        self._next = 0
        self.inserted = []

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

    def insert(self, data):
        self._next += 1
        row = {"id": f"new-{self._next}", **data}
        self.companies.append(row)
        self.inserted.append(row)
        return row


def _company(**kw) -> dict:
    data = {
        "id": kw.pop("id", "c-1"),
        "name": kw.pop("name", "Acme"),
        "website": kw.pop("website", "https://acme.example"),
        "domain": kw.pop("domain", None),
        "parent_company_id": kw.pop("parent_company_id", None),
    }
    data.update(kw)
    return data


class TestNormalizeCompanyName:
    def test_lowercase_and_collapse(self):
        assert normalize_company_name("  Acme   GmbH  ") == "acme"

    def test_strips_legal_suffixes(self):
        assert normalize_company_name("Acme Inc") == "acme"
        assert normalize_company_name("Acme Limited") == "acme"
        assert normalize_company_name("Acme LLC") == "acme"
        assert normalize_company_name("Acme AG") == "acme"
        assert normalize_company_name("Acme & Co KG") == "acme"
        assert normalize_company_name("Acme GmbH") == "acme"

    def test_preserves_meaningful_tokens(self):
        assert normalize_company_name("Acme Group") == "acme group"
        assert normalize_company_name("Acme Systems") == "acme systems"

    def test_empty(self):
        assert normalize_company_name("") == ""
        assert normalize_company_name(None) == ""


class TestExtractDomain:
    def test_scheme_path_port_www(self):
        assert extract_domain("https://www.acme.example/careers?x=1#top") == "acme.example"
        assert extract_domain("http://acme.example:8080/") == "acme.example"
        assert extract_domain("acme.example") == "acme.example"

    def test_none(self):
        assert extract_domain(None) is None
        assert extract_domain("") is None


class TestFindOrCreate:
    def test_domain_match_returns_existing(self):
        repo = FakeCompanyRepo([_company(name="Acme Inc", website="https://acme.example")])
        company_id, created = CompanyMatchingService(repo).find_or_create("Acme Incorporated", "https://acme.example")
        assert company_id == "c-1"
        assert created is False
        assert repo.inserted == []

    def test_normalized_name_exact_match(self):
        repo = FakeCompanyRepo([_company(name="Acme GmbH")])
        company_id, created = CompanyMatchingService(repo).find_or_create("Acme Inc", None)
        assert company_id == "c-1"
        assert created is False

    def test_fuzzy_match_high_similarity(self):
        repo = FakeCompanyRepo([_company(name="Delivery Hero")])
        company_id, created = CompanyMatchingService(repo).find_or_create("Delivery Hero SE", None)
        assert company_id == "c-1"
        assert created is False

    def test_distinct_name_does_not_fuzzy_match(self):
        repo = FakeCompanyRepo([_company(name="Acme GmbH")])
        company_id, created = CompanyMatchingService(repo).find_or_create("ACME Logistics GmbH", None)
        assert created is True
        assert company_id == "new-1"

    def test_creates_when_no_match(self):
        repo = FakeCompanyRepo([])
        company_id, created = CompanyMatchingService(repo).find_or_create("Brand New Co", "https://brand-new.example")
        assert created is True
        assert company_id == "new-1"
        assert repo.inserted[0]["name"] == "Brand New Co"
        assert repo.inserted[0]["domain"] == "brand-new.example"
        assert repo.inserted[0]["status"] == "created"
        assert repo.inserted[0]["source"] == "job"

    def test_alias_matches_resolve_to_main(self):
        repo = FakeCompanyRepo([
            _company(id="main-1", name="Acme GmbH"),
            _company(id="alias-1", name="Acme Inc", parent_company_id="main-1"),
        ])
        company_id, created = CompanyMatchingService(repo).find_or_create("Acme Inc", "https://acme.example")
        assert company_id == "main-1"
        assert created is False

    def test_root_domain_fallback_with_name_confirmation(self):
        repo = FakeCompanyRepo([_company(name="Acme", website="https://www.acme.example")])
        company_id, created = CompanyMatchingService(repo).find_or_create(
            "Acme Company", "https://careers.acme.example"
        )
        assert company_id == "c-1"
        assert created is False

    def test_requires_name(self):
        repo = FakeCompanyRepo([])
        with pytest.raises(ValueError):
            CompanyMatchingService(repo).find_or_create("", "https://x.example")
