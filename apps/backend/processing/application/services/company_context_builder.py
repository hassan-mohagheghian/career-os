"""CompanyContextBuilderService — builds the final CompanyProcessingContext.

Combines company information, extracted content, notes, and source metadata
into a single validated-by-construction object that later becomes the input
for the company analysis phase.
"""

from __future__ import annotations

from processing.domain.workflow.company_processing_context import CompanyProcessingContext
from processing.domain.workflow.company_processing_state import CompanyProcessingState


class CompanyContextBuilderService:
    def build(self, state: CompanyProcessingState) -> CompanyProcessingContext:
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

        return CompanyProcessingContext(
            company_id=state.company_id,
            company=state.company,
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
