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

# --- DB helpers ---

def _db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
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

    conn.execute('''INSERT OR REPLACE INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (d['num'], d['company'], d['role'], d['location'], d['match'],
         d['score'], d['salary'], d['stack'], d['visa'], d['applicants'],
         d['posted'], d['industry'], d['domain'], d['notes'], d['action'], d['url'],
         normalized_wt[0] if normalized_wt else 'On-site', d.get('workflow_log', '[]'),
         d.get('created_at', now), posted_at, json.dumps(locations), 0,
         employment_type, json.dumps(normalized_wt)))
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

def _update_metadata(key, value):
    """Update metadata key-value pair."""
    conn = _db()
    conn.execute('''INSERT OR REPLACE INTO metadata (key, value, updated_at) VALUES (?, ?, ?)''',
        (key, value, datetime.now().isoformat()))
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

def _update_dashboard_insights(pid):
    """Update dashboard insights based on all processed jobs."""
    import subprocess
    prompt = load_prompt('dashboard_update',
        project_root=PROJECT_ROOT, pid=pid)
    result_file = os.path.join(PROJECT_ROOT, 'data', f'dashboard_insights_{pid}.json')

    proc = subprocess.run(
        [MIMO_BIN, 'run', prompt, '--format', 'json', '--dangerously-skip-permissions'],
        cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=120,
        env={**os.environ, 'NO_COLOR': '1'}
    )

    if proc.returncode == 0 and os.path.exists(result_file):
        with open(result_file) as f:
            insights = json.load(f)
        # Save to DB
        conn = _db()
        conn.execute('DELETE FROM dashboard_insights')
        for item_type, items in insights.items():
            if isinstance(items, list):
                for i, item in enumerate(items):
                    conn.execute('''INSERT INTO dashboard_insights (type, icon, title, description, priority)
                        VALUES (?, ?, ?, ?, ?)''',
                        (item_type, item.get('icon', ''), item.get('title', item.get('name', '')),
                         item.get('description', item.get('detail', item.get('note', ''))), i))
        conn.commit(); conn.close()
        _update_metadata('dashboard_updated_at', datetime.now().isoformat())
        try: os.remove(result_file)
        except OSError: pass
        print(f"[worker] Dashboard insights updated")

def _update_skills_insights(pid):
    """Update skills insights based on all processed jobs."""
    import subprocess
    prompt = load_prompt('skills_update',
        project_root=PROJECT_ROOT, pid=pid)
    result_file = os.path.join(PROJECT_ROOT, 'data', f'skills_insights_{pid}.json')

    proc = subprocess.run(
        [MIMO_BIN, 'run', prompt, '--format', 'json', '--dangerously-skip-permissions'],
        cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=120,
        env={**os.environ, 'NO_COLOR': '1'}
    )

    if proc.returncode == 0 and os.path.exists(result_file):
        with open(result_file) as f:
            insights = json.load(f)
        conn = _db()
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
        _update_metadata('skills_updated_at', datetime.now().isoformat())
        try: os.remove(result_file)
        except OSError: pass
        print(f"[worker] Skills insights updated")

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
    Full pipeline in a background thread:
    1. Fetch URL -> save to temp file
    2. Tell mimo to process it (it has memory of this repo)
    3. Parse mimo's JSON output, save to DB
    """
    conn = _db()
    row = conn.execute('SELECT * FROM pending_jobs WHERE id=?', (pid,)).fetchone()
    conn.close()
    if not row:
        return
    item = dict(row)
    url = item['url']
    source = item.get('source', 'cli')

    # Temp file for fetched content
    job_file = os.path.join(tempfile.gettempdir(), f'job_{pid}.txt')

    try:
        current_step = 'fetch'
        _log(pid, 'start', f'Processing {url[:60]}...')
        # Step 1: Fetch the URL
        _log(pid, 'fetch', 'Fetching LinkedIn page...')
        _update_step(pid, 'step_fetch', 0, status='processing')
        raw_text = _fetch_url(url)
        with open(job_file, 'w') as f:
            f.write(raw_text)
        _log(pid, 'fetch', f'Fetched {len(raw_text)} chars')
        _mark(pid, 'step_fetch')

        # Extract job title and company from fetched content so the
        # frontend can display them immediately — before mimo finishes.
        title = ''
        company = ''
        for tline in raw_text.split('\n'):
            tline = tline.strip()
            if tline and 5 < len(tline) < 120:
                if any(kw in tline.lower() for kw in ['engineer', 'developer', 'software', 'senior', 'backend', 'frontend', 'python', 'devops', 'sre', 'platform']):
                    title = tline
                    break
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
            _log(pid, 'fetch', f'Extracted: {company or title}')

        # Step 2+3: Tell mimo to process — it knows this repo's format
        current_step = 'analyze'
        _log(pid, 'analyze', 'Starting MiMo analysis...')
        _update_step(pid, 'step_analyze', 0, status='processing')

        next_num = _get_next_num()
        # If rescoring, use existing job num to avoid duplicates
        existing_num = _get_existing_num(url)
        if existing_num:
            next_num = existing_num
            _log(pid, 'analyze', f'Rescoring existing job #{next_num}...')
        else:
            _log(pid, 'analyze', f'New job #{next_num}...')
        preferences = _load_preferences()
        prompt = load_prompt('job_processing',
            url=url, job_file=job_file, project_root=PROJECT_ROOT,
            pid=pid, next_num=next_num, preferences=preferences)

        # Run mimo in project root — stream output line by line
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

        # Step 3: Read result and save to DB
        current_step = 'resume'
        _update_step(pid, 'step_resume', 0, status='processing')
        result_path = os.path.join(PROJECT_ROOT, 'data', f'pending_result_{pid}.json')
        if not os.path.exists(result_path):
            raise RuntimeError(f"Result file not found: {result_path}")

        with open(result_path) as f:
            data = json.load(f)

        job_data = data['job']
        _mark(pid, 'step_analyze', company=job_data.get('company'), job_num=job_data['num'])

        resume_data = {
            'id': f"pending_{pid}",
            'title': f"{job_data.get('company', 'Unknown')} (Score {job_data.get('score', 0)})",
            'badge': 'Tailored',
            'badgeClass': 'badge-tailored',
            'company': job_data.get('company', 'Unknown'),
            'role': job_data.get('role', 'Unknown'),
            'content': data.get('resume_html', ''),
        }
        _mark(pid, 'step_resume')

        # Step 4: Save to DB
        current_step = 'save'
        _update_step(pid, 'step_db', 0, status='processing')
        _insert_job(job_data)
        _insert_summary({
            'num': job_data['num'],
            'company': job_data.get('company'),
            'match': job_data.get('match'),
            'score': job_data.get('score'),
            'summary': data.get('summary', {}).get('summary', ''),
            'stack': job_data.get('stack'),
            'resumeFit': data.get('summary', {}).get('resumeFit', ''),
            'note': data.get('summary', {}).get('note', ''),
            'url': url,
        })
        _insert_resume(resume_data)
        _mark(pid, 'step_db')

        # If rescore or requeue, mark old job as deleted
        if source in ('rescore', 'requeue'):
            _mark_old_job_deleted(url, exclude_num=job_data['num'])
            _log(pid, 'save', f'Marked old job as deleted (source: {source})')

        # Step 5: Done
        current_step = 'done'
        _update_step(pid, 'step_done', 0, status='done')
        _mark(pid, 'step_done')
        # Save workflow_log to jobs table
        conn = _db()
        row = conn.execute('SELECT workflow_log FROM pending_jobs WHERE id=?', (pid,)).fetchone()
        conn.close()
        if row:
            _save_job_workflow_log(job_data['num'], dict(row)['workflow_log'] or '[]')
        # Cleanup result file
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
        source = {'fetch':'fetch','analyze':'mimo','resume':'mimo','save':'db','done':'worker'}.get(current_step, 'worker')
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
        # Cleanup temp files
        try: os.remove(job_file)
        except OSError: pass
