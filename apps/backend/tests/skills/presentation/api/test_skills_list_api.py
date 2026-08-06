"""Tests for the Skills V2 list API (GET /api/skills/list)."""

from skills.infrastructure.models.skill_model import SkillModel, SkillAliasModel


def _create_skill(sa_session, **kwargs) -> SkillModel:
    defaults = dict(
        name="Python",
        level=1,
        roles="",
        path="",
        category="technical",
        confidence=0.0,
        market_relevance=0.0,
        evidence="[]",
        tags="[]",
        hidden=0,
        source="user",
    )
    defaults.update(kwargs)
    model = SkillModel(**defaults)
    sa_session.add(model)
    sa_session.commit()
    sa_session.refresh(model)
    return model


def _create_alias(sa_session, skill_id: int, alias_name: str) -> SkillAliasModel:
    model = SkillAliasModel(
        skill_id=skill_id,
        alias_name=alias_name,
        normalized_name=alias_name.lower(),
    )
    sa_session.add(model)
    sa_session.commit()
    return model


class TestSkillListV2API:
    def test_list_empty(self, client):
        resp = client.get("/api/skills/list")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total_items"] == 0
        assert data["has_more"] is False
        assert data["next_cursor"] is None

    def test_list_with_skills(self, client, sa_session):
        _create_skill(sa_session, name="Python", level=4)
        _create_skill(sa_session, name="Leadership", category="professional")

        data = client.get("/api/skills/list").json()
        assert len(data["items"]) == 2
        assert data["total_items"] == 2
        names = {i["name"] for i in data["items"]}
        assert names == {"Python", "Leadership"}

    def test_list_excludes_hidden(self, client, sa_session):
        _create_skill(sa_session, name="Python", hidden=0)
        _create_skill(sa_session, name="jQuery", hidden=1)

        data = client.get("/api/skills/list").json()
        assert data["total_items"] == 1
        assert data["items"][0]["name"] == "Python"

    def test_pagination_cursor(self, client, sa_session):
        for i in range(5):
            _create_skill(sa_session, name=f"Skill {i}")

        data = client.get("/api/skills/list?page_size=2").json()
        assert len(data["items"]) == 2
        assert data["has_more"] is True
        assert data["next_cursor"]

        data2 = client.get(f"/api/skills/list?page_size=2&cursor={data['next_cursor']}").json()
        assert len(data2["items"]) == 2
        assert data2["has_more"] is True

        data3 = client.get(f"/api/skills/list?page_size=2&cursor={data2['next_cursor']}").json()
        assert len(data3["items"]) == 1
        assert data3["has_more"] is False
        assert data3["next_cursor"] is None

    def test_pagination_total_constant(self, client, sa_session):
        for i in range(4):
            _create_skill(sa_session, name=f"Skill {i}")
        data = client.get("/api/skills/list?page_size=2").json()
        data2 = client.get(f"/api/skills/list?page_size=2&cursor={data['next_cursor']}").json()
        assert data["total_items"] == 4
        assert data2["total_items"] == 4

    def test_search_by_name(self, client, sa_session):
        _create_skill(sa_session, name="PostgreSQL", category="technical")
        _create_skill(sa_session, name="React", category="engineering")

        data = client.get("/api/skills/list?query=postgres").json()
        assert data["total_items"] == 1
        assert data["items"][0]["name"] == "PostgreSQL"

    def test_search_by_roles(self, client, sa_session):
        _create_skill(sa_session, name="Kafka", roles="backend engineer data")
        _create_skill(sa_session, name="Docker", roles="devops")

        data = client.get("/api/skills/list?query=backend").json()
        assert data["total_items"] == 1
        assert data["items"][0]["name"] == "Kafka"

    def test_search_by_alias(self, client, sa_session):
        skill = _create_skill(sa_session, name="React", category="engineering")
        _create_alias(sa_session, skill.id, "ReactJS")

        data = client.get("/api/skills/list?query=reactjs").json()
        assert data["total_items"] == 1
        assert data["items"][0]["name"] == "React"

    def test_category_filter(self, client, sa_session):
        _create_skill(sa_session, name="Python", category="technical")
        _create_skill(sa_session, name="Leadership", category="professional")

        data = client.get("/api/skills/list?category=professional").json()
        assert data["total_items"] == 1
        assert data["items"][0]["name"] == "Leadership"

    def test_sort_by_level(self, client, sa_session):
        _create_skill(sa_session, name="Kafka", level=1)
        _create_skill(sa_session, name="Python", level=4)
        _create_skill(sa_session, name="React", level=2)

        data = client.get("/api/skills/list?sort=level&order=desc").json()
        names = [i["name"] for i in data["items"]]
        assert names == ["Python", "React", "Kafka"]

        data = client.get("/api/skills/list?sort=level&order=asc").json()
        names = [i["name"] for i in data["items"]]
        assert names == ["Kafka", "React", "Python"]

    def test_sort_by_market_relevance_nulls_last(self, client, sa_session):
        _create_skill(sa_session, name="No Demand", market_relevance=0)
        _create_skill(sa_session, name="High Demand", market_relevance=9.0)

        data = client.get("/api/skills/list?sort=market_relevance&order=desc").json()
        names = [i["name"] for i in data["items"]]
        assert names == ["High Demand", "No Demand"]

    def test_default_sort_newest_first(self, client, sa_session):
        _create_skill(sa_session, name="Old Skill", created_at="2026-01-01T00:00:00Z")
        _create_skill(sa_session, name="New Skill", created_at="2026-07-01T00:00:00Z")

        data = client.get("/api/skills/list").json()
        names = [i["name"] for i in data["items"]]
        assert names == ["New Skill", "Old Skill"]

    def test_item_shape(self, client, sa_session):
        skill = _create_skill(
            sa_session,
            name="Python",
            level=4,
            roles="backend",
            path="engineer",
            category="technical",
            confidence=0.9,
            market_relevance=8.5,
            evidence="[]",
            tags='["ai", "ml"]',
        )
        _create_alias(sa_session, skill.id, "CPython")

        item = client.get("/api/skills/list").json()["items"][0]
        assert item["id"] == skill.id
        assert item["name"] == "Python"
        assert item["level"] == 4
        assert item["roles"] == "backend"
        assert item["path"] == "engineer"
        assert item["category"] == "technical"
        assert item["confidence"] == 0.9
        assert item["market_relevance"] == 8.5
        assert item["tags"] == ["ai", "ml"]
        assert item["aliases"] == ["CPython"]
        assert item["created_at"] is not None
