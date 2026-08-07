from datetime import datetime, UTC
from unittest.mock import patch

import uuid

from processing.infrastructure.models.processing_execution_model import ProcessingExecutionModel


def _execution(status: str, **extra) -> ProcessingExecutionModel:
    return ProcessingExecutionModel(
        id=str(uuid.uuid4()),
        execution_type="job_processing",
        status=status,
        target_type="job",
        target_id="job-1",
        created_at=datetime.now(UTC),
        **extra,
    )


def test_start_queued_execution(client, sa_session):
    execution = _execution("queued")
    sa_session.add(execution)
    sa_session.commit()

    with (
        patch("shared.infrastructure.taskiq.client.enqueue_execution_sync") as enqueue,
        patch("shared.infrastructure.events.processing_events.publish_sync") as publish,
    ):
        response = client.post(f"/api/processing/executions/{execution.id}/start")

    assert response.status_code == 200
    data = response.json()
    assert data["execution_id"] == execution.id
    assert data["status"] == "queued"
    assert data["started"] is True
    enqueue.assert_called_once_with(execution.id)
    publish.assert_called_once()


def test_start_running_execution_is_conflict(client, sa_session):
    execution = _execution("running")
    sa_session.add(execution)
    sa_session.commit()

    with (
        patch("shared.infrastructure.taskiq.client.enqueue_execution_sync") as enqueue,
        patch("shared.infrastructure.events.processing_events.publish_sync") as publish,
    ):
        response = client.post(f"/api/processing/executions/{execution.id}/start")

    assert response.status_code == 409
    enqueue.assert_not_called()
    publish.assert_not_called()


def test_start_unknown_execution_returns_404(client, sa_session):
    response = client.post("/api/processing/executions/unknown-execution/start")
    assert response.status_code == 404


def test_cancel_running_execution(client, sa_session):
    execution = _execution("running")
    sa_session.add(execution)
    sa_session.commit()

    with patch("shared.infrastructure.events.processing_events.publish_sync") as publish:
        response = client.post(f"/api/processing/executions/{execution.id}/cancel")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"
    publish.assert_called_once()


def test_retry_failed_execution(client, sa_session):
    execution = _execution("failed")
    sa_session.add(execution)
    sa_session.commit()

    with (
        patch("shared.infrastructure.taskiq.client.enqueue_execution_sync") as enqueue,
        patch("shared.infrastructure.events.processing_events.publish_sync") as publish,
    ):
        response = client.post(f"/api/processing/executions/{execution.id}/retry")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert data["retry_of"] == execution.id
    assert data["execution_id"] != execution.id
    enqueue.assert_called_once_with(data["execution_id"])

    sa_session.expire_all()
    old = sa_session.get(ProcessingExecutionModel, execution.id)
    assert old.status == "cancelled"


def test_retry_removes_failed_entry_from_queue_snapshot(client, sa_session):
    execution = _execution("failed")
    sa_session.add(execution)
    sa_session.commit()

    with (
        patch("shared.infrastructure.taskiq.client.enqueue_execution_sync"),
        patch("shared.infrastructure.events.processing_events.publish_sync"),
    ):
        response = client.post(f"/api/processing/executions/{execution.id}/retry")

    assert response.status_code == 200
    new_id = response.json()["execution_id"]
    snapshot = client.get("/api/processing/queue").json()
    assert all(
        entry["execution_id"] != execution.id
        for section in snapshot.values()
        for entry in section
    )
    assert any(entry["execution_id"] == new_id for entry in snapshot["queued"])


def test_retry_non_failed_execution_is_conflict(client, sa_session):
    execution = _execution("completed")
    sa_session.add(execution)
    sa_session.commit()

    with (
        patch("shared.infrastructure.taskiq.client.enqueue_execution_sync") as enqueue,
        patch("shared.infrastructure.events.processing_events.publish_sync") as publish,
    ):
        response = client.post(f"/api/processing/executions/{execution.id}/retry")

    assert response.status_code == 409
    enqueue.assert_not_called()
    publish.assert_not_called()


def test_remove_queue_entry(client, sa_session):
    execution = _execution("failed")
    sa_session.add(execution)
    sa_session.commit()

    with patch("shared.infrastructure.events.processing_events.publish_sync") as publish:
        response = client.delete(f"/api/processing/queue/{execution.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["removed"] is True
    publish.assert_called_once()

    sa_session.expire_all()
    stored = sa_session.get(ProcessingExecutionModel, execution.id)
    assert stored.status == "cancelled"


def test_removed_failed_execution_disappears_from_queue(client, sa_session):
    execution = _execution("failed")
    sa_session.add(execution)
    sa_session.commit()

    client.delete(f"/api/processing/queue/{execution.id}")
    response = client.get("/api/processing/queue")

    assert response.status_code == 200
    snapshot = response.json()
    assert all(
        entry["execution_id"] != execution.id
        for section in snapshot.values()
        for entry in section
    )
