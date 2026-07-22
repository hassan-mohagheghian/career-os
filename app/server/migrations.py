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

    conn.execute("CREATE INDEX IF NOT EXISTS idx_pending_companies_status ON pending_companies(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_company_intelligence_company_id ON company_intelligence(company_id)")
    conn.commit()
    conn.close()


def run_migrations():
    """Run all data migrations on startup."""
    _migrate_numeric_scores()
    _backfill_numeric_scores()
    _migrate_rules()
    _migrate_rule_types()
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
