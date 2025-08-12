from unittest.mock import AsyncMock, Mock, patch

from foreman_mcp_server.tools.get_foreman_api_resource_docs import (
    register_get_foreman_api_resource_docs,
)


class TestGetForemanApiResourceDocs:
    @patch('foreman_mcp_server.tools.get_foreman_api_resource_docs.assert_resource')
    @patch('foreman_mcp_server.tools.get_foreman_api_resource_docs.build_tool_result')
    def test_get_foreman_api_resource_docs_success(
        self, mock_build_tool_result, mock_assert_resource
    ):
        mock_foreman_api = Mock()
        mock_foreman_api.apidoc = {
            "docs": {
                "resources": {
                    "test_resource": {
                        "name": "test_resource",
                        "description": "Test resource documentation",
                        "methods": ["GET", "POST"]
                    }
                }
            }
        }
        mock_get_context = Mock()
        mock_mcp = Mock()

        mock_assert_resource.return_value = AsyncMock()
        mock_build_tool_result.return_value = Mock()

        register_get_foreman_api_resource_docs(mock_mcp, mock_foreman_api, mock_get_context)

        # Verify the tool was registered with correct parameters
        mock_mcp.tool.assert_called_once()
        call_args = mock_mcp.tool.call_args
        assert "Fetches the documentation for a specific Foreman API resource" in call_args[1]['description']

    @patch('foreman_mcp_server.tools.get_foreman_api_resource_docs.assert_resource')
    @patch('foreman_mcp_server.tools.get_foreman_api_resource_docs.build_tool_result')
    def test_get_foreman_api_resource_docs_missing_resource(
        self, mock_build_tool_result, mock_assert_resource
    ):
        mock_foreman_api = Mock()
        mock_foreman_api.apidoc = {"docs": {"resources": {}}}
        mock_get_context = Mock()
        mock_mcp = Mock()

        mock_assert_resource.return_value = AsyncMock()
        mock_build_tool_result.return_value = Mock()

        register_get_foreman_api_resource_docs(mock_mcp, mock_foreman_api, mock_get_context)

        # Verify tool registration
        mock_mcp.tool.assert_called_once()

    @patch('foreman_mcp_server.tools.get_foreman_api_resource_docs.get_foreman_api')
    def test_get_foreman_api_resource_docs_without_foreman_api(self, mock_get_foreman_api):
        mock_api = Mock()
        mock_api.apidoc = {
            "docs": {
                "resources": {
                    "fallback_resource": {
                        "name": "fallback_resource",
                        "description": "Fallback resource documentation"
                    }
                }
            }
        }
        mock_get_foreman_api.return_value = mock_api
        mock_get_context = Mock()
        mock_mcp = Mock()

        register_get_foreman_api_resource_docs(mock_mcp, None, mock_get_context)

        # Verify tool registration
        mock_mcp.tool.assert_called_once()
