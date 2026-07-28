"""Tests for generation domain models.

TDD: Tests written BEFORE implementation.
Tests cover: GenerationSource, GenerationStatus, GenerationRun, GenerationHistoryItem.
"""

import sys
import os
import pytest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from shared.domain.models.generation_models import (
    GenerationSource,
    GenerationStatus,
    GenerationRun,
    GenerationHistoryItem,
    SOURCE_STEP_CONFIG,
)


class TestGenerationSource:
    """Test GenerationSource enum."""

    def test_all_sources_defined(self):
        expected = {
            'job_process', 'company_process',
            'resume', 'cover_letter',
            'insight_overview', 'insight_opportunities', 'insight_companies',
            'insight_skills_intel', 'insight_market', 'insight_networking',
            'skill_roadmap_generate', 'skill_roadmap_extend', 'skill_roadmap_finegrain',
        }
        actual = {s.value for s in GenerationSource}
        assert expected == actual

    def test_source_has_steps(self):
        for source in GenerationSource:
            config = SOURCE_STEP_CONFIG.get(source)
            assert config is not None, f"No step config for {source.value}"
            assert 'steps' in config, f"No steps in config for {source.value}"
            assert 'label' in config, f"No label in config for {source.value}"
            assert len(config['steps']) > 0, f"Empty steps for {source.value}"

    def test_source_group(self):
        assert GenerationSource.JOB_PROCESS.group == 'processing'
        assert GenerationSource.COMPANY_PROCESS.group == 'processing'
        assert GenerationSource.RESUME.group == 'generation'
        assert GenerationSource.COVER_LETTER.group == 'generation'
        assert GenerationSource.INSIGHT_OVERVIEW.group == 'insights'
        assert GenerationSource.SKILL_ROADMAP_GENERATE.group == 'roadmap'

    def test_source_display_name(self):
        assert GenerationSource.JOB_PROCESS.display_name == 'Job Processing'
        assert GenerationSource.RESUME.display_name == 'Resume Generation'
        assert GenerationSource.INSIGHT_OVERVIEW.display_name == 'Insight: Overview'
        assert GenerationSource.SKILL_ROADMAP_GENERATE.display_name == 'Skill Roadmap: Generate'


class TestGenerationStatus:
    """Test GenerationStatus enum."""

    def test_valid_transitions(self):
        transitions = GenerationStatus.valid_transitions()
        assert GenerationStatus.QUEUED in transitions[GenerationStatus.PENDING]
        assert GenerationStatus.PROCESSING in transitions[GenerationStatus.QUEUED]
        assert GenerationStatus.COMPLETED in transitions[GenerationStatus.PROCESSING]
        assert GenerationStatus.FAILED in transitions[GenerationStatus.PROCESSING]
        assert GenerationStatus.CANCELLED in transitions[GenerationStatus.PROCESSING]

    def test_can_transition(self):
        assert GenerationStatus.PENDING.can_transition_to(GenerationStatus.QUEUED)
        assert GenerationStatus.QUEUED.can_transition_to(GenerationStatus.PROCESSING)
        assert not GenerationStatus.COMPLETED.can_transition_to(GenerationStatus.PROCESSING)

    def test_is_terminal(self):
        assert GenerationStatus.COMPLETED.is_terminal
        assert GenerationStatus.FAILED.is_terminal
        assert GenerationStatus.CANCELLED.is_terminal
        assert not GenerationStatus.PENDING.is_terminal
        assert not GenerationStatus.PROCESSING.is_terminal


class TestGenerationRun:
    """Test GenerationRun dataclass."""

    def test_create_run(self):
        run = GenerationRun(
            id=1,
            source=GenerationSource.JOB_PROCESS,
            status=GenerationStatus.QUEUED,
        )
        assert run.id == 1
        assert run.source == GenerationSource.JOB_PROCESS
        assert run.status == GenerationStatus.QUEUED
        assert run.step == 0
        assert run.total_steps > 0

    def test_progress_percentage(self):
        run = GenerationRun(
            id=1,
            source=GenerationSource.RESUME,
            status=GenerationStatus.PROCESSING,
            step=2,
            total_steps=5,
        )
        assert run.progress_pct == 40.0

    def test_progress_zero_steps(self):
        run = GenerationRun(
            id=1,
            source=GenerationSource.RESUME,
            status=GenerationStatus.PROCESSING,
            step=0,
            total_steps=0,
        )
        assert run.progress_pct == 0

    def test_to_history_item(self):
        run = GenerationRun(
            id=42,
            source=GenerationSource.INSIGHT_OVERVIEW,
            status=GenerationStatus.COMPLETED,
            step=4,
            total_steps=4,
            title='Insight: Overview',
            started_at='2026-07-27T10:00:00',
            completed_at='2026-07-27T10:05:00',
            session_id='sess_123',
            provider='openai',
        )
        item = run.to_history_item()
        assert item.id == 42
        assert item.source == 'insights'
        assert item.title == 'Insight: Overview'
        assert item.status == 'completed'
        assert item.duration_seconds == 300

    def test_elapsed_seconds(self):
        run = GenerationRun(
            id=1,
            source=GenerationSource.RESUME,
            status=GenerationStatus.PROCESSING,
            started_at='2026-07-27T10:00:00',
        )
        # Can't test exact elapsed since it depends on current time
        # but we can test it returns a number
        assert isinstance(run.elapsed_seconds, (int, float))


class TestGenerationHistoryItem:
    """Test GenerationHistoryItem dataclass."""

    def test_create_item(self):
        item = GenerationHistoryItem(
            id=1,
            source='job-processing',
            title='example.com',
            status='completed',
        )
        assert item.id == 1
        assert item.source == 'job-processing'
        assert item.session_id is None
        assert item.provider is None
        assert item.error is None

    def test_duration_calculation(self):
        item = GenerationHistoryItem(
            id=1,
            source='insights',
            title='Overview',
            status='completed',
            started_at='2026-07-27T10:00:00',
            completed_at='2026-07-27T10:05:30',
        )
        assert item.duration_seconds == 330

    def test_duration_no_end(self):
        item = GenerationHistoryItem(
            id=1,
            source='insights',
            title='Overview',
            status='processing',
            started_at='2026-07-27T10:00:00',
        )
        assert item.duration_seconds is None

    def test_to_dict(self):
        item = GenerationHistoryItem(
            id=1,
            source='roadmap',
            title='Python (generate)',
            status='completed',
            started_at='2026-07-27T10:00:00',
            completed_at='2026-07-27T10:01:00',
            session_id='sess_abc',
            provider='mimo',
        )
        d = item.to_dict()
        assert d['id'] == 1
        assert d['source'] == 'roadmap'
        assert d['session_id'] == 'sess_abc'
        assert d['provider'] == 'mimo'
        assert d['duration_seconds'] == 60
