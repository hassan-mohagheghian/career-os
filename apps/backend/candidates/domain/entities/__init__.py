"""Candidate domain entities."""

from candidates.domain.entities.candidate import Candidate
from candidates.domain.entities.candidate_profile import CandidateProfile
from candidates.domain.entities.candidate_source import CandidateSource, SOURCE_TYPES, SOURCE_STATUSES
from candidates.domain.entities.candidate_skill import CandidateSkill, ORIGINS
from candidates.domain.entities.candidate_experience import CandidateExperience
from candidates.domain.entities.candidate_project import CandidateProject
from candidates.domain.entities.candidate_education import CandidateEducation
from candidates.domain.entities.candidate_certificate import CandidateCertificate
from candidates.domain.entities.candidate_interest import CandidateInterest
from candidates.domain.entities.candidate_language import CandidateLanguage, PROFICIENCIES
from candidates.domain.entities.candidate_profile_version import CandidateProfileVersion

__all__ = [
    "Candidate",
    "CandidateProfile",
    "CandidateSource",
    "SOURCE_TYPES",
    "SOURCE_STATUSES",
    "CandidateSkill",
    "ORIGINS",
    "CandidateExperience",
    "CandidateProject",
    "CandidateEducation",
    "CandidateCertificate",
    "CandidateInterest",
    "CandidateLanguage",
    "PROFICIENCIES",
    "CandidateProfileVersion",
]
