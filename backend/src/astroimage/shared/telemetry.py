from __future__ import annotations

import os

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

_NON_EXPORTING_SDK = frozenset({"none", "noop"})


def current_trace_ids() -> tuple[str | None, str | None]:
    span_context = trace.get_current_span().get_span_context()
    if span_context is None or not span_context.is_valid:
        return None, None
    return format(span_context.trace_id, "032x"), format(span_context.span_id, "016x")


def setup_tracing(app: FastAPI, *, service_name: str, otlp_endpoint: str | None) -> None:
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    exporter_policy = os.environ.get("OTEL_TRACES_EXPORTER", "otlp").strip().lower()
    if otlp_endpoint and exporter_policy not in _NON_EXPORTING_SDK:
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app, excluded_urls="health,metrics")
