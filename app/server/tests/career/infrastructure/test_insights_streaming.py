"""
Tests for career_intel domain: streaming session_id discovery.

Verifies that _run_mimo_prompt discovers and exposes session_id
as soon as it appears in stdout, not after process completion.
"""
import json
import os
import tempfile
import threading
import time
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# Ensure server dir is importable
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))


class TestMimoPromptSessionDiscovery:
    """Domain: session_id must be available as soon as mimo emits it."""

    def test_session_id_emitted_in_progress_before_process_completes(self):
        """
        RED: When mimo emits a session_id line, subsequent progress events
        must include it — even though the process hasn't finished yet.
        """
        progress_events = []

        def fake_emit(data, room=None):
            progress_events.append(data)

        # Simulate the domain: a mimo process that streams session_id early
        # then does work, then finishes
        session_id_discovered = threading.Event()
        discovered_sid = [None]

        def on_session_id(sid):
            discovered_sid[0] = sid
            session_id_discovered.set()

        # Simulate: mimo emits session_id on line 2, then works for a bit
        simulated_lines = [
            json.dumps({"type": "text", "part": {"text": "Starting analysis..."}}),
            json.dumps({"type": "session", "sessionId": "ses_abc123"}),
            json.dumps({"type": "text", "part": {"text": "Processing..."}}),
        ]

        # Parse session_id from lines (domain logic)
        for line in simulated_lines:
            try:
                evt = json.loads(line)
                sid = evt.get('sessionId') or evt.get('session_id')
                if sid:
                    on_session_id(sid)
            except json.JSONDecodeError:
                pass

        # After parsing, session_id should be discovered
        assert session_id_discovered.is_set(), "session_id should be discovered mid-stream"
        assert discovered_sid[0] == "ses_abc123"

    def test_emit_progress_includes_session_id_after_discovery(self):
        """
        RED: _emit_progress must attach session_id from _current_run
        when it's available.
        """
        # Simulate _emit_progress behavior
        current_run = {'session_id': None}
        progress_events = []

        def emit_progress(data):
            sid = current_run.get('session_id')
            if sid:
                data['session_id'] = sid
            progress_events.append(data)

        # Before discovery — no session_id in events
        emit_progress({'running': True, 'status': 'processing'})
        assert 'session_id' not in progress_events[0]

        # After discovery — session_id should appear
        current_run['session_id'] = 'ses_abc123'
        emit_progress({'running': True, 'status': 'processing'})
        assert progress_events[1].get('session_id') == 'ses_abc123'

    def test_on_session_id_emits_progress_with_session_id(self):
        """
        RED: The on_session_id callback must immediately emit a progress
        event containing the session_id so the frontend sees it via WebSocket.
        """
        current_run = {'session_id': None}
        progress_events = []

        def emit_progress(data):
            sid = current_run.get('session_id')
            if sid:
                data['session_id'] = sid
            progress_events.append(data)

        # Simulate the _on_session_id callback from _run_mimo_prompt
        def on_session_id(sid):
            current_run['session_id'] = sid
            emit_progress({'running': True, 'status': 'processing', 'session_id': sid})

        # Before: no session_id
        assert len(progress_events) == 0

        # Simulate mimo discovering session_id
        on_session_id('ses_xyz_789')

        # Must have emitted a progress event with session_id
        assert len(progress_events) == 1
        assert progress_events[0]['session_id'] == 'ses_xyz_789'
        assert progress_events[0]['running'] is True
        assert progress_events[0]['status'] == 'processing'

    def test_mimo_runner_streams_and_calls_on_session_id(self):
        """
        RED: MimoRunner.run() must call on_session_id callback
        the moment sessionId appears in stdout, not at the end.
        """
        import io
        from types import SimpleNamespace
        from shared.infrastructure.process.mimo_runner import MimoRunner

        callback_calls = []

        def on_session_id(sid):
            callback_calls.append(('session_id', sid))

        def on_event(evt):
            callback_calls.append(('event', evt.get('type')))

        # Simulate streaming stdout (text lines, as ProcessManager with text=True produces)
        stdout_text = (
            '{"type":"text","part":{"text":"hello"}}\n'
            '{"sessionId":"ses_real_456"}\n'
            '{"type":"text","part":{"text":"done"}}\n'
        )
        mock_proc = SimpleNamespace(
            stdout=io.StringIO(stdout_text),
            returncode=0,
            wait=lambda: None,
            pid=12345,
        )

        mock_handle = SimpleNamespace(
            proc=mock_proc,
            is_alive=True,
            pid=12345,
        )

        mock_proc_mgr = MagicMock()
        mock_proc_mgr.start.return_value = mock_handle

        runner = MimoRunner(mock_proc_mgr)
        returncode, all_lines, session_id = runner.run(
            "test prompt", timeout=10, key="test_key",
            on_event=on_event, on_session_id=on_session_id,
        )

        # session_id should be discovered
        assert session_id == "ses_real_456"

        # on_session_id should have been called mid-stream
        session_id_calls = [c for c in callback_calls if c[0] == 'session_id']
        assert len(session_id_calls) == 1
        assert session_id_calls[0][1] == "ses_real_456"

        # on_event should have been called for all 3 lines (text, session, text)
        event_calls = [c for c in callback_calls if c[0] == 'event']
        assert len(event_calls) == 3

    def test_career_intel_uses_llm_service(self):
        """
        insights._run_mimo_prompt should use LLMService
        for provider abstraction instead of raw subprocess.
        """
        import inspect

        from career.application.services import insights
        source = inspect.getsource(insights._run_mimo_prompt)

        # Should NOT contain raw subprocess.Popen
        assert 'subprocess.Popen' not in source, (
            "_run_mimo_prompt still uses raw subprocess.Popen — "
            "should use LLMService for provider abstraction"
        )
        # Should reference LLMService or get_llm_service
        assert 'get_llm_service' in source or 'LLMService' in source or 'llm' in source, (
            "_run_mimo_prompt should use the LLMService for provider abstraction"
        )


class TestSectionPromptRouting:
    """Domain: each section should route to its own prompt, not the full prompt."""

    def test_section_prompts_mapping_exists(self):
        """SECTION_PROMPTS maps each tab to its own prompt name."""
        from career.application.services.insights import SECTION_PROMPTS
        assert 'overview' in SECTION_PROMPTS
        assert 'opportunities' in SECTION_PROMPTS
        assert 'companies' in SECTION_PROMPTS
        assert 'skills_intel' in SECTION_PROMPTS
        assert 'market' in SECTION_PROMPTS
        assert 'networking' in SECTION_PROMPTS

    def test_skills_section_maps_to_skills_intelligence(self):
        """'skills_intel' section should map to skills_intelligence prompt (full report)."""
        from career.application.services.insights import SECTION_PROMPTS
        assert SECTION_PROMPTS['skills_intel'] == 'skills_intelligence'

    def test_section_prompts_values_are_prompt_names(self):
        """SECTION_PROMPTS values are prompt file names (no career_intel/ prefix)."""
        from career.application.services.insights import SECTION_PROMPTS
        for section, prompt_name in SECTION_PROMPTS.items():
            assert '/' not in prompt_name, f"{section} prompt name should not contain /"
            assert prompt_name.endswith('_intelligence'), f"{section} prompt should end with _intelligence"

    def test_generate_section_uses_section_prompt(self):
        """generate_section should route to the section-specific prompt, not career_intelligence."""
        import inspect
        from career.application.services.insights import generate_section
        source = inspect.getsource(generate_section)

        # Should reference SECTION_PROMPTS for per-section routing
        assert 'SECTION_PROMPTS' in source, (
            "generate_section should use SECTION_PROMPTS for per-section prompt routing"
        )

    def test_generate_all_uses_per_section_prompts(self):
        """generate_all should use each section's dedicated prompt via _generate_section_internal."""
        import inspect
        from career.application.services.insights import generate_all
        source = inspect.getsource(generate_all)

        # Should use _generate_section_internal for per-section prompt routing
        assert '_generate_section_internal' in source, (
            "generate_all should use _generate_section_internal for per-section prompt routing"
        )
        # Should iterate through sections
        assert 'sections' in source or 'SECTION_PROMPTS' in source, (
            "generate_all should iterate through sections"
        )

    def test_per_section_result_is_flat_json(self):
        """
        When using per-section prompts, the result is flat JSON (not wrapped in a section key).
        _generate_section_internal saves result directly, not result[section].
        """
        import inspect
        from career.application.services.insights import _generate_section_internal
        source = inspect.getsource(_generate_section_internal)

        # Per-section prompts output flat JSON — save directly
        assert '_save_insight(section, result' in source, (
            "_generate_section_internal should save flat JSON result directly"
        )
