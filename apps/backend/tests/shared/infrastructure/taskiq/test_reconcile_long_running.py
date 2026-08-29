"""Tests for reconcile_stuck_executions simple timeout rule.

Verifies that a RUNNING execution older than ``WORKER_JOB_TIMEOUT`` is failed
(with a plain timeout message + ``EXECUTION_FAILED`` event) and that a younger
RUNNING execution is left untouched.
"""

from __future__ import annotations

from datetime import datetime, timedelta, UTC

import pytest

from shared.infrastructure.taskiq import tasks as tasks_module


class FakeRepo:
    def __init__(self, stale_running):
        self._stale = stale_running
        self.saved = []
        self.published = []

    def stale_queued_executions(self, older_than_seconds):
        return []

    def stale_running_executions(self, older_than_seconds):
        from datetime import datetime, timedelta, UTC

        cutoff = datetime.now(UTC) - timedelta(seconds=older_than_seconds)
        out = []
        for e in self._stale:
            sa = getattr(e, "started_at", None)
            if sa is not None and sa < cutoff:
                out.append(e)
        return out

    def save(self, execution):
        self.saved.append(execution)


class FakeSession:
    def close(self):
        pass


def _make_execution(exec_id, started_delta):
    return type(
        "Execution",
        (),
        {
            "id": exec_id,
            "target_type": "job",
            "target_id": "job-1",
            "started_at": datetime.now(UTC) - timedelta(seconds=started_delta),
            "heartbeat_at": datetime.now(UTC) - timedelta(seconds=started_delta),
            "workflow_progress": {"status": "running", "steps": []},
        },
    )()


def _run(monkeypatch, stale_running):
    repo = FakeRepo(stale_running)
    published = []

    async def fake_publish(event_name, *args, **kwargs):
        published.append((event_name, kwargs.get("message")))

    monkeypatch.setattr(
        "processing.infrastructure.repositories.sa_processing_execution_repository.SQLAlchemyProcessingExecutionRepository",
        lambda s: repo,
    )
    monkeypatch.setattr(
        "shared.infrastructure.database.session.get_session_sync",
        lambda: FakeSession(),
    )
    import shared.infrastructure.events.processing_events as pe_mod

    monkeypatch.setattr(pe_mod, "publish", fake_publish)

    return repo, published


@pytest.mark.asyncio
async def test_reconcile_fails_running_exceeding_timeout(monkeypatch):
    execution = _make_execution("exec-old-1", started_delta=612)
    repo, published = _run(monkeypatch, [execution])

    await tasks_module.reconcile_stuck_executions()

    assert getattr(execution, "status", None) == "failed"
    assert "timed out after 612s" in execution.error_message
    assert "execution.failed" in [p[0] for p in published]
    assert repo.saved


@pytest.mark.asyncio
async def test_reconcile_leaves_recent_running_untouched(monkeypatch):
    execution = _make_execution("exec-new-1", started_delta=22)
    repo, published = _run(monkeypatch, [execution])

    await tasks_module.reconcile_stuck_executions()

    assert getattr(execution, "status", None) != "failed"
    assert "execution.failed" not in [p[0] for p in published]
    assert repo.saved == []
