"""AGY CLI provider — wraps the Google Antigravity (agy) CLI subprocess integration.

SRP: Only handles agy CLI communication.
OCP: Extends LLMProvider without modifying it.
DIP: Depends on LLMProvider abstraction.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
from typing import Any, Callable, Optional

from ..base import LLMProvider, ProviderConfig, ProviderResponse
from shared.infrastructure.config.app_config import LLM_DEFAULT_TIMEOUT

_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_file_dir, '..', '..', '..', '..'))

AGY_BIN = shutil.which('agy') or os.path.expanduser('~/.local/bin/agy')


class AGYProvider(LLMProvider):
    """Provider that delegates to agy CLI as a subprocess."""

    def __init__(self, config: Optional[ProviderConfig] = None):
        super().__init__(config or ProviderConfig(name="agy"))
        self._tmp_dir = os.path.join(_project_root, 'tmp')
        os.makedirs(self._tmp_dir, exist_ok=True)

    def generate(
        self,
        prompt: str,
        context: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> ProviderResponse:
        """Run agy CLI with a prompt and return the text response."""
        context = context or {}
        timeout = timeout or self._config.timeout
        conversation_id = context.get("session_id") or context.get("conversation")

        cmd = self._build_cmd(prompt, conversation_id=conversation_id)
        returncode, output_text = self._run_subprocess(cmd, timeout=timeout)

        if returncode != 0:
            raise RuntimeError(f"agy failed (exit code {returncode}): {output_text[:300]}")

        return ProviderResponse(
            content=output_text.strip(),
            metadata={"returncode": returncode},
            provider="agy",
            model=self._config.model or "agy-cli",
        )

    def generate_structured(
        self,
        prompt: str,
        schema: Optional[dict] = None,
        context: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> ProviderResponse:
        """Run agy CLI expecting a JSON structured output."""
        structured_prompt = prompt
        if schema:
            structured_prompt += f"\n\nRespond ONLY with valid JSON matching this schema:\n{json.dumps(schema)}"
        else:
            structured_prompt += "\n\nRespond ONLY with a valid JSON object."

        response = self.generate(structured_prompt, context=context, timeout=timeout)
        content = response.content.strip()

        # Clean markdown codeblocks if wrapped in ```json ... ```
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines).strip()

        # Verify JSON
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse agy JSON output: {e}\nRaw output: {content[:300]}")

        return ProviderResponse(
            content=content,
            metadata=response.metadata,
            provider="agy",
            model=self._config.model or "agy-cli",
        )

    def _build_cmd(self, prompt: str, conversation_id: Optional[str] = None) -> list[str]:
        """Build agy CLI command."""
        cmd = [AGY_BIN, "--print", prompt, "--dangerously-skip-permissions"]
        if self._config.model:
            cmd.extend(["--model", self._config.model])
        if conversation_id:
            cmd.extend(["--conversation", conversation_id])
        return cmd

    def _run_subprocess(
        self,
        cmd: list[str],
        timeout: int = LLM_DEFAULT_TIMEOUT,
        cwd: Optional[str] = None,
    ) -> tuple[int, str]:
        """Run agy subprocess with timeout. Returns (returncode, output_text)."""
        env = {**os.environ, "NO_COLOR": "1"}
        proc = subprocess.Popen(
            cmd,
            cwd=cwd or _project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        )

        output_chunks = []
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
                output_chunks.append(raw_line)
            timed_out.set()
            proc.wait()
            if timed_out.is_set() and proc.returncode == -9:
                raise RuntimeError(f"agy command timed out after {timeout}s")
            return proc.returncode, "".join(output_chunks)
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
