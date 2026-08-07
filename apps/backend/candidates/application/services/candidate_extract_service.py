"""CandidateExtractService — one structured LLM call per source document, plus
the deterministic merge that folds every extracted source into the canonical
candidate profile.

Flow (per the candidate_processing workflow):

    adapter fetch → candidate.extract (LLM + validate + retry once)
        → merge into current profile (core + all children)
        → CandidateProfileVersion snapshot (v1, v2, ...)
        → source row marked processed

The service owns two entry points used by the workflow nodes:

- ``extract(content)`` — pure: runs the LLM for a single source and returns the
  mapped payload. Never persists the profile.
- ``merge_and_persist(extracted)`` — the single persistence path: merges all
  extracted payloads, writes core + children + a version snapshot and records
  the sources as processed.

All AI calls go through LLMService (rule #1). Domain events are emitted through
the CandidateEventPublisher port (in-memory collector by default — EDD is
incremental, no pub/sub yet).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from ai.infrastructure.service import get_llm_service
from pydantic import ValidationError

from candidates.application.adapters.base import CandidateSourceAdapter, SourceContent
from candidates.application.services.candidate_extract_prompt import (
    CANDIDATE_EXTRACT_PROMPT_VERSION,
    CANDIDATE_EXTRACT_SCHEMA_VERSION,
    build_candidate_extract_output_schema,
    build_candidate_extract_prompt,
)
from candidates.application.services.candidate_extract_validation import (
    CandidateExtractOutput,
)
from candidates.domain.event_publisher import CandidateEventPublisher, InMemoryEventCollector
from candidates.domain.events import (
    CandidateMergeCompleted,
    CandidateProfileCreated,
    CandidateProfileUpdated,
    CandidateSkillInferred,
    CandidateSourceAdded,
    CandidateSourceSkipped,
    CandidateSourceUpdated,
    CandidateVersionCreated,
)
from candidates.domain.services.profile_merge_service import (
    CHILD_KINDS,
    CORE_FIELDS,
    ProfileMergeService,
)

SKILL_ORIGIN_EXPLICIT = "explicit"


class CandidateExtractionError(Exception):
    """Raised when candidate.extract fails (unparseable / schema-invalid)."""


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _coerce_payload(content: Any) -> dict[str, Any]:
    if isinstance(content, dict):
        return content
    if isinstance(content, str):
        try:
            parsed = json.loads(content)
            return parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


def _is_json_parse_error(exc: Exception) -> bool:
    msg = str(exc)
    return "Failed to parse" in msg and "JSON output" in msg


def _format_validation_error(exc: ValidationError) -> str:
    first = exc.errors()[0]
    loc = ".".join(str(part) for part in first.get("loc", ())) or "payload"
    return f"invalid field '{loc}': {first.get('msg', 'invalid value')}"


_RETRY_SHORTEN_HINT = (
    "\n\nIMPORTANT: Your previous attempt was cut off or did not match the required schema. "
    "Respond again with a SHORTER, COMPLETE JSON object matching the schema exactly: keep "
    "summary to at most 40 words, list at most 15 skills and at most 8 experiences. Include "
    "all required fields: profile, skills, experiences, projects, educations, certificates, "
    "interests, languages. Never truncate the JSON — every string and bracket must be closed."
)


class CandidateExtractService:
    """Extract and merge structured candidate profiles from source documents."""

    def __init__(
        self,
        profile_repo: Any,
        source_repo: Any,
        skill_repo: Any,
        llm: Any | None = None,
        event_publisher: CandidateEventPublisher | None = None,
        merge_service: ProfileMergeService | None = None,
    ):
        self._profile_repo = profile_repo
        self._source_repo = source_repo
        self._skill_repo = skill_repo
        self._llm = llm
        self.event_publisher = event_publisher or InMemoryEventCollector()
        self._merge_service = merge_service or ProfileMergeService()

    def process(self, adapter: CandidateSourceAdapter) -> dict[str, Any]:
        """Fetch a source via ``adapter`` and extract/persist it."""
        content = adapter.fetch()
        if content is None:
            return {"source_type": adapter.source_type, "status": "skipped", "reason": "no_content"}
        return self.extract_and_store(content)

    def extract_and_store(self, content: SourceContent) -> dict[str, Any]:
        """Single-source convenience wrapper (Phase-100 contract): extract then
        merge. The workflow uses ``extract`` + ``merge_and_persist`` directly."""
        result = self.extract(content)
        source_type = result.get("source_type")
        version = result.get("version")
        if result["status"] == "skipped":
            return {
                "source_type": source_type,
                "version": version,
                "status": "skipped",
                "reason": result["reason"],
            }
        summary = self.merge_and_persist([result])
        return {
            "source_type": source_type,
            "version": version,
            "status": "processed",
            "profile_id": summary["profile_id"],
            "skill_count": summary["skill_count"],
            "prompt_version": result["prompt_version"],
            "schema_version": result["schema_version"],
        }

    # ── Phase 101: split entry points ─────────────────────────────

    def extract(self, content: SourceContent) -> dict[str, Any]:
        """Run candidate.extract for a single source content. Pure (no profile
        writes). Returns either ``{"status": "skipped", reason, ...}`` or
        ``{"status": "extracted", payload, source_type, version, ...}``. Raises
        CandidateExtractionError on LLM/schema failure (source row marked failed
        for audit)."""
        source_type = content.source_type
        version = content.version
        raw_text = content.raw_text or ""

        existing_profile = self._profile_repo.get_current_profile()
        profile = self._profile_repo.get_or_create_current()
        profile_id = profile["id"]
        if existing_profile is None:
            self._emit(CandidateProfileCreated(aggregate_id=profile_id, profile_id=profile_id))

        existing = self._source_repo.get_by_type_and_version(profile_id, source_type, version)
        if existing and existing.get("status") == "processed":
            self._emit(
                CandidateSourceSkipped(
                    aggregate_id=profile_id,
                    profile_id=profile_id,
                    source_type=source_type,
                    version=version,
                    reason="already_processed",
                )
            )
            return {"status": "skipped", "reason": "already_processed", "source_type": source_type, "version": version}

        if not raw_text.strip():
            self._record_source(profile_id, source_type, version, status="failed", error="empty source text")
            self._emit(
                CandidateSourceSkipped(
                    aggregate_id=profile_id,
                    profile_id=profile_id,
                    source_type=source_type,
                    version=version,
                    reason="empty_text",
                )
            )
            return {"status": "skipped", "reason": "empty_text", "source_type": source_type, "version": version}

        prompt = build_candidate_extract_prompt(source_type, raw_text)
        schema = build_candidate_extract_output_schema()
        llm = self._llm or get_llm_service()

        payload, reason = self._obtain_valid_payload(llm, prompt, schema)
        if payload is None:
            self._record_source(profile_id, source_type, version, status="failed", error=reason)
            raise CandidateExtractionError(
                f"candidate.extract failed for {source_type} v{version}: {reason}"
            )

        children = self._map_children(payload, source_type, version)
        core = {field: payload.get("profile", {}).get(field, "") for field in CORE_FIELDS}
        flat_payload = dict(core)
        flat_payload.update(children)
        return {
            "status": "extracted",
            "source_type": source_type,
            "version": version,
            "payload": flat_payload,
            "prompt_version": CANDIDATE_EXTRACT_PROMPT_VERSION,
            "schema_version": CANDIDATE_EXTRACT_SCHEMA_VERSION,
        }

    def merge_and_persist(self, extracted: list[dict[str, Any]]) -> dict[str, Any]:
        """The single persistence path: fold all extracted payloads into the
        canonical profile, write core + children + a CandidateProfileVersion
        and record the sources as processed. Returns a merge summary including
        the emitted domain events."""
        extracted = [e for e in extracted if e.get("status") == "extracted"]
        if not extracted:
            return {"status": "noop", "profile_id": None, "version": None, "events": []}

        profile = self._profile_repo.get_or_create_current()
        profile_id = profile["id"]

        merged_profile = profile
        for entry in extracted:
            result = self._merge_service.merge(merged_profile, entry["payload"])
            merged_profile = result.merged
        diff = self._merge_service.diff(profile, merged_profile)

        versions = self._profile_repo.list_versions(profile_id)
        new_version = 1 if not versions else int(versions[0]["version"]) + 1

        core = {field: merged_profile.get(field, "") for field in CORE_FIELDS}
        core["version"] = new_version
        self._profile_repo.update_core(profile_id, core)
        for kind in CHILD_KINDS:
            self._profile_repo.replace_children(profile_id, kind, merged_profile.get(kind, []))

        source_versions = {e["source_type"]: e["version"] for e in extracted}
        change_summary = diff.to_change_summary()
        snapshot = {
            field: merged_profile.get(field, "") for field in CORE_FIELDS
        }
        for kind in CHILD_KINDS:
            snapshot[kind] = merged_profile.get(kind, [])
        self._profile_repo.create_version(profile_id, new_version, snapshot, source_versions, change_summary)

        for entry in extracted:
            self._record_source(profile_id, entry["source_type"], entry["version"], status="processed")

        events = self._collect_events(profile_id, diff, extracted, new_version)
        self.event_publisher.publish_all(events)
        return {
            "status": "merged",
            "profile_id": profile_id,
            "version": new_version,
            "source_versions": source_versions,
            "change_summary": change_summary,
            "source_types": [e["source_type"] for e in extracted],
            "skill_count": len(merged_profile.get("skills", [])),
            "events": [ev.event_type for ev in events],
        }

    # ── LLM call (validate + retry once) ───────────────────────────

    def _obtain_valid_payload(
        self, llm: Any, prompt: str, schema: dict[str, Any]
    ) -> tuple[dict[str, Any] | None, str]:
        """Run the LLM (with one retry) until the response validates."""
        first_reason = ""
        resp = None
        try:
            resp = llm.generate_structured(prompt, schema=schema, timeout=240)
        except Exception as e:  # noqa: BLE001 — provider errors vary
            if not _is_json_parse_error(e):
                return None, f"LLM call failed: {e}"
            first_reason = "the response was not parseable JSON"

        payload, reason = self._validate(resp)
        if payload is not None:
            return payload, ""

        try:
            resp = llm.generate_structured(prompt + _RETRY_SHORTEN_HINT, schema=schema, timeout=240)
        except Exception as e:  # noqa: BLE001
            return None, reason or first_reason or f"LLM retry failed: {e}"

        payload, retry_reason = self._validate(resp)
        if payload is not None:
            return payload, ""
        return None, reason or retry_reason or first_reason or "unparseable response"

    @staticmethod
    def _validate(resp: Any) -> tuple[dict[str, Any] | None, str]:
        if resp is None:
            return None, "the response was not parseable JSON"
        payload = _coerce_payload(resp.content)
        if not payload:
            return None, "the response was not parseable JSON"
        try:
            validated = CandidateExtractOutput.model_validate(payload)
            return validated.dump_payload(), ""
        except ValidationError as e:
            return None, _format_validation_error(e)

    # ── Mapping ────────────────────────────────────────────────────

    def _resolve_skills(
        self, payload_skills: list[dict[str, Any]], source_type: str, version: int
    ) -> list[dict[str, Any]]:
        """Resolve skill names to the canonical skills vocabulary (deduped)."""
        source_label = f"{source_type} v{version}"
        result: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in payload_skills:
            name = str(item.get("name") or "").strip()
            if not name or name.lower() in seen:
                continue
            seen.add(name.lower())
            skill_id = self._skill_repo.resolve_skill({"name": name, "source_type": "ai_generated"})
            result.append(
                {
                    "skill_id": skill_id,
                    "name": name,
                    "level": item.get("level") or 1,
                    "category": item.get("category") or "",
                    "origin": SKILL_ORIGIN_EXPLICIT,
                    "years_of_experience": item.get("years_of_experience"),
                    "last_used": item.get("last_used"),
                    "evidence": {
                        "sources": [source_label],
                        "confidence": item.get("confidence") or 0.0,
                        "notes": "",
                    },
                }
            )
        return result

    def _map_children(
        self, payload: dict[str, Any], source_type: str, version: int
    ) -> dict[str, list[dict[str, Any]]]:
        """Map validated payload sections to profile child dicts with evidence."""
        source_label = f"{source_type} v{version}"

        def evidence(item: dict[str, Any]) -> dict[str, Any]:
            return {
                "sources": [source_label],
                "confidence": item.get("confidence") or 0.0,
                "notes": "",
            }

        return {
            "skills": self._resolve_skills(payload.get("skills") or [], source_type, version),
            "experiences": [
                {
                    "company": e.get("company", ""),
                    "role": e.get("role", ""),
                    "start_date": e.get("start_date"),
                    "end_date": e.get("end_date"),
                    "duration_months": e.get("duration_months"),
                    "summary": e.get("summary", ""),
                    "highlights": list(e.get("highlights") or []),
                    "skills": list(e.get("skills") or []),
                    "evidence": evidence(e),
                }
                for e in payload.get("experiences") or []
            ],
            "projects": [
                {
                    "name": p.get("name", ""),
                    "description": p.get("description", ""),
                    "url": p.get("url", ""),
                    "role": p.get("role", ""),
                    "skills": list(p.get("skills") or []),
                    "start_date": p.get("start_date"),
                    "end_date": p.get("end_date"),
                    "evidence": evidence(p),
                }
                for p in payload.get("projects") or []
            ],
            "educations": [
                {
                    "institution": ed.get("institution", ""),
                    "degree": ed.get("degree", ""),
                    "field": ed.get("field", ""),
                    "start_date": ed.get("start_date"),
                    "end_date": ed.get("end_date"),
                    "evidence": evidence(ed),
                }
                for ed in payload.get("educations") or []
            ],
            "certificates": [
                {
                    "name": c.get("name", ""),
                    "issuer": c.get("issuer", ""),
                    "issue_date": c.get("issue_date"),
                    "credential_url": c.get("credential_url", ""),
                    "evidence": evidence(c),
                }
                for c in payload.get("certificates") or []
            ],
            "interests": [{"name": i.get("name", "")} for i in payload.get("interests") or []],
            "languages": [
                {"name": lang.get("name", ""), "proficiency": lang.get("proficiency", "")}
                for lang in payload.get("languages") or []
            ],
        }

    # ── Source bookkeeping ─────────────────────────────────────────

    def _record_source(
        self,
        profile_id: str,
        source_type: str,
        version: int,
        status: str,
        error: str = "",
    ) -> None:
        existing = self._source_repo.get_by_type_and_version(profile_id, source_type, version)
        data = {
            "status": status,
            "error": error,
            "processed_at": _now_iso() if status == "processed" else None,
        }
        if existing:
            self._source_repo.update(existing["id"], data)
            self._emit(
                CandidateSourceUpdated(
                    aggregate_id=profile_id,
                    profile_id=profile_id,
                    source_type=source_type,
                    version=version,
                    status=status,
                )
            )
        else:
            self._source_repo.create(
                {
                    "profile_id": profile_id,
                    "source_type": source_type,
                    "version": version,
                    "status": status,
                    "error": error,
                    "processed_at": data["processed_at"],
                }
            )
            self._emit(
                CandidateSourceAdded(
                    aggregate_id=profile_id,
                    profile_id=profile_id,
                    source_type=source_type,
                    version=version,
                )
            )

    # ── Events (EDD — in-memory collector) ────────────────────────

    def _collect_events(
        self,
        profile_id: str,
        diff: Any,
        extracted: list[dict[str, Any]],
        new_version: int,
    ) -> list[Any]:
        events: list[Any] = []
        if not diff.is_empty():
            events.append(CandidateProfileUpdated(aggregate_id=profile_id, profile_id=profile_id))
        for entry in extracted:
            events.append(
                CandidateMergeCompleted(
                    aggregate_id=profile_id,
                    profile_id=profile_id,
                    source_type=entry["source_type"],
                    version=entry["version"],
                )
            )
        events.append(
            CandidateVersionCreated(aggregate_id=profile_id, profile_id=profile_id, version=new_version)
        )
        skills_diff = diff.sections.get("skills")
        if skills_diff is not None:
            for item in skills_diff.added:
                confidence = _num(item.get("evidence", {}).get("confidence"))
                events.append(
                    CandidateSkillInferred(
                        aggregate_id=profile_id,
                        profile_id=profile_id,
                        skill_id=item.get("skill_id"),
                        skill_name=item.get("name", ""),
                        confidence=confidence,
                    )
                )
        return events

    def _emit(self, event: Any) -> None:
        try:
            self.event_publisher.publish(event)
        except Exception:  # noqa: BLE001 — best-effort publishing
            pass


def _num(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0
