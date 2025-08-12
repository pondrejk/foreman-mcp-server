from unittest.mock import AsyncMock, Mock, patch

from foreman_mcp_server.tools.get_foreman_dsl_docs import register_get_foreman_dsl_docs


class TestGetForemanDslDocs:
    @patch('foreman_mcp_server.tools.get_foreman_dsl_docs.assert_resource')
    @patch('foreman_mcp_server.tools.get_foreman_dsl_docs.read_dsl_docs_from_markdown')
    @patch('foreman_mcp_server.tools.get_foreman_dsl_docs.build_tool_result')
    def test_get_foreman_dsl_docs_success(
        self, mock_build_tool_result, mock_read_dsl_docs, mock_assert_resource
    ):
        mock_foreman_api = Mock()
        mock_foreman_api.apidoc_cache_dir = "/test/cache/dir"
        mock_get_context = Mock()
        mock_mcp = Mock()

        mock_assert_resource.return_value = AsyncMock()
        mock_read_dsl_docs.return_value = AsyncMock(return_value="Test documentation content")
        mock_build_tool_result.return_value = Mock()

        register_get_foreman_dsl_docs(mock_mcp, mock_foreman_api, mock_get_context)

        # Verify the tool was registered with correct parameters
        mock_mcp.tool.assert_called_once()
        call_args = mock_mcp.tool.call_args
        assert "Reads from cache and returns the documentation of available macros" in call_args[1]['description']

    @patch('foreman_mcp_server.tools.get_foreman_dsl_docs.assert_resource')
    @patch('foreman_mcp_server.tools.get_foreman_dsl_docs.read_dsl_docs_from_markdown')
    @patch('foreman_mcp_server.tools.get_foreman_dsl_docs.build_tool_result')
    def test_get_foreman_dsl_docs_file_not_found(
        self, mock_build_tool_result, mock_read_dsl_docs, mock_assert_resource
    ):
        mock_foreman_api = Mock()
        mock_foreman_api.apidoc_cache_dir = "/test/cache/dir"
        mock_get_context = Mock()
        mock_mcp = Mock()

        mock_assert_resource.return_value = AsyncMock()
        mock_read_dsl_docs.side_effect = FileNotFoundError()
        mock_build_tool_result.return_value = Mock()

        register_get_foreman_dsl_docs(mock_mcp, mock_foreman_api, mock_get_context)

        # Verify tool registration
        mock_mcp.tool.assert_called_once()

    @patch('foreman_mcp_server.tools.get_foreman_dsl_docs.get_foreman_api')
    def test_get_foreman_dsl_docs_without_foreman_api(self, mock_get_foreman_api):
        mock_api = Mock()
        mock_api.apidoc_cache_dir = "/fallback/cache/dir"
        mock_get_foreman_api.return_value = mock_api
        mock_get_context = Mock()
        mock_mcp = Mock()

        register_get_foreman_dsl_docs(mock_mcp, None, mock_get_context)

        # Verify tool registration
        mock_mcp.tool.assert_called_once()
