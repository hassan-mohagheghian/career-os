"""Candidates bounded context — application layer.

Contains source adapters (reading raw profile documents from ``job.resumes``)
and the structured extraction service (single ``candidate.extract`` LLM call).
"""

from candidates.application.services.candidate_extract_service import (
    CandidateExtractService,
    CandidateExtractionError,
)

__all__ = ["CandidateExtractService", "CandidateExtractionError"]
