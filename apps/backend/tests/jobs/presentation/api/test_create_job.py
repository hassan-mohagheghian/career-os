"""Tests for POST /api/jobs (Add Job Drawer) including the queue flag."""

from unittest.mock import patch

from jobs.infrastructure.models.job_model import JobModel
from processing.infrastructure.models.processing_execution_model import ProcessingExecutionModel


def _count_executions(test_db, job_id: str) -> int:
    return test_db.query(ProcessingExecutionModel).filter(
        ProcessingExecutionModel.target_type == "job",
        ProcessingExecutionModel.target_id == job_id,
    ).count()


def test_create_job_returns_201_imported(client, test_db):
    with (
        patch("shared.infrastructure.taskiq.client.enqueue_execution_sync") as enqueue,
        patch("shared.infrastructure.events.processing_events.publish_sync") as publish,
    ):
        response = client.post(
            "/api/jobs",
            json={
                "job_post_url": "https://example.com/jobs/backend-engineer",
                "job_title": "Backend Engineer",
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "imported"
    assert data["execution_id"] is None

    job = test_db.query(JobModel).filter(JobModel.id == data["id"]).first()
    assert job is not None
    assert job.title == "Backend Engineer"
    assert job.status == "imported"
    assert _count_executions(test_db, job.id) == 0
    enqueue.assert_not_called()
    publish.assert_not_called()


def test_create_job_with_links_and_notes(client, test_db):
    response = client.post(
        "/api/jobs",
        json={
            "job_post_url": "https://example.com/jobs/senior-python",
            "links": [
                {"title": "LinkedIn", "url": "https://linkedin.com/jobs/view/123"},
            ],
            "notes": [
                {"title": "Requirements", "content": "Python 3.14 experience"},
            ],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "imported"

    job = test_db.query(JobModel).filter(JobModel.id == data["id"]).first()
    assert '"url": "https://linkedin.com/jobs/view/123"' in job.links
    assert "Python 3.14 experience" in job.notes


def test_create_and_queue_dispatches_instant_workflow(client, test_db):
    with (
        patch("shared.infrastructure.taskiq.client.enqueue_execution_sync") as enqueue,
        patch("shared.infrastructure.events.processing_events.publish_sync") as publish,
    ):
        response = client.post(
            "/api/jobs",
            json={
                "job_post_url": "https://example.com/jobs/queue-me",
                "job_title": "Queue Me",
                "queue": True,
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "queued"
    assert data["execution_id"] is not None

    execution = test_db.query(ProcessingExecutionModel).filter(
        ProcessingExecutionModel.id == data["execution_id"]
    ).first()
    assert execution is not None
    assert execution.target_type == "job"
    assert execution.target_id == data["id"]
    assert execution.status == "queued"

    enqueue.assert_called_once_with(data["execution_id"])
    publish.assert_called_once()


def test_create_with_queue_defaults_false(client, test_db):
    with patch("shared.infrastructure.taskiq.client.enqueue_execution_sync") as enqueue:
        response = client.post(
            "/api/jobs",
            json={"job_post_url": "https://example.com/jobs/no-queue"},
        )

    assert response.status_code == 201
    assert response.json()["status"] == "imported"
    enqueue.assert_not_called()


def test_create_duplicate_url_returns_409(client, test_db):
    url = "https://example.com/jobs/duplicate"
    with patch("shared.infrastructure.taskiq.client.enqueue_execution_sync"):
        first = client.post("/api/jobs", json={"job_post_url": url})
        assert first.status_code == 201

    second = client.post("/api/jobs", json={"job_post_url": url, "queue": True})
    assert second.status_code == 409


def test_create_job_missing_url_returns_422(client):
    response = client.post("/api/jobs", json={"job_title": "No URL"})
    assert response.status_code == 422
