from __future__ import annotations

import json
from typing import Dict, Any, Optional

from shared.infrastructure.process.worker_base import WorkerBase
from shared.infrastructure.process.models import WorkflowStep, JobStatus
from ai.infrastructure.graphs.runtime.state import create_initial_state
from ai.infrastructure.graphs.job.graph import build_job_processing_graph


# Maps workflow nodes to their corresponding job statuses
NODE_TO_STATUS = {
    'load_context': JobStatus.PROCESSING,
    'validate_input': JobStatus.PROCESSING,
    'fetch_url': JobStatus.PROCESSING,
    'fallback_to_notes': JobStatus.PROCESSING,
    'extract_raw_content': JobStatus.PROCESSING,
    'clean_content': JobStatus.PROCESSING,
    'extract_structured_data': JobStatus.PROCESSING,
    'analyze_job': JobStatus.PROCESSING,
    'extract_skills': JobStatus.PROCESSING,
    'score_job': JobStatus.PROCESSING,
    'generate_summary': JobStatus.PROCESSING,
    'persist_results': JobStatus.PROCESSING,
    'completion_event': JobStatus.PROCESSING,
}

# Maps nodes to WorkflowStep for log events
NODE_TO_STEP = {
    'load_context': WorkflowStep.VALIDATE,
    'validate_input': WorkflowStep.VALIDATE,
    'fetch_url': WorkflowStep.FETCH,
    'fallback_to_notes': WorkflowStep.FETCH,
    'extract_raw_content': WorkflowStep.EXTRACT,
    'clean_content': WorkflowStep.EXTRACT,
    'extract_structured_data': WorkflowStep.EXTRACT,
    'analyze_job': WorkflowStep.ANALYZE,
    'extract_skills': WorkflowStep.ANALYZE,
    'score_job': WorkflowStep.SCORE,
    'generate_summary': WorkflowStep.SUMMARIZE,
    'persist_results': WorkflowStep.PERSIST,
    'completion_event': WorkflowStep.COMPLETE,
}

TOTAL_NODES = len(NODE_TO_STATUS)


class JobWorker(WorkerBase):
    """Concrete worker for job processing using LangGraph state management.

    Template Method: process() is defined by WorkerBase.
    This class implements _execute_pipeline() using the LangGraph job graph.
    No files are written to disk — all state is managed through LangGraph state.
    Workflow progress is emitted via WebSocket events through the broadcaster.
    """

    def __init__(self, pending_repo, process_mgr, temp_mgr, provider_runner, broadcaster,
                 job_repository=None, llm_service=None):
        super().__init__(pending_repo, process_mgr, temp_mgr, provider_runner, broadcaster)
        self._job_repo = job_repository
        self._llm = llm_service
        self._graph = None

    @property
    def table(self) -> str:
        return 'pending_jobs'

    @property
    def pipeline_steps(self) -> list:
        return []

    def _reset_steps(self, pid: int) -> None:
        self._pending_repo.update_status(pid, 'processing', workflow_log='[]')

    def _get_graph(self):
        if self._graph is None:
            builder = build_job_processing_graph()
            self._graph = builder.compile()
        return self._graph

    def _update_node_status(self, pid: int, node_name: str) -> None:
        """Update the pending_jobs status based on which workflow node is executing."""
        status = NODE_TO_STATUS.get(node_name)
        step = NODE_TO_STEP.get(node_name)
        if status:
            self._pending_repo.update_status(
                pid, status,
                current_node=node_name,
            )
        if step:
            self._log(pid, step.value, f'Starting: {step.label}')

        node_names = list(NODE_TO_STATUS.keys())
        node_index = node_names.index(node_name) if node_name in node_names else 0
        progress_pct = round((node_index + 1) / len(node_names) * 100, 1)
        step_label = step.label if step else node_name
        self._progress(pid, 'processing', node_name, progress_pct, step_label)

    def _execute_pipeline(self, pid: int, item: dict) -> Dict[str, Any]:
        url = item.get('url', '')
        notes = json.loads(item.get('notes') or '[]')
        links = json.loads(item.get('links') or '[]')
        source = item.get('source', 'cli')

        self._log(pid, 'fetch', f'Processing {url[:60] if url else "notes/links"}...')

        context = {
            "job_id": str(pid),
            "url": url,
            "notes": notes,
            "links": links,
            "source": source,
        }

        # Set initial status to processing
        self._pending_repo.update_status(pid, JobStatus.PROCESSING, current_node='load_context')
        self._progress(pid, 'processing', 'load_context', 0.0, 'Starting')

        initial = create_initial_state(
            input=url or "",
            context=context,
        )

        graph = self._get_graph()

        # Use streaming to get node-level progress updates
        if graph.backend == 'sequential':
            result = graph.invoke(initial)
            progress = result.get("progress", {})
            completed = progress.get("completed_nodes", [])
            for node_name in completed:
                self._update_node_status(pid, node_name)
        else:
            progress_callback = lambda node: self._update_node_status(pid, node)
            result = graph.invoke(initial)
            progress = result.get("progress", {})
            completed = progress.get("completed_nodes", [])
            for node_name in completed:
                self._update_node_status(pid, node_name)

        errors = result.get("errors", [])
        failure_details_ = result.get("failure_details", [])
        if errors:
            formatted = " | ".join(errors)
            for err in errors:
                self._log(pid, 'error', err)
            details_json = json.dumps(failure_details_, indent=2) if failure_details_ else "[]"
            self._pending_repo.update_fields(pid, "pending_jobs", failure_details=details_json)
            raise RuntimeError(formatted)

        metadata = result.get("metadata", {})
        persistence = metadata.get("persistence", {})
        if persistence.get("success"):
            job_id = persistence.get("job_id")
            company = persistence.get("company", "")
            self._log(pid, 'save', f'Saved job {job_id} to DB')
            return {'id': job_id, 'company': company}

        self._log(pid, 'error', 'Persistence did not complete successfully')
        raise RuntimeError("Job processing failed to persist results")
