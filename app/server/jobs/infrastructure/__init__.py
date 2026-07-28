"""Jobs infrastructure — lazy imports to avoid circular dependencies."""


def __getattr__(name: str):
    _exports = {
        "JobModel": ("jobs.infrastructure.models.job_model", "JobModel"),
        "SummaryModel": ("shared.infrastructure.database.models.misc_models", "SummaryModel"),
        "SQLAlchemyJobRepository": ("jobs.infrastructure.repositories.sa_job_repository", "SQLAlchemyJobRepository"),
        "job_model_to_dict": ("shared.infrastructure.database.mappers", "job_model_to_dict"),
        "dict_to_job_model": ("shared.infrastructure.database.mappers", "dict_to_job_model"),
    }
    if name in _exports:
        module_path, attr = _exports[name]
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "JobModel", "SummaryModel", "SQLAlchemyJobRepository",
    "job_model_to_dict", "dict_to_job_model",
]
