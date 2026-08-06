"""Tests for the context budget module (size caps for LLM prompt inputs)."""

from __future__ import annotations

import pytest

from processing.application.services.context_budget import (
    MAX_COMBINED_CHARS,
    MAX_SOURCE_CHARS,
    trim_text,
)


class TestTrimText:
    def test_returns_small_text_unchanged(self):
        assert trim_text("hello world", max_chars=100) == "hello world"

    def test_trims_head_and_appends_marker(self):
        text = "a" * 50
        result = trim_text(text, max_chars=30)
        assert len(result) == 30
        assert result.endswith("[truncated]")
        assert result.startswith("a" * (30 - len("\n\n[truncated]")))

    def test_keep_tail_when_keep_head_false(self):
        text = "a" * 50
        result = trim_text(text, max_chars=30, keep_head=False)
        assert len(result) == 30
        assert result.startswith("\n\n[truncated]")
        assert result.endswith("a")

    def test_does_not_trim_text_at_exact_limit(self):
        text = "a" * 30
        assert trim_text(text, max_chars=30) == text

    def test_strips_surrounding_whitespace_before_trim(self):
        text = "  " + "a" * 10 + "  "
        assert trim_text(text, max_chars=100) == "a" * 10


class TestBudgetConstants:
    def test_source_cap_is_smaller_than_combined_cap(self):
        assert MAX_SOURCE_CHARS < MAX_COMBINED_CHARS
