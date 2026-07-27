"""Skill Roadmap service — generates learning roadmaps for individual skills.

SRP: Only handles skill roadmap generation, extension, and fine-graining.
OCP: New roadmap operations can be added without modifying existing code.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import time
import threading
import traceback
from datetime import datetime

from core.db import get_db
from prompts import load_prompt
from ai_compat import get_llm_service
from infrastructure.websocket.broadcaster import WebSocketBroadcaster

_file_dir = os.path.dirname(os.path.abspath(__file__))
_server_dir = os.path.join(_file_dir, '..')
PROJECT_ROOT = os.path.abspath(os.path.join(_file_dir, '..', '..'))
_tmp = os.environ.get('TEMP_DIR', 'tmp')
TMP_DIR = _tmp if os.path.isabs(_tmp) else os.path.join(PROJECT_ROOT, _tmp)
os.makedirs(TMP_DIR, exist_ok=True)

TOTAL_STEPS = 4
_broadcaster = WebSocketBroadcaster()


def _db():
    return get_db()


def _emit_skill_update(skill_name: str, data: dict):
    """Emit a skill_roadmap:update event to the skills room.

    Uses WebSocketBroadcaster which handles the async bridge correctly
    even when called from sync threads (run_in_executor).
    """
    payload = {"skill": skill_name, **data}
    _broadcaster._emit('skill_roadmap:update', payload, room='skills')


def _create_job(skill_name: str, job_type: str) -> int:
    """Insert a new job row and return its ID."""
    conn = _db()
    cur = conn.execute(
        "INSERT INTO skill_roadmap_jobs (skill_name, job_type, status, started_at) VALUES (?, ?, 'running', ?)",
        (skill_name, job_type, datetime.now().isoformat()),
    )
    job_id = cur.lastrowid
    conn.commit()
    conn.close()
    return job_id


def _update_job(job_id: int, **kwargs):
    """Update a job row with arbitrary fields."""
    if not kwargs:
        return
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [job_id]
    conn = _db()
    conn.execute(f"UPDATE skill_roadmap_jobs SET {sets} WHERE id=?", vals)
    conn.commit()
    conn.close()


def _get_provider_name() -> str:
    """Get the active AI provider name."""
    try:
        from ai.providers import get_provider
        return get_provider().name
    except Exception:
        return "unknown"


def _get_checked_items(skill_name: str) -> list[str]:
    """Get list of completed roadmap item titles for a skill."""
    conn = _db()
    rows = conn.execute(
        "SELECT sr.title FROM skill_roadmap_progress sp "
        "JOIN skill_roadmaps sr ON sr.id = sp.roadmap_id "
        "WHERE sp.skill_name = ? AND sp.completed = 1",
        (skill_name,),
    ).fetchall()
    conn.close()
    return [r[0] for r in rows] if rows else []


def _get_current_level(skill_name: str) -> str:
    """Determine the user's current level for a skill."""
    conn = _db()
    row = conn.execute(
        "SELECT level FROM skills WHERE LOWER(name) = LOWER(?)",
        (skill_name,),
    ).fetchone()
    conn.close()
    if row and row[0]:
        level = row[0]
        if level >= 80:
            return "Expert"
        elif level >= 60:
            return "Advanced"
        elif level >= 40:
            return "Intermediate"
        elif level >= 20:
            return "Basic"
    return "Beginner"


def _get_existing_roadmap(skill_name: str) -> list[dict]:
    """Get existing roadmap items as a flat list."""
    conn = _db()
    rows = conn.execute(
        "SELECT id, parent_id, title, description, level, sort_order FROM skill_roadmaps "
        "WHERE LOWER(skill_name) = LOWER(?) ORDER BY sort_order, id",
        (skill_name,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows] if rows else []


def _flatten_tree(items: list[dict]) -> list[dict]:
    """Convert tree nodes to JSON-serialisable list for prompts."""
    result = []
    for item in items:
        node = {
            "title": item.get("title", ""),
            "description": item.get("description", ""),
            "level": item.get("level", 0),
        }
        children = item.get("children", [])
        if children:
            node["children"] = _flatten_tree(children)
        else:
            node["children"] = []
        result.append(node)
    return result


def _build_tree(flat_rows: list[dict]) -> list[dict]:
    """Build a nested tree from flat rows with parent_id."""
    nodes_by_id = {}
    for r in flat_rows:
        node = dict(r)
        node["children"] = []
        nodes_by_id[node["id"]] = node

    roots = []
    for node in nodes_by_id.values():
        parent_id = node.get("parent_id")
        if parent_id and parent_id in nodes_by_id:
            nodes_by_id[parent_id]["children"].append(node)
        else:
            roots.append(node)
    return roots


def _save_roadmap_items(skill_name: str, items: list[dict], version: int):
    """Save generated roadmap items to DB (replaces existing for this version)."""
    conn = _db()
    # Delete old items for this skill
    conn.execute("DELETE FROM skill_roadmaps WHERE LOWER(skill_name) = LOWER(?)", (skill_name,))

    sort_order = 0
    _insert_items(conn, skill_name, items, parent_id=None, version=version, sort_order_ref=[sort_order])
    conn.commit()
    conn.close()


def _insert_items(conn, skill_name: str, items: list[dict], parent_id: int | None,
                  version: int, sort_order_ref: list):
    """Recursively insert roadmap items."""
    for item in items:
        sort_order_ref[0] += 1
        cur = conn.execute(
            "INSERT INTO skill_roadmap_posts (skill_name, parent_id, title, description, level, sort_order, version) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (skill_name, parent_id, item.get("title", ""), item.get("description", ""),
             item.get("level", 0), sort_order_ref[0], version),
        )
        new_id = cur.lastrowid
        children = item.get("children", [])
        if children:
            _insert_items(conn, skill_name, children, parent_id=new_id, version=version, sort_order_ref=sort_order_ref)


def _insert_items_fix(conn, skill_name: str, items: list[dict], parent_id: int | None,
                      version: int, sort_order_ref: list):
    """Recursively insert roadmap items into skill_roadmaps."""
    for item in items:
        sort_order_ref[0] += 1
        cur = conn.execute(
            "INSERT INTO skill_roadmaps (skill_name, parent_id, title, description, level, sort_order, version) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (skill_name, parent_id, item.get("title", ""), item.get("description", ""),
             item.get("level", 0), sort_order_ref[0], version),
        )
        new_id = cur.lastrowid
        children = item.get("children", [])
        if children:
            _insert_items_fix(conn, skill_name, children, parent_id=new_id, version=version, sort_order_ref=sort_order_ref)


def _save_roadmap_items_fixed(skill_name: str, items: list[dict], version: int):
    """Save generated roadmap items to DB (replaces existing for this version)."""
    conn = _db()
    conn.execute("DELETE FROM skill_roadmaps WHERE LOWER(skill_name) = LOWER(?)", (skill_name,))
    sort_order_ref = [0]
    _insert_items_fix(conn, skill_name, items, parent_id=None, version=version, sort_order_ref=sort_order_ref)
    conn.commit()
    conn.close()


def _get_next_version(skill_name: str) -> int:
    """Get the next version number for a skill's roadmap."""
    conn = _db()
    row = conn.execute(
        "SELECT MAX(version) FROM skill_roadmaps WHERE LOWER(skill_name) = LOWER(?)",
        (skill_name,),
    ).fetchone()
    conn.close()
    return (row[0] or 0) + 1 if row else 1


def _parse_json_response(text: str) -> list[dict] | None:
    """Extract a JSON array from the LLM response text."""
    if not text:
        return None
    text = text.strip()
    # Try direct parse
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "roadmap" in result:
            return result["roadmap"]
    except json.JSONDecodeError:
        pass
    # Try to find JSON array in text
    match = re.search(r'\[[\s\S]*\]', text)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass
    return None


def _run_llm_for_roadmap(
    prompt: str,
    job_id: int,
    skill_name: str,
    job_type: str = "generate",
    timeout: int = 600,
    result_file: str | None = None,
) -> tuple[list[dict] | None, str | None, str | None, str | None]:
    """Run LLM and return (parsed_items, error, session_id, provider_name).

    Unified logic for generate, extend, finegrain operations.
    """
    provider_name = _get_provider_name()
    session_id = None

    if result_file is None:
        result_file = os.path.join(TMP_DIR, f'skill_roadmap_{job_id}.json')

    _update_job(job_id, step=1, total_steps=TOTAL_STEPS, message="Calling AI...")
    _emit_skill_update(skill_name, {
        "job_id": job_id, "job_type": job_type,
        "step": 1, "total_steps": TOTAL_STEPS,
        "status": "running", "message": "Calling AI...",
        "provider_name": provider_name,
    })

    try:
        llm = get_llm_service()

        def _on_session_id(sid):
            nonlocal session_id
            session_id = sid
            _update_job(job_id, session_id=sid)
            _emit_skill_update(skill_name, {
                "job_id": job_id, "job_type": job_type,
                "step": 1, "total_steps": TOTAL_STEPS,
                "status": "running", "session_id": sid,
                "provider_name": provider_name,
                "message": "AI connected...",
            })

        def _on_event(evt):
            etype = evt.get('type', '')
            if etype == 'text':
                text = evt.get('part', {}).get('text', '')
                if text:
                    _emit_skill_update(skill_name, {
                        "job_id": job_id, "job_type": job_type,
                        "step": 2, "total_steps": TOTAL_STEPS,
                        "status": "running", "message": f"AI: {text[:120]}",
                        "session_id": session_id,
                        "provider_name": provider_name,
                    })

        _update_job(job_id, step=2, total_steps=TOTAL_STEPS, message="AI generating...")
        _emit_skill_update(skill_name, {
            "job_id": job_id, "job_type": job_type,
            "step": 2, "total_steps": TOTAL_STEPS,
            "status": "running", "message": "AI generating...",
            "session_id": session_id,
            "provider_name": provider_name,
        })

        resp = llm.generate_streaming(
            prompt,
            context={
                "pid": job_id,
                "result_file": result_file,
            },
            timeout=timeout,
            on_event=_on_event,
            on_session_id=_on_session_id,
        )

        _update_job(job_id, step=3, total_steps=TOTAL_STEPS, message="Parsing response...")
        _emit_skill_update(skill_name, {
            "job_id": job_id, "job_type": job_type,
            "step": 3, "total_steps": TOTAL_STEPS,
            "status": "running", "message": "Parsing response...",
            "session_id": session_id,
            "provider_name": provider_name,
        })

        # Try reading result file first (used by mimo provider)
        if os.path.exists(result_file):
            with open(result_file) as f:
                result = json.load(f)
            try:
                os.remove(result_file)
            except OSError:
                pass
            if isinstance(result, list):
                return result, None, session_id, provider_name
            return None, "Expected JSON array from LLM", session_id, provider_name

        # Fall back to parsing response content
        items = _parse_json_response(resp.content)
        if items:
            return items, None, session_id, provider_name

        return None, "LLM returned no parseable JSON roadmap", session_id, provider_name

    except Exception as e:
        return None, str(e), session_id, provider_name


def _finish_job(job_id: int, skill_name: str, status: str, job_type: str = "generate",
                version: int | None = None, count: int | None = None,
                error: str | None = None, session_id: str | None = None,
                provider_name: str | None = None):
    """Mark a job as completed/failed and emit final update."""
    kwargs = {
        "status": status,
        "completed_at": datetime.now().isoformat(),
    }
    if version is not None:
        kwargs["version"] = version
    if count is not None:
        kwargs["count"] = count
    if error:
        kwargs["error"] = error
    if session_id:
        kwargs["session_id"] = session_id
    if provider_name:
        kwargs["provider_name"] = provider_name

    _update_job(job_id, **kwargs)

    _emit_skill_update(skill_name, {
        "job_id": job_id,
        "job_type": job_type,
        "step": TOTAL_STEPS if status == "completed" else 0,
        "total_steps": TOTAL_STEPS,
        "status": status,
        "message": error or f"{'Completed' if status == 'completed' else status.title()}",
        "version": version,
        "count": count,
        "session_id": session_id,
        "provider_name": provider_name,
    })


# ── Public API ────────────────────────────────────────────────────


def generate_roadmap(skill_name: str):
    """Generate a new skill roadmap from scratch."""
    job_id = _create_job(skill_name, "generate")
    _emit_skill_update(skill_name, {
        "job_id": job_id, "job_type": "generate",
        "step": 0, "total_steps": TOTAL_STEPS,
        "status": "queued", "message": "Queued for generation...",
    })

    try:
        current_level = _get_current_level(skill_name)
        checked = _get_checked_items(skill_name)
        growth_ctx = (
            f"Already completed items: {json.dumps(checked)}\n"
            if checked else ""
        )

        _update_job(job_id, step=1, total_steps=TOTAL_STEPS, message="Preparing prompt...")
        _emit_skill_update(skill_name, {
            "job_id": job_id, "job_type": "generate",
            "step": 1, "total_steps": TOTAL_STEPS,
            "status": "running", "message": "Preparing prompt...",
        })

        prompt = load_prompt(
            'skill_roadmaps/skill_roadmaps_generate',
            skill_name=skill_name,
            current_level=current_level,
            checked_items=json.dumps(checked),
            growth_context=growth_ctx,
        )

        result_file = os.path.join(TMP_DIR, f'skill_roadmap_gen_{job_id}.json')
        items, error, session_id, provider_name = _run_llm_for_roadmap(
            prompt, job_id, skill_name, job_type="generate",
            timeout=600, result_file=result_file,
        )

        if error:
            _finish_job(job_id, skill_name, "failed", job_type="generate",
                        error=error, session_id=session_id, provider_name=provider_name)
            return

        version = _get_next_version(skill_name)
        _save_roadmap_items_fixed(skill_name, items, version)

        _update_job(job_id, step=4, total_steps=TOTAL_STEPS, message="Saving roadmap...")
        _emit_skill_update(skill_name, {
            "job_id": job_id, "job_type": "generate",
            "step": 4, "total_steps": TOTAL_STEPS,
            "status": "running", "message": "Saving roadmap...",
        })

        _finish_job(job_id, skill_name, "completed", job_type="generate",
                    version=version, count=len(items), session_id=session_id,
                    provider_name=provider_name)
        print(f"[skill_roadmap] Generated roadmap for '{skill_name}' "
              f"(v{version}, {len(items)} items, provider={provider_name}, session={session_id})")

    except Exception as e:
        _finish_job(job_id, skill_name, "failed", job_type="generate", error=str(e))
        print(f"[skill_roadmap] Generate failed for '{skill_name}': {e}")
        traceback.print_exc()


def extend_roadmap(skill_name: str):
    """Extend an existing roadmap with more advanced items."""
    job_id = _create_job(skill_name, "extend")
    _emit_skill_update(skill_name, {
        "job_id": job_id, "job_type": "extend",
        "step": 0, "total_steps": TOTAL_STEPS,
        "status": "queued", "message": "Queued for extension...",
    })

    try:
        existing = _get_existing_roadmap(skill_name)
        if not existing:
            _finish_job(job_id, skill_name, "failed", job_type="extend",
                        error="No roadmap exists. Generate first.")
            return

        tree = _build_tree(existing)
        tree_json = json.dumps(_flatten_tree(tree), indent=2, ensure_ascii=False)
        checked = _get_checked_items(skill_name)

        _update_job(job_id, step=1, total_steps=TOTAL_STEPS, message="Preparing prompt...")
        _emit_skill_update(skill_name, {
            "job_id": job_id, "job_type": "extend",
            "step": 1, "total_steps": TOTAL_STEPS,
            "status": "running", "message": "Preparing prompt...",
        })

        prompt = load_prompt(
            'skill_roadmaps/skill_roadmaps_extend',
            skill_name=skill_name,
            existing_tree_json=tree_json,
            checked_items=json.dumps(checked),
        )

        result_file = os.path.join(TMP_DIR, f'skill_roadmap_extend_{job_id}.json')
        items, error, session_id, provider_name = _run_llm_for_roadmap(
            prompt, job_id, skill_name, job_type="extend",
            timeout=600, result_file=result_file,
        )

        if error:
            _finish_job(job_id, skill_name, "failed", job_type="extend",
                        error=error, session_id=session_id, provider_name=provider_name)
            return

        version = _get_next_version(skill_name)
        _save_roadmap_items_fixed(skill_name, items, version)

        _finish_job(job_id, skill_name, "completed", job_type="extend",
                    version=version, count=len(items), session_id=session_id,
                    provider_name=provider_name)
        print(f"[skill_roadmap] Extended roadmap for '{skill_name}' "
              f"(v{version}, {len(items)} items, provider={provider_name})")

    except Exception as e:
        _finish_job(job_id, skill_name, "failed", job_type="extend", error=str(e))
        print(f"[skill_roadmap] Extend failed for '{skill_name}': {e}")
        traceback.print_exc()


def finegrain_roadmap(skill_name: str):
    """Fine-grain existing roadmap by splitting broad items into sub-items."""
    job_id = _create_job(skill_name, "finegrain")
    _emit_skill_update(skill_name, {
        "job_id": job_id, "job_type": "finegrain",
        "step": 0, "total_steps": TOTAL_STEPS,
        "status": "queued", "message": "Queued for fine-graining...",
    })

    try:
        existing = _get_existing_roadmap(skill_name)
        if not existing:
            _finish_job(job_id, skill_name, "failed", job_type="finegrain",
                        error="No roadmap exists. Generate first.")
            return

        tree = _build_tree(existing)
        tree_json = json.dumps(_flatten_tree(tree), indent=2, ensure_ascii=False)
        checked = _get_checked_items(skill_name)

        _update_job(job_id, step=1, total_steps=TOTAL_STEPS, message="Preparing prompt...")
        _emit_skill_update(skill_name, {
            "job_id": job_id, "job_type": "finegrain",
            "step": 1, "total_steps": TOTAL_STEPS,
            "status": "running", "message": "Preparing prompt...",
        })

        prompt = load_prompt(
            'skill_roadmaps/skill_roadmaps_finegrain',
            skill_name=skill_name,
            existing_tree_json=tree_json,
            checked_items=json.dumps(checked),
        )

        result_file = os.path.join(TMP_DIR, f'skill_roadmap_finegrain_{job_id}.json')
        items, error, session_id, provider_name = _run_llm_for_roadmap(
            prompt, job_id, skill_name, job_type="finegrain",
            timeout=600, result_file=result_file,
        )

        if error:
            _finish_job(job_id, skill_name, "failed", job_type="finegrain",
                        error=error, session_id=session_id, provider_name=provider_name)
            return

        version = _get_next_version(skill_name)
        _save_roadmap_items_fixed(skill_name, items, version)

        _finish_job(job_id, skill_name, "completed", job_type="finegrain",
                    version=version, count=len(items), session_id=session_id,
                    provider_name=provider_name)
        print(f"[skill_roadmap] Fine-grained roadmap for '{skill_name}' "
              f"(v{version}, {len(items)} items, provider={provider_name})")

    except Exception as e:
        _finish_job(job_id, skill_name, "failed", job_type="finegrain", error=str(e))
        print(f"[skill_roadmap] Finegrain failed for '{skill_name}': {e}")
        traceback.print_exc()
