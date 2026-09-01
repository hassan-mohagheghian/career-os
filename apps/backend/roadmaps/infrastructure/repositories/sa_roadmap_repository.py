"""SQLAlchemy implementation of the roadmap repository."""

from typing import Any

from sqlalchemy.orm import Session

from roadmaps.domain.repositories.roadmap_repository import IRoadmapRepository
from roadmaps.infrastructure.mappers import (
    dict_to_goal_model,
    dict_to_milestone_model,
    dict_to_note_model,
    dict_to_resource_model,
    dict_to_roadmap_model,
    dict_to_skill_link_model,
    dict_to_task_model,
    goal_model_to_dict,
    milestone_model_to_dict,
    note_model_to_dict,
    resource_model_to_dict,
    roadmap_model_to_dict,
    skill_link_model_to_dict,
    task_model_to_dict,
)
from roadmaps.infrastructure.models.roadmap_model import (
    RoadmapGoalModel,
    RoadmapMilestoneModel,
    RoadmapModel,
    RoadmapNoteModel,
    RoadmapResourceModel,
    RoadmapSkillLinkModel,
    RoadmapTaskModel,
)

class SQLAlchemyRoadmapRepository(IRoadmapRepository):
    """SQLAlchemy implementation of the roadmap repository."""

    def __init__(self, session: Session, user_id: str = ""):
        self._session = session
        self._user_id = user_id

    # ── Roadmap ─────────────────────────────────────────────────────

    def get_by_id(self, roadmap_id: str) -> dict[str, Any] | None:
        q = self._session.query(RoadmapModel).filter(
            RoadmapModel.id == roadmap_id
        )
        if self._user_id:
            q = q.filter(RoadmapModel.user_id == self._user_id)
        model = q.first()
        return roadmap_model_to_dict(model) if model else None

    def get_by_application_id(self, application_id: str) -> dict[str, Any] | None:
        q = self._session.query(RoadmapModel).filter(
            RoadmapModel.application_id == application_id
        )
        if self._user_id:
            q = q.filter(RoadmapModel.user_id == self._user_id)
        model = q.order_by(RoadmapModel.created_at.desc()).first()
        return roadmap_model_to_dict(model) if model else None

    def list(self) -> list[dict[str, Any]]:
        q = self._session.query(RoadmapModel)
        if self._user_id:
            q = q.filter(RoadmapModel.user_id == self._user_id)
        rows = q.order_by(RoadmapModel.created_at.desc()).all()
        return [roadmap_model_to_dict(r) for r in rows]

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        data.setdefault("user_id", self._user_id)
        model = dict_to_roadmap_model(data)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return roadmap_model_to_dict(model)

    def update(self, roadmap_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        model = (
            self._session.query(RoadmapModel)
            .filter(RoadmapModel.id == roadmap_id)
            .first()
        )
        if not model:
            return None
        for field in ("title", "description", "status", "goal_type", "source", "application_id", "updated_at"):
            if field in data and data[field] is not None:
                setattr(model, field, data[field])
        self._session.commit()
        return roadmap_model_to_dict(model)

    def delete(self, roadmap_id: str) -> bool:
        milestone_ids = [
            row[0]
            for row in self._session.query(RoadmapMilestoneModel.id)
            .filter(RoadmapMilestoneModel.roadmap_id == roadmap_id)
            .all()
        ]
        for milestone_id in milestone_ids:
            task_ids = [
                row[0]
                for row in self._session.query(RoadmapTaskModel.id)
                .filter(RoadmapTaskModel.milestone_id == milestone_id)
                .all()
            ]
            for task_id in task_ids:
                self.delete_task(task_id)
            self._session.query(RoadmapSkillLinkModel).filter(
                RoadmapSkillLinkModel.milestone_id == milestone_id
            ).delete(synchronize_session=False)
            self._session.query(RoadmapNoteModel).filter(
                RoadmapNoteModel.milestone_id == milestone_id
            ).delete(synchronize_session=False)
            self._session.query(RoadmapResourceModel).filter(
                RoadmapResourceModel.milestone_id == milestone_id
            ).delete(synchronize_session=False)
        self._session.query(RoadmapSkillLinkModel).filter(
            RoadmapSkillLinkModel.roadmap_id == roadmap_id
        ).delete(synchronize_session=False)
        self._session.query(RoadmapNoteModel).filter(
            RoadmapNoteModel.roadmap_id == roadmap_id
        ).delete(synchronize_session=False)
        self._session.query(RoadmapResourceModel).filter(
            RoadmapResourceModel.roadmap_id == roadmap_id
        ).delete(synchronize_session=False)
        self._session.query(RoadmapMilestoneModel).filter(
            RoadmapMilestoneModel.roadmap_id == roadmap_id
        ).delete(synchronize_session=False)
        self._session.query(RoadmapGoalModel).filter(
            RoadmapGoalModel.roadmap_id == roadmap_id
        ).delete(synchronize_session=False)
        deleted = (
            self._session.query(RoadmapModel)
            .filter(RoadmapModel.id == roadmap_id)
            .delete(synchronize_session=False)
        )
        self._session.commit()
        return bool(deleted)

    def delete_by_application(self, application_id: str) -> int:
        ids = [
            row[0]
            for row in self._session.query(RoadmapModel.id)
            .filter(RoadmapModel.application_id == application_id)
            .all()
        ]
        for roadmap_id in ids:
            self.delete(roadmap_id)
        return len(ids)

    # ── Goal ────────────────────────────────────────────────────────

    def get_goal(self, roadmap_id: str) -> dict[str, Any] | None:
        model = (
            self._session.query(RoadmapGoalModel)
            .filter(RoadmapGoalModel.roadmap_id == roadmap_id)
            .first()
        )
        return goal_model_to_dict(model) if model else None

    def create_goal(self, data: dict[str, Any]) -> dict[str, Any]:
        model = dict_to_goal_model(data)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return goal_model_to_dict(model)

    def update_goal(self, roadmap_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        model = (
            self._session.query(RoadmapGoalModel)
            .filter(RoadmapGoalModel.roadmap_id == roadmap_id)
            .first()
        )
        if not model:
            return None
        for field in ("type", "title", "description", "target_job_id", "target_company_id", "target_skill_id", "updated_at"):
            if field in data and data[field] is not None:
                setattr(model, field, data[field])
        self._session.commit()
        return goal_model_to_dict(model)

    # ── Milestones ──────────────────────────────────────────────────

    def list_milestones(self, roadmap_id: str) -> list[dict[str, Any]]:
        rows = (
            self._session.query(RoadmapMilestoneModel)
            .filter(RoadmapMilestoneModel.roadmap_id == roadmap_id)
            .order_by(RoadmapMilestoneModel.position.asc())
            .all()
        )
        return [milestone_model_to_dict(r) for r in rows]

    def get_milestone(self, milestone_id: str) -> dict[str, Any] | None:
        model = (
            self._session.query(RoadmapMilestoneModel)
            .filter(RoadmapMilestoneModel.id == milestone_id)
            .first()
        )
        return milestone_model_to_dict(model) if model else None

    def create_milestone(self, data: dict[str, Any]) -> dict[str, Any]:
        model = dict_to_milestone_model(data)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return milestone_model_to_dict(model)

    def update_milestone(self, milestone_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        model = (
            self._session.query(RoadmapMilestoneModel)
            .filter(RoadmapMilestoneModel.id == milestone_id)
            .first()
        )
        if not model:
            return None
        for field in ("position", "title", "description", "status", "priority", "updated_at"):
            if field in data:
                setattr(model, field, data[field])
        self._session.commit()
        return milestone_model_to_dict(model)

    def delete_milestone(self, milestone_id: str) -> bool:
        self._session.query(RoadmapSkillLinkModel).filter(
            RoadmapSkillLinkModel.milestone_id == milestone_id
        ).delete(synchronize_session=False)
        self._session.query(RoadmapNoteModel).filter(
            RoadmapNoteModel.milestone_id == milestone_id
        ).delete(synchronize_session=False)
        self._session.query(RoadmapResourceModel).filter(
            RoadmapResourceModel.milestone_id == milestone_id
        ).delete(synchronize_session=False)
        task_ids = [
            row[0]
            for row in self._session.query(RoadmapTaskModel.id)
            .filter(RoadmapTaskModel.milestone_id == milestone_id)
            .all()
        ]
        for task_id in task_ids:
            self.delete_task(task_id)
        deleted = (
            self._session.query(RoadmapMilestoneModel)
            .filter(RoadmapMilestoneModel.id == milestone_id)
            .delete(synchronize_session=False)
        )
        self._session.commit()
        return bool(deleted)

    # ── Tasks ───────────────────────────────────────────────────────

    def list_tasks(self, milestone_id: str) -> list[dict[str, Any]]:
        rows = (
            self._session.query(RoadmapTaskModel)
            .filter(RoadmapTaskModel.milestone_id == milestone_id)
            .order_by(RoadmapTaskModel.position.asc())
            .all()
        )
        return [task_model_to_dict(r) for r in rows]

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        model = (
            self._session.query(RoadmapTaskModel)
            .filter(RoadmapTaskModel.id == task_id)
            .first()
        )
        return task_model_to_dict(model) if model else None

    def create_task(self, data: dict[str, Any]) -> dict[str, Any]:
        model = dict_to_task_model(data)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return task_model_to_dict(model)

    def update_task(self, task_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        model = (
            self._session.query(RoadmapTaskModel)
            .filter(RoadmapTaskModel.id == task_id)
            .first()
        )
        if not model:
            return None
        for field in ("position", "title", "description", "status", "priority", "estimated_effort", "success_criteria", "completed_at", "updated_at"):
            if field in data:
                setattr(model, field, data[field])
        self._session.commit()
        return task_model_to_dict(model)

    def delete_task(self, task_id: str) -> bool:
        self._session.query(RoadmapSkillLinkModel).filter(
            RoadmapSkillLinkModel.task_id == task_id
        ).delete(synchronize_session=False)
        self._session.query(RoadmapNoteModel).filter(
            RoadmapNoteModel.task_id == task_id
        ).delete(synchronize_session=False)
        self._session.query(RoadmapResourceModel).filter(
            RoadmapResourceModel.task_id == task_id
        ).delete(synchronize_session=False)
        deleted = (
            self._session.query(RoadmapTaskModel)
            .filter(RoadmapTaskModel.id == task_id)
            .delete(synchronize_session=False)
        )
        self._session.commit()
        return bool(deleted)

    # ── Skill links ─────────────────────────────────────────────────

    def list_skills(self, roadmap_id: str) -> list[dict[str, Any]]:
        rows = (
            self._session.query(RoadmapSkillLinkModel)
            .filter(RoadmapSkillLinkModel.roadmap_id == roadmap_id)
            .order_by(RoadmapSkillLinkModel.position.asc())
            .all()
        )
        return [skill_link_model_to_dict(r) for r in rows]

    def get_skill_link(self, link_id: str) -> dict[str, Any] | None:
        model = (
            self._session.query(RoadmapSkillLinkModel)
            .filter(RoadmapSkillLinkModel.id == link_id)
            .first()
        )
        return skill_link_model_to_dict(model) if model else None

    def create_skill_link(self, data: dict[str, Any]) -> dict[str, Any]:
        model = dict_to_skill_link_model(data)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return skill_link_model_to_dict(model)

    def delete_skill_link(self, link_id: str) -> bool:
        deleted = (
            self._session.query(RoadmapSkillLinkModel)
            .filter(RoadmapSkillLinkModel.id == link_id)
            .delete(synchronize_session=False)
        )
        self._session.commit()
        return bool(deleted)

    # ── Notes ───────────────────────────────────────────────────────

    def list_notes(self, roadmap_id: str) -> list[dict[str, Any]]:
        rows = (
            self._session.query(RoadmapNoteModel)
            .filter(RoadmapNoteModel.roadmap_id == roadmap_id)
            .order_by(RoadmapNoteModel.created_at.desc())
            .all()
        )
        return [note_model_to_dict(r) for r in rows]

    def create_note(self, data: dict[str, Any]) -> dict[str, Any]:
        model = dict_to_note_model(data)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return note_model_to_dict(model)

    def delete_note(self, note_id: str) -> bool:
        deleted = (
            self._session.query(RoadmapNoteModel)
            .filter(RoadmapNoteModel.id == note_id)
            .delete(synchronize_session=False)
        )
        self._session.commit()
        return bool(deleted)

    # ── Resources ───────────────────────────────────────────────────

    def list_resources(self, roadmap_id: str) -> list[dict[str, Any]]:
        rows = (
            self._session.query(RoadmapResourceModel)
            .filter(RoadmapResourceModel.roadmap_id == roadmap_id)
            .order_by(RoadmapResourceModel.created_at.desc())
            .all()
        )
        return [resource_model_to_dict(r) for r in rows]

    def create_resource(self, data: dict[str, Any]) -> dict[str, Any]:
        model = dict_to_resource_model(data)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return resource_model_to_dict(model)

    def update_resource(self, resource_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        model = (
            self._session.query(RoadmapResourceModel)
            .filter(RoadmapResourceModel.id == resource_id)
            .first()
        )
        if not model:
            return None
        for field in ("title", "url", "description", "type", "status", "source", "updated_at"):
            if field in data and data[field] is not None:
                setattr(model, field, data[field])
        self._session.commit()
        return resource_model_to_dict(model)

    def delete_resource(self, resource_id: str) -> bool:
        deleted = (
            self._session.query(RoadmapResourceModel)
            .filter(RoadmapResourceModel.id == resource_id)
            .delete(synchronize_session=False)
        )
        self._session.commit()
        return bool(deleted)