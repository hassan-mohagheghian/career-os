#!/usr/bin/env python3
"""Analyze jobs database and generate dashboard insights."""

import sqlite3
import json
import os
from collections import Counter
from typing import List, Dict, Any
import re

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
_file_dir = os.path.dirname(os.path.abspath(__file__))
_db_path = os.environ.get('DB_PATH', os.path.join(_file_dir, 'db', 'jobs.db'))
DB_PATH = _db_path if os.path.isabs(_db_path) else os.path.join(_file_dir, _db_path)
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

def connect_db():
    """Connect to SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_jobs(conn) -> List[Dict[str, Any]]:
    """Get all non-deleted jobs."""
    cursor = conn.execute("""
        SELECT num, company, role, location, match, score, salary, stack, visa, 
               applicants, posted, industry, domain, notes, action, url, work_type,
               created_at, posted_at
        FROM jobs 
        WHERE deleted=0
        ORDER BY score DESC
    """)
    return [dict(row) for row in cursor.fetchall()]

def analyze_skills(jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze skill requirements across jobs."""
    skill_keywords = {
        'Python': ['python'],
        'Django': ['django'],
        'FastAPI': ['fastapi'],
        'Flask': ['flask'],
        'TypeScript': ['typescript', 'ts'],
        'JavaScript': ['javascript', 'js'],
        'React': ['react', 'nextjs'],
        'Node.js': ['node', 'nodejs'],
        'Go': ['golang', 'go,'],
        'Rust': ['rust'],
        'PostgreSQL': ['postgresql', 'postgres'],
        'Docker': ['docker'],
        'Kubernetes': ['kubernetes', 'k8s'],
        'AWS': ['aws'],
        'Azure': ['azure'],
        'GCP': ['gcp', 'google cloud'],
        'Redis': ['redis'],
        'Kafka': ['kafka'],
        'SQLAlchemy': ['sqlalchemy'],
        'Celery': ['celery'],
        'Pydantic': ['pydantic'],
    }
    
    skill_counts = {}
    for skill, keywords in skill_keywords.items():
        count = 0
        for job in jobs:
            stack = (job.get('stack', '') or '').lower()
            role = (job.get('role', '') or '').lower()
            notes = (job.get('notes', '') or '').lower()
            text = f"{stack} {role} {notes}"
            if any(kw in text for kw in keywords):
                count += 1
        skill_counts[skill] = count
    
    return skill_counts

def analyze_visa(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Analyze visa sponsorship ratings."""
    visa_companies = []
    for job in jobs:
        visa = job.get('visa', '') or ''
        company = job.get('company', '')
        score = job.get('score', 0)
        
        if visa in ['BEST', 'Strong', 'High']:
            visa_companies.append({
                'company': company,
                'visa': visa,
                'note': f"Score: {score}, Strong sponsorship program"
            })
        elif 'visa sponsorship' in (job.get('notes', '') or '').lower():
            visa_companies.append({
                'company': company,
                'visa': 'Strong',
                'note': f"Score: {score}, Mentions visa sponsorship"
            })
    
    return visa_companies

def analyze_urgency(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Analyze application urgency based on score and posting freshness."""
    urgency = []
    for job in jobs:
        score = job.get('score', 0)
        posted_at = job.get('posted_at', '')
        company = job.get('company', '')
        role = job.get('role', '')
        action = job.get('action', '') or ''
        notes = job.get('notes', '') or ''
        
        reasons = []
        if score and score >= 75:
            reasons.append(f"High score ({score})")
        
        if 'Apply immediately' in action:
            reasons.append("Marked for immediate application")
        
        if 'fresh' in notes.lower() or 'recent' in notes.lower():
            reasons.append("Fresh posting")
        
        if reasons:
            urgency.append({
                'company': company,
                'reason': f"{role}: {', '.join(reasons)}"
            })
    
    return urgency

def generate_strategy(jobs: List[Dict[str, Any]], skill_counts: Dict[str, int]) -> List[Dict[str, str]]:
    """Generate strategic insights."""
    strategy = []
    
    # Get top 5 companies by score
    top_5 = jobs[:5]
    top_5_list = ', '.join([f"{j['company']} ({j['score']})" for j in top_5])
    strategy.append({
        'icon': '🎯',
        'title': 'Apply Top 5 First',
        'description': f"Top matches: {top_5_list}. These have the highest compatibility with the candidate's profile."
    })
    
    # Visa strategy
    best_visa = [j for j in jobs if j.get('visa') in ['BEST', 'Strong', 'High']]
    strategy.append({
        'icon': '🌍',
        'title': 'Visa Strategy',
        'description': f"{len(best_visa)} companies have BEST/Strong visa ratings. Focus on Cara Care, Audatic, Jobgether for best sponsorship paths."
    })
    
    # Speed matters - recent postings
    recent = [j for j in jobs if j.get('posted_at') and '2026-07' in str(j['posted_at'])]
    if recent:
        recent_list = ', '.join([j['company'] for j in recent[:3]])
        strategy.append({
            'icon': '⚡',
            'title': 'Speed Matters',
            'description': f"Recent postings needing immediate action: {recent_list}. These are fresh and competition is building."
        })
    else:
        strategy.append({
            'icon': '⚡',
            'title': 'Speed Matters',
            'description': "Focus on high-scoring jobs (75+) as they're likely to fill quickly. Apply within 48 hours of seeing."
        })
    
    # Company = Visa
    visa_companies = [j for j in jobs if j.get('visa') in ['BEST', 'Strong']]
    company_visa_list = ', '.join([j['company'] for j in visa_companies[:4]])
    strategy.append({
        'icon': '🏢',
        'title': 'Company = Visa',
        'description': f"Companies with established sponsorship: {company_visa_list}. These have proven track records."
    })
    
    # Python edge
    python_jobs = skill_counts.get('Python', 0)
    strategy.append({
        'icon': '🐍',
        'title': 'Python Edge',
        'description': f"{python_jobs}/{len(jobs)} jobs require Python. 9+ years of experience gives strong competitive advantage in the market."
    })
    
    # Add one more strategy about Django/FastAPI
    django_jobs = skill_counts.get('Django', 0)
    fastapi_jobs = skill_counts.get('FastAPI', 0)
    if django_jobs > 0 or fastapi_jobs > 0:
        strategy.append({
            'icon': '🛠️',
            'title': 'Framework Advantage',
            'description': f"{django_jobs} Django + {fastapi_jobs} FastAPI jobs. Expertise in both frameworks is highly valued."
        })
    
    return strategy

def generate_strengths_weaknesses(skill_counts: Dict[str, int], total_jobs: int) -> tuple:
    """Generate strengths and weaknesses based on candidate's skills."""
    # Candidate's skills based on profile
    candidate_skills = {
        'Python': True,  # 9+ years
        'Django': True,
        'FastAPI': True,
        'Flask': True,
        'PostgreSQL': True,
        'Docker': True,
        'AWS': True,
        'Redis': True,
        'SQLAlchemy': True,
        'Pydantic': True,
        'JavaScript': True,  # Basic
    }
    
    strengths = []
    weaknesses = []
    
    for skill, count in skill_counts.items():
        if count == 0:
            continue
            
        if skill in candidate_skills:
            strengths.append({
                'name': skill,
                'detail': f"{count}/{total_jobs} jobs require {skill} — strong experience"
            })
        else:
            weaknesses.append({
                'name': skill,
                'detail': f"{count}/{total_jobs} jobs require {skill} — gaps or limited experience"
            })
    
    # Add German language analysis
    german_count = 0
    for job in jobs_list:
        notes = (job.get('notes', '') or '').lower()
        if 'german' in notes or 'deutsch' in notes:
            german_count += 1
    
    if german_count > 0:
        weaknesses.append({
            'name': 'German C1',
            'detail': f"{german_count}/{total_jobs} jobs mention German requirement — focus on English-only roles"
        })
    
    # Sort by count
    strengths.sort(key=lambda x: int(x['detail'].split('/')[0]), reverse=True)
    weaknesses.sort(key=lambda x: int(x['detail'].split('/')[0]), reverse=True)
    
    return strengths[:5], weaknesses[:5]

def main():
    conn = connect_db()
    try:
        global jobs_list
        jobs_list = get_all_jobs(conn)
        
        print(f"Total jobs analyzed: {len(jobs_list)}")
        
        # Analyze skills
        skill_counts = analyze_skills(jobs_list)
        print("\nSkill counts:")
        for skill, count in sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {skill}: {count}")
        
        # Generate all insights
        strategy = generate_strategy(jobs_list, skill_counts)
        strengths, weaknesses = generate_strengths_weaknesses(skill_counts, len(jobs_list))
        visa_companies = analyze_visa(jobs_list)
        apply_urgency = analyze_urgency(jobs_list)
        
        # Create final JSON structure
        dashboard_insights = {
            'strategy': strategy,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'visa_companies': visa_companies,
            'apply_urgency': apply_urgency
        }
        
        # Save to file
        output_path = os.path.join(DATA_DIR, 'dashboard_insights_0.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dashboard_insights, f, indent=2, ensure_ascii=False)
        
        print(f"\nDashboard insights saved to: {output_path}")
        print(f"Strategy items: {len(strategy)}")
        print(f"Strengths: {len(strengths)}")
        print(f"Weaknesses: {len(weaknesses)}")
        print(f"Visa companies: {len(visa_companies)}")
        print(f"Apply urgency: {len(apply_urgency)}")
        
    finally:
        conn.close()

if __name__ == '__main__':
    main()