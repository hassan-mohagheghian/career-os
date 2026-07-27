"""Company processing queue endpoints."""

import json
import sqlite3

from fastapi import APIRouter, Depends

from dependencies import get_db
from exceptions import NotFoundError

router = APIRouter()


@router.get("")
def list_pending_companies(db=Depends(get_db)):
    """List pending companies (pending, queued, processing, failed)."""
    rows = db.execute(
        "SELECT * FROM pending_companies WHERE status != 'done' ORDER BY created_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


@router.post("")
def create_pending_company(data: dict, db=Depends(get_db)):
    """Create a pending company and enqueue for processing.

    Accepts:
      - notes: list of {type, content} (url or text)
      - links: list of {url, title}
      - input_text: fallback single text/url
      - source: origin string
    """
    notes = data.get("notes", [])
    links = data.get("links", [])

    all_notes = list(notes)
    for link in links:
        url = link.get("url", link) if isinstance(link, dict) else str(link)
        title = link.get("title", "") if isinstance(link, dict) else ""
        all_notes.append({"type": "url", "content": url, "title": title})

    input_text = data.get("input_text", data.get("name", ""))
    if not input_text and all_notes:
        input_text = all_notes[0].get("content", "")

    cur = db.execute(
        "INSERT INTO pending_companies (input_text, input_type, source, status, notes) VALUES (?, ?, ?, ?, ?)",
        (
            input_text,
            data.get("input_type", "url"),
            data.get("source", "web"),
            "pending",
            json.dumps(all_notes),
        ),
    )
    db.commit()
    pid = cur.lastrowid

    from core.queue import get_queue_manager
    get_queue_manager().enqueue(pid, table='pending_companies')

    row = db.execute("SELECT * FROM pending_companies WHERE id=?", (pid,)).fetchone()
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
    notes = json.loads(existing[0]) if existing[0] else []
    note_content = data.get("note", "")
    note_type = data.get("note_type", "text")
    if note_content:
        notes.append({"type": note_type, "content": note_content})
    db.execute("UPDATE pending_companies SET notes=? WHERE id=?", (json.dumps(notes), id))
    db.commit()
    return {"status": "updated"}


@router.post("/{id}/links")
def add_company_links(id: str, data: dict, db=Depends(get_db)):
    """Add links to a pending company (stored as url-type notes)."""
    existing = db.execute("SELECT notes FROM pending_companies WHERE id=?", (id,)).fetchone()
    if not existing:
        raise NotFoundError(f"Pending company {id} not found")
    notes = json.loads(existing[0]) if existing[0] else []
    links = data.get("links", [])
    for link in links:
        url = link.get("url", link) if isinstance(link, dict) else str(link)
        title = link.get("title", "") if isinstance(link, dict) else ""
        notes.append({"type": "url", "content": url, "title": title})
    db.execute("UPDATE pending_companies SET notes=? WHERE id=?", (json.dumps(notes), id))
    db.commit()
    return {"status": "updated"}
