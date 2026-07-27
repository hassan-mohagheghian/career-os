"""Job repository implementation."""

import sqlite3
from typing import Any

from domain.repositories.job_repository import IJobRepository


class JobRepository(IJobRepository):
    """SQLite implementation of job repository."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def get_by_num(self, num: int) -> dict[str, Any] | None:
        row = self._conn.execute("SELECT * FROM jobs WHERE num=?", (num,)).fetchone()
        if not row:
            return None
        d = dict(row)
        if d.get("company_id"):
            company = self._conn.execute(
                "SELECT id, name, industry, city, country, logo_url FROM companies WHERE id=?",
                (d["company_id"],),
            ).fetchone()
            if company:
                d["linked_company"] = dict(company)
        return d

    def list_jobs(
        self,
        offset: int | None = None,
        limit: int | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        conditions = ["deleted=0"]
        params: list[Any] = []

        if filters:
            if filters.get("filter_cities"):
                cities = [c.strip() for c in filters["filter_cities"].split(",") if c.strip()]
                if cities:
                    city_conditions = []
                    for city in cities:
                        city_conditions.append("locations LIKE ?")
                        params.append(f'%"{city}"%')
                        city_conditions.append("location = ?")
                        params.append(city)
                    conditions.append(f'({" OR ".join(city_conditions)})')

            if filters.get("filter_companies"):
                companies = [c.strip() for c in filters["filter_companies"].split(",") if c.strip()]
                if companies:
                    placeholders = ",".join(["?" for _ in companies])
                    conditions.append(f"company IN ({placeholders})")
                    params.extend(companies)

            if filters.get("filter_matches"):
                matches = [m.strip() for m in filters["filter_matches"].split(",") if m.strip()]
                if matches:
                    placeholders = ",".join(["?" for _ in matches])
                    conditions.append(f"match IN ({placeholders})")
                    params.extend(matches)

            if filters.get("filter_work_types"):
                wtypes = [w.strip() for w in filters["filter_work_types"].split(",") if w.strip()]
                if wtypes:
                    wt_conditions = []
                    for wt in wtypes:
                        wt_conditions.append("work_types LIKE ?")
                        params.append(f'%"{wt}"%')
                        wt_conditions.append("work_type = ?")
                        params.append(wt)
                    conditions.append(f'({" OR ".join(wt_conditions)})')

            if filters.get("filter_employment_types"):
                etypes = [e.strip() for e in filters["filter_employment_types"].split(",") if e.strip()]
                if etypes:
                    placeholders = ",".join(["?" for _ in etypes])
                    conditions.append(f"employment_type IN ({placeholders})")
                    params.extend(etypes)

            if filters.get("filter_tech"):
                like_param = f'%{filters["filter_tech"]}%'
                conditions.append("(stack LIKE ? OR role LIKE ? OR company LIKE ? OR notes LIKE ?)")
                params.extend([like_param, like_param, like_param, like_param])

            if filters.get("filter_response_status"):
                statuses = [s.strip() for s in filters["filter_response_status"].split(",") if s.strip()]
                if statuses:
                    placeholders = ",".join(["?" for _ in statuses])
                    conditions.append(f"response_status IN ({placeholders})")
                    params.extend(statuses)

            if filters.get("filter_applied") == "true":
                conditions.append("apply_time IS NOT NULL")

            if filters.get("filter_scores"):
                scores = [s.strip() for s in filters["filter_scores"].split(",") if s.strip()]
                if scores:
                    placeholders = ",".join(["?" for _ in scores])
                    conditions.append(f"score IN ({placeholders})")
                    params.extend(scores)

        where_clause = " AND ".join(conditions)
        total = self._conn.execute(
            f"SELECT COUNT(*) FROM jobs WHERE {where_clause}", params
        ).fetchone()[0]

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

        if sort_by == "applicants":
            order_clause = f"CAST(REPLACE(REPLACE(applicants, 'Not specified', '999'), '+', '') AS INTEGER) {sort_dir}"
        elif sort_by == "overall_score":
            order_clause = f"COALESCE(overall_score, 0) {sort_dir}"
        elif sort_by == "fit_score":
            order_clause = f"COALESCE(fit_score, 0) {sort_dir}"
        elif sort_by == "success_score":
            order_clause = f"COALESCE(success_score, 0) {sort_dir}"
        elif sort_by == "score":
            order_clause = f"COALESCE(fit_score, 0) {sort_dir}, COALESCE(success_score, 0) {sort_dir}"
        elif sort_by == "score_success":
            order_clause = f"COALESCE(success_score, 0) {sort_dir}, COALESCE(fit_score, 0) {sort_dir}"
        elif sort_by == "score_combined":
            order_clause = f"COALESCE(overall_score, 0) {sort_dir}"
        else:
            order_clause = f"{sort_by} {sort_dir}"

        if offset is not None and limit is not None:
            rows = self._conn.execute(
                f"SELECT * FROM jobs WHERE {where_clause} ORDER BY {order_clause} LIMIT ? OFFSET ?",
                params + [limit, offset],
            ).fetchall()
        else:
            rows = self._conn.execute(
                f"SELECT * FROM jobs WHERE {where_clause} ORDER BY {order_clause}",
                params,
            ).fetchall()

        return [dict(r) for r in rows], total

    def get_stats(self) -> dict[str, int]:
        stats = self._conn.execute(
            """SELECT
            COUNT(*) as total,
            SUM(CASE WHEN match='High' THEN 1 ELSE 0 END) as high_match,
            SUM(CASE WHEN score IN ('A','A+','A++') THEN 1 ELSE 0 END) as apply_now,
            SUM(CASE WHEN work_type='Remote' THEN 1 ELSE 0 END) as remote
            FROM jobs WHERE deleted=0"""
        ).fetchone()
        return {
            "total": stats[0] or 0,
            "high_match": stats[1] or 0,
            "apply_now": stats[2] or 0,
            "remote": stats[3] or 0,
        }

    def update(self, num: int, data: dict[str, Any]) -> dict[str, Any] | None:
        allowed_fields = {"apply_time", "response_time", "response_status", "notes"}
        updates = {k: v for k, v in data.items() if k in allowed_fields}
        if not updates:
            return self.get_by_num(num)

        set_clause = ", ".join(f"{k}=?" for k in updates)
        values = list(updates.values()) + [num]
        self._conn.execute(f"UPDATE jobs SET {set_clause} WHERE num=?", values)
        self._conn.commit()
        return self.get_by_num(num)

    def delete(self, num: int) -> bool:
        self._conn.execute("DELETE FROM jobs WHERE num=?", (num,))
        self._conn.execute("DELETE FROM summaries WHERE num=?", (num,))
        self._conn.execute(
            "DELETE FROM resumes WHERE id=? OR id=?",
            (f"pending_{num}", f"rescore_{num}"),
        )
        self._conn.commit()
        return True

    def mark_deleted(self, num: int) -> None:
        self._conn.execute("UPDATE jobs SET deleted=1 WHERE num=?", (num,))
        self._conn.commit()

    def mark_rescoring(self, num: int, rescoring: bool = True) -> None:
        self._conn.execute("UPDATE jobs SET rescoring=? WHERE num=?", (int(rescoring), num))
        self._conn.commit()

    def get_all_active(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT num, url, company FROM jobs WHERE deleted=0"
        ).fetchall()
        return [dict(r) for r in rows]
