"""API tests for skill multi-categories, catalog CRUD and alias inheritance."""

from skills.infrastructure.models.skill_model import SkillModel, SkillAliasModel


def _create_skill(sa_session, **kwargs):
    defaults = dict(
        name="Python", level=1, category="", hidden=0, source="user",
        source_type="user_input",
    )
    defaults.update(kwargs)
    m = SkillModel(**defaults)
    sa_session.add(m)
    sa_session.commit()
    sa_session.refresh(m)
    return m


def _alias(sa_session, skill_id, alias_name):
    a = SkillAliasModel(
        skill_id=skill_id, alias_name=alias_name, normalized_name=alias_name.lower()
    )
    sa_session.add(a)
    sa_session.commit()
    return a


class TestSkillCategoriesAPI:
    def test_list_items_include_categories(self, client, sa_session):
        skill = _create_skill(sa_session, name="Python")
        resp = client.put(f"/api/skills/{skill.id}/category", json={"category": "technical"})
        assert resp.status_code == 200
        item = client.get("/api/skills/list").json()["items"][0]
        assert "technical" in item["categories"]
        assert item["category"] == "technical"

    def test_update_skill_with_categories(self, client, sa_session):
        skill = _create_skill(sa_session, name="Python")
        resp = client.put(f"/api/skills/{skill.id}", json={"categories": ["technical", "engineering"]})
        assert resp.status_code == 200
        assert set(resp.json()["categories"]) == {"technical", "engineering"}
        assert resp.json()["category"] == "technical"

    def test_create_skill_with_categories(self, client, sa_session):
        resp = client.post("/api/skills", json={"name": "Kafka", "categories": ["technical", "engineering"]})
        assert resp.status_code == 200
        assert set(resp.json()["categories"]) == {"technical", "engineering"}

    def test_category_filter_matches_any_effective_category(self, client, sa_session):
        a = _create_skill(sa_session, name="Python")
        b = _create_skill(sa_session, name="Leadership")
        client.put(f"/api/skills/{a.id}", json={"categories": ["technical", "domain"]})
        client.put(f"/api/skills/{b.id}/category", json={"category": "professional"})
        data = client.get("/api/skills/list?category=domain").json()
        assert data["total_items"] == 1
        assert data["items"][0]["name"] == "Python"

    def test_create_category(self, client, sa_session):
        resp = client.post("/api/skills/categories", json={"name": "security"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "security"
        assert resp.json()["created"] is True

    def test_create_category_idempotent(self, client, sa_session):
        client.post("/api/skills/categories", json={"name": "security"})
        resp = client.post("/api/skills/categories", json={"name": "security"})
        assert resp.status_code == 200
        assert resp.json()["created"] is False

    def test_create_category_blank_400(self, client, sa_session):
        resp = client.post("/api/skills/categories", json={"name": "  "})
        assert resp.status_code == 400

    def test_delete_category_unused(self, client, sa_session):
        client.post("/api/skills/categories", json={"name": "security"})
        resp = client.delete("/api/skills/categories/security")
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"

    def test_delete_category_in_use_conflict(self, client, sa_session):
        skill = _create_skill(sa_session, name="Python")
        client.post("/api/skills/categories", json={"name": "security"})
        client.put(f"/api/skills/{skill.id}/category", json={"category": "security"})
        resp = client.delete("/api/skills/categories/security")
        assert resp.status_code == 409

    def test_delete_category_not_found(self, client, sa_session):
        resp = client.delete("/api/skills/categories/nope")
        assert resp.status_code == 404

    def test_get_categories_endpoint(self, client, sa_session):
        skill = _create_skill(sa_session, name="Python")
        client.put(f"/api/skills/{skill.id}/category", json={"category": "technical"})
        data = client.get("/api/skills/categories").json()
        assert any(c["category"] == "technical" and c["count"] == 1 for c in data)

    def test_alias_inherits_category_via_api(self, client, sa_session):
        kubernetes = _create_skill(sa_session, name="Kubernetes")
        k8s = _create_skill(sa_session, name="K8s")
        _alias(sa_session, kubernetes.id, "K8s")
        client.put(f"/api/skills/{kubernetes.id}/category", json={"category": "engineering"})
        data = client.get("/api/skills/list").json()["items"]
        by_name = {i["name"]: i for i in data}
        assert "engineering" in by_name["K8s"]["categories"]
        assert by_name["K8s"]["category"] == "engineering"

    def test_category_filter_includes_alias_skill(self, client, sa_session):
        kubernetes = _create_skill(sa_session, name="Kubernetes")
        k8s = _create_skill(sa_session, name="K8s")
        _create_skill(sa_session, name="Go")
        _alias(sa_session, kubernetes.id, "K8s")
        client.put(f"/api/skills/{kubernetes.id}/category", json={"category": "engineering"})
        data = client.get("/api/skills/list?category=engineering").json()
        names = {i["name"] for i in data["items"]}
        assert names == {"Kubernetes", "K8s"}

    def test_bulk_categorize_auto_creates(self, client, sa_session):
        a = _create_skill(sa_session, name="Python")
        b = _create_skill(sa_session, name="Go")
        resp = client.post(
            "/api/skills/bulk-categorize", json={"ids": [a.id, b.id], "category": "systems"}
        )
        assert resp.status_code == 200
        assert resp.json()["count"] == 2
        item = client.get("/api/skills/list?category=systems").json()
        assert item["total_items"] == 2
