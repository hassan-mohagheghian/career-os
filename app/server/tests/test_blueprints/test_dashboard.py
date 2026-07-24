"""Tests for dashboard.py skill roadmap progress endpoints."""

import os
import tempfile
import sqlite3
import json
import pytest


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.execute("""CREATE TABLE IF NOT EXISTS skill_roadmaps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        skill_name TEXT NOT NULL,
        parent_id INTEGER REFERENCES skill_roadmaps(id),
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        level INTEGER DEFAULT 0,
        sort_order INTEGER DEFAULT 0,
        version INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS skill_roadmap_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roadmap_id INTEGER NOT NULL REFERENCES skill_roadmaps(id) ON DELETE CASCADE,
        skill_name TEXT NOT NULL,
        completed INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(roadmap_id)
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS skill_roadmap_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        skill_name TEXT NOT NULL,
        job_type TEXT NOT NULL DEFAULT 'generate',
        status TEXT NOT NULL DEFAULT 'queued',
        step INTEGER DEFAULT 0,
        total_steps INTEGER DEFAULT 4,
        message TEXT DEFAULT '',
        version INTEGER,
        count INTEGER,
        error TEXT,
        session_id TEXT,
        pid INTEGER,
        started_at TIMESTAMP,
        completed_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS tech_stack (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, level INTEGER, ml TEXT, mc TEXT,
        sc TEXT, dc TEXT, usage INTEGER, uc TEXT,
        roles TEXT, path TEXT, source TEXT DEFAULT 'service'
    )""")
    conn.commit()
    conn.close()
    yield path
    os.remove(path)


@pytest.fixture
def app(db_path):
    os.environ['DB_PATH'] = db_path
    import database as db_mod
    db_mod.DB_PATH = db_path

    from flask import Flask
    from flask_cors import CORS
    app = Flask(__name__)
    CORS(app)
    app.config['TESTING'] = True

    from blueprints.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp)

    return app


@pytest.fixture
def client(app):
    return app.test_client()


def _insert_roadmap(conn, skill, title, version=1, parent_id=None):
    cur = conn.execute(
        "INSERT INTO skill_roadmaps (skill_name, parent_id, title, version) VALUES (?, ?, ?, ?)",
        (skill, parent_id, title, version)
    )
    conn.commit()
    return cur.lastrowid


# ── GET /api/skill-roadmap-progress/<skill> ────────────────────────

class TestGetSkillProgress:
    def test_no_roadmap_returns_empty(self, client):
        resp = client.get('/api/skill-roadmap-progress?skill=Python')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data == {}

    def test_missing_skill_param(self, client):
        resp = client.get('/api/skill-roadmap-progress')
        assert resp.status_code == 400

    def test_returns_progress_for_latest_version(self, client, db_path):
        conn = sqlite3.connect(db_path)
        id1 = _insert_roadmap(conn, 'Python', 'Basics', version=1)
        id2 = _insert_roadmap(conn, 'Python', 'Advanced', version=2)
        conn.execute("INSERT INTO skill_roadmap_progress (roadmap_id, skill_name, completed) VALUES (?, ?, ?)", (id1, 'Python', 1))
        conn.execute("INSERT INTO skill_roadmap_progress (roadmap_id, skill_name, completed) VALUES (?, ?, ?)", (id2, 'Python', 0))
        conn.commit()
        conn.close()

        resp = client.get('/api/skill-roadmap-progress?skill=Python')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert str(id2) in data
        assert data[str(id2)] == 0

    def test_only_completed_items_shown(self, client, db_path):
        conn = sqlite3.connect(db_path)
        id1 = _insert_roadmap(conn, 'Python', 'Item 1', version=1)
        id2 = _insert_roadmap(conn, 'Python', 'Item 2', version=1)
        conn.execute("INSERT INTO skill_roadmap_progress (roadmap_id, skill_name, completed) VALUES (?, ?, ?)", (id1, 'Python', 1))
        conn.execute("INSERT INTO skill_roadmap_progress (roadmap_id, skill_name, completed) VALUES (?, ?, ?)", (id2, 'Python', 0))
        conn.commit()
        conn.close()

        resp = client.get('/api/skill-roadmap-progress?skill=Python')
        data = json.loads(resp.data)
        assert data[str(id1)] == 1
        assert data[str(id2)] == 0


# ── PUT /api/skill-roadmap-progress/<roadmap_id> ───────────────────

class TestUpdateRoadmapProgress:
    def test_mark_completed(self, client, db_path):
        conn = sqlite3.connect(db_path)
        rid = _insert_roadmap(conn, 'Python', 'Item 1', version=1)
        conn.close()

        resp = client.put(f'/api/skill-roadmap-progress/{rid}', json={'completed': True})
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['status'] == 'updated'

        # Verify in DB
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT completed FROM skill_roadmap_progress WHERE roadmap_id=?", (rid,)).fetchone()
        conn.close()
        assert row[0] == 1

    def test_mark_uncompleted(self, client, db_path):
        conn = sqlite3.connect(db_path)
        rid = _insert_roadmap(conn, 'Python', 'Item 1', version=1)
        conn.execute("INSERT INTO skill_roadmap_progress (roadmap_id, skill_name, completed) VALUES (?, ?, 1)", (rid, 'Python'))
        conn.commit()
        conn.close()

        resp = client.put(f'/api/skill-roadmap-progress/{rid}', json={'completed': False})
        assert resp.status_code == 200

        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT completed FROM skill_roadmap_progress WHERE roadmap_id=?", (rid,)).fetchone()
        conn.close()
        assert row[0] == 0

    def test_nonexistent_roadmap(self, client):
        resp = client.put('/api/skill-roadmap-progress/999', json={'completed': True})
        assert resp.status_code == 404

    def test_creates_progress_if_not_exists(self, client, db_path):
        conn = sqlite3.connect(db_path)
        rid = _insert_roadmap(conn, 'Python', 'Item 1', version=1)
        conn.close()

        resp = client.put(f'/api/skill-roadmap-progress/{rid}', json={'completed': True})
        assert resp.status_code == 200

        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT completed FROM skill_roadmap_progress WHERE roadmap_id=?", (rid,)).fetchone()
        conn.close()
        assert row is not None
        assert row[0] == 1


# ── GET /api/skill-roadmap-progress/all ─────────────────────────────

class TestGetAllProgress:
    def test_empty(self, client):
        resp = client.get('/api/skill-roadmap-progress/all')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data == {}

    def test_multiple_skills(self, client, db_path):
        conn = sqlite3.connect(db_path)
        py_id = _insert_roadmap(conn, 'Python', 'Basics', version=1)
        rust_id = _insert_roadmap(conn, 'Rust', 'Ownership', version=1)
        conn.execute("INSERT INTO skill_roadmap_progress (roadmap_id, skill_name, completed) VALUES (?, ?, ?)", (py_id, 'Python', 1))
        conn.execute("INSERT INTO skill_roadmap_progress (roadmap_id, skill_name, completed) VALUES (?, ?, ?)", (rust_id, 'Rust', 0))
        conn.commit()
        conn.close()

        resp = client.get('/api/skill-roadmap-progress/all')
        data = json.loads(resp.data)
        assert 'Python' in data
        assert 'Rust' in data
        assert data['Python']['completed'] == 1
        assert data['Python']['total'] == 1
        assert data['Rust']['completed'] == 0


# ── Skill roadmap generation endpoint ──────────────────────────────

class TestSkillRoadmapGeneration:
    def test_generate_requires_skill_name(self, client):
        resp = client.post('/api/skill-roadmaps/generate', json={})
        assert resp.status_code == 400

    def test_generate_empty_skill_name(self, client):
        resp = client.post('/api/skill-roadmaps/generate', json={'skill_name': ''})
        assert resp.status_code == 400

    def test_generate_returns_started(self, client, db_path):
        resp = client.post('/api/skill-roadmaps/generate', json={'skill_name': 'Python'})
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['status'] == 'started'
        assert data['skill'] == 'Python'

    def test_generate_rejects_if_already_running(self, client, db_path):
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO tech_stack (name, level) VALUES (?, ?)", ('Python', 3))
        # Insert a running job
        conn.execute(
            "INSERT INTO skill_roadmap_jobs (skill_name, job_type, status) VALUES (?, ?, ?)",
            ('Python', 'generate', 'running')
        )
        conn.commit()
        conn.close()

        resp = client.post('/api/skill-roadmaps/generate', json={'skill_name': 'Python'})
        assert resp.status_code == 409
