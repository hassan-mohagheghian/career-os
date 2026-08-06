"""PersistSkillsNode — writes the analyzed job's skills into the skills table.

For each skill in the analysis result:
  1. Resolve to a skill row (exact name match → alias match → create as
     ai_generated) via `repo.resolve_skill`.
  2. Upsert a `skill_mentions` link (source_type="job") so demand can be
     counted without duplicating skill rows.

Re-processing a job is idempotent: mentions for that job are deleted first,
then re-inserted.
"""

from __future__ import annotations

from typing import Any

from processing.application.workflows import progress_ops
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.job_processing_state import JobProcessingState

NODE_ID = "persist_skills"

SOURCE_TYPE = "job"


class PersistSkillsNode:
    def __init__(
        self,
        skill_repo: Any,
        event_publisher: Any | None = None,
    ):
        self._skills = skill_repo
        self._events = event_publisher

    def __call__(self, state: JobProcessingState) -> JobProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        try:
            result = state.analysis_result or {}
            skills = result.get("skills") or []
            job_id = state.job_id

            self._skills.delete_mentions_for_source(SOURCE_TYPE, job_id)
            for skill in skills:
                name = str(skill.get("name") or "").strip()
                if not name:
                    continue
                skill_id = self._skills.resolve_skill({
                    "name": name,
                    "category": skill.get("category") or "",
                    "level": _level(skill.get("level")),
                    "confidence": skill.get("level") or 0,
                    "evidence": str(skill.get("evidence") or ""),
                    "source_type": "ai_generated",
                })
                self._skills.upsert_mentions(
                    skill_id,
                    SOURCE_TYPE,
                    job_id,
                    status=str(skill.get("status") or ""),
                    evidence=str(skill.get("evidence") or "[]"),
                )
        except Exception as e:
            state.errors.append(f"[{NODE_ID}] Failed to persist skills: {e}")
            state.status = ExecutionStatus.FAILED
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state


def _level(value: Any) -> int:
    """Convert the 0-100 LLM level to the skill row's 1-10 scale."""
    if isinstance(value, bool):
        return 1
    try:
        num = float(value)
    except (TypeError, ValueError):
        return 1
    if num <= 0:
        return 1
    return max(1, min(10, round(num / 10)))
