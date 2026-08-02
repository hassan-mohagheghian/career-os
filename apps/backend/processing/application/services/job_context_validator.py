"""JobContextValidatorService — validates a JobProcessingContext.

A context is valid when at least one meaningful content source exists:

- at least one extracted content with non-empty clean text, or
- at least one non-empty note.

Invalid examples:
- no extracted content
- empty notes
- no usable source
"""

from __future__ import annotations

from processing.domain.workflow.job_processing_context import JobProcessingContext
from processing.domain.workflow.validation_result import ContextValidationResult


class JobContextValidatorService:
    def validate(self, context: JobProcessingContext) -> ContextValidationResult:
        reasons: list[str] = []

        meaningful_extracted = [
            c for c in context.extracted_contents if c.clean_text and c.clean_text.strip()
        ]
        meaningful_notes = [n for n in context.notes if n.strip()]

        if not meaningful_extracted:
            reasons.append("no extracted content")

        if not meaningful_notes:
            reasons.append("empty notes")

        if not context.sources:
            reasons.append("no usable source")

        valid = bool(meaningful_extracted or meaningful_notes) and bool(context.sources)

        return ContextValidationResult(valid=valid, reasons=reasons)
