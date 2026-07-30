from jobs.infrastructure.models.job_model import JobModel


def test_process_job_returns_202(client, sa_session):
    job = JobModel(
        num=1,
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

    response = client.post("/api/jobs/1/process")
    assert response.status_code == 202
    data = response.json()
    assert "execution_id" in data
    assert data["status"] == "created"


def test_process_job_returns_404_when_not_found(client):
    response = client.post("/api/jobs/999/process")
    assert response.status_code == 404
