"""Tests for the Job Context Preparation workflow.

Covers:
- JobProcessingState creation and transitions
- Workflow nodes (LoadJob, CollectSources, FetchSources, ExtractContent,
  BuildContext, ValidateContext)
- The JobContextPreparationGraph end-to-end:
  - successful workflow execution
  - failed source handling (one failed source must not fail the workflow)
  - empty context handling
  - invalid context handling
- Infrastructure adapters (HTTPX fetch, Playwright degradation, composite
  fetcher/extractor fallbacks)
- ProcessingExecutionRunner wiring for JOB_PROCESSING
"""

import json
import uuid

from datetime import datetime, UTC
from unittest.mock import patch

import pytest

from processing.application.services.job_context_builder import JobContextBuilderService
from processing.application.services.job_context_validator import JobContextValidatorService
from processing.application.workflows.job_context_preparation import JobContextPreparationGraph
from processing.application.workflows.job_context_preparation.nodes import (
    BuildContextNode,
    CollectSourcesNode,
    ContextReadyNode,
    ExecutionFailedNode,
    ExtractContentNode,
    FetchSourcesNode,
    LoadJobNode,
    ValidateContextNode,
)
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.extracted_content import ExtractedContent
from processing.domain.workflow.fetched_content import FetchedContent
from processing.domain.workflow.job_data import JobData
from processing.domain.workflow.job_processing_context import JobProcessingContext
from processing.domain.workflow.job_processing_state import JobProcessingState
from processing.domain.workflow.source import JobSource, SourceType
from processing.infrastructure.content.fetchers import (
    CompositeContentFetcher,
    HTTPXContentFetcher,
    PlaywrightContentFetcher,
)
from processing.infrastructure.content.extractors import (
    BeautifulSoupContentExtractor,
    CompositeContentExtractor,
    TrafilaturaContentExtractor,
)
from processing.infrastructure.runner.execution_runner import ProcessingExecutionRunner
from processing.domain.entities.processing_execution import ProcessingExecution
from processing.domain.enums import ExecutionType


# --------------------------------------------------------------------------- #
# Fakes
# --------------------------------------------------------------------------- #


def _job_dict(**overrides) -> dict:
    data = {
        "id": "job-uuid-1",
        "url": "https://example.com/job",
        "company": "Acme Inc",
        "role": "Senior Backend Engineer",
        "title": "Senior Backend Engineer",
        "notes": json.dumps(
            [
                {"type": "url", "content": "https://example.com/more"},
                {"type": "text", "content": "Must know Python and Postgres"},
            ]
        ),
        "links": json.dumps([{"url": "https://example.com/apply"}]),
    }
    data.update(overrides)
    return data


class FakeJobService:
    def __init__(self, job=None, error=None):
        self._job = job
        self._error = error

    def get_job(self, job_id):
        if self._error is not None:
            raise self._error
        return self._job


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
        return FetchedContent(
            source=source,
            url=url,
            success=success,
            content=content,
            error=error,
            metadata={"degraded": True} if not success and "not installed" in (error or "") else {},
        )


class FakeExtractor:
    def __init__(self, texts=None, error=None):
        self._texts = texts or {}
        self._error = error

    def extract(self, content: FetchedContent) -> ExtractedContent:
        if self._error is not None:
            raise self._error
        text = self._texts.get(content.url, f"Content for {content.url}")
        return ExtractedContent(
            source=content.source,
            url=content.url,
            clean_text=text,
            length=len(text),
        )


class RecordingEventPublisher:
    def __init__(self):
        self.events = []

    def publish(self, event_name, execution_id, job_id, status, **kwargs):
        self.events.append((event_name, execution_id, job_id, status, kwargs))


def _build_graph(job=None, fetcher=None, extractor=None, job_error=None, publisher=None):
    return JobContextPreparationGraph(
        job_service=FakeJobService(job, job_error),
        fetcher=fetcher or FakeFetcher(),
        extractor=extractor or FakeExtractor(),
        event_publisher=publisher or RecordingEventPublisher(),
    )


def _initial_state(job_id="job-uuid-1", execution_id="exec-1") -> JobProcessingState:
    return JobProcessingState(execution_id=execution_id, job_id=job_id)


def _successful_outcomes():
    return {
        "https://example.com/job": (True, "<p>Job description here</p>", None),
        "https://example.com/more": (True, "<p>Additional info</p>", None),
        "https://example.com/apply": (True, "<p>How to apply</p>", None),
    }


# --------------------------------------------------------------------------- #
# Domain: state creation / transitions
# --------------------------------------------------------------------------- #


class TestJobProcessingState:
    def test_defaults(self):
        state = _initial_state()
        assert state.execution_id == "exec-1"
        assert state.job_id == "job-uuid-1"
        assert state.job is None
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


class TestLoadJobNode:
    def test_loads_job_and_populates_state(self):
        job = _job_dict()
        node = LoadJobNode(FakeJobService(job), RecordingEventPublisher())
        state = node(_initial_state())

        assert state.job is not None
        assert state.job.id == "job-uuid-1"
        assert state.job.url == "https://example.com/job"
        assert state.errors == []

    def test_missing_job_records_error(self):
        node = LoadJobNode(FakeJobService(None))
        state = node(_initial_state())
        assert state.job is None
        assert any("not found" in e for e in state.errors)

    def test_service_error_records_error(self):
        node = LoadJobNode(FakeJobService(None, error=RuntimeError("db down")))
        state = node(_initial_state())
        assert state.job is None
        assert any("db down" in e for e in state.errors)

    def test_emits_loading_job_event(self):
        publisher = RecordingEventPublisher()
        node = LoadJobNode(FakeJobService(_job_dict()), publisher)
        node(_initial_state())
        assert publisher.events[0][0] == "workflow.step.started"

    def test_job_without_notes_or_links_loads(self):
        job = _job_dict(notes=None, links=None)
        node = LoadJobNode(FakeJobService(job), RecordingEventPublisher())
        state = node(_initial_state())
        assert state.job is not None
        assert state.job.notes_raw == "[]"
        assert state.job.links_raw == "[]"
        assert state.errors == []

    def test_malformed_job_data_records_prefixed_error(self):
        job = _job_dict(notes=["not", "a", "string"])
        node = LoadJobNode(FakeJobService(job), RecordingEventPublisher())
        state = node(_initial_state())
        assert state.job is not None
        assert state.job.notes_raw == "['not', 'a', 'string']"

    def test_errors_are_prefixed_with_step(self):
        node = LoadJobNode(FakeJobService(None))
        state = node(_initial_state())
        assert any(e.startswith("[load_job]") for e in state.errors)


class TestCollectSourcesNode:
    def test_collects_primary_url_notes_and_links(self):
        job = _job_dict()
        state = _initial_state()
        state.job = JobData.from_job_dict(job)

        state = CollectSourcesNode()(state)

        urls = [s.url for s in state.sources]
        assert urls == [
            "https://example.com/job",
            "https://example.com/more",
            "https://example.com/apply",
        ]
        assert state.sources[0].type == SourceType.PRIMARY_URL
        assert state.notes == ["Must know Python and Postgres"]

    def test_deduplicates_urls(self):
        job = _job_dict(
            notes=json.dumps(
                [
                    {"type": "url", "content": "https://example.com/job"},
                    {"type": "url", "content": "https://example.com/job"},
                ]
            )
        )
        state = _initial_state()
        state.job = JobData.from_job_dict(job)

        state = CollectSourcesNode()(state)
        assert len([s for s in state.sources if s.url == "https://example.com/job"]) == 1

    def test_handles_malformed_json(self):
        job = _job_dict(url=None, notes="not json", links="not json")
        state = _initial_state()
        state.job = JobData.from_job_dict(job)

        state = CollectSourcesNode()(state)
        assert state.sources == []
        assert state.notes == ["not json"]

    def test_preserves_plain_string_notes(self):
        note = "Strong technical fit: Python backend skills, senior level"
        job = _job_dict(url="https://example.com/job", notes=note, links="[]")
        state = _initial_state()
        state.job = JobData.from_job_dict(job)

        state = CollectSourcesNode()(state)

        assert state.notes == [note]
        assert any(s.type == SourceType.PRIMARY_URL for s in state.sources)

    def test_preserves_plain_string_json_scalar_note(self):
        job = _job_dict(
            url="https://example.com/job",
            notes=json.dumps("Plain scalar note"),
            links="[]",
        )
        state = _initial_state()
        state.job = JobData.from_job_dict(job)

        state = CollectSourcesNode()(state)

        assert state.notes == ["Plain scalar note"]

    def test_preserves_plain_string_link(self):
        job = _job_dict(
            url="https://example.com/job",
            notes="[]",
            links="https://example.com/apply",
        )
        state = _initial_state()
        state.job = JobData.from_job_dict(job)

        state = CollectSourcesNode()(state)

        assert "https://example.com/apply" in [s.url for s in state.sources]

    def test_no_job_records_error(self):
        state = CollectSourcesNode()(_initial_state())
        assert state.errors and state.sources == []


class TestFetchSourcesNode:
    def test_fetches_all_fetchable_sources(self):
        state = _initial_state()
        state.job = JobData.from_job_dict(_job_dict())
        state = CollectSourcesNode()(state)

        fetcher = FakeFetcher(_successful_outcomes())
        state = FetchSourcesNode(fetcher)(state)

        assert len(state.fetched_contents) == 3
        assert all(f.success for f in state.fetched_contents)
        assert state.errors == []

    def test_one_failed_source_does_not_fail_workflow(self):
        state = _initial_state()
        state.job = JobData.from_job_dict(_job_dict())
        state = CollectSourcesNode()(state)

        outcomes = _successful_outcomes()
        outcomes["https://example.com/apply"] = (False, "", "HTTP 500")
        fetcher = FakeFetcher(outcomes)

        state = FetchSourcesNode(fetcher)(state)

        assert len(state.fetched_contents) == 3
        assert sum(1 for f in state.fetched_contents if f.success) == 2
        assert any("Fetch failed" in e for e in state.errors)

    def test_fetcher_raising_is_captured(self):
        state = _initial_state()
        state.job = JobData.from_job_dict(_job_dict())
        state = CollectSourcesNode()(state)

        fetcher = FakeFetcher(error=RuntimeError("network down"))
        state = FetchSourcesNode(fetcher)(state)

        assert all(not f.success for f in state.fetched_contents)
        assert any("Fetch failed" in e for e in state.errors)

    def test_non_fetchable_sources_are_skipped(self):
        state = _initial_state()
        state.job = JobData.from_job_dict(_job_dict(url=None, notes="[]", links="[]"))
        state = CollectSourcesNode()(state)
        assert state.sources == []

        state = FetchSourcesNode(FakeFetcher())(state)
        assert state.fetched_contents == []

    def test_emits_fetching_sources_event(self):
        state = _initial_state()
        state.job = JobData.from_job_dict(_job_dict())
        state = CollectSourcesNode()(state)

        publisher = RecordingEventPublisher()
        state = FetchSourcesNode(FakeFetcher(_successful_outcomes()), publisher)(state)
        assert publisher.events[0][0] == "workflow.step.started"


class TestExtractContentNode:
    def test_extracts_successful_fetches_only(self):
        state = _initial_state()
        state.job = JobData.from_job_dict(_job_dict())
        state = CollectSourcesNode()(state)
        outcomes = _successful_outcomes()
        outcomes["https://example.com/apply"] = (False, "", "HTTP 500")
        state = FetchSourcesNode(FakeFetcher(outcomes))(state)

        state = ExtractContentNode(FakeExtractor())(state)

        assert len(state.extracted_contents) == 2
        assert state.extracted_contents[0].clean_text

    def test_extractor_error_is_recorded(self):
        state = _initial_state()
        state.job = JobData.from_job_dict(_job_dict())
        state = CollectSourcesNode()(state)
        state = FetchSourcesNode(FakeFetcher(_successful_outcomes()))(state)

        state = ExtractContentNode(FakeExtractor(error=RuntimeError("parse failed")))(state)

        assert state.extracted_contents == []
        assert any("Extraction failed" in e for e in state.errors)

    def test_emits_extracting_content_event(self):
        state = _initial_state()
        state.job = JobData.from_job_dict(_job_dict())
        state = CollectSourcesNode()(state)
        state = FetchSourcesNode(FakeFetcher(_successful_outcomes()))(state)

        publisher = RecordingEventPublisher()
        state = ExtractContentNode(FakeExtractor(), publisher)(state)
        assert publisher.events[0][0] == "workflow.step.started"


class TestBuildContextNode:
    def test_builds_context_with_notes_and_content(self):
        state = _initial_state()
        state.job = JobData.from_job_dict(_job_dict())
        state = CollectSourcesNode()(state)
        state = FetchSourcesNode(FakeFetcher(_successful_outcomes()))(state)
        state = ExtractContentNode(FakeExtractor())(state)

        state = BuildContextNode(JobContextBuilderService())(state)

        context = state.processing_context
        assert context is not None
        assert context.job_id == "job-uuid-1"
        assert context.job is not None
        assert len(context.sources) == 3
        assert context.notes == ["Must know Python and Postgres"]
        assert len(context.extracted_contents) == 3
        assert "[NOTE] Must know Python and Postgres" in context.combined_text
        assert context.metadata["extracted_count"] == 3


class TestValidateContextNode:
    def _built_state(self):
        state = _initial_state()
        state.job = JobData.from_job_dict(_job_dict())
        state = CollectSourcesNode()(state)
        state = FetchSourcesNode(FakeFetcher(_successful_outcomes()))(state)
        state = ExtractContentNode(FakeExtractor())(state)
        return BuildContextNode(JobContextBuilderService())(state)

    def test_valid_when_content_exists(self):
        state = self._built_state()
        state = ValidateContextNode(JobContextValidatorService())(state)

        assert state.validation_result is not None
        assert state.validation_result.valid is True
        assert state.errors == []

    def test_invalid_when_empty(self):
        state = _initial_state()
        state.job = JobData.from_job_dict(_job_dict(url=None, notes="[]", links="[]"))
        state = CollectSourcesNode()(state)
        state = BuildContextNode(JobContextBuilderService())(state)
        state = ValidateContextNode(JobContextValidatorService())(state)

        assert state.validation_result is not None
        assert state.validation_result.valid is False
        assert state.errors == [f"[validate_context] {r}" for r in state.validation_result.reasons]


# --------------------------------------------------------------------------- #
# Graph end-to-end
# --------------------------------------------------------------------------- #


class TestJobContextPreparationGraph:
    def test_successful_execution(self):
        graph = _build_graph(job=_job_dict(), fetcher=FakeFetcher(_successful_outcomes()))
        state = graph.invoke(_initial_state())

        assert state.status == ExecutionStatus.COMPLETED
        assert state.validation_result is not None and state.validation_result.valid
        assert state.processing_context is not None
        assert state.processing_context.combined_text
        assert state.errors == []

    def test_failed_source_handling_still_completes(self):
        outcomes = _successful_outcomes()
        outcomes["https://example.com/more"] = (False, "", "HTTP 404")
        graph = _build_graph(job=_job_dict(), fetcher=FakeFetcher(outcomes))

        state = graph.invoke(_initial_state())

        assert state.status == ExecutionStatus.COMPLETED
        assert any("Fetch failed" in e for e in state.errors)

    def test_empty_context_fails(self):
        job = _job_dict(url=None, notes="[]", links="[]")
        graph = _build_graph(job=job)

        state = graph.invoke(_initial_state())

        assert state.status == ExecutionStatus.FAILED
        assert state.validation_result is not None and not state.validation_result.valid

    def test_no_extracted_content_no_notes_fails(self):
        job = _job_dict(url="https://example.com/job", notes="[]", links="[]")
        graph = _build_graph(
            job=job,
            fetcher=FakeFetcher({"https://example.com/job": (True, "<p>empty</p>", None)}),
            extractor=FakeExtractor({"https://example.com/job": ""}),
        )

        state = graph.invoke(_initial_state())

        assert state.status == ExecutionStatus.FAILED
        assert state.validation_result is not None and not state.validation_result.valid

    def test_job_not_found_fails(self):
        graph = _build_graph(job=None)

        state = graph.invoke(_initial_state())

        assert state.status == ExecutionStatus.FAILED
        assert any("not found" in e for e in state.errors)

    def test_notes_alone_make_context_valid(self):
        job = _job_dict(
            url="https://example.com/job",
            links="[]",
            notes=json.dumps([{"type": "text", "content": "Useful note about the role"}]),
        )
        graph = _build_graph(
            job=job,
            fetcher=FakeFetcher({"https://example.com/job": (True, "<p>empty</p>", None)}),
            extractor=FakeExtractor({"https://example.com/job": ""}),
        )

        state = graph.invoke(_initial_state())

        assert state.status == ExecutionStatus.COMPLETED
        assert state.processing_context is not None
        assert state.processing_context.combined_text == "[NOTE] Useful note about the role"

    def test_plain_string_note_with_failed_fetch_completes(self):
        note = "Strong technical fit: Python backend skills, senior level"
        job = _job_dict(
            url="https://www.linkedin.com/jobs/view/4418271279",
            notes=note,
            links="[]",
        )
        graph = _build_graph(
            job=job,
            fetcher=FakeFetcher(
                {
                    "https://www.linkedin.com/jobs/view/4418271279": (
                        False,
                        "",
                        "Playwright is not installed",
                    )
                }
            ),
            extractor=FakeExtractor({"https://www.linkedin.com/jobs/view/4418271279": ""}),
        )

        state = graph.invoke(_initial_state())

        assert state.status == ExecutionStatus.COMPLETED
        assert state.validation_result is not None and state.validation_result.valid
        assert state.processing_context is not None
        assert state.processing_context.notes == [note]
        assert state.processing_context.combined_text == f"[NOTE] {note}"
        assert any("Fetch failed" in e for e in state.errors)
        assert not any("empty notes" in e for e in state.errors)

    def test_emits_all_context_events(self):
        publisher = RecordingEventPublisher()
        graph = _build_graph(job=_job_dict(), publisher=publisher)

        graph.invoke(_initial_state())

        names = [e[0] for e in publisher.events]
        assert "workflow.step.started" in names
        assert "workflow.step.completed" in names


# --------------------------------------------------------------------------- #
# Infrastructure adapters
# --------------------------------------------------------------------------- #


class TestHTTPXContentFetcher:
    def test_success(self, monkeypatch):
        class FakeResponse:
            is_success = True
            status_code = 200
            text = "<html><body>Hello</body></html>"
            url = "https://example.com/job"
            headers = {"content-type": "text/html"}

        class FakeClient:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def get(self, url):
                return FakeResponse()

        import httpx

        monkeypatch.setattr(httpx, "Client", FakeClient)

        fetcher = HTTPXContentFetcher()
        source = JobSource(url="https://example.com/job", type=SourceType.PRIMARY_URL)
        result = fetcher.fetch(source)

        assert result.success is True
        assert result.status_code == 200
        assert result.content == "<html><body>Hello</body></html>"
        assert result.error is None

    def test_http_error_returns_failure(self, monkeypatch):
        import httpx

        class FakeClient:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def get(self, url):
                raise httpx.HTTPStatusError("500", request=None, response=None)

        monkeypatch.setattr(httpx, "Client", FakeClient)

        fetcher = HTTPXContentFetcher()
        source = JobSource(url="https://example.com/job", type=SourceType.PRIMARY_URL)
        result = fetcher.fetch(source)

        assert result.success is False
        assert "HTTPStatusError" in (result.error or "")

    def test_invalid_url(self):
        fetcher = HTTPXContentFetcher()
        source = JobSource(url="ftp://example.com", type=SourceType.PRIMARY_URL)
        result = fetcher.fetch(source)
        assert result.success is False
        assert "Invalid URL" in (result.error or "")


class TestPlaywrightContentFetcher:
    def test_degrades_when_not_installed(self):
        fetcher = PlaywrightContentFetcher()
        source = JobSource(url="https://example.com/job", type=SourceType.PRIMARY_URL)
        result = fetcher.fetch(source)
        assert result.success is False
        assert "Playwright is not installed" in (result.error or "")


class TestCompositeContentFetcher:
    def test_returns_first_success(self):
        first = FakeFetcher({"https://example.com/job": (False, "", "boom")})
        second = FakeFetcher({"https://example.com/job": (True, "<p>ok</p>", None)})
        composite = CompositeContentFetcher([first, second])

        source = JobSource(url="https://example.com/job", type=SourceType.PRIMARY_URL)
        result = composite.fetch(source)

        assert result.success is True
        assert result.metadata.get("fetcher") == "FakeFetcher"

    def test_returns_last_failure_when_all_fail(self):
        first = FakeFetcher({"https://example.com/job": (False, "", "boom")})
        composite = CompositeContentFetcher([first])

        source = JobSource(url="https://example.com/job", type=SourceType.PRIMARY_URL)
        result = composite.fetch(source)

        assert result.success is False

    def test_returns_primary_error_over_degraded_fallback(self):
        first = FakeFetcher({"https://example.com/job": (False, "", "HTTP 403")})
        second = FakeFetcher(
            {"https://example.com/job": (False, "", "Playwright is not installed")}
        )
        composite = CompositeContentFetcher([first, second])

        source = JobSource(url="https://example.com/job", type=SourceType.PRIMARY_URL)
        result = composite.fetch(source)

        assert result.success is False
        assert result.error == "HTTP 403"

    def test_returns_degraded_error_when_only_fallback_attempted(self):
        first = FakeFetcher(
            {"https://example.com/job": (False, "", "Playwright is not installed")}
        )
        composite = CompositeContentFetcher([first])

        source = JobSource(url="https://example.com/job", type=SourceType.PRIMARY_URL)
        result = composite.fetch(source)

        assert result.success is False
        assert "Playwright is not installed" in (result.error or "")


class TestCompositeContentExtractor:
    def test_falls_back_to_clean_strip_when_no_library(self):
        composite = CompositeContentExtractor(
            [TrafilaturaContentExtractor(), BeautifulSoupContentExtractor()]
        )
        source = JobSource(url="https://example.com/job", type=SourceType.PRIMARY_URL)
        fetched = FetchedContent(
            source=source,
            url="https://example.com/job",
            success=True,
            content="<html><body><p>Hello world</p></body></html>",
            content_type="html",
        )

        result = composite.extract(fetched)

        assert result.clean_text.strip() == "Hello world"

    def test_uses_first_extractor_that_returns_text(self):
        primary = FakeExtractor({"https://example.com/job": "clean text"})
        composite = CompositeContentExtractor([primary])
        source = JobSource(url="https://example.com/job", type=SourceType.PRIMARY_URL)
        fetched = FetchedContent(
            source=source,
            url="https://example.com/job",
            success=True,
            content="<p>raw</p>",
            content_type="html",
        )

        result = composite.extract(fetched)

        assert result.clean_text == "clean text"


# --------------------------------------------------------------------------- #
# Runner wiring
# --------------------------------------------------------------------------- #


class TestRunnerJobContextWiring:
    def test_job_processing_runs_context_graph(self):
        execution = ProcessingExecution(
            id=str(uuid.uuid4()),
            execution_type=ExecutionType.JOB_PROCESSING,
            target_type="job",
            target_id="job-uuid-1",
            status=ExecutionStatus.QUEUED,
            created_at=datetime.now(UTC),
        )

        fake_state = JobProcessingState(
            execution_id=execution.id,
            job_id="job-uuid-1",
            status=ExecutionStatus.COMPLETED,
        )

        fake_graph = type("FakeGraph", (), {"invoke": lambda self, state: fake_state})()

        with patch(
            "processing.infrastructure.workflow.build_job_context_preparation_graph",
            return_value=fake_graph,
        ) as build_mock:
            result = ProcessingExecutionRunner()._run_workflow(execution)

        assert result == {"job_id": "job-uuid-1"}
        build_mock.assert_called_once()
