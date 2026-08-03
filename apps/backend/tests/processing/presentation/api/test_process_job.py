from unittest.mock import patch

import uuid

from jobs.infrastructure.models.job_model import JobModel


def test_process_job_returns_202(client, sa_session):
    job = JobModel(
        id=str(uuid.uuid7()),
        url="https://example.com/job/1",
        title="Software Engineer",
        company="Tech Corp",
        location="Berlin",
        work_type="Remote",
        deleted=0,
        workflow_log="[]",
        locations='["Berlin"]',
        work_types='["Remote"]',
        employment_type="Full-time",
        rescoring=0,
    )
    sa_session.add(job)
    sa_session.commit()

    with (
        patch("shared.infrastructure.taskiq.client.enqueue_execution_sync") as enqueue,
        patch("shared.infrastructure.events.processing_events.publish_sync") as publish,
    ):
        response = client.post(f"/api/jobs/{job.id}/process")

    assert response.status_code == 202
    data = response.json()
    assert "execution_id" in data
    assert data["status"] == "queued"
    enqueue.assert_called_once_with(data["execution_id"])
    publish.assert_called_once()


def test_process_job_returns_404_when_not_found(client):
    response = client.post("/api/jobs/999/process")
    assert response.status_code == 404
