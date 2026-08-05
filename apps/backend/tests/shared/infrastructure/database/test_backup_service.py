"""Tests for shared.infrastructure.database.backup_service."""

import sys
import os
from unittest.mock import MagicMock, mock_open, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

import shared.infrastructure.database.backup_service as backup


@pytest.fixture(autouse=True)
def _patch_config(tmp_path):
    """Point the backup service at a temp directory and known credentials."""
    with patch.object(backup, 'DB_BACKUP_DIR', str(tmp_path)), \
            patch.object(backup, 'DB_BACKUP_CONTAINER', 'job-search-postgres-1'), \
            patch.object(backup, 'DB_BACKUP_KEEP_COUNT', 3), \
            patch.object(backup, '_db_credentials', return_value=('jobsearch', 'jobsearch')):
        yield tmp_path


def _touch_backup(dir_path: str, name: str) -> str:
    path = os.path.join(dir_path, name)
    with open(path, 'w') as fh:
        fh.write('dump')
    return path


class TestCreateDbBackup:
    def test_runs_pg_dump_via_docker_exec(self, _patch_config):
        with patch('shared.infrastructure.database.backup_service.subprocess.run',
                   return_value=MagicMock(returncode=0, stderr=b'')) as m_run, \
                patch('builtins.open', mock_open()):
            path = backup.create_db_backup()

        args = m_run.call_args.args[0]
        assert args[:2] == ['docker', 'exec']
        assert args[2] == 'job-search-postgres-1'
        assert args[3] == 'pg_dump'
        assert '-U' in args and args[args.index('-U') + 1] == 'jobsearch'
        assert '-d' in args and args[args.index('-d') + 1] == 'jobsearch'
        assert '--format=custom' in args
        assert os.path.basename(path).startswith('jobsearch_')
        assert path.endswith('.dump')

    def test_removes_file_and_raises_on_failure(self, _patch_config):
        with patch('shared.infrastructure.database.backup_service.subprocess.run',
                   return_value=MagicMock(returncode=1, stderr=b'connection refused')), \
                patch('builtins.open', mock_open()), \
                patch('shared.infrastructure.database.backup_service.os.remove') as m_remove:
            with pytest.raises(RuntimeError, match='pg_dump failed'):
                backup.create_db_backup()
        m_remove.assert_called_once()
        assert backup.list_backups() == []


class TestListBackups:
    def test_returns_oldest_first(self, _patch_config):
        _touch_backup(_patch_config, 'jobsearch_20260803_100000.dump')
        _touch_backup(_patch_config, 'jobsearch_20260805_100000.dump')
        _touch_backup(_patch_config, 'jobsearch_20260804_100000.dump')
        names = [os.path.basename(p) for p in backup.list_backups()]
        assert names == [
            'jobsearch_20260803_100000.dump',
            'jobsearch_20260804_100000.dump',
            'jobsearch_20260805_100000.dump',
        ]

    def test_ignores_unrelated_files(self, _patch_config):
        _touch_backup(_patch_config, 'jobsearch_20260805_100000.dump')
        _touch_backup(_patch_config, 'notes.txt')
        assert len(backup.list_backups()) == 1


class TestPruneOldBackups:
    def test_keeps_only_three_most_recent(self, _patch_config):
        for name in (
            'jobsearch_20260801_100000.dump',
            'jobsearch_20260802_100000.dump',
            'jobsearch_20260803_100000.dump',
            'jobsearch_20260804_100000.dump',
            'jobsearch_20260805_100000.dump',
        ):
            _touch_backup(_patch_config, name)

        removed = backup.prune_old_backups(keep=3)

        remaining = {os.path.basename(p) for p in backup.list_backups()}
        assert remaining == {
            'jobsearch_20260803_100000.dump',
            'jobsearch_20260804_100000.dump',
            'jobsearch_20260805_100000.dump',
        }
        assert {os.path.basename(p) for p in removed} == {
            'jobsearch_20260801_100000.dump',
            'jobsearch_20260802_100000.dump',
        }

    def test_keep_zero_removes_everything(self, _patch_config):
        _touch_backup(_patch_config, 'jobsearch_20260805_100000.dump')
        removed = backup.prune_old_backups(keep=0)
        assert len(removed) == 1
        assert backup.list_backups() == []

    def test_no_files_removed_within_keep(self, _patch_config):
        _touch_backup(_patch_config, 'jobsearch_20260805_100000.dump')
        assert backup.prune_old_backups(keep=3) == []


class TestRunDbBackup:
    def test_summary(self, _patch_config):
        with patch.object(backup, 'create_db_backup', return_value='/tmp/backups/jobsearch_20260805_100000.dump') as m_create, \
                patch.object(backup, 'prune_old_backups', return_value=['/tmp/backups/jobsearch_20260801_100000.dump']) as m_prune:
            result = backup.run_db_backup()

        m_create.assert_called_once()
        m_prune.assert_called_once_with(3)
        assert result['created'] == '/tmp/backups/jobsearch_20260805_100000.dump'
        assert result['removed'] == ['/tmp/backups/jobsearch_20260801_100000.dump']
