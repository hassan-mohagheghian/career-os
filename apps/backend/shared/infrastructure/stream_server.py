"""
WebSocket server for streaming AI provider output in real-time.
Runs alongside Flask on a separate port.
"""
import asyncio
import json
import subprocess
import os
import signal
from datetime import datetime

import websockets
from shared.infrastructure.process.logging_config import get_logger
from shared.infrastructure.prompts.loader import load_prompt
from shared.infrastructure.utils import repair_llm_json

log = get_logger('stream')

# AI Agent Layer — unified LLM service
from shared.infrastructure.ai.compat import get_llm_service

# Unified Tool Layer — local-first URL fetching
from ai.infrastructure.tools.fetch import fetch_page

# Connected clients per job
clients = {}  # pid -> set of websocket connections
processes = {}  # pid -> Popen object

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _log(pid, step, msg):
    from dependencies import get_session_sync
    from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
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
    from rules.infrastructure.repositories.sa_rule_repository import SQLAlchemyRuleRepository
    session = get_session_sync()
    try:
        repo = SQLAlchemyRuleRepository(session)
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

def _update_step(pid, step, val, status=None, company=None, job_id=None, error=None):
    from dependencies import get_session_sync
    from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
    session = get_session_sync()
    try:
        repo = SQLAlchemyPendingRepository(session)
        fields = {step: val}
        if status:
            fields['status'] = status
        if company:
            fields['company'] = company
        if job_id:
            fields['job_id'] = job_id
        if error:
            fields['error'] = error
        fields['updated_at'] = datetime.now().isoformat()
        repo.update_fields(pid, **fields)
    finally:
        session.close()

def _mark(pid, step, company=None, job_id=None):
    _update_step(pid, step, 1, company=company, job_id=job_id)

def _fail(pid, msg, step=None):
    error_msg = f"[{step}] {msg}" if step else msg
    _update_step(pid, 'step_done', 0, status='failed', error=error_msg)

def _get_existing_id(url):
    """Check if a job with this URL already exists. Returns its UUID id or None."""
    from dependencies import get_session_sync
    from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
    session = get_session_sync()
    try:
        repo = SQLAlchemyJobRepository(session)
        return repo.get_id_by_url(url)
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

    employment_types = d.get('employment_types', [])
    if isinstance(employment_types, str):
        try:
            employment_types = json.loads(employment_types)
        except:
            employment_types = []
    if not employment_types and d.get('employment_type'):
        employment_types = [d['employment_type']]
    normalized_et = []
    for et in employment_types:
        et_lower = (et or '').lower()
        if 'full' in et_lower:
            if 'Full-time' not in normalized_et:
                normalized_et.append('Full-time')
        elif 'part' in et_lower:
            if 'Part-time' not in normalized_et:
                normalized_et.append('Part-time')
        elif 'contract' in et_lower or 'freelance' in et_lower:
            if 'Contract' not in normalized_et:
                normalized_et.append('Contract')
        elif 'intern' in et_lower:
            if 'Internship' not in normalized_et:
                normalized_et.append('Internship')
        elif 'temp' in et_lower:
            if 'Temporary' not in normalized_et:
                normalized_et.append('Temporary')
    if not normalized_et:
        normalized_et = ['Full-time']

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
            'id': d['id'],
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
            'workflow_log': d.get('workflow_log', '[]'),
            'created_at': d.get('created_at', now),
            'locations': json.dumps(locations),
            'deleted': 0,
            'work_types': json.dumps(normalized_wt),
            'employment_types': json.dumps(normalized_et),
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

def _save_job_workflow_log(job_id, log_json):
    from dependencies import get_session_sync
    from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
    session = get_session_sync()
    try:
        repo = SQLAlchemyJobRepository(session)
        repo.update_workflow_log(job_id, log_json)
    finally:
        session.close()

def _insert_summary(d):
    from dependencies import get_session_sync
    from jobs.infrastructure.repositories.sa_summary_repository import SQLAlchemySummaryRepository
    session = get_session_sync()
    try:
        repo = SQLAlchemySummaryRepository(session)
        repo.upsert({
            'job_id': d['job_id'],
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
    from jobs.infrastructure.repositories.sa_resume_repository import SQLAlchemyResumeRepository
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
            'job_id': d.get('job_id'),
        })
    finally:
        session.close()

def _mark_old_job_deleted(url, exclude_id=None):
    """Mark old job with same URL as deleted when rescore/requeue creates a new one."""
    from dependencies import get_session_sync
    from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
    session = get_session_sync()
    try:
        repo = SQLAlchemyJobRepository(session)
        repo.set_deleted_by_url(url, exclude_id=exclude_id)
    finally:
        session.close()

def _normalize_job_data(d):
    """Normalize job location and work_types fields."""
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

# --- Fetch URL (uses unified Tool Layer) ---

import urllib.request
import re

def fetch_url(url):
    """Fetch a URL using the unified Tool Layer.

    Local-first approach: fetch → preprocess → return cleaned text.
    Raises RuntimeError for backward compatibility.
    """
    page = fetch_page(url)
    if page.is_ok:
        return page.plain_text
    else:
        raise RuntimeError(page.error.message if page.error else "Fetch failed")

# --- Stream provider process ---

async def stream_provider(pid, prompt):
    """Run LLM with streaming output via WebSocket.

    Returns (returncode, result_dict). result_dict is parsed from
    the LLM text response when the AI outputs JSON instead of writing
    a result file.
    """
    await broadcast(pid, {'type': 'process_start', 'pid': pid, 'ts': datetime.now().strftime('%H:%M:%S')})

    llm = get_llm_service()

    def on_event(evt):
        """Forward events to WebSocket broadcast."""
        etype = evt.get('type', '')
        if etype == 'text':
            txt = evt.get('part', {}).get('text', '')
            if txt:
                _log(pid, 'ai', txt[:200])
                asyncio.ensure_future(broadcast(pid, {'type': 'tool_output', 'stream': 'text', 'data': txt, 'ts': datetime.now().strftime('%H:%M:%S')}))
        elif etype == 'tool_use':
            part = evt.get('part', {})
            tool = part.get('tool', 'unknown')
            state = part.get('state', {})
            status = state.get('status', '')
            inp = state.get('input', {})
            output = state.get('output', '') or state.get('metadata', {}).get('output', '')
            title = state.get('title', '')
            _log(pid, 'ai', f"Tool: {tool} [{status}] {title}")
            asyncio.ensure_future(broadcast(pid, {'type': 'tool_output', 'stream': 'input', 'tool': tool, 'data': f"$ {inp.get('command', '')}", 'ts': datetime.now().strftime('%H:%M:%S')}))
            if output:
                asyncio.ensure_future(broadcast(pid, {'type': 'tool_output', 'stream': 'output', 'tool': tool, 'data': output.rstrip(), 'ts': datetime.now().strftime('%H:%M:%S')}))
        elif etype == 'step_finish':
            reason = evt.get('part', {}).get('reason', '')
            tokens = evt.get('part', {}).get('tokens', {})
            _log(pid, 'ai', f"Step finished: {reason} ({tokens.get('total', 0)} tokens)")

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

    result_dict = None
    if resp.content:
        try:
            parsed = repair_llm_json(resp.content)
            if isinstance(parsed, dict):
                result_dict = parsed
        except Exception:
            pass

    return returncode, result_dict

# --- Main pipeline ---

async def process_job_stream(pid):
    """Full pipeline with streaming output using LangGraph state management (no file I/O)."""
    from dependencies import get_session_sync
    from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository

    session = get_session_sync()
    try:
        pending_repo = SQLAlchemyPendingRepository(session)
        item = pending_repo.get_by_id(pid)
    finally:
        session.close()

    if not item:
        return
    url = item.get('url', '')
    notes = json.loads(item.get('notes') or '[]')
    links = json.loads(item.get('links') or '[]')
    source = item.get('source', 'cli')

    try:
        _log(pid, 'start', f'Processing {url[:60] if url else "notes/links"}...')
        await broadcast(pid, {'type': 'tool_output', 'stream': 'input', 'tool': 'fetch', 'data': f"$ Processing job from {url[:80] if url else 'notes/links'}...", 'ts': datetime.now().strftime('%H:%M:%S')})

        _update_step(pid, 'step_fetch', 0, status='processing')
        await broadcast(pid, {'type': 'step', 'step': 'fetch', 'status': 'processing', 'ts': datetime.now().strftime('%H:%M:%S')})

        from ai.infrastructure.graphs.runtime.state import create_initial_state
        from ai.infrastructure.graphs.job.graph import build_job_processing_graph

        builder = build_job_processing_graph()

        from dependencies import get_session_sync as _gss
        from jobs.infrastructure.repositories.sa_resume_repository import SQLAlchemyResumeRepository
        from rules.infrastructure.repositories.sa_rule_repository import SQLAlchemyRuleRepository

        resume_text = ""
        linkedin_text = ""
        rules = ""
        sess = _gss()
        try:
            resume_repo = SQLAlchemyResumeRepository(sess)
            resume_text = resume_repo.get_latest_original_raw_text() or ""
            linkedin_text = resume_repo.get_latest_linkedin_raw_text() or ""
            rule_repo = SQLAlchemyRuleRepository(sess)
            rows = rule_repo.get_enabled_by_scopes(["SHARED", "JOB"])
            if rows:
                lines = []
                current_cat = None
                for r in rows:
                    cat = r["category"]
                    if cat != current_cat:
                        current_cat = cat
                        lines.append(f"\n\u2015 {cat.upper()}")
                    weight = r.get("score_weight") or r["priority"]
                    lines.append(f"  #{r['priority']:>3}  {r['key']} (weight:{weight}): {r['value']}")
                rules = "\n".join(lines)
            else:
                rules = "No scoring rules set."
        finally:
            sess.close()

        context = {
            "pid": str(pid),
            "url": url,
            "notes": notes,
            "links": links,
            "source": source,
            "resume_text": resume_text,
            "linkedin_text": linkedin_text,
            "rules": rules,
        }

        initial = create_initial_state(input=url or "", context=context)

        graph = await asyncio.get_event_loop().run_in_executor(None, builder.compile)
        result = await asyncio.get_event_loop().run_in_executor(
            None, lambda: graph.invoke(initial)
        )

        current_step = 'analyze'
        _log(pid, 'analyze', 'Starting analysis...')
        _update_step(pid, 'step_analyze', 0, status='processing')
        await broadcast(pid, {'type': 'step', 'step': 'analyze', 'status': 'processing', 'ts': datetime.now().strftime('%H:%M:%S')})

        errors = result.get("errors", [])
        if errors:
            await broadcast(pid, {'type': 'tool_output', 'stream': 'output', 'tool': 'analyze', 'data': '\n'.join(errors[-3:]), 'ts': datetime.now().strftime('%H:%M:%S')})
            _log(pid, 'error', '\n'.join(errors))
        else:
            await broadcast(pid, {'type': 'tool_output', 'stream': 'output', 'tool': 'analyze', 'data': 'Analysis complete', 'ts': datetime.now().strftime('%H:%M:%S')})

        metadata = result.get("metadata", {})
        extract_raw = metadata.get("extract_raw", {})
        if extract_raw.get("success"):
            await broadcast(pid, {'type': 'tool_output', 'stream': 'output', 'tool': 'analyze', 'data': 'Extraction successful', 'ts': datetime.now().strftime('%H:%M:%S')})

        fetch_meta = metadata.get("fetch", {})
        content_length = fetch_meta.get("length", 0)
        if content_length:
            await broadcast(pid, {'type': 'tool_output', 'stream': 'output', 'tool': 'fetch', 'data': f'→ Received response ({content_length} chars)', 'ts': datetime.now().strftime('%H:%M:%S')})

        extraction = metadata.get("extraction", {})
        company = extraction.get("company", "")
        title = extraction.get("title", "")
        if company or title:
            sess2 = _gss()
            try:
                from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository as _SPR
                _SPR(sess2).update_fields(pid, company=company or title[:40])
            finally:
                sess2.close()
            await broadcast(pid, {'type': 'job_info', 'pid': pid, 'title': title, 'company': company, 'ts': datetime.now().strftime('%H:%M:%S')})
            await broadcast(pid, {'type': 'tool_output', 'stream': 'output', 'tool': 'fetch', 'data': f'→ Extracted: {company} — {title}', 'ts': datetime.now().strftime('%H:%M:%S')})

        _mark(pid, 'step_fetch')
        await broadcast(pid, {'type': 'step', 'step': 'fetch', 'status': 'done', 'ts': datetime.now().strftime('%H:%M:%S')})

        persistence = metadata.get("persistence", {})
        if persistence.get("success"):
            job_id = persistence.get("job_id")
            company_name = persistence.get("company", "Unknown")
            score = metadata.get("score", "P")

            await broadcast(pid, {'type': 'tool_output', 'stream': 'output', 'tool': 'analyze', 'data': f'Score: {score}', 'ts': datetime.now().strftime('%H:%M:%S')})
            await broadcast(pid, {'type': 'tool_output', 'stream': 'output', 'tool': 'read', 'data': f'Parsed: {company_name} | Score: {score}', 'ts': datetime.now().strftime('%H:%M:%S')})

            _mark(pid, 'step_analyze', company=company_name, job_id=job_id)
            _mark(pid, 'step_db')

            current_step = 'save'
            await broadcast(pid, {'type': 'tool_output', 'stream': 'input', 'tool': 'db', 'data': f'$ INSERT INTO jobs (id={job_id}, company="{company_name}", score={score})', 'ts': datetime.now().strftime('%H:%M:%S')})
            _log(pid, 'save', f'Saved to database: #{job_id} {company_name}')
            _update_step(pid, 'step_db', 0, status='processing')
            await broadcast(pid, {'type': 'step', 'step': 'save', 'status': 'processing', 'ts': datetime.now().strftime('%H:%M:%S')})

            await broadcast(pid, {'type': 'tool_output', 'stream': 'output', 'tool': 'db', 'data': f'Job #{job_id} ({company_name}) saved', 'ts': datetime.now().strftime('%H:%M:%S')})
            _mark(pid, 'step_db')
            await broadcast(pid, {'type': 'step', 'step': 'save', 'status': 'done', 'ts': datetime.now().strftime('%H:%M:%S')})

            if source in ('rescore', 'requeue'):
                from jobs.infrastructure.workers.worker import _mark_old_job_deleted
                _mark_old_job_deleted(url, exclude_id=job_id)
                await broadcast(pid, {'type': 'tool_output', 'stream': 'output', 'tool': 'db', 'data': 'Marked old job as deleted', 'ts': datetime.now().strftime('%H:%M:%S')})

            current_step = 'done'
            await broadcast(pid, {'type': 'tool_output', 'stream': 'output', 'tool': 'done', 'data': f'Job #{job_id} ({company_name}) processed successfully', 'ts': datetime.now().strftime('%H:%M:%S')})
            _log(pid, 'done', f"Complete: {company_name} #{job_id}")
            _update_step(pid, 'step_done', 0, status='done')
            _mark(pid, 'step_done')

            from jobs.infrastructure.workers.worker import _save_job_workflow_log
            sess3 = _gss()
            try:
                from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository as _SPR3
                _item = _SPR3(sess3).get_by_id(pid)
            finally:
                sess3.close()
            if _item:
                _save_job_workflow_log(job_id, _item.get('workflow_log') or '[]')

            await broadcast(pid, {'type': 'step', 'step': 'done', 'status': 'done', 'ts': datetime.now().strftime('%H:%M:%S')})
            await broadcast(pid, {'type': 'complete', 'pid': pid, 'job_id': job_id, 'company': company_name, 'ts': datetime.now().strftime('%H:%M:%S')})
            log.info("Job done", pid=pid, company=company_name, job_id=job_id)
        else:
            persist_error = persistence.get("error", "Unknown error")
            raise RuntimeError(f"Persistence failed: {persist_error}")

    except Exception as e:
        msg = str(e)
        if not msg.startswith('['):
            msg = f"[Processing] {msg}"
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
                from dependencies import get_session_sync
                from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
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
    log.info("WebSocket server starting", address="ws://0.0.0.0:8765")
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()  # Run forever

if __name__ == '__main__':
    asyncio.run(main())
