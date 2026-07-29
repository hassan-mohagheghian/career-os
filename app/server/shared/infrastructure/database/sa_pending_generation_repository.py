"""Pending generation repository - DEPRECATED.

The pending_generations table has been removed.
Functionality has moved to the resume context.
"""
from resume.infrastructure.repositories.sa_resume_repository import SQLAlchemyResumeRepository as _SQLAlchemyResumeRepository


class SQLAlchemyPendingGenerationRepository(_SQLAlchemyResumeRepository):
    def __init__(self, *args, **kwargs):
        import warnings
        warnings.warn("pending_generations is deprecated, use resume context instead", DeprecationWarning, stacklevel=2)
        super().__init__(*args, **kwargs)


__all__ = ["SQLAlchemyPendingGenerationRepository"]
