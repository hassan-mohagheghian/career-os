"""Resume infrastructure — lazy imports to avoid circular dependencies."""


def __getattr__(name: str):
    _exports = {
        "ResumeModel": ("shared.infrastructure.database.models.misc_models", "ResumeModel"),
        "SQLAlchemyResumeRepository": ("resume.infrastructure.repositories.sa_resume_repository", "SQLAlchemyResumeRepository"),
        "resume_model_to_dict": ("shared.infrastructure.database.mappers", "resume_model_to_dict"),
    }
    if name in _exports:
        module_path, attr = _exports[name]
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["ResumeModel", "SQLAlchemyResumeRepository", "resume_model_to_dict"]
