from __future__ import annotations

import json
from typing import Any, Optional

from .base import BaseTool, ToolResult
from .web import CompanyFetchTool, MultiSourceFetchTool


class FetchCompanyTool(BaseTool):
    def __init__(self):
        self._fetcher = CompanyFetchTool()

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


class FetchMultiSourceCompanyTool(BaseTool):
    def __init__(self):
        self._fetcher = MultiSourceFetchTool(max_total_length=8000)

    @property
    def name(self) -> str:
        return "fetch_multi_source_company"

    @property
    def description(self) -> str:
        return "Fetch company content from multiple sources (URL + notes + links)"

    def run(self, **kwargs) -> ToolResult:
        return self._fetcher.run(**{k: v for k, v in kwargs.items() if k in ("url", "notes", "links")})


class ExtractCompanyTool(BaseTool):
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

        try:
            from shared.infrastructure.ai.compat import get_llm_service
            from shared.infrastructure.prompts.loader import load_prompt

            prompt = load_prompt(
                "company/company_extract",
                content=content[:8000],
                input_type="multi_note",
            )

            llm = get_llm_service()
            resp = llm.generate_structured(
                prompt,
                timeout=180,
            )
            result = json.loads(resp.content)
            return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(success=False, error=f"Extraction failed: {e}")


class AnalyzeCompanyTool(BaseTool):
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

        company_type = kwargs.get("company_type", "UNKNOWN")

        try:
            from shared.infrastructure.ai.compat import get_llm_service
            from shared.infrastructure.prompts.loader import load_prompt
            from career.infrastructure.repositories.sa_preference_repository import SQLAlchemyPreferenceRepository
            from dependencies import get_session_sync

            session = get_session_sync()
            try:
                pref_repo = SQLAlchemyPreferenceRepository(session)
                scope_map = {
                    "PRODUCT_COMPANY": "COMPANY_PRODUCT",
                    "RECRUITING_AGENCY": "COMPANY_RECRUITING",
                    "STAFFING_COMPANY": "COMPANY_RECRUITING",
                    "CONSULTING_COMPANY": "COMPANY_PRODUCT",
                    "UNKNOWN": "COMPANY_PRODUCT",
                }
                entity_scope = scope_map.get(company_type, "COMPANY_PRODUCT")
                rows = pref_repo.get_enabled_by_scopes(["SHARED", entity_scope])
            finally:
                session.close()

            if not rows:
                rules = "No scoring rules set."
            else:
                lines = []
                current_cat = None
                for r in rows:
                    cat = r["category"]
                    if cat != current_cat:
                        current_cat = cat
                        lines.append(f"\n── {cat.upper()} {'─' * (35 - len(cat))}")
                    weight = r.get("score_weight") or r["priority"]
                    lines.append(f"  #{r['priority']:>3}  {r['key']} (weight:{weight}): {r['value']}")
                rules = "\n".join(lines)

            prompt = load_prompt(
                "company/company_analyze",
                company_data=json.dumps(company_data, ensure_ascii=False)[:4000],
                company_type=company_type,
                rules=rules,
            )

            llm = get_llm_service()
            resp = llm.generate_structured(
                prompt,
                timeout=300,
            )
            result = json.loads(resp.content)
            return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(success=False, error=f"Analysis failed: {e}")
