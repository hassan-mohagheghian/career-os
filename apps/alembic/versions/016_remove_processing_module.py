"""Remove processing module: add lifecycle columns to jobs/companies, drop pending tables.

- Add status + lifecycle columns to jobs table
- Rename processing_status -> status on companies, add lifecycle columns
- Migrate data from pending_jobs/pending_companies to jobs/companies
- Drop pending_jobs, pending_companies, pending_generations tables

Revision ID: 016_remove_processing_module
Revises: 015_add_company_tracking
Create Date: 2026-07-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '016_remove_processing_module'
down_revision: Union[str, None] = '015_add_company_tracking'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Jobs: add lifecycle columns ─────────────────────────────────
    with op.batch_alter_table('jobs') as batch_op:
        batch_op.add_column(sa.Column('status', sa.Text(), server_default='pending'))
        batch_op.add_column(sa.Column('queue_order', sa.Integer(), server_default='0'))
        batch_op.add_column(sa.Column('current_node', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('progress_pct', sa.Integer(), server_default='0'))
        batch_op.add_column(sa.Column('error', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('retry_count', sa.Integer(), server_default='0'))
        batch_op.add_column(sa.Column('failure_reason', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('failure_step', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('failure_timestamp', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('session_id', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('previous_status', sa.Text(), nullable=True))

    # Migrate pending_jobs status to jobs table
    op.execute("""
        UPDATE jobs SET
            status = COALESCE(
                (SELECT CASE
                    WHEN pj.status IN ('completed', 'done') THEN 'completed'
                    WHEN pj.status IN ('failed', 'error') THEN 'failed'
                    WHEN pj.status = 'queued' THEN 'queued'
                    WHEN pj.status IN ('starting', 'waiting', 'fetching', 'analyzing',
                                       'generating', 'finalizing') THEN 'processing'
                    WHEN pj.status = 'cancelled' THEN 'cancelled'
                    ELSE 'pending'
                END
                FROM pending_jobs pj WHERE pj.job_num = jobs.num ORDER BY pj.id DESC LIMIT 1),
                'pending'
            ),
            error = (SELECT pj.error FROM pending_jobs pj WHERE pj.job_num = jobs.num AND pj.error IS NOT NULL ORDER BY pj.id DESC LIMIT 1),
            queue_order = COALESCE((SELECT pj.queue_order FROM pending_jobs pj WHERE pj.job_num = jobs.num ORDER BY pj.id DESC LIMIT 1), 0),
            session_id = (SELECT pj.session_id FROM pending_jobs pj WHERE pj.job_num = jobs.num AND pj.session_id IS NOT NULL ORDER BY pj.id DESC LIMIT 1),
            retry_count = COALESCE((SELECT pj.retry_count FROM pending_jobs pj WHERE pj.job_num = jobs.num ORDER BY pj.id DESC LIMIT 1), 0)
    """)

    # ── Companies: rename processing_status -> status, add lifecycle columns ──
    with op.batch_alter_table('companies') as batch_op:
        batch_op.add_column(sa.Column('new_status', sa.Text(), server_default='pending'))
        batch_op.add_column(sa.Column('queue_order', sa.Integer(), server_default='0'))
        batch_op.add_column(sa.Column('current_node', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('progress_pct', sa.Integer(), server_default='0'))
        batch_op.add_column(sa.Column('error', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('retry_count', sa.Integer(), server_default='0'))
        batch_op.add_column(sa.Column('failure_reason', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('failure_step', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('failure_timestamp', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('session_id', sa.Text(), nullable=True))

    # Copy processing_status to new_status with mapping
    op.execute("""
        UPDATE companies SET new_status = CASE
            WHEN processing_status IN ('completed', 'done') THEN 'completed'
            WHEN processing_status IN ('failed', 'error') THEN 'failed'
            WHEN processing_status = 'queued' THEN 'queued'
            WHEN processing_status IN ('starting', 'waiting', 'fetching', 'analyzing',
                                       'generating', 'finalizing', 'processing') THEN 'processing'
            WHEN processing_status = 'cancelled' THEN 'cancelled'
            ELSE 'pending'
        END
    """)

    # Drop old processing_status
    with op.batch_alter_table('companies') as batch_op:
        batch_op.drop_column('processing_status')

    # Rename new_status to status
    with op.batch_alter_table('companies') as batch_op:
        batch_op.alter_column('new_status', new_column_name='status')

    # Migrate pending_companies data to companies
    op.execute("""
        UPDATE companies SET
            error = (SELECT pc.error FROM pending_companies pc WHERE pc.company_id = companies.id AND pc.error IS NOT NULL ORDER BY pc.id DESC LIMIT 1),
            session_id = (SELECT pc.session_id FROM pending_companies pc WHERE pc.company_id = companies.id AND pc.session_id IS NOT NULL ORDER BY pc.id DESC LIMIT 1),
            retry_count = COALESCE((SELECT pc.retry_count FROM pending_companies pc WHERE pc.company_id = companies.id ORDER BY pc.id DESC LIMIT 1), 0)
    """)

    # Create new pending companies that have no associated company_id
    op.execute("""
        INSERT OR IGNORE INTO companies (name, status, created_at, updated_at)
        SELECT pc.input_text, CASE
            WHEN pc.status IN ('completed', 'done') THEN 'completed'
            WHEN pc.status IN ('failed', 'error') THEN 'failed'
            WHEN pc.status = 'queued' THEN 'queued'
            WHEN pc.status IN ('starting', 'waiting', 'fetching', 'analyzing',
                               'generating', 'finalizing', 'processing') THEN 'processing'
            WHEN pc.status = 'cancelled' THEN 'cancelled'
            ELSE 'pending'
        END, pc.created_at, pc.updated_at
        FROM pending_companies pc
        WHERE pc.company_id IS NULL
    """)

    # ── Drop pending tables ─────────────────────────────────────────
    op.drop_table('pending_generations')
    op.drop_table('pending_companies')
    op.drop_table('pending_jobs')

    # ── Create indexes ──────────────────────────────────────────────
    op.create_index('idx_jobs_status', 'jobs', ['status'])
    op.create_index('idx_companies_status', 'companies', ['status'])


def downgrade() -> None:
    # Remove indexes
    op.drop_index('idx_companies_status', table_name='companies')
    op.drop_index('idx_jobs_status', table_name='jobs')

    # Recreate pending tables
    op.create_table(
        'pending_jobs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('url', sa.Text(), unique=True, nullable=True),
        sa.Column('source', sa.Text(), server_default='cli'),
        sa.Column('status', sa.Text(), server_default='queued'),
        sa.Column('version', sa.Integer(), server_default='1'),
        sa.Column('notes', sa.Text(), server_default='[]'),
        sa.Column('links', sa.Text(), server_default='[]'),
        sa.Column('step_fetch', sa.Integer(), server_default='0'),
        sa.Column('step_analyze', sa.Integer(), server_default='0'),
        sa.Column('step_resume', sa.Integer(), server_default='0'),
        sa.Column('step_cover', sa.Integer(), server_default='0'),
        sa.Column('step_db', sa.Integer(), server_default='0'),
        sa.Column('step_done', sa.Integer(), server_default='0'),
        sa.Column('job_num', sa.Integer(), nullable=True),
        sa.Column('company', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('workflow_log', sa.Text(), server_default='[]'),
        sa.Column('created_at', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.Text(), nullable=True),
        sa.Column('queue_order', sa.Integer(), server_default='0'),
        sa.Column('step_extract_raw', sa.Integer(), server_default='0'),
        sa.Column('step_extract_struct', sa.Integer(), server_default='0'),
        sa.Column('session_id', sa.Text(), nullable=True),
        sa.Column('previous_status', sa.Text(), nullable=True),
        sa.Column('current_node', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0'),
        sa.Column('failure_details', sa.Text(), nullable=True),
        sa.Column('auto_process', sa.Integer(), server_default='1'),
    )
    op.create_table(
        'pending_companies',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('input_text', sa.Text(), nullable=False),
        sa.Column('notes', sa.Text(), server_default='[]'),
        sa.Column('input_type', sa.Text(), server_default='url'),
        sa.Column('source', sa.Text(), server_default='web'),
        sa.Column('status', sa.Text(), server_default='pending'),
        sa.Column('version', sa.Integer(), server_default='1'),
        sa.Column('step_fetch', sa.Integer(), server_default='0'),
        sa.Column('step_extract', sa.Integer(), server_default='0'),
        sa.Column('step_analyze', sa.Integer(), server_default='0'),
        sa.Column('step_save', sa.Integer(), server_default='0'),
        sa.Column('step_done', sa.Integer(), server_default='0'),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('company_name', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('workflow_log', sa.Text(), server_default='[]'),
        sa.Column('links', sa.Text(), server_default='[]'),
        sa.Column('session_id', sa.Text(), nullable=True),
        sa.Column('created_at', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.Text(), nullable=True),
        sa.Column('previous_status', sa.Text(), nullable=True),
        sa.Column('current_node', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0'),
        sa.Column('failure_details', sa.Text(), nullable=True),
    )
    op.create_table(
        'pending_generations',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('job_num', sa.Integer(), nullable=False),
        sa.Column('type', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), server_default='queued'),
        sa.Column('step_prepare', sa.Integer(), server_default='0'),
        sa.Column('step_context', sa.Integer(), server_default='0'),
        sa.Column('step_generate', sa.Integer(), server_default='0'),
        sa.Column('step_save', sa.Integer(), server_default='0'),
        sa.Column('step_done', sa.Integer(), server_default='0'),
        sa.Column('result', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('session_id', sa.Text(), nullable=True),
        sa.Column('created_at', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.Text(), nullable=True),
    )

    # Remove lifecycle columns from jobs
    with op.batch_alter_table('jobs') as batch_op:
        batch_op.drop_column('session_id')
        batch_op.drop_column('failure_timestamp')
        batch_op.drop_column('failure_step')
        batch_op.drop_column('failure_reason')
        batch_op.drop_column('retry_count')
        batch_op.drop_column('error')
        batch_op.drop_column('progress_pct')
        batch_op.drop_column('current_node')
        batch_op.drop_column('queue_order')
        batch_op.drop_column('status')
        batch_op.drop_column('previous_status')

    # Restore processing_status on companies, drop lifecycle columns
    with op.batch_alter_table('companies') as batch_op:
        batch_op.add_column(sa.Column('processing_status', sa.Text(), server_default='pending'))
    op.execute("UPDATE companies SET processing_status = status")
    with op.batch_alter_table('companies') as batch_op:
        batch_op.drop_column('status')
        batch_op.drop_column('queue_order')
        batch_op.drop_column('current_node')
        batch_op.drop_column('progress_pct')
        batch_op.drop_column('error')
        batch_op.drop_column('retry_count')
        batch_op.drop_column('failure_reason')
        batch_op.drop_column('failure_step')
        batch_op.drop_column('failure_timestamp')
        batch_op.drop_column('session_id')
