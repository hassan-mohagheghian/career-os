"""Rules infrastructure — lazy imports to avoid circular dependencies."""


def __getattr__(name: str):
    _exports = {
        "RuleModel": ("rules.infrastructure.models.rule_model", "RuleModel"),
        "SQLAlchemyRuleRepository": ("rules.infrastructure.repositories.sa_rule_repository", "SQLAlchemyRuleRepository"),
    }
    if name in _exports:
        module_path, attr = _exports[name]
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "RuleModel",
    "SQLAlchemyRuleRepository",
]
