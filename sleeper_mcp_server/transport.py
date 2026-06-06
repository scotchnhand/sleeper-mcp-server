"""Transport layer abstraction for MCP server."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .server import SleeperMCPServer


class BaseTransport(ABC):
    """Abstract base class for MCP server transports."""

    @abstractmethod
    async def run(self, server: "SleeperMCPServer") -> None:
        """Run the server with this transport.

        Args:
            server: The SleeperMCPServer instance to run

        Raises:
            RuntimeError: If the server fails to start or encounters an error
        """
        pass


class StdioTransport(BaseTransport):
    """Standard input/output transport for stdio-based MCP servers."""

    async def run(self, server: "SleeperMCPServer") -> None:
        """Run the MCP server using stdio transport.

        Args:
            server: The SleeperMCPServer instance to run
        """
        await server._run_stdio()


class SSETransport(BaseTransport):
    """Server-Sent Events (SSE) HTTP transport for containerized deployments."""

    def __init__(self, host: str, port: int):
        """Initialize the SSE transport.

        Args:
            host: Host to bind the HTTP server to
            port: Port to bind the HTTP server to
        """
        self.host = host
        self.port = port

    async def run(self, server: "SleeperMCPServer") -> None:
        """Run the MCP server using SSE/HTTP transport.

        Args:
            server: The SleeperMCPServer instance to run
        """
        await server._run_sse(self.host, self.port)
