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

DB_PATH = os.path.join(os.path.dirname(__file__), 'jobs.db')
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
MIMO_BIN = os.path.expanduser('~/.mimocode/bin/mimo')
TMP_DIR = tempfile.gettempdir()

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

JOBS_DIR = os.path.abspath(os.environ.get('JOBS_DIR', os.path.join(PROJECT_ROOT, 'jobs')))

# --- DB helpers ---

def _db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    return conn

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

    conn.execute('''INSERT OR REPLACE INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (d['num'], d['company'], d['role'], d['location'], d['match'],
         d['score'], d['salary'], d['stack'], d['visa'], d['applicants'],
         d['posted'], d['industry'], d['domain'], d['notes'], d['action'], d['url'],
         normalized_wt[0] if normalized_wt else 'On-site', d.get('workflow_log', '[]'),
         d.get('created_at', now), posted_at, json.dumps(locations), 0,
         employment_type, json.dumps(normalized_wt), d.get('raw_description'),
         d.get('structured_description'), d.get('raw_file_path'),
         d.get('structured_file_path'), d.get('rescoring', 0)))
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
    conn.execute('''INSERT OR REPLACE INTO resumes VALUES (?,?,?,?,?,?,?)''',
        (d['id'], d['title'], d['badge'], d['badgeClass'],
         d['company'], d['role'], d['content']))
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

    job_file = os.path.join(tempfile.gettempdir(), f'rescore_{num}.txt')
    try:
        with open(job_file, 'w') as f:
            f.write(raw_desc)

        preferences = _load_preferences()
        # Use a unique pid per rescore run to avoid file conflicts
        rescore_pid = f'rescore_{num}_{int(datetime.now().timestamp()*1000)}'
        prompt = load_prompt('step7_score',
            url=url, job_file=job_file, project_root=PROJECT_ROOT,
            pid=rescore_pid, next_num=num, preferences=preferences)

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

        # Update the existing job with new scores
        job_data = {
            'num': num,
            'company': analyzed_data.get('company', j['company']),
            'role': analyzed_data.get('role', j['role']),
            'location': analyzed_data.get('location', j.get('location', 'Not specified')),
            'locations': analyzed_data.get('locations', []),
            'match': analyzed_data.get('match', j.get('match', 'Medium')),
            'score': analyzed_data.get('score', j.get('score', 0)),
            'salary': analyzed_data.get('salary', j.get('salary', 'Not specified')),
            'stack': analyzed_data.get('stack', j.get('stack', '')),
            'visa': analyzed_data.get('visa', j.get('visa', 'Uncertain')),
            'applicants': analyzed_data.get('applicants', j.get('applicants', 'Not specified')),
            'posted': analyzed_data.get('posted', j.get('posted', 'Not specified')),
            'posted_at': analyzed_data.get('posted_at', j.get('posted_at')),
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
            'badge': 'Tailored', 'badgeClass': 'badge-tailored',
            'company': job_data['company'], 'role': job_data['role'],
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
    error_msg = f"[{step}] {msg}" if step else msg
    _update_step(pid, 'step_done', 0, status='failed', error=error_msg)

def _log(pid, step, msg):
    """Append a workflow log entry."""
    conn = _db()
    row = conn.execute('SELECT workflow_log FROM pending_jobs WHERE id=?', (pid,)).fetchone()
    logs = json.loads(row['workflow_log'] or '[]') if row else []
    logs.append({'step': step, 'msg': msg, 'ts': datetime.now().strftime('%H:%M:%S')})
    conn.execute('UPDATE pending_jobs SET workflow_log=? WHERE id=?', (json.dumps(logs), pid))
    conn.commit(); conn.close()

def _load_preferences():
    """Load all enabled preferences from DB and format for prompt."""
    conn = _db()
    rows = conn.execute('SELECT category, key, value, description FROM preferences WHERE enabled=1 ORDER BY category, priority').fetchall()
    conn.close()
    if not rows:
        return "No preferences set."
    lines = []
    current_cat = None
    for row in rows:
        r = dict(row)
        if r['category'] != current_cat:
            current_cat = r['category']
            lines.append(f"\n{current_cat.upper()}:")
        lines.append(f"- {r['key']}: {r['value']}")
        if r['description']:
            lines.append(f"  ({r['description']})")
    return '\n'.join(lines)

def _extract_structured_description(raw_text, num):
    """Extract structured job info from raw description using mimo."""
    output_file = os.path.join(TMP_DIR, f'structured_{num}.json')
    prompt = load_prompt('step4_extract',
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

def _update_dashboard_insights(pid):
    """Update dashboard insights based on all processed jobs."""
    import subprocess
    prompt = load_prompt('dashboard_update',
        project_root=PROJECT_ROOT, tmp_dir=TMP_DIR, pid=pid)
    result_file = os.path.join(TMP_DIR, f'dashboard_insights_{pid}.json')

    proc = subprocess.run(
        [MIMO_BIN, 'run', prompt, '--format', 'json', '--dangerously-skip-permissions'],
        cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=120,
        env={**os.environ, 'NO_COLOR': '1'}
    )

    if proc.returncode == 0 and os.path.exists(result_file):
        with open(result_file) as f:
            insights = json.load(f)

        # Save to analysis_runs table
        conn = _db()
        now = datetime.now().isoformat()
        conn.execute('INSERT INTO analysis_runs (page, created_at, analysis_json) VALUES (?, ?, ?)',
            ('dashboard', now, json.dumps(insights, ensure_ascii=False)))

        # Also update the legacy dashboard_insights table for backward compatibility
        conn.execute('DELETE FROM dashboard_insights')
        for item_type, items in insights.items():
            if isinstance(items, list):
                for i, item in enumerate(items):
                    conn.execute('''INSERT INTO dashboard_insights (type, icon, title, description, priority)
                        VALUES (?, ?, ?, ?, ?)''',
                        (item_type, item.get('icon', ''), item.get('title', item.get('name', '')),
                         item.get('description', item.get('detail', item.get('note', ''))), i))

        conn.commit(); conn.close()
        try: os.remove(result_file)
        except OSError: pass
        print(f"[worker] Dashboard insights updated")

def _update_skills_insights(pid):
    """Update skills insights based on all processed jobs."""
    import subprocess
    prompt = load_prompt('skills_update',
        project_root=PROJECT_ROOT, tmp_dir=TMP_DIR, pid=pid)
    result_file = os.path.join(TMP_DIR, f'skills_insights_{pid}.json')

    proc = subprocess.run(
        [MIMO_BIN, 'run', prompt, '--format', 'json', '--dangerously-skip-permissions'],
        cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=120,
        env={**os.environ, 'NO_COLOR': '1'}
    )

    if proc.returncode == 0 and os.path.exists(result_file):
        with open(result_file) as f:
            insights = json.load(f)

        # Save to analysis_runs table
        conn = _db()
        now = datetime.now().isoformat()
        conn.execute('INSERT INTO analysis_runs (page, created_at, analysis_json) VALUES (?, ?, ?)',
            ('skills', now, json.dumps(insights, ensure_ascii=False)))

        # Also update the legacy tables for backward compatibility
        # Update tech_learning
        if 'techLearning' in insights:
            conn.execute('DELETE FROM tech_learning')
            for t in insights['techLearning']:
                conn.execute('''INSERT INTO tech_learning (name,priority,pl,pc,sc,dc,usage,uc,jobs,jd,reason,action)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (t['name'], t.get('priority', 1), t.get('pl', ''), t.get('pc', 'p3'),
                     t.get('sc', ''), t.get('dc', ''), t.get('usage', 0), t.get('uc', ''),
                     t.get('jobs', ''), t.get('jd', ''), t.get('reason', ''), t.get('action', '')))
        # Update tech_stack
        if 'techStack' in insights:
            conn.execute('DELETE FROM tech_stack')
            for t in insights['techStack']:
                conn.execute('''INSERT INTO tech_stack (name,level,ml,mc,roles,path) VALUES (?,?,?,?,?,?)''',
                    (t['name'], t.get('level', 3), t.get('ml', ''), t.get('mc', 'p3'),
                     t.get('roles', ''), t.get('path', '')))

        conn.commit(); conn.close()
        try: os.remove(result_file)
        except OSError: pass
        print(f"[worker] Skills insights updated")

def _update_unified_analysis(pid):
    """Update unified analysis combining dashboard and skills insights."""
    import subprocess
    prompt = load_prompt('analysis_update',
        project_root=PROJECT_ROOT, tmp_dir=TMP_DIR, pid=pid)
    result_file = os.path.join(TMP_DIR, f'analysis_{pid}.json')

    proc = subprocess.run(
        [MIMO_BIN, 'run', prompt, '--format', 'json', '--dangerously-skip-permissions'],
        cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=180,
        env={**os.environ, 'NO_COLOR': '1'}
    )

    if proc.returncode == 0 and os.path.exists(result_file):
        with open(result_file) as f:
            insights = json.load(f)

        # Save to analysis_runs table
        conn = _db()
        now = datetime.now().isoformat()
        conn.execute('INSERT INTO analysis_runs (page, created_at, analysis_json) VALUES (?, ?, ?)',
            ('analysis', now, json.dumps(insights, ensure_ascii=False)))

        # Also update legacy tables for backward compatibility
        # Dashboard insights
        conn.execute('DELETE FROM dashboard_insights')
        for item_type in ['strategy', 'strengths', 'weaknesses', 'visa_companies', 'apply_urgency']:
            items = insights.get(item_type, [])
            if isinstance(items, list):
                for i, item in enumerate(items):
                    conn.execute('''INSERT INTO dashboard_insights (type, icon, title, description, priority)
                        VALUES (?, ?, ?, ?, ?)''',
                        (item_type, item.get('icon', ''), item.get('title', item.get('name', '')),
                         item.get('description', item.get('detail', item.get('note', ''))), i))

        # Tech learning
        if 'techLearning' in insights:
            conn.execute('DELETE FROM tech_learning')
            for t in insights['techLearning']:
                conn.execute('''INSERT INTO tech_learning (name,priority,pl,pc,sc,dc,usage,uc,jobs,jd,reason,action)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (t['name'], t.get('priority', 1), t.get('pl', ''), t.get('pc', 'p3'),
                     t.get('sc', ''), t.get('dc', ''), t.get('usage', 0), t.get('uc', ''),
                     t.get('jobs', ''), t.get('jd', ''), t.get('reason', ''), t.get('action', '')))

        # Tech stack
        if 'techStack' in insights:
            conn.execute('DELETE FROM tech_stack')
            for t in insights['techStack']:
                conn.execute('''INSERT INTO tech_stack (name,level,ml,mc,roles,path) VALUES (?,?,?,?,?,?)''',
                    (t['name'], t.get('level', 3), t.get('ml', ''), t.get('mc', 'p3'),
                     t.get('roles', ''), t.get('path', '')))

        conn.commit(); conn.close()
        try: os.remove(result_file)
        except OSError: pass
        print(f"[worker] Unified analysis updated")

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
        raise RuntimeError(f"HTTP {e.code}: {e.reason} — LinkedIn blocked the request or URL is invalid") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error: {e.reason} — check internet connection") from None
    except Exception as e:
        raise RuntimeError(f"Fetch failed: {e}") from None
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
        raise RuntimeError("Fetched page too short — LinkedIn may require login or the URL is invalid")
    return text[:5000]

def _validate_job_content(raw_text, pid):
    """Validate and extract main job section from fetched content using mimo."""
    prompt = load_prompt('step2_validate', content=raw_text[:3000])

    result_file = os.path.join(TMP_DIR, f'validate_{pid}.json')
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

    job_file = os.path.join(tempfile.gettempdir(), f'job_{pid}.txt')
    os.makedirs(JOBS_DIR, exist_ok=True)

    try:
        current_step = 'fetch'
        _log(pid, 'start', f'Processing {url[:60]}...')

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

        # ── Step 2: Validate — extract main job section ──
        current_step = 'validate'
        _update_step(pid, 'step_validate', 0, status='processing')
        _log(pid, 'validate', 'Finding main job section...')
        validation = _validate_job_content(raw_text, pid)
        is_valid = validation.get('valid', False)
        reason = validation.get('reason', 'Unknown')
        v_title = validation.get('title')
        v_company = validation.get('company')
        v_content = validation.get('content', raw_text)

        if is_valid:
            _log(pid, 'validate', f'Valid: {reason}')
            # Use extracted content if available
            if v_content and len(v_content) > 100:
                raw_text = v_content
                with open(job_file, 'w') as f:
                    f.write(raw_text)
                _log(pid, 'validate', f'Extracted main section ({len(raw_text)} chars)')
        else:
            _log(pid, 'validate', f'WARNING: {reason} — continuing anyway')

        title = v_title or ''
        company = v_company or ''
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
        _mark(pid, 'step_validate')

        if _is_paused_or_stopped(pid):
            _log(pid, 'pause', 'Job paused/stopped after validate')
            return

        # ── Step 3: Extract raw → save to DB ──
        current_step = 'extract_raw'
        _update_step(pid, 'step_extract_raw', 0, status='processing')
        _log(pid, 'extract_raw', 'Saving raw description...')
        temp_num = _get_next_num()
        existing_num = _get_existing_num(url)
        if existing_num:
            temp_num = existing_num
        job_data = {
            'num': temp_num, 'company': company or title or 'Unknown',
            'role': title or 'Unknown', 'location': 'Not specified',
            'match': 'Pending', 'score': 0, 'salary': 'Not specified',
            'stack': '', 'visa': 'Uncertain', 'applicants': 'Not specified',
            'posted': 'Not specified', 'industry': '', 'domain': '',
            'notes': '', 'action': '', 'url': url,
            'raw_description': raw_text, 'structured_description': None,
        }
        _insert_job(job_data)
        _log(pid, 'extract_raw', f'Saved (job #{temp_num})')
        _mark(pid, 'step_extract_raw')

        if _is_paused_or_stopped(pid):
            _log(pid, 'pause', 'Job paused/stopped after extract raw')
            return

        # ── Step 4: Extract structured → save to DB ──
        current_step = 'extract_struct'
        _update_step(pid, 'step_extract_struct', 0, status='processing')
        _log(pid, 'extract_struct', 'Extracting structured info...')
        structured_json = _extract_structured_description(raw_text, pid)
        if structured_json:
            job_data['structured_description'] = structured_json
            _insert_job(job_data)
            _log(pid, 'extract_struct', 'Structured extraction saved')
        else:
            _log(pid, 'extract_struct', 'Extraction failed, skipping')
        _mark(pid, 'step_extract_struct')

        if _is_paused_or_stopped(pid):
            _log(pid, 'pause', 'Job paused/stopped after extract struct')
            return

        # ── Step 5: Summary — extract summary from structured data ──
        current_step = 'summary'
        _update_step(pid, 'step_summary', 0, status='processing')
        _log(pid, 'summary', 'Generating summary...')
        # Summary is extracted from the analysis step (which runs first now via mimo)
        # For now, extract basic summary from structured data
        sd = None
        if structured_json:
            try:
                sd = json.loads(structured_json) if isinstance(structured_json, str) else structured_json
            except Exception:
                pass
        basic_summary = {
            'summary': f"{job_data['role']} at {job_data['company']}" if sd else '',
            'stack': sd.get('stack', '') if sd else '',
            'resumeFit': '',
            'note': '',
        }
        _log(pid, 'summary', f'Summary: {basic_summary["summary"][:150]}')
        _mark(pid, 'step_summary')

        if _is_paused_or_stopped(pid):
            _log(pid, 'pause', 'Job paused/stopped after summary')
            return

        # ── Step 6: Resume — save extracted data to DB ──
        current_step = 'resume'
        _update_step(pid, 'step_resume', 0, status='processing')
        _log(pid, 'resume', 'Saving to database...')
        _insert_job(job_data)
        _insert_summary({
            'num': temp_num, 'company': job_data['company'],
            'match': 'Pending', 'score': 0,
            'summary': basic_summary['summary'],
            'stack': basic_summary['stack'],
            'resumeFit': '', 'note': '',
            'url': url,
        })
        _log(pid, 'resume', f'Saved job #{temp_num} to DB')
        _mark(pid, 'step_resume')

        if _is_paused_or_stopped(pid):
            _log(pid, 'pause', 'Job paused/stopped after resume')
            return

        # ── Step 7: Score — MiMo scoring + resume generation ──
        current_step = 'score'
        _update_step(pid, 'step_analyze', 0, status='processing')
        next_num = temp_num
        if existing_num:
            _log(pid, 'score', f'Rescoring existing job #{next_num}...')
        else:
            _log(pid, 'score', f'Scoring job #{next_num}...')
        preferences = _load_preferences()
        prompt = load_prompt('step7_score',
            url=url, job_file=job_file, project_root=PROJECT_ROOT, tmp_dir=TMP_DIR,
            pid=pid, next_num=next_num, preferences=preferences)

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
            data = json.load(f)

        analyzed_data = data['job']
        _mark(pid, 'step_analyze', company=analyzed_data.get('company'), job_num=job_data['num'])

        # Log score results
        score = analyzed_data.get('score', 0)
        match = analyzed_data.get('match', 'Medium')
        _log(pid, 'score', f'Score: {score}/100 — Match: {match}')

        # Update job data with scored results
        job_data.update({
            'company': analyzed_data.get('company', job_data['company']),
            'role': analyzed_data.get('role', job_data['role']),
            'location': analyzed_data.get('location', 'Not specified'),
            'locations': analyzed_data.get('locations', []),
            'match': match,
            'score': score,
            'salary': analyzed_data.get('salary', 'Not specified'),
            'stack': analyzed_data.get('stack', ''),
            'visa': analyzed_data.get('visa', 'Uncertain'),
            'applicants': analyzed_data.get('applicants', 'Not specified'),
            'posted': analyzed_data.get('posted', 'Not specified'),
            'posted_at': analyzed_data.get('posted_at'),
            'industry': analyzed_data.get('industry', ''),
            'domain': analyzed_data.get('domain', ''),
            'notes': analyzed_data.get('notes', ''),
            'action': analyzed_data.get('action', ''),
            'employment_type': analyzed_data.get('employment_type', 'Full-time'),
            'work_types': analyzed_data.get('work_types', []),
            'workflow_log': analyzed_data.get('workflow_log', '[]'),
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
            'badge': 'Tailored', 'badgeClass': 'badge-tailored',
            'company': job_data['company'], 'role': job_data['role'],
            'content': data.get('resume_html', ''),
        }
        _insert_resume(resume_data)
        _log(pid, 'score', f'Final score: {score}/100 saved')
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
        msg = f"[mimo] {meaningful}"
        print(f"[worker] Job {pid} FAILED: {msg}")
        _fail(pid, msg[:500], step=current_step)
    except Exception as e:
        msg = str(e)
        if 'Command' in msg and 'run' in msg:
            parts = msg.split('): ', 1)
            if len(parts) > 1:
                msg = parts[1]
        source = {'fetch':'fetch','validate':'validate','extract':'extract','score':'mimo','resume':'db','done':'worker'}.get(current_step, 'worker')
        if not msg.startswith('['):
            msg = f"[{source}] {msg}"
        if len(msg) > 400:
            break_at = msg.rfind('\n', 0, 350)
            if break_at < 100:
                break_at = 300
            msg = msg[:break_at] + '...'
        print(f"[worker] Job {pid} FAILED: {msg}")
        _fail(pid, msg, step=current_step)
    finally:
        try: os.remove(job_file)
        except OSError: pass
