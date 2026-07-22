"""Scoring rules routes."""

from datetime import datetime

from flask import Blueprint, jsonify, request

from database import get_db
from utils import stream_json

bp = Blueprint('rules', __name__)


@bp.route('/api/rules')
def get_rules():
    conn = get_db()
    rows = conn.execute('SELECT * FROM preferences ORDER BY rule_type, category, priority').fetchall()
    conn.close()
    result = {}
    for row in rows:
        r = dict(row)
        rt = r.get('rule_type', 'job')
        if rt not in result:
            result[rt] = []
        result[rt].append(r)
    return stream_json(result)


@bp.route('/api/rules', methods=['POST'])
def create_rule():
    data = request.get_json()
    conn = get_db()
    for item in data.get('rules', []):
        conn.execute('''INSERT OR REPLACE INTO preferences (category, rule_type, key, value, description, priority, score_weight, enabled)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (item['category'], item.get('rule_type', 'job'), item['key'], item['value'],
             item.get('description', ''), item.get('priority', 0),
             item.get('score_weight', 0), item.get('enabled', 1)))
    conn.commit()
    conn.close()
    return jsonify({'status': 'updated'})


@bp.route('/api/rules/<int:id>', methods=['PUT'])
def update_rule(id):
    data = request.get_json()
    conn = get_db()
    fields = []
    values = []
    for key in ['value', 'description', 'priority', 'enabled', 'rule_type', 'score_weight']:
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


@bp.route('/api/rules/<int:id>', methods=['DELETE'])
def delete_rule(id):
    conn = get_db()
    conn.execute('DELETE FROM preferences WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted'})
