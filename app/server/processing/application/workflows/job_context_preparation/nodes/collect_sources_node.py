"""CollectSourcesNode — collects all available sources and normalizes them
into JobSource models.

Sources:
- Primary Job URL
- Additional URLs (job links + URL-type notes)
- Job notes (kept as plain text for the context)
"""

from __future__ import annotations

import json

from processing.domain.workflow.job_processing_state import JobProcessingState
from processing.domain.workflow.source import JobSource, SourceType


class CollectSourcesNode:
    def __call__(self, state: JobProcessingState) -> JobProcessingState:
        sources: list[JobSource] = []
        notes: list[str] = []

        job = state.job
        if job is None:
            state.errors.append("No job data available to collect sources from")
            state.sources = []
            state.notes = []
            return state

        if job.url:
            sources.append(JobSource(url=job.url, type=SourceType.PRIMARY_URL))

        self._collect_notes(job, sources, notes)
        self._collect_links(job, sources)

        state.sources = sources
        state.notes = notes
        return state

    def _collect_notes(self, job, sources: list[JobSource], notes: list[str]) -> None:
        for note in self._parse_json_list(job.notes_raw):
            if isinstance(note, dict):
                note_type = note.get("type", "text")
                content = note.get("content", "")
                if not content:
                    continue
                if note_type == "url" and content.startswith(("http://", "https://")):
                    self._add_url_source(sources, content.strip())
                else:
                    notes.append(str(content))
            elif isinstance(note, str) and note.strip():
                notes.append(note.strip())

    def _collect_links(self, job, sources: list[JobSource]) -> None:
        for link in self._parse_json_list(job.links_raw):
            url = link.get("url", "") if isinstance(link, dict) else str(link)
            if url and url.startswith(("http://", "https://")):
                self._add_url_source(sources, url.strip())

    @staticmethod
    def _parse_json_list(raw: str) -> list:
        try:
            parsed = json.loads(raw or "[]")
            return parsed if isinstance(parsed, list) else []
        except (ValueError, TypeError):
            return []

    @staticmethod
    def _add_url_source(sources: list[JobSource], url: str) -> None:
        if all(s.url != url for s in sources):
            sources.append(JobSource(url=url, type=SourceType.ADDITIONAL_URL))
