"""JobProcessingContext — the final prepared context for a Job.

This object becomes the input for future analysis stages (LLM analysis,
scoring, career guidance, recommendations). It must not contain any LLM
integration itself.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from processing.domain.workflow.extracted_content import ExtractedContent
from processing.domain.workflow.job_data import JobData
from processing.domain.workflow.source import JobSource


class JobProcessingContext(BaseModel):
    job_id: str
    job: JobData | None = None
    sources: list[JobSource] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    extracted_contents: list[ExtractedContent] = Field(default_factory=list)
    combined_text: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
