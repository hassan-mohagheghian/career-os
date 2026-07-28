"""Resume tools — wrap existing resume generation services.

SRP: Each tool handles one resume-related operation.
"""

from __future__ import annotations

from .base import BaseTool, ToolResult


class GenerateResumeSectionTool(BaseTool):
    """Generates tailored resume content for a specific job."""

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
            from core.db import get_db
            conn = get_db()
            resume_row = conn.execute(
                "SELECT raw_text FROM resumes WHERE id LIKE 'original_%' ORDER BY version DESC LIMIT 1"
            ).fetchone()
            conn.close()

            if resume_row and resume_row[0]:
                return ToolResult(
                    success=True,
                    data={
                        "resume_text": resume_row[0],
                        "job": job_data,
                    },
                )
            return ToolResult(success=False, error="No original resume found in database")
        except Exception as e:
            return ToolResult(success=False, error=f"Resume lookup failed: {e}")
