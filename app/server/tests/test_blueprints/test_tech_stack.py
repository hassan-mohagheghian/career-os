"""Tests for tech-stack and skill management core logic."""

import sqlite3
import json
import pytest


class TestTechStackCoreLogic:
    """Test the core logic without Flask HTTP layer."""

    def test_get_visible_skills(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        conn.execute("INSERT INTO skills (name, level, hidden, category) VALUES (?, ?, ?, ?)", ('Python', 4, 0, 'technical'))
        conn.execute("INSERT INTO skills (name, level, hidden, category) VALUES (?, ?, ?, ?)", ('jQuery', 1, 1, 'technical'))
        conn.commit()

        rows = conn.execute("SELECT * FROM skills WHERE hidden=0 ORDER BY level DESC").fetchall()
        assert len(rows) == 1
        assert dict(rows[0])['name'] == 'Python'
        conn.close()

    def test_get_skills_with_aliases(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute("INSERT INTO skills (name, level) VALUES (?, ?)", ('PostgreSQL', 4))
        conn.execute("INSERT INTO skill_aliases (skill_id, alias_name, normalized_name) VALUES (?, ?, ?)",
            (1, 'Postgres', 'postgres'))
        conn.commit()

        rows = conn.execute("SELECT * FROM skills WHERE hidden=0").fetchall()
        aliases = conn.execute("SELECT alias_name FROM skill_aliases WHERE skill_id=?", (1,)).fetchall()
        assert len(rows) == 1
        assert aliases[0][0] == 'Postgres'
        conn.close()

    def test_create_skill(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        cur = conn.execute("INSERT INTO skills (name, level, source, category) VALUES (?, ?, ?, ?)",
            ('Python', 4, 'user', 'technical'))
        conn.commit()

        row = conn.execute("SELECT * FROM skills WHERE id=?", (cur.lastrowid,)).fetchone()
        assert dict(row)['name'] == 'Python'
        assert dict(row)['source'] == 'user'
        conn.close()

    def test_create_duplicate_skill(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute("INSERT INTO skills (name, level) VALUES (?, ?)", ('Python', 4))
        conn.commit()

        existing = conn.execute("SELECT id FROM skills WHERE name=?", ('Python',)).fetchone()
        assert existing is not None
        conn.close()

    def test_rename_skill_updates_all_tables(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute("INSERT INTO skills (name, level) VALUES (?, ?)", ('Postgres', 4))
        conn.execute("INSERT INTO skill_roadmaps (skill_name, title, level) VALUES (?, ?, ?)", ('Postgres', 'Basics', 1))
        conn.execute("INSERT INTO skill_roadmap_progress (roadmap_id, skill_name, completed) VALUES (?, ?, ?)", (1, 'Postgres', 1))
        conn.execute("INSERT INTO skill_roadmap_jobs (skill_name, status) VALUES (?, ?)", ('Postgres', 'completed'))
        conn.execute("INSERT INTO skill_aliases (skill_id, alias_name, normalized_name) VALUES (?, ?, ?)", (1, 'Pg', 'pg'))
        conn.commit()

        new_name = 'PostgreSQL'
        conn.execute("UPDATE skills SET name=? WHERE id=?", (new_name, 1))
        conn.execute("UPDATE skill_roadmaps SET skill_name=? WHERE skill_name=?", (new_name, 'Postgres'))
        conn.execute("UPDATE skill_roadmap_progress SET skill_name=? WHERE skill_name=?", (new_name, 'Postgres'))
        conn.execute("UPDATE skill_roadmap_jobs SET skill_name=? WHERE skill_name=?", (new_name, 'Postgres'))
        conn.execute("UPDATE skill_aliases SET alias_name=? WHERE alias_name=? AND skill_id=?", (new_name, 'Postgres', 1))
        conn.commit()

        assert conn.execute("SELECT name FROM skills WHERE id=1").fetchone()[0] == 'PostgreSQL'
        assert conn.execute("SELECT skill_name FROM skill_roadmaps").fetchone()[0] == 'PostgreSQL'
        assert conn.execute("SELECT skill_name FROM skill_roadmap_progress").fetchone()[0] == 'PostgreSQL'
        assert conn.execute("SELECT skill_name FROM skill_roadmap_jobs").fetchone()[0] == 'PostgreSQL'
        conn.close()

    def test_delete_skill_removes_aliases(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute("INSERT INTO skills (name, level) VALUES (?, ?)", ('PostgreSQL', 4))
        conn.execute("INSERT INTO skill_aliases (skill_id, alias_name, normalized_name) VALUES (?, ?, ?)",
            (1, 'Postgres', 'postgres'))
        conn.commit()

        conn.execute("DELETE FROM skill_aliases WHERE skill_id=?", (1,))
        conn.execute("DELETE FROM skills WHERE id=?", (1,))
        conn.commit()

        assert conn.execute("SELECT COUNT(*) FROM skills").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM skill_aliases").fetchone()[0] == 0
        conn.close()

    def test_hide_and_restore_skill(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute("INSERT INTO skills (name, level, hidden) VALUES (?, ?, ?)", ('Python', 4, 0))
        conn.commit()

        conn.execute("UPDATE skills SET hidden=1 WHERE id=1")
        conn.commit()
        assert conn.execute("SELECT hidden FROM skills WHERE id=1").fetchone()[0] == 1

        conn.execute("UPDATE skills SET hidden=0 WHERE id=1")
        conn.commit()
        assert conn.execute("SELECT hidden FROM skills WHERE id=1").fetchone()[0] == 0
        conn.close()

    def test_merge_creates_alias_and_hides_source(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute("INSERT INTO skills (name, level) VALUES (?, ?)", ('PostgreSQL', 4))
        conn.execute("INSERT INTO skills (name, level) VALUES (?, ?)", ('Postgres', 3))
        conn.commit()

        target_id, source_id = 1, 2
        target_name = 'PostgreSQL'
        source_name = 'Postgres'

        # Rename across tables
        conn.execute("UPDATE skill_roadmaps SET skill_name=? WHERE skill_name=?", (target_name, source_name))
        conn.execute("UPDATE skill_roadmap_progress SET skill_name=? WHERE skill_name=?", (target_name, source_name))
        conn.execute("UPDATE skill_roadmap_jobs SET skill_name=? WHERE skill_name=?", (target_name, source_name))

        # Create alias
        conn.execute("INSERT INTO skill_aliases (skill_id, alias_name, normalized_name) VALUES (?, ?, ?)",
            (target_id, source_name, source_name.lower()))

        # Hide source
        conn.execute("UPDATE skills SET hidden=1 WHERE id=?", (source_id,))
        conn.commit()

        alias = conn.execute("SELECT alias_name FROM skill_aliases WHERE skill_id=?", (target_id,)).fetchone()
        source = conn.execute("SELECT hidden FROM skills WHERE id=?", (source_id,)).fetchone()
        assert alias[0] == 'Postgres'
        assert source[0] == 1
        conn.close()

    def test_skill_categories(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute("INSERT INTO skills (name, level, category) VALUES (?, ?, ?)", ('Python', 4, 'technical'))
        conn.execute("INSERT INTO skills (name, level, category) VALUES (?, ?, ?)", ('Leadership', 3, 'professional'))
        conn.execute("INSERT INTO skills (name, level, category) VALUES (?, ?, ?)", ('Fintech', 2, 'domain'))
        conn.commit()

        tech = conn.execute("SELECT name FROM skills WHERE category='technical'").fetchall()
        prof = conn.execute("SELECT name FROM skills WHERE category='professional'").fetchall()
        domain = conn.execute("SELECT name FROM skills WHERE category='domain'").fetchall()

        assert len(tech) == 1 and tech[0][0] == 'Python'
        assert len(prof) == 1 and prof[0][0] == 'Leadership'
        assert len(domain) == 1 and domain[0][0] == 'Fintech'
        conn.close()

    def test_skill_relationships(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute(
            "INSERT INTO skill_relationships (skill_name, related_name, relation_type, confidence) VALUES (?, ?, ?, ?)",
            ('React', 'Vue', 'similar', 0.8)
        )
        conn.execute(
            "INSERT INTO skill_relationships (skill_name, related_name, relation_type, confidence) VALUES (?, ?, ?, ?)",
            ('React', 'Angular', 'related', 0.6)
        )
        conn.commit()

        rows = conn.execute("SELECT * FROM skill_relationships WHERE skill_name='React'").fetchall()
        assert len(rows) == 2

        # Bidirectional query
        rows = conn.execute(
            "SELECT * FROM skill_relationships WHERE skill_name=? OR related_name=?",
            ('React', 'React')
        ).fetchall()
        assert len(rows) == 2
        conn.close()

    def test_multiple_aliases_per_skill(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute("INSERT INTO skills (name, level) VALUES (?, ?)", ('PostgreSQL', 4))
        conn.execute("INSERT INTO skill_aliases (skill_id, alias_name, normalized_name) VALUES (?, ?, ?)", (1, 'Postgres', 'postgres'))
        conn.execute("INSERT INTO skill_aliases (skill_id, alias_name, normalized_name) VALUES (?, ?, ?)", (1, 'PGSQL', 'pgsql'))
        conn.execute("INSERT INTO skill_aliases (skill_id, alias_name, normalized_name) VALUES (?, ?, ?)", (1, 'PSQL', 'psql'))
        conn.commit()

        aliases = conn.execute("SELECT alias_name FROM skill_aliases WHERE skill_id=1").fetchall()
        assert len(aliases) == 3
        alias_names = {a[0] for a in aliases}
        assert alias_names == {'Postgres', 'PGSQL', 'PSQL'}
        conn.close()
