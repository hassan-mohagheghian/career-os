"""Tests for SQLAlchemyCityRepository merge / alias / promote operations."""

from cities.application.services.city_service import CityService
from cities.infrastructure.repositories.sa_city_repository import SQLAlchemyCityRepository
from jobs.infrastructure.models.job_model import JobModel
from companies.infrastructure.models.company_model import CompanyModel


def _city(sa_session, city, country):
    service = CityService(SQLAlchemyCityRepository(sa_session))
    return service.ensure(city, country, original_text=f"{city}, {country}")


def _job(sa_session, city_id, location="Berlin", deleted=0):
    job = JobModel(url="https://example.com/job", location=location, city_id=city_id, deleted=deleted)
    sa_session.add(job)
    sa_session.commit()
    return job


def _company(sa_session, city_id, name="Co", city="Berlin", country="Germany"):
    co = CompanyModel(name=name, city_id=city_id, city=city, country=country)
    sa_session.add(co)
    sa_session.commit()
    return co


class TestMerge:
    def test_merge_repoints_references_and_hides_source(self, sa_session):
        repo = SQLAlchemyCityRepository(sa_session)
        target = _city(sa_session, "Munich", "Germany")
        source = _city(sa_session, "München", "Germany")
        job = _job(sa_session, source["id"], location="München")
        co = _company(sa_session, source["id"], name="MunichCo", city="München", country="Germany")

        result = repo.merge(target["id"], [source["id"]])

        assert result["status"] == "merged"
        assert result["merged"] == ["München"]
        assert result["aliases"] == ["München"]

        sa_session.expire_all()
        job = sa_session.get(JobModel, job.id)
        co = sa_session.get(CompanyModel, co.id)
        assert job.city_id == target["id"]
        assert job.city == "Munich"
        assert job.country == "Germany"
        assert co.city_id == target["id"]
        assert co.city == "Munich"


        assert repo.get_by_id(source["id"])["hidden"] is True

    def test_merge_folds_job_count_into_target_and_hides_source_from_list(self, sa_session):
        repo = SQLAlchemyCityRepository(sa_session)
        target = _city(sa_session, "Munich", "Germany")
        source = _city(sa_session, "München", "Germany")
        _job(sa_session, target["id"])
        _job(sa_session, source["id"], location="München")

        repo.merge(target["id"], [source["id"]])

        rows = repo.list_with_job_counts()
        names = [r["city"] for r in rows]
        assert "München" not in names
        munich = next(r for r in rows if r["city"] == "Munich")
        assert munich["job_count"] == 2
        assert munich["aliases"] == ["München"]

    def test_merge_skips_missing_and_self(self, sa_session):
        repo = SQLAlchemyCityRepository(sa_session)
        target = _city(sa_session, "Munich", "Germany")

        result = repo.merge(target["id"], [target["id"], "missing-id"])

        assert result["status"] == "merged"
        assert result["merged"] == []

    def test_merge_returns_error_when_target_missing(self, sa_session):
        repo = SQLAlchemyCityRepository(sa_session)
        assert repo.merge("nope", ["also-nope"])["error"] == "Target city not found"


class TestAliases:
    def test_add_and_remove_alias(self, sa_session):
        repo = SQLAlchemyCityRepository(sa_session)
        city = _city(sa_session, "Munich", "Germany")

        updated = repo.add_alias(city["id"], "München")
        assert updated["aliases"] == ["München"]

        updated = repo.add_alias(city["id"], "München")
        assert updated["aliases"] == ["München"]

        updated = repo.remove_alias(city["id"], "München")
        assert updated["aliases"] == []

    def test_add_alias_missing_city_returns_none(self, sa_session):
        repo = SQLAlchemyCityRepository(sa_session)
        assert repo.add_alias("nope", "X") is None


class TestPromoteCanonical:
    def test_promote_swaps_name_and_keeps_old_as_alias(self, sa_session):
        repo = SQLAlchemyCityRepository(sa_session)
        city = _city(sa_session, "Munich", "Germany")
        repo.add_alias(city["id"], "München")

        updated = repo.promote_alias_to_canonical(city["id"], "München")

        assert updated["city"] == "München"
        assert updated["aliases"] == ["Munich"]

    def test_promote_missing_alias_returns_none(self, sa_session):
        repo = SQLAlchemyCityRepository(sa_session)
        city = _city(sa_session, "Munich", "Germany")
        assert repo.promote_alias_to_canonical(city["id"], "Nope") is None

    def test_promote_conflict_returns_error(self, sa_session):
        repo = SQLAlchemyCityRepository(sa_session)
        city = _city(sa_session, "Munich", "Germany")
        other = _city(sa_session, "München", "Germany")
        repo.add_alias(city["id"], "München")

        result = repo.promote_alias_to_canonical(city["id"], "München")

        assert result["error"] == "conflict"