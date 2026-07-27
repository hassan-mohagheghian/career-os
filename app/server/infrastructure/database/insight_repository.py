"""Insight repository implementation."""

import json
import sqlite3
from typing import Any

from domain.repositories.insight_repository import IInsightRepository


class InsightRepository(IInsightRepository):
    """SQLite implementation of insight repository.

    Handles both schemas:
        Production: career_insights(insight_type, data_json, created_at)
        Test:       career_insights(section, data, status, updated_at)
    """

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def _has_column(self, table: str, column: str) -> bool:
        try:
            cols = {r[1] for r in self._conn.execute(f"PRAGMA table_info({table})").fetchall()}
            return column in cols
        except Exception:
            return False

    def _data_column(self) -> str:
        return "data_json" if self._has_column("career_insights", "data_json") else "data"

    def _type_column(self) -> str:
        return "insight_type" if self._has_column("career_insights", "insight_type") else "section"

    def _time_column(self) -> str:
        if self._has_column("career_insights", "created_at"):
            return "created_at"
        if self._has_column("career_insights", "updated_at"):
            return "updated_at"
        return "NULL"

    def get_all(self) -> dict[str, Any]:
        tc = self._type_column()
        dc = self._data_column()
        tcol = self._time_column()
        rows = self._conn.execute(
            f"SELECT {tc}, {dc}, {tcol} FROM career_insights ORDER BY rowid DESC"
        ).fetchall()
        result = {}
        for row in rows:
            section = row[0]
            try:
                data = json.loads(row[1]) if row[1] else {}
            except (json.JSONDecodeError, TypeError):
                data = {}
            result[section] = {"data": data, "updated_at": row[2]}
        return result

    def get_section(self, section: str) -> dict[str, Any] | None:
        tc = self._type_column()
        dc = self._data_column()
        tcol = self._time_column()
        row = self._conn.execute(
            f"SELECT {tc}, {dc}, {tcol} FROM career_insights WHERE {tc}=?",
            (section,),
        ).fetchone()
        if not row:
            return None
        try:
            data = json.loads(row[1]) if row[1] else {}
        except (json.JSONDecodeError, TypeError):
            data = {}
        return {"section": row[0], "data": data, "updated_at": row[2]}

    def get_statuses(self) -> list[dict[str, Any]]:
        tc = self._type_column()
        dc = self._data_column()

        # Try to get statuses from career_insight_runs if it exists
        result = []
        try:
            run_cols = {r[1] for r in self._conn.execute("PRAGMA table_info(career_insight_runs)").fetchall()}
            if run_cols:
                # Use status column if it exists, otherwise default to 'completed'
                status_col = "status" if "status" in run_cols else None
                time_col = "completed_at" if "completed_at" in run_cols else ("started_at" if "started_at" in run_cols else None)

                if status_col and time_col:
                    rows = self._conn.execute(
                        f"SELECT insight_type, {status_col}, {time_col} FROM career_insight_runs ORDER BY rowid DESC"
                    ).fetchall()
                elif status_col:
                    rows = self._conn.execute(
                        f"SELECT insight_type, {status_col}, NULL FROM career_insight_runs ORDER BY rowid DESC"
                    ).fetchall()
                else:
                    rows = self._conn.execute(
                        f"SELECT insight_type, 'completed', NULL FROM career_insight_runs ORDER BY rowid DESC"
                    ).fetchall()

                seen = set()
                for row in rows:
                    insight_type = row[0]
                    if insight_type not in seen:
                        seen.add(insight_type)
                        result.append({
                            "section": insight_type,
                            "status": row[1] or "idle",
                            "updated_at": row[2],
                        })
        except Exception:
            pass

        # Also add any insight types that exist in career_insights but not in runs
        all_types = self._conn.execute(
            f"SELECT DISTINCT {tc} FROM career_insights"
        ).fetchall()
        seen = {r["section"] for r in result}
        for row in all_types:
            if row[0] not in seen:
                result.append({
                    "section": row[0],
                    "status": "completed",
                    "updated_at": None,
                })
        return result

    def upsert_section(self, section: str, data: dict[str, Any], status: str = "completed") -> None:
        tc = self._type_column()
        dc = self._data_column()
        existing = self._conn.execute(
            f"SELECT id FROM career_insights WHERE {tc}=?", (section,)
        ).fetchone()

        data_json = json.dumps(data)

        if existing:
            self._conn.execute(
                f"UPDATE career_insights SET {dc}=? WHERE {tc}=?",
                (data_json, section),
            )
        else:
            if self._has_column("career_insights", "insight_type"):
                self._conn.execute(
                    "INSERT INTO career_insights (insight_type, data_json, version) VALUES (?, ?, 1)",
                    (section, data_json),
                )
            else:
                self._conn.execute(
                    "INSERT INTO career_insights (section, data, status) VALUES (?, ?, ?)",
                    (section, data_json, status),
                )
        self._conn.commit()
