"""Pending infrastructure — lazy imports to avoid circular dependencies."""


def __getattr__(name: str):
    _exports = {
        "PendingJobModel": ("pending.infrastructure.models.pending_model", "PendingJobModel"),
        "PendingCompanyModel": ("pending.infrastructure.models.pending_model", "PendingCompanyModel"),
        "PendingGenerationModel": ("pending.infrastructure.models.pending_model", "PendingGenerationModel"),
        "SQLAlchemyPendingRepository": ("pending.infrastructure.repositories.sa_pending_repository", "SQLAlchemyPendingRepository"),
        "SQLAlchemyPendingGenerationRepository": ("pending.infrastructure.repositories.sa_pending_generation_repository", "SQLAlchemyPendingGenerationRepository"),
        "pending_job_model_to_dict": ("shared.infrastructure.database.mappers", "pending_job_model_to_dict"),
        "pending_company_model_to_dict": ("shared.infrastructure.database.mappers", "pending_company_model_to_dict"),
    }
    if name in _exports:
        module_path, attr = _exports[name]
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "PendingJobModel", "PendingCompanyModel", "PendingGenerationModel",
    "SQLAlchemyPendingRepository", "SQLAlchemyPendingGenerationRepository",
    "pending_job_model_to_dict", "pending_company_model_to_dict",
]
