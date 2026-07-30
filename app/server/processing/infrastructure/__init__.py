def __getattr__(name: str):
    _exports = {
        "ProcessingExecutionModel": ("processing.infrastructure.models.processing_execution_model", "ProcessingExecutionModel"),
        "SQLAlchemyProcessingExecutionRepository": ("processing.infrastructure.repositories.sa_processing_execution_repository", "SQLAlchemyProcessingExecutionRepository"),
    }
    if name in _exports:
        module_path, attr = _exports[name]
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "ProcessingExecutionModel",
    "SQLAlchemyProcessingExecutionRepository",
]
