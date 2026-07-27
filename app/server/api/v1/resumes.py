"""Resume/cover letter generation endpoints."""

from fastapi import APIRouter, Depends

from dependencies import get_db
from exceptions import NotFoundError

router = APIRouter()


@router.get("")
def list_resumes(db=Depends(get_db)):
    """List all resumes."""
    rows = db.execute("SELECT * FROM resumes ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


@router.get("/active-generations")
def get_active_generations(db=Depends(get_db)):
    """Get any active (queued/processing) resume or cover generations."""
    rows = db.execute(
        "SELECT id, job_num, type, status, step_prepare, step_context, "
        "step_generate, step_save, step_done, error "
        "FROM pending_generations WHERE status IN ('queued', 'processing') "
        "ORDER BY created_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


@router.get("/{id}")
def get_resume(id: str, db=Depends(get_db)):
    """Get a resume by ID."""
    row = db.execute("SELECT * FROM resumes WHERE id=?", (id,)).fetchone()
    if not row:
        raise NotFoundError(f"Resume {id} not found")
    return dict(row)


@router.post("")
def create_resume(data: dict, db=Depends(get_db)):
    """Create a new resume."""
    import uuid
    resume_id = f"resume_{uuid.uuid4().hex[:8]}"
    db.execute(
        "INSERT INTO resumes (id, title, content) VALUES (?, ?, ?)",
        (resume_id, data.get("title", "Original"), data.get("content", "")),
    )
    db.commit()
    row = db.execute("SELECT * FROM resumes WHERE id=?", (resume_id,)).fetchone()
    return dict(row)


@router.put("/{id}")
def update_resume(id: str, data: dict, db=Depends(get_db)):
    """Update a resume."""
    row = db.execute("SELECT * FROM resumes WHERE id=?", (id,)).fetchone()
    if not row:
        raise NotFoundError(f"Resume {id} not found")

    fields = []
    values = []
    for field in ["title", "content"]:
        if field in data:
            fields.append(f"{field}=?")
            values.append(data[field])

    if fields:
        values.append(id)
        db.execute(f"UPDATE resumes SET {','.join(fields)} WHERE id=?", values)
        db.commit()

    row = db.execute("SELECT * FROM resumes WHERE id=?", (id,)).fetchone()
    return dict(row)


@router.delete("/{id}")
def delete_resume(id: str, db=Depends(get_db)):
    """Delete a resume."""
    db.execute("DELETE FROM resumes WHERE id=?", (id,))
    db.commit()
    return {"status": "deleted", "id": id}


@router.post("/{id}/generate-cover")
def generate_cover_letter(id: str, data: dict, db=Depends(get_db)):
    """Generate a cover letter for a job."""
    return {"status": "started", "resume_id": id, "job_num": data.get("job_num")}
