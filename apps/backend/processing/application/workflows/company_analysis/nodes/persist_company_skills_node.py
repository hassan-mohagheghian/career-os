"""PersistCompanySkillsNode — writes the analyzed company's skills into the skills table.

For each skill in the analysis result extraction:
  1. Resolve to a skill row (exact name match → alias match → create as
     ai_generated) via `repo.resolve_skill`.
  2. Upsert a `skill_mentions` link (source_type="company") so demand can be
     counted without duplicating skill rows.

Re-processing a company is idempotent: mentions for that company are deleted
first, then re-inserted.
"""

from __future__ import annotations

from typing import Any

from processing.application.workflows import progress_ops
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.company_processing_state import CompanyProcessingState

NODE_ID = "persist_company_skills"

SOURCE_TYPE = "company"


class PersistCompanySkillsNode:
    def __init__(
        self,
        skill_repo: Any,
        event_publisher: Any | None = None,
    ):
        self._skills = skill_repo
        self._events = event_publisher

    def __call__(self, state: CompanyProcessingState) -> CompanyProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        if self._skills is None:
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state
        try:
            result = state.analysis_result or {}
            skills = (result.get("extraction") or {}).get("skills") or []
            company_id = state.company_id

            self._skills.delete_mentions_for_source(SOURCE_TYPE, company_id)
            for skill in skills:
                name = str(skill.get("name") or "").strip()
                if not name:
                    continue
                skill_id = self._skills.resolve_skill({
                    "name": name,
                    "category": str(skill.get("category") or ""),
                    "level": 1,
                    "confidence": 1,
                    "evidence": str(skill.get("evidence") or ""),
                    "source_type": "ai_generated",
                })
                self._skills.upsert_mentions(
                    skill_id,
                    SOURCE_TYPE,
                    company_id,
                    status="",
                    evidence=str(skill.get("evidence") or "[]"),
                )
        except Exception as e:
            state.errors.append(f"[{NODE_ID}] Failed to persist skills: {e}")
            state.status = ExecutionStatus.FAILED
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
