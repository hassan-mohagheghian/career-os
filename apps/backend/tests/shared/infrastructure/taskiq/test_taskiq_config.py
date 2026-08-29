"""Tests for TaskIQ taskiq config env-driven settings."""

from __future__ import annotations

import importlib

from shared.infrastructure.taskiq import config as taskiq_config


def test_reconcile_interval_defaults_to_30(monkeypatch):
    monkeypatch.delenv("RECONCILE_INTERVAL_SECONDS", raising=False)
    importlib.reload(taskiq_config)
    assert taskiq_config.RECONCILE_INTERVAL_SECONDS == 30


def test_reconcile_interval_honors_env(monkeypatch):
    monkeypatch.setenv("RECONCILE_INTERVAL_SECONDS", "45")
    importlib.reload(taskiq_config)
    assert taskiq_config.RECONCILE_INTERVAL_SECONDS == 45
