"""SQLAlchemy-based skill repository implementation."""

import json
from collections import Counter
from typing import Any

from sqlalchemy import cast, func
from sqlalchemy.orm import Session
from sqlalchemy.types import Numeric

from skills.domain.repositories.skill_repository import ISkillRepository
from skills.domain.slug_utils import slugify
from skills.infrastructure.models.skill_model import (
    SkillModel,
    SkillAliasModel,
    SkillRelationshipModel,
    SkillMentionModel,
    SkillCategoryModel,
    SkillCategoryLinkModel,
    SkillBreakdownModel,
)
from skills.infrastructure.mappers import skill_model_to_dict


class SQLAlchemySkillRepository(ISkillRepository):
    """SQLAlchemy implementation of skill repository."""

    def __init__(self, session: Session, user_id: str = ""):
        self._session = session
        self._user_id = user_id

    def _get_aliases(self, skill_id: int) -> list[str]:
        aliases = self._session.query(SkillAliasModel).filter(
            SkillAliasModel.skill_id == skill_id
        ).all()
        return [a.alias_name for a in aliases]

    # ── Categories ────────────────────────────────────────────────

    @staticmethod
    def _normalize_categories(categories: list[str] | None) -> list[str]:
        """Trim, drop empties and dedupe preserving order."""
        seen: list[str] = []
        for name in categories or []:
            name = (name or "").strip()
            if name and name not in seen:
                seen.append(name)
        return seen

    def _ensure_category(self, name: str) -> int:
        """Return the category id for ``name``, resolving by canonical slug.

        Existing categories are matched by exact name first, then by slug, so
        "Data Engineering" and "data engineering" resolve to one category.
        A missing category is created with the slugified canonical name.
        """
        cleaned = (name or "").strip()
        if not cleaned:
            raise ValueError("Category name is required")
        cat = self._session.query(SkillCategoryModel).filter(
            SkillCategoryModel.name == cleaned
        ).first()
        if cat:
            return cat.id
        slug = slugify(cleaned)
        if slug:
            cat = self._session.query(SkillCategoryModel).filter(
                SkillCategoryModel.slug == slug
            ).first()
            if cat:
                return cat.id
        cat = SkillCategoryModel(name=cleaned, slug=slug or f"category-{id(cleaned)}")
        self._session.add(cat)
        self._session.flush()
        return cat.id

    def _set_category_links(self, skill_id: int, names: list[str]) -> None:
        """Replace a skill's category links with ``names`` (catalog rows auto-created)."""
        self._session.query(SkillCategoryLinkModel).filter(
            SkillCategoryLinkModel.skill_id == skill_id
        ).delete()
        for name in names:
            self._session.add(SkillCategoryLinkModel(
                skill_id=skill_id,
                category_id=self._ensure_category(name),
            ))

    def _own_category_names(self, skill_ids: list[int]) -> dict[int, list[str]]:
        """skill_id -> own linked category names (no inheritance)."""
        if not skill_ids:
            return {}
        rows = self._session.query(
            SkillCategoryLinkModel.skill_id, SkillCategoryModel.name
        ).join(
            SkillCategoryModel,
            SkillCategoryModel.id == SkillCategoryLinkModel.category_id,
        ).filter(SkillCategoryLinkModel.skill_id.in_(skill_ids)).all()
        result: dict[int, list[str]] = {}
        for skill_id, name in rows:
            result.setdefault(skill_id, []).append(name)
        return result

    def _effective_categories(self, models: list[SkillModel]) -> dict[int, list[str]]:
        """skill_id -> effective category names for a batch of skill models.

        Effective categories = the skill's own linked categories (with the
        primary ``category`` column as a backward-compatible fallback) plus the
        canonical skill's categories when the row's name is registered as an
        alias of that canonical skill (one level, mirroring the alias mention
        folding in ``get_mention_counts``).
        """
        if not models:
            return {}
        ids = [m.id for m in models]
        names = {m.id: m.name for m in models}

        own = self._own_category_names(ids)
        for m in models:
            cats = own.setdefault(m.id, [])
            if m.category and m.category not in cats:
                cats.append(m.category)

        alias_rows = self._session.query(
            SkillAliasModel.alias_name, SkillAliasModel.skill_id
        ).filter(SkillAliasModel.alias_name.in_(list(names.values()))).all()
        if not alias_rows:
            return own

        canonical_ids = {skill_id for _, skill_id in alias_rows}
        canonical_own = self._own_category_names(list(canonical_ids))
        alias_to_canonical = dict(alias_rows)

        result: dict[int, list[str]] = {}
        for m in models:
            cats = list(own.get(m.id, []))
            canonical_id = alias_to_canonical.get(m.name)
            if canonical_id is not None:
                for name in canonical_own.get(canonical_id, []):
                    if name not in cats:
                        cats.append(name)
            result[m.id] = cats
        return result

    def _to_dict(self, model: SkillModel, categories: list[str]) -> dict[str, Any]:
        """Build a skill dict with effective categories; primary falls back to the first."""
        result = skill_model_to_dict(
            model,
            aliases=self._get_aliases(model.id),
            categories=categories,
        )
        if not result["category"] and categories:
            result["category"] = categories[0]
        return result

    def get_categories(self) -> list[dict[str, Any]]:
        """Return the category catalog (plus legacy primary-only categories) with counts."""
        cats = self._session.query(SkillCategoryModel).order_by(
            SkillCategoryModel.name
        ).all()
        known_names = {c.name for c in cats}

        visible = self._session.query(SkillModel).filter(
            SkillModel.hidden == 0
        ).all()
        eff = self._effective_categories(visible)

        # Backward compatibility: any primary category value that predates the
        # catalog (no catalog row / no link) is still reported.
        for skill in visible:
            if skill.category:
                known_names.add(skill.category)

        counts: Counter = Counter()
        sum_demand: Counter = Counter()
        sum_level: Counter = Counter()
        for skill in visible:
            for name in eff.get(skill.id, []):
                counts[name] += 1
                sum_demand[name] += skill.market_relevance or 0
                sum_level[name] += skill.level or 0

        result = []
        for name in known_names:
            result.append({
                "category": name,
                "count": counts.get(name, 0),
                "avg_demand": round(sum_demand[name] / counts[name], 1) if counts[name] else None,
                "avg_level": round(sum_level[name] / counts[name], 1) if counts[name] else None,
            })
        result.sort(key=lambda c: (-c["count"], c["category"]))
        return result

    def create_category(self, name: str) -> dict[str, Any] | None:
        """Add a category to the catalog. Returns None for blank names."""
        name = (name or "").strip()
        if not name:
            return None
        existing = self._session.query(SkillCategoryModel).filter(
            SkillCategoryModel.name == name
        ).first()
        if existing:
            return {"id": existing.id, "name": existing.name, "created": False}
        slug = slugify(name)
        if slug:
            existing = self._session.query(SkillCategoryModel).filter(
                SkillCategoryModel.slug == slug
            ).first()
            if existing:
                return {"id": existing.id, "name": existing.name, "created": False}
        cat = SkillCategoryModel(name=name, slug=slug or f"category-{id(name)}")
        self._session.add(cat)
        self._session.commit()
        self._session.refresh(cat)
        return {"id": cat.id, "name": cat.name, "created": True}

    def delete_category(self, name: str) -> dict[str, Any]:
        """Remove an unused category. Result status: deleted / in_use / not_found."""
        cat = self._session.query(SkillCategoryModel).filter(
            SkillCategoryModel.name == name
        ).first()
        if not cat:
            return {"status": "not_found"}
        count = self._session.query(func.count(SkillCategoryLinkModel.id)).filter(
            SkillCategoryLinkModel.category_id == cat.id
        ).scalar()
        if count:
            return {"status": "in_use", "count": count}
        self._session.delete(cat)
        self._session.commit()
        return {"status": "deleted"}

    def set_categories(self, skill_id: int, categories: list[str]) -> dict[str, Any] | None:
        """Replace a skill's categories and keep the primary column in sync."""
        model = self._session.query(SkillModel).filter(SkillModel.id == skill_id).first()
        if not model:
            return None
        names = self._normalize_categories(categories)
        self._set_category_links(model.id, names)
        model.category = names[0] if names else ""
        self._session.commit()
        self._session.refresh(model)
        return self.get_by_id(model.id)

    def list_visible(self, category: str = "") -> list[dict[str, Any]]:
        query = self._session.query(SkillModel).filter(SkillModel.hidden == 0)
        if self._user_id:
            query = query.filter(SkillModel.user_id == self._user_id)
        query = query.order_by(SkillModel.level.desc().nulls_last())
        rows = query.all()
        eff = self._effective_categories(rows)
        result = []
        for row in rows:
            categories = eff.get(row.id, [])
            if category and category not in categories:
                continue
            result.append(self._to_dict(row, categories))
        return result

    def list_hidden(self) -> list[dict[str, Any]]:
        q = self._session.query(SkillModel).filter(
            SkillModel.hidden == 1
        )
        if self._user_id:
            q = q.filter(SkillModel.user_id == self._user_id)
        rows = q.order_by(SkillModel.name).all()
        eff = self._effective_categories(rows)
        return [self._to_dict(r, eff.get(r.id, [])) for r in rows]

    def get_by_id(self, skill_id: int) -> dict[str, Any] | None:
        q = self._session.query(SkillModel).filter(SkillModel.id == skill_id)
        if self._user_id:
            q = q.filter(SkillModel.user_id == self._user_id)
        model = q.first()
        if not model:
            return None
        categories = self._effective_categories([model]).get(model.id, [])
        return self._to_dict(model, categories)

    def get_by_name(self, name: str) -> dict[str, Any] | None:
        q = self._session.query(SkillModel).filter(SkillModel.name == name)
        if self._user_id:
            q = q.filter(SkillModel.user_id == self._user_id)
        model = q.first()
        if not model:
            return None
        categories = self._effective_categories([model]).get(model.id, [])
        return self._to_dict(model, categories)

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        categories = self._normalize_categories(
            data.get("categories") if "categories" in data else (
                [data["category"]] if data.get("category") else []
            )
        )
        model = SkillModel(
            name=data["name"],
            slug=slugify(data["name"]) or f"skill-{id(data)}",
            level=data.get("level", 1),
            roles=data.get("roles", ""),
            path=data.get("path", ""),
            source=data.get("source", "user"),
            source_type=data.get("source_type", "user_input"),
            category=categories[0] if categories else (data.get("category") or ""),
            user_id=self._user_id,
        )
        self._session.add(model)
        self._session.flush()
        if categories:
            self._set_category_links(model.id, categories)
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

        if "name" in data:
            model.slug = slugify(model.name) or f"skill-{model.id}"

        if "tags" in data:
            model.tags = json.dumps(data["tags"]) if isinstance(data["tags"], list) else data["tags"]

        if "categories" in data:
            names = self._normalize_categories(data["categories"])
            self._set_category_links(model.id, names)
            model.category = names[0] if names else ""
        elif "category" in data:
            # Legacy single-category update: keep the link table in sync.
            names = self._normalize_categories([data["category"]]) if data["category"] else []
            self._set_category_links(model.id, names)

        self._session.commit()
        self._session.refresh(model)
        return self.get_by_id(model.id)

    def delete(self, skill_id: int) -> bool:
        model = self._session.query(SkillModel).filter(SkillModel.id == skill_id).first()
        if not model:
            return False

        self._session.query(SkillAliasModel).filter(SkillAliasModel.skill_id == skill_id).delete()
        self._session.query(SkillMentionModel).filter(SkillMentionModel.skill_id == skill_id).delete()
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

    def set_pinned(self, skill_id: int, pinned: bool) -> dict[str, Any] | None:
        model = self._session.query(SkillModel).filter(SkillModel.id == skill_id).first()
        if not model:
            return None
        model.pinned = 1 if pinned else 0
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
        new_slug = slugify(new_name)
        slug_collision = None
        if new_slug:
            slug_collision = self._session.query(SkillModel).filter(
                SkillModel.slug == new_slug, SkillModel.id != skill_id
            ).first()
        if exists or slug_collision:
            return None

        model.name = new_name
        model.slug = new_slug or f"skill-{skill_id}"

        # Update references in other tables
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

        for sid in source_ids:
            source = self._session.query(SkillModel).filter(SkillModel.id == sid).first()
            if not source or source.name == target_name:
                continue

            source_name = source.name

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

            # Fold mention links onto the target skill
            self._fold_mentions(target_id, sid)

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

    def _fold_mentions(self, target_id: int, source_id: int) -> None:
        """Re-point source skill mention rows to the target skill. When a mention
        already exists for the same (source_type, source_id) on the target, skip
        the duplicate so the unique constraint is respected."""
        existing_keys = set()
        for row in self._session.query(
            SkillMentionModel.source_type, SkillMentionModel.source_id
        ).filter(SkillMentionModel.skill_id == target_id).all():
            existing_keys.add((row[0], row[1]))

        for row in self._session.query(SkillMentionModel).filter(
            SkillMentionModel.skill_id == source_id
        ).all():
            key = (row.source_type, row.source_id)
            if key in existing_keys:
                self._session.delete(row)
                continue
            row.skill_id = target_id
            existing_keys.add(key)

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

        return {
            "total": total or 0,
            "hidden": hidden or 0,
            "avg_level": avg_level or 0,
            "avg_demand": avg_demand or 0,
            "by_source": by_source,
            "total_relationships": total_relationships or 0,
            "total_aliases": total_aliases or 0,
        }

    def bulk_hide(self, skill_ids: list[int]) -> int:
        self._session.query(SkillModel).filter(SkillModel.id.in_(skill_ids)).update({"hidden": 1}, synchronize_session=False)
        self._session.commit()
        return len(skill_ids)

    def bulk_categorize(self, skill_ids: list[int], category: str) -> int:
        name = (category or "").strip()
        if not name:
            return 0
        for sid in skill_ids:
            model = self._session.query(SkillModel).filter(SkillModel.id == sid).first()
            if not model:
                continue
            self._set_category_links(model.id, [name])
            model.category = name
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

    # ── Skill mentions (job/company demand links) ───────────────────

    def resolve_skill(self, data: dict[str, Any]) -> int:
        """Resolve a skill row by exact name, then alias, then canonical slug.
        Creates the row (source_type="ai_generated") when neither matches."""
        name = (data.get("name") or "").strip()
        if not name:
            raise ValueError("Skill name is required")

        existing_q = self._session.query(SkillModel).filter(SkillModel.name == name)
        if self._user_id:
            existing_q = existing_q.filter(SkillModel.user_id == self._user_id)
        existing = existing_q.first()
        if not existing:
            existing = self._session.query(SkillModel).join(
                SkillAliasModel, SkillAliasModel.skill_id == SkillModel.id
            ).filter(SkillAliasModel.alias_name == name)
            if self._user_id:
                existing = existing.filter(SkillModel.user_id == self._user_id)
            existing = existing.first()
        if not existing:
            slug = slugify(name)
            if slug:
                existing = self._session.query(SkillModel).filter(
                    SkillModel.slug == slug
                )
                if self._user_id:
                    existing = existing.filter(SkillModel.user_id == self._user_id)
                existing = existing.first()
        if not existing:
            slug = slugify(name)
            if slug:
                existing = self._session.query(SkillModel).join(
                    SkillAliasModel, SkillAliasModel.skill_id == SkillModel.id
                ).filter(SkillAliasModel.normalized_name == slug)
                if self._user_id:
                    existing = existing.filter(SkillModel.user_id == self._user_id)
                existing = existing.first()

        if existing:
            return existing.id

        slug = slugify(name)
        m = SkillModel(
            name=name,
            slug=slug or f"skill-{id(data)}",
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
            user_id=self._user_id,
        )
        self._session.add(m)
        self._session.flush()
        categories = self._normalize_categories(data.get("categories"))
        if categories:
            self._set_category_links(m.id, categories)
            m.category = categories[0]
        self._session.commit()
        self._session.refresh(m)
        return m.id

    def upsert_mentions(self, skill_id: int, source_type: str, source_id: str, status: str = "", evidence: str = "[]") -> None:
        """Upsert a skill mention link for a job/company source."""
        existing = self._session.query(SkillMentionModel).filter(
            SkillMentionModel.skill_id == skill_id,
            SkillMentionModel.source_type == source_type,
            SkillMentionModel.source_id == source_id,
        ).first()
        if existing:
            existing.status = status or existing.status
            existing.evidence = evidence or existing.evidence
        else:
            self._session.add(SkillMentionModel(
                skill_id=skill_id,
                source_type=source_type,
                source_id=source_id,
                status=status,
                evidence=evidence,
            ))
        self._session.commit()

    def delete_mentions_for_source(self, source_type: str, source_id: str) -> None:
        """Delete all mention links for a job/company source."""
        self._session.query(SkillMentionModel).filter(
            SkillMentionModel.source_type == source_type,
            SkillMentionModel.source_id == source_id,
        ).delete()
        self._session.commit()

    def get_job_mention_ids(self, skill_id: int) -> list[str]:
        """Return the distinct job ids that mention the given skill."""
        rows = self._session.query(SkillMentionModel.source_id).filter(
            SkillMentionModel.skill_id == skill_id,
            SkillMentionModel.source_type == "job",
        ).all()
        seen: list[str] = []
        for (source_id,) in rows:
            if source_id and source_id not in seen:
                seen.append(source_id)
        return seen

    def get_mention_counts(self, skill_ids: list[int]) -> dict[int, int]:
        """Return {skill_id: total mention count} for the given skill ids.

        A skill's count is the sum of its own mentions plus the mentions
        recorded under any separate skill row whose name matches one of the
        skill's aliases (e.g. an ai_generated "K8s" row folds into
        "Kubernetes" once "K8s" is registered as an alias)."""
        if not skill_ids:
            return {}

        counts = {
            r[0]: r[1]
            for r in self._session.query(
                SkillMentionModel.skill_id, func.count(SkillMentionModel.id)
            ).filter(SkillMentionModel.skill_id.in_(skill_ids))
            .group_by(SkillMentionModel.skill_id).all()
        }

        alias_rows = self._session.query(
            SkillAliasModel.skill_id, SkillAliasModel.alias_name
        ).filter(SkillAliasModel.skill_id.in_(skill_ids)).all()
        if not alias_rows:
            return counts

        alias_names = {name for _, name in alias_rows}
        name_to_id = {
            name: sid
            for sid, name in self._session.query(
                SkillModel.id, SkillModel.name
            ).filter(SkillModel.name.in_(alias_names)).all()
        }
        extra_ids = {
            name_to_id[name]
            for sid, name in alias_rows
            if name in name_to_id and name_to_id[name] != sid
        }
        if not extra_ids:
            return counts

        extra_counts = dict(
            self._session.query(
                SkillMentionModel.skill_id, func.count(SkillMentionModel.id)
            ).filter(SkillMentionModel.skill_id.in_(extra_ids))
            .group_by(SkillMentionModel.skill_id).all()
        )
        for sid, name in alias_rows:
            alias_id = name_to_id.get(name)
            if alias_id is not None and alias_id != sid:
                counts[sid] = counts.get(sid, 0) + extra_counts.get(alias_id, 0)
        return counts

    def add_alias(self, skill_id: int, alias_name: str) -> dict[str, Any] | None:
        """Add an alias to a skill. Returns the updated skill or None."""
        alias = alias_name.strip()
        if not alias:
            return None
        model = self._session.query(SkillModel).filter(SkillModel.id == skill_id).first()
        if not model:
            return None

        exists = self._session.query(SkillAliasModel).filter(
            SkillAliasModel.skill_id == skill_id,
            SkillAliasModel.alias_name == alias,
        ).first()
        if not exists:
            self._session.add(SkillAliasModel(
                skill_id=skill_id,
                alias_name=alias,
                normalized_name=alias.lower(),
            ))
            self._session.commit()
        return self.get_by_id(skill_id)

    def remove_alias(self, skill_id: int, alias_name: str) -> dict[str, Any] | None:
        """Remove an alias from a skill. Returns the updated skill or None."""
        model = self._session.query(SkillModel).filter(SkillModel.id == skill_id).first()
        if not model:
            return None
        self._session.query(SkillAliasModel).filter(
            SkillAliasModel.skill_id == skill_id,
            SkillAliasModel.alias_name == alias_name,
        ).delete()
        self._session.commit()
        return self.get_by_id(skill_id)

    # ── Break-down ──────────────────────────────────────────────────

    def break_down(self, origin_id: int, child_names: list[str]) -> dict[str, Any]:
        """Break a composite skill into atomic children.

        Children are resolved by name/alias/canonical slug and created only
        when missing. The origin's job mentions are duplicated onto every
        child (deduped) and the origin is soft-hidden. The origin→children
        links are stored in ``skill.skill_breakdowns`` and feed extraction.
        """
        origin = self._session.query(SkillModel).filter(SkillModel.id == origin_id).first()
        if not origin:
            return {"error": "Origin skill not found"}
        if origin.hidden == 1:
            return {"error": "Origin skill is hidden"}

        # Normalize child names: trim, dedupe, drop empties and self.
        seen: list[str] = []
        for name in child_names or []:
            cleaned = (name or "").strip()
            if not cleaned or cleaned.lower() == origin.name.lower():
                continue
            if cleaned not in seen:
                seen.append(cleaned)
        if len(seen) < 2:
            return {"error": "Provide at least two distinct child skill names"}

        children: list[dict[str, Any]] = []
        for name in seen:
            child_id = self.resolve_skill({
                "name": name,
                "category": origin.category,
                "source_type": "ai_generated",
            })
            child = self.get_by_id(child_id)
            if child:
                children.append({"id": child_id, "name": child["name"]})

        # Record the origin→children map (idempotent).
        for child in children:
            existing = self._session.query(SkillBreakdownModel).filter(
                SkillBreakdownModel.origin_skill_id == origin_id,
                SkillBreakdownModel.child_skill_id == child["id"],
            ).first()
            if not existing:
                self._session.add(SkillBreakdownModel(
                    origin_skill_id=origin_id,
                    child_skill_id=child["id"],
                ))

        # Duplicate the origin's mentions onto every child (skip existing keys).
        for child in children:
            self._duplicate_mentions(origin_id, child["id"])

        origin.hidden = 1
        self._session.commit()
        self._session.refresh(origin)

        return {
            "status": "broken_down",
            "origin": self.get_by_id(origin_id),
            "children": children,
            "hidden": True,
        }

    def _duplicate_mentions(self, source_skill_id: int, target_skill_id: int) -> None:
        """Copy all mention rows from one skill onto another, deduping by
        (skill_id, source_type, source_id) so the unique constraint holds."""
        existing_keys = {
            (row[0], row[1])
            for row in self._session.query(
                SkillMentionModel.source_type, SkillMentionModel.source_id
            ).filter(SkillMentionModel.skill_id == target_skill_id).all()
        }
        for row in self._session.query(SkillMentionModel).filter(
            SkillMentionModel.skill_id == source_skill_id
        ).all():
            key = (row.source_type, row.source_id)
            if key in existing_keys:
                continue
            self._session.add(SkillMentionModel(
                skill_id=target_skill_id,
                source_type=row.source_type,
                source_id=row.source_id,
                status=row.status,
                evidence=row.evidence,
            ))
            existing_keys.add(key)

    def get_breakdown_map(self) -> list[dict[str, Any]]:
        """Return the origin→children decomposition map for extraction."""
        rows = self._session.query(SkillBreakdownModel).order_by(
            SkillBreakdownModel.origin_skill_id, SkillBreakdownModel.child_skill_id
        ).all()
        by_origin: dict[int, list[int]] = {}
        for row in rows:
            by_origin.setdefault(row.origin_skill_id, []).append(row.child_skill_id)

        result: list[dict[str, Any]] = []
        origin_ids = list(by_origin.keys())
        if not origin_ids:
            return result
        origins = {
            m.id: m
            for m in self._session.query(SkillModel).filter(SkillModel.id.in_(origin_ids)).all()
        }
        child_ids = sorted({cid for ids in by_origin.values() for cid in ids})
        children = {
            m.id: m
            for m in self._session.query(SkillModel).filter(SkillModel.id.in_(child_ids)).all()
        }
        for oid in origin_ids:
            origin = origins.get(oid)
            if not origin:
                continue
            result.append({
                "origin": {"id": origin.id, "name": origin.name},
                "children": [
                    {"id": children[cid].id, "name": children[cid].name}
                    for cid in by_origin[oid] if cid in children
                ],
            })
        return result

    def list_breakdowns(self, skill_id: int) -> dict[str, Any]:
        """Children (and origin) for a skill, used by the skill drawer."""
        child_rows = self._session.query(
            SkillBreakdownModel, SkillModel
        ).join(
            SkillModel, SkillModel.id == SkillBreakdownModel.child_skill_id
        ).filter(SkillBreakdownModel.origin_skill_id == skill_id).order_by(
            SkillModel.name
        ).all()
        children = [{"id": m.id, "name": m.name} for _, m in child_rows]

        origin_row = self._session.query(
            SkillBreakdownModel, SkillModel
        ).join(
            SkillModel, SkillModel.id == SkillBreakdownModel.origin_skill_id
        ).filter(SkillBreakdownModel.child_skill_id == skill_id).first()
        origin = {"id": origin_row[1].id, "name": origin_row[1].name} if origin_row else None

        return {"children": children, "origin": origin}

    # ── Promote alias to canonical ──────────────────────────────────

    def promote_alias_to_canonical(self, skill_id: int, alias_name: str) -> dict[str, Any] | None:
        """Make an existing alias the canonical name; the old canonical becomes
        an alias. Returns None when the skill or alias is missing or the
        alias's slug collides with another skill's canonical slug."""
        model = self._session.query(SkillModel).filter(SkillModel.id == skill_id).first()
        if not model:
            return None
        alias = (alias_name or "").strip()
        if not alias:
            return None

        alias_row = self._session.query(SkillAliasModel).filter(
            SkillAliasModel.skill_id == skill_id,
            SkillAliasModel.alias_name == alias,
        ).first()
        if not alias_row:
            return None

        new_slug = slugify(alias)
        if new_slug:
            collision = self._session.query(SkillModel).filter(
                SkillModel.slug == new_slug, SkillModel.id != skill_id
            ).first()
            if collision:
                return None

        old_name = model.name
        self._session.delete(alias_row)
        model.name = alias
        model.slug = new_slug or f"skill-{skill_id}"

        # Old canonical becomes an alias (only if it isn't already one).
        if not self._session.query(SkillAliasModel).filter(
            SkillAliasModel.skill_id == skill_id,
            SkillAliasModel.alias_name == old_name,
        ).first():
            self._session.add(SkillAliasModel(
                skill_id=skill_id,
                alias_name=old_name,
                normalized_name=old_name.lower(),
            ))

        self._session.commit()
        self._session.refresh(model)
        return self.get_by_id(skill_id)

    # ── Normalize all (one-time cleanup) ────────────────────────────

    def normalize_all(self) -> dict[str, Any]:
        """Recompute slugs and merge collisions across all skills/categories.

        Idempotent cleanup pass: each skill/category gets its canonical slug,
        slug collisions are merged (mentions/category links re-pointed, the
        duplicate name aliased and hidden). Returns a summary dict.
        """
        stats = {
            "skills_processed": 0,
            "skills_hidden": 0,
            "categories_processed": 0,
            "categories_removed": 0,
        }

        # Skills: free every slug first so recomputation cannot collide
        # (two pre-existing rows may already share the same target slug).
        skills = self._session.query(SkillModel).order_by(SkillModel.id).all()
        for m in skills:
            m.slug = f"skill-norm-{m.id}"
        self._session.flush()

        groups: dict[str, list[SkillModel]] = {}
        for m in skills:
            slug = slugify(m.name) or f"skill-{m.id}"
            groups.setdefault(slug, []).append(m)
        for slug, members in groups.items():
            if len(members) == 1:
                members[0].slug = slug
                stats["skills_processed"] += 1
                continue
            canonical = members[0]
            canonical.slug = slug
            for dup in members[1:]:
                self._duplicate_mentions(dup.id, canonical.id)
                self._session.query(SkillMentionModel).filter(
                    SkillMentionModel.skill_id == dup.id
                ).delete()
                if not self._session.query(SkillAliasModel).filter(
                    SkillAliasModel.skill_id == canonical.id,
                    SkillAliasModel.alias_name == dup.name,
                ).first():
                    self._session.add(SkillAliasModel(
                        skill_id=canonical.id,
                        alias_name=dup.name,
                        normalized_name=slugify(dup.name),
                    ))
                dup.hidden = 1
                dup.slug = f"{slug}-{dup.id}"
                stats["skills_hidden"] += 1
            stats["skills_processed"] += 1
        self._session.flush()

        # Categories: free slugs, merge collisions, drop the duplicates.
        cats = self._session.query(SkillCategoryModel).order_by(SkillCategoryModel.id).all()
        for c in cats:
            c.slug = f"category-norm-{c.id}"
        self._session.flush()

        cat_groups: dict[str, list[SkillCategoryModel]] = {}
        for c in cats:
            cat_groups.setdefault(slugify(c.name) or f"category-{c.id}", []).append(c)
        for slug, members in cat_groups.items():
            if len(members) == 1:
                members[0].slug = slug
                stats["categories_processed"] += 1
                continue
            canonical = members[0]
            canonical.slug = slug
            for dup in members[1:]:
                for link in self._session.query(SkillCategoryLinkModel).filter(
                    SkillCategoryLinkModel.category_id == dup.id
                ).all():
                    if not self._session.query(SkillCategoryLinkModel).filter(
                        SkillCategoryLinkModel.skill_id == link.skill_id,
                        SkillCategoryLinkModel.category_id == canonical.id,
                    ).first():
                        self._session.add(SkillCategoryLinkModel(
                            skill_id=link.skill_id,
                            category_id=canonical.id,
                        ))
                    self._session.delete(link)
                self._session.query(SkillModel).filter(
                    SkillModel.category == dup.name
                ).update({"category": canonical.name}, synchronize_session=False)
                self._session.delete(dup)
                stats["categories_removed"] += 1
            stats["categories_processed"] += 1

        self._session.commit()
        return stats

    # ── Extended methods for services ───────────────────────────────

    def get_all(self) -> list[dict[str, Any]]:
        q = self._session.query(SkillModel)
        if self._user_id:
            q = q.filter(SkillModel.user_id == self._user_id)
        rows = q.all()
        return [skill_model_to_dict(r) for r in rows]

    def get_level_by_name(self, name: str) -> int | None:
        q = self._session.query(SkillModel.level).filter(SkillModel.name == name)
        if self._user_id:
            q = q.filter(SkillModel.user_id == self._user_id)
        m = q.first()
        return m[0] if m else None

    def update_fields_by_name(self, name: str, **fields) -> bool:
        q = self._session.query(SkillModel).filter(SkillModel.name == name)
        if self._user_id:
            q = q.filter(SkillModel.user_id == self._user_id)
        m = q.first()
        if not m:
            return False
        for k, v in fields.items():
            if hasattr(m, k):
                setattr(m, k, v)
        self._session.commit()
        return True

    def create_from_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        categories = self._normalize_categories(data.get("categories"))
        name = str(data.get("name") or "").strip()
        m = SkillModel(
            name=name,
            slug=slugify(name) or f"skill-{id(data)}",
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
            user_id=self._user_id,
        )
        self._session.add(m)
        self._session.flush()
        if categories:
            self._set_category_links(m.id, categories)
            m.category = categories[0]
        self._session.commit()
        self._session.refresh(m)
        return self.get_by_id(m.id)
