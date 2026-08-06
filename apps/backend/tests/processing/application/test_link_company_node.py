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

    def find_or_create(self, name, website, company_type=None):
        self.calls.append((name, website, company_type))
        if self._error is not None:
            raise self._error
        return self._company_id, self._created


class FakeJobRepo:
    def __init__(self):
        self.updated = []

    def update_fields(self, job_id, **fields):
        self.updated.append((job_id, fields))
        return True


class FakeJobCompanyRepo:
    def __init__(self):
        self.replaced = []

    def replace_for_job(self, job_id, rows):
        self.replaced.append((job_id, rows))


def _state(fields=None, companies=None) -> JobProcessingState:
    state = JobProcessingState(execution_id="exec-1", job_id="job-1")
    state.workflow_progress = progress_ops.build_initial_progress("exec-1")
    state.analysis_result = {"fields": fields or {}, "companies": companies}
    return state


def _hiring(name="Acme Inc", company_type="hiring", confidence=0.98, reason="clearly stated"):
    return {
        "name": name,
        "normalized_name": name,
        "company_type": company_type,
        "confidence": confidence,
        "reason": reason,
    }


def _related(name="Hays", company_type="recruiter", confidence=0.96):
    return {
        "name": name,
        "normalized_name": name,
        "company_type": company_type,
        "confidence": confidence,
        "reason": "published the job",
    }


class TestLinkCompanyNode:
    def test_links_job_to_existing_hiring_company(self):
        matching = FakeMatchingService(company_id="c-1", created=False)
        repo = FakeJobRepo()
        jc_repo = FakeJobCompanyRepo()
        node = LinkCompanyNode(matching, repo, jc_repo)

        state = node(_state(
            fields={"company_url": "https://acme.example"},
            companies={"hiring_company": _hiring(), "related_companies": []},
        ))
        assert repo.updated == [("job-1", {"company_id": "c-1"})]
        assert matching.calls == [("Acme Inc", "https://acme.example", "hiring")]
        assert jc_repo.replaced == [("job-1", [{
            "company_id": "c-1",
            "role": "hiring",
            "company_type": "hiring",
            "confidence": 0.98,
            "reason": "clearly stated",
        }])]
        assert state.status.name == "CREATED"

    def test_creates_and_links_new_hiring_company(self):
        matching = FakeMatchingService(company_id="c-2", created=True)
        repo = FakeJobRepo()
        node = LinkCompanyNode(matching, repo)

        state = node(_state(companies={"hiring_company": _hiring(name="Brand New Co"), "related_companies": []}))
        assert repo.updated == [("job-1", {"company_id": "c-2"})]

    def test_related_companies_become_recruiter_rows(self):
        matching = FakeMatchingService(company_id="c-9", created=True)
        repo = FakeJobRepo()
        jc_repo = FakeJobCompanyRepo()
        node = LinkCompanyNode(matching, repo, jc_repo)

        companies = {
            "hiring_company": _hiring(),
            "related_companies": [_related("Hays"), _related("Michael Page", confidence=0.90)],
        }
        state = node(_state(fields={"company_url": "https://acme.example"}, companies=companies))

        assert matching.calls == [
            ("Acme Inc", "https://acme.example", "hiring"),
            ("Hays", None, "recruiter"),
            ("Michael Page", None, "recruiter"),
        ]
        rows = jc_repo.replaced[0][1]
        assert [r["role"] for r in rows] == ["hiring", "recruiter", "recruiter"]
        assert rows[1]["company_id"] == "c-9"
        assert rows[1]["company_type"] == "recruiter"
        assert rows[1]["confidence"] == 0.96

    def test_null_hiring_falls_back_display_company_to_related(self):
        matching = FakeMatchingService(company_id="c-r", created=False)
        repo = FakeJobRepo()
        jc_repo = FakeJobCompanyRepo()
        node = LinkCompanyNode(matching, repo, jc_repo)

        companies = {
            "hiring_company": None,
            "related_companies": [_related("Hays", confidence=0.95), _related("Michael Page", confidence=0.85)],
        }
        state = node(_state(companies=companies))

        assert ("job-1", {"company": "Hays"}) in repo.updated
        rows = jc_repo.replaced[0][1]
        assert all(r["role"] == "recruiter" for r in rows)

    def test_skips_when_no_companies(self):
        matching = FakeMatchingService()
        repo = FakeJobRepo()
        jc_repo = FakeJobCompanyRepo()
        node = LinkCompanyNode(matching, repo, jc_repo)

        state = node(_state(companies={"hiring_company": None, "related_companies": []}))
        assert repo.updated == []
        assert matching.calls == []
        assert jc_repo.replaced == []

    def test_never_fails_execution_on_match_error(self):
        matching = FakeMatchingService(error=RuntimeError("boom"))
        repo = FakeJobRepo()
        node = LinkCompanyNode(matching, repo)

        state = node(_state(companies={"hiring_company": _hiring(), "related_companies": []}))
        assert repo.updated == []
        assert any("Failed to link company" in e for e in state.errors)
        assert state.status.name == "CREATED"

    def test_noop_when_no_matching_service_wired(self):
        repo = FakeJobRepo()
        node = LinkCompanyNode(None, repo)

        state = node(_state(companies={"hiring_company": _hiring(), "related_companies": []}))
        assert repo.updated == []
