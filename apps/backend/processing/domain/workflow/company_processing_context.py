"""CompanyProcessingContext — the final prepared context for a Company.

This object becomes the input for the company analysis phase (single combined
LLM call). It must not contain any LLM integration itself.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from processing.domain.workflow.company_data import CompanyData
from processing.domain.workflow.extracted_content import ExtractedContent
from processing.domain.workflow.source import JobSource


class CompanyProcessingContext(BaseModel):
    company_id: str
    company: CompanyData | None = None
    sources: list[JobSource] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    extracted_contents: list[ExtractedContent] = Field(default_factory=list)
    combined_text: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
