"""
gRPC Optimization for High-Performance Microservice Communication
Implementing optimized gRPC services with streaming, compression, and load balancing
"""

import asyncio
import time
import logging
from typing import Any, Dict, List, Optional, AsyncIterator, Callable
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import grpc
from grpc.aio import ServicerContext, AioRpcError
import grpc.aio
from concurrent.futures import ThreadPoolExecutor
import orjson
import msgpack
import snappy
import prometheus_client as prom
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode

logger = logging.getLogger(__name__)

# Metrics
GRPC_REQUEST_COUNT = prom.Counter(
    'grpc_request_count',
    'gRPC request count',
    ['service', 'method', 'status_code']
)

GRPC_REQUEST_LATENCY = prom.Histogram(
    'grpc_request_latency_seconds',
    'gRPC request latency',
    ['service', 'method']
)

GRPC_ACTIVE_CONNECTIONS = prom.Gauge(
    'grpc_active_connections',
    'Active gRPC connections',
    ['service']
)

@dataclass
class GrpcServiceConfig:
    """Configuration for gRPC service"""
    name: str
    host: str
    port: int
    max_workers: int = 10
    max_message_length: int = 4 * 1024 * 1024  # 4MB
    enable_compression: bool = True
    compression_level: int = 6
    enable_metrics: bool = True
    enable_tracing: bool = True
    deadline_timeout: float = 30.0
    keepalive_time: int = 30
    keepalive_timeout: int = 5
    keepalive_permit_without_calls: bool = True

class CompressionInterceptor(grpc.aio.ServerInterceptor):
    """Interceptor for request/response compression"""

    def __init__(self, enable_compression: bool = True, compression_level: int = 6):
        self.enable_compression = enable_compression
        self.compression_level = compression_level
        self.compressor = snappy if enable_compression else None

    async def intercept_service(
        self,
        continuation: Callable,
        handler_call_details: grpc.HandlerCallDetails
    ):
        # Wrap service handler
        service = await continuation(handler_call_details)
        if service is None:
            return service

        async def wrapped_method(request, context):
            # Decompress request if needed
            if self.compressor and hasattr(request, 'compressed'):
                try:
                    request.data = self.compressor.decompress(request.data)
                except:
                    pass

            # Call service method
            response = await service.unary_unary(request, context)

            # Compress response if needed
            if self.compressor and hasattr(response, 'data'):
                try:
                    response.data = self.compressor.compress(response.data)
                    response.compressed = True
                except:
                    pass

            return response

        return grpc.aio.unary_unary_rpc_method_handler(wrapped_method)

class MetricsInterceptor(grpc.aio.ServerInterceptor):
    """Interceptor for collecting metrics"""

    def __init__(self, service_name: str):
        self.service_name = service_name

    async def intercept_service(
        self,
        continuation: Callable,
        handler_call_details: grpc.HandlerCallDetails
    ):
        method_name = handler_call_details.method.split('/')[-1]
        start_time = time.time()

        # Wrap service handler
        service = await continuation(handler_call_details)
        if service is None:
            return service

        async def wrapped_method(request, context):
            try:
                # Increment request count
                GRPC_REQUEST_COUNT.labels(
                    service=self.service_name,
                    method=method_name,
                    status_code='OK'
                ).inc()

                # Call service method
                response = await service.unary_unary(request, context)

                # Record latency
                latency = time.time() - start_time
                GRPC_REQUEST_LATENCY.labels(
                    service=self.service_name,
                    method=method_name
                ).observe(latency)

                return response

            except AioRpcError as e:
                # Record error
                GRPC_REQUEST_COUNT.labels(
                    service=self.service_name,
                    method=method_name,
                    status_code=str(e.code())
                ).inc()
                raise
            except Exception as e:
                GRPC_REQUEST_COUNT.labels(
                    service=self.service_name,
                    method=method_name,
                    status_code='INTERNAL'
                ).inc()
                raise

        return grpc.aio.unary_unary_rpc_method_handler(wrapped_method)

class TracingInterceptor(grpc.aio.ServerInterceptor):
    """Interceptor for OpenTelemetry tracing"""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.tracer = trace.get_tracer(service_name)

    async def intercept_service(
        self,
        continuation: Callable,
        handler_call_details: grpc.HandlerDetails
    ):
        method_name = handler_call_details.method.split('/')[-1]
        span_name = f"{self.service_name}/{method_name}"

        # Create span
        span = self.tracer.start_span(span_name)

        # Wrap service handler
        service = await continuation(handler_call_details)
        if service is None:
            span.end()
            return service

        async def wrapped_method(request, context):
            try:
                # Add metadata to span
                span.set_attribute("grpc.method", method_name)
                span.set_attribute("grpc.service", self.service_name)

                # Call service method
                response = await service.unary_unary(request, context)

                # Set success status
                span.set_status(Status(StatusCode.OK))
                return response

            except AioRpcError as e:
                # Set error status
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("error", True)
                span.set_attribute("grpc.status_code", str(e.code()))
                raise
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("error", True)
                raise
            finally:
                span.end()

        return grpc.aio.unary_unary_rpc_method_handler(wrapped_method)

class OptimizedGrpcServer:
    """High-performance gRPC server with optimizations"""

    def __init__(self, config: GrpcServiceConfig):
        self.config = config
        self.server = None
        self.interceptors = []
        self.services = []
        self.connection_count = 0

    def add_interceptor(self, interceptor: grpc.aio.ServerInterceptor):
        """Add custom interceptor"""
        self.interceptors.append(interceptor)

    def add_service(self, service):
        """Add service to server"""
        self.services.append(service)

    async def start(self):
        """Start gRPC server"""
        # Create server with options
        options = [
            ('grpc.max_send_message_length', self.config.max_message_length),
            ('grpc.max_receive_message_length', self.config.max_message_length),
            ('grpc.keepalive_time_ms', self.config.keepalive_time * 1000),
            ('grpc.keepalive_timeout_ms', self.config.keepalive_timeout * 1000),
            ('grpc.keepalive_permit_without_calls', 1 if self.config.keepalive_permit_without_calls else 0),
            ('grpc.http2.min_time_between_pings_ms', 10000),
            ('grpc.http2.max_pings_without_data', 0),
            ('grpc.http2.min_ping_interval_without_data_ms', 300000),
        ]

        self.server = grpc.aio.server(
            options=options,
            interceptors=self._get_interceptors()
        )

        # Add services
        for service in self.services:
            self.server.add_insecure_port(f'{self.config.host}:{self.config.port}')

        # Start server
        await self.server.start()
        logger.info(f"gRPC server started on {self.config.host}:{self.config.port}")

    async def stop(self, grace: float = 1.0):
        """Stop gRPC server"""
        if self.server:
            await self.server.stop(grace)
            logger.info("gRPC server stopped")

    def _get_interceptors(self) -> List[grpc.aio.ServerInterceptor]:
        """Get all configured interceptors"""
        interceptors = []

        if self.config.enable_compression:
            interceptors.append(
                CompressionInterceptor(
                    enable_compression=True,
                    compression_level=self.config.compression_level
                )
            )

        if self.config.enable_metrics:
            interceptors.append(MetricsInterceptor(self.config.name))

        if self.config.enable_tracing:
            interceptors.append(TracingInterceptor(self.config.name))

        # Add custom interceptors
        interceptors.extend(self.interceptors)

        return interceptors

class GrpcClientPool:
    """Connection pool for gRPC clients"""

    def __init__(self, max_connections: int = 100):
        self.max_connections = max_connections
        self.connections = {}
        self.semaphore = asyncio.Semaphore(max_connections)
        self.metrics = {
            'created': 0,
            'reused': 0,
            'closed': 0
        }

    async def get_channel(self, target: str, options: Dict = None) -> grpc.aio.Channel:
        """Get gRPC channel from pool"""
        await self.semaphore.acquire()

        # Check for existing channel
        if target in self.connections:
            channel = self.connections[target]
            if not channel.closed():
                self.metrics['reused'] += 1
                return channel
            else:
                del self.connections[target]

        # Create new channel
        channel_options = {
            'grpc.max_send_message_length': 4 * 1024 * 1024,
            'grpc.max_receive_message_length': 4 * 1024 * 1024,
            'grpc.keepalive_time_ms': 30000,
            'grpc.keepalive_timeout_ms': 5000,
        }
        if options:
            channel_options.update(options)

        channel = grpc.aio.insecure_channel(target, options=channel_options)
        self.connections[target] = channel
        self.metrics['created'] += 1
        GRPC_ACTIVE_CONNECTIONS.labels(service=target).inc()

        return channel

    async def release_channel(self, target: str):
        """Release channel back to pool"""
        self.semaphore.release()

    async def close_all(self):
        """Close all channels"""
        for target, channel in self.connections.items():
            await channel.close()
            GRPC_ACTIVE_CONNECTIONS.labels(service=target).dec()
        self.connections.clear()
        self.metrics['closed'] += len(self.connections)

# Global client pool
grpc_client_pool = GrpcClientPool()

class OptimizedGrpcClient:
    """High-performance gRPC client with optimizations"""

    def __init__(self, service_name: str, target: str):
        self.service_name = service_name
        self.target = target
        self.channel = None
        self.stub = None
        self.timeout = 30.0

    async def connect(self):
        """Connect to gRPC server"""
        self.channel = await grpc_client_pool.get_channel(self.target)
        # Stub will be set by specific client implementation

    async def disconnect(self):
        """Disconnect from server"""
        if self.channel:
            await grpc_client_pool.release_channel(self.target)
            self.channel = None

    @asynccontextmanager
    async def call_context(self):
        """Context manager for gRPC calls"""
        await self.connect()
        try:
            yield self
        finally:
            await self.disconnect()

    async def unary_unary(self, method: str, request, timeout: float = None):
        """Make unary-unary call with optimization"""
        start_time = time.time()
        timeout = timeout or self.timeout

        try:
            # Make call
            response = await getattr(self.stub, method)(request, timeout=timeout)

            # Record metrics
            latency = time.time() - start_time
            GRPC_REQUEST_LATENCY.labels(
                service=self.service_name,
                method=method
            ).observe(latency)

            return response

        except AioRpcError as e:
            GRPC_REQUEST_COUNT.labels(
                service=self.service_name,
                method=method,
                status_code=str(e.code())
            ).inc()
            raise
        except Exception as e:
            GRPC_REQUEST_COUNT.labels(
                service=self.service_name,
                method=method,
                status_code='INTERNAL'
            ).inc()
            raise

    async def unary_stream(self, method: str, request, timeout: float = None) -> AsyncIterator:
        """Make unary-stream call"""
        timeout = timeout or self.timeout

        try:
            response_stream = await getattr(self.stub, method)(request, timeout=timeout)
            async for response in response_stream:
                yield response

        except AioRpcError as e:
            logger.error(f"Stream error: {e}")
            raise

    async def stream_unary(self, method: str, request_iterator: AsyncIterator, timeout: float = None):
        """Make stream-unary call"""
        timeout = timeout or self.timeout

        try:
            response = await getattr(self.stub, method)(request_iterator, timeout=timeout)
            return response

        except AioRpcError as e:
            logger.error(f"Stream error: {e}")
            raise

    async def stream_stream(self, method: str, request_iterator: AsyncIterator, timeout: float = None) -> AsyncIterator:
        """Make stream-stream call"""
        timeout = timeout or self.timeout

        try:
            response_stream = await getattr(self.stub, method)(request_iterator, timeout=timeout)
            async for response in response_stream:
                yield response

        except AioRpcError as e:
            logger.error(f"Stream error: {e}")
            raise

class GrpcMessageSerializer:
    """Optimized message serialization for gRPC"""

    def __init__(self, format: str = "msgpack"):
        self.format = format
        if format == "msgpack":
            self.serializer = msgpack
        elif format == "orjson":
            self.serializer = orjson
        else:
            self.serializer = None

    def serialize(self, data: Any) -> bytes:
        """Serialize data to bytes"""
        if self.serializer:
            if self.format == "msgpack":
                return self.serializer.packb(data, use_bin_type=True)
            else:
                return self.serializer.dumps(data)
        return str(data).encode()

    def deserialize(self, data: bytes, type_hint: type = None):
        """Deserialize bytes to data"""
        if self.serializer:
            if self.format == "msgpack":
                return self.serializer.unpackb(data, raw=False)
            else:
                return self.serializer.loads(data)
        return data.decode()

# Utility functions
def create_grpc_server(config: GrpcServiceConfig) -> OptimizedGrpcServer:
    """Create optimized gRPC server"""
    return OptimizedGrpcServer(config)

async def create_grpc_client(
    service_name: str,
    target: str,
    stub_class: type
) -> OptimizedGrpcClient:
    """Create optimized gRPC client"""
    client = OptimizedGrpcClient(service_name, target)
    await client.connect()
    client.stub = stub_class(client.channel)
    return client

# Exception classes
class GrpcError(Exception):
    """Base gRPC error"""
    pass

class GrpcConnectionError(GrpcError):
    """gRPC connection error"""
    pass

class GrpcTimeoutError(GrpcError):
    """gRPC timeout error"""
    pass

# Example usage
async def example_grpc_service():
    """Example of optimized gRPC service"""

    # Define service config
    config = GrpcServiceConfig(
        name="patient_service",
        host="0.0.0.0",
        port=50051,
        max_workers=10,
        enable_compression=True,
        enable_metrics=True,
        enable_tracing=True
    )

    # Create server
    server = create_grpc_server(config)

    # Add service
    # server.add_service(PatientServiceServicer())

    # Start server
    await server.start()

    # Keep running
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        await server.stop()