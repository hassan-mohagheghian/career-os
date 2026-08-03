"""Summary entity — value object for job summary data."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Summary:
    """Job summary value object.

    Stores a compact summary of a job for quick display.
    Uses `job_id` (job UUID) as the key.
    """

    job_id: str
    company: str | None = None
    match: str | None = None
    score: str | None = None
    summary: str | None = None
    stack: str | None = None
    resume_fit: str | None = None
    note: str | None = None
    url: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> Summary:
        return cls(
            job_id=data["job_id"],
            company=data.get("company"),
            match=data.get("match"),
            score=data.get("score"),
            summary=data.get("summary"),
            stack=data.get("stack"),
            resume_fit=data.get("resumeFit"),
            note=data.get("note"),
            url=data.get("url"),
        )

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "company": self.company,
            "match": self.match,
            "score": self.score,
            "summary": self.summary,
            "stack": self.stack,
            "resumeFit": self.resume_fit,
            "note": self.note,
            "url": self.url,
        }
