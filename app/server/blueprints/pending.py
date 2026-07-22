"""Pending job queue routes."""

import json
import time
from datetime import datetime

from flask import Blueprint, jsonify, request, Response

from database import get_db, rows_to_list
from utils import stream_json, normalize_url
from core.queue import get_queue_manager

bp = Blueprint('pending', __name__)


@bp.route('/api/pending', methods=['GET'])
def get_pending():
    conn = get_db()
    rows = conn.execute('SELECT * FROM pending_jobs ORDER BY created_at DESC').fetchall()
    conn.close()
    return stream_json(rows_to_list(rows))


@bp.route('/api/pending', methods=['POST'])
def add_pending():
    data = request.get_json()
    url = data.get('url', '').strip()
    source = data.get('source', 'web')
    if not url:
        return jsonify({'error': 'URL required'}), 400

    normalized = normalize_url(url)
    conn = get_db()

    pending = conn.execute('SELECT id, status, url FROM pending_jobs WHERE status NOT IN (?,?)', ('done', 'failed')).fetchall()
    for row in pending:
        r = dict(row)
        if normalize_url(r['url']) == normalized:
            conn.close()
            return jsonify({'error': 'Already in queue', 'id': r['id'], 'status': r['status']}), 409

    jobs = conn.execute('SELECT num, company, url, score, match FROM jobs WHERE deleted=0').fetchall()
    for row in jobs:
        j = dict(row)
        if normalize_url(j['url']) == normalized:
            conn.close()
            return jsonify({
                'status': 'exists',
                'num': j['num'],
                'company': j['company'],
                'score': j['score'],
                'match': j['match'],
                'url': url
            })

    old_pending = conn.execute('SELECT id FROM pending_jobs WHERE url=? AND status IN (?,?)', (url, 'done', 'failed')).fetchall()
    for row in old_pending:
        conn.execute('DELETE FROM pending_jobs WHERE id=?', (dict(row)['id'],))
    if old_pending:
        conn.commit()

    try:
        cur = conn.execute('INSERT INTO pending_jobs (url, source, status) VALUES (?, ?, ?)',
                           (url, source, 'pending'))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return jsonify({'status': 'pending', 'id': new_id, 'url': url, 'source': source})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'URL already exists', 'url': url}), 409


@bp.route('/api/pending/<int:id>', methods=['DELETE'])
def delete_pending(id):
    conn = get_db()
    row = conn.execute('SELECT url FROM pending_jobs WHERE id=?', (id,)).fetchone()
    if row:
        url = dict(row)['url']
        job_row = conn.execute('SELECT num, company FROM jobs WHERE url=?', (url,)).fetchone()
        conn.execute('UPDATE jobs SET deleted=1 WHERE url=?', (url,))
        conn.execute('DELETE FROM summaries WHERE url=?', (url,))
        if job_row:
            num = dict(job_row)['num']
            conn.execute('DELETE FROM resumes WHERE id=? OR id=?', (f'pending_{num}', f'rescore_{num}'))
    conn.execute('DELETE FROM pending_jobs WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted'})


@bp.route('/api/pending/<int:id>/reset', methods=['PUT'])
def reset_pending(id):
    conn = get_db()
    conn.execute('''UPDATE pending_jobs SET status='pending', error=NULL, queue_order=0,
                    step_fetch=0, step_validate=0, step_extract_raw=0, step_extract_struct=0,
                    step_analyze=0, step_summary=0, step_db=0, step_done=0,
                    updated_at=? WHERE id=?''',
                 (datetime.now().isoformat(), id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'pending', 'id': id})


@bp.route('/api/pending/<int:id>/pause', methods=['PUT'])
def pause_pending(id):
    conn = get_db()
    row = conn.execute('SELECT * FROM pending_jobs WHERE id=?', (id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Not found'}), 404
    item = dict(row)
    step_cols = ['step_fetch', 'step_validate', 'step_extract_raw', 'step_extract_struct', 'step_summary', 'step_analyze']
    reset_col = None
    for col in step_cols:
        if item.get(col) == 0:
            reset_col = col
            break
    if reset_col:
        conn.execute(f'UPDATE pending_jobs SET status="paused", error=NULL, {reset_col}=0, updated_at=? WHERE id=?',
                     (datetime.now().isoformat(), id))
    else:
        conn.execute('UPDATE pending_jobs SET status="paused", updated_at=? WHERE id=?',
                     (datetime.now().isoformat(), id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'paused', 'id': id})


@bp.route('/api/pending/<int:id>/process', methods=['POST'])
def process_pending(id):
    conn = get_db()
    row = conn.execute('SELECT * FROM pending_jobs WHERE id=?', (id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Not found'}), 404

    item = dict(row)
    if item['status'] == 'done':
        conn.close()
        return jsonify({'error': 'Already completed'}), 400
    if item['status'] == 'processing':
        conn.close()
        return jsonify({'error': 'Already processing', 'id': id}), 409
    if item['status'] == 'queued':
        conn.close()
        return jsonify({'error': 'Already queued', 'id': id}), 409

    if item['status'] == 'failed':
        conn.execute('''UPDATE pending_jobs SET error=NULL,
                        step_fetch=0, step_validate=0, step_extract_raw=0, step_extract_struct=0,
                        step_analyze=0, step_summary=0, step_db=0, step_done=0,
                        updated_at=? WHERE id=?''',
                     (datetime.now().isoformat(), id))
        conn.commit()
    conn.close()

    get_queue_manager().enqueue(id)
    return jsonify({'status': 'queued', 'id': id, 'url': item['url']})


@bp.route('/api/pending/<int:id>/step', methods=['PUT'])
def update_step(id):
    data = request.get_json()
    conn = get_db()
    fields = []
    values = []
    for key in ['status', 'step_fetch', 'step_analyze', 'step_db', 'step_done', 'job_num', 'company', 'error']:
        if key in data:
            fields.append(f'{key}=?')
            values.append(data[key])
    if fields:
        fields.append('updated_at=?')
        values.append(datetime.now().isoformat())
        values.append(id)
        conn.execute(f'UPDATE pending_jobs SET {",".join(fields)} WHERE id=?', values)
        conn.commit()
    conn.close()
    return jsonify({'status': 'updated'})


@bp.route('/api/pending/stream')
def stream_pending():
    def generate():
        last_modified = ''
        while True:
            conn = get_db()
            rows = conn.execute('SELECT * FROM pending_jobs ORDER BY created_at DESC').fetchall()
            conn.close()
            data = json.dumps(rows_to_list(rows), ensure_ascii=False)
            current_hash = str(hash(data))
            if current_hash != last_modified:
                last_modified = current_hash
                yield f'data: {data}\n\n'
            time.sleep(2)
    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@bp.route('/api/pending/queue-all', methods=['POST'])
def queue_all_pending():
    conn = get_db()
    rows = conn.execute("SELECT id FROM pending_jobs WHERE status='pending' ORDER BY created_at ASC").fetchall()
    conn.close()
    pending_ids = [dict(r)['id'] for r in rows]
    if pending_ids:
        get_queue_manager().enqueue_bulk(pending_ids)
    return jsonify({'status': 'queued', 'count': len(pending_ids)})


@bp.route('/api/queue/status')
def queue_status():
    return jsonify(get_queue_manager().get_status())
