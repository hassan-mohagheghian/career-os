import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Ensure app/ and app/server/ are on sys.path for imports
_this_file = os.path.abspath(__file__ if '__file__' in dir() else '.')
_app_dir = os.path.dirname(_this_file)
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)
_server_dir = os.path.join(_app_dir, "server")
if _server_dir not in sys.path:
    sys.path.insert(0, _server_dir)

import typer
from rich.console import Console
from rich.table import Table

from server.shared.infrastructure.process.logging_config import setup_logging, get_logger

setup_logging(level='INFO')
log = get_logger('dev-cli')

app = typer.Typer(
    name="start",
    help="Job Search Application — Developer CLI",
    no_args_is_help=True,
)
db_app = typer.Typer(help="Database operations")
docker_app = typer.Typer(help="Docker operations")
app.add_typer(db_app, name="db")
app.add_typer(docker_app, name="docker")

console = Console()

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVER_DIR = REPO_ROOT / "app" / "server"
CLIENT_DIR = REPO_ROOT / "app" / "client"
BACKGROUND_DIR = REPO_ROOT / "app" / "background"
VENV_DIR = REPO_ROOT / ".venv"
PID_FILE = REPO_ROOT / ".server.pid"
CLIENT_PID_FILE = REPO_ROOT / ".client.pid"
PID_BG_FILE = REPO_ROOT / ".background.pid"


def _load_port_from_env(key: str, default: int) -> int:
    env_file = REPO_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                if k.strip() == key:
                    try:
                        return int(v.strip())
                    except ValueError:
                        pass
    try:
        return int(os.environ.get(key, default))
    except (ValueError, TypeError):
        return default


def _python_path() -> str:
    venv_python = VENV_DIR / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return "python3"


def _alembic_path() -> str:
    venv_alembic = VENV_DIR / "bin" / "alembic"
    if venv_alembic.exists():
        return str(venv_alembic)
    return "alembic"


def _read_pid(pid_file: Path) -> Optional[int]:
    try:
        return int(pid_file.read_text().strip())
    except (FileNotFoundError, ValueError):
        return None


def _is_process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _kill_process(pid: int):
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    import time as _time
    _time.sleep(0.5)
    if _is_process_alive(pid):
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def _save_pid(pid_file: Path, pid: int):
    pid_file.write_text(str(pid))


def _stop_service(name: str, pid_file: Path):
    pid = _read_pid(pid_file)
    if pid is not None and _is_process_alive(pid):
        console.print(f"[yellow][job-search][/] Stopping {name} (PID: {pid})")
        _kill_process(pid)
    pid_file.unlink(missing_ok=True)


def _kill_by_pattern(pattern: str):
    subprocess.run(["pkill", "-f", pattern], capture_output=True)


def _log(msg: str):
    log.info(msg)
    console.print(f"[blue][job-search][/] {msg}")


def _ok(msg: str):
    log.info(msg)
    console.print(f"[green][job-search][/] {msg}")


def _warn(msg: str):
    log.warning(msg)
    console.print(f"[yellow][job-search][/] {msg}")


def _err(msg: str):
    log.error(msg)
    console.print(f"[red][job-search][/] {msg}")


def _header(msg: str):
    console.print()
    console.print(f"[blue]═══ {msg} ═══[/]")
    console.print()


def _run_migrations():
    alembic = _alembic_path()
    if not Path(alembic).exists():
        return
    log.info("Running database migrations")
    result = subprocess.run(
        [alembic, "upgrade", "head"],
        cwd=str(REPO_ROOT),
        capture_output=True,
    )
    if result.returncode != 0:
        log.warning("Alembic migration warning (non-fatal)", stderr=result.stderr.decode() if result.stderr else None)


def _check_tool(name: str, *args: str):
    if not shutil.which(name):
        return False, f"{name} not found"
    try:
        result = subprocess.run([name, *args], capture_output=True, text=True)
        version = result.stdout.strip()
        return True, f"{name} {version}"
    except FileNotFoundError:
        return False, f"{name} not found"


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        dev()


@app.command()
def dev(
    backend_port: Optional[int] = typer.Option(
        None, "--backend-port", help="Backend port"
    ),
    frontend_port: Optional[int] = typer.Option(
        None, "--frontend-port", help="Frontend port"
    ),
    with_background: bool = typer.Option(
        False, "--background", "-b", help="Also start the background worker"
    ),
):
    """Start backend + frontend"""
    port_be = backend_port or _load_port_from_env("BACKEND_PORT", 5000)
    port_fe = frontend_port or _load_port_from_env("FRONTEND_PORT", 5173)

    _log("Starting all services...")
    console.print()

    _start_backend(port_be)
    import time
    time.sleep(2)
    _start_frontend(port_fe)

    if with_background:
        time.sleep(1)
        _start_background()

    console.print()
    _ok("All services started!")
    console.print()
    console.print(f"  Backend:  http://localhost:{port_be}")
    console.print(f"  Frontend: http://localhost:{port_fe}")
    if with_background:
        console.print("  Background: worker running")
    console.print()
    console.print("  Press Ctrl+C to stop all services")
    console.print()

    try:
        signal.signal(signal.SIGINT, lambda s, f: (_stop_service("backend", PID_FILE), _stop_service("frontend", CLIENT_PID_FILE), _kill_by_pattern("mimo run"), _ok("All processes stopped."), sys.exit(0)))
        signal.pause()
    except KeyboardInterrupt:
        pass

    _stop_service("backend", PID_FILE)
    _stop_service("frontend", CLIENT_PID_FILE)
    if with_background:
        _stop_service("background", PID_BG_FILE)
    _kill_by_pattern("mimo run")
    _ok("All processes stopped.")


def _start_backend(port: int):
    _log("Starting backend server...")
    python = _python_path()
    _log(f"Using Python: {python}")

    _run_migrations()

    port_str = str(port)
    proc = subprocess.Popen(
        [
            python, "-m", "uvicorn", "app.server.entrypoints.api:app",
            "--host", "0.0.0.0", "--port", port_str, "--reload",
        ],
        cwd=str(REPO_ROOT),
    )
    _save_pid(PID_FILE, proc.pid)
    _ok(f"Backend started (PID: {proc.pid}) on http://localhost:{port}")


def _start_frontend(port: int):
    _log("Starting frontend dev server...")
    port_str = str(port)
    proc = subprocess.Popen(
        ["npm", "run", "dev", "--", "--port", port_str],
        cwd=str(CLIENT_DIR),
    )
    _save_pid(CLIENT_PID_FILE, proc.pid)
    _ok(f"Frontend started (PID: {proc.pid}) on http://localhost:{port}")


def _start_background():
    _log("Starting background worker...")
    python = _python_path()
    env = os.environ.copy()
    app_dir = str(REPO_ROOT / "app")
    server_dir = str(REPO_ROOT / "app" / "server")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{app_dir}:{server_dir}" + (f":{existing}" if existing else "")
    proc = subprocess.Popen(
        [
            python, "-m", "background.main",
        ],
        cwd=str(REPO_ROOT),
        env=env,
    )
    _save_pid(PID_BG_FILE, proc.pid)
    _ok(f"Background worker started (PID: {proc.pid})")


@app.command()
def backend(
    port: Optional[int] = typer.Option(
        None, "--port", help="Backend port"
    ),
):
    """Start only the FastAPI backend"""
    port_val = port or _load_port_from_env("BACKEND_PORT", 5000)

    _log("Starting backend server...")
    python = _python_path()
    _log(f"Using Python: {python}")

    _run_migrations()

    port_str = str(port_val)
    proc = subprocess.Popen(
        [
            python, "-m", "uvicorn", "app.server.entrypoints.api:app",
            "--host", "0.0.0.0", "--port", port_str, "--reload",
        ],
        cwd=str(REPO_ROOT),
    )
    _save_pid(PID_FILE, proc.pid)
    _ok(f"Backend started (PID: {proc.pid}) on http://localhost:{port_val}")

    try:
        signal.pause()
    except KeyboardInterrupt:
        pass

    _log("Shutting down backend...")
    _stop_service("backend", PID_FILE)
    _kill_by_pattern("mimo run")
    _ok("Backend stopped.")


@app.command()
def frontend(
    port: Optional[int] = typer.Option(
        None, "--port", help="Frontend port"
    ),
):
    """Start only the frontend dev server"""
    port_val = port or _load_port_from_env("FRONTEND_PORT", 5173)

    _log("Starting frontend dev server...")
    port_str = str(port_val)
    proc = subprocess.Popen(
        ["npm", "run", "dev", "--", "--port", port_str],
        cwd=str(CLIENT_DIR),
    )
    _save_pid(CLIENT_PID_FILE, proc.pid)
    _ok(f"Frontend started (PID: {proc.pid}) on http://localhost:{port_val}")

    try:
        signal.pause()
    except KeyboardInterrupt:
        pass

    _log("Shutting down frontend...")
    _stop_service("frontend", CLIENT_PID_FILE)
    _ok("Frontend stopped.")


@app.command()
def background():
    """Start only the background worker"""
    _log("Starting background worker...")
    python = _python_path()
    env = os.environ.copy()
    app_dir = str(REPO_ROOT / "app")
    server_dir = str(REPO_ROOT / "app" / "server")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{app_dir}:{server_dir}" + (f":{existing}" if existing else "")
    proc = subprocess.Popen(
        [python, "-m", "background.main"],
        cwd=str(REPO_ROOT),
        env=env,
    )
    _save_pid(PID_BG_FILE, proc.pid)
    _ok(f"Background worker started (PID: {proc.pid})")

    try:
        signal.pause()
    except KeyboardInterrupt:
        pass

    _log("Shutting down background worker...")
    _stop_service("background", PID_BG_FILE)
    _ok("Background worker stopped.")


test_app = typer.Typer(help="Run tests")
app.add_typer(test_app, name="test", no_args_is_help=True)


def _run_backend_tests() -> bool:
    config = _python_path()
    _log("Running backend tests...")
    result = subprocess.run(
        [config, "-m", "pytest", "server/tests", "-v", "--tb=short"],
        cwd=str(REPO_ROOT / "app"),
    )
    if result.returncode == 0:
        return True
    _err("Backend tests failed.")
    return False


def _run_frontend_tests() -> bool:
    _log("Running frontend tests...")
    result = subprocess.run(
        ["npm", "run", "test"],
        cwd=str(CLIENT_DIR),
    )
    if result.returncode == 0:
        return True
    _err("Frontend tests failed.")
    return False


@test_app.command()
def all():
    """Run backend + frontend tests"""
    ok = True
    if not _run_backend_tests():
        ok = False
    if not _run_frontend_tests():
        ok = False
    if ok:
        _ok("All tests passed.")
    else:
        raise typer.Exit(code=1)


@test_app.command()
def backend():
    """Run backend tests only"""
    if _run_backend_tests():
        _ok("Backend tests passed.")
    else:
        raise typer.Exit(code=1)


@test_app.command()
def frontend():
    """Run frontend tests only"""
    if _run_frontend_tests():
        _ok("Frontend tests passed.")
    else:
        raise typer.Exit(code=1)


@app.command()
def lint():
    """Run all linters"""
    _log("Running linters...")
    failed = False

    _log("Linting backend (ruff)...")
    python = _python_path()
    ruff = subprocess.run(
        [python, "-m", "ruff", "check", "app/server"],
        cwd=str(REPO_ROOT),
    )
    if ruff.returncode != 0:
        _warn("Ruff lint issues found")
        failed = True
    else:
        _ok("Ruff: OK")

    _log("Linting frontend (eslint)...")
    eslint = subprocess.run(
        ["npm", "run", "lint"],
        cwd=str(CLIENT_DIR),
    )
    if eslint.returncode != 0:
        _warn("ESLint issues found")
        failed = True
    else:
        _ok("ESLint: OK")

    if failed:
        raise typer.Exit(code=1)
    _ok("All linters passed.")


@app.command()
def format():
    """Run all formatters"""
    _log("Running formatters...")
    failed = False

    _log("Formatting backend (ruff)...")
    python = _python_path()
    ruff = subprocess.run(
        [python, "-m", "ruff", "format", "app/server"],
        cwd=str(REPO_ROOT),
    )
    if ruff.returncode != 0:
        _warn("Ruff format issues")
        failed = True
    else:
        _ok("Ruff format: OK")

    _log("Formatting frontend (prettier)...")
    prettier = subprocess.run(
        ["npm", "run", "format"],
        cwd=str(CLIENT_DIR),
    )
    if prettier.returncode != 0:
        _warn("Prettier format issues")
        failed = True
    else:
        _ok("Prettier: OK")

    if failed:
        raise typer.Exit(code=1)
    _ok("All formatters passed.")


@app.command()
def migrate():
    """Run database migrations"""
    _log("Running database migrations...")
    alembic = _alembic_path()
    result = subprocess.run(
        [alembic, "upgrade", "head"],
        cwd=str(REPO_ROOT),
    )
    if result.returncode == 0:
        _ok("Migrations applied successfully.")
    else:
        raise typer.Exit(code=1)


@db_app.command()
def up():
    """Run pending migrations up"""
    _log("Running migrations up...")
    alembic = _alembic_path()
    result = subprocess.run(
        [alembic, "upgrade", "head"],
        cwd=str(REPO_ROOT),
    )
    if result.returncode == 0:
        _ok("Migrations applied.")
    else:
        raise typer.Exit(code=1)


@db_app.command()
def down():
    """Rollback last migration"""
    _log("Rolling back last migration...")
    alembic = _alembic_path()
    result = subprocess.run(
        [alembic, "downgrade", "-1"],
        cwd=str(REPO_ROOT),
    )
    if result.returncode == 0:
        _ok("Migration rolled back.")
    else:
        raise typer.Exit(code=1)


@db_app.command()
def new(name: str = typer.Argument(..., help="Migration name")):
    """Create a new migration"""
    _log(f"Creating migration: {name}")
    alembic = _alembic_path()
    result = subprocess.run(
        [alembic, "revision", "--autogenerate", "-m", name],
        cwd=str(REPO_ROOT),
    )
    if result.returncode == 0:
        _ok(f"Migration '{name}' created.")
    else:
        raise typer.Exit(code=1)


@docker_app.command()
def up():
    """Start docker containers"""
    _log("Starting docker containers...")
    result = subprocess.run(
        ["docker", "compose", "up", "-d"],
        cwd=str(REPO_ROOT),
    )
    if result.returncode == 0:
        _ok("Docker containers started.")
    else:
        raise typer.Exit(code=1)


@docker_app.command()
def down():
    """Stop docker containers"""
    _log("Stopping docker containers...")
    result = subprocess.run(
        ["docker", "compose", "down"],
        cwd=str(REPO_ROOT),
    )
    if result.returncode == 0:
        _ok("Docker containers stopped.")
    else:
        raise typer.Exit(code=1)


@docker_app.command()
def status():
    """Show docker container status"""
    _log("Docker container status:")
    result = subprocess.run(
        ["docker", "compose", "ps"],
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        raise typer.Exit(code=1)


@app.command()
def clean():
    """Remove build artifacts and caches"""
    _log("Cleaning build artifacts...")
    dirs = [
        REPO_ROOT / "app" / "server" / "__pycache__",
        REPO_ROOT / "app" / "client" / "node_modules" / ".cache",
        REPO_ROOT / "target",
        REPO_ROOT / "tmp",
        REPO_ROOT / ".pytest_cache",
    ]
    for d in dirs:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
            _ok(f"Removed: {d}")
    _ok("Clean completed.")


@app.command()
def doctor():
    """Validate development environment"""
    _header("Environment Check")
    all_ok = True

    tools = [
        ("rustc", ("--version",)),
        ("cargo", ("--version",)),
        ("python3", ("--version",)),
        ("node", ("--version",)),
        ("npm", ("--version",)),
        ("docker", ("--version",)),
        ("git", ("--version",)),
    ]
    for tool_name, args in tools:
        ok, msg = _check_tool(tool_name, *args)
        if ok:
            _ok(msg)
        else:
            _err(msg)
            all_ok = False

    if VENV_DIR.exists():
        _ok(f"Python venv: {VENV_DIR}")
    else:
        _warn("Python venv not found (expected at .venv/)")

    if SERVER_DIR.exists():
        _ok(f"Server dir: {SERVER_DIR}")
    else:
        _err("Server directory not found")
        all_ok = False

    if CLIENT_DIR.exists():
        _ok(f"Client dir: {CLIENT_DIR}")
    else:
        _err("Client directory not found")
        all_ok = False

    if (REPO_ROOT / ".env").exists():
        _ok(".env file found")
    else:
        _warn(".env file not found")

    console.print()
    if all_ok:
        _ok("All checks passed! Environment is ready.")
    else:
        _warn("Some checks failed. Please fix the issues above.")


@app.command()
def logs():
    """Stream logs from running services"""
    _log("Streaming logs...")
    log_file = REPO_ROOT / "tmp" / "app.log"
    if log_file.exists():
        subprocess.run(["tail", "-f", str(log_file)])
    else:
        _warn("No log file found at tmp/app.log")
        _log("Starting log tail from journalctl...")
        subprocess.run(["journalctl", "-f", "-u", "job-search"])


@app.command()
def version():
    """Show version information"""
    _header("Job Search Developer CLI")
    console.print("  Version: 0.1.0")
    console.print("  Binary:  start")
    console.print()


@app.command()
def stop():
    """Stop all running processes"""
    _log("Stopping all processes...")
    _stop_service("backend", PID_FILE)
    _stop_service("frontend", CLIENT_PID_FILE)
    _stop_service("background", PID_BG_FILE)
    _kill_by_pattern("mimo run")
    _ok("All processes stopped.")


@app.command()
def status():
    """Show status of running processes"""
    _header("Job Search App Status")

    backend_pid = _read_pid(PID_FILE)
    if backend_pid is not None and _is_process_alive(backend_pid):
        port = _load_port_from_env("BACKEND_PORT", 5000)
        _ok(f"Backend:  Running (PID: {backend_pid}) — http://localhost:{port}")
    else:
        _warn("Backend:  Not running")

    frontend_pid = _read_pid(CLIENT_PID_FILE)
    if frontend_pid is not None and _is_process_alive(frontend_pid):
        port = _load_port_from_env("FRONTEND_PORT", 5173)
        _ok(f"Frontend: Running (PID: {frontend_pid}) — http://localhost:{port}")
    else:
        _warn("Frontend: Not running")

    background_pid = _read_pid(PID_BG_FILE)
    if background_pid is not None and _is_process_alive(background_pid):
        _ok(f"Background: Running (PID: {background_pid})")
    else:
        _warn("Background: Not running")

    mimo = subprocess.run(
        ["pgrep", "-f", "mimo run"], capture_output=True, text=True
    )
    count = len([l for l in mimo.stdout.splitlines() if l.strip()])
    if count > 0:
        _warn(f"Mimo AI:  {count} process(es) running")
    else:
        _ok("Mimo AI:  No processes running")

    env_file = REPO_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("AI_PROVIDER="):
                provider = line.split("=", 1)[1]
                _ok(f"AI Provider: {provider}")
                break

    console.print()


if __name__ == "__main__":
    app()
