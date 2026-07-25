"""Mimo CLI provider — wraps the existing MimoRunner subprocess integration.

SRP: Only handles mimo CLI communication.
OCP: Extends LLMProvider without modifying it.
DIP: Depends on LLMProvider abstraction.
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Any, Callable, Optional

from ..base import LLMProvider, ProviderConfig, ProviderResponse

_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_file_dir, '..', '..', '..', '..'))
MIMO_BIN = os.path.expanduser('~/.mimocode/bin/mimo')


class MimoProvider(LLMProvider):
    """Provider that delegates to mimo CLI as a subprocess.

    Wraps the existing MimoRunner logic — handles session awareness,
    JSON event parsing, and process lifecycle. Agents should never
    call MimoRunner directly; they go through this provider.
    """

    def __init__(self, config: Optional[ProviderConfig] = None):
        super().__init__(config or ProviderConfig(name="mimo"))
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
        """Run mimo CLI with a prompt and return the text response."""
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
            raise RuntimeError(f"mimo failed (exit code {returncode}): {content[:300]}")

        return ProviderResponse(
            content=content,
            metadata={"returncode": returncode, "lines": len(output_lines)},
            provider="mimo",
            model="mimo-cli",
        )

    def generate_structured(
        self,
        prompt: str,
        schema: Optional[dict] = None,
        context: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> ProviderResponse:
        """Run mimo CLI expecting a JSON result file as output."""
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
            raise RuntimeError(f"mimo failed: {error_msg}")

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
                    metadata={"result_file": result_file, "returncode": returncode},
                    provider="mimo",
                    model="mimo-cli",
                )
            except (json.JSONDecodeError, OSError) as e:
                raise RuntimeError(f"Failed to parse mimo result: {e}")

        raise RuntimeError(f"mimo returned no result file: {result_file}")

    def generate_streaming(
        self,
        prompt: str,
        context: Optional[dict] = None,
        timeout: Optional[int] = None,
        on_event: Optional[Callable] = None,
        on_session_id: Optional[Callable] = None,
    ) -> ProviderResponse:
        """Run mimo with streaming event callbacks.

        Supports real-time event forwarding and session ID discovery.
        Used by workers that need live progress updates.

        Args:
            prompt: The prompt to send.
            context: Optional context (session_id, pid, key, cwd).
            timeout: Timeout in seconds.
            on_event: Called for each JSON event from mimo.
            on_session_id: Called when session_id is discovered.

        Returns:
            ProviderResponse with raw output lines in metadata.
        """
        context = context or {}
        timeout = timeout or self._config.timeout
        session_id = context.get("session_id")
        key = context.get("key")

        cmd = self._build_cmd(prompt, session_id)
        cwd = context.get("cwd", _project_root)

        returncode, output_lines, discovered_session_id = self._run_subprocess(
            cmd, timeout=timeout, cwd=cwd,
            on_event=on_event, on_session_id=on_session_id,
        )

        if returncode == -9:
            raise RuntimeError(f"mimo timed out after {timeout}s")

        # Build content from text events
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

        return ProviderResponse(
            content='\n'.join(text_parts),
            metadata={
                "returncode": returncode,
                "lines": output_lines,
                "session_id": discovered_session_id,
                "line_count": len(output_lines),
            },
            provider="mimo",
            model="mimo-cli",
        )

    def _build_cmd(self, prompt: str, session_id: Optional[str] = None) -> list:
        """Build mimo CLI command."""
        cmd = [MIMO_BIN, 'run', prompt, '--format', 'json', '--dangerously-skip-permissions']
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
        """Run mimo subprocess with streaming output and event callbacks.

        Returns (returncode, output_lines, session_id).
        """
        import subprocess
        import threading

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
