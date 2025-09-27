"""
Common utilities and shared components for HMS microservices
"""

# Import commonly used utilities
from .correlation_id import (
    CorrelationIDMiddleware,
    add_correlation_to_message,
    ensure_correlation_id,
    extract_correlation_from_message,
    generate_correlation_id,
    get_correlation_id,
    set_correlation_id,
    with_correlation_id,
)
from .database_correlation import (
    DatabaseConnectionPool,
    DatabaseCorrelationMiddleware,
    DatabaseCorrelationMixin,
    DjangoQuerySetCorrelation,
    QueryCorrelationLogger,
    SQLAlchemyCorrelationExtension,
    database_operation_context,
    with_database_correlation,
)
from .message_correlation import (
    CorrelationTask,
    KafkaCorrelationConsumer,
    KafkaCorrelationProducer,
    RabbitMQCorrelationConsumer,
    RabbitMQCorrelationPublisher,
    RedisCorrelationPublisher,
    RedisCorrelationSubscriber,
    message_processing_context,
    with_message_correlation,
)
from .middleware import (
    CacheControlMiddleware,
    PerformanceMonitoringMiddleware,
    RateLimitMiddleware,
    RequestBodyLoggingMiddleware,
    ResponseSizeMiddleware,
    SecurityHeadersMiddleware,
    create_middleware_stack,
)
from .otel_config import (
    get_meter,
    get_otel_config,
    get_tracer,
    setup_otel,
    trace_async,
    trace_sync,
)

# Version
__version__ = "1.0.0"

# Export commonly used items
__all__ = [
    # Correlation ID
    "get_correlation_id",
    "set_correlation_id",
    "generate_correlation_id",
    "ensure_correlation_id",
    "CorrelationIDMiddleware",
    "with_correlation_id",
    "add_correlation_to_message",
    "extract_correlation_from_message",
    # OpenTelemetry
    "setup_otel",
    "get_otel_config",
    "get_tracer",
    "get_meter",
    "trace_async",
    "trace_sync",
    # Middleware
    "PerformanceMonitoringMiddleware",
    "RateLimitMiddleware",
    "SecurityHeadersMiddleware",
    "CacheControlMiddleware",
    "ResponseSizeMiddleware",
    "RequestBodyLoggingMiddleware",
    "create_middleware_stack",
    # Message Correlation
    "RabbitMQCorrelationPublisher",
    "RabbitMQCorrelationConsumer",
    "KafkaCorrelationProducer",
    "KafkaCorrelationConsumer",
    "RedisCorrelationPublisher",
    "RedisCorrelationSubscriber",
    "CorrelationTask",
    "with_message_correlation",
    "message_processing_context",
    # Database Correlation
    "DatabaseCorrelationMixin",
    "DjangoQuerySetCorrelation",
    "SQLAlchemyCorrelationExtension",
    "DatabaseConnectionPool",
    "QueryCorrelationLogger",
    "DatabaseCorrelationMiddleware",
    "database_operation_context",
    "with_database_correlation",
]
