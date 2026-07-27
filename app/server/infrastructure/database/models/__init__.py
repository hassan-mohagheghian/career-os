"""SQLAlchemy ORM models package.

All models are exported here for easy import and Alembic auto-discovery.
"""

from infrastructure.database.models.job_model import JobModel
from infrastructure.database.models.skill_model import SkillModel, SkillAliasModel, SkillRelationshipModel
from infrastructure.database.models.company_model import CompanyModel, CompanyIntelligenceModel, CompanyLinkModel
from infrastructure.database.models.pending_model import PendingJobModel, PendingCompanyModel, PendingGenerationModel
from infrastructure.database.models.insight_model import CareerInsightModel, CareerInsightRunModel
from infrastructure.database.models.misc_models import (
    SummaryModel,
    ResumeModel,
    SkillRoadmapModel,
    SkillRoadmapProgressModel,
    SkillRoadmapJobModel,
    PreferenceModel,
    DashboardInsightModel,
    AnalysisRunModel,
    TechLearningModel,
    CityModel,
)

__all__ = [
    "JobModel",
    "SkillModel",
    "SkillAliasModel",
    "SkillRelationshipModel",
    "CompanyModel",
    "CompanyIntelligenceModel",
    "CompanyLinkModel",
    "PendingJobModel",
    "PendingCompanyModel",
    "PendingGenerationModel",
    "CareerInsightModel",
    "CareerInsightRunModel",
    "SummaryModel",
    "ResumeModel",
    "SkillRoadmapModel",
    "SkillRoadmapProgressModel",
    "SkillRoadmapJobModel",
    "PreferenceModel",
    "DashboardInsightModel",
    "AnalysisRunModel",
    "TechLearningModel",
    "CityModel",
]
