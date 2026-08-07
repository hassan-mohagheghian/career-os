from __future__ import annotations

from enum import Enum


class ExecutionType(str, Enum):
    JOB_PROCESSING = "job_processing"
    COMPANY_PROCESSING = "company_processing"
    COVER_LETTER_GENERATION = "cover_letter_generation"
    RESUME_GENERATION = "resume_generation"
    RESUME_OPTIMIZATION = "resume_optimization"
    COMPANY_ANALYSIS = "company_analysis"
    MARKET_ANALYSIS = "market_analysis"
    CAREER_INSIGHTS = "career_insights"
    CANDIDATE_PROCESSING = "candidate_processing"


class ExecutionStatus(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    STARTING = "starting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
