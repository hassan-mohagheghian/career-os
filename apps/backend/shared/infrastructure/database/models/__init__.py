"""SQLAlchemy ORM models package.

All models are exported here for easy import and Alembic auto-discovery.
Uses lazy imports to avoid circular dependencies.
"""


# Eager import to register models with Base.metadata for Alembic autogeneration
from processing.infrastructure.models import processing_execution_model  # noqa: F401
from jobs.infrastructure.models.job_analysis_model import JobAnalysisModel  # noqa: F401


def __getattr__(name: str):
    _models = {
        "JobModel": ("jobs.infrastructure.models.job_model", "JobModel"),
        "SkillModel": ("skills.infrastructure.models.skill_model", "SkillModel"),
        "SkillAliasModel": ("skills.infrastructure.models.skill_model", "SkillAliasModel"),
        "SkillRelationshipModel": ("skills.infrastructure.models.skill_model", "SkillRelationshipModel"),
        "CompanyModel": ("companies.infrastructure.models.company_model", "CompanyModel"),
        "CompanyIntelligenceModel": ("companies.infrastructure.models.company_model", "CompanyIntelligenceModel"),
        "CompanyLinkModel": ("companies.infrastructure.models.company_model", "CompanyLinkModel"),

        "SummaryModel": ("shared.infrastructure.database.models.misc_models", "SummaryModel"),
        "ResumeModel": ("shared.infrastructure.database.models.misc_models", "ResumeModel"),
        "SkillRoadmapModel": ("shared.infrastructure.database.models.misc_models", "SkillRoadmapModel"),
        "SkillRoadmapProgressModel": ("shared.infrastructure.database.models.misc_models", "SkillRoadmapProgressModel"),
        "SkillRoadmapJobModel": ("shared.infrastructure.database.models.misc_models", "SkillRoadmapJobModel"),
        "RuleModel": ("shared.infrastructure.database.models.misc_models", "RuleModel"),

        "CityModel": ("shared.infrastructure.database.models.misc_models", "CityModel"),

        "LLMConfigurationModel": ("ai.infrastructure.models.llm_configuration_model", "LLMConfigurationModel"),

        "ProcessingExecutionModel": ("processing.infrastructure.models.processing_execution_model", "ProcessingExecutionModel"),
    }
    if name in _models:
        module_path, attr = _models[name]
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "JobModel", "SkillModel", "SkillAliasModel", "SkillRelationshipModel",
    "CompanyModel", "CompanyIntelligenceModel", "CompanyLinkModel",
    "SummaryModel", "ResumeModel", "SkillRoadmapModel", "SkillRoadmapProgressModel",
    "SkillRoadmapJobModel", "RuleModel", "CityModel",
    "LLMConfigurationModel",
    "ProcessingExecutionModel",
]
