"""Initial schema - captures current database state

Revision ID: 001
Revises:
Create Date: 2025-07-21
"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            num INTEGER PRIMARY KEY,
            company TEXT, role TEXT, location TEXT, match TEXT,
            score TEXT, success TEXT, salary TEXT, stack TEXT, visa TEXT,
            applicants TEXT, posted TEXT, industry TEXT,
            domain TEXT, notes TEXT, action TEXT, url TEXT,
            work_type TEXT DEFAULT 'On-site',
            workflow_log TEXT DEFAULT '[]',
            locations TEXT DEFAULT '[]',
            deleted INTEGER DEFAULT 0,
            employment_type TEXT DEFAULT 'Full-time',
            work_types TEXT DEFAULT '[]',
            raw_description TEXT,
            structured_description TEXT,
            raw_file_path TEXT,
            structured_file_path TEXT,
            rescoring INTEGER DEFAULT 0,
            adv_at TEXT,
            see_at TEXT,
            apply_reason TEXT,
            company_url TEXT,
            linkedin_url TEXT,
            apply_time TEXT,
            response_time TEXT,
            response_status TEXT
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            num INTEGER PRIMARY KEY,
            company TEXT, match TEXT, score TEXT,
            summary TEXT, stack TEXT, resumeFit TEXT, note TEXT, url TEXT
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id TEXT PRIMARY KEY,
            title TEXT, company TEXT, role TEXT, content TEXT,
            version INTEGER DEFAULT 1,
            raw_text TEXT,
            created_at TEXT,
            job_num INTEGER
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS pending_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            source TEXT DEFAULT 'cli',
            status TEXT DEFAULT 'queued',
            step_fetch INTEGER DEFAULT 0,
            step_analyze INTEGER DEFAULT 0,
            step_resume INTEGER DEFAULT 0,
            step_cover INTEGER DEFAULT 0,
            step_db INTEGER DEFAULT 0,
            step_done INTEGER DEFAULT 0,
            step_extract_raw INTEGER DEFAULT 0,
            step_extract_struct INTEGER DEFAULT 0,
            step_summary INTEGER DEFAULT 0,
            step_validate INTEGER DEFAULT 0,
            job_num INTEGER,
            company TEXT,
            error TEXT,
            workflow_log TEXT DEFAULT '[]',
            queue_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            description TEXT,
            priority INTEGER DEFAULT 0,
            enabled INTEGER DEFAULT 1,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category, key)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS dashboard_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            icon TEXT,
            title TEXT,
            description TEXT,
            priority INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS tech_learning (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, priority INTEGER, pl TEXT, pc TEXT,
            sc TEXT, dc TEXT, usage INTEGER, uc TEXT,
            jobs TEXT, jd TEXT, reason TEXT, action TEXT
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS tech_stack (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, level INTEGER, ml TEXT, mc TEXT,
            roles TEXT, path TEXT
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS analysis_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            analysis_json TEXT NOT NULL
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS cities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            icon TEXT, name TEXT, info TEXT, jobs TEXT
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Indexes
    op.execute("CREATE INDEX IF NOT EXISTS idx_jobs_url ON jobs(url)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_jobs_posted_at ON jobs(posted_at)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_analysis_runs_page ON analysis_runs(page)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_analysis_runs_page_created ON analysis_runs(page, created_at DESC)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS jobs")
    op.execute("DROP TABLE IF EXISTS summaries")
    op.execute("DROP TABLE IF EXISTS resumes")
    op.execute("DROP TABLE IF EXISTS pending_jobs")
    op.execute("DROP TABLE IF EXISTS preferences")
    op.execute("DROP TABLE IF EXISTS dashboard_insights")
    op.execute("DROP TABLE IF EXISTS tech_learning")
    op.execute("DROP TABLE IF EXISTS tech_stack")
    op.execute("DROP TABLE IF EXISTS analysis_runs")
    op.execute("DROP TABLE IF EXISTS cities")
    op.execute("DROP TABLE IF EXISTS metadata")
