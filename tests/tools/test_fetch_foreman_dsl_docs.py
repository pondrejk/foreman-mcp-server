from unittest.mock import AsyncMock, Mock, patch

from foreman_mcp_server.tools.fetch_foreman_dsl_docs import (
    register_fetch_foreman_dsl_docs,
)


class TestFetchForemanDslDocs:
    @patch('foreman_mcp_server.tools.fetch_foreman_dsl_docs.assert_resource')
    @patch('foreman_mcp_server.tools.fetch_foreman_dsl_docs.save_dsl_docs_as_markdown')
    @patch('foreman_mcp_server.tools.fetch_foreman_dsl_docs.build_tool_result')
    @patch('foreman_mcp_server.tools.fetch_foreman_dsl_docs.mcp_info_headers')
    def test_fetch_foreman_dsl_docs_success(
        self, mock_mcp_info_headers, mock_build_tool_result, mock_save_dsl_docs,
        mock_assert_resource
    ):
        mock_foreman_api = Mock()
        mock_foreman_api.apidoc_cache_dir = "/test/cache/dir"
        mock_foreman_api.http_call = Mock(return_value={"test": "response"})
        mock_get_context = Mock()
        mock_mcp = Mock()

        mock_assert_resource.return_value = AsyncMock()
        mock_save_dsl_docs.return_value = AsyncMock()
        mock_build_tool_result.return_value = Mock()
        mock_mcp_info_headers.return_value = {"User-Agent": "test"}

        register_fetch_foreman_dsl_docs(mock_mcp, mock_foreman_api, mock_get_context)

        # Verify the tool was registered with correct parameters
        mock_mcp.tool.assert_called_once()
        call_args = mock_mcp.tool.call_args
        assert "Fetches the DSL documentation from Foreman" in call_args[1]['description']

    @patch('foreman_mcp_server.tools.fetch_foreman_dsl_docs.assert_resource')
    @patch('foreman_mcp_server.tools.fetch_foreman_dsl_docs.build_tool_result')
    def test_fetch_foreman_dsl_docs_http_error(
        self, mock_build_tool_result, mock_assert_resource
    ):
        mock_foreman_api = Mock()
        mock_foreman_api.http_call = Mock(side_effect=Exception("HTTP Error"))
        mock_get_context = Mock()
        mock_mcp = Mock()

        mock_assert_resource.return_value = AsyncMock()
        mock_build_tool_result.return_value = Mock()

        register_fetch_foreman_dsl_docs(mock_mcp, mock_foreman_api, mock_get_context)

        # Verify tool registration
        mock_mcp.tool.assert_called_once()

    @patch('foreman_mcp_server.tools.fetch_foreman_dsl_docs.get_foreman_api')
    def test_fetch_foreman_dsl_docs_without_foreman_api(self, mock_get_foreman_api):
        mock_api = Mock()
        mock_api.apidoc_cache_dir = "/fallback/cache/dir"
        mock_api.http_call = Mock(return_value={"fallback": "response"})
        mock_get_foreman_api.return_value = mock_api
        mock_get_context = Mock()
        mock_mcp = Mock()

        register_fetch_foreman_dsl_docs(mock_mcp, None, mock_get_context)

        # Verify tool registration
        mock_mcp.tool.assert_called_once()
