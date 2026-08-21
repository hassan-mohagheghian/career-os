"""Cities infrastructure — lazy imports to avoid circular dependencies."""


def __getattr__(name: str):
    _exports = {
        "CityModel": ("cities.infrastructure.models.city_model", "CityModel"),
        "SQLAlchemyCityRepository": ("cities.infrastructure.repositories.sa_city_repository", "SQLAlchemyCityRepository"),
        "city_model_to_dict": ("cities.infrastructure.mappers", "city_model_to_dict"),
    }
    if name in _exports:
        module_path, attr = _exports[name]
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")