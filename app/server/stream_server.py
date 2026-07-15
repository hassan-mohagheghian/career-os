"""
WebSocket server for streaming Mimo CLI output in real-time.
Runs alongside Flask on a separate port.
"""
import asyncio
import json
import subprocess
import os
import signal
from datetime import datetime

import websockets
from prompts import load_prompt

# Connected clients per job
clients = {}  # pid -> set of websocket connections
processes = {}  # pid -> Popen object

MIMO_BIN = os.path.expanduser('~/.mimocode/bin/mimo')
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DB_PATH = os.path.join(os.path.dirname(__file__), 'jobs.db')

# --- DB helpers (async-safe: each call opens its own connection) ---

def _db():
    import sqlite3
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def _log(pid, step, msg):
    import sqlite3
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

def _update_step(pid, step, val, status=None, company=None, job_num=None, error=None):
    import sqlite3
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

def _mark(pid, step, company=None, job_num=None):
    _update_step(pid, step, 1, company=company, job_num=job_num)

def _fail(pid, msg, step=None):
    error_msg = f"[{step}] {msg}" if step else msg
    _update_step(pid, 'step_done', 0, status='failed', error=error_msg)

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
    import sqlite3
    # Normalize location and work_type
    d = _normalize_job_data(d)
    conn = _db()
    locations = d.get('locations', [])
    if isinstance(locations, str):
        locations = [locations] if locations else []
    conn.execute('''INSERT OR REPLACE INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (d['num'], d['company'], d['role'], d['location'], d['match'],
         d['score'], d['salary'], d['stack'], d['visa'], d['applicants'],
         d['posted'], d['industry'], d['domain'], d['notes'], d['action'], d['url'],
         d.get('work_type', 'On-site'), d.get('workflow_log', '[]'),
         d.get('created_at', datetime.now().isoformat()), d.get('posted_at'), json.dumps(locations), 0))

def _save_job_workflow_log(num, log_json):
    conn = _db()
    conn.execute('UPDATE jobs SET workflow_log=? WHERE num=?', (log_json, num))
    conn.commit(); conn.close()
    conn.commit(); conn.close()

def _insert_summary(d):
    import sqlite3
    conn = _db()
    conn.execute('''INSERT OR REPLACE INTO summaries VALUES (?,?,?,?,?,?,?,?,?)''',
        (d['num'], d['company'], d['match'], d['score'],
         d['summary'], d['stack'], d['resumeFit'], d['note'], d['url']))
    conn.commit(); conn.close()

def _insert_resume(d):
    import sqlite3
    conn = _db()
    conn.execute('''INSERT OR REPLACE INTO resumes VALUES (?,?,?,?,?,?,?)''',
        (d['id'], d['title'], d['badge'], d['badgeClass'],
         d['company'], d['role'], d['content']))
    conn.commit(); conn.close()

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
        text = re.sub(r'\(.*?\)', '', text)
        parts = re.split(r'[,/\|]', text)
        for part in parts:
            part = part.strip().lower()
            if part in CITIES and CITIES[part] not in cities:
                cities.append(CITIES[part])
        return cities

    location = d.get('location', '')
    if location:
        cities = extract_cities(location)
        if cities:
            d['location'] = cities[0]

    locations = d.get('locations', [])
    if isinstance(locations, str):
        try:
            locations = json.loads(locations)
        except:
            locations = []

    if location:
        for city in extract_cities(location):
            if city not in locations:
                locations.append(city)

    normalized = []
    for loc in locations:
        if isinstance(loc, str):
            cities = extract_cities(loc)
            for c in cities:
                if c not in normalized:
                    normalized.append(c)
            if not cities and loc.strip():
                if loc.strip() not in normalized:
                    normalized.append(loc.strip())

    d['locations'] = normalized if normalized else [d.get('location', 'Not specified')]

    work_type = d.get('work_type', 'On-site')
    wt_lower = (work_type or '').lower()
    if 'remote' in wt_lower or 'work from anywhere' in wt_lower:
        d['work_type'] = 'Remote'
    elif 'hybrid' in wt_lower or 'flexible' in wt_lower:
        d['work_type'] = 'Hybrid'
    else:
        d['work_type'] = 'On-site'

    return d

async def _update_dashboard_insights(pid):
    """Update dashboard insights based on all processed jobs."""
    prompt = load_prompt('dashboard_update',
        project_root=PROJECT_ROOT, pid=pid)
    result_file = os.path.join(PROJECT_ROOT, 'data', f'dashboard_insights_{pid}.json')

    proc = await asyncio.create_subprocess_exec(
        MIMO_BIN, 'run', prompt, '--format', 'json', '--dangerously-skip-permissions',
        cwd=PROJECT_ROOT, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        env={**os.environ, 'NO_COLOR': '1'}
    )
    await proc.wait()

    if proc.returncode == 0 and os.path.exists(result_file):
        with open(result_file) as f:
            insights = json.load(f)
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
        try: os.remove(result_file)
        except OSError: pass
        print(f"[stream] Dashboard insights updated")

# --- Broadcast to all connected clients for a job ---

async def broadcast(pid, event):
    """Send event to all clients watching this job."""
    msg = json.dumps(event)
    if pid in clients:
        dead = set()
        for ws in clients[pid]:
            try:
                await ws.send(msg)
            except websockets.ConnectionClosed:
                dead.add(ws)
        clients[pid] -= dead

# --- Fetch URL ---

import urllib.request
import re

def fetch_url(url):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        raise RuntimeError(f"Fetch failed: {e}") from None
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    for marker in ['About The Role', 'Job Description', 'Description', 'What you.ll do', 'The Role']:
        idx = text.find(marker)
        if idx != -1:
            text = text[idx:]
            break
    if len(text) < 100:
        raise RuntimeError("Page too short — LinkedIn may require login")
    return text[:5000]

# --- Stream mimo process ---

async def stream_mimo(pid, prompt):
    """Run mimo with Popen and stream output line by line via WebSocket."""
    proc = await asyncio.create_subprocess_exec(
        MIMO_BIN, 'run', prompt, '--format', 'json', '--dangerously-skip-permissions',
        cwd=PROJECT_ROOT,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={**os.environ, 'NO_COLOR': '1'},
    )
    processes[pid] = proc

    await broadcast(pid, {'type': 'process_start', 'pid': pid, 'ts': datetime.now().strftime('%H:%M:%S')})

    # Read stdout line by line
    async def read_stream(stream, stream_name):
        while True:
            line = await stream.readline()
            if not line:
                break
            text = line.decode('utf-8', errors='replace').strip()
            if not text:
                continue
            # Parse JSON events
            try:
                evt = json.loads(text)
                # Forward structured event
                await broadcast(pid, {'type': 'mimo_event', 'event': evt, 'ts': datetime.now().strftime('%H:%M:%S')})
                # Log and forward tool outputs
                if evt.get('type') == 'text':
                    txt = evt.get('part', {}).get('text', '')
                    _log(pid, 'mimo', txt[:200])
                    await broadcast(pid, {'type': 'tool_output', 'stream': 'text', 'data': txt, 'ts': datetime.now().strftime('%H:%M:%S')})
                elif evt.get('type') == 'tool_use':
                    tool = evt.get('part', {}).get('tool', 'unknown')
                    state = evt.get('part', {}).get('state', {})
                    status = state.get('status', '')
                    inp = state.get('input', {})
                    output = state.get('output', '') or state.get('metadata', {}).get('output', '')
                    title = state.get('title', '')
                    _log(pid, 'mimo', f"Tool: {tool} [{status}] {title}")
                    # Forward tool input (command)
                    if inp.get('command'):
                        await broadcast(pid, {'type': 'tool_output', 'stream': 'input', 'tool': tool, 'data': f"$ {inp['command']}", 'ts': datetime.now().strftime('%H:%M:%S')})
                    # Forward tool output (result)
                    if output:
                        await broadcast(pid, {'type': 'tool_output', 'stream': 'output', 'tool': tool, 'data': output.rstrip(), 'ts': datetime.now().strftime('%H:%M:%S')})
                    # Forward tool error
                    if status == 'error':
                        err = state.get('error', '')
                        if err:
                            await broadcast(pid, {'type': 'tool_output', 'stream': 'error', 'tool': tool, 'data': err, 'ts': datetime.now().strftime('%H:%M:%S')})
                elif evt.get('type') == 'step_finish':
                    reason = evt.get('part', {}).get('reason', '')
                    tokens = evt.get('part', {}).get('tokens', {})
                    _log(pid, 'mimo', f"Step finished: {reason} ({tokens.get('total', 0)} tokens)")
            except json.JSONDecodeError:
                # Non-JSON output (mimo UI noise) — forward as-is
                await broadcast(pid, {'type': 'mimo_raw', 'line': text, 'stream': stream_name, 'ts': datetime.now().strftime('%H:%M:%S')})

    # Run both streams concurrently
    await asyncio.gather(
        read_stream(proc.stdout, 'stdout'),
        read_stream(proc.stderr, 'stderr'),
    )

    # Wait for process to finish
    returncode = await proc.wait()
    processes.pop(pid, None)

    await broadcast(pid, {'type': 'process_end', 'pid': pid, 'returncode': returncode, 'ts': datetime.now().strftime('%H:%M:%S')})
    return returncode

# --- Main pipeline ---

async def process_job_stream(pid):
    """Full pipeline with streaming output."""
    conn = _db()
    row = conn.execute('SELECT * FROM pending_jobs WHERE id=?', (pid,)).fetchone()
    conn.close()
    if not row:
        return
    item = dict(row)
    url = item['url']
    source = item.get('source', 'cli')

    job_file = os.path.join('/tmp', f'job_{pid}.txt')

    try:
        # === STEP 1: FETCH ===
        _log(pid, 'start', f'Processing {url[:60]}...')
        await broadcast(pid, {'type': 'tool_output', 'stream': 'input', 'tool': 'fetch', 'data': f"$ curl -sL '{url[:80]}...'", 'ts': datetime.now().strftime('%H:%M:%S')})
        _log(pid, 'fetch', 'Fetching LinkedIn page...')
        _update_step(pid, 'step_fetch', 0, status='processing')
        await broadcast(pid, {'type': 'step', 'step': 'fetch', 'status': 'processing', 'ts': datetime.now().strftime('%H:%M:%S')})
        await broadcast(pid, {'type': 'tool_output', 'stream': 'output', 'tool': 'fetch', 'data': '→ Connecting to linkedin.com...', 'ts': datetime.now().strftime('%H:%M:%S')})
        await broadcast(pid, {'type': 'tool_output', 'stream': 'output', 'tool': 'fetch', 'data': '→ Sending request with browser User-Agent...', 'ts': datetime.now().strftime('%H:%M:%S')})

        raw_text = await asyncio.get_event_loop().run_in_executor(None, fetch_url, url)
        await broadcast(pid, {'type': 'tool_output', 'stream': 'output', 'tool': 'fetch', 'data': f'→ Received response ({len(raw_text)} chars)', 'ts': datetime.now().strftime('%H:%M:%S')})

        with open(job_file, 'w') as f:
            f.write(raw_text)
        await broadcast(pid, {'type': 'tool_output', 'stream': 'output', 'tool': 'fetch', 'data': f'→ Saved raw content to {job_file}', 'ts': datetime.now().strftime('%H:%M:%S')})

        # Extract job title and company
        import re as _re
        title = ''
        company = ''
        for line in raw_text.split('\n'):
            line = line.strip()
            if line and 5 < len(line) < 120:
                if any(kw in line.lower() for kw in ['engineer', 'developer', 'software', 'senior', 'backend', 'frontend', 'python', 'devops', 'sre', 'platform']):
                    title = line
                    break
        for marker in ['hiring', ' at ', '—', '|']:
            idx = raw_text.find(marker)
            if 0 < idx < 200:
                company = raw_text[max(0,idx-50):idx].strip().split('\n')[-1].strip()
                company = company.replace('hiring', '').replace(' at ', '').strip()
                if company and 2 < len(company) < 60:
                    break
                company = ''
        if title or company:
            conn = _db()
            conn.execute('UPDATE pending_jobs SET company=? WHERE id=?', (company or title[:40], pid))
            conn.commit(); conn.close()
            await broadcast(pid, {'type': 'job_info', 'pid': pid, 'title': title, 'company': company, 'ts': datetime.now().strftime('%H:%M:%S')})
            await broadcast(pid, {'type': 'tool_output', 'stream': 'output', 'tool': 'fetch', 'data': f'→ Extracted: {company} — {title}', 'ts': datetime.now().strftime('%H:%M:%S')})
        _mark(pid, 'step_fetch')
        await broadcast(pid, {'type': 'step', 'step': 'fetch', 'status': 'done', 'ts': datetime.now().strftime('%H:%M:%S')})

        # Step 2+3: Mimo analysis
        current_step = 'analyze'
        _log(pid, 'analyze', 'Starting MiMo analysis...')
        _update_step(pid, 'step_analyze', 0, status='processing')
        await broadcast(pid, {'type': 'step', 'step': 'analyze', 'status': 'processing', 'ts': datetime.now().strftime('%H:%M:%S')})

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

        returncode = await stream_mimo(pid, prompt)

        if returncode != 0:
            raise RuntimeError(f"MiMo process exited with code {returncode}")

        # Step 3: Read result
        current_step = 'resume'
        await broadcast(pid, {'type': 'tool_output', 'stream': 'input', 'tool': 'read', 'data': f'$ cat data/pending_result_{pid}.json', 'ts': datetime.now().strftime('%H:%M:%S')})
        _log(pid, 'resume', 'Reading analysis result...')
        _update_step(pid, 'step_resume', 0, status='processing')
        await broadcast(pid, {'type': 'step', 'step': 'resume', 'status': 'processing', 'ts': datetime.now().strftime('%H:%M:%S')})

        result_path = os.path.join(PROJECT_ROOT, 'data', f'pending_result_{pid}.json')
        if not os.path.exists(result_path):
            raise RuntimeError(f"Result file not found: {result_path}")

        with open(result_path) as f:
            data = json.load(f)

        job_data = data['job']
        _mark(pid, 'step_analyze', company=job_data.get('company'), job_num=job_data['num'])
        _log(pid, 'resume', f"Got result: {job_data.get('company')} score={job_data.get('score')}")
        await broadcast(pid, {'type': 'tool_output', 'stream': 'output', 'tool': 'read', 'data': f'Parsed: {job_data.get("company")} | {job_data.get("role")} | Score: {job_data.get("score")}', 'ts': datetime.now().strftime('%H:%M:%S')})

        resume_data = {
            'id': f"pending_{pid}",
            'title': f"{job_data.get('company', 'Unknown')} (Score {job_data.get('score', 0)})",
            'badge': 'Tailored', 'badgeClass': 'badge-tailored',
            'company': job_data.get('company', 'Unknown'),
            'role': job_data.get('role', 'Unknown'),
            'content': data.get('resume_html', ''),
        }
        _mark(pid, 'step_resume')
        _mark(pid, 'step_db')
        await broadcast(pid, {'type': 'step', 'step': 'resume', 'status': 'done', 'ts': datetime.now().strftime('%H:%M:%S')})

        # Step 4: Save to DB
        current_step = 'save'
        await broadcast(pid, {'type': 'tool_output', 'stream': 'input', 'tool': 'db', 'data': f'$ INSERT INTO jobs (num={job_data["num"]}, company="{job_data.get("company")}", score={job_data.get("score")})', 'ts': datetime.now().strftime('%H:%M:%S')})
        _log(pid, 'save', 'Saving to database...')
        _update_step(pid, 'step_db', 0, status='processing')
        await broadcast(pid, {'type': 'step', 'step': 'save', 'status': 'processing', 'ts': datetime.now().strftime('%H:%M:%S')})

        _insert_job(job_data)
        await broadcast(pid, {'type': 'tool_output', 'stream': 'output', 'tool': 'db', 'data': 'Saved job entry', 'ts': datetime.now().strftime('%H:%M:%S')})
        _insert_summary({
            'num': job_data['num'], 'company': job_data.get('company'),
            'match': job_data.get('match'), 'score': job_data.get('score'),
            'summary': data.get('summary', {}).get('summary', ''),
            'stack': job_data.get('stack'),
            'resumeFit': data.get('summary', {}).get('resumeFit', ''),
            'note': data.get('summary', {}).get('note', ''), 'url': url,
        })
        await broadcast(pid, {'type': 'tool_output', 'stream': 'output', 'tool': 'db', 'data': 'Saved summary entry', 'ts': datetime.now().strftime('%H:%M:%S')})
        _insert_resume(resume_data)
        await broadcast(pid, {'type': 'tool_output', 'stream': 'output', 'tool': 'db', 'data': 'Saved tailored resume', 'ts': datetime.now().strftime('%H:%M:%S')})
        _mark(pid, 'step_db')

        # If rescore or requeue, mark old job as deleted
        if source in ('rescore', 'requeue'):
            _mark_old_job_deleted(url, exclude_num=job_data['num'])
            _log(pid, 'save', f'Marked old job as deleted (source: {source})')
            await broadcast(pid, {'type': 'tool_output', 'stream': 'output', 'tool': 'db', 'data': f'Marked old job as deleted', 'ts': datetime.now().strftime('%H:%M:%S')})

        await broadcast(pid, {'type': 'step', 'step': 'save', 'status': 'done', 'ts': datetime.now().strftime('%H:%M:%S')})

        # Step 5: Done
        current_step = 'done'
        await broadcast(pid, {'type': 'tool_output', 'stream': 'output', 'tool': 'done', 'data': f'🎉 Job #{job_data["num"]} ({job_data.get("company")}) processed successfully', 'ts': datetime.now().strftime('%H:%M:%S')})
        _log(pid, 'done', f"Complete: {job_data.get('company')} #{job_data['num']}")
        _update_step(pid, 'step_done', 0, status='done')
        _mark(pid, 'step_done')
        # Save workflow_log to jobs table
        conn = _db()
        row = conn.execute('SELECT workflow_log FROM pending_jobs WHERE id=?', (pid,)).fetchone()
        conn.close()
        if row:
            _save_job_workflow_log(job_data['num'], dict(row)['workflow_log'] or '[]')

        await broadcast(pid, {'type': 'step', 'step': 'done', 'status': 'done', 'ts': datetime.now().strftime('%H:%M:%S')})
        await broadcast(pid, {'type': 'complete', 'pid': pid, 'num': job_data['num'], 'company': job_data.get('company'), 'ts': datetime.now().strftime('%H:%M:%S')})
        print(f"[stream] Job {pid} done: {job_data.get('company')} #{job_data['num']}")

        # Cleanup
        try: os.remove(result_path)
        except OSError: pass

    except Exception as e:
        msg = str(e)
        source = {'fetch':'fetch','analyze':'mimo','resume':'mimo','save':'db','done':'worker'}.get(current_step, 'worker')
        if not msg.startswith('['):
            msg = f"[{source}] {msg}"
        _log(pid, 'error', msg[:200])
        _fail(pid, msg[:500], step=current_step)
        await broadcast(pid, {'type': 'error', 'pid': pid, 'msg': msg[:300], 'step': current_step, 'ts': datetime.now().strftime('%H:%M:%S')})

# --- WebSocket handler ---

async def handler(websocket):
    """Handle WebSocket connections for streaming job progress."""
    pid = None
    try:
        async for message in websocket:
            data = json.loads(message)
            if data.get('action') == 'watch':
                pid = data.get('pid')
                if pid not in clients:
                    clients[pid] = set()
                clients[pid].add(websocket)
                # Send current state
                conn = _db()
                row = conn.execute('SELECT * FROM pending_jobs WHERE id=?', (pid,)).fetchone()
                conn.close()
                if row:
                    item = dict(row)
                    logs = json.loads(item.get('workflow_log') or '[]')
                    await websocket.send(json.dumps({
                        'type': 'state',
                        'pid': pid,
                        'status': item['status'],
                        'logs': logs,
                        'ts': datetime.now().strftime('%H:%M:%S'),
                    }))
            elif data.get('action') == 'process':
                pid = data.get('pid')
                asyncio.create_task(process_job_stream(pid))
            elif data.get('action') == 'stop':
                pid = data.get('pid')
                proc = processes.get(pid)
                if proc:
                    proc.terminate()
                    _log(pid, 'error', 'Process terminated by user')
                    _fail(pid, 'Terminated by user')
                    await broadcast(pid, {'type': 'error', 'pid': pid, 'msg': 'Terminated by user', 'ts': datetime.now().strftime('%H:%M:%S')})
    except websockets.ConnectionClosed:
        pass
    finally:
        if pid and pid in clients:
            clients[pid].discard(websocket)

# --- Start server ---

async def main():
    print(f"[stream] WebSocket server starting on ws://0.0.0.0:8765")
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()  # Run forever

if __name__ == '__main__':
    asyncio.run(main())
