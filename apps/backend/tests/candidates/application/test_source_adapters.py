"""Tests for candidate source adapters (resume / linkedin / stubs)."""

from candidates.application.adapters.base import SourceContent
from candidates.application.adapters import (
    LinkedInAdapter,
    ResumeAdapter,
    GitHubAdapter,
    PortfolioAdapter,
    build_adapter,
)


class FakeResumeRepository:
    """Minimal IResumeRepository fake exposing get_all() with versioned rows."""

    def __init__(self, rows=None):
        self.rows = list(rows or [])

    def get_all(self):
        return list(self.rows)


def _row(prefix, version, raw_text):
    return {"id": f"{prefix}_{version}", "version": version, "raw_text": raw_text}


class TestSourceContent:
    def test_fields(self):
        content = SourceContent("resume", "hello", 3)
        assert content.source_type == "resume"
        assert content.raw_text == "hello"
        assert content.version == 3


class TestResumeAdapter:
    def test_fetch_returns_latest_original(self):
        repo = FakeResumeRepository(
            [
                _row("original", 1, "v1"),
                _row("original", 2, "v2"),
                _row("linkedin", 5, "li"),
                _row("cover", 1, "cover"),
            ]
        )
        adapter = ResumeAdapter(repo)
        content = adapter.fetch()
        assert content == SourceContent("resume", "v2", 2)

    def test_fetch_none_when_no_original(self):
        adapter = ResumeAdapter(FakeResumeRepository([_row("linkedin", 1, "li")]))
        assert adapter.fetch() is None

    def test_fetch_none_when_empty_rows(self):
        adapter = ResumeAdapter(FakeResumeRepository())
        assert adapter.fetch() is None

    def test_source_type_attribute(self):
        assert ResumeAdapter.source_type == "resume"


class TestLinkedInAdapter:
    def test_fetch_returns_latest_linkedin(self):
        repo = FakeResumeRepository(
            [
                _row("linkedin", 1, "li1"),
                _row("linkedin", 3, "li3"),
                _row("original", 2, "orig"),
            ]
        )
        adapter = LinkedInAdapter(repo)
        content = adapter.fetch()
        assert content == SourceContent("linkedin", "li3", 3)

    def test_fetch_none_when_no_linkedin(self):
        adapter = LinkedInAdapter(FakeResumeRepository([_row("original", 1, "r")]))
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
        adapter = build_adapter("resume", FakeResumeRepository([_row("original", 1, "r")]))
        assert isinstance(adapter, ResumeAdapter)

    def test_linkedin_adapter_built(self):
        adapter = build_adapter("linkedin", FakeResumeRepository([_row("linkedin", 1, "l")]))
        assert isinstance(adapter, LinkedInAdapter)

    def test_github_stub_built_without_repo(self):
        assert isinstance(build_adapter("github"), GitHubAdapter)

    def test_portfolio_stub_built_without_repo(self):
        assert isinstance(build_adapter("portfolio"), PortfolioAdapter)

    def test_unknown_source_returns_none(self):
        assert build_adapter("unknown", FakeResumeRepository()) is None
