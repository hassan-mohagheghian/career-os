import json
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "jobs.db")


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
        score INTEGER, salary TEXT, stack TEXT, visa TEXT,
        applicants TEXT, posted TEXT, industry TEXT,
        domain TEXT, notes TEXT, action TEXT, url TEXT,
        work_type TEXT DEFAULT 'On-site',
        workflow_log TEXT DEFAULT '[]',
        locations TEXT DEFAULT '[]',
        deleted INTEGER DEFAULT 0,
        employment_type TEXT DEFAULT 'Full-time',
        work_types TEXT DEFAULT '[]',
        raw_description TEXT,
        structured_description TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS summaries (
        num INTEGER PRIMARY KEY,
        company TEXT, match TEXT, score INTEGER,
        summary TEXT, stack TEXT, resumeFit TEXT, note TEXT, url TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS resumes (
        id TEXT PRIMARY KEY,
        title TEXT, badge TEXT, badgeClass TEXT,
        company TEXT, role TEXT, content TEXT
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
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        description TEXT,
        priority INTEGER DEFAULT 0,
        enabled INTEGER DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(category, key)
    )""")

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

    # Add step_extract_raw, step_extract_struct to pending_jobs
    for col in ['step_extract_raw', 'step_extract_struct']:
        try:
            c.execute(f"SELECT {col} FROM pending_jobs LIMIT 1")
        except sqlite3.OperationalError:
            c.execute(f"ALTER TABLE pending_jobs ADD COLUMN {col} INTEGER DEFAULT 0")

    conn.commit()
    conn.close()


def load_json_to_db():
    """No-op: data is now managed entirely in SQLite. Kept for backwards compatibility."""
    pass


def load_initial_preferences():
    """Load initial preferences from extracted data."""
    conn = get_db()
    c = conn.cursor()

    # Check if preferences already exist
    count = c.execute("SELECT COUNT(*) FROM preferences").fetchone()[0]
    if count > 0:
        conn.close()
        return

    preferences = [
        # Scoring weights
        (
            "scoring",
            "python_match",
            "high",
            "Python stack match is primary scoring factor",
            1,
        ),
        (
            "scoring",
            "visa_path",
            "high",
            "Visa sponsorship availability affects score significantly",
            2,
        ),
        (
            "scoring",
            "competition",
            "medium",
            "Number of applicants affects competitiveness",
            3,
        ),
        (
            "scoring",
            "location",
            "medium",
            "Berlin/preferred cities get bonus points",
            4,
        ),
        (
            "scoring",
            "work_type",
            "medium",
            "Remote/Hybrid preferred for visa flexibility",
            5,
        ),
        ("scoring", "salary_range", "low", "Salary information when available", 6),
        # Tech preferences
        (
            "tech",
            "languages_use",
            "Python, Rust, TypeScript, C, WASM, SQL",
            "Languages to use and learn",
            1,
        ),
        (
            "tech",
            "languages_avoid",
            "Go",
            "Do NOT learn Go or other languages right now",
            2,
        ),
        (
            "tech",
            "frontend",
            "React, Next.js, Shadcn, Tailwind",
            "Frontend technologies",
            3,
        ),
        (
            "tech",
            "strengths",
            "Python 9+ years, Django/FastAPI, PostgreSQL, Docker/K8s",
            "Core strengths for scoring",
            4,
        ),
        ("tech", "gaps", "Go, TypeScript, German A1", "Skill gaps to consider", 5),
        # Domain preferences
        ("domain", "primary", "Software engineering", "Primary job domain", 1),
        (
            "domain",
            "improvement",
            "Supply chain domain",
            "Domain needing improvement",
            2,
        ),
        # Visa & relocation
        (
            "visa",
            "need",
            "Visa sponsorship for Germany + relocation from Iran",
            "Visa requirement",
            1,
        ),
        (
            "visa",
            "best_path",
            "Companies with remote-first policy (work from Iran initially while visa processes)",
            "Best visa strategy",
            2,
        ),
        (
            "visa",
            "priority_companies",
            "Cara Care (Bayer), Sunday Natural (40+ nationalities), Cresta (US-funded)",
            "Priority companies for visa",
            3,
        ),
        (
            "visa",
            "relocation_package",
            "preferred",
            "Relocation package is a plus factor",
            4,
        ),
        # Apply strategy
        (
            "strategy",
            "apply_top_first",
            "Cara Care, Audatic, Jobgether, Flix, Sunday Natural",
            "Top companies to apply first",
            1,
        ),
        (
            "strategy",
            "avoid_german_c1",
            "Focus on English-only positions",
            "Avoid jobs requiring German C1",
            2,
        ),
        (
            "strategy",
            "speed_matters",
            "Fresh postings: apply immediately",
            "Time-sensitive applications",
            3,
        ),
    ]

    for cat, key, value, desc, priority in preferences:
        c.execute(
            """INSERT OR IGNORE INTO preferences (category, key, value, description, priority)
            VALUES (?, ?, ?, ?, ?)""",
            (cat, key, value, desc, priority),
        )

    conn.commit()
    conn.close()
    print(f"Loaded {len(preferences)} initial preferences")


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


if __name__ == "__main__":
    init_db()
    load_json_to_db()
    load_initial_preferences()
    migrate_existing_analysis_files()
    print(f"Database initialized at {DB_PATH}")
