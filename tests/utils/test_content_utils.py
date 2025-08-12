import json

from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from foreman_mcp_server.utils.content_utils import (
    build_tool_result,
    derive_legacy_content,
    to_markdown_like,
)


class TestToMarkdownLike:
    def test_to_markdown_like_string_value(self):
        """Test to_markdown_like with string value."""
        result = to_markdown_like("title", "simple string")
        expected = "# Title\nsimple string\n"
        assert result == expected

    def test_to_markdown_like_dict_value(self):
        """Test to_markdown_like with dictionary value."""
        test_dict = {"key1": "value1", "key2": "value2"}
        result = to_markdown_like("config", test_dict)

        expected_json = json.dumps(test_dict, indent=2)
        expected = f"# Config\n```json\n{expected_json}\n```\n"
        assert result == expected

    def test_to_markdown_like_list_value(self):
        """Test to_markdown_like with list value."""
        test_list = ["item1", "item2", "item3"]
        result = to_markdown_like("items", test_list)

        expected_json = json.dumps(test_list, indent=2)
        expected = f"# Items\n```json\n{expected_json}\n```\n"
        assert result == expected

    def test_to_markdown_like_nested_dict(self):
        """Test to_markdown_like with nested dictionary."""
        test_dict = {
            "level1": {
                "level2": ["item1", "item2"],
                "other": "value"
            }
        }
        result = to_markdown_like("nested", test_dict)

        expected_json = json.dumps(test_dict, indent=2)
        expected = f"# Nested\n```json\n{expected_json}\n```\n"
        assert result == expected

    def test_to_markdown_like_number_value(self):
        """Test to_markdown_like with number value."""
        result = to_markdown_like("count", 42)
        expected = "# Count\n42\n"
        assert result == expected

    def test_to_markdown_like_boolean_value(self):
        """Test to_markdown_like with boolean value."""
        result = to_markdown_like("enabled", True)
        expected = "# Enabled\nTrue\n"
        assert result == expected

    def test_to_markdown_like_none_value(self):
        """Test to_markdown_like with None value."""
        result = to_markdown_like("empty", None)
        expected = "# Empty\nNone\n"
        assert result == expected

    def test_to_markdown_like_key_capitalization(self):
        """Test to_markdown_like capitalizes key properly."""
        result = to_markdown_like("multi_word_key", "value")
        expected = "# Multi_word_key\nvalue\n"
        assert result == expected


class TestDeriveLegacyContent:
    def test_derive_legacy_content_single_item(self):
        """Test derive_legacy_content with single key-value pair."""
        structured_content = {"message": "Success"}
        result = derive_legacy_content(structured_content)
        expected = "# Message\nSuccess\n"
        assert result == expected

    def test_derive_legacy_content_multiple_items(self):
        """Test derive_legacy_content with multiple key-value pairs."""
        structured_content = {
            "message": "Success",
            "data": {"id": 1, "name": "test"},
            "status": "completed"
        }
        result = derive_legacy_content(structured_content)

        expected_parts = [
            "# Message\nSuccess\n",
            f"# Data\n```json\n{json.dumps({'id': 1, 'name': 'test'}, indent=2)}\n```\n",
            "# Status\ncompleted\n"
        ]
        expected = "\n".join(expected_parts)
        assert result == expected

    def test_derive_legacy_content_empty_dict(self):
        """Test derive_legacy_content with empty dictionary."""
        structured_content = {}
        result = derive_legacy_content(structured_content)
        assert result == ""

    def test_derive_legacy_content_complex_data(self):
        """Test derive_legacy_content with complex nested data."""
        structured_content = {
            "response": {
                "users": [
                    {"id": 1, "name": "Alice"},
                    {"id": 2, "name": "Bob"}
                ],
                "total": 2
            },
            "error": None
        }
        result = derive_legacy_content(structured_content)

        expected_response_json = json.dumps({
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ],
            "total": 2
        }, indent=2)

        expected_parts = [
            f"# Response\n```json\n{expected_response_json}\n```\n",
            "# Error\nNone\n"
        ]
        expected = "\n".join(expected_parts)
        assert result == expected


class TestBuildToolResult:
    def test_build_tool_result_simple(self):
        """Test build_tool_result with simple structured content."""
        structured_content = {"message": "Test message", "status": "success"}
        result = build_tool_result(structured_content)

        assert isinstance(result, ToolResult)
        assert len(result.content) == 1
        assert isinstance(result.content[0], TextContent)
        assert result.content[0].type == "text"

        expected_text = "# Message\nTest message\n\n# Status\nsuccess\n"
        assert result.content[0].text == expected_text
        assert result.structured_content == structured_content

    def test_build_tool_result_with_dict_data(self):
        """Test build_tool_result with dictionary data."""
        structured_content = {
            "result": {"id": 123, "name": "test_item"},
            "metadata": {"created": "2024-01-01"}
        }
        result = build_tool_result(structured_content)

        assert isinstance(result, ToolResult)
        assert result.structured_content == structured_content

        # Check that the text content contains JSON formatting
        text_content = result.content[0].text
        assert "```json" in text_content
        assert '"id": 123' in text_content
        assert '"name": "test_item"' in text_content

    def test_build_tool_result_empty_content(self):
        """Test build_tool_result with empty structured content."""
        structured_content = {}
        result = build_tool_result(structured_content)

        assert isinstance(result, ToolResult)
        assert len(result.content) == 1
        assert result.content[0].text == ""
        assert result.structured_content == {}

    def test_build_tool_result_complex_content(self):
        """Test build_tool_result with complex structured content."""
        structured_content = {
            "action": "create_user",
            "request": {
                "method": "POST",
                "endpoint": "/api/users",
                "payload": {"name": "John Doe", "email": "john@example.com"}
            },
            "response": {
                "status": 201,
                "data": {"id": 456, "name": "John Doe", "email": "john@example.com"}
            },
            "timestamp": "2024-01-01T12:00:00Z"
        }
        result = build_tool_result(structured_content)

        assert isinstance(result, ToolResult)
        assert result.structured_content == structured_content

        text_content = result.content[0].text
        # Verify all sections are present
        assert "# Action" in text_content
        assert "# Request" in text_content
        assert "# Response" in text_content
        assert "# Timestamp" in text_content

        # Verify JSON formatting for complex objects
        assert "```json" in text_content
        assert "create_user" in text_content
        assert "2024-01-01T12:00:00Z" in text_content
