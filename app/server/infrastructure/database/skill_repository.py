"""Skill repository implementation."""

import json
import sqlite3
from typing import Any

from domain.repositories.skill_repository import ISkillRepository


class SkillRepository(ISkillRepository):
    """SQLite implementation of skill repository."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def _parse_tags(self, row: dict) -> dict:
        try:
            row["tags"] = json.loads(row.get("tags", "[]") or "[]")
        except (ValueError, TypeError):
            row["tags"] = []
        return row

    def list_visible(self, category: str = "") -> list[dict[str, Any]]:
        if category:
            rows = self._conn.execute(
                "SELECT * FROM skills WHERE hidden=0 AND category=? ORDER BY level DESC",
                (category,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM skills WHERE hidden=0 ORDER BY level DESC"
            ).fetchall()

        result = []
        for row in rows:
            skill_dict = self._parse_tags(dict(row))
            aliases = self._conn.execute(
                "SELECT alias_name FROM skill_aliases WHERE skill_id=?", (row["id"],)
            ).fetchall()
            skill_dict["aliases"] = [a[0] for a in aliases]
            result.append(skill_dict)
        return result

    def list_hidden(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM skills WHERE hidden=1 ORDER BY name"
        ).fetchall()
        return [self._parse_tags(dict(r)) for r in rows]

    def get_by_id(self, skill_id: int) -> dict[str, Any] | None:
        row = self._conn.execute("SELECT * FROM skills WHERE id=?", (skill_id,)).fetchone()
        if not row:
            return None
        return self._parse_tags(dict(row))

    def get_by_name(self, name: str) -> dict[str, Any] | None:
        row = self._conn.execute("SELECT * FROM skills WHERE name=?", (name,)).fetchone()
        if not row:
            return None
        return self._parse_tags(dict(row))

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        cur = self._conn.execute(
            "INSERT INTO skills (name, level, roles, path, source, source_type, category) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                data["name"],
                data.get("level", 1),
                data.get("roles", ""),
                data.get("path", ""),
                data.get("source", "user"),
                data.get("source_type", "user_input"),
                data.get("category", ""),
            ),
        )
        self._conn.commit()
        return self.get_by_id(cur.lastrowid)

    def update(self, skill_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        fields = []
        values = []
        for field in ["name", "level", "roles", "path", "source", "source_type", "category", "confidence", "market_relevance", "evidence"]:
            if field in data:
                fields.append(f"{field}=?")
                values.append(data[field])

        if "tags" in data:
            fields.append("tags=?")
            values.append(json.dumps(data["tags"]) if isinstance(data["tags"], list) else data["tags"])

        if not fields:
            return self.get_by_id(skill_id)

        values.append(skill_id)
        self._conn.execute(f"UPDATE skills SET {','.join(fields)} WHERE id=?", values)
        self._conn.commit()
        return self.get_by_id(skill_id)

    def delete(self, skill_id: int) -> bool:
        skill = self._conn.execute("SELECT name FROM skills WHERE id=?", (skill_id,)).fetchone()
        if not skill:
            return False

        self._conn.execute("DELETE FROM skill_aliases WHERE skill_id=?", (skill_id,))
        self._conn.execute("DELETE FROM skills WHERE id=?", (skill_id,))
        self._conn.commit()
        return True

    def set_hidden(self, skill_id: int, hidden: int) -> dict[str, Any] | None:
        self._conn.execute("UPDATE skills SET hidden=? WHERE id=?", (hidden, skill_id))
        self._conn.commit()
        return self.get_by_id(skill_id)

    def rename(self, skill_id: int, new_name: str) -> dict[str, Any] | None:
        old = self._conn.execute("SELECT name FROM skills WHERE id=?", (skill_id,)).fetchone()
        if not old:
            return None

        old_name = old[0]
        if old_name == new_name:
            return self.get_by_id(skill_id)

        exists = self._conn.execute(
            "SELECT id FROM skills WHERE name=? AND id!=?", (new_name, skill_id)
        ).fetchone()
        if exists:
            return None

        self._conn.execute("UPDATE skills SET name=? WHERE id=?", (new_name, skill_id))
        self._conn.execute("UPDATE skill_roadmaps SET skill_name=? WHERE skill_name=?", (new_name, old_name))
        self._conn.execute("UPDATE skill_roadmap_progress SET skill_name=? WHERE skill_name=?", (new_name, old_name))
        self._conn.execute("UPDATE skill_roadmap_jobs SET skill_name=? WHERE skill_name=?", (new_name, old_name))
        self._conn.execute(
            "UPDATE skill_aliases SET alias_name=? WHERE alias_name=? AND skill_id=?",
            (new_name, old_name, skill_id),
        )
        self._conn.commit()
        return self.get_by_id(skill_id)

    def merge(self, target_id: int, source_ids: list[int]) -> dict[str, Any]:
        target = self._conn.execute("SELECT name FROM skills WHERE id=?", (target_id,)).fetchone()
        if not target:
            return {"error": "Target skill not found"}

        target_name = target[0]
        merged = []

        for sid in source_ids:
            source = self._conn.execute("SELECT name FROM skills WHERE id=?", (sid,)).fetchone()
            if not source or source[0] == target_name:
                continue

            source_name = source[0]
            self._conn.execute("UPDATE skill_roadmaps SET skill_name=? WHERE skill_name=?", (target_name, source_name))
            self._conn.execute("UPDATE skill_roadmap_progress SET skill_name=? WHERE skill_name=?", (target_name, source_name))
            self._conn.execute("UPDATE skill_roadmap_jobs SET skill_name=? WHERE skill_name=?", (target_name, source_name))

            existing = self._conn.execute(
                "SELECT id FROM skill_aliases WHERE skill_id=? AND alias_name=?",
                (target_id, source_name),
            ).fetchone()
            if not existing:
                self._conn.execute(
                    "INSERT INTO skill_aliases (skill_id, alias_name, normalized_name) VALUES (?, ?, ?)",
                    (target_id, source_name, source_name.lower()),
                )

            self._conn.execute("UPDATE skills SET hidden=1 WHERE id=?", (sid,))
            merged.append(source_name)

        self._conn.commit()

        aliases = self._conn.execute(
            "SELECT alias_name FROM skill_aliases WHERE skill_id=?", (target_id,)
        ).fetchall()
        row = self._conn.execute("SELECT * FROM skills WHERE id=?", (target_id,)).fetchone()

        return {
            "status": "merged",
            "target": self._parse_tags(dict(row)) if row else None,
            "merged": merged,
            "aliases": [a[0] for a in aliases],
        }

    def get_categories(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT category, COUNT(*) as count, "
            "ROUND(AVG(market_relevance), 1) as avg_demand, "
            "ROUND(AVG(level), 1) as avg_level "
            "FROM skills WHERE hidden=0 AND category != '' "
            "GROUP BY category ORDER BY count DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_stats(self) -> dict[str, Any]:
        total = self._conn.execute("SELECT COUNT(*) FROM skills WHERE hidden=0").fetchone()[0]
        hidden = self._conn.execute("SELECT COUNT(*) FROM skills WHERE hidden=1").fetchone()[0]
        by_source = self._conn.execute(
            "SELECT source, COUNT(*) as count FROM skills WHERE hidden=0 GROUP BY source"
        ).fetchall()
        avg_level = self._conn.execute("SELECT ROUND(AVG(level), 1) FROM skills WHERE hidden=0").fetchone()[0]
        avg_demand = self._conn.execute(
            "SELECT ROUND(AVG(market_relevance), 1) FROM skills WHERE hidden=0 AND market_relevance > 0"
        ).fetchone()[0]
        total_relationships = self._conn.execute("SELECT COUNT(*) FROM skill_relationships").fetchone()[0]
        total_aliases = self._conn.execute("SELECT COUNT(*) FROM skill_aliases").fetchone()[0]
        total_roadmaps = self._conn.execute("SELECT COUNT(DISTINCT skill_name) FROM skill_roadmaps").fetchone()[0]

        return {
            "total": total,
            "hidden": hidden,
            "avg_level": avg_level or 0,
            "avg_demand": avg_demand or 0,
            "by_source": {r[0]: r[1] for r in by_source},
            "total_relationships": total_relationships,
            "total_aliases": total_aliases,
            "total_roadmaps": total_roadmaps,
        }

    def bulk_hide(self, skill_ids: list[int]) -> int:
        placeholders = ",".join("?" * len(skill_ids))
        self._conn.execute(f"UPDATE skills SET hidden=1 WHERE id IN ({placeholders})", skill_ids)
        self._conn.commit()
        return len(skill_ids)

    def bulk_categorize(self, skill_ids: list[int], category: str) -> int:
        placeholders = ",".join("?" * len(skill_ids))
        self._conn.execute(
            f"UPDATE skills SET category=? WHERE id IN ({placeholders})",
            [category] + skill_ids,
        )
        self._conn.commit()
        return len(skill_ids)

    def get_relationships(self, skill_name: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM skill_relationships WHERE skill_name=? OR related_name=?",
            (skill_name, skill_name),
        ).fetchall()
        return [dict(r) for r in rows]

    def create_relationship(self, data: dict[str, Any]) -> bool:
        try:
            self._conn.execute(
                "INSERT INTO skill_relationships (skill_name, related_name, relation_type, confidence) VALUES (?, ?, ?, ?)",
                (data["skill_name"], data["related_name"], data["relation_type"], data.get("confidence", 0)),
            )
            self._conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def delete_relationship(self, rel_id: int) -> bool:
        self._conn.execute("DELETE FROM skill_relationships WHERE id=?", (rel_id,))
        self._conn.commit()
        return True
