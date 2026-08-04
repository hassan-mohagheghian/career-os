"""SQLAlchemy-based skill repository implementation."""

import json
from typing import Any

from sqlalchemy import cast, func
from sqlalchemy.orm import Session
from sqlalchemy.types import Numeric

from skills.domain.repositories.skill_repository import ISkillRepository
from skills.infrastructure.models.skill_model import SkillModel, SkillAliasModel, SkillRelationshipModel
from skills.infrastructure.mappers import skill_model_to_dict


class SQLAlchemySkillRepository(ISkillRepository):
    """SQLAlchemy implementation of skill repository."""

    def __init__(self, session: Session):
        self._session = session

    def _get_aliases(self, skill_id: int) -> list[str]:
        aliases = self._session.query(SkillAliasModel).filter(
            SkillAliasModel.skill_id == skill_id
        ).all()
        return [a.alias_name for a in aliases]

    def list_visible(self, category: str = "") -> list[dict[str, Any]]:
        query = self._session.query(SkillModel).filter(SkillModel.hidden == 0)
        if category:
            query = query.filter(SkillModel.category == category)
        query = query.order_by(SkillModel.level.desc().nulls_last())
        rows = query.all()
        result = []
        for row in rows:
            skill_dict = skill_model_to_dict(row, aliases=self._get_aliases(row.id))
            result.append(skill_dict)
        return result

    def list_hidden(self) -> list[dict[str, Any]]:
        rows = self._session.query(SkillModel).filter(
            SkillModel.hidden == 1
        ).order_by(SkillModel.name).all()
        return [skill_model_to_dict(r) for r in rows]

    def get_by_id(self, skill_id: int) -> dict[str, Any] | None:
        model = self._session.query(SkillModel).filter(SkillModel.id == skill_id).first()
        if not model:
            return None
        return skill_model_to_dict(model, aliases=self._get_aliases(model.id))

    def get_by_name(self, name: str) -> dict[str, Any] | None:
        model = self._session.query(SkillModel).filter(SkillModel.name == name).first()
        if not model:
            return None
        return skill_model_to_dict(model, aliases=self._get_aliases(model.id))

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        model = SkillModel(
            name=data["name"],
            level=data.get("level", 1),
            roles=data.get("roles", ""),
            path=data.get("path", ""),
            source=data.get("source", "user"),
            source_type=data.get("source_type", "user_input"),
            category=data.get("category", ""),
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self.get_by_id(model.id)

    def update(self, skill_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        model = self._session.query(SkillModel).filter(SkillModel.id == skill_id).first()
        if not model:
            return None

        for field in ["name", "level", "roles", "path", "source", "source_type", "category", "confidence", "market_relevance", "evidence"]:
            if field in data:
                setattr(model, field, data[field])

        if "tags" in data:
            model.tags = json.dumps(data["tags"]) if isinstance(data["tags"], list) else data["tags"]

        self._session.commit()
        self._session.refresh(model)
        return self.get_by_id(model.id)

    def delete(self, skill_id: int) -> bool:
        model = self._session.query(SkillModel).filter(SkillModel.id == skill_id).first()
        if not model:
            return False

        self._session.query(SkillAliasModel).filter(SkillAliasModel.skill_id == skill_id).delete()
        self._session.delete(model)
        self._session.commit()
        return True

    def set_hidden(self, skill_id: int, hidden: int) -> dict[str, Any] | None:
        model = self._session.query(SkillModel).filter(SkillModel.id == skill_id).first()
        if not model:
            return None
        model.hidden = hidden
        self._session.commit()
        self._session.refresh(model)
        return self.get_by_id(model.id)

    def rename(self, skill_id: int, new_name: str) -> dict[str, Any] | None:
        model = self._session.query(SkillModel).filter(SkillModel.id == skill_id).first()
        if not model:
            return None

        old_name = model.name
        if old_name == new_name:
            return self.get_by_id(skill_id)

        exists = self._session.query(SkillModel).filter(
            SkillModel.name == new_name, SkillModel.id != skill_id
        ).first()
        if exists:
            return None

        model.name = new_name

        # Update references in other tables
        from skills.infrastructure.models.skill_roadmap_models import SkillRoadmapModel, SkillRoadmapProgressModel, SkillRoadmapJobModel
        self._session.query(SkillRoadmapModel).filter(SkillRoadmapModel.skill_name == old_name).update({"skill_name": new_name})
        self._session.query(SkillRoadmapProgressModel).filter(SkillRoadmapProgressModel.skill_name == old_name).update({"skill_name": new_name})
        self._session.query(SkillRoadmapJobModel).filter(SkillRoadmapJobModel.skill_name == old_name).update({"skill_name": new_name})
        self._session.query(SkillAliasModel).filter(
            SkillAliasModel.alias_name == old_name, SkillAliasModel.skill_id == skill_id
        ).update({"alias_name": new_name})

        self._session.commit()
        self._session.refresh(model)
        return self.get_by_id(model.id)

    def merge(self, target_id: int, source_ids: list[int]) -> dict[str, Any]:
        target = self._session.query(SkillModel).filter(SkillModel.id == target_id).first()
        if not target:
            return {"error": "Target skill not found"}

        target_name = target.name
        merged = []

        from skills.infrastructure.models.skill_roadmap_models import SkillRoadmapModel, SkillRoadmapProgressModel, SkillRoadmapJobModel

        for sid in source_ids:
            source = self._session.query(SkillModel).filter(SkillModel.id == sid).first()
            if not source or source.name == target_name:
                continue

            source_name = source.name

            # Update references
            self._session.query(SkillRoadmapModel).filter(SkillRoadmapModel.skill_name == source_name).update({"skill_name": target_name})
            self._session.query(SkillRoadmapProgressModel).filter(SkillRoadmapProgressModel.skill_name == source_name).update({"skill_name": target_name})
            self._session.query(SkillRoadmapJobModel).filter(SkillRoadmapJobModel.skill_name == source_name).update({"skill_name": target_name})

            # Create alias if not exists
            existing = self._session.query(SkillAliasModel).filter(
                SkillAliasModel.skill_id == target_id, SkillAliasModel.alias_name == source_name
            ).first()
            if not existing:
                self._session.add(SkillAliasModel(
                    skill_id=target_id,
                    alias_name=source_name,
                    normalized_name=source_name.lower(),
                ))

            source.hidden = 1
            merged.append(source_name)

        self._session.commit()

        # Return merged result
        aliases = self._get_aliases(target_id)
        return {
            "status": "merged",
            "target": self.get_by_id(target_id),
            "merged": merged,
            "aliases": aliases,
        }

    def get_categories(self) -> list[dict[str, Any]]:
        rows = self._session.query(
            SkillModel.category,
            func.count(SkillModel.id).label("count"),
            func.round(cast(func.avg(SkillModel.market_relevance), Numeric), 1).label("avg_demand"),
            func.round(cast(func.avg(SkillModel.level), Numeric), 1).label("avg_level"),
        ).filter(
            SkillModel.hidden == 0, SkillModel.category != ""
        ).group_by(SkillModel.category).order_by(func.count(SkillModel.id).desc()).all()

        return [{"category": r[0], "count": r[1], "avg_demand": r[2], "avg_level": r[3]} for r in rows]

    def get_stats(self) -> dict[str, Any]:
        total = self._session.query(func.count(SkillModel.id)).filter(SkillModel.hidden == 0).scalar()
        hidden = self._session.query(func.count(SkillModel.id)).filter(SkillModel.hidden == 1).scalar()

        by_source_rows = self._session.query(
            SkillModel.source, func.count(SkillModel.id)
        ).filter(SkillModel.hidden == 0).group_by(SkillModel.source).all()
        by_source = {r[0]: r[1] for r in by_source_rows}

        avg_level = self._session.query(func.round(cast(func.avg(SkillModel.level), Numeric), 1)).filter(SkillModel.hidden == 0).scalar()
        avg_demand = self._session.query(func.round(cast(func.avg(SkillModel.market_relevance), Numeric), 1)).filter(
            SkillModel.hidden == 0, SkillModel.market_relevance > 0
        ).scalar()
        total_relationships = self._session.query(func.count(SkillRelationshipModel.id)).scalar()
        total_aliases = self._session.query(func.count(SkillAliasModel.id)).scalar()
        total_roadmaps = self._session.query(func.count(func.distinct(SkillModel.name))).scalar()

        return {
            "total": total or 0,
            "hidden": hidden or 0,
            "avg_level": avg_level or 0,
            "avg_demand": avg_demand or 0,
            "by_source": by_source,
            "total_relationships": total_relationships or 0,
            "total_aliases": total_aliases or 0,
            "total_roadmaps": total_roadmaps or 0,
        }

    def bulk_hide(self, skill_ids: list[int]) -> int:
        self._session.query(SkillModel).filter(SkillModel.id.in_(skill_ids)).update({"hidden": 1}, synchronize_session=False)
        self._session.commit()
        return len(skill_ids)

    def bulk_categorize(self, skill_ids: list[int], category: str) -> int:
        self._session.query(SkillModel).filter(SkillModel.id.in_(skill_ids)).update({"category": category}, synchronize_session=False)
        self._session.commit()
        return len(skill_ids)

    def get_relationships(self, skill_name: str) -> list[dict[str, Any]]:
        rows = self._session.query(SkillRelationshipModel).filter(
            (SkillRelationshipModel.skill_name == skill_name) | (SkillRelationshipModel.related_name == skill_name)
        ).all()
        return [
            {"id": r.id, "skill_name": r.skill_name, "related_name": r.related_name, "relation_type": r.relation_type, "confidence": r.confidence}
            for r in rows
        ]

    def create_relationship(self, data: dict[str, Any]) -> bool:
        try:
            rel = SkillRelationshipModel(
                skill_name=data["skill_name"],
                related_name=data["related_name"],
                relation_type=data["relation_type"],
                confidence=data.get("confidence", 0),
            )
            self._session.add(rel)
            self._session.commit()
            return True
        except Exception:
            self._session.rollback()
            return False

    def delete_relationship(self, rel_id: int) -> bool:
        self._session.query(SkillRelationshipModel).filter(SkillRelationshipModel.id == rel_id).delete()
        self._session.commit()
        return True

    # ── Extended methods for services ───────────────────────────────

    def get_all(self) -> list[dict[str, Any]]:
        rows = self._session.query(SkillModel).all()
        return [skill_model_to_dict(r) for r in rows]

    def get_level_by_name(self, name: str) -> int | None:
        m = self._session.query(SkillModel.level).filter(SkillModel.name == name).first()
        return m[0] if m else None

    def update_fields_by_name(self, name: str, **fields) -> bool:
        m = self._session.query(SkillModel).filter(SkillModel.name == name).first()
        if not m:
            return False
        for k, v in fields.items():
            if hasattr(m, k):
                setattr(m, k, v)
        self._session.commit()
        return True

    def create_from_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        m = SkillModel(
            name=data.get("name", ""),
            level=data.get("level", 1),
            roles=data.get("roles", ""),
            path=data.get("path", ""),
            source=data.get("source", "service"),
            source_type=data.get("source_type", "ai_generated"),
            category=data.get("category", ""),
            confidence=data.get("confidence", 0),
            market_relevance=data.get("market_relevance", 0),
            evidence=data.get("evidence", "[]"),
            tags=data.get("tags", "[]"),
        )
        self._session.add(m)
        self._session.commit()
        self._session.refresh(m)
        return skill_model_to_dict(m)
