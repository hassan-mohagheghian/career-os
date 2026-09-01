"""API tests for skill normalization: breakdown, promote-to-canonical, breakdowns."""

from skills.infrastructure.models.skill_model import SkillModel, SkillAliasModel, SkillMentionModel


def _create_skill(sa_session, name: str, hidden: int = 0) -> SkillModel:
    model = SkillModel(name=name, hidden=hidden, source="user", source_type="user_input", user_id="test-user")
    sa_session.add(model)
    sa_session.commit()
    sa_session.refresh(model)
    return model


def _create_alias(sa_session, skill_id: int, alias_name: str) -> SkillAliasModel:
    model = SkillAliasModel(skill_id=skill_id, alias_name=alias_name, normalized_name=alias_name.lower())
    sa_session.add(model)
    sa_session.commit()
    return model


class TestBreakDownAPI:
    def test_break_down_skill(self, client, sa_session):
        origin = _create_skill(sa_session, name="Data Engineering")

        resp = client.post(f"/api/skills/{origin.id}/breakdown", json={"child_names": ["Spark", "Airflow"]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "broken_down"
        assert data["hidden"] is True
        assert len(data["children"]) == 2

        # Origin is hidden now; children are visible.
        listing = client.get("/api/skills/list").json()
        assert origin.id not in {i["id"] for i in listing["items"]}

    def test_break_down_duplicates_mentions(self, client, sa_session):
        origin = _create_skill(sa_session, name="Data Engineering")
        mention = SkillMentionModel(skill_id=origin.id, source_type="job", source_id="job-1")
        sa_session.add(mention)
        sa_session.commit()

        resp = client.post(f"/api/skills/{origin.id}/breakdown", json={"child_names": ["Spark", "Airflow"]})
        assert resp.status_code == 200
        child_ids = [c["id"] for c in resp.json()["children"]]
        for cid in child_ids:
            mentions = sa_session.query(SkillMentionModel).filter(SkillMentionModel.skill_id == cid).all()
            assert len(mentions) == 1

    def test_break_down_not_found(self, client):
        resp = client.post("/api/skills/9999/breakdown", json={"child_names": ["Spark", "Airflow"]})
        assert resp.status_code == 404

    def test_break_down_requires_two_children(self, client, sa_session):
        origin = _create_skill(sa_session, name="Data Engineering")
        resp = client.post(f"/api/skills/{origin.id}/breakdown", json={"child_names": ["Spark"]})
        assert resp.status_code == 422


class TestBreakdownsAPI:
    def test_get_skill_breakdowns(self, client, sa_session):
        origin = _create_skill(sa_session, name="Data Engineering")
        client.post(f"/api/skills/{origin.id}/breakdown", json={"child_names": ["Spark", "Airflow"]})

        resp = client.get(f"/api/skills/{origin.id}/breakdowns")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["children"]) == 2

    def test_list_breakdowns_map(self, client, sa_session):
        origin = _create_skill(sa_session, name="Data Engineering")
        client.post(f"/api/skills/{origin.id}/breakdown", json={"child_names": ["Spark", "Airflow"]})

        resp = client.get("/api/skills/breakdowns")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["breakdowns"]) == 1
        assert data["breakdowns"][0]["origin"]["name"] == "Data Engineering"


class TestPromoteCanonicalAPI:
    def test_promote_alias_to_canonical(self, client, sa_session):
        skill = _create_skill(sa_session, name="React")
        _create_alias(sa_session, skill.id, "ReactJS")

        resp = client.patch(f"/api/skills/{skill.id}/canonical", json={"alias_name": "ReactJS"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "ReactJS"
        assert "React" in data["aliases"]

    def test_promote_unknown_alias_returns_400(self, client, sa_session):
        skill = _create_skill(sa_session, name="React")
        resp = client.patch(f"/api/skills/{skill.id}/canonical", json={"alias_name": "NotAnAlias"})
        assert resp.status_code == 400

    def test_promote_missing_skill_returns_404(self, client):
        resp = client.patch("/api/skills/9999/canonical", json={"alias_name": "ReactJS"})
        assert resp.status_code == 404

    def test_promote_slug_collision_returns_409(self, client, sa_session):
        skill_a = _create_skill(sa_session, name="React")
        _create_skill(sa_session, name="ReactJS")
        _create_alias(sa_session, skill_a.id, "ReactJS")

        resp = client.patch(f"/api/skills/{skill_a.id}/canonical", json={"alias_name": "ReactJS"})
        assert resp.status_code == 409
