"""Tests for insights_service.py and skill_roadmap_service.py OOP wrappers."""
import sys, os
from unittest.mock import patch, MagicMock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))


class TestInsightsService:
    def _reset_singleton(self):
        import services.process.insights_service as mod
        mod._insights_service = None

    def test_singleton(self):
        self._reset_singleton()
        from services.process.insights_service import get_insights_service
        import services.process.insights_service as mod
        s1 = get_insights_service()
        s2 = get_insights_service()
        assert s1 is s2
        self._reset_singleton()

    def test_not_running_initially(self):
        from services.process.insights_service import InsightsService
        svc = InsightsService()
        assert not svc.is_running

    def test_current_type_none_initially(self):
        from services.process.insights_service import InsightsService
        svc = InsightsService()
        assert svc.current_type is None

    def test_get_source_for_type(self):
        from services.process.insights_service import InsightsService
        svc = InsightsService()
        from services.process.generation_models import GenerationSource
        assert svc.get_source_for_type('skills') == GenerationSource.INSIGHT_SKILLS_INTEL
        assert svc.get_source_for_type('skills_intel') == GenerationSource.INSIGHT_SKILLS_INTEL
        assert svc.get_source_for_type('overview') == GenerationSource.INSIGHT_OVERVIEW
        assert svc.get_source_for_type('opportunities') == GenerationSource.INSIGHT_OPPORTUNITIES
        assert svc.get_source_for_type('companies') == GenerationSource.INSIGHT_COMPANIES
        assert svc.get_source_for_type('market') == GenerationSource.INSIGHT_MARKET
        assert svc.get_source_for_type('networking') == GenerationSource.INSIGHT_NETWORKING
        assert svc.get_source_for_type('unknown') == GenerationSource.INSIGHT_OVERVIEW

    def test_generate_all_delegates(self):
        from services.process.insights_service import InsightsService
        svc = InsightsService()
        mock_fn = MagicMock(return_value={"status": "ok"})
        with patch.dict('sys.modules', {'insights': MagicMock(generate_all=mock_fn)}):
            result = svc.generate_all(pid=42)
            mock_fn.assert_called_once_with(42)
            assert result == {"status": "ok"}

    def test_generate_section_delegates(self):
        from services.process.insights_service import InsightsService
        svc = InsightsService()
        mock_fn = MagicMock(return_value={"section": "skills"})
        with patch.dict('sys.modules', {'insights': MagicMock(generate_section=mock_fn)}):
            result = svc.generate_section('skills', pid=7)
            mock_fn.assert_called_once_with('skills', 7)
            assert result == {"section": "skills"}

    def test_generate_skills_intel_delegates(self):
        from services.process.insights_service import InsightsService
        svc = InsightsService()
        mock_fn = MagicMock(return_value={"intel": True})
        with patch.dict('sys.modules', {'insights': MagicMock(generate_skills_intel=mock_fn)}):
            result = svc.generate_skills_intel(pid=3)
            mock_fn.assert_called_once_with(3)
            assert result == {"intel": True}

    def test_cancel_delegates(self):
        from services.process.insights_service import InsightsService
        svc = InsightsService()
        mock_cancel = MagicMock(return_value=True)
        with patch.dict('sys.modules', {'insights': MagicMock(cancel_run=mock_cancel)}):
            result = svc.cancel()
            mock_cancel.assert_called_once()
            assert result is True

    def test_get_progress_delegates(self):
        from services.process.insights_service import InsightsService
        svc = InsightsService()
        mock_progress = MagicMock(return_value={"running": False})
        with patch.dict('sys.modules', {'insights': MagicMock(get_progress=mock_progress)}):
            result = svc.get_progress()
            mock_progress.assert_called_once()
            assert result == {"running": False}

    def test_get_latest_delegates(self):
        from services.process.insights_service import InsightsService
        svc = InsightsService()
        mock_latest = MagicMock(return_value={"data": "latest"})
        with patch.dict('sys.modules', {'insights': MagicMock(get_latest=mock_latest)}):
            result = svc.get_latest('overview')
            mock_latest.assert_called_once_with('overview')
            assert result == {"data": "latest"}

    def test_get_runs_delegates(self):
        from services.process.insights_service import InsightsService
        svc = InsightsService()
        mock_runs = MagicMock(return_value=[])
        with patch.dict('sys.modules', {'insights': MagicMock(get_runs=mock_runs)}):
            result = svc.get_runs(insight_type='skills', limit=5, offset=0)
            mock_runs.assert_called_once_with('skills', 5, 0)
            assert result == []

    def test_insight_source_map_complete(self):
        from services.process.insights_service import InsightsService
        expected_keys = {'overview', 'opportunities', 'companies', 'skills', 'skills_intel', 'market', 'networking'}
        assert set(InsightsService.INSIGHT_SOURCE_MAP.keys()) == expected_keys


class TestSkillRoadmapService:
    def _reset_singleton(self):
        import services.process.skill_roadmap_service as mod
        mod._skill_roadmap_service = None

    def test_singleton(self):
        self._reset_singleton()
        from services.process.skill_roadmap_service import get_skill_roadmap_service
        import services.process.skill_roadmap_service as mod
        s1 = get_skill_roadmap_service()
        s2 = get_skill_roadmap_service()
        assert s1 is s2
        self._reset_singleton()

    def test_get_source_for_operation(self):
        from services.process.skill_roadmap_service import SkillRoadmapService
        svc = SkillRoadmapService()
        from services.process.generation_models import GenerationSource
        assert svc.get_source_for_operation('generate') == GenerationSource.SKILL_ROADMAP_GENERATE
        assert svc.get_source_for_operation('extend') == GenerationSource.SKILL_ROADMAP_EXTEND
        assert svc.get_source_for_operation('finegrain') == GenerationSource.SKILL_ROADMAP_FINEGRAIN
        assert svc.get_source_for_operation('unknown') == GenerationSource.SKILL_ROADMAP_GENERATE

    def test_generate_delegates(self):
        from services.process.skill_roadmap_service import SkillRoadmapService
        svc = SkillRoadmapService()
        mock_fn = MagicMock(return_value={"roadmap": []})
        with patch.dict('sys.modules', {'skill_roadmap_service': MagicMock(generate_roadmap=mock_fn)}):
            result = svc.generate("Python")
            mock_fn.assert_called_once_with("Python")
            assert result == {"roadmap": []}

    def test_extend_delegates(self):
        from services.process.skill_roadmap_service import SkillRoadmapService
        svc = SkillRoadmapService()
        mock_fn = MagicMock(return_value={"extended": True})
        with patch.dict('sys.modules', {'skill_roadmap_service': MagicMock(extend_roadmap=mock_fn)}):
            result = svc.extend("Python")
            mock_fn.assert_called_once_with("Python")
            assert result == {"extended": True}

    def test_finegrain_delegates(self):
        from services.process.skill_roadmap_service import SkillRoadmapService
        svc = SkillRoadmapService()
        mock_fn = MagicMock(return_value={"finegrained": True})
        with patch.dict('sys.modules', {'skill_roadmap_service': MagicMock(finegrain_roadmap=mock_fn)}):
            result = svc.finegrain("Python")
            mock_fn.assert_called_once_with("Python")
            assert result == {"finegrained": True}

    def test_operation_source_map_complete(self):
        from services.process.skill_roadmap_service import SkillRoadmapService
        expected_keys = {'generate', 'extend', 'finegrain'}
        assert set(SkillRoadmapService.OPERATION_SOURCE_MAP.keys()) == expected_keys
