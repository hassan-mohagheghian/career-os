import json
import os
import sqlite3

from dotenv import load_dotenv
load_dotenv()

_file_dir = os.path.dirname(os.path.abspath(__file__))
_server_dir = os.path.join(_file_dir, '..')
_db_path = os.environ.get('DB_PATH', os.path.join(_server_dir, "db", "jobs.db"))
# Resolve relative paths against the server directory
DB_PATH = _db_path if os.path.isabs(_db_path) else os.path.normpath(os.path.join(_server_dir, _db_path))

# Ensure db directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS jobs (
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
        adv_at TEXT,
        see_at TEXT,
        apply_reason TEXT,
        fit_score INTEGER,
        success_score INTEGER,
        overall_score INTEGER,
        company_id INTEGER
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS summaries (
        num INTEGER PRIMARY KEY,
        company TEXT, match TEXT, score TEXT,
        summary TEXT, stack TEXT, resumeFit TEXT, note TEXT, url TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS resumes (
        id TEXT PRIMARY KEY,
        title TEXT,
        company TEXT, role TEXT, content TEXT,
        version INTEGER DEFAULT 1,
        raw_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        job_num INTEGER
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS tech_learning (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, priority INTEGER, pl TEXT, pc TEXT,
        sc TEXT, dc TEXT, usage INTEGER, uc TEXT,
        jobs TEXT, jd TEXT, reason TEXT, action TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS tech_stack (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, level INTEGER, ml TEXT, mc TEXT,
        roles TEXT, path TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS cities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        icon TEXT, name TEXT, info TEXT, jobs TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS pending_jobs (
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
        job_num INTEGER,
        company TEXT,
        error TEXT,
        workflow_log TEXT DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS dashboard_insights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        icon TEXT,
        title TEXT,
        description TEXT,
        priority INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS preferences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        rule_type TEXT NOT NULL DEFAULT 'job',
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        description TEXT,
        priority INTEGER DEFAULT 0,
        score_weight INTEGER DEFAULT 0,
        enabled INTEGER DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(category, key)
    )""")

    # Seed initial rules if table is empty
    if c.execute("SELECT COUNT(*) FROM preferences").fetchone()[0] == 0:
        c.executemany(
            "INSERT OR IGNORE INTO preferences (category, rule_type, key, value, description, priority, score_weight) VALUES (?,?,?,?,?,?,?)",
            [
                # ═══ SHARED RULES — Used for both Job and Company processing ═══

                # visa_and_relocation_compatibility (Critical, Weight 100)
                ("success", "shared", "visa_and_relocation_compatibility",
                 "Evaluate visa sponsorship and relocation support. Positive: Work visa sponsorship, EU Blue Card support, history of hiring non-EU engineers, relocation support, international hiring process. Negative: EU work authorization required, local candidates only, no relocation support.",
                 "Main impact: Success Score", 100, 100),

                # market_and_location_accessibility (Critical, Weight 90)
                ("success", "shared", "market_and_location_accessibility",
                 "Evaluate location accessibility. Highest priority: Germany (Berlin, Munich, Hamburg), Netherlands (Amsterdam, Eindhoven, Rotterdam). Other positive: Spain, Sweden, Denmark, Switzerland, Austria. Negative: Local-only markets, difficult immigration countries.",
                 "Main impact: Success Score", 95, 90),

                # communication_and_work_culture (High, Weight 70)
                ("success", "shared", "communication_and_work_culture",
                 "Evaluate work culture and communication. Positive: English-first workplace, international teams, remote/hybrid options, distributed teams, async communication culture. Negative: German/French/etc mandatory, local-only communication.",
                 "Main impact: Success Score", 80, 70),

                # sensitive_industry_penalty (Medium, Weight 50)
                ("success", "shared", "sensitive_industry_penalty",
                 "Reduce score for sensitive industries: defense/military, weapons systems, intelligence agencies, surveillance platforms, gambling/betting, alcohol/tobacco, adult content, fraud-related industries, highly controversial industries. Apply stronger penalties when core business is related. Do not heavily penalize normal tech companies that only serve these industries.",
                 "Main impact: Success Score", 60, 50),

                # ═══ JOB RULES — Used for Job scoring only ═══

                # ═══ FIT (16 rules) — Technical match ═══
                ("fit", "job", "python_primary", "Python must be the primary language in the job posting", "Core requirement — Python-heavy roles only", 100, 100),
                ("fit", "job", "avoid_wrong_stack", "Go/Java/C#-primary roles = automatic skip", "Wrong tech stack = waste of time", 98, 98),
                ("fit", "job", "backend_core", "Django, FastAPI, Flask, SQLAlchemy, Celery — match if 2+ required", "Core Python backend stack", 95, 95),
                ("fit", "job", "database_match", "PostgreSQL (expert), Redis, SQL — PostgreSQL is a major plus", "Database expertise matters", 92, 92),
                ("fit", "job", "seniority_match", "Senior level (9+ years), tech lead or architect preferred", "No junior/mid roles", 88, 88),
                ("fit", "job", "infrastructure_match", "Docker, Kubernetes, CI/CD, Linux, AWS/GCP", "Cloud and containerization", 85, 85),
                ("fit", "job", "domain_match", "Backend engineering, systems, data platforms, API design", "Core domain alignment", 82, 82),
                ("fit", "job", "secondary_tech", "Rust (Axum/Tokio), TypeScript (React/Next.js) — adds value", "Bonus technical skills", 78, 78),
                ("fit", "job", "role_alignment", "Backend engineer, Platform engineer, Systems engineer, Data engineer, SRE", "Title patterns that match", 75, 75),
                ("fit", "job", "min_tech_overlap", "Must require at least 3 technologies the candidate knows", "Minimum threshold for fit", 72, 72),
                ("fit", "job", "growth_fit", "Fintech, healthtech, developer tools, supply chain, AI/ML infrastructure", "Domains where the candidate can grow", 68, 68),
                ("fit", "job", "ai_ml_fit", "Python ML pipelines, model serving, data processing", "AI/ML experience value", 65, 65),
                ("fit", "job", "api_backend_match", "REST API design, GraphQL, gRPC — backend API work", "API design experience", 62, 62),
                ("fit", "job", "no_critical_gaps", "No must-have skills that the candidate completely lacks", "Critical gaps = bad fit", 58, 58),
                ("fit", "job", "tech_depth", "Job requires deep expertise, not just surface-level knowledge", "Depth over breadth rule", 55, 55),
                ("fit", "job", "team_composition", "Small focused teams (3-8 engineers) preferred over large orgs", "Team structure compatibility", 50, 50),

                # ═══ SUCCESS (16 rules) — Application probability ═══
                ("success", "job", "visa_requirement", "Company must sponsor work visa for non-EU nationals — HARD REQUIREMENT", "No sponsorship = very unlikely", 100, 100),
                ("success", "job", "visa_path_clarity", "Company has documented visa process or history of sponsoring", "Clear process = higher chance", 95, 95),
                ("success", "job", "remote_option", "Remote or hybrid work available — helps visa transition", "Remote increases success", 92, 92),
                ("success", "job", "language_match", "English-only preferred, German C1 required = major negative factor", "Language barrier impact", 88, 88),
                ("success", "job", "competition_level", "<50 applicants = excellent, 50-100 = good, 100-200 = moderate, 200+ = poor", "Competition thresholds", 85, 85),
                ("success", "job", "posting_freshness", "<7 days = excellent, 7-30 = good, 30-90 = moderate, 90+ = stale", "Job age affects success", 82, 82),
                ("success", "job", "location_match", "Berlin = best, Munich = good, Hamburg = moderate, Remote = best", "City compatibility", 80, 80),
                ("success", "job", "work_arrangement", "Remote > Hybrid > On-site for visa flexibility", "Work type rule", 78, 78),
                ("success", "job", "company_stability", "50-500 employees, funded (Series A-C) or profitable", "Size and financial health", 75, 75),
                ("success", "job", "salary_clarity", "Jobs with listed salary have higher success (clear expectations)", "Transparency helps", 70, 70),
                ("success", "job", "niche_posting", "Niche/specialized roles have fewer applicants, better odds", "Avoid mass-posted jobs", 68, 68),
                ("success", "job", "relocation_support", "Relocation package or assistance removes barriers", "Relocation bonus", 65, 65),
                ("success", "job", "hiring_speed", "Company known for fast hiring process (<4 weeks)", "Speed matters for visa", 60, 60),
                ("success", "job", "response_rate", "Company responds to applications (not black hole)", "Communication quality", 55, 55),
                ("success", "job", "role_clarity", "Clear job description with specific requirements listed", "Ambiguous = harder to target", 50, 50),
                ("success", "job", "growth_opportunity", "Clear career progression, learning budget, or mentorship", "Long-term success factor", 45, 45),

                # ═══ COMPANY RULES — Used for Company scoring only ═══

                # company_quality (Critical, Weight 100)
                ("fit", "company", "company_quality",
                 "Evaluate company quality. Positive: Strong product company, SaaS, developer tools, AI infrastructure, FinTech, HealthTech, B2B platforms, good funding/revenue signals, product maturity, market presence. Negative: Weak product signals, unclear business model, very unstable companies.",
                 "Core company evaluation", 100, 100),

                # engineering_culture (High, Weight 85)
                ("fit", "company", "engineering_culture",
                 "Evaluate engineering culture. Positive: Strong engineering team, technical blog, open source activity, modern tech stack, testing culture, CI/CD practices, code review, architecture ownership, senior engineering environment, backend/platform engineering teams.",
                 "Engineering team quality", 90, 85),

                # growth_and_career_potential (High, Weight 75)
                ("fit", "company", "growth_and_career_potential",
                 "Evaluate growth opportunities. Positive: Senior ownership opportunities, technical leadership path, mentorship, learning culture, complex technical challenges, international growth opportunities. Negative: Maintenance-only products, limited engineering growth.",
                 "Career advancement potential", 80, 75),

                # candidate_company_alignment (Medium, Weight 60)
                ("fit", "company", "candidate_company_alignment",
                 "Evaluate alignment with candidate profile. Positive: Python backend, distributed systems, cloud-native systems, AI infrastructure, developer tools, data platforms. Additional bonus: Rust usage, backend/platform teams. Negative: Pure frontend companies, mobile-only companies, hardware-only companies.",
                 "Profile match quality", 65, 60),

                # ═══ RECRUITER RULES — Used for Recruiter/Staffing company scoring only ═══

                # recruiter_network_value (Critical, Weight 100)
                ("fit", "recruiter", "recruiter_network_value",
                 "Evaluate how valuable this recruiter is as a gateway to job opportunities. Positive: Specialized in technology recruitment, backend/software engineering recruitment, works with Germany/Netherlands/EU companies, works with startups, has many active vacancies, represents multiple companies, has international candidate experience, has history hiring non-EU engineers. Negative: Generic recruitment, non-technical recruitment, low-quality staffing, no evidence of technology hiring.",
                 "Main impact: Company Fit Score", 100, 100),

                # recruiter_market_access (High, Weight 85)
                ("success", "recruiter", "recruiter_market_access",
                 "Evaluate recruiter access to target markets. Positive: Works with German companies, works with European startups, supports international candidates, works with English-speaking roles, understands relocation hiring. Negative: Local-only recruitment, only domestic candidates.",
                 "Main impact: Company Success Score", 95, 85),

                # recruiter_profile_alignment (High, Weight 80)
                ("fit", "recruiter", "recruiter_profile_alignment",
                 "Evaluate if the recruiter can help the candidate find relevant positions. Positive: Backend engineering roles, Python roles, AI engineering, cloud/platform roles, senior engineering positions, distributed systems roles. Negative: Frontend-only recruitment, junior mass recruitment, non-technical positions.",
                 "Main impact: Company Fit Score", 85, 80),

                # recruiter_activity_and_opportunity (Medium, Weight 70)
                ("success", "recruiter", "recruiter_activity_and_opportunity",
                 "Evaluate opportunity generation capability. Positive: Many active jobs, frequently updated vacancies, multiple relevant companies, fast communication, dedicated recruiters. Negative: No recent activity, few relevant opportunities.",
                 "Main impact: Company Success Score", 70, 70),
            ]
        )
        conn.commit()
        print(f"[db] Seeded {c.execute('SELECT COUNT(*) FROM preferences').fetchone()[0]} scoring rules")

    c.execute("""CREATE TABLE IF NOT EXISTS analysis_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        page TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        analysis_json TEXT NOT NULL
    )""")

    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_analysis_runs_page ON analysis_runs(page)"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_analysis_runs_page_created ON analysis_runs(page, created_at DESC)"
    )

    # --- Company Intelligence tables ---
    c.execute("""CREATE TABLE IF NOT EXISTS pending_companies (
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

    c.execute("""CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        website TEXT,
        domain TEXT,
        industry TEXT,
        country TEXT,
        city TEXT,
        description TEXT,
        company_size TEXT,
        company_type TEXT,
        logo_url TEXT,
        founded_year TEXT,
        headquarters_full TEXT,
        countries_of_operation TEXT,
        funding_stage TEXT,
        funding_amount TEXT,
        products TEXT,
        tech_stack TEXT,
        work_environment TEXT,
        extra TEXT,
        processing_status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS company_intelligence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        overview TEXT,
        culture_analysis TEXT,
        international_analysis TEXT,
        career_analysis TEXT,
        benefits_analysis TEXT,
        visa_analysis TEXT,
        technology_analysis TEXT,
        recommendation TEXT,
        scores TEXT,
        raw_source_data TEXT,
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies(id)
    )""")

    c.execute("CREATE INDEX IF NOT EXISTS idx_pending_companies_status ON pending_companies(status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_company_intelligence_company_id ON company_intelligence(company_id)")

    # Add workflow_log column if missing (for existing DBs)
    try:
        c.execute("SELECT workflow_log FROM pending_jobs LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE pending_jobs ADD COLUMN workflow_log TEXT DEFAULT '[]'")

    # Add locations column if missing (for existing DBs)
    try:
        c.execute("SELECT locations FROM jobs LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE jobs ADD COLUMN locations TEXT DEFAULT '[]'")

    # Add deleted column if missing (for existing DBs)
    try:
        c.execute("SELECT deleted FROM jobs LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE jobs ADD COLUMN deleted INTEGER DEFAULT 0")

    # Add employment_type column if missing (for existing DBs)
    try:
        c.execute("SELECT employment_type FROM jobs LIMIT 1")
    except sqlite3.OperationalError:
        c.execute(
            "ALTER TABLE jobs ADD COLUMN employment_type TEXT DEFAULT 'Full-time'"
        )

    # Add work_types column if missing (for existing DBs)
    try:
        c.execute("SELECT work_types FROM jobs LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE jobs ADD COLUMN work_types TEXT DEFAULT '[]'")

    # Add raw_description column if missing (for existing DBs)
    try:
        c.execute("SELECT raw_description FROM jobs LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE jobs ADD COLUMN raw_description TEXT")

    # Add structured_description column if missing (for existing DBs)
    try:
        c.execute("SELECT structured_description FROM jobs LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE jobs ADD COLUMN structured_description TEXT")

    # Add adv_at, see_at, apply_reason columns if missing (for existing DBs)
    for col in ['adv_at', 'see_at', 'apply_reason', 'company_url', 'linkedin_url']:
        try:
            c.execute(f"SELECT {col} FROM jobs LIMIT 1")
        except sqlite3.OperationalError:
            c.execute(f"ALTER TABLE jobs ADD COLUMN {col} TEXT")

    # Add step_extract_raw, step_extract_struct to pending_jobs
    for col in ['step_extract_raw', 'step_extract_struct']:
        try:
            c.execute(f"SELECT {col} FROM pending_jobs LIMIT 1")
        except sqlite3.OperationalError:
            c.execute(f"ALTER TABLE pending_jobs ADD COLUMN {col} INTEGER DEFAULT 0")

    # Add queue_order column for FIFO queue ordering
    try:
        c.execute("SELECT queue_order FROM pending_jobs LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE pending_jobs ADD COLUMN queue_order INTEGER DEFAULT 0")

    # Add version, raw_text, created_at to resumes
    for col, default in [('version', 1), ('raw_text', None), ('created_at', None)]:
        try:
            c.execute(f"SELECT {col} FROM resumes LIMIT 1")
        except sqlite3.OperationalError:
            if default is None:
                c.execute(f"ALTER TABLE resumes ADD COLUMN {col} TEXT")
            else:
                c.execute(f"ALTER TABLE resumes ADD COLUMN {col} INTEGER DEFAULT {default}")

    # Add job_num to resumes (links tailored resume to its job)
    try:
        c.execute("SELECT job_num FROM resumes LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE resumes ADD COLUMN job_num INTEGER")

    conn.commit()
    conn.close()


def load_json_to_db():
    """No-op: data is now managed entirely in SQLite. Kept for backwards compatibility."""
    pass


def migrate_existing_analysis_files():
    """Migrate existing analysis JSON files to the analysis_runs table."""
    data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
    conn = get_db()
    c = conn.cursor()

    # Check if migration has already been done
    count = c.execute("SELECT COUNT(*) FROM analysis_runs").fetchone()[0]
    if count > 0:
        conn.close()
        return

    import re
    from datetime import datetime

    migrated = 0

    if not os.path.isdir(data_dir):
        conn.close()
        return

    # Migrate dashboard_insights_*.json files
    for filename in os.listdir(data_dir):
        match = re.match(r"dashboard_insights_(\d+)\.json", filename)
        if match:
            filepath = os.path.join(data_dir, filename)
            try:
                with open(filepath) as f:
                    data = json.load(f)
                c.execute(
                    "INSERT INTO analysis_runs (page, created_at, analysis_json) VALUES (?, ?, ?)",
                    (
                        "dashboard",
                        datetime.now().isoformat(),
                        json.dumps(data, ensure_ascii=False),
                    ),
                )
                migrated += 1
            except Exception as e:
                print(f"Warning: Failed to migrate {filename}: {e}")

    # Migrate skills_insights_*.json files
    for filename in os.listdir(data_dir):
        match = re.match(r"skills_insights_(\d+)\.json", filename)
        if match:
            filepath = os.path.join(data_dir, filename)
            try:
                with open(filepath) as f:
                    data = json.load(f)
                c.execute(
                    "INSERT INTO analysis_runs (page, created_at, analysis_json) VALUES (?, ?, ?)",
                    (
                        "skills",
                        datetime.now().isoformat(),
                        json.dumps(data, ensure_ascii=False),
                    ),
                )
                migrated += 1
            except Exception as e:
                print(f"Warning: Failed to migrate {filename}: {e}")

    # If no files found but we have data in legacy tables, migrate from there
    if migrated == 0:
        # Check if dashboard_insights table has data
        dash_count = c.execute("SELECT COUNT(*) FROM dashboard_insights").fetchone()[0]
        if dash_count > 0:
            # Reconstruct dashboard insights from legacy table
            rows = c.execute(
                "SELECT type, icon, title, description, priority FROM dashboard_insights ORDER BY type, priority"
            ).fetchall()
            insights = {}
            for row in rows:
                r = dict(row)
                t = r["type"]
                if t not in insights:
                    insights[t] = []
                insights[t].append(
                    {
                        "icon": r["icon"],
                        "title": r["title"],
                        "description": r["description"],
                    }
                )
            if insights:
                c.execute(
                    "INSERT INTO analysis_runs (page, created_at, analysis_json) VALUES (?, ?, ?)",
                    (
                        "dashboard",
                        datetime.now().isoformat(),
                        json.dumps(insights, ensure_ascii=False),
                    ),
                )
                migrated += 1

        # Check if tech_learning or tech_stack tables have data
        tl_count = c.execute("SELECT COUNT(*) FROM tech_learning").fetchone()[0]
        ts_count = c.execute("SELECT COUNT(*) FROM tech_stack").fetchone()[0]
        if tl_count > 0 or ts_count > 0:
            insights = {}
            if tl_count > 0:
                rows = c.execute(
                    "SELECT * FROM tech_learning ORDER BY priority"
                ).fetchall()
                insights["techLearning"] = [dict(r) for r in rows]
            if ts_count > 0:
                rows = c.execute(
                    "SELECT * FROM tech_stack ORDER BY level DESC"
                ).fetchall()
                insights["techStack"] = [dict(r) for r in rows]
            if insights:
                c.execute(
                    "INSERT INTO analysis_runs (page, created_at, analysis_json) VALUES (?, ?, ?)",
                    (
                        "skills",
                        datetime.now().isoformat(),
                        json.dumps(insights, ensure_ascii=False),
                    ),
                )
                migrated += 1

    conn.commit()
    conn.close()
    print(f"Migrated {migrated} analysis records to analysis_runs table")


def migrate_resume_files_to_db():
    """Migrate existing resume files from inputs/ and resumes/ to the DB, then delete them."""
    import glob as globmod
    project_root = os.path.join(os.path.dirname(__file__), "..", "..")
    conn = get_db()
    c = conn.cursor()

    # 1. Migrate master resume from inputs/original/resume.txt
    master_path = os.path.join(project_root, "inputs", "original", "resume.txt")
    if os.path.exists(master_path):
        existing = c.execute("SELECT COUNT(*) FROM resumes WHERE id LIKE 'original_%'").fetchone()[0]
        if existing == 0:
            with open(master_path) as f:
                raw_text = f.read().strip()
            if raw_text:
                # Simple HTML conversion
                content_html = _text_to_html(raw_text)
                c.execute(
                    """INSERT OR REPLACE INTO resumes (id, title, company, role, content, version, raw_text, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    ('original_1', 'Resume v1', '', '', content_html, 1, raw_text, datetime.now().isoformat()),
                )
                print(f"[migrate] Imported master resume from {master_path}")
                try:
                    os.remove(master_path)
                    print(f"[migrate] Deleted {master_path}")
                except OSError:
                    pass
        else:
            # Already in DB, just remove file
            try:
                os.remove(master_path)
                print(f"[migrate] Deleted existing {master_path}")
            except OSError:
                pass

    # 2. Migrate tailored resumes from resumes/by_job/
    by_job_dir = os.path.join(project_root, "resumes", "by_job")
    if os.path.isdir(by_job_dir):
        txt_files = sorted(globmod.glob(os.path.join(by_job_dir, "*.txt")))
        migrated_count = 0
        for filepath in txt_files:
            basename = os.path.basename(filepath)
            # Parse filename: 001_GALVANY_Backend_Engineer.txt
            parts = basename.replace('.txt', '').split('_', 2)
            company = parts[1] if len(parts) > 1 else basename
            role = parts[2].replace('_', ' ') if len(parts) > 2 else ''

            with open(filepath) as f:
                raw_text = f.read().strip()
            if not raw_text:
                continue

            resume_id = f"file_{basename.replace('.txt', '')}"
            existing = c.execute("SELECT id FROM resumes WHERE id=?", (resume_id,)).fetchone()
            if not existing:
                content_html = _text_to_html(raw_text)
                c.execute(
                    """INSERT OR REPLACE INTO resumes (id, title, company, role, content, version, raw_text, created_at, job_num)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (resume_id, f'{company} (File Import)', company, role, content_html, 1, raw_text, datetime.now().isoformat(), None),
                )
                migrated_count += 1

        conn.commit()

        if migrated_count > 0:
            print(f"[migrate] Imported {migrated_count} tailored resumes from {by_job_dir}")

        # Delete files after migration
        for filepath in txt_files:
            try:
                os.remove(filepath)
            except OSError:
                pass

        # Clean up empty directory
        try:
            os.rmdir(by_job_dir)
        except OSError:
            pass

    # 3. Delete other resume artifacts from resumes/ directory
    resumes_dir = os.path.join(project_root, "resumes")
    if os.path.isdir(resumes_dir):
        for fname in os.listdir(resumes_dir):
            fpath = os.path.join(resumes_dir, fname)
            if os.path.isfile(fpath):
                try:
                    os.remove(fpath)
                    print(f"[migrate] Deleted {fpath}")
                except OSError:
                    pass
        try:
            os.rmdir(resumes_dir)
            print(f"[migrate] Removed empty {resumes_dir}")
        except OSError:
            pass

    conn.commit()
    conn.close()


def _text_to_html(text):
    """Convert plain text resume to simple HTML."""
    import re
    lines = text.strip().split('\n')
    html_parts = []
    for line in lines:
        line = line.strip()
        if not line:
            html_parts.append('<br/>')
            continue
        # Detect section headers (short ALL CAPS or known headers)
        if re.match(r'^[A-Z][A-Z\s]{3,}$', line) or line in ('Summary', 'Experience', 'Education', 'Skills', 'Projects', 'Certifications', 'Languages'):
            html_parts.append(f'<h3 style="margin:12px 0 4px;font-size:13px;border-bottom:1px solid #ddd;padding-bottom:2px;">{line}</h3>')
        elif line.startswith('•') or line.startswith('-'):
            html_parts.append(f'<li style="margin:2px 0;font-size:11px;">{line.lstrip("•- ")}</li>')
        else:
            html_parts.append(f'<p style="margin:3px 0;font-size:11px;">{line}</p>')
    return '\n'.join(html_parts)


if __name__ == "__main__":
    init_db()
    load_json_to_db()
    migrate_existing_analysis_files()
    migrate_resume_files_to_db()
    print(f"Database initialized at {DB_PATH}")
