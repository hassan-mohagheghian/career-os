"""Drop career_insights, career_insight_runs, dashboard_insights, analysis_runs tables.

Revision ID: 018_remove_insights_tables
Revises: 017_add_worker_data_columns
Create Date: 2026-07-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '018_remove_insights_tables'
down_revision: Union[str, None] = '017_add_worker_data_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('analysis_runs')
    op.drop_table('dashboard_insights')
    op.drop_table('career_insight_runs')
    op.drop_table('career_insights')


def downgrade() -> None:
    op.create_table(
        'career_insights',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('insight_type', sa.Text(), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1'),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('data_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.Text(), nullable=True),
    )
    op.create_index('idx_career_insights_type', 'career_insights', ['insight_type', 'version', sa.desc('created_at')])

    op.create_table(
        'career_insight_runs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('insight_type', sa.Text(), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1'),
        sa.Column('status', sa.Text(), server_default='pending'),
        sa.Column('started_at', sa.Text(), nullable=True),
        sa.Column('completed_at', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', sa.Text(), server_default='{}'),
        sa.Column('session_id', sa.Text(), nullable=True),
    )
    op.create_index('idx_career_insight_runs_type', 'career_insight_runs', ['insight_type', 'status'])

    op.create_table(
        'dashboard_insights',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('type', sa.Text(), nullable=False),
        sa.Column('icon', sa.Text(), nullable=True),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.Integer(), server_default='0'),
        sa.Column('updated_at', sa.Text(), nullable=True),
    )

    op.create_table(
        'analysis_runs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('page', sa.Text(), nullable=False),
        sa.Column('created_at', sa.Text(), nullable=True),
        sa.Column('analysis_json', sa.Text(), nullable=False),
    )
    op.create_index('idx_analysis_runs_page', 'analysis_runs', ['page'])
    op.create_index('idx_analysis_runs_page_created', 'analysis_runs', ['page', sa.desc('created_at')])
