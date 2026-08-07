"""add raw_text to candidate_sources, align candidate indexes, backfill from job.resumes

Revision ID: candidate_002
Revises: candidate_001
Create Date: 2026-08-07 11:06:30.362677
"""
import uuid
from datetime import datetime, UTC
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "candidate_002"
down_revision: Union[str, None] = "candidate_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_OLD_INDEXES = [
    ("ix_candidate_sources_profile_id", "candidate_sources"),
    ("ix_candidate_skills_profile_id", "candidate_skills"),
    ("ix_candidate_experiences_profile_id", "candidate_experiences"),
    ("ix_candidate_profile_versions_profile_id", "candidate_profile_versions"),
]
_NEW_INDEXES = [
    ("ix_candidate_candidate_sources_profile_id", "candidate_sources"),
    ("ix_candidate_candidate_skills_profile_id", "candidate_skills"),
    ("ix_candidate_candidate_experiences_profile_id", "candidate_experiences"),
    ("ix_candidate_candidate_profile_versions_profile_id", "candidate_profile_versions"),
]


def _backfill_sources_from_job_resumes() -> None:
    """Port legacy resume/LinkedIn rows from the job schema into candidate
    sources so the job.resumes table can be dropped later (Phase 111, task 3).

    Only ``original_*`` (resume) and ``linkedin_*`` (linkedin) rows are ported —
    per-job tailored resume rows are being retired with tailored generation.
    """
    conn = op.get_bind()
    dialect = conn.dialect

    if not dialect.has_table(conn, "resumes", schema="job"):
        return

    rows = conn.execute(
        sa.text(
            "SELECT id, raw_text, content, version, created_at "
            "FROM job.resumes "
            "WHERE id LIKE 'original_%' OR id LIKE 'linkedin_%' "
            "ORDER BY created_at ASC"
        )
    ).fetchall()
    if not rows:
        return

    existing_profiles = conn.execute(
        sa.text("SELECT id FROM candidate.candidate_profiles ORDER BY created_at ASC LIMIT 1")
    ).fetchone()
    if existing_profiles:
        profile_id = existing_profiles[0]
    else:
        now = datetime.now(UTC).isoformat()
        candidate_id = str(uuid.uuid4())
        profile_id = str(uuid.uuid4())
        conn.execute(
            sa.text(
                "INSERT INTO candidate.candidates "
                "(id, name, headline, summary, location, created_at, updated_at) "
                "VALUES (:id, '', '', '', '', :now, :now)"
            ),
            {"id": candidate_id, "now": now},
        )
        conn.execute(
            sa.text(
                "INSERT INTO candidate.candidate_profiles "
                "(id, candidate_id, version, name, title, headline, summary, location, created_at, updated_at) "
                "VALUES (:id, :candidate_id, 1, '', '', '', '', '', :now, :now)"
            ),
            {"id": profile_id, "candidate_id": candidate_id, "now": now},
        )

    now = datetime.now(UTC).isoformat()
    for row in rows:
        resume_id = row.id
        if resume_id.startswith("original_"):
            source_type = "resume"
        elif resume_id.startswith("linkedin_"):
            source_type = "linkedin"
        else:
            continue
        raw_text = row.raw_text or row.content or ""
        if not raw_text.strip():
            continue
        exists = conn.execute(
            sa.text(
                "SELECT 1 FROM candidate.candidate_sources "
                "WHERE profile_id = :profile_id AND source_type = :source_type AND version = :version"
            ),
            {"profile_id": profile_id, "source_type": source_type, "version": row.version},
        ).fetchone()
        if exists:
            continue
        conn.execute(
            sa.text(
                "INSERT INTO candidate.candidate_sources "
                "(id, profile_id, source_type, version, raw_text, status, error, processed_at, created_at, updated_at) "
                "VALUES (:id, :profile_id, :source_type, :version, :raw_text, 'processed', '', :now, :now, :now)"
            ),
            {
                "id": str(uuid.uuid4()),
                "profile_id": profile_id,
                "source_type": source_type,
                "version": row.version,
                "raw_text": raw_text,
                "now": now,
            },
        )


def upgrade() -> None:
    op.add_column(
        "candidate_sources",
        sa.Column("raw_text", sa.Text(), nullable=False),
        schema="candidate",
    )

    # Indexes are now declared on the ORM models (index=True), so alembic's
    # schema-scoped autogenerate produces candidate-prefixed names. Migrate the
    # manually-created indexes from candidate_001 to the model-declared names.
    for name, table in _OLD_INDEXES:
        op.drop_index(op.f(name), table_name=table, schema="candidate")
    for name, table in _NEW_INDEXES:
        op.create_index(op.f(name), table, ["profile_id"], unique=False, schema="candidate")

    _backfill_sources_from_job_resumes()


def downgrade() -> None:
    # Drop backfilled sources that came from job.resumes.
    conn = op.get_bind()
    dialect = conn.dialect
    if dialect.has_table(conn, "resumes", schema="job"):
        conn.execute(
            sa.text(
                "DELETE FROM candidate.candidate_sources "
                "WHERE source_type IN ('resume', 'linkedin') "
                "AND id IN ("
                "  SELECT cs.id FROM candidate.candidate_sources cs "
                "  JOIN job.resumes r ON cs.source_type = "
                "    (CASE WHEN r.id LIKE 'original_%' THEN 'resume' ELSE 'linkedin' END) "
                "  AND cs.version = r.version"
                ")"
            )
        )

    for name, table in _NEW_INDEXES:
        op.drop_index(op.f(name), table_name=table, schema="candidate")
    for name, table in _OLD_INDEXES:
        op.create_index(op.f(name), table, ["profile_id"], unique=False, schema="candidate")

    op.drop_column("candidate_sources", "raw_text", schema="candidate")
