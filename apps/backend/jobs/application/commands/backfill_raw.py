"""
Backfill raw job descriptions for existing jobs.
Fetches from web and saves directly to DB — no file I/O.
Uses the unified Tool Layer for URL fetching.
"""
import os
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_file_dir = os.path.dirname(os.path.abspath(__file__))
_db_path = os.environ.get('DB_PATH', os.path.join(_file_dir, 'db', 'jobs.db'))
DB_PATH = _db_path if os.path.isabs(_db_path) else os.path.join(_file_dir, _db_path)

import sys
sys.path.insert(0, os.path.join(_file_dir, '..'))
from shared.infrastructure.process.logging_config import get_logger
from shared.infrastructure.database.sqlalchemy_config import Base

log = get_logger('jobs.commands.backfill_raw')
import jobs.infrastructure.models.job_model
from jobs.infrastructure.models.job_model import JobModel

from ai.infrastructure.tools.fetch import fetch_page


def get_session():
    engine = create_engine(f"sqlite:///{DB_PATH}")
    Session = sessionmaker(bind=engine)
    return Session(), engine


def fetch_url(url, retries=2):
    page = fetch_page(url, max_retries=retries)
    if page.is_ok and len(page.plain_text) >= 100:
        return page.plain_text[:5000]
    return None


def main():
    session, engine = get_session()
    try:
        rows = session.query(JobModel).filter(JobModel.deleted == 0, JobModel.raw_description.is_(None)).order_by(JobModel.created_at).all()
        log.info("Found jobs without raw descriptions", count=len(rows))
        fetched, failed = 0, 0
        for i, job in enumerate(rows):
            if not job.url:
                failed += 1
                continue
            raw_text = fetch_url(job.url)
            if raw_text:
                job.raw_description = raw_text
                session.commit()
                fetched += 1
            else:
                failed += 1
            if i < len(rows) - 1:
                time.sleep(2 + (i % 3))
        log.info("Backfill raw done", fetched=fetched, failed=failed)
    finally:
        session.close()
        engine.dispose()


if __name__ == '__main__':
    main()
