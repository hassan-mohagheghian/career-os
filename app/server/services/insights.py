"""
Career Intelligence service — generates actionable insights from jobs, companies,
skills, and market data. Each section can be refreshed independently.
Only one analysis can run at a time (concurrency lock).
"""
import json
import os
import sqlite3
import subprocess
import threading
import time
import traceback
from datetime import datetime

from core.db import get_db
from prompts import load_prompt

_socketio = None  # set by app.py after SocketIO init


def set_socketio(sio):
    global _socketio
    _socketio = sio

_file_dir = os.path.dirname(os.path.abspath(__file__))
_server_dir = os.path.join(_file_dir, '..')
PROJECT_ROOT = os.path.abspath(os.path.join(_file_dir, '..', '..'))
MIMO_BIN = os.path.expanduser('~/.mimocode/bin/mimo')
_tmp = os.environ.get('TEMP_DIR', 'tmp')
TMP_DIR = _tmp if os.path.isabs(_tmp) else os.path.join(PROJECT_ROOT, _tmp)
os.makedirs(TMP_DIR, exist_ok=True)

INSIGHT_TYPES = ['overview', 'opportunities', 'companies', 'skills', 'market', 'networking', 'skills_intel']
CURRENT_VERSION = 1

# Per-section prompt mapping
# Values are prompt names WITHOUT the insights/ prefix (added by _run_mimo_prompt)
# 'skills' maps to skills_intelligence (full report), not the minimal skills section in the combined prompt
SECTION_PROMPTS = {
    'overview': 'overview_intelligence',
    'opportunities': 'opportunities_intelligence',
    'companies': 'companies_intelligence',
    'skills_intel': 'skills_intelligence',
    'market': 'market_intelligence',
    'networking': 'networking_intelligence',
}

# Concurrency lock — only one analysis at a time
_analysis_lock = threading.Lock()
_current_run = {'active': False, 'type': None, 'started_at': None, 'run_id': None, 'process': None, 'session_id': None}
_cancel_requested = False


def _db():
    return get_db()


def _emit_progress(progress_data):
    """Emit progress update via SocketIO to the insights room."""
    if _socketio is not None:
        try:
            # Always include session_id if available
            sid = _current_run.get('session_id')
            if sid:
                progress_data['session_id'] = sid
            _socketio.emit('insights:progress', progress_data, room='insights')
        except Exception:
            pass


def _cleanup_stale_runs():
    """Mark any processing runs older than 5 minutes as failed (stale from crashed sessions)."""
    from datetime import timedelta
    for attempt in range(3):
        try:
            conn = _db()
            cutoff = (datetime.now() - timedelta(minutes=5)).isoformat()
            conn.execute(
                "UPDATE career_insight_runs SET status='failed', error_message='Stale run cleaned up', completed_at=? WHERE status='processing' AND started_at < ?",
                (datetime.now().isoformat(), cutoff)
            )
            conn.commit()
            conn.close()
            return
        except sqlite3.OperationalError as e:
            if 'locked' in str(e) and attempt < 2:
                time.sleep(0.5 * (attempt + 1))
            else:
                return  # non-fatal, just skip cleanup


def is_running():
    """Check if an analysis is currently running. Returns (bool, info_dict)."""
    if _current_run['active']:
        return True, {
            'type': _current_run['type'],
            'started_at': _current_run['started_at'],
            'run_id': _current_run['run_id'],
            'session_id': _current_run.get('session_id'),
            'cancellable': _current_run['process'] is not None
        }
    # Clean up stale processing records from crashed sessions
    _cleanup_stale_runs()
    # Also check DB for any recent in-progress runs
    conn = _db()
    row = conn.execute(
        "SELECT id, insight_type, started_at FROM career_insight_runs WHERE status='processing' ORDER BY started_at DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if row:
        # row is a tuple (id, insight_type, started_at) since row_factory=None
        return True, {
            'type': row[1],
            'started_at': row[2],
            'run_id': row[0],
            'cancellable': False
        }
    return False, None


def get_progress():
    """Get current analysis progress info."""
    running, info = is_running()
    if not running:
        return {'running': False, 'status': 'idle'}
    # Calculate elapsed time
    started = info.get('started_at')
    elapsed = None
    if started:
        try:
            start_dt = datetime.fromisoformat(started)
            elapsed = int((datetime.now() - start_dt).total_seconds())
        except:
            pass
    return {
        'running': True,
        'status': 'processing',
        'type': info['type'],
        'started_at': info['started_at'],
        'elapsed_seconds': elapsed,
        'run_id': info['run_id'],
        'session_id': info.get('session_id'),
        'cancellable': info.get('cancellable', False)
    }


def cancel_run():
    """Cancel the current running analysis. Returns True if cancelled."""
    global _cancel_requested
    # Cancel in-memory process if active
    if _current_run['active']:
        run_id = _current_run.get('run_id')
        _cancel_requested = True
        # Try to kill via ProcessManager (MimoRunner manages processes here)
        try:
            from services.process.process_manager import ProcessManager
            proc_type = _current_run.get('type', '')
            proc_key = _current_run.get('process_key')
            if proc_key:
                handle = ProcessManager().get(proc_key)
                if handle:
                    ProcessManager().cancel(handle)
        except Exception:
            pass
        # Fallback: kill raw process if stored
        proc = _current_run.get('process')
        if proc and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except:
                try:
                    proc.kill()
                except:
                    pass
        if run_id:
            _complete_run(run_id, 'cancelled', 'Cancelled by user')
        _emit_progress({'running': False, 'status': 'cancelled', 'type': _current_run.get('type'), 'run_id': run_id})
        print(f"[insights] Run {run_id} cancelled")
        return True
    # Also handle stale DB records (from crashed sessions)
    conn = _db()
    row = conn.execute(
        "SELECT id FROM career_insight_runs WHERE status='processing' ORDER BY started_at DESC LIMIT 1"
    ).fetchone()
    if row:
        _complete_run(row[0], 'cancelled', 'Cancelled by user (stale)')
        _emit_progress({'running': False, 'status': 'cancelled', 'run_id': row[0]})
        conn.close()
        print(f"[insights] Stale run {row[0]} cancelled")
        return True
    conn.close()
    return False


def _start_run(insight_type):
    """Create a career_insight_runs row and return its id."""
    conn = _db()
    cur = conn.execute(
        "INSERT INTO career_insight_runs (insight_type, version, status, started_at) VALUES (?, ?, 'processing', ?)",
        (insight_type, CURRENT_VERSION, datetime.now().isoformat())
    )
    run_id = cur.lastrowid
    conn.commit()
    conn.close()
    return run_id


def _complete_run(run_id, status='completed', error=None, session_id=None):
    conn = _db()
    if session_id:
        conn.execute(
            "UPDATE career_insight_runs SET status=?, completed_at=?, error_message=?, session_id=? WHERE id=?",
            (status, datetime.now().isoformat(), error, session_id, run_id)
        )
    else:
        conn.execute(
            "UPDATE career_insight_runs SET status=?, completed_at=?, error_message=? WHERE id=?",
            (status, datetime.now().isoformat(), error, run_id)
        )
    conn.commit()
    conn.close()


def _save_session_id(run_id, session_id):
    """Save session_id to DB immediately when discovered (for crash recovery)."""
    if not run_id or not session_id:
        return
    try:
        conn = _db()
        conn.execute("UPDATE career_insight_runs SET session_id=? WHERE id=?", (session_id, run_id))
        conn.commit()
        conn.close()
    except Exception:
        pass


def _save_insight(insight_type, data, score=None, summary=None):
    """Save generated insight to career_insights table."""
    conn = _db()
    conn.execute(
        "INSERT INTO career_insights (insight_type, version, score, summary, data_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (insight_type, CURRENT_VERSION, score, summary, json.dumps(data, ensure_ascii=False), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def _parse_session_id(stdout):
    """Extract sessionID from Mimo JSON stream output."""
    if not stdout:
        return None
    decoded = stdout.decode('utf-8', errors='replace')
    for line in decoded.split('\n'):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            # Try multiple possible keys
            sid = obj.get('sessionID') or obj.get('session_id') or obj.get('sessionId')
            if sid:
                return sid
            # Also check nested objects
            if 'session' in obj and isinstance(obj['session'], dict):
                sid = obj['session'].get('id') or obj['session'].get('ID')
                if sid:
                    return sid
        except (json.JSONDecodeError, AttributeError):
            continue
    return None


def _run_mimo_prompt(prompt_name, pid=0, timeout=600, result_file=None, previous_session_id=None, **kwargs):
    """Run a mimo analysis prompt and return (result, error_message, session_id). Supports cancellation."""
    global _cancel_requested
    prompt = load_prompt(f'insights/{prompt_name}', project_root=PROJECT_ROOT, tmp_dir=TMP_DIR, pid=pid, **kwargs)
    if result_file is None:
        result_file = os.path.join(TMP_DIR, f'insights_{pid}.json')
    session_id = None
    job_key = f'insights_{prompt_name}_{pid}'
    _current_run['process_key'] = job_key
    try:
        from services.process.mimo_runner import MimoRunner
        from services.process.process_manager import ProcessManager
        mimo = MimoRunner(ProcessManager())

        def _on_session_id(sid):
            nonlocal session_id
            session_id = sid
            _current_run['session_id'] = sid
            # Save to DB immediately for crash recovery
            _save_session_id(_current_run.get('run_id'), sid)
            _emit_progress({'running': True, 'status': 'processing', 'session_id': sid})

        def _on_event(evt):
            etype = evt.get('type', '')
            if etype == 'text':
                text = evt.get('part', {}).get('text', '')
                if text:
                    _emit_progress({'running': True, 'status': 'processing', 'message': f"AI: {text[:120]}"})

        returncode, output_lines, session_id = mimo.run(
            prompt, timeout=timeout, key=f'insights_{prompt_name}_{pid}',
            session_id=previous_session_id,
            on_event=_on_event, on_session_id=_on_session_id,
        )

        if _cancel_requested:
            return None, None, session_id

        if returncode == 0 and os.path.exists(result_file):
            with open(result_file) as f:
                result = json.load(f)
            try:
                os.remove(result_file)
            except OSError:
                pass
            return result, None, session_id
        else:
            err = f'Exit code {returncode}' if returncode != 0 else 'Mimo returned no result file'
            return None, err, session_id
    except Exception as e:
        return None, str(e), session_id
    finally:
        _current_run['process'] = None
        _current_run['process_key'] = None


def _collect_jobs_data():
    """Collect summarized job data for the prompt (avoids passing raw DB)."""
    conn = _db()
    rows = conn.execute(
        "SELECT num, company, role, location, score, match, fit_score, success_score, overall_score, "
        "stack, visa, work_type, employment_type, posted, applicants "
        "FROM jobs WHERE deleted=0 ORDER BY overall_score DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows] if rows else []


def _collect_companies_data():
    conn = _db()
    rows = conn.execute(
        "SELECT c.id, c.name, c.industry, c.company_type, c.country, c.city, c.skills, "
        "c.funding_stage, c.company_size, "
        "(SELECT COUNT(*) FROM jobs j WHERE j.company=c.name AND j.deleted=0) as job_count "
        "FROM companies c ORDER BY job_count DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows] if rows else []


def _collect_skills_data():
    conn = _db()
    stack = conn.execute("SELECT * FROM skills ORDER BY level DESC").fetchall()
    learning = conn.execute("SELECT * FROM tech_learning ORDER BY priority").fetchall()
    conn.close()
    return {
        'techStack': [dict(r) for r in stack] if stack else [],
        'techLearning': [dict(r) for r in learning] if learning else [],
    }


def generate_skills_intel(pid=0):
    """Generate the Skills Intelligence Report using the dedicated prompt. Only one run at a time."""
    global _cancel_requested
    if not _analysis_lock.acquire(blocking=False):
        running, info = is_running()
        print(f"[insights] Analysis already running: {info}")
        return {'error': 'Analysis already running', 'running': info}
    try:
        _cancel_requested = False
        _current_run['active'] = True
        _current_run['type'] = 'skills_intel'
        _current_run['started_at'] = datetime.now().isoformat()
        run_id = _start_run('skills_intel')
        _current_run['run_id'] = run_id
        _emit_progress({
            'running': True, 'status': 'processing', 'type': 'skills_intel',
            'started_at': _current_run['started_at'], 'run_id': run_id,
        })

        # Read previous session_id for retry resumption
        prev_sid = None
        try:
            conn = _db()
            row = conn.execute(
                "SELECT session_id FROM career_insight_runs WHERE insight_type='skills_intel' AND session_id IS NOT NULL ORDER BY started_at DESC LIMIT 1"
            ).fetchone()
            if row and row[0]:
                prev_sid = row[0]
            conn.close()
        except Exception:
            pass

        section_data, error_msg, session_id = _generate_section_internal(
            'skills_intel', pid=pid, timeout=900, previous_session_id=prev_sid,
        )
        if session_id:
            _current_run['session_id'] = session_id

        if section_data:
            _complete_run(run_id, 'completed', session_id=session_id)
            _emit_progress({'running': False, 'status': 'completed', 'type': 'skills_intel', 'run_id': run_id})
            print(f"[insights] Skills intelligence generated successfully (session: {session_id})")
            return section_data

        _complete_run(run_id, 'failed', error_msg or 'Mimo analysis returned no result', session_id=session_id)
        _emit_progress({'running': False, 'status': 'failed', 'type': 'skills_intel', 'error': error_msg, 'run_id': run_id})
        print(f"[insights] Skills intelligence generation failed: {error_msg}")
        return None
    except Exception as e:
        if not _cancel_requested:
            _complete_run(run_id, 'failed', str(e))
        print(f"[insights] Error: {e}")
        traceback.print_exc()
        return None
    finally:
        _current_run['active'] = False
        _current_run['type'] = None
        _current_run['started_at'] = None
        _current_run['run_id'] = None
        _current_run['process'] = None
        _analysis_lock.release()


def _normalize_skill_name(name):
    """Normalize a skill name for deduplication: lowercase, strip whitespace, collapse spaces."""
    if not name:
        return name
    return ' '.join(name.strip().lower().split())


def _resolve_skill_name(conn, name):
    """Resolve a skill name to its canonical form via skill_aliases."""
    normalized = _normalize_skill_name(name)
    # Check if this name is an alias
    alias_row = conn.execute(
        "SELECT ts.name FROM skill_aliases sa JOIN skills ts ON ts.id=sa.skill_id "
        "WHERE LOWER(sa.alias_name)=?", (normalized,)
    ).fetchone()
    if alias_row:
        return alias_row[0]
    # Check exact match
    exact = conn.execute("SELECT name FROM skills WHERE name=?", (name,)).fetchone()
    if exact:
        return exact[0]
    # Check case-insensitive match
    ci = conn.execute("SELECT name FROM skills WHERE LOWER(name)=?", (normalized,)).fetchone()
    if ci:
        return ci[0]
    return name


def _fill_skills_from_insights(result):
    """Parse AI insights report and fill skills into skills + skill_relationships."""
    if not result:
        return

    try:
        conn = _db()
        current_state = result.get('current_state', {})
        recommendations = result.get('recommendations', [])
        relationships = result.get('relationships', [])

        # 1. Update existing skills with AI-derived data
        all_ai_skills = current_state.get('strengths', []) + current_state.get('gaps', []) + current_state.get('maintain', [])
        for skill_data in all_ai_skills:
            name = skill_data.get('skill', '')
            if not name:
                continue
            # Resolve to canonical name (handles aliases)
            canonical = _resolve_skill_name(conn, name)
            market_demand = skill_data.get('market_demand', 0)
            confidence = skill_data.get('confidence', 0)
            evidence = json.dumps(skill_data.get('evidence', []))
            category = skill_data.get('category', '')

            # Try to update existing skill
            row = conn.execute("SELECT id FROM skills WHERE name=?", (canonical,)).fetchone()
            if row:
                updates = []
                params = []
                if market_demand and market_demand > 0:
                    updates.append("market_relevance=?")
                    params.append(market_demand)
                if confidence and confidence > 0:
                    updates.append("confidence=?")
                    params.append(confidence)
                if evidence and evidence != '[]':
                    updates.append("evidence=?")
                    params.append(evidence)
                if category:
                    updates.append("category=?")
                    params.append(category)
                if updates:
                    params.append(canonical)
                    conn.execute(f"UPDATE skills SET {', '.join(updates)} WHERE name=?", params)

        # 2. Add new skills from recommendations that don't exist in skills
        for rec in recommendations:
            name = rec.get('skill', '')
            if not name:
                continue
            canonical = _resolve_skill_name(conn, name)
            existing = conn.execute("SELECT id FROM skills WHERE name=?", (canonical,)).fetchone()
            if not existing:
                category = rec.get('category', 'technical')
                confidence = rec.get('confidence', 0.5)
                market_demand = rec.get('market_demand', 0)
                evidence = json.dumps(rec.get('evidence', []))
                conn.execute(
                    "INSERT INTO skills (name, level, source, source_type, category, confidence, market_relevance, evidence) "
                    "VALUES (?, 1, 'service', 'ai_generated', ?, ?, ?, ?)",
                    (canonical, category, confidence, market_demand, evidence)
                )
                print(f"[insights] Added new skill: {canonical}")

        # 3. Create skill relationships
        for rel in relationships:
            skill_name = rel.get('skill', '')
            related_name = rel.get('related', '')
            rel_type = rel.get('type', 'related')
            confidence = rel.get('confidence', 0.5)
            if not skill_name or not related_name:
                continue
            # Resolve both names
            skill_name = _resolve_skill_name(conn, skill_name)
            related_name = _resolve_skill_name(conn, related_name)
            # Check if relationship already exists
            existing = conn.execute(
                "SELECT id FROM skill_relationships WHERE skill_name=? AND related_name=? AND relation_type=?",
                (skill_name, related_name, rel_type)
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT OR IGNORE INTO skill_relationships (skill_name, related_name, relation_type, confidence) VALUES (?, ?, ?, ?)",
                    (skill_name, related_name, rel_type, confidence)
                )

        # 4. Auto-create aliases from AI-reported synonyms/variants
        for skill_data in all_ai_skills:
            name = skill_data.get('skill', '')
            if not name:
                continue
            canonical = _resolve_skill_name(conn, name)
            canonical_row = conn.execute("SELECT id FROM skills WHERE name=?", (canonical,)).fetchone()
            if not canonical_row:
                continue
            # If the original name differs from canonical, create an alias
            if name != canonical:
                existing_alias = conn.execute(
                    "SELECT id FROM skill_aliases WHERE skill_id=? AND alias_name=?",
                    (canonical_row[0], name)
                ).fetchone()
                if not existing_alias:
                    conn.execute(
                        "INSERT OR IGNORE INTO skill_aliases (skill_id, alias_name, normalized_name) VALUES (?, ?, ?)",
                        (canonical_row[0], name, _normalize_skill_name(name))
                    )

        conn.commit()
        conn.close()
        print(f"[insights] Skills DB filled from insights report")
    except Exception as e:
        print(f"[insights] Error filling skills from insights: {e}")


def _generate_section_internal(section, pid=0, timeout=600, previous_session_id=None):
    """Run a single section's dedicated prompt and save to DB. No lock management.

    Returns (section_data, error_msg, session_id) or (None, error_msg, session_id).
    """
    if _cancel_requested:
        return None, 'Cancelled', None

    prompt_name = SECTION_PROMPTS.get(section)
    if not prompt_name:
        return None, f'No prompt for section: {section}', None

    result_file = os.path.join(TMP_DIR, f'{section}_intelligence_{pid}.json')
    result, error_msg, session_id = _run_mimo_prompt(
        prompt_name, pid=pid, result_file=result_file, timeout=timeout,
        previous_session_id=previous_session_id,
    )

    if _cancel_requested:
        return None, 'Cancelled', session_id

    if not result:
        return None, error_msg or f'Mimo returned no result for {section}', session_id

    # Per-section prompts output flat JSON — save directly
    score = None
    summary = None
    if section == 'overview':
        score = result.get('careerHealthScore', {}).get('overall')
        summary = f"Career readiness: {score}/100"
    elif section == 'skills_intel':
        score = result.get('summary', {}).get('career_readiness_score')
        parts = []
        if result.get('summary', {}).get('main_strength'):
            parts.append(f"Strength: {result['summary']['main_strength']}")
        if result.get('summary', {}).get('biggest_gap'):
            parts.append(f"Gap: {result['summary']['biggest_gap']}")
        summary = '; '.join(parts) if parts else f"Readiness: {score}/100"
    _save_insight(section, result, score, summary)

    # Fill skills into skills and skill_relationships from AI report
    if section == 'skills_intel':
        _fill_skills_from_insights(result)

    print(f"[insights] {section} saved to DB (session: {session_id})")
    return result, None, session_id


def generate_all(pid=0):
    """Generate all insights sections using each section's dedicated prompt.

    Runs sequentially: overview → opportunities → companies → market → networking → skills_intel.
    Each section uses its own focused prompt for better quality.
    If one section fails, continues with the rest.
    """
    global _cancel_requested
    if not _analysis_lock.acquire(blocking=False):
        running, info = is_running()
        print(f"[insights] Analysis already running: {info}")
        return {'error': 'Analysis already running', 'running': info}
    try:
        _cancel_requested = False
        _current_run['active'] = True
        _current_run['type'] = 'all'
        _current_run['started_at'] = datetime.now().isoformat()
        run_id = _start_run('all')
        _current_run['run_id'] = run_id
        _emit_progress({
            'running': True, 'status': 'processing', 'type': 'all',
            'started_at': _current_run['started_at'], 'run_id': run_id,
        })

        # Sections to generate in order (skills has its own independent flow)
        sections = ['overview', 'opportunities', 'companies', 'market', 'networking']
        results = {}
        errors = []
        last_session_id = None

        # Read previous session_ids for retry resumption
        prev_sessions = {}
        try:
            conn = _db()
            for section in sections:
                row = conn.execute(
                    "SELECT session_id FROM career_insight_runs WHERE insight_type=? AND session_id IS NOT NULL ORDER BY started_at DESC LIMIT 1",
                    (section,)
                ).fetchone()
                if row and row[0]:
                    prev_sessions[section] = row[0]
            conn.close()
        except Exception:
            pass

        for section in sections:
            if _cancel_requested:
                print(f"[insights] All sections generation cancelled at {section}")
                break

            _emit_progress({
                'running': True, 'status': 'processing', 'type': 'all',
                'section': section, 'message': f'Generating {section}...',
            })

            timeout = 900 if section == 'skills_intel' else 600
            prev_sid = prev_sessions.get(section)
            section_data, err, sid = _generate_section_internal(section, pid=pid, timeout=timeout, previous_session_id=prev_sid)
            if sid:
                last_session_id = sid
                _current_run['session_id'] = sid

            if section_data:
                results[section] = section_data
            elif err and err != 'Cancelled':
                errors.append(f'{section}: {err}')
                print(f"[insights] {section} failed: {err}")

        if _cancel_requested:
            _complete_run(run_id, 'cancelled', session_id=last_session_id)
            _emit_progress({'running': False, 'status': 'cancelled', 'type': 'all', 'run_id': run_id})
            print(f"[insights] All sections generation cancelled")
            return None

        if not results:
            # All sections failed
            _complete_run(run_id, 'failed', error=f'All failed: {"; ".join(errors)}', session_id=last_session_id)
            _emit_progress({'running': False, 'status': 'failed', 'type': 'all', 'error': errors[0] if errors else 'All sections failed', 'run_id': run_id})
        elif errors:
            # Some succeeded, some failed
            _complete_run(run_id, 'completed', error=f'Partial: {"; ".join(errors)}', session_id=last_session_id)
            _emit_progress({
                'running': False, 'status': 'completed', 'type': 'all', 'run_id': run_id,
                'message': f'Completed with {len(errors)} error(s)',
            })
        else:
            _complete_run(run_id, 'completed', session_id=last_session_id)
            _emit_progress({'running': False, 'status': 'completed', 'type': 'all', 'run_id': run_id})

        print(f"[insights] All sections generated: {len(results)}/{len(sections)} succeeded "
              f"(errors: {len(errors)}, session: {last_session_id})")
        return results if results else None

    except Exception as e:
        if not _cancel_requested:
            _complete_run(run_id, 'failed', str(e))
        print(f"[insights] Error: {e}")
        traceback.print_exc()
        return None
    finally:
        _current_run['active'] = False
        _current_run['type'] = None
        _current_run['started_at'] = None
        _current_run['run_id'] = None
        _current_run['process'] = None
        _analysis_lock.release()


def generate_section(section, pid=0):
    """Generate a single insights section. Only one run at a time."""
    if section in ('skills', 'skills_intel'):
        return generate_skills_intel(pid)
    if section not in SECTION_PROMPTS:
        return None
    global _cancel_requested
    if not _analysis_lock.acquire(blocking=False):
        running, info = is_running()
        print(f"[insights] Analysis already running: {info}")
        return {'error': 'Analysis already running', 'running': info}
    try:
        _cancel_requested = False
        _current_run['active'] = True
        _current_run['type'] = section
        _current_run['started_at'] = datetime.now().isoformat()
        run_id = _start_run(section)
        _current_run['run_id'] = run_id
        _emit_progress({
            'running': True, 'status': 'processing', 'type': section,
            'started_at': _current_run['started_at'], 'run_id': run_id,
        })

        # Read previous session_id for retry resumption
        prev_sid = None
        try:
            conn = _db()
            row = conn.execute(
                "SELECT session_id FROM career_insight_runs WHERE insight_type=? AND session_id IS NOT NULL ORDER BY started_at DESC LIMIT 1",
                (section,)
            ).fetchone()
            if row and row[0]:
                prev_sid = row[0]
            conn.close()
        except Exception:
            pass

        section_data, error_msg, session_id = _generate_section_internal(section, pid=pid, previous_session_id=prev_sid)
        if session_id:
            _current_run['session_id'] = session_id

        if section_data:
            _complete_run(run_id, 'completed', session_id=session_id)
            _emit_progress({'running': False, 'status': 'completed', 'type': section, 'run_id': run_id})
            print(f"[insights] {section} generated successfully (session: {session_id})")
            return section_data

        _complete_run(run_id, 'failed', error_msg or f'Mimo analysis failed for {section}', session_id=session_id)
        _emit_progress({'running': False, 'status': 'failed', 'type': section, 'error': error_msg, 'run_id': run_id})
        return None
    except Exception as e:
        if not _cancel_requested:
            _complete_run(run_id, 'failed', str(e))
        print(f"[insights] Error generating {section}: {e}")
        return None
    finally:
        _current_run['active'] = False
        _current_run['type'] = None
        _current_run['started_at'] = None
        _current_run['run_id'] = None
        _current_run['process'] = None
        _analysis_lock.release()


def get_latest(insight_type=None):
    """Get the latest career insight(s)."""
    conn = _db()
    conn.row_factory = None
    cols = ['id', 'insight_type', 'version', 'score', 'summary', 'data_json', 'created_at']
    if insight_type:
        row = conn.execute(
            f"SELECT {', '.join(cols)} FROM career_insights WHERE insight_type=? ORDER BY created_at DESC LIMIT 1",
            (insight_type,)
        ).fetchone()
        conn.close()
        if row:
            r = dict(zip(cols, row))
            r['data'] = json.loads(r['data_json'])
            del r['data_json']
            return r
        return None
    else:
        results = {}
        for it in INSIGHT_TYPES:
            row = conn.execute(
                f"SELECT {', '.join(cols)} FROM career_insights WHERE insight_type=? ORDER BY created_at DESC LIMIT 1",
                (it,)
            ).fetchone()
            if row:
                r = dict(zip(cols, row))
                r['data'] = json.loads(r['data_json'])
                del r['data_json']
                results[it] = r
        conn.close()
        return results


def get_runs(insight_type=None, limit=10, offset=0):
    """Get recent insight generation runs with total count for infinite scroll."""
    conn = _db()
    conn.row_factory = None
    cols = ['id', 'insight_type', 'version', 'status', 'started_at', 'completed_at', 'error_message', 'session_id']
    if insight_type:
        total = conn.execute(
            f"SELECT COUNT(*) FROM career_insight_runs WHERE insight_type=?", (insight_type,)
        ).fetchone()[0]
        rows = conn.execute(
            f"SELECT {', '.join(cols)} FROM career_insight_runs WHERE insight_type=? ORDER BY started_at DESC LIMIT ? OFFSET ?",
            (insight_type, limit, offset)
        ).fetchall()
    else:
        total = conn.execute("SELECT COUNT(*) FROM career_insight_runs").fetchone()[0]
        rows = conn.execute(
            f"SELECT {', '.join(cols)} FROM career_insight_runs ORDER BY started_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
    conn.close()
    return {'items': [dict(zip(cols, r)) for r in rows] if rows else [], 'total': total}
