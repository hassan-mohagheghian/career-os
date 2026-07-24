"""Tests for skill management: hide and merge."""

import sqlite3
import pytest


def _merge(conn, target_id, source_ids):
    """Core merge logic extracted from the endpoint."""
    target = conn.execute("SELECT name FROM tech_stack WHERE id=?", (target_id,)).fetchone()
    if not target:
        return None
    target_name = target[0]
    merged = []
    for sid in source_ids:
        source = conn.execute("SELECT name FROM tech_stack WHERE id=?", (sid,)).fetchone()
        if not source or source[0] == target_name:
            continue
        source_name = source[0]
        conn.execute("UPDATE skill_roadmaps SET skill_name=? WHERE skill_name=?", (target_name, source_name))
        conn.execute("UPDATE skill_roadmap_progress SET skill_name=? WHERE skill_name=?", (target_name, source_name))
        conn.execute("UPDATE skill_roadmap_jobs SET skill_name=? WHERE skill_name=?", (target_name, source_name))
        conn.execute("DELETE FROM tech_stack WHERE id=?", (sid,))
        merged.append(source_name)
    conn.commit()
    return merged


class TestMergeSkills:
    def test_merge_renames_roadmaps(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute("INSERT INTO tech_stack (name, level, source) VALUES (?, ?, ?)", ('PostgreSQL', 3, 'user'))
        conn.execute("INSERT INTO tech_stack (name, level, source) VALUES (?, ?, ?)", ('postgres', 2, 'service'))
        conn.execute("INSERT INTO skill_roadmaps (skill_name, title, level) VALUES (?, ?, ?)", ('postgres', 'Basics', 1))
        conn.execute("INSERT INTO skill_roadmap_progress (roadmap_id, skill_name, completed) VALUES (?, ?, ?)", (1, 'postgres', 1))
        conn.execute("INSERT INTO skill_roadmap_jobs (skill_name, status) VALUES (?, ?)", ('postgres', 'completed'))
        conn.commit()

        merged = _merge(conn, 1, [2])
        assert merged == ['postgres']

        roads = conn.execute("SELECT skill_name FROM skill_roadmaps").fetchall()
        progress = conn.execute("SELECT skill_name FROM skill_roadmap_progress").fetchall()
        jobs = conn.execute("SELECT skill_name FROM skill_roadmap_jobs").fetchall()
        tech = conn.execute("SELECT name FROM tech_stack").fetchall()

        assert all(r[0] == 'PostgreSQL' for r in roads)
        assert all(r[0] == 'PostgreSQL' for r in progress)
        assert all(r[0] == 'PostgreSQL' for r in jobs)
        assert len(tech) == 1
        assert tech[0][0] == 'PostgreSQL'
        conn.close()

    def test_hide_skill(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute("INSERT INTO tech_stack (name, level, source) VALUES (?, ?, ?)", ('CSS', 1, 'service'))
        conn.commit()

        conn.execute("UPDATE tech_stack SET hidden=1 WHERE id=1")
        conn.commit()

        row = conn.execute("SELECT hidden FROM tech_stack WHERE id=1").fetchone()
        assert row[0] == 1

        visible = conn.execute("SELECT name FROM tech_stack WHERE hidden=0").fetchall()
        assert len(visible) == 0
        conn.close()

    def test_merge_skips_self(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute("INSERT INTO tech_stack (name, level, source) VALUES (?, ?, ?)", ('Python', 4, 'user'))
        conn.commit()

        merged = _merge(conn, 1, [1])
        assert merged == []
        assert conn.execute("SELECT COUNT(*) FROM tech_stack").fetchone()[0] == 1
        conn.close()

    def test_merge_multiple_sources(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute("INSERT INTO tech_stack (name, level, source) VALUES (?, ?, ?)", ('React', 4, 'user'))
        conn.execute("INSERT INTO tech_stack (name, level, source) VALUES (?, ?, ?)", ('ReactJS', 3, 'service'))
        conn.execute("INSERT INTO tech_stack (name, level, source) VALUES (?, ?, ?)", ('react.js', 2, 'service'))
        conn.execute("INSERT INTO skill_roadmaps (skill_name, title, level) VALUES (?, ?, ?)", ('ReactJS', 'Basics', 1))
        conn.execute("INSERT INTO skill_roadmap_progress (roadmap_id, skill_name, completed) VALUES (?, ?, ?)", (1, 'ReactJS', 1))
        conn.commit()

        merged = _merge(conn, 1, [2, 3])
        assert set(merged) == {'ReactJS', 'react.js'}

        roads = conn.execute("SELECT skill_name FROM skill_roadmaps").fetchall()
        assert all(r[0] == 'React' for r in roads)

        tech = conn.execute("SELECT name FROM tech_stack ORDER BY id").fetchall()
        assert len(tech) == 1
        assert tech[0][0] == 'React'
        conn.close()
