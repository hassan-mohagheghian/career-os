"""Tests for CandidateExtractService orchestration (adapters → LLM → persist)."""

from types import SimpleNamespace

import pytest

from candidates.application.services.candidate_extract_prompt import (
    CANDIDATE_EXTRACT_PROMPT_VERSION,
    CANDIDATE_EXTRACT_SCHEMA_VERSION,
)
from candidates.application.services.candidate_extract_service import (
    CandidateExtractService,
    CandidateExtractionError,
)
from candidates.application.adapters.base import SourceContent


class FakeLLM:
    def __init__(self, content=None, fail_first=False):
        self.content = content
        self.fail_first = fail_first
        self.calls = 0

    def generate_structured(self, prompt, schema=None, timeout=None):
        self.calls += 1
        if self.fail_first and self.calls == 1:
            raise RuntimeError("Failed to parse model JSON output")
        if self.content is None:
            raise RuntimeError("LLM unavailable")
        return SimpleNamespace(content=self.content)


class FakeProfileRepo:
    def __init__(self):
        self.current = {"id": "profile-1", "candidate_id": "cand-1", "version": 1}
        self.core = None
        self.children = {}
        self.versions = []

    def get_current_profile(self):
        profile = dict(self.current)
        if self.versions:
            profile["version"] = self.versions[0]["version"]
        for kind, items in self.children.items():
            profile[kind] = list(items)
        return profile

    def get_or_create_current(self):
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
        self.updated = []

    def _key(self, profile_id, source_type, version):
        return (profile_id, source_type, version)

    def get_by_type_and_version(self, profile_id, source_type, version):
        return self.rows.get(self._key(profile_id, source_type, version))

    def create(self, data):
        key = self._key(data["profile_id"], data["source_type"], data["version"])
        self.rows[key] = {"id": f"src-{len(self.rows) + 1}", **data}

    def update(self, source_id, data):
        self.updated.append((source_id, data))
        for key, row in self.rows.items():
            if row.get("id") == source_id:
                row.update(data)
                return row
        return None


class FakeSkillRepo:
    def __init__(self):
        self.ids = {}
        self.calls = []

    def resolve_skill(self, data):
        name = data["name"]
        self.calls.append(name)
        if name not in self.ids:
            self.ids[name] = len(self.ids) + 1
        return self.ids[name]


class FakeAdapter:
    source_type = "resume"

    def __init__(self, content=None):
        self._content = content

    def fetch(self):
        return self._content


def _valid_llm_payload():
    return {
        "profile": {"name": "Hassan", "title": "Backend Engineer", "headline": "h", "summary": "s", "location": "Cairo"},
        "skills": [
            {"name": "Python", "level": 5, "category": "language", "years_of_experience": 8, "last_used": "2025", "confidence": 0.98},
            {"name": "Python", "level": 4, "category": "language", "confidence": 0.5},
            {"name": "Go", "level": 4, "category": "language", "confidence": 0.9},
        ],
        "experiences": [{"company": "Acme", "role": "Backend", "start_date": "2020", "end_date": "2024", "duration_months": 48, "summary": "s", "highlights": ["h"], "skills": ["Python"], "confidence": 0.9}],
        "projects": [{"name": "CLI", "description": "d", "url": "u", "role": "author", "skills": ["Go"], "start_date": "2023", "end_date": "2023", "confidence": 0.8}],
        "educations": [{"institution": "CU", "degree": "BSc", "field": "CS", "start_date": "2010", "end_date": "2014", "confidence": 0.9}],
        "certificates": [{"name": "AWS", "issuer": "Amazon", "issue_date": "2022", "credential_url": "u", "confidence": 0.9}],
        "interests": [{"name": "Open Source"}],
        "languages": [{"name": "Arabic", "proficiency": "native"}],
    }


def _make_service(llm_content=None, **kwargs):
    llm = kwargs.pop("llm", None) or FakeLLM(content=llm_content)
    return (
        CandidateExtractService(
            profile_repo=FakeProfileRepo(),
            source_repo=FakeSourceRepo(),
            skill_repo=FakeSkillRepo(),
            llm=llm,
        ),
        llm,
    )


class TestProcessSkipped:
    def test_no_content_skipped(self):
        service, _ = _make_service()
        result = service.process(FakeAdapter(content=None))
        assert result["status"] == "skipped"
        assert result["reason"] == "no_content"

    def test_already_processed_skipped(self):
        service, _ = _make_service(llm_content=None)
        service._source_repo.create(
            {"profile_id": "profile-1", "source_type": "resume", "version": 2, "status": "processed"}
        )
        result = service.process(FakeAdapter(content=SourceContent("resume", "text", 2)))
        assert result["status"] == "skipped"
        assert result["reason"] == "already_processed"


class TestProcessHappyPath:
    def test_persists_core_and_children(self):
        service, llm = _make_service(llm_content=_valid_llm_payload())
        result = service.process(FakeAdapter(content=SourceContent("resume", "raw text", 2)))

        assert result["status"] == "processed"
        assert result["version"] == 2
        assert result["profile_id"] == "profile-1"
        assert result["prompt_version"] == CANDIDATE_EXTRACT_PROMPT_VERSION
        assert result["schema_version"] == CANDIDATE_EXTRACT_SCHEMA_VERSION
        assert llm.calls == 1

        assert service._profile_repo.core["name"] == "Hassan"
        assert service._profile_repo.core["title"] == "Backend Engineer"
        assert service._profile_repo.core["location"] == "Cairo"

        for kind in ("skills", "experiences", "projects", "educations", "certificates", "interests", "languages"):
            assert kind in service._profile_repo.children

    def test_skills_deduped_and_resolved(self):
        service, _ = _make_service(llm_content=_valid_llm_payload())
        service.process(FakeAdapter(content=SourceContent("resume", "raw", 1)))

        skills = service._profile_repo.children["skills"]
        assert [s["name"] for s in skills] == ["Python", "Go"]
        assert skills[0]["skill_id"] == service._skill_repo.ids["Python"]
        assert skills[0]["origin"] == "explicit"
        assert skills[0]["evidence"]["confidence"] == pytest.approx(0.98)

    def test_skills_carry_evidence(self):
        service, _ = _make_service(llm_content=_valid_llm_payload())
        service.process(FakeAdapter(content=SourceContent("resume", "raw", 3)))
        skill = service._profile_repo.children["skills"][0]
        assert skill["evidence"]["sources"] == ["resume v3"]
        assert skill["evidence"]["confidence"] == pytest.approx(0.98)

    def test_source_row_created_processed(self):
        service, _ = _make_service(llm_content=_valid_llm_payload())
        service.process(FakeAdapter(content=SourceContent("linkedin", "raw", 1)))
        row = service._source_repo.get_by_type_and_version("profile-1", "linkedin", 1)
        assert row["status"] == "processed"
        assert row["processed_at"]

    def test_all_children_carried(self):
        service, _ = _make_service(llm_content=_valid_llm_payload())
        service.process(FakeAdapter(content=SourceContent("resume", "raw", 1)))
        children = service._profile_repo.children
        assert children["experiences"][0]["company"] == "Acme"
        assert children["experiences"][0]["evidence"]["sources"] == ["resume v1"]
        assert children["projects"][0]["name"] == "CLI"
        assert children["educations"][0]["institution"] == "CU"
        assert children["certificates"][0]["name"] == "AWS"
        assert children["interests"][0]["name"] == "Open Source"
        assert children["languages"][0]["proficiency"] == "native"


class TestProcessLLMFailures:
    def test_retries_once_on_parse_error(self):
        service, llm = _make_service(llm_content=_valid_llm_payload(), llm=FakeLLM(content=_valid_llm_payload(), fail_first=True))
        result = service.process(FakeAdapter(content=SourceContent("resume", "raw", 1)))
        assert result["status"] == "processed"
        assert llm.calls == 2

    def test_garbage_fails_and_marks_source_failed(self):
        service, _ = _make_service(llm_content="not json at all")
        with pytest.raises(CandidateExtractionError):
            service.process(FakeAdapter(content=SourceContent("resume", "raw", 1)))
        row = service._source_repo.get_by_type_and_version("profile-1", "resume", 1)
        assert row is not None
        assert row["status"] == "failed"
        assert row["error"]

    def test_invalid_schema_fails(self):
        service, _ = _make_service(llm_content={"skills": "not-a-list", "experiences": [], "projects": [], "educations": [], "certificates": [], "interests": [], "languages": [], "profile": {}})
        with pytest.raises(CandidateExtractionError):
            service.process(FakeAdapter(content=SourceContent("resume", "raw", 1)))
