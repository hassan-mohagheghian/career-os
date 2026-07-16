from flask import Flask, jsonify, Response, send_from_directory, request
from flask_cors import CORS
import sqlite3
import json
import os
import threading
from datetime import datetime
from urllib.parse import urlparse
from worker import process_job

app = Flask(__name__, static_folder='../client/dist', static_url_path='')
CORS(app)

DB_PATH = os.path.join(os.path.dirname(__file__), 'jobs.db')

def _ensure_db_schema():
    """Auto-migrate: add missing columns to jobs table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute('PRAGMA table_info(jobs)')
    columns = {row[1] for row in cursor.fetchall()}
    migrations = {
        'locations': "ALTER TABLE jobs ADD COLUMN locations TEXT DEFAULT '[]'",
        'deleted': "ALTER TABLE jobs ADD COLUMN deleted INTEGER DEFAULT 0",
        'employment_type': "ALTER TABLE jobs ADD COLUMN employment_type TEXT DEFAULT 'Full-time'",
        'work_types': "ALTER TABLE jobs ADD COLUMN work_types TEXT DEFAULT '[]'",
        'raw_description': "ALTER TABLE jobs ADD COLUMN raw_description TEXT",
        'structured_description': "ALTER TABLE jobs ADD COLUMN structured_description TEXT",
        'raw_file_path': "ALTER TABLE jobs ADD COLUMN raw_file_path TEXT",
        'structured_file_path': "ALTER TABLE jobs ADD COLUMN structured_file_path TEXT",
    }
    # pending_jobs: add step columns if missing
    cursor2 = conn.execute('PRAGMA table_info(pending_jobs)')
    pending_cols = {row[1] for row in cursor2.fetchall()}
    for col in ['step_extract_raw', 'step_extract_struct', 'step_summary', 'step_validate']:
        if col not in pending_cols:
            conn.execute(f"ALTER TABLE pending_jobs ADD COLUMN {col} INTEGER DEFAULT 0")
    # jobs: add rescoring column if missing
    if 'rescoring' not in columns:
        conn.execute("ALTER TABLE jobs ADD COLUMN rescoring INTEGER DEFAULT 0")
    for col, sql in migrations.items():
        if col not in columns:
            conn.execute(sql)
    conn.commit()
    conn.close()

_ensure_db_schema()


def normalize_url(url):
    """Remove query parameters and trailing slash from URL for duplicate detection."""
    if not url:
        return url
    parsed = urlparse(url)
    base_url = f'{parsed.scheme}://{parsed.netloc}{parsed.path}'
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    return base_url

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    return conn

def row_to_dict(row):
    return dict(row) if row else None

def rows_to_list(rows):
    return [dict(r) for r in rows]

# --- Streaming helpers ---

def stream_json(data):
    """Stream JSON response for large payloads."""
    def generate():
        yield json.dumps(data, ensure_ascii=False)
    return Response(generate(), mimetype='application/json')

# --- API Routes ---

@app.route('/api/jobs')
def get_jobs():
    conn = get_db()
    offset = request.args.get('offset', type=int)
    limit = request.args.get('limit', type=int)

    # Sorting
    sort_by = request.args.get('sort_by', 'created_at')
    sort_dir = request.args.get('sort_dir', 'desc')
    allowed_sorts = {'created_at', 'score', 'num', 'company', 'location', 'posted_at', 'applicants'}
    if sort_by not in allowed_sorts:
        sort_by = 'created_at'
    if sort_dir not in ('asc', 'desc'):
        sort_dir = 'desc'

    # Build WHERE clause
    conditions = ['deleted=0']
    params = []

    # Filter: cities
    filter_cities = request.args.get('filter_cities', '')
    if filter_cities:
        cities = [c.strip() for c in filter_cities.split(',') if c.strip()]
        if cities:
            # Match against locations JSON array or location column
            city_conditions = []
            for city in cities:
                city_conditions.append("locations LIKE ?")
                params.append(f'%"{city}"%')
                city_conditions.append("location = ?")
                params.append(city)
            conditions.append(f'({" OR ".join(city_conditions)})')

    # Filter: companies
    filter_companies = request.args.get('filter_companies', '')
    if filter_companies:
        companies = [c.strip() for c in filter_companies.split(',') if c.strip()]
        if companies:
            placeholders = ','.join(['?' for _ in companies])
            conditions.append(f'company IN ({placeholders})')
            params.extend(companies)

    # Filter: matches
    filter_matches = request.args.get('filter_matches', '')
    if filter_matches:
        matches = [m.strip() for m in filter_matches.split(',') if m.strip()]
        if matches:
            placeholders = ','.join(['?' for _ in matches])
            conditions.append(f'match IN ({placeholders})')
            params.extend(matches)

    # Filter: work types
    filter_work_types = request.args.get('filter_work_types', '')
    if filter_work_types:
        wtypes = [w.strip() for w in filter_work_types.split(',') if w.strip()]
        if wtypes:
            wt_conditions = []
            for wt in wtypes:
                wt_conditions.append("work_types LIKE ?")
                params.append(f'%"{wt}"%')
                wt_conditions.append("work_type = ?")
                params.append(wt)
            conditions.append(f'({" OR ".join(wt_conditions)})')

    # Filter: employment types
    filter_employment_types = request.args.get('filter_employment_types', '')
    if filter_employment_types:
        etypes = [e.strip() for e in filter_employment_types.split(',') if e.strip()]
        if etypes:
            placeholders = ','.join(['?' for _ in etypes])
            conditions.append(f'employment_type IN ({placeholders})')
            params.extend(etypes)

    # Filter: text search (stack, role, company, notes)
    filter_tech = request.args.get('filter_tech', '').strip()
    if filter_tech:
        like_param = f'%{filter_tech}%'
        conditions.append('(stack LIKE ? OR role LIKE ? OR company LIKE ? OR notes LIKE ?)')
        params.extend([like_param, like_param, like_param, like_param])

    where_clause = ' AND '.join(conditions)
    total = conn.execute(f'SELECT COUNT(*) FROM jobs WHERE {where_clause}', params).fetchone()[0]

    # Handle applicants sorting specially (parse numeric from text)
    if sort_by == 'applicants':
        order_clause = f"CAST(REPLACE(REPLACE(applicants, 'Not specified', '999'), '+', '') AS INTEGER) {sort_dir}"
    else:
        order_clause = f'{sort_by} {sort_dir}'

    if offset is not None and limit is not None:
        rows = conn.execute(f'SELECT * FROM jobs WHERE {where_clause} ORDER BY {order_clause} LIMIT ? OFFSET ?', params + [limit, offset]).fetchall()
        conn.close()
        return jsonify({'jobs': rows_to_list(rows), 'total': total})
    rows = conn.execute(f'SELECT * FROM jobs WHERE {where_clause} ORDER BY {order_clause}', params).fetchall()
    conn.close()
    return jsonify({'jobs': rows_to_list(rows), 'total': total})

@app.route('/api/jobs/<int:num>')
def get_job(num):
    conn = get_db()
    row = conn.execute('SELECT * FROM jobs WHERE num=?', (num,)).fetchone()
    conn.close()
    if row:
        return jsonify(row_to_dict(row))
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/jobs/<int:num>', methods=['DELETE'])
def delete_job(num):
    """Soft delete a processed job."""
    conn = get_db()
    conn.execute('UPDATE jobs SET deleted=1 WHERE num=?', (num,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted', 'num': num})

@app.route('/api/jobs/<int:num>/requeue', methods=['POST'])
def requeue_job(num):
    """Re-queue a job for fresh processing. Old job deleted only after new one succeeds."""
    conn = get_db()
    job = conn.execute('SELECT * FROM jobs WHERE num=?', (num,)).fetchone()
    if not job:
        conn.close()
        return jsonify({'error': 'Job not found'}), 404
    j = dict(job)
    url = j['url']
    company = j.get('company', '')
    # Mark old job for deferred deletion (worker deletes after success)
    conn.execute('UPDATE jobs SET deleted=1 WHERE num=?', (num,))
    # Find or create pending entry
    row = conn.execute('SELECT id FROM pending_jobs WHERE url=?', (url,)).fetchone()
    if row:
        pid = dict(row)['id']
        conn.execute('''UPDATE pending_jobs SET status='queued', error=NULL, source='requeue',
            company=?, step_fetch=0, step_validate=0, step_extract_raw=0, step_extract_struct=0,
            step_analyze=0, step_summary=0, step_resume=0, step_db=0, step_done=0,
            workflow_log='[]', updated_at=? WHERE id=?''',
            (company, datetime.now().isoformat(), pid))
    else:
        cur = conn.execute('INSERT INTO pending_jobs (url, source, company) VALUES (?, ?, ?)',
            (url, 'requeue', company))
        pid = cur.lastrowid
    conn.commit()
    conn.close()
    threading.Thread(target=process_job, args=(pid,), daemon=True).start()
    return jsonify({'status': 'requeuing', 'pid': pid, 'num': num, 'company': company})

@app.route('/api/summaries')
def get_summaries():
    conn = get_db()
    rows = conn.execute('SELECT * FROM summaries ORDER BY score DESC').fetchall()
    conn.close()
    return stream_json(rows_to_list(rows))

@app.route('/api/resumes')
def get_resumes():
    conn = get_db()
    rows = conn.execute('SELECT * FROM resumes').fetchall()
    conn.close()
    return stream_json(rows_to_list(rows))

@app.route('/api/tech-learning')
def get_tech_learning():
    conn = get_db()
    rows = conn.execute('SELECT * FROM tech_learning ORDER BY priority').fetchall()
    conn.close()
    return stream_json(rows_to_list(rows))

@app.route('/api/tech-stack')
def get_tech_stack():
    conn = get_db()
    rows = conn.execute('SELECT * FROM tech_stack ORDER BY level DESC').fetchall()
    conn.close()
    return stream_json(rows_to_list(rows))

@app.route('/api/cities')
def get_cities():
    """Get cities dynamically from all job locations."""
    conn = get_db()
    # Get all locations from non-deleted jobs
    rows = conn.execute('SELECT location, locations FROM jobs WHERE deleted=0').fetchall()
    conn.close()

    city_counts = {}
    for row in rows:
        r = dict(row)
        # Parse locations JSON array
        locations = []
        if r.get('locations'):
            try:
                locations = json.loads(r['locations']) if isinstance(r['locations'], str) else r['locations']
            except:
                pass
        if not locations and r.get('location'):
            locations = [r['location']]

        for loc in locations:
            if loc and loc != 'Not specified':
                city_counts[loc] = city_counts.get(loc, 0) + 1

    # City icons and descriptions
    city_info = {
        'Berlin': {'icon': '🐻', 'info': 'Largest tech hub. 350K+ tech workers.'},
        'Munich': {'icon': '🦁', 'info': 'Highest salaries. Enterprise & automotive.'},
        'Hamburg': {'icon': '🎵', 'info': 'Growing tech scene. AdTech, energy.'},
        'Heidelberg': {'icon': '🏛️', 'info': 'Enterprise AI startup scene.'},
        'Frankfurt': {'icon': '🏦', 'info': 'FinTech capital. Banking infrastructure.'},
        'Cologne': {'icon': '🗼', 'info': 'Media & commerce tech.'},
        'Stuttgart': {'icon': '🏭', 'info': 'Engineering & automotive.'},
        'Remote': {'icon': '🏠', 'info': 'Best for visa from Iran.'},
        'Remote Germany': {'icon': '🏠', 'info': 'Best for visa from Iran.'},
        'Germany': {'icon': '🇩🇪', 'info': 'Country-wide opportunities.'},
    }

    total_jobs = len(city_counts)
    cities = []
    for city, count in sorted(city_counts.items(), key=lambda x: -x[1]):
        info = city_info.get(city, {'icon': '📍', 'info': 'Tech hub.'})
        cities.append({
            'icon': info['icon'],
            'name': city,
            'info': info['info'],
            'jobs': f'{count}/{total_jobs} jobs'
        })

    return stream_json(cities)

@app.route('/api/dashboard-insights')
def get_dashboard_insights():
    conn = get_db()
    rows = conn.execute('SELECT * FROM dashboard_insights ORDER BY type, priority').fetchall()
    conn.close()
    insights = {}
    for row in rows:
        r = dict(row)
        t = r['type']
        if t not in insights:
            insights[t] = []
        insights[t].append(r)
    return stream_json(insights)

@app.route('/api/dashboard-insights', methods=['POST'])
def update_dashboard_insights():
    data = request.get_json()
    conn = get_db()
    conn.execute('DELETE FROM dashboard_insights')
    for item_type, items in data.items():
        if isinstance(items, list):
            for i, item in enumerate(items):
                conn.execute('''INSERT INTO dashboard_insights (type, icon, title, description, priority)
                    VALUES (?, ?, ?, ?, ?)''',
                    (item_type, item.get('icon', ''), item.get('title', item.get('name', '')),
                     item.get('description', item.get('detail', item.get('note', ''))), i))
    conn.commit()
    conn.close()
    return jsonify({'status': 'updated', 'count': sum(len(v) for v in data.values() if isinstance(v, list))})

@app.route('/api/preferences')
def get_preferences():
    conn = get_db()
    rows = conn.execute('SELECT * FROM preferences ORDER BY category, priority').fetchall()
    conn.close()
    prefs = {}
    for row in rows:
        r = dict(row)
        cat = r['category']
        if cat not in prefs:
            prefs[cat] = []
        prefs[cat].append(r)
    return stream_json(prefs)

@app.route('/api/preferences', methods=['POST'])
def update_preferences():
    data = request.get_json()
    conn = get_db()
    for item in data.get('preferences', []):
        conn.execute('''INSERT OR REPLACE INTO preferences (category, key, value, description, priority, enabled)
            VALUES (?, ?, ?, ?, ?, ?)''',
            (item['category'], item['key'], item['value'],
             item.get('description', ''), item.get('priority', 0), item.get('enabled', 1)))
    conn.commit()
    conn.close()
    return jsonify({'status': 'updated'})

@app.route('/api/preferences/<int:id>', methods=['PUT'])
def update_preference(id):
    data = request.get_json()
    conn = get_db()
    fields = []
    values = []
    for key in ['value', 'description', 'priority', 'enabled']:
        if key in data:
            fields.append(f'{key}=?')
            values.append(data[key])
    if fields:
        fields.append('updated_at=?')
        values.append(datetime.now().isoformat())
        values.append(id)
        conn.execute(f'UPDATE preferences SET {",".join(fields)} WHERE id=?', values)
        conn.commit()
    conn.close()
    return jsonify({'status': 'updated'})

@app.route('/api/preferences/<int:id>', methods=['DELETE'])
def delete_preference(id):
    conn = get_db()
    conn.execute('DELETE FROM preferences WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted'})

@app.route('/api/pending', methods=['GET'])
def get_pending():
    conn = get_db()
    rows = conn.execute('SELECT * FROM pending_jobs ORDER BY created_at DESC').fetchall()
    conn.close()
    return stream_json(rows_to_list(rows))

@app.route('/api/pending', methods=['POST'])
def add_pending():
    data = request.get_json()
    url = data.get('url', '').strip()
    source = data.get('source', 'web')
    if not url:
        return jsonify({'error': 'URL required'}), 400

    normalized = normalize_url(url)
    conn = get_db()

    # Check if there's an active (non-done/failed) pending entry
    pending = conn.execute('SELECT id, status, url FROM pending_jobs WHERE status NOT IN (?,?)', ('done', 'failed')).fetchall()
    for row in pending:
        r = dict(row)
        if normalize_url(r['url']) == normalized:
            conn.close()
            return jsonify({'error': 'Already in queue', 'id': r['id'], 'status': r['status']}), 409

    # Check jobs table for duplicate (normalized URL) - only non-deleted
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

    # Clean up any old done/failed pending entries for this URL
    old_pending = conn.execute('SELECT id FROM pending_jobs WHERE url=? AND status IN (?,?)', (url, 'done', 'failed')).fetchall()
    for row in old_pending:
        conn.execute('DELETE FROM pending_jobs WHERE id=?', (dict(row)['id'],))
    if old_pending:
        conn.commit()

    try:
        cur = conn.execute('INSERT INTO pending_jobs (url, source) VALUES (?, ?)', (url, source))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return jsonify({'status': 'queued', 'id': new_id, 'url': url, 'source': source})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'URL already exists', 'url': url}), 409

@app.route('/api/pending/<int:id>', methods=['DELETE'])
def delete_pending(id):
    conn = get_db()
    # Get the URL and associated job num before deleting
    row = conn.execute('SELECT url FROM pending_jobs WHERE id=?', (id,)).fetchone()
    if row:
        url = dict(row)['url']
        # Find associated job num
        job_row = conn.execute('SELECT num, company FROM jobs WHERE url=?', (url,)).fetchone()
        # Soft-delete any processed job with the same URL
        conn.execute('UPDATE jobs SET deleted=1 WHERE url=?', (url,))
        conn.execute('DELETE FROM summaries WHERE url=?', (url,))
        if job_row:
            num = dict(job_row)['num']
            conn.execute('DELETE FROM resumes WHERE id=? OR id=?', (f'pending_{num}', f'rescore_{num}'))
    conn.execute('DELETE FROM pending_jobs WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted'})

@app.route('/api/pending/<int:id>/reset', methods=['PUT'])
def reset_pending(id):
    """Reset a pending job back to queued status (stop — from scratch)."""
    conn = get_db()
    conn.execute('''UPDATE pending_jobs SET status='queued', error=NULL,
                    step_fetch=0, step_validate=0, step_extract_raw=0, step_extract_struct=0,
                    step_analyze=0, step_summary=0, step_resume=0, step_db=0, step_done=0,
                    updated_at=? WHERE id=?''',
                 (datetime.now().isoformat(), id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'queued', 'id': id})

@app.route('/api/pending/<int:id>/pause', methods=['PUT'])
def pause_pending(id):
    """Pause a processing job — keep completed steps, reset current step, move to paused."""
    conn = get_db()
    row = conn.execute('SELECT * FROM pending_jobs WHERE id=?', (id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Not found'}), 404
    item = dict(row)
    # Find the current (first incomplete) step and reset only that one
    step_cols = ['step_fetch', 'step_extract_raw', 'step_extract_struct', 'step_analyze', 'step_resume']
    reset_col = None
    for col in step_cols:
        if item.get(col) == 0:
            reset_col = col
            break
    if reset_col:
        conn.execute(f'UPDATE pending_jobs SET status="paused", error=NULL, {reset_col}=0, updated_at=? WHERE id=?',
                     (datetime.now().isoformat(), id))
    else:
        # All steps complete, just pause
        conn.execute('UPDATE pending_jobs SET status="paused", updated_at=? WHERE id=?',
                     (datetime.now().isoformat(), id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'paused', 'id': id})

@app.route('/api/pending/<int:id>/process', methods=['POST'])
def process_pending(id):
    """Mark a pending job for processing and write trigger file."""
    conn = get_db()
    row = conn.execute('SELECT * FROM pending_jobs WHERE id=?', (id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Not found'}), 404

    item = dict(row)
    if item['status'] == 'done':
        conn.close()
        return jsonify({'error': 'Already completed'}), 400

    # Update status to processing (reset steps if retrying a failed job)
    if item['status'] == 'failed':
        conn.execute('''UPDATE pending_jobs SET status='processing', error=NULL,
                        step_fetch=0, step_validate=0, step_extract_raw=0, step_extract_struct=0,
                        step_analyze=0, step_summary=0, step_resume=0, step_db=0, step_done=0,
                        updated_at=? WHERE id=?''',
                     (datetime.now().isoformat(), id))
    else:
        # For paused or queued: keep existing steps (continue from current step)
        conn.execute('''UPDATE pending_jobs SET status='processing', updated_at=? WHERE id=?''',
                     (datetime.now().isoformat(), id))
    conn.commit()
    conn.close()

    # Spawn background worker thread (autonomous — no MiMoCode dependency)
    threading.Thread(target=process_job, args=(id,), daemon=True).start()

    return jsonify({'status': 'processing', 'id': id, 'url': item['url']})

@app.route('/api/refresh/dashboard', methods=['POST'])
def refresh_dashboard():
    """Manually refresh dashboard insights."""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from worker import _update_dashboard_insights
    try:
        _update_dashboard_insights(0)
        return jsonify({'status': 'updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/refresh/skills', methods=['POST'])
def refresh_skills():
    """Manually refresh skills insights."""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from worker import _update_skills_insights
    try:
        _update_skills_insights(0)
        return jsonify({'status': 'updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/refresh/analysis', methods=['POST'])
def refresh_analysis():
    """Manually refresh unified analysis (combines dashboard + skills)."""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from worker import _update_unified_analysis
    try:
        _update_unified_analysis(0)
        return jsonify({'status': 'updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis')
def get_unified_analysis():
    """Get the latest unified analysis from the analysis_runs table.
    Falls back to 'dashboard' page records if no 'analysis' page exists yet."""
    conn = get_db()
    # Try unified analysis first
    row = conn.execute(
        'SELECT id, page, created_at, analysis_json FROM analysis_runs WHERE page=? ORDER BY created_at DESC LIMIT 1',
        ('analysis',)
    ).fetchone()
    # Fall back to dashboard records
    if not row:
        row = conn.execute(
            'SELECT id, page, created_at, analysis_json FROM analysis_runs WHERE page=? ORDER BY created_at DESC LIMIT 1',
            ('dashboard',)
        ).fetchone()
    conn.close()
    if row:
        r = dict(row)
        r['analysis'] = json.loads(r['analysis_json'])
        del r['analysis_json']
        return jsonify(r)
    return jsonify({'error': 'No analysis found'}), 404

@app.route('/api/analysis/<page>')
def get_analysis(page):
    """Get the latest analysis for a page from the analysis_runs table."""
    conn = get_db()
    row = conn.execute(
        'SELECT id, page, created_at, analysis_json FROM analysis_runs WHERE page=? ORDER BY created_at DESC LIMIT 1',
        (page,)
    ).fetchone()
    conn.close()
    if row:
        r = dict(row)
        r['analysis'] = json.loads(r['analysis_json'])
        del r['analysis_json']
        return jsonify(r)
    return jsonify({'error': 'No analysis found', 'page': page}), 404

@app.route('/api/analysis/<page>/history')
def get_analysis_history(page):
    """Get all analysis runs for a page."""
    conn = get_db()
    rows = conn.execute(
        'SELECT id, page, created_at FROM analysis_runs WHERE page=? ORDER BY created_at DESC',
        (page,)
    ).fetchall()
    conn.close()
    return jsonify(rows_to_list(rows))

@app.route('/api/pending/stream')
def stream_pending():
    """SSE endpoint for real-time pending job updates."""
    import time
    def generate():
        last_modified = ''
        while True:
            conn = get_db()
            rows = conn.execute('SELECT * FROM pending_jobs ORDER BY created_at DESC').fetchall()
            conn.close()
            data = json.dumps(rows_to_list(rows), ensure_ascii=False)
            # Simple change detection via hash
            current_hash = str(hash(data))
            if current_hash != last_modified:
                last_modified = current_hash
                yield f'data: {data}\n\n'
            time.sleep(2)
    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

@app.route('/api/pending/<int:id>/step', methods=['PUT'])
def update_step(id):
    data = request.get_json()
    conn = get_db()
    fields = []
    values = []
    for key in ['status', 'step_fetch', 'step_analyze', 'step_resume', 'step_db', 'step_done', 'job_num', 'company', 'error']:
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

# --- Serve React app ---

@app.route('/')
def serve():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
@app.route('/api/jobs/<int:num>/rescore', methods=['POST'])
def rescore_job(num):
    """Re-score a single job in the background without moving to processing queue."""
    conn = get_db()
    job = conn.execute('SELECT * FROM jobs WHERE num=?', (num,)).fetchone()
    if not job:
        conn.close()
        return jsonify({'error': 'Job not found'}), 404
    j = dict(job)
    # Set rescoring flag
    conn.execute('UPDATE jobs SET rescoring=1 WHERE num=?', (num,))
    conn.commit()
    conn.close()
    # Spawn background rescore thread
    from worker import rescore_only
    threading.Thread(target=rescore_only, args=(num,), daemon=True).start()
    return jsonify({'status': 'rescoring', 'num': num, 'company': j.get('company', '')})

@app.route('/api/jobs/rescore-all', methods=['POST'])
def rescore_all():
    """Re-score all jobs in the background."""
    conn = get_db()
    jobs = conn.execute('SELECT num FROM jobs WHERE deleted=0 AND rescoring=0').fetchall()
    conn.close()
    count = 0
    from worker import rescore_only
    for job in jobs:
        num = dict(job)['num']
        threading.Thread(target=rescore_only, args=(num,), daemon=True).start()
        count += 1
    return jsonify({'status': 'rescoring', 'count': count})

@app.route('/api/jobs/reprocess-all', methods=['POST'])
def reprocess_all():
    """Hard-delete all processed jobs and re-queue for fresh processing."""
    conn = get_db()
    jobs = conn.execute('SELECT num, url, company FROM jobs WHERE deleted=0').fetchall()
    # Hard-delete all jobs and related data
    conn.execute('DELETE FROM jobs WHERE deleted=0')
    conn.execute('DELETE FROM summaries')
    conn.execute("DELETE FROM resumes WHERE id != 'original'")
    conn.commit()
    conn.close()
    count = 0
    for job in jobs:
        j = dict(job)
        url = j['url']
        company = j.get('company', '')
        # Find or create pending entry
        c = get_db()
        row = c.execute('SELECT id FROM pending_jobs WHERE url=?', (url,)).fetchone()
        if row:
            pid = dict(row)['id']
            c.execute('''UPDATE pending_jobs SET status='queued', error=NULL, source='requeue',
                company=?, step_fetch=0, step_validate=0, step_extract_raw=0, step_extract_struct=0,
                step_analyze=0, step_summary=0, step_resume=0, step_db=0, step_done=0,
                workflow_log='[]', updated_at=? WHERE id=?''',
                (company, datetime.now().isoformat(), pid))
        else:
            cur = c.execute('INSERT INTO pending_jobs (url, source, company) VALUES (?, ?, ?)',
                (url, 'requeue', company))
            pid = cur.lastrowid
        c.commit()
        c.close()
        threading.Thread(target=process_job, args=(pid,), daemon=True).start()
        count += 1
    return jsonify({'status': 'reprocessing', 'count': count})

def static_proxy(path):
    file_path = os.path.join(app.static_folder, path)
    if os.path.isfile(file_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
