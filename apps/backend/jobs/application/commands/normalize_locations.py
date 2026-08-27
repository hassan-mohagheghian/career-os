"""Normalize job locations - extract cities into locations array."""
import os
import json
import re

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_file_dir = os.path.dirname(os.path.abspath(__file__))
_db_path = os.environ.get('DB_PATH', os.path.join(_file_dir, 'db', 'jobs.db'))
DB_PATH = _db_path if os.path.isabs(_db_path) else os.path.join(_file_dir, _db_path)

import sys
sys.path.insert(0, os.path.join(_file_dir, '..'))
from shared.infrastructure.process.logging_config import get_logger
from shared.infrastructure.database.sqlalchemy_config import Base

log = get_logger('jobs.commands.normalize_locs')
import jobs.infrastructure.models.job_model
from jobs.infrastructure.models.job_model import JobModel
from cities.domain.entities.city import CityNormalizer

WORK_TYPE_PATTERNS = {
    'Remote': ['remote', 'fully remote', 'work from anywhere', 'work from home'],
    'Hybrid': ['hybrid', 'flexible', 'partial remote'],
    'On-site': ['on-site', 'onsite', 'in office', 'office'],
}


def extract_cities(location_str):
    if not location_str:
        return []
    cities = []
    loc = re.sub(r'\(.*?\)', '', location_str.strip())
    loc = loc.replace('Europe (Remote/Hybrid)', 'Europe')
    for part in re.split(r'[,/\|]', loc):
        part = part.strip()
        if not part:
            continue
        canonical, _ = CityNormalizer.normalize(part)
        if canonical and canonical not in cities:
            cities.append(canonical)
    return cities if cities else [location_str] if location_str else []


def detect_work_type(location_str, notes_str):
    text = (location_str or '').lower() + ' ' + (notes_str or '').lower()
    for work_type, patterns in WORK_TYPE_PATTERNS.items():
        for pattern in patterns:
            if pattern in text:
                return work_type
    return 'On-site'


def normalize_locations():
    engine = create_engine(f"sqlite:///{DB_PATH}")
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        rows = session.query(JobModel).filter(JobModel.deleted == 0).all()
        updated = 0
        for job in rows:
            location = job.location or ''
            existing_locations = job.locations or '[]'
            notes = job.notes or ''
            try:
                locs = json.loads(existing_locations) if isinstance(existing_locations, str) else existing_locations
            except Exception:
                locs = []
            new_cities = extract_cities(location)
            all_locations = list(locs)
            for city in new_cities:
                if city not in all_locations:
                    all_locations.append(city)
            detected_type = detect_work_type(location, notes)
            work_types = json.loads(job.work_types or '[]') if isinstance(job.work_types, str) else (job.work_types or [])
            if detected_type not in work_types:
                work_types.append(detected_type)
            if all_locations != locs:
                job.locations = json.dumps(all_locations)
                updated += 1
            if detected_type not in work_types:
                job.work_types = json.dumps(work_types)
                updated += 1
        session.commit()
        log.info("Normalized locations", updated=updated)
    finally:
        session.close()
        engine.dispose()


if __name__ == '__main__':
    normalize_locations()
