"""Company repository implementation."""

import json
import sqlite3
from typing import Any

from domain.repositories.company_repository import ICompanyRepository


def _serialize(val):
    if isinstance(val, (list, dict)):
        return json.dumps(val)
    return val


class CompanyRepository(ICompanyRepository):
    """SQLite implementation of company repository."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def list_all(self) -> list[dict[str, Any]]:
        rows = self._conn.execute("SELECT * FROM companies ORDER BY name").fetchall()
        return [dict(r) for r in rows]

    def get_by_id(self, company_id: int) -> dict[str, Any] | None:
        row = self._conn.execute("SELECT * FROM companies WHERE id=?", (company_id,)).fetchone()
        if not row:
            return None
        return dict(row)

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        cur = self._conn.execute(
            "INSERT INTO companies (name, industry, city, country, logo_url, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (
                data.get("name"),
                data.get("industry"),
                data.get("city"),
                data.get("country"),
                data.get("logo_url"),
                _serialize(data.get("notes")),
            ),
        )
        self._conn.commit()
        return self.get_by_id(cur.lastrowid)

    def update(self, company_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        fields = []
        values = []
        for field in ["name", "industry", "city", "country", "logo_url", "notes", "description", "tech_stack", "website", "domain", "company_size", "company_type"]:
            if field in data:
                fields.append(f"{field}=?")
                values.append(_serialize(data[field]))

        if fields:
            values.append(company_id)
            self._conn.execute(f"UPDATE companies SET {','.join(fields)} WHERE id=?", values)
            self._conn.commit()

        return self.get_by_id(company_id)

    def delete(self, company_id: int) -> bool:
        self._conn.execute("DELETE FROM companies WHERE id=?", (company_id,))
        self._conn.commit()
        return True

    def get_intelligence(self, company_id: int) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT * FROM company_intelligence WHERE company_id=?", (company_id,)
        ).fetchone()
        if not row:
            return None
        return dict(row)
