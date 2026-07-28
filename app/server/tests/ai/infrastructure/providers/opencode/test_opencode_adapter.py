"""Tests for OpencodeProvider — _project_root, start_new_session, session_id flow."""

import os
import pytest
from unittest.mock import patch, MagicMock


class TestProjectRoot:
    """Test _project_root resolves to repo root (4 levels up from adapter.py)."""

    def test_project_root_points_to_repo_root(self):
        from ai.infrastructure.providers.opencode import adapter
        expected = os.path.abspath(os.path.join(
            os.path.dirname(adapter.__file__), '..', '..', '..', '..', '..', '..'
        ))
        assert adapter._project_root == expected

    def test_project_root_is_valid_directory(self):
        from ai.infrastructure.providers.opencode import adapter
        assert os.path.isdir(adapter._project_root)

    def test_project_root_contains_app_dir(self):
        from ai.infrastructure.providers.opencode import adapter
        assert os.path.isdir(os.path.join(adapter._project_root, 'app'))


class TestOpenCodeBin:
    """Test OPENCODE_BIN points to existing binary."""

    def test_opencode_bin_path(self):
        from ai.infrastructure.providers.opencode import adapter
        assert adapter.OPENCODE_BIN.endswith('opencode')

    @pytest.mark.skipif(not os.path.exists(os.path.expanduser('~/.opencode/bin/opencode')),
                        reason="opencode binary not installed")
    def test_opencode_bin_exists(self):
        from ai.infrastructure.providers.opencode import adapter
        assert os.path.exists(adapter.OPENCODE_BIN)


class TestBuildCmd:
    """Test command building."""

    def test_basic_cmd(self):
        from ai.infrastructure.providers.opencode.adapter import OpencodeProvider
        provider = OpencodeProvider()
        cmd = provider._build_cmd('test prompt')
        assert cmd[0].endswith('opencode')
        assert 'run' in cmd
        assert 'test prompt' in cmd
        assert '--format' in cmd
        assert 'json' in cmd
        assert '--dangerously-skip-permissions' in cmd

    def test_cmd_with_session_id(self):
        from ai.infrastructure.providers.opencode.adapter import OpencodeProvider
        provider = OpencodeProvider()
        cmd = provider._build_cmd('test prompt', session_id='ses_123')
        assert '--session' in cmd
        assert 'ses_123' in cmd

    def test_cmd_without_session_id(self):
        from ai.infrastructure.providers.opencode.adapter import OpencodeProvider
        provider = OpencodeProvider()
        cmd = provider._build_cmd('test prompt', session_id=None)
        assert '--session' not in cmd


class TestRunSubprocess:
    """Test subprocess uses start_new_session=True."""

    def test_start_new_session_flag(self):
        """Verify Popen is called with start_new_session=True."""
        import subprocess
        original_popen = subprocess.Popen

        captured_kwargs = {}

        def mock_popen(*args, **kwargs):
            captured_kwargs.update(kwargs)
            raise RuntimeError("Don't actually run")

        with patch('subprocess.Popen', side_effect=mock_popen):
            from ai.infrastructure.providers.opencode.adapter import OpencodeProvider
            provider = OpencodeProvider()
            try:
                provider._run_subprocess(['echo', 'test'], timeout=5)
            except RuntimeError:
                pass

        assert captured_kwargs.get('start_new_session') is True


class TestSessionIdFlow:
    """Test session_id is passed through context and saved."""

    def test_session_id_extracted_from_events(self):
        """Verify _run_subprocess extracts session_id from JSON events."""
        from ai.infrastructure.providers.opencode.adapter import OpencodeProvider
        import json

        events = [
            json.dumps({"type": "step_start", "sessionID": "ses_test123"}),
            json.dumps({"type": "text", "part": {"text": "hello"}}),
            json.dumps({"type": "step_finish"}),
        ]

        proc_mock = MagicMock()
        proc_mock.stdout = iter(events)
        proc_mock.returncode = 0
        proc_mock.wait.return_value = 0

        with patch('subprocess.Popen', return_value=proc_mock):
            provider = OpencodeProvider()
            returncode, lines, session_id = provider._run_subprocess(
                ['test'], timeout=10
            )

        assert returncode == 0
        assert session_id == "ses_test123"
        assert len(lines) == 3

    def test_session_id_none_when_no_events(self):
        from ai.infrastructure.providers.opencode.adapter import OpencodeProvider
        import json

        events = [
            json.dumps({"type": "text", "part": {"text": "hello"}}),
        ]

        proc_mock = MagicMock()
        proc_mock.stdout = iter(events)
        proc_mock.returncode = 0
        proc_mock.wait.return_value = 0

        with patch('subprocess.Popen', return_value=proc_mock):
            provider = OpencodeProvider()
            returncode, lines, session_id = provider._run_subprocess(
                ['test'], timeout=10
            )

        assert session_id is None

    def test_session_id_callback_called(self):
        from ai.infrastructure.providers.opencode.adapter import OpencodeProvider
        import json

        events = [
            json.dumps({"type": "step_start", "sessionID": "ses_cb_test"}),
        ]

        proc_mock = MagicMock()
        proc_mock.stdout = iter(events)
        proc_mock.returncode = 0
        proc_mock.wait.return_value = 0

        callback = MagicMock()

        with patch('subprocess.Popen', return_value=proc_mock):
            provider = OpencodeProvider()
            provider._run_subprocess(
                ['test'], timeout=10, on_session_id=callback
            )

        callback.assert_called_once_with("ses_cb_test")


class TestExtractAllSessionId:
    """Test _extract_all passes and saves session_id."""

    def test_extract_all_passes_session_id(self):
        """Verify _extract_all passes session_id in context."""
        from jobs.infrastructure.workers.worker import _extract_all
        from unittest.mock import patch, MagicMock

        mock_resp = MagicMock()
        mock_resp.content = '{"valid": true}'
        mock_resp.metadata = {"session_id": "ses_extract_test"}

        mock_llm = MagicMock()
        mock_llm.generate_structured.return_value = mock_resp

        with patch('jobs.infrastructure.workers.worker.get_llm_service', return_value=mock_llm), \
             patch('jobs.infrastructure.workers.worker.load_prompt', return_value='test prompt'), \
             patch('jobs.infrastructure.workers.worker._save_session_id') as mock_save:

            result = _extract_all("test content", 999, session_id="ses_prev_123")

        mock_llm.generate_structured.assert_called_once()
        call_args = mock_llm.generate_structured.call_args
        context = call_args[1]['context'] if 'context' in call_args[1] else call_args[0][1] if len(call_args[0]) > 1 else {}
        assert context.get('session_id') == 'ses_prev_123'

        mock_save.assert_called_once_with(999, 'ses_extract_test')

    def test_extract_all_saves_none_session_id(self):
        """When provider returns no session_id, _save_session_id is not called."""
        from jobs.infrastructure.workers.worker import _extract_all
        from unittest.mock import patch, MagicMock

        mock_resp = MagicMock()
        mock_resp.content = '{"valid": true}'
        mock_resp.metadata = {}

        mock_llm = MagicMock()
        mock_llm.generate_structured.return_value = mock_resp

        with patch('jobs.infrastructure.workers.worker.get_llm_service', return_value=mock_llm), \
             patch('jobs.infrastructure.workers.worker.load_prompt', return_value='test prompt'), \
             patch('jobs.infrastructure.workers.worker._save_session_id') as mock_save:

            result = _extract_all("test content", 999)

        mock_save.assert_not_called()
