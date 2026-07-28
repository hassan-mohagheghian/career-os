"""
Backfill raw job descriptions for existing jobs.
Fetches from web, saves to jobs/ folder and raw_description column in DB.
Uses the unified Tool Layer for URL fetching.
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

# Unified Tool Layer — local-first URL fetching
from ai.infrastructure.tools.fetch import fetch_page


def get_session():
    engine = create_engine(f"sqlite:///{DB_PATH}")
    Session = sessionmaker(bind=engine)
    return Session(), engine


def fetch_url(url, retries=2):
    """Fetch a URL using the unified Tool Layer.

    Local-first approach with retry support for backfill operations.
    Returns cleaned text or None on failure.
    """
    page = fetch_page(url, max_retries=retries)
    if page.is_ok and len(page.plain_text) >= 100:
        return page.plain_text[:5000]
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
