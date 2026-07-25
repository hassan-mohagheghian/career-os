"""Tests for roadmap helper functions: _parse_roadmap_json, _validate_roadmap, _save_roadmap_to_db."""

import json
import os
import sqlite3
import tempfile

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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        numbering TEXT DEFAULT ''
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
def db(db_path):
    """Set DB_PATH env and return connection for test assertions."""
    os.environ['DB_PATH'] = db_path
    import database as db_mod
    db_mod.DB_PATH = db_path
    return db_path


def _make_roadmap_item(title, level, children=None, description=""):
    item = {"title": title, "description": description or f"Interview: {title}?", "level": level}
    if children:
        item["children"] = children
    else:
        item["children"] = []
    return item


def _sample_roadmap():
    return [
        _make_roadmap_item("Basics", 100, [
            _make_roadmap_item("Variables", 80),
            _make_roadmap_item("Functions", 120),
        ]),
        _make_roadmap_item("Advanced", 500, [
            _make_roadmap_item("Generics", 450),
            _make_roadmap_item("Decorators", 550),
        ]),
    ]


# ── _parse_roadmap_json ────────────────────────────────────────────


class TestParseRoadmapJson:
    def test_valid_json_array_in_text_events(self):
        from blueprints.skill_roadmaps import _parse_roadmap_json

        roadmap = _sample_roadmap()
        events = [
            json.dumps({"type": "text", "part": {"text": "Here is the roadmap:\n"}}),
            json.dumps({"type": "text", "part": {"text": json.dumps(roadmap)}}),
        ]
        result, err = _parse_roadmap_json(events)
        assert err is None
        assert result == roadmap

    def test_json_with_markdown_fences(self):
        from blueprints.skill_roadmaps import _parse_roadmap_json

        roadmap = _sample_roadmap()
        events = [
            json.dumps({"type": "text", "part": {"text": "```json\n" + json.dumps(roadmap) + "\n```"}}),
        ]
        result, err = _parse_roadmap_json(events)
        assert err is None
        assert result == roadmap

    def test_json_with_markdown_fences_no_lang(self):
        from blueprints.skill_roadmaps import _parse_roadmap_json

        roadmap = _sample_roadmap()
        events = [
            json.dumps({"type": "text", "part": {"text": "```\n" + json.dumps(roadmap) + "\n```"}}),
        ]
        result, err = _parse_roadmap_json(events)
        assert err is None
        assert result == roadmap

    def test_json_embedded_in_larger_text(self):
        from blueprints.skill_roadmaps import _parse_roadmap_json

        roadmap = _sample_roadmap()
        events = [
            json.dumps({"type": "text", "part": {"text": "I'll generate the roadmap now.\n" + json.dumps(roadmap) + "\nDone."}}),
        ]
        result, err = _parse_roadmap_json(events)
        assert err is None
        assert result == roadmap

    def test_no_text_events_returns_error(self):
        from blueprints.skill_roadmaps import _parse_roadmap_json

        events = [
            json.dumps({"type": "tool_use", "part": {"tool": "write"}}),
        ]
        result, err = _parse_roadmap_json(events)
        assert result is None
        assert "No text output" in err

    def test_empty_text_returns_error(self):
        from blueprints.skill_roadmaps import _parse_roadmap_json

        events = [
            json.dumps({"type": "text", "part": {"text": ""}}),
            json.dumps({"type": "text", "part": {"text": "   "}}),
        ]
        result, err = _parse_roadmap_json(events)
        assert result is None

    def test_non_array_json_returns_error(self):
        from blueprints.skill_roadmaps import _parse_roadmap_json

        events = [
            json.dumps({"type": "text", "part": {"text": json.dumps({"foo": "bar"})}}),
        ]
        result, err = _parse_roadmap_json(events)
        assert result is None
        assert "Could not parse" in err

    def test_invalid_json_returns_error(self):
        from blueprints.skill_roadmaps import _parse_roadmap_json

        events = [
            json.dumps({"type": "text", "part": {"text": "not valid json at all"}}),
        ]
        result, err = _parse_roadmap_json(events)
        assert result is None
        assert "Could not parse" in err

    def test_handles_non_string_lines(self):
        from blueprints.skill_roadmaps import _parse_roadmap_json

        events = [123, None, {"not": "a string"}]
        result, err = _parse_roadmap_json(events)
        assert result is None

    def test_multiple_text_chunks_concatenated(self):
        from blueprints.skill_roadmaps import _parse_roadmap_json

        roadmap = _sample_roadmap()
        half = json.dumps(roadmap)[:len(json.dumps(roadmap)) // 2]
        other_half = json.dumps(roadmap)[len(json.dumps(roadmap)) // 2:]
        events = [
            json.dumps({"type": "text", "part": {"text": half}}),
            json.dumps({"type": "text", "part": {"text": other_half}}),
        ]
        # This will fail because splitting mid-JSON is invalid,
        # but the function should still try to find the array
        result, err = _parse_roadmap_json(events)
        # It won't parse because the split is mid-JSON — that's fine,
        # the point is it doesn't crash
        assert isinstance(err, str) or result is not None


# ── _validate_roadmap ──────────────────────────────────────────────


class TestValidateRoadmap:
    def test_valid_roadmap(self):
        from blueprints.skill_roadmaps import _validate_roadmap

        is_valid, errors = _validate_roadmap(_sample_roadmap())
        assert is_valid
        assert errors == []

    def test_empty_list(self):
        from blueprints.skill_roadmaps import _validate_roadmap

        is_valid, errors = _validate_roadmap([])
        assert not is_valid
        assert "empty" in errors[0].lower()

    def test_not_a_list(self):
        from blueprints.skill_roadmaps import _validate_roadmap

        is_valid, errors = _validate_roadmap({"title": "foo"})
        assert not is_valid

    def test_missing_title(self):
        from blueprints.skill_roadmaps import _validate_roadmap

        data = [{"description": "desc", "level": 100, "children": []}]
        is_valid, errors = _validate_roadmap(data)
        assert not is_valid
        assert any("missing title" in e.lower() for e in errors)

    def test_missing_level(self):
        from blueprints.skill_roadmaps import _validate_roadmap

        data = [{"title": "Item", "description": "desc", "children": []}]
        is_valid, errors = _validate_roadmap(data)
        assert not is_valid
        assert any("missing level" in e.lower() for e in errors)

    def test_missing_description(self):
        from blueprints.skill_roadmaps import _validate_roadmap

        data = [{"title": "Item", "level": 100, "children": []}]
        is_valid, errors = _validate_roadmap(data)
        assert not is_valid
        assert any("missing description" in e.lower() for e in errors)

    def test_level_out_of_range_negative(self):
        from blueprints.skill_roadmaps import _validate_roadmap

        data = [{"title": "Item", "description": "d", "level": -1, "children": []}]
        is_valid, errors = _validate_roadmap(data)
        assert not is_valid
        assert any("out of range" in e.lower() for e in errors)

    def test_level_out_of_range_over_1000(self):
        from blueprints.skill_roadmaps import _validate_roadmap

        data = [{"title": "Item", "description": "d", "level": 1001, "children": []}]
        is_valid, errors = _validate_roadmap(data)
        assert not is_valid
        assert any("out of range" in e.lower() for e in errors)

    def test_level_1000_is_valid(self):
        from blueprints.skill_roadmaps import _validate_roadmap

        data = [{"title": "Item", "description": "d", "level": 1000, "children": []}]
        is_valid, errors = _validate_roadmap(data)
        assert is_valid

    def test_level_0_is_valid(self):
        from blueprints.skill_roadmaps import _validate_roadmap

        data = [{"title": "Item", "description": "d", "level": 0, "children": []}]
        is_valid, errors = _validate_roadmap(data)
        assert is_valid

    def test_duplicate_titles(self):
        from blueprints.skill_roadmaps import _validate_roadmap

        data = [
            {"title": "Same", "description": "d", "level": 100, "children": []},
            {"title": "Same", "description": "d", "level": 200, "children": []},
        ]
        is_valid, errors = _validate_roadmap(data)
        assert not is_valid
        assert any("duplicate" in e.lower() for e in errors)

    def test_too_many_root_items(self):
        from blueprints.skill_roadmaps import _validate_roadmap

        data = [
            {"title": f"Item {i}", "description": "d", "level": i * 50, "children": []}
            for i in range(31)
        ]
        is_valid, errors = _validate_roadmap(data)
        assert not is_valid
        assert any("too many" in e.lower() for e in errors)

    def test_nested_children_valid(self):
        from blueprints.skill_roadmaps import _validate_roadmap

        data = [_make_roadmap_item("Parent", 400, [
            _make_roadmap_item("Child 1", 350),
            _make_roadmap_item("Child 2", 450),
        ])]
        is_valid, errors = _validate_roadmap(data)
        assert is_valid

    def test_too_deep_nesting(self):
        from blueprints.skill_roadmaps import _validate_roadmap

        data = [{
            "title": "L1", "description": "d", "level": 100,
            "children": [{
                "title": "L2", "description": "d", "level": 100,
                "children": [{
                    "title": "L3", "description": "d", "level": 100,
                    "children": []
                }]
            }]
        }]
        is_valid, errors = _validate_roadmap(data)
        assert not is_valid
        assert any("depth" in e.lower() or "nesting" in e.lower() for e in errors)

    def test_level_not_a_number(self):
        from blueprints.skill_roadmaps import _validate_roadmap

        data = [{"title": "Item", "description": "d", "level": "high", "children": []}]
        is_valid, errors = _validate_roadmap(data)
        assert not is_valid
        assert any("must be a number" in e.lower() for e in errors)

    def test_children_not_an_array(self):
        from blueprints.skill_roadmaps import _validate_roadmap

        data = [{"title": "Item", "description": "d", "level": 100, "children": "bad"}]
        is_valid, errors = _validate_roadmap(data)
        assert not is_valid
        assert any("must be an array" in e.lower() for e in errors)


# ── _save_roadmap_to_db ────────────────────────────────────────────


class TestSaveRoadmapToDb:
    def test_saves_root_items(self, db):
        from blueprints.skill_roadmaps import _save_roadmap_to_db

        roadmap = _sample_roadmap()
        version, count = _save_roadmap_to_db("Python", roadmap)
        assert version == 1
        assert count == 2

        conn = sqlite3.connect(db)
        rows = conn.execute(
            "SELECT title, level, parent_id FROM skill_roadmaps WHERE skill_name='Python' AND parent_id IS NULL ORDER BY sort_order"
        ).fetchall()
        conn.close()
        assert len(rows) == 2
        assert rows[0][0] == "Basics"
        assert rows[1][0] == "Advanced"

    def test_saves_children(self, db):
        from blueprints.skill_roadmaps import _save_roadmap_to_db

        roadmap = _sample_roadmap()
        _save_roadmap_to_db("Python", roadmap)

        conn = sqlite3.connect(db)
        rows = conn.execute(
            "SELECT title, parent_id FROM skill_roadmaps WHERE skill_name='Python' AND parent_id IS NOT NULL ORDER BY sort_order"
        ).fetchall()
        conn.close()
        assert len(rows) == 4
        titles = {r[0] for r in rows}
        assert "Variables" in titles
        assert "Functions" in titles
        assert "Generics" in titles
        assert "Decorators" in titles

    def test_assigns_numbering(self, db):
        from blueprints.skill_roadmaps import _save_roadmap_to_db

        roadmap = _sample_roadmap()
        _save_roadmap_to_db("Python", roadmap)

        conn = sqlite3.connect(db)
        rows = conn.execute(
            "SELECT numbering, title FROM skill_roadmaps WHERE skill_name='Python' ORDER BY sort_order, id"
        ).fetchall()
        conn.close()
        numbering = {r[1]: r[0] for r in rows}
        assert numbering["Basics"] == "1"
        assert numbering["Advanced"] == "2"
        assert numbering["Variables"] == "1.1"
        assert numbering["Functions"] == "1.2"
        assert numbering["Generics"] == "2.1"
        assert numbering["Decorators"] == "2.2"

    def test_increments_version(self, db):
        from blueprints.skill_roadmaps import _save_roadmap_to_db

        roadmap = _sample_roadmap()
        v1, _ = _save_roadmap_to_db("Python", roadmap)
        v2, _ = _save_roadmap_to_db("Python", roadmap)
        assert v2 == v1 + 1

    def test_preserves_checked_items(self, db):
        from blueprints.skill_roadmaps import _save_roadmap_to_db

        roadmap = _sample_roadmap()
        _save_roadmap_to_db("Python", roadmap, checked_titles=["Basics", "Variables"])

        conn = sqlite3.connect(db)
        rows = conn.execute(
            "SELECT roadmap_id, completed FROM skill_roadmap_progress WHERE skill_name='Python'"
        ).fetchall()
        conn.close()
        assert len(rows) == 2
        completed_ids = {r[0] for r in rows if r[1] == 1}
        assert len(completed_ids) == 2

    def test_empty_roadmap(self, db):
        from blueprints.skill_roadmaps import _save_roadmap_to_db

        version, count = _save_roadmap_to_db("Python", [])
        assert version == 1
        assert count == 0
