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

CITY_PATTERNS = [
    'Berlin', 'Munich', 'München', 'Hamburg', 'Heidelberg', 'Frankfurt',
    'Cologne', 'Köln', 'Stuttgart', 'Leipzig', 'Dortmund', 'Magdeburg',
    'Madrid', 'Barcelona', 'Paris', 'London', 'Amsterdam', 'Vienna', 'Wien',
    'Zurich', 'Zürich', 'Remote', 'Germany', 'Europe',
]

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
        for city in CITY_PATTERNS:
            if city.lower() in part.lower():
                if city.lower() == 'münchen':
                    city = 'Munich'
                elif city.lower() == 'köln':
                    city = 'Cologne'
                elif city.lower() == 'zürich':
                    city = 'Zurich'
                elif city.lower() == 'wien':
                    city = 'Vienna'
                if city not in cities:
                    cities.append(city)
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
            work_type = job.work_type or 'On-site'
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
            if all_locations != locs or detected_type != work_type:
                job.locations = json.dumps(all_locations)
                job.work_type = detected_type
                updated += 1
        session.commit()
        log.info("Normalized locations", updated=updated)
    finally:
        session.close()
        engine.dispose()


if __name__ == '__main__':
    normalize_locations()
