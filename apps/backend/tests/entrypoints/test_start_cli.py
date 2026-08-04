"""Tests for the developer CLI reload configuration (apps/start.py).

Reload mode must pick up code changes but never restart the apps for
test-file edits, so the uvicorn command excludes test files/directories.
"""

import os
import sys
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from apps.start import REPO_ROOT, SERVER_DIR, _start_backend, _uvicorn_args


def test_uvicorn_args_enable_reload():
    args = _uvicorn_args(5000)
    assert '-m' in args
    assert 'uvicorn' in args
    assert '--reload' in args
    assert '--host' in args and '0.0.0.0' in args
    assert '--port' in args and '5000' in args


def test_uvicorn_args_exclude_backend_tests_dir():
    args = _uvicorn_args(5000)
    assert '--reload-exclude' in args
    assert str(SERVER_DIR / 'tests') in args


def test_uvicorn_args_exclude_test_file_globs():
    args = _uvicorn_args(5000)
    assert 'test_*.py' in args
    assert '*_test.py' in args


def test_uvicorn_args_bounded_graceful_shutdown():
    """Long-lived SSE connections must not block reloads forever.

    The frontend keeps an open stream at /events/processing; without a graceful
    shutdown timeout uvicorn waits indefinitely for it to close and the reload
    hangs on "Waiting for connections to close".
    """
    args = _uvicorn_args(5000)
    assert '--timeout-graceful-shutdown' in args
    assert args[args.index('--timeout-graceful-shutdown') + 1] == '5'


def test_start_backend_passes_reload_excludes_to_uvicorn():
    with patch('apps.start._run_migrations'), \
         patch('apps.start._save_pid'), \
         patch('apps.start.subprocess.Popen') as popen:
        _start_backend(5000)
    args = popen.call_args[0][0]
    assert '--reload' in args
    assert '--reload-exclude' in args
    assert str(SERVER_DIR / 'tests') in args
    assert 'test_*.py' in args
    assert '*_test.py' in args
    assert popen.call_args[1]['cwd'] == str(REPO_ROOT)


def test_uvicorn_reload_filter_ignores_tests_but_keeps_source():
    from uvicorn.supervisors.watchfilesreload import FileFilter
    cfg = Mock()
    cfg.reload_includes = []
    cfg.reload_excludes = [str(SERVER_DIR / 'tests'), 'test_*.py', '*_test.py']
    flt = FileFilter(cfg)
    assert not flt(SERVER_DIR / 'tests' / 'jobs' / 'presentation' / 'test_jobs_api.py')
    assert not flt(SERVER_DIR / 'tests' / 'conftest.py')
    assert not flt(SERVER_DIR / 'tests' / '__init__.py')
    assert flt(SERVER_DIR / 'jobs' / 'application' / 'services.py')
    assert flt(SERVER_DIR / 'entrypoints' / 'api.py')
