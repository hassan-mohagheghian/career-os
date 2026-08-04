"""JobLocation value object — represents location and work arrangement."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JobLocation:
    """Value object for job location details."""

    city: str = "Not specified"
    work_types: tuple[str, ...] = ("On-site",)
    employment_types: tuple[str, ...] = ("Full-time",)

    @classmethod
    def from_dict(cls, data: dict) -> JobLocation:
        return cls(
            city=data.get("location", "Not specified"),
            work_types=tuple(data.get("work_types") or ["On-site"]),
            employment_types=tuple(data.get("employment_types") or ["Full-time"]),
        )
