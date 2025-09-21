"""
OpenTelemetry Configuration for HMS Microservices
Unified tracing and metrics collection across all services
"""

import os
import logging
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.propagators.jaeger import JaegerPropagator
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.propagate import set_global_textmap

logger = logging.getLogger(__name__)

class OtelConfig:
    """OpenTelemetry configuration for HMS services"""

    def __init__(
        self,
        service_name: str,
        service_version: str = "1.0.0",
        environment: str = "production",
        enabled: bool = True,
        metrics_enabled: bool = True,
        traces_enabled: bool = True,
        logs_enabled: bool = True
    ):
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment
        self.enabled = enabled
        self.metrics_enabled = metrics_enabled
        self.traces_enabled = traces_enabled
        self.logs_enabled = logs_enabled

        # Configuration
        self.otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
        self.jaeger_endpoint = os.getenv("JAEGER_ENDPOINT", "http://jaeger-collector:14250")
        self.prometheus_port = int(os.getenv("PROMETHEUS_PORT", "8090"))

        # Initialize resources
        self.resource = self._create_resource()

        # Initialize providers
        self.tracer_provider = None
        self.meter_provider = None
        self.logger_provider = None

    def _create_resource(self) -> Resource:
        """Create OpenTelemetry resource with service information"""
        return Resource.create({
            ResourceAttributes.SERVICE_NAME: self.service_name,
            ResourceAttributes.SERVICE_VERSION: self.service_version,
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: self.environment,
            "service.namespace": "hms",
            "team": "platform",
            "application": "hms"
        })

    def setup_tracing(self) -> Optional[TracerProvider]:
        """Setup distributed tracing"""
        if not self.traces_enabled or not self.enabled:
            logger.info("Tracing is disabled")
            return None

        try:
            # Create tracer provider
            self.tracer_provider = TracerProvider(resource=self.resource)

            # Create exporters
            exporters = []

            # OTLP exporter
            otlp_exporter = OTLPSpanExporter(
                endpoint=self.otlp_endpoint,
                insecure=True,
                timeout=30
            )
            exporters.append(otlp_exporter)

            # Jaeger exporter (backup)
            jaeger_exporter = JaegerExporter(
                agent_host_name="jaeger-agent",
                agent_port=6831,
                collector_endpoint=self.jaeger_endpoint,
            )
            exporters.append(jaeger_exporter)

            # Add batch processors for each exporter
            for exporter in exporters:
                span_processor = BatchSpanProcessor(
                    exporter,
                    max_queue_size=10000,
                    max_export_batch_size=1000,
                    export_timeout_sec=30,
                    schedule_delay_millis=5000
                )
                self.tracer_provider.add_span_processor(span_processor)

            # Set as global tracer provider
            trace.set_tracer_provider(self.tracer_provider)

            logger.info(f"Tracing configured for service: {self.service_name}")
            return self.tracer_provider

        except Exception as e:
            logger.error(f"Failed to setup tracing: {e}")
            return None

    def setup_metrics(self) -> Optional[MeterProvider]:
        """Setup metrics collection"""
        if not self.metrics_enabled or not self.enabled:
            logger.info("Metrics collection is disabled")
            return None

        try:
            # Create meter provider
            self.meter_provider = MeterProvider(resource=self.resource)

            # Add Prometheus reader
            prometheus_reader = PrometheusMetricReader(
                prefix=f"{self.service_name}_",
                endpoint=f"0.0.0.0:{self.prometheus_port}"
            )

            # Add OTLP exporter
            otlp_metric_exporter = OTLPMetricExporter(
                endpoint=self.otlp_endpoint,
                insecure=True,
                timeout=30
            )

            metric_reader = PeriodicExportingMetricReader(
                otlp_metric_exporter,
                export_interval_millis=60000,
                export_timeout_millis=30000
            )

            self.meter_provider.add_metric_reader(prometheus_reader)
            self.meter_provider.add_metric_reader(metric_reader)

            # Set as global meter provider
            metrics.set_meter_provider(self.meter_provider)

            logger.info(f"Metrics configured for service: {self.service_name}")
            return self.meter_provider

        except Exception as e:
            logger.error(f"Failed to setup metrics: {e}")
            return None

    def setup_logging(self):
        """Setup structured logging with trace correlation"""
        if not self.logs_enabled or not self.enabled:
            logger.info("Logging instrumentation is disabled")
            return

        try:
            # Setup logging instrumentation
            LoggingInstrumentor().instrument(
                log_level=logging.INFO,
                set_logging_format=True,
                exporter=ConsoleMetricExporter()
            )

            logger.info("Logging instrumentation configured")

        except Exception as e:
            logger.error(f"Failed to setup logging instrumentation: {e}")

    def setup_propagators(self):
        """Setup context propagators"""
        # Set composite propagator
        propagator = CompositePropagator([
            B3MultiFormat(),
            JaegerPropagator(),
        ])
        set_global_textmap(propagator)

        logger.info("Context propagators configured")

    def instrument_django(self):
        """Instrument Django application"""
        try:
            DjangoInstrumentor().instrument(
                enabled=self.traces_enabled,
                tracer_provider=self.tracer_provider
            )
            logger.info("Django instrumentation configured")
        except Exception as e:
            logger.error(f"Failed to instrument Django: {e}")

    def instrument_fastapi(self, app):
        """Instrument FastAPI application"""
        try:
            FastAPIInstrumentor().instrument_app(
                app,
                tracer_provider=self.tracer_provider,
                meter_provider=self.meter_provider,
                excluded_urls="/health,/metrics,/ready,/live"
            )
            logger.info("FastAPI instrumentation configured")
        except Exception as e:
            logger.error(f"Failed to instrument FastAPI: {e}")

    def instrument_libraries(self):
        """Instrument third-party libraries"""
        try:
            # Database
            Psycopg2Instrumentor().instrument(tracer_provider=self.tracer_provider)
            SQLAlchemyInstrumentor().instrument(tracer_provider=self.tracer_provider)

            # Redis
            RedisInstrumentor().instrument(tracer_provider=self.tracer_provider)

            # HTTP clients
            RequestsInstrumentor().instrument(tracer_provider=self.tracer_provider)
            HTTPXClientInstrumentor().instrument(tracer_provider=self.tracer_provider)
            AioHttpClientInstrumentor().instrument(tracer_provider=self.tracer_provider)

            logger.info("Library instrumentation configured")

        except Exception as e:
            logger.error(f"Failed to instrument libraries: {e}")

    def setup(self) -> bool:
        """Setup complete OpenTelemetry configuration"""
        if not self.enabled:
            logger.info("OpenTelemetry is disabled")
            return False

        try:
            # Setup all components
            self.setup_tracing()
            self.setup_metrics()
            self.setup_logging()
            self.setup_propagators()
            self.instrument_libraries()

            logger.info(f"OpenTelemetry setup completed for {self.service_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to setup OpenTelemetry: {e}")
            return False

    def get_tracer(self, name: str = None):
        """Get tracer instance"""
        if not self.tracer_provider:
            return None
        tracer_name = name or f"{self.service_name}.tracer"
        return self.tracer_provider.get_tracer(tracer_name)

    def get_meter(self, name: str = None):
        """Get meter instance"""
        if not self.meter_provider:
            return None
        meter_name = name or f"{self.service_name}.meter"
        return self.meter_provider.get_meter(meter_name)

    @asynccontextmanager
    async def trace_operation(self, operation_name: str, attributes: Dict[str, Any] = None):
        """Context manager for tracing async operations"""
        tracer = self.get_tracer()
        if not tracer:
            yield
            return

        with tracer.start_as_current_span(operation_name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            yield

    def record_metric(self, name: str, value: float, unit: str = "", attributes: Dict[str, Any] = None):
        """Record a metric"""
        meter = self.get_meter()
        if not meter:
            return

        try:
            counter = meter.create_counter(
                name,
                unit=unit,
                description=f"HMS metric: {name}"
            )
            counter.add(value, attributes or {})
        except Exception as e:
            logger.error(f"Failed to record metric {name}: {e}")

    def record_histogram(self, name: str, value: float, unit: str = "", attributes: Dict[str, Any] = None, buckets: list = None):
        """Record a histogram metric"""
        meter = self.get_meter()
        if not meter:
            return

        try:
            histogram = meter.create_histogram(
                name,
                unit=unit,
                description=f"HMS histogram: {name}",
                buckets=buckets or [0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 300.0]
            )
            histogram.record(value, attributes or {})
        except Exception as e:
            logger.error(f"Failed to record histogram {name}: {e}")

# Global configuration instance
otel_config = None

def setup_otel(service_name: str, **kwargs) -> OtelConfig:
    """Setup OpenTelemetry for a service"""
    global otel_config
    otel_config = OtelConfig(service_name, **kwargs)
    otel_config.setup()
    return otel_config

def get_otel_config() -> Optional[OtelConfig]:
    """Get the global OpenTelemetry configuration"""
    return otel_config

def get_tracer(name: str = None):
    """Get tracer from global config"""
    if otel_config:
        return otel_config.get_tracer(name)
    return None

def get_meter(name: str = None):
    """Get meter from global config"""
    if otel_config:
        return otel_config.get_meter(name)
    return None

# Decorators for easy tracing
def trace_async(operation_name: str = None):
    """Decorator for tracing async functions"""
    def decorator(func):
        import functools

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = get_tracer()
            if not tracer:
                return await func(*args, **kwargs)

            name = operation_name or f"{func.__module__}.{func.__name__}"

            with tracer.start_as_current_span(name) as span:
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", str(e))
                    span.set_attribute("error.type", type(e).__name__)
                    raise
        return wrapper
    return decorator

def trace_sync(operation_name: str = None):
    """Decorator for tracing sync functions"""
    def decorator(func):
        import functools

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            if not tracer:
                return func(*args, **kwargs)

            name = operation_name or f"{func.__module__}.{func.__name__}"

            with tracer.start_as_current_span(name) as span:
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", str(e))
                    span.set_attribute("error.type", type(e).__name__)
                    raise
        return wrapper
    return decorator

# Middleware for correlation ID propagation
class CorrelationIDMiddleware:
    """Middleware for correlation ID propagation"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        # Extract or create correlation ID
        headers = dict(scope.get("headers", []))
        correlation_id = headers.get(b"x-correlation-id", b"").decode()

        if not correlation_id:
            import uuid
            correlation_id = str(uuid.uuid4())

        # Add to scope for handlers
        scope["correlation_id"] = correlation_id

        # Inject into OpenTelemetry context
        tracer = get_tracer()
        if tracer:
            context = trace.set_span_in_context(trace.get_current_span())
            context = trace.set_span_attributes(
                {"correlation.id": correlation_id},
                context
            )

        # Add correlation ID to response headers
        async def send_with_correlation(message):
            if message["type"] == "http.response.start":
                headers = message.get("headers", [])
                headers.append((b"x-correlation-id", correlation_id.encode()))
                message["headers"] = headers
            await send(message)

        return await self.app(scope, receive, send_with_correlation)