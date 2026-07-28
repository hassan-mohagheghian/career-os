from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class JobExtractionInput(BaseModel):
    content: str = Field(..., description="Raw job posting content", min_length=1)


class JobScoreInput(BaseModel):
    title: str = Field(default="", description="Job title")
    company: str = Field(default="", description="Company name")
    location: str = Field(default="", description="Job location")
    stack: str = Field(default="", description="Required tech stack")
    description: str = Field(default="", description="Job description")
    user_skills: str = Field(default="", description="User's skills")
    user_experience: str = Field(default="", description="User's experience")
    user_preferences: str = Field(default="", description="User's preferences")


class JobSummaryInput(BaseModel):
    title: str = Field(default="", description="Job title")
    company: str = Field(default="", description="Company name")
    location: str = Field(default="", description="Job location")
    stack: str = Field(default="", description="Required tech stack")
    description: str = Field(default="", description="Job description")
    requirements: str = Field(default="", description="Job requirements")
    benefits: str = Field(default="", description="Benefits offered")


class CompanyExtractionInput(BaseModel):
    content: str = Field(..., description="Raw company content", min_length=1)


class CompanyAnalysisInput(BaseModel):
    name: str = Field(default="", description="Company name")
    company_type: str = Field(default="", description="Company type")
    industry: str = Field(default="", description="Industry sector")
    size: str = Field(default="", description="Company size")
    location: str = Field(default="", description="Company location")
    tech_stack: str = Field(default="", description="Technologies used")
    visa_sponsorship: str = Field(default="", description="Visa sponsorship status")


class ResumeTailorInput(BaseModel):
    job_title: str = Field(default="", description="Job title")
    job_company: str = Field(default="", description="Company name")
    job_requirements: str = Field(default="", description="Job requirements")
    job_stack: str = Field(default="", description="Required tech stack")
    resume_text: str = Field(default="", description="Original resume text")


class CoverLetterInput(BaseModel):
    job_title: str = Field(default="", description="Job title")
    job_company: str = Field(default="", description="Company name")
    job_description: str = Field(default="", description="Job description")
    job_requirements: str = Field(default="", description="Job requirements")
    resume_text: str = Field(default="", description="Candidate's resume")


class SkillExtractionInput(BaseModel):
    job_data: str = Field(default="", description="Job posting data")


class RoadmapInput(BaseModel):
    current_skills: str = Field(default="", description="Current skills")
    market_demand: str = Field(default="", description="Market demand data")


class CareerInsightsInput(BaseModel):
    job_count: str = Field(default="0", description="Total jobs tracked")
    skill_count: str = Field(default="0", description="Total skills")
    health_score: str = Field(default="0", description="Career health score")
