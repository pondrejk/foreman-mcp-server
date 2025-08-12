from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastmcp.exceptions import ToolError

from foreman_mcp_server.utils.utils import (
    assert_http_method,
    assert_resource,
    get_foreman_api,
    mcp_info_headers,
)


class TestAssertResource:
    def test_assert_resource_found(self):
        """Test assert_resource when resource is found in the list."""
        mock_context = Mock()
        mock_context.read_resource = AsyncMock(
            return_value=[Mock(content="resource1, resource2, resource3")]
        )
        get_context = Mock(return_value=mock_context)

        resource_info = {
            "type": "test_type",
            "list_name": "test_list",
            "name": "Test Resource",
        }

        import asyncio
        result = asyncio.run(assert_resource("resource2", resource_info, get_context))

        assert result is True
        mock_context.read_resource.assert_called_once_with(
            "foreman://documentation/test_type/test_list"
        )

    def test_assert_resource_not_found(self):
        """Test assert_resource when resource is not found in the list."""
        mock_context = Mock()
        mock_context.read_resource = AsyncMock(
            return_value=[Mock(content="resource1, resource2, resource3")]
        )
        get_context = Mock(return_value=mock_context)

        resource_info = {
            "type": "test_type",
            "list_name": "test_list",
            "name": "Test Resource",
        }

        import asyncio
        with pytest.raises(ToolError) as exc_info:
            asyncio.run(assert_resource("resource4", resource_info, get_context))

        assert "Test Resource 'resource4' is not available in the list" in str(
            exc_info.value
        )
        assert "resource1, resource2, resource3" in str(exc_info.value)


class TestAssertHttpMethod:
    @patch("foreman_mcp_server.utils.utils.Resource")
    def test_assert_http_method_valid(self, mock_resource_class):
        """Test assert_http_method when HTTP method matches."""
        mock_route = Mock()
        mock_route.method = "post"

        mock_action = Mock()
        mock_action.find_route.return_value = mock_route

        mock_resource = Mock()
        mock_resource.action.return_value = mock_action

        mock_resource_class.return_value = mock_resource

        foreman_api = Mock()
        action_info = {
            "resource": "test_resource",
            "name": "test_action",
            "params": {"test": "param"},
        }

        result = assert_http_method(foreman_api, action_info, "POST")

        assert result is True
        mock_resource_class.assert_called_once_with(foreman_api, "test_resource")
        mock_resource.action.assert_called_once_with("test_action")
        mock_action.find_route.assert_called_once_with({"test": "param"})

    @patch("foreman_mcp_server.utils.utils.Resource")
    def test_assert_http_method_invalid(self, mock_resource_class):
        """Test assert_http_method when HTTP method doesn't match."""
        mock_route = Mock()
        mock_route.method = "get"

        mock_action = Mock()
        mock_action.find_route.return_value = mock_route

        mock_resource = Mock()
        mock_resource.action.return_value = mock_action

        mock_resource_class.return_value = mock_resource

        foreman_api = Mock()
        action_info = {
            "resource": "test_resource",
            "name": "test_action",
            "params": {"test": "param"},
        }

        with pytest.raises(ToolError) as exc_info:
            assert_http_method(foreman_api, action_info, "POST")

        assert "Action 'test_action' on resource 'test_resource' is not allowed" in str(
            exc_info.value
        )
        assert "GET method is not allowed, expected POST" in str(exc_info.value)


class TestMcpInfoHeaders:
    def test_mcp_info_headers(self):
        """Test mcp_info_headers returns correct headers."""
        mock_request = Mock()
        mock_request.client.host = "localhost"
        mock_request.client.port = 8080
        mock_request.headers.get.return_value = "test-session-id"

        mock_context = Mock()
        mock_context.request_context.request = mock_request

        get_context = Mock(return_value=mock_context)

        result = mcp_info_headers(get_context)

        expected = {
            "X-Foreman-MCP-Server-Host": "localhost:8080",
            "X-Foreman-MCP-Server-MCP-Session-ID": "test-session-id",
        }

        assert result == expected
        mock_request.headers.get.assert_called_once_with("mcp-session-id")


class TestGetForemanApi:
    def test_get_foreman_api_success(self):
        """Test get_foreman_api when user and session exist."""
        mock_api = Mock()
        user_map = {"test_user": {"test_session": mock_api}}

        mock_request = Mock()
        mock_request.headers.get.side_effect = lambda key: {
            "foreman_username": "test_user",
            "mcp-session-id": "test_session",
        }.get(key)

        mock_context = Mock()
        mock_context.request_context.request = mock_request
        mock_context.user_map = user_map

        get_context = Mock(return_value=mock_context)

        result = get_foreman_api(get_context)

        assert result is mock_api

    def test_get_foreman_api_user_not_found(self):
        """Test get_foreman_api when user doesn't exist."""
        mock_request = Mock()
        mock_request.headers.get.side_effect = lambda key: {
            "foreman_username": "nonexistent_user",
            "mcp-session-id": "test_session",
        }.get(key)

        mock_context = Mock()
        mock_context.request_context.request = mock_request
        mock_context.user_map = {}

        get_context = Mock(return_value=mock_context)

        with pytest.raises(RuntimeError) as exc_info:
            get_foreman_api(get_context)

        assert "Foreman API is not available for nonexistent_user" in str(exc_info.value)

    def test_get_foreman_api_session_not_found(self):
        """Test get_foreman_api when session doesn't exist for user."""
        user_map = {"test_user": {"other_session": Mock()}}

        mock_request = Mock()
        mock_request.headers.get.side_effect = lambda key: {
            "foreman_username": "test_user",
            "mcp-session-id": "nonexistent_session",
        }.get(key)

        mock_context = Mock()
        mock_context.request_context.request = mock_request
        mock_context.user_map = user_map

        get_context = Mock(return_value=mock_context)

        with pytest.raises(RuntimeError) as exc_info:
            get_foreman_api(get_context)

        assert "Foreman API is not available for test_user" in str(exc_info.value)

    def test_get_foreman_api_no_user_map(self):
        """Test get_foreman_api when user_map attribute doesn't exist."""
        mock_request = Mock()
        mock_request.headers.get.side_effect = lambda key: {
            "foreman_username": "test_user",
            "mcp-session-id": "test_session",
        }.get(key)

        mock_context = Mock()
        mock_context.request_context.request = mock_request
        # No user_map attribute - getattr will return empty dict as default
        del mock_context.user_map  # Ensure the attribute doesn't exist

        get_context = Mock(return_value=mock_context)

        with pytest.raises(RuntimeError) as exc_info:
            get_foreman_api(get_context)

        assert "Foreman API is not available for test_user" in str(exc_info.value)
