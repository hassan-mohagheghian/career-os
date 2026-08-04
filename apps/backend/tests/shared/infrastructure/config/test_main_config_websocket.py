"""Tests for config, main, websocket, ai_compat, prompts, logging, and more."""

import sys
import os
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', '..'))


# ── Config ────────────────────────────────────────────────────────

class TestConfig:
    def test_project_root(self):
        from shared.infrastructure.config.app_config import PROJECT_ROOT
        assert PROJECT_ROOT is not None

    def test_static_folder(self):
        from shared.infrastructure.config.app_config import STATIC_FOLDER
        assert STATIC_FOLDER is not None

    def test_ai_provider(self):
        from shared.infrastructure.config.app_config import AI_PROVIDER
        assert AI_PROVIDER is not None


# ── WebSocket Manager ─────────────────────────────────────────────

class TestConnectionManager:
    def test_init(self):
        from shared.infrastructure.websocket.manager import ConnectionManager
        mgr = ConnectionManager()
        assert mgr.active == {}

    def test_disconnect(self):
        from shared.infrastructure.websocket.manager import ConnectionManager
        mgr = ConnectionManager()
        ws = MagicMock()
        mgr.active["room1"] = {ws}
        mgr.disconnect(ws, "room1")
        assert "room1" not in mgr.active

    def test_disconnect_empty_room(self):
        from shared.infrastructure.websocket.manager import ConnectionManager
        mgr = ConnectionManager()
        ws = MagicMock()
        mgr.disconnect(ws, "nonexistent")

    def test_join_room(self):
        from shared.infrastructure.websocket.manager import ConnectionManager
        mgr = ConnectionManager()
        ws = MagicMock()
        mgr.join_room(ws, "room1")
        assert ws in mgr.active["room1"]

    def test_leave_room(self):
        from shared.infrastructure.websocket.manager import ConnectionManager
        mgr = ConnectionManager()
        ws = MagicMock()
        mgr.active["room1"] = {ws}
        mgr.leave_room(ws, "room1")
        assert "room1" not in mgr.active

    def test_leave_room_not_exist(self):
        from shared.infrastructure.websocket.manager import ConnectionManager
        mgr = ConnectionManager()
        ws = MagicMock()
        mgr.leave_room(ws, "nonexistent")

    def test_get_connection_manager_singleton(self):
        from shared.infrastructure.websocket.manager import get_connection_manager
        mgr1 = get_connection_manager()
        mgr2 = get_connection_manager()
        assert mgr1 is mgr2

    @pytest.mark.asyncio
    async def test_broadcast_empty_room(self):
        from shared.infrastructure.websocket.manager import ConnectionManager
        mgr = ConnectionManager()
        await mgr.broadcast("nonexistent", {"event": "test"})

    @pytest.mark.asyncio
    async def test_broadcast_all_empty(self):
        from shared.infrastructure.websocket.manager import ConnectionManager
        mgr = ConnectionManager()
        await mgr.broadcast_all({"event": "test"})

    @pytest.mark.asyncio
    async def test_broadcast_disconnected(self):
        from shared.infrastructure.websocket.manager import ConnectionManager
        mgr = ConnectionManager()
        ws = MagicMock()
        ws.send_json = AsyncMock(side_effect=Exception("disconnected"))
        mgr.active["room1"] = {ws}
        await mgr.broadcast("room1", {"event": "test"})
        assert "room1" not in mgr.active


# ── WebSocket Broadcaster ─────────────────────────────────────────

class TestWebSocketBroadcaster:
    def test_set_socketio(self):
        from shared.infrastructure.websocket.broadcaster import WebSocketBroadcaster, set_socketio_server
        b = WebSocketBroadcaster()
        mock_sio = MagicMock()
        b.set_socketio(mock_sio)
        from shared.infrastructure.websocket.broadcaster import get_socketio_server
        assert get_socketio_server() is mock_sio

    def test_add_listener(self):
        from shared.infrastructure.websocket.broadcaster import WebSocketBroadcaster
        b = WebSocketBroadcaster()
        listener = MagicMock()
        b.add_listener(listener)
        assert listener in b._listeners

    def test_emit_no_server(self):
        from shared.infrastructure.websocket.broadcaster import WebSocketBroadcaster, set_socketio_server
        set_socketio_server(None)
        b = WebSocketBroadcaster()
        event = MagicMock(table="pending_jobs", pid=1, step="fetch", val=1, status="processing", error=None, ts="now", extra=None)
        b.step_update(event)

    def test_room_for(self):
        from shared.infrastructure.websocket.broadcaster import WebSocketBroadcaster
        b = WebSocketBroadcaster()
        assert b._room_for("pending_jobs", 1) == "pending_jobs_1"
        assert b._room_for("pending_companies", 2) == "pending_companies_2"
        assert b._room_for("generation", 3) == "generation_3"

    def test_prefix(self):
        from shared.infrastructure.websocket.broadcaster import WebSocketBroadcaster
        b = WebSocketBroadcaster()
        assert b._prefix("pending_jobs") == "company"
        assert b._prefix("pending_companies") == "company"
        assert b._prefix("generation") == "generation"

    def test_notify_listeners(self):
        from shared.infrastructure.websocket.broadcaster import WebSocketBroadcaster
        b = WebSocketBroadcaster()
        listener = MagicMock()
        b.add_listener(listener)
        b._notify_listeners("test_event", {"data": "val"})
        listener.assert_called_once_with("test_event", {"data": "val"})

    def test_notify_listeners_error(self):
        from shared.infrastructure.websocket.broadcaster import WebSocketBroadcaster
        b = WebSocketBroadcaster()
        listener = MagicMock(side_effect=Exception("boom"))
        b.add_listener(listener)
        b._notify_listeners("test_event", {"data": "val"})


# ── Prompts ───────────────────────────────────────────────────────

class TestPrompts:
    def test_load_prompt_not_found(self):
        from shared.infrastructure.prompts.loader import load_prompt
        with pytest.raises(FileNotFoundError):
            load_prompt("nonexistent_prompt")


# ── Logging Config ────────────────────────────────────────────────

class TestLoggingConfig:
    def test_setup_logging(self):
        from shared.infrastructure.process.logging_config import setup_logging
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            setup_logging(log_dir=tmpdir, level="DEBUG")
            assert os.path.exists(tmpdir)

    def test_setup_logging_idempotent(self):
        from shared.infrastructure.process import logging_config
        logging_config._initialized = False
        from shared.infrastructure.process.logging_config import setup_logging
        setup_logging()
        setup_logging()
        assert logging_config._initialized is True

    def test_get_logger(self):
        from shared.infrastructure.process.logging_config import get_logger
        log = get_logger("test")
        assert log is not None

    def test_get_logger_default(self):
        from shared.infrastructure.process.logging_config import get_logger
        log = get_logger()
        assert log is not None


# ── Main App (create_app without lifespan) ────────────────────────

class TestMainApp:
    def test_create_app(self):
        from apps.backend.entrypoints.api import create_app
        app = create_app()
        assert app.title == "Job Search Intelligence API"

    def test_health_endpoint(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


# ── Services process_utils ────────────────────────────────────────

class TestProcessUtils:
    def test_import(self):
        from shared.infrastructure.process_utils import broadcaster
        assert broadcaster is not None


# ── More SA skill_repository tests ────────────────────────────────

class TestSASkillRepositoryExtended:
    def test_bulk_categorize(self, sa_session):
        from skills.infrastructure.repositories.sa_skill_repository import SQLAlchemySkillRepository
        from skills.infrastructure.models.skill_model import SkillModel
        sa_session.add(SkillModel(name="Python"))
        sa_session.add(SkillModel(name="Java"))
        sa_session.commit()
        ids = [s.id for s in sa_session.query(SkillModel).all()]
        repo = SQLAlchemySkillRepository(sa_session)
        count = repo.bulk_categorize(ids, "engineering")
        assert count == 2

    def test_get_relationships_empty(self, sa_session):
        from skills.infrastructure.repositories.sa_skill_repository import SQLAlchemySkillRepository
        repo = SQLAlchemySkillRepository(sa_session)
        result = repo.get_relationships("Python")
        assert result == []

    def test_create_relationship_exception(self, sa_session):
        from skills.infrastructure.repositories.sa_skill_repository import SQLAlchemySkillRepository
        repo = SQLAlchemySkillRepository(sa_session)
        result = repo.create_relationship({})
        assert result is False

    def test_merge_with_roadmap_references(self, sa_session):
        from skills.infrastructure.repositories.sa_skill_repository import SQLAlchemySkillRepository
        from skills.infrastructure.models.skill_model import SkillModel
        from skills.infrastructure.models.skill_roadmap_models import SkillRoadmapModel, SkillRoadmapProgressModel, SkillRoadmapJobModel
        sa_session.add(SkillModel(name="Python"))
        sa_session.add(SkillModel(name="Python3"))
        sa_session.commit()
        target = sa_session.query(SkillModel).filter(SkillModel.name == "Python").first()
        source = sa_session.query(SkillModel).filter(SkillModel.name == "Python3").first()
        sa_session.add(SkillRoadmapModel(skill_name="Python3", title="Basics"))
        sa_session.add(SkillRoadmapProgressModel(roadmap_id=1, skill_name="Python3"))
        sa_session.add(SkillRoadmapJobModel(skill_name="Python3"))
        sa_session.commit()
        repo = SQLAlchemySkillRepository(sa_session)
        result = repo.merge(target.id, [source.id])
        assert result["status"] == "merged"
        roadmap = sa_session.query(SkillRoadmapModel).filter(SkillRoadmapModel.skill_name == "Python3").first()
        # Roadmap should be renamed to Python
        assert roadmap is None or roadmap.skill_name == "Python"


# ── SA preference extended ────────────────────────────────────────

class TestSARuleExtended:
    def test_get_enabled_by_scopes_empty(self, sa_session):
        from rules.infrastructure.repositories.sa_rule_repository import SQLAlchemyRuleRepository
        repo = SQLAlchemyRuleRepository(sa_session)
        assert repo.get_enabled_by_scopes(["JOB"]) == []

    def test_bulk_update_multiple(self, sa_session):
        from rules.infrastructure.repositories.sa_rule_repository import SQLAlchemyRuleRepository
        from rules.infrastructure.models.rule_model import RuleModel
        p1 = RuleModel(category="fit", key="a", value="1")
        p2 = RuleModel(category="fit", key="b", value="2")
        sa_session.add_all([p1, p2])
        sa_session.commit()
        repo = SQLAlchemyRuleRepository(sa_session)
        count = repo.bulk_update([
            {"id": p1.id, "value": "10"},
            {"id": p2.id, "value": "20"},
        ])
        assert count == 2


# ── SA company link extended ──────────────────────────────────────

class TestSACompanyLinkExtended:
    def test_get_by_company_id_empty(self, sa_session):
        from companies.infrastructure.repositories.sa_company_link_repository import SQLAlchemyCompanyLinkRepository
        repo = SQLAlchemyCompanyLinkRepository(sa_session)
        assert repo.get_by_company_id(999) == []

    def test_get_by_id(self, sa_session):
        from companies.infrastructure.repositories.sa_company_link_repository import SQLAlchemyCompanyLinkRepository
        from companies.infrastructure.models.company_model import CompanyLinkModel, CompanyModel
        company = CompanyModel(name="TestCorp", website="https://ex.com")
        sa_session.add(company)
        sa_session.flush()
        link = CompanyLinkModel(company_id=company.id, url="https://ex.com/link")
        sa_session.add(link)
        sa_session.commit()
        repo = SQLAlchemyCompanyLinkRepository(sa_session)
        result = repo.get_by_id(link.id)
        assert result["url"] == "https://ex.com/link"

    def test_get_by_id_not_found(self, sa_session):
        from companies.infrastructure.repositories.sa_company_link_repository import SQLAlchemyCompanyLinkRepository
        repo = SQLAlchemyCompanyLinkRepository(sa_session)
        assert repo.get_by_id(999) is None


# ── SA skill roadmap extended ─────────────────────────────────────

class TestSASkillRoadmapExtended:
    def test_delete_by_skill_name_empty(self, sa_session):
        from skills.infrastructure.repositories.sa_skill_roadmap_repository import SQLAlchemySkillRoadmapRepository
        repo = SQLAlchemySkillRoadmapRepository(sa_session)
        assert repo.delete_by_skill_name("Nonexistent") == 0

    def test_get_max_version_empty(self, sa_session):
        from skills.infrastructure.repositories.sa_skill_roadmap_repository import SQLAlchemySkillRoadmapRepository
        repo = SQLAlchemySkillRoadmapRepository(sa_session)
        assert repo.get_max_version("Nonexistent") == 0


# ── SA skill roadmap job extended ─────────────────────────────────

class TestSASkillRoadmapJobExtended:
    def test_create_with_kwargs(self, sa_session):
        from skills.infrastructure.repositories.sa_skill_roadmap_job_repository import SQLAlchemySkillRoadmapJobRepository
        repo = SQLAlchemySkillRoadmapJobRepository(sa_session)
        result = repo.create("Python", "extend", "queued", message="Starting", version=2)
        assert result["message"] == "Starting"
        assert result["version"] == 2

    def test_get_all_empty(self, sa_session):
        from skills.infrastructure.repositories.sa_skill_roadmap_job_repository import SQLAlchemySkillRoadmapJobRepository
        repo = SQLAlchemySkillRoadmapJobRepository(sa_session)
        assert repo.get_all() == []

    def test_get_for_skill_empty(self, sa_session):
        from skills.infrastructure.repositories.sa_skill_roadmap_job_repository import SQLAlchemySkillRoadmapJobRepository
        repo = SQLAlchemySkillRoadmapJobRepository(sa_session)
        assert repo.get_for_skill("Python") == []


# ── SA skill relationship extended ────────────────────────────────

class TestSASkillRelationshipExtended:
    def test_get_for_skill_empty(self, sa_session):
        from skills.infrastructure.repositories.sa_skill_relationship_repository import SQLAlchemySkillRelationshipRepository
        repo = SQLAlchemySkillRelationshipRepository(sa_session)
        assert repo.get_for_skill("Python") == []

    def test_delete_all_empty(self, sa_session):
        from skills.infrastructure.repositories.sa_skill_relationship_repository import SQLAlchemySkillRelationshipRepository
        repo = SQLAlchemySkillRelationshipRepository(sa_session)
        assert repo.delete_all() == 0


# ── SA skill alias extended ───────────────────────────────────────

class TestSASkillAliasExtended:
    def test_get_by_skill_id_empty(self, sa_session):
        from skills.infrastructure.repositories.sa_skill_alias_repository import SQLAlchemySkillAliasRepository
        repo = SQLAlchemySkillAliasRepository(sa_session)
        assert repo.get_by_skill_id(999) == []

    def test_delete_nonexistent(self, sa_session):
        from skills.infrastructure.repositories.sa_skill_alias_repository import SQLAlchemySkillAliasRepository
        repo = SQLAlchemySkillAliasRepository(sa_session)
        assert repo.delete_by_skill_id(999) == 0


