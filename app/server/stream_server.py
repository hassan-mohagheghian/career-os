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

# AI Agent Layer — unified LLM service
from ai_compat import get_llm_service

# Connected clients per job
clients = {}  # pid -> set of websocket connections
processes = {}  # pid -> Popen object

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
_file_dir = os.path.dirname(os.path.abspath(__file__))
_tmp = os.environ.get('TEMP_DIR', 'tmp')
TMP_DIR = _tmp if os.path.isabs(_tmp) else os.path.join(PROJECT_ROOT, _tmp)
os.makedirs(TMP_DIR, exist_ok=True)


def _log(pid, step, msg):
    from dependencies import get_session_sync
    from pending.infrastructure.repositories.sa_pending_repository import SQLAlchemyPendingRepository
    session = get_session_sync()
    try:
        repo = SQLAlchemyPendingRepository(session)
        item = repo.get_by_id(pid)
        logs = json.loads(item['workflow_log'] or '[]') if item else []
        logs.append({'step': step, 'msg': msg, 'ts': datetime.now().strftime('%H:%M:%S')})
        repo.update_workflow_log(pid, json.dumps(logs))
    finally:
        session.close()

def _load_rules(context='job'):
    """Load enabled scoring rules from DB, filtered by context, ordered by priority desc."""
    from dependencies import get_session_sync
    from career.infrastructure.repositories.sa_preference_repository import SQLAlchemyPreferenceRepository
    session = get_session_sync()
    try:
        repo = SQLAlchemyPreferenceRepository(session)
        if context == 'company':
            scopes = ['SHARED', 'COMPANY_PRODUCT', 'COMPANY_RECRUITING']
        else:
            scopes = ['SHARED', 'JOB']
        rows = repo.get_enabled_by_scopes(scopes)
    finally:
        session.close()
    if not rows:
        return "No scoring rules set."
    lines = []
    current_cat = None
    for r in rows:
        cat = r['category']
        if cat != current_cat:
            current_cat = cat
            lines.append(f"\n── {cat.upper()} {'─' * (35 - len(cat))}")
        weight = r.get('score_weight') or r['priority']
        lines.append(f"  #{r['priority']:>3}  {r['key']} (weight:{weight}): {r['value']}")
    return '\n'.join(lines)

def _update_step(pid, step, val, status=None, company=None, job_num=None, error=None):
    from dependencies import get_session_sync
    from pending.infrastructure.repositories.sa_pending_repository import SQLAlchemyPendingRepository
    session = get_session_sync()
    try:
        repo = SQLAlchemyPendingRepository(session)
        fields = {step: val}
        if status:
            fields['status'] = status
        if company:
            fields['company'] = company
        if job_num:
            fields['job_num'] = job_num
        if error:
            fields['error'] = error
        fields['updated_at'] = datetime.now().isoformat()
        repo.update_fields(pid, **fields)
    finally:
        session.close()

def _mark(pid, step, company=None, job_num=None):
    _update_step(pid, step, 1, company=company, job_num=job_num)

def _fail(pid, msg, step=None):
    error_msg = f"[{step}] {msg}" if step else msg
    _update_step(pid, 'step_done', 0, status='failed', error=error_msg)

def _get_next_num():
    from dependencies import get_session_sync
    from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
    session = get_session_sync()
    try:
        repo = SQLAlchemyJobRepository(session)
        return repo.get_next_num()
    finally:
        session.close()

def _get_existing_num(url):
    """Check if a job with this URL already exists. Returns its num or None."""
    from dependencies import get_session_sync
    from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
    session = get_session_sync()
    try:
        repo = SQLAlchemyJobRepository(session)
        return repo.get_num_by_url(url)
    finally:
        session.close()

def _parse_adv_at(posted_text):
    """Estimate when the job was advertised. If no specific datetime, return current datetime."""
    from datetime import timedelta
    now = datetime.now()
    if not posted_text or posted_text in ('Active', 'N/A', 'Not specified'):
        return now.isoformat()
    posted_text = posted_text.lower().strip()
    has_plus = '+' in posted_text
    try:
        if 'hour' in posted_text:
            hours = int(''.join(filter(str.isdigit, posted_text)) or 1)
            return (now - timedelta(hours=hours)).isoformat()
        elif 'day' in posted_text:
            days = int(''.join(filter(str.isdigit, posted_text)) or 1)
            return (now - timedelta(days=days)).isoformat()
        elif 'week' in posted_text:
            weeks = int(''.join(filter(str.isdigit, posted_text)) or 1)
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


def _insert_job(d):
    from dependencies import get_session_sync
    from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
    d = _normalize_job_data(d)
    now = datetime.now().isoformat()
    adv_at = d.get('adv_at') or _parse_adv_at(d.get('posted', ''))
    see_at = d.get('see_at') or now
    locations = d.get('locations', [])
    if isinstance(locations, str):
        locations = [locations] if locations else []

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

    work_types = d.get('work_types', [])
    if isinstance(work_types, str):
        try:
            work_types = json.loads(work_types)
        except:
            work_types = []
    if not work_types and d.get('work_type'):
        work_types = [d['work_type']]
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

    session = get_session_sync()
    try:
        repo = SQLAlchemyJobRepository(session)
        repo.upsert({
            'num': d['num'],
            'company': d['company'],
            'role': d['role'],
            'location': d['location'],
            'match': d['match'],
            'score': d['score'],
            'salary': d['salary'],
            'stack': d['stack'],
            'visa': d['visa'],
            'applicants': d['applicants'],
            'posted': d['posted'],
            'industry': d['industry'],
            'domain': d['domain'],
            'notes': d['notes'],
            'action': d['action'],
            'url': d['url'],
            'work_type': normalized_wt[0] if normalized_wt else 'On-site',
            'workflow_log': d.get('workflow_log', '[]'),
            'created_at': d.get('created_at', now),
            'locations': json.dumps(locations),
            'deleted': 0,
            'employment_type': employment_type,
            'work_types': json.dumps(normalized_wt),
            'raw_description': d.get('raw_description'),
            'structured_description': d.get('structured_description'),
            'rescoring': d.get('rescoring', 0),
            'success': d.get('success'),
            'adv_at': adv_at,
            'see_at': see_at,
            'apply_reason': d.get('apply_reason', ''),
        })
    finally:
        session.close()

def _save_job_workflow_log(num, log_json):
    from dependencies import get_session_sync
    from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
    session = get_session_sync()
    try:
        repo = SQLAlchemyJobRepository(session)
        repo.update_workflow_log(num, log_json)
    finally:
        session.close()

def _insert_summary(d):
    from dependencies import get_session_sync
    from jobs.infrastructure.repositories.sa_summary_repository import SQLAlchemySummaryRepository
    session = get_session_sync()
    try:
        repo = SQLAlchemySummaryRepository(session)
        repo.upsert({
            'num': d['num'],
            'company': d['company'],
            'match': d['match'],
            'score': d['score'],
            'summary': d['summary'],
            'stack': d['stack'],
            'resumeFit': d['resumeFit'],
            'note': d['note'],
            'url': d['url'],
        })
    finally:
        session.close()

def _insert_resume(d):
    from dependencies import get_session_sync
    from resume.infrastructure.repositories.sa_resume_repository import SQLAlchemyResumeRepository
    session = get_session_sync()
    try:
        repo = SQLAlchemyResumeRepository(session)
        repo.upsert({
            'id': d['id'],
            'title': d.get('title'),
            'company': d.get('company'),
            'role': d.get('role'),
            'content': d.get('content'),
            'version': d.get('version', 1),
            'raw_text': d.get('raw_text'),
            'created_at': d.get('created_at'),
            'job_num': d.get('job_num'),
        })
    finally:
        session.close()

def _mark_old_job_deleted(url, exclude_num=None):
    """Mark old job with same URL as deleted when rescore/requeue creates a new one."""
    from dependencies import get_session_sync
    from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
    session = get_session_sync()
    try:
        repo = SQLAlchemyJobRepository(session)
        repo.set_deleted_by_url(url, exclude_num=exclude_num)
    finally:
        session.close()

def _normalize_job_data(d):
    """Normalize job location and work_type fields."""
    import re

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
    """Run LLM with streaming output via WebSocket."""
    await broadcast(pid, {'type': 'process_start', 'pid': pid, 'ts': datetime.now().strftime('%H:%M:%S')})

    llm = get_llm_service()

    def on_event(evt):
        """Forward events to WebSocket broadcast."""
        etype = evt.get('type', '')
        if etype == 'text':
            txt = evt.get('part', {}).get('text', '')
            if txt:
                _log(pid, 'mimo', txt[:200])
                asyncio.ensure_future(broadcast(pid, {'type': 'tool_output', 'stream': 'text', 'data': txt, 'ts': datetime.now().strftime('%H:%M:%S')}))
        elif etype == 'tool_use':
            part = evt.get('part', {})
            tool = part.get('tool', 'unknown')
            state = part.get('state', {})
            status = state.get('status', '')
            inp = state.get('input', {})
            output = state.get('output', '') or state.get('metadata', {}).get('output', '')
            title = state.get('title', '')
            _log(pid, 'mimo', f"Tool: {tool} [{status}] {title}")
            asyncio.ensure_future(broadcast(pid, {'type': 'tool_output', 'stream': 'input', 'tool': tool, 'data': f"$ {inp.get('command', '')}", 'ts': datetime.now().strftime('%H:%M:%S')}))
            if output:
                asyncio.ensure_future(broadcast(pid, {'type': 'tool_output', 'stream': 'output', 'tool': tool, 'data': output.rstrip(), 'ts': datetime.now().strftime('%H:%M:%S')}))
        elif etype == 'step_finish':
            reason = evt.get('part', {}).get('reason', '')
            tokens = evt.get('part', {}).get('tokens', {})
            _log(pid, 'mimo', f"Step finished: {reason} ({tokens.get('total', 0)} tokens)")

    def on_session_id(sid):
        asyncio.ensure_future(broadcast(pid, {'type': 'session_id', 'session_id': sid, 'ts': datetime.now().strftime('%H:%M:%S')}))

    loop = asyncio.get_event_loop()
    resp = await loop.run_in_executor(
        None,
        lambda: llm.generate_streaming(
            prompt,
            context={"pid": pid},
            timeout=300,
            on_event=on_event,
            on_session_id=on_session_id,
        ),
    )

    returncode = resp.metadata.get("returncode", 0)
    await broadcast(pid, {'type': 'process_end', 'pid': pid, 'returncode': returncode, 'ts': datetime.now().strftime('%H:%M:%S')})
    return returncode

# --- Main pipeline ---

async def process_job_stream(pid):
    """Full pipeline with streaming output."""
    from dependencies import get_session_sync
    from pending.infrastructure.repositories.sa_pending_repository import SQLAlchemyPendingRepository
    from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository

    session = get_session_sync()
    try:
        pending_repo = SQLAlchemyPendingRepository(session)
        item = pending_repo.get_by_id(pid)
    finally:
        session.close()

    if not item:
        return
    url = item['url']
    source = item.get('source', 'cli')

    job_file = os.path.join(TMP_DIR, f'job_{pid}.txt')

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
            from dependencies import get_session_sync as _gss
            from pending.infrastructure.repositories.sa_pending_repository import SQLAlchemyPendingRepository as _SPR
            _s = _gss()
            try:
                _SPR(_s).update_fields(pid, company=company or title[:40])
            finally:
                _s.close()
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
        existing_num = _get_existing_num(url)
        if existing_num:
            next_num = existing_num
            _log(pid, 'analyze', f'Rescoring existing job #{next_num}...')
        else:
            _log(pid, 'analyze', f'New job #{next_num}...')

        rules = _load_rules()
        prompt = load_prompt('job_processing/step8_score',
            url=url, job_file=job_file, project_root=PROJECT_ROOT,
            pid=pid, next_num=next_num, rules=rules)

        returncode = await stream_mimo(pid, prompt)

        if returncode != 0:
            raise RuntimeError(f"MiMo process exited with code {returncode}")

        # Step 3: Read result
        current_step = 'resume'
        await broadcast(pid, {'type': 'tool_output', 'stream': 'input', 'tool': 'read', 'data': f'$ cat /tmp/pending_result_{pid}.json', 'ts': datetime.now().strftime('%H:%M:%S')})
        _log(pid, 'resume', 'Reading analysis result...')
        await broadcast(pid, {'type': 'step', 'step': 'resume', 'status': 'processing', 'ts': datetime.now().strftime('%H:%M:%S')})

        result_path = os.path.join(TMP_DIR, f'pending_result_{pid}.json')
        if not os.path.exists(result_path):
            raise RuntimeError(f"Result file not found: {result_path}")

        with open(result_path) as f:
            data = json.loads(f.read(), strict=False)

        job_data = data['job']
        _mark(pid, 'step_analyze', company=job_data.get('company'), job_num=job_data['num'])
        _log(pid, 'resume', f"Got result: {job_data.get('company')} score={job_data.get('score')}")
        await broadcast(pid, {'type': 'tool_output', 'stream': 'output', 'tool': 'read', 'data': f'Parsed: {job_data.get("company")} | {job_data.get("role")} | Score: {job_data.get("score")}', 'ts': datetime.now().strftime('%H:%M:%S')})

        resume_data = {
            'id': f"pending_{pid}",
            'title': f"{job_data.get('company', 'Unknown')} ({job_data.get('score', 'P')})",
            'company': job_data.get('company', 'Unknown'),
            'role': job_data.get('role', 'Unknown'),
            'content': data.get('resume_html', ''),
        }
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
        await broadcast(pid, {'type': 'tool_output', 'stream': 'output', 'tool': 'done', 'data': f'Job #{job_data["num"]} ({job_data.get("company")}) processed successfully', 'ts': datetime.now().strftime('%H:%M:%S')})
        _log(pid, 'done', f"Complete: {job_data.get('company')} #{job_data['num']}")
        _update_step(pid, 'step_done', 0, status='done')
        _mark(pid, 'step_done')
        # Save workflow_log to jobs table
        from dependencies import get_session_sync as _gss2
        from pending.infrastructure.repositories.sa_pending_repository import SQLAlchemyPendingRepository as _SPR2
        _s2 = _gss2()
        try:
            _item = _SPR2(_s2).get_by_id(pid)
        finally:
            _s2.close()
        if _item:
            _save_job_workflow_log(job_data['num'], _item.get('workflow_log') or '[]')

        await broadcast(pid, {'type': 'step', 'step': 'done', 'status': 'done', 'ts': datetime.now().strftime('%H:%M:%S')})
        await broadcast(pid, {'type': 'complete', 'pid': pid, 'num': job_data['num'], 'company': job_data.get('company'), 'ts': datetime.now().strftime('%H:%M:%S')})
        print(f"[stream] Job {pid} done: {job_data.get('company')} #{job_data['num']}")

    except Exception as e:
        msg = str(e)
        source = {'fetch':'fetch','analyze':'mimo','resume':'mimo','save':'db','done':'worker'}.get(current_step, 'worker')
        if not msg.startswith('['):
            msg = f"[{source}] {msg}"
        _log(pid, 'error', msg[:200])
        _fail(pid, msg[:500], step=current_step)
        await broadcast(pid, {'type': 'error', 'pid': pid, 'msg': msg[:300], 'step': current_step, 'ts': datetime.now().strftime('%H:%M:%S')})
    finally:
        for f in [job_file, os.path.join(TMP_DIR, f'pending_result_{pid}.json')]:
            try: os.remove(f)
            except OSError: pass

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
                from dependencies import get_session_sync
                from pending.infrastructure.repositories.sa_pending_repository import SQLAlchemyPendingRepository
                session = get_session_sync()
                try:
                    pending_repo = SQLAlchemyPendingRepository(session)
                    row = pending_repo.get_by_id(pid)
                finally:
                    session.close()
                if row:
                    logs = json.loads(row.get('workflow_log') or '[]')
                    await websocket.send(json.dumps({
                        'type': 'state',
                        'pid': pid,
                        'status': row['status'],
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
