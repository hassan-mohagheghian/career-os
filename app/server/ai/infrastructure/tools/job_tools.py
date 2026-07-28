from __future__ import annotations

import json
from typing import Any, Optional

from .base import BaseTool, ToolResult
from .web import WebFetchTool, MultiSourceFetchTool


class FetchJobTool(BaseTool):
    def __init__(self):
        self._fetcher = WebFetchTool()

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

        page = self._fetcher.fetch_direct(url)

        if page.is_ok:
            return ToolResult(
                success=True,
                data=page.plain_text,
                metadata={"url": url, "length": len(page.plain_text), "cache_hit": page.cache_hit},
            )
        else:
            return ToolResult(
                success=False,
                error=page.error.message if page.error else "Fetch failed",
                metadata={"url": url},
            )


class FetchMultiSourceJobTool(BaseTool):
    def __init__(self):
        self._fetcher = MultiSourceFetchTool()

    @property
    def name(self) -> str:
        return "fetch_multi_source_job"

    @property
    def description(self) -> str:
        return "Fetch job content from multiple sources (URL + notes + links)"

    def run(self, **kwargs) -> ToolResult:
        return self._fetcher.run(**{k: v for k, v in kwargs.items() if k in ("url", "notes", "links")})


class ExtractJobDataTool(BaseTool):
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
            },
            "required": ["content"],
        }

    def run(self, **kwargs) -> ToolResult:
        content = kwargs.get("content")
        if not content:
            return ToolResult(success=False, error="content parameter is required")

        try:
            from shared.infrastructure.ai.compat import get_llm_service
            from shared.infrastructure.prompts.loader import load_prompt

            prompt = load_prompt(
                "job_processing/step3_extract_raw",
                content=content[:5000],
                output_file="/tmp/ai_extract_result.json",
            )

            llm = get_llm_service()
            resp = llm.generate_structured(
                prompt,
                timeout=90,
            )
            result = json.loads(resp.content)
            return ToolResult(
                success=True,
                data=result,
                metadata={"valid": result.get("valid", False)},
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Extraction failed: {e}")


class ScoreJobTool(BaseTool):
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
            from jobs.infrastructure.workers.worker import normalize_score
            score = normalize_score(job_data.get("score"))
            return ToolResult(
                success=True,
                data={"score": score, "job_data": job_data},
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Scoring failed: {e}")
