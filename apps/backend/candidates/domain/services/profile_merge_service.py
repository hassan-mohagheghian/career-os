"""ProfileMergeService — deterministic merge of extracted source payloads into
the canonical candidate profile.

The merge is the single persistence primitive of the Candidate Profile domain:
each source version is extracted independently, then all extractions are merged
into the current profile in one operation that produces a new
CandidateProfileVersion snapshot.

Merging is deterministic and idempotent. Every section has a natural key:

- skills          → skill_id (fallback: normalized name)
- experiences     → (company, role)
- projects        → name
- educations      → (institution, degree)
- certificates    → name
- interests       → name
- languages       → name

Core fields (name/title/headline/summary/location) follow a simple rule: an
incoming non-empty value wins. Evidence is always merged (union of sources,
max confidence) so provenance is preserved across merges.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

CORE_FIELDS = ("name", "title", "headline", "summary", "location")
CHILD_KINDS = (
    "skills",
    "experiences",
    "projects",
    "educations",
    "certificates",
    "interests",
    "languages",
)

# keys that never participate in field-level merging / comparison
_METADATA_KEYS = frozenset({"id", "profile_id", "created_at", "updated_at"})
# keys dropped when copying a current item into a merge (rebuilt by the repo)
_DROP_KEYS = frozenset({"id", "profile_id", "created_at", "updated_at"})


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _num(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _merge_evidence(
    current: dict[str, Any] | None, incoming: dict[str, Any] | None
) -> dict[str, Any]:
    cur = current or {}
    inc = incoming or {}
    sources = list(
        dict.fromkeys(list(cur.get("sources") or []) + list(inc.get("sources") or []))
    )
    confidence = max(_num(cur.get("confidence")), _num(inc.get("confidence")))
    return {
        "sources": sources,
        "confidence": confidence,
        "notes": inc.get("notes") or cur.get("notes") or "",
    }


def _merge_generic(current: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """Merge an incoming item into a current one: incoming non-empty wins."""
    merged = {k: v for k, v in current.items() if k not in _DROP_KEYS}
    for key, value in incoming.items():
        if key in _DROP_KEYS:
            continue
        if key == "evidence":
            merged["evidence"] = _merge_evidence(current.get("evidence"), incoming.get("evidence"))
        elif value is not None and value != "" and value != []:
            merged[key] = value
    return merged


def _merge_skill(current: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """Skill merge: max level/confidence/years, union evidence, filled extras."""
    merged = {k: v for k, v in current.items() if k not in _DROP_KEYS}
    merged["evidence"] = _merge_evidence(current.get("evidence"), incoming.get("evidence"))
    merged["level"] = int(max(_num(current.get("level")), _num(incoming.get("level"))))
    years = max(
        _num(current.get("years_of_experience")), _num(incoming.get("years_of_experience"))
    )
    merged["years_of_experience"] = years or None
    for fname in ("category", "last_used", "name"):
        if incoming.get(fname):
            merged[fname] = incoming[fname]
    origins = {o for o in (current.get("origin"), incoming.get("origin")) if o}
    merged["origin"] = "explicit" if "explicit" in origins else ("inferred" if origins else "explicit")
    return merged


@dataclass
class SectionDiff:
    """Per-section merge outcome: items added, updated or removed."""

    added: list[dict[str, Any]] = field(default_factory=list)
    updated: list[dict[str, Any]] = field(default_factory=list)
    removed: list[dict[str, Any]] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not (self.added or self.updated or self.removed)


@dataclass
class ProfileDiff:
    """Full profile merge outcome: core field changes + per-section diffs."""

    core: dict[str, dict[str, Any]] = field(default_factory=dict)
    sections: dict[str, SectionDiff] = field(default_factory=dict)

    def is_empty(self) -> bool:
        return not self.core and all(s.is_empty() for s in self.sections.values())

    def to_change_summary(self) -> str:
        parts: list[str] = []
        for fname, change in self.core.items():
            parts.append(f"{fname} updated")
        for kind, diff in self.sections.items():
            if diff.added:
                parts.append(f"{len(diff.added)} {kind} added")
            if diff.updated:
                parts.append(f"{len(diff.updated)} {kind} updated")
            if diff.removed:
                parts.append(f"{len(diff.removed)} {kind} removed")
        return "; ".join(parts) if parts else "no changes"

    def to_dict(self) -> dict[str, Any]:
        return {
            "core": dict(self.core),
            "sections": {
                kind: {
                    "added": diff.added,
                    "updated": diff.updated,
                    "removed": diff.removed,
                }
                for kind, diff in self.sections.items()
            },
        }


@dataclass
class MergeResult:
    """Outcome of merging one or more extracted payloads into a profile."""

    merged: dict[str, Any]
    diff: ProfileDiff


class ProfileMergeService:
    """Pure domain service implementing the merge natural-key rules."""

    _MERGE_POLICY: dict[str, Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]] = {
        "skills": _merge_skill,
    }

    def merge(
        self,
        current: dict[str, Any] | None,
        incoming: dict[str, Any],
    ) -> MergeResult:
        base = dict(current or {})
        core_diff: dict[str, dict[str, Any]] = {}
        merged_core = self._merge_core(base, incoming, core_diff)

        section_diff: dict[str, SectionDiff] = {}
        merged_sections: dict[str, list[dict[str, Any]]] = {}
        for kind in CHILD_KINDS:
            diff = SectionDiff()
            merged_sections[kind] = self._merge_section(
                kind, base.get(kind, []), incoming.get(kind, []), diff
            )
            section_diff[kind] = diff

        merged = dict(base)
        merged.update(merged_core)
        merged.update(merged_sections)
        return MergeResult(merged=merged, diff=ProfileDiff(core=core_diff, sections=section_diff))

    def diff(
        self,
        before: dict[str, Any] | None,
        after: dict[str, Any] | None,
    ) -> ProfileDiff:
        """Compute the diff between two full profile snapshots (used for the
        change summary of a multi-source merge)."""
        before = before or {}
        after = after or {}
        core_diff: dict[str, dict[str, Any]] = {}
        for fname in CORE_FIELDS:
            old = before.get(fname, "")
            new = after.get(fname, "")
            if new != old:
                core_diff[fname] = {"old": old, "new": new}

        section_diff: dict[str, SectionDiff] = {}
        for kind in CHILD_KINDS:
            section_diff[kind] = self._diff_section(kind, before.get(kind, []), after.get(kind, []))
        return ProfileDiff(core=core_diff, sections=section_diff)

    def _diff_section(
        self,
        kind: str,
        before_items: list[dict[str, Any]],
        after_items: list[dict[str, Any]],
    ) -> SectionDiff:
        key_fn = _key_fns[kind]
        before_by_key = {key_fn(item): item for item in before_items}
        after_by_key = {key_fn(item): item for item in after_items}
        diff = SectionDiff()
        for key, item in after_by_key.items():
            if key not in before_by_key:
                diff.added.append(dict(item))
        for key, item in before_by_key.items():
            if key not in after_by_key:
                diff.removed.append(dict(item))
        for key, after_item in after_by_key.items():
            before_item = before_by_key.get(key)
            if before_item is not None and _item_changed(before_item, _strip(after_item)):
                diff.updated.append(dict(after_item))
        return diff

    # ── core ──────────────────────────────────────────────────────

    @staticmethod
    def _merge_core(
        base: dict[str, Any],
        incoming: dict[str, Any],
        diff: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        updated: dict[str, Any] = {}
        for fname in CORE_FIELDS:
            old = base.get(fname, "")
            new = incoming.get(fname, "")
            if new and new != old:
                updated[fname] = new
                diff[fname] = {"old": old, "new": new}
        return updated

    # ── sections ──────────────────────────────────────────────────

    def _merge_section(
        self,
        kind: str,
        current_items: list[dict[str, Any]],
        incoming_items: list[dict[str, Any]],
        diff: SectionDiff,
    ) -> list[dict[str, Any]]:
        policy = self._MERGE_POLICY.get(kind, _merge_generic)
        key_fn = _key_fns[kind]
        current_by_key = {key_fn(item): item for item in current_items}
        incoming_by_key = {key_fn(item): item for item in incoming_items}

        merged: list[dict[str, Any]] = []
        merged_keys: set[str] = set()

        for key, incoming_item in incoming_by_key.items():
            current_item = current_by_key.get(key)
            if current_item is None:
                merged.append(dict(incoming_item))
                diff.added.append(dict(incoming_item))
            else:
                merged_item = policy(current_item, incoming_item)
                if _item_changed(current_item, merged_item):
                    diff.updated.append(merged_item)
                merged.append(merged_item)
            merged_keys.add(key)

        for key, current_item in current_by_key.items():
            if key not in merged_keys:
                diff.removed.append(dict(current_item))
                merged.append(dict(current_item))

        return merged


def _item_changed(current: dict[str, Any], merged: dict[str, Any]) -> bool:
    """True when a merge actually changed the current item."""
    return _strip(current) != merged


def _strip(item: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in item.items() if k not in _DROP_KEYS}


def _key_skills(item: dict[str, Any]) -> str:
    skill_id = item.get("skill_id")
    if skill_id is not None and str(skill_id):
        return f"skill:{skill_id}"
    return f"name:{_norm(item.get('name'))}"


def _key_experiences(item: dict[str, Any]) -> str:
    return f"{_norm(item.get('company'))}|{_norm(item.get('role'))}"


def _key_projects(item: dict[str, Any]) -> str:
    return f"name:{_norm(item.get('name'))}"


def _key_educations(item: dict[str, Any]) -> str:
    return f"{_norm(item.get('institution'))}|{_norm(item.get('degree'))}"


def _key_certificates(item: dict[str, Any]) -> str:
    return f"name:{_norm(item.get('name'))}"


def _key_interests(item: dict[str, Any]) -> str:
    return f"name:{_norm(item.get('name'))}"


def _key_languages(item: dict[str, Any]) -> str:
    return f"name:{_norm(item.get('name'))}"


_key_fns: dict[str, Callable[[dict[str, Any]], str]] = {
    "skills": _key_skills,
    "experiences": _key_experiences,
    "projects": _key_projects,
    "educations": _key_educations,
    "certificates": _key_certificates,
    "interests": _key_interests,
    "languages": _key_languages,
}

__all__ = [
    "CORE_FIELDS",
    "CHILD_KINDS",
    "ProfileMergeService",
    "ProfileDiff",
    "SectionDiff",
    "MergeResult",
]
