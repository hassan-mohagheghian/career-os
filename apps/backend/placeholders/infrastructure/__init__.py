"""Placeholders infrastructure — lazy imports to avoid circular dependencies."""


def __getattr__(name: str):
    _exports = {
        "PlaceholderModel": (
            "placeholders.infrastructure.models.placeholder_model",
            "PlaceholderModel",
        ),
        "SQLAlchemyPlaceholderRepository": (
            "placeholders.infrastructure.repositories.sa_placeholder_repository",
            "SQLAlchemyPlaceholderRepository",
        ),
    }
    if name in _exports:
        module_path, attr = _exports[name]
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "PlaceholderModel",
    "SQLAlchemyPlaceholderRepository",
]