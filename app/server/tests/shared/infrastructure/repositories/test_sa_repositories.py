"""Comprehensive SA repository tests."""

import sys
import os
import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from shared.infrastructure.database.sqlalchemy_config import Base
import jobs.infrastructure.models.job_model
import skills.infrastructure.models.skill_model
import companies.infrastructure.models.company_model
import processing.infrastructure.models.pending_model
import career.infrastructure.models.insight_model
import shared.infrastructure.database.models.misc_models


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:", echo=False, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()
    engine.dispose()


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

    def test_get_all_for_insights(self, session):
        from shared.infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
        from shared.infrastructure.database.models.job_model import JobModel
        session.add(JobModel(num=1, url="https://ex.com/1", overall_score=90))
        session.add(JobModel(num=2, url="https://ex.com/2", overall_score=50))
        session.commit()
        repo = SQLAlchemyJobRepository(session)
        result = repo.get_all_for_insights()
        assert result[0]["overall_score"] == 90

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
        from shared.infrastructure.database.models.pending_model import PendingJobModel
        session.add(PendingJobModel(url="https://ex.com/1", status="pending"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        result = repo.list_pending("pending_jobs")
        assert len(result) == 1

    def test_list_pending_companies(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from shared.infrastructure.database.models.pending_model import PendingCompanyModel
        session.add(PendingCompanyModel(input_text="Google", status="pending"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        result = repo.list_pending("pending_companies")
        assert len(result) == 1

    def test_list_pending_done_excluded(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from shared.infrastructure.database.models.pending_model import PendingJobModel
        session.add(PendingJobModel(url="https://ex.com/1", status="done"))
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
        from shared.infrastructure.database.models.pending_model import PendingJobModel
        pj = PendingJobModel(url="https://ex.com/1", status="pending")
        session.add(pj)
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        result = repo.get_by_id(str(pj.id), "pending_jobs")
        assert result["url"] == "https://ex.com/1"

    def test_get_by_id_companies(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from shared.infrastructure.database.models.pending_model import PendingCompanyModel
        pc = PendingCompanyModel(input_text="Google", status="pending")
        session.add(pc)
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        result = repo.get_by_id(str(pc.id), "pending_companies")
        assert result["input_text"] == "Google"

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
        from shared.infrastructure.database.models.pending_model import PendingJobModel
        session.add(PendingJobModel(url="https://ex.com/1", status="done"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        result = repo.create({"url": "https://ex.com/1", "source": "api"}, "pending_jobs")
        assert result["status"] == "pending"

    def test_create_pending_company(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        repo = SQLAlchemyPendingRepository(session)
        result = repo.create({"name": "Google"}, "pending_companies")
        assert result["input_text"] == "Google"

    def test_create_unknown_table(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        repo = SQLAlchemyPendingRepository(session)
        with pytest.raises(ValueError):
            repo.create({}, "unknown")

    def test_update_status(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from shared.infrastructure.database.models.pending_model import PendingJobModel
        pj = PendingJobModel(url="https://ex.com/1", status="pending")
        session.add(pj)
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        assert repo.update_status(str(pj.id), "processing", "pending_jobs") is True

    def test_count_pending(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from shared.infrastructure.database.models.pending_model import PendingJobModel
        session.add(PendingJobModel(url="https://ex.com/1", status="pending"))
        session.add(PendingJobModel(url="https://ex.com/2", status="done"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        assert repo.count_pending("pending_jobs") == 1

    def test_count_pending_companies(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from shared.infrastructure.database.models.pending_model import PendingCompanyModel
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
        from shared.infrastructure.database.models.pending_model import PendingJobModel
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
        from shared.infrastructure.database.models.pending_model import PendingJobModel
        pj = PendingJobModel(url="https://ex.com/1", status="pending")
        session.add(pj)
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        assert repo.update_fields(pj.id, table="pending_jobs", status="processing") is True

    def test_update_fields_companies(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from shared.infrastructure.database.models.pending_model import PendingCompanyModel
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
        from shared.infrastructure.database.models.pending_model import PendingJobModel
        pj = PendingJobModel(url="https://ex.com/1")
        session.add(pj)
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        assert repo.update_step(pj.id, "step_fetch", 1, "pending_jobs") is True

    def test_save_session_id(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from shared.infrastructure.database.models.pending_model import PendingJobModel
        pj = PendingJobModel(url="https://ex.com/1")
        session.add(pj)
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        assert repo.save_session_id(pj.id, "sess123") is True

    def test_update_workflow_log(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from shared.infrastructure.database.models.pending_model import PendingJobModel
        pj = PendingJobModel(url="https://ex.com/1")
        session.add(pj)
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        assert repo.update_workflow_log(pj.id, "[\"step1\"]") is True

    def test_get_max_queue_order(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from shared.infrastructure.database.models.pending_model import PendingJobModel
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
        from shared.infrastructure.database.models.pending_model import PendingJobModel
        session.add(PendingJobModel(url="https://ex.com/1", status="processing"))
        session.add(PendingJobModel(url="https://ex.com/2", status="pending"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        assert repo.get_processing_count("pending_jobs") == 1

    def test_get_queued_count(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from shared.infrastructure.database.models.pending_model import PendingJobModel
        session.add(PendingJobModel(url="https://ex.com/1", status="queued"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        assert repo.get_queued_count("pending_jobs") == 1

    def test_get_processing_items(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from shared.infrastructure.database.models.pending_model import PendingJobModel
        session.add(PendingJobModel(url="https://ex.com/1", status="processing"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        result = repo.get_processing_items("pending_jobs")
        assert len(result) == 1

    def test_mark_processing_as_paused(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from shared.infrastructure.database.models.pending_model import PendingJobModel
        session.add(PendingJobModel(url="https://ex.com/1", status="processing"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        count = repo.mark_processing_as_paused("pending_jobs")
        assert count == 1

    def test_reset_processing_orphans(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from shared.infrastructure.database.models.pending_model import PendingJobModel
        session.add(PendingJobModel(url="https://ex.com/1", status="processing"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        count = repo.reset_processing_orphans("pending_jobs")
        assert count == 1

    def test_pick_queued_item(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from shared.infrastructure.database.models.pending_model import PendingJobModel
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
        from shared.infrastructure.database.models.pending_model import PendingCompanyModel
        session.add(PendingCompanyModel(input_text="Google", status="queued"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        result = repo.pick_queued_item("pending_companies")
        assert result["status"] == "processing"

    def test_get_queued_items(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from shared.infrastructure.database.models.pending_model import PendingJobModel
        session.add(PendingJobModel(url="https://ex.com/1", status="queued"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        result = repo.get_queued_items("pending_jobs")
        assert len(result) == 1

    def test_reset_steps(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from shared.infrastructure.database.models.pending_model import PendingJobModel
        pj = PendingJobModel(url="https://ex.com/1", status="failed", step_fetch=1)
        session.add(pj)
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        assert repo.reset_steps(pj.id, 2, "pending_jobs") is True

    def test_reset_steps_companies(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from shared.infrastructure.database.models.pending_model import PendingCompanyModel
        pc = PendingCompanyModel(input_text="Google", status="failed", step_fetch=1)
        session.add(pc)
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        assert repo.reset_steps(pc.id, 2, "pending_companies") is True

    def test_get_all_for_stream(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from shared.infrastructure.database.models.pending_model import PendingJobModel
        session.add(PendingJobModel(url="https://ex.com/1"))
        session.commit()
        repo = SQLAlchemyPendingRepository(session)
        result = repo.get_all_for_stream("pending_jobs")
        assert len(result) == 1

    def test_get_by_url_pending(self, session):
        from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
        from shared.infrastructure.database.models.pending_model import PendingJobModel
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
        assert result["input_text"] == "Google"


# ── Insight Repository ────────────────────────────────────────────

class TestSAInsightRepository:
    def test_get_all(self, session):
        from shared.infrastructure.database.sa_insight_repository import SQLAlchemyInsightRepository
        from shared.infrastructure.database.models.insight_model import CareerInsightModel
        session.add(CareerInsightModel(insight_type="skills", data_json='{"key": "val"}'))
        session.commit()
        repo = SQLAlchemyInsightRepository(session)
        result = repo.get_all()
        assert "skills" in result

    def test_get_section(self, session):
        from shared.infrastructure.database.sa_insight_repository import SQLAlchemyInsightRepository
        from shared.infrastructure.database.models.insight_model import CareerInsightModel
        session.add(CareerInsightModel(insight_type="market", data_json='{"data": 1}'))
        session.commit()
        repo = SQLAlchemyInsightRepository(session)
        result = repo.get_section("market")
        assert result["insight_type"] == "market"

    def test_get_section_not_found(self, session):
        from shared.infrastructure.database.sa_insight_repository import SQLAlchemyInsightRepository
        repo = SQLAlchemyInsightRepository(session)
        assert repo.get_section("nonexistent") is None

    def test_get_statuses(self, session):
        from shared.infrastructure.database.sa_insight_repository import SQLAlchemyInsightRepository
        from shared.infrastructure.database.models.insight_model import CareerInsightModel, CareerInsightRunModel
        session.add(CareerInsightModel(insight_type="skills", data_json='{}'))
        session.add(CareerInsightRunModel(insight_type="skills", status="completed"))
        session.commit()
        repo = SQLAlchemyInsightRepository(session)
        result = repo.get_statuses()
        assert len(result) >= 1

    def test_upsert_section_new(self, session):
        from shared.infrastructure.database.sa_insight_repository import SQLAlchemyInsightRepository
        repo = SQLAlchemyInsightRepository(session)
        repo.upsert_section("skills", {"skills": []})
        result = repo.get_section("skills")
        assert result is not None

    def test_upsert_section_existing(self, session):
        from shared.infrastructure.database.sa_insight_repository import SQLAlchemyInsightRepository
        from shared.infrastructure.database.models.insight_model import CareerInsightModel
        session.add(CareerInsightModel(insight_type="skills", data_json='{}'))
        session.commit()
        repo = SQLAlchemyInsightRepository(session)
        repo.upsert_section("skills", {"skills": [{"name": "Python"}]})
        result = repo.get_section("skills")
        assert "skills" in result["data_json"]


# ── Preference Repository ─────────────────────────────────────────

class TestSAPreferenceRepository:
    def test_get_all(self, session):
        from shared.infrastructure.database.sa_preference_repository import SQLAlchemyPreferenceRepository
        from shared.infrastructure.database.models.misc_models import PreferenceModel
        session.add(PreferenceModel(category="fit", key="remote", value="true", scope="JOB"))
        session.commit()
        repo = SQLAlchemyPreferenceRepository(session)
        result = repo.get_all()
        assert len(result) == 1

    def test_get_by_id(self, session):
        from shared.infrastructure.database.sa_preference_repository import SQLAlchemyPreferenceRepository
        from shared.infrastructure.database.models.misc_models import PreferenceModel
        pref = PreferenceModel(category="fit", key="remote", value="true")
        session.add(pref)
        session.commit()
        repo = SQLAlchemyPreferenceRepository(session)
        result = repo.get_by_id(pref.id)
        assert result["key"] == "remote"

    def test_get_by_id_not_found(self, session):
        from shared.infrastructure.database.sa_preference_repository import SQLAlchemyPreferenceRepository
        repo = SQLAlchemyPreferenceRepository(session)
        assert repo.get_by_id(999) is None

    def test_get_enabled_by_scopes(self, session):
        from shared.infrastructure.database.sa_preference_repository import SQLAlchemyPreferenceRepository
        from shared.infrastructure.database.models.misc_models import PreferenceModel
        session.add(PreferenceModel(category="fit", key="remote", value="true", scope="JOB", enabled=1))
        session.add(PreferenceModel(category="fit", key="local", value="true", scope="COMPANY", enabled=0))
        session.commit()
        repo = SQLAlchemyPreferenceRepository(session)
        result = repo.get_enabled_by_scopes(["JOB"])
        assert len(result) == 1

    def test_create(self, session):
        from shared.infrastructure.database.sa_preference_repository import SQLAlchemyPreferenceRepository
        repo = SQLAlchemyPreferenceRepository(session)
        result = repo.create({"category": "fit", "key": "remote", "value": "true"})
        assert result["key"] == "remote"

    def test_update(self, session):
        from shared.infrastructure.database.sa_preference_repository import SQLAlchemyPreferenceRepository
        from shared.infrastructure.database.models.misc_models import PreferenceModel
        pref = PreferenceModel(category="fit", key="remote", value="true")
        session.add(pref)
        session.commit()
        repo = SQLAlchemyPreferenceRepository(session)
        result = repo.update(pref.id, {"value": "false"})
        assert result["value"] == "false"

    def test_update_not_found(self, session):
        from shared.infrastructure.database.sa_preference_repository import SQLAlchemyPreferenceRepository
        repo = SQLAlchemyPreferenceRepository(session)
        assert repo.update(999, {"value": "x"}) is None

    def test_delete(self, session):
        from shared.infrastructure.database.sa_preference_repository import SQLAlchemyPreferenceRepository
        from shared.infrastructure.database.models.misc_models import PreferenceModel
        pref = PreferenceModel(category="fit", key="remote", value="true")
        session.add(pref)
        session.commit()
        repo = SQLAlchemyPreferenceRepository(session)
        assert repo.delete(pref.id) is True

    def test_delete_not_found(self, session):
        from shared.infrastructure.database.sa_preference_repository import SQLAlchemyPreferenceRepository
        repo = SQLAlchemyPreferenceRepository(session)
        assert repo.delete(999) is False

    def test_bulk_update(self, session):
        from shared.infrastructure.database.sa_preference_repository import SQLAlchemyPreferenceRepository
        from shared.infrastructure.database.models.misc_models import PreferenceModel
        pref = PreferenceModel(category="fit", key="remote", value="true")
        session.add(pref)
        session.commit()
        repo = SQLAlchemyPreferenceRepository(session)
        count = repo.bulk_update([{"id": pref.id, "value": "false", "priority": 10}])
        assert count == 1

    def test_bulk_update_skip_no_id(self, session):
        from shared.infrastructure.database.sa_preference_repository import SQLAlchemyPreferenceRepository
        repo = SQLAlchemyPreferenceRepository(session)
        count = repo.bulk_update([{"value": "false"}])
        assert count == 0


# ── Summary Repository ────────────────────────────────────────────

class TestSASummaryRepository:
    def test_get_all(self, session):
        from shared.infrastructure.database.sa_summary_repository import SQLAlchemySummaryRepository
        from shared.infrastructure.database.models.misc_models import SummaryModel
        session.add(SummaryModel(num=1, company="A", score="A"))
        session.add(SummaryModel(num=2, company="B", score="B"))
        session.commit()
        repo = SQLAlchemySummaryRepository(session)
        result = repo.get_all()
        assert len(result) == 2

    def test_get_by_num(self, session):
        from shared.infrastructure.database.sa_summary_repository import SQLAlchemySummaryRepository
        from shared.infrastructure.database.models.misc_models import SummaryModel
        session.add(SummaryModel(num=1, company="A", score="A"))
        session.commit()
        repo = SQLAlchemySummaryRepository(session)
        result = repo.get_by_num(1)
        assert result["company"] == "A"

    def test_get_by_num_not_found(self, session):
        from shared.infrastructure.database.sa_summary_repository import SQLAlchemySummaryRepository
        repo = SQLAlchemySummaryRepository(session)
        assert repo.get_by_num(999) is None

    def test_upsert_insert(self, session):
        from shared.infrastructure.database.sa_summary_repository import SQLAlchemySummaryRepository
        repo = SQLAlchemySummaryRepository(session)
        result = repo.upsert({"num": 1, "company": "A", "score": "A"})
        assert result["num"] == 1

    def test_upsert_update(self, session):
        from shared.infrastructure.database.sa_summary_repository import SQLAlchemySummaryRepository
        from shared.infrastructure.database.models.misc_models import SummaryModel
        session.add(SummaryModel(num=1, company="A"))
        session.commit()
        repo = SQLAlchemySummaryRepository(session)
        result = repo.upsert({"num": 1, "score": "A+"})
        assert result["score"] == "A+"

    def test_delete_by_num(self, session):
        from shared.infrastructure.database.sa_summary_repository import SQLAlchemySummaryRepository
        from shared.infrastructure.database.models.misc_models import SummaryModel
        session.add(SummaryModel(num=1, company="A"))
        session.commit()
        repo = SQLAlchemySummaryRepository(session)
        assert repo.delete_by_num(1) is True

    def test_delete_by_num_not_found(self, session):
        from shared.infrastructure.database.sa_summary_repository import SQLAlchemySummaryRepository
        repo = SQLAlchemySummaryRepository(session)
        assert repo.delete_by_num(999) is False

    def test_delete_all(self, session):
        from shared.infrastructure.database.sa_summary_repository import SQLAlchemySummaryRepository
        from shared.infrastructure.database.models.misc_models import SummaryModel
        session.add(SummaryModel(num=1, company="A"))
        session.add(SummaryModel(num=2, company="B"))
        session.commit()
        repo = SQLAlchemySummaryRepository(session)
        assert repo.delete_all() == 2


# ── Resume Repository ─────────────────────────────────────────────

class TestSAResumeRepository:
    def test_get_all(self, session):
        from shared.infrastructure.database.sa_resume_repository import SQLAlchemyResumeRepository
        from shared.infrastructure.database.models.misc_models import ResumeModel
        session.add(ResumeModel(id="original", title="Resume"))
        session.commit()
        repo = SQLAlchemyResumeRepository(session)
        result = repo.get_all()
        assert len(result) == 1

    def test_get_by_id(self, session):
        from shared.infrastructure.database.sa_resume_repository import SQLAlchemyResumeRepository
        from shared.infrastructure.database.models.misc_models import ResumeModel
        session.add(ResumeModel(id="original", title="Resume"))
        session.commit()
        repo = SQLAlchemyResumeRepository(session)
        result = repo.get_by_id("original")
        assert result["title"] == "Resume"

    def test_get_by_id_not_found(self, session):
        from shared.infrastructure.database.sa_resume_repository import SQLAlchemyResumeRepository
        repo = SQLAlchemyResumeRepository(session)
        assert repo.get_by_id("nonexistent") is None

    def test_upsert_insert(self, session):
        from shared.infrastructure.database.sa_resume_repository import SQLAlchemyResumeRepository
        repo = SQLAlchemyResumeRepository(session)
        result = repo.upsert({"id": "original", "title": "Resume"})
        assert result["id"] == "original"

    def test_upsert_update(self, session):
        from shared.infrastructure.database.sa_resume_repository import SQLAlchemyResumeRepository
        from shared.infrastructure.database.models.misc_models import ResumeModel
        session.add(ResumeModel(id="original", title="Old"))
        session.commit()
        repo = SQLAlchemyResumeRepository(session)
        result = repo.upsert({"id": "original", "title": "New"})
        assert result["title"] == "New"

    def test_delete_by_id(self, session):
        from shared.infrastructure.database.sa_resume_repository import SQLAlchemyResumeRepository
        from shared.infrastructure.database.models.misc_models import ResumeModel
        session.add(ResumeModel(id="original"))
        session.commit()
        repo = SQLAlchemyResumeRepository(session)
        assert repo.delete_by_id("original") is True

    def test_delete_by_id_not_found(self, session):
        from shared.infrastructure.database.sa_resume_repository import SQLAlchemyResumeRepository
        repo = SQLAlchemyResumeRepository(session)
        assert repo.delete_by_id("nonexistent") is False

    def test_get_for_job(self, session):
        from shared.infrastructure.database.sa_resume_repository import SQLAlchemyResumeRepository
        from shared.infrastructure.database.models.misc_models import ResumeModel
        session.add(ResumeModel(id="pending_1", title="Resume", job_num=1))
        session.commit()
        repo = SQLAlchemyResumeRepository(session)
        result = repo.get_for_job(1)
        assert result is not None

    def test_get_cover_for_job(self, session):
        from shared.infrastructure.database.sa_resume_repository import SQLAlchemyResumeRepository
        from shared.infrastructure.database.models.misc_models import ResumeModel
        session.add(ResumeModel(id="cover_1", title="Cover", job_num=1))
        session.commit()
        repo = SQLAlchemyResumeRepository(session)
        result = repo.get_cover_for_job(1)
        assert result is not None

    def test_get_latest_original_raw_text(self, session):
        from shared.infrastructure.database.sa_resume_repository import SQLAlchemyResumeRepository
        from shared.infrastructure.database.models.misc_models import ResumeModel
        session.add(ResumeModel(id="original_1", raw_text="Hello", version=1))
        session.commit()
        repo = SQLAlchemyResumeRepository(session)
        assert repo.get_latest_original_raw_text() == "Hello"

    def test_get_latest_original_raw_text_none(self, session):
        from shared.infrastructure.database.sa_resume_repository import SQLAlchemyResumeRepository
        repo = SQLAlchemyResumeRepository(session)
        assert repo.get_latest_original_raw_text() is None

    def test_get_latest_linkedin_raw_text(self, session):
        from shared.infrastructure.database.sa_resume_repository import SQLAlchemyResumeRepository
        from shared.infrastructure.database.models.misc_models import ResumeModel
        session.add(ResumeModel(id="linkedin_1", raw_text="LinkedIn"))
        session.commit()
        repo = SQLAlchemyResumeRepository(session)
        assert repo.get_latest_linkedin_raw_text() == "LinkedIn"

    def test_get_latest_linkedin_raw_text_none(self, session):
        from shared.infrastructure.database.sa_resume_repository import SQLAlchemyResumeRepository
        repo = SQLAlchemyResumeRepository(session)
        assert repo.get_latest_linkedin_raw_text() is None

    def test_delete_non_original(self, session):
        from shared.infrastructure.database.sa_resume_repository import SQLAlchemyResumeRepository
        from shared.infrastructure.database.models.misc_models import ResumeModel
        session.add(ResumeModel(id="original"))
        session.add(ResumeModel(id="pending_1"))
        session.add(ResumeModel(id="cover_1"))
        session.commit()
        repo = SQLAlchemyResumeRepository(session)
        count = repo.delete_non_original()
        assert count == 2


# ── Company Link Repository ───────────────────────────────────────

class TestSACompanyLinkRepository:
    def test_get_by_company_id(self, session):
        from shared.infrastructure.database.sa_company_link_repository import SQLAlchemyCompanyLinkRepository
        from shared.infrastructure.database.models.company_model import CompanyLinkModel
        session.add(CompanyLinkModel(company_id=1, url="https://ex.com", title="Main"))
        session.commit()
        repo = SQLAlchemyCompanyLinkRepository(session)
        result = repo.get_by_company_id(1)
        assert len(result) == 1

    def test_create(self, session):
        from shared.infrastructure.database.sa_company_link_repository import SQLAlchemyCompanyLinkRepository
        repo = SQLAlchemyCompanyLinkRepository(session)
        result = repo.create(1, "https://ex.com", "Main", "Description")
        assert result["url"] == "https://ex.com"

    def test_delete(self, session):
        from shared.infrastructure.database.sa_company_link_repository import SQLAlchemyCompanyLinkRepository
        from shared.infrastructure.database.models.company_model import CompanyLinkModel
        link = CompanyLinkModel(company_id=1, url="https://ex.com")
        session.add(link)
        session.commit()
        repo = SQLAlchemyCompanyLinkRepository(session)
        assert repo.delete(link.id, 1) is True

    def test_delete_not_found(self, session):
        from shared.infrastructure.database.sa_company_link_repository import SQLAlchemyCompanyLinkRepository
        repo = SQLAlchemyCompanyLinkRepository(session)
        assert repo.delete(999, 1) is False

    def test_reset_statuses(self, session):
        from shared.infrastructure.database.sa_company_link_repository import SQLAlchemyCompanyLinkRepository
        from shared.infrastructure.database.models.company_model import CompanyLinkModel
        session.add(CompanyLinkModel(company_id=1, url="https://ex.com", status="done", extracted_content="data"))
        session.commit()
        repo = SQLAlchemyCompanyLinkRepository(session)
        count = repo.reset_statuses(1)
        assert count == 1

    def test_update_status(self, session):
        from shared.infrastructure.database.sa_company_link_repository import SQLAlchemyCompanyLinkRepository
        from shared.infrastructure.database.models.company_model import CompanyLinkModel
        link = CompanyLinkModel(company_id=1, url="https://ex.com", status="pending")
        session.add(link)
        session.commit()
        repo = SQLAlchemyCompanyLinkRepository(session)
        assert repo.update_status(link.id, "done", "content") is True

    def test_update_status_not_found(self, session):
        from shared.infrastructure.database.sa_company_link_repository import SQLAlchemyCompanyLinkRepository
        repo = SQLAlchemyCompanyLinkRepository(session)
        assert repo.update_status(999, "done") is False

    def test_update_status_no_content(self, session):
        from shared.infrastructure.database.sa_company_link_repository import SQLAlchemyCompanyLinkRepository
        from shared.infrastructure.database.models.company_model import CompanyLinkModel
        link = CompanyLinkModel(company_id=1, url="https://ex.com", status="pending")
        session.add(link)
        session.commit()
        repo = SQLAlchemyCompanyLinkRepository(session)
        assert repo.update_status(link.id, "done") is True


# ── Company Intelligence Repository ───────────────────────────────

class TestSACompanyIntelligenceRepository:
    def test_get_by_company_id(self, session):
        from shared.infrastructure.database.sa_company_intelligence_repository import SQLAlchemyCompanyIntelligenceRepository
        from shared.infrastructure.database.models.company_model import CompanyIntelligenceModel
        session.add(CompanyIntelligenceModel(company_id=1, overview="Great"))
        session.commit()
        repo = SQLAlchemyCompanyIntelligenceRepository(session)
        result = repo.get_by_company_id(1)
        assert result["overview"] == "Great"

    def test_get_by_company_id_not_found(self, session):
        from shared.infrastructure.database.sa_company_intelligence_repository import SQLAlchemyCompanyIntelligenceRepository
        repo = SQLAlchemyCompanyIntelligenceRepository(session)
        assert repo.get_by_company_id(999) is None

    def test_upsert_new(self, session):
        from shared.infrastructure.database.sa_company_intelligence_repository import SQLAlchemyCompanyIntelligenceRepository
        repo = SQLAlchemyCompanyIntelligenceRepository(session)
        result = repo.upsert(1, {"overview": "Great"})
        assert result["overview"] == "Great"

    def test_upsert_existing(self, session):
        from shared.infrastructure.database.sa_company_intelligence_repository import SQLAlchemyCompanyIntelligenceRepository
        from shared.infrastructure.database.models.company_model import CompanyIntelligenceModel
        session.add(CompanyIntelligenceModel(company_id=1, overview="Old"))
        session.commit()
        repo = SQLAlchemyCompanyIntelligenceRepository(session)
        result = repo.upsert(1, {"overview": "New"})
        assert result["overview"] == "New"

    def test_delete_by_company_id(self, session):
        from shared.infrastructure.database.sa_company_intelligence_repository import SQLAlchemyCompanyIntelligenceRepository
        from shared.infrastructure.database.models.company_model import CompanyIntelligenceModel
        session.add(CompanyIntelligenceModel(company_id=1))
        session.commit()
        repo = SQLAlchemyCompanyIntelligenceRepository(session)
        assert repo.delete_by_company_id(1) is True

    def test_delete_by_company_id_not_found(self, session):
        from shared.infrastructure.database.sa_company_intelligence_repository import SQLAlchemyCompanyIntelligenceRepository
        repo = SQLAlchemyCompanyIntelligenceRepository(session)
        assert repo.delete_by_company_id(999) is False


# ── Pending Generation Repository ─────────────────────────────────

class TestSAPendingGenerationRepository:
    def test_get_by_id(self, session):
        from shared.infrastructure.database.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
        from shared.infrastructure.database.models.pending_model import PendingGenerationModel
        gen = PendingGenerationModel(job_num=1, type="resume", status="queued")
        session.add(gen)
        session.commit()
        repo = SQLAlchemyPendingGenerationRepository(session)
        result = repo.get_by_id(gen.id)
        assert result["type"] == "resume"

    def test_get_by_id_not_found(self, session):
        from shared.infrastructure.database.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
        repo = SQLAlchemyPendingGenerationRepository(session)
        assert repo.get_by_id(999) is None

    def test_create(self, session):
        from shared.infrastructure.database.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
        repo = SQLAlchemyPendingGenerationRepository(session)
        result = repo.create(1, "resume", "queued")
        assert result["job_num"] == 1

    def test_update_fields(self, session):
        from shared.infrastructure.database.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
        from shared.infrastructure.database.models.pending_model import PendingGenerationModel
        gen = PendingGenerationModel(job_num=1, type="resume", status="queued")
        session.add(gen)
        session.commit()
        repo = SQLAlchemyPendingGenerationRepository(session)
        assert repo.update_fields(gen.id, status="processing") is True

    def test_update_fields_not_found(self, session):
        from shared.infrastructure.database.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
        repo = SQLAlchemyPendingGenerationRepository(session)
        assert repo.update_fields(999, status="done") is False

    def test_get_active_for_job(self, session):
        from shared.infrastructure.database.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
        from shared.infrastructure.database.models.pending_model import PendingGenerationModel
        session.add(PendingGenerationModel(job_num=1, type="resume", status="processing"))
        session.commit()
        repo = SQLAlchemyPendingGenerationRepository(session)
        result = repo.get_active_for_job(1, "resume")
        assert result is not None

    def test_get_active_for_job_none(self, session):
        from shared.infrastructure.database.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
        repo = SQLAlchemyPendingGenerationRepository(session)
        assert repo.get_active_for_job(1, "resume") is None

    def test_get_all_active(self, session):
        from shared.infrastructure.database.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
        from shared.infrastructure.database.models.pending_model import PendingGenerationModel
        session.add(PendingGenerationModel(job_num=1, type="resume", status="processing"))
        session.add(PendingGenerationModel(job_num=2, type="cover", status="done"))
        session.commit()
        repo = SQLAlchemyPendingGenerationRepository(session)
        result = repo.get_all_active()
        assert len(result) == 1

    def test_get_history_for_job(self, session):
        from shared.infrastructure.database.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
        from shared.infrastructure.database.models.pending_model import PendingGenerationModel
        session.add(PendingGenerationModel(job_num=1, type="resume", status="done"))
        session.commit()
        repo = SQLAlchemyPendingGenerationRepository(session)
        result = repo.get_history_for_job(1)
        assert len(result) == 1

    def test_get_active_count(self, session):
        from shared.infrastructure.database.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
        from shared.infrastructure.database.models.pending_model import PendingGenerationModel
        session.add(PendingGenerationModel(job_num=1, type="resume", status="processing"))
        session.commit()
        repo = SQLAlchemyPendingGenerationRepository(session)
        assert repo.get_active_count(1) == 1


# ── Career Insight Repository ─────────────────────────────────────

class TestSACareerInsightRepository:
    def test_get_all(self, session):
        from shared.infrastructure.database.sa_career_insight_repository import SQLAlchemyCareerInsightRepository
        from shared.infrastructure.database.models.insight_model import CareerInsightModel
        session.add(CareerInsightModel(insight_type="skills", data_json='{"skills": []}'))
        session.commit()
        repo = SQLAlchemyCareerInsightRepository(session)
        result = repo.get_all()
        assert "skills" in result

    def test_get_section(self, session):
        from shared.infrastructure.database.sa_career_insight_repository import SQLAlchemyCareerInsightRepository
        from shared.infrastructure.database.models.insight_model import CareerInsightModel
        session.add(CareerInsightModel(insight_type="market", data_json='{"data": 1}'))
        session.commit()
        repo = SQLAlchemyCareerInsightRepository(session)
        result = repo.get_section("market")
        assert result["insight_type"] == "market"

    def test_get_section_not_found(self, session):
        from shared.infrastructure.database.sa_career_insight_repository import SQLAlchemyCareerInsightRepository
        repo = SQLAlchemyCareerInsightRepository(session)
        assert repo.get_section("nonexistent") is None

    def test_upsert_new(self, session):
        from shared.infrastructure.database.sa_career_insight_repository import SQLAlchemyCareerInsightRepository
        repo = SQLAlchemyCareerInsightRepository(session)
        repo.upsert("skills", {"skills": []})
        result = repo.get_section("skills")
        assert result is not None

    def test_upsert_existing(self, session):
        from shared.infrastructure.database.sa_career_insight_repository import SQLAlchemyCareerInsightRepository
        from shared.infrastructure.database.models.insight_model import CareerInsightModel
        session.add(CareerInsightModel(insight_type="skills", data_json='{}', score=5.0))
        session.commit()
        repo = SQLAlchemyCareerInsightRepository(session)
        repo.upsert("skills", {"skills": [{"name": "Python"}]}, score=9.0, summary="Great")
        result = repo.get_section("skills")
        assert result["score"] == 9.0

    def test_delete_all(self, session):
        from shared.infrastructure.database.sa_career_insight_repository import SQLAlchemyCareerInsightRepository
        from shared.infrastructure.database.models.insight_model import CareerInsightModel
        session.add(CareerInsightModel(insight_type="skills", data_json='{}'))
        session.add(CareerInsightModel(insight_type="market", data_json='{}'))
        session.commit()
        repo = SQLAlchemyCareerInsightRepository(session)
        assert repo.delete_all() == 2


# ── Career Insight Run Repository ─────────────────────────────────

class TestSACareerInsightRunRepository:
    def test_create(self, session):
        from shared.infrastructure.database.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository
        repo = SQLAlchemyCareerInsightRunRepository(session)
        result = repo.create("skills", 1, "processing", "sess123")
        assert result["insight_type"] == "skills"

    def test_complete(self, session):
        from shared.infrastructure.database.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository
        from shared.infrastructure.database.models.insight_model import CareerInsightRunModel
        run = CareerInsightRunModel(insight_type="skills", status="processing")
        session.add(run)
        session.commit()
        repo = SQLAlchemyCareerInsightRunRepository(session)
        assert repo.complete(run.id, "completed") is True

    def test_complete_not_found(self, session):
        from shared.infrastructure.database.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository
        repo = SQLAlchemyCareerInsightRunRepository(session)
        assert repo.complete(999, "completed") is False

    def test_complete_with_error(self, session):
        from shared.infrastructure.database.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository
        from shared.infrastructure.database.models.insight_model import CareerInsightRunModel
        run = CareerInsightRunModel(insight_type="skills", status="processing")
        session.add(run)
        session.commit()
        repo = SQLAlchemyCareerInsightRunRepository(session)
        assert repo.complete(run.id, "failed", "error msg", "sess123") is True

    def test_update_session_id(self, session):
        from shared.infrastructure.database.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository
        from shared.infrastructure.database.models.insight_model import CareerInsightRunModel
        run = CareerInsightRunModel(insight_type="skills", status="processing")
        session.add(run)
        session.commit()
        repo = SQLAlchemyCareerInsightRunRepository(session)
        assert repo.update_session_id(run.id, "new_sess") is True

    def test_update_session_id_not_found(self, session):
        from shared.infrastructure.database.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository
        repo = SQLAlchemyCareerInsightRunRepository(session)
        assert repo.update_session_id(999, "sess") is False

    def test_get_latest_processing(self, session):
        from shared.infrastructure.database.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository
        from shared.infrastructure.database.models.insight_model import CareerInsightRunModel
        session.add(CareerInsightRunModel(insight_type="skills", status="processing"))
        session.commit()
        repo = SQLAlchemyCareerInsightRunRepository(session)
        result = repo.get_latest_processing("skills")
        assert result is not None

    def test_get_latest_processing_none(self, session):
        from shared.infrastructure.database.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository
        repo = SQLAlchemyCareerInsightRunRepository(session)
        assert repo.get_latest_processing() is None

    def test_cleanup_stale_runs(self, session):
        from shared.infrastructure.database.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository
        from shared.infrastructure.database.models.insight_model import CareerInsightRunModel
        session.add(CareerInsightRunModel(insight_type="skills", status="processing", started_at="2020-01-01"))
        session.commit()
        repo = SQLAlchemyCareerInsightRunRepository(session)
        count = repo.cleanup_stale_runs("2025-01-01")
        assert count == 1

    def test_cancel_stale_run(self, session):
        from shared.infrastructure.database.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository
        from shared.infrastructure.database.models.insight_model import CareerInsightRunModel
        session.add(CareerInsightRunModel(insight_type="skills", status="processing"))
        session.commit()
        repo = SQLAlchemyCareerInsightRunRepository(session)
        assert repo.cancel_stale_run("skills") is True

    def test_cancel_stale_run_not_found(self, session):
        from shared.infrastructure.database.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository
        repo = SQLAlchemyCareerInsightRunRepository(session)
        assert repo.cancel_stale_run("nonexistent") is False

    def test_get_runs(self, session):
        from shared.infrastructure.database.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository
        from shared.infrastructure.database.models.insight_model import CareerInsightRunModel
        session.add(CareerInsightRunModel(insight_type="skills", status="done"))
        session.commit()
        repo = SQLAlchemyCareerInsightRunRepository(session)
        result = repo.get_runs()
        assert len(result) == 1

    def test_get_runs_filtered(self, session):
        from shared.infrastructure.database.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository
        from shared.infrastructure.database.models.insight_model import CareerInsightRunModel
        session.add(CareerInsightRunModel(insight_type="skills", status="done"))
        session.add(CareerInsightRunModel(insight_type="market", status="done"))
        session.commit()
        repo = SQLAlchemyCareerInsightRunRepository(session)
        result = repo.get_runs(insight_type="skills")
        assert len(result) == 1

    def test_get_total_count(self, session):
        from shared.infrastructure.database.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository
        from shared.infrastructure.database.models.insight_model import CareerInsightRunModel
        session.add(CareerInsightRunModel(insight_type="skills", status="done"))
        session.add(CareerInsightRunModel(insight_type="market", status="done"))
        session.commit()
        repo = SQLAlchemyCareerInsightRunRepository(session)
        assert repo.get_total_count() == 2

    def test_get_total_count_filtered(self, session):
        from shared.infrastructure.database.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository
        from shared.infrastructure.database.models.insight_model import CareerInsightRunModel
        session.add(CareerInsightRunModel(insight_type="skills", status="done"))
        session.commit()
        repo = SQLAlchemyCareerInsightRunRepository(session)
        assert repo.get_total_count("skills") == 1

    def test_get_latest_session_id(self, session):
        from shared.infrastructure.database.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository
        from shared.infrastructure.database.models.insight_model import CareerInsightRunModel
        session.add(CareerInsightRunModel(insight_type="skills", status="processing", session_id="sess123"))
        session.commit()
        repo = SQLAlchemyCareerInsightRunRepository(session)
        assert repo.get_latest_session_id("skills") == "sess123"

    def test_get_latest_session_id_none(self, session):
        from shared.infrastructure.database.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository
        repo = SQLAlchemyCareerInsightRunRepository(session)
        assert repo.get_latest_session_id("nonexistent") is None


# ── Skill Roadmap Repository ──────────────────────────────────────

class TestSASkillRoadmapRepository:
    def test_get_by_skill_name(self, session):
        from shared.infrastructure.database.sa_skill_roadmap_repository import SQLAlchemySkillRoadmapRepository
        from shared.infrastructure.database.models.misc_models import SkillRoadmapModel
        session.add(SkillRoadmapModel(skill_name="Python", title="Basics"))
        session.commit()
        repo = SQLAlchemySkillRoadmapRepository(session)
        result = repo.get_by_skill_name("Python")
        assert len(result) == 1

    def test_get_by_id(self, session):
        from shared.infrastructure.database.sa_skill_roadmap_repository import SQLAlchemySkillRoadmapRepository
        from shared.infrastructure.database.models.misc_models import SkillRoadmapModel
        rm = SkillRoadmapModel(skill_name="Python", title="Basics")
        session.add(rm)
        session.commit()
        repo = SQLAlchemySkillRoadmapRepository(session)
        result = repo.get_by_id(rm.id)
        assert result["title"] == "Basics"

    def test_get_by_id_not_found(self, session):
        from shared.infrastructure.database.sa_skill_roadmap_repository import SQLAlchemySkillRoadmapRepository
        repo = SQLAlchemySkillRoadmapRepository(session)
        assert repo.get_by_id(999) is None

    def test_delete_by_skill_name(self, session):
        from shared.infrastructure.database.sa_skill_roadmap_repository import SQLAlchemySkillRoadmapRepository
        from shared.infrastructure.database.models.misc_models import SkillRoadmapModel
        session.add(SkillRoadmapModel(skill_name="Python", title="Basics"))
        session.commit()
        repo = SQLAlchemySkillRoadmapRepository(session)
        assert repo.delete_by_skill_name("Python") == 1

    def test_get_max_version(self, session):
        from shared.infrastructure.database.sa_skill_roadmap_repository import SQLAlchemySkillRoadmapRepository
        from shared.infrastructure.database.models.misc_models import SkillRoadmapModel
        session.add(SkillRoadmapModel(skill_name="Python", title="A", version=1))
        session.add(SkillRoadmapModel(skill_name="Python", title="B", version=3))
        session.commit()
        repo = SQLAlchemySkillRoadmapRepository(session)
        assert repo.get_max_version("Python") == 3

    def test_insert_items(self, session):
        from shared.infrastructure.database.sa_skill_roadmap_repository import SQLAlchemySkillRoadmapRepository
        repo = SQLAlchemySkillRoadmapRepository(session)
        count = repo.insert_items("Python", [{"title": "A", "level": 0}, {"title": "B", "level": 1}], 1)
        assert count == 2

    def test_get_all(self, session):
        from shared.infrastructure.database.sa_skill_roadmap_repository import SQLAlchemySkillRoadmapRepository
        from shared.infrastructure.database.models.misc_models import SkillRoadmapModel
        session.add(SkillRoadmapModel(skill_name="Python", title="A"))
        session.add(SkillRoadmapModel(skill_name="Java", title="B"))
        session.commit()
        repo = SQLAlchemySkillRoadmapRepository(session)
        result = repo.get_all()
        assert len(result) == 2


# ── Skill Roadmap Progress Repository ─────────────────────────────

class TestSASkillRoadmapProgressRepository:
    def test_get_completed_titles(self, session):
        from shared.infrastructure.database.sa_skill_roadmap_progress_repository import SQLAlchemySkillRoadmapProgressRepository
        from shared.infrastructure.database.models.misc_models import SkillRoadmapModel, SkillRoadmapProgressModel
        rm = SkillRoadmapModel(skill_name="Python", title="Basics")
        session.add(rm)
        session.commit()
        session.add(SkillRoadmapProgressModel(roadmap_id=rm.id, skill_name="Python", completed=1))
        session.commit()
        repo = SQLAlchemySkillRoadmapProgressRepository(session)
        result = repo.get_completed_titles("Python")
        assert "Basics" in result

    def test_get_by_roadmap_id(self, session):
        from shared.infrastructure.database.sa_skill_roadmap_progress_repository import SQLAlchemySkillRoadmapProgressRepository
        from shared.infrastructure.database.models.misc_models import SkillRoadmapModel, SkillRoadmapProgressModel
        rm = SkillRoadmapModel(skill_name="Python", title="Basics")
        session.add(rm)
        session.commit()
        session.add(SkillRoadmapProgressModel(roadmap_id=rm.id, skill_name="Python", completed=1))
        session.commit()
        repo = SQLAlchemySkillRoadmapProgressRepository(session)
        result = repo.get_by_roadmap_id(rm.id)
        assert result["completed"] == 1

    def test_get_by_roadmap_id_not_found(self, session):
        from shared.infrastructure.database.sa_skill_roadmap_progress_repository import SQLAlchemySkillRoadmapProgressRepository
        repo = SQLAlchemySkillRoadmapProgressRepository(session)
        assert repo.get_by_roadmap_id(999) is None

    def test_toggle_existing(self, session):
        from shared.infrastructure.database.sa_skill_roadmap_progress_repository import SQLAlchemySkillRoadmapProgressRepository
        from shared.infrastructure.database.models.misc_models import SkillRoadmapModel, SkillRoadmapProgressModel
        rm = SkillRoadmapModel(skill_name="Python", title="Basics")
        session.add(rm)
        session.commit()
        session.add(SkillRoadmapProgressModel(roadmap_id=rm.id, skill_name="Python", completed=1))
        session.commit()
        repo = SQLAlchemySkillRoadmapProgressRepository(session)
        result = repo.toggle(rm.id, "Python")
        assert result["completed"] == 0

    def test_toggle_new(self, session):
        from shared.infrastructure.database.sa_skill_roadmap_progress_repository import SQLAlchemySkillRoadmapProgressRepository
        from shared.infrastructure.database.models.misc_models import SkillRoadmapModel
        rm = SkillRoadmapModel(skill_name="Python", title="Basics")
        session.add(rm)
        session.commit()
        repo = SQLAlchemySkillRoadmapProgressRepository(session)
        result = repo.toggle(rm.id, "Python")
        assert result["completed"] == 1

    def test_set_completed_existing(self, session):
        from shared.infrastructure.database.sa_skill_roadmap_progress_repository import SQLAlchemySkillRoadmapProgressRepository
        from shared.infrastructure.database.models.misc_models import SkillRoadmapModel, SkillRoadmapProgressModel
        rm = SkillRoadmapModel(skill_name="Python", title="Basics")
        session.add(rm)
        session.commit()
        session.add(SkillRoadmapProgressModel(roadmap_id=rm.id, skill_name="Python", completed=0))
        session.commit()
        repo = SQLAlchemySkillRoadmapProgressRepository(session)
        result = repo.set_completed(rm.id, 1)
        assert result["completed"] == 1

    def test_set_completed_new(self, session):
        from shared.infrastructure.database.sa_skill_roadmap_progress_repository import SQLAlchemySkillRoadmapProgressRepository
        from shared.infrastructure.database.models.misc_models import SkillRoadmapModel
        rm = SkillRoadmapModel(skill_name="Python", title="Basics")
        session.add(rm)
        session.commit()
        repo = SQLAlchemySkillRoadmapProgressRepository(session)
        result = repo.set_completed(rm.id, 1)
        assert result["completed"] == 1

    def test_get_all(self, session):
        from shared.infrastructure.database.sa_skill_roadmap_progress_repository import SQLAlchemySkillRoadmapProgressRepository
        from shared.infrastructure.database.models.misc_models import SkillRoadmapModel, SkillRoadmapProgressModel
        rm = SkillRoadmapModel(skill_name="Python", title="Basics")
        session.add(rm)
        session.commit()
        session.add(SkillRoadmapProgressModel(roadmap_id=rm.id, skill_name="Python"))
        session.commit()
        repo = SQLAlchemySkillRoadmapProgressRepository(session)
        result = repo.get_all()
        assert len(result) == 1

    def test_get_by_skill(self, session):
        from shared.infrastructure.database.sa_skill_roadmap_progress_repository import SQLAlchemySkillRoadmapProgressRepository
        from shared.infrastructure.database.models.misc_models import SkillRoadmapModel, SkillRoadmapProgressModel
        rm = SkillRoadmapModel(skill_name="Python", title="Basics")
        session.add(rm)
        session.commit()
        session.add(SkillRoadmapProgressModel(roadmap_id=rm.id, skill_name="Python", completed=1))
        session.commit()
        repo = SQLAlchemySkillRoadmapProgressRepository(session)
        result = repo.get_by_skill("Python")
        assert rm.id in result

    def test_get_all_aggregated(self, session):
        from shared.infrastructure.database.sa_skill_roadmap_progress_repository import SQLAlchemySkillRoadmapProgressRepository
        from shared.infrastructure.database.models.misc_models import SkillRoadmapModel, SkillRoadmapProgressModel
        rm = SkillRoadmapModel(skill_name="Python", title="Basics")
        session.add(rm)
        session.commit()
        session.add(SkillRoadmapProgressModel(roadmap_id=rm.id, skill_name="Python", completed=1))
        session.commit()
        repo = SQLAlchemySkillRoadmapProgressRepository(session)
        result = repo.get_all_aggregated()
        assert "Python" in result
        assert result["Python"]["total"] == 1
        assert result["Python"]["completed"] == 1


# ── Skill Roadmap Job Repository ──────────────────────────────────

class TestSASkillRoadmapJobRepository:
    def test_create(self, session):
        from shared.infrastructure.database.sa_skill_roadmap_job_repository import SQLAlchemySkillRoadmapJobRepository
        repo = SQLAlchemySkillRoadmapJobRepository(session)
        result = repo.create("Python", "generate", "queued")
        assert result["skill_name"] == "Python"

    def test_update(self, session):
        from shared.infrastructure.database.sa_skill_roadmap_job_repository import SQLAlchemySkillRoadmapJobRepository
        from shared.infrastructure.database.models.misc_models import SkillRoadmapJobModel
        job = SkillRoadmapJobModel(skill_name="Python", status="queued")
        session.add(job)
        session.commit()
        repo = SQLAlchemySkillRoadmapJobRepository(session)
        assert repo.update(job.id, status="done") is True

    def test_update_not_found(self, session):
        from shared.infrastructure.database.sa_skill_roadmap_job_repository import SQLAlchemySkillRoadmapJobRepository
        repo = SQLAlchemySkillRoadmapJobRepository(session)
        assert repo.update(999, status="done") is False

    def test_get_latest_for_skill(self, session):
        from shared.infrastructure.database.sa_skill_roadmap_job_repository import SQLAlchemySkillRoadmapJobRepository
        from shared.infrastructure.database.models.misc_models import SkillRoadmapJobModel
        session.add(SkillRoadmapJobModel(skill_name="Python", status="done"))
        session.commit()
        repo = SQLAlchemySkillRoadmapJobRepository(session)
        result = repo.get_latest_for_skill("Python")
        assert result is not None

    def test_get_latest_for_skill_not_found(self, session):
        from shared.infrastructure.database.sa_skill_roadmap_job_repository import SQLAlchemySkillRoadmapJobRepository
        repo = SQLAlchemySkillRoadmapJobRepository(session)
        assert repo.get_latest_for_skill("Nonexistent") is None

    def test_get_all(self, session):
        from shared.infrastructure.database.sa_skill_roadmap_job_repository import SQLAlchemySkillRoadmapJobRepository
        from shared.infrastructure.database.models.misc_models import SkillRoadmapJobModel
        session.add(SkillRoadmapJobModel(skill_name="Python", status="done"))
        session.commit()
        repo = SQLAlchemySkillRoadmapJobRepository(session)
        result = repo.get_all()
        assert len(result) == 1

    def test_get_for_skill(self, session):
        from shared.infrastructure.database.sa_skill_roadmap_job_repository import SQLAlchemySkillRoadmapJobRepository
        from shared.infrastructure.database.models.misc_models import SkillRoadmapJobModel
        session.add(SkillRoadmapJobModel(skill_name="Python", status="done"))
        session.add(SkillRoadmapJobModel(skill_name="Java", status="done"))
        session.commit()
        repo = SQLAlchemySkillRoadmapJobRepository(session)
        result = repo.get_for_skill("Python")
        assert len(result) == 1


# ── Tech Learning Repository ──────────────────────────────────────

class TestSATechLearningRepository:
    def test_get_all(self, session):
        from shared.infrastructure.database.sa_tech_learning_repository import SQLAlchemyTechLearningRepository
        from shared.infrastructure.database.models.misc_models import TechLearningModel
        session.add(TechLearningModel(name="Python", priority=1))
        session.commit()
        repo = SQLAlchemyTechLearningRepository(session)
        result = repo.get_all()
        assert len(result) == 1

    def test_get_by_id(self, session):
        from shared.infrastructure.database.sa_tech_learning_repository import SQLAlchemyTechLearningRepository
        from shared.infrastructure.database.models.misc_models import TechLearningModel
        tl = TechLearningModel(name="Python", priority=1)
        session.add(tl)
        session.commit()
        repo = SQLAlchemyTechLearningRepository(session)
        result = repo.get_by_id(tl.id)
        assert result["name"] == "Python"

    def test_get_by_id_not_found(self, session):
        from shared.infrastructure.database.sa_tech_learning_repository import SQLAlchemyTechLearningRepository
        repo = SQLAlchemyTechLearningRepository(session)
        assert repo.get_by_id(999) is None

    def test_upsert_new(self, session):
        from shared.infrastructure.database.sa_tech_learning_repository import SQLAlchemyTechLearningRepository
        repo = SQLAlchemyTechLearningRepository(session)
        result = repo.upsert({"name": "Go", "priority": 5})
        assert result["name"] == "Go"

    def test_upsert_existing(self, session):
        from shared.infrastructure.database.sa_tech_learning_repository import SQLAlchemyTechLearningRepository
        from shared.infrastructure.database.models.misc_models import TechLearningModel
        tl = TechLearningModel(name="Python", priority=1)
        session.add(tl)
        session.commit()
        repo = SQLAlchemyTechLearningRepository(session)
        result = repo.upsert({"id": tl.id, "name": "Python3", "priority": 10})
        assert result["name"] == "Python3"


# ── Skill Alias Repository ────────────────────────────────────────

class TestSASkillAliasRepository:
    def test_get_by_skill_id(self, session):
        from shared.infrastructure.database.sa_skill_alias_repository import SQLAlchemySkillAliasRepository
        from shared.infrastructure.database.models.skill_model import SkillModel, SkillAliasModel
        skill = SkillModel(name="Python")
        session.add(skill)
        session.commit()
        session.add(SkillAliasModel(skill_id=skill.id, alias_name="Python3", normalized_name="python3"))
        session.commit()
        repo = SQLAlchemySkillAliasRepository(session)
        result = repo.get_by_skill_id(skill.id)
        assert len(result) == 1

    def test_resolve_name(self, session):
        from shared.infrastructure.database.sa_skill_alias_repository import SQLAlchemySkillAliasRepository
        from shared.infrastructure.database.models.skill_model import SkillModel, SkillAliasModel
        skill = SkillModel(name="Python")
        session.add(skill)
        session.commit()
        session.add(SkillAliasModel(skill_id=skill.id, alias_name="Python3", normalized_name="python3"))
        session.commit()
        repo = SQLAlchemySkillAliasRepository(session)
        result = repo.resolve_name("Python3")
        assert result["name"] == "Python"

    def test_resolve_name_not_found(self, session):
        from shared.infrastructure.database.sa_skill_alias_repository import SQLAlchemySkillAliasRepository
        repo = SQLAlchemySkillAliasRepository(session)
        assert repo.resolve_name("Nonexistent") is None

    def test_resolve_name_skill_deleted(self, session):
        from shared.infrastructure.database.sa_skill_alias_repository import SQLAlchemySkillAliasRepository
        from shared.infrastructure.database.models.skill_model import SkillAliasModel
        session.add(SkillAliasModel(skill_id=999, alias_name="Ghost", normalized_name="ghost"))
        session.commit()
        repo = SQLAlchemySkillAliasRepository(session)
        assert repo.resolve_name("Ghost") is None

    def test_create(self, session):
        from shared.infrastructure.database.sa_skill_alias_repository import SQLAlchemySkillAliasRepository
        from shared.infrastructure.database.models.skill_model import SkillModel
        skill = SkillModel(name="Python")
        session.add(skill)
        session.commit()
        repo = SQLAlchemySkillAliasRepository(session)
        result = repo.create(skill.id, "Python3")
        assert result["alias_name"] == "Python3"

    def test_exists(self, session):
        from shared.infrastructure.database.sa_skill_alias_repository import SQLAlchemySkillAliasRepository
        from shared.infrastructure.database.models.skill_model import SkillModel, SkillAliasModel
        skill = SkillModel(name="Python")
        session.add(skill)
        session.commit()
        session.add(SkillAliasModel(skill_id=skill.id, alias_name="Python3"))
        session.commit()
        repo = SQLAlchemySkillAliasRepository(session)
        assert repo.exists(skill.id, "Python3") is True

    def test_exists_false(self, session):
        from shared.infrastructure.database.sa_skill_alias_repository import SQLAlchemySkillAliasRepository
        from shared.infrastructure.database.models.skill_model import SkillModel
        skill = SkillModel(name="Python")
        session.add(skill)
        session.commit()
        repo = SQLAlchemySkillAliasRepository(session)
        assert repo.exists(skill.id, "Python3") is False

    def test_delete_by_skill_id(self, session):
        from shared.infrastructure.database.sa_skill_alias_repository import SQLAlchemySkillAliasRepository
        from shared.infrastructure.database.models.skill_model import SkillModel, SkillAliasModel
        skill = SkillModel(name="Python")
        session.add(skill)
        session.commit()
        session.add(SkillAliasModel(skill_id=skill.id, alias_name="Python3"))
        session.commit()
        repo = SQLAlchemySkillAliasRepository(session)
        count = repo.delete_by_skill_id(skill.id)
        assert count == 1


# ── Skill Relationship Repository ─────────────────────────────────

class TestSASkillRelationshipRepository:
    def test_get_for_skill(self, session):
        from shared.infrastructure.database.sa_skill_relationship_repository import SQLAlchemySkillRelationshipRepository
        from shared.infrastructure.database.models.skill_model import SkillRelationshipModel
        session.add(SkillRelationshipModel(skill_name="Python", related_name="Django", relation_type="related"))
        session.commit()
        repo = SQLAlchemySkillRelationshipRepository(session)
        result = repo.get_for_skill("Python")
        assert len(result) == 1

    def test_get_for_skill_reverse(self, session):
        from shared.infrastructure.database.sa_skill_relationship_repository import SQLAlchemySkillRelationshipRepository
        from shared.infrastructure.database.models.skill_model import SkillRelationshipModel
        session.add(SkillRelationshipModel(skill_name="Python", related_name="Django", relation_type="related"))
        session.commit()
        repo = SQLAlchemySkillRelationshipRepository(session)
        result = repo.get_for_skill("Django")
        assert len(result) == 1

    def test_exists(self, session):
        from shared.infrastructure.database.sa_skill_relationship_repository import SQLAlchemySkillRelationshipRepository
        from shared.infrastructure.database.models.skill_model import SkillRelationshipModel
        session.add(SkillRelationshipModel(skill_name="Python", related_name="Django", relation_type="related"))
        session.commit()
        repo = SQLAlchemySkillRelationshipRepository(session)
        assert repo.exists("Python", "Django", "related") is True

    def test_exists_false(self, session):
        from shared.infrastructure.database.sa_skill_relationship_repository import SQLAlchemySkillRelationshipRepository
        repo = SQLAlchemySkillRelationshipRepository(session)
        assert repo.exists("Python", "Django", "related") is False

    def test_create(self, session):
        from shared.infrastructure.database.sa_skill_relationship_repository import SQLAlchemySkillRelationshipRepository
        repo = SQLAlchemySkillRelationshipRepository(session)
        result = repo.create("Python", "Django", "related", 0.9)
        assert result is True

    def test_create_duplicate(self, session):
        from shared.infrastructure.database.sa_skill_relationship_repository import SQLAlchemySkillRelationshipRepository
        from shared.infrastructure.database.models.skill_model import SkillRelationshipModel
        session.add(SkillRelationshipModel(skill_name="Python", related_name="Django", relation_type="related"))
        session.commit()
        repo = SQLAlchemySkillRelationshipRepository(session)
        result = repo.create("Python", "Django", "related")
        assert result is False

    def test_delete(self, session):
        from shared.infrastructure.database.sa_skill_relationship_repository import SQLAlchemySkillRelationshipRepository
        from shared.infrastructure.database.models.skill_model import SkillRelationshipModel
        rel = SkillRelationshipModel(skill_name="Python", related_name="Django", relation_type="related")
        session.add(rel)
        session.commit()
        repo = SQLAlchemySkillRelationshipRepository(session)
        assert repo.delete(rel.id) is True

    def test_delete_not_found(self, session):
        from shared.infrastructure.database.sa_skill_relationship_repository import SQLAlchemySkillRelationshipRepository
        repo = SQLAlchemySkillRelationshipRepository(session)
        assert repo.delete(999) is False

    def test_delete_all(self, session):
        from shared.infrastructure.database.sa_skill_relationship_repository import SQLAlchemySkillRelationshipRepository
        from shared.infrastructure.database.models.skill_model import SkillRelationshipModel
        session.add(SkillRelationshipModel(skill_name="A", related_name="B", relation_type="related"))
        session.add(SkillRelationshipModel(skill_name="C", related_name="D", relation_type="related"))
        session.commit()
        repo = SQLAlchemySkillRelationshipRepository(session)
        assert repo.delete_all() == 2
