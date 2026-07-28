"""JobLocation value object — represents location and work arrangement."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JobLocation:
    """Value object for job location details."""

    city: str = "Not specified"
    work_type: str = "On-site"
    employment_type: str = "Full-time"

    @classmethod
    def from_dict(cls, data: dict) -> JobLocation:
        return cls(
            city=data.get("location", "Not specified"),
            work_type=data.get("work_type", "On-site"),
            employment_type=data.get("employment_type", "Full-time"),
        )
