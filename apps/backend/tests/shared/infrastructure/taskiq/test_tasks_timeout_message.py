"""Unit tests for the processing-timeout error message helper."""

from __future__ import annotations

from datetime import datetime, UTC, timedelta

from shared.infrastructure.taskiq.tasks import _timeout_message


def test_message_reports_real_elapsed():
    msg = _timeout_message(612)
    assert "timed out after 612s" in msg
    assert "Check status or retry" in msg


def test_message_no_liveness_claim():
    msg = _timeout_message(600)
    assert "still reporting progress" not in msg
    assert "worker stopped responding" not in msg


def test_elapsed_seconds_uses_real_start_time():
    from shared.infrastructure.taskiq import tasks as tasks_module

    assert tasks_module._elapsed_seconds(datetime.now(UTC) - timedelta(seconds=123)) == 123
    assert tasks_module._elapsed_seconds(None) == 0
