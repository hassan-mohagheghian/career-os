"""Consolidate job type fields.

Work type is stored under a single multi-value key `work_types` (JSON array of
On-site / Remote / Hybrid) and employment type under `employment_types` (JSON
array of Full-time / Part-time / Contract / Internship / Temporary). The
redundant singular `work_type` and `employment_type` columns are dropped.

Also repairs historical corrupt rows where a LinkedIn URL leaked into
`work_type` and values were shifted between `employment_type` / `work_types`.

Revision ID: 026_consolidate_job_type_fields
Revises: 42c200d12fd5
Create Date: 2026-08-03
"""
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '026_consolidate_job_type_fields'
down_revision: Union[str, None] = '42c200d12fd5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json_loads(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return json.loads(value)
    except Exception:
        return None


def _is_json_array(value):
    if not isinstance(value, str) or not value.strip().startswith("["):
        return False
    return isinstance(_json_loads(value), list)


def _match_work_type(text):
    lower = (text or "").lower()
    if "remote" in lower or "work from anywhere" in lower:
        return "Remote"
    if "hybrid" in lower or "flexible" in lower:
        return "Hybrid"
    if "on-site" in lower or "onsite" in lower or "office" in lower:
        return "On-site"
    return None


def _match_employment_type(text):
    lower = (text or "").lower()
    if "full" in lower:
        return "Full-time"
    if "part" in lower:
        return "Part-time"
    if "contract" in lower or "freelance" in lower:
        return "Contract"
    if "intern" in lower:
        return "Internship"
    if "temp" in lower:
        return "Temporary"
    return None


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column(
        "jobs",
        sa.Column("employment_types", sa.Text, nullable=True),
        schema="job",
    )

    rows = bind.execute(
        sa.text(
            "SELECT id, work_type, employment_type, work_types, raw_description "
            "FROM job.jobs"
        )
    ).fetchall()

    for job_id, work_type, employment_type, work_types, raw_description in rows:
        # Recover employment types. Corrupt rows carried the employment value as
        # a scalar in work_types and a '0' in employment_type.
        emp = _match_employment_type(employment_type)
        if not emp and not _is_json_array(work_types):
            emp = _match_employment_type(work_types)
        employment_types = [emp] if emp else ["Full-time"]

        # Recover work types. Corrupt rows carried the work-types array in
        # raw_description. Prefer stored work_types when valid.
        parsed_wt = _json_loads(work_types) if _is_json_array(work_types) else []
        work = [m for w in parsed_wt if (m := _match_work_type(w))] if isinstance(parsed_wt, list) else []
        if not work:
            raw_parsed = _json_loads(raw_description) if _is_json_array(raw_description) else []
            if isinstance(raw_parsed, list):
                work = [m for w in raw_parsed if (m := _match_work_type(w))]
        if not work:
            matched = _match_work_type(work_type)
            work = [matched] if matched else ["On-site"]

        bind.execute(
            sa.text(
                "UPDATE job.jobs SET employment_types = :et, work_types = :wt "
                "WHERE id = :id"
            ),
            {
                "et": json.dumps(employment_types, ensure_ascii=False),
                "wt": json.dumps(work, ensure_ascii=False),
                "id": job_id,
            },
        )

    op.drop_column("jobs", "work_type", schema="job")
    op.drop_column("jobs", "employment_type", schema="job")


def downgrade() -> None:
    bind = op.get_bind()
    op.add_column(
        "jobs",
        sa.Column("work_type", sa.String, nullable=True, server_default="On-site"),
        schema="job",
    )
    op.add_column(
        "jobs",
        sa.Column("employment_type", sa.String, nullable=True, server_default="Full-time"),
        schema="job",
    )
    rows = bind.execute(
        sa.text("SELECT id, work_types, employment_types FROM job.jobs")
    ).fetchall()
    for job_id, work_types, employment_types in rows:
        wt = _json_loads(work_types) if _is_json_array(work_types) else []
        et = _json_loads(employment_types) if _is_json_array(employment_types) else []
        bind.execute(
            sa.text(
                "UPDATE job.jobs SET work_type = :wt, employment_type = :et "
                "WHERE id = :id"
            ),
            {
                "wt": (wt[0] if wt else "On-site"),
                "et": (et[0] if et else "Full-time"),
                "id": job_id,
            },
        )
    op.drop_column("jobs", "employment_types", schema="job")
