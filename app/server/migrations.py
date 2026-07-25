"""Database schema migrations and startup initialization."""

import json
import sqlite3

from config import DB_PATH
from services.process.logging_config import get_logger

log = get_logger('migrate')


def ensure_db_schema():
    """Add missing columns/tables to existing databases for backward compatibility."""
    conn = sqlite3.connect(DB_PATH)

    # Jobs columns
    cursor = conn.execute("PRAGMA table_info(jobs)")
    columns = {row[1] for row in cursor.fetchall()}
    migrations = {
        "apply_time": "ALTER TABLE jobs ADD COLUMN apply_time TEXT",
        "response_time": "ALTER TABLE jobs ADD COLUMN response_time TEXT",
        "response_status": "ALTER TABLE jobs ADD COLUMN response_status TEXT",
        "company_id": "ALTER TABLE jobs ADD COLUMN company_id INTEGER",
    }
    for col, sql in migrations.items():
        if col not in columns:
            conn.execute(sql)

    # Company tables
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }

    if "pending_companies" not in tables:
        conn.execute("""CREATE TABLE IF NOT EXISTS pending_companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_text TEXT NOT NULL,
            notes TEXT DEFAULT '[]',
            input_type TEXT DEFAULT 'url',
            source TEXT DEFAULT 'web',
            status TEXT DEFAULT 'pending',
            step_fetch INTEGER DEFAULT 0,
            step_extract INTEGER DEFAULT 0,
            step_analyze INTEGER DEFAULT 0,
            step_save INTEGER DEFAULT 0,
            step_done INTEGER DEFAULT 0,
            company_id INTEGER,
            company_name TEXT,
            error TEXT,
            workflow_log TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    else:
        try:
            conn.execute("SELECT notes FROM pending_companies LIMIT 1")
        except sqlite3.OperationalError:
            conn.execute(
                "ALTER TABLE pending_companies ADD COLUMN notes TEXT DEFAULT '[]'"
            )
            rows = conn.execute(
                "SELECT id, input_text FROM pending_companies WHERE notes='[]' OR notes IS NULL"
            ).fetchall()
            for row in rows:
                notes = json.dumps(
                    [{"type": "text", "content": dict(row)["input_text"]}]
                )
                conn.execute(
                    "UPDATE pending_companies SET notes=? WHERE id=?",
                    (notes, dict(row)["id"]),
                )

    # Add links column to pending_companies
    try:
        conn.execute("SELECT links FROM pending_companies LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE pending_companies ADD COLUMN links TEXT DEFAULT '[]'")

    if "companies" not in tables:
        conn.execute("""CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, website TEXT, domain TEXT, industry TEXT,
            country TEXT, city TEXT, description TEXT, company_size TEXT,
            company_type TEXT, logo_url TEXT, founded_year TEXT,
            headquarters_full TEXT, countries_of_operation TEXT,
            funding_stage TEXT, funding_amount TEXT, products TEXT,
            skills TEXT, work_environment TEXT, extra TEXT,
            notes TEXT DEFAULT '[]', processing_status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    else:
        company_cols = {
            row[1] for row in conn.execute("PRAGMA table_info(companies)").fetchall()
        }
        for col in [
            "founded_year",
            "headquarters_full",
            "countries_of_operation",
            "funding_stage",
            "funding_amount",
            "products",
            "skills",
            "work_environment",
            "extra",
            "notes",
        ]:
            if col not in company_cols:
                conn.execute(f"ALTER TABLE companies ADD COLUMN {col} TEXT")

    if "company_intelligence" not in tables:
        conn.execute("""CREATE TABLE IF NOT EXISTS company_intelligence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            overview TEXT, culture_analysis TEXT, international_analysis TEXT,
            career_analysis TEXT, benefits_analysis TEXT, visa_analysis TEXT,
            technology_analysis TEXT, recommendation TEXT, scores TEXT,
            raw_source_data TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )""")

    if "company_links" not in tables:
        conn.execute("""CREATE TABLE IF NOT EXISTS company_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            title TEXT DEFAULT '',
            description TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            extracted_content TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )""")

    if "career_insight_runs" not in tables:
        conn.execute("""CREATE TABLE IF NOT EXISTS career_insight_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            insight_type TEXT NOT NULL,
            version INTEGER DEFAULT 1,
            status TEXT DEFAULT 'pending',
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            error_message TEXT,
            metadata TEXT DEFAULT '{}',
            session_id TEXT
        )""")
    else:
        try:
            conn.execute("SELECT session_id FROM career_insight_runs LIMIT 1")
        except sqlite3.OperationalError:
            conn.execute("ALTER TABLE career_insight_runs ADD COLUMN session_id TEXT")

    if "career_insights" not in tables:
        conn.execute("""CREATE TABLE IF NOT EXISTS career_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            insight_type TEXT NOT NULL,
            version INTEGER DEFAULT 1,
            score REAL,
            summary TEXT,
            data_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_pending_companies_status ON pending_companies(status)"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name)")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_company_intelligence_company_id ON company_intelligence(company_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_company_links_company_id ON company_links(company_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_career_insight_runs_type ON career_insight_runs(insight_type, status)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_career_insights_type ON career_insights(insight_type, version, created_at DESC)"
    )

    # Skill roadmaps tables
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if "skill_roadmaps" not in tables:
        conn.execute("""CREATE TABLE IF NOT EXISTS skill_roadmaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_name TEXT NOT NULL,
            parent_id INTEGER REFERENCES skill_roadmaps(id),
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            level INTEGER DEFAULT 0,
            sort_order INTEGER DEFAULT 0,
            version INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    else:
        # Add level column if missing
        roadmap_cols = {
            row[1]
            for row in conn.execute("PRAGMA table_info(skill_roadmaps)").fetchall()
        }
        if "level" not in roadmap_cols:
            conn.execute(
                "ALTER TABLE skill_roadmaps ADD COLUMN level INTEGER DEFAULT 0"
            )

    # Add source column to skills/tech_stack if missing (before rename migration)
    try:
        conn.execute("SELECT source FROM tech_stack LIMIT 1")
    except sqlite3.OperationalError:
        try:
            conn.execute("ALTER TABLE tech_stack ADD COLUMN source TEXT DEFAULT 'service'")
        except sqlite3.OperationalError:
            pass
    try:
        conn.execute("SELECT source FROM skills LIMIT 1")
    except sqlite3.OperationalError:
        try:
            conn.execute("ALTER TABLE skills ADD COLUMN source TEXT DEFAULT 'service'")
        except sqlite3.OperationalError:
            pass
    if "skill_roadmap_progress" not in tables:
        conn.execute("""CREATE TABLE IF NOT EXISTS skill_roadmap_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roadmap_id INTEGER NOT NULL REFERENCES skill_roadmaps(id) ON DELETE CASCADE,
            skill_name TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(roadmap_id)
        )""")
    if "skill_roadmap_jobs" not in tables:
        conn.execute("""CREATE TABLE IF NOT EXISTS skill_roadmap_jobs (
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
        )""")
    else:
        job_cols = {
            row[1]
            for row in conn.execute("PRAGMA table_info(skill_roadmap_jobs)").fetchall()
        }
        if "session_id" not in job_cols:
            conn.execute("ALTER TABLE skill_roadmap_jobs ADD COLUMN session_id TEXT")
        if "pid" not in job_cols:
            conn.execute("ALTER TABLE skill_roadmap_jobs ADD COLUMN pid INTEGER")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_skill_roadmaps_skill ON skill_roadmaps(skill_name, parent_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_skill_roadmap_progress_skill ON skill_roadmap_progress(skill_name)"
    )

    conn.commit()
    conn.close()


def run_migrations():
    """Run all data migrations on startup."""
    _migrate_numeric_scores()
    _backfill_numeric_scores()
    _migrate_rules()
    _migrate_rule_types()
    _migrate_recruiter_rules()
    _migrate_scope_column()
    _migrate_rule_groups()  # New: migrate to entity-based rule groups
    _migrate_success_field()
    _migrate_resume_files()
    _migrate_roadmap_progress_column()
    _migrate_roadmap_numbering_column()
    _migrate_pending_session_id()
    _migrate_pending_version()
    _migrate_pending_notes_links()
    _migrate_skill_management()
    _migrate_skill_taxonomy()
    _migrate_skill_aliases()
    _categorize_existing_skills()
    _migrate_rename_tech_stack_to_skills()


def _migrate_roadmap_numbering_column():
    """Add numbering column to skill_roadmaps for hierarchical display."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute("PRAGMA table_info(skill_roadmaps)")
        columns = {row[1] for row in cursor.fetchall()}
        if 'numbering' not in columns:
            log.info("migrate.adding_numbering_column")
            conn.execute("ALTER TABLE skill_roadmaps ADD COLUMN numbering TEXT DEFAULT ''")
            conn.commit()
        else:
            log.info("migrate.numbering_column_exists")
        conn.close()
    except Exception as e:
        log.warning("migrate.failed", error=str(e))


def _migrate_roadmap_progress_column():
    """Rename topic_id -> roadmap_id in skill_roadmap_progress if needed."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute("PRAGMA table_info(skill_roadmap_progress)")
        columns = {row[1] for row in cursor.fetchall()}
        if 'topic_id' in columns and 'roadmap_id' not in columns:
            log.info("migrate.renaming_roadmap_progress_column")
            conn.execute("ALTER TABLE skill_roadmap_progress RENAME COLUMN topic_id TO roadmap_id")
            conn.commit()
        conn.close()
    except Exception as e:
        log.warning("migrate.failed", error=str(e))


def _migrate_pending_session_id():
    """Add session_id column to pending_jobs and pending_companies."""
    try:
        conn = sqlite3.connect(DB_PATH)
        # pending_jobs
        cols = {row[1] for row in conn.execute("PRAGMA table_info(pending_jobs)").fetchall()}
        if 'session_id' not in cols:
            log.info("migrate.adding_pending_jobs_session_id")
            conn.execute("ALTER TABLE pending_jobs ADD COLUMN session_id TEXT")
        # pending_companies
        cols = {row[1] for row in conn.execute("PRAGMA table_info(pending_companies)").fetchall()}
        if 'session_id' not in cols:
            log.info("migrate.adding_pending_companies_session_id")
            conn.execute("ALTER TABLE pending_companies ADD COLUMN session_id TEXT")
        conn.commit()
        conn.close()
    except Exception as e:
        log.warning("migrate.failed", error=str(e))


def _migrate_pending_version():
    """Add version column to pending_jobs and pending_companies for retry tracking."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cols = {row[1] for row in conn.execute("PRAGMA table_info(pending_jobs)").fetchall()}
        if 'version' not in cols:
            log.info("migrate.adding_pending_jobs_version")
            conn.execute("ALTER TABLE pending_jobs ADD COLUMN version INTEGER DEFAULT 1")
        cols = {row[1] for row in conn.execute("PRAGMA table_info(pending_companies)").fetchall()}
        if 'version' not in cols:
            log.info("migrate.adding_pending_companies_version")
            conn.execute("ALTER TABLE pending_companies ADD COLUMN version INTEGER DEFAULT 1")
        conn.commit()
        conn.close()
    except Exception as e:
        log.warning("migrate.failed", error=str(e))


def _migrate_pending_notes_links():
    """Add notes and links columns to pending_jobs for multi-source input."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cols = {row[1] for row in conn.execute("PRAGMA table_info(pending_jobs)").fetchall()}
        if 'notes' not in cols:
            log.info("migrate.adding_pending_jobs_notes")
            conn.execute("ALTER TABLE pending_jobs ADD COLUMN notes TEXT DEFAULT '[]'")
        if 'links' not in cols:
            log.info("migrate.adding_pending_jobs_links")
            conn.execute("ALTER TABLE pending_jobs ADD COLUMN links TEXT DEFAULT '[]'")
        conn.commit()
        conn.close()
    except Exception as e:
        log.warning("migrate.failed", error=str(e))


def _migrate_skill_management():
    """Add hidden and merged_into columns to tech_stack."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cols = {row[1] for row in conn.execute("PRAGMA table_info(tech_stack)").fetchall()}
        if 'hidden' not in cols:
            log.info("migrate.adding_skills_hidden")
            conn.execute("ALTER TABLE tech_stack ADD COLUMN hidden INTEGER DEFAULT 0")
        if 'merged_into' not in cols:
            log.info("migrate.adding_skills_merged_into")
            conn.execute("ALTER TABLE tech_stack ADD COLUMN merged_into TEXT DEFAULT ''")
        conn.commit()
        conn.close()
    except Exception as e:
        log.warning("migrate.failed", error=str(e))


def _migrate_skill_taxonomy():
    """Add skill taxonomy columns and skill_relationships table."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cols = {row[1] for row in conn.execute("PRAGMA table_info(tech_stack)").fetchall()}
        for col, default in [
            ('category', "''"), ('confidence', '0'), ('market_relevance', '0'),
            ('evidence', "'[]'"), ('source_type', "'service'"), ('tags', "'[]'"),
        ]:
            if col not in cols:
                log.info(f"migrate.adding_skills_{col}")
                conn.execute(f"ALTER TABLE tech_stack ADD COLUMN {col} TEXT DEFAULT {default}" if col in ('category', 'evidence', 'source_type', 'tags') else f"ALTER TABLE tech_stack ADD COLUMN {col} REAL DEFAULT {default}")
        # Create skill_relationships table if not exists
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if 'skill_relationships' not in tables:
            log.info("migrate.creating_skill_relationships")
            conn.execute("""CREATE TABLE IF NOT EXISTS skill_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name TEXT NOT NULL,
                related_name TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                confidence REAL DEFAULT 0,
                UNIQUE(skill_name, related_name, relation_type)
            )""")
        conn.commit()
        conn.close()
    except Exception as e:
        log.warning("migrate.failed", error=str(e))


def _migrate_skill_aliases():
    """Create skill_aliases table for merged skills."""
    try:
        conn = sqlite3.connect(DB_PATH)
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if 'skill_aliases' not in tables:
            log.info("migrate.creating_skill_aliases")
            conn.execute("""CREATE TABLE IF NOT EXISTS skill_aliases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id INTEGER NOT NULL,
                alias_name TEXT NOT NULL,
                normalized_name TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (skill_id) REFERENCES tech_stack(id)
            )""")
        # Migrate existing merged_into data to skill_aliases
        rows = conn.execute("SELECT id, name, merged_into FROM tech_stack WHERE merged_into != '' AND merged_into IS NOT NULL").fetchall()
        for skill_id, name, merged_into in rows:
            # Find the canonical skill
            canonical = conn.execute("SELECT id FROM tech_stack WHERE name=?", (merged_into,)).fetchone()
            if canonical:
                # Check if alias already exists
                existing = conn.execute("SELECT id FROM skill_aliases WHERE skill_id=? AND alias_name=?", (canonical[0], name)).fetchone()
                if not existing:
                    conn.execute("INSERT INTO skill_aliases (skill_id, alias_name, normalized_name) VALUES (?, ?, ?)",
                        (canonical[0], name, name.lower()))
                    log.info(f"migrate.migrating_alias {name} -> {merged_into}")
        conn.commit()
        conn.close()
    except Exception as e:
        log.warning("migrate.failed", error=str(e))


# Skill categorization map — maps skill name patterns to categories
_SKILL_CATEGORIES = {
    # Technical
    'python': 'technical', 'javascript': 'technical', 'typescript': 'technical',
    'java': 'technical', 'go': 'technical', 'rust': 'technical', 'c++': 'technical',
    'c#': 'technical', 'ruby': 'technical', 'php': 'technical', 'swift': 'technical',
    'kotlin': 'technical', 'scala': 'technical', 'elixir': 'technical',
    'sql': 'technical', 'nosql': 'technical', 'graphql': 'technical', 'rest': 'technical',
    'html': 'technical', 'css': 'technical', 'scss': 'technical', 'sass': 'technical',
    'react': 'technical', 'angular': 'technical', 'vue': 'technical', 'svelte': 'technical',
    'next.js': 'technical', 'nextjs': 'technical', 'nuxt': 'technical',
    'node.js': 'technical', 'nodejs': 'technical', 'deno': 'technical', 'bun': 'technical',
    'django': 'technical', 'flask': 'technical', 'fastapi': 'technical', 'fastapi': 'technical',
    'express': 'technical', 'spring': 'technical', 'rails': 'technical', 'laravel': 'technical',
    'asp.net': 'technical', 'dotnet': 'technical',
    'docker': 'technical', 'kubernetes': 'technical', 'k8s': 'technical',
    'aws': 'technical', 'azure': 'technical', 'gcp': 'technical', 'cloud': 'technical',
    'terraform': 'technical', 'ansible': 'technical', 'puppet': 'technical',
    'jenkins': 'technical', 'ci/cd': 'technical', 'github actions': 'technical',
    'gitlab': 'technical', 'github': 'technical',
    'postgresql': 'technical', 'postgres': 'technical', 'mysql': 'technical',
    'mongodb': 'technical', 'redis': 'technical', 'elasticsearch': 'technical',
    'kafka': 'technical', 'rabbitmq': 'technical', 'cassandra': 'technical',
    'sqlite': 'technical', 'dynamodb': 'technical', 'cosmosdb': 'technical',
    'linux': 'technical', 'bash': 'technical', 'shell': 'technical', 'powershell': 'technical',
    'nginx': 'technical', 'apache': 'technical', 'haproxy': 'technical',
    'prometheus': 'technical', 'grafana': 'technical', 'datadog': 'technical',
    'splunk': 'technical', 'elk': 'technical',
    'machine learning': 'technical', 'ml': 'technical', 'ai': 'technical',
    'deep learning': 'technical', 'nlp': 'technical', 'computer vision': 'technical',
    'pytorch': 'technical', 'tensorflow': 'technical', 'scikit-learn': 'technical',
    'pandas': 'technical', 'numpy': 'technical', 'jupyter': 'technical',
    'spark': 'technical', 'hadoop': 'technical', 'airflow': 'technical',
    'dbt': 'technical', 'snowflake': 'technical', 'bigquery': 'technical',
    'redshift': 'technical', 'etl': 'technical', 'data engineering': 'technical',
    'api': 'technical', 'microservices': 'technical', 'serverless': 'technical',
    'websockets': 'technical', 'grpc': 'technical', 'protobuf': 'technical',
    'oauth': 'technical', 'jwt': 'technical', 'saml': 'technical',
    'cryptography': 'technical', 'encryption': 'technical', 'security': 'technical',
    'penetration testing': 'technical', 'owasp': 'technical',
    'blockchain': 'technical', 'web3': 'technical', 'solidity': 'technical',
    'regex': 'technical', 'json': 'technical', 'xml': 'technical', 'yaml': 'technical',
    'vim': 'technical', 'vscode': 'technical', 'intellij': 'technical',
    'postman': 'technical', 'swagger': 'technical', 'openapi': 'technical',
    # Engineering
    'agile': 'engineering', 'scrum': 'engineering', 'kanban': 'engineering',
    'sprint': 'engineering', 'standup': 'engineering', 'retrospective': 'engineering',
    'tdd': 'engineering', 'test driven': 'engineering', 'unit testing': 'engineering',
    'integration testing': 'engineering', 'e2e testing': 'engineering',
    'ci/cd': 'engineering', 'code review': 'engineering', 'pull request': 'engineering',
    'pair programming': 'engineering', 'mob programming': 'engineering',
    'refactoring': 'engineering', 'clean code': 'engineering', 'solid': 'engineering',
    'design patterns': 'engineering', 'architecture': 'engineering',
    'microservices': 'engineering', 'monolith': 'engineering', 'soa': 'engineering',
    'ddd': 'engineering', 'domain driven': 'engineering',
    'event driven': 'engineering', 'cqrs': 'engineering', 'event sourcing': 'engineering',
    'load testing': 'engineering', 'performance testing': 'engineering',
    'chaos engineering': 'engineering', 'observability': 'engineering',
    'monitoring': 'engineering', 'logging': 'engineering', 'tracing': 'engineering',
    'technical debt': 'engineering', 'code quality': 'engineering',
    'documentation': 'engineering', 'adr': 'engineering',
    'feature flags': 'engineering', 'canary': 'engineering', 'blue green': 'engineering',
    'rolling deployment': 'engineering', 'gitops': 'engineering',
    'infrastructure as code': 'engineering', 'containerization': 'engineering',
    'orchestration': 'engineering', 'service mesh': 'engineering',
    'api design': 'engineering', 'system design': 'engineering',
    'database design': 'engineering', 'data modeling': 'engineering',
    # Professional
    'communication': 'professional', 'presentation': 'professional',
    'public speaking': 'professional', 'writing': 'professional',
    'technical writing': 'professional', 'storytelling': 'professional',
    'collaboration': 'professional', 'teamwork': 'professional',
    'leadership': 'professional', 'mentoring': 'professional', 'coaching': 'professional',
    'management': 'professional', 'delegation': 'professional',
    'stakeholder management': 'professional', 'expectation management': 'professional',
    'conflict resolution': 'professional', 'negotiation': 'professional',
    'influence': 'professional', 'persuasion': 'professional',
    'empathy': 'professional', 'emotional intelligence': 'professional',
    'adaptability': 'professional', 'flexibility': 'professional',
    'problem solving': 'professional', 'critical thinking': 'professional',
    'analytical thinking': 'professional', 'creative thinking': 'professional',
    'decision making': 'professional', 'judgment': 'professional',
    'time management': 'professional', 'prioritization': 'professional',
    'organization': 'professional', 'planning': 'professional',
    'ownership': 'professional', 'accountability': 'professional',
    'initiative': 'professional', 'proactive': 'professional',
    'attention to detail': 'professional', 'quality focus': 'professional',
    'continuous learning': 'professional', 'curiosity': 'professional',
    'feedback': 'professional', 'self-awareness': 'professional',
    'resilience': 'professional', 'stress management': 'professional',
    'work life balance': 'professional',
    # Domain
    'fintech': 'domain', 'banking': 'domain', 'payments': 'domain',
    'trading': 'domain', 'quantitative': 'domain', 'risk management': 'domain',
    'compliance': 'domain', 'regulatory': 'domain', 'kyc': 'domain', 'aml': 'domain',
    'healthcare': 'domain', 'medical': 'domain', 'pharma': 'domain',
    'hipaa': 'domain', 'ehr': 'domain', 'clinical': 'domain',
    'ecommerce': 'domain', 'retail': 'domain', 'supply chain': 'domain',
    'logistics': 'domain', 'inventory': 'domain', 'warehouse': 'domain',
    'edtech': 'domain', 'education': 'domain', 'lms': 'domain',
    'gaming': 'domain', 'game development': 'domain', 'unity': 'domain', 'unreal': 'domain',
    'automotive': 'domain', 'manufacturing': 'domain', 'iot': 'domain',
    'telecommunications': 'domain', 'telco': 'domain',
    'energy': 'domain', 'renewable': 'domain', 'utilities': 'domain',
    'real estate': 'domain', 'proptech': 'domain',
    'legal': 'domain', 'regtech': 'domain', 'insurtech': 'domain',
    'saas': 'domain', 'paas': 'domain', 'iaas': 'domain',
    'product management': 'domain', 'agile product': 'domain',
    'user research': 'domain', 'ux research': 'domain',
    'market analysis': 'domain', 'competitive analysis': 'domain',
    'business strategy': 'domain', 'go to market': 'domain',
    # Career
    'networking': 'career', 'professional networking': 'career',
    'linkedin': 'career', 'personal branding': 'career',
    'resume': 'career', 'cover letter': 'career',
    'interviewing': 'career', 'technical interview': 'career',
    'behavioral interview': 'career', 'system design interview': 'career',
    'salary negotiation': 'career', 'career planning': 'career',
    'career development': 'career', 'career growth': 'career',
    'job search': 'career', 'job hunting': 'career',
    'portfolio': 'career', 'github portfolio': 'career',
    'open source': 'career', 'blogging': 'career', 'tech blogging': 'career',
    'speaking': 'career', 'conference speaking': 'career', 'meetup': 'career',
    'mentoring': 'career', 'coaching': 'career',
    'certification': 'career', 'aws certification': 'career',
    'gcp certification': 'career', 'azure certification': 'career',
    'pmp': 'career', 'scrum master': 'career',
    'visa': 'career', 'work permit': 'career', 'relocation': 'career',
    'german': 'career', 'english': 'career', 'language': 'career',
    'multilingual': 'career', 'bilingual': 'career',
}


def _categorize_existing_skills():
    """Categorize uncategorized skills based on name matching."""
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT id, name FROM tech_stack WHERE category='' OR category IS NULL").fetchall()
        if not rows:
            conn.close()
            return
        categorized = 0
        for skill_id, name in rows:
            name_lower = name.lower().strip()
            # Direct match
            cat = _SKILL_CATEGORIES.get(name_lower)
            # Partial match
            if not cat:
                for key, category in _SKILL_CATEGORIES.items():
                    if key in name_lower or name_lower in key:
                        cat = category
                        break
            # Default to technical if no match found
            if not cat:
                cat = 'technical'
            conn.execute("UPDATE tech_stack SET category=? WHERE id=?", (cat, skill_id))
            categorized += 1
        conn.commit()
        conn.close()
        if categorized:
            log.info(f"migrate.categorized {categorized} skills")
    except Exception as e:
        log.warning("migrate.failed", error=str(e))
    try:
        from services.worker import normalize_score

        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT num, score FROM jobs WHERE deleted=0").fetchall()
        converted = 0
        for num, score in rows:
            if isinstance(score, (int, float)):
                new_grade = normalize_score(int(score))
                conn.execute("UPDATE jobs SET score=? WHERE num=?", (new_grade, num))
                converted += 1
        rows2 = conn.execute("SELECT num, score FROM summaries").fetchall()
        for num, score in rows2:
            if isinstance(score, (int, float)):
                new_grade = normalize_score(int(score))
                conn.execute(
                    "UPDATE summaries SET score=? WHERE num=?", (new_grade, num)
                )
        if converted:
            conn.commit()
            log.info("migrate.converted_scores", count=converted)
        conn.close()
    except Exception as e:
        log.warning("migrate.failed", error=str(e))


def _migrate_numeric_scores():
    try:
        from services.worker import normalize_score

        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT num, score FROM jobs WHERE deleted=0").fetchall()
        converted = 0
        for num, score in rows:
            if isinstance(score, (int, float)):
                new_grade = normalize_score(int(score))
                conn.execute("UPDATE jobs SET score=? WHERE num=?", (new_grade, num))
                converted += 1
        rows2 = conn.execute("SELECT num, score FROM summaries").fetchall()
        for num, score in rows2:
            if isinstance(score, (int, float)):
                new_grade = normalize_score(int(score))
                conn.execute(
                    "UPDATE summaries SET score=? WHERE num=?", (new_grade, num)
                )
        if converted:
            conn.commit()
            log.info("migrate.converted_scores", count=converted)
        conn.close()
    except Exception as e:
        log.warning("migrate.failed", error=str(e))


def _backfill_numeric_scores():
    try:
        conn = sqlite3.connect(DB_PATH)
        grade_to_numeric = {
            "A++": 95,
            "A+": 85,
            "A": 75,
            "B": 60,
            "C": 40,
            "D": 20,
            "E": 10,
        }
        rows = conn.execute(
            "SELECT num, score, success FROM jobs WHERE deleted=0 AND fit_score IS NULL"
        ).fetchall()
        backfilled = 0
        for num, score, success in rows:
            fit_num = grade_to_numeric.get(score)
            success_num = grade_to_numeric.get(success) if success else fit_num
            if fit_num is not None:
                overall = int(round(fit_num * 0.6 + (success_num or fit_num) * 0.4))
                conn.execute(
                    "UPDATE jobs SET fit_score=?, success_score=?, overall_score=? WHERE num=?",
                    (fit_num, success_num, overall, num),
                )
                backfilled += 1
        if backfilled:
            conn.commit()
            log.info("migrate.backfilled_numeric_scores", count=backfilled)
        conn.close()
    except Exception as e:
        log.warning("migrate.failed", error=str(e))


def _migrate_rules():
    try:
        conn = sqlite3.connect(DB_PATH)
        old_cats = conn.execute(
            "SELECT DISTINCT category FROM preferences WHERE category NOT IN ('fit','success')"
        ).fetchall()
        if old_cats:
            log.info("migrate.Removing old rule categories: {[r[0] for r in old_cats]}")
            conn.execute(
                "DELETE FROM preferences WHERE category NOT IN ('fit','success')"
            )
            conn.commit()
        existing_keys = {
            r[0] for r in conn.execute("SELECT key FROM preferences").fetchall()
        }
        if "python_expertise" in existing_keys:
            log.info("migrate.replacing_rules")
            conn.execute("DELETE FROM preferences")
            conn.commit()
            conn.close()
            from core.db import init_db

            init_db()
        else:
            conn.close()
    except Exception as e:
        log.warning("migrate.failed", error=str(e))


def _migrate_rule_types():
    """Add rule_type and score_weight columns to preferences table for backward compatibility."""
    try:
        conn = sqlite3.connect(DB_PATH)
        # Check if rule_type column exists
        cursor = conn.execute("PRAGMA table_info(preferences)")
        columns = {row[1] for row in cursor.fetchall()}

        if "rule_type" not in columns:
            log.info("migrate.adding_rule_type_column")
            conn.execute(
                "ALTER TABLE preferences ADD COLUMN rule_type TEXT NOT NULL DEFAULT 'job'"
            )
            # Mark all existing rules as 'job' type (backward compatible)
            conn.execute(
                "UPDATE preferences SET rule_type='job' WHERE rule_type IS NULL"
            )

        if "score_weight" not in columns:
            log.info("migrate.adding_score_weight_column")
            conn.execute(
                "ALTER TABLE preferences ADD COLUMN score_weight INTEGER DEFAULT 0"
            )
            # Copy priority to score_weight for existing rules
            conn.execute(
                "UPDATE preferences SET score_weight=priority WHERE score_weight=0 OR score_weight IS NULL"
            )

        # Check if shared/company rules exist by rule_type
        shared_count = conn.execute(
            "SELECT COUNT(*) FROM preferences WHERE rule_type='shared'"
        ).fetchone()[0]
        company_count = conn.execute(
            "SELECT COUNT(*) FROM preferences WHERE rule_type='company'"
        ).fetchone()[0]

        if shared_count == 0 or company_count == 0:
            log.info("migrate.seeding_shared_company_rules")

            # Convert existing matching rules to shared type
            shared_keys = [
                "visa_and_relocation_compatibility",
                "market_accessibility",
                "communication_and_work_culture",
                "sensitive_industry_penalty",
            ]
            for key in shared_keys:
                conn.execute(
                    "UPDATE preferences SET rule_type='shared' WHERE key=? AND rule_type='job'",
                    (key,),
                )

            # Add shared rules that don't exist yet
            shared_rules = [
                (
                    "success",
                    "shared",
                    "visa_and_relocation_compatibility",
                    "Evaluate visa sponsorship and relocation support. Positive: Work visa sponsorship, EU Blue Card support, history of hiring non-EU engineers, relocation support, international hiring process. Negative: EU work authorization required, local candidates only, no relocation support.",
                    "Main impact: Success Score",
                    100,
                    100,
                ),
                (
                    "success",
                    "shared",
                    "market_and_location_accessibility",
                    "Evaluate location accessibility. Highest priority: Germany (Berlin, Munich, Hamburg), Netherlands (Amsterdam, Eindhoven, Rotterdam). Other positive: Spain, Sweden, Denmark, Switzerland, Austria. Negative: Local-only markets, difficult immigration countries.",
                    "Main impact: Success Score",
                    95,
                    90,
                ),
                (
                    "success",
                    "shared",
                    "communication_and_work_culture",
                    "Evaluate work culture and communication. Positive: English-first workplace, international teams, remote/hybrid options, distributed teams, async communication culture. Negative: German/French/etc mandatory, local-only communication.",
                    "Main impact: Success Score",
                    80,
                    70,
                ),
                (
                    "success",
                    "shared",
                    "sensitive_industry_penalty",
                    "Reduce score for sensitive industries: defense/military, weapons systems, intelligence agencies, surveillance platforms, gambling/betting, alcohol/tobacco, adult content, fraud-related industries, highly controversial industries. Apply stronger penalties when core business is related. Do not heavily penalize normal tech companies that only serve these industries.",
                    "Main impact: Success Score",
                    60,
                    50,
                ),
            ]
            conn.executemany(
                "INSERT OR IGNORE INTO preferences (category, rule_type, key, value, description, priority, score_weight) VALUES (?,?,?,?,?,?,?)",
                shared_rules,
            )

            # Add company rules
            company_rules = [
                (
                    "fit",
                    "company",
                    "company_quality",
                    "Evaluate company quality. Positive: Strong product company, SaaS, developer tools, AI infrastructure, FinTech, HealthTech, B2B platforms, good funding/revenue signals, product maturity, market presence. Negative: Weak product signals, unclear business model, very unstable companies.",
                    "Core company evaluation",
                    100,
                    100,
                ),
                (
                    "fit",
                    "company",
                    "engineering_culture",
                    "Evaluate engineering culture. Positive: Strong engineering team, technical blog, open source activity, modern tech stack, testing culture, CI/CD practices, code review, architecture ownership, senior engineering environment, backend/platform engineering teams.",
                    "Engineering team quality",
                    90,
                    85,
                ),
                (
                    "fit",
                    "company",
                    "growth_and_career_potential",
                    "Evaluate growth opportunities. Positive: Senior ownership opportunities, technical leadership path, mentorship, learning culture, complex technical challenges, international growth opportunities. Negative: Maintenance-only products, limited engineering growth.",
                    "Career advancement potential",
                    80,
                    75,
                ),
                (
                    "fit",
                    "company",
                    "candidate_company_alignment",
                    "Evaluate alignment with candidate profile. Positive: Python backend, distributed systems, cloud-native systems, AI infrastructure, developer tools, data platforms. Additional bonus: Rust usage, backend/platform teams. Negative: Pure frontend companies, mobile-only companies, hardware-only companies.",
                    "Profile match quality",
                    65,
                    60,
                ),
            ]
            conn.executemany(
                "INSERT OR IGNORE INTO preferences (category, rule_type, key, value, description, priority, score_weight) VALUES (?,?,?,?,?,?,?)",
                company_rules,
            )
            log.info("migrate.seeded_shared_company_rules")

        conn.commit()
        conn.close()
    except Exception as e:
        log.warning("migrate.failed", error=str(e))


def _migrate_success_field():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "UPDATE jobs SET success = score WHERE success IS NULL AND score != 'P'"
        )
        conn.commit()
        conn.close()
    except Exception as e:
        log.warning("migrate.failed", error=str(e))


def _migrate_resume_files():
    try:
        from core.db import migrate_resume_files_to_db

        migrate_resume_files_to_db()
    except Exception as e:
        log.warning("migrate.failed", error=str(e))


def _migrate_recruiter_rules():
    """Seed recruiter scoring rules for existing databases."""
    try:
        conn = sqlite3.connect(DB_PATH)
        recruiter_count = conn.execute(
            "SELECT COUNT(*) FROM preferences WHERE rule_type='recruiter'"
        ).fetchone()[0]

        if recruiter_count == 0:
            log.info("migrate.seeding_recruiter_rules")
            recruiter_rules = [
                (
                    "fit",
                    "recruiter",
                    "recruiter_network_value",
                    "Evaluate how valuable this recruiter is as a gateway to job opportunities. Positive: Specialized in technology recruitment, backend/software engineering recruitment, works with Germany/Netherlands/EU companies, works with startups, has many active vacancies, represents multiple companies, has international candidate experience, has history hiring non-EU engineers. Negative: Generic recruitment, non-technical recruitment, low-quality staffing, no evidence of technology hiring.",
                    "Main impact: Company Fit Score",
                    100,
                    100,
                ),
                (
                    "success",
                    "recruiter",
                    "recruiter_market_access",
                    "Evaluate recruiter access to target markets. Positive: Works with German companies, works with European startups, supports international candidates, works with English-speaking roles, understands relocation hiring. Negative: Local-only recruitment, only domestic candidates.",
                    "Main impact: Company Success Score",
                    95,
                    85,
                ),
                (
                    "fit",
                    "recruiter",
                    "recruiter_profile_alignment",
                    "Evaluate if the recruiter can help the candidate find relevant positions. Positive: Backend engineering roles, Python roles, AI engineering, cloud/platform roles, senior engineering positions, distributed systems roles. Negative: Frontend-only recruitment, junior mass recruitment, non-technical positions.",
                    "Main impact: Company Fit Score",
                    85,
                    80,
                ),
                (
                    "success",
                    "recruiter",
                    "recruiter_activity_and_opportunity",
                    "Evaluate opportunity generation capability. Positive: Many active jobs, frequently updated vacancies, multiple relevant companies, fast communication, dedicated recruiters. Negative: No recent activity, few relevant opportunities.",
                    "Main impact: Company Success Score",
                    70,
                    70,
                ),
            ]
            conn.executemany(
                "INSERT OR IGNORE INTO preferences (category, rule_type, key, value, description, priority, score_weight) VALUES (?,?,?,?,?,?,?)",
                recruiter_rules,
            )
            conn.commit()
            log.info("migrate.seeded_recruiter_rules")

        conn.close()
    except Exception as e:
        log.warning("migrate.failed", error=str(e))


def _migrate_scope_column():
    """Add scope column to preferences table and migrate existing rule_type values."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute("PRAGMA table_info(preferences)")
        columns = {row[1] for row in cursor.fetchall()}

        if "scope" not in columns:
            log.info("migrate.adding_scope_column")
            conn.execute(
                "ALTER TABLE preferences ADD COLUMN scope TEXT NOT NULL DEFAULT 'JOB'"
            )

            # Map rule_type to scope
            type_to_scope = {
                "shared": "ALL",
                "job": "JOB",
                "company": "PRODUCT_COMPANY",
                "recruiter": "RECRUITING_AGENCY",
            }
            for rule_type, scope in type_to_scope.items():
                conn.execute(
                    "UPDATE preferences SET scope=? WHERE rule_type=?",
                    (scope, rule_type),
                )

            # Also add scope for staffing company rules (copy from RECRUITING_AGENCY)
            staffing_rules = conn.execute(
                "SELECT category, rule_type, key, value, description, priority, score_weight, enabled "
                "FROM preferences WHERE rule_type='recruiter'"
            ).fetchall()
            for row in staffing_rules:
                row = dict(row)
                conn.execute(
                    "INSERT OR IGNORE INTO preferences (category, rule_type, scope, key, value, description, priority, score_weight, enabled) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        row["category"],
                        row["rule_type"],
                        "STAFFING_COMPANY",
                        row["key"],
                        row["value"],
                        row["description"],
                        row["priority"],
                        row["score_weight"],
                        row["enabled"],
                    ),
                )

            conn.commit()
            log.info("migrate.migrated_scope_column")

        conn.close()
    except Exception as e:
        log.warning("migrate.failed", error=str(e))


def _migrate_rule_groups():
    """Migrate scope values to the new entity-based rule groups.

    Mapping:
      ALL              -> SHARED
      JOB              -> JOB
      PRODUCT_COMPANY  -> COMPANY_PRODUCT
      RECRUITING_AGENCY -> COMPANY_RECRUITING
      STAFFING_COMPANY -> COMPANY_RECRUITING  (merged)
      CONSULTING_COMPANY -> COMPANY_RECRUITING (merged)

    Also removes duplicate rules (e.g. market_accessibility vs market_and_location_accessibility).
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute("PRAGMA table_info(preferences)")
        columns = {row[1] for row in cursor.fetchall()}

        if "scope" not in columns:
            conn.close()
            return

        # Check if migration already done by looking for new values
        existing_scopes = {
            r[0]
            for r in conn.execute("SELECT DISTINCT scope FROM preferences").fetchall()
        }
        if "SHARED" in existing_scopes or "COMPANY_PRODUCT" in existing_scopes:
            log.info("migrate.rule_groups_already_migrated")
            conn.close()
            return

        log.info("migrate.migrating_rule_groups")

        # Map old scope values to new
        scope_map = {
            "ALL": "SHARED",
            "JOB": "JOB",
            "PRODUCT_COMPANY": "COMPANY_PRODUCT",
            "RECRUITING_AGENCY": "COMPANY_RECRUITING",
            "STAFFING_COMPANY": "COMPANY_RECRUITING",
            "CONSULTING_COMPANY": "COMPANY_RECRUITING",
        }

        for old_scope, new_scope in scope_map.items():
            conn.execute(
                "UPDATE preferences SET scope=? WHERE scope=?", (new_scope, old_scope)
            )

        # Remove duplicate rules (STAFFING_COMPANY and CONSULTING_COMPANY copies that
        # now have the same scope as RECRUITING_AGENCY). Keep the original RECRUITING_AGENCY rows.
        # Delete all COMPANY_RECRUITING rules, then re-insert the canonical set.
        conn.execute("DELETE FROM preferences WHERE scope='COMPANY_RECRUITING'")

        # Re-insert the 4 canonical recruiting company rules
        recruiting_rules = [
            (
                "fit",
                "recruiter",
                "COMPANY_RECRUITING",
                "recruiter_network_value",
                "Evaluate how valuable this recruiter is as a gateway to job opportunities. Positive: Specialized in technology recruitment, backend/software engineering recruitment, works with Germany/Netherlands/EU companies, works with startups, has many active vacancies, represents multiple companies, has international candidate experience, has history hiring non-EU engineers. Negative: Generic recruitment, non-technical recruitment, low-quality staffing, no evidence of technology hiring.",
                "Main impact: Company Fit Score",
                100,
                100,
            ),
            (
                "success",
                "recruiter",
                "COMPANY_RECRUITING",
                "recruiter_market_access",
                "Evaluate recruiter access to target markets. Positive: Works with German companies, works with European startups, supports international candidates, works with English-speaking roles, understands relocation hiring. Negative: Local-only recruitment, only domestic candidates.",
                "Main impact: Company Success Score",
                95,
                85,
            ),
            (
                "fit",
                "recruiter",
                "COMPANY_RECRUITING",
                "recruiter_profile_alignment",
                "Evaluate if the recruiter can help the candidate find relevant positions. Positive: Backend engineering roles, Python roles, AI engineering, cloud/platform roles, senior engineering positions, distributed systems roles. Negative: Frontend-only recruitment, junior mass recruitment, non-technical positions.",
                "Main impact: Company Fit Score",
                85,
                80,
            ),
            (
                "success",
                "recruiter",
                "COMPANY_RECRUITING",
                "recruiter_activity_and_opportunity",
                "Evaluate opportunity generation capability. Positive: Many active jobs, frequently updated vacancies, multiple relevant companies, fast communication, dedicated recruiters. Negative: No recent activity, few relevant opportunities.",
                "Main impact: Company Success Score",
                70,
                70,
            ),
        ]
        conn.executemany(
            "INSERT OR IGNORE INTO preferences (category, rule_type, scope, key, value, description, priority, score_weight) "
            "VALUES (?,?,?,?,?,?,?,?)",
            recruiting_rules,
        )

        # Now trim job rules down to the 6 canonical ones per the spec.
        # Get existing JOB scope rules
        job_rules = conn.execute(
            "SELECT id, key FROM preferences WHERE scope='JOB'"
        ).fetchall()
        # Keep only these 6 keys
        keep_job_keys = {
            "python_backend_core",
            "role_alignment",
            "hiring_probability",
            "technical_synergy",
            "engineering_depth",
            "work_and_communication_fit",
        }
        # If the current DB has old keys like 'python_primary', 'backend_core', etc.,
        # we need to rename and consolidate. The simplest approach: clear and re-seed.
        existing_job_keys = {dict(r)["key"] for r in job_rules}
        if existing_job_keys != keep_job_keys:
            log.info("migrate.replacing_job_rules", old=existing_job_keys, new=keep_job_keys)
            conn.execute("DELETE FROM preferences WHERE scope='JOB'")
            job_rules_data = [
                (
                    "fit",
                    "job",
                    "JOB",
                    "python_backend_core",
                    "Python must be the primary language with Django, FastAPI, Flask, or SQLAlchemy. Rust/Axum as secondary is a plus.",
                    "Core Python backend requirement",
                    100,
                    100,
                ),
                (
                    "fit",
                    "job",
                    "JOB",
                    "role_alignment",
                    "Backend engineer, Platform engineer, Systems engineer, Data engineer, SRE — title patterns that match the candidate's profile.",
                    "Title patterns that match",
                    85,
                    85,
                ),
                (
                    "success",
                    "job",
                    "JOB",
                    "hiring_probability",
                    "Assess hiring likelihood: company is actively hiring (multiple open roles), has funding, growing team, fast hiring process, responds to applications.",
                    "Application success likelihood",
                    80,
                    80,
                ),
                (
                    "fit",
                    "job",
                    "JOB",
                    "technical_synergy",
                    "Evaluate technical synergy: Docker, Kubernetes, CI/CD, Linux, AWS/GCP, PostgreSQL, Redis, REST API design, GraphQL.",
                    "Cloud and backend infrastructure overlap",
                    75,
                    75,
                ),
                (
                    "fit",
                    "job",
                    "JOB",
                    "engineering_depth",
                    "Evaluate engineering depth: senior-level role (9+ years), small focused teams (3-8), complex technical challenges, depth over breadth.",
                    "Seniority and depth match",
                    70,
                    70,
                ),
                (
                    "fit",
                    "job",
                    "JOB",
                    "work_and_communication_fit",
                    "Evaluate work arrangement and culture: remote/hybrid preferred, English-only workplace, async communication culture, international teams.",
                    "Work culture compatibility",
                    65,
                    65,
                ),
            ]
            conn.executemany(
                "INSERT OR IGNORE INTO preferences (category, rule_type, scope, key, value, description, priority, score_weight) "
                "VALUES (?,?,?,?,?,?,?,?)",
                job_rules_data,
            )

        # Trim shared rules to the 4 canonical ones
        shared_rules = conn.execute(
            "SELECT id, key FROM preferences WHERE scope='SHARED'"
        ).fetchall()
        keep_shared_keys = {
            "visa_and_relocation_compatibility",
            "market_and_location_accessibility",
            "communication_and_work_culture",
            "sensitive_industry_penalty",
        }
        existing_shared_keys = {dict(r)["key"] for r in shared_rules}
        # Remove old 'market_accessibility' duplicate if present
        if "market_accessibility" in existing_shared_keys:
            conn.execute(
                "DELETE FROM preferences WHERE scope='SHARED' AND key='market_accessibility'"
            )
            existing_shared_keys.discard("market_accessibility")

        if existing_shared_keys != keep_shared_keys:
            log.info("migrate.replacing_shared_rules", old=existing_shared_keys, new=keep_shared_keys)
            conn.execute("DELETE FROM preferences WHERE scope='SHARED'")
            shared_rules_data = [
                (
                    "success",
                    "shared",
                    "SHARED",
                    "visa_and_relocation_compatibility",
                    "Evaluate visa sponsorship and relocation support. Positive: Work visa sponsorship, EU Blue Card support, history of hiring non-EU engineers, relocation support. Negative: EU work authorization required, local candidates only.",
                    "Main impact: Success Score",
                    100,
                    100,
                ),
                (
                    "success",
                    "shared",
                    "SHARED",
                    "market_and_location_accessibility",
                    "Evaluate location accessibility. Highest priority: Germany (Berlin, Munich, Hamburg), Netherlands (Amsterdam, Eindhoven). Other positive: Spain, Sweden, Denmark, Switzerland, Austria. Negative: Local-only markets.",
                    "Main impact: Success Score",
                    95,
                    90,
                ),
                (
                    "success",
                    "shared",
                    "SHARED",
                    "communication_and_work_culture",
                    "Evaluate work culture and communication. Positive: English-first workplace, international teams, remote/hybrid, distributed teams, async communication. Negative: German/French mandatory, local-only communication.",
                    "Main impact: Success Score",
                    80,
                    70,
                ),
                (
                    "success",
                    "shared",
                    "SHARED",
                    "sensitive_industry_penalty",
                    "Reduce score for sensitive industries: defense/military, weapons, intelligence, surveillance, gambling, alcohol/tobacco, adult content, fraud-related. Apply stronger penalties when core business is related.",
                    "Main impact: Success Score",
                    60,
                    50,
                ),
            ]
            conn.executemany(
                "INSERT OR IGNORE INTO preferences (category, rule_type, scope, key, value, description, priority, score_weight) "
                "VALUES (?,?,?,?,?,?,?,?)",
                shared_rules_data,
            )

        # Trim product company rules to the 4 canonical ones
        product_rules = conn.execute(
            "SELECT id, key FROM preferences WHERE scope='COMPANY_PRODUCT'"
        ).fetchall()
        keep_product_keys = {
            "company_quality",
            "engineering_culture",
            "growth_and_career_potential",
            "candidate_company_alignment",
        }
        existing_product_keys = {dict(r)["key"] for r in product_rules}
        if existing_product_keys != keep_product_keys:
            log.info("migrate.replacing_product_rules", old=existing_product_keys, new=keep_product_keys)
            conn.execute("DELETE FROM preferences WHERE scope='COMPANY_PRODUCT'")
            product_rules_data = [
                (
                    "fit",
                    "company",
                    "COMPANY_PRODUCT",
                    "company_quality",
                    "Evaluate company quality. Positive: Strong product company, SaaS, developer tools, AI infrastructure, FinTech, HealthTech, good funding, product maturity. Negative: Weak product signals, unclear business model.",
                    "Core company evaluation",
                    100,
                    100,
                ),
                (
                    "fit",
                    "company",
                    "COMPANY_PRODUCT",
                    "engineering_culture",
                    "Evaluate engineering culture. Positive: Strong engineering team, technical blog, open source, modern stack, testing culture, CI/CD, code review, architecture ownership.",
                    "Engineering team quality",
                    90,
                    85,
                ),
                (
                    "fit",
                    "company",
                    "COMPANY_PRODUCT",
                    "growth_and_career_potential",
                    "Evaluate growth opportunities. Positive: Senior ownership, technical leadership path, mentorship, complex challenges, international growth. Negative: Maintenance-only products.",
                    "Career advancement potential",
                    80,
                    75,
                ),
                (
                    "fit",
                    "company",
                    "COMPANY_PRODUCT",
                    "candidate_company_alignment",
                    "Evaluate alignment with candidate profile. Positive: Python backend, distributed systems, cloud-native, AI infrastructure, developer tools. Negative: Pure frontend, mobile-only, hardware-only.",
                    "Profile match quality",
                    65,
                    60,
                ),
            ]
            conn.executemany(
                "INSERT OR IGNORE INTO preferences (category, rule_type, scope, key, value, description, priority, score_weight) "
                "VALUES (?,?,?,?,?,?,?,?)",
                product_rules_data,
            )

        conn.commit()
        conn.close()
        log.info("migrate.rule_groups_complete", counts="SHARED(4) JOB(6) COMPANY_PRODUCT(4) COMPANY_RECRUITING(4)")
    except Exception as e:
        log.warning("migrate.failed", error=str(e))


def _migrate_rename_tech_stack_to_skills():
    """Rename tech_stack table to skills for accurate naming (handles all skill types)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if 'tech_stack' in tables and 'skills' not in tables:
            log.info("migrate.renaming_tech_stack_to_skills")
            conn.execute("ALTER TABLE tech_stack RENAME TO skills")
            conn.commit()
            log.info("migrate.tech_stack_renamed_to_skills")
        elif 'skills' in tables:
            log.info("migrate.skills_table_already_exists")
        conn.close()
    except Exception as e:
        log.warning("migrate.failed", error=str(e))
