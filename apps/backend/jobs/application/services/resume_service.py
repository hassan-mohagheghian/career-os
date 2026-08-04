"""ResumeService — application service for uploading user profile documents.

Handles the creation of versioned resume (`original_N`) and LinkedIn
(`linkedin_N`) rows. Both are stored with PII masked (matching the Resume page's
privacy claim) and an HTML `content` preview built from the raw text.
"""

from __future__ import annotations

from typing import Any

from jobs.domain.repositories.resume_repository import IResumeRepository
from shared.infrastructure.utils import mask_pii, text_to_html

ORIGINAL_PREFIX = "original"
LINKEDIN_PREFIX = "linkedin"


class ResumeService:
    def __init__(self, resume_repo: IResumeRepository):
        self._resumes = resume_repo

    def upload_resume(self, raw_text: str, title: str | None = None) -> dict[str, Any]:
        """Save a new master resume as the next `original_*` version."""
        version = self._resumes.get_next_version(ORIGINAL_PREFIX)
        resume_id = f"{ORIGINAL_PREFIX}_{version}"
        data = self._resumes.upsert({
            "id": resume_id,
            "title": title or f"Resume v{version}",
            "company": "",
            "role": "",
            "version": version,
            "raw_text": mask_pii(raw_text),
            "content": text_to_html(raw_text),
        })
        return {"status": "saved", "version": data.get("version", version), "id": data.get("id", resume_id)}

    def upload_linkedin(self, raw_text: str) -> dict[str, Any]:
        """Save a new LinkedIn profile as the next `linkedin_*` version."""
        version = self._resumes.get_next_version(LINKEDIN_PREFIX)
        profile_id = f"{LINKEDIN_PREFIX}_{version}"
        data = self._resumes.upsert({
            "id": profile_id,
            "title": f"LinkedIn Profile v{version}",
            "company": "",
            "role": "",
            "version": version,
            "raw_text": mask_pii(raw_text),
            "content": text_to_html(raw_text),
        })
        return {"status": "saved", "version": data.get("version", version), "id": data.get("id", profile_id)}
