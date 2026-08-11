from __future__ import annotations

from enum import Enum


class ExecutionType(str, Enum):
    JOB_PROCESSING = "job_processing"
    COMPANY_PROCESSING = "company_processing"
    COMPANY_ANALYSIS = "company_analysis"
    MARKET_ANALYSIS = "market_analysis"
    CAREER_INSIGHTS = "career_insights"
    CANDIDATE_PROCESSING = "candidate_processing"
    APPLICATION_PREPARATION = "application_preparation"
    APPLICATION_RESUME = "application_resume"
    APPLICATION_COVER_LETTER = "application_cover_letter"


class ExecutionStatus(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    STARTING = "starting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
