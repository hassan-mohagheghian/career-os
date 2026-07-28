"""Database tool — provides raw SQL query execution for agents.

SRP: Only handles database query execution.
DIP: Agents use this tool instead of directly calling sqlite3.
"""

from __future__ import annotations

import sqlite3
from typing import Optional

from .base import BaseTool, ToolResult


class DatabaseTool(BaseTool):
    """Executes read-only SQL queries against the project database.

    Agents use this to access data without importing DB modules directly.
    Only SELECT queries are allowed — no mutations.
    """

    def __init__(self, db_path: Optional[str] = None):
        self._db_path = db_path

    @property
    def name(self) -> str:
        return "database"

    @property
    def description(self) -> str:
        return "Execute read-only SQL queries against the project database"

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "SQL SELECT query"},
                "params": {
                    "type": "array",
                    "description": "Query parameters",
                    "items": {"type": "string"},
                },
            },
            "required": ["query"],
        }

    def run(self, **kwargs) -> ToolResult:
        query = kwargs.get("query")
        if not query:
            return ToolResult(success=False, error="query parameter is required")

        # Safety: only allow SELECT queries
        query_upper = query.strip().upper()
        if not query_upper.startswith("SELECT"):
            return ToolResult(
                success=False,
                error="Only SELECT queries are allowed",
            )

        params = kwargs.get("params", [])

        try:
            if self._db_path:
                conn = sqlite3.connect(self._db_path)
                conn.row_factory = sqlite3.Row
            else:
                from core.db import get_db
                conn = get_db()

            rows = conn.execute(query, params).fetchall()
            conn.close()

            result = [dict(row) for row in rows]
            return ToolResult(
                success=True,
                data=result,
                metadata={"row_count": len(result)},
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Query failed: {e}")
