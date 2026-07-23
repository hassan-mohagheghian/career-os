"""
Background worker that processes pending jobs by spawning mimo as a subprocess.
Fetches the URL, hands off to mimo for analysis/resume, then saves to DB.
Runs in a daemon thread — never blocks Flask.
"""
import os
import re
import json
import sqlite3
import subprocess
import threading
import tempfile
import traceback
import urllib.request
from datetime import datetime
from prompts import load_prompt

_file_dir = os.path.dirname(os.path.abspath(__file__))
_server_dir = os.path.join(_file_dir, '..')  # services/ -> server/
_db_path = os.environ.get('DB_PATH', os.path.join(_server_dir, 'db', 'jobs.db'))
DB_PATH = _db_path if os.path.isabs(_db_path) else os.path.normpath(os.path.join(_server_dir, _db_path))
PROJECT_ROOT = os.path.abspath(os.path.join(_file_dir, '..', '..', '..'))
MIMO_BIN = os.path.expanduser('~/.mimocode/bin/mimo')
_tmp = os.environ.get('TEMP_DIR', 'tmp')
TMP_DIR = _tmp if os.path.isabs(_tmp) else os.path.join(PROJECT_ROOT, _tmp)
os.makedirs(TMP_DIR, exist_ok=True)

VALID_GRADES = ['P', 'E', 'D', 'C', 'B', 'A', 'A+', 'A++']
GRADE_RANK = {g: i for i, g in enumerate(VALID_GRADES)}
NUMERIC_TO_GRADE = {
    range(0, 30): 'D', range(30, 50): 'C', range(50, 70): 'B',
    range(70, 80): 'A', range(80, 90): 'A+', range(90, 101): 'A++',
}

def normalize_score(score):
    """Ensure score is a valid letter grade. Converts numeric or invalid values."""
    if isinstance(score, str):
        s = score.strip().upper()
        # Handle variants like "a++", "A +", "a + +"
        s = s.replace(' ', '')
        if s in VALID_GRADES:
            return s
        # Try parsing as numeric
        try:
            n = int(float(s))
            return _numeric_to_grade(n)
        except (ValueError, TypeError):
            pass
    elif isinstance(score, (int, float)):
        return _numeric_to_grade(int(score))
    return 'P'

def _numeric_to_grade(n):
    """Convert a numeric score (0-100) to a letter grade."""
    n = max(0, min(100, n))
    for r, g in NUMERIC_TO_GRADE.items():
        if n in r:
            return g
    return 'P'

def calculate_overall_score(fit_score, success_score):
    """Calculate overall score as weighted average of fit and success scores."""
    if fit_score is None or success_score is None:
        return None
    return round(fit_score * 0.6 + success_score * 0.4, 1)

def score_to_grade(score):
    """Convert a numeric score (0-100) to a letter grade."""
    if score is None:
        return 'P'
    return _numeric_to_grade(int(score))

def _load_env():
    """Read .env file from project root into os.environ."""
    env_path = os.path.join(PROJECT_ROOT, '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())
_load_env()

# --- DB helpers ---

def _db():
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

def _update_step(pid, step, val, status=None, company=None, job_num=None, error=None):
    conn = _db()
    fields = [f'{step}=?']
    values = [val]
    if status:
        fields.append('status=?'); values.append(status)
    if company:
        fields.append('company=?'); values.append(company)
    if job_num:
        fields.append('job_num=?'); values.append(job_num)
    if error:
        fields.append('error=?'); values.append(error)
    fields.append('updated_at=?'); values.append(datetime.now().isoformat())
    values.append(pid)
    conn.execute(f'UPDATE pending_jobs SET {",".join(fields)} WHERE id=?', values)
    conn.commit(); conn.close()

def _get_next_num():
    conn = _db()
    row = conn.execute("SELECT MAX(num) FROM jobs").fetchone()
    conn.close()
    return (row[0] or 0) + 1

def _get_existing_num(url):
    """Check if a job with this URL already exists. Returns its num or None."""
    conn = _db()
    row = conn.execute("SELECT num FROM jobs WHERE url=?", (url,)).fetchone()
    conn.close()
    return dict(row)['num'] if row else None

def _insert_job(d):
    # Normalize location and work_type
    d = _normalize_job_data(d)
    conn = _db()
    now = datetime.now().isoformat()
    posted_at = d.get('posted_at') or _parse_posted_date(d.get('posted', ''))
    adv_at = d.get('adv_at') or _parse_adv_at(d.get('posted', ''))
    see_at = d.get('see_at') or now
    locations = d.get('locations', [])
    if isinstance(locations, str):
        locations = [locations] if locations else []

    # Employment type (single value)
    employment_type = d.get('employment_type', 'Full-time')
    et_lower = (employment_type or '').lower()
    if 'full' in et_lower:
        employment_type = 'Full-time'
    elif 'part' in et_lower:
        employment_type = 'Part-time'
    elif 'contract' in et_lower or 'freelance' in et_lower:
        employment_type = 'Contract'
    elif 'intern' in et_lower:
        employment_type = 'Internship'
    elif 'temp' in et_lower:
        employment_type = 'Temporary'
    else:
        employment_type = 'Full-time'

    # Work types (multiple values as JSON array)
    work_types = d.get('work_types', [])
    if isinstance(work_types, str):
        try:
            work_types = json.loads(work_types)
        except:
            work_types = []
    if not work_types and d.get('work_type'):
        work_types = [d['work_type']]
    # Normalize each work type
    normalized_wt = []
    for wt in work_types:
        wt_lower = (wt or '').lower()
        if 'remote' in wt_lower:
            if 'Remote' not in normalized_wt:
                normalized_wt.append('Remote')
        elif 'hybrid' in wt_lower:
            if 'Hybrid' not in normalized_wt:
                normalized_wt.append('Hybrid')
        elif 'on-site' in wt_lower or 'onsite' in wt_lower or 'office' in wt_lower:
            if 'On-site' not in normalized_wt:
                normalized_wt.append('On-site')
    if not normalized_wt:
        normalized_wt = ['On-site']

    conn.execute('''INSERT OR REPLACE INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (d['num'], d['company'], d['role'], d['location'], d['match'],
         d['score'], d['salary'], d['stack'], d['visa'], d['applicants'],
         d['posted'], d['industry'], d['domain'], d['notes'], d['action'], d['url'],
         normalized_wt[0] if normalized_wt else 'On-site', d.get('workflow_log', '[]'),
         d.get('created_at', now), posted_at, json.dumps(locations), 0,
         employment_type, json.dumps(normalized_wt), d.get('raw_description'),
         d.get('structured_description'), d.get('raw_file_path'),
         d.get('structured_file_path'), d.get('rescoring', 0), d.get('success'),
         adv_at, see_at, d.get('apply_reason', ''), d.get('company_url'), d.get('linkedin_url'),
         d.get('apply_time'), d.get('response_time'), d.get('response_status'),
         d.get('fit_score'), d.get('success_score'), d.get('overall_score'),
         d.get('company_id')))
    conn.commit(); conn.close()


def _parse_posted_date(posted_text):
    """Parse relative posted text like '~2 weeks ago' into ISO datetime."""
    if not posted_text or posted_text in ('Active', 'N/A', 'Not specified'):
        return None
    now = datetime.now()
    posted_text = posted_text.lower().strip()
    try:
        if 'hour' in posted_text:
            hours = int(''.join(filter(str.isdigit, posted_text)) or 1)
            from datetime import timedelta
            return (now - timedelta(hours=hours)).isoformat()
        elif 'day' in posted_text:
            days = int(''.join(filter(str.isdigit, posted_text)) or 1)
            from datetime import timedelta
            return (now - timedelta(days=days)).isoformat()
        elif 'week' in posted_text:
            weeks = int(''.join(filter(str.isdigit, posted_text)) or 1)
            from datetime import timedelta
            return (now - timedelta(weeks=weeks)).isoformat()
        elif 'month' in posted_text:
            months = int(''.join(filter(str.isdigit, posted_text)) or 1)
            from dateutil.relativedelta import relativedelta
            return (now - relativedelta(months=months)).isoformat()
    except Exception:
        return None
    return None


def _parse_adv_at(posted_text):
    """Estimate when the job was advertised. If no specific datetime, return current datetime.
    For human-readable text like '1 month', '1 month+', '4 months+':
    - exact like '1 month' -> 1 month ago
    - with '+' like '1 month+' -> 1.5 months ago (adds 0.5)
    - '4 months+' -> 4.5 months ago
    """
    now = datetime.now()
    if not posted_text or posted_text in ('Active', 'N/A', 'Not specified'):
        return now.isoformat()
    posted_text = posted_text.lower().strip()
    has_plus = '+' in posted_text
    try:
        if 'hour' in posted_text:
            hours = int(''.join(filter(str.isdigit, posted_text)) or 1)
            from datetime import timedelta
            return (now - timedelta(hours=hours)).isoformat()
        elif 'day' in posted_text:
            days = int(''.join(filter(str.isdigit, posted_text)) or 1)
            from datetime import timedelta
            return (now - timedelta(days=days)).isoformat()
        elif 'week' in posted_text:
            weeks = int(''.join(filter(str.isdigit, posted_text)) or 1)
            from datetime import timedelta
            return (now - timedelta(weeks=weeks)).isoformat()
        elif 'month' in posted_text:
            months = int(''.join(filter(str.isdigit, posted_text)) or 1)
            if has_plus:
                months += 0.5
            from dateutil.relativedelta import relativedelta
            return (now - relativedelta(months=months)).isoformat()
    except Exception:
        pass
    return now.isoformat()

def _save_job_workflow_log(num, log_json):
    """Save workflow log to the jobs table."""
    conn = _db()
    conn.execute('UPDATE jobs SET workflow_log=? WHERE num=?', (log_json, num))
    conn.commit(); conn.close()

def _insert_summary(d):
    conn = _db()
    conn.execute('''INSERT OR REPLACE INTO summaries VALUES (?,?,?,?,?,?,?,?,?)''',
        (d['num'], d['company'], d['match'], d['score'],
         d['summary'], d['stack'], d['resumeFit'], d['note'], d['url']))
    conn.commit(); conn.close()

def _insert_resume(d):
    conn = _db()
    conn.execute('''INSERT OR REPLACE INTO resumes (id, title, company, role, content, version, raw_text, created_at, job_num) VALUES (?,?,?,?,?,?,?,?,?)''',
        (d['id'], d.get('title'),
         d.get('company'), d.get('role'), d.get('content'),
         d.get('version', 1), d.get('raw_text'), d.get('created_at'), d.get('job_num')))
    conn.commit(); conn.close()

def _mark(pid, step, company=None, job_num=None):
    _update_step(pid, step, 1, company=company, job_num=job_num)

def _get_item(pid):
    """Re-read the pending item from DB to check for status changes (pause/stop)."""
    conn = _db()
    row = conn.execute('SELECT * FROM pending_jobs WHERE id=?', (pid,)).fetchone()
    conn.close()
    return dict(row) if row else None

def _is_paused_or_stopped(pid):
    """Check if job was paused or stopped (status changed to non-processing)."""
    item = _get_item(pid)
    if not item:
        return True  # Item deleted, stop
    return item['status'] not in ('processing',)

def rescore_only(num):
    """Re-score an existing job without the full pipeline.
    Reads the raw description, runs mimo analysis, and updates the job."""
    conn = _db()
    job = conn.execute('SELECT * FROM jobs WHERE num=?', (num,)).fetchone()
    conn.close()
    if not job:
        print(f"[worker] Rescore: job #{num} not found")
        return

    j = dict(job)
    url = j['url']
    raw_desc = j.get('raw_description', '')
    if not raw_desc:
        # Try reading from file
        raw_path = j.get('raw_file_path', '')
        if raw_path and os.path.exists(raw_path):
            with open(raw_path) as f:
                raw_desc = f.read()
    if not raw_desc:
        print(f"[worker] Rescore: no raw description for job #{num}")
        conn = _db()
        conn.execute('UPDATE jobs SET rescoring=0 WHERE num=?', (num,))
        conn.commit(); conn.close()
        return

    job_file = os.path.join(TMP_DIR, f'rescore_{num}.txt')
    try:
        with open(job_file, 'w') as f:
            f.write(raw_desc)

        rules = _load_rules()
        # Load resume from DB (latest version)
        resume_file = os.path.join(TMP_DIR, f'rescore_resume_{num}.txt')
        conn = _db()
        resume_row = conn.execute("SELECT raw_text FROM resumes WHERE id LIKE 'original_%' ORDER BY version DESC LIMIT 1").fetchone()
        conn.close()
        if resume_row and dict(resume_row).get('raw_text'):
            with open(resume_file, 'w') as f:
                f.write(dict(resume_row)['raw_text'])
            resume_path = resume_file
        else:
            resume_path = os.path.join(PROJECT_ROOT, 'inputs', 'original', 'resume.txt')

        # Use a unique pid per rescore run to avoid file conflicts
        rescore_pid = f'rescore_{num}_{int(datetime.now().timestamp()*1000)}'
        prompt = load_prompt('step8_score',
            url=url, job_file=job_file, resume_file=resume_path,
            tmp_dir=TMP_DIR, pid=rescore_pid, next_num=num, rules=rules)

        returncode, output_lines = _stream_mimo_output(
            [MIMO_BIN, 'run', prompt, '--format', 'json', '--dangerously-skip-permissions'],
            cwd=PROJECT_ROOT,
            env={**os.environ, 'NO_COLOR': '1'},
            timeout=300,
            pid=rescore_pid,
        )

        if returncode != 0:
            error_msg = f"exit code {returncode}"
            for line in output_lines:
                try:
                    evt = json.loads(line)
                    if evt.get('type') == 'text':
                        error_msg = evt.get('part', {}).get('text', error_msg)[:300]
                except json.JSONDecodeError:
                    continue
            raise RuntimeError(f"mimo failed: {error_msg}")

        result_path = os.path.join(TMP_DIR, f'pending_result_{rescore_pid}.json')
        if not os.path.exists(result_path):
            raise RuntimeError(f"Result file not found: {result_path}")

        with open(result_path) as f:
            data = json.load(f)

        analyzed_data = data['job']

        # Parse numeric scores from mimo output
        fit_score_raw = analyzed_data.get('fit_score')
        success_score_raw = analyzed_data.get('success_score')
        fit_score = max(0, min(100, int(fit_score_raw))) if fit_score_raw is not None else None
        success_score = max(0, min(100, int(success_score_raw))) if success_score_raw is not None else None

        # Compute overall_score: (fit * 0.6) + (success * 0.4)
        overall_score = None
        if fit_score is not None and success_score is not None:
            overall_score = int(round(fit_score * 0.6 + success_score * 0.4))

        # Update the existing job with new scores
        job_data = {
            'num': num,
            'company': analyzed_data.get('company', j['company']),
            'role': analyzed_data.get('role', j['role']),
            'location': analyzed_data.get('location', j.get('location', 'Not specified')),
            'locations': analyzed_data.get('locations', []),
            'match': analyzed_data.get('match', j.get('match', 'Medium')),
            'score': normalize_score(analyzed_data.get('score', j.get('score', 'P'))),
            'success': normalize_score(analyzed_data.get('success', j.get('success', 'P'))),
            'fit_score': fit_score,
            'success_score': success_score,
            'overall_score': overall_score,
            'salary': analyzed_data.get('salary', j.get('salary', 'Not specified')),
            'stack': analyzed_data.get('stack', j.get('stack', '')),
            'visa': analyzed_data.get('visa', j.get('visa', 'Uncertain')),
            'applicants': analyzed_data.get('applicants', j.get('applicants', 'Not specified')),
            'posted': analyzed_data.get('posted', j.get('posted', 'Not specified')),
            'posted_at': analyzed_data.get('posted_at', j.get('posted_at')),
            'adv_at': analyzed_data.get('adv_at', j.get('adv_at')),
            'see_at': j.get('see_at'),
            'apply_reason': analyzed_data.get('apply_reason', j.get('apply_reason', '')),
            'industry': analyzed_data.get('industry', j.get('industry', '')),
            'domain': analyzed_data.get('domain', j.get('domain', '')),
            'notes': analyzed_data.get('notes', j.get('notes', '')),
            'action': analyzed_data.get('action', j.get('action', '')),
            'employment_type': analyzed_data.get('employment_type', j.get('employment_type', 'Full-time')),
            'work_types': analyzed_data.get('work_types', []),
            'workflow_log': analyzed_data.get('workflow_log', j.get('workflow_log', '[]')),
            'raw_description': raw_desc,
            'structured_description': j.get('structured_description'),
            'raw_file_path': j.get('raw_file_path'),
            'structured_file_path': j.get('structured_file_path'),
        }

        _insert_job(job_data)
        _insert_summary({
            'num': num, 'company': job_data['company'],
            'match': job_data['match'], 'score': job_data['score'],
            'summary': data.get('summary', {}).get('summary', ''),
            'stack': job_data['stack'],
            'resumeFit': data.get('summary', {}).get('resumeFit', ''),
            'note': data.get('summary', {}).get('note', ''),
            'url': url,
        })

        resume_data = {
            'id': f"rescore_{num}",
            'title': f"{job_data['company']} (Score {job_data['score']})",
            'company': job_data['company'], 'role': job_data['role'],
            'job_num': num,
            'content': data.get('resume_html', ''),
        }
        _insert_resume(resume_data)

        # Clear rescoring flag
        conn = _db()
        conn.execute('UPDATE jobs SET rescoring=0 WHERE num=?', (num,))
        conn.commit(); conn.close()

        try: os.remove(result_path)
        except OSError: pass
        print(f"[worker] Rescore #{num} done: {job_data['company']} (score: {job_data['score']})")

    except Exception as e:
        print(f"[worker] Rescore #{num} FAILED: {e}")
        # Clear rescoring flag on failure
        conn = _db()
        conn.execute('UPDATE jobs SET rescoring=0 WHERE num=?', (num,))
        conn.commit(); conn.close()
    finally:
        try: os.remove(job_file)
        except OSError: pass

def _fail(pid, msg, step=None):
    """Mark job as failed with error message and which step failed."""
    STEP_LABELS = {
        'fetch': 'Fetching job page',
        'validate': 'Validating content',
        'extract_raw': 'Extracting raw info',
        'extract_struct': 'Structuring data',
        'summary': 'Building summary',
        'score': 'Scoring & analyzing',
        'resume': 'Saving results',
        'done': 'Finalizing',
        'mimo': 'AI analysis',
        'worker': 'Processing',
    }
    label = STEP_LABELS.get(step, step) if step else 'Processing'
    error_msg = f"[{label}] {msg}" if step else msg
    _update_step(pid, 'step_done', 0, status='failed', error=error_msg)

def _log(pid, step, msg):
    """Append a workflow log entry."""
    conn = _db()
    row = conn.execute('SELECT workflow_log FROM pending_jobs WHERE id=?', (pid,)).fetchone()
    logs = json.loads(row['workflow_log'] or '[]') if row else []
    logs.append({'step': step, 'msg': msg, 'ts': datetime.now().strftime('%H:%M:%S')})
    conn.execute('UPDATE pending_jobs SET workflow_log=? WHERE id=?', (json.dumps(logs), pid))
    conn.commit(); conn.close()

def _load_rules(context='job'):
    """Load enabled scoring rules from DB, filtered by context, ordered by priority desc.

    Args:
        context: 'job' loads SHARED + JOB rules only.
                 'company' loads SHARED + company-type rules (caller must pass correct scopes).

    Validation: Job processor must NEVER load COMPANY_PRODUCT or COMPANY_RECRUITING rules.
    """
    conn = _db()
    # Only load SHARED and JOB rules for job processing — never company rules
    rows = conn.execute(
        "SELECT category, scope, key, value, description, priority, score_weight "
        "FROM preferences WHERE enabled=1 AND scope IN ('SHARED', 'JOB') "
        "ORDER BY priority DESC"
    ).fetchall()
    conn.close()
    if not rows:
        return "No scoring rules set."
    lines = []
    current_cat = None
    for row in rows:
        r = dict(row)
        cat = r['category']
        if cat != current_cat:
            current_cat = cat
            lines.append(f"\n── {cat.upper()} {'─' * (35 - len(cat))}")
        weight = r.get('score_weight') or r['priority']
        lines.append(f"  #{r['priority']:>3}  {r['key']} (weight:{weight}): {r['value']}")
    return '\n'.join(lines)

def _extract_structured_description(raw_text, num):
    """Extract structured job info from raw description using mimo."""
    output_file = os.path.join(TMP_DIR, f'structured_{num}.json')
    prompt = load_prompt('step4_extract_struct',
        raw_content=raw_text[:5000], output_file=output_file)

    proc = subprocess.run(
        [MIMO_BIN, 'run', prompt, '--format', 'json', '--dangerously-skip-permissions'],
        cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=60,
        env={**os.environ, 'NO_COLOR': '1'}
    )

    if proc.returncode == 0 and os.path.exists(output_file):
        try:
            with open(output_file) as f:
                structured = json.load(f)
            os.remove(output_file)
            return json.dumps(structured, ensure_ascii=False)
        except Exception:
            pass
    return None

def _extract_all(raw_text, pid):
    """Combined extraction: validate + structured + summary in one mimo call."""
    output_file = os.path.join(TMP_DIR, f'extract_{pid}.json')
    prompt = load_prompt('step3_extract_raw',
        content=raw_text[:5000], output_file=output_file)

    proc = subprocess.run(
        [MIMO_BIN, 'run', prompt, '--format', 'json', '--dangerously-skip-permissions'],
        cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=90,
        env={**os.environ, 'NO_COLOR': '1'}
    )

    if proc.returncode == 0 and os.path.exists(output_file):
        try:
            with open(output_file) as f:
                result = json.load(f)
            os.remove(output_file)
            return result
        except Exception:
            pass
    return None

def _mark_old_job_deleted(url, exclude_num=None):
    """Mark old job with same URL as deleted when rescore/requeue creates a new one."""
    conn = _db()
    if exclude_num:
        conn.execute('UPDATE jobs SET deleted=1 WHERE url=? AND num!=?', (url, exclude_num))
    else:
        conn.execute('UPDATE jobs SET deleted=1 WHERE url=?', (url,))
    conn.commit(); conn.close()

def _normalize_job_data(d):
    """Normalize job location and work_type fields."""
    import re

    # Known cities
    CITIES = {
        'berlin': 'Berlin', 'munich': 'Munich', 'münchen': 'Munich',
        'hamburg': 'Hamburg', 'heidelberg': 'Heidelberg', 'frankfurt': 'Frankfurt',
        'cologne': 'Cologne', 'köln': 'Cologne', 'stuttgart': 'Stuttgart',
        'leipzig': 'Leipzig', 'dortmund': 'Dortmund', 'magdeburg': 'Magdeburg',
        'madrid': 'Madrid', 'barcelona': 'Barcelona', 'paris': 'Paris',
        'london': 'London', 'amsterdam': 'Amsterdam', 'vienna': 'Vienna',
        'wien': 'Vienna', 'zurich': 'Zurich', 'zürich': 'Zurich',
    }

    def extract_cities(text):
        if not text:
            return []
        cities = []
        text = re.sub(r'\(.*?\)', '', text)  # Remove parentheses
        parts = re.split(r'[,/\|]', text)
        for part in parts:
            part = part.strip().lower()
            if part in CITIES and CITIES[part] not in cities:
                cities.append(CITIES[part])
        return cities

    # Normalize location
    location = d.get('location', '')
    if location:
        # Extract just city from "Munich, Bavaria, Germany" -> "Munich"
        cities = extract_cities(location)
        if cities:
            d['location'] = cities[0]

    # Normalize locations array
    locations = d.get('locations', [])
    if isinstance(locations, str):
        try:
            locations = json.loads(locations)
        except:
            locations = []

    # Add cities from primary location if not in array
    if location:
        for city in extract_cities(location):
            if city not in locations:
                locations.append(city)

    # Normalize each location in array
    normalized = []
    for loc in locations:
        if isinstance(loc, str):
            cities = extract_cities(loc)
            for c in cities:
                if c not in normalized:
                    normalized.append(c)
            if not cities and loc.strip():
                # Keep as-is if not a known city but not empty
                if loc.strip() not in normalized:
                    normalized.append(loc.strip())

    d['locations'] = normalized if normalized else [d.get('location', 'Not specified')]

    # Normalize work_type
    work_type = d.get('work_type', 'On-site')
    wt_lower = (work_type or '').lower()
    if 'remote' in wt_lower or 'work from anywhere' in wt_lower:
        d['work_type'] = 'Remote'
    elif 'hybrid' in wt_lower or 'flexible' in wt_lower:
        d['work_type'] = 'Hybrid'
    else:
        d['work_type'] = 'On-site'

    return d

# --- URL fetcher ---

def _fetch_url(url):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise RuntimeError(f"Page not found (404) — the job posting no longer exists or the URL is incorrect: {url}") from None
        elif e.code == 403:
            raise RuntimeError(f"Access denied (403) — the website is blocking automated requests. The job may require login to view: {url}") from None
        elif e.code == 503:
            raise RuntimeError(f"Service unavailable (503) — the website is temporarily down. Try again later: {url}") from None
        else:
            raise RuntimeError(f"HTTP error {e.code}: {e.reason} — could not fetch job posting: {url}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error — could not connect to the server. Check your internet connection and verify the URL is correct: {url}") from None
    except Exception as e:
        raise RuntimeError(f"Failed to fetch URL: {e}") from None
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    for marker in ['About The Role', 'Job Description', 'Description', 'What you.ll do', 'What You.ll Do', 'The Role']:
        idx = text.find(marker)
        if idx != -1:
            text = text[idx:]
            break
    if len(text) < 100:
        raise RuntimeError(f"Page content too short ({len(text)} chars) — LinkedIn may require login to view this job, or the URL is not a valid job posting: {url}")
    return text[:5000]

def _validate_job_content(raw_text, pid):
    """Validate and extract main job section from fetched content using mimo."""
    result_file = os.path.join(TMP_DIR, f'validate_{pid}.json')
    prompt = load_prompt('step2_validate', content=raw_text[:3000], result_file=result_file)

    proc = subprocess.run(
        [MIMO_BIN, 'run', prompt, '--format', 'json', '--dangerously-skip-permissions'],
        cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=60,
        env={**os.environ, 'NO_COLOR': '1'}
    )

    if proc.returncode == 0 and os.path.exists(result_file):
        try:
            with open(result_file) as f:
                result = json.load(f)
            os.remove(result_file)
            return result
        except Exception:
            pass
    # Fallback: heuristic validation
    job_keywords = ['engineer', 'developer', 'software', 'senior', 'backend', 'frontend',
                    'python', 'devops', 'sre', 'platform', 'role', 'responsibilities',
                    'requirements', 'qualifications', 'experience', 'apply', 'salary']
    text_lower = raw_text.lower()
    matches = sum(1 for kw in job_keywords if kw in text_lower)
    return {'valid': matches >= 2, 'content': raw_text, 'reason': f'Heuristic: {matches} job keywords found', 'title': None, 'company': None}

# --- Streaming subprocess execution ---

def _stream_mimo_output(cmd, cwd, env, timeout, pid):
    """Run mimo with Popen and stream stdout line by line.

    Reads output incrementally while the process is still running.
    Merges stderr into stdout (stderr=subprocess.STDOUT) to avoid the
    classic deadlock where one pipe fills up while the other is starved.
    Each JSON event is parsed and logged to the DB *immediately* —
    before the child process exits — so the frontend can pick it up
    via SSE polling or WebSocket with no additional delay.

    Returns (returncode, all_lines).
    Raises RuntimeError on timeout.
    """
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,   # merge — avoids deadlock entirely
        text=True,
        env=env,
    )

    all_lines = []
    timed_out = threading.Event()

    def watchdog():
        timed_out.wait(timeout)
        if not timed_out.is_set():
            try:
                proc.kill()
            except OSError:
                pass

    timer = threading.Thread(target=watchdog, daemon=True)
    timer.start()

    try:
        # Python's file iterator reads chunks from the OS pipe and
        # yields complete lines.  Because we merged stderr, there is
        # only one pipe to drain — no cross-thread coordination needed.
        for raw_line in proc.stdout:
            line = raw_line.rstrip('\n')
            if not line:
                continue
            all_lines.append(line)

            # ── Process each event IMMEDIATELY ──
            try:
                evt = json.loads(line)
                _handle_mimo_event(pid, evt)
            except json.JSONDecodeError:
                _log(pid, 'mimo', f'[raw] {line[:200]}')

        timed_out.set()        # cancel watchdog
        proc.wait()

        if proc.returncode == -9:   # SIGKILL from watchdog
            raise RuntimeError(f"mimo timed out after {timeout}s")

        return proc.returncode, all_lines

    except:
        timed_out.set()
        try:
            proc.kill()
        except OSError:
            pass
        proc.wait()
        raise


def _handle_mimo_event(pid, evt):
    """Process a single JSON event the moment it arrives on stdout.

    This function is the extension point for real-time delivery:
    - Log to DB (already wired via _log)
    - Push to WebSocket / SSE / queue / callback — add here
    """
    event_type = evt.get('type', '')

    if event_type == 'text':
        text = evt.get('part', {}).get('text', '')
        if text:
            _log(pid, 'mimo', f'text: {text[:200]}')

    elif event_type == 'tool_use':
        part = evt.get('part', {})
        tool = part.get('tool', 'unknown')
        state = part.get('state', {})
        status = state.get('status', '')
        title = state.get('title', '')
        _log(pid, 'mimo', f'tool: {tool} [{status}] {title}')

    elif event_type == 'step_finish':
        part = evt.get('part', {})
        reason = part.get('reason', '')
        tokens = part.get('tokens', {})
        _log(pid, 'mimo',
             f'step_finish: {reason} ({tokens.get("total", 0)} tokens)')


# --- Main pipeline ---

def process_job(pid):
    """
    Full pipeline (5 steps + done):
    1. Fetch     — download URL, save raw to temp file
    2. Extract   — extract structured description via mimo
    3. Analyze   — mimo scores/resumes the job
    4. Resume    — read mimo result, save raw+structured files
    5. Save      — write to DB (jobs, summaries, resumes)
    Done         — finalize
    """
    conn = _db()
    row = conn.execute('SELECT * FROM pending_jobs WHERE id=?', (pid,)).fetchone()
    conn.close()
    if not row:
        return
    item = dict(row)
    url = item['url']
    source = item.get('source', 'cli')

    job_file = os.path.join(TMP_DIR, f'job_{pid}.txt')

    try:
        current_step = 'fetch'
        _log(pid, 'start', f'Processing {url[:60]}...')

        if source == 'rescore':
            # ── RESCORE PATH: skip fetch/validate/extract, go straight to scoring ──
            _log(pid, 'rescore', 'Rescoring — loading existing job data from DB...')

            # Load existing job from DB
            conn = _db()
            existing_job = conn.execute('SELECT * FROM jobs WHERE num=?', (item.get('job_num', 0),)).fetchone()
            conn.close()
            if not existing_job:
                raise RuntimeError(f"Original job #{item.get('job_num')} not found in DB")

            ej = dict(existing_job)
            raw_text = ej.get('raw_description', '')
            if not raw_text:
                raw_path = ej.get('raw_file_path', '')
                if raw_path and os.path.exists(raw_path):
                    with open(raw_path) as f:
                        raw_text = f.read()
            if not raw_text:
                raise RuntimeError("No raw description available for rescoring")

            # Write raw content to temp file for the prompt
            with open(job_file, 'w') as f:
                f.write(raw_text)

            # Mark early steps as done instantly
            _mark(pid, 'step_fetch')
            _mark(pid, 'step_validate')
            _mark(pid, 'step_extract_raw')
            _mark(pid, 'step_extract_struct')
            _mark(pid, 'step_summary')

            # Build job_data from existing job
            job_data = {
                'num': ej['num'],
                'company': ej['company'],
                'role': ej['role'],
                'location': ej['location'],
                'locations': ej.get('locations', '[]'),
                'match': ej['match'],
                'score': ej['score'],
                'success': ej.get('success', 'P'),
                'salary': ej.get('salary', 'Not specified'),
                'stack': ej.get('stack', ''),
                'visa': ej.get('visa', 'Uncertain'),
                'applicants': ej.get('applicants', 'Not specified'),
                'posted': ej.get('posted', 'Not specified'),
                'industry': ej.get('industry', ''),
                'domain': ej.get('domain', ''),
                'notes': ej.get('notes', ''),
                'action': ej.get('action', ''),
                'url': url,
                'raw_description': raw_text,
                'structured_description': ej.get('structured_description'),
                'employment_type': ej.get('employment_type', 'Full-time'),
                'work_types': ej.get('work_types', []),
                'adv_at': ej.get('adv_at'),
                'see_at': ej.get('see_at'),
                'apply_reason': ej.get('apply_reason', ''),
            }
            existing_num = ej['num']

            # Skip to scoring step
            current_step = 'score'
            _update_step(pid, 'step_analyze', 0, status='processing')
            _log(pid, 'analyze', f'Rescoring existing job #{existing_num}...')
            rules = _load_rules()

            resume_file = os.path.join(TMP_DIR, f'resume_{pid}.txt')
            conn = _db()
            resume_row = conn.execute("SELECT raw_text FROM resumes WHERE id LIKE 'original_%' ORDER BY version DESC LIMIT 1").fetchone()
            conn.close()
            if resume_row and dict(resume_row).get('raw_text'):
                with open(resume_file, 'w') as f:
                    f.write(dict(resume_row)['raw_text'])
                resume_path = resume_file
            else:
                resume_path = os.path.join(PROJECT_ROOT, 'inputs', 'original', 'resume.txt')

            # Load LinkedIn profile for rescore
            linkedin_file = os.path.join(TMP_DIR, f'linkedin_{pid}.txt')
            conn = _db()
            linkedin_row = conn.execute("SELECT raw_text FROM resumes WHERE id LIKE 'linkedin_%' ORDER BY version DESC LIMIT 1").fetchone()
            conn.close()
            linkedin_step = "Read the candidate's LinkedIn profile from {linkedin_file} for additional context about their experience and skills"
            if linkedin_row and dict(linkedin_row).get('raw_text'):
                with open(linkedin_file, 'w') as f:
                    f.write(dict(linkedin_row)['raw_text'])
                linkedin_path = linkedin_file
            else:
                linkedin_path = None
                linkedin_step = "No LinkedIn profile available — skip this step"

            prompt = load_prompt('step8_score',
                url=url, job_file=job_file, resume_file=resume_path,
                linkedin_file=linkedin_path or '', linkedin_step=linkedin_step,
                tmp_dir=TMP_DIR, pid=pid, next_num=existing_num, rules=rules)

            returncode, output_lines = _stream_mimo_output(
                [MIMO_BIN, 'run', prompt, '--format', 'json', '--dangerously-skip-permissions'],
                cwd=PROJECT_ROOT,
                env={**os.environ, 'NO_COLOR': '1'},
                timeout=300,
                pid=pid,
            )

            if returncode != 0:
                error_msg = f"exit code {returncode}"
                for line in output_lines:
                    try:
                        evt = json.loads(line)
                        if evt.get('type') == 'text':
                            error_msg = evt.get('part', {}).get('text', error_msg)[:300]
                    except json.JSONDecodeError:
                        continue
                raise RuntimeError(f"mimo failed: {error_msg}")

            result_path = os.path.join(TMP_DIR, f'pending_result_{pid}.json')
            if not os.path.exists(result_path):
                raise RuntimeError(f"Result file not found: {result_path}")

            with open(result_path) as f:
                data = json.loads(f.read(), strict=False)

            analyzed_data = data['job']
            _mark(pid, 'step_analyze', company=analyzed_data.get('company'), job_num=job_data['num'])

            # Parse numeric scores from mimo output
            fit_score_raw = analyzed_data.get('fit_score')
            success_score_raw = analyzed_data.get('success_score')
            fit_score = max(0, min(100, int(fit_score_raw))) if fit_score_raw is not None else None
            success_score = max(0, min(100, int(success_score_raw))) if success_score_raw is not None else None

            # Compute overall_score: (fit * 0.6) + (success * 0.4)
            overall_score = None
            if fit_score is not None and success_score is not None:
                overall_score = int(round(fit_score * 0.6 + success_score * 0.4))

            score = normalize_score(analyzed_data.get('score', 'P'))
            match = analyzed_data.get('match', 'Medium')
            _log(pid, 'analyze', f'Score: {score} (fit={fit_score}) — Success: {normalize_score(analyzed_data.get("success", "P"))} (prob={success_score}) — Overall: {overall_score} — Match: {match}')

            job_data.update({
                'company': analyzed_data.get('company', job_data['company']),
                'role': analyzed_data.get('role', job_data['role']),
                'location': analyzed_data.get('location', job_data['location']),
                'locations': analyzed_data.get('locations', []),
                'match': match,
                'score': score,
                'success': normalize_score(analyzed_data.get('success', 'P')),
                'fit_score': fit_score,
                'success_score': success_score,
                'overall_score': overall_score,
                'salary': analyzed_data.get('salary', job_data.get('salary', 'Not specified')),
                'stack': analyzed_data.get('stack', job_data.get('stack', '')),
                'visa': analyzed_data.get('visa', job_data.get('visa', 'Uncertain')),
                'applicants': analyzed_data.get('applicants', job_data.get('applicants', 'Not specified')),
                'posted': analyzed_data.get('posted', job_data.get('posted', 'Not specified')),
                'posted_at': analyzed_data.get('posted_at'),
                'adv_at': analyzed_data.get('adv_at', job_data.get('adv_at')),
                'apply_reason': analyzed_data.get('apply_reason', job_data.get('apply_reason', '')),
                'industry': analyzed_data.get('industry', job_data.get('industry', '')),
                'domain': analyzed_data.get('domain', job_data.get('domain', '')),
                'notes': analyzed_data.get('notes', job_data.get('notes', '')),
                'action': analyzed_data.get('action', job_data.get('action', '')),
                'employment_type': analyzed_data.get('employment_type', job_data.get('employment_type', 'Full-time')),
                'work_types': analyzed_data.get('work_types', job_data.get('work_types', [])),
                'workflow_log': analyzed_data.get('workflow_log', '[]'),
                'company_url': analyzed_data.get('company_url', job_data.get('company_url')),
                'linkedin_url': analyzed_data.get('linkedin_url', job_data.get('linkedin_url')),
            })

            # Save updated job, summary, and resume
            _insert_job(job_data)
            _log(pid, 'save', 'Updated job with new score')
            _insert_summary({
                'num': job_data['num'], 'company': job_data['company'],
                'match': match, 'score': score,
                'summary': data.get('summary', {}).get('summary', ''),
                'stack': job_data.get('stack'),
                'resumeFit': data.get('summary', {}).get('resumeFit', ''),
                'note': data.get('summary', {}).get('note', ''), 'url': url,
            })
            # Clear rescoring flag
            conn = _db()
            conn.execute('UPDATE jobs SET rescoring=0 WHERE num=?', (job_data['num'],))
            conn.commit(); conn.close()
            _log(pid, 'done', f"Rescore complete: {job_data['company']} #{job_data['num']} → score {score}")

            # Mark pending done
            _update_step(pid, 'step_done', 0, status='done')
            _mark(pid, 'step_done')

            # Save workflow_log to jobs table
            conn = _db()
            row = conn.execute('SELECT workflow_log FROM pending_jobs WHERE id=?', (pid,)).fetchone()
            conn.close()
            if row:
                _save_job_workflow_log(job_data['num'], dict(row)['workflow_log'] or '[]')

            try: os.remove(result_path)
            except OSError: pass
            return

        # ── NORMAL PATH: fetch, validate, extract, score ──

        # Check before step 1
        if _is_paused_or_stopped(pid):
            _log(pid, 'pause', 'Job paused/stopped before fetch')
            return

        # ── Step 1: Fetch ──
        _update_step(pid, 'step_fetch', 0, status='processing')
        _log(pid, 'fetch', 'Fetching page...')
        raw_text = _fetch_url(url)
        with open(job_file, 'w') as f:
            f.write(raw_text)
        _log(pid, 'fetch', f'Fetched {len(raw_text)} chars')
        _mark(pid, 'step_fetch')

        if _is_paused_or_stopped(pid):
            _log(pid, 'pause', 'Job paused/stopped after fetch')
            return

        # ── Steps 2-6: Combined extraction (one mimo call, separate UI steps) ──
        # Step 2: Validate
        current_step = 'validate'
        _update_step(pid, 'step_validate', 0, status='processing')
        _log(pid, 'validate', 'Extracting job info...')
        _mark(pid, 'step_validate')

        # Step 3: Extract structured + summary (one mimo call)
        current_step = 'extract_raw'
        _update_step(pid, 'step_extract_raw', 0, status='processing')
        extraction = _extract_all(raw_text, pid)
        if extraction and extraction.get('valid', False):
            _log(pid, 'extract_raw', f'Valid: {extraction.get("reason", "OK")}')
        else:
            reason = extraction.get('reason', 'Unknown') if extraction else 'Extraction failed'
            _log(pid, 'extract_raw', f'WARNING: {reason} — continuing anyway')
        _mark(pid, 'step_extract_raw')

        # Step 4: Process structured data
        current_step = 'extract_struct'
        _update_step(pid, 'step_extract_struct', 0, status='processing')
        structured_json = json.dumps(extraction, ensure_ascii=False) if extraction else None
        _mark(pid, 'step_extract_struct')

        # Step 5: Build summary
        current_step = 'summary'
        _update_step(pid, 'step_summary', 0, status='processing')
        title = (extraction or {}).get('title') or ''
        company = (extraction or {}).get('company') or ''
        if not title:
            for tline in raw_text.split('\n'):
                tline = tline.strip()
                if tline and 5 < len(tline) < 120:
                    if any(kw in tline.lower() for kw in ['engineer', 'developer', 'software', 'senior', 'backend', 'frontend', 'python', 'devops', 'sre', 'platform']):
                        title = tline
                        break
        if not company:
            for marker in ['hiring', ' at ', '—', '|']:
                idx = raw_text.find(marker)
                if 0 < idx < 200:
                    company = raw_text[max(0, idx-50):idx].strip().split('\n')[-1].strip()
                    company = company.replace('hiring', '').replace(' at ', '').strip()
                    if company and 2 < len(company) < 60:
                        break
                    company = ''
        if title or company:
            conn = _db()
            conn.execute('UPDATE pending_jobs SET company=? WHERE id=?', (company or title[:40], pid))
            conn.commit(); conn.close()
        _log(pid, 'summary', f'Summary: {(extraction or {}).get("summary", "")[:150]}')
        _mark(pid, 'step_summary')

        # Step 6: Save to DB
        current_step = 'resume'
        temp_num = _get_next_num()
        existing_num = _get_existing_num(url)
        if existing_num:
            temp_num = existing_num
        job_data = {
            'num': temp_num, 'company': company or title or 'Unknown',
            'role': title or 'Unknown', 'location': (extraction or {}).get('location', 'Not specified'),
            'locations': (extraction or {}).get('locations', []),
            'match': 'Pending', 'score': 'P', 'success': 'P',
            'salary': (extraction or {}).get('salary', 'Not specified'),
            'stack': (extraction or {}).get('stack', ''),
            'visa': (extraction or {}).get('visa', 'Uncertain'),
            'applicants': (extraction or {}).get('applicants', 'Not specified'),
            'posted': (extraction or {}).get('posted', 'Not specified'),
            'industry': (extraction or {}).get('industry', ''),
            'domain': (extraction or {}).get('domain', ''),
            'notes': '', 'action': '', 'url': url,
            'raw_description': raw_text, 'structured_description': structured_json,
            'apply_reason': '', 'company_url': (extraction or {}).get('company_url'),
            'linkedin_url': (extraction or {}).get('linkedin_url'),
        }
        _insert_job(job_data)
        _insert_summary({
            'num': temp_num, 'company': job_data['company'],
            'match': 'Pending', 'score': 'P',
            'summary': (extraction or {}).get('summary', ''),
            'stack': (extraction or {}).get('stack', ''),
            'resumeFit': '', 'note': '', 'url': url,
        })
        _log(pid, 'save', f'Saved job #{temp_num} to DB')

        if _is_paused_or_stopped(pid):
            _log(pid, 'pause', 'Job paused/stopped after save')
            return

        # ── Step 7: Score — MiMo scoring ──
        current_step = 'score'
        _update_step(pid, 'step_analyze', 0, status='processing')
        next_num = temp_num
        if existing_num:
            _log(pid, 'analyze', f'Rescoring existing job #{next_num}...')
        else:
            _log(pid, 'analyze', f'Scoring job #{next_num}...')
        rules = _load_rules()

        # Load resume from DB for scoring context
        resume_file = os.path.join(TMP_DIR, f'resume_{pid}.txt')
        conn = _db()
        resume_row = conn.execute("SELECT raw_text FROM resumes WHERE id LIKE 'original_%' ORDER BY version DESC LIMIT 1").fetchone()
        conn.close()
        if resume_row and dict(resume_row).get('raw_text'):
            with open(resume_file, 'w') as f:
                f.write(dict(resume_row)['raw_text'])
            resume_path = resume_file
        else:
            resume_path = os.path.join(PROJECT_ROOT, 'inputs', 'original', 'resume.txt')

        # Load LinkedIn profile from DB if available
        linkedin_file = os.path.join(TMP_DIR, f'linkedin_{pid}.txt')
        conn = _db()
        linkedin_row = conn.execute("SELECT raw_text FROM resumes WHERE id LIKE 'linkedin_%' ORDER BY version DESC LIMIT 1").fetchone()
        conn.close()
        linkedin_step = "Read the candidate's LinkedIn profile from {linkedin_file} for additional context about their experience and skills"
        if linkedin_row and dict(linkedin_row).get('raw_text'):
            with open(linkedin_file, 'w') as f:
                f.write(dict(linkedin_row)['raw_text'])
            linkedin_path = linkedin_file
        else:
            linkedin_path = None
            linkedin_step = "No LinkedIn profile available — skip this step"

        prompt = load_prompt('step8_score',
            url=url, job_file=job_file, resume_file=resume_path,
            linkedin_file=linkedin_path or '', linkedin_step=linkedin_step,
            tmp_dir=TMP_DIR, pid=pid, next_num=next_num, rules=rules)

        returncode, output_lines = _stream_mimo_output(
            [MIMO_BIN, 'run', prompt, '--format', 'json', '--dangerously-skip-permissions'],
            cwd=PROJECT_ROOT,
            env={**os.environ, 'NO_COLOR': '1'},
            timeout=300,
            pid=pid,
        )

        if returncode != 0:
            error_msg = f"exit code {returncode}"
            for line in output_lines:
                try:
                    evt = json.loads(line)
                    if evt.get('type') == 'text':
                        error_msg = evt.get('part', {}).get('text', error_msg)[:300]
                except json.JSONDecodeError:
                    continue
            raise RuntimeError(f"mimo failed: {error_msg}")

        # Read score result
        result_path = os.path.join(TMP_DIR, f'pending_result_{pid}.json')
        if not os.path.exists(result_path):
            raise RuntimeError(f"Result file not found: {result_path}")

        with open(result_path) as f:
            data = json.loads(f.read(), strict=False)

        analyzed_data = data['job']
        _mark(pid, 'step_analyze', company=analyzed_data.get('company'), job_num=job_data['num'])

        # Parse numeric scores from mimo output
        fit_score_raw = analyzed_data.get('fit_score')
        success_score_raw = analyzed_data.get('success_score')
        fit_score = max(0, min(100, int(fit_score_raw))) if fit_score_raw is not None else None
        success_score = max(0, min(100, int(success_score_raw))) if success_score_raw is not None else None

        # Compute overall_score: (fit * 0.6) + (success * 0.4)
        overall_score = None
        if fit_score is not None and success_score is not None:
            overall_score = int(round(fit_score * 0.6 + success_score * 0.4))

        # Log score results
        score = normalize_score(analyzed_data.get('score', 'P'))
        match = analyzed_data.get('match', 'Medium')
        _log(pid, 'analyze', f'Score: {score} (fit={fit_score}) — Success: {normalize_score(analyzed_data.get("success", "P"))} (prob={success_score}) — Overall: {overall_score} — Match: {match}')

        # Update job data with scored results
        job_data.update({
            'company': analyzed_data.get('company', job_data['company']),
            'role': analyzed_data.get('role', job_data['role']),
            'location': analyzed_data.get('location', 'Not specified'),
            'locations': analyzed_data.get('locations', []),
            'match': match,
            'score': score,
            'success': normalize_score(analyzed_data.get('success', 'P')),
            'fit_score': fit_score,
            'success_score': success_score,
            'overall_score': overall_score,
            'salary': analyzed_data.get('salary', 'Not specified'),
            'stack': analyzed_data.get('stack', ''),
            'visa': analyzed_data.get('visa', 'Uncertain'),
            'applicants': analyzed_data.get('applicants', 'Not specified'),
            'posted': analyzed_data.get('posted', 'Not specified'),
            'posted_at': analyzed_data.get('posted_at'),
            'adv_at': analyzed_data.get('adv_at', job_data.get('adv_at')),
            'apply_reason': analyzed_data.get('apply_reason', job_data.get('apply_reason', '')),
            'industry': analyzed_data.get('industry', ''),
            'domain': analyzed_data.get('domain', ''),
            'notes': analyzed_data.get('notes', ''),
            'action': analyzed_data.get('action', ''),
            'employment_type': analyzed_data.get('employment_type', 'Full-time'),
            'work_types': analyzed_data.get('work_types', []),
            'workflow_log': analyzed_data.get('workflow_log', '[]'),
            'company_url': analyzed_data.get('company_url', job_data.get('company_url')),
            'linkedin_url': analyzed_data.get('linkedin_url', job_data.get('linkedin_url')),
        })

        # Save final results
        _insert_job(job_data)
        _insert_summary({
            'num': analyzed_data.get('num', temp_num), 'company': job_data['company'],
            'match': match, 'score': score,
            'summary': data.get('summary', {}).get('summary', ''),
            'stack': job_data['stack'],
            'resumeFit': data.get('summary', {}).get('resumeFit', ''),
            'note': data.get('summary', {}).get('note', ''),
            'url': url,
        })
        resume_data = {
            'id': f"pending_{pid}",
            'title': f"{job_data['company']} (Score {score})",
            'company': job_data['company'], 'role': job_data['role'],
            'job_num': job_data.get('num'),
            'content': data.get('resume_html', ''),
        }
        _insert_resume(resume_data)
        _log(pid, 'analyze', f'Final score: {score} saved')
        _mark(pid, 'step_analyze')

        if source == 'rescore':
            _log(pid, 'save', 'Rescoring completed')
        elif source == 'requeue':
            old_num = _get_existing_num(url)
            if old_num and old_num != job_data['num']:
                conn = _db()
                conn.execute('DELETE FROM jobs WHERE num=?', (old_num,))
                conn.execute('DELETE FROM summaries WHERE num=?', (old_num,))
                conn.execute("DELETE FROM resumes WHERE id=? OR id=?", (f'pending_{old_num}', f'rescore_{old_num}'))
                conn.commit(); conn.close()
                _log(pid, 'save', f'Deleted old #{old_num}, new #{job_data["num"]} created')

        # ── Done ──
        current_step = 'done'
        _update_step(pid, 'step_done', 0, status='done')
        _mark(pid, 'step_done')
        conn = _db()
        row = conn.execute('SELECT workflow_log FROM pending_jobs WHERE id=?', (pid,)).fetchone()
        conn.close()
        if row:
            _save_job_workflow_log(job_data['num'], dict(row)['workflow_log'] or '[]')
        try: os.remove(result_path)
        except OSError: pass
        print(f"[worker] Job {pid} done: {job_data.get('company')} #{job_data['num']}")

    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or '').strip()
        stdout = (e.stdout or '').strip()
        err_lines = stderr.split('\n') if stderr else []
        meaningful = '\n'.join(err_lines[-5:]) if err_lines else ''
        if not meaningful and stdout:
            out_lines = stdout.split('\n')
            meaningful = '\n'.join(out_lines[-5:])
        if not meaningful:
            meaningful = f"Process exited with code {e.returncode}"
        msg = f"AI service error: {meaningful}"
        print(f"[worker] Job {pid} FAILED: {msg}")
        _fail(pid, msg[:500], step=current_step)
    except Exception as e:
        msg = str(e)
        if 'Command' in msg and 'run' in msg:
            parts = msg.split('): ', 1)
            if len(parts) > 1:
                msg = parts[1]
        if not msg.startswith('['):
            msg = f"{msg}"
        if len(msg) > 500:
            break_at = msg.rfind('\n', 0, 450)
            if break_at < 100:
                break_at = 400
            msg = msg[:break_at] + '...'
        print(f"[worker] Job {pid} FAILED: {msg}")
        _fail(pid, msg, step=current_step)
    finally:
        for f in [job_file,
                  os.path.join(TMP_DIR, f'resume_{pid}.txt'),
                  os.path.join(TMP_DIR, f'linkedin_{pid}.txt')]:
            try: os.remove(f)
            except OSError: pass
        # Signal queue manager to pick up next job
        try:
            from core.queue import get_queue_manager
            get_queue_manager().signal_job_done(pid)
        except Exception:
            pass
