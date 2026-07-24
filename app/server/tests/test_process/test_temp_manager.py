"""Tests for TempFileManager — temp file tracking and cleanup."""

import os
import tempfile

import pytest
from services.process.temp_manager import TempFileManager


@pytest.fixture(autouse=True)
def reset_singleton():
    TempFileManager.reset()
    yield
    TempFileManager.reset()


@pytest.fixture
def tmp_files():
    """Create temp files and yield their paths, then clean up."""
    files = []
    for _ in range(3):
        f = tempfile.NamedTemporaryFile(delete=False, prefix='test_proc_')
        f.write(b'test data')
        f.close()
        files.append(f.name)
    yield files
    for p in files:
        try:
            os.remove(p)
        except OSError:
            pass


class TestTempFileManager:
    def test_register_and_cleanup(self, tmp_files):
        tm = TempFileManager()
        for f in tmp_files:
            tm.register('job1', f)

        removed = tm.cleanup('job1')
        assert removed == 3
        for f in tmp_files:
            assert not os.path.exists(f)

    def test_cleanup_nonexistent_key(self):
        tm = TempFileManager()
        removed = tm.cleanup('nonexistent')
        assert removed == 0

    def test_cleanup_all(self, tmp_files):
        tm = TempFileManager()
        for f in tmp_files:
            tm.register('job1', f)

        removed = tm.cleanup_all()
        assert removed == 3
        for f in tmp_files:
            assert not os.path.exists(f)

    def test_no_duplicates(self, tmp_files):
        tm = TempFileManager()
        tm.register('job1', tmp_files[0])
        tm.register('job1', tmp_files[0])  # duplicate
        removed = tm.cleanup('job1')
        assert removed == 1  # only one file, not two

    def test_multiple_jobs(self, tmp_files):
        tm = TempFileManager()
        tm.register('job1', tmp_files[0])
        tm.register('job2', tmp_files[1])
        tm.register('job2', tmp_files[2])

        tm.cleanup('job1')
        assert not os.path.exists(tmp_files[0])
        assert os.path.exists(tmp_files[1])  # still exists
        assert os.path.exists(tmp_files[2])  # still exists

        tm.cleanup('job2')
        assert not os.path.exists(tmp_files[1])
        assert not os.path.exists(tmp_files[2])
