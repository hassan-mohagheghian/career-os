"""SQLAlchemy ORM models package.

All models are exported here for easy import and Alembic auto-discovery.
Uses lazy imports to avoid circular dependencies.
"""


def __getattr__(name: str):
    _models = {
        "JobModel": ("jobs.infrastructure.models.job_model", "JobModel"),
        "SkillModel": ("skills.infrastructure.models.skill_model", "SkillModel"),
        "SkillAliasModel": ("skills.infrastructure.models.skill_model", "SkillAliasModel"),
        "SkillRelationshipModel": ("skills.infrastructure.models.skill_model", "SkillRelationshipModel"),
        "CompanyModel": ("companies.infrastructure.models.company_model", "CompanyModel"),
        "CompanyIntelligenceModel": ("companies.infrastructure.models.company_model", "CompanyIntelligenceModel"),
        "CompanyLinkModel": ("companies.infrastructure.models.company_model", "CompanyLinkModel"),
        "PendingJobModel": ("pending.infrastructure.models.pending_model", "PendingJobModel"),
        "PendingCompanyModel": ("pending.infrastructure.models.pending_model", "PendingCompanyModel"),
        "PendingGenerationModel": ("pending.infrastructure.models.pending_model", "PendingGenerationModel"),
        "CareerInsightModel": ("career.infrastructure.models.insight_model", "CareerInsightModel"),
        "CareerInsightRunModel": ("career.infrastructure.models.insight_model", "CareerInsightRunModel"),
        "SummaryModel": ("shared.infrastructure.database.models.misc_models", "SummaryModel"),
        "ResumeModel": ("shared.infrastructure.database.models.misc_models", "ResumeModel"),
        "SkillRoadmapModel": ("shared.infrastructure.database.models.misc_models", "SkillRoadmapModel"),
        "SkillRoadmapProgressModel": ("shared.infrastructure.database.models.misc_models", "SkillRoadmapProgressModel"),
        "SkillRoadmapJobModel": ("shared.infrastructure.database.models.misc_models", "SkillRoadmapJobModel"),
        "PreferenceModel": ("shared.infrastructure.database.models.misc_models", "PreferenceModel"),
        "DashboardInsightModel": ("shared.infrastructure.database.models.misc_models", "DashboardInsightModel"),
        "AnalysisRunModel": ("shared.infrastructure.database.models.misc_models", "AnalysisRunModel"),
        "TechLearningModel": ("shared.infrastructure.database.models.misc_models", "TechLearningModel"),
        "CityModel": ("shared.infrastructure.database.models.misc_models", "CityModel"),
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
    "PendingJobModel", "PendingCompanyModel", "PendingGenerationModel",
    "CareerInsightModel", "CareerInsightRunModel",
    "SummaryModel", "ResumeModel", "SkillRoadmapModel", "SkillRoadmapProgressModel",
    "SkillRoadmapJobModel", "PreferenceModel", "DashboardInsightModel",
    "AnalysisRunModel", "TechLearningModel", "CityModel",
]
