"""SQLAlchemy-based job repository implementation."""

from typing import Any

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from domain.repositories.job_repository import IJobRepository
from infrastructure.database.models.job_model import JobModel
from infrastructure.database.mappers import job_model_to_dict


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
            from infrastructure.database.models.company_model import CompanyModel
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
        from infrastructure.database.models.misc_models import SummaryModel, ResumeModel
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
