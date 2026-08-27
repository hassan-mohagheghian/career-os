"""Tests for CandidateExtractService merge/versioning and EDD event emission."""

from types import SimpleNamespace

import pytest

from candidates.application.adapters.base import SourceContent
from candidates.application.services.candidate_extract_service import (
    CandidateExtractService,
    CandidateExtractionError,
)


class FakeLLM:
    def __init__(self, contents):
        self._contents = list(contents)
        self.calls = 0

    def generate_structured(self, prompt, schema=None, timeout=None):
        self.calls += 1
        if not self._contents:
            raise RuntimeError("LLM unavailable")
        return SimpleNamespace(content=self._contents.pop(0))


class FakeProfileRepo:
    def __init__(self):
        self.current = None
        self.core = None
        self.children = {}
        self.versions = []

    def get_current_profile(self):
        if self.current is None:
            return None
        profile = dict(self.current)
        if self.versions:
            profile["version"] = self.versions[0]["version"]
        for kind, items in self.children.items():
            profile[kind] = list(items)
        return profile

    def get_or_create_current(self):
        if self.current is None:
            self.current = {"id": "profile-1", "candidate_id": "cand-1", "version": 1}
        return self.get_current_profile()

    def update_core(self, profile_id, data):
        self.core = {"profile_id": profile_id, **data}
        self.current.update(data)

    def replace_children(self, profile_id, kind, items):
        self.children[kind] = list(items)

    def create_version(self, profile_id, version, snapshot, source_versions, change_summary=""):
        self.versions.insert(
            0,
            {
                "profile_id": profile_id,
                "version": version,
                "snapshot": snapshot,
                "source_versions": source_versions,
                "change_summary": change_summary,
            },
        )
        return self.versions[0]

    def list_versions(self, profile_id):
        return [dict(v) for v in self.versions]


class FakeSourceRepo:
    def __init__(self):
        self.rows = {}

    def _key(self, profile_id, source_type, version):
        return (profile_id, source_type, version)

    def get_by_type_and_version(self, profile_id, source_type, version):
        return self.rows.get(self._key(profile_id, source_type, version))

    def create(self, data):
        key = self._key(data["profile_id"], data["source_type"], data["version"])
        self.rows[key] = {"id": f"src-{len(self.rows) + 1}", **data}

    def update(self, source_id, data):
        for key, row in self.rows.items():
            if row.get("id") == source_id:
                row.update(data)
                return row
        return None


class FakeSkillRepo:
    def __init__(self):
        self.ids = {}

    def resolve_skill(self, data):
        name = data["name"]
        if name not in self.ids:
            self.ids[name] = len(self.ids) + 1
        return self.ids[name]


def _payload(**profile_overrides):
    profile = {"name": "Hassan", "title": "Backend", "headline": "h", "summary": "s", "location": "Cairo"}
    profile.update(profile_overrides)
    return {
        "profile": profile,
        "skills": [{"name": "Python", "level": 5, "category": "language", "years_of_experience": 8, "confidence": 0.9}],
        "experiences": [{"company": "Acme", "role": "Backend", "confidence": 0.8}],
        "projects": [{"name": "CLI", "description": "d", "confidence": 0.7}],
        "educations": [{"institution": "CU", "degree": "BSc", "confidence": 0.9}],
        "certificates": [{"name": "AWS", "issuer": "Amazon", "confidence": 0.9}],
        "interests": [{"name": "Open Source"}],
        "languages": [{"name": "Arabic", "proficiency": "native"}],
    }


def _make_service(payloads, **kwargs):
    llm = FakeLLM(list(payloads))
    profile_repo = kwargs.pop("profile_repo", None) or FakeProfileRepo()
    service = CandidateExtractService(
        profile_repo=profile_repo,
        source_repo=kwargs.pop("source_repo", None) or FakeSourceRepo(),
        skill_repo=kwargs.pop("skill_repo", None) or FakeSkillRepo(),
        llm=llm,
        event_publisher=kwargs.pop("event_publisher", None),
    )
    return service, llm


def _content(source_type="resume", version=1, raw="raw text"):
    return SourceContent(source_type, raw, version)


class TestExtractPure:
    def test_extract_does_not_persist_profile(self):
        service, _ = _make_service([_payload()])
        result = service.extract(_content("resume", 2))

        assert result["status"] == "extracted"
        assert result["version"] == 2
        assert result["payload"]["name"] == "Hassan"
        assert service._profile_repo.children == {}
        assert service._profile_repo.versions == []

    def test_extract_reprocesses_already_processed_source(self):
        service, _ = _make_service([_payload()])
        service._source_repo.create(
            {"profile_id": "profile-1", "source_type": "resume", "version": 1, "status": "processed"}
        )
        result = service.extract(_content("resume", 1))
        assert result["status"] == "extracted"
        assert result["source_type"] == "resume"

    def test_extract_empty_text_marks_failed_and_skips(self):
        service, _ = _make_service([_payload()])
        result = service.extract(_content("linkedin", 3, raw="   "))
        assert result["status"] == "skipped"
        assert result["reason"] == "empty_text"
        row = service._source_repo.get_by_type_and_version("profile-1", "linkedin", 3)
        assert row["status"] == "failed"

    def test_extract_failure_raises_and_marks_source_failed(self):
        service, _ = _make_service(["not json at all"])
        with pytest.raises(CandidateExtractionError):
            service.extract(_content("resume", 1))
        row = service._source_repo.get_by_type_and_version("profile-1", "resume", 1)
        assert row is not None
        assert row["status"] == "failed"


class TestMergeAndPersist:
    def test_first_merge_creates_version_v1(self):
        service, _ = _make_service([_payload()])
        result = service.extract(_content("resume", 1))
        summary = service.merge_and_persist([result])

        assert summary["version"] == 1
        assert summary["profile_id"] == "profile-1"
        assert summary["source_versions"] == {"resume": 1}
        assert service._profile_repo.versions[0]["version"] == 1
        assert service._profile_repo.core["version"] == 1

    def test_second_merge_bumps_version_to_v2(self):
        service, _ = _make_service([_payload(), _payload(name="Hassan Updated")])
        first = service.extract(_content("resume", 1))
        service.merge_and_persist([first])
        second = service.extract(_content("linkedin", 1))
        summary = service.merge_and_persist([second])

        assert summary["version"] == 2
        assert service._profile_repo.versions[0]["version"] == 2
        assert service._profile_repo.core["name"] == "Hassan Updated"

    def test_merge_combines_sources_and_evidence(self):
        service, _ = _make_service([_payload(), _payload()])
        resume = service.extract(_content("resume", 1))
        linkedin = service.extract(_content("linkedin", 2))
        summary = service.merge_and_persist([resume, linkedin])

        assert summary["source_versions"] == {"resume": 1, "linkedin": 2}
        assert service._profile_repo.versions[0]["source_versions"] == {"resume": 1, "linkedin": 2}
        python = service._profile_repo.children["skills"][0]
        assert python["evidence"]["sources"] == ["resume v1", "linkedin v2"]
        assert service._profile_repo.versions[0]["snapshot"]["skills"][0]["evidence"]["sources"] == ["resume v1", "linkedin v2"]

    def test_merge_change_summary_reflects_diff(self):
        service, _ = _make_service([_payload(), _payload()])
        first = service.extract(_content("resume", 1))
        service.merge_and_persist([first])
        second = service.extract(_content("linkedin", 1))
        summary = service.merge_and_persist([second])

        assert summary["change_summary"]
        assert "linkedin" in service._profile_repo.versions[0]["source_versions"]

    def test_sources_recorded_processed(self):
        service, _ = _make_service([_payload()])
        result = service.extract(_content("resume", 4))
        service.merge_and_persist([result])
        row = service._source_repo.get_by_type_and_version("profile-1", "resume", 4)
        assert row["status"] == "processed"
        assert row["processed_at"]


class TestEventEmission:
    def test_merge_emits_core_event_set(self):
        service, _ = _make_service([_payload()])
        result = service.extract(_content("resume", 1))
        summary = service.merge_and_persist([result])

        # summary lists the merge-event set; the collector also carries the
        # source added/updated events emitted while recording source rows.
        for event_type in summary["events"]:
            assert any(e.event_type == event_type for e in service.event_publisher.events)
        types = {e.event_type for e in service.event_publisher.events}
        assert "candidate.profile.created" in types
        assert "candidate.merge.completed" in types
        assert "candidate.version.created" in types
        assert "candidate.source.added" in types
        assert "candidate.skill.inferred" in types
        assert "candidate.profile.updated" in types

    def test_skill_inferred_event_carries_skill(self):
        service, _ = _make_service([_payload()])
        result = service.extract(_content("resume", 1))
        service.merge_and_persist([result])

        inferred = [e for e in service.event_publisher.events if e.event_type == "candidate.skill.inferred"]
        assert len(inferred) == 1
        assert inferred[0].skill_name == "Python"
        assert inferred[0].skill_id == service._skill_repo.ids["Python"]

    def test_reprocess_extracts_from_already_processed_source(self):
        service, _ = _make_service([_payload(), _payload()])
        service._source_repo.create(
            {"profile_id": "profile-1", "source_type": "resume", "version": 1, "status": "processed"}
        )
        result = service.extract(_content("resume", 1))

        assert result["status"] == "extracted"
        assert result["source_type"] == "resume"
        assert result["version"] == 1
        assert "payload" in result
