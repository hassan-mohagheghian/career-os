"""
Backfill structured descriptions for existing jobs.
Uses mimo to extract structured info from raw_description.
Includes delay between requests to avoid rate limiting.
"""
import sqlite3
import os
import json
import time
import subprocess

DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), 'db', 'jobs.db'))
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
MIMO_BIN = os.path.expanduser('~/.mimocode/bin/mimo')

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

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def extract_structured(raw_text, num):
    """Extract structured job info from raw description using mimo."""
    output_file = os.path.join(PROJECT_ROOT, 'data', f'structured_{num}.json')
    prompt = EXTRACT_PROMPT.format(raw_content=raw_text[:5000], output_file=output_file)

    proc = subprocess.run(
        [MIMO_BIN, 'run', prompt, '--format', 'json', '--dangerously-skip-permissions'],
        cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=60,
        env={**os.environ, 'NO_COLOR': '1'}
    )

    if proc.returncode == 0 and os.path.exists(output_file):
        try:
            with open(output_file) as f:
                structured = json.load(f)
            os.remove(output_file)
            return json.dumps(structured, ensure_ascii=False)
        except Exception as e:
            print(f"  Parse error: {e}")
            if os.path.exists(output_file):
                os.remove(output_file)
    return None

def main():
    conn = get_db()

    # Find jobs with raw_description but without structured_description
    rows = conn.execute(
        '''SELECT num, company, raw_description FROM jobs
           WHERE deleted=0 AND raw_description IS NOT NULL AND structured_description IS NULL
           ORDER BY num'''
    ).fetchall()

    print(f"Found {len(rows)} jobs needing structured extraction")

    success = 0
    failed = 0

    for i, row in enumerate(rows):
        r = dict(row)
        num = r['num']
        company = r['company']
        raw_text = r['raw_description']

        print(f"#{num:03d} {company}: extracting...")
        structured_json = extract_structured(raw_text, num)

        if structured_json:
            conn.execute('UPDATE jobs SET structured_description=? WHERE num=?',
                        (structured_json, num))
            conn.commit()
            success += 1
            print(f"  Success ({len(structured_json)} chars)")
        else:
            failed += 1
            print(f"  Failed")

        # Delay between requests (3-5 seconds)
        if i < len(rows) - 1:
            delay = 3 + (i % 3)
            time.sleep(delay)

    conn.close()
    print(f"\nDone: {success} extracted, {failed} failed")

if __name__ == '__main__':
    main()
