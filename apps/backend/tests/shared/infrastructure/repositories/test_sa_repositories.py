"""Comprehensive SA repository tests."""

import sys
import os
import json
import pytest
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from shared.infrastructure.database.sqlalchemy_config import Base
import jobs.infrastructure.models.job_model
import skills.infrastructure.models.skill_model
import companies.infrastructure.models.company_model

import shared.infrastructure.database.models.misc_models


@pytest.fixture
def session(_engine):
    connection = _engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    s = Session()
    yield s
    s.close()
    transaction.rollback()
    connection.close()


# ── Job Repository ────────────────────────────────────────────────

class TestSAJobRepository:
    def test_get_by_num(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1", company="Google"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        result = repo.get_by_num(1)
        assert result is not None
        assert result["num"] == 1

    def test_get_by_num_not_found(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        repo = SQLAlchemyJobRepository(session)
        assert repo.get_by_num(999) is None

    def test_get_by_num_with_company(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        from shared.infrastructure.database.models.company_model import CompanyModel
        co = CompanyModel(name="Google")
        session.add(co)
        session.commit()
        session.add(JobModel(num=1, url="https://ex.com/1", company="Google", company_id=co.id))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        result = repo.get_by_num(1)
        assert result["linked_company"]["name"] == "Google"

    def test_list_jobs(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1", company="A", deleted=0))
        session.add(JobModel(num=2, url="https://ex.com/2", company="B", deleted=0))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        jobs, total = repo.list_jobs()
        assert total == 2
        assert len(jobs) == 2

    def test_list_jobs_pagination(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        for i in range(5):
            session.add(JobModel(num=i+1, url=f"https://ex.com/{i}", company=f"C{i}"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        jobs, total = repo.list_jobs(offset=0, limit=2)
        assert total == 5
        assert len(jobs) == 2

    def test_list_jobs_filter_companies(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1", company="Google"))
        session.add(JobModel(num=2, url="https://ex.com/2", company="Meta"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        jobs, total = repo.list_jobs(filters={"filter_companies": "Google"})
        assert total == 1

    def test_list_jobs_filter_cities(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1", location="Berlin"))
        session.add(JobModel(num=2, url="https://ex.com/2", location="Munich"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        jobs, total = repo.list_jobs(filters={"filter_cities": "Berlin"})
        assert total == 1

    def test_list_jobs_filter_tech(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1", stack="Python"))
        session.add(JobModel(num=2, url="https://ex.com/2", stack="Java"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        jobs, total = repo.list_jobs(filters={"filter_tech": "Python"})
        assert total == 1

    def test_list_jobs_filter_matches(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1", match="High"))
        session.add(JobModel(num=2, url="https://ex.com/2", match="Low"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        jobs, total = repo.list_jobs(filters={"filter_matches": "High"})
        assert total == 1

    def test_list_jobs_filter_work_types(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1", work_type="Remote"))
        session.add(JobModel(num=2, url="https://ex.com/2", work_type="On-site"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        jobs, total = repo.list_jobs(filters={"filter_work_types": "Remote"})
        assert total == 1

    def test_list_jobs_filter_employment_types(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1", employment_type="Full-time"))
        session.add(JobModel(num=2, url="https://ex.com/2", employment_type="Part-time"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        jobs, total = repo.list_jobs(filters={"filter_employment_types": "Full-time"})
        assert total == 1

    def test_list_jobs_filter_response_status(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1", response_status="applied"))
        session.add(JobModel(num=2, url="https://ex.com/2", response_status="pending"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        jobs, total = repo.list_jobs(filters={"filter_response_status": "applied"})
        assert total == 1

    def test_list_jobs_filter_applied(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1", apply_time="2024-01-01"))
        session.add(JobModel(num=2, url="https://ex.com/2"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        jobs, total = repo.list_jobs(filters={"filter_applied": "true"})
        assert total == 1

    def test_list_jobs_filter_scores(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1", score="A"))
        session.add(JobModel(num=2, url="https://ex.com/2", score="B"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        jobs, total = repo.list_jobs(filters={"filter_scores": "A"})
        assert total == 1

    def test_list_jobs_sorting(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1", overall_score=50))
        session.add(JobModel(num=2, url="https://ex.com/2", overall_score=90))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        jobs, total = repo.list_jobs(sort_by="overall_score", sort_dir="desc")
        assert jobs[0]["overall_score"] == 90

    def test_list_jobs_invalid_sort(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        jobs, total = repo.list_jobs(sort_by="invalid_field", sort_dir="invalid")
        assert len(jobs) == 1

    def test_get_stats(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1", match="High", score="A", work_type="Remote"))
        session.add(JobModel(num=2, url="https://ex.com/2", match="Low", score="B"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        stats = repo.get_stats()
        assert stats["total"] == 2
        assert stats["high_match"] == 1
        assert stats["apply_now"] == 1
        assert stats["remote"] == 1

    def test_update(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        result = repo.update(1, {"notes": "test", "apply_time": "2024-01-01"})
        assert result["notes"] == "test"

    def test_update_not_found(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        repo = SQLAlchemyJobRepository(session)
        assert repo.update(999, {"notes": "test"}) is None

    def test_update_empty(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        result = repo.update(1, {})
        assert result is not None

    def test_delete(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        assert repo.delete(1) is True

    def test_mark_deleted(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        repo.mark_deleted(1)
        result = repo.get_by_num(1)
        assert result["deleted"] == 1

    def test_mark_rescoring(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        repo.mark_rescoring(1, False)
        result = repo.get_by_num(1)
        assert result["rescoring"] == 0

    def test_get_all_active(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1", deleted=0))
        session.add(JobModel(num=2, url="https://ex.com/2", deleted=1))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        active = repo.get_all_active()
        assert len(active) == 1

    def test_get_next_num(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=5, url="https://ex.com/1"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        assert repo.get_next_num() == 6

    def test_get_next_num_empty(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        repo = SQLAlchemyJobRepository(session)
        assert repo.get_next_num() == 1

    def test_get_by_url(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        result = repo.get_by_url("https://ex.com/1")
        assert result["num"] == 1

    def test_get_by_url_not_found(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        repo = SQLAlchemyJobRepository(session)
        assert repo.get_by_url("https://nonexistent.com") is None

    def test_get_num_by_url(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        assert repo.get_num_by_url("https://ex.com/1") == 1

    def test_get_num_by_url_not_found(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        repo = SQLAlchemyJobRepository(session)
        assert repo.get_num_by_url("https://nonexistent.com") is None

    def test_upsert_insert(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        repo = SQLAlchemyJobRepository(session)
        result = repo.upsert({"num": 1, "url": "https://ex.com/1", "company": "A"})
        assert result["num"] == 1

    def test_upsert_update(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1", company="A"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        result = repo.upsert({"num": 1, "company": "B"})
        assert result["company"] == "B"

    def test_update_fields(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        assert repo.update_fields(1, company_id=5) is True

    def test_update_workflow_log(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        assert repo.update_workflow_log(1, "[\"step1\"]") is True

    def test_set_deleted_by_url(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1"))
        session.add(JobModel(num=2, url="https://ex.com/1"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        count = repo.set_deleted_by_url("https://ex.com/1", exclude_num=1)
        assert count == 1

    def test_delete_all_active(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1", deleted=0))
        session.add(JobModel(num=2, url="https://ex.com/2", deleted=0))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        count = repo.delete_all_active()
        assert count == 2

    def test_get_company_id(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1", company_id=5))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        assert repo.get_company_id(1) == 5

    def test_get_company_id_none(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        assert repo.get_company_id(1) is None

    def test_get_dashboard_counts(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1", match="High"))
        session.add(JobModel(num=2, url="https://ex.com/2", match="Low"))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        counts = repo.get_dashboard_counts()
        assert counts["jobs_total"] == 2
        assert counts["jobs_high_match"] == 1

    def test_get_location_data(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1", location="Berlin", locations='["Berlin"]'))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        result = repo.get_location_data()
        assert len(result) == 1
        assert result[0]["location"] == "Berlin"

    def test_get_company_id_by_num(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1", company_id=3))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        assert repo.get_company_id_by_num(1) == 3

    def test_get_jobs_by_company_id(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1", company_id=1))
        session.add(JobModel(num=2, url="https://ex.com/2", company_id=2))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        result = repo.get_jobs_by_company_id(1)
        assert len(result) == 1


# ── Skill Repository ──────────────────────────────────────────────

class TestSASkillRepository:
    def test_list_visible(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        from shared.infrastructure.database.models.skill_model import SkillModel
        session.add(SkillModel(name="Python", level=8, hidden=0))
        session.add(SkillModel(name="Java", level=5, hidden=1))
        session.commit()
        repo = SQLAlchemySkillRepository(session)
        result = repo.list_visible()
        assert len(result) == 1

    def test_list_visible_by_category(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        from shared.infrastructure.database.models.skill_model import SkillModel
        session.add(SkillModel(name="Python", level=8, category="technical"))
        session.add(SkillModel(name="Leadership", level=5, category="professional"))
        session.commit()
        repo = SQLAlchemySkillRepository(session)
        result = repo.list_visible(category="technical")
        assert len(result) == 1

    def test_list_hidden(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        from shared.infrastructure.database.models.skill_model import SkillModel
        session.add(SkillModel(name="OldSkill", hidden=1))
        session.commit()
        repo = SQLAlchemySkillRepository(session)
        result = repo.list_hidden()
        assert len(result) == 1

    def test_get_by_id(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        from shared.infrastructure.database.models.skill_model import SkillModel
        session.add(SkillModel(name="Python", level=8))
        session.commit()
        skill_id = session.query(SkillModel).first().id
        repo = SQLAlchemySkillRepository(session)
        result = repo.get_by_id(skill_id)
        assert result["name"] == "Python"

    def test_get_by_id_not_found(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        repo = SQLAlchemySkillRepository(session)
        assert repo.get_by_id(999) is None

    def test_get_by_name(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        from shared.infrastructure.database.models.skill_model import SkillModel
        session.add(SkillModel(name="Python", level=8))
        session.commit()
        repo = SQLAlchemySkillRepository(session)
        result = repo.get_by_name("Python")
        assert result["name"] == "Python"

    def test_get_by_name_not_found(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        repo = SQLAlchemySkillRepository(session)
        assert repo.get_by_name("Nonexistent") is None

    def test_create(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        repo = SQLAlchemySkillRepository(session)
        result = repo.create({"name": "Rust", "level": 5, "category": "technical"})
        assert result["name"] == "Rust"

    def test_update(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        from shared.infrastructure.database.models.skill_model import SkillModel
        session.add(SkillModel(name="Python", level=8))
        session.commit()
        skill_id = session.query(SkillModel).first().id
        repo = SQLAlchemySkillRepository(session)
        result = repo.update(skill_id, {"level": 10, "tags": ["web"]})
        assert result["level"] == 10

    def test_update_not_found(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        repo = SQLAlchemySkillRepository(session)
        assert repo.update(999, {"level": 10}) is None

    def test_delete(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        from shared.infrastructure.database.models.skill_model import SkillModel
        session.add(SkillModel(name="Python"))
        session.commit()
        skill_id = session.query(SkillModel).first().id
        repo = SQLAlchemySkillRepository(session)
        assert repo.delete(skill_id) is True

    def test_delete_not_found(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        repo = SQLAlchemySkillRepository(session)
        assert repo.delete(999) is False

    def test_set_hidden(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        from shared.infrastructure.database.models.skill_model import SkillModel
        session.add(SkillModel(name="Python"))
        session.commit()
        skill_id = session.query(SkillModel).first().id
        repo = SQLAlchemySkillRepository(session)
        result = repo.set_hidden(skill_id, 1)
        assert result["hidden"] == 1

    def test_set_hidden_not_found(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        repo = SQLAlchemySkillRepository(session)
        assert repo.set_hidden(999, 1) is None

    def test_rename(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        from shared.infrastructure.database.models.skill_model import SkillModel
        session.add(SkillModel(name="Python"))
        session.commit()
        skill_id = session.query(SkillModel).first().id
        repo = SQLAlchemySkillRepository(session)
        result = repo.rename(skill_id, "Python3")
        assert result["name"] == "Python3"

    def test_rename_same_name(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        from shared.infrastructure.database.models.skill_model import SkillModel
        session.add(SkillModel(name="Python"))
        session.commit()
        skill_id = session.query(SkillModel).first().id
        repo = SQLAlchemySkillRepository(session)
        result = repo.rename(skill_id, "Python")
        assert result["name"] == "Python"

    def test_rename_conflict(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        from shared.infrastructure.database.models.skill_model import SkillModel
        session.add(SkillModel(name="Python"))
        session.add(SkillModel(name="Java"))
        session.commit()
        java_id = session.query(SkillModel).filter(SkillModel.name == "Java").first().id
        repo = SQLAlchemySkillRepository(session)
        result = repo.rename(java_id, "Python")
        assert result is None

    def test_rename_not_found(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        repo = SQLAlchemySkillRepository(session)
        assert repo.rename(999, "New") is None

    def test_merge(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        from shared.infrastructure.database.models.skill_model import SkillModel
        session.add(SkillModel(name="Python"))
        session.add(SkillModel(name="Python3"))
        session.commit()
        target = session.query(SkillModel).filter(SkillModel.name == "Python").first()
        source = session.query(SkillModel).filter(SkillModel.name == "Python3").first()
        repo = SQLAlchemySkillRepository(session)
        result = repo.merge(target.id, [source.id])
        assert result["status"] == "merged"
        assert "Python3" in result["aliases"]

    def test_merge_target_not_found(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        repo = SQLAlchemySkillRepository(session)
        result = repo.merge(999, [])
        assert "error" in result

    def test_get_categories(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        from shared.infrastructure.database.models.skill_model import SkillModel
        session.add(SkillModel(name="Python", level=8, category="technical"))
        session.add(SkillModel(name="Java", level=5, category="technical"))
        session.commit()
        repo = SQLAlchemySkillRepository(session)
        cats = repo.get_categories()
        assert len(cats) == 1
        assert cats[0]["count"] == 2

    def test_get_stats(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        from shared.infrastructure.database.models.skill_model import SkillModel
        session.add(SkillModel(name="Python", level=8, source="user", market_relevance=9.0))
        session.commit()
        repo = SQLAlchemySkillRepository(session)
        stats = repo.get_stats()
        assert stats["total"] == 1
        assert stats["hidden"] == 0

    def test_bulk_hide(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        from shared.infrastructure.database.models.skill_model import SkillModel
        session.add(SkillModel(name="Python"))
        session.add(SkillModel(name="Java"))
        session.commit()
        ids = [s.id for s in session.query(SkillModel).all()]
        repo = SQLAlchemySkillRepository(session)
        count = repo.bulk_hide(ids)
        assert count == 2

    def test_bulk_categorize(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        from shared.infrastructure.database.models.skill_model import SkillModel
        session.add(SkillModel(name="Python"))
        session.commit()
        ids = [s.id for s in session.query(SkillModel).all()]
        repo = SQLAlchemySkillRepository(session)
        count = repo.bulk_categorize(ids, "technical")
        assert count == 1

    def test_get_relationships(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        from shared.infrastructure.database.models.skill_model import SkillRelationshipModel
        session.add(SkillRelationshipModel(skill_name="Python", related_name="Django", relation_type="related"))
        session.commit()
        repo = SQLAlchemySkillRepository(session)
        result = repo.get_relationships("Python")
        assert len(result) == 1

    def test_create_relationship(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        repo = SQLAlchemySkillRepository(session)
        result = repo.create_relationship({"skill_name": "Python", "related_name": "Django", "relation_type": "related"})
        assert result is True

    def test_delete_relationship(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        from shared.infrastructure.database.models.skill_model import SkillRelationshipModel
        session.add(SkillRelationshipModel(skill_name="A", related_name="B", relation_type="related"))
        session.commit()
        rel_id = session.query(SkillRelationshipModel).first().id
        repo = SQLAlchemySkillRepository(session)
        assert repo.delete_relationship(rel_id) is True

    def test_get_all(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        from shared.infrastructure.database.models.skill_model import SkillModel
        session.add(SkillModel(name="Python"))
        session.add(SkillModel(name="Java"))
        session.commit()
        repo = SQLAlchemySkillRepository(session)
        result = repo.get_all()
        assert len(result) == 2

    def test_get_level_by_name(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        from shared.infrastructure.database.models.skill_model import SkillModel
        session.add(SkillModel(name="Python", level=8))
        session.commit()
        repo = SQLAlchemySkillRepository(session)
        assert repo.get_level_by_name("Python") == 8

    def test_get_level_by_name_not_found(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        repo = SQLAlchemySkillRepository(session)
        assert repo.get_level_by_name("Nonexistent") is None

    def test_update_fields_by_name(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        from shared.infrastructure.database.models.skill_model import SkillModel
        session.add(SkillModel(name="Python", level=8))
        session.commit()
        repo = SQLAlchemySkillRepository(session)
        assert repo.update_fields_by_name("Python", level=10) is True

    def test_update_fields_by_name_not_found(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        repo = SQLAlchemySkillRepository(session)
        assert repo.update_fields_by_name("Nonexistent", level=10) is False

    def test_create_from_dict(self, session):
        from shared.infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        repo = SQLAlchemySkillRepository(session)
        result = repo.create_from_dict({"name": "Go", "level": 6, "source": "service"})
        assert result["name"] == "Go"


# ── Company Repository ────────────────────────────────────────────

class TestSACompanyRepository:
    def test_list_all(self, session):
        from shared.infrastructure.database.sa_company_repository import SQLAlchemyCompanyRepository
        from shared.infrastructure.database.models.company_model import CompanyModel
        session.add(CompanyModel(name="Google"))
        session.add(CompanyModel(name="Meta"))
        session.commit()
        repo = SQLAlchemyCompanyRepository(session)
        result = repo.list_all()
        assert len(result) == 2

    def test_get_by_id(self, session):
        from shared.infrastructure.database.sa_company_repository import SQLAlchemyCompanyRepository
        from shared.infrastructure.database.models.company_model import CompanyModel
        co = CompanyModel(name="Google")
        session.add(co)
        session.commit()
        repo = SQLAlchemyCompanyRepository(session)
        result = repo.get_by_id(co.id)
        assert result["name"] == "Google"

    def test_get_by_id_not_found(self, session):
        from shared.infrastructure.database.sa_company_repository import SQLAlchemyCompanyRepository
        repo = SQLAlchemyCompanyRepository(session)
        assert repo.get_by_id(999) is None

    def test_create(self, session):
        from shared.infrastructure.database.sa_company_repository import SQLAlchemyCompanyRepository
        repo = SQLAlchemyCompanyRepository(session)
        result = repo.create({"name": "Google", "industry": "Tech"})
        assert result["name"] == "Google"

    def test_update(self, session):
        from shared.infrastructure.database.sa_company_repository import SQLAlchemyCompanyRepository
        from shared.infrastructure.database.models.company_model import CompanyModel
        co = CompanyModel(name="Google")
        session.add(co)
        session.commit()
        repo = SQLAlchemyCompanyRepository(session)
        result = repo.update(co.id, {"industry": "Tech", "tech_stack": ["Python"]})
        assert result["industry"] == "Tech"

    def test_update_not_found(self, session):
        from shared.infrastructure.database.sa_company_repository import SQLAlchemyCompanyRepository
        repo = SQLAlchemyCompanyRepository(session)
        assert repo.update(999, {"name": "X"}) is None

    def test_delete(self, session):
        from shared.infrastructure.database.sa_company_repository import SQLAlchemyCompanyRepository
        from shared.infrastructure.database.models.company_model import CompanyModel
        co = CompanyModel(name="Google")
        session.add(co)
        session.commit()
        repo = SQLAlchemyCompanyRepository(session)
        assert repo.delete(co.id) is True

    def test_get_intelligence(self, session):
        from shared.infrastructure.database.sa_company_repository import SQLAlchemyCompanyRepository
        from shared.infrastructure.database.models.company_model import CompanyModel, CompanyIntelligenceModel
        co = CompanyModel(name="Google")
        session.add(co)
        session.commit()
        session.add(CompanyIntelligenceModel(company_id=co.id, overview="Great"))
        session.commit()
        repo = SQLAlchemyCompanyRepository(session)
        result = repo.get_intelligence(co.id)
        assert result["overview"] == "Great"

    def test_get_intelligence_not_found(self, session):
        from shared.infrastructure.database.sa_company_repository import SQLAlchemyCompanyRepository
        repo = SQLAlchemyCompanyRepository(session)
        assert repo.get_intelligence(999) is None

    def test_insert(self, session):
        from shared.infrastructure.database.sa_company_repository import SQLAlchemyCompanyRepository
        repo = SQLAlchemyCompanyRepository(session)
        result = repo.insert({"name": "TestCo"})
        assert result["name"] == "TestCo"

    def test_get_total_count(self, session):
        from shared.infrastructure.database.sa_company_repository import SQLAlchemyCompanyRepository
        from shared.infrastructure.database.models.company_model import CompanyModel
        session.add(CompanyModel(name="A"))
        session.add(CompanyModel(name="B"))
        session.commit()
        repo = SQLAlchemyCompanyRepository(session)
        assert repo.get_total_count() == 2

    def test_get_all_with_job_counts(self, session):
        from shared.infrastructure.database.sa_company_repository import SQLAlchemyCompanyRepository
        from shared.infrastructure.database.models.company_model import CompanyModel
        from shared.infrastructure.database.models.job_model import JobModel
        co = CompanyModel(name="Google")
        session.add(co)
        session.commit()
        session.add(JobModel(num=1, url="https://ex.com/1", company_id=co.id))
        session.commit()
        repo = SQLAlchemyCompanyRepository(session)
        result = repo.get_all_with_job_counts()
        assert result[0]["job_count"] == 1


# ── Pending Repository ────────────────────────────────────────────

class TestSAPendingRepository:
    def test_list_pending_jobs(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from jobs.infrastructure.models.job_model import JobModel as PendingJobModel
        session.add(PendingJobModel(url="https://ex.com/1", status="pending"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        result = repo.list_pending("pending_jobs")
        assert len(result) == 1

    def test_list_pending_companies(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from companies.infrastructure.models.company_model import CompanyModel as PendingCompanyModel
        session.add(PendingCompanyModel(input_text="Google", status="pending"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        result = repo.list_pending("pending_companies")
        assert len(result) == 1

    def test_list_pending_done_excluded(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from jobs.infrastructure.models.job_model import JobModel as PendingJobModel
        session.add(PendingJobModel(url="https://ex.com/1", status="processed"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        result = repo.list_pending("pending_jobs")
        assert len(result) == 0

    def test_list_pending_unknown_table(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        repo = SQLAlchemyPendingRepository(session)
        assert repo.list_pending("unknown") == []

    def test_get_by_id_jobs(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from jobs.infrastructure.models.job_model import JobModel as PendingJobModel
        pj = PendingJobModel(url="https://ex.com/1", status="pending")
        session.add(pj)
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        result = repo.get_by_id(str(pj.num), "pending_jobs")
        assert result["url"] == "https://ex.com/1"

    def test_get_by_id_companies(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from companies.infrastructure.models.company_model import CompanyModel as PendingCompanyModel
        pc = PendingCompanyModel(input_text="Google", status="pending")
        session.add(pc)
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        result = repo.get_by_id(str(pc.id), "pending_companies")
        assert result["name"] is None

    def test_get_by_id_not_found(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        repo = SQLAlchemyPendingRepository(session)
        assert repo.get_by_id("999", "pending_jobs") is None

    def test_get_by_id_unknown_table(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        repo = SQLAlchemyPendingRepository(session)
        assert repo.get_by_id("1", "unknown") is None

    def test_create_pending_job(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        repo = SQLAlchemyPendingRepository(session)
        result = repo.create({"url": "https://ex.com/1", "source": "api"}, "pending_jobs")
        assert result["url"] == "https://ex.com/1"

    def test_create_pending_job_existing_url(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from jobs.infrastructure.models.job_model import JobModel as PendingJobModel
        session.add(PendingJobModel(url="https://ex.com/1", status="done"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        result = repo.create({"url": "https://ex.com/1", "source": "api"}, "pending_jobs")
        assert result["status"] == "created"

    def test_create_pending_company(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        repo = SQLAlchemyPendingRepository(session)
        result = repo.create({"name": "Google"}, "pending_companies")
        assert result["status"] == "created"

    def test_create_unknown_table(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        repo = SQLAlchemyPendingRepository(session)
        with pytest.raises(ValueError):
            repo.create({}, "unknown")

    def test_update_status(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from jobs.infrastructure.models.job_model import JobModel as PendingJobModel
        pj = PendingJobModel(url="https://ex.com/1", status="pending")
        session.add(pj)
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        assert repo.update_status(str(pj.num), "processing", "pending_jobs") is True

    def test_count_pending(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from jobs.infrastructure.models.job_model import JobModel as PendingJobModel
        session.add(PendingJobModel(url="https://ex.com/1", status="pending"))
        session.add(PendingJobModel(url="https://ex.com/2", status="processed"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        assert repo.count_pending("pending_jobs") == 1

    def test_count_pending_companies(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from companies.infrastructure.models.company_model import CompanyModel as PendingCompanyModel
        session.add(PendingCompanyModel(input_text="A", status="pending"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        assert repo.count_pending("pending_companies") == 1

    def test_count_pending_unknown(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        repo = SQLAlchemyPendingRepository(session)
        assert repo.count_pending("unknown") == 0

    def test_get_by_url(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from jobs.infrastructure.models.job_model import JobModel as PendingJobModel
        session.add(PendingJobModel(url="https://ex.com/1"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        result = repo.get_by_url("https://ex.com/1")
        assert result is not None

    def test_get_by_url_not_found(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        repo = SQLAlchemyPendingRepository(session)
        assert repo.get_by_url("https://nonexistent.com") is None

    def test_update_fields(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from jobs.infrastructure.models.job_model import JobModel as PendingJobModel
        pj = PendingJobModel(url="https://ex.com/1", status="pending")
        session.add(pj)
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        assert repo.update_fields(pj.num, table="pending_jobs", status="processing") is True

    def test_update_fields_companies(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from companies.infrastructure.models.company_model import CompanyModel as PendingCompanyModel
        pc = PendingCompanyModel(input_text="Google", status="pending")
        session.add(pc)
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        assert repo.update_fields(pc.id, table="pending_companies", status="processing") is True

    def test_update_fields_unknown_table(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        repo = SQLAlchemyPendingRepository(session)
        assert repo.update_fields(1, table="unknown") is False

    def test_update_fields_not_found(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        repo = SQLAlchemyPendingRepository(session)
        assert repo.update_fields(999, table="pending_jobs") is False

    def test_update_step(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from jobs.infrastructure.models.job_model import JobModel as PendingJobModel
        pj = PendingJobModel(url="https://ex.com/1")
        session.add(pj)
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        assert repo.update_step(pj.num, "step_fetch", 1, "pending_jobs") is True

    def test_save_session_id(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from jobs.infrastructure.models.job_model import JobModel as PendingJobModel
        pj = PendingJobModel(url="https://ex.com/1")
        session.add(pj)
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        assert repo.save_session_id(pj.num, "sess123") is True

    def test_update_workflow_log(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from jobs.infrastructure.models.job_model import JobModel as PendingJobModel
        pj = PendingJobModel(url="https://ex.com/1")
        session.add(pj)
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        assert repo.update_workflow_log(pj.num, "[\"step1\"]") is True

    def test_get_max_queue_order(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from jobs.infrastructure.models.job_model import JobModel as PendingJobModel
        session.add(PendingJobModel(url="https://ex.com/1", queue_order=5))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        assert repo.get_max_queue_order("pending_jobs") == 5

    def test_get_max_queue_order_empty(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        repo = SQLAlchemyPendingRepository(session)
        assert repo.get_max_queue_order("pending_jobs") == 0

    def test_get_max_queue_order_companies(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        repo = SQLAlchemyPendingRepository(session)
        assert repo.get_max_queue_order("pending_companies") == 0

    def test_get_processing_count(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from jobs.infrastructure.models.job_model import JobModel as PendingJobModel
        session.add(PendingJobModel(url="https://ex.com/1", status="processing"))
        session.add(PendingJobModel(url="https://ex.com/2", status="created"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        assert repo.get_processing_count("pending_jobs") == 1

    def test_get_queued_count(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from jobs.infrastructure.models.job_model import JobModel as PendingJobModel
        session.add(PendingJobModel(url="https://ex.com/1", status="queued"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        assert repo.get_queued_count("pending_jobs") == 1

    def test_get_processing_items(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from jobs.infrastructure.models.job_model import JobModel as PendingJobModel
        session.add(PendingJobModel(url="https://ex.com/1", status="processing"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        result = repo.get_processing_items("pending_jobs")
        assert len(result) == 1

    def test_mark_processing_as_waiting(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from jobs.infrastructure.models.job_model import JobModel as PendingJobModel
        session.add(PendingJobModel(url="https://ex.com/1", status="processing"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        count = repo.mark_processing_as_waiting("pending_jobs")
        assert count == 1

    def test_reset_processing_orphans(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from jobs.infrastructure.models.job_model import JobModel as PendingJobModel
        session.add(PendingJobModel(url="https://ex.com/1", status="processing"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        count = repo.reset_processing_orphans("pending_jobs")
        assert count == 1

    def test_pick_queued_item(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from jobs.infrastructure.models.job_model import JobModel as PendingJobModel
        session.add(PendingJobModel(url="https://ex.com/1", status="queued"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        result = repo.pick_queued_item("pending_jobs")
        assert result["status"] == "processing"

    def test_pick_queued_item_none(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        repo = SQLAlchemyPendingRepository(session)
        assert repo.pick_queued_item("pending_jobs") is None

    def test_pick_queued_item_companies(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from companies.infrastructure.models.company_model import CompanyModel as PendingCompanyModel
        session.add(PendingCompanyModel(input_text="Google", status="queued"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        result = repo.pick_queued_item("pending_companies")
        assert result["status"] == "processing"

    def test_get_queued_items(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from jobs.infrastructure.models.job_model import JobModel as PendingJobModel
        session.add(PendingJobModel(url="https://ex.com/1", status="queued"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        result = repo.get_queued_items("pending_jobs")
        assert len(result) == 1

    def test_reset_steps(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from jobs.infrastructure.models.job_model import JobModel as PendingJobModel
        pj = PendingJobModel(url="https://ex.com/1", status="failed")
        session.add(pj)
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        assert repo.reset_steps(pj.num, 2, "pending_jobs") is True

    def test_reset_steps_companies(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from companies.infrastructure.models.company_model import CompanyModel as PendingCompanyModel
        pc = PendingCompanyModel(status="failed")
        session.add(pc)
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        assert repo.reset_steps(pc.id, 2, "pending_companies") is True

    def test_get_all_for_stream(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from jobs.infrastructure.models.job_model import JobModel as PendingJobModel
        session.add(PendingJobModel(url="https://ex.com/1"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        result = repo.get_all_for_stream("pending_jobs")
        assert len(result) == 1

    def test_get_by_url_pending(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from jobs.infrastructure.models.job_model import JobModel as PendingJobModel
        session.add(PendingJobModel(url="https://ex.com/1"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        result = repo.get_by_url_pending("https://ex.com/1")
        assert result is not None

    def test_create_pending_job_direct(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        repo = SQLAlchemyPendingRepository(session)
        result = repo.create_pending_job("https://ex.com/1", "api", "Google", "pending")
        assert result["url"] == "https://ex.com/1"

    def test_create_pending_company_direct(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        repo = SQLAlchemyPendingRepository(session)
        result = repo.create_pending_company("Google", "url", "web", "pending", "[]")
        assert result["name"] is None
