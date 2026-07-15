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
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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

def stream_jsonl(rows):
    """Stream JSONL (newline-delimited JSON) for progressive loading."""
    def generate():
        for row in rows:
            yield json.dumps(dict(row), ensure_ascii=False) + '\n'
    return Response(generate(), mimetype='application/x-ndjson')

# --- API Routes ---

@app.route('/api/jobs')
def get_jobs():
    conn = get_db()
    rows = conn.execute('SELECT * FROM jobs WHERE deleted=0 ORDER BY score DESC').fetchall()
    conn.close()
    return stream_json(rows_to_list(rows))

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
    """Re-queue a deleted job for processing. Creates a new job after processing."""
    conn = get_db()
    job = conn.execute('SELECT * FROM jobs WHERE num=?', (num,)).fetchone()
    if not job:
        conn.close()
        return jsonify({'error': 'Job not found'}), 404
    j = dict(job)
    url = j['url']
    company = j.get('company', '')
    # Find or create pending entry
    row = conn.execute('SELECT id FROM pending_jobs WHERE url=?', (url,)).fetchone()
    if row:
        pid = dict(row)['id']
        conn.execute('''UPDATE pending_jobs SET status='queued', error=NULL, source='requeue',
            company=?, step_fetch=0, step_analyze=0, step_resume=0, step_db=0, step_done=0,
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

    # Check pending_jobs for duplicate (normalized URL)
    pending = conn.execute('SELECT id, status, url FROM pending_jobs').fetchall()
    for row in pending:
        r = dict(row)
        if normalize_url(r['url']) == normalized:
            conn.close()
            return jsonify({'error': 'Already in queue', 'id': r['id'], 'status': r['status']}), 409

    # Check jobs table for duplicate (normalized URL) - only non-deleted
    jobs = conn.execute('SELECT num, company, url FROM jobs WHERE deleted=0').fetchall()
    for row in jobs:
        j = dict(row)
        if normalize_url(j['url']) == normalized:
            conn.close()
            return jsonify({'error': f'Already processed as #{j["num"]} ({j["company"]})', 'num': j['num']}), 409

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
    conn.execute('DELETE FROM pending_jobs WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted'})

@app.route('/api/pending/<int:id>/reset', methods=['PUT'])
def reset_pending(id):
    """Reset a pending job back to queued status."""
    conn = get_db()
    conn.execute('''UPDATE pending_jobs SET status='queued', error=NULL,
                    step_fetch=0, step_analyze=0, step_resume=0, step_db=0, step_done=0,
                    updated_at=? WHERE id=?''',
                 (datetime.now().isoformat(), id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'queued', 'id': id})

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
                        step_fetch=0, step_analyze=0, step_resume=0, step_db=0, step_done=0,
                        updated_at=? WHERE id=?''',
                     (datetime.now().isoformat(), id))
    else:
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

@app.route('/api/all')
def get_all():
    """Single endpoint returning all data — reduces round trips."""
    conn = get_db()

    # Build cities dynamically from job locations
    job_rows = conn.execute('SELECT location, locations FROM jobs').fetchall()
    city_counts = {}
    for row in job_rows:
        r = dict(row)
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
    city_info = {
        'Berlin': {'icon': '🐻', 'info': 'Largest tech hub.'},
        'Munich': {'icon': '🦁', 'info': 'Highest salaries.'},
        'Hamburg': {'icon': '🎵', 'info': 'Growing tech scene.'},
        'Heidelberg': {'icon': '🏛️', 'info': 'Enterprise AI.'},
        'Frankfurt': {'icon': '🏦', 'info': 'FinTech capital.'},
        'Cologne': {'icon': '🗼', 'info': 'Media & commerce.'},
        'Stuttgart': {'icon': '🏭', 'info': 'Engineering.'},
        'Remote': {'icon': '🏠', 'info': 'Best for visa.'},
        'Remote Germany': {'icon': '🏠', 'info': 'Best for visa.'},
        'Germany': {'icon': '🇩🇪', 'info': 'Country-wide.'},
    }
    total = len(city_counts)
    cities = []
    for city, count in sorted(city_counts.items(), key=lambda x: -x[1]):
        info = city_info.get(city, {'icon': '📍', 'info': 'Tech hub.'})
        cities.append({'icon': info['icon'], 'name': city, 'info': info['info'], 'jobs': f'{count}/{total} jobs'})

    data = {
        'jobs': rows_to_list(conn.execute('SELECT * FROM jobs WHERE deleted=0 ORDER BY score DESC').fetchall()),
        'summaries': rows_to_list(conn.execute('SELECT * FROM summaries ORDER BY score DESC').fetchall()),
        'resumes': rows_to_list(conn.execute('SELECT * FROM resumes').fetchall()),
        'techLearning': rows_to_list(conn.execute('SELECT * FROM tech_learning ORDER BY priority').fetchall()),
        'techStack': rows_to_list(conn.execute('SELECT * FROM tech_stack ORDER BY level DESC').fetchall()),
        'cities': cities,
        'dashboardInsights': rows_to_list(conn.execute('SELECT * FROM dashboard_insights ORDER BY type, priority').fetchall()),
    }
    conn.close()
    return stream_json(data)

@app.route('/api/metadata')
def get_metadata():
    conn = get_db()
    rows = conn.execute('SELECT key, value, updated_at FROM metadata').fetchall()
    conn.close()
    meta = {}
    for row in rows:
        r = dict(row)
        meta[r['key']] = {'value': r['value'], 'updated_at': r['updated_at']}
    return jsonify(meta)

@app.route('/api/metadata/<key>', methods=['PUT'])
def update_metadata(key):
    data = request.get_json()
    value = data.get('value', '')
    conn = get_db()
    conn.execute('''INSERT OR REPLACE INTO metadata (key, value, updated_at) VALUES (?, ?, ?)''',
        (key, value, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({'status': 'updated', 'key': key})

@app.route('/api/stream/all')
def stream_all():
    """Streaming version — sends data incrementally."""
    conn = get_db()
    def generate():
        yield '{"jobs":['
        rows = conn.execute('SELECT * FROM jobs WHERE deleted=0 ORDER BY score DESC').fetchall()
        for i, row in enumerate(rows):
            if i > 0: yield ','
            yield json.dumps(dict(row), ensure_ascii=False)
        yield '],"summaries":['
        rows = conn.execute('SELECT * FROM summaries ORDER BY score DESC').fetchall()
        for i, row in enumerate(rows):
            if i > 0: yield ','
            yield json.dumps(dict(row), ensure_ascii=False)
        yield '],"resumes":['
        rows = conn.execute('SELECT * FROM resumes').fetchall()
        for i, row in enumerate(rows):
            if i > 0: yield ','
            yield json.dumps(dict(row), ensure_ascii=False)
        yield '],"techLearning":['
        rows = conn.execute('SELECT * FROM tech_learning ORDER BY priority').fetchall()
        for i, row in enumerate(rows):
            if i > 0: yield ','
            yield json.dumps(dict(row), ensure_ascii=False)
        yield '],"techStack":['
        rows = conn.execute('SELECT * FROM tech_stack ORDER BY level DESC').fetchall()
        for i, row in enumerate(rows):
            if i > 0: yield ','
            yield json.dumps(dict(row), ensure_ascii=False)
        yield '],"cities":['
        # Build cities dynamically from job locations
        job_rows = conn.execute('SELECT location, locations FROM jobs').fetchall()
        city_counts = {}
        for row in job_rows:
            r = dict(row)
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
        city_info = {
            'Berlin': {'icon': '🐻', 'info': 'Largest tech hub.'},
            'Munich': {'icon': '🦁', 'info': 'Highest salaries.'},
            'Hamburg': {'icon': '🎵', 'info': 'Growing tech scene.'},
            'Heidelberg': {'icon': '🏛️', 'info': 'Enterprise AI.'},
            'Frankfurt': {'icon': '🏦', 'info': 'FinTech capital.'},
            'Cologne': {'icon': '🗼', 'info': 'Media & commerce.'},
            'Stuttgart': {'icon': '🏭', 'info': 'Engineering.'},
            'Remote': {'icon': '🏠', 'info': 'Best for visa.'},
            'Remote Germany': {'icon': '🏠', 'info': 'Best for visa.'},
            'Germany': {'icon': '🇩🇪', 'info': 'Country-wide.'},
        }
        total = len(city_counts)
        first = True
        for city, count in sorted(city_counts.items(), key=lambda x: -x[1]):
            info = city_info.get(city, {'icon': '📍', 'info': 'Tech hub.'})
            if not first: yield ','
            first = False
            yield json.dumps({'icon': info['icon'], 'name': city, 'info': info['info'], 'jobs': f'{count}/{total} jobs'}, ensure_ascii=False)
        yield '],"dashboardInsights":['
        rows = conn.execute('SELECT * FROM dashboard_insights ORDER BY type, priority').fetchall()
        for i, row in enumerate(rows):
            if i > 0: yield ','
            yield json.dumps(dict(row), ensure_ascii=False)
        yield ']}'
        conn.close()
    return Response(generate(), mimetype='application/json')

# --- Serve React app ---

@app.route('/')
def serve():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
@app.route('/api/jobs/<int:num>/rescore', methods=['POST'])
def rescore_job(num):
    """Re-score a single job — reset its pending entry and reprocess (updates existing job)."""
    conn = get_db()
    job = conn.execute('SELECT * FROM jobs WHERE num=?', (num,)).fetchone()
    if not job:
        conn.close()
        return jsonify({'error': 'Job not found'}), 404
    j = dict(job)
    url = j['url']
    company = j.get('company', '')
    role = j.get('role', '')
    # Find or create pending entry
    row = conn.execute('SELECT id FROM pending_jobs WHERE url=?', (url,)).fetchone()
    if row:
        pid = dict(row)['id']
        conn.execute('''UPDATE pending_jobs SET status='queued', error=NULL, source='rescore',
            company=?, step_fetch=0, step_analyze=0, step_resume=0, step_db=0, step_done=0,
            workflow_log='[]', updated_at=? WHERE id=?''',
            (company, datetime.now().isoformat(), pid))
    else:
        cur = conn.execute('INSERT INTO pending_jobs (url, source, company) VALUES (?, ?, ?)', (url, 'rescore', company))
        pid = cur.lastrowid
    conn.commit()
    conn.close()
    threading.Thread(target=process_job, args=(pid,), daemon=True).start()
    return jsonify({'status': 'rescoring', 'pid': pid, 'num': num, 'company': company})

@app.route('/api/jobs/rescore-all', methods=['POST'])
def rescore_all():
    """Re-score all jobs — reset and reprocess each (updates existing jobs)."""
    conn = get_db()
    jobs = conn.execute('SELECT num, url FROM jobs').fetchall()
    conn.close()
    count = 0
    for job in jobs:
        j = dict(job)
        conn = get_db()
        row = conn.execute('SELECT id FROM pending_jobs WHERE url=?', (j['url'],)).fetchone()
        if row:
            pid = dict(row)['id']
            conn.execute('''UPDATE pending_jobs SET status='queued', error=NULL, source='rescore',
                step_fetch=0, step_analyze=0, step_resume=0, step_db=0, step_done=0,
                workflow_log='[]', updated_at=? WHERE id=?''',
                (datetime.now().isoformat(), pid))
        else:
            cur = conn.execute('INSERT INTO pending_jobs (url, source) VALUES (?, ?)', (j['url'], 'rescore'))
            pid = cur.lastrowid
        conn.commit()
        conn.close()
        threading.Thread(target=process_job, args=(pid,), daemon=True).start()
        count += 1
    return jsonify({'status': 'rescoring', 'count': count})

def static_proxy(path):
    file_path = os.path.join(app.static_folder, path)
    if os.path.isfile(file_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
