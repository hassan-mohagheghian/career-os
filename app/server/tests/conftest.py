"""Shared test fixtures and configuration."""

import sys
import os
import tempfile
import sqlite3
import pytest

# Add server directory to Python path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

ALL_TABLES = """
CREATE TABLE IF NOT EXISTS pending_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL, title TEXT, company TEXT, source TEXT DEFAULT 'web',
    status TEXT DEFAULT 'pending', version INTEGER DEFAULT 1,
    notes TEXT DEFAULT '[]', links TEXT DEFAULT '[]',
    job_num INTEGER,
    step_fetch INTEGER DEFAULT 0, step_validate INTEGER DEFAULT 0,
    step_extract_raw INTEGER DEFAULT 0, step_extract_struct INTEGER DEFAULT 0,
    step_summary INTEGER DEFAULT 0, step_analyze INTEGER DEFAULT 0,
    step_db INTEGER DEFAULT 0, step_done INTEGER DEFAULT 0,
    workflow_log TEXT DEFAULT '[]', error TEXT,
    queue_order INTEGER DEFAULT 0, session_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS pending_companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    input_text TEXT NOT NULL, notes TEXT DEFAULT '[]',
    links TEXT DEFAULT '[]', input_type TEXT DEFAULT 'url',
    source TEXT DEFAULT 'web', status TEXT DEFAULT 'pending', version INTEGER DEFAULT 1,
    step_fetch INTEGER DEFAULT 0, step_extract INTEGER DEFAULT 0,
    step_analyze INTEGER DEFAULT 0, step_save INTEGER DEFAULT 0,
    step_done INTEGER DEFAULT 0, company_id INTEGER,
    company_name TEXT, error TEXT,
    workflow_log TEXT DEFAULT '[]', session_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, website TEXT, domain TEXT, industry TEXT,
    country TEXT, city TEXT, description TEXT, company_size TEXT,
    company_type TEXT, logo_url TEXT, founded_year TEXT,
    headquarters_full TEXT, countries_of_operation TEXT,
    funding_stage TEXT, funding_amount TEXT, products TEXT,
    tech_stack TEXT, work_environment TEXT, extra TEXT,
    notes TEXT DEFAULT '[]', processing_status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS company_intelligence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    overview TEXT, culture_analysis TEXT, international_analysis TEXT,
    career_analysis TEXT, benefits_analysis TEXT, visa_analysis TEXT,
    technology_analysis TEXT, recommendation TEXT, scores TEXT,
    raw_source_data TEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);
CREATE TABLE IF NOT EXISTS company_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    url TEXT NOT NULL, title TEXT DEFAULT '', description TEXT DEFAULT '',
    status TEXT DEFAULT 'pending', extracted_content TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);
CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, level INTEGER, ml TEXT, mc TEXT,
    roles TEXT, path TEXT, source TEXT DEFAULT 'service',
    hidden INTEGER DEFAULT 0, merged_into TEXT DEFAULT '',
    category TEXT DEFAULT '', confidence REAL DEFAULT 0,
    market_relevance REAL DEFAULT 0, evidence TEXT DEFAULT '[]',
    source_type TEXT DEFAULT 'service', tags TEXT DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS skill_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_id INTEGER NOT NULL,
    alias_name TEXT NOT NULL,
    normalized_name TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS skill_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name TEXT NOT NULL,
    related_name TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    confidence REAL DEFAULT 0,
    UNIQUE(skill_name, related_name, relation_type)
);
CREATE TABLE IF NOT EXISTS skill_roadmaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name TEXT NOT NULL,
    parent_id INTEGER,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    level INTEGER DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS skill_roadmap_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roadmap_id INTEGER NOT NULL,
    skill_name TEXT NOT NULL,
    completed INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS skill_roadmap_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name TEXT NOT NULL,
    job_type TEXT NOT NULL DEFAULT 'generate',
    status TEXT NOT NULL DEFAULT 'queued',
    step INTEGER DEFAULT 0,
    total_steps INTEGER DEFAULT 4,
    message TEXT DEFAULT '',
    version INTEGER,
    count INTEGER,
    error TEXT,
    session_id TEXT,
    pid INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


@pytest.fixture
def test_db():
    """Create a temporary DB with all tables, return path. Auto-cleanup."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.executescript(ALL_TABLES)
    conn.commit()
    conn.close()
    yield path
    os.remove(path)


@pytest.fixture
def db_conn(test_db):
    """Return a live connection to the test DB (row_factory=sqlite3.Row)."""
    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()
