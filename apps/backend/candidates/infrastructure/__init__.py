"""Candidate infrastructure — lazy imports to avoid circular dependencies."""


def __getattr__(name: str):
    _exports = {
        "CandidateModel": ("candidates.infrastructure.models.candidate_model", "CandidateModel"),
        "CandidateProfileModel": ("candidates.infrastructure.models.candidate_model", "CandidateProfileModel"),
        "CandidateSourceModel": ("candidates.infrastructure.models.candidate_model", "CandidateSourceModel"),
        "CandidateSkillModel": ("candidates.infrastructure.models.candidate_model", "CandidateSkillModel"),
        "CandidateExperienceModel": ("candidates.infrastructure.models.candidate_model", "CandidateExperienceModel"),
        "CandidateProjectModel": ("candidates.infrastructure.models.candidate_model", "CandidateProjectModel"),
        "CandidateEducationModel": ("candidates.infrastructure.models.candidate_model", "CandidateEducationModel"),
        "CandidateCertificateModel": ("candidates.infrastructure.models.candidate_model", "CandidateCertificateModel"),
        "CandidateInterestModel": ("candidates.infrastructure.models.candidate_model", "CandidateInterestModel"),
        "CandidateLanguageModel": ("candidates.infrastructure.models.candidate_model", "CandidateLanguageModel"),
        "CandidateProfileVersionModel": ("candidates.infrastructure.models.candidate_model", "CandidateProfileVersionModel"),
        "SQLAlchemyCandidateRepository": ("candidates.infrastructure.repositories.sa_candidate_repository", "SQLAlchemyCandidateRepository"),
        "SQLAlchemyCandidateProfileRepository": ("candidates.infrastructure.repositories.sa_candidate_profile_repository", "SQLAlchemyCandidateProfileRepository"),
        "SQLAlchemyCandidateSourceRepository": ("candidates.infrastructure.repositories.sa_candidate_source_repository", "SQLAlchemyCandidateSourceRepository"),
    }
    if name in _exports:
        module_path, attr = _exports[name]
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "CandidateModel",
    "CandidateProfileModel",
    "CandidateSourceModel",
    "CandidateSkillModel",
    "CandidateExperienceModel",
    "CandidateProjectModel",
    "CandidateEducationModel",
    "CandidateCertificateModel",
    "CandidateInterestModel",
    "CandidateLanguageModel",
    "CandidateProfileVersionModel",
    "SQLAlchemyCandidateRepository",
    "SQLAlchemyCandidateProfileRepository",
    "SQLAlchemyCandidateSourceRepository",
]
