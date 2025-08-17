"""Tests for CLI module."""

from unittest.mock import patch

import pytest

from mcp_local_repo_analyzer.cli import main, parse_args


@pytest.mark.unit
class TestCLI:
    """Test CLI functionality."""

    def test_parse_args_default(self):
        """Test parsing with default arguments."""
        with patch("sys.argv", ["cli.py"]):
            args = parse_args()

            assert args.transport == "stdio"
            assert args.host == "127.0.0.1"
            assert args.port == 9070
            assert args.log_level == "INFO"
            assert args.work_dir is None

    def test_parse_args_custom_transport(self):
        """Test parsing with custom transport."""
        with patch("sys.argv", ["cli.py", "--transport", "streamable-http"]):
            args = parse_args()

            assert args.transport == "streamable-http"

    def test_parse_args_custom_host_port(self):
        """Test parsing with custom host and port."""
        with patch("sys.argv", ["cli.py", "--host", "0.0.0.0", "--port", "8080"]):
            args = parse_args()

            assert args.host == "0.0.0.0"
            assert args.port == 8080

    def test_parse_args_custom_log_level(self):
        """Test parsing with custom log level."""
        with patch("sys.argv", ["cli.py", "--log-level", "DEBUG"]):
            args = parse_args()

            assert args.log_level == "DEBUG"

    def test_parse_args_with_work_dir(self):
        """Test parsing with work directory."""
        with patch("sys.argv", ["cli.py", "--work-dir", "/tmp/test"]):
            args = parse_args()

            assert args.work_dir == "/tmp/test"

    def test_parse_args_all_options(self):
        """Test parsing with all options."""
        with patch(
            "sys.argv",
            [
                "cli.py",
                "--transport",
                "sse",
                "--host",
                "192.168.1.1",
                "--port",
                "9999",
                "--log-level",
                "WARNING",
                "--work-dir",
                "/path/to/work",
            ],
        ):
            args = parse_args()

            assert args.transport == "sse"
            assert args.host == "192.168.1.1"
            assert args.port == 9999
            assert args.log_level == "WARNING"
            assert args.work_dir == "/path/to/work"

    @patch("mcp_local_repo_analyzer.cli.run_main")
    @patch("mcp_local_repo_analyzer.cli.logging.basicConfig")
    @patch("sys.argv", ["cli.py", "--transport", "stdio"])
    def test_main_success(self, mock_logging_config, mock_run_main):
        """Test successful main execution."""
        main()

        # Check logging was configured
        mock_logging_config.assert_called_once()

        # Check main was called
        mock_run_main.assert_called_once()

    @patch("mcp_local_repo_analyzer.cli.run_main")
    @patch("mcp_local_repo_analyzer.cli.logging.basicConfig")
    @patch("sys.argv", ["cli.py", "--work-dir", "/tmp/test"])
    def test_main_with_work_dir(self, mock_logging_config, mock_run_main):
        """Test main execution with work directory."""
        main()

        mock_run_main.assert_called_once()

    @patch("mcp_local_repo_analyzer.cli.run_main")
    @patch("mcp_local_repo_analyzer.cli.logging.basicConfig")
    @patch("sys.argv", ["cli.py"])
    def test_main_without_work_dir(self, mock_logging_config, mock_run_main):
        """Test main execution without work directory."""
        main()

        mock_run_main.assert_called_once()

    @patch("mcp_local_repo_analyzer.cli.run_main")
    @patch("mcp_local_repo_analyzer.cli.logging.basicConfig")
    @patch("sys.argv", ["cli.py"])
    def test_main_keyboard_interrupt(self, mock_logging_config, mock_run_main):
        """Test main execution with keyboard interrupt."""
        mock_run_main.side_effect = KeyboardInterrupt()

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0

    @patch("mcp_local_repo_analyzer.cli.run_main")
    @patch("mcp_local_repo_analyzer.cli.logging.basicConfig")
    @patch("sys.argv", ["cli.py"])
    def test_main_exception(self, mock_logging_config, mock_run_main):
        """Test main execution with exception."""
        mock_run_main.side_effect = RuntimeError("Test error")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("mcp_local_repo_analyzer.cli.run_main")
    @patch("mcp_local_repo_analyzer.cli.logging.basicConfig")
    @patch(
        "sys.argv",
        [
            "cli.py",
            "--transport",
            "streamable-http",
            "--host",
            "0.0.0.0",
            "--port",
            "8080",
            "--log-level",
            "DEBUG",
            "--work-dir",
            "/test/dir",
        ],
    )
    def test_main_argv_manipulation(self, mock_logging_config, mock_run_main):
        """Test that argv is properly manipulated for main.py."""
        main()

        # Verify main was called
        mock_run_main.assert_called_once()

    def test_parse_args_invalid_transport(self):
        """Test parsing with invalid transport."""
        with patch("sys.argv", ["cli.py", "--transport", "invalid"]), pytest.raises(
            SystemExit
        ):
            parse_args()

    def test_parse_args_invalid_log_level(self):
        """Test parsing with invalid log level."""
        with patch("sys.argv", ["cli.py", "--log-level", "INVALID"]), pytest.raises(
            SystemExit
        ):
            parse_args()

    def test_parse_args_invalid_port(self):
        """Test parsing with invalid port."""
        with patch("sys.argv", ["cli.py", "--port", "not_a_number"]), pytest.raises(
            SystemExit
        ):
            parse_args()
