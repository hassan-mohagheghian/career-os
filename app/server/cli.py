#!/usr/bin/env python3
"""
Job Search CLI — add, list, process, and manage pending jobs.
Source tags: cli (this tool), web (dashboard), mimo (MiMo agent).
"""
import os
import sys
import sqlite3
import subprocess
import threading
from datetime import datetime
from urllib.parse import urlparse

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(help="Job Search CLI — manage pending jobs", no_args_is_help=True)
console = Console()

DB_PATH = os.path.join(os.path.dirname(__file__), 'jobs.db')
MIMO_BIN = os.path.expanduser('~/.mimocode/bin/mimo')
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def normalize_url(url):
    """Remove query parameters and trailing slash from URL for duplicate detection."""
    if not url:
        return url
    parsed = urlparse(url)
    base_url = f'{parsed.scheme}://{parsed.netloc}{parsed.path}'
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    return base_url

# --- DB helpers ---

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def get_next_num():
    conn = get_db()
    row = conn.execute("SELECT MAX(num) FROM jobs").fetchone()
    conn.close()
    return (row[0] or 0) + 1

def get_pending(status=None):
    conn = get_db()
    if status:
        rows = conn.execute("SELECT * FROM pending_jobs WHERE status=? ORDER BY created_at", (status,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM pending_jobs WHERE status NOT IN ('done') ORDER BY created_at").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_pending(url, source='cli', company=''):
    conn = get_db()
    try:
        cur = conn.execute('INSERT INTO pending_jobs (url, source, company) VALUES (?, ?, ?)', (url, source, company))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return new_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

def reset_pending(pid):
    conn = get_db()
    conn.execute('''UPDATE pending_jobs SET status='queued', error=NULL,
        step_fetch=0, step_analyze=0, step_resume=0, step_db=0, step_done=0,
        updated_at=? WHERE id=?''', (datetime.now().isoformat(), pid))
    conn.commit()
    conn.close()

def delete_pending(pid):
    conn = get_db()
    conn.execute('DELETE FROM pending_jobs WHERE id=?', (pid,))
    conn.commit()
    conn.close()

def process_pending_sync(pid):
    """Run worker.process_job in current thread (blocking)."""
    sys.path.insert(0, os.path.dirname(__file__))
    from worker import process_job
    process_job(pid)

# --- Commands ---

@app.command()
def add(url: str = typer.Argument(..., help="LinkedIn job URL to add"),
        no_process: bool = typer.Option(False, "--no-process", "-n", help="Just queue, don't process")):
    """Add a new job URL to the queue."""
    normalized = normalize_url(url)
    conn = get_db()

    # Check pending_jobs for duplicate (normalized URL)
    existing = conn.execute("SELECT id, status, url FROM pending_jobs").fetchall()
    for row in existing:
        r = dict(row)
        if normalize_url(r['url']) == normalized:
            console.print(f"[yellow]Already in queue (ID:{r['id']}, status:{r['status']})[/yellow]")
            conn.close()
            return

    # Check jobs table for duplicate (normalized URL)
    jobs = conn.execute("SELECT num, company, url FROM jobs").fetchall()
    for row in jobs:
        j = dict(row)
        if normalize_url(j['url']) == normalized:
            console.print(f"[yellow]Already processed as #{j['num']} ({j['company']})[/yellow]")
            conn.close()
            return

    conn.close()

    pid = add_pending(url, source='cli')
    if not pid:
        console.print("[red]Failed to add job[/red]")
        return
    console.print(f"[green]Added (ID:{pid})[/green] {url[:60]}...")

    if not no_process:
        console.print("[cyan]Processing...[/cyan]")
        try:
            process_pending_sync(pid)
            console.print(f"[green]Done![/green]")
        except Exception as e:
            console.print(f"[red]Failed: {e}[/red]")

@app.command(name="list")
def list_jobs(status: str = typer.Option(None, "--status", "-s", help="Filter: queued, processing, failed, done"),
              all_jobs: bool = typer.Option(False, "--all", "-a", help="Show all including done")):
    """List pending/active jobs."""
    if all_jobs:
        rows = get_pending(status=None)
        # Include done too
        conn = get_db()
        done = conn.execute("SELECT * FROM pending_jobs WHERE status='done' ORDER BY created_at DESC LIMIT 10").fetchall()
        conn.close()
        rows = [dict(r) for r in done] + rows
    else:
        rows = get_pending(status=status)

    if not rows:
        console.print("[dim]No jobs found[/dim]")
        return

    table = Table(title=f"Pending Jobs ({len(rows)})")
    table.add_column("ID", style="bold", width=4)
    table.add_column("Status", width=12)
    table.add_column("Source", width=6)
    table.add_column("Company", width=20)
    table.add_column("Steps", width=6)
    table.add_column("URL", max_width=50)
    table.add_column("Error", max_width=30, style="red")

    status_colors = {'queued':'yellow','processing':'cyan','failed':'red','done':'green'}
    for r in rows:
        steps = sum(1 for s in [r['step_fetch'],r['step_analyze'],r['step_resume'],r['step_db'],r['step_done']] if s == 1)
        sc = status_colors.get(r['status'], 'dim')
        err = (r['error'] or '')[:30]
        table.add_row(
            str(r['id']),
            f"[{sc}]{r['status']}[/{sc}]",
            r['source'] or '-',
            r['company'] or '-',
            f"{steps}/5",
            r['url'][:50] + ('...' if len(r['url']) > 50 else ''),
            err
        )
    console.print(table)

@app.command()
def process(pid: int = typer.Argument(..., help="Job ID to process"),
            reset_first: bool = typer.Option(False, "--reset", "-r", help="Reset to queued before processing")):
    """Process a specific pending job."""
    if reset_first:
        reset_pending(pid)
        console.print(f"[yellow]Reset ID:{pid} to queued[/yellow]")
    console.print(f"[cyan]Processing ID:{pid}...[/cyan]")
    try:
        process_pending_sync(pid)
        console.print("[green]Done![/green]")
    except Exception as e:
        console.print(f"[red]Failed: {e}[/red]")

@app.command()
def process_all():
    """Process all queued jobs."""
    rows = get_pending(status='queued')
    if not rows:
        console.print("[dim]No queued jobs[/dim]")
        return
    console.print(f"[cyan]Processing {len(rows)} jobs...[/cyan]")
    for r in rows:
        console.print(f"  [{r['id']}] {r['url'][:50]}...")
        try:
            process_pending_sync(r['id'])
            console.print(f"  [green][{r['id']}] Done[/green]")
        except Exception as e:
            console.print(f"  [red][{r['id']}] Failed: {e}[/red]")

@app.command()
def reset(pid: int = typer.Argument(..., help="Job ID to reset")):
    """Reset a failed/processing job back to queued."""
    reset_pending(pid)
    console.print(f"[green]Reset ID:{pid} to queued[/green]")

@app.command()
def remove(pid: int = typer.Argument(..., help="Job ID to remove")):
    """Remove a pending job."""
    delete_pending(pid)
    console.print(f"[green]Removed ID:{pid}[/green]")

@app.command()
def rescore(num: int = typer.Argument(..., help="Job number to rescore")):
    """Re-score a processed job by re-analyzing it."""
    conn = get_db()
    job = conn.execute("SELECT * FROM jobs WHERE num=?", (num,)).fetchone()
    conn.close()
    if not job:
        console.print(f"[red]Job #{num} not found[/red]")
        return
    j = dict(job)
    console.print(f"[cyan]Rescoring #{num} ({j['company']})...[/cyan]")
    # Find or create pending entry — reset existing one to avoid duplicates
    conn = get_db()
    row = conn.execute('SELECT id FROM pending_jobs WHERE url=?', (j['url'],)).fetchone()
    if row:
        pid = dict(row)['id']
        conn.execute('''UPDATE pending_jobs SET status='queued', error=NULL, source='rescore',
            company=?, step_fetch=0, step_analyze=0, step_resume=0, step_db=0, step_done=0,
            workflow_log='[]', updated_at=? WHERE id=?''',
            (j.get('company', ''), datetime.now().isoformat(), pid))
    else:
        cur = conn.execute('INSERT INTO pending_jobs (url, source, company) VALUES (?, ?, ?)',
            (j['url'], 'rescore', j.get('company', '')))
        pid = cur.lastrowid
    conn.commit()
    conn.close()
    try:
        process_pending_sync(pid)
        console.print(f"[green]Done![/green]")
    except Exception as e:
        console.print(f"[red]Failed: {e}[/red]")

@app.command()
def rescore_all():
    """Re-score all processed jobs."""
    conn = get_db()
    jobs = conn.execute("SELECT num, company, url FROM jobs ORDER BY num").fetchall()
    conn.close()
    if not jobs:
        console.print("[dim]No processed jobs[/dim]")
        return
    console.print(f"[cyan]Rescoring {len(jobs)} jobs...[/cyan]")
    for job in jobs:
        j = dict(job)
        console.print(f"  [#{j['num']}] {j['company']}...", end=" ")
        # Find or create pending entry — reset existing one to avoid duplicates
        conn = get_db()
        row = conn.execute('SELECT id FROM pending_jobs WHERE url=?', (j['url'],)).fetchone()
        if row:
            pid = dict(row)['id']
            conn.execute('''UPDATE pending_jobs SET status='queued', error=NULL, source='rescore',
                company=?, step_fetch=0, step_analyze=0, step_resume=0, step_db=0, step_done=0,
                workflow_log='[]', updated_at=? WHERE id=?''',
                (j.get('company', ''), datetime.now().isoformat(), pid))
        else:
            cur = conn.execute('INSERT INTO pending_jobs (url, source, company) VALUES (?, ?, ?)',
                (j['url'], 'rescore', j.get('company', '')))
            pid = cur.lastrowid
        conn.commit()
        conn.close()
        try:
            process_pending_sync(pid)
            console.print("[green]done[/green]")
        except Exception as e:
            console.print(f"[red]failed: {e}[/red]")

@app.command()
def status():
    """Show summary of all job states."""
    conn = get_db()
    counts = {}
    for s in ['queued','processing','failed','done']:
        row = conn.execute("SELECT COUNT(*) as c FROM pending_jobs WHERE status=?", (s,)).fetchone()
        counts[s] = row['c']
    total = conn.execute("SELECT COUNT(*) as c FROM pending_jobs").fetchone()['c']
    jobs_count = conn.execute("SELECT COUNT(*) as c FROM jobs").fetchone()['c']
    conn.close()

    panel = Panel.fit(
        f"[yellow]Queued:[/yellow] {counts['queued']}  "
        f"[cyan]Processing:[/cyan] {counts['processing']}  "
        f"[red]Failed:[/red] {counts['failed']}  "
        f"[green]Processed:[/green] {counts['done']}  "
        f"\n[dim]Total pending: {total} | Total jobs in DB: {jobs_count}[/dim]",
        title="Job Queue Status"
    )
    console.print(panel)

@app.command()
def update_insights():
    """Update all insights (dashboard + skills) based on processed jobs."""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from worker import _update_dashboard_insights, _update_skills_insights

    console.print("[cyan]Updating dashboard insights...[/cyan]")
    try:
        _update_dashboard_insights(0)
        console.print("[green]Dashboard insights updated![/green]")
    except Exception as e:
        console.print(f"[red]Dashboard failed: {e}[/red]")

    console.print("[cyan]Updating skills insights...[/cyan]")
    try:
        _update_skills_insights(0)
        console.print("[green]Skills insights updated![/green]")
    except Exception as e:
        console.print(f"[red]Skills failed: {e}[/red]")

@app.command()
def update_dashboard():
    """Update dashboard insights only."""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from worker import _update_dashboard_insights
    console.print("[cyan]Updating dashboard insights...[/cyan]")
    try:
        _update_dashboard_insights(0)
        console.print("[green]Dashboard insights updated![/green]")
    except Exception as e:
        console.print(f"[red]Failed: {e}[/red]")

@app.command()
def update_skills():
    """Update skills insights only."""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from worker import _update_skills_insights
    console.print("[cyan]Updating skills insights...[/cyan]")
    try:
        _update_skills_insights(0)
        console.print("[green]Skills insights updated![/green]")
    except Exception as e:
        console.print(f"[red]Failed: {e}[/red]")

@app.command()
def prefs():
    """Show all scoring preferences."""
    conn = get_db()
    rows = conn.execute('SELECT category, key, value, description, enabled FROM preferences ORDER BY category, priority').fetchall()
    conn.close()
    if not rows:
        console.print("[dim]No preferences set[/dim]")
        return

    current_cat = None
    for row in rows:
        r = dict(row)
        if r['category'] != current_cat:
            current_cat = r['category']
            console.print(f"\n[bold cyan]{current_cat.upper()}[/bold cyan]")
        status = "[green]ON[/green]" if r['enabled'] else "[red]OFF[/red]"
        console.print(f"  {status} {r['key']} = {r['value']}")
        if r['description']:
            console.print(f"    [dim]{r['description']}[/dim]")

@app.command()
def add_pref(category: str = typer.Argument(..., help="Category: scoring, tech, domain, visa, strategy"),
             key: str = typer.Argument(..., help="Preference key"),
             value: str = typer.Argument(..., help="Preference value"),
             description: str = typer.Option("", help="Description")):
    """Add a new scoring preference."""
    conn = get_db()
    try:
        conn.execute('''INSERT INTO preferences (category, key, value, description) VALUES (?, ?, ?, ?)''',
            (category, key, value, description))
        conn.commit()
        console.print(f"[green]Added: {category}/{key} = {value}[/green]")
    except Exception as e:
        console.print(f"[red]Failed: {e}[/red]")
    finally:
        conn.close()

def _load_env():
    """Read .env file from project root into os.environ."""
    env_path = os.path.join(PROJECT_ROOT, '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())
_load_env()
JOBS_DIR = os.path.abspath(os.environ.get('JOBS_DIR', os.path.join(PROJECT_ROOT, 'jobs')))

@app.command()
def generate_files(job_num: int = typer.Option(None, help="Generate files for a specific job number (all jobs if omitted)"),
                   force: bool = typer.Option(False, help="Overwrite existing files")):
    """Generate raw and structured files for processed jobs."""
    conn = get_db()
    if job_num:
        rows = conn.execute('SELECT * FROM jobs WHERE num=? AND deleted=0', (job_num,)).fetchall()
    else:
        rows = conn.execute('SELECT * FROM jobs WHERE deleted=0 ORDER BY num').fetchall()
    conn.close()

    if not rows:
        console.print("[yellow]No jobs found[/yellow]")
        return

    raw_dir = os.path.join(JOBS_DIR, 'raw')
    struct_dir = os.path.join(JOBS_DIR, 'structured')
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(struct_dir, exist_ok=True)

    created = 0
    skipped = 0
    for row in rows:
        j = dict(row)
        num = j['num']
        co = (j.get('company') or 'Unknown').replace(' ', '_').replace('/', '_')
        ro = (j.get('role') or 'Unknown').replace(' ', '_').replace('/', '_')
        date_str = ''
        if j.get('created_at'):
            try:
                date_str = j['created_at'][:10]
            except:
                pass
        base = f"{num:03d}_{co}_{ro}_{date_str}"

        # Raw file
        raw_path = os.path.join(raw_dir, f"{base}.md")
        if os.path.exists(raw_path) and not force:
            skipped += 1
        elif j.get('raw_description'):
            with open(raw_path, 'w') as f:
                f.write(j['raw_description'])
            created += 1
            console.print(f"  [green]Raw:[/green] {base}.md")

        # Structured file
        struct_path = os.path.join(struct_dir, f"{base}.json")
        if os.path.exists(struct_path) and not force:
            skipped += 1
        elif j.get('structured_description'):
            try:
                import json
                structured = json.loads(j['structured_description'])
                with open(struct_path, 'w') as f:
                    json.dump(structured, f, indent=2, ensure_ascii=False)
                created += 1
                console.print(f"  [green]Struct:[/green] {base}.json")
            except:
                skipped += 1

    console.print(f"\n[bold]Done:[/bold] {created} files created, {skipped} skipped")

@app.command()
def sync_db(fix: bool = typer.Option(False, help="Actually update DB (dry run by default)")):
    """Check jobs with missing raw_description or structured_description."""
    conn = get_db()
    rows = conn.execute('SELECT num, company, role, raw_description, structured_description FROM jobs WHERE deleted=0 ORDER BY num').fetchall()
    conn.close()

    missing_raw = []
    missing_struct = []
    for row in rows:
        j = dict(row)
        if not j.get('raw_description'):
            missing_raw.append(j)
        if not j.get('structured_description'):
            missing_struct.append(j)

    if not missing_raw and not missing_struct:
        console.print("[green]All jobs have both raw and structured descriptions[/green]")
        return

    console.print(f"[yellow]Found {len(missing_raw)} jobs missing raw_description[/yellow]")
    for j in missing_raw:
        console.print(f"  #{j['num']} {j['company']} — {j['role']}")

    console.print(f"[yellow]Found {len(missing_struct)} jobs missing structured_description[/yellow]")
    for j in missing_struct:
        console.print(f"  #{j['num']} {j['company']} — {j['role']}")

    if not fix:
        console.print("\n[dim]Dry run — use --fix to update[/dim]")
        return

    console.print("\n[bold]Re-processing missing jobs...[/bold]")
    from worker import process_job
    for j in missing_raw + missing_struct:
        num = j['num']
        console.print(f"  Re-processing #{num} {j['company']}...")
        # Create a temp pending entry and process it
        conn = get_db()
        cur = conn.execute('INSERT INTO pending_jobs (url, source, company) VALUES (?, ?, ?)',
            ('', 'sync', j['company']))
        pid = cur.lastrowid
        conn.commit()
        conn.close()
        # Note: this needs the URL — we can't re-process without it
        console.print(f"  [yellow]Skipped #{num} — URL not available in DB for re-processing[/yellow]")

if __name__ == '__main__':
    app()
