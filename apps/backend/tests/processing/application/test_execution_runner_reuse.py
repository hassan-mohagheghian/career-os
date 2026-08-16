"""Tests for the LLM-error content-reuse behaviour of the processing runner.

Reuse (skip re-fetch + re-extract) is allowed only when the target already has
persisted prepared content AND its most recent prior execution FAILED. A first
process and a reprocess of a completed target must run from scratch.
"""

import uuid
from datetime import datetime, UTC
from unittest.mock import patch

from processing.domain.enums import ExecutionType, ExecutionStatus
from processing.domain.entities.processing_execution import ProcessingExecution
from processing.infrastructure.runner.execution_runner import ProcessingExecutionRunner
from processing.domain.workflow.job_processing_state import JobProcessingState


class FakeExecutionRepo:
    def __init__(self):
        self._store: dict[str, ProcessingExecution] = {}

    def save(self, execution: ProcessingExecution) -> ProcessingExecution:
        self._store[execution.id] = execution
        return execution

    def list_by_target(self, target_type: str, target_id: str) -> list[ProcessingExecution]:
        return [e for e in self._store.values() if e.target_type == target_type and e.target_id == target_id]


def _execution(
    target_type: str = "job",
    target_id: str = "tgt-1",
    status: ExecutionStatus = ExecutionStatus.FAILED,
) -> ProcessingExecution:
    return ProcessingExecution(
        id=str(uuid.uuid4()),
        execution_type=ExecutionType.JOB_PROCESSING,
        target_type=target_type,
        target_id=target_id,
        status=status,
        created_at=datetime.now(UTC),
    )


class TestShouldReuse:
    def test_reuse_requires_content_and_failed_prior(self):
        assert ProcessingExecutionRunner._should_reuse(True, ExecutionStatus.FAILED) is True

    def test_no_content_means_no_reuse(self):
        assert ProcessingExecutionRunner._should_reuse(False, ExecutionStatus.FAILED) is False

    def test_completed_prior_means_no_reuse(self):
        assert ProcessingExecutionRunner._should_reuse(True, ExecutionStatus.COMPLETED) is False

    def test_queued_prior_means_no_reuse(self):
        assert ProcessingExecutionRunner._should_reuse(True, ExecutionStatus.QUEUED) is False


class TestReuseAvailable:
    def _runner_with_prior(self, prior_status: ExecutionStatus) -> ProcessingExecutionRunner:
        repo = FakeExecutionRepo()
        repo.save(_execution(status=prior_status))
        return ProcessingExecutionRunner(repo)

    def test_true_when_content_and_failed_prior(self):
        runner = self._runner_with_prior(ExecutionStatus.FAILED)
        with patch.object(ProcessingExecutionRunner, "_target_content", return_value="   cached content  "):
            assert runner._reuse_available(_execution(), None) is True

    def test_false_when_prior_completed(self):
        runner = self._runner_with_prior(ExecutionStatus.COMPLETED)
        with patch.object(ProcessingExecutionRunner, "_target_content", return_value="cached content"):
            assert runner._reuse_available(_execution(), None) is False

    def test_false_when_no_content(self):
        runner = self._runner_with_prior(ExecutionStatus.FAILED)
        with patch.object(ProcessingExecutionRunner, "_target_content", return_value="   "):
            assert runner._reuse_available(_execution(), None) is False

    def test_false_when_no_prior_execution(self):
        runner = ProcessingExecutionRunner(FakeExecutionRepo())
        with patch.object(ProcessingExecutionRunner, "_target_content", return_value="cached content"):
            assert runner._reuse_available(_execution(), None) is False

    def test_false_for_non_job_company_target(self):
        runner = self._runner_with_prior(ExecutionStatus.FAILED)
        with patch.object(ProcessingExecutionRunner, "_target_content", return_value="cached content"):
            assert runner._reuse_available(_execution(target_type="candidate"), None) is False


class TestRunnerSkipsPrepOnReuse:
    """_run_workflow must skip the context preparation graph when reuse is
    available (no re-fetch/extract), and must run it from scratch otherwise."""

    def _fake_analysis_graph(self, status: ExecutionStatus = ExecutionStatus.COMPLETED):
        class FakeGraph:
            def invoke(self, state):
                if isinstance(state, JobProcessingState):
                    state.status = status
                else:
                    state.status = status
                return state

        return FakeGraph()

    def test_reuse_skips_prep_and_runs_analysis_directly(self):
        execution = _execution()
        fake = self._fake_analysis_graph()

        with (
            patch.object(ProcessingExecutionRunner, "_reuse_available", return_value=True),
            patch(
                "processing.infrastructure.workflow.build_job_context_preparation_graph"
            ) as build_prep,
            patch(
                "processing.infrastructure.workflow.build_job_analysis_graph",
                return_value=fake,
            ) as build_analysis,
        ):
            result = ProcessingExecutionRunner()._run_workflow(execution, None, object())

        assert result == {"job_id": "tgt-1"}
        build_prep.assert_not_called()
        build_analysis.assert_called_once()

    def test_no_reuse_runs_prep_then_analysis(self):
        execution = _execution()
        fake = self._fake_analysis_graph()

        with (
            patch.object(ProcessingExecutionRunner, "_reuse_available", return_value=False),
            patch(
                "processing.infrastructure.workflow.build_job_context_preparation_graph",
                return_value=fake,
            ) as build_prep,
            patch(
                "processing.infrastructure.workflow.build_job_analysis_graph",
                return_value=fake,
            ) as build_analysis,
        ):
            result = ProcessingExecutionRunner()._run_workflow(execution, None, object())

        assert result == {"job_id": "tgt-1"}
        build_prep.assert_called_once()
        build_analysis.assert_called_once()