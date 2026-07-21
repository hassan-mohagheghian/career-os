"""Normalize job locations - extract cities into locations array."""
import os
import sqlite3
import json
import re

_file_dir = os.path.dirname(os.path.abspath(__file__))
_db_path = os.environ.get('DB_PATH', os.path.join(_file_dir, 'db', 'jobs.db'))
DB_PATH = _db_path if os.path.isabs(_db_path) else os.path.join(_file_dir, _db_path)

# Known city patterns
CITY_PATTERNS = [
    'Berlin', 'Munich', 'München', 'Hamburg', 'Heidelberg', 'Frankfurt',
    'Cologne', 'Köln', 'Stuttgart', 'Leipzig', 'Dortmund', 'Magdeburg',
    'Madrid', 'Barcelona', 'Paris', 'London', 'Amsterdam', 'Vienna', 'Wien',
    'Zurich', 'Zürich', 'Remote', 'Germany', 'Europe',
]

# Work type patterns
WORK_TYPE_PATTERNS = {
    'Remote': ['remote', 'fully remote', 'work from anywhere', 'work from home'],
    'Hybrid': ['hybrid', 'flexible', 'partial remote'],
    'On-site': ['on-site', 'onsite', 'in office', 'office'],
}

def extract_cities(location_str):
    """Extract city names from a location string."""
    if not location_str:
        return []

    cities = []
    loc = location_str.strip()

    # Handle special patterns
    loc = re.sub(r'\(.*?\)', '', loc)  # Remove parentheses content
    loc = loc.replace('Europe (Remote/Hybrid)', 'Europe')

    # Split by common separators
    parts = re.split(r'[,/\|]', loc)

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Check against known cities
        for city in CITY_PATTERNS:
            if city.lower() in part.lower():
                # Normalize city names
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

    # Handle "Leipzig/Berlin" pattern
    if '/' in location_str:
        for part in location_str.split('/'):
            part = part.strip()
            for city in CITY_PATTERNS:
                if city.lower() == part.lower() and city not in cities:
                    cities.append(city)

    return cities if cities else [location_str] if location_str else []

def detect_work_type(location_str, notes_str):
    """Detect work type from location and notes."""
    text = (location_str or '').lower() + ' ' + (notes_str or '').lower()

    for work_type, patterns in WORK_TYPE_PATTERNS.items():
        for pattern in patterns:
            if pattern in text:
                return work_type

    return 'On-site'  # default

def normalize_locations():
    """Normalize all job locations in the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute('SELECT num, location, locations, work_type, notes FROM jobs WHERE deleted=0').fetchall()

    updated = 0
    for row in rows:
        r = dict(row)
        num = r['num']
        location = r['location'] or ''
        existing_locations = r['locations'] or '[]'
        work_type = r['work_type'] or 'On-site'
        notes = r['notes'] or ''

        # Parse existing locations
        try:
            locs = json.loads(existing_locations) if isinstance(existing_locations, str) else existing_locations
        except:
            locs = []

        # Extract cities from location
        new_cities = extract_cities(location)

        # Merge with existing, avoiding duplicates
        all_locations = list(locs)
        for city in new_cities:
            if city not in all_locations:
                all_locations.append(city)

        # Detect work type from location if it contains work type info
        detected_type = detect_work_type(location, notes)

        # Only update if we found locations or work type changed
        if all_locations != locs or detected_type != work_type:
            print(f'#{num}: "{location}" -> locations={all_locations}, work_type="{detected_type}"')
            conn.execute('UPDATE jobs SET locations=?, work_type=? WHERE num=?',
                (json.dumps(all_locations), detected_type, num))
            updated += 1

    conn.commit()
    conn.close()
    print(f'\nUpdated {updated} jobs')

if __name__ == '__main__':
    normalize_locations()
