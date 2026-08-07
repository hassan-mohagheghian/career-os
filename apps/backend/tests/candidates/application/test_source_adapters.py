"""Tests for candidate source adapters (resume / linkedin / stubs)."""

from candidates.application.adapters.base import SourceContent
from candidates.application.adapters import (
    LinkedInAdapter,
    ResumeAdapter,
    GitHubAdapter,
    PortfolioAdapter,
    build_adapter,
)


class FakeSourceRepository:
    """Minimal ICandidateSourceRepository fake exposing get_latest_by_type."""

    def __init__(self, rows=None):
        self.rows = list(rows or [])

    def get_latest_by_type(self, profile_id, source_type):
        matched = [r for r in self.rows if r.get("source_type") == source_type]
        if not matched:
            return None
        return max(matched, key=lambda r: r.get("version") or 0)


def _row(source_type, version, raw_text):
    return {"source_type": source_type, "version": version, "raw_text": raw_text}


class TestSourceContent:
    def test_fields(self):
        content = SourceContent("resume", "hello", 3)
        assert content.source_type == "resume"
        assert content.raw_text == "hello"
        assert content.version == 3


class TestResumeAdapter:
    def test_fetch_returns_latest_resume(self):
        repo = FakeSourceRepository(
            [
                _row("resume", 1, "v1"),
                _row("resume", 2, "v2"),
                _row("linkedin", 5, "li"),
            ]
        )
        adapter = ResumeAdapter(repo, profile_id="p1")
        content = adapter.fetch()
        assert content == SourceContent("resume", "v2", 2)

    def test_fetch_none_when_no_resume(self):
        adapter = ResumeAdapter(FakeSourceRepository([_row("linkedin", 1, "li")]), profile_id="p1")
        assert adapter.fetch() is None

    def test_fetch_none_when_empty_rows(self):
        adapter = ResumeAdapter(FakeSourceRepository(), profile_id="p1")
        assert adapter.fetch() is None

    def test_fetch_none_without_profile_id(self):
        adapter = ResumeAdapter(FakeSourceRepository([_row("resume", 1, "r")]))
        assert adapter.fetch() is None

    def test_source_type_attribute(self):
        assert ResumeAdapter.source_type == "resume"


class TestLinkedInAdapter:
    def test_fetch_returns_latest_linkedin(self):
        repo = FakeSourceRepository(
            [
                _row("linkedin", 1, "li1"),
                _row("linkedin", 3, "li3"),
                _row("resume", 2, "orig"),
            ]
        )
        adapter = LinkedInAdapter(repo, profile_id="p1")
        content = adapter.fetch()
        assert content == SourceContent("linkedin", "li3", 3)

    def test_fetch_none_when_no_linkedin(self):
        adapter = LinkedInAdapter(FakeSourceRepository([_row("resume", 1, "r")]), profile_id="p1")
        assert adapter.fetch() is None

    def test_source_type_attribute(self):
        assert LinkedInAdapter.source_type == "linkedin"


class TestStubAdapters:
    def test_github_stub_returns_none(self):
        assert GitHubAdapter().fetch() is None
        assert GitHubAdapter.source_type == "github"

    def test_portfolio_stub_returns_none(self):
        assert PortfolioAdapter().fetch() is None
        assert PortfolioAdapter.source_type == "portfolio"


class TestBuildAdapter:
    def test_resume_adapter_built(self):
        adapter = build_adapter("resume", FakeSourceRepository([_row("resume", 1, "r")]), "p1")
        assert isinstance(adapter, ResumeAdapter)

    def test_linkedin_adapter_built(self):
        adapter = build_adapter("linkedin", FakeSourceRepository([_row("linkedin", 1, "l")]), "p1")
        assert isinstance(adapter, LinkedInAdapter)

    def test_github_stub_built_without_repo(self):
        assert isinstance(build_adapter("github"), GitHubAdapter)

    def test_portfolio_stub_built_without_repo(self):
        assert isinstance(build_adapter("portfolio"), PortfolioAdapter)

    def test_unknown_source_returns_none(self):
        assert build_adapter("unknown", FakeSourceRepository(), "p1") is None
