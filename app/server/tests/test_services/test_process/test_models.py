"""Tests for domain models — value objects, enums, and events."""

import pytest
from shared.infrastructure.process.models import (
    ItemStatus, PipelineStep, CompanyPipelineStep,
    WorkflowLogEntry, ScoreResult, ProcessHandle,
    StatusUpdate, LogEntry, ProcessingComplete, ProcessingError,
)


# ── ItemStatus ─────────────────────────────────────────────────────

class TestItemStatus:
    def test_valid_transitions_from_pending(self):
        assert ItemStatus.PENDING.can_transition_to(ItemStatus.QUEUED)
        assert ItemStatus.PENDING.can_transition_to(ItemStatus.FAILED)
        assert not ItemStatus.PENDING.can_transition_to(ItemStatus.PROCESSING)
        assert not ItemStatus.PENDING.can_transition_to(ItemStatus.DONE)

    def test_valid_transitions_from_queued(self):
        assert ItemStatus.QUEUED.can_transition_to(ItemStatus.PROCESSING)
        assert ItemStatus.QUEUED.can_transition_to(ItemStatus.PENDING)
        assert not ItemStatus.QUEUED.can_transition_to(ItemStatus.DONE)

    def test_valid_transitions_from_processing(self):
        assert ItemStatus.PROCESSING.can_transition_to(ItemStatus.DONE)
        assert ItemStatus.PROCESSING.can_transition_to(ItemStatus.FAILED)
        assert ItemStatus.PROCESSING.can_transition_to(ItemStatus.PAUSED)
        assert ItemStatus.PROCESSING.can_transition_to(ItemStatus.QUEUED)

    def test_valid_transitions_from_paused(self):
        assert ItemStatus.PAUSED.can_transition_to(ItemStatus.QUEUED)
        assert ItemStatus.PAUSED.can_transition_to(ItemStatus.PENDING)
        assert not ItemStatus.PAUSED.can_transition_to(ItemStatus.DONE)

    def test_valid_transitions_from_done(self):
        assert ItemStatus.DONE.can_transition_to(ItemStatus.PENDING)  # reprocess
        assert not ItemStatus.DONE.can_transition_to(ItemStatus.PROCESSING)

    def test_valid_transitions_from_failed(self):
        assert ItemStatus.FAILED.can_transition_to(ItemStatus.PENDING)
        assert ItemStatus.FAILED.can_transition_to(ItemStatus.QUEUED)
        assert not ItemStatus.FAILED.can_transition_to(ItemStatus.DONE)

    def test_string_values(self):
        assert ItemStatus.PENDING.value == 'pending'
        assert ItemStatus.PROCESSING.value == 'processing'
        assert ItemStatus.DONE.value == 'done'


# ── PipelineStep ───────────────────────────────────────────────────

class TestPipelineStep:
    def test_all_steps_have_labels(self):
        for step in PipelineStep:
            assert step.label, f"{step.name} has no label"

    def test_step_order(self):
        steps = list(PipelineStep)
        assert steps[0] == PipelineStep.FETCH
        assert steps[-1] == PipelineStep.DONE


class TestCompanyPipelineStep:
    def test_all_steps_have_labels(self):
        for step in CompanyPipelineStep:
            assert step.label, f"{step.name} has no label"

    def test_step_order(self):
        steps = list(CompanyPipelineStep)
        assert steps[0] == CompanyPipelineStep.FETCH
        assert steps[-1] == CompanyPipelineStep.DONE


# ── WorkflowLogEntry ───────────────────────────────────────────────

class TestWorkflowLogEntry:
    def test_create(self):
        entry = WorkflowLogEntry(step='fetch', msg='Fetching URL')
        assert entry.step == 'fetch'
        assert entry.msg == 'Fetching URL'
        assert entry.ts  # auto-generated

    def test_to_dict(self):
        entry = WorkflowLogEntry(step='fetch', msg='Done', ts='12:34:56')
        d = entry.to_dict()
        assert d == {'step': 'fetch', 'msg': 'Done', 'ts': '12:34:56'}

    def test_from_dict(self):
        d = {'step': 'analyze', 'msg': 'Scoring', 'ts': '10:00:00'}
        entry = WorkflowLogEntry.from_dict(d)
        assert entry.step == 'analyze'
        assert entry.msg == 'Scoring'
        assert entry.ts == '10:00:00'

    def test_roundtrip(self):
        original = WorkflowLogEntry(step='save', msg='Saved', ts='09:00:00')
        restored = WorkflowLogEntry.from_dict(original.to_dict())
        assert restored == original

    def test_frozen(self):
        entry = WorkflowLogEntry(step='x', msg='y')
        with pytest.raises(AttributeError):
            entry.step = 'changed'


# ── ScoreResult ────────────────────────────────────────────────────

class TestScoreResult:
    def test_compute_overall(self):
        s = ScoreResult(fit_score=80, success_score=60)
        s.compute_overall()
        assert s.overall_score == int(round(80 * 0.6 + 60 * 0.4))  # 72

    def test_compute_overall_custom_weights(self):
        s = ScoreResult(fit_score=100, success_score=0)
        s.compute_overall(fit_weight=1.0, success_weight=0.0)
        assert s.overall_score == 100

    def test_compute_overall_none_values(self):
        s = ScoreResult(fit_score=None, success_score=50)
        s.compute_overall()
        assert s.overall_score is None

    def test_defaults(self):
        s = ScoreResult()
        assert s.grade == 'P'
        assert s.match == 'Medium'
        assert s.fit_score is None


# ── Domain Events ──────────────────────────────────────────────────

class TestStatusUpdate:
    def test_create(self):
        e = StatusUpdate(table='pending_jobs', pid=1, step='step_fetch', val=1)
        assert e.table == 'pending_jobs'
        assert e.pid == 1
        assert e.val == 1
        assert e.ts  # auto-generated

    def test_frozen(self):
        e = StatusUpdate(table='t', pid=1, step='s', val=0)
        with pytest.raises(AttributeError):
            e.pid = 2


class TestLogEntry:
    def test_create(self):
        e = LogEntry(table='pending_jobs', pid=1, step='fetch', msg='hello')
        assert e.msg == 'hello'


class TestProcessingComplete:
    def test_create(self):
        e = ProcessingComplete(table='pending_jobs', pid=1, result={'num': 42})
        assert e.result['num'] == 42


class TestProcessingError:
    def test_create(self):
        e = ProcessingError(table='pending_jobs', pid=1, msg='boom', step='fetch')
        assert e.step == 'fetch'
        assert e.msg == 'boom'
