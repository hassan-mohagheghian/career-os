"""Tests for the Agent Tools layer.

TDD: These tests define the tool contract.
DDD: Tools are domain services wrapping existing business logic.
SRP: Each tool has one responsibility.
DIP: Tools depend on abstractions (LLMProvider), not concretions.
"""

import pytest
from unittest.mock import MagicMock, patch, mock_open

from app.ai.tools.base import BaseTool, ToolResult
from app.ai.tools.job_tools import FetchJobTool, ExtractJobDataTool
from app.ai.tools.company_tools import FetchCompanyTool
from app.ai.tools.skill_tools import FindSkillTool
from app.ai.tools.database import DatabaseTool


# ── Value Object Tests ──────────────────────────────────────────────

class TestToolResult:
    """ToolResult is a value object — standardized tool output."""

    def test_success_result(self):
        result = ToolResult(success=True, data={"key": "value"})
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.error is None

    def test_failure_result(self):
        result = ToolResult(success=False, error="something went wrong")
        assert result.success is False
        assert result.error == "something went wrong"

    def test_minimal_result(self):
        result = ToolResult(success=True)
        assert result.data is None
        assert result.error is None


# ── Interface Contract Tests ────────────────────────────────────────

class TestBaseToolContract:
    """Test the BaseTool abstract interface.

    SRP: Each test verifies one aspect of the tool contract.
    DIP: Tests depend on the abstraction, not concrete tools.
    """

    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            BaseTool()

    def test_concrete_tool_must_implement_run(self):
        class IncompleteTool(BaseTool):
            name = "incomplete"
            description = "test"

        with pytest.raises(TypeError):
            IncompleteTool()

    def test_concrete_tool_satisfies_interface(self):
        class ValidTool(BaseTool):
            name = "valid"
            description = "A valid tool"

            def run(self, **kwargs):
                return ToolResult(success=True, data="ok")

        tool = ValidTool()
        assert isinstance(tool, BaseTool)
        assert tool.name == "valid"
        assert tool.description == "A valid tool"

        result = tool.run()
        assert result.success is True

    def test_tool_has_schema(self):
        class SchemaTool(BaseTool):
            name = "schema_tool"
            description = "Tool with schema"

            @property
            def input_schema(self):
                return {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    },
                    "required": ["query"],
                }

            def run(self, **kwargs):
                return ToolResult(success=True)

        tool = SchemaTool()
        schema = tool.input_schema
        assert schema["type"] == "object"
        assert "query" in schema["properties"]


# ── Job Tools Tests ─────────────────────────────────────────────────

class TestFetchJobTool:
    """FetchJobTool wraps the existing URL fetching logic."""

    def test_tool_name_and_description(self):
        tool = FetchJobTool()
        assert tool.name == "fetch_job_url"
        assert "fetch" in tool.description.lower()

    @patch("services.worker._fetch_url")
    def test_run_fetches_url(self, mock_fetch):
        mock_fetch.return_value = "Job description content here"
        tool = FetchJobTool()
        result = tool.run(url="https://example.com/job/123")
        assert result.success is True
        assert "Job description" in result.data
        mock_fetch.assert_called_once_with("https://example.com/job/123")

    def test_run_requires_url(self):
        tool = FetchJobTool()
        result = tool.run()
        assert result.success is False
        assert "url" in result.error.lower()


class TestExtractJobDataTool:
    """ExtractJobDataTool wraps the existing extraction logic."""

    def test_tool_name(self):
        tool = ExtractJobDataTool()
        assert tool.name == "extract_job_data"

    def test_run_requires_content(self):
        tool = ExtractJobDataTool()
        result = tool.run()
        assert result.success is False


# ── Company Tools Tests ─────────────────────────────────────────────

class TestFetchCompanyTool:
    def test_tool_name(self):
        tool = FetchCompanyTool()
        assert tool.name == "fetch_company_url"


# ── Skill Tools Tests ───────────────────────────────────────────────

class TestFindSkillTool:
    def test_tool_name(self):
        tool = FindSkillTool()
        assert tool.name == "find_skill"


# ── Database Tool Tests ─────────────────────────────────────────────

class TestDatabaseTool:
    def test_tool_name(self):
        tool = DatabaseTool(db_path=":memory:")
        assert tool.name == "database"

    def test_run_requires_query(self):
        tool = DatabaseTool(db_path=":memory:")
        result = tool.run()
        assert result.success is False
