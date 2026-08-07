"""SQLAlchemy implementation of the candidate profile repository.

The profile aggregate owns all children. `replace_children` is the persistence
primitive for the merge system: it swaps the full child set for a kind in one
operation (never recreating unrelated parts of the profile).
"""

import uuid
from typing import Any, Callable

from sqlalchemy.orm import Session

from candidates.domain.repositories.candidate_profile_repository import (
    ICandidateProfileRepository,
    CHILD_KINDS,
)
from candidates.infrastructure.models.candidate_model import (
    CandidateModel,
    CandidateProfileModel,
    CandidateProfileVersionModel,
    CandidateSkillModel,
    CandidateExperienceModel,
    CandidateProjectModel,
    CandidateEducationModel,
    CandidateCertificateModel,
    CandidateInterestModel,
    CandidateLanguageModel,
    _now_iso,
)
from candidates.infrastructure.mappers import (
    candidate_skill_model_to_dict,
    dict_to_candidate_model,
    dict_to_candidate_skill_model,
    dict_to_certificate_model,
    dict_to_education_model,
    dict_to_experience_model,
    dict_to_interest_model,
    dict_to_language_model,
    dict_to_project_model,
    education_model_to_dict,
    experience_model_to_dict,
    interest_model_to_dict,
    certificate_model_to_dict,
    language_model_to_dict,
    profile_model_to_dict,
    project_model_to_dict,
    version_model_to_dict,
    _json_dump,
)

_CHILD_BUILDERS: dict[str, tuple[Any, Callable[[dict[str, Any]], Any]]] = {
    "skills": (CandidateSkillModel, dict_to_candidate_skill_model),
    "experiences": (CandidateExperienceModel, dict_to_experience_model),
    "projects": (CandidateProjectModel, dict_to_project_model),
    "educations": (CandidateEducationModel, dict_to_education_model),
    "certificates": (CandidateCertificateModel, dict_to_certificate_model),
    "interests": (CandidateInterestModel, dict_to_interest_model),
    "languages": (CandidateLanguageModel, dict_to_language_model),
}

_CHILD_READERS: dict[str, Callable[[Any], dict[str, Any]]] = {
    "skills": candidate_skill_model_to_dict,
    "experiences": experience_model_to_dict,
    "projects": project_model_to_dict,
    "educations": education_model_to_dict,
    "certificates": certificate_model_to_dict,
    "interests": interest_model_to_dict,
    "languages": language_model_to_dict,
}


class SQLAlchemyCandidateProfileRepository(ICandidateProfileRepository):
    """SQLAlchemy implementation of the candidate profile repository."""

    def __init__(self, session: Session):
        self._session = session

    def get_current_profile(self) -> dict[str, Any] | None:
        profile = (
            self._session.query(CandidateProfileModel)
            .order_by(CandidateProfileModel.created_at.desc())
            .first()
        )
        if not profile:
            return None
        return self._profile_with_children(profile.id)

    def get_or_create_current(self) -> dict[str, Any]:
        current = self.get_current_profile()
        if current:
            return current

        candidate = (
            self._session.query(CandidateModel)
            .order_by(CandidateModel.created_at.asc())
            .first()
        )
        if candidate is None:
            candidate = dict_to_candidate_model({})
            self._session.add(candidate)
            self._session.flush()

        profile = CandidateProfileModel(id=str(uuid.uuid4()), candidate_id=candidate.id, version=1)
        self._session.add(profile)
        self._session.commit()
        return self.get_current_profile()

    def update_core(self, profile_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        model = (
            self._session.query(CandidateProfileModel)
            .filter(CandidateProfileModel.id == profile_id)
            .first()
        )
        if not model:
            return None
        for field in ["version", "name", "title", "headline", "summary", "location"]:
            if field in data:
                setattr(model, field, data[field])
        model.updated_at = _now_iso()
        self._session.commit()
        return profile_model_to_dict(model)

    def replace_children(self, profile_id: str, kind: str, items: list[dict[str, Any]]) -> int:
        if kind not in CHILD_KINDS:
            raise ValueError(f"Unknown child kind: {kind}")
        model_cls, builder = _CHILD_BUILDERS[kind]

        self._session.query(model_cls).filter(model_cls.profile_id == profile_id).delete()
        self._session.flush()

        for item in items:
            data = dict(item)
            data.setdefault("profile_id", profile_id)
            self._session.add(builder(data))
        self._session.commit()
        return len(items)

    def create_version(
        self,
        profile_id: str,
        version: int,
        snapshot: dict[str, Any],
        source_versions: dict[str, int],
        change_summary: str = "",
    ) -> dict[str, Any]:
        model = CandidateProfileVersionModel(
            id=str(uuid.uuid4()),
            profile_id=profile_id,
            version=version,
            snapshot=_json_dump(snapshot),
            source_versions=_json_dump(source_versions),
            change_summary=change_summary,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return version_model_to_dict(model)

    def list_versions(self, profile_id: str) -> list[dict[str, Any]]:
        rows = (
            self._session.query(CandidateProfileVersionModel)
            .filter(CandidateProfileVersionModel.profile_id == profile_id)
            .order_by(CandidateProfileVersionModel.version.desc())
            .all()
        )
        return [version_model_to_dict(r) for r in rows]

    # ── helpers ──────────────────────────────────────────────────

    def _profile_with_children(self, profile_id: str) -> dict[str, Any]:
        profile = self._session.query(CandidateProfileModel).filter(CandidateProfileModel.id == profile_id).first()
        result = profile_model_to_dict(profile)
        for kind, reader in _CHILD_READERS.items():
            model_cls = _CHILD_BUILDERS[kind][0]
            rows = (
                self._session.query(model_cls)
                .filter(model_cls.profile_id == profile_id)
                .order_by(model_cls.created_at.desc())
                .all()
            )
            result[kind] = [reader(r) for r in rows]
        return result
