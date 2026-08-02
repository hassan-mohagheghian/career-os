"""ProcessJobUseCase — orchestrates the job processing workflow graph."""

from __future__ import annotations

from typing import Any, Optional

from ..commands.process_job import ProcessJobCommand
from ..dto.job_processing_result import JobProcessingResult
from ...domain.entities.generation_session import GenerationSession
from ...domain.repositories.generation_session_repository import IGenerationSessionRepository


class ProcessJobUseCase:
    """Use case for processing a job through the AI workflow graph.

    Business contexts call this use case. The AI context owns:
    - Graph execution
    - Provider coordination
    - Progress tracking
    - Result persistence
    """

    def __init__(
        self,
        session_repository: IGenerationSessionRepository,
        graph_executor: Any = None,
        progress_emitter: Any = None,
    ):
        self._session_repo = session_repository
        self._graph_executor = graph_executor
        self._progress_emitter = progress_emitter

    def execute(self, command: ProcessJobCommand) -> JobProcessingResult:
        """Execute the job processing workflow.

        Args:
            command: The process job command with input data.

        Returns:
            JobProcessingResult with the processing outcome.
        """
        # Validate command
        errors = command.validate()
        if errors:
            return JobProcessingResult(success=False, errors=errors)

        # Create generation session
        session = GenerationSession(
            workflow_type="job_processing",
            entity_type="job",
            entity_id=command.url or str(command.pid),
        )
        session.start()
        session_id = self._session_repo.save(session)

        try:
            # Execute the graph
            if self._graph_executor:
                result = self._graph_executor.execute(
                    command=command,
                    session_id=session_id,
                    progress_callback=self._emit_progress,
                )
            else:
                result = self._execute_fallback(command, session_id)

            # Update session
            session.complete()
            self._session_repo.save(session)

            return result

        except Exception as e:
            session.fail(str(e))
            self._session_repo.save(session)
            return JobProcessingResult(
                success=False,
                errors=[str(e)],
                session_id=session_id,
            )

    def _execute_fallback(
        self,
        command: ProcessJobCommand,
        session_id: str,
    ) -> JobProcessingResult:
        """Fallback execution when no graph executor is provided."""
        return JobProcessingResult(
            success=False,
            errors=["No graph executor configured"],
            session_id=session_id,
        )

    def _emit_progress(
        self,
        stage: str,
        progress: float,
        message: str = "",
    ) -> None:
        """Emit progress event to connected clients."""
        if self._progress_emitter:
            self._progress_emitter.emit(
                "ai.progress",
                {
                    "stage": stage,
                    "progress": progress,
                    "message": message,
                },
            )
