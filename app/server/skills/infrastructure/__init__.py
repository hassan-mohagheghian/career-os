"""Skills infrastructure — lazy imports to avoid circular dependencies."""


def __getattr__(name: str):
    _exports = {
        "SkillModel": ("skills.infrastructure.models.skill_model", "SkillModel"),
        "SkillAliasModel": ("skills.infrastructure.models.skill_model", "SkillAliasModel"),
        "SkillRelationshipModel": ("skills.infrastructure.models.skill_model", "SkillRelationshipModel"),
        "SkillRoadmapModel": ("shared.infrastructure.database.models.misc_models", "SkillRoadmapModel"),
        "SkillRoadmapProgressModel": ("shared.infrastructure.database.models.misc_models", "SkillRoadmapProgressModel"),
        "SkillRoadmapJobModel": ("shared.infrastructure.database.models.misc_models", "SkillRoadmapJobModel"),
        "SQLAlchemySkillRepository": ("skills.infrastructure.repositories.sa_skill_repository", "SQLAlchemySkillRepository"),
        "SQLAlchemySkillAliasRepository": ("skills.infrastructure.repositories.sa_skill_alias_repository", "SQLAlchemySkillAliasRepository"),
        "SQLAlchemySkillRelationshipRepository": ("skills.infrastructure.repositories.sa_skill_relationship_repository", "SQLAlchemySkillRelationshipRepository"),
        "SQLAlchemySkillRoadmapRepository": ("skills.infrastructure.repositories.sa_skill_roadmap_repository", "SQLAlchemySkillRoadmapRepository"),
        "SQLAlchemySkillRoadmapProgressRepository": ("skills.infrastructure.repositories.sa_skill_roadmap_progress_repository", "SQLAlchemySkillRoadmapProgressRepository"),
        "SQLAlchemySkillRoadmapJobRepository": ("skills.infrastructure.repositories.sa_skill_roadmap_job_repository", "SQLAlchemySkillRoadmapJobRepository"),
        "skill_model_to_dict": ("shared.infrastructure.database.mappers", "skill_model_to_dict"),
        "dict_to_skill_model": ("shared.infrastructure.database.mappers", "dict_to_skill_model"),
    }
    if name in _exports:
        module_path, attr = _exports[name]
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "SkillModel", "SkillAliasModel", "SkillRelationshipModel",
    "SkillRoadmapModel", "SkillRoadmapProgressModel", "SkillRoadmapJobModel",
    "SQLAlchemySkillRepository", "SQLAlchemySkillAliasRepository",
    "SQLAlchemySkillRelationshipRepository", "SQLAlchemySkillRoadmapRepository",
    "SQLAlchemySkillRoadmapProgressRepository", "SQLAlchemySkillRoadmapJobRepository",
    "skill_model_to_dict", "dict_to_skill_model",
]
