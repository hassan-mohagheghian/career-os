"""Tests for ProfileMergeService — deterministic natural-key merge rules."""

from candidates.domain.services.profile_merge_service import (
    ProfileMergeService,
)


def _empty_profile():
    return {
        "id": "p1",
        "candidate_id": "c1",
        "version": 1,
        "name": "",
        "title": "",
        "headline": "",
        "summary": "",
        "location": "",
        "skills": [],
        "experiences": [],
        "projects": [],
        "educations": [],
        "certificates": [],
        "interests": [],
        "languages": [],
    }


def _skill(name, skill_id=None, level=1, confidence=0.5, years=None, category="", evidence_sources=None):
    return {
        "skill_id": skill_id,
        "name": name,
        "level": level,
        "category": category,
        "origin": "explicit",
        "years_of_experience": years,
        "last_used": None,
        "evidence": {
            "sources": evidence_sources or [f"{name.lower()} v1"],
            "confidence": confidence,
            "notes": "",
        },
    }


def _experience(company, role, summary=""):
    return {"company": company, "role": role, "start_date": None, "end_date": None, "summary": summary, "evidence": {"sources": ["resume v1"], "confidence": 0.5, "notes": ""}}


class TestMergeCore:
    def test_incoming_non_empty_wins(self):
        current = _empty_profile()
        current["name"] = "Old Name"
        incoming = _empty_profile()
        incoming["name"] = "New Name"

        result = ProfileMergeService().merge(current, incoming)
        assert result.merged["name"] == "New Name"
        assert result.diff.core["name"] == {"old": "Old Name", "new": "New Name"}

    def test_empty_incoming_preserves_current(self):
        current = _empty_profile()
        current["name"] = "Keep Me"
        incoming = _empty_profile()

        result = ProfileMergeService().merge(current, incoming)
        assert result.merged["name"] == "Keep Me"
        assert result.diff.core == {}

    def test_identical_core_no_diff(self):
        current = _empty_profile()
        current["title"] = "Engineer"
        incoming = _empty_profile()
        incoming["title"] = "Engineer"

        result = ProfileMergeService().merge(current, incoming)
        assert result.diff.core == {}


class TestMergeSkills:
    def test_skills_keyed_by_skill_id_dedup(self):
        current = _empty_profile()
        current["skills"] = [_skill("Python", skill_id=1, level=3, confidence=0.6, evidence_sources=["resume v1"])]
        incoming = _empty_profile()
        incoming["skills"] = [_skill("Python", skill_id=1, level=5, confidence=0.9, years=8, evidence_sources=["linkedin v1"])]

        result = ProfileMergeService().merge(current, incoming)
        skills = result.merged["skills"]
        assert len(skills) == 1
        assert skills[0]["level"] == 5
        assert skills[0]["evidence"]["confidence"] == 0.9
        assert skills[0]["years_of_experience"] == 8
        assert skills[0]["evidence"]["sources"] == ["resume v1", "linkedin v1"]

    def test_new_skill_added(self):
        current = _empty_profile()
        incoming = _empty_profile()
        incoming["skills"] = [_skill("Go", skill_id=9, confidence=0.8)]

        result = ProfileMergeService().merge(current, incoming)
        assert len(result.merged["skills"]) == 1
        assert result.diff.sections["skills"].added[0]["name"] == "Go"

    def test_removed_skill_when_incoming_drops_it(self):
        current = _empty_profile()
        current["skills"] = [_skill("Python", skill_id=1)]
        incoming = _empty_profile()

        result = ProfileMergeService().merge(current, incoming)
        assert result.diff.sections["skills"].removed[0]["name"] == "Python"
        assert result.merged["skills"] == [current["skills"][0]]


class TestMergeOtherSections:
    def test_experiences_keyed_by_company_role(self):
        current = _empty_profile()
        current["experiences"] = [_experience("Acme", "Backend", summary="old")]
        incoming = _empty_profile()
        incoming["experiences"] = [_experience("Acme", "Backend", summary="new summary")]

        result = ProfileMergeService().merge(current, incoming)
        merged = result.merged["experiences"]
        assert len(merged) == 1
        assert merged[0]["summary"] == "new summary"
        assert result.diff.sections["experiences"].updated[0]["company"] == "Acme"

    def test_projects_by_name(self):
        current = _empty_profile()
        current["projects"] = [{"name": "CLI", "description": "old"}]
        incoming = _empty_profile()
        incoming["projects"] = [{"name": "CLI", "description": "new"}]

        result = ProfileMergeService().merge(current, incoming)
        assert result.merged["projects"][0]["description"] == "new"

    def test_educations_by_institution_degree(self):
        current = _empty_profile()
        current["educations"] = [{"institution": "CU", "degree": "BSc", "field": "CS"}]
        incoming = _empty_profile()
        incoming["educations"] = [{"institution": "CU", "degree": "BSc", "field": "Maths"}]

        result = ProfileMergeService().merge(current, incoming)
        assert result.merged["educations"][0]["field"] == "Maths"

    def test_certificates_by_name(self):
        current = _empty_profile()
        current["certificates"] = [{"name": "AWS", "issuer": "Amazon"}]
        incoming = _empty_profile()
        incoming["certificates"] = [{"name": "AWS", "issuer": "Amazon"}]

        result = ProfileMergeService().merge(current, incoming)
        assert len(result.merged["certificates"]) == 1
        assert result.diff.sections["certificates"].is_empty()

    def test_interests_and_languages_union(self):
        current = _empty_profile()
        current["interests"] = [{"name": "Open Source"}]
        current["languages"] = [{"name": "Arabic", "proficiency": "native"}]
        incoming = _empty_profile()
        incoming["interests"] = [{"name": "Open Source"}, {"name": "Chess"}]
        incoming["languages"] = [{"name": "Arabic", "proficiency": "native"}]

        result = ProfileMergeService().merge(current, incoming)
        assert [i["name"] for i in result.merged["interests"]] == ["Open Source", "Chess"]
        assert len(result.merged["languages"]) == 1


class TestDiffAndIdempotency:
    def test_change_summary(self):
        current = _empty_profile()
        current["skills"] = [_skill("Python", skill_id=1)]
        incoming = _empty_profile()
        incoming["skills"] = [_skill("Python", skill_id=1, level=4), _skill("Go", skill_id=2)]

        result = ProfileMergeService().merge(current, incoming)
        summary = result.diff.to_change_summary()
        assert "skills added" in summary
        assert "skills updated" in summary

    def test_idempotent_remerge_no_diff(self):
        current = _empty_profile()
        current["skills"] = [_skill("Python", skill_id=1, level=4)]
        current["name"] = "Hassan"

        result = ProfileMergeService().merge(current, current)
        assert result.diff.is_empty()

    def test_empty_incoming_noop(self):
        result = ProfileMergeService().merge(_empty_profile(), {})
        assert result.diff.is_empty()

    def test_diff_method_between_snapshots(self):
        before = _empty_profile()
        before["skills"] = [_skill("Python", skill_id=1)]
        after = _empty_profile()
        after["skills"] = [_skill("Python", skill_id=1, level=5), _skill("Go", skill_id=2)]
        after["name"] = "Hassan"

        diff = ProfileMergeService().diff(before, after)
        assert diff.core["name"]["new"] == "Hassan"
        assert len(diff.sections["skills"].added) == 1
        assert len(diff.sections["skills"].updated) == 1
