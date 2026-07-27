"""Scoring rules endpoints."""

from fastapi import APIRouter, Depends

from dependencies import get_db

router = APIRouter()


@router.get("")
def get_rules(db=Depends(get_db)):
    """Get all scoring rules grouped by scope."""
    rows = db.execute("SELECT * FROM preferences ORDER BY priority DESC").fetchall()
    grouped = {}
    for row in rows:
        r = dict(row)
        scope = r.get("scope", "SHARED")
        grouped.setdefault(scope, []).append(r)
    return grouped


@router.put("/{id}")
def update_rule(id: int, data: dict, db=Depends(get_db)):
    """Update a single rule."""
    fields = []
    values = []
    for field in ["value", "description", "score_weight", "priority", "enabled", "scope", "category", "key"]:
        if field in data:
            fields.append(f"{field}=?")
            values.append(data[field])
    if fields:
        values.append(id)
        db.execute(f"UPDATE preferences SET {','.join(fields)} WHERE id=?", values)
        db.commit()
    return {"status": "updated"}


@router.post("")
def create_rule(data: dict, db=Depends(get_db)):
    """Create a new rule."""
    rules = data.get("rules", [data])
    for rule in rules:
        db.execute(
            "INSERT INTO preferences (category, rule_type, scope, key, value, description, priority, score_weight, enabled) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                rule.get("category", "fit"),
                rule.get("rule_type", "job"),
                rule.get("scope", "JOB"),
                rule.get("key", ""),
                rule.get("value", ""),
                rule.get("description", ""),
                rule.get("priority", 50),
                rule.get("score_weight", 50),
                rule.get("enabled", 1),
            ),
        )
    db.commit()
    return {"status": "created"}


@router.delete("/{id}")
def delete_rule(id: int, db=Depends(get_db)):
    """Delete a rule."""
    db.execute("DELETE FROM preferences WHERE id=?", (id,))
    db.commit()
    return {"status": "deleted"}


@router.put("")
def bulk_update_rules(data: dict, db=Depends(get_db)):
    """Bulk update rules (e.g. reordering priorities)."""
    rules = data.get("rules", [])
    for rule in rules:
        if "id" in rule:
            db.execute(
                "UPDATE preferences SET value=?, score_weight=?, enabled=?, priority=?, scope=? WHERE id=?",
                (rule.get("value"), rule.get("score_weight", 0), rule.get("enabled", 1), rule.get("priority", 50), rule.get("scope", "JOB"), rule["id"]),
            )
    db.commit()
    return {"status": "updated"}
