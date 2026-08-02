"""Companies infrastructure — lazy imports to avoid circular dependencies."""


def __getattr__(name: str):
    _exports = {
        "CompanyModel": ("companies.infrastructure.models.company_model", "CompanyModel"),
        "CompanyIntelligenceModel": ("companies.infrastructure.models.company_model", "CompanyIntelligenceModel"),
        "CompanyLinkModel": ("companies.infrastructure.models.company_model", "CompanyLinkModel"),
        "SQLAlchemyCompanyRepository": ("companies.infrastructure.repositories.sa_company_repository", "SQLAlchemyCompanyRepository"),
        "SQLAlchemyCompanyIntelligenceRepository": ("companies.infrastructure.repositories.sa_company_intelligence_repository", "SQLAlchemyCompanyIntelligenceRepository"),
        "SQLAlchemyCompanyLinkRepository": ("companies.infrastructure.repositories.sa_company_link_repository", "SQLAlchemyCompanyLinkRepository"),
        "company_model_to_dict": ("shared.infrastructure.database.mappers", "company_model_to_dict"),
        "company_intelligence_model_to_dict": ("shared.infrastructure.database.mappers", "company_intelligence_model_to_dict"),
    }
    if name in _exports:
        module_path, attr = _exports[name]
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "CompanyModel", "CompanyIntelligenceModel", "CompanyLinkModel",
    "SQLAlchemyCompanyRepository", "SQLAlchemyCompanyIntelligenceRepository",
    "SQLAlchemyCompanyLinkRepository", "company_model_to_dict",
    "company_intelligence_model_to_dict",
]
