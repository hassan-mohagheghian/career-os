"""Tests for the Companies V2 list API (GET /api/companies/list)."""

import json

from companies.infrastructure.models.company_model import CompanyModel, CompanyIntelligenceModel


def _create_company(sa_session, **kwargs) -> CompanyModel:
    defaults = dict(
        name="Tech Corp",
        industry="Technology",
        city="Berlin",
        country="Germany",
        company_size="500",
        status="completed",
        notes="[]",
        workflow_log="[]",
        source="web",
        input_type="url",
    )
    defaults.update(kwargs)
    model = CompanyModel(**defaults)
    sa_session.add(model)
    sa_session.commit()
    sa_session.refresh(model)
    return model


def _create_intel(sa_session, company_id: str, scores: dict) -> CompanyIntelligenceModel:
    model = CompanyIntelligenceModel(
        company_id=company_id,
        scores=json.dumps(scores),
        overview=json.dumps({"products": "X"}),
    )
    sa_session.add(model)
    sa_session.commit()
    return model


class TestCompanyListV2API:
    def test_list_empty(self, client):
        resp = client.get("/api/companies/list")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total_items"] == 0
        assert data["has_more"] is False
        assert data["next_cursor"] is None

    def test_list_with_companies(self, client, sa_session):
        _create_company(sa_session, name="Alpha Corp", industry="Technology")
        _create_company(sa_session, name="Beta Inc", industry="Finance")

        data = client.get("/api/companies/list").json()
        assert len(data["items"]) == 2
        assert data["total_items"] == 2

    def test_list_excludes_unnamed(self, client, sa_session):
        _create_company(sa_session, name="")
        _create_company(sa_session, name=None)
        _create_company(sa_session, name="Named Co")

        data = client.get("/api/companies/list").json()
        assert data["total_items"] == 1
        assert data["items"][0]["name"] == "Named Co"

    def test_pagination_cursor(self, client, sa_session):
        for i in range(5):
            _create_company(sa_session, name=f"Co {i}")

        data = client.get("/api/companies/list?page_size=2").json()
        assert len(data["items"]) == 2
        assert data["has_more"] is True
        assert data["next_cursor"]

        data2 = client.get(f"/api/companies/list?page_size=2&cursor={data['next_cursor']}").json()
        assert len(data2["items"]) == 2
        assert data2["has_more"] is True

        data3 = client.get(f"/api/companies/list?page_size=2&cursor={data2['next_cursor']}").json()
        assert len(data3["items"]) == 1
        assert data3["has_more"] is False
        assert data3["next_cursor"] is None

    def test_pagination_total_constant(self, client, sa_session):
        for i in range(4):
            _create_company(sa_session, name=f"Co {i}")
        data = client.get("/api/companies/list?page_size=2").json()
        data2 = client.get(f"/api/companies/list?page_size=2&cursor={data['next_cursor']}").json()
        assert data["total_items"] == 4
        assert data2["total_items"] == 4

    def test_search_by_name_and_city(self, client, sa_session):
        _create_company(sa_session, name="SAP SE", city="Waldorf")
        _create_company(sa_session, name="Delivery Hero", city="Berlin", description="food delivery")

        data = client.get("/api/companies/list?query=berlin").json()
        assert data["total_items"] == 1
        assert data["items"][0]["name"] == "Delivery Hero"

        data = client.get("/api/companies/list?query=delivery").json()
        assert data["total_items"] == 1

    def test_industry_filter(self, client, sa_session):
        _create_company(sa_session, name="A", industry="Technology")
        _create_company(sa_session, name="B", industry="Finance")

        data = client.get("/api/companies/list?industry=Finance").json()
        assert data["total_items"] == 1
        assert data["items"][0]["name"] == "B"

    def test_sort_by_fit_score_nulls_last(self, client, sa_session):
        c1 = _create_company(sa_session, name="No Score")
        _create_intel(sa_session, c1.id, {"company_fit_score": None})
        c2 = _create_company(sa_session, name="Low Fit")
        _create_intel(sa_session, c2.id, {"company_fit_score": 30})
        c3 = _create_company(sa_session, name="High Fit")
        _create_intel(sa_session, c3.id, {"company_fit_score": 90})

        data = client.get("/api/companies/list?sort=fit_score&order=desc").json()
        names = [i["name"] for i in data["items"]]
        assert names == ["High Fit", "Low Fit", "No Score"]

        data = client.get("/api/companies/list?sort=fit_score&order=asc").json()
        names = [i["name"] for i in data["items"]]
        assert names == ["Low Fit", "High Fit", "No Score"]

    def test_default_sort_newest_first(self, client, sa_session):
        _create_company(sa_session, name="Old Co", created_at="2026-01-01T00:00:00Z")
        _create_company(sa_session, name="New Co", created_at="2026-07-01T00:00:00Z")

        data = client.get("/api/companies/list").json()
        names = [i["name"] for i in data["items"]]
        assert names == ["New Co", "Old Co"]

    def test_scores_and_processing_shape(self, client, sa_session):
        c = _create_company(
            sa_session,
            name="Shape Co",
            status="processing",
            current_node="analyze_company",
            progress_pct=40,
        )
        _create_intel(sa_session, c.id, {
            "company_overall_score": 78,
            "company_fit_score": 80,
            "company_success_score": 76,
            "overall_grade": "A",
        })

        item = client.get("/api/companies/list").json()["items"][0]
        assert item["scores"]["overall"] == 78
        assert item["scores"]["fit"] == 80
        assert item["scores"]["success"] == 76
        assert item["scores"]["overall_grade"] == "A"
        assert item["processing"]["status"] == "processing"
        assert item["processing"]["current_node"] == "analyze_company"
        assert item["processing"]["progress_pct"] == 40

    def test_legacy_detail_route_still_works(self, client, sa_session):
        c = _create_company(sa_session, name="Detail Co")
        resp = client.get(f"/api/companies/{c.id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Detail Co"
