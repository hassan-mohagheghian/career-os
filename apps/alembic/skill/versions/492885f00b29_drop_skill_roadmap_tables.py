"""drop skill roadmap tables

Revision ID: 492885f00b29
Revises: ba15ab77d3cd
Create Date: 2026-08-07 20:34:20.520055

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '492885f00b29'
down_revision: Union[str, None] = 'ba15ab77d3cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the skill roadmap feature tables (skill schema).
    # Order matters: child tables reference skill_roadmaps.
    op.drop_table('skill_roadmap_jobs', schema='skill')
    op.drop_table('skill_roadmap_progress', schema='skill')
    op.drop_table('skill_roadmaps', schema='skill')


def downgrade() -> None:
    # Recreate the skill roadmap tables in reverse dependency order.
    op.create_table(
        'skill_roadmaps',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('skill_name', sa.String(), nullable=False),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('skill.skill_roadmaps.id'), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), server_default=''),
        sa.Column('level', sa.Integer(), server_default='0'),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('version', sa.Integer(), server_default='1'),
        sa.Column('numbering', sa.String(), nullable=True),
        sa.Column('created_at', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='skill',
    )

    op.create_table(
        'skill_roadmap_progress',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('roadmap_id', sa.Integer(), sa.ForeignKey('skill.skill_roadmaps.id', ondelete='CASCADE'), nullable=False),
        sa.Column('skill_name', sa.String(), nullable=False),
        sa.Column('completed', sa.Integer(), server_default='0'),
        sa.Column('updated_at', sa.Text(), nullable=True),
        sa.UniqueConstraint('roadmap_id'),
        sa.PrimaryKeyConstraint('id'),
        schema='skill',
    )

    op.create_table(
        'skill_roadmap_jobs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('skill_name', sa.String(), nullable=False),
        sa.Column('job_type', sa.String(), server_default='generate'),
        sa.Column('status', sa.String(), server_default='queued'),
        sa.Column('step', sa.Integer(), server_default='0'),
        sa.Column('total_steps', sa.Integer(), server_default='4'),
        sa.Column('message', sa.Text(), server_default=''),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.Column('count', sa.Integer(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('provider_name', sa.String(), nullable=True),
        sa.Column('pid', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.Text(), nullable=True),
        sa.Column('completed_at', sa.Text(), nullable=True),
        sa.Column('created_at', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='skill',
    )
