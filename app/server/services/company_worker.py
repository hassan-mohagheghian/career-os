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
import urllib.error
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
    # Map step keys to human-readable labels
    STEP_LABELS = {
        'fetch': 'Fetching content',
        'extract': 'Extracting company info',
        'analyze': 'Analyzing company',
        'save': 'Saving to database',
        'pipeline': 'Processing',
    }
    label = STEP_LABELS.get(step, step) if step else 'Processing'
    error_msg = f"[{label}] {msg}" if step else msg
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
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise RuntimeError(f"Page not found (404) — the URL does not exist or has been moved: {url}") from None
        elif e.code == 403:
            raise RuntimeError(f"Access denied (403) — the website is blocking automated requests: {url}") from None
        elif e.code == 503:
            raise RuntimeError(f"Service unavailable (503) — the website is temporarily down: {url}") from None
        else:
            raise RuntimeError(f"HTTP error {e.code}: {e.reason} — could not fetch: {url}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error — could not connect to the server. Check if the URL is correct and your internet is working: {url}") from None
    except Exception as e:
        raise RuntimeError(f"Failed to fetch URL: {e}") from None
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) < 50:
        raise RuntimeError(f"Page content too short ({len(text)} chars) — the URL may require login, be a JavaScript-rendered page, or is not a valid company page: {url}")
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
    if input_type == 'multi_note':
        content = input_text[:8000]
    elif input_type == 'manual':
        content = input_text[:6000]
    else:
        content = f"URL: {input_text}"
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
        except Exception as e:
            _log(pid, 'extract', f'Warning: Failed to parse extraction output: {e}')
    else:
        _log(pid, 'extract', f'Warning: mimo returned code {returncode}')
    return None


def _load_rules(context='company', company_type='UNKNOWN'):
    """Load enabled scoring rules from DB, filtered by context and company type.

    Args:
        context: 'company' loads SHARED + type-specific company rules.
        company_type: For 'company' context, selects type-specific rules by scope:
            - PRODUCT_COMPANY -> SHARED + COMPANY_PRODUCT rules
            - RECRUITING_AGENCY -> SHARED + COMPANY_RECRUITING rules
            - STAFFING_COMPANY -> SHARED + COMPANY_RECRUITING rules (merged)
            - CONSULTING_COMPANY / UNKNOWN -> SHARED + COMPANY_PRODUCT rules (default)

    Validation: Company processor must NEVER load JOB rules.
    """
    conn = _db()
    if context == 'company':
        # Map company_type to entity scope (new rule groups)
        scope_map = {
            'PRODUCT_COMPANY': 'COMPANY_PRODUCT',
            'RECRUITING_AGENCY': 'COMPANY_RECRUITING',
            'STAFFING_COMPANY': 'COMPANY_RECRUITING',
            'CONSULTING_COMPANY': 'COMPANY_PRODUCT',
            'UNKNOWN': 'COMPANY_PRODUCT',
        }
        entity_scope = scope_map.get(company_type, 'COMPANY_PRODUCT')
        rows = conn.execute(
            "SELECT category, scope, key, value, description, priority, score_weight "
            "FROM preferences WHERE enabled=1 AND scope IN ('SHARED', ?) "
            "ORDER BY priority DESC",
            (entity_scope,)
        ).fetchall()
    else:
        # Fallback: load SHARED + JOB (should not be used for company processing)
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


def _analyze_company(company_data, pid, company_type='UNKNOWN'):
    """Step 2: Generate full intelligence analysis using mimo."""
    output_file = os.path.join(TMP_DIR, f'company_analyze_{pid}.json')
    rules = _load_rules(context='company', company_type=company_type)
    prompt = load_prompt('company_analyze',
        company_data=json.dumps(company_data, ensure_ascii=False)[:4000],
        company_type=company_type,
        rules=rules,
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


def _save_company(company_data, intelligence_data, raw_source, notes=None):
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
        'notes': json.dumps(notes or [], ensure_ascii=False),
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
    1. Fetch     — fetch URL content from notes and links, combine all text
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

    # Get company_id from pending item or from company_name lookup
    company_id = item.get('company_id')

    # Reset link statuses for this company if company_id exists
    if company_id:
        try:
            conn = _db()
            conn.execute('UPDATE company_links SET status=?, extracted_content=?, updated_at=? WHERE company_id=?',
                       ('pending', '', datetime.now().isoformat(), company_id))
            conn.commit()
            conn.close()
        except:
            pass

    try:
        note_summary = '; '.join([n.get('content', '')[:40] for n in notes[:3]])
        _log(pid, 'start', f'Processing {len(notes)} note(s): {note_summary}...')

        # ── Step 1: Fetch all URLs and combine all text ──
        _update_step(pid, 'step_fetch', 0, status='processing')
        _log(pid, 'fetch', f'Processing {len(notes)} note(s)...')

        all_content_parts = []
        url_count = 0

        # Process notes (text content and inline URLs)
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

        # Process company links (from company_links table if company_id exists)
        if company_id:
            try:
                conn = _db()
                links = conn.execute('SELECT * FROM company_links WHERE company_id=?', (company_id,)).fetchall()
                conn.close()
                if links:
                    _log(pid, 'fetch', f'Processing {len(links)} company link(s)...')
                    for link in links:
                        link_dict = dict(link)
                        link_url = link_dict.get('url', '').strip()
                        if not link_url:
                            continue
                        link_title = link_dict.get('title', '') or ''
                        link_desc = link_dict.get('description', '') or ''
                        try:
                            _log(pid, 'fetch', f'Fetching link: {link_url[:60]}...')
                            fetched = _fetch_url(link_url)
                            header = f"[LINK: {link_url}]"
                            if link_title:
                                header += f" Title: {link_title}"
                            if link_desc:
                                header += f" - {link_desc}"
                            all_content_parts.append(f"{header}\n{fetched}")
                            url_count += 1
                            # Update link status to processed
                            try:
                                conn = _db()
                                conn.execute('UPDATE company_links SET status=?, extracted_content=?, updated_at=? WHERE id=?',
                                           ('processed', fetched[:5000], datetime.now().isoformat(), link_dict['id']))
                                conn.commit()
                                conn.close()
                            except:
                                pass
                        except Exception as e:
                            _log(pid, 'fetch', f'Warning: Failed to fetch link {link_url[:40]}: {e}')
                            all_content_parts.append(f"[LINK: {link_url}] (fetch failed: {e})")
                            # Update link status to failed
                            try:
                                conn = _db()
                                conn.execute('UPDATE company_links SET status=?, updated_at=? WHERE id=?',
                                           ('failed', datetime.now().isoformat(), link_dict['id']))
                                conn.commit()
                                conn.close()
                            except:
                                pass
            except Exception as e:
                _log(pid, 'fetch', f'Warning: Failed to process links: {e}')

        # Also process links from pending_companies.links (for new companies without company_id yet)
        try:
            pending_links_raw = item.get('links') or '[]'
            pending_links = json.loads(pending_links_raw) if isinstance(pending_links_raw, str) else pending_links_raw
            if pending_links:
                _log(pid, 'fetch', f'Processing {len(pending_links)} pending link(s)...')
                for link in pending_links:
                    link_url = link.get('url', '').strip()
                    if not link_url:
                        continue
                    link_title = link.get('title', '') or ''
                    link_desc = link.get('description', '') or ''
                    try:
                        _log(pid, 'fetch', f'Fetching pending link: {link_url[:60]}...')
                        fetched = _fetch_url(link_url)
                        header = f"[LINK: {link_url}]"
                        if link_title:
                            header += f" Title: {link_title}"
                        if link_desc:
                            header += f" - {link_desc}"
                        all_content_parts.append(f"{header}\n{fetched}")
                        url_count += 1
                    except Exception as e:
                        _log(pid, 'fetch', f'Warning: Failed to fetch pending link {link_url[:40]}: {e}')
                        all_content_parts.append(f"[LINK: {link_url}] (fetch failed: {e})")
        except Exception as e:
            _log(pid, 'fetch', f'Warning: Failed to process pending links: {e}')

        raw_content = '\n\n---\n\n'.join(all_content_parts)

        if not raw_content.strip():
            raise RuntimeError("No content to process — all notes were empty and all URLs failed to load. Check that the URLs are accessible and try again.")

        if _is_paused_or_stopped(pid):
            return
        _mark(pid, 'step_fetch')
        _log(pid, 'fetch', f'Collected {len(raw_content)} chars from {url_count} URL(s) + {len(notes) - url_count} text note(s)')

        # ── Step 2: Extract ──
        _update_step(pid, 'step_extract', 0, status='processing')
        _log(pid, 'extract', 'Extracting company information from all sources...')

        company_data = _extract_company_info(raw_content, 'multi_note', pid)
        if not company_data:
            raise RuntimeError("Could not extract company information from the provided content. The content may be too short, in an unsupported format, or the AI service may be temporarily unavailable.")

        if _is_paused_or_stopped(pid):
            return
        _mark(pid, 'step_extract')
        _log(pid, 'extract', f'Extracted: {company_data.get("name", "Unknown")} — {company_data.get("industry", "Unknown industry")}')

        # Update pending item with detected company name
        _update_step(pid, 'step_extract', 1, company_name=company_data.get('name', ''))

        # Detect company type for type-specific scoring
        company_type = company_data.get('company_type', 'UNKNOWN')
        _log(pid, 'extract', f'Company type detected: {company_type}')

        # ── Step 3: Analyze ──
        _update_step(pid, 'step_analyze', 0, status='processing')
        _log(pid, 'analyze', f'Generating intelligence analysis (rules: {company_type})...')

        intelligence_data = _analyze_company(company_data, pid, company_type=company_type)
        if not intelligence_data:
            raise RuntimeError("AI analysis failed — the analysis service may be temporarily unavailable or the company data was too complex to process. You can retry this step.")

        if _is_paused_or_stopped(pid):
            return
        _mark(pid, 'step_analyze')
        scores = intelligence_data.get('scores', {})
        _log(pid, 'analyze', f'Fit: {scores.get("company_fit_score", "?")} | Success: {scores.get("company_success_score", "?")} | Overall: {scores.get("company_overall_score", "?")} | Grade: {scores.get("overall_grade", "?")}')

        # ── Step 4: Save ──
        _update_step(pid, 'step_save', 0, status='processing')
        _log(pid, 'save', 'Saving to database...')

        company_id = _save_company(company_data, intelligence_data, raw_content, notes=notes)

        # Move links from pending_companies to company_links
        try:
            pending_links_raw = item.get('links') or '[]'
            pending_links = json.loads(pending_links_raw) if isinstance(pending_links_raw, str) else pending_links_raw
            if pending_links and company_id:
                conn = _db()
                for link in pending_links:
                    url = link.get('url', '').strip()
                    if not url:
                        continue
                    title = link.get('title', '') or ''
                    desc = link.get('description', '') or ''
                    conn.execute('INSERT INTO company_links (company_id, url, title, description, status) VALUES (?,?,?,?,?)',
                                 (company_id, url, title, desc, 'pending'))
                conn.commit()
                conn.close()
                _log(pid, 'save', f'Saved {len(pending_links)} link(s) to company_links')
        except Exception as e:
            _log(pid, 'save', f'Warning: Failed to save pending links: {e}')

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
        # Detect which step was active when the error occurred
        step_labels = {
            'step_fetch': 'fetch',
            'step_extract': 'extract',
            'step_analyze': 'analyze',
            'step_save': 'save',
        }
        failed_step = 'pipeline'
        conn = _db()
        row = conn.execute('SELECT step_fetch, step_extract, step_analyze, step_save FROM pending_companies WHERE id=?', (pid,)).fetchone()
        conn.close()
        if row:
            row = dict(row)
            for step_key, step_name in step_labels.items():
                if row.get(step_key) == 0 and all(row.get(k) == 1 for k in list(step_labels.keys())[:list(step_labels.keys()).index(step_key)]):
                    failed_step = step_name
                    break
        _fail(pid, str(e), step=failed_step)
