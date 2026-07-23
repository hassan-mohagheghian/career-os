"""Dashboard insights and refresh routes."""

import json

from database import get_db
from flask import Blueprint, jsonify, request
from utils import stream_json

bp = Blueprint("dashboard", __name__)


@bp.route("/api/dashboard-insights")
def get_dashboard_insights():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM dashboard_insights ORDER BY type, priority"
    ).fetchall()
    conn.close()
    insights = {}
    for row in rows:
        r = dict(row)
        t = r["type"]
        if t not in insights:
            insights[t] = []
        insights[t].append(r)
    return stream_json(insights)


@bp.route("/api/dashboard-insights", methods=["POST"])
def update_dashboard_insights():
    data = request.get_json()
    conn = get_db()
    conn.execute("DELETE FROM dashboard_insights")
    for item_type, items in data.items():
        if isinstance(items, list):
            for i, item in enumerate(items):
                conn.execute(
                    """INSERT INTO dashboard_insights (type, icon, title, description, priority)
                    VALUES (?, ?, ?, ?, ?)""",
                    (
                        item_type,
                        item.get("icon", ""),
                        item.get("title", item.get("name", "")),
                        item.get(
                            "description", item.get("detail", item.get("note", ""))
                        ),
                        i,
                    ),
                )
    conn.commit()
    conn.close()
    return jsonify(
        {
            "status": "updated",
            "count": sum(len(v) for v in data.values() if isinstance(v, list)),
        }
    )


@bp.route("/api/tech-learning")
def get_tech_learning():
    conn = get_db()
    rows = conn.execute("SELECT * FROM tech_learning ORDER BY priority").fetchall()
    conn.close()
    return stream_json([dict(r) for r in rows])


@bp.route("/api/tech-learning", methods=["POST"])
def create_tech_learning():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "name is required"}), 400
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO tech_learning (name, priority, usage, reason, action) VALUES (?, ?, ?, ?, ?)",
        (
            data["name"],
            data.get("priority", 100),
            data.get("usage", 0),
            data.get("reason", ""),
            data.get("action", ""),
        ),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM tech_learning WHERE id=?", (cur.lastrowid,)
    ).fetchone()
    conn.close()
    return jsonify(dict(row)), 201


@bp.route("/api/tech-learning/<int:id>", methods=["PUT"])
def update_tech_learning(id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    conn = get_db()
    fields = []
    values = []
    for field in ["name", "priority", "usage", "reason", "action"]:
        if field in data:
            fields.append(f"{field}=?")
            values.append(data[field])
    if not fields:
        return jsonify({"error": "No valid fields to update"}), 400
    values.append(id)
    conn.execute(f"UPDATE tech_learning SET {','.join(fields)} WHERE id=?", values)
    conn.commit()
    row = conn.execute("SELECT * FROM tech_learning WHERE id=?", (id,)).fetchone()
    conn.close()
    if row:
        return jsonify(dict(row))
    return jsonify({"error": "Not found"}), 404


@bp.route("/api/tech-learning/<int:id>", methods=["DELETE"])
def delete_tech_learning(id):
    conn = get_db()
    conn.execute("DELETE FROM tech_learning WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})


@bp.route("/api/tech-stack")
def get_tech_stack():
    conn = get_db()
    rows = conn.execute("SELECT * FROM tech_stack ORDER BY level DESC").fetchall()
    conn.close()
    return stream_json([dict(r) for r in rows])


@bp.route("/api/tech-stack", methods=["POST"])
def create_tech_stack():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "name is required"}), 400
    conn = get_db()
    # Check if skill already exists
    existing = conn.execute(
        "SELECT id FROM tech_stack WHERE name=?", (data["name"],)
    ).fetchone()
    if existing:
        conn.close()
        return jsonify(
            {"id": existing[0], "name": data["name"], "message": "Skill already exists"}
        ), 200
    cur = conn.execute(
        "INSERT INTO tech_stack (name, level, roles, path, source) VALUES (?, ?, ?, ?, ?)",
        (
            data["name"],
            data.get("level", 1),
            data.get("roles", ""),
            data.get("path", ""),
            data.get("source", "user"),
        ),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM tech_stack WHERE id=?", (cur.lastrowid,)
    ).fetchone()
    conn.close()
    return jsonify(dict(row)), 201


@bp.route("/api/tech-stack/<int:id>", methods=["PUT"])
def update_tech_stack(id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    conn = get_db()
    fields = []
    values = []
    for field in ["name", "level", "roles", "path", "source"]:
        if field in data:
            fields.append(f"{field}=?")
            values.append(data[field])
    if not fields:
        return jsonify({"error": "No valid fields to update"}), 400
    values.append(id)
    conn.execute(f"UPDATE tech_stack SET {','.join(fields)} WHERE id=?", values)
    conn.commit()
    row = conn.execute("SELECT * FROM tech_stack WHERE id=?", (id,)).fetchone()
    conn.close()
    if row:
        return jsonify(dict(row))
    return jsonify({"error": "Not found"}), 404


@bp.route("/api/tech-stack/<int:id>", methods=["DELETE"])
def delete_tech_stack(id):
    conn = get_db()
    conn.execute("DELETE FROM tech_stack WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})


@bp.route("/api/cities")
def get_cities():
    conn = get_db()
    rows = conn.execute(
        "SELECT location, locations FROM jobs WHERE deleted=0"
    ).fetchall()
    conn.close()

    city_counts = {}
    for row in rows:
        r = dict(row)
        locations = []
        if r.get("locations"):
            try:
                locations = (
                    json.loads(r["locations"])
                    if isinstance(r["locations"], str)
                    else r["locations"]
                )
            except:
                pass
        if not locations and r.get("location"):
            locations = [r["location"]]
        for loc in locations:
            if loc and loc != "Not specified":
                city_counts[loc] = city_counts.get(loc, 0) + 1

    city_info = {
        "Berlin": {"icon": "🐻", "info": "Largest tech hub. 350K+ tech workers."},
        "Munich": {"icon": "🦁", "info": "Highest salaries. Enterprise & automotive."},
        "Hamburg": {"icon": "🎵", "info": "Growing tech scene. AdTech, energy."},
        "Heidelberg": {"icon": "🏛️", "info": "Enterprise AI startup scene."},
        "Frankfurt": {"icon": "🏦", "info": "FinTech capital. Banking infrastructure."},
        "Cologne": {"icon": "🗼", "info": "Media & commerce tech."},
        "Stuttgart": {"icon": "🏭", "info": "Engineering & automotive."},
        "Remote": {"icon": "🏠", "info": "Best for visa from Iran."},
        "Remote Germany": {"icon": "🏠", "info": "Best for visa from Iran."},
        "Germany": {"icon": "🇩🇪", "info": "Country-wide opportunities."},
    }

    total_jobs = len(city_counts)
    cities = []
    for city, count in sorted(city_counts.items(), key=lambda x: -x[1]):
        info = city_info.get(city, {"icon": "📍", "info": "Tech hub."})
        cities.append(
            {
                "icon": info["icon"],
                "name": city,
                "info": info["info"],
                "jobs": f"{count}/{total_jobs} jobs",
            }
        )

    return stream_json(cities)


@bp.route("/api/refresh/dashboard", methods=["POST"])
def refresh_dashboard():
    """Refresh dashboard — now delegates to career intelligence."""
    from services.career_intel import generate_all, is_running

    running, _ = is_running()
    if running:
        return jsonify({"status": "already_running"}), 409
    import threading

    threading.Thread(target=generate_all, daemon=True).start()
    return jsonify({"status": "started"})


@bp.route("/api/refresh/networking", methods=["POST"])
def refresh_networking():
    """Refresh networking — now delegates to career intelligence."""
    from services.career_intel import generate_section, is_running

    running, _ = is_running()
    if running:
        return jsonify({"status": "already_running"}), 409
    import threading

    threading.Thread(target=generate_section, args=("networking",), daemon=True).start()
    return jsonify({"status": "started"})


@bp.route("/api/refresh/skills", methods=["POST"])
def refresh_skills():
    """Refresh skills — now delegates to career intelligence."""
    from services.career_intel import generate_section, is_running

    running, _ = is_running()
    if running:
        return jsonify({"status": "already_running"}), 409
    import threading

    threading.Thread(target=generate_section, args=("skills",), daemon=True).start()
    return jsonify({"status": "started"})


@bp.route("/api/refresh/analysis", methods=["POST"])
def refresh_analysis():
    """Refresh all analysis — now delegates to career intelligence."""
    from services.career_intel import generate_all, is_running

    running, _ = is_running()
    if running:
        return jsonify({"status": "already_running"}), 409
    import threading

    threading.Thread(target=generate_all, daemon=True).start()
    return jsonify({"status": "started"})


# ═══════════════════════════════════════════════════════
# Skill Roadmaps — hierarchical learning tree per skill
# ═══════════════════════════════════════════════════════


def _build_roadmap_tree(rows):
    """Build a nested tree from flat roadmap rows."""
    by_id = {}
    roots = []
    for r in rows:
        r["children"] = []
        by_id[r["id"]] = r
    for r in rows:
        pid = r.get("parent_id")
        if pid and pid in by_id:
            by_id[pid]["children"].append(r)
        else:
            roots.append(r)
    return roots


@bp.route("/api/skill-roadmaps")
def get_skill_roadmaps():
    """Get roadmap tree for a skill. Query param: ?skill=<name>"""
    skill = request.args.get("skill", "")
    if not skill:
        return jsonify({"error": "skill param required"}), 400
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM skill_roadmaps WHERE skill_name=? ORDER BY version DESC, sort_order, id",
        (skill,),
    ).fetchall()
    conn.close()
    rows_data = [dict(r) for r in rows]
    # Get latest version
    if rows_data:
        max_version = max(t["version"] for t in rows_data)
        rows_data = [t for t in rows_data if t["version"] == max_version]
    tree = _build_roadmap_tree(rows_data)
    # Get latest created_at from this version
    updated_at = rows_data[0]["created_at"] if rows_data else None
    return jsonify(
        {
            "skill": skill,
            "version": rows_data[0]["version"] if rows_data else 0,
            "roadmap": tree,
            "updated_at": updated_at,
        }
    )


@bp.route("/api/skill-roadmaps", methods=["POST"])
def create_skill_roadmap():
    """Create a roadmap item. Accepts single or batch."""
    data = request.get_json()
    conn = get_db()
    created = []
    items = data if isinstance(data, list) else [data]
    for item in items:
        if not item.get("skill_name") or not item.get("title"):
            continue
        cur = conn.execute(
            "INSERT INTO skill_roadmaps (skill_name, parent_id, title, description, level, sort_order, version) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                item["skill_name"],
                item.get("parent_id"),
                item["title"],
                item.get("description", ""),
                item.get("level", 0),
                item.get("sort_order", 0),
                item.get("version", 1),
            ),
        )
        created.append(cur.lastrowid)
    conn.commit()
    conn.close()
    return jsonify({"created": len(created), "ids": created}), 201


@bp.route("/api/skill-roadmaps/<int:id>", methods=["PUT"])
def update_skill_roadmap(id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400
    conn = get_db()
    fields, values = [], []
    for f in ["title", "description", "sort_order", "parent_id"]:
        if f in data:
            fields.append(f"{f}=?")
            values.append(data[f])
    if fields:
        values.append(id)
        conn.execute(f"UPDATE skill_roadmaps SET {','.join(fields)} WHERE id=?", values)
        conn.commit()
    row = conn.execute("SELECT * FROM skill_roadmaps WHERE id=?", (id,)).fetchone()
    conn.close()
    return jsonify(dict(row)) if row else (jsonify({"error": "Not found"}), 404)


@bp.route("/api/skill-roadmaps/<int:id>", methods=["DELETE"])
def delete_skill_roadmap(id):
    conn = get_db()

    # Delete children recursively
    def _delete_children(parent_id):
        children = conn.execute(
            "SELECT id FROM skill_roadmaps WHERE parent_id=?", (parent_id,)
        ).fetchall()
        for c in children:
            _delete_children(c[0])
        conn.execute(
            "DELETE FROM skill_roadmap_progress WHERE roadmap_id=?", (parent_id,)
        )
        conn.execute("DELETE FROM skill_roadmaps WHERE id=?", (parent_id,))

    _delete_children(id)
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})


@bp.route("/api/skill-roadmaps/bulk", methods=["POST"])
def bulk_create_skill_roadmaps():
    """Replace all roadmap items for a skill with a new set. Used by AI generation."""
    data = request.get_json()
    skill = data.get("skill_name")
    roadmap_items = data.get("roadmap", data.get("roadmap", []))
    version = data.get("version", 1)
    if not skill:
        return jsonify({"error": "skill_name required"}), 400
    conn = get_db()
    # Get existing progress to preserve
    progress_rows = conn.execute(
        "SELECT roadmap_id, completed FROM skill_roadmap_progress WHERE skill_name=?",
        (skill,),
    ).fetchall()
    # Build title→completed map from old tree
    old_progress = {}
    for pr in progress_rows:
        roadmap_item = conn.execute(
            "SELECT title FROM skill_roadmaps WHERE id=?", (pr[0],)
        ).fetchone()
        if roadmap_item:
            old_progress[roadmap_item[0]] = pr[1]
    # Delete old roadmap items for this skill+version
    old_ids = [
        r[0]
        for r in conn.execute(
            "SELECT id FROM skill_roadmaps WHERE skill_name=? AND version=?",
            (skill, version),
        ).fetchall()
    ]
    for oid in old_ids:
        conn.execute("DELETE FROM skill_roadmap_progress WHERE roadmap_id=?", (oid,))
    conn.execute(
        "DELETE FROM skill_roadmaps WHERE skill_name=? AND version=?", (skill, version)
    )
    # Insert new roadmap items
    id_map = {}  # old client_id → new db_id
    created = []
    for i, t in enumerate(roadmap_items):
        cur = conn.execute(
            "INSERT INTO skill_roadmaps (skill_name, parent_id, title, description, level, sort_order, version) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                skill,
                None,
                t["title"],
                t.get("description", ""),
                t.get("level", 0),
                i,
                version,
            ),
        )
        new_id = cur.lastrowid
        id_map[i] = new_id
        created.append(new_id)
        # Re-apply progress if title matched
        if t["title"] in old_progress:
            conn.execute(
                "INSERT OR REPLACE INTO skill_roadmap_progress (roadmap_id, skill_name, completed) VALUES (?, ?, ?)",
                (new_id, skill, old_progress[t["title"]]),
            )
        # Insert children
        for j, child in enumerate(t.get("children", [])):
            cur2 = conn.execute(
                "INSERT INTO skill_roadmaps (skill_name, parent_id, title, description, level, sort_order, version) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    skill,
                    new_id,
                    child["title"],
                    child.get("description", ""),
                    child.get("level", t.get("level", 0)),
                    j,
                    version,
                ),
            )
            child_id = cur2.lastrowid
            if child["title"] in old_progress:
                conn.execute(
                    "INSERT OR REPLACE INTO skill_roadmap_progress (roadmap_id, skill_name, completed) VALUES (?, ?, ?)",
                    (child_id, skill, old_progress[child["title"]]),
                )
    conn.commit()
    conn.close()
    return jsonify({"created": len(created), "version": version})


@bp.route("/api/skill-roadmap-progress/<int:roadmap_id>", methods=["PUT"])
def update_roadmap_progress(roadmap_id):
    """Toggle roadmap item completion."""
    data = request.get_json() or {}
    completed = data.get("completed", 1)
    conn = get_db()
    # Get skill_name from roadmap item
    roadmap_item = conn.execute(
        "SELECT skill_name FROM skill_roadmaps WHERE id=?", (roadmap_id,)
    ).fetchone()
    if not roadmap_item:
        conn.close()
        return jsonify({"error": "Roadmap not found"}), 404
    conn.execute(
        'INSERT OR REPLACE INTO skill_roadmap_progress (roadmap_id, skill_name, completed, updated_at) VALUES (?, ?, ?, datetime("now"))',
        (roadmap_id, roadmap_item[0], completed),
    )
    conn.commit()
    conn.close()
    return jsonify(
        {"status": "updated", "roadmap_id": roadmap_id, "completed": completed}
    )


@bp.route("/api/skill-roadmap-progress")
def get_skill_progress():
    """Get progress for a skill's LATEST version only. Query: ?skill=<name>"""
    skill = request.args.get("skill", "")
    if not skill:
        return jsonify({"error": "skill param required"}), 400
    conn = get_db()
    # Get latest version
    max_ver = conn.execute(
        "SELECT COALESCE(MAX(version),0) FROM skill_roadmaps WHERE skill_name=?",
        (skill,),
    ).fetchone()[0]
    if max_ver == 0:
        conn.close()
        return jsonify({})
    # Only return progress for roadmap items in latest version
    rows = conn.execute(
        """SELECT tp.roadmap_id, tp.completed FROM skill_roadmap_progress tp
           JOIN skill_roadmaps st ON st.id = tp.roadmap_id
           WHERE tp.skill_name=? AND st.version=?""",
        (skill, max_ver),
    ).fetchall()
    conn.close()
    return jsonify({str(r[0]): r[1] for r in rows})


@bp.route("/api/skill-roadmap-progress/all")
def get_all_skill_progress():
    """Get progress summary for all skills — LATEST version only."""
    conn = get_db()
    skills = conn.execute("SELECT DISTINCT skill_name FROM skill_roadmaps").fetchall()
    result = {}
    for (skill_name,) in skills:
        max_ver = conn.execute(
            "SELECT MAX(version) FROM skill_roadmaps WHERE skill_name=?", (skill_name,)
        ).fetchone()[0]
        if not max_ver:
            continue
        # Get all roadmap IDs in latest version
        all_roadmap_items = conn.execute(
            "SELECT id, parent_id FROM skill_roadmaps WHERE skill_name=? AND version=?",
            (skill_name, max_ver),
        ).fetchall()
        parent_ids = {t[1] for t in all_roadmap_items if t[1] is not None}
        # Leaf nodes = items whose id is NOT a parent_id of any other item
        leaf_ids = [t[0] for t in all_roadmap_items if t[0] not in parent_ids]
        total = len(leaf_ids)
        if total == 0:
            continue
        # Count how many leaf nodes are completed
        done = 0
        if leaf_ids:
            placeholders = ",".join(["?"] * len(leaf_ids))
            row = conn.execute(
                f"SELECT COUNT(*) FROM skill_roadmap_progress WHERE skill_name=? AND roadmap_id IN ({placeholders}) AND completed=1",
                [skill_name] + leaf_ids,
            ).fetchone()
            done = row[0] or 0
        # Get source from tech_stack
        src_row = conn.execute(
            "SELECT source FROM tech_stack WHERE name=?", (skill_name,)
        ).fetchone()
        source = src_row[0] if src_row else "service"
        result[skill_name] = {
            "total": total,
            "completed": done,
            "pct": round((done / total) * 100),
            "source": source,
        }
    conn.close()
    return jsonify(result)


# ═══════════════════════════════════════════════════════
# Skill Roadmap Generation — background worker
# ═══════════════════════════════════════════════════════

import json as _json
import os as _os
import subprocess as _subprocess
import threading as _threading
from datetime import datetime as _datetime


def _update_skill_progress(skill, job_type="generate", **kwargs):
    """Update job progress in DB. Creates a new job row if none exists for this skill+type."""
    conn = get_db()
    # Find active job for this skill
    row = conn.execute(
        "SELECT id FROM skill_roadmap_jobs WHERE skill_name=? AND job_type=? AND status IN ('queued','running') ORDER BY id DESC LIMIT 1",
        (skill, job_type),
    ).fetchone()
    if row:
        fields, values = [], []
        for k, v in kwargs.items():
            fields.append(f"{k}=?")
            values.append(v)
        if fields:
            values.append(row[0])
            conn.execute(
                f"UPDATE skill_roadmap_jobs SET {','.join(fields)} WHERE id=?", values
            )
    else:
        cols = ["skill_name", "job_type"] + list(kwargs.keys())
        vals = [skill, job_type] + list(kwargs.values())
        placeholders = ",".join(["?"] * len(vals))
        conn.execute(
            f"INSERT INTO skill_roadmap_jobs ({','.join(cols)}) VALUES ({placeholders})",
            vals,
        )
    conn.commit()
    conn.close()


def _parse_mimo_session_id(stdout):
    """Extract sessionID from Mimo JSON stream output."""
    if not stdout:
        return None
    for line in stdout.decode("utf-8", errors="replace").split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            obj = _json.loads(line)
            sid = obj.get("sessionID")
            if sid:
                return sid
        except (_json.JSONDecodeError, AttributeError):
            continue
    return None


def _get_skill_progress(skill):
    """Get latest job progress for a skill from DB. Prioritize active/failed jobs."""
    conn = get_db()
    cols = "status, step, total_steps, message, version, count, error, session_id, pid, started_at, completed_at"
    # First check for active or failed jobs (these need to be shown ASAP)
    row = conn.execute(
        f"SELECT {cols} FROM skill_roadmap_jobs WHERE skill_name=? AND status IN ('queued','running','failed') ORDER BY id DESC LIMIT 1",
        (skill,),
    ).fetchone()
    if not row:
        # Fall back to latest completed job
        row = conn.execute(
            f"SELECT {cols} FROM skill_roadmap_jobs WHERE skill_name=? ORDER BY id DESC LIMIT 1",
            (skill,),
        ).fetchone()
    conn.close()
    if row:
        return {
            "status": row[0],
            "step": row[1],
            "total_steps": row[2],
            "message": row[3],
            "version": row[4],
            "count": row[5],
            "error": row[6],
            "session_id": row[7],
            "pid": row[8],
            "started_at": row[9],
            "completed_at": row[10],
        }
    return {"status": "idle", "step": 0, "total_steps": 4, "message": ""}


def _run_generate_worker(skill):
    """Background worker for roadmap generation."""
    from config import PROJECT_ROOT
    from prompts import load_prompt

    _tmp = _os.environ.get("TEMP_DIR", "tmp")
    TMP_DIR = _tmp if _os.path.isabs(_tmp) else _os.path.join(PROJECT_ROOT, _tmp)
    MIMO_BIN = _os.path.expanduser("~/.mimocode/bin/mimo")
    _update_skill_progress(
        skill,
        status="running",
        step=1,
        message="Preparing prompt",
        started_at=_datetime.now().isoformat(),
        error=None,
    )
    try:
        # Step 1: Get level
        _update_skill_progress(skill, step=1, message="Reading skill level")
        conn = get_db()
        row = conn.execute(
            "SELECT level FROM tech_stack WHERE name=?", (skill,)
        ).fetchone()
        conn.close()
        level_map = {
            1: "beginner",
            2: "beginner",
            3: "intermediate",
            4: "advanced",
            5: "expert",
        }
        current_level = level_map.get(row[0], "intermediate") if row else "intermediate"
        # Step 2: Build prompt
        _update_skill_progress(skill, step=2, message="Building AI prompt")
        prompt = load_prompt(
            "skill_roadmaps",
            project_root=PROJECT_ROOT,
            tmp_dir=TMP_DIR,
            pid=0,
            skill_name=skill,
            current_level=current_level,
            checked_items="none",
            growth_context="",
            task_instruction="Generate a comprehensive learning outline for this skill, ordered from basic to advanced.",
        )
        result_file = _os.path.join(TMP_DIR, "skill_roadmaps_0.json")
        # Step 3: Run AI
        _update_skill_progress(skill, step=3, message="AI is generating roadmap...")
        proc = _subprocess.Popen(
            [
                MIMO_BIN,
                "run",
                prompt,
                "--format",
                "json",
                "--dangerously-skip-permissions",
            ],
            cwd=PROJECT_ROOT,
            stdout=_subprocess.PIPE,
            stderr=_subprocess.PIPE,
            env={**_os.environ, "NO_COLOR": "1"},
        )
        # Save process ID for cancellation
        _update_skill_progress(skill, job_type="generate", pid=proc.pid)
        stdout, stderr = proc.communicate(timeout=180)
        # Parse session ID from output
        session_id = _parse_mimo_session_id(stdout)
        if session_id:
            _update_skill_progress(skill, job_type="generate", session_id=session_id)
        if proc.returncode == 0 and _os.path.exists(result_file):
            with open(result_file) as f:
                roadmap_data = _json.load(f)
            _os.remove(result_file)
            # Step 4: Save to DB
            _update_skill_progress(skill, step=4, message="Saving roadmap to database")
            conn = get_db()
            max_ver = conn.execute(
                "SELECT COALESCE(MAX(version),0) FROM skill_roadmaps WHERE skill_name=?",
                (skill,),
            ).fetchone()[0]
            new_version = max_ver + 1
            for i, t in enumerate(roadmap_data):
                cur = conn.execute(
                    "INSERT INTO skill_roadmaps (skill_name, parent_id, title, description, level, sort_order, version) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        skill,
                        None,
                        t["title"],
                        t.get("description", ""),
                        t.get("level", 0),
                        i,
                        new_version,
                    ),
                )
                parent_id = cur.lastrowid
                for j, child in enumerate(t.get("children", [])):
                    conn.execute(
                        "INSERT INTO skill_roadmaps (skill_name, parent_id, title, description, level, sort_order, version) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            skill,
                            parent_id,
                            child["title"],
                            child.get("description", ""),
                            child.get("level", t.get("level", 0)),
                            j,
                            new_version,
                        ),
                    )
            conn.commit()
            conn.close()
            _update_skill_progress(
                skill,
                status="completed",
                step=4,
                message="Done",
                completed_at=_datetime.now().isoformat(),
                version=new_version,
                count=len(roadmap_data),
            )
        else:
            err = (
                stderr[:500].decode("utf-8", errors="replace")
                if stderr
                else "Generation failed"
            )
            _update_skill_progress(
                skill,
                status="failed",
                error=err,
                completed_at=_datetime.now().isoformat(),
            )
    except Exception as e:
        _update_skill_progress(
            skill,
            status="failed",
            error=str(e),
            completed_at=_datetime.now().isoformat(),
        )


def _run_grow_worker(skill, mode="extend"):
    """Background worker for roadmap extending or fine-graining."""
    from config import PROJECT_ROOT
    from prompts import load_prompt

    _tmp = _os.environ.get("TEMP_DIR", "tmp")
    TMP_DIR = _tmp if _os.path.isabs(_tmp) else _os.path.join(PROJECT_ROOT, _tmp)
    MIMO_BIN = _os.path.expanduser("~/.mimocode/bin/mimo")
    action_label = "Extending" if mode == "extend" else "Fine-graining"
    _update_skill_progress(
        skill,
        job_type=mode,
        status="running",
        step=1,
        message=f"Preparing {action_label.lower()}",
        started_at=_datetime.now().isoformat(),
        error=None,
    )
    try:
        # Step 1: Get current tree + progress
        _update_skill_progress(skill, step=1, message="Reading current roadmap")
        conn = get_db()
        rows = conn.execute(
            "SELECT * FROM skill_roadmaps WHERE skill_name=? ORDER BY version DESC, sort_order, id",
            (skill,),
        ).fetchall()
        roadmap_rows = [dict(r) for r in rows]
        if roadmap_rows:
            max_version = max(t["version"] for t in roadmap_rows)
            roadmap_rows = [t for t in roadmap_rows if t["version"] == max_version]
        tree = _build_roadmap_tree_for_prompt(roadmap_rows)
        progress = conn.execute(
            "SELECT tp.roadmap_id, tp.completed, st.title FROM skill_roadmap_progress tp JOIN skill_roadmaps st ON st.id=tp.roadmap_id WHERE tp.skill_name=?",
            (skill,),
        ).fetchall()
        checked_titles = [p[2] for p in progress if p[1] == 1]
        row = conn.execute(
            "SELECT level FROM tech_stack WHERE name=?", (skill,)
        ).fetchone()
        conn.close()
        level_map = {
            1: "beginner",
            2: "beginner",
            3: "intermediate",
            4: "advanced",
            5: "expert",
        }
        current_level = level_map.get(row[0], "intermediate") if row else "intermediate"
        # Step 2: Build prompt
        _update_skill_progress(
            skill, job_type=mode, step=2, message="Building AI prompt"
        )
        growth_ctx = f"Existing roadmap tree:\n{_json.dumps(tree, indent=2)}\n\nUser has completed: {_json.dumps(checked_titles)}"
        if mode == "extend":
            task_instruction = "EXTEND this roadmap: Add NEW items that go beyond the current level range (add more advanced items at 80-100 if not covered). Also fill any important coverage gaps. Keep ALL existing items and their levels unchanged. The result should be a SUPERSET of the original."
            ai_msg = "AI is extending roadmap..."
        else:
            task_instruction = "FINE-GRAIN this roadmap: Split each broad item into 2-4 more specific child items. Keep ALL existing item titles as parents. Children should have sub-levels within the parent level. Make each item more specific and actionable for interview preparation."
            ai_msg = "AI is fine-graining roadmap..."
        prompt = load_prompt(
            "skill_roadmaps",
            project_root=PROJECT_ROOT,
            tmp_dir=TMP_DIR,
            pid=0,
            skill_name=skill,
            current_level=current_level,
            checked_items=_json.dumps(checked_titles),
            growth_context=growth_ctx,
            task_instruction=task_instruction,
        )
        result_file = _os.path.join(TMP_DIR, "skill_roadmaps_0.json")
        # Step 3: Run AI
        _update_skill_progress(skill, job_type=mode, step=3, message=ai_msg)
        proc = _subprocess.Popen(
            [
                MIMO_BIN,
                "run",
                prompt,
                "--format",
                "json",
                "--dangerously-skip-permissions",
            ],
            cwd=PROJECT_ROOT,
            stdout=_subprocess.PIPE,
            stderr=_subprocess.PIPE,
            env={**_os.environ, "NO_COLOR": "1"},
        )
        # Save process ID for cancellation
        _update_skill_progress(skill, job_type=mode, pid=proc.pid)
        stdout, stderr = proc.communicate(timeout=180)
        # Parse session ID from output
        session_id = _parse_mimo_session_id(stdout)
        if session_id:
            _update_skill_progress(skill, job_type=mode, session_id=session_id)
        if proc.returncode == 0 and _os.path.exists(result_file):
            with open(result_file) as f:
                new_roadmap_data = _json.load(f)
            _os.remove(result_file)
            # Step 4: Save with progress preservation
            _update_skill_progress(
                skill,
                job_type=mode,
                step=4,
                message=f"Saving {action_label.lower()}ed roadmap",
            )
            conn = get_db()
            max_ver = conn.execute(
                "SELECT COALESCE(MAX(version),0) FROM skill_roadmaps WHERE skill_name=?",
                (skill,),
            ).fetchone()[0]
            new_version = max_ver + 1
            for i, t in enumerate(new_roadmap_data):
                cur = conn.execute(
                    "INSERT INTO skill_roadmaps (skill_name, parent_id, title, description, level, sort_order, version) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        skill,
                        None,
                        t["title"],
                        t.get("description", ""),
                        t.get("level", 0),
                        i,
                        new_version,
                    ),
                )
                parent_id = cur.lastrowid
                if t["title"] in checked_titles:
                    conn.execute(
                        "INSERT OR REPLACE INTO skill_roadmap_progress (roadmap_id, skill_name, completed) VALUES (?, ?, 1)",
                        (parent_id, skill),
                    )
                for j, child in enumerate(t.get("children", [])):
                    cur2 = conn.execute(
                        "INSERT INTO skill_roadmaps (skill_name, parent_id, title, description, level, sort_order, version) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            skill,
                            parent_id,
                            child["title"],
                            child.get("description", ""),
                            child.get("level", t.get("level", 0)),
                            j,
                            new_version,
                        ),
                    )
                    if child["title"] in checked_titles:
                        conn.execute(
                            "INSERT OR REPLACE INTO skill_roadmap_progress (roadmap_id, skill_name, completed) VALUES (?, ?, 1)",
                            (cur2.lastrowid, skill),
                        )
            conn.commit()
            conn.close()
            _update_skill_progress(
                skill,
                job_type=mode,
                status="completed",
                step=4,
                message="Done",
                completed_at=_datetime.now().isoformat(),
                version=new_version,
                count=len(new_roadmap_data),
            )
        else:
            err = (
                stderr[:500].decode("utf-8", errors="replace")
                if stderr
                else f"{action_label} failed"
            )
            _update_skill_progress(
                skill,
                job_type=mode,
                status="failed",
                error=err,
                completed_at=_datetime.now().isoformat(),
            )
    except Exception as e:
        _update_skill_progress(
            skill,
            status="failed",
            error=str(e),
            completed_at=_datetime.now().isoformat(),
        )


@bp.route("/api/skill-roadmaps/generate", methods=["POST"])
def generate_skill_roadmaps():
    """Start background roadmap generation for a skill."""
    data = request.get_json() or {}
    skill = data.get("skill_name", "")
    if not skill:
        return jsonify({"error": "skill_name required"}), 400
    # Check if already running or queued
    current_status = _get_skill_progress(skill).get("status", "idle")
    if current_status in ("running", "queued"):
        return jsonify({"status": "already_running"}), 409
    _update_skill_progress(
        skill,
        status="queued",
        step=0,
        message="Queued",
        started_at=None,
        completed_at=None,
        error=None,
    )
    t = _threading.Thread(target=_run_generate_worker, args=(skill,), daemon=True)
    t.start()
    return jsonify({"status": "started", "skill": skill})


@bp.route("/api/skill-roadmaps/extend", methods=["POST"])
def extend_skill_roadmaps():
    """Start background roadmap extension — adds more items beyond current range."""
    data = request.get_json() or {}
    skill = data.get("skill_name", "")
    if not skill:
        return jsonify({"error": "skill_name required"}), 400
    current_status = _get_skill_progress(skill).get("status", "idle")
    if current_status in ("running", "queued"):
        return jsonify({"status": "already_running"}), 409
    _update_skill_progress(
        skill,
        job_type="extend",
        status="queued",
        step=0,
        message="Queued",
        started_at=None,
        completed_at=None,
        error=None,
    )
    t = _threading.Thread(target=_run_grow_worker, args=(skill, "extend"), daemon=True)
    t.start()
    return jsonify({"status": "started", "skill": skill})


@bp.route("/api/skill-roadmaps/finegrain", methods=["POST"])
def finegrain_skill_roadmaps():
    """Start background fine-graining — splits existing roadmap items into more specific ones."""
    data = request.get_json() or {}
    skill = data.get("skill_name", "")
    if not skill:
        return jsonify({"error": "skill_name required"}), 400
    current_status = _get_skill_progress(skill).get("status", "idle")
    if current_status in ("running", "queued"):
        return jsonify({"status": "already_running"}), 409
    _update_skill_progress(
        skill,
        job_type="finegrain",
        status="queued",
        step=0,
        message="Queued",
        started_at=None,
        completed_at=None,
        error=None,
    )
    t = _threading.Thread(
        target=_run_grow_worker, args=(skill, "finegrain"), daemon=True
    )
    t.start()
    return jsonify({"status": "started", "skill": skill})


@bp.route("/api/skill-roadmaps/cancel", methods=["POST"])
def cancel_skill_gen():
    """Cancel or force-clear stuck generation for a skill."""
    skill = request.args.get("skill", "")
    if not skill:
        return jsonify({"error": "skill param required"}), 400
    # Try to kill the process if still running
    conn = get_db()
    row = conn.execute(
        "SELECT pid FROM skill_roadmap_jobs WHERE skill_name=? AND status IN ('running','queued') ORDER BY id DESC LIMIT 1",
        (skill,),
    ).fetchone()
    conn.close()
    if row and row[0]:
        try:
            import os as _os_signal

            _os_signal.kill(row[0], 9)  # SIGKILL
        except (ProcessLookupError, PermissionError):
            pass
    # Mark as cancelled in DB
    _update_skill_progress(
        skill,
        status="cancelled",
        message="Cancelled by user",
        completed_at=_datetime.now().isoformat(),
    )
    return jsonify({"status": "cancelled", "skill": skill})


@bp.route("/api/skill-roadmaps/progress")
def get_skill_gen_progress():
    """Get generation progress for a skill. Query: ?skill=<name>"""
    skill = request.args.get("skill", "")
    if not skill:
        return jsonify({"error": "skill param required"}), 400
    return jsonify(_get_skill_progress(skill))


def _build_roadmap_tree_for_prompt(rows):
    """Build tree for prompt context (simplified)."""
    by_id = {}
    roots = []
    for r in rows:
        r["children"] = []
        by_id[r["id"]] = r
    for r in rows:
        pid = r.get("parent_id")
        if pid and pid in by_id:
            by_id[pid]["children"].append(r)
        else:
            roots.append(r)
    return [
        {
            "title": r["title"],
            "description": r.get("description", ""),
            "children": [
                {"title": c["title"], "description": c.get("description", "")}
                for c in r["children"]
            ],
        }
        for r in roots
    ]
