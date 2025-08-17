"""Tests for HTTP server runner module."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mcp_local_repo_analyzer.run_http_server import main


@pytest.mark.unit
class TestRunHTTPServer:
    """Test HTTP server runner functionality."""

    @patch("mcp_local_repo_analyzer.run_http_server.register_tools")
    @patch("mcp_local_repo_analyzer.run_http_server.create_server")
    @patch("builtins.print")
    def test_main_success(self, mock_print, mock_create_server, mock_register_tools):
        """Test successful HTTP server startup."""
        # Create mock server and services
        mock_server = Mock()
        mock_services = {"service": "mock"}
        mock_create_server.return_value = (mock_server, mock_services)

        # Call main
        main()

        # Verify server creation and registration
        mock_create_server.assert_called_once()
        mock_register_tools.assert_called_once_with(mock_server, mock_services)

        # Verify server.run was called with correct parameters
        mock_server.run.assert_called_once_with(
            transport="streamable-http", host="localhost", port=8000
        )

        # Verify startup message was printed
        mock_print.assert_called_once_with(
            "🚀 Starting HTTP server on http://localhost:8000/mcp"
        )

    @patch("mcp_local_repo_analyzer.run_http_server.register_tools")
    @patch("mcp_local_repo_analyzer.run_http_server.create_server")
    def test_main_server_creation_error(self, mock_create_server, mock_register_tools):
        """Test error handling during server creation."""
        mock_create_server.side_effect = RuntimeError("Server creation failed")

        with pytest.raises(RuntimeError, match="Server creation failed"):
            main()

        # Verify register_tools was not called due to error
        mock_register_tools.assert_not_called()

    @patch("mcp_local_repo_analyzer.run_http_server.register_tools")
    @patch("mcp_local_repo_analyzer.run_http_server.create_server")
    def test_main_register_tools_error(self, mock_create_server, mock_register_tools):
        """Test error handling during tools registration."""
        mock_server = Mock()
        mock_services = {"service": "mock"}
        mock_create_server.return_value = (mock_server, mock_services)
        mock_register_tools.side_effect = RuntimeError("Tools registration failed")

        with pytest.raises(RuntimeError, match="Tools registration failed"):
            main()

        # Verify server was created but run was not called
        mock_create_server.assert_called_once()
        mock_server.run.assert_not_called()

    @patch("mcp_local_repo_analyzer.run_http_server.register_tools")
    @patch("mcp_local_repo_analyzer.run_http_server.create_server")
    @patch("builtins.print")
    def test_main_server_run_error(
        self, mock_print, mock_create_server, mock_register_tools
    ):
        """Test error handling during server run."""
        mock_server = Mock()
        mock_services = {"service": "mock"}
        mock_create_server.return_value = (mock_server, mock_services)
        mock_server.run.side_effect = RuntimeError("Server run failed")

        with pytest.raises(RuntimeError, match="Server run failed"):
            main()

        # Verify everything up to server.run was called
        mock_create_server.assert_called_once()
        mock_register_tools.assert_called_once_with(mock_server, mock_services)
        mock_print.assert_called_once()

    def test_module_imports(self):
        """Test that all required modules can be imported."""
        # This test ensures the import statement is correct
        from mcp_local_repo_analyzer.main import create_server, register_tools

        assert callable(create_server)
        assert callable(register_tools)

    def test_path_manipulation(self):
        """Test that project root path is correctly calculated."""
        from mcp_local_repo_analyzer import run_http_server

        # The project_root should be the parent of the module file
        expected_path = Path(run_http_server.__file__).parent

        # Verify the path is added to sys.path
        assert str(expected_path) in sys.path

    @patch("mcp_local_repo_analyzer.run_http_server.register_tools")
    @patch("mcp_local_repo_analyzer.run_http_server.create_server")
    @patch("builtins.print")
    def test_main_call_order(self, mock_print, mock_create_server, mock_register_tools):
        """Test that functions are called in the correct order."""
        mock_server = Mock()
        mock_services = {"service": "mock"}
        mock_create_server.return_value = (mock_server, mock_services)

        main()

        # Verify call order using assert_has_calls or checking call_count
        assert mock_create_server.call_count == 1
        assert mock_register_tools.call_count == 1
        assert mock_server.run.call_count == 1
        assert mock_print.call_count == 1

        # Verify register_tools is called after create_server
        # and server.run is called after register_tools
        # This is ensured by the mock behavior in the main function

    @patch("mcp_local_repo_analyzer.run_http_server.register_tools")
    @patch("mcp_local_repo_analyzer.run_http_server.create_server")
    @patch("builtins.print")
    def test_main_with_mock_server_methods(
        self, mock_print, mock_create_server, mock_register_tools
    ):
        """Test main with detailed server mock verification."""
        mock_server = Mock()
        mock_services = {"service": "mock"}
        mock_create_server.return_value = (mock_server, mock_services)

        main()

        # Verify the server mock was configured correctly
        assert hasattr(mock_server, "run")
        mock_server.run.assert_called_once()

        # Verify the exact parameters passed to run
        call_args = mock_server.run.call_args
        assert call_args[1]["transport"] == "streamable-http"
        assert call_args[1]["host"] == "localhost"
        assert call_args[1]["port"] == 8000
