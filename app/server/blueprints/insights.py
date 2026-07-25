"""Insights API routes."""

import json
import re
import threading
from collections import Counter

from flask import Blueprint, jsonify, request

bp = Blueprint('insights', __name__)

INSIGHT_TYPES = ['overview', 'opportunities', 'companies', 'skills', 'market', 'networking', 'skills_intel']


@bp.route('/api/insights', methods=['GET'])
def get_all():
    """Get all latest insights sections.
    ---
    tags: [Insights]
    responses:
      200:
        description: All intelligence sections (overview, opportunities, companies, market, networking, skills_intel)
    """
    from services.insights import get_latest
    data = get_latest()
    return jsonify(data or {})


@bp.route('/api/insights/<section>', methods=['GET'])
def get_section(section):
    """Get latest insights for a specific section.
    ---
    tags: [Insights]
    parameters:
      - name: section
        in: path
        required: true
        type: string
        enum: [overview, opportunities, companies, market, networking, skills_intel]
    responses:
      200:
        description: Section intelligence data
      404:
        description: No intelligence found for this section
    """
    if section not in INSIGHT_TYPES:
        return jsonify({'error': f'Invalid section: {section}'}), 400
    from services.insights import get_latest
    data = get_latest(section)
    if data:
        return jsonify(data)
    return jsonify({'error': f'No {section} intelligence found'}), 404


@bp.route('/api/insights/runs', methods=['GET'])
def get_runs():
    """Get recent insight generation runs with total count for infinite scroll."""
    from services.insights import get_runs
    section = request.args.get('section')
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    result = get_runs(section, limit, offset)
    return jsonify(result)


@bp.route('/api/insights/progress', methods=['GET'])
def get_progress():
    """Get current analysis progress (real-time status)."""
    from services.insights import get_progress as _get_progress
    return jsonify(_get_progress())


@bp.route('/api/insights/refresh', methods=['POST'])
def refresh_all():
    """Generate all insights sections in background.
    ---
    tags: [Insights]
    responses:
      200:
        description: Generation started
      409:
        description: Analysis already running
    """
    from services.insights import generate_all, is_running
    running, info = is_running()
    if running:
        return jsonify({
            'status': 'already_running',
            'message': f'Analysis already in progress ({info["type"]})',
            'running': info
        }), 409
    def _run():
        generate_all()
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return jsonify({'status': 'started', 'message': 'Insights generation started'})


@bp.route('/api/insights/<section>/refresh', methods=['POST'])
def refresh_section(section):
    """Generate a single insights section in background."""
    if section not in INSIGHT_TYPES:
        return jsonify({'error': f'Invalid section: {section}'}), 400
    from services.insights import generate_section, is_running
    running, info = is_running()
    if running:
        return jsonify({
            'status': 'already_running',
            'message': f'Analysis already in progress ({info["type"]})',
            'running': info
        }), 409
    def _run():
        generate_section(section)
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return jsonify({'status': 'started', 'section': section, 'message': f'{section} intelligence generation started'})


@bp.route('/api/insights/status', methods=['GET'])
def get_status():
    """Get current generation status for all sections."""
    from services.insights import get_runs, is_running
    running, run_info = is_running()
    status = {'_running': running, '_currentRun': run_info}
    for section in INSIGHT_TYPES:
        result = get_runs(section, limit=1)
        items = result.get('items', []) if isinstance(result, dict) else result
        if items:
            latest = items[0]
            status[section] = {
                'status': latest['status'],
                'lastRun': latest['started_at'],
                'completedAt': latest.get('completed_at'),
                'error': latest.get('error_message')
            }
        else:
            status[section] = {'status': 'never', 'lastRun': None}
    return jsonify(status)


@bp.route('/api/insights/skills-intel', methods=['GET'])
def get_skills_intel():
    """Get the latest Skills Intelligence Report.
    ---
    tags: [Skills]
    responses:
      200:
        description: Skills intelligence data with strengths, gaps, recommendations
      404:
        description: No skills intelligence found
    """
    from services.insights import get_latest
    data = get_latest('skills_intel')
    if data:
        return jsonify(data)
    return jsonify({'error': 'No skills intelligence found. Run refresh first.'}), 404


@bp.route('/api/insights/skills-intel/refresh', methods=['POST'])
def refresh_skills_intel():
    """Generate the Skills Intelligence Report in background."""
    from services.insights import generate_skills_intel, is_running
    running, info = is_running()
    if running:
        return jsonify({
            'status': 'already_running',
            'message': f'Analysis already in progress ({info["type"]})',
            'running': info
        }), 409
    def _run():
        generate_skills_intel()
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return jsonify({'status': 'started', 'message': 'Skills intelligence generation started'})


@bp.route('/api/insights/cancel', methods=['POST'])
def cancel():
    """Cancel the currently running insights analysis.
    ---
    tags: [Insights]
    responses:
      200:
        description: Analysis cancelled
    """
    from services.insights import cancel_run, is_running
    running, info = is_running()
    if not running:
        return jsonify({'status': 'idle', 'message': 'No analysis running'}), 200
    cancelled = cancel_run()
    if cancelled:
        return jsonify({'status': 'cancelled', 'message': 'Analysis cancelled'})
    return jsonify({'status': 'error', 'message': 'Could not cancel analysis'}), 500


def _parse_stack_skills(stack_text):
    """Parse a stack string into individual skill names."""
    if not stack_text:
        return []
    # Split on common delimiters
    parts = re.split(r'[,;|/]+', stack_text)
    skills = []
    for p in parts:
        s = p.strip()
        if s and len(s) < 60:  # skip unreasonable entries
            skills.append(s)
    return skills


def _get_dashboard_data():
    """Aggregate skills intelligence data for the dashboard."""
    from database import get_db, row_to_dict
    from services.insights import get_latest

    conn = get_db()

    # 1. Get all visible skills
    skill_rows = conn.execute(
        "SELECT * FROM skills WHERE hidden=0 ORDER BY level DESC"
    ).fetchall()
    skills = [row_to_dict(r) for r in skill_rows]

    # 2. Get latest skills_intel report
    intel_data = None
    intel_row = conn.execute(
        "SELECT data_json, score, summary, created_at FROM career_insights "
        "WHERE insight_type='skills_intel' ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    if intel_row:
        intel_data = {
            'data': json.loads(intel_row[0]) if intel_row[0] else {},
            'score': intel_row[1],
            'summary': intel_row[2],
            'created_at': intel_row[3],
        }

    # 3. Get roadmap progress for all skills
    roadmap_rows = conn.execute(
        "SELECT sr.skill_name, "
        "COUNT(*) as total, "
        "SUM(CASE WHEN srp.completed=1 THEN 1 ELSE 0 END) as completed "
        "FROM skill_roadmaps sr "
        "LEFT JOIN skill_roadmap_progress srp ON srp.roadmap_id=sr.id "
        "WHERE sr.parent_id IS NULL "
        "GROUP BY sr.skill_name"
    ).fetchall()
    roadmap_progress = {}
    for r in roadmap_rows:
        total = r[1] or 0
        completed = r[2] or 0
        pct = round(completed / total * 100) if total > 0 else 0
        roadmap_progress[r[0]] = {'total': total, 'completed': completed, 'pct': pct}

    # 4. Get skill relationships count
    rel_count = conn.execute("SELECT COUNT(*) FROM skill_relationships").fetchone()[0]

    # 5. Parse all job stacks to get market skill frequency
    job_rows = conn.execute(
        "SELECT stack FROM jobs WHERE deleted=0 AND stack IS NOT NULL AND stack != ''"
    ).fetchall()
    market_skill_freq = Counter()
    total_jobs = len(job_rows)
    for r in job_rows:
        for sk in _parse_stack_skills(r[0]):
            market_skill_freq[sk] += 1

    # 6. Build category breakdown
    category_stats = {}
    for s in skills:
        cat = s.get('category', 'technical') or 'technical'
        if cat not in category_stats:
            category_stats[cat] = {'count': 0, 'total_demand': 0, 'avg_demand': 0}
        category_stats[cat]['count'] += 1
        category_stats[cat]['total_demand'] += s.get('market_relevance', 0) or 0
    for cat in category_stats:
        c = category_stats[cat]
        c['avg_demand'] = round(c['total_demand'] / c['count']) if c['count'] > 0 else 0
        del c['total_demand']  # don't expose internal field

    # 7. Build gap matrix from intel data
    gap_matrix = []
    intel = intel_data['data'] if intel_data and intel_data.get('data') else {}
    current_state = intel.get('current_state', {})
    recommendations = intel.get('recommendations', [])

    for gap in current_state.get('gaps', []):
        gap_matrix.append({
            'skill': gap.get('skill', ''),
            'category': gap.get('category', ''),
            'market_demand': gap.get('market_demand', 0),
            'current_level': gap.get('current_level', ''),
            'gap': 'high',
            'priority': 'P1',
            'evidence': gap.get('evidence', []),
        })
    for gap in current_state.get('missing', []):
        gap_matrix.append({
            'skill': gap.get('skill', ''),
            'category': gap.get('category', ''),
            'market_demand': gap.get('demand_percentage', 0),
            'current_level': 'none',
            'gap': 'critical',
            'priority': 'P1',
            'evidence': gap.get('evidence', []),
        })

    # 8. Top skills by market demand (from intel or job frequency)
    top_market_skills = []
    if intel.get('recommendations'):
        # Use AI recommendations sorted by market_demand
        sorted_recs = sorted(recommendations, key=lambda r: r.get('market_demand', 0), reverse=True)
        for rec in sorted_recs[:15]:
            top_market_skills.append({
                'skill': rec.get('skill', ''),
                'demand': rec.get('market_demand', 0),
                'priority': rec.get('priority', 'P3'),
                'roi_score': rec.get('roi_score', 0),
            })
    else:
        # Fallback: use job stack frequency
        if total_jobs > 0:
            for sk, freq in market_skill_freq.most_common(15):
                top_market_skills.append({
                    'skill': sk,
                    'demand': round(freq / total_jobs * 100),
                    'priority': 'P2',
                    'roi_score': 0,
                })

    # 9. Summary stats
    strengths = current_state.get('strengths', [])
    gaps = current_state.get('gaps', [])
    missing = current_state.get('missing', [])
    maintain = current_state.get('maintain', [])
    p1_recs = [r for r in recommendations if r.get('priority') == 'P1']

    summary = {
        'total_skills': len(skills),
        'market_skills_count': len(top_market_skills),
        'strengths_count': len(strengths),
        'gaps_count': len(gaps) + len(missing),
        'maintain_count': len(maintain),
        'high_roi_count': len(p1_recs),
        'career_readiness_score': intel.get('summary', {}).get('career_readiness_score', 0) if intel else 0,
        'main_strength': intel.get('summary', {}).get('main_strength', '') if intel else '',
        'biggest_gap': intel.get('summary', {}).get('biggest_gap', '') if intel else '',
        'highest_roi_skill': intel.get('summary', {}).get('highest_roi_skill', '') if intel else '',
        'total_jobs_analyzed': total_jobs,
        'skill_relationships': rel_count,
        'roadmap_skills': len(roadmap_progress),
        'last_generated': intel_data.get('created_at') if intel_data else None,
    }

    # 10. Recommendations with learning path
    top_recommendations = recommendations[:10]

    # 11. Roadmap summary
    roadmap = intel.get('roadmap', {}) if intel else {}

    conn.close()

    return {
        'summary': summary,
        'skills': skills,
        'top_market_skills': top_market_skills,
        'gap_matrix': gap_matrix,
        'category_stats': category_stats,
        'recommendations': top_recommendations,
        'roadmap': roadmap,
        'roadmap_progress': roadmap_progress,
        'intel_report': intel,
    }


@bp.route('/api/skills-intelligence/dashboard', methods=['GET'])
def get_skills_dashboard():
    """Get aggregated skills intelligence dashboard data.
    ---
    tags: [Skills]
    responses:
      200:
        description: Dashboard data with summary, skills, market demand, gaps, recommendations
    """
    data = _get_dashboard_data()
    return jsonify(data)
