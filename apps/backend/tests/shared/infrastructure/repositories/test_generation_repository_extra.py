"""Extra tests for GenerationHistoryRepository.

Covers source_filter variants, pagination, context-filtered queries
(get_for_job/get_for_company/get_for_skill), get_active_count for all
contexts, and exception branches.
"""

import pytest
from unittest.mock import patch

from jobs.infrastructure.models.job_model import JobModel
from companies.infrastructure.models.company_model import CompanyModel
from skills.infrastructure.models.skill_roadmap_models import SkillRoadmapJobModel
from shared.infrastructure.repositories.generation_repository import GenerationHistoryRepository

PATCH_TARGET = "shared.infrastructure.repositories.generation_repository.get_session_sync"


@pytest.fixture
def repo(sa_session):
    with patch(PATCH_TARGET, return_value=sa_session):
        yield GenerationHistoryRepository()


def _job(sa_session, job_id='job-1', **kwargs):
    defaults = {
        "id": job_id,
        "url": f"https://example.com/{job_id}",
        "source": "web",
        "status": "done",
        "created_at": "2026-07-27T10:00:00",
        "updated_at": "2026-07-27T10:05:00",
    }
    defaults.update(kwargs)
    m = JobModel(**defaults)
    sa_session.add(m)
    sa_session.commit()
    return m


def _company(sa_session, **kwargs):
    defaults = {
        "name": "TechCorp",
        "source": "web",
        "status": "done",
        "created_at": "2026-07-27T10:00:00",
        "updated_at": "2026-07-27T10:03:00",
    }
    defaults.update(kwargs)
    m = CompanyModel(**defaults)
    sa_session.add(m)
    sa_session.commit()
    return m


def _roadmap(sa_session, **kwargs):
    defaults = {
        "skill_name": "Python",
        "job_type": "generate",
        "status": "completed",
        "started_at": "2026-07-27T10:00:00",
        "completed_at": "2026-07-27T10:04:00",
        "session_id": "sess_rm",
    }
    defaults.update(kwargs)
    m = SkillRoadmapJobModel(**defaults)
    sa_session.add(m)
    sa_session.commit()
    return m


class TestSourceFilter:
    def test_filter_job_processing_only(self, repo, sa_session):
        _job(sa_session)
        _company(sa_session)
        _roadmap(sa_session)
        result = repo.get_all(source_filter="job-processing")
        assert result["total"] == 1
        assert result["items"][0].source == "job-processing"

    def test_filter_company_processing_only(self, repo, sa_session):
        _job(sa_session)
        _company(sa_session)
        result = repo.get_all(source_filter="company-processing")
        assert result["total"] == 1
        assert result["items"][0].source == "company-processing"

    def test_filter_generation_only(self, repo, sa_session):
        _job(sa_session)
        result = repo.get_all(source_filter="generation")
        assert result["total"] == 0

    def test_filter_roadmap_only(self, repo, sa_session):
        _job(sa_session)
        _company(sa_session)
        _roadmap(sa_session)
        result = repo.get_all(source_filter="roadmap")
        assert result["total"] == 1
        assert result["items"][0].source == "roadmap"

    def test_all_sources_combined(self, repo, sa_session):
        _job(sa_session)
        _company(sa_session)
        _roadmap(sa_session)
        result = repo.get_all()
        sources = {i.source for i in result["items"]}
        assert sources == {"job-processing", "company-processing", "roadmap"}

    def test_pagination_limit_and_offset(self, repo, sa_session):
        _job(sa_session, job_id="job-a")
        _job(sa_session, job_id="job-b")
        _job(sa_session, job_id="job-c")
        result = repo.get_all(limit=1, offset=1)
        assert result["total"] == 3
        assert len(result["items"]) == 1

    def test_sorting_desc_by_started_at(self, repo, sa_session):
        _job(sa_session, job_id="job-a", created_at="2026-07-27T10:00:00")
        _job(sa_session, job_id="job-b", created_at="2026-07-27T11:00:00")
        result = repo.get_all(source_filter="job-processing")
        assert result["items"][0].id == "job-b"

    def test_exception_in_query_is_silent(self, repo):
        with patch(PATCH_TARGET, side_effect=RuntimeError("boom")):
            result = repo.get_all()
            assert result["items"] == []
            assert result["total"] == 0


class TestDefaultTitles:
    def test_pending_job_without_company(self, repo, sa_session):
        _job(sa_session, company=None, status="imported")
        result = repo.get_all(source_filter="job-processing")
        assert result["items"][0].title == "Job"
        assert result["items"][0].completed_at is None

    def test_pending_company_without_name(self, repo, sa_session):
        _company(sa_session, name=None)
        result = repo.get_all(source_filter="company-processing")
        assert result["items"][0].title == "Company"

    def test_roadmap_item_fields(self, repo, sa_session):
        _roadmap(sa_session, skill_name="Python", status="failed", error="err",
                 provider_name="mimo")
        result = repo.get_all(source_filter="roadmap")
        item = result["items"][0]
        assert item.status == "failed"
        assert item.error == "err"
        assert item.provider == "mimo"
        assert item.started_at == "2026-07-27T10:00:00"
        assert item.completed_at == "2026-07-27T10:04:00"


class TestContextQueries:
    def test_get_for_job(self, repo, sa_session):
        _job(sa_session, job_id="5", status="completed", company=None)
        result = repo.get_for_job("5")
        assert result["total"] == 1
        item = result["items"][0]
        assert item.source == "job-processing"
        assert item.id == "5"

    def test_get_for_job_empty(self, repo, sa_session):
        _job(sa_session)
        result = repo.get_for_job("6")
        assert result["items"] == []
        assert result["total"] == 0

    def test_get_for_company(self, repo, sa_session):
        c = _company(sa_session, status="done")
        result = repo.get_for_company(c.id)
        assert result["total"] == 1
        assert result["items"][0].source == "company-processing"

    def test_get_for_company_empty(self, repo):
        result = repo.get_for_company(999)
        assert result["items"] == []
        assert result["total"] == 0

    def test_get_for_skill(self, repo, sa_session):
        _roadmap(sa_session, skill_name="Python")
        result = repo.get_for_skill("Python")
        assert result["total"] == 1
        assert result["items"][0].source == "roadmap"
        assert result["items"][0].provider is None

    def test_get_for_skill_empty(self, repo):
        result = repo.get_for_skill("Nonexistent")
        assert result["items"] == []
        assert result["total"] == 0

    def test_get_for_skill_provider(self, repo, sa_session):
        _roadmap(sa_session, skill_name="Go", provider_name="mimo")
        result = repo.get_for_skill("Go")
        assert result["items"][0].provider == "mimo"

    def test_context_query_exception_is_silent(self, repo, sa_session):
        _job(sa_session)
        c = _company(sa_session)
        _roadmap(sa_session, skill_name="Python")
        c_id = c.id
        with patch(PATCH_TARGET, side_effect=RuntimeError("boom")):
            assert repo.get_for_job("5")["items"] == []
            assert repo.get_for_company(c_id)["items"] == []
            assert repo.get_for_skill("Python")["items"] == []


class TestGetActiveCount:
    def test_job_context(self, repo, sa_session):
        j1_id = _job(sa_session, job_id="job-1", status="processing").id
        j2_id = _job(sa_session, job_id="job-2", status="queued").id
        _job(sa_session, job_id="job-3", status="imported")
        assert repo.get_active_count("job", job_id=j1_id) == 1
        assert repo.get_active_count("job", job_id=j2_id) == 1

    def test_company_context(self, repo, sa_session):
        c1 = _company(sa_session, status="processing")
        c2 = _company(sa_session, status="queued")
        _company(sa_session, status="done")
        c1_id, c2_id = c1.id, c2.id
        assert repo.get_active_count("company", company_id=c1_id) == 1
        assert repo.get_active_count("company", company_id=c2_id) == 1

    def test_skill_context(self, repo, sa_session):
        _roadmap(sa_session, skill_name="Python", status="queued")
        _roadmap(sa_session, skill_name="Go", status="running")
        _roadmap(sa_session, skill_name="Java", status="completed")
        assert repo.get_active_count("skill", skill_name="python") == 1
        assert repo.get_active_count("skill", skill_name="go") == 1

    def test_unknown_context(self, repo):
        assert repo.get_active_count("bogus") == 0

    def test_job_context_without_num(self, repo, sa_session):
        _job(sa_session, job_id="job-1", status="processing")
        assert repo.get_active_count("job") == 0

    def test_exception_returns_zero(self, repo):
        with patch(PATCH_TARGET, side_effect=RuntimeError("boom")):
            assert repo.get_active_count("job", job_id="job-x") == 0
