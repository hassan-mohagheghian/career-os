"""Tests for the Placeholders API router."""

from __future__ import annotations

from placeholders.infrastructure.models.placeholder_model import PlaceholderModel


class TestPlaceholdersAPI:
    def test_list_returns_keys_and_values(self, client, sa_session):
        sa_session.add(PlaceholderModel(key="name", value="Hassan"))
        sa_session.commit()
        resp = client.get("/api/placeholders")
        assert resp.status_code == 200
        body = resp.json()
        keys = {k["key"] for k in body["keys"]}
        assert "name" in keys and "email" in keys and "linkedin" in keys
        assert body["values"]["name"] == "Hassan"

    def test_update_upserts_values(self, client, sa_session):
        resp = client.put("/api/placeholders", json={"name": "Hassan", "email": "h@x.com"})
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert {i["key"] for i in items} == {"name", "email"}
        fetched = client.get("/api/placeholders").json()
        assert fetched["values"]["email"] == "h@x.com"

    def test_update_overwrites_existing(self, client, sa_session):
        sa_session.add(PlaceholderModel(key="name", value="Old"))
        sa_session.commit()
        client.put("/api/placeholders", json={"name": "New"})
        assert client.get("/api/placeholders").json()["values"]["name"] == "New"