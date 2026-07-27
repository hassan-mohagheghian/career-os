"""
Backfill structured descriptions for existing jobs.
Uses LLM service to extract structured info from raw_description.
"""
import os
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_file_dir = os.path.dirname(os.path.abspath(__file__))
_server_dir = os.path.join(_file_dir, '..')
_db_path = os.environ.get('DB_PATH', os.path.join(_server_dir, 'db', 'jobs.db'))
DB_PATH = _db_path if os.path.isabs(_db_path) else os.path.join(_file_dir, _db_path)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

import sys
sys.path.insert(0, os.path.join(_file_dir, '..'))
from infrastructure.database.sqlalchemy_config import Base
import infrastructure.database.models.job_model
from infrastructure.database.models.job_model import JobModel

from ai_compat import get_llm_service

EXTRACT_PROMPT = """Extract structured information from this raw job description.

Raw content:
{raw_content}

Extract the following into JSON and save to {output_file}:

{{
  "company": "Company name",
  "role": "Job title",
  "location": "Primary city only (Berlin, Munich, etc.)",
  "locations": ["City1", "City2"],
  "employment_type": "Full-time|Part-time|Contract|Internship|Temporary",
  "work_types": ["On-site", "Remote", "Hybrid"],
  "salary": "Salary range if mentioned, else 'Not specified'",
  "stack": "Comma-separated tech stack",
  "visa": "BEST|Strong|Good|Moderate|Uncertain",
  "visa_reason": "Why this visa rating",
  "applicants": "Number if mentioned, else 'Not specified'",
  "posted": "Relative time if mentioned, else 'Not specified'",
  "industry": "Industry sector",
  "domain": "Business domain",
  "requirements": ["Must-have 1", "Must-have 2"],
  "nice_to_have": ["Nice-to-have 1", "Nice-to-have 2"],
  "responsibilities": ["Key responsibility 1", "Key responsibility 2"],
  "benefits": ["Benefit 1", "Benefit 2"],
  "company_size": "Size if mentioned",
  "company_description": "Brief company description"
}}

RULES:
- location: ONLY city name, no country/region
- locations: array of city names only
- employment_type: exactly one of Full-time, Part-time, Contract, Internship, Temporary
- work_types: array of On-site, Remote, Hybrid
- stack: extract ALL technologies mentioned
- visa: rate based on evidence in the posting
- requirements: extract ALL must-have skills/qualifications
- nice_to_have: extract preferred but not required skills
- responsibilities: top 3-5 key duties
- benefits: perks, insurance, remote options, learning budget, etc.
- Keep all fields concise but complete"""


def get_session():
    engine = create_engine(f"sqlite:///{DB_PATH}")
    Session = sessionmaker(bind=engine)
    return Session(), engine


def extract_structured(raw_text, num):
    output_file = os.path.join(PROJECT_ROOT, 'data', f'structured_{num}.json')
    prompt = EXTRACT_PROMPT.format(raw_content=raw_text[:5000], output_file=output_file)
    try:
        llm = get_llm_service()
        resp = llm.generate_structured(prompt, context={"result_file": output_file, "pid": str(num)}, timeout=60)
        return resp.content
    except Exception as e:
        print(f"  LLM error: {e}")
    return None


def main():
    session, engine = get_session()
    try:
        rows = session.query(JobModel).filter(
            JobModel.deleted == 0,
            JobModel.raw_description.isnot(None),
            JobModel.structured_description.is_(None)
        ).order_by(JobModel.num).all()
        print(f"Found {len(rows)} jobs needing structured extraction")
        success, failed = 0, 0
        for i, job in enumerate(rows):
            print(f"#{job.num:03d} {job.company}: extracting...")
            structured_json = extract_structured(job.raw_description, job.num)
            if structured_json:
                job.structured_description = structured_json
                session.commit()
                success += 1
            else:
                failed += 1
            if i < len(rows) - 1:
                time.sleep(3 + (i % 3))
        print(f"\nDone: {success} extracted, {failed} failed")
    finally:
        session.close()
        engine.dispose()


if __name__ == '__main__':
    main()
