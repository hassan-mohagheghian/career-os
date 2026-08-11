"""Tests for job URL duplicate rules (jobs.domain.services.job_url_rules)."""

from jobs.domain.services.job_url_rules import (
    JOB_URL_DUPLICATE_RULES,
    LinkedInJobUrlRule,
    find_duplicate_job,
)


class FakeRepo:
    def __init__(self, jobs=None):
        self.jobs = jobs or []
        self.calls = []

    def get_by_url_fragment(self, fragment):
        self.calls.append(fragment)
        for job in self.jobs:
            if job["url"] and fragment in job["url"]:
                return job
        return None


LINKEDIN_WITH_TRACKING = (
    "https://www.linkedin.com/jobs/view/4333938709/"
    "?trackingId=ZCfBkmB6DbH1BJW0ll2JzA%3D%3D&refId=oDiPdgm6JnDKSsvRCjG9Sg%3D%3D"
)


class TestLinkedInJobUrlRule:
    def test_extracts_job_id_from_path_ignoring_query(self):
        assert LinkedInJobUrlRule().duplicate_fragment(
            LINKEDIN_WITH_TRACKING
        ) == "linkedin.com/jobs/view/4333938709"

    def test_matches_without_trailing_slash(self):
        assert LinkedInJobUrlRule().duplicate_fragment(
            "https://www.linkedin.com/jobs/view/4333938709"
        ) == "linkedin.com/jobs/view/4333938709"

    def test_matches_without_www(self):
        assert LinkedInJobUrlRule().duplicate_fragment(
            "https://linkedin.com/jobs/view/12345/"
        ) == "linkedin.com/jobs/view/12345"

    def test_returns_none_for_non_linkedin(self):
        assert LinkedInJobUrlRule().duplicate_fragment(
            "https://company.com/jobs/view/12345"
        ) is None

    def test_returns_none_for_linkedin_non_job_path(self):
        assert LinkedInJobUrlRule().duplicate_fragment(
            "https://www.linkedin.com/in/someone"
        ) is None

    def test_returns_none_for_empty(self):
        assert LinkedInJobUrlRule().duplicate_fragment("") is None


class TestFindDuplicateJob:
    def test_returns_existing_job_when_rule_matches(self):
        existing = {"id": "job-1", "url": LINKEDIN_WITH_TRACKING, "deleted": 0}
        repo = FakeRepo([existing])
        result = find_duplicate_job(repo, LINKEDIN_WITH_TRACKING)
        assert result is existing

    def test_returns_none_when_no_job_matches(self):
        repo = FakeRepo([{"id": "job-1", "url": "https://example.com/x", "deleted": 0}])
        assert find_duplicate_job(repo, LINKEDIN_WITH_TRACKING) is None

    def test_skips_deleted_jobs(self):
        deleted = {"id": "job-1", "url": LINKEDIN_WITH_TRACKING, "deleted": 1}
        repo = FakeRepo([deleted])
        assert find_duplicate_job(repo, LINKEDIN_WITH_TRACKING) is None

    def test_skips_rules_that_do_not_apply(self):
        repo = FakeRepo([{"id": "job-1", "url": "https://example.com/jobs/123", "deleted": 0}])
        assert find_duplicate_job(repo, "https://example.com/jobs/123") is None
        assert repo.calls == []


def test_registry_contains_linkedin_rule():
    assert any(isinstance(rule, LinkedInJobUrlRule) for rule in JOB_URL_DUPLICATE_RULES)
