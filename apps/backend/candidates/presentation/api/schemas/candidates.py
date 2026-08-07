"""Pydantic schemas for the Candidate API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class CandidateProfileResponse(BaseModel):
    id: str | None = None
    candidate_id: str | None = None
    version: int | None = None
    name: str = ""
    title: str = ""
    headline: str = ""
    summary: str = ""
    location: str = ""
    skills: list[dict[str, Any]] = []
    experiences: list[dict[str, Any]] = []
    projects: list[dict[str, Any]] = []
    educations: list[dict[str, Any]] = []
    certificates: list[dict[str, Any]] = []
    interests: list[dict[str, Any]] = []
    languages: list[dict[str, Any]] = []
    created_at: str | None = None
    updated_at: str | None = None


class CandidateSourceListResponse(BaseModel):
    items: list[dict[str, Any]]


class CandidateVersionListResponse(BaseModel):
    items: list[dict[str, Any]]


class CandidateAnalyzeResponse(BaseModel):
    execution_id: str
    status: str
