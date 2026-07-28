"""Resume tools — wrap existing resume generation services.

SRP: Each tool handles one resume-related operation.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from shared.infrastructure.database.models.misc_models import ResumeModel
from .base import BaseTool, ToolResult


class GenerateResumeSectionTool(BaseTool):
    """Generates tailored resume content for a specific job."""

    def __init__(self, session: Session | None = None):
        self._session = session

    @property
    def name(self) -> str:
        return "generate_resume_section"

    @property
    def description(self) -> str:
        return "Generate a tailored resume section for a specific job posting"

    def run(self, **kwargs) -> ToolResult:
        job_data = kwargs.get("job_data")
        if not job_data:
            return ToolResult(success=False, error="job_data parameter is required")

        try:
            if self._session is None:
                from shared.infrastructure.database.session import get_session_sync
                self._session = get_session_sync()

            model = self._session.query(ResumeModel).filter(
                ResumeModel.id.like("original_%")
            ).order_by(ResumeModel.version.desc()).first()

            if model and model.raw_text:
                return ToolResult(
                    success=True,
                    data={
                        "resume_text": model.raw_text,
                        "job": job_data,
                    },
                )
            return ToolResult(success=False, error="No original resume found in database")
        except Exception as e:
            return ToolResult(success=False, error=f"Resume lookup failed: {e}")
