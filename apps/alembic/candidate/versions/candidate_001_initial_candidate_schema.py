"""initial candidate schema

Revision ID: candidate_001
Revises: cfb9c0c021da
Create Date: 2026-08-07 07:54:59.816266
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "candidate_001"
down_revision: Union[str, None] = "cfb9c0c021da"
branch_labels: Union[str, Sequence[str], None] = ("candidate",)
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS candidate")

    op.create_table(
        "candidates",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("headline", sa.String(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("location", sa.String(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidates")),
        schema="candidate",
    )
    op.create_table(
        "candidate_profiles",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("candidate_id", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("headline", sa.String(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("location", sa.String(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["candidate.candidates.id"],
            name=op.f("fk_candidate_profiles_candidate_id_candidates"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidate_profiles")),
        schema="candidate",
    )
    op.create_table(
        "candidate_sources",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("profile_id", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("error", sa.Text(), nullable=False),
        sa.Column("processed_at", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["candidate.candidate_profiles.id"],
            name=op.f("fk_candidate_sources_profile_id_candidate_profiles"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidate_sources")),
        schema="candidate",
    )
    op.create_table(
        "candidate_skills",
        # skill_id is a logical reference to skill.skills (cross-context) —
        # deliberately no ForeignKey constraint (AGENTS.md rule 15).
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("profile_id", sa.String(), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("origin", sa.String(), nullable=False),
        sa.Column("years_of_experience", sa.Float(), nullable=True),
        sa.Column("last_used", sa.String(), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["candidate.candidate_profiles.id"],
            name=op.f("fk_candidate_skills_profile_id_candidate_profiles"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidate_skills")),
        schema="candidate",
    )
    op.create_table(
        "candidate_experiences",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("profile_id", sa.String(), nullable=False),
        sa.Column("company", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("start_date", sa.String(), nullable=True),
        sa.Column("end_date", sa.String(), nullable=True),
        sa.Column("duration_months", sa.Integer(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("highlights", sa.Text(), nullable=False),
        sa.Column("skills", sa.Text(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["candidate.candidate_profiles.id"],
            name=op.f("fk_candidate_experiences_profile_id_candidate_profiles"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidate_experiences")),
        schema="candidate",
    )
    op.create_table(
        "candidate_projects",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("profile_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("skills", sa.Text(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("start_date", sa.String(), nullable=True),
        sa.Column("end_date", sa.String(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["candidate.candidate_profiles.id"],
            name=op.f("fk_candidate_projects_profile_id_candidate_profiles"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidate_projects")),
        schema="candidate",
    )
    op.create_table(
        "candidate_educations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("profile_id", sa.String(), nullable=False),
        sa.Column("institution", sa.String(), nullable=False),
        sa.Column("degree", sa.String(), nullable=False),
        sa.Column("field", sa.String(), nullable=False),
        sa.Column("start_date", sa.String(), nullable=True),
        sa.Column("end_date", sa.String(), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["candidate.candidate_profiles.id"],
            name=op.f("fk_candidate_educations_profile_id_candidate_profiles"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidate_educations")),
        schema="candidate",
    )
    op.create_table(
        "candidate_certificates",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("profile_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("issuer", sa.String(), nullable=False),
        sa.Column("issue_date", sa.String(), nullable=True),
        sa.Column("credential_url", sa.String(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["candidate.candidate_profiles.id"],
            name=op.f("fk_candidate_certificates_profile_id_candidate_profiles"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidate_certificates")),
        schema="candidate",
    )
    op.create_table(
        "candidate_interests",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("profile_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["candidate.candidate_profiles.id"],
            name=op.f("fk_candidate_interests_profile_id_candidate_profiles"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidate_interests")),
        schema="candidate",
    )
    op.create_table(
        "candidate_languages",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("profile_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("proficiency", sa.String(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["candidate.candidate_profiles.id"],
            name=op.f("fk_candidate_languages_profile_id_candidate_profiles"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidate_languages")),
        schema="candidate",
    )
    op.create_table(
        "candidate_profile_versions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("profile_id", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("snapshot", sa.Text(), nullable=False),
        sa.Column("source_versions", sa.Text(), nullable=False),
        sa.Column("change_summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["candidate.candidate_profiles.id"],
            name=op.f("fk_candidate_profile_versions_profile_id_candidate_profiles"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidate_profile_versions")),
        schema="candidate",
    )

    # Indexes on the profile_id lookups used by the merge / list queries.
    op.create_index(
        op.f("ix_candidate_skills_profile_id"), "candidate_skills", ["profile_id"], unique=False, schema="candidate"
    )
    op.create_index(
        op.f("ix_candidate_experiences_profile_id"),
        "candidate_experiences",
        ["profile_id"],
        unique=False,
        schema="candidate",
    )
    op.create_index(
        op.f("ix_candidate_sources_profile_id"), "candidate_sources", ["profile_id"], unique=False, schema="candidate"
    )
    op.create_index(
        op.f("ix_candidate_profile_versions_profile_id"),
        "candidate_profile_versions",
        ["profile_id"],
        unique=False,
        schema="candidate",
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_candidate_profile_versions_profile_id"), table_name="candidate_profile_versions", schema="candidate")
    op.drop_index(op.f("ix_candidate_sources_profile_id"), table_name="candidate_sources", schema="candidate")
    op.drop_index(op.f("ix_candidate_experiences_profile_id"), table_name="candidate_experiences", schema="candidate")
    op.drop_index(op.f("ix_candidate_skills_profile_id"), table_name="candidate_skills", schema="candidate")
    op.drop_table("candidate_profile_versions", schema="candidate")
    op.drop_table("candidate_languages", schema="candidate")
    op.drop_table("candidate_interests", schema="candidate")
    op.drop_table("candidate_certificates", schema="candidate")
    op.drop_table("candidate_educations", schema="candidate")
    op.drop_table("candidate_projects", schema="candidate")
    op.drop_table("candidate_experiences", schema="candidate")
    op.drop_table("candidate_skills", schema="candidate")
    op.drop_table("candidate_sources", schema="candidate")
    op.drop_table("candidate_profiles", schema="candidate")
    op.drop_table("candidates", schema="candidate")
    op.execute("DROP SCHEMA IF EXISTS candidate")
