import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'jobs.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS jobs (
        num INTEGER PRIMARY KEY,
        company TEXT, role TEXT, location TEXT, match TEXT,
        score INTEGER, salary TEXT, stack TEXT, visa TEXT,
        applicants TEXT, posted TEXT, industry TEXT,
        domain TEXT, notes TEXT, action TEXT, url TEXT,
        work_type TEXT DEFAULT 'On-site',
        workflow_log TEXT DEFAULT '[]',
        locations TEXT DEFAULT '[]',
        deleted INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS summaries (
        num INTEGER PRIMARY KEY,
        company TEXT, match TEXT, score INTEGER,
        summary TEXT, stack TEXT, resumeFit TEXT, note TEXT, url TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS resumes (
        id TEXT PRIMARY KEY,
        title TEXT, badge TEXT, badgeClass TEXT,
        company TEXT, role TEXT, content TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS tech_learning (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, priority INTEGER, pl TEXT, pc TEXT,
        sc TEXT, dc TEXT, usage INTEGER, uc TEXT,
        jobs TEXT, jd TEXT, reason TEXT, action TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS tech_stack (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, level INTEGER, ml TEXT, mc TEXT,
        roles TEXT, path TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS cities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        icon TEXT, name TEXT, info TEXT, jobs TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS pending_jobs (
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
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS dashboard_insights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        icon TEXT,
        title TEXT,
        description TEXT,
        priority INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS preferences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        description TEXT,
        priority INTEGER DEFAULT 0,
        enabled INTEGER DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(category, key)
    )''')

    # Add workflow_log column if missing (for existing DBs)
    try:
        c.execute('SELECT workflow_log FROM pending_jobs LIMIT 1')
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE pending_jobs ADD COLUMN workflow_log TEXT DEFAULT '[]'")

    # Add locations column if missing (for existing DBs)
    try:
        c.execute('SELECT locations FROM jobs LIMIT 1')
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE jobs ADD COLUMN locations TEXT DEFAULT '[]'")

    # Add deleted column if missing (for existing DBs)
    try:
        c.execute('SELECT deleted FROM jobs LIMIT 1')
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE jobs ADD COLUMN deleted INTEGER DEFAULT 0")

    conn.commit()
    conn.close()

def load_json_to_db():
    data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
    conn = get_db()
    c = conn.cursor()

    # Jobs
    with open(os.path.join(data_dir, 'jobs.json')) as f:
        for j in json.load(f):
            c.execute('''INSERT OR REPLACE INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (j['num'], j['company'], j['role'], j['location'], j['match'],
                 j['score'], j['salary'], j['stack'], j['visa'], j['applicants'],
                 j['posted'], j['industry'], j['domain'], j['notes'], j['action'], j['url'],
                 j.get('work_type', 'On-site')))

    # Summaries
    with open(os.path.join(data_dir, 'summaries.json')) as f:
        for s in json.load(f):
            c.execute('''INSERT OR REPLACE INTO summaries VALUES (?,?,?,?,?,?,?,?,?)''',
                (s['num'], s['company'], s['match'], s['score'],
                 s['summary'], s['stack'], s['resumeFit'], s['note'], s['url']))

    # Resumes
    with open(os.path.join(data_dir, 'resumes.json')) as f:
        for r in json.load(f):
            c.execute('''INSERT OR REPLACE INTO resumes VALUES (?,?,?,?,?,?,?)''',
                (r['id'], r['title'], r['badge'], r['badgeClass'],
                 r['company'], r['role'], r['content']))

    # Tech learning
    c.execute('DELETE FROM tech_learning')
    with open(os.path.join(data_dir, 'tech-learning.json')) as f:
        for t in json.load(f):
            c.execute('''INSERT INTO tech_learning (name,priority,pl,pc,sc,dc,usage,uc,jobs,jd,reason,action) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
                (t['name'], t['priority'], t['pl'], t['pc'], t['sc'], t['dc'],
                 t['usage'], t['uc'], t['jobs'], t['jd'], t['reason'], t['action']))

    # Tech stack
    c.execute('DELETE FROM tech_stack')
    with open(os.path.join(data_dir, 'tech-stack.json')) as f:
        for t in json.load(f):
            c.execute('''INSERT INTO tech_stack (name,level,ml,mc,roles,path) VALUES (?,?,?,?,?,?)''',
                (t['name'], t['level'], t['ml'], t['mc'], t['roles'], t['path']))

    # Cities
    c.execute('DELETE FROM cities')
    with open(os.path.join(data_dir, 'cities.json')) as f:
        for ci in json.load(f):
            c.execute('''INSERT INTO cities (icon,name,info,jobs) VALUES (?,?,?,?)''',
                (ci['icon'], ci['name'], ci['info'], ci['jobs']))

    conn.commit()
    conn.close()

def load_initial_preferences():
    """Load initial preferences from extracted data."""
    conn = get_db()
    c = conn.cursor()

    # Check if preferences already exist
    count = c.execute('SELECT COUNT(*) FROM preferences').fetchone()[0]
    if count > 0:
        conn.close()
        return

    preferences = [
        # Scoring weights
        ('scoring', 'python_match', 'high', 'Python stack match is primary scoring factor', 1),
        ('scoring', 'visa_path', 'high', 'Visa sponsorship availability affects score significantly', 2),
        ('scoring', 'competition', 'medium', 'Number of applicants affects competitiveness', 3),
        ('scoring', 'location', 'medium', 'Berlin/preferred cities get bonus points', 4),
        ('scoring', 'work_type', 'medium', 'Remote/Hybrid preferred for visa flexibility', 5),
        ('scoring', 'salary_range', 'low', 'Salary information when available', 6),

        # Tech preferences
        ('tech', 'languages_use', 'Python, Rust, TypeScript, C, WASM, SQL', 'Languages to use and learn', 1),
        ('tech', 'languages_avoid', 'Go', 'Do NOT learn Go or other languages right now', 2),
        ('tech', 'frontend', 'React, Next.js, Shadcn, Tailwind', 'Frontend technologies', 3),
        ('tech', 'strengths', 'Python 9+ years, Django/FastAPI, PostgreSQL, Docker/K8s', 'Core strengths for scoring', 4),
        ('tech', 'gaps', 'Go, TypeScript, German A1', 'Skill gaps to consider', 5),

        # Domain preferences
        ('domain', 'primary', 'Software engineering', 'Primary job domain', 1),
        ('domain', 'improvement', 'Supply chain domain', 'Domain needing improvement', 2),

        # Visa & relocation
        ('visa', 'need', 'Visa sponsorship for Germany + relocation from Iran', 'Visa requirement', 1),
        ('visa', 'best_path', 'Companies with remote-first policy (work from Iran initially while visa processes)', 'Best visa strategy', 2),
        ('visa', 'priority_companies', 'Cara Care (Bayer), Sunday Natural (40+ nationalities), Cresta (US-funded)', 'Priority companies for visa', 3),
        ('visa', 'relocation_package', 'preferred', 'Relocation package is a plus factor', 4),

        # Apply strategy
        ('strategy', 'apply_top_first', 'Cara Care, Audatic, Jobgether, Flix, Sunday Natural', 'Top companies to apply first', 1),
        ('strategy', 'avoid_german_c1', 'Focus on English-only positions', 'Avoid jobs requiring German C1', 2),
        ('strategy', 'speed_matters', 'Fresh postings: apply immediately', 'Time-sensitive applications', 3),
    ]

    for cat, key, value, desc, priority in preferences:
        c.execute('''INSERT OR IGNORE INTO preferences (category, key, value, description, priority)
            VALUES (?, ?, ?, ?, ?)''', (cat, key, value, desc, priority))

    conn.commit()
    conn.close()
    print(f"Loaded {len(preferences)} initial preferences")

if __name__ == '__main__':
    init_db()
    load_json_to_db()
    load_initial_preferences()
    print(f'Database initialized at {DB_PATH}')
