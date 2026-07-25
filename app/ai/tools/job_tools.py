"""Job tools — wrap existing job processing services.

SRP: Each tool handles one job-related operation.
DIP: Tools import existing functions, not concrete implementations.
"""

from __future__ import annotations

import os
import sys
from typing import Optional

from .base import BaseTool, ToolResult

# Add server to path for imports
_server_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'server'))
if _server_dir not in sys.path:
    sys.path.insert(0, _server_dir)


class FetchJobTool(BaseTool):
    """Fetches job posting content from a URL.

    Wraps the existing _fetch_url() function from worker.py.
    """

    @property
    def name(self) -> str:
        return "fetch_job_url"

    @property
    def description(self) -> str:
        return "Fetch and clean job posting content from a URL"

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Job posting URL to fetch"},
            },
            "required": ["url"],
        }

    def run(self, **kwargs) -> ToolResult:
        url = kwargs.get("url")
        if not url:
            return ToolResult(success=False, error="url parameter is required")

        try:
            # Import from existing worker module
            from services.worker import _fetch_url
            content = _fetch_url(url)
            return ToolResult(
                success=True,
                data=content,
                metadata={"url": url, "length": len(content)},
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to fetch URL: {e}")


class ExtractJobDataTool(BaseTool):
    """Extracts structured data from job content.

    Wraps the existing _extract_all() function from worker.py.
    """

    @property
    def name(self) -> str:
        return "extract_job_data"

    @property
    def description(self) -> str:
        return "Extract structured job information from raw text content"

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Raw job text content"},
                "pid": {"type": "string", "description": "Processing ID for temp files"},
            },
            "required": ["content"],
        }

    def run(self, **kwargs) -> ToolResult:
        content = kwargs.get("content")
        if not content:
            return ToolResult(success=False, error="content parameter is required")

        pid = kwargs.get("pid", "ai_extract")

        try:
            from services.worker import _extract_all
            result = _extract_all(content, pid)
            if result:
                return ToolResult(
                    success=True,
                    data=result,
                    metadata={"valid": result.get("valid", False)},
                )
            return ToolResult(success=False, error="Extraction returned no result")
        except Exception as e:
            return ToolResult(success=False, error=f"Extraction failed: {e}")


class ScoreJobTool(BaseTool):
    """Scores a job using the existing analysis pipeline.

    Wraps the existing scoring logic from worker.py.
    """

    @property
    def name(self) -> str:
        return "score_job"

    @property
    def description(self) -> str:
        return "Score and analyze a job for fit and success probability"

    def run(self, **kwargs) -> ToolResult:
        job_data = kwargs.get("job_data")
        if not job_data:
            return ToolResult(success=False, error="job_data parameter is required")

        try:
            from services.worker import normalize_score, calculate_overall_score
            score = normalize_score(job_data.get("score"))
            return ToolResult(
                success=True,
                data={"score": score, "job_data": job_data},
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Scoring failed: {e}")
