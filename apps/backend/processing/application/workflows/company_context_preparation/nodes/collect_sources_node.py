"""CollectSourcesNode — collects all available company sources and normalizes
them into JobSource models.

Sources:
- Primary Company Website
- Additional URLs (company links + URL-type notes)
- Company notes (kept as plain text for the context)
"""

from __future__ import annotations

import json
from typing import Any

from processing.application.workflows import progress_ops
from processing.domain.workflow.company_processing_state import CompanyProcessingState
from processing.domain.workflow.source import JobSource, SourceType

NODE_ID = "collect_sources"


class CollectSourcesNode:
    def __init__(self, event_publisher: Any | None = None):
        self._events = event_publisher

    def __call__(self, state: CompanyProcessingState) -> CompanyProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        sources: list[JobSource] = []
        notes: list[str] = []

        company = state.company
        if company is None:
            state.errors.append(f"[{NODE_ID}] No company data available to collect sources from")
            state.sources = []
            state.notes = []
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state

        if company.website:
            sources.append(JobSource(url=company.website, type=SourceType.PRIMARY_URL))

        self._collect_notes(company, sources, notes)
        self._collect_links(company, sources)

        state.sources = sources
        state.notes = notes
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state

    def _collect_notes(self, company, sources: list[JobSource], notes: list[str]) -> None:
        for note in self._parse_json_list(company.notes_raw):
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

    def _collect_links(self, company, sources: list[JobSource]) -> None:
        for link in self._parse_json_list(company.links_raw):
            url = link.get("url", "") if isinstance(link, dict) else str(link)
            if url and url.startswith(("http://", "https://")):
                self._add_url_source(sources, url.strip())

    @staticmethod
    def _parse_json_list(raw: str | None) -> list:
        """Parse a stored notes/links value into a list of items.

        Tolerates every storage format produced by the system over time:
        JSON arrays, JSON scalars, and plain non-JSON strings.
        """
        if raw is None or str(raw).strip() == "":
            return []
        try:
            parsed = json.loads(raw)
        except (ValueError, TypeError):
            return [str(raw).strip()]
        return parsed if isinstance(parsed, list) else [parsed]

    @staticmethod
    def _add_url_source(sources: list[JobSource], url: str) -> None:
        if all(s.url != url for s in sources):
            sources.append(JobSource(url=url, type=SourceType.ADDITIONAL_URL))
