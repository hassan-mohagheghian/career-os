"""Pending models - DEPRECATED.

These tables no longer exist. Data is now stored in the jobs/companies
tables with a status field.
"""
import warnings


def __getattr__(name):
    if name in ("PendingJobModel", "PendingCompanyModel"):
        warnings.warn("pending models are deprecated, use jobs/companies models instead", DeprecationWarning, stacklevel=2)
        if name == "PendingJobModel":
            from jobs.infrastructure.models.job_model import JobModel
            return JobModel
        else:
            from companies.infrastructure.models.company_model import CompanyModel
            return CompanyModel
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


class PendingGenerationModel:
    """Placeholder - pending_generations table has been removed."""
    @classmethod
    def __init_subclass__(cls, **kwargs):
        pass

    def __init__(self, *args, **kwargs):
        raise RuntimeError("PendingGenerationModel is no longer available - the pending_generations table has been removed")


__all__ = ["PendingJobModel", "PendingCompanyModel", "PendingGenerationModel"]
