"""Company CRUD, intelligence, notes, links."""

import sqlite3

from fastapi import APIRouter, Depends

from dependencies import get_db
from infrastructure.database.company_repository import CompanyRepository
from exceptions import NotFoundError

router = APIRouter()


def _get_repo(db: sqlite3.Connection = Depends(get_db)) -> CompanyRepository:
    return CompanyRepository(db)


@router.get("")
def list_companies(repo: CompanyRepository = Depends(_get_repo)):
    """List all companies."""
    return repo.list_all()


@router.get("/{id}")
def get_company(id: int, db: sqlite3.Connection = Depends(get_db)):
    """Get a company by ID with intelligence and linked jobs."""
    import json
    row = db.execute("SELECT * FROM companies WHERE id=?", (id,)).fetchone()
    if not row:
        raise NotFoundError(f"Company {id} not found")
    company = dict(row)

    # Attach intelligence (parse JSON fields)
    intel_row = db.execute("SELECT * FROM company_intelligence WHERE company_id=?", (id,)).fetchone()
    if intel_row:
        intel = dict(intel_row)
        for field in ["overview", "culture_analysis", "international_analysis", "career_analysis",
                       "benefits_analysis", "visa_analysis", "technology_analysis", "recommendation",
                       "scores", "raw_source_data"]:
            if intel.get(field) and isinstance(intel[field], str):
                try:
                    intel[field] = json.loads(intel[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        company["intelligence"] = intel
    else:
        company["intelligence"] = None

    # Attach linked jobs
    jobs = db.execute(
        "SELECT num, company, role, location, match, score, fit_score, success_score, overall_score FROM jobs WHERE company_id=? AND deleted=0",
        (id,),
    ).fetchall()
    company["jobs"] = [dict(j) for j in jobs]

    return company


@router.post("")
def create_company(data: dict, repo: CompanyRepository = Depends(_get_repo)):
    """Create a new company."""
    return repo.create(data)


@router.put("/{id}")
def update_company(id: int, data: dict, repo: CompanyRepository = Depends(_get_repo)):
    """Update a company."""
    company = repo.update(id, data)
    if not company:
        raise NotFoundError(f"Company {id} not found")
    return company


@router.delete("/{id}")
def delete_company(id: int, repo: CompanyRepository = Depends(_get_repo)):
    """Delete a company."""
    repo.delete(id)
    return {"status": "deleted", "id": id}


@router.get("/{id}/intelligence")
def get_company_intelligence(id: int, db: sqlite3.Connection = Depends(get_db)):
    """Get company intelligence."""
    import json
    row = db.execute("SELECT * FROM company_intelligence WHERE company_id=?", (id,)).fetchone()
    if not row:
        return {"company_id": id, "overview": None}
    intel = dict(row)
    for field in ["overview", "culture_analysis", "international_analysis", "career_analysis",
                   "benefits_analysis", "visa_analysis", "technology_analysis", "recommendation",
                   "scores", "raw_source_data"]:
        if intel.get(field) and isinstance(intel[field], str):
            try:
                intel[field] = json.loads(intel[field])
            except (json.JSONDecodeError, TypeError):
                pass
    return intel


@router.get("/{id}/jobs")
def get_company_jobs(id: int, db: sqlite3.Connection = Depends(get_db)):
    """Get jobs linked to this company."""
    rows = db.execute(
        "SELECT * FROM jobs WHERE company_id=? AND deleted=0 ORDER BY created_at DESC",
        (id,),
    ).fetchall()
    return [dict(r) for r in rows]


@router.get("/{id}/links")
def get_company_links(id: int, db: sqlite3.Connection = Depends(get_db)):
    """Get all links for a company."""
    rows = db.execute("SELECT * FROM company_links WHERE company_id=?", (id,)).fetchall()
    return [dict(r) for r in rows]


@router.post("/{id}/links")
def add_company_link(id: int, data: dict, db: sqlite3.Connection = Depends(get_db)):
    """Add a link to a company."""
    cur = db.execute(
        "INSERT INTO company_links (company_id, url, title, description) VALUES (?, ?, ?, ?)",
        (id, data.get("url", ""), data.get("title", ""), data.get("description", "")),
    )
    db.commit()
    row = db.execute("SELECT * FROM company_links WHERE id=?", (cur.lastrowid,)).fetchone()
    return dict(row)


@router.delete("/{id}/links/{link_id}")
def delete_company_link(id: int, link_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Delete a company link."""
    db.execute("DELETE FROM company_links WHERE id=? AND company_id=?", (link_id, id))
    db.commit()
    return {"status": "deleted"}


@router.post("/{id}/notes")
def add_note(id: int, data: dict, db: sqlite3.Connection = Depends(get_db)):
    """Add a note to a company."""
    content = data.get("content", "")
    db.execute(
        "INSERT INTO company_links (company_id, url, title) VALUES (?, ?, ?)",
        (id, "", f"note:{content}"),
    )
    db.commit()
    return {"status": "created"}


@router.get("/{id}/notes")
def get_company_notes(id: int, db: sqlite3.Connection = Depends(get_db)):
    """Get all notes for a company."""
    rows = db.execute(
        "SELECT * FROM company_links WHERE company_id=? AND title LIKE 'note:%'",
        (id,),
    ).fetchall()
    return [dict(r) for r in rows]


@router.delete("/{id}/notes/{note_id}")
def delete_company_note(id: int, note_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Delete a company note."""
    db.execute("DELETE FROM company_links WHERE id=? AND company_id=?", (note_id, id))
    db.commit()
    return {"status": "deleted"}
