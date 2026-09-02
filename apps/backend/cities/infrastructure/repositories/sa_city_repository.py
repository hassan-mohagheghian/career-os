"""SQLAlchemy implementation of the Cities repository.

The job-count aggregation joins the ``city`` schema's cities table with the
``job`` schema's jobs table on the logical ``jobs.city_id`` column. This is a
plain-column join (no FK constraint — AGENTS.md rule 15) which is safe across
bounded contexts.

Merge re-points the logical references on jobs / companies / candidate profiles
(``city_id`` plus the denormalized ``city``/``country`` text) to the target and
soft-hides the merged-away city, mirroring the Skills merge pattern.
"""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from cities.domain.repositories.city_repository import ICityRepository
from cities.infrastructure.mappers import city_model_to_dict
from cities.infrastructure.models.city_model import CityModel, CityAliasModel
from jobs.infrastructure.models.job_model import JobModel
from companies.infrastructure.models.company_model import CompanyModel
from candidates.infrastructure.models.candidate_model import CandidateProfileModel


class SQLAlchemyCityRepository(ICityRepository):
    def __init__(self, session: Session, user_id: str = ""):
        self._session = session
        self._user_id = user_id

    def find_by_city_country(self, city: str, country: str) -> dict[str, Any] | None:
        q = select(CityModel).where(
            func.lower(CityModel.city) == (city or "").lower(),
            func.lower(CityModel.country) == (country or "").lower(),
        )
        if self._user_id:
            q = q.where(CityModel.user_id == self._user_id)
        model = self._session.scalar(q)
        return city_model_to_dict(model, aliases=self._get_aliases(model.id)) if model else None

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        model = CityModel(
            city=data.get("city") or "",
            country=data.get("country") or "",
            original_text=data.get("original_text"),
            address=data.get("address"),
            created_at=now,
            updated_at=now,
            user_id=self._user_id,
        )
        self._session.add(model)
        try:
            self._session.flush()
        except IntegrityError:
            self._session.rollback()
            existing = self.find_by_city_country(
                data.get("city") or "", data.get("country") or ""
            )
            if existing is not None:
                return existing
            raise
        return city_model_to_dict(model)

    def get_by_id(self, city_id: str) -> dict[str, Any] | None:
        model = self._session.get(CityModel, city_id)
        if model is None:
            return None
        return city_model_to_dict(model, aliases=self._get_aliases(model.id))

    def list_with_job_counts(
        self, sort: str = "jobs", order: str = "desc"
    ) -> list[dict[str, Any]]:
        count_col = func.count(JobModel.id).label("job_count")
        city_q = (
            select(
                CityModel,
                count_col,
            )
            .outerjoin(JobModel, JobModel.city_id == CityModel.id)
            .where((JobModel.deleted == 0) | (JobModel.deleted.is_(None)))
            .where(CityModel.hidden == 0)
        )
        if self._user_id:
            city_q = city_q.where(CityModel.user_id == self._user_id)
        rows = self._session.execute(
            city_q.group_by(CityModel.id)
        ).all()

        alias_rows = self._session.execute(
            select(CityAliasModel.city_id, CityAliasModel.alias_name).where(
                CityAliasModel.city_id.in_([m.id for m, _ in rows])
            )
        ).all() if rows else []
        aliases_by_city: dict[str, list[str]] = {}
        for city_id, alias_name in alias_rows:
            aliases_by_city.setdefault(city_id, []).append(alias_name)

        items = []
        for city_model, job_count in rows:
            item = city_model_to_dict(
                city_model, aliases=aliases_by_city.get(city_model.id, [])
            )
            item["job_count"] = job_count or 0
            items.append(item)

        desc = order == "desc"

        def key(item: dict[str, Any]) -> Any:
            if sort == "country":
                return (item.get("country") or "").lower()
            if sort == "city":
                return (item.get("city") or "").lower()
            if sort == "created_at":
                return item.get("created_at") or ""
            return item.get("job_count") or 0

        with_value = [r for r in items if key(r) is not None]
        without_value = [r for r in items if key(r) is None]
        with_value.sort(key=key, reverse=desc)
        items = with_value + without_value
        return items

    # ── Aliases ─────────────────────────────────────────────────

    def _get_aliases(self, city_id: str) -> list[str]:
        rows = self._session.execute(
            select(CityAliasModel.alias_name)
            .where(CityAliasModel.city_id == city_id)
            .order_by(CityAliasModel.created_at)
        ).scalars().all()
        return list(rows)

    def add_alias(self, city_id: str, alias_name: str) -> dict[str, Any] | None:
        model = self._session.get(CityModel, city_id)
        if model is None:
            return None
        alias_name = (alias_name or "").strip()
        if not alias_name:
            return city_model_to_dict(model, aliases=self._get_aliases(city_id))
        exists = self._session.scalar(
            select(CityAliasModel.id).where(
                CityAliasModel.city_id == city_id,
                CityAliasModel.alias_name == alias_name,
            )
        )
        if not exists:
            self._session.add(
                CityAliasModel(
                    city_id=city_id,
                    alias_name=alias_name,
                    normalized_name=alias_name.lower(),
                )
            )
            self._session.flush()
        return city_model_to_dict(model, aliases=self._get_aliases(city_id))

    def remove_alias(self, city_id: str, alias_name: str) -> dict[str, Any] | None:
        model = self._session.get(CityModel, city_id)
        if model is None:
            return None
        row = self._session.scalar(
            select(CityAliasModel).where(
                CityAliasModel.city_id == city_id,
                CityAliasModel.alias_name == alias_name,
            )
        )
        if row is not None:
            self._session.delete(row)
            self._session.flush()
        return city_model_to_dict(model, aliases=self._get_aliases(city_id))

    def promote_alias_to_canonical(
        self, city_id: str, alias_name: str
    ) -> dict[str, Any] | None:
        model = self._session.get(CityModel, city_id)
        if model is None:
            return None
        row = self._session.scalar(
            select(CityAliasModel).where(
                CityAliasModel.city_id == city_id,
                CityAliasModel.alias_name == alias_name,
            )
        )
        if row is None:
            return None
        old_city = model.city
        # A city with a different country but the same canonical name would
        # collide on the unique (city, country) constraint only if the country
        # matches too; guard the same (city, country) combo.
        clash = self._session.scalar(
            select(CityModel.id).where(
                CityModel.id != city_id,
                func.lower(CityModel.city) == alias_name.lower(),
                func.lower(CityModel.country) == (model.country or "").lower(),
            )
        )
        if clash:
            return {"error": "conflict"}
        self._session.delete(row)
        model.city = alias_name
        model.updated_at = datetime.now(UTC).isoformat()
        # Old canonical becomes an alias, unless it equals the new name.
        if old_city and old_city.lower() != alias_name.lower():
            exists = self._session.scalar(
                select(CityAliasModel.id).where(
                    CityAliasModel.city_id == city_id,
                    CityAliasModel.alias_name == old_city,
                )
            )
            if not exists:
                self._session.add(
                    CityAliasModel(
                        city_id=city_id,
                        alias_name=old_city,
                        normalized_name=old_city.lower(),
                    )
                )
        self._session.flush()
        result = city_model_to_dict(model, aliases=self._get_aliases(city_id))
        result["previous_name"] = old_city
        return result

    # ── Merge ────────────────────────────────────────────────────

    def merge(self, target_id: str, source_ids: list[str]) -> dict[str, Any]:
        target = self._session.get(CityModel, target_id)
        if target is None:
            return {"error": "Target city not found"}
        target_name = (target.city or "").lower()
        merged: list[str] = []
        for sid in source_ids:
            if sid == target_id:
                continue
            source = self._session.get(CityModel, sid)
            if source is None or source.hidden:
                continue
            if (source.city or "").lower() == target_name:
                continue
            source_name = source.city or ""
            self._add_alias_row(target_id, source_name)
            self._repoint_references(sid, target)
            source.hidden = 1
            source.updated_at = datetime.now(UTC).isoformat()
            merged.append(source_name)
        self._session.flush()
        return {
            "status": "merged",
            "target": city_model_to_dict(target, aliases=self._get_aliases(target_id)),
            "merged": merged,
            "aliases": self._get_aliases(target_id),
        }

    def _add_alias_row(self, city_id: str, alias_name: str) -> None:
        if not alias_name:
            return
        exists = self._session.scalar(
            select(CityAliasModel.id).where(
                CityAliasModel.city_id == city_id,
                CityAliasModel.alias_name == alias_name,
            )
        )
        if not exists:
            self._session.add(
                CityAliasModel(
                    city_id=city_id,
                    alias_name=alias_name,
                    normalized_name=alias_name.lower(),
                )
            )

    def _repoint_references(self, source_id: str, target: CityModel) -> None:
        """Re-point every logical reference to a source city onto the target.

        Mirrors Skills' mention-folding but across the owning tables: the plain
        ``city_id`` column plus the denormalized ``city``/``country`` text are
        updated to the target's canonical values (application-level integrity,
        no cross-context FK — AGENTS.md rule 15).
        """
        now = datetime.now(UTC).isoformat()
        city, country = target.city or "", target.country or ""

        self._session.query(JobModel).filter(JobModel.city_id == source_id).update(
            {"city_id": target.id, "city": city, "country": country, "updated_at": now}
        )
        self._session.query(CompanyModel).filter(CompanyModel.city_id == source_id).update(
            {"city_id": target.id, "city": city, "country": country}
        )
        self._session.query(CandidateProfileModel).filter(
            CandidateProfileModel.city_id == source_id
        ).update({"city_id": target.id, "city": city, "country": country})


__all__ = ["SQLAlchemyCityRepository"]