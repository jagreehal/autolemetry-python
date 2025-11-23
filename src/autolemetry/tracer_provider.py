"""Isolated tracer provider support for library authors.

This module allows library authors to use Autolemetry without interfering with
the application's global OpenTelemetry setup. It provides isolated tracer
provider management for libraries that ship with embedded instrumentation.
"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

# Global variable to store the isolated tracer provider
_autolemetry_tracer_provider: TracerProvider | None = None


def set_autolemetry_tracer_provider(provider: TracerProvider | None) -> None:
    """
    Set an isolated tracer provider for Autolemetry.

    This allows library authors to configure a separate tracer provider that
    won't interfere with the application's global OpenTelemetry configuration.
    Useful for libraries that want to provide observability without requiring
    users to set up OTEL themselves.

    Args:
        provider: The TracerProvider instance to use for Autolemetry traces.
            Pass None to clear the isolated provider and revert to the global
            provider.

    Example:
        >>> from opentelemetry.sdk.trace import TracerProvider
        >>> from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
        >>> from autolemetry import set_autolemetry_tracer_provider
        >>>
        >>> # Create isolated provider for your library
        >>> provider = TracerProvider()
        >>> provider.add_span_processor(
        ...     SimpleSpanProcessor(ConsoleSpanExporter())
        ... )
        >>> set_autolemetry_tracer_provider(provider)

    Use Cases:
        - Libraries that ship with embedded Autolemetry
        - SDKs that want observability without requiring users to set up OTEL
        - Testing scenarios with isolated trace collection
        - Multiple subsystems with different exporters

    Important Limitations:
        - Context (trace IDs, parent spans) is still shared globally due to
          OpenTelemetry's global context propagation mechanism
        - This only isolates the tracer provider, not the entire OTEL pipeline
        - Baggage and context propagation remain global

    Note:
        If you need complete isolation including context, you'll need to use
        OpenTelemetry's context API directly with custom context managers.
    """
    global _autolemetry_tracer_provider
    _autolemetry_tracer_provider = provider


def get_autolemetry_tracer_provider() -> TracerProvider | None:
    """
    Get the current isolated tracer provider for Autolemetry.

    Returns the provider set by set_autolemetry_tracer_provider(), or None
    if no isolated provider has been configured.

    Returns:
        The isolated TracerProvider if set, None otherwise

    Example:
        >>> from autolemetry import get_autolemetry_tracer_provider
        >>>
        >>> provider = get_autolemetry_tracer_provider()
        >>> if provider:
        ...     print("Using isolated tracer provider")
        ... else:
        ...     print("Using global tracer provider")
    """
    return _autolemetry_tracer_provider


def get_autolemetry_tracer(
    name: str, version: str | None = None, schema_url: str | None = None
) -> trace.Tracer:
    """
    Get a tracer from the isolated Autolemetry tracer provider.

    If an isolated provider has been set via set_autolemetry_tracer_provider(),
    this function returns a tracer from that provider. Otherwise, it falls back
    to the global tracer provider.

    Args:
        name: Tracer name (typically __name__)
        version: Optional tracer version
        schema_url: Optional schema URL for semantic conventions

    Returns:
        Tracer instance from isolated or global provider

    Example:
        >>> from autolemetry import get_autolemetry_tracer
        >>>
        >>> # Get tracer (will use isolated provider if set)
        >>> tracer = get_autolemetry_tracer(__name__, version="1.0.0")
        >>>
        >>> # Use tracer normally
        >>> with tracer.start_as_current_span("operation") as span:
        ...     span.set_attribute("key", "value")

    Library Author Example:
        >>> # In your library code:
        >>> from autolemetry import get_autolemetry_tracer, set_autolemetry_tracer_provider
        >>> from opentelemetry.sdk.trace import TracerProvider
        >>> from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
        >>>
        >>> # Setup isolated provider for your library
        >>> def setup_library_telemetry():
        ...     provider = TracerProvider()
        ...     provider.add_span_processor(
        ...         SimpleSpanProcessor(ConsoleSpanExporter())
        ...     )
        ...     set_autolemetry_tracer_provider(provider)
        >>>
        >>> # Use in your library functions
        >>> tracer = get_autolemetry_tracer(__name__)
        >>> def library_function():
        ...     with tracer.start_as_current_span("library.operation"):
        ...         # Your library code
        ...         pass
    """
    provider = get_autolemetry_tracer_provider()

    if provider:
        # Use isolated provider
        return provider.get_tracer(name, version, schema_url)
    else:
        # Fall back to global provider
        return trace.get_tracer(name, version, tracer_provider=None, schema_url=schema_url)
