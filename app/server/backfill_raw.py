"""
Backfill raw job descriptions for existing jobs.
Fetches from web, saves to jobs/ folder and raw_description column in DB.
Includes delay between requests to avoid rate limiting.
"""
import sqlite3
import os
import re
import json
import time
import urllib.request
import urllib.error

DB_PATH = os.path.join(os.path.dirname(__file__), 'jobs.db')
JOBS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'jobs')

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_url(url, retries=2):
    """Fetch URL content with retries."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                html = resp.read().decode('utf-8', errors='replace')
            # Strip HTML tags
            text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            # Find job description section
            for marker in ['About The Role', 'Job Description', 'Description', 'What you.ll do', 'What You.ll Do', 'The Role']:
                idx = text.find(marker)
                if idx != -1:
                    text = text[idx:]
                    break
            if len(text) < 100:
                return None
            return text[:5000]
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            if attempt < retries:
                print(f"  Retry {attempt + 1} for {url[:60]}...")
                time.sleep(5)
            else:
                print(f"  Failed to fetch: {e}")
                return None
    return None

def main():
    os.makedirs(JOBS_DIR, exist_ok=True)
    conn = get_db()

    # Find jobs without raw_description
    rows = conn.execute(
        'SELECT num, company, role, url, posted_at FROM jobs WHERE deleted=0 AND raw_description IS NULL ORDER BY num'
    ).fetchall()

    print(f"Found {len(rows)} jobs without raw descriptions")

    fetched = 0
    failed = 0
    skipped = 0

    for i, row in enumerate(rows):
        r = dict(row)
        num = r['num']
        company = (r['company'] or 'Unknown').replace(' ', '_').replace('/', '_')
        role = (r['role'] or 'Unknown').replace(' ', '_').replace('/', '_')
        url = r['url']

        # Check if file already exists in jobs/
        posted = r.get('posted_at', '')
        if posted:
            date_str = posted[:10]
        else:
            date_str = '2026-01-01'

        filename = f"{num:03d}_{company}_{role}_{date_str}.md"
        filepath = os.path.join(JOBS_DIR, filename)

        # If file exists, read from it
        if os.path.exists(filepath):
            with open(filepath) as f:
                raw_text = f.read()
            conn.execute('UPDATE jobs SET raw_description=? WHERE num=?', (raw_text, num))
            conn.commit()
            skipped += 1
            print(f"#{num:03d} {r['company']}: loaded from existing file")
            continue

        # Fetch from web
        if not url:
            print(f"#{num:03d} {r['company']}: no URL, skipping")
            failed += 1
            continue

        print(f"#{num:03d} {r['company']}: fetching from web...")
        raw_text = fetch_url(url)

        if raw_text:
            # Save to file
            with open(filepath, 'w') as f:
                f.write(raw_text)
            # Save to DB
            conn.execute('UPDATE jobs SET raw_description=? WHERE num=?', (raw_text, num))
            conn.commit()
            fetched += 1
            print(f"  Saved ({len(raw_text)} chars)")
        else:
            failed += 1
            print(f"  Failed to fetch")

        # Delay between requests (2-4 seconds random)
        if i < len(rows) - 1:
            delay = 2 + (i % 3)
            time.sleep(delay)

    conn.close()
    print(f"\nDone: {fetched} fetched, {skipped} from files, {failed} failed")

if __name__ == '__main__':
    main()
