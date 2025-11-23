"""
AFTER AUTOLEMETRY: Automatic Context Propagation

Autolemetry handles all context propagation automatically!
From 135 lines to ~5 lines.
"""

from typing import Any

import autolemetry


def make_downstream_call() -> None:
    """Placeholder downstream call to demonstrate context propagation."""
    return None

# ==================== ENTIRE SETUP ====================
autolemetry.init(
    service_name="mcp-server",
    instrumentation=["mcp"],  # Auto-instruments MCP with context propagation
)
# ==================== THAT'S IT ====================


# Usage example - no manual decorator needed!
async def my_mcp_tool(query: str) -> str:
    """
    MCP tool with automatic context propagation.

    Autolemetry automatically:
    1. Extracts context from _meta fields (if present)
    2. Propagates context to child spans
    3. Injects context when calling other MCP servers
    4. Handles both sync and async functions

    NO decorators needed!
    NO _meta parameter needed in your function signature!
    NO manual wrapper classes!
    """

    # Just write your business logic
    with autolemetry.span("process_query"):
        result = f"Processed: {query}"
        return result


# And server setup is automatic:
# server = MCPServer(...)
# agent = Agent(mcp_servers=[server], ...)
#
# Autolemetry's MCP instrumentation automatically:
# - Wraps call_tool to inject context
# - Adds decorators to tool handlers to extract context
# - Handles all the plumbing transparently


# ==================== ADVANCED: Custom Context Fields ====================
# If you need custom baggage propagation, autolemetry provides simple APIs:

def my_service_call() -> None:
    # Set baggage that will propagate to downstream services
    with autolemetry.with_baggage({
        "user.id": "user-123",
        "tenant.id": "tenant-456"
    }):
        # Make downstream calls here
        # Autolemetry automatically propagates baggage through:
        # - HTTP headers (via instrumented requests/httpx)
        # - MCP _meta fields
        # - gRPC metadata
        # - Any custom transport you configure
        make_downstream_call()


# You can also access propagated baggage:
def downstream_handler() -> None:
    # Access via span context
    with autolemetry.span("handle_request") as ctx:
        user_id = ctx.get_baggage("user.id")  # "user-123" from upstream

        # Use it in your business logic
        ctx.set_attribute("processing.user", user_id)
