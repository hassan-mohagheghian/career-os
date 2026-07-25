"""Tech stack CRUD, skill relationships, merge, hide/restore."""

import json
import sqlite3

from database import get_db
from flask import Blueprint, jsonify, request
from utils import stream_json

bp = Blueprint("tech_stack", __name__)


@bp.route("/api/tech-stack")
def get_tech_stack():
    """Get visible skills with aliases and tags.
    ---
    tags: [Skills]
    parameters:
      - name: category
        in: query
        type: string
        enum: [technical, engineering, professional, domain, career]
        description: Filter by skill category
    responses:
      200:
        description: List of visible skills
    """
    conn = get_db()
    category = request.args.get("category", "")
    if category:
        rows = conn.execute("SELECT * FROM tech_stack WHERE hidden=0 AND category=? ORDER BY level DESC", (category,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM tech_stack WHERE hidden=0 ORDER BY level DESC").fetchall()
    # Attach aliases to each skill
    result = []
    for row in rows:
        skill_dict = dict(row)
        aliases = conn.execute("SELECT alias_name FROM skill_aliases WHERE skill_id=?", (row['id'],)).fetchall()
        skill_dict['aliases'] = [a[0] for a in aliases]
        # Parse tags from JSON string to array
        import json as _json
        try:
            skill_dict['tags'] = _json.loads(skill_dict.get('tags', '[]') or '[]')
        except (ValueError, TypeError):
            skill_dict['tags'] = []
        result.append(skill_dict)
    conn.close()
    return stream_json(result)


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
    # Tags stored as JSON string
    if "tags" in data:
        import json as _json
        fields.append("tags=?")
        values.append(_json.dumps(data["tags"]) if isinstance(data["tags"], list) else data["tags"])
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


@bp.route("/api/tech-stack/<int:id>/rename", methods=["PATCH"])
def rename_skill(id):
    """Rename a skill and update all references."""
    data = request.get_json() or {}
    new_name = data.get("name", "").strip()
    if not new_name:
        return jsonify({"error": "name is required"}), 400
    conn = get_db()
    old = conn.execute("SELECT name FROM tech_stack WHERE id=?", (id,)).fetchone()
    if not old:
        conn.close()
        return jsonify({"error": "Not found"}), 404
    old_name = old[0]
    if old_name == new_name:
        conn.close()
        return jsonify({"status": "unchanged"})
    # Check for duplicates
    exists = conn.execute("SELECT id FROM tech_stack WHERE name=? AND id!=?", (new_name, id)).fetchone()
    if exists:
        conn.close()
        return jsonify({"error": f'Skill "{new_name}" already exists'}), 409
    # Rename across all tables
    conn.execute("UPDATE tech_stack SET name=? WHERE id=?", (new_name, id))
    conn.execute("UPDATE skill_roadmaps SET skill_name=? WHERE skill_name=?", (new_name, old_name))
    conn.execute("UPDATE skill_roadmap_progress SET skill_name=? WHERE skill_name=?", (new_name, old_name))
    conn.execute("UPDATE skill_roadmap_jobs SET skill_name=? WHERE skill_name=?", (new_name, old_name))
    # Update aliases pointing to this skill
    conn.execute("UPDATE skill_aliases SET alias_name=? WHERE alias_name=? AND skill_id=?", (new_name, old_name, id))
    conn.commit()
    row = conn.execute("SELECT * FROM tech_stack WHERE id=?", (id,)).fetchone()
    conn.close()
    return jsonify(dict(row))


@bp.route("/api/tech-stack/<int:id>", methods=["DELETE"])
def delete_tech_stack(id):
    """Delete a skill and all its aliases."""
    conn = get_db()
    skill = conn.execute("SELECT name FROM tech_stack WHERE id=?", (id,)).fetchone()
    if not skill:
        conn.close()
        return jsonify({"error": "Not found"}), 404
    skill_name = skill[0]
    # Delete aliases pointing to this skill
    aliases = conn.execute("SELECT alias_name FROM skill_aliases WHERE skill_id=?", (id,)).fetchall()
    alias_names = [a[0] for a in aliases]
    conn.execute("DELETE FROM skill_aliases WHERE skill_id=?", (id,))
    # Delete the skill itself
    conn.execute("DELETE FROM tech_stack WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted", "name": skill_name, "aliases_deleted": alias_names})


@bp.route("/api/tech-stack/<int:id>/hide", methods=["PATCH"])
def toggle_hide_skill(id):
    """Toggle hidden flag on a skill."""
    data = request.get_json() or {}
    hidden = data.get("hidden", 1)
    conn = get_db()
    conn.execute("UPDATE tech_stack SET hidden=? WHERE id=?", (hidden, id))
    conn.commit()
    row = conn.execute("SELECT * FROM tech_stack WHERE id=?", (id,)).fetchone()
    conn.close()
    if row:
        return jsonify(dict(row))
    return jsonify({"error": "Not found"}), 404


@bp.route("/api/tech-stack/merge", methods=["POST"])
def merge_skills():
    """Merge source skills into target skill.

    Target stays in tech_stack as canonical. Source skills become aliases in skill_aliases.
    """
    data = request.get_json() or {}
    target_id = data.get("target_id")
    source_ids = data.get("source_ids", [])
    if not target_id or not source_ids:
        return jsonify({"error": "target_id and source_ids required"}), 400

    conn = get_db()
    target = conn.execute("SELECT name FROM tech_stack WHERE id=?", (target_id,)).fetchone()
    if not target:
        conn.close()
        return jsonify({"error": "Target skill not found"}), 404
    target_name = target[0]

    merged = []
    for sid in source_ids:
        source = conn.execute("SELECT name FROM tech_stack WHERE id=?", (sid,)).fetchone()
        if not source or source[0] == target_name:
            continue
        source_name = source[0]
        # Rename across all tables
        conn.execute("UPDATE skill_roadmaps SET skill_name=? WHERE skill_name=?", (target_name, source_name))
        conn.execute("UPDATE skill_roadmap_progress SET skill_name=? WHERE skill_name=?", (target_name, source_name))
        conn.execute("UPDATE skill_roadmap_jobs SET skill_name=? WHERE skill_name=?", (target_name, source_name))
        # Create alias record
        existing = conn.execute("SELECT id FROM skill_aliases WHERE skill_id=? AND alias_name=?", (target_id, source_name)).fetchone()
        if not existing:
            conn.execute("INSERT INTO skill_aliases (skill_id, alias_name, normalized_name) VALUES (?, ?, ?)",
                (target_id, source_name, source_name.lower()))
        # Hide the source skill (keep it but don't show in main list)
        conn.execute("UPDATE tech_stack SET hidden=1 WHERE id=?", (sid,))
        merged.append(source_name)

    conn.commit()
    # Get all aliases for this skill
    aliases = conn.execute("SELECT alias_name FROM skill_aliases WHERE skill_id=?", (target_id,)).fetchall()
    row = conn.execute("SELECT * FROM tech_stack WHERE id=?", (target_id,)).fetchone()
    conn.close()
    return jsonify({
        "status": "merged", "target": dict(row) if row else None,
        "merged": merged, "aliases": [a[0] for a in aliases]
    })


@bp.route("/api/tech-stack/hidden")
def get_hidden_skills():
    """List all hidden skills."""
    conn = get_db()
    rows = conn.execute("SELECT * FROM tech_stack WHERE hidden=1 ORDER BY name").fetchall()
    conn.close()
    import json as _json
    result = []
    for r in rows:
        d = dict(r)
        try:
            d['tags'] = _json.loads(d.get('tags', '[]') or '[]')
        except (ValueError, TypeError):
            d['tags'] = []
        result.append(d)
    return stream_json(result)


@bp.route("/api/tech-stack/<int:id>/restore", methods=["PATCH"])
def restore_skill(id):
    """Restore a hidden skill (unhide it)."""
    conn = get_db()
    conn.execute("UPDATE tech_stack SET hidden=0 WHERE id=?", (id,))
    conn.commit()
    row = conn.execute("SELECT * FROM tech_stack WHERE id=?", (id,)).fetchone()
    conn.close()
    if row:
        return jsonify(dict(row))
    return jsonify({"error": "Not found"}), 404


@bp.route("/api/skill-relationships/<skill_name>")
def get_skill_relationships(skill_name):
    """Get all relationships for a skill."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM skill_relationships WHERE skill_name=? OR related_name=?",
        (skill_name, skill_name)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@bp.route("/api/skill-relationships", methods=["POST"])
def create_skill_relationship():
    """Create a skill relationship."""
    data = request.get_json() or {}
    skill = data.get("skill_name")
    related = data.get("related_name")
    rel_type = data.get("relation_type")
    confidence = data.get("confidence", 0)
    if not skill or not related or not rel_type:
        return jsonify({"error": "skill_name, related_name, relation_type required"}), 400
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO skill_relationships (skill_name, related_name, relation_type, confidence) VALUES (?, ?, ?, ?)",
            (skill, related, rel_type, confidence)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Relationship already exists"}), 409
    conn.close()
    return jsonify({"status": "created"}), 201


@bp.route("/api/skill-relationships/<int:id>", methods=["DELETE"])
def delete_skill_relationship(id):
    """Delete a skill relationship."""
    conn = get_db()
    conn.execute("DELETE FROM skill_relationships WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})

