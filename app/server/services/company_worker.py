"""
Background worker that processes pending companies.
Fetches company URL or uses manual notes, runs AI extraction and analysis,
then saves structured company intelligence to DB.
"""
import os
import re
import json
import sqlite3
import subprocess
import threading
import urllib.request
from datetime import datetime
from prompts import load_prompt

_file_dir = os.path.dirname(os.path.abspath(__file__))
_server_dir = os.path.join(_file_dir, '..')
_db_path = os.environ.get('DB_PATH', os.path.join(_server_dir, 'db', 'jobs.db'))
DB_PATH = _db_path if os.path.isabs(_db_path) else os.path.normpath(os.path.join(_server_dir, _db_path))
PROJECT_ROOT = os.path.abspath(os.path.join(_file_dir, '..', '..', '..'))
MIMO_BIN = os.path.expanduser('~/.mimocode/bin/mimo')
_tmp = os.environ.get('TEMP_DIR', 'tmp')
TMP_DIR = _tmp if os.path.isabs(_tmp) else os.path.join(PROJECT_ROOT, _tmp)
os.makedirs(TMP_DIR, exist_ok=True)


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


def _update_step(pid, step, val, status=None, company_name=None, company_id=None, error=None):
    conn = _db()
    fields = [f'{step}=?']
    values = [val]
    if status:
        fields.append('status=?'); values.append(status)
    if company_name:
        fields.append('company_name=?'); values.append(company_name)
    if company_id:
        fields.append('company_id=?'); values.append(company_id)
    if error:
        fields.append('error=?'); values.append(error)
    fields.append('updated_at=?'); values.append(datetime.now().isoformat())
    values.append(pid)
    conn.execute(f'UPDATE pending_companies SET {",".join(fields)} WHERE id=?', values)
    conn.commit(); conn.close()


def _mark(pid, step):
    _update_step(pid, step, 1)


def _log(pid, step, msg):
    conn = _db()
    row = conn.execute('SELECT workflow_log FROM pending_companies WHERE id=?', (pid,)).fetchone()
    logs = json.loads(row['workflow_log'] or '[]') if row else []
    logs.append({'step': step, 'msg': msg, 'ts': datetime.now().strftime('%H:%M:%S')})
    conn.execute('UPDATE pending_companies SET workflow_log=? WHERE id=?', (json.dumps(logs), pid))
    conn.commit(); conn.close()


def _fail(pid, msg, step=None):
    error_msg = f"[{step}] {msg}" if step else msg
    _update_step(pid, 'step_done', 0, status='failed', error=error_msg)


def _is_paused_or_stopped(pid):
    conn = _db()
    row = conn.execute('SELECT status FROM pending_companies WHERE id=?', (pid,)).fetchone()
    conn.close()
    if not row:
        return True
    return dict(row)['status'] not in ('processing',)


def _fetch_url(url):
    """Fetch a URL and return cleaned text content."""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
    if len(text) < 50:
        raise RuntimeError("Fetched page too short — URL may be invalid")
    return text[:8000]


def _stream_mimo_output(cmd, cwd, env, timeout, pid):
    """Run mimo with streaming output, logging events to DB in real-time."""
    proc = subprocess.Popen(
        cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, env=env,
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
        for raw_line in proc.stdout:
            line = raw_line.rstrip('\n')
            if not line:
                continue
            all_lines.append(line)
            try:
                evt = json.loads(line)
                event_type = evt.get('type', '')
                if event_type == 'text':
                    text = evt.get('part', {}).get('text', '')
                    if text:
                        _log(pid, 'mimo', f'text: {text[:200]}')
                elif event_type == 'tool_use':
                    part = evt.get('part', {})
                    tool = part.get('tool', 'unknown')
                    _log(pid, 'mimo', f'tool: {tool}')
                elif event_type == 'step_finish':
                    part = evt.get('part', {})
                    tokens = part.get('tokens', {})
                    _log(pid, 'mimo', f'step: {part.get("reason", "")} ({tokens.get("total", 0)} tokens)')
            except json.JSONDecodeError:
                _log(pid, 'mimo', f'[raw] {line[:200]}')

        timed_out.set()
        proc.wait()
        if proc.returncode == -9:
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


def _extract_company_info(input_text, input_type, pid):
    """Step 1: Extract structured company data using mimo."""
    output_file = os.path.join(TMP_DIR, f'company_extract_{pid}.json')
    content = input_text[:6000] if input_type == 'manual' else f"URL: {input_text}"
    prompt = load_prompt('company_extract',
        content=content, input_type=input_type, output_file=output_file)

    returncode, _ = _stream_mimo_output(
        [MIMO_BIN, 'run', prompt, '--format', 'json', '--dangerously-skip-permissions'],
        cwd=PROJECT_ROOT, env={**os.environ, 'NO_COLOR': '1'},
        timeout=180, pid=pid,
    )

    if returncode == 0 and os.path.exists(output_file):
        try:
            with open(output_file) as f:
                data = json.load(f)
            os.remove(output_file)
            return data
        except Exception:
            pass
    return None


def _analyze_company(company_data, pid):
    """Step 2: Generate full intelligence analysis using mimo."""
    output_file = os.path.join(TMP_DIR, f'company_analyze_{pid}.json')
    prompt = load_prompt('company_analyze',
        company_data=json.dumps(company_data, ensure_ascii=False)[:4000],
        output_file=output_file)

    returncode, _ = _stream_mimo_output(
        [MIMO_BIN, 'run', prompt, '--format', 'json', '--dangerously-skip-permissions'],
        cwd=PROJECT_ROOT, env={**os.environ, 'NO_COLOR': '1'},
        timeout=300, pid=pid,
    )

    if returncode == 0 and os.path.exists(output_file):
        try:
            with open(output_file) as f:
                data = json.load(f)
            os.remove(output_file)
            return data
        except Exception:
            pass
    return None


def _save_company(company_data, intelligence_data, raw_source):
    """Step 3: Save company + intelligence to DB."""
    conn = _db()
    now = datetime.now().isoformat()

    # Prepare all fields
    fields = {
        'name': company_data.get('name', ''),
        'website': company_data.get('website', ''),
        'domain': company_data.get('domain', ''),
        'industry': company_data.get('industry', ''),
        'country': company_data.get('country', ''),
        'city': company_data.get('city', ''),
        'description': company_data.get('description', ''),
        'company_size': company_data.get('company_size', ''),
        'company_type': company_data.get('company_type', ''),
        'logo_url': company_data.get('logo_url', ''),
        'founded_year': company_data.get('founded_year', ''),
        'headquarters_full': company_data.get('headquarters_full', ''),
        'countries_of_operation': json.dumps(company_data.get('countries_of_operation', []), ensure_ascii=False),
        'funding_stage': company_data.get('funding_stage', ''),
        'funding_amount': company_data.get('funding_amount', ''),
        'products': json.dumps(company_data.get('products', []), ensure_ascii=False),
        'tech_stack': json.dumps(company_data.get('tech_stack', {}), ensure_ascii=False),
        'work_environment': json.dumps(company_data.get('work_environment', {}), ensure_ascii=False),
        'extra': json.dumps({
            'key_clients': company_data.get('key_clients', []),
            'competitors': company_data.get('competitors', []),
            'investors': company_data.get('investors', []),
            'contact_info': company_data.get('contact_info', {}),
            'engineering_culture': company_data.get('engineering_culture', {}),
            'culture_signals': company_data.get('culture_signals', {}),
            'international_signals': company_data.get('international_signals', {}),
            'benefits': company_data.get('benefits', {}),
            'any_other_notable_info': company_data.get('extra', {}).get('any_other_notable_info', ''),
        }, ensure_ascii=False),
    }

    # Insert or update company
    company_id = company_data.get('id')
    if company_id:
        set_clause = ', '.join(f'{k}=?' for k in fields)
        values = list(fields.values()) + ['completed', now, company_id]
        conn.execute(f'UPDATE companies SET {set_clause}, processing_status=?, updated_at=? WHERE id=?', values)
    else:
        cols = ', '.join(fields.keys())
        placeholders = ', '.join(['?' for _ in fields])
        values = list(fields.values()) + ['completed', now, now]
        cur = conn.execute(f'INSERT INTO companies ({cols}, processing_status, created_at, updated_at) VALUES ({placeholders},?,?,?)', values)
        company_id = cur.lastrowid

    # Save intelligence
    scores = intelligence_data.get('scores', {})
    conn.execute('''INSERT OR REPLACE INTO company_intelligence
        (company_id, overview, culture_analysis, international_analysis, career_analysis,
         benefits_analysis, visa_analysis, technology_analysis, recommendation, scores, raw_source_data, generated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
        (company_id,
         json.dumps(intelligence_data.get('overview', {}), ensure_ascii=False),
         json.dumps(intelligence_data.get('culture_analysis', {}), ensure_ascii=False),
         json.dumps(intelligence_data.get('international_analysis', {}), ensure_ascii=False),
         json.dumps(intelligence_data.get('career_analysis', {}), ensure_ascii=False),
         json.dumps(intelligence_data.get('benefits_analysis', {}), ensure_ascii=False),
         json.dumps(intelligence_data.get('visa_analysis', {}), ensure_ascii=False),
         json.dumps(intelligence_data.get('technology_analysis', {}), ensure_ascii=False),
         json.dumps(intelligence_data.get('recommendation', {}), ensure_ascii=False),
         json.dumps(scores, ensure_ascii=False),
         json.dumps(raw_source[:10000] if raw_source else '', ensure_ascii=False),
         now))

    conn.commit()
    conn.close()
    return company_id


def process_company(pid):
    """
    Full pipeline for company processing:
    1. Fetch     — fetch URL content from notes, combine all text
    2. Extract   — extract structured company data via mimo
    3. Analyze   — generate intelligence analysis via mimo
    4. Save      — write to DB (companies, company_intelligence)
    Done         — finalize
    """
    conn = _db()
    row = conn.execute('SELECT * FROM pending_companies WHERE id=?', (pid,)).fetchone()
    conn.close()
    if not row:
        return
    item = dict(row)

    # Parse notes (new multi-note system)
    notes_raw = item.get('notes', '[]')
    try:
        notes = json.loads(notes_raw) if isinstance(notes_raw, str) else notes_raw
    except (json.JSONDecodeError, TypeError):
        notes = []

    # Fallback to legacy input_text if no notes
    if not notes:
        input_text = item.get('input_text', '')
        note_type = 'url' if input_text.startswith('http') else 'text'
        notes = [{"type": note_type, "content": input_text}]

    try:
        note_summary = '; '.join([n.get('content', '')[:40] for n in notes[:3]])
        _log(pid, 'start', f'Processing {len(notes)} note(s): {note_summary}...')

        # ── Step 1: Fetch all URLs and combine all text ──
        _update_step(pid, 'step_fetch', 0, status='processing')
        _log(pid, 'fetch', f'Processing {len(notes)} note(s)...')

        all_content_parts = []
        url_count = 0
        for note in notes:
            ntype = note.get('type', 'text')
            content = note.get('content', '').strip()
            if not content:
                continue
            if ntype == 'url' or content.startswith('http'):
                try:
                    _log(pid, 'fetch', f'Fetching URL: {content[:60]}...')
                    fetched = _fetch_url(content)
                    all_content_parts.append(f"[SOURCE: {content}]\n{fetched}")
                    url_count += 1
                except Exception as e:
                    _log(pid, 'fetch', f'Warning: Failed to fetch {content[:40]}: {e}')
                    all_content_parts.append(f"[URL: {content}] (fetch failed: {e})")
            else:
                all_content_parts.append(f"[NOTE]\n{content}")

        raw_content = '\n\n---\n\n'.join(all_content_parts)

        if not raw_content.strip():
            raise RuntimeError("No content to process — all notes empty and all URLs failed")

        if _is_paused_or_stopped(pid):
            return
        _mark(pid, 'step_fetch')
        _log(pid, 'fetch', f'Collected {len(raw_content)} chars from {url_count} URL(s) + {len(notes) - url_count} text note(s)')

        # ── Step 2: Extract ──
        _update_step(pid, 'step_extract', 0, status='processing')
        _log(pid, 'extract', 'Extracting company information from all sources...')

        company_data = _extract_company_info(raw_content, 'multi_note', pid)
        if not company_data:
            raise RuntimeError("Failed to extract company information")

        if _is_paused_or_stopped(pid):
            return
        _mark(pid, 'step_extract')
        _log(pid, 'extract', f'Extracted: {company_data.get("name", "Unknown")} — {company_data.get("industry", "Unknown industry")}')

        # Update pending item with detected company name
        _update_step(pid, 'step_extract', 1, company_name=company_data.get('name', ''))

        # ── Step 3: Analyze ──
        _update_step(pid, 'step_analyze', 0, status='processing')
        _log(pid, 'analyze', 'Generating intelligence analysis...')

        intelligence_data = _analyze_company(company_data, pid)
        if not intelligence_data:
            raise RuntimeError("Failed to generate company intelligence")

        if _is_paused_or_stopped(pid):
            return
        _mark(pid, 'step_analyze')
        scores = intelligence_data.get('scores', {})
        _log(pid, 'analyze', f'Visa: {scores.get("visa_score", "?")} | Tech: {scores.get("tech_match", "?")} | Career: {scores.get("career_score", "?")} | Priority: {scores.get("priority", "?")}')

        # ── Step 4: Save ──
        _update_step(pid, 'step_save', 0, status='processing')
        _log(pid, 'save', 'Saving to database...')

        company_id = _save_company(company_data, intelligence_data, raw_content)

        if _is_paused_or_stopped(pid):
            return
        _mark(pid, 'step_save')
        _update_step(pid, 'step_save', 1, company_id=company_id)
        _log(pid, 'save', f'Saved company #{company_id}: {company_data.get("name", "Unknown")}')

        # ── Done ──
        _mark(pid, 'step_done')
        _update_step(pid, 'step_done', 1, status='done')
        _log(pid, 'done', f'Company intelligence complete: {company_data.get("name", "Unknown")}')

        print(f"[company_worker] Done: {company_data.get('name', 'Unknown')} (id={company_id})")

    except Exception as e:
        print(f"[company_worker] FAILED (pid={pid}): {e}")
        _fail(pid, str(e), step='pipeline')
