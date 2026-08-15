"""Tests for SQLAlchemyJobCompanyRepository.

Covers replace-for-job semantics, listing by job/company, and the
recruiter-hiring pair projection used by the company detail API.
"""

import uuid

import pytest

from jobs.infrastructure.models.job_model import JobModel
from jobs.infrastructure.models.job_company_model import JobCompanyModel
from companies.infrastructure.models.company_model import CompanyModel
from jobs.infrastructure.repositories.sa_job_company_repository import (
    SQLAlchemyJobCompanyRepository,
)


@pytest.fixture
def repo(sa_session):
    return SQLAlchemyJobCompanyRepository(sa_session)


def _add_job(session, company_id=None) -> JobModel:
    job = JobModel(
        url="https://example.com/job",
        deleted=0,
        company_id=company_id,
        workflow_log="[]",
        rescoring=0,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def _add_company(session, name="Acme GmbH") -> CompanyModel:
    company = CompanyModel(name=name)
    session.add(company)
    session.commit()
    session.refresh(company)
    return company


def _row(job_id, company_id, role, **kw):
    data = {"job_id": job_id, "company_id": company_id, "role": role}
    data.update(kw)
    return data


class TestReplaceForJob:
    def test_replace_clears_previous_rows(self, repo, sa_session):
        job = _add_job(sa_session)
        recruiter = _add_company(sa_session, "RecruitCo")
        repo.replace_for_job(job.id, [_row(job.id, recruiter.id, "recruiter")])
        sa_session.commit()

        repo.replace_for_job(job.id, [])
        sa_session.commit()

        assert repo.list_by_job(job.id) == []

    def test_replace_persists_columns(self, repo, sa_session):
        job = _add_job(sa_session)
        recruiter = _add_company(sa_session, "RecruitCo")
        repo.replace_for_job(job.id, [
            _row(
                job.id,
                recruiter.id,
                "recruiter",
                company_type="RECRUITING_AGENCY",
                confidence=0.9,
                reason="listed as recruiting partner",
            ),
        ])
        sa_session.commit()

        rows = repo.list_by_job(job.id)
        assert len(rows) == 1
        assert rows[0]["company_id"] == recruiter.id
        assert rows[0]["role"] == "recruiter"
        assert rows[0]["company_type"] == "RECRUITING_AGENCY"
        assert rows[0]["confidence"] == 0.9
        assert rows[0]["reason"] == "listed as recruiting partner"

    def test_replace_only_affects_target_job(self, repo, sa_session):
        job_a = _add_job(sa_session)
        job_b = _add_job(sa_session)
        company = _add_company(sa_session)
        repo.replace_for_job(job_a.id, [_row(job_a.id, company.id, "hiring")])
        repo.replace_for_job(job_b.id, [_row(job_b.id, company.id, "hiring")])
        sa_session.commit()

        repo.replace_for_job(job_a.id, [])
        sa_session.commit()

        assert repo.list_by_job(job_a.id) == []
        assert len(repo.list_by_job(job_b.id)) == 1


class TestListByCompany:
    def test_lists_rows_for_company(self, repo, sa_session):
        job_a = _add_job(sa_session)
        job_b = _add_job(sa_session)
        company = _add_company(sa_session, "RecruitCo")
        repo.replace_for_job(job_a.id, [_row(job_a.id, company.id, "recruiter")])
        repo.replace_for_job(job_b.id, [_row(job_b.id, company.id, "recruiter")])
        sa_session.commit()

        rows = repo.list_by_company(company.id)
        assert len(rows) == 2

    def test_filters_by_role(self, repo, sa_session):
        job = _add_job(sa_session)
        company = _add_company(sa_session, "Mixed Co")
        repo.replace_for_job(job.id, [
            _row(job.id, company.id, "hiring"),
            _row(job.id, company.id, "recruiter"),
        ])
        sa_session.commit()

        recruiters = repo.list_by_company(company.id, role="recruiter")
        assert len(recruiters) == 1
        assert recruiters[0]["role"] == "recruiter"


class TestRecruiterHiringPairs:
    def test_returns_hiring_companies_for_recruiters(self, repo, sa_session):
        recruiter = _add_company(sa_session, "RecruitCo")
        hiring = _add_company(sa_session, "Acme GmbH")
        job_a = _add_job(sa_session, company_id=hiring.id)
        job_b = _add_job(sa_session, company_id=hiring.id)
        job_c = _add_job(sa_session, company_id=hiring.id)
        for job in (job_a, job_b, job_c):
            repo.replace_for_job(job.id, [
                _row(job.id, recruiter.id, "recruiter"),
                _row(job.id, hiring.id, "hiring"),
            ])
        sa_session.commit()

        pairs = repo.recruiter_hiring_pairs(recruiter.id)
        assert len(pairs) == 3
        assert all(p["hiring_company_id"] == hiring.id for p in pairs)

    def test_excludes_self_referencing_hiring_row(self, repo, sa_session):
        company = _add_company(sa_session, "Mixed Co")
        job = _add_job(sa_session, company_id=company.id)
        repo.replace_for_job(job.id, [
            _row(job.id, company.id, "recruiter"),
            _row(job.id, company.id, "hiring"),
        ])
        sa_session.commit()

        assert repo.recruiter_hiring_pairs(company.id) == []

    def test_jobs_without_hiring_row_are_skipped(self, repo, sa_session):
        recruiter = _add_company(sa_session, "RecruitCo")
        job = _add_job(sa_session)
        repo.replace_for_job(job.id, [_row(job.id, recruiter.id, "recruiter")])
        sa_session.commit()

        assert repo.recruiter_hiring_pairs(recruiter.id) == []

    def test_unknown_company_returns_empty(self, repo, sa_session):
        assert repo.recruiter_hiring_pairs("does-not-exist") == []


class TestRecruiterJobCounts:
    def test_aggregates_per_company(self, repo, sa_session):
        recruiter_a = _add_company(sa_session, "RecruitCo A")
        recruiter_b = _add_company(sa_session, "RecruitCo B")
        hiring = _add_company(sa_session, "Acme GmbH")
        job_a = _add_job(sa_session, company_id=hiring.id)
        job_b = _add_job(sa_session, company_id=hiring.id)
        job_c = _add_job(sa_session, company_id=hiring.id)
        repo.replace_for_job(job_a.id, [
            _row(job_a.id, recruiter_a.id, "recruiter"),
            _row(job_a.id, hiring.id, "hiring"),
        ])
        repo.replace_for_job(job_b.id, [
            _row(job_b.id, recruiter_a.id, "recruiter"),
            _row(job_b.id, hiring.id, "hiring"),
        ])
        repo.replace_for_job(job_c.id, [
            _row(job_c.id, recruiter_b.id, "recruiter"),
            _row(job_c.id, hiring.id, "hiring"),
        ])
        sa_session.commit()

        counts = repo.recruiter_job_counts([recruiter_a.id, recruiter_b.id, hiring.id])
        assert counts[recruiter_a.id] == 2
        assert counts[recruiter_b.id] == 1
        assert hiring.id not in counts

    def test_counts_jobs_without_known_hiring_company_but_excludes_self_hiring(self, repo, sa_session):
        recruiter = _add_company(sa_session, "RecruitCo")
        company = _add_company(sa_session, "Mixed Co")
        job_a = _add_job(sa_session, company_id=company.id)
        job_b = _add_job(sa_session)
        repo.replace_for_job(job_a.id, [
            _row(job_a.id, recruiter.id, "recruiter"),
            _row(job_a.id, recruiter.id, "hiring"),
        ])
        repo.replace_for_job(job_b.id, [
            _row(job_b.id, recruiter.id, "recruiter"),
        ])
        sa_session.commit()

        counts = repo.recruiter_job_counts([recruiter.id])
        assert counts.get(recruiter.id, 0) == 1

    def test_empty_input_returns_empty(self, repo, sa_session):
        assert repo.recruiter_job_counts([]) == {}
