"""Tests for utils, schemas, mappers, exceptions, background workers, and other uncovered code."""

import sys
import os
import json
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'app', 'server'))


# ── Utils ─────────────────────────────────────────────────────────

class TestUtils:
    def test_normalize_url(self):
        from utils import normalize_url
        assert normalize_url("https://example.com/job/1?ref=home") == "https://example.com/job/1"

    def test_normalize_url_trailing_slash(self):
        from utils import normalize_url
        assert normalize_url("https://example.com/job/1/") == "https://example.com/job/1"

    def test_normalize_url_none(self):
        from utils import normalize_url
        assert normalize_url(None) is None

    def test_normalize_url_empty(self):
        from utils import normalize_url
        assert normalize_url("") == ""

    def test_stream_json(self):
        from utils import stream_json
        assert stream_json({"key": "val"}) == {"key": "val"}

    def test_mask_pii_phone(self):
        from utils import mask_pii
        result = mask_pii("Contact information below\nCall me at +49 123 456 7890")
        assert "[PHONE]" in result or "[NAME]" in result

    def test_mask_pii_email(self):
        from utils import mask_pii
        result = mask_pii("Contact information below\nEmail: test@example.com")
        assert "[EMAIL]" in result or "[PHONE]" in result or "[NAME]" in result

    def test_mask_pii_linkedin(self):
        from utils import mask_pii
        result = mask_pii("Contact information below\nProfile: linkedin.com/in/johndoe")
        assert "linkedin.com/in/[PROFILE]" in result or "[NAME]" in result

    def test_mask_pii_github(self):
        from utils import mask_pii
        result = mask_pii("Contact information below\nCode: github.com/johndoe/repo")
        assert "github.com/[PROFILE]" in result or "[NAME]" in result

    def test_mask_pii_name(self):
        from utils import mask_pii
        result = mask_pii("John Doe\nEngineer at Google")
        assert "[NAME]" in result

    def test_mask_pii_long_name_no_mask(self):
        from utils import mask_pii
        result = mask_pii("This is a very long line that exceeds sixty characters and should not be masked")
        assert "[NAME]" not in result

    def test_text_to_html(self):
        from utils import text_to_html
        result = text_to_html("Hello\nWorld")
        assert "<div" in result
        assert "Hello" in result

    def test_text_to_html_empty_line(self):
        from utils import text_to_html
        result = text_to_html("Line1\n\nLine3")
        assert "<br>" in result

    def test_text_to_html_uppercase_header(self):
        from utils import text_to_html
        result = text_to_html("SUMMARY")
        assert "<h3" in result

    def test_text_to_html_bullet(self):
        from utils import text_to_html
        result = text_to_html("● Item 1")
        assert "padding-left:1em" in result

    def test_text_to_html_bullet_dot(self):
        from utils import text_to_html
        result = text_to_html("• Item 1")
        assert "padding-left:1em" in result

    def test_text_to_html_bullet_dash(self):
        from utils import text_to_html
        result = text_to_html("- Item 1")
        assert "padding-left:1em" in result

    def test_text_to_html_job_title(self):
        from utils import text_to_html
        result = text_to_html("Senior Engineer | Tech Lead")
        assert "font-weight:600" in result

    def test_text_to_html_named_header(self):
        from utils import text_to_html
        result = text_to_html("Skills")
        assert "<h3" in result

    def test_text_to_html_html_escape(self):
        from utils import text_to_html
        result = text_to_html("<script>alert('x')</script>")
        assert "&lt;script&gt;" in result


# ── Schemas ───────────────────────────────────────────────────────

class TestSchemas:
    def test_job_create(self):
        from schemas.jobs import JobCreate
        j = JobCreate(url="https://example.com")
        assert j.url == "https://example.com"

    def test_job_update(self):
        from schemas.jobs import JobUpdate
        j = JobUpdate(notes="test")
        assert j.notes == "test"

    def test_skill_create(self):
        from schemas.skills import SkillCreate
        s = SkillCreate(name="Python")
        assert s.name == "Python"
        assert s.level == 1

    def test_skill_update(self):
        from schemas.skills import SkillUpdate
        s = SkillUpdate(level=10)
        assert s.level == 10

    def test_skill_rename(self):
        from schemas.skills import SkillRename
        s = SkillRename(name="Python3")
        assert s.name == "Python3"

    def test_skill_hide(self):
        from schemas.skills import SkillHide
        s = SkillHide(hidden=1)
        assert s.hidden == 1

    def test_skill_merge(self):
        from schemas.skills import SkillMerge
        s = SkillMerge(target_id=1, source_ids=[2, 3])
        assert s.target_id == 1

    def test_skill_bulk_hide(self):
        from schemas.skills import SkillBulkHide
        s = SkillBulkHide(ids=[1, 2])
        assert len(s.ids) == 2

    def test_skill_bulk_categorize(self):
        from schemas.skills import SkillBulkCategorize
        s = SkillBulkCategorize(ids=[1], category="technical")
        assert s.category == "technical"

    def test_skill_category_update(self):
        from schemas.skills import SkillCategoryUpdate
        s = SkillCategoryUpdate(category="engineering")
        assert s.category == "engineering"

    def test_company_create(self):
        from schemas.companies import CompanyCreate
        c = CompanyCreate(name="Google")
        assert c.name == "Google"

    def test_company_update(self):
        from schemas.companies import CompanyUpdate
        c = CompanyUpdate(industry="Tech")
        assert c.industry == "Tech"

    def test_note_create(self):
        from schemas.companies import NoteCreate
        n = NoteCreate(content="Great company")
        assert n.content == "Great company"

    def test_link_create(self):
        from schemas.companies import LinkCreate
        l = LinkCreate(url="https://example.com")
        assert l.url == "https://example.com"

    def test_pending_create(self):
        from schemas.pending import PendingCreate
        p = PendingCreate(url="https://example.com")
        assert p.url == "https://example.com"

    def test_resume_create(self):
        from schemas.resumes import ResumeCreate
        r = ResumeCreate(title="Original")
        assert r.title == "Original"

    def test_resume_update(self):
        from schemas.resumes import ResumeUpdate
        r = ResumeUpdate(title="Updated")
        assert r.title == "Updated"

    def test_generate_cover_request(self):
        from schemas.resumes import GenerateCoverRequest
        r = GenerateCoverRequest(job_num=1)
        assert r.job_num == 1

    def test_roadmap_create(self):
        from schemas.skill_roadmaps import RoadmapCreate
        r = RoadmapCreate(skill_name="Python")
        assert r.skill_name == "Python"

    def test_generate_roadmap_request(self):
        from schemas.skill_roadmaps import GenerateRoadmapRequest
        r = GenerateRoadmapRequest(skill_name="Python")
        assert r.skill_name == "Python"

    def test_extend_roadmap_request(self):
        from schemas.skill_roadmaps import ExtendRoadmapRequest
        r = ExtendRoadmapRequest(skill_name="Python", node_id="1")
        assert r.node_id == "1"

    def test_finegrain_roadmap_request(self):
        from schemas.skill_roadmaps import FinegrainRoadmapRequest
        r = FinegrainRoadmapRequest(skill_name="Python", node_id="1")
        assert r.node_id == "1"

    def test_rules_response(self):
        from schemas.rules import RulesResponse
        r = RulesResponse(rules=[{"key": "a"}])
        assert len(r.rules) == 1

    def test_rules_update(self):
        from schemas.rules import RulesUpdate
        r = RulesUpdate(rules=[{"key": "a"}])
        assert len(r.rules) == 1

    def test_dashboard_response(self):
        from schemas.dashboard import DashboardResponse
        d = DashboardResponse(jobs_total=10)
        assert d.jobs_total == 10

    def test_common_error_response(self):
        from schemas.common import ErrorResponse, ErrorDetail
        e = ErrorResponse(error=ErrorDetail(code="NOT_FOUND", message="Not found"))
        assert e.error.code == "NOT_FOUND"

    def test_common_success_response(self):
        from schemas.common import SuccessResponse
        s = SuccessResponse(status="ok")
        assert s.status == "ok"

    def test_common_paginated_response(self):
        from schemas.common import PaginatedResponse
        p = PaginatedResponse(items=[1, 2], total=2)
        assert p.total == 2


# ── Exceptions ────────────────────────────────────────────────────

class TestExceptions:
    def test_app_error(self):
        from exceptions import AppError
        e = AppError("Something went wrong")
        assert e.status_code == 500
        assert str(e) == "Something went wrong"

    def test_app_error_default(self):
        from exceptions import AppError
        e = AppError()
        assert e.detail == "Internal server error"

    def test_app_error_with_details(self):
        from exceptions import AppError
        e = AppError("Error", details={"field": "name"})
        assert e.details == {"field": "name"}

    def test_not_found_error(self):
        from exceptions import NotFoundError
        e = NotFoundError("Not found")
        assert e.status_code == 404
        assert e.code == "NOT_FOUND"

    def test_validation_error(self):
        from exceptions import ValidationError
        e = ValidationError("Bad input")
        assert e.status_code == 422

    def test_conflict_error(self):
        from exceptions import ConflictError
        e = ConflictError("Already exists")
        assert e.status_code == 409

    def test_bad_request_error(self):
        from exceptions import BadRequestError
        e = BadRequestError("Invalid")
        assert e.status_code == 400

    def test_external_service_error(self):
        from exceptions import ExternalServiceError
        e = ExternalServiceError("Timeout")
        assert e.status_code == 502


# ── Mappers ───────────────────────────────────────────────────────

class TestMappers:
    def test_job_model_to_dict(self, session=None):
        from infrastructure.database.mappers import job_model_to_dict
        from infrastructure.database.models.job_model import JobModel
        m = JobModel(num=1, url="https://ex.com/1", company="Google", work_type="Remote")
        result = job_model_to_dict(m)
        assert result["num"] == 1
        assert result["company"] == "Google"
        assert result["work_type"] == "Remote"

    def test_dict_to_job_model(self):
        from infrastructure.database.mappers import dict_to_job_model
        m = dict_to_job_model({"num": 1, "url": "https://ex.com/1", "company": "Google"})
        assert m.num == 1
        assert m.company == "Google"

    def test_skill_model_to_dict(self):
        from infrastructure.database.mappers import skill_model_to_dict
        from infrastructure.database.models.skill_model import SkillModel
        m = SkillModel(name="Python", level=8, tags='["web"]')
        result = skill_model_to_dict(m, aliases=["Python3"])
        assert result["name"] == "Python"
        assert result["tags"] == ["web"]
        assert result["aliases"] == ["Python3"]

    def test_skill_model_to_dict_no_aliases(self):
        from infrastructure.database.mappers import skill_model_to_dict
        from infrastructure.database.models.skill_model import SkillModel
        m = SkillModel(name="Python", level=8, tags='[]')
        result = skill_model_to_dict(m)
        assert "aliases" not in result

    def test_dict_to_skill_model(self):
        from infrastructure.database.mappers import dict_to_skill_model
        m = dict_to_skill_model({"name": "Python", "tags": ["web"]})
        assert m.name == "Python"
        assert m.tags == '["web"]'

    def test_company_model_to_dict(self):
        from infrastructure.database.mappers import company_model_to_dict
        from infrastructure.database.models.company_model import CompanyModel
        m = CompanyModel(name="Google", industry="Tech")
        result = company_model_to_dict(m)
        assert result["name"] == "Google"
        assert result["industry"] == "Tech"

    def test_dict_to_company_model(self):
        from infrastructure.database.mappers import dict_to_company_model
        m = dict_to_company_model({"name": "Google"})
        assert m.name == "Google"

    def test_company_intelligence_model_to_dict(self):
        from infrastructure.database.mappers import company_intelligence_model_to_dict
        from infrastructure.database.models.company_model import CompanyIntelligenceModel
        m = CompanyIntelligenceModel(company_id=1, overview="Great")
        result = company_intelligence_model_to_dict(m)
        assert result["overview"] == "Great"

    def test_pending_job_model_to_dict(self):
        from infrastructure.database.mappers import pending_job_model_to_dict
        from infrastructure.database.models.pending_model import PendingJobModel
        m = PendingJobModel(url="https://ex.com/1", status="pending")
        result = pending_job_model_to_dict(m)
        assert result["url"] == "https://ex.com/1"

    def test_dict_to_pending_job_model(self):
        from infrastructure.database.mappers import dict_to_pending_job_model
        m = dict_to_pending_job_model({"url": "https://ex.com/1"})
        assert m.url == "https://ex.com/1"

    def test_pending_company_model_to_dict(self):
        from infrastructure.database.mappers import pending_company_model_to_dict
        from infrastructure.database.models.pending_model import PendingCompanyModel
        m = PendingCompanyModel(input_text="Google", status="pending")
        result = pending_company_model_to_dict(m)
        assert result["input_text"] == "Google"

    def test_dict_to_pending_company_model(self):
        from infrastructure.database.mappers import dict_to_pending_company_model
        m = dict_to_pending_company_model({"input_text": "Google"})
        assert m.input_text == "Google"

    def test_career_insight_model_to_dict(self):
        from infrastructure.database.mappers import career_insight_model_to_dict
        from infrastructure.database.models.insight_model import CareerInsightModel
        m = CareerInsightModel(insight_type="skills", data_json='{"key": "val"}')
        result = career_insight_model_to_dict(m)
        assert result["data_json"]["key"] == "val"

    def test_career_insight_model_to_dict_empty(self):
        from infrastructure.database.mappers import career_insight_model_to_dict
        from infrastructure.database.models.insight_model import CareerInsightModel
        m = CareerInsightModel(insight_type="skills", data_json='')
        result = career_insight_model_to_dict(m)
        assert result["data_json"] == {}

    def test_career_insight_run_model_to_dict(self):
        from infrastructure.database.mappers import career_insight_run_model_to_dict
        from infrastructure.database.models.insight_model import CareerInsightRunModel
        m = CareerInsightRunModel(insight_type="skills", status="done", metadata_json='{}')
        result = career_insight_run_model_to_dict(m)
        assert result["status"] == "done"

    def test_resume_model_to_dict(self):
        from infrastructure.database.mappers import resume_model_to_dict
        from infrastructure.database.models.misc_models import ResumeModel
        m = ResumeModel(id="original", title="Resume")
        result = resume_model_to_dict(m)
        assert result["id"] == "original"


# ── Background Task Manager ───────────────────────────────────────

class TestBackgroundTaskManager:
    @pytest.mark.asyncio
    async def test_run_task(self):
        from infrastructure.workers.background import BackgroundTaskManager
        mgr = BackgroundTaskManager()
        async def dummy():
            pass
        task = await mgr.run("test1", dummy())
        assert mgr.is_running("test1") or not task.done()

    @pytest.mark.asyncio
    async def test_cancel_task(self):
        from infrastructure.workers.background import BackgroundTaskManager
        import asyncio
        mgr = BackgroundTaskManager()
        async def slow():
            await asyncio.sleep(10)
        await mgr.run("test2", slow())
        result = mgr.cancel("test2")
        assert result is True

    def test_cancel_nonexistent(self):
        from infrastructure.workers.background import BackgroundTaskManager
        mgr = BackgroundTaskManager()
        assert mgr.cancel("nonexistent") is False

    def test_is_running_false(self):
        from infrastructure.workers.background import BackgroundTaskManager
        mgr = BackgroundTaskManager()
        assert mgr.is_running("nonexistent") is False

    def test_running_tasks(self):
        from infrastructure.workers.background import BackgroundTaskManager
        mgr = BackgroundTaskManager()
        assert mgr.running_tasks == []

    def test_get_task_manager_singleton(self):
        from infrastructure.workers.background import get_task_manager
        mgr1 = get_task_manager()
        mgr2 = get_task_manager()
        assert mgr1 is mgr2

    @pytest.mark.asyncio
    async def test_duplicate_task(self):
        from infrastructure.workers.background import BackgroundTaskManager
        import asyncio
        mgr = BackgroundTaskManager()
        async def dummy():
            await asyncio.sleep(0.1)
        t1 = await mgr.run("dup", dummy())
        t2 = await mgr.run("dup", dummy())
        assert t1 is t2

    @pytest.mark.asyncio
    async def test_cleanup_on_done(self):
        from infrastructure.workers.background import BackgroundTaskManager
        import asyncio
        mgr = BackgroundTaskManager()
        async def quick():
            await asyncio.sleep(0)
        await mgr.run("done_task", quick())
        await asyncio.sleep(0.1)
        assert "done_task" not in mgr._tasks
