"""SQLAlchemy-based job repository implementation."""

from typing import Any
from datetime import datetime, UTC

from sqlalchemy import func, or_, and_, case, cast, select
from sqlalchemy.orm import Session

from jobs.domain.repositories.job_repository import IJobRepository
from jobs.infrastructure.models.job_model import JobModel
from jobs.infrastructure.models.job_analysis_model import JobAnalysisModel
from jobs.infrastructure.mappers import job_model_to_dict

# Keyset-cursor sentinel encoding a NULL sort value. NULLs always sort last,
# so the cursor must distinguish a NULL boundary row from a non-NULL one.
NULL_CURSOR = "__null__"


class SQLAlchemyJobRepository(IJobRepository):
    """SQLAlchemy implementation of job repository."""

    def __init__(self, session: Session):
        self._session = session

    def get_by_id(self, uuid: str) -> dict[str, Any] | None:
        m = self._session.query(JobModel).filter(JobModel.id == uuid).first()
        if not m:
            return None
        return job_model_to_dict(m)

    def get_by_ids(self, job_ids: list[str]) -> list[dict[str, Any]]:
        if not job_ids:
            return []
        rows = (
            self._session.query(JobModel)
            .filter(JobModel.id.in_(job_ids), JobModel.deleted == 0)
            .all()
        )
        return [{"id": m.id, "title": m.title, "location": m.location} for m in rows]

    def list_jobs(
        self,
        offset: int | None = None,
        limit: int | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        query = self._session.query(JobModel).filter(JobModel.deleted == 0)

        if filters:
            if filters.get("filter_cities"):
                cities = [c.strip() for c in filters["filter_cities"].split(",") if c.strip()]
                if cities:
                    city_conditions = []
                    for city in cities:
                        city_conditions.append(JobModel.locations.contains(f'"{city}"'))
                        city_conditions.append(JobModel.location == city)
                    query = query.filter(or_(*city_conditions))

            if filters.get("filter_companies"):
                companies = [c.strip() for c in filters["filter_companies"].split(",") if c.strip()]
                if companies:
                    query = query.filter(JobModel.company.in_(companies))

            if filters.get("filter_matches"):
                matches = [m.strip() for m in filters["filter_matches"].split(",") if m.strip()]
                if matches:
                    query = query.filter(JobModel.match.in_(matches))

            if filters.get("filter_work_types"):
                wtypes = [w.strip() for w in filters["filter_work_types"].split(",") if w.strip()]
                if wtypes:
                    wt_conditions = []
                    for wt in wtypes:
                        wt_conditions.append(JobModel.work_types.contains(f'"{wt}"'))
                    query = query.filter(or_(*wt_conditions))

            if filters.get("filter_employment_types"):
                etypes = [e.strip() for e in filters["filter_employment_types"].split(",") if e.strip()]
                if etypes:
                    et_conditions = []
                    for et in etypes:
                        et_conditions.append(JobModel.employment_types.contains(f'"{et}"'))
                    query = query.filter(or_(*et_conditions))

            if filters.get("filter_tech"):
                like_param = f'%{filters["filter_tech"]}%'
                query = query.filter(
                    or_(
                        JobModel.stack.contains(like_param),
                        JobModel.role.contains(like_param),
                        JobModel.company.contains(like_param),
                        JobModel.notes.contains(like_param),
                    )
                )

            if filters.get("filter_response_status"):
                statuses = [s.strip() for s in filters["filter_response_status"].split(",") if s.strip()]
                if statuses:
                    query = query.filter(JobModel.response_status.in_(statuses))

            if filters.get("filter_applied") == "true":
                query = query.filter(JobModel.apply_time.isnot(None))

            if filters.get("filter_scores"):
                scores = [s.strip() for s in filters["filter_scores"].split(",") if s.strip()]
                if scores:
                    query = query.filter(JobModel.score.in_(scores))

            if filters.get("filter_status"):
                statuses = [s.strip() for s in filters["filter_status"].split(",") if s.strip()]
                if statuses:
                    query = query.filter(JobModel.status.in_(statuses))

        total = query.count()

        # Build ORDER BY
        allowed_sorts = {
            "created_at", "overall_score", "fit_score", "success_score", "score",
            "score_success", "score_combined", "company", "location",
            "posted_at", "applicants", "adv_at", "see_at", "apply_time", "response_time",
        }
        if sort_by not in allowed_sorts:
            sort_by = "created_at"
        if sort_dir not in ("asc", "desc"):
            sort_dir = "desc"

        sort_column = getattr(JobModel, sort_by, JobModel.created_at)
        if sort_dir == "desc":
            query = query.order_by(sort_column.desc().nulls_last())
        else:
            query = query.order_by(sort_column.asc().nulls_last())

        if offset is not None and limit is not None:
            query = query.offset(offset).limit(limit)

        rows = query.all()
        return [job_model_to_dict(r) for r in rows], total

    def get_stats(self) -> dict[str, int]:
        total = self._session.query(func.count(JobModel.id)).filter(JobModel.deleted == 0).scalar()
        high_match = self._session.query(func.count(JobModel.id)).filter(
            JobModel.deleted == 0, JobModel.match == "High"
        ).scalar()
        apply_now = self._session.query(func.count(JobModel.id)).filter(
            JobModel.deleted == 0, JobModel.score.in_(["A", "A+", "A++"])
        ).scalar()
        remote = self._session.query(func.count(JobModel.id)).filter(
            JobModel.deleted == 0, JobModel.work_types.contains('"Remote"')
        ).scalar()

        return {
            "total": total or 0,
            "high_match": high_match or 0,
            "apply_now": apply_now or 0,
            "remote": remote or 0,
        }

    def delete_by_id(self, uuid: str) -> bool:
        """Hard-delete a job by UUID and its related tables.

        Deletes the job row plus related records that reference it (summaries,
        resumes, tailored documents). Processing executions are handled by the
        caller via the processing execution repository.
        """
        from jobs.infrastructure.models.misc_models import SummaryModel, ResumeModel
        from jobs.infrastructure.models.job_analysis_model import JobAnalysisModel
        model = self._session.query(JobModel).filter(JobModel.id == uuid).first()
        if not model:
            return False
        self._session.query(JobModel).filter(JobModel.id == uuid).delete()
        self._session.query(JobAnalysisModel).filter(JobAnalysisModel.job_id == uuid).delete(synchronize_session=False)
        self._session.query(SummaryModel).filter(SummaryModel.job_id == uuid).delete(synchronize_session=False)
        self._session.query(ResumeModel).filter(ResumeModel.job_id == uuid).delete(synchronize_session=False)
        self._session.commit()
        return True

    def mark_deleted(self, job_id: str) -> None:
        self._session.query(JobModel).filter(JobModel.id == job_id).update(
            {"deleted": 1, "updated_at": datetime.now(UTC).isoformat()}
        )
        self._session.commit()

    def mark_rescoring(self, job_id: str, rescoring: bool = True) -> None:
        self._session.query(JobModel).filter(JobModel.id == job_id).update(
            {"rescoring": int(rescoring), "updated_at": datetime.now(UTC).isoformat()}
        )
        self._session.commit()

    def get_all_active(self) -> list[dict[str, Any]]:
        rows = self._session.query(JobModel).filter(JobModel.deleted == 0).all()
        return [{"id": r.id, "url": r.url, "company": r.company} for r in rows]

    # ── Extended methods for services ───────────────────────────────

    # Editable job fields for the Edit Job feature (whitelist).
    EDITABLE_FIELDS = {
        "title",
        "role",
        "company",
        "location",
        "url",
        "work_types",
        "employment_types",
        "visa",
        "salary",
        "description",
        "notes",
        "links",
    }

    def update_by_id(self, uuid: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Partially update a job's core data by UUID.

        Only whitelisted fields are applied; keys not present in ``data`` are
        left unchanged. ``None`` values are ignored (treated as "not provided").
        Returns the updated job dict, or ``None`` if the job does not exist.
        """
        updates = {k: v for k, v in data.items() if k in self.EDITABLE_FIELDS and v is not None}
        model = self._session.query(JobModel).filter(JobModel.id == uuid).first()
        if not model:
            return None
        if updates:
            model.updated_at = datetime.now(UTC).replace(tzinfo=None)
            for k, v in updates.items():
                setattr(model, k, v)
            self._session.commit()
            self._session.refresh(model)
        return job_model_to_dict(model)

    def create_job(self, url: str, title: str | None = None, notes: str = "[]", links: str = "[]", source: str = "api") -> dict[str, Any]:
        model = JobModel(
            url=url,
            title=title,
            links=links,
            notes=notes,
            status="imported",
            source=source,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return job_model_to_dict(model)

    def get_by_url(self, url: str) -> dict[str, Any] | None:
        m = self._session.query(JobModel).filter(JobModel.url == url).first()
        return job_model_to_dict(m) if m else None

    def get_id_by_url(self, url: str) -> str | None:
        m = self._session.query(JobModel.id).filter(JobModel.url == url).first()
        return m[0] if m else None

    def upsert(self, data: dict[str, Any]) -> dict[str, Any]:
        job_id = data.get("id") or data.get("url")
        existing = self._session.query(JobModel).filter(
            or_(JobModel.id == job_id, JobModel.url == job_id)
        ).first() if job_id else None
        if existing:
            existing.updated_at = datetime.now(UTC).isoformat()
            for k, v in data.items():
                if hasattr(existing, k) and k != "id":
                    setattr(existing, k, v)
            self._session.commit()
            self._session.refresh(existing)
            return job_model_to_dict(existing)
        m = JobModel(**{k: v for k, v in data.items() if hasattr(JobModel, k)})
        self._session.add(m)
        self._session.commit()
        self._session.refresh(m)
        return job_model_to_dict(m)

    def update_fields(self, item_id: str, **fields) -> bool:
        fields.setdefault("updated_at", datetime.now(UTC).isoformat())
        valid_fields = {k: v for k, v in fields.items() if hasattr(JobModel, k)}
        self._session.query(JobModel).filter(JobModel.id == item_id).update(valid_fields)
        self._session.commit()
        return True

    def set_company(self, job_id: str, company_id: str | None, company_name: str | None = None) -> bool:
        """Link a job to a company (or unlink it with ``company_id=None``).

        When linking, ``company_name`` is also written so the display name
        matches the company's canonical name.
        """
        fields: dict[str, Any] = {"company_id": company_id}
        if company_name is not None:
            fields["company"] = company_name
        return self.update_fields(job_id, **fields)

    def update_workflow_log(self, job_id: str, log_json: str) -> bool:
        self._session.query(JobModel).filter(JobModel.id == job_id).update(
            {"workflow_log": log_json, "updated_at": datetime.now(UTC).isoformat()}
        )
        self._session.commit()
        return True

    def set_deleted_by_url(self, url: str, exclude_id: str | None = None) -> int:
        q = self._session.query(JobModel).filter(JobModel.url == url)
        if exclude_id is not None:
            q = q.filter(JobModel.id != exclude_id)
        count = q.update({"deleted": 1, "updated_at": datetime.now(UTC).isoformat()})
        self._session.commit()
        return count

    def delete_all_active(self) -> int:
        count = self._session.query(JobModel).filter(JobModel.deleted == 0).delete(synchronize_session=False)
        self._session.commit()
        return count

    # ── Queue management methods (consolidated from pending repo) ──

    EXCLUDED_STATUSES = {"processed"}

    def list_pending(self) -> list[dict[str, Any]]:
        rows = self._session.query(JobModel).filter(
            JobModel.deleted == 0,
            ~JobModel.status.in_(self.EXCLUDED_STATUSES)
        ).order_by(JobModel.created_at.desc()).all()
        return [job_model_to_dict(r) for r in rows]

    def count_pending(self) -> int:
        return self._session.query(JobModel).filter(
            JobModel.deleted == 0,
            ~JobModel.status.in_(self.EXCLUDED_STATUSES)
        ).count()

    def get_max_queue_order(self) -> int:
        result = self._session.query(func.max(JobModel.queue_order)).scalar()
        return result or 0

    def mark_processing_as_waiting(self) -> int:
        count = self._session.query(JobModel).filter(
            JobModel.deleted == 0,
            JobModel.status.in_(self.ACTIVE_STATUSES)
        ).update({"status": "pending", "updated_at": datetime.now(UTC).isoformat()})
        self._session.commit()
        return count

    def reset_processing_orphans(self) -> int:
        count = self._session.query(JobModel).filter(
            JobModel.deleted == 0,
            JobModel.status.in_(self.ACTIVE_STATUSES)
        ).update({"status": "created", "updated_at": datetime.now(UTC).isoformat()})
        self._session.commit()
        return count

    def get_queued_items(self) -> list[dict[str, Any]]:
        rows = self._session.query(JobModel).filter(
            JobModel.deleted == 0,
            JobModel.status == "queued"
        ).order_by(JobModel.queue_order.asc(), JobModel.id.asc()).all()
        return [job_model_to_dict(r) for r in rows]

    def reset_steps(self, item_id: str) -> bool:
        updates = {
            "error": None,
            "workflow_log": "[]",
            "current_node": None,
            "retry_count": 0,
            "failure_reason": None,
            "status": "created",
            "updated_at": datetime.now(UTC).isoformat(),
        }
        self._session.query(JobModel).filter(JobModel.id == item_id).update(updates)
        self._session.commit()
        return True

    def get_all_for_stream(self) -> list[dict[str, Any]]:
        rows = self._session.query(JobModel).order_by(JobModel.created_at.desc()).all()
        return [job_model_to_dict(r) for r in rows]

    def create_pending_job(self, url: str, source: str, company: str, status: str = "created") -> dict[str, Any]:
        model = JobModel(url=url, source=source, company=company, status=status)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return job_model_to_dict(model)

    def soft_delete(self, item_id: str) -> bool:
        m = self._session.query(JobModel).filter(JobModel.id == item_id).first()
        if m:
            m.deleted = 1
            m.updated_at = datetime.now(UTC).isoformat()
            self._session.commit()
            return True
        return False

    def get_company_id(self, job_id: str) -> str | None:
        m = self._session.query(JobModel.company_id).filter(JobModel.id == job_id).first()
        return m[0] if m else None

    # ── Lifecycle methods ───────────────────────────────────────────

    ACTIVE_STATUSES = {'processing'}

    def get_pending_count(self) -> int:
        return self._session.query(JobModel).filter(
            JobModel.deleted == 0,
            JobModel.status == 'pending',
        ).count()

    def list_by_status(self, status: str) -> list[dict[str, Any]]:
        rows = self._session.query(JobModel).filter(
            JobModel.deleted == 0,
            JobModel.status == status,
        ).order_by(JobModel.created_at.desc()).all()
        return [job_model_to_dict(r) for r in rows]

    def get_processing_count(self) -> int:
        return self._session.query(JobModel).filter(
            JobModel.deleted == 0,
            JobModel.status.in_(self.ACTIVE_STATUSES),
        ).count()

    def get_queued_count(self) -> int:
        return self._session.query(JobModel).filter(
            JobModel.deleted == 0,
            JobModel.status == 'queued',
        ).count()

    def update_status(self, job_id: str, status: str, **extra: Any) -> bool:
        extra.setdefault("updated_at", datetime.now(UTC).isoformat())
        fields = {'status': status, **extra}
        self._session.query(JobModel).filter(JobModel.id == job_id).update(fields)
        self._session.commit()
        return True

    def pick_queued_item(self) -> dict[str, Any] | None:
        model = self._session.query(JobModel).filter(
            JobModel.deleted == 0,
            JobModel.status == 'queued',
        ).order_by(
            JobModel.queue_order.asc(),
            JobModel.created_at.asc(),
        ).first()
        if model:
            model.status = 'processing'
            model.updated_at = datetime.now(UTC).isoformat()
            self._session.commit()
            self._session.refresh(model)
            return job_model_to_dict(model)
        return None

    def get_processing_items(self) -> list[dict[str, Any]]:
        rows = self._session.query(JobModel).filter(
            JobModel.deleted == 0,
            JobModel.status.in_(self.ACTIVE_STATUSES),
        ).all()
        return [job_model_to_dict(r) for r in rows]

    def get_dashboard_counts(self) -> dict[str, int]:
        total = self._session.query(func.count(JobModel.id)).filter(JobModel.deleted == 0).scalar() or 0
        high = self._session.query(func.count(JobModel.id)).filter(
            JobModel.deleted == 0, JobModel.match == "High"
        ).scalar() or 0
        return {"jobs_total": total, "jobs_high_match": high}

    def get_location_data(self) -> list[dict[str, Any]]:
        rows = self._session.query(JobModel.location, JobModel.locations).filter(
            JobModel.deleted == 0
        ).all()
        return [{"location": r[0], "locations": r[1]} for r in rows]

    def get_company_id_by_id(self, job_id: str) -> str | None:
        m = self._session.query(JobModel.company_id).filter(JobModel.id == job_id).first()
        return m[0] if m else None

    def get_jobs_by_company_id(self, company_id: str) -> list[dict[str, Any]]:
        rows = self._session.query(JobModel).filter(
            JobModel.company_id == company_id,
            JobModel.deleted == 0,
        ).order_by(JobModel.created_at.desc()).all()
        return [job_model_to_dict(r) for r in rows]

    def reassign_company(self, from_company_id: str, to_company_id: str) -> bool:
        """Re-point all non-deleted jobs linked to ``from_company_id`` to ``to_company_id``."""
        self._session.query(JobModel).filter(
            JobModel.company_id == from_company_id,
            JobModel.deleted == 0,
        ).update(
            {"company_id": to_company_id, "updated_at": datetime.now(UTC).isoformat()},
            synchronize_session=False,
        )
        self._session.commit()
        return True

    def search_jobs(
        self,
        page: int = 1,
        page_size: int = 25,
        query: str | None = None,
        sort: str = "updated_at",
        order: str = "desc",
        processing_status: str | None = None,
        company_id: str | None = None,
        remote: bool | None = None,
        visa: bool | None = None,
        overall_score_min: int | None = None,
        overall_score_max: int | None = None,
        fit_score_min: int | None = None,
        fit_score_max: int | None = None,
        success_score_min: int | None = None,
        success_score_max: int | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        q = self._session.query(JobModel).filter(JobModel.deleted == 0)

        if query:
            like = f"%{query}%"
            q = q.filter(
                or_(
                    JobModel.title.ilike(like),
                    JobModel.company.ilike(like),
                    JobModel.location.ilike(like),
                    JobModel.role.ilike(like),
                )
            )

        if processing_status:
            q = q.filter(JobModel.status == processing_status)

        if company_id is not None:
            q = q.filter(JobModel.company_id == company_id)

        if remote is not None:
            if remote:
                q = q.filter(JobModel.work_types.contains('"Remote"'))
            else:
                q = q.filter(~JobModel.work_types.contains('"Remote"'))

        if visa is not None:
            if visa:
                q = q.filter(JobModel.visa.isnot(None), JobModel.visa != "")
            else:
                q = q.filter(
                    or_(JobModel.visa.is_(None), JobModel.visa == "")
                )

        if overall_score_min is not None:
            q = q.filter(JobModel.overall_score >= overall_score_min)
        if overall_score_max is not None:
            q = q.filter(JobModel.overall_score <= overall_score_max)
        if fit_score_min is not None:
            q = q.filter(JobModel.fit_score >= fit_score_min)
        if fit_score_max is not None:
            q = q.filter(JobModel.fit_score <= fit_score_max)
        if success_score_min is not None:
            q = q.filter(JobModel.success_score >= success_score_min)
        if success_score_max is not None:
            q = q.filter(JobModel.success_score <= success_score_max)

        total = q.count()

        sort_map = {
            "created_at": JobModel.created_at,
            "updated_at": JobModel.updated_at,
            "title": JobModel.title,
            "company": JobModel.company,
            "status": JobModel.status,
            "overall_score": JobModel.overall_score,
            "fit_score": JobModel.fit_score,
            "success_score": JobModel.success_score,
        }
        sort_column = sort_map.get(sort, JobModel.updated_at)
        if order == "asc":
            q = q.order_by(sort_column.asc().nulls_last())
        else:
            q = q.order_by(sort_column.desc().nulls_last())

        offset = (page - 1) * page_size
        q = q.offset(offset).limit(page_size)

        rows = q.all()
        return [job_model_to_dict(r) for r in rows], total

    def search_jobs_cursor(
        self,
        cursor: str | None = None,
        page_size: int = 25,
        page: int = 1,
        query: str | None = None,
        sort: str = "updated_at",
        order: str = "desc",
        job_ids: list[str] | None = None,
        exclude_job_ids: list[str] | None = None,
        status_lookup: dict[str, str] | None = None,
        company_id: str | None = None,
        location: str | None = None,
        remote: bool | None = None,
        visa: bool | None = None,
        overall_score_min: int | None = None,
        overall_score_max: int | None = None,
        fit_score_min: int | None = None,
        fit_score_max: int | None = None,
        success_score_min: int | None = None,
        success_score_max: int | None = None,
        pinned: bool | None = None,
        recommendation: str | None = None,
    ) -> tuple[list[dict[str, Any]], int, str | None, bool]:
        q = self._session.query(JobModel).filter(JobModel.deleted == 0)

        if query:
            like = f"%{query}%"
            q = q.filter(
                or_(
                    JobModel.title.ilike(like),
                    JobModel.company.ilike(like),
                    JobModel.location.ilike(like),
                    JobModel.role.ilike(like),
                )
            )

        if job_ids is not None:
            q = q.filter(JobModel.id.in_(job_ids))

        if exclude_job_ids:
            q = q.filter(~JobModel.id.in_(exclude_job_ids))

        if company_id is not None:
            q = q.filter(JobModel.company_id == company_id)

        if location:
            q = q.filter(JobModel.location.ilike(f"%{location}%"))

        if remote is not None:
            if remote:
                q = q.filter(JobModel.work_types.contains('"Remote"'))
            else:
                q = q.filter(~JobModel.work_types.contains('"Remote"'))

        if visa is not None:
            if visa:
                q = q.filter(JobModel.visa.isnot(None), JobModel.visa != "")
            else:
                q = q.filter(
                    or_(JobModel.visa.is_(None), JobModel.visa == "")
                )

        if overall_score_min is not None:
            q = q.filter(JobModel.overall_score >= overall_score_min)
        if overall_score_max is not None:
            q = q.filter(JobModel.overall_score <= overall_score_max)
        if fit_score_min is not None:
            q = q.filter(JobModel.fit_score >= fit_score_min)
        if fit_score_max is not None:
            q = q.filter(JobModel.fit_score <= fit_score_max)
        if success_score_min is not None:
            q = q.filter(JobModel.success_score >= success_score_min)
        if success_score_max is not None:
            q = q.filter(JobModel.success_score <= success_score_max)

        if pinned is not None:
            q = q.filter(JobModel.pinned == (1 if pinned else 0))

        if recommendation:
            q = q.filter(JobModel.id.in_(
                select(JobAnalysisModel.job_id).where(
                    JobAnalysisModel.recommendation == recommendation
                )
            ))

        total = q.count()

        sort_map = {
            "created_at": JobModel.created_at,
            "updated_at": JobModel.updated_at,
            "title": JobModel.title,
            "company": JobModel.company,
            "status": JobModel.status,
            "overall_score": JobModel.overall_score,
            "fit_score": JobModel.fit_score,
            "success_score": JobModel.success_score,
        }
        sort_column = sort_map.get(sort, JobModel.updated_at)

        # Status sort orders by the same execution status each row displays
        # (the latest execution), grouping rows by status. Unprocessed rows
        # (no execution, absent from ``status_lookup``) always sort last, in
        # both directions — achieved with a direction-aware sentinel for the
        # COALESCE (unprocessed rank = max in asc, = -1 in desc).
        status_mode = sort == "status" and status_lookup is not None
        if status_mode:
            statuses = sorted(set(status_lookup.values()))
            rank_of = {status: i for i, status in enumerate(statuses)}
            grouped: dict[str, list[str]] = {}
            for job_id, status in status_lookup.items():
                grouped.setdefault(status, []).append(job_id)
            status_rank = case(
                *[
                    (JobModel.id.in_(ids), rank_of[status])
                    for status, ids in grouped.items()
                ]
            )
            sentinel = len(statuses) if order == "asc" else -1
            rank_expr = func.coalesce(status_rank, sentinel)
        else:
            rank_expr = None

        if cursor:
            if status_mode:
                try:
                    cur_rank, cur_id = cursor.split(":", 1)
                    cur_rank = int(cur_rank)
                except (ValueError, TypeError):
                    cur_rank = cur_id = None
                if cur_rank is not None:
                    if order == "desc":
                        q = q.filter(
                            or_(
                                rank_expr < cur_rank,
                                and_(rank_expr == cur_rank, JobModel.id < cur_id),
                            )
                        )
                    else:
                        q = q.filter(
                            or_(
                                rank_expr > cur_rank,
                                and_(rank_expr == cur_rank, JobModel.id > cur_id),
                            )
                        )
            else:
                # NULLS LAST is the policy for every sort, so keyset
                # pagination must be NULL-aware. Cursor format: ``value|id``
                # (a legacy single-value cursor without ``|`` is tolerated).
                # While the boundary row is non-NULL the next page is every
                # row strictly below it plus all NULL rows (they sort last);
                # once the boundary row is NULL, remaining pages walk the
                # NULL tail by id alone.
                cur_value, cur_id = cursor, None
                if "|" in cursor:
                    cur_value, cur_id = cursor.rsplit("|", 1)
                if cur_value == NULL_CURSOR and cur_id is not None:
                    if order == "desc":
                        q = q.filter(and_(sort_column.is_(None), JobModel.id < cur_id))
                    else:
                        q = q.filter(and_(sort_column.is_(None), JobModel.id > cur_id))
                else:
                    cur = cast(cur_value, sort_column.type)
                    cmp = sort_column < cur if order == "desc" else sort_column > cur
                    if cur_id is not None:
                        tiebreak = JobModel.id < cur_id if order == "desc" else JobModel.id > cur_id
                        q = q.filter(
                            or_(cmp, and_(sort_column == cur, tiebreak), sort_column.is_(None))
                        )
                    else:
                        q = q.filter(or_(cmp, sort_column.is_(None)))

        if status_mode:
            if order == "asc":
                q = q.order_by(rank_expr.asc(), JobModel.id.asc())
            else:
                q = q.order_by(rank_expr.desc(), JobModel.id.desc())
        elif order == "asc":
            q = q.order_by(sort_column.asc().nulls_last(), JobModel.id.asc())
        else:
            q = q.order_by(sort_column.desc().nulls_last(), JobModel.id.desc())

        q = q.limit(page_size + 1)
        if cursor is None and page and page > 1:
            q = q.offset((page - 1) * page_size)

        rows = q.all()
        has_more = len(rows) > page_size
        items = [job_model_to_dict(r) for r in rows[:page_size]]
        if len(rows) >= page_size:
            boundary = rows[page_size - 1]
            if status_mode:
                boundary_status = status_lookup.get(boundary.id)
                boundary_rank = (
                    sentinel
                    if boundary_status is None
                    else rank_of.get(boundary_status, sentinel)
                )
                next_cursor = f"{boundary_rank}:{boundary.id}"
            else:
                boundary_value = getattr(boundary, sort, boundary.updated_at)
                value = NULL_CURSOR if boundary_value is None else str(boundary_value)
                next_cursor = f"{value}|{boundary.id}"
        else:
            next_cursor = None

        return items, total, next_cursor, has_more

    def set_pinned(self, job_id: str, pinned: bool) -> bool:
        """Set or clear the pinned flag on a job. Returns True if the job exists."""
        model = self._session.query(JobModel).filter(JobModel.id == job_id).first()
        if not model:
            return False
        model.pinned = 1 if pinned else 0
        model.updated_at = datetime.now(UTC).replace(tzinfo=None)
        self._session.commit()
        return True
