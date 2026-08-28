"""Unit tests for the processing-timeout error message helper."""

from __future__ import annotations

from datetime import datetime, UTC, timedelta

from shared.infrastructure.taskiq.tasks import _build_timeout_message


def test_message_when_heartbeat_recent_indicates_slow_or_stuck():
    heartbeat = datetime.now(UTC) - timedelta(seconds=20)
    msg = _build_timeout_message(heartbeat, 600)
    assert "exceeded 600s" in msg
    assert "still reporting progress" in msg
    assert "worker stopped responding" not in msg


def test_message_when_heartbeat_stale_indicates_crash():
    heartbeat = datetime.now(UTC) - timedelta(seconds=600)
    msg = _build_timeout_message(heartbeat, 600)
    assert "worker stopped responding" in msg
    assert "still reporting progress" not in msg


def test_message_when_heartbeat_is_none_indicates_crash():
    msg = _build_timeout_message(None, 600)
    assert "worker stopped responding" in msg


def test_message_accepts_iso_string_heartbeat():
    heartbeat = (datetime.now(UTC) - timedelta(seconds=15)).isoformat()
    msg = _build_timeout_message(heartbeat, 300)
    assert "still reporting progress" in msg


def test_message_handles_malformed_heartbeat_as_crash():
    msg = _build_timeout_message("not-a-date", 600)
    assert "worker stopped responding" in msg
