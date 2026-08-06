"""Tests for the Company Context Preparation workflow.

Covers:
- CompanyProcessingState creation and transitions
- Workflow nodes (LoadCompany, CollectSources, FetchSources, ExtractContent,
  BuildContext, ValidateContext, PersistContext)
- The CompanyContextPreparationGraph end-to-end:
  - successful workflow execution
  - failed source handling (one failed source must not fail the workflow)
  - empty context handling
  - invalid context handling
- progress_ops target_type/target_id dispatch for company states
"""

import json

import pytest

from processing.application.services.company_context_builder import CompanyContextBuilderService
from processing.application.services.company_context_validator import CompanyContextValidatorService
from processing.application.workflows.company_context_preparation import CompanyContextPreparationGraph
from processing.application.workflows.company_context_preparation.nodes import (
    BuildContextNode,
    CollectSourcesNode,
    ContextReadyNode,
    ExecutionFailedNode,
    ExtractContentNode,
    FetchSourcesNode,
    LoadCompanyNode,
    PersistContextNode,
    ValidateContextNode,
)
from processing.application.workflows import progress_ops
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.company_data import CompanyData
from processing.domain.workflow.company_processing_state import CompanyProcessingState
from processing.domain.workflow.extracted_content import ExtractedContent
from processing.domain.workflow.fetched_content import FetchedContent
from processing.domain.workflow.source import JobSource, SourceType


# --------------------------------------------------------------------------- #
# Fakes
# --------------------------------------------------------------------------- #


def _company_dict(**overrides) -> dict:
    data = {
        "id": "company-uuid-1",
        "name": "Acme GmbH",
        "website": "https://acme.example",
        "notes": json.dumps(
            [
                {"type": "url", "content": "https://acme.example/about"},
                {"type": "text", "content": "Company notes: builds developer tools"},
            ]
        ),
        "links": json.dumps([{"url": "https://acme.example/careers"}]),
    }
    data.update(overrides)
    return data


class FakeCompanyService:
    def __init__(self, company=None, error=None, persist_error=None):
        self._company = company
        self._error = error
        self._persist_error = persist_error
        self.persisted = None

    def get_company(self, company_id):
        if self._error is not None:
            raise self._error
        return self._company

    def persist_prepared_context(self, company_id, combined_text):
        if self._persist_error is not None:
            raise self._persist_error
        self.persisted = (company_id, combined_text)


class FakeFetcher:
    def __init__(self, outcomes=None, error=None):
        self._outcomes = outcomes or {}
        self._error = error

    def fetch(self, source: JobSource) -> FetchedContent:
        if self._error is not None:
            raise self._error
        url = source.url or ""
        outcome = self._outcomes.get(url)
        if outcome is None:
            return FetchedContent(source=source, url=url, success=False, error="no outcome")
        success, content, error = outcome
        return FetchedContent(source=source, url=url, success=success, content=content, error=error)


class FakeExtractor:
    def __init__(self, texts=None, error=None):
        self._texts = texts or {}
        self._error = error

    def extract(self, content: FetchedContent) -> ExtractedContent:
        if self._error is not None:
            raise self._error
        text = self._texts.get(content.url, f"Content for {content.url}")
        return ExtractedContent(source=content.source, url=content.url, clean_text=text, length=len(text))


class RecordingEventPublisher:
    def __init__(self):
        self.events = []

    def publish(self, event_name, execution_id, job_id, status, **kwargs):
        self.events.append((event_name, execution_id, job_id, status, kwargs))


def _build_graph(company=None, fetcher=None, extractor=None, company_error=None, publisher=None, persist_error=None):
    return CompanyContextPreparationGraph(
        company_service=FakeCompanyService(company, company_error, persist_error),
        fetcher=fetcher or FakeFetcher(),
        extractor=extractor or FakeExtractor(),
        event_publisher=publisher or RecordingEventPublisher(),
    )


def _initial_state(company_id="company-uuid-1", execution_id="exec-1") -> CompanyProcessingState:
    return CompanyProcessingState(execution_id=execution_id, company_id=company_id)


def _successful_outcomes():
    return {
        "https://acme.example": (True, "<p>Acme homepage</p>", None),
        "https://acme.example/about": (True, "<p>About page</p>", None),
        "https://acme.example/careers": (True, "<p>Careers page</p>", None),
    }


# --------------------------------------------------------------------------- #
# Domain: state creation / transitions
# --------------------------------------------------------------------------- #


class TestCompanyProcessingState:
    def test_defaults(self):
        state = _initial_state()
        assert state.execution_id == "exec-1"
        assert state.company_id == "company-uuid-1"
        assert state.company is None
        assert state.sources == []
        assert state.fetched_contents == []
        assert state.extracted_contents == []
        assert state.notes == []
        assert state.processing_context is None
        assert state.validation_result is None
        assert state.errors == []
        assert state.status == ExecutionStatus.CREATED

    def test_terminal_transitions(self):
        state = _initial_state()
        state = ContextReadyNode()(state)
        assert state.status == ExecutionStatus.COMPLETED

        state = _initial_state()
        state = ExecutionFailedNode()(state)
        assert state.status == ExecutionStatus.FAILED


# --------------------------------------------------------------------------- #
# Nodes
# --------------------------------------------------------------------------- #


class TestLoadCompanyNode:
    def test_loads_company_and_populates_state(self):
        company = _company_dict()
        node = LoadCompanyNode(FakeCompanyService(company), RecordingEventPublisher())
        state = node(_initial_state())

        assert state.company is not None
        assert state.company.id == "company-uuid-1"
        assert state.company.name == "Acme GmbH"
        assert state.errors == []

    def test_missing_company_records_error(self):
        node = LoadCompanyNode(FakeCompanyService(None))
        state = node(_initial_state())
        assert state.company is None
        assert any("not found" in e for e in state.errors)

    def test_service_error_records_error(self):
        node = LoadCompanyNode(FakeCompanyService(None, error=RuntimeError("db down")))
        state = node(_initial_state())
        assert state.company is None
        assert any("db down" in e for e in state.errors)

    def test_emits_loading_company_event(self):
        publisher = RecordingEventPublisher()
        node = LoadCompanyNode(FakeCompanyService(_company_dict()), publisher)
        node(_initial_state())
        assert publisher.events[0][0] == "workflow.step.started"


class TestCollectSourcesNode:
    def test_collects_primary_url_notes_and_links(self):
        company = _company_dict()
        state = _initial_state()
        state.company = CompanyData.from_company_dict(company)

        state = CollectSourcesNode()(state)

        urls = [s.url for s in state.sources]
        assert urls == [
            "https://acme.example",
            "https://acme.example/about",
            "https://acme.example/careers",
        ]
        assert state.sources[0].type == SourceType.PRIMARY_URL
        assert state.notes == ["Company notes: builds developer tools"]

    def test_deduplicates_urls(self):
        company = _company_dict(
            notes=json.dumps(
                [
                    {"type": "url", "content": "https://acme.example/about"},
                    {"type": "url", "content": "https://acme.example/about"},
                ]
            )
        )
        state = _initial_state()
        state.company = CompanyData.from_company_dict(company)

        state = CollectSourcesNode()(state)

        urls = [s.url for s in state.sources]
        assert len(urls) == len(set(urls))

    def test_no_company_produces_no_sources(self):
        state = CollectSourcesNode()(_initial_state())
        assert state.sources == []
        assert any("No company" in e for e in state.errors)


class TestFetchSourcesNode:
    def test_fetches_all_sources(self):
        state = _initial_state()
        state.sources = [
            JobSource(url="https://acme.example", type=SourceType.PRIMARY_URL),
            JobSource(url="https://acme.example/about", type=SourceType.ADDITIONAL_URL),
        ]
        node = FetchSourcesNode(FakeFetcher(_successful_outcomes()))
        state = node(state)

        assert len(state.fetched_contents) == 2
        assert all(f.success for f in state.fetched_contents)
        assert state.errors == []

    def test_failed_source_does_not_fail_workflow(self):
        state = _initial_state()
        state.sources = [
            JobSource(url="https://acme.example", type=SourceType.PRIMARY_URL),
            JobSource(url="https://broken.example", type=SourceType.ADDITIONAL_URL),
        ]
        node = FetchSourcesNode(FakeFetcher({}))
        state = node(state)

        assert len(state.fetched_contents) == 2
        assert any(not f.success for f in state.fetched_contents)
        assert any("Fetch failed" in e for e in state.errors)
        assert state.status == ExecutionStatus.CREATED


class TestExtractContentNode:
    def test_extracts_all_fetched_content(self):
        state = _initial_state()
        state.fetched_contents = [
            FetchedContent(
                source=JobSource(url="https://acme.example", type=SourceType.PRIMARY_URL),
                url="https://acme.example",
                success=True,
                content="<p>Home</p>",
            )
        ]
        node = ExtractContentNode(FakeExtractor())
        state = node(state)

        assert len(state.extracted_contents) == 1
        assert state.extracted_contents[0].clean_text.startswith("Content for")


class TestBuildContextNode:
    def test_builds_combined_text(self):
        state = _initial_state()
        state.company = CompanyData.from_company_dict(_company_dict())
        state.notes = ["Note one"]
        state.extracted_contents = [
            ExtractedContent(
                source=JobSource(url="https://acme.example", type=SourceType.PRIMARY_URL),
                url="https://acme.example",
                clean_text="Extracted text here",
                length=18,
            )
        ]
        node = BuildContextNode(CompanyContextBuilderService())
        state = node(state)

        assert state.processing_context is not None
        assert "[NOTE] Note one" in state.processing_context.combined_text
        assert "Extracted text here" in state.processing_context.combined_text


class TestValidateContextNode:
    def test_valid_context(self):
        from processing.domain.workflow.company_processing_context import CompanyProcessingContext

        state = _initial_state()
        state.sources = [JobSource(url="https://acme.example", type=SourceType.PRIMARY_URL)]
        state.processing_context = CompanyProcessingContext(
            company_id=state.company_id,
            sources=state.sources,
            extracted_contents=[
                ExtractedContent(
                    source=state.sources[0], url="https://acme.example", clean_text="Some text", length=9
                )
            ],
        )
        node = ValidateContextNode(CompanyContextValidatorService())
        state = node(state)

        assert state.validation_result is not None
        assert state.validation_result.valid is True

    def test_invalid_context(self):
        node = ValidateContextNode(CompanyContextValidatorService())
        state = node(_initial_state())

        assert state.validation_result is not None
        assert state.validation_result.valid is False


class TestPersistContextNode:
    def test_persists_combined_text(self):
        service = FakeCompanyService(_company_dict())
        node = PersistContextNode(service)
        state = _initial_state()
        state.processing_context = CompanyProcessingContextPlaceholder("combined text body")

        node(state)

        assert service.persisted == ("company-uuid-1", "combined text body")

    def test_persist_error_marks_failed(self):
        service = FakeCompanyService(_company_dict(), persist_error=RuntimeError("db down"))
        node = PersistContextNode(service)
        state = _initial_state()
        state.processing_context = CompanyProcessingContextPlaceholder("combined text body")

        node(state)

        assert state.status == ExecutionStatus.FAILED
        assert any("persist" in e for e in state.errors)


class CompanyProcessingContextPlaceholder:
    """Minimal stand-in for CompanyProcessingContext used by PersistContextNode."""

    def __init__(self, combined_text: str):
        self.combined_text = combined_text


# --------------------------------------------------------------------------- #
# Graph
# --------------------------------------------------------------------------- #


class TestCompanyContextPreparationGraph:
    def test_successful_execution(self):
        graph = _build_graph(company=_company_dict())
        state = graph.invoke(_initial_state())

        assert state.status == ExecutionStatus.COMPLETED
        assert state.processing_context is not None
        assert state.processing_context.combined_text
        assert state.workflow_progress is not None
        prep_ids = [s.id for s in state.workflow_progress.steps]
        assert all(
            s.status.value in ("completed", "pending")
            for s in state.workflow_progress.steps
        )
        assert prep_ids[0] == "load_company"

    def test_missing_company_fails(self):
        graph = _build_graph(company=None)
        state = graph.invoke(_initial_state())

        assert state.status == ExecutionStatus.FAILED
        assert any("not found" in e for e in state.errors)

    def test_invalid_context_fails(self):
        company = _company_dict(
            notes=json.dumps([{"type": "url", "content": "https://acme.example/about"}]),
            links="[]",
        )
        graph = _build_graph(
            company=company,
            fetcher=FakeFetcher({}),
            extractor=FakeExtractor({}),
        )
        state = graph.invoke(_initial_state())

        assert state.status == ExecutionStatus.FAILED
        assert state.validation_result is not None
        assert state.validation_result.valid is False

    def test_workflow_progress_tree_uses_company_steps(self):
        graph = _build_graph(company=_company_dict())
        state = graph.invoke(_initial_state())

        assert state.workflow_progress is not None
        ids = [s.id for s in state.workflow_progress.steps]
        assert "load_company" in ids
        assert "persist_context" in ids


# --------------------------------------------------------------------------- #
# progress_ops dispatch
# --------------------------------------------------------------------------- #


class TestProgressOpsDispatch:
    def test_initial_progress_dispatches_to_company_mapper(self):
        progress = progress_ops.build_initial_progress("exec-1", "company")
        assert progress.id == "company_processing"
        ids = [s.id for s in progress.steps]
        assert "load_company" in ids

    def test_initial_progress_defaults_to_job_mapper(self):
        progress = progress_ops.build_initial_progress("exec-1")
        assert progress.id != "company_processing"

    def test_step_events_carry_company_target(self):
        publisher = RecordingEventPublisher()
        state = _initial_state()
        progress_ops.start_step(publisher, state, "load_company")

        event = publisher.events[0]
        kwargs = event[4]
        assert kwargs.get("target_type") == "company"
        assert kwargs.get("target_id") == "company-uuid-1"

    def test_step_events_carry_job_target(self):
        from processing.domain.workflow.job_processing_state import JobProcessingState

        publisher = RecordingEventPublisher()
        state = JobProcessingState(execution_id="exec-1", job_id="job-1")
        progress_ops.start_step(publisher, state, "load_job")

        event = publisher.events[0]
        kwargs = event[4]
        assert kwargs.get("target_type") == "job"
        assert kwargs.get("target_id") == "job-1"
