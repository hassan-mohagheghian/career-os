#!/usr/bin/env python3
"""
Job Search CLI — add, list, process, and manage pending jobs.
Source tags: cli (this tool), web (dashboard), mimo (MiMo agent).
"""
from dotenv import load_dotenv
load_dotenv()

import os
import sys

from shared.infrastructure.process.logging_config import setup_logging
setup_logging(level='INFO')
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

_file_dir = os.path.dirname(os.path.abspath(__file__))
_server_dir = os.path.dirname(_file_dir)  # app/server/
_db_path = os.environ.get('DB_PATH', os.path.join(_server_dir, 'db', 'jobs.db'))
DB_PATH = _db_path if os.path.isabs(_db_path) else os.path.join(_server_dir, _db_path)
MIMO_BIN = os.path.expanduser('~/.mimocode/bin/mimo')
PROJECT_ROOT = os.path.abspath(os.path.join(_server_dir, '..', '..'))


def normalize_url(url):
    """Remove query parameters and trailing slash from URL for duplicate detection."""
    if not url:
        return url
    parsed = urlparse(url)
    base_url = f'{parsed.scheme}://{parsed.netloc}{parsed.path}'
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    return base_url

# --- Helpers ---

def _get_job_repo():
    from dependencies import get_session_sync
    from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
    session = get_session_sync()
    return session, SQLAlchemyJobRepository(session)

def _get_pending_repo():
    from dependencies import get_session_sync
    from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
    session = get_session_sync()
    return session, SQLAlchemyPendingRepository(session)

def _get_pref_repo():
    from dependencies import get_session_sync
    from career.infrastructure.repositories.sa_preference_repository import SQLAlchemyPreferenceRepository
    session = get_session_sync()
    return session, SQLAlchemyPreferenceRepository(session)

def get_next_num():
    session, repo = _get_job_repo()
    try:
        return repo.get_next_num()
    finally:
        session.close()

def get_pending(status=None):
    session, repo = _get_pending_repo()
    try:
        rows = repo.list_pending()
        if status:
            rows = [r for r in rows if r['status'] == status]
        else:
            rows = [r for r in rows if r['status'] != 'done']
        rows.sort(key=lambda r: r.get('created_at', '') or '')
        return rows
    finally:
        session.close()

def add_pending(url, source='cli', company=''):
    session, repo = _get_pending_repo()
    try:
        existing = repo.get_by_url(url)
        if existing:
            return None
        result = repo.create({'url': url, 'source': source, 'company': company})
        return result['id']
    except Exception:
        return None
    finally:
        session.close()

def reset_pending(pid):
    session, repo = _get_pending_repo()
    try:
        repo.update_fields(pid, status='queued', error=None,
            step_fetch=0, step_analyze=0, step_db=0, step_done=0,
            workflow_log='[]', updated_at=datetime.now().isoformat())
    finally:
        session.close()

def delete_pending(pid):
    from jobs.infrastructure.models.job_model import JobModel
    session, repo = _get_pending_repo()
    try:
        session.query(JobModel).filter(JobModel.num == pid).update({"deleted": 1})
        session.commit()
    finally:
        session.close()

def process_pending_sync(pid):
    """Run worker.process_job in current thread (blocking)."""
    sys.path.insert(0, _server_dir)
    from jobs.infrastructure.workers.worker import process_job
    process_job(pid)

# --- Commands ---

@app.command()
def add(url: str = typer.Argument(..., help="LinkedIn job URL to add"),
        no_process: bool = typer.Option(False, "--no-process", "-n", help="Just queue, don't process")):
    """Add a new job URL to the queue."""
    normalized = normalize_url(url)

    # Check pending_jobs for duplicate (normalized URL)
    session_p, pending_repo = _get_pending_repo()
    try:
        existing_pending = pending_repo.list_pending()
        for r in existing_pending:
            if normalize_url(r['url']) == normalized:
                console.print(f"[yellow]Already in queue (ID:{r['id']}, status:{r['status']})[/yellow]")
                return
    finally:
        session_p.close()

    # Check jobs table for duplicate (normalized URL)
    session_j, job_repo = _get_job_repo()
    try:
        active_jobs = job_repo.get_all_active()
        for j in active_jobs:
            if normalize_url(j['url']) == normalized:
                console.print(f"[yellow]Already processed as #{j['num']} ({j['company']})[/yellow]")
                return
    finally:
        session_j.close()

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
        session, _repo = _get_pending_repo()
        try:
            from jobs.infrastructure.models.job_model import JobModel
            done_rows = session.query(JobModel).filter(
                JobModel.deleted == 0,
                JobModel.status == 'completed'
            ).order_by(JobModel.created_at.desc()).limit(10).all()
            from shared.infrastructure.database.mappers import job_model_to_dict
            done = [job_model_to_dict(r) for r in done_rows]
            rows = done + rows
        finally:
            session.close()
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
        steps = sum(1 for s in [r['step_fetch'],r['step_analyze'],r['step_db'],r['step_done']] if s == 1)
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
    session_j, job_repo = _get_job_repo()
    try:
        job = job_repo.get_by_num(num)
    finally:
        session_j.close()
    if not job:
        console.print(f"[red]Job #{num} not found[/red]")
        return
    console.print(f"[cyan]Rescoring #{num} ({job['company']})...[/cyan]")

    session_p, pending_repo = _get_pending_repo()
    try:
        existing = pending_repo.get_by_url(job['url'])
        if existing:
            pid = existing['id']
            pending_repo.update_fields(pid, status='queued', error=None, source='rescore',
                company=job.get('company', ''),
                step_fetch=0, step_analyze=0, step_db=0, step_done=0,
                workflow_log='[]', updated_at=datetime.now().isoformat())
        else:
            result = pending_repo.create({'url': job['url'], 'source': 'rescore', 'company': job.get('company', '')})
            pid = result['id']
    finally:
        session_p.close()

    try:
        process_pending_sync(pid)
        console.print(f"[green]Done![/green]")
    except Exception as e:
        console.print(f"[red]Failed: {e}[/red]")

@app.command()
def rescore_all():
    """Re-score all processed jobs."""
    session_j, job_repo = _get_job_repo()
    try:
        jobs = job_repo.get_all_active()
    finally:
        session_j.close()
    if not jobs:
        console.print("[dim]No processed jobs[/dim]")
        return
    console.print(f"[cyan]Rescoring {len(jobs)} jobs...[/cyan]")
    for j in jobs:
        console.print(f"  [#{j['num']}] {j['company']}...", end=" ")

        session_p, pending_repo = _get_pending_repo()
        try:
            existing = pending_repo.get_by_url(j['url'])
            if existing:
                pid = existing['id']
                pending_repo.update_fields(pid, status='queued', error=None, source='rescore',
                    company=j.get('company', ''),
                    step_fetch=0, step_analyze=0, step_db=0, step_done=0,
                    workflow_log='[]', updated_at=datetime.now().isoformat())
            else:
                result = pending_repo.create({'url': j['url'], 'source': 'rescore', 'company': j.get('company', '')})
                pid = result['id']
        finally:
            session_p.close()

        try:
            process_pending_sync(pid)
            console.print("[green]done[/green]")
        except Exception as e:
            console.print(f"[red]failed: {e}[/red]")

@app.command()
def status():
    """Show summary of all job states."""
    from jobs.infrastructure.models.job_model import JobModel
    from dependencies import get_session_sync
    session = get_session_sync()
    try:
        counts = {}
        for s in ['queued','processing','failed','completed']:
            counts[s] = session.query(JobModel).filter(JobModel.deleted == 0, JobModel.status == s).count()
        total = session.query(JobModel).filter(JobModel.deleted == 0).count()
        jobs_count = total
    finally:
        session.close()

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
    """Update all insights insights based on processed jobs."""
    sys.path.insert(0, _server_dir)
    from career.application.services.insights import generate_all

    console.print("[cyan]Generating insights...[/cyan]")
    try:
        result = generate_all()
        if result:
            console.print("[green]Insights updated![/green]")
        else:
            console.print("[red]Generation returned no result[/red]")
    except Exception as e:
        console.print(f"[red]Failed: {e}[/red]")

@app.command()
def update_dashboard():
    """Update insights (alias for update-insights)."""
    update_insights()

@app.command()
def update_skills():
    """Update skills section only."""
    sys.path.insert(0, _server_dir)
    from career.application.services.insights import generate_section
    console.print("[cyan]Updating skills intelligence...[/cyan]")
    try:
        result = generate_section('skills')
        if result:
            console.print("[green]Skills intelligence updated![/green]")
        else:
            console.print("[red]Generation returned no result[/red]")
    except Exception as e:
        console.print(f"[red]Failed: {e}[/red]")

@app.command()
def rules():
    """Show all scoring rules."""
    session, repo = _get_pref_repo()
    try:
        rows = repo.get_all()
    finally:
        session.close()
    if not rows:
        console.print("[dim]No scoring rules set[/dim]")
        return

    rows.sort(key=lambda r: (r.get('rule_type', 'job'), r.get('category', ''), -(r.get('priority') or 0)))

    current_type = None
    current_cat = None
    for r in rows:
        rt = r.get('rule_type', 'job')
        if rt != current_type:
            current_type = rt
            console.print(f"\n[bold magenta]═══ {current_type.upper()} RULES ═══[/bold magenta]")
            current_cat = None
        if r['category'] != current_cat:
            current_cat = r['category']
            console.print(f"\n[bold cyan]{current_cat.upper()}[/bold cyan]")
        status = "[green]ON[/green]" if r['enabled'] else "[red]OFF[/red]"
        weight = r.get('score_weight') or r['priority']
        console.print(f"  {status} {r['key']} (w:{weight}) = {r['value']}")
        if r['description']:
            console.print(f"    [dim]{r['description']}[/dim]")

@app.command()
def add_rule(category: str = typer.Argument(..., help="Category: fit or success"),
             key: str = typer.Argument(..., help="Rule key"),
             value: str = typer.Argument(..., help="Rule value"),
             rule_type: str = typer.Option("job", help="Rule type: shared, job, or company"),
             description: str = typer.Option("", help="Description"),
             score_weight: int = typer.Option(0, help="Score weight (0 = use priority)")):
    """Add a new scoring rule."""
    session, repo = _get_pref_repo()
    try:
        repo.create({
            'category': category,
            'rule_type': rule_type,
            'key': key,
            'value': value,
            'description': description,
            'score_weight': score_weight,
        })
        console.print(f"[green]Added: {rule_type}/{category}/{key} = {value} (weight: {score_weight})[/green]")
    except Exception as e:
        console.print(f"[red]Failed: {e}[/red]")
    finally:
        session.close()

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
EXPORT_DIR = os.path.abspath(os.environ.get('EXPORT_DIR', os.path.join(PROJECT_ROOT, 'export')))

@app.command()
def generate_files(job_num: int = typer.Option(None, help="Generate files for a specific job number (all jobs if omitted)"),
                   force: bool = typer.Option(False, help="Overwrite existing files")):
    """Generate raw and structured files for processed jobs."""
    session, job_repo = _get_job_repo()
    try:
        if job_num:
            rows, _ = job_repo.list_jobs(offset=0, limit=1, sort_by='num', sort_dir='asc',
                                          filters={})
            job = job_repo.get_by_num(job_num)
            rows = [job] if job and job.get('deleted', 0) == 0 else []
        else:
            rows, _ = job_repo.list_jobs(offset=0, limit=99999, sort_by='num', sort_dir='asc')
    finally:
        session.close()

    if not rows:
        console.print("[yellow]No jobs found[/yellow]")
        return

    raw_dir = os.path.join(EXPORT_DIR, 'raw')
    struct_dir = os.path.join(EXPORT_DIR, 'structured')
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(struct_dir, exist_ok=True)

    created = 0
    skipped = 0
    for j in rows:
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
    session, job_repo = _get_job_repo()
    try:
        rows, _ = job_repo.list_jobs(offset=0, limit=99999, sort_by='num', sort_dir='asc')
    finally:
        session.close()

    missing_raw = []
    missing_struct = []
    for j in rows:
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
    from jobs.infrastructure.workers.worker import process_job
    for j in missing_raw + missing_struct:
        num = j['num']
        console.print(f"  Re-processing #{num} {j['company']}...")
        # Create a temp pending entry and process it
        pid = add_pending('', source='sync', company=j['company'])
        if pid:
            # Note: this needs the URL — we can't re-process without it
            console.print(f"  [yellow]Skipped #{num} — URL not available in DB for re-processing[/yellow]")
        else:
            console.print(f"  [yellow]Skipped #{num} — could not create pending entry[/yellow]")

@app.command()
def cleanup(
    kill_mimo: bool = typer.Option(False, "--kill-mimo", "-m", help="Kill all mimo processes"),
    reset_jobs: bool = typer.Option(False, "--reset-jobs", "-j", help="Reset stuck insights jobs"),
    reset_roadmaps: bool = typer.Option(False, "--reset-roadmaps", "-r", help="Reset stuck roadmap generation jobs"),
    all: bool = typer.Option(False, "--all", "-a", help="Run all cleanup actions"),
):
    """Clean up stuck processes and reset failed jobs."""
    import signal as _signal

    if all:
        kill_mimo = reset_jobs = reset_roadmaps = True

    console.print(Panel("[bold]Cleanup[/bold]", title="Job Search CLI"))

    if kill_mimo:
        console.print("\n[bold]Killing mimo processes...[/bold]")
        import subprocess
        result = subprocess.run(["pgrep", "-f", "mimo run"], capture_output=True, text=True)
        pids = result.stdout.strip().split('\n') if result.stdout.strip() else []
        if pids:
            for pid in pids:
                if pid:
                    try:
                        os.kill(int(pid), _signal.SIGTERM)
                        console.print(f"  [green]Sent SIGTERM to PID {pid}[/green]")
                    except Exception as e:
                        console.print(f"  [red]Failed to kill PID {pid}: {e}[/red]")
        else:
            console.print("  [dim]No mimo processes found[/dim]")

    if reset_jobs:
        console.print("\n[bold]Resetting stuck insights jobs...[/bold]")
        from career.infrastructure.models.insight_model import CareerInsightRunModel as InsightRunModel
        from dependencies import get_session_sync
        session = get_session_sync()
        try:
            count = session.query(InsightRunModel).filter(
                InsightRunModel.status.in_(['processing', 'queued'])
            ).update({'status': 'failed', 'error_message': 'Reset by CLI'})
            session.commit()
        finally:
            session.close()
        console.print(f"  [green]Reset {count} jobs[/green]")

    if reset_roadmaps:
        console.print("\n[bold]Resetting stuck roadmap jobs...[/bold]")
        from shared.infrastructure.database.models.misc_models import SkillRoadmapJobModel
        from dependencies import get_session_sync
        session = get_session_sync()
        try:
            count = session.query(SkillRoadmapJobModel).filter(
                SkillRoadmapJobModel.status.in_(['running', 'queued'])
            ).update({'status': 'failed', 'error': 'Reset by CLI'})
            session.commit()
        finally:
            session.close()
        console.print(f"  [green]Reset {count} jobs[/green]")

    if not (kill_mimo or reset_jobs or reset_roadmaps):
        console.print("[dim]No cleanup actions specified. Use --all or individual flags.[/dim]")

    console.print("\n[green]Done.[/green]")


if __name__ == '__main__':
    app()
