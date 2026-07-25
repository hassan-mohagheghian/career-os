"""Company tools — wrap existing company processing services.

SRP: Each tool handles one company-related operation.
"""

from __future__ import annotations

from .base import BaseTool, ToolResult


class FetchCompanyTool(BaseTool):
    """Fetches company page content from a URL."""

    @property
    def name(self) -> str:
        return "fetch_company_url"

    @property
    def description(self) -> str:
        return "Fetch and clean company page content from a URL"

    def run(self, **kwargs) -> ToolResult:
        url = kwargs.get("url")
        if not url:
            return ToolResult(success=False, error="url parameter is required")

        try:
            from services.company_worker import _fetch_url
            content = _fetch_url(url)
            return ToolResult(
                success=True,
                data=content,
                metadata={"url": url, "length": len(content)},
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to fetch URL: {e}")


class ExtractCompanyTool(BaseTool):
    """Extracts structured company data from content."""

    @property
    def name(self) -> str:
        return "extract_company_data"

    @property
    def description(self) -> str:
        return "Extract structured company information from raw text"

    def run(self, **kwargs) -> ToolResult:
        content = kwargs.get("content")
        if not content:
            return ToolResult(success=False, error="content parameter is required")

        pid = kwargs.get("pid", "ai_extract")

        try:
            from services.company_worker import _extract_company_info
            result = _extract_company_info(content, "multi_note", pid)
            if result:
                return ToolResult(success=True, data=result)
            return ToolResult(success=False, error="Extraction returned no result")
        except Exception as e:
            return ToolResult(success=False, error=f"Extraction failed: {e}")


class AnalyzeCompanyTool(BaseTool):
    """Generates intelligence analysis for a company."""

    @property
    def name(self) -> str:
        return "analyze_company"

    @property
    def description(self) -> str:
        return "Generate comprehensive company intelligence analysis"

    def run(self, **kwargs) -> ToolResult:
        company_data = kwargs.get("company_data")
        if not company_data:
            return ToolResult(success=False, error="company_data parameter is required")

        pid = kwargs.get("pid", "ai_analyze")
        company_type = kwargs.get("company_type", "UNKNOWN")

        try:
            from services.company_worker import _analyze_company
            result = _analyze_company(company_data, pid, company_type=company_type)
            if result:
                return ToolResult(success=True, data=result)
            return ToolResult(success=False, error="Analysis returned no result")
        except Exception as e:
            return ToolResult(success=False, error=f"Analysis failed: {e}")
