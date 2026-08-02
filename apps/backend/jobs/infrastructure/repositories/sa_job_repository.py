"""SQLAlchemy-based job repository implementation."""

from typing import Any

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from jobs.domain.repositories.job_repository import IJobRepository
from jobs.infrastructure.models.job_model import JobModel
from shared.infrastructure.database.mappers import job_model_to_dict


class SQLAlchemyJobRepository(IJobRepository):
    """SQLAlchemy implementation of job repository."""

    def __init__(self, session: Session):
        self._session = session

    def get_by_num(self, num: int) -> dict[str, Any] | None:
        model = self._session.query(JobModel).filter(JobModel.num == num).first()
        if not model:
            return None
        result = job_model_to_dict(model)
        if model.company_id:
            from companies.infrastructure.models.company_model import CompanyModel
            company = self._session.query(CompanyModel).filter(CompanyModel.id == model.company_id).first()
            if company:
                result["linked_company"] = {
                    "id": company.id,
                    "name": company.name,
                    "industry": company.industry,
                    "city": company.city,
                    "country": company.country,
                    "logo_url": company.logo_url,
                }
        return result

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
                        wt_conditions.append(JobModel.work_type == wt)
                    query = query.filter(or_(*wt_conditions))

            if filters.get("filter_employment_types"):
                etypes = [e.strip() for e in filters["filter_employment_types"].split(",") if e.strip()]
                if etypes:
                    query = query.filter(JobModel.employment_type.in_(etypes))

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
            "score_success", "score_combined", "num", "company", "location",
            "posted_at", "applicants", "adv_at", "see_at", "apply_time", "response_time",
        }
        if sort_by not in allowed_sorts:
            sort_by = "created_at"
        if sort_dir not in ("asc", "desc"):
            sort_dir = "desc"

        sort_column = getattr(JobModel, sort_by, JobModel.created_at)
        if sort_dir == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        if offset is not None and limit is not None:
            query = query.offset(offset).limit(limit)

        rows = query.all()
        return [job_model_to_dict(r) for r in rows], total

    def get_stats(self) -> dict[str, int]:
        total = self._session.query(func.count(JobModel.num)).filter(JobModel.deleted == 0).scalar()
        high_match = self._session.query(func.count(JobModel.num)).filter(
            JobModel.deleted == 0, JobModel.match == "High"
        ).scalar()
        apply_now = self._session.query(func.count(JobModel.num)).filter(
            JobModel.deleted == 0, JobModel.score.in_(["A", "A+", "A++"])
        ).scalar()
        remote = self._session.query(func.count(JobModel.num)).filter(
            JobModel.deleted == 0, JobModel.work_type == "Remote"
        ).scalar()

        return {
            "total": total or 0,
            "high_match": high_match or 0,
            "apply_now": apply_now or 0,
            "remote": remote or 0,
        }

    def update(self, num: int, data: dict[str, Any]) -> dict[str, Any] | None:
        allowed_fields = {"apply_time", "response_time", "response_status", "notes"}
        updates = {k: v for k, v in data.items() if k in allowed_fields}
        if not updates:
            return self.get_by_num(num)

        self._session.query(JobModel).filter(JobModel.num == num).update(updates)
        self._session.commit()
        return self.get_by_num(num)

    def delete(self, num: int) -> bool:
        from shared.infrastructure.database.models.misc_models import SummaryModel, ResumeModel
        self._session.query(JobModel).filter(JobModel.num == num).delete()
        self._session.query(SummaryModel).filter(SummaryModel.num == num).delete()
        self._session.query(ResumeModel).filter(
            ResumeModel.id.in_([f"pending_{num}", f"rescore_{num}"])
        ).delete(synchronize_session=False)
        self._session.commit()
        return True

    def mark_deleted(self, num: int) -> None:
        self._session.query(JobModel).filter(JobModel.num == num).update({"deleted": 1})
        self._session.commit()

    def mark_rescoring(self, num: int, rescoring: bool = True) -> None:
        self._session.query(JobModel).filter(JobModel.num == num).update({"rescoring": int(rescoring)})
        self._session.commit()

    def get_all_active(self) -> list[dict[str, Any]]:
        rows = self._session.query(JobModel).filter(JobModel.deleted == 0).all()
        return [{"num": r.num, "url": r.url, "company": r.company} for r in rows]

    # ── Extended methods for services ───────────────────────────────

    def get_next_num(self) -> int:
        result = self._session.query(func.max(JobModel.num)).scalar()
        return (result or 0) + 1

    def create_job(self, url: str, title: str | None = None, notes: str = "[]", links: str = "[]", source: str = "api") -> dict[str, Any]:
        num = self.get_next_num()
        model = JobModel(
            num=num,
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

    def get_by_id(self, uuid: str) -> dict[str, Any] | None:
        m = self._session.query(JobModel).filter(JobModel.id == uuid).first()
        if not m:
            return None
        return job_model_to_dict(m)

    def get_by_url(self, url: str) -> dict[str, Any] | None:
        m = self._session.query(JobModel).filter(JobModel.url == url).first()
        return job_model_to_dict(m) if m else None

    def get_num_by_url(self, url: str) -> int | None:
        m = self._session.query(JobModel.num).filter(JobModel.url == url).first()
        return m[0] if m else None

    def upsert(self, data: dict[str, Any]) -> dict[str, Any]:
        num = data.get("num")
        existing = self._session.query(JobModel).filter(JobModel.num == num).first() if num else None
        if existing:
            for k, v in data.items():
                if hasattr(existing, k) and k != "num":
                    setattr(existing, k, v)
            self._session.commit()
            self._session.refresh(existing)
            return job_model_to_dict(existing)
        m = JobModel(**{k: v for k, v in data.items() if hasattr(JobModel, k)})
        self._session.add(m)
        self._session.commit()
        self._session.refresh(m)
        return job_model_to_dict(m)

    def update_fields(self, num: int, **fields) -> bool:
        self._session.query(JobModel).filter(JobModel.num == num).update(fields)
        self._session.commit()
        return True

    def update_workflow_log(self, num: int, log_json: str) -> bool:
        self._session.query(JobModel).filter(JobModel.num == num).update({"workflow_log": log_json})
        self._session.commit()
        return True

    def set_deleted_by_url(self, url: str, exclude_num: int | None = None) -> int:
        q = self._session.query(JobModel).filter(JobModel.url == url)
        if exclude_num is not None:
            q = q.filter(JobModel.num != exclude_num)
        count = q.update({"deleted": 1})
        self._session.commit()
        return count

    def delete_all_active(self) -> int:
        count = self._session.query(JobModel).filter(JobModel.deleted == 0).delete(synchronize_session=False)
        self._session.commit()
        return count

    def get_company_id(self, num: int) -> int | None:
        m = self._session.query(JobModel.company_id).filter(JobModel.num == num).first()
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

    def update_status(self, num: int, status: str, **extra: Any) -> bool:
        fields = {'status': status, **extra}
        self._session.query(JobModel).filter(JobModel.num == num).update(fields)
        self._session.commit()
        return True

    def pick_queued_item(self) -> dict[str, Any] | None:
        model = self._session.query(JobModel).filter(
            JobModel.deleted == 0,
            JobModel.status == 'queued',
        ).order_by(
            JobModel.queue_order.asc(),
            JobModel.num.asc(),
        ).first()
        if model:
            model.status = 'processing'
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
        total = self._session.query(func.count(JobModel.num)).filter(JobModel.deleted == 0).scalar() or 0
        high = self._session.query(func.count(JobModel.num)).filter(
            JobModel.deleted == 0, JobModel.match == "High"
        ).scalar() or 0
        return {"jobs_total": total, "jobs_high_match": high}

    def get_location_data(self) -> list[dict[str, Any]]:
        rows = self._session.query(JobModel.location, JobModel.locations).filter(
            JobModel.deleted == 0
        ).all()
        return [{"location": r[0], "locations": r[1]} for r in rows]

    def get_company_id_by_num(self, num: int) -> int | None:
        m = self._session.query(JobModel.company_id).filter(JobModel.num == num).first()
        return m[0] if m else None

    def get_jobs_by_company_id(self, company_id: int) -> list[dict[str, Any]]:
        rows = self._session.query(JobModel).filter(
            JobModel.company_id == company_id,
            JobModel.deleted == 0,
        ).order_by(JobModel.created_at.desc()).all()
        return [job_model_to_dict(r) for r in rows]

    def search_jobs(
        self,
        page: int = 1,
        page_size: int = 25,
        query: str | None = None,
        sort: str = "updated_at",
        order: str = "desc",
        processing_status: str | None = None,
        company_id: int | None = None,
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
            work_type_filter = "Remote" if remote else "On-site"
            q = q.filter(JobModel.work_type == work_type_filter)

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
            q = q.order_by(sort_column.asc())
        else:
            q = q.order_by(sort_column.desc())

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
        processing_status: str | None = None,
        company_id: int | None = None,
        remote: bool | None = None,
        visa: bool | None = None,
        overall_score_min: int | None = None,
        overall_score_max: int | None = None,
        fit_score_min: int | None = None,
        fit_score_max: int | None = None,
        success_score_min: int | None = None,
        success_score_max: int | None = None,
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

        if processing_status:
            q = q.filter(JobModel.status == processing_status)

        if company_id is not None:
            q = q.filter(JobModel.company_id == company_id)

        if remote is not None:
            work_type_filter = "Remote" if remote else "On-site"
            q = q.filter(JobModel.work_type == work_type_filter)

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

        if cursor:
            cursor_op = sort_column < cursor if order == "desc" else sort_column > cursor
            q = q.filter(cursor_op)

        if order == "asc":
            q = q.order_by(sort_column.asc())
        else:
            q = q.order_by(sort_column.desc())

        q = q.limit(page_size + 1)
        if cursor is None and page and page > 1:
            q = q.offset((page - 1) * page_size)

        rows = q.all()
        has_more = len(rows) > page_size
        items = [job_model_to_dict(r) for r in rows[:page_size]]
        next_cursor = str(getattr(rows[page_size - 1], sort, rows[page_size - 1].updated_at)) if len(rows) >= page_size else None

        return items, total, next_cursor, has_more
