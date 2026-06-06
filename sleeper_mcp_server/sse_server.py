"""SSE/HTTP server implementation for MCP using MCP SDK's SseServerTransport."""

import logging
from typing import TYPE_CHECKING

from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

if TYPE_CHECKING:
    from .server import SleeperMCPServer

logger = logging.getLogger(__name__)


class SSEServerApp:
    """HTTP/SSE server for MCP protocol using Starlette and MCP SDK's SSE transport."""

    def __init__(self, mcp_server: "SleeperMCPServer"):
        """Initialize the SSE server.

        Args:
            mcp_server: The SleeperMCPServer instance to wrap
        """
        self.mcp_server = mcp_server
        self.sse_transport = SseServerTransport("/mcp/messages/")
        self.app = self._create_app()

    def _create_app(self) -> Starlette:
        """Create and configure the Starlette application.

        Returns:
            Configured Starlette application
        """
        async def handle_sse(scope: Scope, receive: Receive, send: Send) -> None:
            """Handle SSE connection from client."""
            try:
                async with self.sse_transport.connect_sse(scope, receive, send) as streams:
                    # Run the MCP server with the SSE transport streams
                    await self.mcp_server.server.run(
                        streams[0],
                        streams[1],
                        self.mcp_server._get_initialization_options()
                    )
            except Exception as e:
                logger.error(f"Error handling SSE connection: {e}", exc_info=True)
                # Send error response
                await send({
                    "type": "http.response.start",
                    "status": 500,
                    "headers": [[b"content-type", b"application/json"]],
                })
                await send({
                    "type": "http.response.body",
                    "body": b'{"error": "Internal server error"}',
                })

        async def handle_health(scope: Scope, receive: Receive, send: Send) -> None:
            """Health check endpoint."""
            response = JSONResponse({"status": "ok"})
            await response(scope, receive, send)

        async def handle_readiness(scope: Scope, receive: Receive, send: Send) -> None:
            """Readiness probe endpoint."""
            is_ready = (
                self.mcp_server.client is not None
                and self.mcp_server.cache is not None
                and self.mcp_server.league_tools is not None
                and self.mcp_server.matchup_tools is not None
                and self.mcp_server.trade_tools is not None
                and self.mcp_server.player_tools is not None
            )

            if is_ready:
                response = JSONResponse({"status": "ready"})
            else:
                response = JSONResponse({"status": "initializing"}, status_code=503)

            await response(scope, receive, send)

        routes = [
            Route("/health", endpoint=handle_health, methods=["GET"]),
            Route("/readiness", endpoint=handle_readiness, methods=["GET"]),
            Mount("/mcp/", app=self.sse_transport.handle_post_message),
        ]

        # Create the base Starlette app
        app = Starlette(routes=routes)

        # Register the SSE handler as the first route for /mcp/sse
        app.router.routes.insert(0, Route("/mcp/sse", endpoint=handle_sse, methods=["GET"]))

        return app

    async def start(self, host: str, port: int) -> None:
        """Start the HTTP/SSE server.

        Args:
            host: Host to bind to
            port: Port to bind to

        Raises:
            RuntimeError: If the server fails to start
        """
        import uvicorn

        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info"
        )

        server = uvicorn.Server(config)

        logger.info(f"SSE server starting on http://{host}:{port}")
        logger.info(f"MCP SSE endpoint: http://{host}:{port}/mcp/sse")
        logger.info(f"Health check: http://{host}:{port}/health")

        try:
            await server.serve()
        except Exception as e:
            logger.error(f"Failed to start SSE server: {e}", exc_info=True)
            raise
