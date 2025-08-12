import json
from unittest.mock import AsyncMock, patch

import pytest

from foreman_mcp_server.utils.dsl_docs_utils import (
    _format_class_documentation,
    _format_method_documentation,
    _process_keyword_param,
    _process_optional_param,
    get_dsldocs_path,
    method_returns,
    method_signature,
    parse_dsl_docs,
    read_dsl_docs_from_markdown,
    resolve_default,
    save_dsl_docs_as_markdown,
)


class TestResolveDefault:
    def test_resolve_default_none(self):
        """Test resolve_default with None value."""
        param = {"default": None}
        result = resolve_default(param)
        assert result == "nil"

    def test_resolve_default_missing_key(self):
        """Test resolve_default with missing default key."""
        param = {}
        result = resolve_default(param)
        assert result == "nil"

    def test_resolve_default_empty_dict(self):
        """Test resolve_default with empty dictionary."""
        param = {"default": {}}
        result = resolve_default(param)
        assert result == "{}"

    def test_resolve_default_non_empty_dict(self):
        """Test resolve_default with non-empty dictionary."""
        param = {"default": {"key": "value"}}
        result = resolve_default(param)
        assert result == "{}"

    def test_resolve_default_empty_string(self):
        """Test resolve_default with empty string."""
        param = {"default": ""}
        result = resolve_default(param)
        assert result == '""'

    def test_resolve_default_non_empty_string(self):
        """Test resolve_default with non-empty string."""
        param = {"default": "test_value"}
        result = resolve_default(param)
        assert result == '"test_value"'

    def test_resolve_default_number(self):
        """Test resolve_default with number."""
        param = {"default": 42}
        result = resolve_default(param)
        assert result == "42"

    def test_resolve_default_boolean_true(self):
        """Test resolve_default with boolean True."""
        param = {"default": True}
        result = resolve_default(param)
        assert result == "True"

    def test_resolve_default_boolean_false(self):
        """Test resolve_default with boolean False."""
        param = {"default": False}
        result = resolve_default(param)
        assert result == "False"


class TestMethodReturns:
    def test_method_returns_simple_class(self):
        """Test method_returns with simple class return."""
        method = {
            "returns": {
                "object": {
                    "class": "String",
                    "data": None
                }
            }
        }
        result = method_returns(method)
        assert result == ": String"

    def test_method_returns_with_data(self):
        """Test method_returns with data."""
        method = {
            "returns": {
                "object": {
                    "class": "Hash",
                    "data": {"key": "value"}
                }
            }
        }
        result = method_returns(method)
        assert result == ': {"key": "value"}'

    def test_method_returns_with_meta(self):
        """Test method_returns with meta information."""
        method = {
            "returns": {
                "object": {
                    "class": "Array",
                    "meta": "collection_of_hosts",
                    "data": ["host1", "host2"]
                }
            }
        }
        result = method_returns(method)
        assert result == 'Collection of hosts: ["host1", "host2"]'

    def test_method_returns_hash_with_list_data(self):
        """Test method_returns with Hash class and list data."""
        method = {
            "returns": {
                "object": {
                    "class": "Hash",
                    "data": [{"key": "value"}]
                }
            }
        }
        result = method_returns(method)
        assert result == "Object"

    def test_method_returns_no_returns_key(self):
        """Test method_returns with missing returns key."""
        method = {}
        result = method_returns(method)
        assert result == ": None"

    def test_method_returns_null_replacement(self):
        """Test method_returns replaces null with nil."""
        method = {
            "returns": {
                "object": {
                    "class": "Mixed",
                    "data": None
                }
            }
        }
        result = method_returns(method)
        assert result == ": Mixed"


class TestProcessOptionalParam:
    def test_process_optional_param_list(self):
        """Test _process_optional_param with list type."""
        param = {"name": "items", "expected_type": "list"}
        result = _process_optional_param(param)
        assert result == "*items"

    def test_process_optional_param_non_list(self):
        """Test _process_optional_param with non-list type."""
        param = {"name": "count", "default": 10}
        result = _process_optional_param(param)
        assert result == "count = 10"

    def test_process_optional_param_missing_name(self):
        """Test _process_optional_param with missing name."""
        param = {"default": "test"}
        result = _process_optional_param(param)
        assert result == ' = "test"'


class TestProcessKeywordParam:
    def test_process_keyword_param_basic(self):
        """Test _process_keyword_param with basic parameter."""
        param = {"name": "debug", "default": True}
        result = _process_keyword_param(param)
        assert result == "debug: True"

    def test_process_keyword_param_string_default(self):
        """Test _process_keyword_param with string default."""
        param = {"name": "format", "default": "json"}
        result = _process_keyword_param(param)
        assert result == 'format: "json"'

    def test_process_keyword_param_none_default(self):
        """Test _process_keyword_param with None default."""
        param = {"name": "callback", "default": None}
        result = _process_keyword_param(param)
        assert result == "callback: nil"


class TestMethodSignature:
    def test_method_signature_no_params(self):
        """Test method_signature with no parameters."""
        method = {"name": "simple_method"}
        result = method_signature(method)
        assert result == "simple_method"

    def test_method_signature_required_params(self):
        """Test method_signature with required parameters."""
        method = {
            "name": "create_user",
            "params": [
                {"type": "required", "name": "username"},
                {"type": "required", "name": "email"}
            ]
        }
        result = method_signature(method)
        assert result == "create_user(username, email)"

    def test_method_signature_mixed_params(self):
        """Test method_signature with mixed parameter types."""
        method = {
            "name": "find_hosts",
            "params": [
                {"type": "required", "name": "search"},
                {"type": "optional", "name": "limit", "default": 20},
                {"type": "keyword", "name": "include_facts", "default": False}
            ]
        }
        result = method_signature(method)
        assert result == "find_hosts(search, limit = 20, include_facts: False)"

    def test_method_signature_with_block(self):
        """Test method_signature with block parameter."""
        method = {
            "name": "each_host",
            "params": [
                {"type": "required", "name": "collection"},
                {"type": "block", "schema": "{ |host| ... }"}
            ]
        }
        result = method_signature(method)
        assert result == "each_host(collection) { |host| ... }"

    def test_method_signature_optional_list(self):
        """Test method_signature with optional list parameter."""
        method = {
            "name": "select_items",
            "params": [
                {"type": "optional", "name": "items", "expected_type": "list"}
            ]
        }
        result = method_signature(method)
        assert result == "select_items(*items)"


class TestFormatMethodDocumentation:
    def test_format_method_documentation_basic(self):
        """Test _format_method_documentation with basic method."""
        method = {
            "name": "test_method",
            "short_description": "A test method",
            "returns": {"object": {"class": "String"}}
        }
        result = _format_method_documentation(method)

        assert "- `test_method` - A test method" in result
        assert "  - Returns: : String" in result
        assert "  - Usage: test_method" in result

    def test_format_method_documentation_property(self):
        """Test _format_method_documentation with property."""
        method = {
            "name": "hostname",
            "short_description": "Host's hostname",
            "returns": {"object": {"class": "String"}}
        }
        result = _format_method_documentation(method, is_property=True)

        assert "- `hostname` - Host's hostname" in result
        assert "  - Usage: obj.hostname" in result

    def test_format_method_documentation_with_examples(self):
        """Test _format_method_documentation with examples."""
        method = {
            "name": "format_name",
            "short_description": "Format host name",
            "returns": {"object": {"class": "String"}},
            "examples": [
                {
                    "desc": "Basic formatting",
                    "example": "format_name(@host)"
                },
                {
                    "desc": "With prefix",
                    "example": "format_name(@host, 'prod-')"
                }
            ]
        }
        result = _format_method_documentation(method)

        assert "  - Examples:" in result
        assert "    - Basic formatting" in result
        assert "    - With prefix" in result
        assert "      ```erb" in result
        assert "      format_name(@host)" in result


class TestFormatClassDocumentation:
    def test_format_class_documentation_with_methods(self):
        """Test _format_class_documentation with methods."""
        class_desc = {
            "methods": [
                {
                    "name": "create",
                    "short_description": "Create new item",
                    "returns": {"object": {"class": "Object"}}
                }
            ]
        }
        result = _format_class_documentation("TestClass", class_desc)

        assert "### TestClass" in result
        assert "**Methods:**" in result
        assert "- `create` - Create new item" in result

    def test_format_class_documentation_with_properties(self):
        """Test _format_class_documentation with properties."""
        class_desc = {
            "properties": [
                {
                    "name": "id",
                    "short_description": "Object ID",
                    "returns": {"object": {"class": "Integer"}}
                }
            ]
        }
        result = _format_class_documentation("TestClass", class_desc)

        assert "### TestClass" in result
        assert "**Properties:**" in result
        assert "- `id` - Object ID" in result
        assert "  - Usage: obj.id" in result


class TestParseDslDocs:
    def test_parse_dsl_docs_empty_content(self):
        """Test parse_dsl_docs with empty content."""
        result = parse_dsl_docs("")
        assert result == "# Foreman DSL Documentation\n\nNo documentation available."

    def test_parse_dsl_docs_valid_json(self):
        """Test parse_dsl_docs with valid JSON."""
        docs_data = {
            "docs": {
                "classes": {
                    "Host": {
                        "methods": [
                            {
                                "name": "hostname",
                                "short_description": "Returns hostname",
                                "returns": {"object": {"class": "String"}}
                            }
                        ]
                    }
                }
            }
        }
        json_content = json.dumps(docs_data)
        result = parse_dsl_docs(json_content)

        assert "# Foreman DSL Documentation" in result
        assert "## ERB Templates" in result
        assert "<% code %>" in result
        assert "### Host" in result
        assert "**Methods:**" in result
        assert "- `hostname` - Returns hostname" in result

    def test_parse_dsl_docs_invalid_json(self):
        """Test parse_dsl_docs with invalid JSON."""
        result = parse_dsl_docs("invalid json content")

        assert "# Foreman DSL Documentation" in result
        assert "Error parsing documentation:" in result

    def test_parse_dsl_docs_erb_templates(self):
        """Test parse_dsl_docs includes ERB templates."""
        result = parse_dsl_docs("{}")

        assert "<% code %>" in result
        assert "Executes code, but does not insert a value" in result
        assert "<%= expression %>" in result
        assert "Inserts the value of an expression" in result
        assert "<%# comment -%>" in result
        assert "Comment, removed from the final output" in result


class TestGetDsldocsPath:
    @patch("foreman_mcp_server.utils.dsl_docs_utils.Path")
    def test_get_dsldocs_path_existing_dir(self, mock_path):
        """Test get_dsldocs_path with existing directory."""
        mock_cache_dir = mock_path.return_value
        mock_dsldoc_dir = mock_cache_dir.__truediv__.return_value
        mock_dsldoc_dir.exists.return_value = True

        get_dsldocs_path("/cache", "test.md")

        mock_path.assert_called_once_with("/cache")
        mock_cache_dir.__truediv__.assert_called_with("dsldoc")
        mock_dsldoc_dir.exists.assert_called_once()
        mock_dsldoc_dir.mkdir.assert_not_called()

    @patch("foreman_mcp_server.utils.dsl_docs_utils.Path")
    def test_get_dsldocs_path_create_dir(self, mock_path):
        """Test get_dsldocs_path creates directory when it doesn't exist."""
        mock_cache_dir = mock_path.return_value
        mock_dsldoc_dir = mock_cache_dir.__truediv__.return_value
        mock_dsldoc_dir.exists.return_value = False

        get_dsldocs_path("/cache", "test.md")

        mock_dsldoc_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)


class TestSaveDslDocsAsMarkdown:
    def test_save_dsl_docs_as_markdown_success(self):
        """Test save_dsl_docs_as_markdown successful save."""
        with patch("foreman_mcp_server.utils.dsl_docs_utils.get_dsldocs_path") as mock_get_path, \
             patch("foreman_mcp_server.utils.dsl_docs_utils.aiofiles.open") as mock_aiofiles_open:

            mock_get_path.return_value = "/cache/dsldoc/test.md"
            mock_file = AsyncMock()
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value = mock_file
            mock_aiofiles_open.return_value = mock_context_manager

            docs = {"docs": {"classes": {}}}

            import asyncio
            asyncio.run(save_dsl_docs_as_markdown("/cache", "test.md", docs))

            mock_aiofiles_open.assert_called_once_with("/cache/dsldoc/test.md", "w")
            mock_file.write.assert_called_once()

            # Verify the written content includes header
            written_content = mock_file.write.call_args[0][0]
            assert "# Foreman DSL Documentation" in written_content

    def test_save_dsl_docs_as_markdown_error(self):
        """Test save_dsl_docs_as_markdown handles errors."""
        with patch("foreman_mcp_server.utils.dsl_docs_utils.get_dsldocs_path") as mock_get_path, \
             patch("foreman_mcp_server.utils.dsl_docs_utils.aiofiles.open") as mock_aiofiles_open:

            mock_get_path.return_value = "/cache/dsldoc/test.md"
            mock_aiofiles_open.side_effect = Exception("Write error")

            docs = {"docs": {"classes": {}}}

            import asyncio
            with pytest.raises(RuntimeError) as exc_info:
                asyncio.run(save_dsl_docs_as_markdown("/cache", "test.md", docs))

            assert "Failed to save DSL documentation: Write error" in str(exc_info.value)


class TestReadDslDocsFromMarkdown:
    def test_read_dsl_docs_from_markdown_success(self):
        """Test read_dsl_docs_from_markdown successful read."""
        with patch("foreman_mcp_server.utils.dsl_docs_utils.get_dsldocs_path") as mock_get_path, \
             patch("foreman_mcp_server.utils.dsl_docs_utils.aiofiles.open") as mock_aiofiles_open:

            mock_get_path.return_value = "/cache/dsldoc/test.md"
            mock_file = AsyncMock()
            mock_file.read.return_value = "# Test Documentation\nContent here"
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value = mock_file
            mock_aiofiles_open.return_value = mock_context_manager

            import asyncio
            result = asyncio.run(read_dsl_docs_from_markdown("/cache", "test.md"))

            assert result == "# Test Documentation\nContent here"
            mock_aiofiles_open.assert_called_once_with("/cache/dsldoc/test.md")

    def test_read_dsl_docs_from_markdown_file_not_found(self):
        """Test read_dsl_docs_from_markdown handles file not found."""
        with patch("foreman_mcp_server.utils.dsl_docs_utils.get_dsldocs_path") as mock_get_path, \
             patch("foreman_mcp_server.utils.dsl_docs_utils.aiofiles.open") as mock_aiofiles_open:

            mock_get_path.return_value = "/cache/dsldoc/test.md"
            mock_aiofiles_open.side_effect = FileNotFoundError()

            import asyncio
            with pytest.raises(FileNotFoundError) as exc_info:
                asyncio.run(read_dsl_docs_from_markdown("/cache", "test.md"))

            assert "DSL documentation file '/cache/dsldoc/test.md' not found" in str(exc_info.value)

    def test_read_dsl_docs_from_markdown_error(self):
        """Test read_dsl_docs_from_markdown handles other errors."""
        with patch("foreman_mcp_server.utils.dsl_docs_utils.get_dsldocs_path") as mock_get_path, \
             patch("foreman_mcp_server.utils.dsl_docs_utils.aiofiles.open") as mock_aiofiles_open:

            mock_get_path.return_value = "/cache/dsldoc/test.md"
            mock_aiofiles_open.side_effect = Exception("Read error")

            import asyncio
            with pytest.raises(RuntimeError) as exc_info:
                asyncio.run(read_dsl_docs_from_markdown("/cache", "test.md"))

            assert "Failed to read DSL documentation: Read error" in str(exc_info.value)

