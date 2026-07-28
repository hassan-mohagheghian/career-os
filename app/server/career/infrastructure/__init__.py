"""Career infrastructure — lazy imports to avoid circular dependencies."""


def __getattr__(name: str):
    _exports = {
        "CareerInsightModel": ("career.infrastructure.models.insight_model", "CareerInsightModel"),
        "CareerInsightRunModel": ("career.infrastructure.models.insight_model", "CareerInsightRunModel"),
        "PreferenceModel": ("shared.infrastructure.database.models.misc_models", "PreferenceModel"),
        "DashboardInsightModel": ("shared.infrastructure.database.models.misc_models", "DashboardInsightModel"),
        "AnalysisRunModel": ("shared.infrastructure.database.models.misc_models", "AnalysisRunModel"),
        "SQLAlchemyInsightRepository": ("career.infrastructure.repositories.sa_insight_repository", "SQLAlchemyInsightRepository"),
        "SQLAlchemyCareerInsightRepository": ("career.infrastructure.repositories.sa_career_insight_repository", "SQLAlchemyCareerInsightRepository"),
        "SQLAlchemyCareerInsightRunRepository": ("career.infrastructure.repositories.sa_career_insight_run_repository", "SQLAlchemyCareerInsightRunRepository"),
        "SQLAlchemyPreferenceRepository": ("career.infrastructure.repositories.sa_preference_repository", "SQLAlchemyPreferenceRepository"),
        "career_insight_model_to_dict": ("shared.infrastructure.database.mappers", "career_insight_model_to_dict"),
        "career_insight_run_model_to_dict": ("shared.infrastructure.database.mappers", "career_insight_run_model_to_dict"),
    }
    if name in _exports:
        module_path, attr = _exports[name]
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "CareerInsightModel", "CareerInsightRunModel", "PreferenceModel",
    "DashboardInsightModel", "AnalysisRunModel",
    "SQLAlchemyInsightRepository", "SQLAlchemyCareerInsightRepository",
    "SQLAlchemyCareerInsightRunRepository", "SQLAlchemyPreferenceRepository",
    "career_insight_model_to_dict", "career_insight_run_model_to_dict",
]
