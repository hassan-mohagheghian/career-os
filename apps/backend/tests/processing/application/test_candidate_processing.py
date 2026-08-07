"""Tests for the candidate processing workflows (preparation + extraction/merge),
the candidate step mapper and the runner dispatch branch."""

import json
import uuid
from datetime import datetime, UTC
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from candidates.application.services.candidate_extract_service import (
    CandidateExtractService,
)
from processing.application.workflows.candidate_source_preparation import (
    CandidateSourcePreparationGraph,
)
from processing.application.workflows.candidate_processing import CandidateProcessingGraph
from processing.application.workflows.candidate_workflow_step_mapper import (
    CandidateWorkflowStepMapper,
)
from processing.application.workflows import progress_ops
from processing.domain.enums import ExecutionStatus, ExecutionType
from processing.domain.entities.processing_execution import ProcessingExecution
from processing.domain.workflow.candidate_processing_state import CandidateProcessingState
from processing.domain.workflow.workflow_step import WorkflowStepStatus


# ── fakes ──────────────────────────────────────────────────────────


class FakeProfileRepo:
    def __init__(self):
        self.current = None
        self.core = None
        self.children = {}
        self.versions = []

    def get_current_profile(self):
        if self.current is None:
            return None
        profile = dict(self.current)
        if self.versions:
            profile["version"] = self.versions[0]["version"]
        for kind, items in self.children.items():
            profile[kind] = list(items)
        return profile

    def get_or_create_current(self):
        if self.current is None:
            self.current = {"id": "profile-1", "candidate_id": "cand-1", "version": 1}
        return self.get_current_profile()

    def update_core(self, profile_id, data):
        self.core = {"profile_id": profile_id, **data}
        self.current.update(data)

    def replace_children(self, profile_id, kind, items):
        self.children[kind] = list(items)

    def create_version(self, profile_id, version, snapshot, source_versions, change_summary=""):
        self.versions.insert(
            0,
            {
                "profile_id": profile_id,
                "version": version,
                "snapshot": snapshot,
                "source_versions": source_versions,
                "change_summary": change_summary,
            },
        )
        return self.versions[0]

    def list_versions(self, profile_id):
        return [dict(v) for v in self.versions]


class FakeSourceRepo:
    def __init__(self, rows=None):
        self.rows = {r["source_type"]: r for r in rows or []}

    def list_for_profile(self, profile_id):
        return list(self.rows.values())

    def get_latest_by_type(self, profile_id, source_type):
        row = self.rows.get(source_type)
        return dict(row) if row else None

    def get_by_type_and_version(self, profile_id, source_type, version):
        row = self.rows.get(source_type)
        return row if row and row["version"] == version else None

    def create(self, data):
        self.rows[data["source_type"]] = {"id": f"src-{len(self.rows) + 1}", **data}

    def update(self, source_id, data):
        for row in self.rows.values():
            if row.get("id") == source_id:
                row.update(data)
                return row
        return None


class FakeSkillRepo:
    def __init__(self):
        self.ids = {}

    def resolve_skill(self, data):
        name = data["name"]
        if name not in self.ids:
            self.ids[name] = len(self.ids) + 1
        return self.ids[name]


class FakeLLM:
    def __init__(self, content=None, fail=False):
        self._content = content
        self._fail = fail
        self.calls = 0

    def generate_structured(self, prompt, schema=None, timeout=None):
        self.calls += 1
        if self._fail:
            raise RuntimeError("Failed to parse model JSON output")
        return SimpleNamespace(content=self._content)


def _payload():
    return {
        "profile": {"name": "Hassan", "title": "Backend", "headline": "h", "summary": "s", "location": "Cairo"},
        "skills": [{"name": "Python", "level": 5, "category": "language", "confidence": 0.9}],
        "experiences": [{"company": "Acme", "role": "Backend", "confidence": 0.8}],
        "projects": [],
        "educations": [],
        "certificates": [],
        "interests": [],
        "languages": [],
    }


def _resume_rows():
    return [
        {"id": "src-1", "source_type": "resume", "version": 1, "raw_text": "My resume text", "status": "pending"},
        {"id": "src-2", "source_type": "linkedin", "version": 1, "raw_text": "LinkedIn profile", "status": "pending"},
    ]


def _make_service(profile_repo, source_repo, skill_repo, llm_content, llm_fail=False):
    return CandidateExtractService(
        profile_repo=profile_repo,
        source_repo=source_repo,
        skill_repo=skill_repo,
        llm=FakeLLM(content=llm_content, fail=llm_fail),
    )


def _state(profile_id="profile-1"):
    return CandidateProcessingState(
        execution_id=str(uuid.uuid4()),
        profile_id=profile_id,
        workflow_progress=progress_ops.build_initial_progress(str(uuid.uuid4()), "candidate"),
    )


# ── preparation graph ──────────────────────────────────────────────


class TestCandidateSourcePreparation:
    def test_prep_collects_pending_sources(self):
        graph = CandidateSourcePreparationGraph(
            profile_repo=FakeProfileRepo(),
            source_repo=FakeSourceRepo(_resume_rows()),
        )
        final = graph.invoke(_state())

        assert final.status == ExecutionStatus.COMPLETED
        assert final.profile_id == "profile-1"
        assert {s["source_type"] for s in final.pending_sources} == {"resume", "linkedin"}
        assert final.pending_sources[0]["raw_text"]

    def test_prep_skips_already_known_source_versions(self):
        source_repo = FakeSourceRepo(
            [
                {"id": "s1", "profile_id": "profile-1", "source_type": "resume", "version": 1, "status": "processed"},
                {"source_type": "linkedin", "version": 1, "raw_text": "LinkedIn profile", "status": "pending"},
            ]
        )
        graph = CandidateSourcePreparationGraph(
            profile_repo=FakeProfileRepo(),
            source_repo=source_repo,
        )
        final = graph.invoke(_state())

        types = {s["source_type"] for s in final.pending_sources}
        assert "resume" not in types
        assert "linkedin" in types

    def test_prep_processes_pending_sources_even_if_version_known(self):
        source_repo = FakeSourceRepo(
            [
                {"id": "s1", "profile_id": "profile-1", "source_type": "resume", "version": 1, "status": "pending", "raw_text": "My resume text"},
                {"source_type": "linkedin", "version": 1, "raw_text": "LinkedIn profile", "status": "pending"},
            ]
        )
        graph = CandidateSourcePreparationGraph(
            profile_repo=FakeProfileRepo(),
            source_repo=source_repo,
        )
        final = graph.invoke(_state())

        types = {s["source_type"] for s in final.pending_sources}
        assert "resume" in types
        assert "linkedin" in types

    def test_prep_no_content_yields_no_pending_sources(self):
        graph = CandidateSourcePreparationGraph(
            profile_repo=FakeProfileRepo(),
            source_repo=FakeSourceRepo(),
        )
        final = graph.invoke(_state())
        assert final.status == ExecutionStatus.COMPLETED
        assert final.pending_sources == []

    def test_prep_load_failure_fails(self):
        class Boom:
            def get_or_create_current(self):
                raise RuntimeError("db down")

        graph = CandidateSourcePreparationGraph(
            profile_repo=Boom(),
            source_repo=FakeSourceRepo(),
        )
        final = graph.invoke(_state())
        assert final.status == ExecutionStatus.FAILED
        assert final.errors


# ── processing graph ───────────────────────────────────────────────


class TestCandidateProcessing:
    def _run_full(self, profile_repo=None, source_repo=None, llm_content=None, llm_fail=False):
        profile_repo = profile_repo or FakeProfileRepo()
        source_repo = source_repo or FakeSourceRepo(_resume_rows())
        skill_repo = FakeSkillRepo()
        service = _make_service(profile_repo, source_repo, skill_repo, llm_content or json.dumps(_payload()), llm_fail)

        prep = CandidateSourcePreparationGraph(
            profile_repo=profile_repo,
            source_repo=source_repo,
        )
        state = prep.invoke(_state())
        processing = CandidateProcessingGraph(extract_service=service)
        return processing.invoke(state), profile_repo, source_repo, service

    def test_full_flow_extracts_merges_and_versions(self):
        final, profile_repo, source_repo, service = self._run_full()

        assert final.status == ExecutionStatus.COMPLETED
        assert final.merge_result is not None
        assert final.merge_result["version"] == 1
        assert profile_repo.versions[0]["version"] == 1
        assert profile_repo.core["name"] == "Hassan"
        assert profile_repo.children["skills"][0]["name"] == "Python"
        assert source_repo.rows["resume"]["status"] == "processed"
        assert source_repo.rows["linkedin"]["status"] == "processed"

    def test_full_flow_progress_tree_completes(self):
        final, *_ = self._run_full()
        steps = final.workflow_progress.steps
        ids = [s.id for s in steps]
        assert ids == ["load_profile", "prepare_sources", "extract", "merge"]
        assert all(s.status == WorkflowStepStatus.COMPLETED for s in steps)
        assert final.workflow_progress.status.value == "completed"

    def test_extraction_failure_fails_whole_run(self):
        final, *_ = self._run_full(llm_fail=True)
        assert final.status == ExecutionStatus.FAILED
        assert any("extract" in e for e in final.errors)

    def test_events_emitted_through_workflow(self):
        final, profile_repo, source_repo, service = self._run_full()
        types = {e.event_type for e in service.event_publisher.events}
        assert "candidate.merge.completed" in types
        assert "candidate.version.created" in types
        assert "candidate.skill.inferred" in types


# ── step mapper + progress ops dispatch ───────────────────────────


class TestCandidateStepMapper:
    def test_initial_progress_uses_candidate_tree(self):
        progress = progress_ops.build_initial_progress("exec-1", "candidate")
        assert progress.id == "candidate_processing"
        assert [s.id for s in progress.steps] == ["load_profile", "prepare_sources", "extract", "merge"]

    def test_hidden_nodes_not_displayable(self):
        assert not CandidateWorkflowStepMapper.is_displayable("execution_failed")
        assert not CandidateWorkflowStepMapper.is_displayable("sources_ready")
        assert not CandidateWorkflowStepMapper.is_displayable("candidate_ready")
        assert CandidateWorkflowStepMapper.is_displayable("extract")

    def test_state_dispatch_uses_profile_id(self):
        state = CandidateProcessingState(execution_id="exec-1", profile_id="p1")
        progress = progress_ops._build_initial_progress(state)
        assert progress.id == "candidate_processing"


# ── runner dispatch ────────────────────────────────────────────────


class TestRunnerCandidateDispatch:
    def test_run_workflow_runs_both_graphs(self):
        from processing.infrastructure.runner.execution_runner import ProcessingExecutionRunner

        class FakeGraph:
            def __init__(self, fail=False):
                self._fail = fail

            def invoke(self, state):
                if self._fail:
                    state.status = ExecutionStatus.FAILED
                    state.errors.append("boom")
                return state

        execution = ProcessingExecution(
            id=str(uuid.uuid4()),
            execution_type=ExecutionType.CANDIDATE_PROCESSING,
            target_type="candidate",
            target_id="profile-1",
            status=ExecutionStatus.CREATED,
            created_at=datetime.now(UTC),
        )
        runner = ProcessingExecutionRunner()

        with (
            patch(
                "processing.infrastructure.workflow.build_candidate_source_preparation_graph",
                return_value=FakeGraph(),
            ) as prep_builder,
            patch(
                "processing.infrastructure.workflow.build_candidate_processing_graph",
                return_value=FakeGraph(),
            ) as process_builder,
        ):
            result = runner._run_workflow(execution)

        prep_builder.assert_called_once()
        process_builder.assert_called_once()
        assert result == {"profile_id": "profile-1"}

    def test_run_workflow_raises_when_graph_fails(self):
        from processing.infrastructure.runner.execution_runner import ProcessingExecutionRunner

        class FakeGraph:
            def invoke(self, state):
                state.status = ExecutionStatus.FAILED
                state.errors.append("extract failed")
                return state

        execution = ProcessingExecution(
            id=str(uuid.uuid4()),
            execution_type=ExecutionType.CANDIDATE_PROCESSING,
            target_type="candidate",
            target_id="profile-1",
            status=ExecutionStatus.CREATED,
            created_at=datetime.now(UTC),
        )
        runner = ProcessingExecutionRunner()

        with (
            patch(
                "processing.infrastructure.workflow.build_candidate_source_preparation_graph",
                return_value=FakeGraph(),
            ),
            patch(
                "processing.infrastructure.workflow.build_candidate_processing_graph",
                return_value=FakeGraph(),
            ),
        ):
            with pytest.raises(RuntimeError, match="extract failed"):
                runner._run_workflow(execution)
