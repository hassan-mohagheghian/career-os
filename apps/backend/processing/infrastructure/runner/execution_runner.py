"""Worker-side ProcessingExecution runner.

Drives a ProcessingExecution through its lifecycle by coordinating the
LangGraph workflow execution:

    Load ProcessingExecution
        ↓
    Mark execution running
        ↓
    Start LangGraph workflow
        ↓
    Update workflow progress after each node
        ↓
    Complete or fail execution

TaskIQ starts this runner (via process_execution_task). The runner updates
ProcessingExecution state and publishes processing events for SSE delivery.
"""

from __future__ import annotations

from datetime import datetime, UTC

from processing.application.workflows import progress_ops
from processing.domain.enums import ExecutionStatus, ExecutionType
from processing.infrastructure.repositories.sa_processing_execution_repository import (
    SQLAlchemyProcessingExecutionRepository,
)
from shared.infrastructure.database.session import get_session_sync
from shared.infrastructure.events import processing_events
from shared.infrastructure.process.logging_config import get_logger

log = get_logger("processing.runner")


class ProcessingExecutionRunner:
    """Executes a ProcessingExecution and updates its lifecycle state."""

    def __init__(self, repository=None, job_repository=None):
        self._repository = repository
        self._job_repository = job_repository

    def run(self, execution_id: str) -> dict:
        session = None
        try:
            if self._repository is not None:
                repo = self._repository
                job_repo = self._job_repository
            else:
                session = get_session_sync()
                repo = SQLAlchemyProcessingExecutionRepository(session)
                job_repo = None
            execution = repo.get_by_id(execution_id)
            if not execution:
                raise RuntimeError(f"ProcessingExecution {execution_id} not found")

            job_id = self._job_id(execution)
            started_at = datetime.now(UTC)

            execution.status = ExecutionStatus.RUNNING
            execution.started_at = started_at
            execution.workflow_progress = progress_ops.build_initial_progress(
                execution.id, execution.target_type
            ).to_dict()
            repo.save(execution)
            processing_events.publish_sync(
                processing_events.EXECUTION_STARTED,
                execution.id,
                job_id,
                ExecutionStatus.RUNNING.value,
                target_type=execution.target_type,
                target_id=execution.target_id,
                updated_at=started_at.isoformat(),
            )

            try:
                result = self._run_workflow(execution, job_repo, session)
            except Exception as e:
                finished_at = datetime.now(UTC)
                if session is not None:
                    session.rollback()
                execution.status = ExecutionStatus.FAILED
                execution.finished_at = finished_at
                execution.error_message = str(e)
                if execution.workflow_progress:
                    execution.workflow_progress["status"] = "failed"
                repo.save(execution)
                processing_events.publish_sync(
                    processing_events.EXECUTION_FAILED,
                    execution.id,
                    job_id,
                    ExecutionStatus.FAILED.value,
                    message=str(e),
                    target_type=execution.target_type,
                    target_id=execution.target_id,
                    updated_at=finished_at.isoformat(),
                )
                log.error("processing.execution.failed", execution_id=execution.id, error=str(e))
                raise

            finished_at = datetime.now(UTC)
            if session is not None:
                session.rollback()
            execution.status = ExecutionStatus.COMPLETED
            execution.finished_at = finished_at
            if execution.workflow_progress:
                execution.workflow_progress["status"] = "completed"
            repo.save(execution)
            processing_events.publish_sync(
                processing_events.EXECUTION_COMPLETED,
                execution.id,
                job_id,
                ExecutionStatus.COMPLETED.value,
                target_type=execution.target_type,
                target_id=execution.target_id,
                updated_at=finished_at.isoformat(),
            )
            log.info("processing.execution.completed", execution_id=execution.id)
            return result
        finally:
            if session is not None:
                session.close()

    @staticmethod
    def _job_id(execution) -> str | None:
        """Map a processing execution to the job_id used in SSE payloads.

        The new processing features identify jobs by their UUID `id`, so the
        SSE payload carries the job's UUID rather than the numeric `num`.
        """
        if execution.target_type == "job":
            return execution.target_id
        return None

    def _run_workflow(self, execution, job_repo=None, session=None) -> dict:
        """Start the LangGraph workflow matching the execution's type.

        Business logic is not duplicated here — the runner delegates to the
        existing application workers / workflows that own LangGraph execution.

        JOB_PROCESSING executions run the JobContextPreparationGraph (no LLM).
        """
        if execution.execution_type == ExecutionType.JOB_PROCESSING:
            from processing.domain.workflow.job_processing_state import JobProcessingState
            from processing.infrastructure.workflow import (
                build_job_analysis_graph,
                build_job_context_preparation_graph,
            )

            graph_session = session
            owns_session = False
            if graph_session is None:
                graph_session = get_session_sync()
                owns_session = True
            try:
                graph = build_job_context_preparation_graph(graph_session)
                state = JobProcessingState(
                    execution_id=execution.id,
                    job_id=self._job_id(execution) or "",
                    workflow_progress=progress_ops.build_initial_progress(
                        execution.id, execution.target_type
                    ),
                )
                final = graph.invoke(state)
                if final.status != ExecutionStatus.FAILED:
                    analysis_graph = build_job_analysis_graph(graph_session)
                    final = analysis_graph.invoke(final)
                if final.workflow_progress is not None:
                    execution.workflow_progress = final.workflow_progress.to_dict()
                if final.status == ExecutionStatus.FAILED:
                    raise RuntimeError("; ".join(final.errors) or "Job processing failed")
                return {"job_id": self._job_id(execution)}
            finally:
                if owns_session:
                    graph_session.close()

        if execution.execution_type == ExecutionType.COMPANY_PROCESSING:
            from processing.domain.workflow.company_processing_state import CompanyProcessingState
            from processing.infrastructure.workflow import (
                build_company_analysis_graph,
                build_company_context_preparation_graph,
            )

            graph_session = session
            owns_session = False
            if graph_session is None:
                graph_session = get_session_sync()
                owns_session = True
            try:
                graph = build_company_context_preparation_graph(graph_session)
                state = CompanyProcessingState(
                    execution_id=execution.id,
                    company_id=execution.target_id,
                    workflow_progress=progress_ops.build_initial_progress(
                        execution.id, execution.target_type
                    ),
                )
                final = graph.invoke(state)
                if final.status != ExecutionStatus.FAILED:
                    analysis_graph = build_company_analysis_graph(graph_session)
                    final = analysis_graph.invoke(final)
                if final.workflow_progress is not None:
                    execution.workflow_progress = final.workflow_progress.to_dict()
                if final.status == ExecutionStatus.FAILED:
                    raise RuntimeError("; ".join(final.errors) or "Company processing failed")
                return {"company_id": execution.target_id}
            finally:
                if owns_session:
                    graph_session.close()

        if execution.execution_type == ExecutionType.CANDIDATE_PROCESSING:
            from processing.domain.workflow.candidate_processing_state import CandidateProcessingState
            from processing.infrastructure.workflow import (
                build_candidate_processing_graph,
                build_candidate_source_preparation_graph,
            )

            graph_session = session
            owns_session = False
            if graph_session is None:
                graph_session = get_session_sync()
                owns_session = True
            try:
                graph = build_candidate_source_preparation_graph(graph_session)
                state = CandidateProcessingState(
                    execution_id=execution.id,
                    profile_id=execution.target_id or "",
                    workflow_progress=progress_ops.build_initial_progress(
                        execution.id, execution.target_type
                    ),
                )
                final = graph.invoke(state)
                if final.status != ExecutionStatus.FAILED:
                    processing_graph = build_candidate_processing_graph(graph_session)
                    final = processing_graph.invoke(final)
                if final.workflow_progress is not None:
                    execution.workflow_progress = final.workflow_progress.to_dict()
                if final.status == ExecutionStatus.FAILED:
                    raise RuntimeError("; ".join(final.errors) or "Candidate processing failed")
                return {"profile_id": final.profile_id or execution.target_id}
            finally:
                if owns_session:
                    graph_session.close()

        raise RuntimeError(f"Unsupported execution type: {execution.execution_type}")
