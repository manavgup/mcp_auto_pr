"""Server runner module for executing MCP servers with different transport configurations."""

from fastmcp import FastMCP

from mcp_shared_lib.transports.config import TransportConfig
from mcp_shared_lib.transports.factory import get_transport


def run_server(
    mcp_server: FastMCP,
    transport_config: TransportConfig,
    server_name: str = "MCP Server",
) -> None:
    """Run the MCP server with the specified transport configuration.

    Args:
        mcp_server (FastMCP): The MCP server instance to run.
        transport_config (TransportConfig): Configuration for the transport layer.
        server_name (str, optional): Name of the server for logging. Defaults to "MCP Server".

    This function initializes the transport based on the provided configuration,
    logs the startup message, and runs the transport with the MCP server.
    """
    transport = get_transport(transport_config)
    print(f"Starting {server_name} with transport: {transport_config.type}")
    transport.run(mcp_server)
