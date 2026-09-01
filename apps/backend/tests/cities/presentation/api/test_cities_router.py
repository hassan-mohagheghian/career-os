"""Tests for the Cities API router (GET /api/cities/list)."""

from cities.application.services.city_service import CityService
from cities.infrastructure.repositories.sa_city_repository import SQLAlchemyCityRepository
from jobs.infrastructure.models.job_model import JobModel


def _create_city(sa_session, city="Berlin", country="Germany", original_text=None, address=None):
    service = CityService(SQLAlchemyCityRepository(sa_session, user_id="test-user"))
    return service.ensure(city, country, original_text=original_text, address=address)


def _create_job(sa_session, city_id, deleted=0):
    job = JobModel(
        url="https://example.com/job",
        location="Berlin",
        city_id=city_id,
        deleted=deleted,
        user_id="test-user",
    )
    sa_session.add(job)
    sa_session.commit()
    return job


class TestCitiesListAPI:
    def test_lists_cities_with_job_counts_default_sorted_by_jobs(self, client, sa_session):
        berlin = _create_city(sa_session, "Berlin", "Germany")
        munich = _create_city(sa_session, "Munich", "Germany")
        for _ in range(3):
            _create_job(sa_session, berlin["id"])
        _create_job(sa_session, munich["id"])

        resp = client.get("/api/cities/list")
        data = resp.json()
        assert data["total_items"] == 2
        assert data["items"][0]["city"] == "Berlin"
        assert data["items"][0]["job_count"] == 3
        assert data["items"][1]["city"] == "Munich"
        assert data["items"][1]["job_count"] == 1

    def test_sort_by_city_asc(self, client, sa_session):
        _create_city(sa_session, "Munich", "Germany")
        _create_city(sa_session, "Berlin", "Germany")
        resp = client.get("/api/cities/list?sort=city&order=asc")
        cities = [i["city"] for i in resp.json()["items"]]
        assert cities == ["Berlin", "Munich"]

    def test_sort_by_country(self, client, sa_session):
        _create_city(sa_session, "Berlin", "Germany")
        _create_city(sa_session, "Paris", "France")
        resp = client.get("/api/cities/list?sort=country&order=asc")
        countries = [i["country"] for i in resp.json()["items"]]
        assert countries == ["France", "Germany"]

    def test_excludes_deleted_jobs_from_count(self, client, sa_session):
        berlin = _create_city(sa_session, "Berlin", "Germany")
        _create_job(sa_session, berlin["id"], deleted=0)
        _create_job(sa_session, berlin["id"], deleted=1)
        resp = client.get("/api/cities/list")
        item = resp.json()["items"][0]
        assert item["job_count"] == 1

    def test_search_by_country(self, client, sa_session):
        _create_city(sa_session, "Berlin", "Germany")
        _create_city(sa_session, "Paris", "France")
        resp = client.get("/api/cities/list?query=ger")
        data = resp.json()
        assert data["total_items"] == 1
        assert data["items"][0]["country"] == "Germany"

    def test_empty(self, client):
        resp = client.get("/api/cities/list")
        data = resp.json()
        assert data["total_items"] == 0
        assert data["items"] == []


class TestCitiesMergeAPI:
    def _create(self, sa_session, city, country):
        from cities.application.services.city_service import CityService
        service = CityService(SQLAlchemyCityRepository(sa_session, user_id="test-user"))
        return service.ensure(city, country, original_text=f"{city}, {country}")

    def test_merge_ok(self, client, sa_session):
        target = self._create(sa_session, "Munich", "Germany")
        source = self._create(sa_session, "München", "Germany")
        resp = client.post("/api/cities/merge", json={"target_id": target["id"], "source_ids": [source["id"]]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "merged"
        assert data["merged"] == ["München"]

    def test_merge_empty_sources_400(self, client, sa_session):
        target = self._create(sa_session, "Munich", "Germany")
        resp = client.post("/api/cities/merge", json={"target_id": target["id"], "source_ids": []})
        assert resp.status_code == 400

    def test_merge_target_in_sources_400(self, client, sa_session):
        target = self._create(sa_session, "Munich", "Germany")
        resp = client.post("/api/cities/merge", json={"target_id": target["id"], "source_ids": [target["id"]]})
        assert resp.status_code == 400

    def test_merge_missing_target_404(self, client, sa_session):
        resp = client.post("/api/cities/merge", json={"target_id": "nope", "source_ids": ["also-nope"]})
        assert resp.status_code == 404


class TestCitiesAliasesAPI:
    def _create(self, sa_session, city, country):
        from cities.application.services.city_service import CityService
        service = CityService(SQLAlchemyCityRepository(sa_session, user_id="test-user"))
        return service.ensure(city, country)

    def test_add_alias(self, client, sa_session):
        city = self._create(sa_session, "Munich", "Germany")
        resp = client.post(f"/api/cities/{city['id']}/aliases", json={"alias_name": "München"})
        assert resp.status_code == 200
        assert resp.json()["aliases"] == ["München"]

    def test_add_alias_missing_city_404(self, client, sa_session):
        resp = client.post("/api/cities/nope/aliases", json={"alias_name": "X"})
        assert resp.status_code == 404

    def test_remove_alias(self, client, sa_session):
        city = self._create(sa_session, "Munich", "Germany")
        client.post(f"/api/cities/{city['id']}/aliases", json={"alias_name": "München"})
        resp = client.delete(f"/api/cities/{city['id']}/aliases", params={"alias_name": "München"})
        assert resp.status_code == 200
        assert resp.json()["aliases"] == []

    def test_remove_alias_missing_city_404(self, client, sa_session):
        resp = client.delete("/api/cities/nope/aliases", params={"alias_name": "X"})
        assert resp.status_code == 404


class TestCitiesCanonicalAPI:
    def _create(self, sa_session, city, country):
        from cities.application.services.city_service import CityService
        service = CityService(SQLAlchemyCityRepository(sa_session, user_id="test-user"))
        return service.ensure(city, country)

    def test_promote_canonical_ok(self, client, sa_session):
        city = self._create(sa_session, "Munich", "Germany")
        client.post(f"/api/cities/{city['id']}/aliases", json={"alias_name": "München"})
        resp = client.patch(f"/api/cities/{city['id']}/canonical", json={"alias_name": "München"})
        assert resp.status_code == 200
        assert resp.json()["city"] == "München"
        assert resp.json()["aliases"] == ["Munich"]

    def test_promote_unknown_alias_404(self, client, sa_session):
        city = self._create(sa_session, "Munich", "Germany")
        resp = client.patch(f"/api/cities/{city['id']}/canonical", json={"alias_name": "Nope"})
        assert resp.status_code == 404

    def test_promote_missing_city_404(self, client, sa_session):
        resp = client.patch("/api/cities/nope/canonical", json={"alias_name": "X"})
        assert resp.status_code == 404

    def test_promote_conflict_409(self, client, sa_session):
        city = self._create(sa_session, "Munich", "Germany")
        self._create(sa_session, "München", "Germany")
        client.post(f"/api/cities/{city['id']}/aliases", json={"alias_name": "München"})
        resp = client.patch(f"/api/cities/{city['id']}/canonical", json={"alias_name": "München"})
        assert resp.status_code == 409