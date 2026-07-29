"""Pending generation repository - DEPRECATED.

The pending_generations table has been removed.
Functionality has moved to the jobs tailored document context.
"""
from jobs.infrastructure.repositories.sa_tailored_document_repository import SQLAlchemyTailoredDocumentRepository as _SQLAlchemyTailoredDocumentRepository


class SQLAlchemyPendingGenerationRepository(_SQLAlchemyTailoredDocumentRepository):
    def __init__(self, *args, **kwargs):
        import warnings
        warnings.warn("pending_generations is deprecated, use jobs tailored document context instead", DeprecationWarning, stacklevel=2)
        super().__init__(*args, **kwargs)


__all__ = ["SQLAlchemyPendingGenerationRepository"]
