"""PendingJob entity — aggregate root for the Pending (Queue) bounded context."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shared.domain.entity import BaseEntity


class PendingJob(BaseEntity):
    """Pending job queue entry."""

    def __init__(
        self,
        id: int | None = None,
        url: str | None = None,
        source: str = "cli",
        status: str = "queued",
        version: int = 1,
        notes: str = "[]",
        links: str = "[]",
        step_fetch: int = 0,
        step_analyze: int = 0,
        step_resume: int = 0,
        step_cover: int = 0,
        step_db: int = 0,
        step_done: int = 0,
        job_num: int | None = None,
        company: str | None = None,
        error: str | None = None,
        workflow_log: str = "[]",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        queue_order: int = 0,
        step_extract_raw: int = 0,
        step_extract_struct: int = 0,
        session_id: str | None = None,
    ):
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.url = url
        self.source = source
        self.status = status
        self.version = version
        self.notes = notes
        self.links = links
        self.step_fetch = step_fetch
        self.step_analyze = step_analyze
        self.step_resume = step_resume
        self.step_cover = step_cover
        self.step_db = step_db
        self.step_done = step_done
        self.job_num = job_num
        self.company = company
        self.error = error
        self.workflow_log = workflow_log
        self.queue_order = queue_order
        self.step_extract_raw = step_extract_raw
        self.step_extract_struct = step_extract_struct
        self.session_id = session_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "url": self.url,
            "source": self.source,
            "status": self.status,
            "version": self.version,
            "notes": self.notes,
            "links": self.links,
            "step_fetch": self.step_fetch,
            "step_analyze": self.step_analyze,
            "step_resume": self.step_resume,
            "step_cover": self.step_cover,
            "step_db": self.step_db,
            "step_done": self.step_done,
            "job_num": self.job_num,
            "company": self.company,
            "error": self.error,
            "workflow_log": self.workflow_log,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "queue_order": self.queue_order,
            "step_extract_raw": self.step_extract_raw,
            "step_extract_struct": self.step_extract_struct,
            "session_id": self.session_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PendingJob:
        return cls(
            id=data.get("id"),
            url=data.get("url"),
            source=data.get("source", "cli"),
            status=data.get("status", "queued"),
            version=data.get("version", 1),
            notes=data.get("notes", "[]"),
            links=data.get("links", "[]"),
            step_fetch=data.get("step_fetch", 0),
            step_analyze=data.get("step_analyze", 0),
            step_resume=data.get("step_resume", 0),
            step_cover=data.get("step_cover", 0),
            step_db=data.get("step_db", 0),
            step_done=data.get("step_done", 0),
            job_num=data.get("job_num"),
            company=data.get("company"),
            error=data.get("error"),
            workflow_log=data.get("workflow_log", "[]"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            queue_order=data.get("queue_order", 0),
            step_extract_raw=data.get("step_extract_raw", 0),
            step_extract_struct=data.get("step_extract_struct", 0),
            session_id=data.get("session_id"),
        )
