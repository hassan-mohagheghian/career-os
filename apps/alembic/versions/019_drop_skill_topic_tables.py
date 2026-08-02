"""Drop unused skill_topic tables (skill_topics, skill_topic_progress, skill_topic_jobs).

Revision ID: 019_drop_skill_topic_tables
Revises: 018_remove_insights_tables
Create Date: 2026-07-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '019_drop_skill_topic_tables'
down_revision: Union[str, None] = '018_remove_insights_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('skill_topic_jobs')
    op.drop_table('skill_topic_progress')
    op.drop_table('skill_topics')


def downgrade() -> None:
    op.create_table(
        'skill_topics',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('skill_topics.id'), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('order', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.Text(), nullable=True),
    )
    op.create_index('idx_skill_topics_parent', 'skill_topics', ['parent_id'])

    op.create_table(
        'skill_topic_progress',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('topic_id', sa.Integer(), sa.ForeignKey('skill_topics.id', ondelete='CASCADE'), nullable=False),
        sa.Column('completed', sa.Integer(), server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.Text(), nullable=True),
    )
    op.create_index('idx_topic_progress_topic', 'skill_topic_progress', ['topic_id'])

    op.create_table(
        'skill_topic_jobs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('topic_id', sa.Integer(), sa.ForeignKey('skill_topics.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_num', sa.Integer(), nullable=False),
        sa.Column('relevance', sa.String(), nullable=True),
    )
    op.create_index('idx_topic_jobs_topic', 'skill_topic_jobs', ['topic_id'])
    op.create_index('idx_topic_jobs_job', 'skill_topic_jobs', ['job_num'])
