"""Company processing queue endpoints."""

import sqlite3

from fastapi import APIRouter, Depends

from dependencies import get_db
from exceptions import NotFoundError

router = APIRouter()


@router.get("")
def list_pending_companies(db=Depends(get_db)):
    """List pending companies."""
    rows = db.execute(
        "SELECT * FROM pending_companies WHERE status != 'done' ORDER BY created_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


@router.post("")
def create_pending_company(data: dict, db=Depends(get_db)):
    """Queue a new company for processing."""
    cur = db.execute(
        "INSERT INTO pending_companies (input_text, input_type, source, status, notes) VALUES (?, ?, ?, ?, ?)",
        (data.get("name", data.get("input_text", "")), data.get("input_type", "url"), data.get("source", "api"), "pending", data.get("notes", "[]")),
    )
    db.commit()
    row = db.execute("SELECT * FROM pending_companies WHERE id=?", (cur.lastrowid,)).fetchone()
    return dict(row)


@router.get("/{id}")
def get_pending_company(id: str, db=Depends(get_db)):
    """Get a pending company."""
    row = db.execute("SELECT * FROM pending_companies WHERE id=?", (id,)).fetchone()
    if not row:
        raise NotFoundError(f"Pending company {id} not found")
    return dict(row)


@router.delete("/{id}")
def cancel_pending_company(id: str, db=Depends(get_db)):
    """Cancel a pending company."""
    from core.queue import get_queue_manager
    get_queue_manager().cancel_job(id, "pending_companies")
    return {"status": "cancelled", "id": id}


@router.post("/{id}/notes")
def add_company_notes(id: str, data: dict, db=Depends(get_db)):
    """Add notes to a pending company."""
    existing = db.execute("SELECT notes FROM pending_companies WHERE id=?", (id,)).fetchone()
    if not existing:
        raise NotFoundError(f"Pending company {id} not found")
    import json
    notes = json.loads(existing[0]) if existing[0] else []
    notes.append(data.get("note", ""))
    db.execute("UPDATE pending_companies SET notes=? WHERE id=?", (json.dumps(notes), id))
    db.commit()
    return {"status": "updated"}


@router.post("/{id}/links")
def add_company_links(id: str, data: dict, db=Depends(get_db)):
    """Add links to a pending company."""
    existing = db.execute("SELECT links FROM pending_companies WHERE id=?", (id,)).fetchone()
    if not existing:
        raise NotFoundError(f"Pending company {id} not found")
    import json
    links = json.loads(existing[0]) if existing[0] else []
    links.append(data.get("link", ""))
    db.execute("UPDATE pending_companies SET links=? WHERE id=?", (json.dumps(links), id))
    db.commit()
    return {"status": "updated"}
