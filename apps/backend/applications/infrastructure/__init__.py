"""Applications infrastructure — lazy imports to avoid circular dependencies."""


def __getattr__(name: str):
    _exports = {
        "ApplicationModel": ("applications.infrastructure.models.application_model", "ApplicationModel"),
        "ApplicationStatusEventModel": ("applications.infrastructure.models.application_model", "ApplicationStatusEventModel"),
        "ApplicationFollowUpModel": ("applications.infrastructure.models.application_model", "ApplicationFollowUpModel"),
        "ApplicationDocumentModel": ("applications.infrastructure.models.application_model", "ApplicationDocumentModel"),
        "SQLAlchemyApplicationRepository": ("applications.infrastructure.repositories.sa_application_repository", "SQLAlchemyApplicationRepository"),
        "SQLAlchemyStatusEventRepository": ("applications.infrastructure.repositories.sa_status_event_repository", "SQLAlchemyStatusEventRepository"),
        "SQLAlchemyFollowUpRepository": ("applications.infrastructure.repositories.sa_follow_up_repository", "SQLAlchemyFollowUpRepository"),
        "SQLAlchemyDocumentRepository": ("applications.infrastructure.repositories.sa_document_repository", "SQLAlchemyDocumentRepository"),
    }
    if name in _exports:
        module_path, attr = _exports[name]
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "ApplicationModel",
    "ApplicationStatusEventModel",
    "ApplicationFollowUpModel",
    "ApplicationDocumentModel",
    "SQLAlchemyApplicationRepository",
    "SQLAlchemyStatusEventRepository",
    "SQLAlchemyFollowUpRepository",
    "SQLAlchemyDocumentRepository",
]
