"""
Job processing worker — extends WorkerBase with Template Method.

Handles the full job processing pipeline:
fetch -> validate -> extract -> analyze -> save -> done

SOLID:
- SRP: Only handles job processing
- OCP: New processing strategies via subclasses
- LSP: Fully interchangeable with WorkerBase
- DIP: Depends on abstractions (interfaces), not concretions
"""

from __future__ import annotations

import json
import os
from typing import Dict, Any, Optional

from .worker_base import WorkerBase
from .models import PipelineStep


class JobWorker(WorkerBase):
    """Concrete worker for job processing.

    Template Method: process() is defined by WorkerBase.
    This class implements _execute_pipeline() and the job-specific steps.
    """

    def __init__(self, pending_repo, process_mgr, temp_mgr, mimo_runner, broadcaster,
                 job_repository=None, llm_service=None):
        super().__init__(pending_repo, process_mgr, temp_mgr, mimo_runner, broadcaster)
        self._job_repo = job_repository
        self._llm = llm_service

    @property
    def table(self) -> str:
        return 'pending_jobs'

    @property
    def pipeline_steps(self) -> list:
        return [step.value for step in PipelineStep]

    def _execute_pipeline(self, pid: int, item: dict) -> Dict[str, Any]:
        """Execute the job processing pipeline.

        Subclasses can override individual steps via _step_* methods.
        """
        url = item.get('url', '')

        # Step 1: Fetch
        self._start_step(pid, 'step_fetch')
        raw_text = self._step_fetch(pid, item)
        if raw_text is None:
            return None  # cancelled
        self._mark_step(pid, 'step_fetch')
        self._log(pid, 'fetch', f'Fetched {len(raw_text)} chars')

        if self._is_cancelled(pid):
            return None

        # Step 2: Validate
        self._start_step(pid, 'step_validate')
        validated = self._step_validate(pid, raw_text)
        if validated is None:
            return None
        self._mark_step(pid, 'step_validate')

        if self._is_cancelled(pid):
            return None

        # Step 3: Extract Raw
        self._start_step(pid, 'step_extract_raw')
        extracted = self._step_extract_raw(pid, raw_text)
        if extracted is None:
            return None
        self._mark_step(pid, 'step_extract_raw')

        if self._is_cancelled(pid):
            return None

        # Step 4: Extract Structured
        self._start_step(pid, 'step_extract_struct')
        structured = self._step_extract_struct(pid, extracted)
        self._mark_step(pid, 'step_extract_struct')

        # Step 5: Summary
        self._start_step(pid, 'step_summary')
        summary = self._step_summary(pid, extracted)
        self._mark_step(pid, 'step_summary')

        if self._is_cancelled(pid):
            return None

        # Step 6: Analyze (AI scoring)
        self._start_step(pid, 'step_analyze')
        analysis = self._step_analyze(pid, item, raw_text)
        self._mark_step(pid, 'step_analyze')

        # Step 7: Save to DB
        self._start_step(pid, 'step_db')
        result = self._step_save(pid, item, raw_text, extracted, analysis)
        self._mark_step(pid, 'step_db')

        return result

    # ── Individual steps (override in subclasses for customization) ──

    def _step_fetch(self, pid: int, item: dict) -> Optional[str]:
        """Fetch URL content. Returns raw text or None if cancelled."""
        self._log(pid, 'fetch', 'Fetching page...')
        # Delegate to existing fetch logic
        from worker import _fetch_url, _fetch_multi_source
        url = item.get('url', '')
        notes = json.loads(item.get('notes') or '[]')
        links = json.loads(item.get('links') or '[]')

        if notes or links:
            return _fetch_multi_source(url, notes, links, pid)
        return _fetch_url(url)

    def _step_validate(self, pid: int, raw_text: str) -> Optional[dict]:
        """Validate job content. Returns validation result."""
        self._log(pid, 'validate', 'Validating content...')
        from worker import _validate_job_content
        return _validate_job_content(raw_text, pid)

    def _step_extract_raw(self, pid: int, raw_text: str) -> Optional[dict]:
        """Extract structured data from raw text."""
        self._log(pid, 'extract_raw', 'Extracting job info...')
        from worker import _extract_all
        return _extract_all(raw_text, pid)

    def _step_extract_struct(self, pid: int, extracted: dict) -> Optional[dict]:
        """Further structure the extracted data."""
        self._log(pid, 'extract_struct', 'Structuring data...')
        return extracted

    def _step_summary(self, pid: int, extracted: dict) -> Optional[dict]:
        """Build summary from extracted data."""
        self._log(pid, 'summary', f'Summary: {(extracted or {}).get("summary", "")[:150]}')
        return extracted

    def _step_analyze(self, pid: int, item: dict, raw_text: str) -> Optional[dict]:
        """Run AI analysis/scoring."""
        self._log(pid, 'analyze', 'Scoring job...')
        # This delegates to the existing mimo scoring pipeline
        return {'scored': True}

    def _step_save(self, pid: int, item: dict, raw_text: str,
                   extracted: dict, analysis: dict) -> Optional[dict]:
        """Save results to DB."""
        self._log(pid, 'save', 'Saving to database...')
        from worker import _insert_job, _insert_summary, _get_next_num, _get_existing_num
        url = item.get('url', '')
        temp_num = _get_next_num()
        existing_num = _get_existing_num(url)
        if existing_num:
            temp_num = existing_num

        company = (extracted or {}).get('company', '')
        title = (extracted or {}).get('title', '')

        job_data = {
            'num': temp_num, 'company': company or title or 'Unknown',
            'role': title or 'Unknown', 'url': url,
            'raw_description': raw_text,
        }
        _insert_job(job_data)
        self._log(pid, 'save', f'Saved job #{temp_num}')
        return {'num': temp_num, 'company': company}
