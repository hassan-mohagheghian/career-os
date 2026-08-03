"""Tailored document schemas for request/response validation."""

from pydantic import BaseModel


class TailoredDocumentCreate(BaseModel):
    title: str = "Original"
    content: str = ""


class TailoredDocumentUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


class TailoredDocumentResponse(BaseModel):
    id: str
    title: str | None = None
    content: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"from_attributes": True}


class GenerateCoverRequest(BaseModel):
    job_id: str
    resume_id: str = "original"
    tone: str = "professional"


class CoverLetterResponse(BaseModel):
    id: str
    content: str
    created_at: str | None = None
