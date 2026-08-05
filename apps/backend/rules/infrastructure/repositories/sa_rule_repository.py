"""SQLAlchemy-based rule repository implementation."""

from typing import Any

from sqlalchemy.orm import Session

from rules.domain.repositories.rule_repository import IRuleRepository
from rules.infrastructure.models.rule_model import RuleModel


class SQLAlchemyRuleRepository(IRuleRepository):
    """SQLAlchemy implementation of rule repository."""

    def __init__(self, session: Session):
        self._session = session

    def _to_dict(self, m: RuleModel) -> dict[str, Any]:
        return {
            "id": m.id,
            "category": m.category,
            "rule_type": m.rule_type,
            "scope": m.scope,
            "key": m.key,
            "value": m.value,
            "description": m.description,
            "priority": m.priority,
            "enabled": m.enabled,
            "updated_at": m.updated_at,
        }

    def get_all(self) -> list[dict[str, Any]]:
        rows = self._session.query(RuleModel).order_by(RuleModel.priority.desc()).all()
        return [self._to_dict(r) for r in rows]

    def get_by_id(self, rule_id: int) -> dict[str, Any] | None:
        m = self._session.query(RuleModel).filter(RuleModel.id == rule_id).first()
        return self._to_dict(m) if m else None

    def get_enabled_by_scopes(self, scopes: list[str]) -> list[dict[str, Any]]:
        rows = self._session.query(RuleModel).filter(
            RuleModel.enabled == 1,
            RuleModel.scope.in_(scopes),
        ).order_by(RuleModel.priority.desc()).all()
        return [self._to_dict(r) for r in rows]

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        m = RuleModel(
            category=data.get("category", "fit"),
            rule_type=data.get("rule_type", "job"),
            scope=data.get("scope", "JOB"),
            key=data.get("key", ""),
            value=data.get("value", ""),
            description=data.get("description", ""),
            priority=data.get("priority", 50),
            enabled=data.get("enabled", 1),
        )
        self._session.add(m)
        self._session.commit()
        self._session.refresh(m)
        return self._to_dict(m)

    def update(self, rule_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        m = self._session.query(RuleModel).filter(RuleModel.id == rule_id).first()
        if not m:
            return None
        for field in ["value", "description", "priority", "enabled", "scope", "category", "key"]:
            if field in data:
                setattr(m, field, data[field])
        self._session.commit()
        self._session.refresh(m)
        return self._to_dict(m)

    def delete(self, rule_id: int) -> bool:
        m = self._session.query(RuleModel).filter(RuleModel.id == rule_id).first()
        if not m:
            return False
        self._session.delete(m)
        self._session.commit()
        return True

    def bulk_update(self, items: list[dict[str, Any]]) -> int:
        count = 0
        for item in items:
            if "id" not in item:
                continue
            m = self._session.query(RuleModel).filter(RuleModel.id == item["id"]).first()
            if not m:
                continue
            for field in ["value", "enabled", "priority", "scope"]:
                if field in item:
                    setattr(m, field, item[field])
            count += 1
        self._session.commit()
        return count
