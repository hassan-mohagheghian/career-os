"""Skills infrastructure — lazy imports to avoid circular dependencies."""


def __getattr__(name: str):
    _exports = {
        "SkillModel": ("skills.infrastructure.models.skill_model", "SkillModel"),
        "SkillAliasModel": ("skills.infrastructure.models.skill_model", "SkillAliasModel"),
        "SkillRelationshipModel": ("skills.infrastructure.models.skill_model", "SkillRelationshipModel"),
        "SkillMentionModel": ("skills.infrastructure.models.skill_model", "SkillMentionModel"),
        "SkillNoteModel": ("skills.infrastructure.models.skill_model", "SkillNoteModel"),
        "SkillLinkModel": ("skills.infrastructure.models.skill_model", "SkillLinkModel"),
        "SQLAlchemySkillRepository": ("skills.infrastructure.repositories.sa_skill_repository", "SQLAlchemySkillRepository"),
        "SQLAlchemySkillAliasRepository": ("skills.infrastructure.repositories.sa_skill_alias_repository", "SQLAlchemySkillAliasRepository"),
        "SQLAlchemySkillRelationshipRepository": ("skills.infrastructure.repositories.sa_skill_relationship_repository", "SQLAlchemySkillRelationshipRepository"),
        "SQLAlchemySkillNoteRepository": ("skills.infrastructure.repositories.sa_skill_note_repository", "SQLAlchemySkillNoteRepository"),
        "SQLAlchemySkillLinkRepository": ("skills.infrastructure.repositories.sa_skill_link_repository", "SQLAlchemySkillLinkRepository"),
        "skill_model_to_dict": ("skills.infrastructure.mappers", "skill_model_to_dict"),
        "dict_to_skill_model": ("skills.infrastructure.mappers", "dict_to_skill_model"),
    }
    if name in _exports:
        module_path, attr = _exports[name]
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "SkillModel", "SkillAliasModel", "SkillRelationshipModel", "SkillMentionModel",
    "SQLAlchemySkillRepository", "SQLAlchemySkillAliasRepository",
    "SQLAlchemySkillRelationshipRepository",
    "skill_model_to_dict", "dict_to_skill_model",
]
