"""JobContextBuilderService — builds the final JobProcessingContext.

Combines job information, extracted content, notes, and source metadata into
a single validated-by-construction object that later becomes the input for
LLM analysis, scoring, and career guidance.
"""

from __future__ import annotations

from processing.domain.workflow.extracted_content import ExtractedContent
from processing.domain.workflow.job_processing_context import JobProcessingContext
from processing.domain.workflow.job_processing_state import JobProcessingState


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
            parts.append(content.clean_text.strip())

        combined_text = "\n\n".join(parts)

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
            },
        )

    @staticmethod
    def _meaningful(content: ExtractedContent) -> bool:
        return bool(content.clean_text and content.clean_text.strip())
