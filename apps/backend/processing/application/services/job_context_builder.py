"""JobContextBuilderService — builds the final JobProcessingContext.

Combines job information, extracted content, notes, and source metadata into
a single validated-by-construction object that later becomes the input for
LLM analysis, scoring, and career guidance.
"""

from __future__ import annotations

import re

from processing.application.services.context_budget import (
    MAX_COMBINED_CHARS,
    MAX_SOURCE_CHARS,
    trim_text,
)
from processing.domain.workflow.extracted_content import ExtractedContent
from processing.domain.workflow.job_processing_context import JobProcessingContext
from processing.domain.workflow.job_processing_state import JobProcessingState

_EASY_APPLY_RE = re.compile(r"\beasy\s+apply\b", re.IGNORECASE)
_EBP_PARAM_RE = re.compile(r"[?&]eBP=", re.IGNORECASE)


class JobContextBuilderService:
    def build(self, state: JobProcessingState) -> JobProcessingContext:
        notes = list(state.notes)
        extracted = [
            c for c in state.extracted_contents
            if c.clean_text and c.clean_text.strip()
        ]

        parts: list[str] = []
        for note in notes:
            if note.strip():
                parts.append(f"[NOTE] {note.strip()}")
        for content in extracted:
            parts.append(trim_text(content.clean_text, max_chars=MAX_SOURCE_CHARS))

        combined_text = trim_text("\n\n".join(parts), max_chars=MAX_COMBINED_CHARS)

        job_url = state.job.url if state.job else None
        easy_apply = self._detect_easy_apply(extracted, job_url)

        return JobProcessingContext(
            job_id=state.job_id,
            job=state.job,
            sources=list(state.sources),
            notes=notes,
            extracted_contents=extracted,
            combined_text=combined_text,
            metadata={
                "extracted_count": len(extracted),
                "source_count": len(state.sources),
                "note_count": len(notes),
                "easy_apply": easy_apply,
            },
        )

    @staticmethod
    def _detect_easy_apply(
        extracted: list[ExtractedContent], job_url: str | None = None
    ) -> bool:
        for content in extracted:
            if content.clean_text and _EASY_APPLY_RE.search(content.clean_text):
                return True
        if job_url and _EBP_PARAM_RE.search(job_url):
            return True
        return False

    @staticmethod
    def _meaningful(content: ExtractedContent) -> bool:
        return bool(content.clean_text and content.clean_text.strip())
