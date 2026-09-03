from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

from astroimage.shared.telemetry import current_trace_ids


def test_current_trace_ids_empty_without_span() -> None:
    previous = trace.get_tracer_provider()
    trace.set_tracer_provider(trace.NoOpTracerProvider())
    try:
        trace_id, span_id = current_trace_ids()
    finally:
        trace.set_tracer_provider(previous)
    assert trace_id is None
    assert span_id is None


def test_current_trace_ids_from_active_span() -> None:
    previous = trace.get_tracer_provider()
    provider = TracerProvider()
    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer("astroimage.tests")
    try:
        with tracer.start_as_current_span("unit"):
            trace_id, span_id = current_trace_ids()
    finally:
        trace.set_tracer_provider(previous)
    assert trace_id is not None
    assert span_id is not None
    assert len(trace_id) == 32
    assert len(span_id) == 16
    assert int(trace_id, 16) != 0
