"""Database schema migrations and startup initialization."""

import json
import sqlite3

from config import DB_PATH


def ensure_db_schema():
    """Add missing columns/tables to existing databases for backward compatibility."""
    conn = sqlite3.connect(DB_PATH)

    # Jobs columns
    cursor = conn.execute('PRAGMA table_info(jobs)')
    columns = {row[1] for row in cursor.fetchall()}
    migrations = {
        'apply_time': "ALTER TABLE jobs ADD COLUMN apply_time TEXT",
        'response_time': "ALTER TABLE jobs ADD COLUMN response_time TEXT",
        'response_status': "ALTER TABLE jobs ADD COLUMN response_status TEXT",
        'company_id': "ALTER TABLE jobs ADD COLUMN company_id INTEGER",
    }
    for col, sql in migrations.items():
        if col not in columns:
            conn.execute(sql)

    # Company tables
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

    if 'pending_companies' not in tables:
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
            conn.execute("ALTER TABLE pending_companies ADD COLUMN notes TEXT DEFAULT '[]'")
            rows = conn.execute("SELECT id, input_text FROM pending_companies WHERE notes='[]' OR notes IS NULL").fetchall()
            for row in rows:
                notes = json.dumps([{"type": "text", "content": dict(row)["input_text"]}])
                conn.execute("UPDATE pending_companies SET notes=? WHERE id=?", (notes, dict(row)["id"]))

    # Add links column to pending_companies
    try:
        conn.execute("SELECT links FROM pending_companies LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE pending_companies ADD COLUMN links TEXT DEFAULT '[]'")

    if 'companies' not in tables:
        conn.execute("""CREATE TABLE IF NOT EXISTS companies (
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
        )""")
    else:
        company_cols = {row[1] for row in conn.execute('PRAGMA table_info(companies)').fetchall()}
        for col in ['founded_year', 'headquarters_full', 'countries_of_operation',
                     'funding_stage', 'funding_amount', 'products', 'tech_stack',
                     'work_environment', 'extra', 'notes']:
            if col not in company_cols:
                conn.execute(f'ALTER TABLE companies ADD COLUMN {col} TEXT')

    if 'company_intelligence' not in tables:
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

    if 'company_links' not in tables:
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

    if 'career_insight_runs' not in tables:
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

    if 'career_insights' not in tables:
        conn.execute("""CREATE TABLE IF NOT EXISTS career_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            insight_type TEXT NOT NULL,
            version INTEGER DEFAULT 1,
            score REAL,
            summary TEXT,
            data_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

    conn.execute("CREATE INDEX IF NOT EXISTS idx_pending_companies_status ON pending_companies(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_company_intelligence_company_id ON company_intelligence(company_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_company_links_company_id ON company_links(company_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_career_insight_runs_type ON career_insight_runs(insight_type, status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_career_insights_type ON career_insights(insight_type, version, created_at DESC)")

    # Skill topics tables
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    if 'skill_roadmaps' not in tables:
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
        topic_cols = {row[1] for row in conn.execute('PRAGMA table_info(skill_roadmaps)').fetchall()}
        if 'level' not in topic_cols:
            conn.execute("ALTER TABLE skill_roadmaps ADD COLUMN level INTEGER DEFAULT 0")

    # Add source column to tech_stack if missing
    try:
        conn.execute("SELECT source FROM tech_stack LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE tech_stack ADD COLUMN source TEXT DEFAULT 'service'")
    if 'skill_roadmap_progress' not in tables:
        conn.execute("""CREATE TABLE IF NOT EXISTS skill_roadmap_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roadmap_id INTEGER NOT NULL REFERENCES skill_roadmaps(id) ON DELETE CASCADE,
            skill_name TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(roadmap_id)
        )""")
    if 'skill_roadmap_jobs' not in tables:
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
        job_cols = {row[1] for row in conn.execute('PRAGMA table_info(skill_roadmap_jobs)').fetchall()}
        if 'session_id' not in job_cols:
            conn.execute("ALTER TABLE skill_roadmap_jobs ADD COLUMN session_id TEXT")
        if 'pid' not in job_cols:
            conn.execute("ALTER TABLE skill_roadmap_jobs ADD COLUMN pid INTEGER")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_skill_roadmaps_skill ON skill_roadmaps(skill_name, parent_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_skill_roadmap_progress_skill ON skill_roadmap_progress(skill_name)")

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


def _migrate_numeric_scores():
    try:
        from services.worker import normalize_score
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute('SELECT num, score FROM jobs WHERE deleted=0').fetchall()
        converted = 0
        for num, score in rows:
            if isinstance(score, (int, float)):
                new_grade = normalize_score(int(score))
                conn.execute('UPDATE jobs SET score=? WHERE num=?', (new_grade, num))
                converted += 1
        rows2 = conn.execute('SELECT num, score FROM summaries').fetchall()
        for num, score in rows2:
            if isinstance(score, (int, float)):
                new_grade = normalize_score(int(score))
                conn.execute('UPDATE summaries SET score=? WHERE num=?', (new_grade, num))
        if converted:
            conn.commit()
            print(f"[migrate] Converted {converted} numeric scores to letter grades")
        conn.close()
    except Exception as e:
        print(f"Warning: score migration failed: {e}")


def _backfill_numeric_scores():
    try:
        conn = sqlite3.connect(DB_PATH)
        grade_to_numeric = {
            'A++': 95, 'A+': 85, 'A': 75, 'B': 60, 'C': 40, 'D': 20, 'E': 10
        }
        rows = conn.execute('SELECT num, score, success FROM jobs WHERE deleted=0 AND fit_score IS NULL').fetchall()
        backfilled = 0
        for num, score, success in rows:
            fit_num = grade_to_numeric.get(score)
            success_num = grade_to_numeric.get(success) if success else fit_num
            if fit_num is not None:
                overall = int(round(fit_num * 0.6 + (success_num or fit_num) * 0.4))
                conn.execute('UPDATE jobs SET fit_score=?, success_score=?, overall_score=? WHERE num=?',
                            (fit_num, success_num, overall, num))
                backfilled += 1
        if backfilled:
            conn.commit()
            print(f"[migrate] Backfilled numeric scores for {backfilled} jobs")
        conn.close()
    except Exception as e:
        print(f"Warning: numeric score backfill failed: {e}")


def _migrate_rules():
    try:
        conn = sqlite3.connect(DB_PATH)
        old_cats = conn.execute("SELECT DISTINCT category FROM preferences WHERE category NOT IN ('fit','success')").fetchall()
        if old_cats:
            print(f"[migrate] Removing old rule categories: {[r[0] for r in old_cats]}")
            conn.execute("DELETE FROM preferences WHERE category NOT IN ('fit','success')")
            conn.commit()
        existing_keys = {r[0] for r in conn.execute("SELECT key FROM preferences").fetchall()}
        if 'python_expertise' in existing_keys:
            print("[migrate] Replacing old rules with unified fine-grained rules")
            conn.execute("DELETE FROM preferences")
            conn.commit()
            conn.close()
            from core.db import init_db
            init_db()
        else:
            conn.close()
    except Exception as e:
        print(f"Warning: rules migration failed: {e}")


def _migrate_rule_types():
    """Add rule_type and score_weight columns to preferences table for backward compatibility."""
    try:
        conn = sqlite3.connect(DB_PATH)
        # Check if rule_type column exists
        cursor = conn.execute('PRAGMA table_info(preferences)')
        columns = {row[1] for row in cursor.fetchall()}

        if 'rule_type' not in columns:
            print("[migrate] Adding rule_type column to preferences")
            conn.execute("ALTER TABLE preferences ADD COLUMN rule_type TEXT NOT NULL DEFAULT 'job'")
            # Mark all existing rules as 'job' type (backward compatible)
            conn.execute("UPDATE preferences SET rule_type='job' WHERE rule_type IS NULL")

        if 'score_weight' not in columns:
            print("[migrate] Adding score_weight column to preferences")
            conn.execute("ALTER TABLE preferences ADD COLUMN score_weight INTEGER DEFAULT 0")
            # Copy priority to score_weight for existing rules
            conn.execute("UPDATE preferences SET score_weight=priority WHERE score_weight=0 OR score_weight IS NULL")

        # Check if shared/company rules exist by rule_type
        shared_count = conn.execute("SELECT COUNT(*) FROM preferences WHERE rule_type='shared'").fetchone()[0]
        company_count = conn.execute("SELECT COUNT(*) FROM preferences WHERE rule_type='company'").fetchone()[0]

        if shared_count == 0 or company_count == 0:
            print("[migrate] Seeding default shared and company rules")

            # Convert existing matching rules to shared type
            shared_keys = ['visa_and_relocation_compatibility', 'market_accessibility',
                          'communication_and_work_culture', 'sensitive_industry_penalty']
            for key in shared_keys:
                conn.execute("UPDATE preferences SET rule_type='shared' WHERE key=? AND rule_type='job'", (key,))

            # Add shared rules that don't exist yet
            shared_rules = [
                ("success", "shared", "visa_and_relocation_compatibility",
                 "Evaluate visa sponsorship and relocation support. Positive: Work visa sponsorship, EU Blue Card support, history of hiring non-EU engineers, relocation support, international hiring process. Negative: EU work authorization required, local candidates only, no relocation support.",
                 "Main impact: Success Score", 100, 100),
                ("success", "shared", "market_and_location_accessibility",
                 "Evaluate location accessibility. Highest priority: Germany (Berlin, Munich, Hamburg), Netherlands (Amsterdam, Eindhoven, Rotterdam). Other positive: Spain, Sweden, Denmark, Switzerland, Austria. Negative: Local-only markets, difficult immigration countries.",
                 "Main impact: Success Score", 95, 90),
                ("success", "shared", "communication_and_work_culture",
                 "Evaluate work culture and communication. Positive: English-first workplace, international teams, remote/hybrid options, distributed teams, async communication culture. Negative: German/French/etc mandatory, local-only communication.",
                 "Main impact: Success Score", 80, 70),
                ("success", "shared", "sensitive_industry_penalty",
                 "Reduce score for sensitive industries: defense/military, weapons systems, intelligence agencies, surveillance platforms, gambling/betting, alcohol/tobacco, adult content, fraud-related industries, highly controversial industries. Apply stronger penalties when core business is related. Do not heavily penalize normal tech companies that only serve these industries.",
                 "Main impact: Success Score", 60, 50),
            ]
            conn.executemany(
                "INSERT OR IGNORE INTO preferences (category, rule_type, key, value, description, priority, score_weight) VALUES (?,?,?,?,?,?,?)",
                shared_rules
            )

            # Add company rules
            company_rules = [
                ("fit", "company", "company_quality",
                 "Evaluate company quality. Positive: Strong product company, SaaS, developer tools, AI infrastructure, FinTech, HealthTech, B2B platforms, good funding/revenue signals, product maturity, market presence. Negative: Weak product signals, unclear business model, very unstable companies.",
                 "Core company evaluation", 100, 100),
                ("fit", "company", "engineering_culture",
                 "Evaluate engineering culture. Positive: Strong engineering team, technical blog, open source activity, modern tech stack, testing culture, CI/CD practices, code review, architecture ownership, senior engineering environment, backend/platform engineering teams.",
                 "Engineering team quality", 90, 85),
                ("fit", "company", "growth_and_career_potential",
                 "Evaluate growth opportunities. Positive: Senior ownership opportunities, technical leadership path, mentorship, learning culture, complex technical challenges, international growth opportunities. Negative: Maintenance-only products, limited engineering growth.",
                 "Career advancement potential", 80, 75),
                ("fit", "company", "candidate_company_alignment",
                 "Evaluate alignment with candidate profile. Positive: Python backend, distributed systems, cloud-native systems, AI infrastructure, developer tools, data platforms. Additional bonus: Rust usage, backend/platform teams. Negative: Pure frontend companies, mobile-only companies, hardware-only companies.",
                 "Profile match quality", 65, 60),
            ]
            conn.executemany(
                "INSERT OR IGNORE INTO preferences (category, rule_type, key, value, description, priority, score_weight) VALUES (?,?,?,?,?,?,?)",
                company_rules
            )
            print(f"[migrate] Added shared and company rules")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Warning: rule_types migration failed: {e}")


def _migrate_success_field():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE jobs SET success = score WHERE success IS NULL AND score != 'P'")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Warning: success migration failed: {e}")


def _migrate_resume_files():
    try:
        from core.db import migrate_resume_files_to_db
        migrate_resume_files_to_db()
    except Exception as e:
        print(f"Warning: resume file migration failed: {e}")


def _migrate_recruiter_rules():
    """Seed recruiter scoring rules for existing databases."""
    try:
        conn = sqlite3.connect(DB_PATH)
        recruiter_count = conn.execute("SELECT COUNT(*) FROM preferences WHERE rule_type='recruiter'").fetchone()[0]

        if recruiter_count == 0:
            print("[migrate] Seeding recruiter scoring rules")
            recruiter_rules = [
                ("fit", "recruiter", "recruiter_network_value",
                 "Evaluate how valuable this recruiter is as a gateway to job opportunities. Positive: Specialized in technology recruitment, backend/software engineering recruitment, works with Germany/Netherlands/EU companies, works with startups, has many active vacancies, represents multiple companies, has international candidate experience, has history hiring non-EU engineers. Negative: Generic recruitment, non-technical recruitment, low-quality staffing, no evidence of technology hiring.",
                 "Main impact: Company Fit Score", 100, 100),
                ("success", "recruiter", "recruiter_market_access",
                 "Evaluate recruiter access to target markets. Positive: Works with German companies, works with European startups, supports international candidates, works with English-speaking roles, understands relocation hiring. Negative: Local-only recruitment, only domestic candidates.",
                 "Main impact: Company Success Score", 95, 85),
                ("fit", "recruiter", "recruiter_profile_alignment",
                 "Evaluate if the recruiter can help the candidate find relevant positions. Positive: Backend engineering roles, Python roles, AI engineering, cloud/platform roles, senior engineering positions, distributed systems roles. Negative: Frontend-only recruitment, junior mass recruitment, non-technical positions.",
                 "Main impact: Company Fit Score", 85, 80),
                ("success", "recruiter", "recruiter_activity_and_opportunity",
                 "Evaluate opportunity generation capability. Positive: Many active jobs, frequently updated vacancies, multiple relevant companies, fast communication, dedicated recruiters. Negative: No recent activity, few relevant opportunities.",
                 "Main impact: Company Success Score", 70, 70),
            ]
            conn.executemany(
                "INSERT OR IGNORE INTO preferences (category, rule_type, key, value, description, priority, score_weight) VALUES (?,?,?,?,?,?,?)",
                recruiter_rules
            )
            conn.commit()
            print(f"[migrate] Added 4 recruiter scoring rules")

        conn.close()
    except Exception as e:
        print(f"Warning: recruiter rules migration failed: {e}")


def _migrate_scope_column():
    """Add scope column to preferences table and migrate existing rule_type values."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute('PRAGMA table_info(preferences)')
        columns = {row[1] for row in cursor.fetchall()}

        if 'scope' not in columns:
            print("[migrate] Adding scope column to preferences")
            conn.execute("ALTER TABLE preferences ADD COLUMN scope TEXT NOT NULL DEFAULT 'JOB'")

            # Map rule_type to scope
            type_to_scope = {
                'shared': 'ALL',
                'job': 'JOB',
                'company': 'PRODUCT_COMPANY',
                'recruiter': 'RECRUITING_AGENCY',
            }
            for rule_type, scope in type_to_scope.items():
                conn.execute("UPDATE preferences SET scope=? WHERE rule_type=?", (scope, rule_type))

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
                    (row['category'], row['rule_type'], 'STAFFING_COMPANY', row['key'],
                     row['value'], row['description'], row['priority'], row['score_weight'], row['enabled'])
                )

            conn.commit()
            print(f"[migrate] Migrated {type_to_scope} rules to scope column")

        conn.close()
    except Exception as e:
        print(f"Warning: scope migration failed: {e}")


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
        cursor = conn.execute('PRAGMA table_info(preferences)')
        columns = {row[1] for row in cursor.fetchall()}

        if 'scope' not in columns:
            conn.close()
            return

        # Check if migration already done by looking for new values
        existing_scopes = {r[0] for r in conn.execute("SELECT DISTINCT scope FROM preferences").fetchall()}
        if 'SHARED' in existing_scopes or 'COMPANY_PRODUCT' in existing_scopes:
            print("[migrate] Rule groups already migrated")
            conn.close()
            return

        print("[migrate] Migrating scope values to entity-based rule groups...")

        # Map old scope values to new
        scope_map = {
            'ALL': 'SHARED',
            'JOB': 'JOB',
            'PRODUCT_COMPANY': 'COMPANY_PRODUCT',
            'RECRUITING_AGENCY': 'COMPANY_RECRUITING',
            'STAFFING_COMPANY': 'COMPANY_RECRUITING',
            'CONSULTING_COMPANY': 'COMPANY_RECRUITING',
        }

        for old_scope, new_scope in scope_map.items():
            conn.execute("UPDATE preferences SET scope=? WHERE scope=?", (new_scope, old_scope))

        # Remove duplicate rules (STAFFING_COMPANY and CONSULTING_COMPANY copies that
        # now have the same scope as RECRUITING_AGENCY). Keep the original RECRUITING_AGENCY rows.
        # Delete all COMPANY_RECRUITING rules, then re-insert the canonical set.
        conn.execute("DELETE FROM preferences WHERE scope='COMPANY_RECRUITING'")

        # Re-insert the 4 canonical recruiting company rules
        recruiting_rules = [
            ("fit", "recruiter", "COMPANY_RECRUITING", "recruiter_network_value",
             "Evaluate how valuable this recruiter is as a gateway to job opportunities. Positive: Specialized in technology recruitment, backend/software engineering recruitment, works with Germany/Netherlands/EU companies, works with startups, has many active vacancies, represents multiple companies, has international candidate experience, has history hiring non-EU engineers. Negative: Generic recruitment, non-technical recruitment, low-quality staffing, no evidence of technology hiring.",
             "Main impact: Company Fit Score", 100, 100),
            ("success", "recruiter", "COMPANY_RECRUITING", "recruiter_market_access",
             "Evaluate recruiter access to target markets. Positive: Works with German companies, works with European startups, supports international candidates, works with English-speaking roles, understands relocation hiring. Negative: Local-only recruitment, only domestic candidates.",
             "Main impact: Company Success Score", 95, 85),
            ("fit", "recruiter", "COMPANY_RECRUITING", "recruiter_profile_alignment",
             "Evaluate if the recruiter can help the candidate find relevant positions. Positive: Backend engineering roles, Python roles, AI engineering, cloud/platform roles, senior engineering positions, distributed systems roles. Negative: Frontend-only recruitment, junior mass recruitment, non-technical positions.",
             "Main impact: Company Fit Score", 85, 80),
            ("success", "recruiter", "COMPANY_RECRUITING", "recruiter_activity_and_opportunity",
             "Evaluate opportunity generation capability. Positive: Many active jobs, frequently updated vacancies, multiple relevant companies, fast communication, dedicated recruiters. Negative: No recent activity, few relevant opportunities.",
             "Main impact: Company Success Score", 70, 70),
        ]
        conn.executemany(
            "INSERT OR IGNORE INTO preferences (category, rule_type, scope, key, value, description, priority, score_weight) "
            "VALUES (?,?,?,?,?,?,?,?)",
            recruiting_rules
        )

        # Now trim job rules down to the 6 canonical ones per the spec.
        # Get existing JOB scope rules
        job_rules = conn.execute(
            "SELECT id, key FROM preferences WHERE scope='JOB'"
        ).fetchall()
        # Keep only these 6 keys
        keep_job_keys = {
            'python_backend_core', 'role_alignment', 'hiring_probability',
            'technical_synergy', 'engineering_depth', 'work_and_communication_fit'
        }
        # If the current DB has old keys like 'python_primary', 'backend_core', etc.,
        # we need to rename and consolidate. The simplest approach: clear and re-seed.
        existing_job_keys = {dict(r)['key'] for r in job_rules}
        if existing_job_keys != keep_job_keys:
            print(f"[migrate] Replacing job rules: {existing_job_keys} -> {keep_job_keys}")
            conn.execute("DELETE FROM preferences WHERE scope='JOB'")
            job_rules_data = [
                ("fit", "job", "JOB", "python_backend_core",
                 "Python must be the primary language with Django, FastAPI, Flask, or SQLAlchemy. Rust/Axum as secondary is a plus.",
                 "Core Python backend requirement", 100, 100),
                ("fit", "job", "JOB", "role_alignment",
                 "Backend engineer, Platform engineer, Systems engineer, Data engineer, SRE — title patterns that match the candidate's profile.",
                 "Title patterns that match", 85, 85),
                ("success", "job", "JOB", "hiring_probability",
                 "Assess hiring likelihood: company is actively hiring (multiple open roles), has funding, growing team, fast hiring process, responds to applications.",
                 "Application success likelihood", 80, 80),
                ("fit", "job", "JOB", "technical_synergy",
                 "Evaluate technical synergy: Docker, Kubernetes, CI/CD, Linux, AWS/GCP, PostgreSQL, Redis, REST API design, GraphQL.",
                 "Cloud and backend infrastructure overlap", 75, 75),
                ("fit", "job", "JOB", "engineering_depth",
                 "Evaluate engineering depth: senior-level role (9+ years), small focused teams (3-8), complex technical challenges, depth over breadth.",
                 "Seniority and depth match", 70, 70),
                ("fit", "job", "JOB", "work_and_communication_fit",
                 "Evaluate work arrangement and culture: remote/hybrid preferred, English-only workplace, async communication culture, international teams.",
                 "Work culture compatibility", 65, 65),
            ]
            conn.executemany(
                "INSERT OR IGNORE INTO preferences (category, rule_type, scope, key, value, description, priority, score_weight) "
                "VALUES (?,?,?,?,?,?,?,?)",
                job_rules_data
            )

        # Trim shared rules to the 4 canonical ones
        shared_rules = conn.execute(
            "SELECT id, key FROM preferences WHERE scope='SHARED'"
        ).fetchall()
        keep_shared_keys = {
            'visa_and_relocation_compatibility',
            'market_and_location_accessibility',
            'communication_and_work_culture',
            'sensitive_industry_penalty'
        }
        existing_shared_keys = {dict(r)['key'] for r in shared_rules}
        # Remove old 'market_accessibility' duplicate if present
        if 'market_accessibility' in existing_shared_keys:
            conn.execute("DELETE FROM preferences WHERE scope='SHARED' AND key='market_accessibility'")
            existing_shared_keys.discard('market_accessibility')

        if existing_shared_keys != keep_shared_keys:
            print(f"[migrate] Replacing shared rules: {existing_shared_keys} -> {keep_shared_keys}")
            conn.execute("DELETE FROM preferences WHERE scope='SHARED'")
            shared_rules_data = [
                ("success", "shared", "SHARED", "visa_and_relocation_compatibility",
                 "Evaluate visa sponsorship and relocation support. Positive: Work visa sponsorship, EU Blue Card support, history of hiring non-EU engineers, relocation support. Negative: EU work authorization required, local candidates only.",
                 "Main impact: Success Score", 100, 100),
                ("success", "shared", "SHARED", "market_and_location_accessibility",
                 "Evaluate location accessibility. Highest priority: Germany (Berlin, Munich, Hamburg), Netherlands (Amsterdam, Eindhoven). Other positive: Spain, Sweden, Denmark, Switzerland, Austria. Negative: Local-only markets.",
                 "Main impact: Success Score", 95, 90),
                ("success", "shared", "SHARED", "communication_and_work_culture",
                 "Evaluate work culture and communication. Positive: English-first workplace, international teams, remote/hybrid, distributed teams, async communication. Negative: German/French mandatory, local-only communication.",
                 "Main impact: Success Score", 80, 70),
                ("success", "shared", "SHARED", "sensitive_industry_penalty",
                 "Reduce score for sensitive industries: defense/military, weapons, intelligence, surveillance, gambling, alcohol/tobacco, adult content, fraud-related. Apply stronger penalties when core business is related.",
                 "Main impact: Success Score", 60, 50),
            ]
            conn.executemany(
                "INSERT OR IGNORE INTO preferences (category, rule_type, scope, key, value, description, priority, score_weight) "
                "VALUES (?,?,?,?,?,?,?,?)",
                shared_rules_data
            )

        # Trim product company rules to the 4 canonical ones
        product_rules = conn.execute(
            "SELECT id, key FROM preferences WHERE scope='COMPANY_PRODUCT'"
        ).fetchall()
        keep_product_keys = {
            'company_quality', 'engineering_culture',
            'growth_and_career_potential', 'candidate_company_alignment'
        }
        existing_product_keys = {dict(r)['key'] for r in product_rules}
        if existing_product_keys != keep_product_keys:
            print(f"[migrate] Replacing product company rules: {existing_product_keys} -> {keep_product_keys}")
            conn.execute("DELETE FROM preferences WHERE scope='COMPANY_PRODUCT'")
            product_rules_data = [
                ("fit", "company", "COMPANY_PRODUCT", "company_quality",
                 "Evaluate company quality. Positive: Strong product company, SaaS, developer tools, AI infrastructure, FinTech, HealthTech, good funding, product maturity. Negative: Weak product signals, unclear business model.",
                 "Core company evaluation", 100, 100),
                ("fit", "company", "COMPANY_PRODUCT", "engineering_culture",
                 "Evaluate engineering culture. Positive: Strong engineering team, technical blog, open source, modern stack, testing culture, CI/CD, code review, architecture ownership.",
                 "Engineering team quality", 90, 85),
                ("fit", "company", "COMPANY_PRODUCT", "growth_and_career_potential",
                 "Evaluate growth opportunities. Positive: Senior ownership, technical leadership path, mentorship, complex challenges, international growth. Negative: Maintenance-only products.",
                 "Career advancement potential", 80, 75),
                ("fit", "company", "COMPANY_PRODUCT", "candidate_company_alignment",
                 "Evaluate alignment with candidate profile. Positive: Python backend, distributed systems, cloud-native, AI infrastructure, developer tools. Negative: Pure frontend, mobile-only, hardware-only.",
                 "Profile match quality", 65, 60),
            ]
            conn.executemany(
                "INSERT OR IGNORE INTO preferences (category, rule_type, scope, key, value, description, priority, score_weight) "
                "VALUES (?,?,?,?,?,?,?,?)",
                product_rules_data
            )

        conn.commit()
        conn.close()
        print("[migrate] Rule groups migration complete: SHARED(4) JOB(6) COMPANY_PRODUCT(4) COMPANY_RECRUITING(4)")
    except Exception as e:
        print(f"Warning: rule groups migration failed: {e}")
