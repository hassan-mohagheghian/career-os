"""Dashboard insights and refresh routes."""

import json
import sqlite3

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

