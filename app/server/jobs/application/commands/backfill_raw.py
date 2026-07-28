"""
Backfill raw job descriptions for existing jobs.
Fetches from web, saves to jobs/ folder and raw_description column in DB.
"""
import os
import re
import time
import urllib.request
import urllib.error

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_file_dir = os.path.dirname(os.path.abspath(__file__))
_db_path = os.environ.get('DB_PATH', os.path.join(_file_dir, 'db', 'jobs.db'))
DB_PATH = _db_path if os.path.isabs(_db_path) else os.path.join(_file_dir, _db_path)
TEMP_DIR = os.environ.get('TEMP_DIR', '/tmp')

import sys
sys.path.insert(0, os.path.join(_file_dir, '..'))
from shared.infrastructure.database.sqlalchemy_config import Base
import jobs.infrastructure.models.job_model
from jobs.infrastructure.models.job_model import JobModel


def get_session():
    engine = create_engine(f"sqlite:///{DB_PATH}")
    Session = sessionmaker(bind=engine)
    return Session(), engine


def fetch_url(url, retries=2):
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36', 'Accept-Language': 'en-US,en;q=0.9'}
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                html = resp.read().decode('utf-8', errors='replace')
            text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            for marker in ['About The Role', 'Job Description', 'Description', 'What you.ll do', 'What You.ll Do', 'The Role']:
                idx = text.find(marker)
                if idx != -1:
                    text = text[idx:]
                    break
            return text[:5000] if len(text) >= 100 else None
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            if attempt < retries:
                time.sleep(5)
            else:
                print(f"  Failed to fetch: {e}")
                return None
    return None


def main():
    os.makedirs(TEMP_DIR, exist_ok=True)
    session, engine = get_session()
    try:
        rows = session.query(JobModel).filter(JobModel.deleted == 0, JobModel.raw_description.is_(None)).order_by(JobModel.num).all()
        print(f"Found {len(rows)} jobs without raw descriptions")
        fetched, failed, skipped = 0, 0, 0
        for i, job in enumerate(rows):
            num = job.num
            company = (job.company or 'Unknown').replace(' ', '_').replace('/', '_')
            role = (job.role or 'Unknown').replace(' ', '_').replace('/', '_')
            url = job.url
            posted = job.posted_at or ''
            date_str = posted[:10] if posted else '2026-01-01'
            filename = f"{num:03d}_{company}_{role}_{date_str}.md"
            filepath = os.path.join(TEMP_DIR, filename)
            if os.path.exists(filepath):
                with open(filepath) as f:
                    raw_text = f.read()
                job.raw_description = raw_text
                session.commit()
                skipped += 1
                continue
            if not url:
                failed += 1
                continue
            raw_text = fetch_url(url)
            if raw_text:
                with open(filepath, 'w') as f:
                    f.write(raw_text)
                job.raw_description = raw_text
                session.commit()
                fetched += 1
            else:
                failed += 1
            if i < len(rows) - 1:
                time.sleep(2 + (i % 3))
        print(f"\nDone: {fetched} fetched, {skipped} from files, {failed} failed")
    finally:
        session.close()
        engine.dispose()


if __name__ == '__main__':
    main()
