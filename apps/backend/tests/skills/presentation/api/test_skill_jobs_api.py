"""Tests for GET /api/skills/{id}/jobs — jobs that mention a skill."""

from skills.infrastructure.models.skill_model import SkillModel, SkillMentionModel


def _create_skill(sa_session, **kwargs) -> SkillModel:
    defaults = dict(
        name="Kubernetes",
        level=4,
        roles="",
        path="",
        category="technical",
        confidence=0.0,
        market_relevance=0.0,
        evidence="[]",
        tags="[]",
        hidden=0,
        source="user",
        source_type="user_input",
    )
    defaults.update(kwargs)
    model = SkillModel(**defaults)
    sa_session.add(model)
    sa_session.commit()
    sa_session.refresh(model)
    return model


def _mention(sa_session, skill_id: int, source_type: str, source_id: str) -> SkillMentionModel:
    model = SkillMentionModel(skill_id=skill_id, source_type=source_type, source_id=source_id)
    sa_session.add(model)
    sa_session.commit()
    return model


def _create_jobs(sa_session, titles: list[tuple[str, str]]) -> list:
    from jobs.infrastructure.models.job_model import JobModel

    jobs = []
    for title, location in titles:
        job = JobModel(
            title=title,
            location=location,
            company="TechCo",
            deleted=0,
            workflow_log="[]",
            rescoring=0,
        )
        sa_session.add(job)
        jobs.append(job)
    sa_session.commit()
    return jobs


class TestSkillJobsAPI:
    def test_returns_jobs_that_mention_skill(self, client, sa_session):
        skill = _create_skill(sa_session, name="Kubernetes")
        job1, job2 = _create_jobs(sa_session, [("SRE Engineer", "Berlin"), ("Platform Eng", "Munich")])
        _mention(sa_session, skill.id, "job", job1.id)
        _mention(sa_session, skill.id, "job", job2.id)

        data = client.get(f"/api/skills/{skill.id}/jobs").json()
        assert data["total"] == 2
        assert len(data["jobs"]) == 2
        by_id = {j["id"]: j for j in data["jobs"]}
        assert by_id[job1.id]["title"] == "SRE Engineer"
        assert by_id[job2.id]["title"] == "Platform Eng"
        assert by_id[job1.id]["company"] == "TechCo"
        assert by_id[job1.id]["location"] == "Berlin"

    def test_ignores_company_mentions(self, client, sa_session):
        skill = _create_skill(sa_session, name="Kubernetes")
        job, = _create_jobs(sa_session, [("SRE Engineer", "Berlin")])
        _mention(sa_session, skill.id, "job", job.id)
        _mention(sa_session, skill.id, "company", "company-1")

        data = client.get(f"/api/skills/{skill.id}/jobs").json()
        assert data["total"] == 1
        assert [j["id"] for j in data["jobs"]] == [job.id]

    def test_empty_when_no_mentions(self, client, sa_session):
        skill = _create_skill(sa_session, name="Go")
        data = client.get(f"/api/skills/{skill.id}/jobs").json()
        assert data["total"] == 0
        assert data["jobs"] == []

    def test_unknown_skill_returns_404(self, client):
        resp = client.get("/api/skills/999999/jobs")
        assert resp.status_code == 404

    def test_dedupes_repeated_job_mentions(self, client, sa_session):
        from skills.infrastructure.repositories.sa_skill_repository import SQLAlchemySkillRepository

        skill = _create_skill(sa_session, name="Python")
        job, = _create_jobs(sa_session, [("Backend Dev", "Berlin")])
        repo = SQLAlchemySkillRepository(sa_session)
        repo.upsert_mentions(skill.id, "job", job.id)
        repo.upsert_mentions(skill.id, "job", job.id)

        data = client.get(f"/api/skills/{skill.id}/jobs").json()
        assert data["total"] == 1
        assert len(data["jobs"]) == 1