"""Roadmaps infrastructure — lazy imports to avoid circular dependencies."""


def __getattr__(name: str):
    _exports = {
        "RoadmapModel": ("roadmaps.infrastructure.models.roadmap_model", "RoadmapModel"),
        "RoadmapGoalModel": ("roadmaps.infrastructure.models.roadmap_model", "RoadmapGoalModel"),
        "RoadmapMilestoneModel": ("roadmaps.infrastructure.models.roadmap_model", "RoadmapMilestoneModel"),
        "RoadmapTaskModel": ("roadmaps.infrastructure.models.roadmap_model", "RoadmapTaskModel"),
        "RoadmapSkillLinkModel": ("roadmaps.infrastructure.models.roadmap_model", "RoadmapSkillLinkModel"),
        "RoadmapNoteModel": ("roadmaps.infrastructure.models.roadmap_model", "RoadmapNoteModel"),
        "RoadmapResourceModel": ("roadmaps.infrastructure.models.roadmap_model", "RoadmapResourceModel"),
        "SQLAlchemyRoadmapRepository": ("roadmaps.infrastructure.repositories.sa_roadmap_repository", "SQLAlchemyRoadmapRepository"),
    }
    if name in _exports:
        module_path, attr = _exports[name]
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "RoadmapModel",
    "RoadmapGoalModel",
    "RoadmapMilestoneModel",
    "RoadmapTaskModel",
    "RoadmapSkillLinkModel",
    "RoadmapNoteModel",
    "RoadmapResourceModel",
    "SQLAlchemyRoadmapRepository",
]