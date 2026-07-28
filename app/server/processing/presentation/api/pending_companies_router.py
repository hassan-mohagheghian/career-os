"""Company processing queue endpoints."""

import json

from fastapi import APIRouter, Depends

from dependencies import get_pending_repo
from processing.infrastructure import SQLAlchemyPendingRepository
from shared.application.exceptions import NotFoundError

router = APIRouter()


@router.get("")
def list_pending_companies(repo: SQLAlchemyPendingRepository = Depends(get_pending_repo)):
    """List pending companies (pending, queued, processing, failed)."""
    return repo.list_pending("pending_companies")


@router.post("")
def create_pending_company(data: dict, repo: SQLAlchemyPendingRepository = Depends(get_pending_repo)):
    """Create a pending company and enqueue for processing."""
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

    result = repo.create_pending_company(
        input_text=input_text,
        input_type=data.get("input_type", "url"),
        source=data.get("source", "web"),
        status="pending",
        notes=json.dumps(all_notes),
    )
    pid = result["id"]

    from shared.infrastructure.config.queue import get_queue_manager
    get_queue_manager().enqueue(pid, table='pending_companies')

    return repo.get_by_id(str(pid), "pending_companies")


@router.get("/{id}")
def get_pending_company(id: str, repo: SQLAlchemyPendingRepository = Depends(get_pending_repo)):
    """Get a pending company."""
    item = repo.get_by_id(id, "pending_companies")
    if not item:
        raise NotFoundError(f"Pending company {id} not found")
    return item


@router.delete("/{id}")
def delete_pending_company(id: str, repo: SQLAlchemyPendingRepository = Depends(get_pending_repo)):
    """Delete a pending company."""
    repo.delete(int(id), "pending_companies")
    return {"status": "deleted", "id": id}


@router.post("/{id}/notes")
def add_company_notes(id: str, data: dict, repo: SQLAlchemyPendingRepository = Depends(get_pending_repo)):
    """Add notes to a pending company."""
    existing = repo.get_by_id(id, "pending_companies")
    if not existing:
        raise NotFoundError(f"Pending company {id} not found")
    notes = json.loads(existing.get("notes", "[]") or "[]")
    note_content = data.get("note", "")
    note_type = data.get("note_type", "text")
    if note_content:
        notes.append({"type": note_type, "content": note_content})
    repo.update_fields(int(id), table="pending_companies", notes=json.dumps(notes))
    return {"status": "updated"}


@router.post("/{id}/links")
def add_company_links(id: str, data: dict, repo: SQLAlchemyPendingRepository = Depends(get_pending_repo)):
    """Add links to a pending company."""
    existing = repo.get_by_id(id, "pending_companies")
    if not existing:
        raise NotFoundError(f"Pending company {id} not found")
    notes = json.loads(existing.get("notes", "[]") or "[]")
    links = data.get("links", [])
    for link in links:
        url = link.get("url", link) if isinstance(link, dict) else str(link)
        title = link.get("title", "") if isinstance(link, dict) else ""
        notes.append({"type": "url", "content": url, "title": title})
    repo.update_fields(int(id), table="pending_companies", notes=json.dumps(notes))
    return {"status": "updated"}
