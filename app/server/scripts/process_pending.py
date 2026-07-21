import sqlite3
import json
import os
from datetime import datetime

_file_dir = os.path.dirname(os.path.abspath(__file__))
_db_path = os.environ.get('DB_PATH', os.path.join(_file_dir, 'db', 'jobs.db'))
DB_PATH = _db_path if os.path.isabs(_db_path) else os.path.join(_file_dir, _db_path)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def update_step(pending_id, step, value, status=None, company=None, job_num=None, error=None):
    conn = get_db()
    fields = [f'{step}=?']
    values = [value]
    if status:
        fields.append('status=?')
        values.append(status)
    if company:
        fields.append('company=?')
        values.append(company)
    if job_num:
        fields.append('job_num=?')
        values.append(job_num)
    if error:
        fields.append('error=?')
        values.append(error)
    fields.append('updated_at=?')
    values.append(datetime.now().isoformat())
    values.append(pending_id)
    conn.execute(f'UPDATE pending_jobs SET {",".join(fields)} WHERE id=?', values)
    conn.commit()
    conn.close()

def get_pending():
    conn = get_db()
    rows = conn.execute("SELECT * FROM pending_jobs WHERE status NOT IN ('done','failed') ORDER BY created_at").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_job(data):
    import json
    conn = get_db()
    c = conn.cursor()
    locations = data.get('locations', [])
    if isinstance(locations, str):
        locations = [locations] if locations else []
    c.execute('''INSERT OR REPLACE INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (data['num'], data['company'], data['role'], data['location'], data['match'],
         data['score'], data['salary'], data['stack'], data['visa'], data['applicants'],
         data['posted'], data['industry'], data['domain'], data['notes'], data['action'], data['url'],
         data.get('work_type', 'On-site'), data.get('workflow_log', '[]'), json.dumps(locations)))
    conn.commit()
    conn.close()

def add_summary(data):
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO summaries VALUES (?,?,?,?,?,?,?,?,?)''',
        (data['num'], data['company'], data['match'], data['score'],
         data['summary'], data['stack'], data['resumeFit'], data['note'], data['url']))
    conn.commit()
    conn.close()

def add_resume(data):
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO resumes (id, title, company, role, content, version, raw_text, created_at, job_num) VALUES (?,?,?,?,?,?,?,?,?)''',
        (data['id'], data.get('title'),
         data.get('company'), data.get('role'), data.get('content'),
         data.get('version', 1), data.get('raw_text'), data.get('created_at'), data.get('job_num')))
    conn.commit()
    conn.close()

def get_next_job_num():
    conn = get_db()
    row = conn.execute("SELECT MAX(num) FROM jobs").fetchone()
    conn.close()
    return (row[0] or 0) + 1

if __name__ == '__main__':
    pending = get_pending()
    print(f'Pending jobs: {len(pending)}')
    for p in pending:
        print(f"  [{p['id']}] {p['source']} | {p['status']} | {p['url'][:60]}...")
