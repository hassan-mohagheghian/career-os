#!/usr/bin/env python3
"""Analyze jobs database and generate dashboard insights."""

import json
import os
from collections import Counter
from typing import List, Dict, Any
import re

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
_file_dir = os.path.dirname(os.path.abspath(__file__))
_db_path = os.environ.get('DB_PATH', os.path.join(_file_dir, 'db', 'jobs.db'))
DB_PATH = _db_path if os.path.isabs(_db_path) else os.path.join(_file_dir, _db_path)
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

import sys
sys.path.insert(0, os.path.join(_file_dir, '..'))
from infrastructure.database.sqlalchemy_config import Base
import infrastructure.database.models.job_model
from infrastructure.database.models.job_model import JobModel


def get_session():
    engine = create_engine(f"sqlite:///{DB_PATH}")
    Session = sessionmaker(bind=engine)
    return Session(), engine


def get_all_jobs(session) -> List[Dict[str, Any]]:
    rows = session.query(JobModel).filter(JobModel.deleted == 0).order_by(JobModel.score.desc()).all()
    return [{
        'num': r.num, 'company': r.company, 'role': r.role, 'location': r.location,
        'match': r.match, 'score': r.score, 'salary': r.salary, 'stack': r.stack,
        'visa': r.visa, 'applicants': r.applicants, 'posted': r.posted,
        'industry': r.industry, 'domain': r.domain, 'notes': r.notes,
        'action': r.action, 'url': r.url, 'work_type': r.work_type,
        'created_at': r.created_at, 'posted_at': r.posted_at,
    } for r in rows]


def analyze_skills(jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    skill_keywords = {
        'Python': ['python'], 'Django': ['django'], 'FastAPI': ['fastapi'],
        'Flask': ['flask'], 'TypeScript': ['typescript', 'ts'],
        'JavaScript': ['javascript', 'js'], 'React': ['react', 'nextjs'],
        'Node.js': ['node', 'nodejs'], 'Go': ['golang', 'go,'], 'Rust': ['rust'],
        'PostgreSQL': ['postgresql', 'postgres'], 'Docker': ['docker'],
        'Kubernetes': ['kubernetes', 'k8s'], 'AWS': ['aws'], 'Azure': ['azure'],
        'GCP': ['gcp', 'google cloud'], 'Redis': ['redis'], 'Kafka': ['kafka'],
        'SQLAlchemy': ['sqlalchemy'], 'Celery': ['celery'], 'Pydantic': ['pydantic'],
    }
    skill_counts = {}
    for skill, keywords in skill_keywords.items():
        count = sum(1 for job in jobs if any(kw in f"{(job.get('stack', '') or '')} {(job.get('role', '') or '')} {(job.get('notes', '') or '')}".lower() for kw in keywords))
        skill_counts[skill] = count
    return skill_counts


def analyze_visa(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    visa_companies = []
    for job in jobs:
        visa = job.get('visa', '') or ''
        if visa in ['BEST', 'Strong', 'High']:
            visa_companies.append({'company': job.get('company', ''), 'visa': visa, 'note': f"Score: {job.get('score', 0)}, Strong sponsorship program"})
        elif 'visa sponsorship' in (job.get('notes', '') or '').lower():
            visa_companies.append({'company': job.get('company', ''), 'visa': 'Strong', 'note': f"Score: {job.get('score', 0)}, Mentions visa sponsorship"})
    return visa_companies


def analyze_urgency(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    urgency = []
    for job in jobs:
        reasons = []
        if job.get('score', 0) and job['score'] >= 75:
            reasons.append(f"High score ({job['score']})")
        if 'Apply immediately' in (job.get('action', '') or ''):
            reasons.append("Marked for immediate application")
        if 'fresh' in (job.get('notes', '') or '').lower() or 'recent' in (job.get('notes', '') or '').lower():
            reasons.append("Fresh posting")
        if reasons:
            urgency.append({'company': job.get('company', ''), 'reason': f"{job.get('role', '')}: {', '.join(reasons)}"})
    return urgency


def generate_strategy(jobs, skill_counts):
    strategy = []
    top_5 = jobs[:5]
    strategy.append({'icon': '🎯', 'title': 'Apply Top 5 First', 'description': f"Top matches: {', '.join([f\"{j['company']} ({j['score']})\" for j in top_5])}. These have the highest compatibility with the candidate's profile."})
    best_visa = [j for j in jobs if j.get('visa') in ['BEST', 'Strong', 'High']]
    strategy.append({'icon': '🌍', 'title': 'Visa Strategy', 'description': f"{len(best_visa)} companies have BEST/Strong visa ratings."})
    recent = [j for j in jobs if j.get('posted_at') and '2026-07' in str(j['posted_at'])]
    if recent:
        strategy.append({'icon': '⚡', 'title': 'Speed Matters', 'description': f"Recent postings needing immediate action: {', '.join([j['company'] for j in recent[:3]])}."})
    else:
        strategy.append({'icon': '⚡', 'title': 'Speed Matters', 'description': "Focus on high-scoring jobs (75+) as they're likely to fill quickly."})
    python_jobs = skill_counts.get('Python', 0)
    strategy.append({'icon': '🐍', 'title': 'Python Edge', 'description': f"{python_jobs}/{len(jobs)} jobs require Python."})
    return strategy


def generate_strengths_weaknesses(skill_counts, total_jobs, jobs):
    candidate_skills = {'Python': True, 'Django': True, 'FastAPI': True, 'Flask': True, 'PostgreSQL': True, 'Docker': True, 'AWS': True, 'Redis': True, 'SQLAlchemy': True, 'Pydantic': True, 'JavaScript': True}
    strengths, weaknesses = [], []
    for skill, count in skill_counts.items():
        if count == 0:
            continue
        entry = {'name': skill, 'detail': f"{count}/{total_jobs} jobs require {skill}"}
        if skill in candidate_skills:
            strengths.append(entry)
        else:
            weaknesses.append(entry)
    strengths.sort(key=lambda x: int(x['detail'].split('/')[0]), reverse=True)
    weaknesses.sort(key=lambda x: int(x['detail'].split('/')[0]), reverse=True)
    return strengths[:5], weaknesses[:5]


def main():
    session, engine = get_session()
    try:
        jobs = get_all_jobs(session)
        print(f"Total jobs analyzed: {len(jobs)}")
        skill_counts = analyze_skills(jobs)
        strategy = generate_strategy(jobs, skill_counts)
        strengths, weaknesses = generate_strengths_weaknesses(skill_counts, len(jobs), jobs)
        visa_companies = analyze_visa(jobs)
        apply_urgency = analyze_urgency(jobs)
        dashboard_insights = {'strategy': strategy, 'strengths': strengths, 'weaknesses': weaknesses, 'visa_companies': visa_companies, 'apply_urgency': apply_urgency}
        output_path = os.path.join(DATA_DIR, 'dashboard_insights_0.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dashboard_insights, f, indent=2, ensure_ascii=False)
        print(f"\nDashboard insights saved to: {output_path}")
    finally:
        session.close()
        engine.dispose()


if __name__ == '__main__':
    main()
