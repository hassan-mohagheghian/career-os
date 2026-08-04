"""Jobs infrastructure — lazy imports to avoid circular dependencies."""


def __getattr__(name: str):
    _exports = {
        "JobModel": ("jobs.infrastructure.models.job_model", "JobModel"),
        "SummaryModel": ("jobs.infrastructure.models.misc_models", "SummaryModel"),
        "SQLAlchemyJobRepository": ("jobs.infrastructure.repositories.sa_job_repository", "SQLAlchemyJobRepository"),
        "SQLAlchemySummaryRepository": ("jobs.infrastructure.repositories.sa_summary_repository", "SQLAlchemySummaryRepository"),
        "SQLAlchemyResumeRepository": ("jobs.infrastructure.repositories.sa_resume_repository", "SQLAlchemyResumeRepository"),
        "SQLAlchemyTailoredDocumentRepository": ("jobs.infrastructure.repositories.sa_tailored_document_repository", "SQLAlchemyTailoredDocumentRepository"),
        "SQLAlchemyJobAnalysisRepository": ("jobs.infrastructure.repositories.sa_job_analysis_repository", "SQLAlchemyJobAnalysisRepository"),
        "job_model_to_dict": ("jobs.infrastructure.mappers", "job_model_to_dict"),
        "dict_to_job_model": ("jobs.infrastructure.mappers", "dict_to_job_model"),
        "process_job": ("jobs.infrastructure.workers.worker", "process_job"),
        "process_generation": ("jobs.infrastructure.workers.generation_worker", "process_generation"),
    }
    if name in _exports:
        module_path, attr = _exports[name]
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "JobModel", "SummaryModel", "SQLAlchemyJobRepository", "SQLAlchemySummaryRepository",
    "SQLAlchemyResumeRepository", "SQLAlchemyTailoredDocumentRepository", "SQLAlchemyJobAnalysisRepository",
    "job_model_to_dict", "dict_to_job_model", "process_job", "process_generation",
]
