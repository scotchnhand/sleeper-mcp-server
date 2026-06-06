"""Configuration management for the Sleeper MCP server."""

import logging
import os
from dataclasses import dataclass
from typing import Literal


@dataclass
class TransportConfig:
    """Configuration for transport selection."""

    transport_type: Literal["stdio", "sse"]
    sse_port: int
    sse_host: str
    log_level: str

    @staticmethod
    def from_env() -> "TransportConfig":
        """Load configuration from environment variables.

        Environment variables:
        - TRANSPORT: "stdio" or "sse" (default: "stdio")
        - SSE_PORT: Port for SSE server (default: 8000)
        - SSE_HOST: Host for SSE server (default: "0.0.0.0")
        - LOG_LEVEL: Logging level (default: "INFO")

        Returns:
            TransportConfig instance with loaded values
        """
        transport_type = os.getenv("TRANSPORT", "stdio")
        if transport_type not in ("stdio", "sse"):
            transport_type = "stdio"

        try:
            sse_port = int(os.getenv("SSE_PORT", "8000"))
        except ValueError:
            sse_port = 8000

        sse_host = os.getenv("SSE_HOST", "0.0.0.0")
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

        # Validate log level
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if log_level not in valid_levels:
            log_level = "INFO"

        return TransportConfig(
            transport_type=transport_type,  # type: ignore
            sse_port=sse_port,
            sse_host=sse_host,
            log_level=log_level
        )
