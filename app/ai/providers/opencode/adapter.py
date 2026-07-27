"""Opencode CLI provider — wraps the existing opencode CLI integration.

SRP: Only handles opencode CLI communication.
OCP: Extends LLMProvider without modifying it.
DIP: Depends on LLMProvider abstraction.
"""

from __future__ import annotations

import json
import os
import subprocess
import uuid
from typing import Any, Callable, Optional

from ..base import LLMProvider, ProviderConfig, ProviderResponse

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
OPENCODE_BIN = os.path.expanduser('~/.opencode/bin/opencode')


class OpencodeProvider(LLMProvider):
    """Provider that delegates to opencode CLI as a subprocess.

    Wraps the existing opencode CLI integration — handles session awareness,
    JSON event parsing, and process lifecycle. Agents should never
    call opencode CLI directly; they go through this provider.
    """

    def __init__(self, config: Optional[ProviderConfig] = None):
        super().__init__(config or ProviderConfig(name="opencode"))
        self._tmp_dir = os.environ.get('TEMP_DIR', 'tmp')
        if not os.path.isabs(self._tmp_dir):
            self._tmp_dir = os.path.join(_project_root, self._tmp_dir)
        os.makedirs(self._tmp_dir, exist_ok=True)

    def generate(
        self,
        prompt: str,
        context: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> ProviderResponse:
        """Run opencode CLI with a prompt and return the text response."""
        context = context or {}
        timeout = timeout or self._config.timeout
        session_id = context.get("session_id")

        cmd = self._build_cmd(prompt, session_id)
        returncode, output_lines, discovered_session_id = self._run_subprocess(
            cmd, timeout=timeout
        )

        text_parts = []
        for line in output_lines:
            try:
                evt = json.loads(line)
                if evt.get('type') == 'text':
                    text = evt.get('part', {}).get('text', '')
                    if text:
                        text_parts.append(text)
            except json.JSONDecodeError:
                pass

        content = '\n'.join(text_parts)

        if returncode != 0:
            raise RuntimeError(f"opencode failed (exit code {returncode}): {content[:300]}")

        return ProviderResponse(
            content=content,
            metadata={"returncode": returncode, "lines": len(output_lines)},
            provider="opencode",
            model="opencode-cli",
        )

    def generate_structured(
        self,
        prompt: str,
        schema: Optional[dict] = None,
        context: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> ProviderResponse:
        """Run opencode CLI expecting a JSON result file as output."""
        context = context or {}
        timeout = timeout or self._config.timeout
        session_id = context.get("session_id")
        result_file = context.get("result_file")

        if not result_file:
            pid = context.get("pid", uuid.uuid4().hex[:12])
            result_file = os.path.join(self._tmp_dir, f'ai_result_{pid}.json')

        cmd = self._build_cmd(prompt, session_id)
        returncode, output_lines, discovered_session_id = self._run_subprocess(
            cmd, timeout=timeout
        )

        if returncode != 0:
            error_msg = f"exit code {returncode}"
            for line in output_lines:
                try:
                    evt = json.loads(line)
                    if evt.get('type') == 'text':
                        error_msg = evt.get('part', {}).get('text', error_msg)[:300]
                except json.JSONDecodeError:
                    continue
            raise RuntimeError(f"opencode failed: {error_msg}")

        if os.path.exists(result_file):
            try:
                with open(result_file) as f:
                    result = json.load(f)
                try:
                    os.remove(result_file)
                except OSError:
                    pass
                return ProviderResponse(
                    content=json.dumps(result, ensure_ascii=False),
                    metadata={"result_file": result_file, "returncode": returncode, "session_id": discovered_session_id},
                    provider="opencode",
                    model="opencode-cli",
                )
            except (json.JSONDecodeError, OSError) as e:
                raise RuntimeError(f"Failed to parse opencode result: {e}")

        raise RuntimeError(f"opencode returned no result file: {result_file}")

    def _build_cmd(self, prompt: str, session_id: Optional[str] = None) -> list:
        """Build opencode CLI command."""
        cmd = [OPENCODE_BIN, 'run', prompt, '--format', 'json', '--dangerously-skip-permissions']
        if session_id:
            cmd.extend(['--session', session_id])
        return cmd

    def _run_subprocess(
        self,
        cmd: list,
        timeout: int = 300,
        cwd: Optional[str] = None,
        on_event: Optional[Callable] = None,
        on_session_id: Optional[Callable] = None,
    ) -> tuple[int, list[str], Optional[str]]:
        """Run opencode subprocess with streaming output and event callbacks.

        Returns (returncode, output_lines, session_id).
        """
        env = {**os.environ, 'NO_COLOR': '1'}
        proc = subprocess.Popen(
            cmd,
            cwd=cwd or _project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        )

        all_lines = []
        session_id = None
        import threading
        timed_out = threading.Event()

        def watchdog():
            timed_out.wait(timeout)
            if not timed_out.is_set():
                try:
                    proc.kill()
                except OSError:
                    pass

        timer = threading.Thread(target=watchdog, daemon=True)
        timer.start()

        try:
            for raw_line in proc.stdout:
                line = raw_line.rstrip('\n')
                if not line:
                    continue
                all_lines.append(line)
                try:
                    evt = json.loads(line)

                    # Extract session_id
                    if not session_id:
                        sid = (evt.get('sessionID') or evt.get('session_id')
                               or evt.get('sessionId'))
                        if not sid and 'session' in evt and isinstance(evt['session'], dict):
                            sid = evt['session'].get('id') or evt['session'].get('ID')
                        if sid:
                            session_id = sid
                            if on_session_id:
                                try:
                                    on_session_id(sid)
                                except Exception:
                                    pass

                    # Forward event to callback
                    if on_event:
                        try:
                            on_event(evt)
                        except Exception:
                            pass

                except json.JSONDecodeError:
                    pass

            timed_out.set()
            proc.wait()
            return proc.returncode, all_lines, session_id

        except Exception:
            timed_out.set()
            try:
                proc.kill()
            except OSError:
                pass
            proc.wait()
            raise
        finally:
            timed_out.set()
