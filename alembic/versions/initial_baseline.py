"""Initial schema baseline - all tables.

This is the baseline migration that defines the complete database schema
as it exists before the SQLAlchemy migration. Future migrations will be
generated relative to this state.

Revision ID: initial
Revises:
Create Date: 2026-07-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Jobs ──────────────────────────────────────────────────────
    op.create_table(
        'jobs',
        sa.Column('num', sa.Integer(), primary_key=True),
        sa.Column('company', sa.Text(), nullable=True),
        sa.Column('role', sa.Text(), nullable=True),
        sa.Column('location', sa.Text(), nullable=True),
        sa.Column('match', sa.Text(), nullable=True),
        sa.Column('score', sa.Text(), nullable=True),
        sa.Column('success', sa.Text(), nullable=True),
        sa.Column('salary', sa.Text(), nullable=True),
        sa.Column('stack', sa.Text(), nullable=True),
        sa.Column('visa', sa.Text(), nullable=True),
        sa.Column('applicants', sa.Text(), nullable=True),
        sa.Column('posted', sa.Text(), nullable=True),
        sa.Column('industry', sa.Text(), nullable=True),
        sa.Column('domain', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('action', sa.Text(), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('work_type', sa.Text(), server_default='On-site'),
        sa.Column('workflow_log', sa.Text(), server_default='[]'),
        sa.Column('locations', sa.Text(), server_default='[]'),
        sa.Column('deleted', sa.Integer(), server_default='0'),
        sa.Column('employment_type', sa.Text(), server_default='Full-time'),
        sa.Column('work_types', sa.Text(), server_default='[]'),
        sa.Column('raw_description', sa.Text(), nullable=True),
        sa.Column('structured_description', sa.Text(), nullable=True),
        sa.Column('adv_at', sa.Text(), nullable=True),
        sa.Column('see_at', sa.Text(), nullable=True),
        sa.Column('apply_reason', sa.Text(), nullable=True),
        sa.Column('fit_score', sa.Integer(), nullable=True),
        sa.Column('success_score', sa.Integer(), nullable=True),
        sa.Column('overall_score', sa.Integer(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.Text(), nullable=True),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('apply_time', sa.Text(), nullable=True),
        sa.Column('response_time', sa.Text(), nullable=True),
        sa.Column('response_status', sa.Text(), nullable=True),
        sa.Column('rescoring', sa.Integer(), server_default='0'),
    )

    # ── Summaries ─────────────────────────────────────────────────
    op.create_table(
        'summaries',
        sa.Column('num', sa.Integer(), primary_key=True),
        sa.Column('company', sa.Text(), nullable=True),
        sa.Column('match', sa.Text(), nullable=True),
        sa.Column('score', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('stack', sa.Text(), nullable=True),
        sa.Column('resumeFit', sa.Text(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
    )

    # ── Resumes ───────────────────────────────────────────────────
    op.create_table(
        'resumes',
        sa.Column('id', sa.Text(), primary_key=True),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('company', sa.Text(), nullable=True),
        sa.Column('role', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1'),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.Text(), nullable=True),
        sa.Column('job_num', sa.Integer(), nullable=True),
    )

    # ── Tech Learning ─────────────────────────────────────────────
    op.create_table(
        'tech_learning',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.Text(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('pl', sa.Text(), nullable=True),
        sa.Column('pc', sa.Text(), nullable=True),
        sa.Column('sc', sa.Text(), nullable=True),
        sa.Column('dc', sa.Text(), nullable=True),
        sa.Column('usage', sa.Integer(), nullable=True),
        sa.Column('uc', sa.Text(), nullable=True),
        sa.Column('jobs', sa.Text(), nullable=True),
        sa.Column('jd', sa.Text(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('action', sa.Text(), nullable=True),
    )

    # ── Skills ────────────────────────────────────────────────────
    op.create_table(
        'skills',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.Text(), unique=True, nullable=False),
        sa.Column('level', sa.Integer(), server_default='1'),
        sa.Column('ml', sa.Text(), nullable=True),
        sa.Column('mc', sa.Text(), nullable=True),
        sa.Column('roles', sa.Text(), server_default=''),
        sa.Column('path', sa.Text(), server_default=''),
        sa.Column('source', sa.Text(), server_default='service'),
        sa.Column('hidden', sa.Integer(), server_default='0'),
        sa.Column('merged_into', sa.Text(), server_default=''),
        sa.Column('category', sa.Text(), server_default=''),
        sa.Column('confidence', sa.Float(), server_default='0'),
        sa.Column('market_relevance', sa.Float(), server_default='0'),
        sa.Column('evidence', sa.Text(), server_default='[]'),
        sa.Column('source_type', sa.Text(), server_default='service'),
        sa.Column('tags', sa.Text(), server_default='[]'),
        sa.Column('created_at', sa.Text(), nullable=True),
    )

    # ── Skill Relationships ───────────────────────────────────────
    op.create_table(
        'skill_relationships',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('skill_name', sa.Text(), nullable=False),
        sa.Column('related_name', sa.Text(), nullable=False),
        sa.Column('relation_type', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), server_default='0'),
        sa.UniqueConstraint('skill_name', 'related_name', 'relation_type'),
    )

    # ── Skill Aliases ─────────────────────────────────────────────
    op.create_table(
        'skill_aliases',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('skill_id', sa.Integer(), sa.ForeignKey('skills.id'), nullable=False),
        sa.Column('alias_name', sa.Text(), nullable=False),
        sa.Column('normalized_name', sa.Text(), server_default=''),
        sa.Column('created_at', sa.Text(), nullable=True),
    )

    # ── Skill Roadmaps ────────────────────────────────────────────
    op.create_table(
        'skill_roadmaps',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('skill_name', sa.Text(), nullable=False),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('skill_roadmaps.id'), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), server_default=''),
        sa.Column('level', sa.Integer(), server_default='0'),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('version', sa.Integer(), server_default='1'),
        sa.Column('numbering', sa.Text(), nullable=True),
        sa.Column('created_at', sa.Text(), nullable=True),
    )

    # ── Skill Roadmap Progress ────────────────────────────────────
    op.create_table(
        'skill_roadmap_progress',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('roadmap_id', sa.Integer(), sa.ForeignKey('skill_roadmaps.id', ondelete='CASCADE'), nullable=False),
        sa.Column('skill_name', sa.Text(), nullable=False),
        sa.Column('completed', sa.Integer(), server_default='0'),
        sa.Column('updated_at', sa.Text(), nullable=True),
        sa.UniqueConstraint('roadmap_id'),
    )

    # ── Skill Roadmap Jobs ────────────────────────────────────────
    op.create_table(
        'skill_roadmap_jobs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('skill_name', sa.Text(), nullable=False),
        sa.Column('job_type', sa.Text(), server_default='generate'),
        sa.Column('status', sa.Text(), server_default='queued'),
        sa.Column('step', sa.Integer(), server_default='0'),
        sa.Column('total_steps', sa.Integer(), server_default='4'),
        sa.Column('message', sa.Text(), server_default=''),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.Column('count', sa.Integer(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('session_id', sa.Text(), nullable=True),
        sa.Column('provider_name', sa.Text(), nullable=True),
        sa.Column('pid', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.Text(), nullable=True),
        sa.Column('completed_at', sa.Text(), nullable=True),
        sa.Column('created_at', sa.Text(), nullable=True),
    )

    # ── Cities ────────────────────────────────────────────────────
    op.create_table(
        'cities',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('icon', sa.Text(), nullable=True),
        sa.Column('name', sa.Text(), nullable=True),
        sa.Column('info', sa.Text(), nullable=True),
        sa.Column('jobs', sa.Text(), nullable=True),
    )

    # ── Pending Jobs ──────────────────────────────────────────────
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
    )

    # ── Pending Generations ───────────────────────────────────────
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

    # ── Dashboard Insights ────────────────────────────────────────
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

    # ── Preferences ───────────────────────────────────────────────
    op.create_table(
        'preferences',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('category', sa.Text(), nullable=False),
        sa.Column('rule_type', sa.Text(), server_default='job'),
        sa.Column('scope', sa.Text(), server_default='JOB'),
        sa.Column('key', sa.Text(), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.Integer(), server_default='0'),
        sa.Column('score_weight', sa.Integer(), server_default='0'),
        sa.Column('enabled', sa.Integer(), server_default='1'),
        sa.Column('updated_at', sa.Text(), nullable=True),
        sa.UniqueConstraint('category', 'key'),
    )

    # ── Analysis Runs ─────────────────────────────────────────────
    op.create_table(
        'analysis_runs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('page', sa.Text(), nullable=False),
        sa.Column('created_at', sa.Text(), nullable=True),
        sa.Column('analysis_json', sa.Text(), nullable=False),
    )
    op.create_index('idx_analysis_runs_page', 'analysis_runs', ['page'])
    op.create_index('idx_analysis_runs_page_created', 'analysis_runs', ['page', sa.text('created_at DESC')])

    # ── Pending Companies ─────────────────────────────────────────
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
        sa.Column('created_at', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.Text(), nullable=True),
    )
    op.create_index('idx_pending_companies_status', 'pending_companies', ['status'])

    # ── Companies ─────────────────────────────────────────────────
    op.create_table(
        'companies',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.Text(), nullable=True),
        sa.Column('website', sa.Text(), nullable=True),
        sa.Column('domain', sa.Text(), nullable=True),
        sa.Column('industry', sa.Text(), nullable=True),
        sa.Column('country', sa.Text(), nullable=True),
        sa.Column('city', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('company_size', sa.Text(), nullable=True),
        sa.Column('company_type', sa.Text(), nullable=True),
        sa.Column('logo_url', sa.Text(), nullable=True),
        sa.Column('founded_year', sa.Text(), nullable=True),
        sa.Column('headquarters_full', sa.Text(), nullable=True),
        sa.Column('countries_of_operation', sa.Text(), nullable=True),
        sa.Column('funding_stage', sa.Text(), nullable=True),
        sa.Column('funding_amount', sa.Text(), nullable=True),
        sa.Column('products', sa.Text(), nullable=True),
        sa.Column('tech_stack', sa.Text(), nullable=True),
        sa.Column('work_environment', sa.Text(), nullable=True),
        sa.Column('extra', sa.Text(), nullable=True),
        sa.Column('processing_status', sa.Text(), server_default='pending'),
        sa.Column('created_at', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.Text(), nullable=True),
    )
    op.create_index('idx_companies_name', 'companies', ['name'])

    # ── Company Intelligence ──────────────────────────────────────
    op.create_table(
        'company_intelligence',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('overview', sa.Text(), nullable=True),
        sa.Column('culture_analysis', sa.Text(), nullable=True),
        sa.Column('international_analysis', sa.Text(), nullable=True),
        sa.Column('career_analysis', sa.Text(), nullable=True),
        sa.Column('benefits_analysis', sa.Text(), nullable=True),
        sa.Column('visa_analysis', sa.Text(), nullable=True),
        sa.Column('technology_analysis', sa.Text(), nullable=True),
        sa.Column('recommendation', sa.Text(), nullable=True),
        sa.Column('scores', sa.Text(), nullable=True),
        sa.Column('raw_source_data', sa.Text(), nullable=True),
        sa.Column('generated_at', sa.Text(), nullable=True),
    )
    op.create_index('idx_company_intelligence_company_id', 'company_intelligence', ['company_id'])

    # ── Company Links ─────────────────────────────────────────────
    op.create_table(
        'company_links',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=True),
        sa.Column('extracted_content', sa.Text(), nullable=True),
        sa.Column('created_at', sa.Text(), nullable=True),
    )
    op.create_index('idx_company_links_company_id', 'company_links', ['company_id'])

    # ── Career Insights ───────────────────────────────────────────
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
    op.create_index('idx_career_insights_type', 'career_insights', ['insight_type', 'version', sa.text('created_at DESC')])

    # ── Career Insight Runs ───────────────────────────────────────
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


def downgrade() -> None:
    op.drop_table('career_insight_runs')
    op.drop_table('career_insights')
    op.drop_table('company_links')
    op.drop_table('company_intelligence')
    op.drop_table('companies')
    op.drop_table('pending_companies')
    op.drop_table('analysis_runs')
    op.drop_table('preferences')
    op.drop_table('dashboard_insights')
    op.drop_table('pending_generations')
    op.drop_table('pending_jobs')
    op.drop_table('cities')
    op.drop_table('skill_roadmap_jobs')
    op.drop_table('skill_roadmap_progress')
    op.drop_table('skill_roadmaps')
    op.drop_table('skill_aliases')
    op.drop_table('skill_relationships')
    op.drop_table('skills')
    op.drop_table('tech_learning')
    op.drop_table('resumes')
    op.drop_table('summaries')
    op.drop_table('jobs')
