from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify, Response, send_from_directory, request
from flask_cors import CORS
import sqlite3
import json
import os
import threading
from datetime import datetime
from urllib.parse import urlparse
from worker import process_job
from queue_manager import init_queue_manager, get_queue_manager

app = Flask(__name__, static_folder='../client/dist', static_url_path='')
CORS(app)

DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), 'db', 'jobs.db'))
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def get_db():
    """Get database connection with retry for locked databases."""
    import time
    for attempt in range(5):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.OperationalError as e:
            if 'locked' in str(e) and attempt < 4:
                time.sleep(0.5 * (attempt + 1))
            else:
                raise

def _ensure_db_schema():
    """Auto-migrate: add missing columns to jobs table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute('PRAGMA table_info(jobs)')
    columns = {row[1] for row in cursor.fetchall()}
    migrations = {
        'locations': "ALTER TABLE jobs ADD COLUMN locations TEXT DEFAULT '[]'",
        'deleted': "ALTER TABLE jobs ADD COLUMN deleted INTEGER DEFAULT 0",
        'employment_type': "ALTER TABLE jobs ADD COLUMN employment_type TEXT DEFAULT 'Full-time'",
        'work_types': "ALTER TABLE jobs ADD COLUMN work_types TEXT DEFAULT '[]'",
        'raw_description': "ALTER TABLE jobs ADD COLUMN raw_description TEXT",
        'structured_description': "ALTER TABLE jobs ADD COLUMN structured_description TEXT",
        'raw_file_path': "ALTER TABLE jobs ADD COLUMN raw_file_path TEXT",
        'structured_file_path': "ALTER TABLE jobs ADD COLUMN structured_file_path TEXT",
        'adv_at': "ALTER TABLE jobs ADD COLUMN adv_at TEXT",
        'see_at': "ALTER TABLE jobs ADD COLUMN see_at TEXT",
        'apply_reason': "ALTER TABLE jobs ADD COLUMN apply_reason TEXT",
    }
    # pending_jobs: add step columns if missing
    cursor2 = conn.execute('PRAGMA table_info(pending_jobs)')
    pending_cols = {row[1] for row in cursor2.fetchall()}
    for col in ['step_extract_raw', 'step_extract_struct', 'step_summary', 'step_validate']:
        if col not in pending_cols:
            conn.execute(f"ALTER TABLE pending_jobs ADD COLUMN {col} INTEGER DEFAULT 0")
    if 'queue_order' not in pending_cols:
        conn.execute("ALTER TABLE pending_jobs ADD COLUMN queue_order INTEGER DEFAULT 0")
    # jobs: add rescoring column if missing
    if 'rescoring' not in columns:
        conn.execute("ALTER TABLE jobs ADD COLUMN rescoring INTEGER DEFAULT 0")
    if 'success' not in columns:
        conn.execute("ALTER TABLE jobs ADD COLUMN success TEXT")
    for col, sql in migrations.items():
        if col not in columns:
            conn.execute(sql)
    conn.commit()
    conn.close()

_ensure_db_schema()

# Initialize the persistent job queue manager
queue_mgr = init_queue_manager(DB_PATH)

# Migrate numeric scores to letter grades
try:
    from worker import normalize_score
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

# Migrate old preferences (scoring/tech/domain/visa/strategy) to new fit/success
try:
    conn = sqlite3.connect(DB_PATH)
    old_cats = conn.execute("SELECT DISTINCT category FROM preferences WHERE category NOT IN ('fit','success')").fetchall()
    if old_cats:
        print(f"[migrate] Removing old preference categories: {[r[0] for r in old_cats]}")
        conn.execute("DELETE FROM preferences WHERE category NOT IN ('fit','success')")
        conn.commit()
    # Check if rules need updating (old keys vs new keys)
    existing_keys = {r[0] for r in conn.execute("SELECT key FROM preferences").fetchall()}
    if 'python_expertise' in existing_keys or 'visa_sponsorship' not in existing_keys:
        print("[migrate] Replacing old rules with unified fine-grained rules")
        conn.execute("DELETE FROM preferences")
        conn.commit()
        conn.close()
        from db import init_db
        init_db()
    else:
        conn.close()
except Exception as e:
    print(f"Warning: preferences migration failed: {e}")

# Migrate existing jobs: set success = score for jobs without success
try:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE jobs SET success = score WHERE success IS NULL AND score != 'P'")
    conn.commit()
    conn.close()
except Exception as e:
    print(f"Warning: success migration failed: {e}")

# Migrate existing resume files from disk to DB on startup
try:
    from db import migrate_resume_files_to_db
    migrate_resume_files_to_db()
except Exception as e:
    print(f"Warning: resume file migration failed: {e}")


def normalize_url(url):
    """Remove query parameters and trailing slash from URL for duplicate detection."""
    if not url:
        return url
    parsed = urlparse(url)
    base_url = f'{parsed.scheme}://{parsed.netloc}{parsed.path}'
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    return base_url

def get_db():
    """Get database connection with retry for locked databases."""
    import time
    for attempt in range(5):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            conn.row_factory = sqlite3.Row
            conn.execute('PRAGMA journal_mode=WAL')
            return conn
        except sqlite3.OperationalError as e:
            if 'locked' in str(e) and attempt < 4:
                time.sleep(0.5 * (attempt + 1))
            else:
                raise

def row_to_dict(row):
    return dict(row) if row else None

def rows_to_list(rows):
    return [dict(r) for r in rows]

# --- Streaming helpers ---

def stream_json(data):
    """Stream JSON response for large payloads."""
    def generate():
        yield json.dumps(data, ensure_ascii=False)
    return Response(generate(), mimetype='application/json')

# --- API Routes ---

@app.route('/api/jobs')
def get_jobs():
    conn = get_db()
    offset = request.args.get('offset', type=int)
    limit = request.args.get('limit', type=int)

    # Sorting
    sort_by = request.args.get('sort_by', 'created_at')
    sort_dir = request.args.get('sort_dir', 'desc')
    allowed_sorts = {'created_at', 'score', 'score_success', 'score_combined', 'num', 'company', 'location', 'posted_at', 'applicants', 'adv_at', 'see_at'}
    if sort_by not in allowed_sorts:
        sort_by = 'created_at'
    if sort_dir not in ('asc', 'desc'):
        sort_dir = 'desc'

    # Build WHERE clause
    conditions = ['deleted=0']
    params = []

    # Filter: cities
    filter_cities = request.args.get('filter_cities', '')
    if filter_cities:
        cities = [c.strip() for c in filter_cities.split(',') if c.strip()]
        if cities:
            # Match against locations JSON array or location column
            city_conditions = []
            for city in cities:
                city_conditions.append("locations LIKE ?")
                params.append(f'%"{city}"%')
                city_conditions.append("location = ?")
                params.append(city)
            conditions.append(f'({" OR ".join(city_conditions)})')

    # Filter: companies
    filter_companies = request.args.get('filter_companies', '')
    if filter_companies:
        companies = [c.strip() for c in filter_companies.split(',') if c.strip()]
        if companies:
            placeholders = ','.join(['?' for _ in companies])
            conditions.append(f'company IN ({placeholders})')
            params.extend(companies)

    # Filter: matches
    filter_matches = request.args.get('filter_matches', '')
    if filter_matches:
        matches = [m.strip() for m in filter_matches.split(',') if m.strip()]
        if matches:
            placeholders = ','.join(['?' for _ in matches])
            conditions.append(f'match IN ({placeholders})')
            params.extend(matches)

    # Filter: work types
    filter_work_types = request.args.get('filter_work_types', '')
    if filter_work_types:
        wtypes = [w.strip() for w in filter_work_types.split(',') if w.strip()]
        if wtypes:
            wt_conditions = []
            for wt in wtypes:
                wt_conditions.append("work_types LIKE ?")
                params.append(f'%"{wt}"%')
                wt_conditions.append("work_type = ?")
                params.append(wt)
            conditions.append(f'({" OR ".join(wt_conditions)})')

    # Filter: employment types
    filter_employment_types = request.args.get('filter_employment_types', '')
    if filter_employment_types:
        etypes = [e.strip() for e in filter_employment_types.split(',') if e.strip()]
        if etypes:
            placeholders = ','.join(['?' for _ in etypes])
            conditions.append(f'employment_type IN ({placeholders})')
            params.extend(etypes)

    # Filter: text search (stack, role, company, notes)
    filter_tech = request.args.get('filter_tech', '').strip()
    if filter_tech:
        like_param = f'%{filter_tech}%'
        conditions.append('(stack LIKE ? OR role LIKE ? OR company LIKE ? OR notes LIKE ?)')
        params.extend([like_param, like_param, like_param, like_param])

    where_clause = ' AND '.join(conditions)
    total = conn.execute(f'SELECT COUNT(*) FROM jobs WHERE {where_clause}', params).fetchone()[0]

    # Aggregate stats (always from full table, not filtered)
    stats = conn.execute('''SELECT
        COUNT(*) as total,
        SUM(CASE WHEN match='High' THEN 1 ELSE 0 END) as high_match,
        SUM(CASE WHEN score IN ('A','A+','A++') THEN 1 ELSE 0 END) as apply_now,
        SUM(CASE WHEN work_type='Remote' THEN 1 ELSE 0 END) as remote
        FROM jobs WHERE deleted=0''').fetchone()
    agg = {
        'total': stats[0] or 0,
        'high_match': stats[1] or 0,
        'apply_now': stats[2] or 0,
        'remote': stats[3] or 0,
    }

    # Handle applicants sorting specially (parse numeric from text)
    if sort_by == 'applicants':
        order_clause = f"CAST(REPLACE(REPLACE(applicants, 'Not specified', '999'), '+', '') AS INTEGER) {sort_dir}"
    elif sort_by == 'score':
        # Fit score primary, success score as tiebreaker
        fit_rank = "CASE score WHEN 'A++' THEN 7 WHEN 'A+' THEN 6 WHEN 'A' THEN 5 WHEN 'B' THEN 4 WHEN 'C' THEN 3 WHEN 'D' THEN 2 WHEN 'E' THEN 1 ELSE 0 END"
        success_rank = "CASE success WHEN 'A++' THEN 7 WHEN 'A+' THEN 6 WHEN 'A' THEN 5 WHEN 'B' THEN 4 WHEN 'C' THEN 3 WHEN 'D' THEN 2 WHEN 'E' THEN 1 ELSE 0 END"
        order_clause = f"{fit_rank} {sort_dir}, {success_rank} {sort_dir}"
    elif sort_by == 'score_success':
        # Success score primary, fit score as tiebreaker
        fit_rank = "CASE score WHEN 'A++' THEN 7 WHEN 'A+' THEN 6 WHEN 'A' THEN 5 WHEN 'B' THEN 4 WHEN 'C' THEN 3 WHEN 'D' THEN 2 WHEN 'E' THEN 1 ELSE 0 END"
        success_rank = "CASE success WHEN 'A++' THEN 7 WHEN 'A+' THEN 6 WHEN 'A' THEN 5 WHEN 'B' THEN 4 WHEN 'C' THEN 3 WHEN 'D' THEN 2 WHEN 'E' THEN 1 ELSE 0 END"
        order_clause = f"{success_rank} {sort_dir}, {fit_rank} {sort_dir}"
    elif sort_by == 'score_combined':
        # Combined sum of fit + success
        fit_rank = "CASE score WHEN 'A++' THEN 7 WHEN 'A+' THEN 6 WHEN 'A' THEN 5 WHEN 'B' THEN 4 WHEN 'C' THEN 3 WHEN 'D' THEN 2 WHEN 'E' THEN 1 ELSE 0 END"
        success_rank = "CASE success WHEN 'A++' THEN 7 WHEN 'A+' THEN 6 WHEN 'A' THEN 5 WHEN 'B' THEN 4 WHEN 'C' THEN 3 WHEN 'D' THEN 2 WHEN 'E' THEN 1 ELSE 0 END"
        order_clause = f"({fit_rank} + {success_rank}) {sort_dir}"
    else:
        order_clause = f'{sort_by} {sort_dir}'

    if offset is not None and limit is not None:
        rows = conn.execute(f'SELECT * FROM jobs WHERE {where_clause} ORDER BY {order_clause} LIMIT ? OFFSET ?', params + [limit, offset]).fetchall()
        conn.close()
        return jsonify({'jobs': rows_to_list(rows), 'total': total, 'agg': agg})
    rows = conn.execute(f'SELECT * FROM jobs WHERE {where_clause} ORDER BY {order_clause}', params).fetchall()
    conn.close()
    return jsonify({'jobs': rows_to_list(rows), 'total': total, 'agg': agg})

@app.route('/api/jobs/<int:num>')
def get_job(num):
    conn = get_db()
    row = conn.execute('SELECT * FROM jobs WHERE num=?', (num,)).fetchone()
    conn.close()
    if row:
        return jsonify(row_to_dict(row))
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/jobs/<int:num>', methods=['DELETE'])
def delete_job(num):
    """Hard delete a processed job and all related data."""
    conn = get_db()
    conn.execute('DELETE FROM jobs WHERE num=?', (num,))
    conn.execute('DELETE FROM summaries WHERE num=?', (num,))
    conn.execute("DELETE FROM resumes WHERE id=? OR id=?", (f'pending_{num}', f'rescore_{num}'))
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted', 'num': num})

@app.route('/api/jobs/<int:num>/requeue', methods=['POST'])
def requeue_job(num):
    """Re-queue a job for fresh processing. Old job deleted only after new one succeeds."""
    conn = get_db()
    job = conn.execute('SELECT * FROM jobs WHERE num=?', (num,)).fetchone()
    if not job:
        conn.close()
        return jsonify({'error': 'Job not found'}), 404
    j = dict(job)
    url = j['url']
    company = j.get('company', '')
    # Mark old job for deferred deletion (worker deletes after success)
    conn.execute('UPDATE jobs SET deleted=1 WHERE num=?', (num,))
    # Find or create pending entry
    row = conn.execute('SELECT id FROM pending_jobs WHERE url=?', (url,)).fetchone()
    if row:
        pid = dict(row)['id']
        conn.execute('''UPDATE pending_jobs SET status='pending', error=NULL, source='requeue',
            company=?, queue_order=0, step_fetch=0, step_validate=0, step_extract_raw=0, step_extract_struct=0,
            step_analyze=0, step_summary=0, step_db=0, step_done=0,
            workflow_log='[]', updated_at=? WHERE id=?''',
            (company, datetime.now().isoformat(), pid))
    else:
        cur = conn.execute('INSERT INTO pending_jobs (url, source, company, status) VALUES (?, ?, ?, ?)',
            (url, 'requeue', company, 'pending'))
        pid = cur.lastrowid
    conn.commit()
    conn.close()
    get_queue_manager().enqueue(pid)
    return jsonify({'status': 'queued', 'pid': pid, 'num': num, 'company': company})

@app.route('/api/summaries')
def get_summaries():
    conn = get_db()
    grade_order = "CASE score WHEN 'A++' THEN 7 WHEN 'A+' THEN 6 WHEN 'A' THEN 5 WHEN 'B' THEN 4 WHEN 'C' THEN 3 WHEN 'D' THEN 2 WHEN 'E' THEN 1 ELSE 0 END"
    rows = conn.execute(f'SELECT * FROM summaries ORDER BY {grade_order} DESC').fetchall()
    conn.close()
    return stream_json(rows_to_list(rows))

@app.route('/api/resumes')
def get_resumes():
    conn = get_db()
    rows = conn.execute('SELECT * FROM resumes ORDER BY created_at DESC').fetchall()
    conn.close()
    return stream_json(rows_to_list(rows))

@app.route('/api/resumes/latest')
def get_latest_resume():
    conn = get_db()
    row = conn.execute("SELECT * FROM resumes WHERE id LIKE 'original_%' ORDER BY version DESC LIMIT 1").fetchone()
    conn.close()
    if row:
        return jsonify(row_to_dict(row))
    return jsonify({})

@app.route('/api/resumes', methods=['POST'])
def save_resume():
    """Save a new resume version."""
    data = request.get_json()
    raw_text = data.get('raw_text', '').strip()
    if not raw_text:
        return jsonify({'error': 'Resume text required'}), 400

    conn = get_db()
    # Get next version number
    row = conn.execute("SELECT MAX(version) as max_v FROM resumes WHERE id LIKE 'original_%'").fetchone()
    next_version = (dict(row)['max_v'] or 0) + 1

    # Generate masked version for preview
    masked_text = _mask_pii(raw_text)

    # Convert to simple HTML for storage
    content_html = _text_to_html(masked_text)

    resume_id = f'original_{next_version}'
    conn.execute('''INSERT OR REPLACE INTO resumes (id, title, company, role, content, version, raw_text, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (resume_id, f'Resume v{next_version}', '', '', content_html, next_version, raw_text, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    return jsonify({
        'status': 'saved', 'id': resume_id, 'version': next_version,
        'content': content_html, 'raw_text': raw_text, 'masked_text': masked_text
    })

@app.route('/api/resumes/<version>', methods=['DELETE'])
def delete_resume_version(version):
    """Delete a specific resume by version (original) or by full ID (tailored)."""
    conn = get_db()
    # Try as original version first, then as raw ID
    resume_id = f'original_{version}'
    deleted = conn.execute("DELETE FROM resumes WHERE id=?", (resume_id,)).rowcount
    if not deleted:
        # Try deleting by raw ID (for tailored resumes like pending_X, rescore_X)
        deleted = conn.execute("DELETE FROM resumes WHERE id=?", (version,)).rowcount
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted', 'id': resume_id if deleted else version})

# ─── LinkedIn Profile endpoints ───

@app.route('/api/linkedin')
def get_linkedin_profiles():
    conn = get_db()
    rows = conn.execute("SELECT * FROM resumes WHERE id LIKE 'linkedin_%' ORDER BY created_at DESC").fetchall()
    conn.close()
    return stream_json(rows_to_list(rows))

@app.route('/api/linkedin/latest')
def get_latest_linkedin():
    conn = get_db()
    row = conn.execute("SELECT * FROM resumes WHERE id LIKE 'linkedin_%' ORDER BY version DESC LIMIT 1").fetchone()
    conn.close()
    if row:
        return jsonify(row_to_dict(row))
    return jsonify({})

@app.route('/api/linkedin', methods=['POST'])
def save_linkedin():
    """Save a new LinkedIn profile version."""
    data = request.get_json()
    raw_text = data.get('raw_text', '').strip()
    if not raw_text:
        return jsonify({'error': 'LinkedIn profile text required'}), 400

    conn = get_db()
    row = conn.execute("SELECT MAX(version) as max_v FROM resumes WHERE id LIKE 'linkedin_%'").fetchone()
    next_version = (dict(row)['max_v'] or 0) + 1

    masked_text = _mask_pii(raw_text)
    content_html = _text_to_html(masked_text)

    profile_id = f'linkedin_{next_version}'
    conn.execute('''INSERT OR REPLACE INTO resumes (id, title, company, role, content, version, raw_text, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (profile_id, f'LinkedIn Profile v{next_version}', '', '', content_html, next_version, raw_text, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    return jsonify({
        'status': 'saved', 'id': profile_id, 'version': next_version,
        'content': content_html, 'raw_text': raw_text, 'masked_text': masked_text
    })

@app.route('/api/linkedin/<version>', methods=['DELETE'])
def delete_linkedin(version):
    """Delete a LinkedIn profile by version or full ID."""
    conn = get_db()
    profile_id = f'linkedin_{version}'
    deleted = conn.execute("DELETE FROM resumes WHERE id=?", (profile_id,)).rowcount
    if not deleted:
        deleted = conn.execute("DELETE FROM resumes WHERE id=?", (version,)).rowcount
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted', 'id': profile_id if deleted else version})

@app.route('/api/jobs/<int:num>/generate-resume', methods=['POST'])
def generate_resume(num):
    """Generate a tailored resume for a processed job (on-demand)."""
    import subprocess
    from prompts import load_prompt

    conn = get_db()
    job = conn.execute('SELECT * FROM jobs WHERE num=? AND deleted=0', (num,)).fetchone()
    if not job:
        conn.close()
        return jsonify({'error': 'Job not found'}), 404
    j = dict(job)

    # Load master resume
    resume_row = conn.execute("SELECT raw_text FROM resumes WHERE id LIKE 'original_%' ORDER BY version DESC LIMIT 1").fetchone()
    conn.close()
    if not resume_row or not dict(resume_row).get('raw_text'):
        return jsonify({'error': 'No master resume uploaded'}), 400

    # Write temp files
    import tempfile
    _tmp = os.environ.get('TEMP_DIR', 'tmp')
    tmp_dir = _tmp if os.path.isabs(_tmp) else os.path.join(PROJECT_ROOT, _tmp)
    os.makedirs(tmp_dir, exist_ok=True)
    pid = f'resume_{num}_{int(datetime.now().timestamp()*1000)}'
    job_file = os.path.join(tmp_dir, f'gen_job_{pid}.txt')
    resume_file = os.path.join(tmp_dir, f'gen_resume_{pid}.txt')

    raw_desc = j.get('raw_description', '')
    if not raw_desc:
        return jsonify({'error': 'No job description available'}), 400

    with open(job_file, 'w') as f:
        f.write(raw_desc)
    with open(resume_file, 'w') as f:
        f.write(dict(resume_row)['raw_text'])

    try:
        prompt = load_prompt('step_resume_generate',
            job_file=job_file, resume_file=resume_file,
            tmp_dir=tmp_dir, pid=pid)

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        mimo_bin = os.path.expanduser('~/.mimocode/bin/mimo')

        proc = subprocess.run(
            [mimo_bin, 'run', prompt, '--format', 'json', '--dangerously-skip-permissions'],
            cwd=project_root, capture_output=True, text=True,
            env={**os.environ, 'NO_COLOR': '1'}, timeout=180
        )

        result_path = os.path.join(tmp_dir, f'resume_{pid}.json')
        if not os.path.exists(result_path):
            return jsonify({'error': 'Resume generation failed — no output file'}), 500

        with open(result_path) as f:
            data = json.loads(f.read(), strict=False)

        resume_html = data.get('resume_html', '')
        if not resume_html:
            return jsonify({'error': 'Resume generation returned empty content'}), 500

        # Save to DB
        conn = get_db()
        conn.execute('''INSERT OR REPLACE INTO resumes (id, title, company, role, content, version, raw_text, created_at, job_num)
            VALUES (?,?,?,?,?,?,?,?,?)''',
            (f'pending_{num}', f"{j['company']} (Score {j['score']})", j['company'], j['role'],
             resume_html, 1, '', datetime.now().isoformat(), num))
        conn.commit()
        conn.close()

        try: os.remove(result_path)
        except OSError: pass

        return jsonify({'status': 'generated', 'id': f'pending_{num}', 'content': resume_html})
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Resume generation timed out'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        for f in [job_file, resume_file]:
            try: os.remove(f)
            except OSError: pass

@app.route('/api/jobs/<int:num>/generate-cover', methods=['POST'])
def generate_cover(num):
    """Generate a cover letter for a processed job (on-demand)."""
    import subprocess
    from prompts import load_prompt

    conn = get_db()
    job = conn.execute('SELECT * FROM jobs WHERE num=? AND deleted=0', (num,)).fetchone()
    if not job:
        conn.close()
        return jsonify({'error': 'Job not found'}), 404
    j = dict(job)

    # Load master resume
    resume_row = conn.execute("SELECT raw_text FROM resumes WHERE id LIKE 'original_%' ORDER BY version DESC LIMIT 1").fetchone()
    conn.close()
    if not resume_row or not dict(resume_row).get('raw_text'):
        return jsonify({'error': 'No master resume uploaded'}), 400

    # Write temp files
    import tempfile
    _tmp = os.environ.get('TEMP_DIR', 'tmp')
    tmp_dir = _tmp if os.path.isabs(_tmp) else os.path.join(PROJECT_ROOT, _tmp)
    os.makedirs(tmp_dir, exist_ok=True)
    pid = f'cover_{num}_{int(datetime.now().timestamp()*1000)}'
    job_file = os.path.join(tmp_dir, f'gen_job_{pid}.txt')
    resume_file = os.path.join(tmp_dir, f'gen_resume_{pid}.txt')

    raw_desc = j.get('raw_description', '')
    if not raw_desc:
        return jsonify({'error': 'No job description available'}), 400

    with open(job_file, 'w') as f:
        f.write(raw_desc)
    with open(resume_file, 'w') as f:
        f.write(dict(resume_row)['raw_text'])

    try:
        preferences = ''
        conn = get_db()
        pref_rows = conn.execute("SELECT key, value, priority FROM preferences WHERE enabled=1 ORDER BY priority DESC").fetchall()
        conn.close()
        if pref_rows:
            preferences = '\n'.join([f"- {r['key']}: {r['value']} (priority: {r['priority']})" for r in pref_rows])

        prompt = load_prompt('step7_cover_generate',
            url=j.get('url', ''), job_file=job_file, resume_file=resume_file,
            tmp_dir=tmp_dir, pid=pid, preferences=preferences)

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        mimo_bin = os.path.expanduser('~/.mimocode/bin/mimo')

        proc = subprocess.run(
            [mimo_bin, 'run', prompt, '--format', 'json', '--dangerously-skip-permissions'],
            cwd=project_root, capture_output=True, text=True,
            env={**os.environ, 'NO_COLOR': '1'}, timeout=120
        )

        result_path = os.path.join(tmp_dir, f'cover_{pid}.json')
        if not os.path.exists(result_path):
            return jsonify({'error': 'Cover letter generation failed — no output file'}), 500

        with open(result_path) as f:
            data = json.loads(f.read(), strict=False)

        cover_html = data.get('cover_letter', '')
        if not cover_html:
            return jsonify({'error': 'Cover letter generation returned empty content'}), 500

        # Save to DB
        conn = get_db()
        conn.execute('''INSERT OR REPLACE INTO resumes (id, title, company, role, content, version, raw_text, created_at, job_num)
            VALUES (?,?,?,?,?,?,?,?,?)''',
            (f'cover_{num}', f"{j['company']} Cover Letter", j['company'], j['role'],
             cover_html, 1, '', datetime.now().isoformat(), num))
        conn.commit()
        conn.close()

        try: os.remove(result_path)
        except OSError: pass

        return jsonify({'status': 'generated', 'id': f'cover_{num}', 'content': cover_html})
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Cover letter generation timed out'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        for f in [job_file, resume_file]:
            try: os.remove(f)
            except OSError: pass

def _mask_pii(text):
    """Mask personally identifiable information for safe sharing."""
    import re
    masked = text
    # Mask phone numbers (various formats)
    masked = re.sub(r'[\+]?\d[\d\s\-\(\)]{8,15}', '[PHONE]', masked)
    # Mask email addresses
    masked = re.sub(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', '[EMAIL]', masked)
    # Mask LinkedIn URLs
    masked = re.sub(r'linkedin\.com/in/[^\s]+', 'linkedin.com/in/[PROFILE]', masked)
    # Mask GitHub URLs
    masked = re.sub(r'github\.com/[^\s]+', 'github.com/[PROFILE]', masked)
    # Mask names at the top (first line if it looks like a name - no special chars, short)
    lines = masked.split('\n')
    if lines and len(lines[0].strip()) < 60 and not any(c in lines[0] for c in '@:;#'):
        lines[0] = '[NAME]'
        masked = '\n'.join(lines)
    return masked

def _text_to_html(text):
    """Convert plain text resume to simple HTML."""
    import html
    lines = text.split('\n')
    html_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            html_lines.append('<br>')
            continue
        escaped = html.escape(line)
        # Detect section headers (ALL CAPS or known keywords)
        if line.isupper() or line in ('Summary', 'Professional Experience', 'Skills', 'Education', 'Languages'):
            html_lines.append(f'<h3 style="margin:0.5em 0 0.2em;color:#e6edf3;font-size:14px;border-bottom:1px solid #30363d;padding-bottom:2px">{escaped}</h3>')
        elif line.startswith('●') or line.startswith('•') or line.startswith('-'):
            html_lines.append(f'<div style="margin:2px 0;padding-left:1em">{escaped}</div>')
        elif '|' in line and ('Engineer' in line or 'Developer' in line):
            html_lines.append(f'<div style="font-weight:600;color:#c9d1d9;margin:4px 0 2px">{escaped}</div>')
        else:
            html_lines.append(f'<div style="margin:2px 0">{escaped}</div>')
    return '\n'.join(html_lines)

@app.route('/api/tech-learning')
def get_tech_learning():
    conn = get_db()
    rows = conn.execute('SELECT * FROM tech_learning ORDER BY priority').fetchall()
    conn.close()
    return stream_json(rows_to_list(rows))

@app.route('/api/tech-stack')
def get_tech_stack():
    conn = get_db()
    rows = conn.execute('SELECT * FROM tech_stack ORDER BY level DESC').fetchall()
    conn.close()
    return stream_json(rows_to_list(rows))

@app.route('/api/cities')
def get_cities():
    """Get cities dynamically from all job locations."""
    conn = get_db()
    # Get all locations from non-deleted jobs
    rows = conn.execute('SELECT location, locations FROM jobs WHERE deleted=0').fetchall()
    conn.close()

    city_counts = {}
    for row in rows:
        r = dict(row)
        # Parse locations JSON array
        locations = []
        if r.get('locations'):
            try:
                locations = json.loads(r['locations']) if isinstance(r['locations'], str) else r['locations']
            except:
                pass
        if not locations and r.get('location'):
            locations = [r['location']]

        for loc in locations:
            if loc and loc != 'Not specified':
                city_counts[loc] = city_counts.get(loc, 0) + 1

    # City icons and descriptions
    city_info = {
        'Berlin': {'icon': '🐻', 'info': 'Largest tech hub. 350K+ tech workers.'},
        'Munich': {'icon': '🦁', 'info': 'Highest salaries. Enterprise & automotive.'},
        'Hamburg': {'icon': '🎵', 'info': 'Growing tech scene. AdTech, energy.'},
        'Heidelberg': {'icon': '🏛️', 'info': 'Enterprise AI startup scene.'},
        'Frankfurt': {'icon': '🏦', 'info': 'FinTech capital. Banking infrastructure.'},
        'Cologne': {'icon': '🗼', 'info': 'Media & commerce tech.'},
        'Stuttgart': {'icon': '🏭', 'info': 'Engineering & automotive.'},
        'Remote': {'icon': '🏠', 'info': 'Best for visa from Iran.'},
        'Remote Germany': {'icon': '🏠', 'info': 'Best for visa from Iran.'},
        'Germany': {'icon': '🇩🇪', 'info': 'Country-wide opportunities.'},
    }

    total_jobs = len(city_counts)
    cities = []
    for city, count in sorted(city_counts.items(), key=lambda x: -x[1]):
        info = city_info.get(city, {'icon': '📍', 'info': 'Tech hub.'})
        cities.append({
            'icon': info['icon'],
            'name': city,
            'info': info['info'],
            'jobs': f'{count}/{total_jobs} jobs'
        })

    return stream_json(cities)

@app.route('/api/dashboard-insights')
def get_dashboard_insights():
    conn = get_db()
    rows = conn.execute('SELECT * FROM dashboard_insights ORDER BY type, priority').fetchall()
    conn.close()
    insights = {}
    for row in rows:
        r = dict(row)
        t = r['type']
        if t not in insights:
            insights[t] = []
        insights[t].append(r)
    return stream_json(insights)

@app.route('/api/dashboard-insights', methods=['POST'])
def update_dashboard_insights():
    data = request.get_json()
    conn = get_db()
    conn.execute('DELETE FROM dashboard_insights')
    for item_type, items in data.items():
        if isinstance(items, list):
            for i, item in enumerate(items):
                conn.execute('''INSERT INTO dashboard_insights (type, icon, title, description, priority)
                    VALUES (?, ?, ?, ?, ?)''',
                    (item_type, item.get('icon', ''), item.get('title', item.get('name', '')),
                     item.get('description', item.get('detail', item.get('note', ''))), i))
    conn.commit()
    conn.close()
    return jsonify({'status': 'updated', 'count': sum(len(v) for v in data.values() if isinstance(v, list))})

@app.route('/api/preferences')
def get_preferences():
    conn = get_db()
    rows = conn.execute('SELECT * FROM preferences ORDER BY category, priority').fetchall()
    conn.close()
    prefs = {}
    for row in rows:
        r = dict(row)
        cat = r['category']
        if cat not in prefs:
            prefs[cat] = []
        prefs[cat].append(r)
    return stream_json(prefs)

@app.route('/api/preferences', methods=['POST'])
def update_preferences():
    data = request.get_json()
    conn = get_db()
    for item in data.get('preferences', []):
        conn.execute('''INSERT OR REPLACE INTO preferences (category, key, value, description, priority, enabled)
            VALUES (?, ?, ?, ?, ?, ?)''',
            (item['category'], item['key'], item['value'],
             item.get('description', ''), item.get('priority', 0), item.get('enabled', 1)))
    conn.commit()
    conn.close()
    return jsonify({'status': 'updated'})

@app.route('/api/preferences/<int:id>', methods=['PUT'])
def update_preference(id):
    data = request.get_json()
    conn = get_db()
    fields = []
    values = []
    for key in ['value', 'description', 'priority', 'enabled']:
        if key in data:
            fields.append(f'{key}=?')
            values.append(data[key])
    if fields:
        fields.append('updated_at=?')
        values.append(datetime.now().isoformat())
        values.append(id)
        conn.execute(f'UPDATE preferences SET {",".join(fields)} WHERE id=?', values)
        conn.commit()
    conn.close()
    return jsonify({'status': 'updated'})

@app.route('/api/preferences/<int:id>', methods=['DELETE'])
def delete_preference(id):
    conn = get_db()
    conn.execute('DELETE FROM preferences WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted'})

@app.route('/api/pending', methods=['GET'])
def get_pending():
    conn = get_db()
    rows = conn.execute('SELECT * FROM pending_jobs ORDER BY created_at DESC').fetchall()
    conn.close()
    return stream_json(rows_to_list(rows))

@app.route('/api/pending', methods=['POST'])
def add_pending():
    data = request.get_json()
    url = data.get('url', '').strip()
    source = data.get('source', 'web')
    if not url:
        return jsonify({'error': 'URL required'}), 400

    normalized = normalize_url(url)
    conn = get_db()

    # Check if there's an active (non-done/failed) pending entry
    pending = conn.execute('SELECT id, status, url FROM pending_jobs WHERE status NOT IN (?,?)', ('done', 'failed')).fetchall()
    for row in pending:
        r = dict(row)
        if normalize_url(r['url']) == normalized:
            conn.close()
            return jsonify({'error': 'Already in queue', 'id': r['id'], 'status': r['status']}), 409

    # Check jobs table for duplicate (normalized URL) - only non-deleted
    jobs = conn.execute('SELECT num, company, url, score, match FROM jobs WHERE deleted=0').fetchall()
    for row in jobs:
        j = dict(row)
        if normalize_url(j['url']) == normalized:
            conn.close()
            return jsonify({
                'status': 'exists',
                'num': j['num'],
                'company': j['company'],
                'score': j['score'],
                'match': j['match'],
                'url': url
            })

    # Clean up any old done/failed pending entries for this URL
    old_pending = conn.execute('SELECT id FROM pending_jobs WHERE url=? AND status IN (?,?)', (url, 'done', 'failed')).fetchall()
    for row in old_pending:
        conn.execute('DELETE FROM pending_jobs WHERE id=?', (dict(row)['id'],))
    if old_pending:
        conn.commit()

    try:
        cur = conn.execute('INSERT INTO pending_jobs (url, source, status) VALUES (?, ?, ?)',
                           (url, source, 'pending'))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return jsonify({'status': 'pending', 'id': new_id, 'url': url, 'source': source})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'URL already exists', 'url': url}), 409

@app.route('/api/pending/<int:id>', methods=['DELETE'])
def delete_pending(id):
    conn = get_db()
    # Get the URL and associated job num before deleting
    row = conn.execute('SELECT url FROM pending_jobs WHERE id=?', (id,)).fetchone()
    if row:
        url = dict(row)['url']
        # Find associated job num
        job_row = conn.execute('SELECT num, company FROM jobs WHERE url=?', (url,)).fetchone()
        # Soft-delete any processed job with the same URL
        conn.execute('UPDATE jobs SET deleted=1 WHERE url=?', (url,))
        conn.execute('DELETE FROM summaries WHERE url=?', (url,))
        if job_row:
            num = dict(job_row)['num']
            conn.execute('DELETE FROM resumes WHERE id=? OR id=?', (f'pending_{num}', f'rescore_{num}'))
    conn.execute('DELETE FROM pending_jobs WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted'})

@app.route('/api/pending/<int:id>/reset', methods=['PUT'])
def reset_pending(id):
    """Reset a pending job back to pending status (from scratch)."""
    conn = get_db()
    conn.execute('''UPDATE pending_jobs SET status='pending', error=NULL, queue_order=0,
                    step_fetch=0, step_validate=0, step_extract_raw=0, step_extract_struct=0,
                    step_analyze=0, step_summary=0, step_db=0, step_done=0,
                    updated_at=? WHERE id=?''',
                 (datetime.now().isoformat(), id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'pending', 'id': id})

@app.route('/api/pending/<int:id>/pause', methods=['PUT'])
def pause_pending(id):
    """Pause a processing job — keep completed steps, reset current step, move to paused."""
    conn = get_db()
    row = conn.execute('SELECT * FROM pending_jobs WHERE id=?', (id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Not found'}), 404
    item = dict(row)
    # Find the current (first incomplete) step and reset only that one
    step_cols = ['step_fetch', 'step_validate', 'step_extract_raw', 'step_extract_struct', 'step_summary', 'step_analyze']
    reset_col = None
    for col in step_cols:
        if item.get(col) == 0:
            reset_col = col
            break
    if reset_col:
        conn.execute(f'UPDATE pending_jobs SET status="paused", error=NULL, {reset_col}=0, updated_at=? WHERE id=?',
                     (datetime.now().isoformat(), id))
    else:
        # All steps complete, just pause
        conn.execute('UPDATE pending_jobs SET status="paused", updated_at=? WHERE id=?',
                     (datetime.now().isoformat(), id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'paused', 'id': id})

@app.route('/api/pending/<int:id>/process', methods=['POST'])
def process_pending(id):
    """Move a pending/failed job to the queue for processing."""
    conn = get_db()
    row = conn.execute('SELECT * FROM pending_jobs WHERE id=?', (id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Not found'}), 404

    item = dict(row)
    if item['status'] == 'done':
        conn.close()
        return jsonify({'error': 'Already completed'}), 400
    if item['status'] == 'processing':
        conn.close()
        return jsonify({'error': 'Already processing', 'id': id}), 409
    if item['status'] == 'queued':
        conn.close()
        return jsonify({'error': 'Already queued', 'id': id}), 409

    # Reset steps if retrying a failed job
    if item['status'] == 'failed':
        conn.execute('''UPDATE pending_jobs SET error=NULL,
                        step_fetch=0, step_validate=0, step_extract_raw=0, step_extract_struct=0,
                        step_analyze=0, step_summary=0, step_db=0, step_done=0,
                        updated_at=? WHERE id=?''',
                     (datetime.now().isoformat(), id))
        conn.commit()
    conn.close()

    # Enqueue — queue manager will pick it up
    get_queue_manager().enqueue(id)

    return jsonify({'status': 'queued', 'id': id, 'url': item['url']})

@app.route('/api/refresh/dashboard', methods=['POST'])
def refresh_dashboard():
    """Manually refresh dashboard insights."""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from worker import _update_dashboard_insights
    try:
        _update_dashboard_insights(0)
        return jsonify({'status': 'updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/refresh/skills', methods=['POST'])
def refresh_skills():
    """Manually refresh skills insights."""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from worker import _update_skills_insights
    try:
        _update_skills_insights(0)
        return jsonify({'status': 'updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/refresh/analysis', methods=['POST'])
def refresh_analysis():
    """Manually refresh unified analysis (combines dashboard + skills)."""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from worker import _update_unified_analysis
    try:
        _update_unified_analysis(0)
        return jsonify({'status': 'updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis')
def get_unified_analysis():
    """Get the latest unified analysis from the analysis_runs table.
    Falls back to 'dashboard' page records if no 'analysis' page exists yet."""
    conn = get_db()
    # Try unified analysis first
    row = conn.execute(
        'SELECT id, page, created_at, analysis_json FROM analysis_runs WHERE page=? ORDER BY created_at DESC LIMIT 1',
        ('analysis',)
    ).fetchone()
    # Fall back to dashboard records
    if not row:
        row = conn.execute(
            'SELECT id, page, created_at, analysis_json FROM analysis_runs WHERE page=? ORDER BY created_at DESC LIMIT 1',
            ('dashboard',)
        ).fetchone()
    conn.close()
    if row:
        r = dict(row)
        r['analysis'] = json.loads(r['analysis_json'])
        del r['analysis_json']
        return jsonify(r)
    return jsonify({'error': 'No analysis found'}), 404

@app.route('/api/analysis/<page>')
def get_analysis(page):
    """Get the latest analysis for a page from the analysis_runs table."""
    conn = get_db()
    row = conn.execute(
        'SELECT id, page, created_at, analysis_json FROM analysis_runs WHERE page=? ORDER BY created_at DESC LIMIT 1',
        (page,)
    ).fetchone()
    conn.close()
    if row:
        r = dict(row)
        r['analysis'] = json.loads(r['analysis_json'])
        del r['analysis_json']
        return jsonify(r)
    return jsonify({'error': 'No analysis found', 'page': page}), 404

@app.route('/api/analysis/<page>/history')
def get_analysis_history(page):
    """Get all analysis runs for a page."""
    conn = get_db()
    rows = conn.execute(
        'SELECT id, page, created_at FROM analysis_runs WHERE page=? ORDER BY created_at DESC',
        (page,)
    ).fetchall()
    conn.close()
    return jsonify(rows_to_list(rows))

@app.route('/api/pending/stream')
def stream_pending():
    """SSE endpoint for real-time pending job updates."""
    import time
    def generate():
        last_modified = ''
        while True:
            conn = get_db()
            rows = conn.execute('SELECT * FROM pending_jobs ORDER BY created_at DESC').fetchall()
            conn.close()
            data = json.dumps(rows_to_list(rows), ensure_ascii=False)
            # Simple change detection via hash
            current_hash = str(hash(data))
            if current_hash != last_modified:
                last_modified = current_hash
                yield f'data: {data}\n\n'
            time.sleep(2)
    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

@app.route('/api/pending/<int:id>/step', methods=['PUT'])
def update_step(id):
    data = request.get_json()
    conn = get_db()
    fields = []
    values = []
    for key in ['status', 'step_fetch', 'step_analyze', 'step_db', 'step_done', 'job_num', 'company', 'error']:
        if key in data:
            fields.append(f'{key}=?')
            values.append(data[key])
    if fields:
        fields.append('updated_at=?')
        values.append(datetime.now().isoformat())
        values.append(id)
        conn.execute(f'UPDATE pending_jobs SET {",".join(fields)} WHERE id=?', values)
        conn.commit()
    conn.close()
    return jsonify({'status': 'updated'})

@app.route('/api/queue/status')
def queue_status():
    """Get current queue status."""
    return jsonify(get_queue_manager().get_status())

@app.route('/api/pending/queue-all', methods=['POST'])
def queue_all_pending():
    """Move all pending jobs to queued for processing."""
    conn = get_db()
    rows = conn.execute("SELECT id FROM pending_jobs WHERE status='pending' ORDER BY created_at ASC").fetchall()
    conn.close()
    pending_ids = [dict(r)['id'] for r in rows]
    if pending_ids:
        get_queue_manager().enqueue_bulk(pending_ids)
    return jsonify({'status': 'queued', 'count': len(pending_ids)})

# --- Serve React app ---

@app.route('/')
def serve():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
@app.route('/api/jobs/<int:num>/rescore', methods=['POST'])
def rescore_job(num):
    """Re-score a job through the processing pipeline."""
    conn = get_db()
    job = conn.execute('SELECT * FROM jobs WHERE num=?', (num,)).fetchone()
    if not job:
        conn.close()
        return jsonify({'error': 'Job not found'}), 404
    j = dict(job)
    url = j['url']
    # Set rescoring flag
    conn.execute('UPDATE jobs SET rescoring=1 WHERE num=?', (num,))
    # Clean up any old pending entries for this URL
    conn.execute('DELETE FROM pending_jobs WHERE url=?', (url,))
    # Insert into pending pipeline with source=rescore, status=pending
    cur = conn.execute('INSERT INTO pending_jobs (url, source, company, job_num, status) VALUES (?, ?, ?, ?, ?)',
                        (url, 'rescore', j.get('company', ''), num, 'pending'))
    conn.commit()
    pending_id = cur.lastrowid
    conn.close()
    # Enqueue — queue manager will process it
    get_queue_manager().enqueue(pending_id)
    return jsonify({'status': 'queued', 'num': num, 'company': j.get('company', ''), 'pending_id': pending_id})

@app.route('/api/jobs/rescore-all', methods=['POST'])
def rescore_all():
    """Re-score all jobs through the processing pipeline."""
    conn = get_db()
    jobs = conn.execute('SELECT num, url, company FROM jobs WHERE deleted=0 AND rescoring=0').fetchall()
    count = 0
    pending_ids = []
    for job in jobs:
        j = dict(job)
        num = j['num']
        url = j['url']
        conn.execute('UPDATE jobs SET rescoring=1 WHERE num=?', (num,))
        cur = conn.execute('INSERT INTO pending_jobs (url, source, company, job_num, status) VALUES (?, ?, ?, ?, ?)',
                            (url, 'rescore', j.get('company', ''), num, 'pending'))
        pending_ids.append(cur.lastrowid)
        count += 1
    conn.commit()
    conn.close()
    # Bulk enqueue all pending jobs in order
    if pending_ids:
        get_queue_manager().enqueue_bulk(pending_ids)
    return jsonify({'status': 'rescoring', 'count': count})

@app.route('/api/jobs/reprocess-all', methods=['POST'])
def reprocess_all():
    """Hard-delete all processed jobs and re-queue for fresh processing."""
    conn = get_db()
    jobs = conn.execute('SELECT num, url, company FROM jobs WHERE deleted=0').fetchall()
    # Hard-delete all jobs and related data
    conn.execute('DELETE FROM jobs WHERE deleted=0')
    conn.execute('DELETE FROM summaries')
    conn.execute("DELETE FROM resumes WHERE id != 'original'")
    pending_ids = []
    for job in jobs:
        j = dict(job)
        url = j['url']
        company = j.get('company', '')
        # Find or create pending entry
        row = conn.execute('SELECT id FROM pending_jobs WHERE url=?', (url,)).fetchone()
        if row:
            pid = dict(row)['id']
            conn.execute('''UPDATE pending_jobs SET status='pending', error=NULL, source='requeue',
                company=?, queue_order=0, step_fetch=0, step_validate=0, step_extract_raw=0, step_extract_struct=0,
                step_analyze=0, step_summary=0, step_db=0, step_done=0,
                workflow_log='[]', updated_at=? WHERE id=?''',
                (company, datetime.now().isoformat(), pid))
            pending_ids.append(pid)
        else:
            cur = conn.execute('INSERT INTO pending_jobs (url, source, company, status) VALUES (?, ?, ?, ?)',
                (url, 'requeue', company, 'pending'))
            pending_ids.append(cur.lastrowid)
    conn.commit()
    conn.close()
    # Bulk enqueue all pending jobs
    if pending_ids:
        get_queue_manager().enqueue_bulk(pending_ids)
    return jsonify({'status': 'reprocessing', 'count': len(pending_ids)})

def static_proxy(path):
    file_path = os.path.join(app.static_folder, path)
    if os.path.isfile(file_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
