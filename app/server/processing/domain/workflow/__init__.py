"""Workflow domain models for the processing bounded context.

Strongly typed Pydantic models that flow through LangGraph workflows:

- JobSource
- FetchedContent
- ExtractedContent
- JobData
- JobProcessingContext
- ContextValidationResult
- JobProcessingState
"""

from processing.domain.workflow.source import JobSource, SourceType
from processing.domain.workflow.fetched_content import FetchedContent
from processing.domain.workflow.extracted_content import ExtractedContent
from processing.domain.workflow.job_data import JobData
from processing.domain.workflow.job_processing_context import JobProcessingContext
from processing.domain.workflow.validation_result import ContextValidationResult
from processing.domain.workflow.job_processing_state import JobProcessingState

__all__ = [
    "JobSource",
    "SourceType",
    "FetchedContent",
    "ExtractedContent",
    "JobData",
    "JobProcessingContext",
    "ContextValidationResult",
    "JobProcessingState",
]
