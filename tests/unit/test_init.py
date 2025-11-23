"""Tests for autolemetry initialization."""

from typing import Any

from opentelemetry import _logs as otel_logs
from opentelemetry import context, trace
from opentelemetry import metrics as otel_metrics
from opentelemetry.baggage import propagation
from opentelemetry.sdk._logs import LoggerProvider, LogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

from autolemetry import init, span
from autolemetry.exporters import InMemorySpanExporter
from autolemetry.processors import SimpleSpanProcessor


def _set_baggage_dict(ctx: Any, baggage_dict: Any) -> Any:
    """Helper to set multiple baggage entries from a dict."""
    new_context = ctx
    for key, value in baggage_dict.items():
        new_context = propagation.set_baggage(key, value, new_context)
    return new_context


class DummyLogRecordProcessor(LogRecordProcessor):
    """Test log record processor to verify registration."""

    def __init__(self: Any) -> None:
        self.seen = 0

    def on_emit(self: Any, _log_data: Any) -> None:  # noqa: ANN001
        self.seen += 1

    def shutdown(self: Any) -> None:  # pragma: no cover - simple stub
        return None

    def force_flush(self: Any, timeout_millis: int | None = None) -> bool:  # noqa: ARG002
        return True


def test_init_basic() -> None:
    """Test basic initialization."""
    init(service="test-service")
    provider = trace.get_tracer_provider()
    assert provider is not None


def test_init_with_custom_endpoint() -> None:
    """Test initialization with custom endpoint."""
    init(service="test", endpoint="http://custom:4318")
    provider = trace.get_tracer_provider()
    assert provider is not None


def test_init_with_resource_attributes() -> None:
    """Test initialization with resource attributes."""
    init(service="test", resource_attributes={"custom.key": "value"})
    provider = trace.get_tracer_provider()
    assert provider is not None


def test_init_with_baggage_true() -> None:
    """Test initialization with baggage=True (default prefix)."""
    exporter = InMemorySpanExporter()
    init(service="test", span_processor=SimpleSpanProcessor(exporter), baggage=True)

    # Set baggage and create span
    active_context = context.get_current()
    baggage_dict = {"tenant.id": "tenant-123"}
    context_with_baggage = _set_baggage_dict(active_context, baggage_dict)

    token = context.attach(context_with_baggage)
    try:
        with span("test.operation"):
            pass
    finally:
        context.detach(token)

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].attributes is not None
    assert spans[0].attributes.get("baggage.tenant.id") == "tenant-123"


def test_init_with_baggage_custom_prefix() -> None:
    """Test initialization with baggage='custom' (custom prefix)."""
    exporter = InMemorySpanExporter()
    init(service="test", span_processor=SimpleSpanProcessor(exporter), baggage="ctx")

    # Set baggage and create span
    active_context = context.get_current()
    baggage_dict = {"tenant.id": "tenant-123"}
    context_with_baggage = _set_baggage_dict(active_context, baggage_dict)

    token = context.attach(context_with_baggage)
    try:
        with span("test.operation"):
            pass
    finally:
        context.detach(token)

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].attributes is not None
    assert spans[0].attributes.get("ctx.tenant.id") == "tenant-123"


def test_init_with_baggage_empty_string() -> None:
    """Test initialization with baggage='' (no prefix)."""
    exporter = InMemorySpanExporter()
    init(service="test", span_processor=SimpleSpanProcessor(exporter), baggage="")

    # Set baggage and create span
    active_context = context.get_current()
    baggage_dict = {"tenant.id": "tenant-123"}
    context_with_baggage = _set_baggage_dict(active_context, baggage_dict)

    token = context.attach(context_with_baggage)
    try:
        with span("test.operation"):
            pass
    finally:
        context.detach(token)

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].attributes is not None
    assert spans[0].attributes.get("tenant.id") == "tenant-123"


def test_init_with_baggage_false() -> None:
    """Test initialization with baggage=False (disabled)."""
    exporter = InMemorySpanExporter()
    init(service="test", span_processor=SimpleSpanProcessor(exporter), baggage=False)

    # Set baggage and create span
    active_context = context.get_current()
    baggage_dict = {"tenant.id": "tenant-123"}
    context_with_baggage = _set_baggage_dict(active_context, baggage_dict)

    token = context.attach(context_with_baggage)
    try:
        with span("test.operation"):
            pass
    finally:
        context.detach(token)

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    # Should not have baggage attributes when disabled
    assert spans[0].attributes is not None
    assert "baggage.tenant.id" not in spans[0].attributes
    assert "tenant.id" not in spans[0].attributes


def test_init_with_multiple_span_processors() -> None:
    """Ensure multiple span processors are supported."""
    exporter_one = InMemorySpanExporter()
    exporter_two = InMemorySpanExporter()
    processors = [
        SimpleSpanProcessor(exporter_one),
        SimpleSpanProcessor(exporter_two),
    ]

    init(service="test", span_processors=processors)  # type: ignore[arg-type]

    with span("test.operation"):
        pass

    assert len(exporter_one.get_finished_spans()) == 1
    assert len(exporter_two.get_finished_spans()) == 1


def test_init_with_multiple_span_exporters() -> None:
    """Ensure multiple span exporters are wrapped and exported."""
    exporter_one = InMemorySpanExporter()
    exporter_two = InMemorySpanExporter()

    init(
        service="test",
        span_exporters=[exporter_one, exporter_two],
        batch_timeout=10,
    )

    with span("test.exporters"):
        pass

    getattr(trace.get_tracer_provider(), "force_flush", lambda: None)()

    assert len(exporter_one.get_finished_spans()) == 1
    assert len(exporter_two.get_finished_spans()) == 1


def test_init_with_metric_readers() -> None:
    """Ensure custom metric readers are registered."""
    reader = InMemoryMetricReader()

    init(
        service="test",
        span_processors=[SimpleSpanProcessor(InMemorySpanExporter())],
        metric_readers=[reader],
    )

    provider = otel_metrics.get_meter_provider()
    assert isinstance(provider, MeterProvider)
    assert reader in getattr(provider, "_all_metric_readers", [])


def test_init_with_log_record_processors() -> None:
    """Ensure custom log record processors are registered."""
    processor = DummyLogRecordProcessor()

    init(
        service="test",
        span_processors=[SimpleSpanProcessor(InMemorySpanExporter())],
        log_record_processors=[processor],
    )

    provider = otel_logs.get_logger_provider()
    assert isinstance(provider, LoggerProvider)
    assert processor in provider._multi_log_record_processor._log_record_processors
