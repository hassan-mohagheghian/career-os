"""Tests for the LinkCompanyNode — best-effort company linking during job analysis."""

from processing.application.workflows import progress_ops
from processing.application.workflows.job_analysis.nodes import LinkCompanyNode
from processing.domain.workflow.job_processing_state import JobProcessingState


class FakeMatchingService:
    def __init__(self, company_id="company-1", created=False, error=None):
        self._company_id = company_id
        self._created = created
        self._error = error
        self.calls = []

    def find_or_create(self, name, website):
        self.calls.append((name, website))
        if self._error is not None:
            raise self._error
        return self._company_id, self._created


class FakeJobRepo:
    def __init__(self):
        self.updated = []

    def update_fields(self, job_id, **fields):
        self.updated.append((job_id, fields))
        return True


def _state(**analysis) -> JobProcessingState:
    state = JobProcessingState(execution_id="exec-1", job_id="job-1")
    state.workflow_progress = progress_ops.build_initial_progress("exec-1")
    state.analysis_result = {"fields": analysis}
    return state


class TestLinkCompanyNode:
    def test_links_job_to_existing_company(self):
        matching = FakeMatchingService(company_id="c-1", created=False)
        repo = FakeJobRepo()
        node = LinkCompanyNode(matching, repo)

        state = node(_state(company="Acme Inc", company_url="https://acme.example"))
        assert repo.updated == [("job-1", {"company_id": "c-1"})]
        assert matching.calls == [("Acme Inc", "https://acme.example")]
        assert state.status.name == "CREATED"

    def test_creates_and_links_new_company(self):
        matching = FakeMatchingService(company_id="c-2", created=True)
        repo = FakeJobRepo()
        node = LinkCompanyNode(matching, repo)

        state = node(_state(company="Brand New Co"))
        assert repo.updated == [("job-1", {"company_id": "c-2"})]

    def test_skips_when_no_company(self):
        matching = FakeMatchingService()
        repo = FakeJobRepo()
        node = LinkCompanyNode(matching, repo)

        state = node(_state(title="A job without company"))
        assert repo.updated == []
        assert matching.calls == []

    def test_never_fails_execution_on_match_error(self):
        matching = FakeMatchingService(error=RuntimeError("boom"))
        repo = FakeJobRepo()
        node = LinkCompanyNode(matching, repo)

        state = node(_state(company="Acme Inc"))
        assert repo.updated == []
        assert any("Failed to link company" in e for e in state.errors)
        assert state.status.name == "CREATED"

    def test_noop_when_no_matching_service_wired(self):
        repo = FakeJobRepo()
        node = LinkCompanyNode(None, repo)

        state = node(_state(company="Acme Inc"))
        assert repo.updated == []
