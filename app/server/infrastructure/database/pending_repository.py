"""Pending job repository implementation."""

import json
import sqlite3
from typing import Any

from domain.repositories.pending_repository import IPendingRepository


def _serialize(val):
    """Serialize complex types to JSON strings for SQLite."""
    if isinstance(val, (list, dict)):
        return json.dumps(val)
    return val


class PendingRepository(IPendingRepository):
    """SQLite implementation of pending job repository."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def list_pending(self, table: str = "pending_jobs") -> list[dict[str, Any]]:
        rows = self._conn.execute(
            f"SELECT * FROM {table} WHERE status != 'done' ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_by_id(self, item_id: str, table: str = "pending_jobs") -> dict[str, Any] | None:
        row = self._conn.execute(f"SELECT * FROM {table} WHERE id=?", (item_id,)).fetchone()
        if not row:
            return None
        return dict(row)

    def _has_column(self, table: str, column: str) -> bool:
        try:
            cols = {r[1] for r in self._conn.execute(f"PRAGMA table_info({table})").fetchall()}
            return column in cols
        except Exception:
            return False

    def create(self, data: dict[str, Any], table: str = "pending_jobs") -> dict[str, Any]:
        if table == "pending_jobs":
            url = data.get("url", "")
            # Check if URL already exists — reset it instead of inserting duplicate
            existing = self._conn.execute(
                "SELECT id FROM pending_jobs WHERE url=?", (url,)
            ).fetchone()
            if existing:
                from datetime import datetime
                self._conn.execute(
                    """UPDATE pending_jobs SET status='pending', error=NULL, source=?,
                    company=?, queue_order=0, workflow_log='[]', updated_at=?
                    WHERE id=?""",
                    (data.get("source", "api"), data.get("company", ""), datetime.now().isoformat(), existing[0]),
                )
                self._conn.commit()
                return self.get_by_id(str(existing[0]), table)

            cols = ["url", "source", "company", "status", "notes"]
            vals = [
                url,
                data.get("source", "api"),
                data.get("company", ""),
                "pending",
                _serialize(data.get("notes", "[]")),
            ]
            if self._has_column(table, "links"):
                cols.append("links")
                vals.append(_serialize(data.get("links", "[]")))
            placeholders = ",".join(["?"] * len(cols))
            cur = self._conn.execute(
                f"INSERT INTO pending_jobs ({','.join(cols)}) VALUES ({placeholders})",
                vals,
            )
            self._conn.commit()
            return self.get_by_id(str(cur.lastrowid), table)
        elif table == "pending_companies":
            cols = ["input_text", "input_type", "source", "status", "notes"]
            vals = [
                data.get("name", data.get("input_text", "")),
                data.get("input_type", "url"),
                data.get("source", "api"),
                "pending",
                _serialize(data.get("notes", "[]")),
            ]
            if self._has_column(table, "links"):
                cols.append("links")
                vals.append(_serialize(data.get("links", "[]")))
            placeholders = ",".join(["?"] * len(cols))
            cur = self._conn.execute(
                f"INSERT INTO pending_companies ({','.join(cols)}) VALUES ({placeholders})",
                vals,
            )
        else:
            raise ValueError(f"Unknown table: {table}")

        self._conn.commit()
        return self.get_by_id(str(cur.lastrowid), table)

    def update_status(self, item_id: str, status: str, table: str = "pending_jobs") -> bool:
        self._conn.execute(f"UPDATE {table} SET status=? WHERE id=?", (status, item_id))
        self._conn.commit()
        return True

    def count_pending(self, table: str = "pending_jobs") -> int:
        return self._conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE status != 'done'"
        ).fetchone()[0]
