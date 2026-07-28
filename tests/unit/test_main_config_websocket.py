"""Tests for config, main, websocket, ai_compat, prompts, logging, and more."""

import sys
import os
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'app', 'server'))


# ── Config ────────────────────────────────────────────────────────

class TestConfig:
    def test_db_path(self):
        from config import DB_PATH
        assert DB_PATH is not None
        assert isinstance(DB_PATH, str)

    def test_project_root(self):
        from config import PROJECT_ROOT
        assert PROJECT_ROOT is not None

    def test_static_folder(self):
        from config import STATIC_FOLDER
        assert STATIC_FOLDER is not None

    def test_ai_provider(self):
        from config import AI_PROVIDER
        assert AI_PROVIDER is not None


# ── WebSocket Manager ─────────────────────────────────────────────

class TestConnectionManager:
    def test_init(self):
        from infrastructure.websocket.manager import ConnectionManager
        mgr = ConnectionManager()
        assert mgr.active == {}

    def test_disconnect(self):
        from infrastructure.websocket.manager import ConnectionManager
        mgr = ConnectionManager()
        ws = MagicMock()
        mgr.active["room1"] = {ws}
        mgr.disconnect(ws, "room1")
        assert "room1" not in mgr.active

    def test_disconnect_empty_room(self):
        from infrastructure.websocket.manager import ConnectionManager
        mgr = ConnectionManager()
        ws = MagicMock()
        mgr.disconnect(ws, "nonexistent")

    def test_join_room(self):
        from infrastructure.websocket.manager import ConnectionManager
        mgr = ConnectionManager()
        ws = MagicMock()
        mgr.join_room(ws, "room1")
        assert ws in mgr.active["room1"]

    def test_leave_room(self):
        from infrastructure.websocket.manager import ConnectionManager
        mgr = ConnectionManager()
        ws = MagicMock()
        mgr.active["room1"] = {ws}
        mgr.leave_room(ws, "room1")
        assert "room1" not in mgr.active

    def test_leave_room_not_exist(self):
        from infrastructure.websocket.manager import ConnectionManager
        mgr = ConnectionManager()
        ws = MagicMock()
        mgr.leave_room(ws, "nonexistent")

    def test_get_connection_manager_singleton(self):
        from infrastructure.websocket.manager import get_connection_manager
        mgr1 = get_connection_manager()
        mgr2 = get_connection_manager()
        assert mgr1 is mgr2

    @pytest.mark.asyncio
    async def test_broadcast_empty_room(self):
        from infrastructure.websocket.manager import ConnectionManager
        mgr = ConnectionManager()
        await mgr.broadcast("nonexistent", {"event": "test"})

    @pytest.mark.asyncio
    async def test_broadcast_all_empty(self):
        from infrastructure.websocket.manager import ConnectionManager
        mgr = ConnectionManager()
        await mgr.broadcast_all({"event": "test"})

    @pytest.mark.asyncio
    async def test_broadcast_disconnected(self):
        from infrastructure.websocket.manager import ConnectionManager
        mgr = ConnectionManager()
        ws = MagicMock()
        ws.send_json = AsyncMock(side_effect=Exception("disconnected"))
        mgr.active["room1"] = {ws}
        await mgr.broadcast("room1", {"event": "test"})
        assert "room1" not in mgr.active


# ── WebSocket Broadcaster ─────────────────────────────────────────

class TestWebSocketBroadcaster:
    def test_set_socketio(self):
        from infrastructure.websocket.broadcaster import WebSocketBroadcaster, set_socketio_server
        b = WebSocketBroadcaster()
        mock_sio = MagicMock()
        b.set_socketio(mock_sio)
        from infrastructure.websocket.broadcaster import get_socketio_server
        assert get_socketio_server() is mock_sio

    def test_add_listener(self):
        from infrastructure.websocket.broadcaster import WebSocketBroadcaster
        b = WebSocketBroadcaster()
        listener = MagicMock()
        b.add_listener(listener)
        assert listener in b._listeners

    def test_emit_no_server(self):
        from infrastructure.websocket.broadcaster import WebSocketBroadcaster, set_socketio_server
        set_socketio_server(None)
        b = WebSocketBroadcaster()
        event = MagicMock(table="pending_jobs", pid=1, step="fetch", val=1, status="processing", error=None, ts="now", extra=None)
        b.step_update(event)

    def test_room_for(self):
        from infrastructure.websocket.broadcaster import WebSocketBroadcaster
        b = WebSocketBroadcaster()
        assert b._room_for("pending_jobs", 1) == "pending_1"
        assert b._room_for("pending_companies", 2) == "company_2"
        assert b._room_for("pending_generations", 3) == "generation_3"

    def test_prefix(self):
        from infrastructure.websocket.broadcaster import WebSocketBroadcaster
        b = WebSocketBroadcaster()
        assert b._prefix("pending_jobs") == "pending"
        assert b._prefix("pending_companies") == "company"
        assert b._prefix("pending_generations") == "generation"

    def test_notify_listeners(self):
        from infrastructure.websocket.broadcaster import WebSocketBroadcaster
        b = WebSocketBroadcaster()
        listener = MagicMock()
        b.add_listener(listener)
        b._notify_listeners("test_event", {"data": "val"})
        listener.assert_called_once_with("test_event", {"data": "val"})

    def test_notify_listeners_error(self):
        from infrastructure.websocket.broadcaster import WebSocketBroadcaster
        b = WebSocketBroadcaster()
        listener = MagicMock(side_effect=Exception("boom"))
        b.add_listener(listener)
        b._notify_listeners("test_event", {"data": "val"})


# ── AI Compat ─────────────────────────────────────────────────────

class TestAiCompat:
    def test_ai_compat_path_setup(self):
        import ai_compat
        assert hasattr(ai_compat, 'get_llm_service')


# ── Prompts ───────────────────────────────────────────────────────

class TestPrompts:
    def test_load_prompt_not_found(self):
        from prompts import load_prompt
        with pytest.raises(FileNotFoundError):
            load_prompt("nonexistent_prompt")


# ── Logging Config ────────────────────────────────────────────────

class TestLoggingConfig:
    def test_setup_logging(self):
        from services.process.logging_config import setup_logging
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            setup_logging(log_dir=tmpdir, level="DEBUG")
            assert os.path.exists(tmpdir)

    def test_setup_logging_idempotent(self):
        from services.process import logging_config
        logging_config._initialized = False
        from services.process.logging_config import setup_logging
        setup_logging()
        setup_logging()
        assert logging_config._initialized is True

    def test_get_logger(self):
        from services.process.logging_config import get_logger
        log = get_logger("test")
        assert log is not None

    def test_get_logger_default(self):
        from services.process.logging_config import get_logger
        log = get_logger()
        assert log is not None


# ── Main App (create_app without lifespan) ────────────────────────

class TestMainApp:
    def test_create_app(self):
        from main import create_app
        app = create_app()
        assert app.title == "Job Search Intelligence API"

    def test_health_endpoint(self):
        from main import create_app
        app = create_app()
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            r = client.get("/api/health")
            assert r.status_code == 200
            assert r.json()["status"] == "ok"


# ── Services process_utils ────────────────────────────────────────

class TestProcessUtils:
    def test_import(self):
        from services.process_utils import broadcaster
        assert broadcaster is not None


# ── More SA skill_repository tests ────────────────────────────────

class TestSASkillRepositoryExtended:
    def test_bulk_categorize(self, session):
        from infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        from infrastructure.database.models.skill_model import SkillModel
        session.add(SkillModel(name="Python"))
        session.add(SkillModel(name="Java"))
        session.commit()
        ids = [s.id for s in session.query(SkillModel).all()]
        repo = SQLAlchemySkillRepository(session)
        count = repo.bulk_categorize(ids, "engineering")
        assert count == 2

    def test_get_relationships_empty(self, session):
        from infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        repo = SQLAlchemySkillRepository(session)
        result = repo.get_relationships("Python")
        assert result == []

    def test_create_relationship_exception(self, session):
        from infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        repo = SQLAlchemySkillRepository(session)
        result = repo.create_relationship({})
        assert result is False

    def test_merge_with_roadmap_references(self, session):
        from infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
        from infrastructure.database.models.skill_model import SkillModel
        from infrastructure.database.models.misc_models import SkillRoadmapModel, SkillRoadmapProgressModel, SkillRoadmapJobModel
        session.add(SkillModel(name="Python"))
        session.add(SkillModel(name="Python3"))
        session.commit()
        target = session.query(SkillModel).filter(SkillModel.name == "Python").first()
        source = session.query(SkillModel).filter(SkillModel.name == "Python3").first()
        session.add(SkillRoadmapModel(skill_name="Python3", title="Basics"))
        session.add(SkillRoadmapProgressModel(roadmap_id=1, skill_name="Python3"))
        session.add(SkillRoadmapJobModel(skill_name="Python3"))
        session.commit()
        repo = SQLAlchemySkillRepository(session)
        result = repo.merge(target.id, [source.id])
        assert result["status"] == "merged"
        roadmap = session.query(SkillRoadmapModel).filter(SkillRoadmapModel.skill_name == "Python3").first()
        # Roadmap should be renamed to Python
        assert roadmap is None or roadmap.skill_name == "Python"


# ── SA pending generation - more tests ────────────────────────────

class TestSAPendingGenerationExtended:
    def test_create_with_defaults(self, session):
        from infrastructure.database.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
        repo = SQLAlchemyPendingGenerationRepository(session)
        result = repo.create(1, "cover")
        assert result["type"] == "cover"
        assert result["status"] == "queued"

    def test_get_all_active_empty(self, session):
        from infrastructure.database.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
        repo = SQLAlchemyPendingGenerationRepository(session)
        assert repo.get_all_active() == []

    def test_get_history_for_job_empty(self, session):
        from infrastructure.database.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
        repo = SQLAlchemyPendingGenerationRepository(session)
        assert repo.get_history_for_job(1) == []

    def test_get_active_count_zero(self, session):
        from infrastructure.database.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
        repo = SQLAlchemyPendingGenerationRepository(session)
        assert repo.get_active_count(1) == 0


# ── SA preference extended ────────────────────────────────────────

class TestSAPreferenceExtended:
    def test_get_enabled_by_scopes_empty(self, session):
        from infrastructure.database.sa_preference_repository import SQLAlchemyPreferenceRepository
        repo = SQLAlchemyPreferenceRepository(session)
        assert repo.get_enabled_by_scopes(["JOB"]) == []

    def test_bulk_update_multiple(self, session):
        from infrastructure.database.sa_preference_repository import SQLAlchemyPreferenceRepository
        from infrastructure.database.models.misc_models import PreferenceModel
        p1 = PreferenceModel(category="fit", key="a", value="1")
        p2 = PreferenceModel(category="fit", key="b", value="2")
        session.add_all([p1, p2])
        session.commit()
        repo = SQLAlchemyPreferenceRepository(session)
        count = repo.bulk_update([
            {"id": p1.id, "value": "10"},
            {"id": p2.id, "value": "20"},
        ])
        assert count == 2


# ── SA company link extended ──────────────────────────────────────

class TestSACompanyLinkExtended:
    def test_get_by_company_id_empty(self, session):
        from infrastructure.database.sa_company_link_repository import SQLAlchemyCompanyLinkRepository
        repo = SQLAlchemyCompanyLinkRepository(session)
        assert repo.get_by_company_id(999) == []

    def test_get_by_id(self, session):
        from infrastructure.database.sa_company_link_repository import SQLAlchemyCompanyLinkRepository
        from infrastructure.database.models.company_model import CompanyLinkModel
        link = CompanyLinkModel(company_id=1, url="https://ex.com")
        session.add(link)
        session.commit()
        repo = SQLAlchemyCompanyLinkRepository(session)
        result = repo.get_by_id(link.id)
        assert result["url"] == "https://ex.com"

    def test_get_by_id_not_found(self, session):
        from infrastructure.database.sa_company_link_repository import SQLAlchemyCompanyLinkRepository
        repo = SQLAlchemyCompanyLinkRepository(session)
        assert repo.get_by_id(999) is None


# ── SA insight extended ───────────────────────────────────────────

class TestSAInsightExtended:
    def test_upsert_section_with_score(self, session):
        from infrastructure.database.sa_insight_repository import SQLAlchemyInsightRepository
        repo = SQLAlchemyInsightRepository(session)
        repo.upsert_section("skills", {"skills": []}, "completed")
        result = repo.get_section("skills")
        assert result is not None


# ── SA skill roadmap extended ─────────────────────────────────────

class TestSASkillRoadmapExtended:
    def test_delete_by_skill_name_empty(self, session):
        from infrastructure.database.sa_skill_roadmap_repository import SQLAlchemySkillRoadmapRepository
        repo = SQLAlchemySkillRoadmapRepository(session)
        assert repo.delete_by_skill_name("Nonexistent") == 0

    def test_get_max_version_empty(self, session):
        from infrastructure.database.sa_skill_roadmap_repository import SQLAlchemySkillRoadmapRepository
        repo = SQLAlchemySkillRoadmapRepository(session)
        assert repo.get_max_version("Nonexistent") == 0


# ── SA skill roadmap job extended ─────────────────────────────────

class TestSASkillRoadmapJobExtended:
    def test_create_with_kwargs(self, session):
        from infrastructure.database.sa_skill_roadmap_job_repository import SQLAlchemySkillRoadmapJobRepository
        repo = SQLAlchemySkillRoadmapJobRepository(session)
        result = repo.create("Python", "extend", "queued", message="Starting", version=2)
        assert result["message"] == "Starting"
        assert result["version"] == 2

    def test_get_all_empty(self, session):
        from infrastructure.database.sa_skill_roadmap_job_repository import SQLAlchemySkillRoadmapJobRepository
        repo = SQLAlchemySkillRoadmapJobRepository(session)
        assert repo.get_all() == []

    def test_get_for_skill_empty(self, session):
        from infrastructure.database.sa_skill_roadmap_job_repository import SQLAlchemySkillRoadmapJobRepository
        repo = SQLAlchemySkillRoadmapJobRepository(session)
        assert repo.get_for_skill("Python") == []


# ── SA skill relationship extended ────────────────────────────────

class TestSASkillRelationshipExtended:
    def test_get_for_skill_empty(self, session):
        from infrastructure.database.sa_skill_relationship_repository import SQLAlchemySkillRelationshipRepository
        repo = SQLAlchemySkillRelationshipRepository(session)
        assert repo.get_for_skill("Python") == []

    def test_delete_all_empty(self, session):
        from infrastructure.database.sa_skill_relationship_repository import SQLAlchemySkillRelationshipRepository
        repo = SQLAlchemySkillRelationshipRepository(session)
        assert repo.delete_all() == 0


# ── SA skill alias extended ───────────────────────────────────────

class TestSASkillAliasExtended:
    def test_get_by_skill_id_empty(self, session):
        from infrastructure.database.sa_skill_alias_repository import SQLAlchemySkillAliasRepository
        repo = SQLAlchemySkillAliasRepository(session)
        assert repo.get_by_skill_id(999) == []

    def test_delete_nonexistent(self, session):
        from infrastructure.database.sa_skill_alias_repository import SQLAlchemySkillAliasRepository
        repo = SQLAlchemySkillAliasRepository(session)
        assert repo.delete_by_skill_id(999) == 0


# ── SA tech learning extended ─────────────────────────────────────

class TestSATechLearningExtended:
    def test_upsert_with_existing_id(self, session):
        from infrastructure.database.sa_tech_learning_repository import SQLAlchemyTechLearningRepository
        from infrastructure.database.models.misc_models import TechLearningModel
        tl = TechLearningModel(name="Python", priority=1)
        session.add(tl)
        session.commit()
        repo = SQLAlchemyTechLearningRepository(session)
        result = repo.upsert({"id": tl.id, "priority": 10})
        assert result["priority"] == 10


# ── SA career insight run extended ────────────────────────────────

class TestSACareerInsightRunExtended:
    def test_get_runs_empty(self, session):
        from infrastructure.database.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository
        repo = SQLAlchemyCareerInsightRunRepository(session)
        assert repo.get_runs() == []

    def test_get_total_count_empty(self, session):
        from infrastructure.database.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository
        repo = SQLAlchemyCareerInsightRunRepository(session)
        assert repo.get_total_count() == 0

    def test_get_latest_processing_with_type(self, session):
        from infrastructure.database.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository
        from infrastructure.database.models.insight_model import CareerInsightRunModel
        session.add(CareerInsightRunModel(insight_type="skills", status="processing"))
        session.add(CareerInsightRunModel(insight_type="market", status="processing"))
        session.commit()
        repo = SQLAlchemyCareerInsightRunRepository(session)
        result = repo.get_latest_processing("skills")
        assert result["insight_type"] == "skills"

    def test_cleanup_stale_empty(self, session):
        from infrastructure.database.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository
        repo = SQLAlchemyCareerInsightRunRepository(session)
        assert repo.cleanup_stale_runs("2025-01-01") == 0
