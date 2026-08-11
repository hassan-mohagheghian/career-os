"""Applications infrastructure — lazy imports to avoid circular dependencies."""


def __getattr__(name: str):
    _exports = {
        "ApplicationModel": ("applications.infrastructure.models.application_model", "ApplicationModel"),
        "ApplicationFollowUpModel": ("applications.infrastructure.models.application_model", "ApplicationFollowUpModel"),
        "ApplicationDocumentModel": ("applications.infrastructure.models.application_model", "ApplicationDocumentModel"),
        "ApplicationPreparationModel": ("applications.infrastructure.models.application_model", "ApplicationPreparationModel"),
        "SQLAlchemyApplicationRepository": ("applications.infrastructure.repositories.sa_application_repository", "SQLAlchemyApplicationRepository"),
        "SQLAlchemyFollowUpRepository": ("applications.infrastructure.repositories.sa_follow_up_repository", "SQLAlchemyFollowUpRepository"),
        "SQLAlchemyDocumentRepository": ("applications.infrastructure.repositories.sa_document_repository", "SQLAlchemyDocumentRepository"),
        "SQLAlchemyPreparationRepository": ("applications.infrastructure.repositories.sa_preparation_repository", "SQLAlchemyPreparationRepository"),
    }
    if name in _exports:
        module_path, attr = _exports[name]
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "ApplicationModel",
    "ApplicationFollowUpModel",
    "ApplicationDocumentModel",
    "ApplicationPreparationModel",
    "SQLAlchemyApplicationRepository",
    "SQLAlchemyFollowUpRepository",
    "SQLAlchemyDocumentRepository",
    "SQLAlchemyPreparationRepository",
]
