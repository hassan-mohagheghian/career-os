"""Tests for ProcessManager — subprocess lifecycle with process groups."""

import os
import signal
import subprocess
import time

import pytest
from services.process.process_manager import ProcessManager
from services.process.models import ProcessHandle


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset ProcessManager singleton before each test."""
    ProcessManager.reset()
    yield
    ProcessManager.reset()


class TestProcessManager:
    def test_singleton(self):
        a = ProcessManager()
        b = ProcessManager()
        assert a is b

    def test_start_and_track(self):
        pm = ProcessManager()
        handle = pm.start(
            ['sleep', '10'], cwd='/tmp', env=os.environ.copy(),
            timeout=30, description='test sleep', key='test1',
        )
        assert handle.is_alive
        assert pm.is_alive('test1')
        assert pm.get('test1') is handle
        pm.cancel(handle)
        pm.remove('test1')

    def test_cancel_sigterm_then_sigkill(self):
        pm = ProcessManager()
        # Start a process that ignores SIGTERM
        handle = pm.start(
            ['python3', '-c', 'import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)'],
            cwd='/tmp', env=os.environ.copy(),
            timeout=30, description='ignorer', key='ignore1',
        )
        assert handle.is_alive
        terminated = pm.cancel(handle, grace_period=1.0)
        assert terminated
        assert not handle.is_alive
        pm.remove('ignore1')

    def test_cancel_already_dead(self):
        pm = ProcessManager()
        handle = pm.start(
            ['true'], cwd='/tmp', env=os.environ.copy(),
            timeout=5, description='instant', key='dead1',
        )
        time.sleep(0.5)  # let it finish
        assert pm.cancel(handle)  # should return True even if already dead
        pm.remove('dead1')

    def test_cleanup_all(self):
        pm = ProcessManager()
        h1 = pm.start(['sleep', '10'], cwd='/tmp', env=os.environ.copy(),
                       timeout=30, key='c1')
        h2 = pm.start(['sleep', '10'], cwd='/tmp', env=os.environ.copy(),
                       timeout=30, key='c2')
        killed = pm.cleanup_all()
        assert killed == 2
        assert not h1.is_alive
        assert not h2.is_alive

    def test_get_nonexistent(self):
        pm = ProcessManager()
        assert pm.get('nope') is None
        assert not pm.is_alive('nope')
