"""
Company processing worker — extends WorkerBase with Template Method.

Handles the full company processing pipeline:
fetch -> extract -> analyze -> save -> done

SOLID: SRP, OCP, LSP, DIP
"""

from __future__ import annotations

import json
import os
from typing import Dict, Any, Optional

from shared.infrastructure.process.worker_base import WorkerBase
from shared.infrastructure.process.models import CompanyPipelineStep


class CompanyWorker(WorkerBase):
    """Concrete worker for company processing."""

    def __init__(self, pending_repo, process_mgr, temp_mgr, provider_runner, broadcaster):
        super().__init__(pending_repo, process_mgr, temp_mgr, provider_runner, broadcaster)

    @property
    def table(self) -> str:
        return 'pending_companies'

    @property
    def pipeline_steps(self) -> list:
        return [step.value for step in CompanyPipelineStep]

    def _execute_pipeline(self, pid: int, item: dict) -> Dict[str, Any]:
        """Execute the company processing pipeline."""

        # Step 1: Fetch
        self._start_step(pid, 'step_fetch')
        raw_content = self._step_fetch(pid, item)
        if raw_content is None:
            return None
        self._mark_step(pid, 'step_fetch')

        if self._is_cancelled(pid):
            return None

        # Step 2: Extract
        self._start_step(pid, 'step_extract')
        company_data = self._step_extract(pid, raw_content)
        if company_data is None:
            return None
        self._mark_step(pid, 'step_extract')

        if self._is_cancelled(pid):
            return None

        # Step 3: Analyze
        self._start_step(pid, 'step_analyze')
        intelligence = self._step_analyze(pid, company_data)
        if intelligence is None:
            return None
        self._mark_step(pid, 'step_analyze')

        if self._is_cancelled(pid):
            return None

        # Step 4: Save
        self._start_step(pid, 'step_save')
        result = self._step_save(pid, company_data, intelligence, raw_content)
        self._mark_step(pid, 'step_save')

        return result

    def _step_fetch(self, pid: int, item: dict) -> Optional[str]:
        """Fetch company content from URLs and notes."""
        self._log(pid, 'fetch', 'Processing sources...')

        notes_raw = item.get('notes', '[]')
        try:
            notes = json.loads(notes_raw) if isinstance(notes_raw, str) else notes_raw
        except (json.JSONDecodeError, TypeError):
            notes = []

        if not notes:
            input_text = item.get('input_text', '')
            note_type = 'url' if input_text.startswith('http') else 'text'
            notes = [{"type": note_type, "content": input_text}]

        all_parts = []
        for note in notes:
            ntype = note.get('type', 'text')
            content = note.get('content', '').strip()
            if not content:
                continue
            if ntype == 'url' or content.startswith('http'):
                try:
                    from companies.infrastructure.workers.company_worker import _fetch_url
                    fetched = _fetch_url(content)
                    all_parts.append(f"[SOURCE: {content}]\n{fetched}")
                except Exception as e:
                    self._log(pid, 'fetch', f'Failed to fetch: {e}')
            else:
                all_parts.append(f"[NOTE]\n{content}")

        raw_content = '\n\n'.join(all_parts)
        if not raw_content.strip():
            raise RuntimeError("No content to process")
        return raw_content[:8000]

    def _step_extract(self, pid: int, raw_content: str) -> Optional[dict]:
        """Extract structured company data via LLM."""
        self._log(pid, 'extract', 'Extracting company information...')
        from companies.infrastructure.workers.company_worker import _extract_company_info
        return _extract_company_info(raw_content, 'multi_note', pid)

    def _step_analyze(self, pid: int, company_data: dict) -> Optional[dict]:
        """Generate intelligence analysis via LLM."""
        company_type = company_data.get('company_type', 'UNKNOWN')
        self._log(pid, 'analyze', f'Analyzing company ({company_type})...')
        from companies.infrastructure.workers.company_worker import _analyze_company
        return _analyze_company(company_data, 0, company_type=company_type)

    def _step_save(self, pid: int, company_data: dict,
                   intelligence: dict, raw_content: str) -> Optional[dict]:
        """Save company and intelligence to DB."""
        self._log(pid, 'save', 'Saving to database...')
        from companies.infrastructure.workers.company_worker import _save_company
        company_id = _save_company(company_data, intelligence, raw_content)
        self._log(pid, 'save', f'Saved company #{company_id}: {company_data.get("name", "Unknown")}')
        return {'company_id': company_id, 'name': company_data.get('name')}
