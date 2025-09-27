"""
Microservice Communication Optimization Utilities
High-performance inter-service communication with minimal latency
"""

import asyncio
import json
import logging
import pickle
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from functools import partial, wraps
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

import aiohttp
import aiohttp.web
import msgpack
import orjson
import prometheus_client as prom
import redis
import snappy
from django_redis import get_redis_connection

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Prometheus metrics
COMMUNICATION_LATENCY = prom.Histogram(
    "service_communication_latency_seconds",
    "Service communication latency",
    ["source_service", "target_service", "method", "status"],
)

ACTIVE_CONNECTIONS = prom.Gauge(
    "service_active_connections", "Active connections to services", ["service"]
)

ERROR_RATE = prom.Counter(
    "service_communication_errors",
    "Service communication errors",
    ["source_service", "target_service", "error_type"],
)


@dataclass
class ServiceConfig:
    """Configuration for a microservice"""

    name: str
    host: str
    port: int
    version: str
    protocol: str = "http"
    timeout: float = 30.0
    max_connections: int = 100
    connection_pool_size: int = 20
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    enable_compression: bool = True
    enable_metrics: bool = True
    cache_ttl: int = 300
    retry_attempts: int = 3
    retry_backoff: float = 0.1


@dataclass
class CircuitBreaker:
    """Circuit breaker for fault tolerance"""

    failure_count: int = 0
    last_failure_time: float = 0
    state: str = "closed"  # closed, open, half-open
    threshold: int = 5
    timeout: int = 60

    def record_success(self):
        """Record a successful call"""
        if self.state == "half-open":
            self.state = "closed"
        self.failure_count = 0

    def record_failure(self):
        """Record a failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.threshold:
            self.state = "open"

    def allow_request(self) -> bool:
        """Check if request is allowed"""
        if self.state == "closed":
            return True
        elif self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half-open"
                return True
            return False
        else:  # half-open
            return True


class ConnectionPool:
    """Optimized connection pool for microservice communication"""

    def __init__(self, config: ServiceConfig):
        self.config = config
        self.pool = {}
        self.semaphore = asyncio.Semaphore(config.max_connections)
        self.metrics = {
            "total_connections": 0,
            "active_connections": 0,
            "failed_connections": 0,
            "pool_hits": 0,
            "pool_misses": 0,
        }

    async def get_connection(self) -> aiohttp.ClientSession:
        """Get a connection from the pool"""
        await self.semaphore.acquire()

        # Check for available connection
        session = self.pool.get(self.config.name)
        if not session or session.closed:
            # Create new connection
            connector = aiohttp.TCPConnector(
                limit=self.config.connection_pool_size,
                limit_per_host=self.config.connection_pool_size,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True,
            )

            timeout = aiohttp.ClientTimeout(
                total=self.config.timeout, connect=10, sock_read=30
            )

            session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                json_serialize=lambda x: orjson.dumps(x).decode(),
            )

            self.pool[self.config.name] = session
            self.metrics["pool_misses"] += 1
            self.metrics["total_connections"] += 1
        else:
            self.metrics["pool_hits"] += 1

        self.metrics["active_connections"] += 1
        ACTIVE_CONNECTIONS.labels(service=self.config.name).inc()

        return session

    async def release_connection(self):
        """Release connection back to pool"""
        self.semaphore.release()
        self.metrics["active_connections"] -= 1
        ACTIVE_CONNECTIONS.labels(service=self.config.name).dec()


class ServiceCommunicator:
    """High-performance service communication with optimization"""

    def __init__(self, config: ServiceConfig):
        self.config = config
        self.connection_pool = ConnectionPool(config)
        self.circuit_breaker = CircuitBreaker(
            threshold=config.circuit_breaker_threshold,
            timeout=config.circuit_breaker_timeout,
        )
        self.cache = get_redis_connection("default") if settings.USE_REDIS else cache
        self.compressor = snappy if config.enable_compression else None
        self.serializer = self._get_best_serializer()

    def _get_best_serializer(self):
        """Get the best available serializer"""
        try:
            import msgpack

            return {
                "serialize": msgpack.packb,
                "deserialize": msgpack.unpackb,
                "format": "msgpack",
            }
        except ImportError:
            try:
                import orjson

                return {
                    "serialize": orjson.dumps,
                    "deserialize": orjson.loads,
                    "format": "json",
                }
            except ImportError:
                return {
                    "serialize": json.dumps,
                    "deserialize": json.loads,
                    "format": "json",
                }

    async def request(
        self,
        method: str,
        endpoint: str,
        data: Any = None,
        params: Dict = None,
        headers: Dict = None,
        cache_key: str = None,
        retry_on_failure: bool = True,
    ) -> Dict[str, Any]:
        """Make optimized request to service"""
        start_time = time.time()

        # Check circuit breaker
        if not self.circuit_breaker.allow_request():
            logger.warning(f"Circuit breaker open for {self.config.name}")
            raise ServiceUnavailableError(f"Service {self.config.name} is unavailable")

        # Check cache if applicable
        if cache_key and method.upper() == "GET":
            cached_response = await self._get_from_cache(cache_key)
            if cached_response:
                return cached_response

        # Prepare request
        url = (
            f"{self.config.protocol}://{self.config.host}:{self.config.port}{endpoint}"
        )

        # Serialize and compress data
        if data is not None:
            if self.compressor:
                data = self.compressor.compress(self.serializer["serialize"](data))
                headers = headers or {}
                headers["Content-Encoding"] = "snappy"
            else:
                data = self.serializer["serialize"](data)

        # Make request with retry logic
        last_error = None
        for attempt in range(self.config.retry_attempts if retry_on_failure else 1):
            try:
                session = await self.connection_pool.get_connection()

                async with session.request(
                    method, url, data=data, params=params, headers=headers
                ) as response:

                    # Read response
                    if response.headers.get("Content-Encoding") == "snappy":
                        content = await response.read()
                        if self.compressor:
                            content = self.compressor.decompress(content)
                        data = self.serializer["deserialize"](content)
                    else:
                        data = await response.json()

                    # Update metrics
                    latency = time.time() - start_time
                    COMMUNICATION_LATENCY.labels(
                        source_service="client",
                        target_service=self.config.name,
                        method=method,
                        status=response.status,
                    ).observe(latency)

                    # Handle response
                    if response.status == 200:
                        self.circuit_breaker.record_success()

                        # Cache response if applicable
                        if cache_key and method.upper() == "GET":
                            await self._cache_response(cache_key, data)

                        return {
                            "status": "success",
                            "data": data,
                            "latency": latency,
                            "cached": False,
                        }
                    else:
                        raise ServiceError(f"Service returned status {response.status}")

            except Exception as e:
                last_error = e
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_backoff * (2**attempt))
                continue
            finally:
                await self.connection_pool.release_connection()

        # All attempts failed
        self.circuit_breaker.record_failure()
        ERROR_RATE.labels(
            source_service="client",
            target_service=self.config.name,
            error_type=type(last_error).__name__,
        ).inc()

        raise last_error or ServiceError("Unknown error occurred")

    async def _get_from_cache(self, key: str) -> Optional[Dict]:
        """Get response from cache"""
        try:
            if isinstance(self.cache, redis.Redis):
                cached = self.cache.get(key)
                if cached:
                    return self.serializer["deserialize"](cached)
            else:
                return self.cache.get(key)
        except Exception as e:
            logger.error(f"Cache error: {e}")
        return None

    async def _cache_response(self, key: str, data: Dict):
        """Cache response"""
        try:
            if isinstance(self.cache, redis.Redis):
                self.cache.setex(
                    key, self.config.cache_ttl, self.serializer["serialize"](data)
                )
            else:
                self.cache.set(key, data, self.config.cache_ttl)
        except Exception as e:
            logger.error(f"Cache error: {e}")

    @asynccontextmanager
    async def stream(self, endpoint: str, method: str = "GET"):
        """Stream response from service"""
        session = await self.connection_pool.get_connection()
        try:
            url = f"{self.config.protocol}://{self.config.host}:{self.config.port}{endpoint}"

            async with session.request(method, url) as response:
                if response.status != 200:
                    raise ServiceError(f"Stream error: {response.status}")

                async for chunk in response.content.iter_chunked(8192):
                    yield chunk

        finally:
            await self.connection_pool.release_connection()


class ServiceBus:
    """High-performance message bus for async communication"""

    def __init__(self):
        self.subscribers = {}
        self.topics = {}
        self.message_queue = asyncio.Queue(maxsize=10000)
        self.processors = {}
        self.metrics = {
            "messages_published": 0,
            "messages_delivered": 0,
            "processing_errors": 0,
        }

    def subscribe(self, topic: str, callback: Callable[[Dict], Awaitable[None]]):
        """Subscribe to a topic"""
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(callback)

        # Start processor if not running
        if topic not in self.processors:
            self.processors[topic] = asyncio.create_task(self._process_messages(topic))

    async def publish(self, topic: str, message: Dict):
        """Publish message to topic"""
        self.metrics["messages_published"] += 1

        # Add timestamp
        message["_timestamp"] = time.time()
        message["_topic"] = topic

        # Queue message
        await self.message_queue.put((topic, message))

    async def _process_messages(self, topic: str):
        """Process messages for a topic"""
        while True:
            try:
                # Get message from queue
                topic, message = await self.message_queue.get()

                # Deliver to subscribers
                if topic in self.subscribers:
                    tasks = []
                    for callback in self.subscribers[topic]:
                        task = asyncio.create_task(callback(message))
                        tasks.append(task)

                    # Wait for all subscribers
                    if tasks:
                        results = await asyncio.gather(*tasks, return_exceptions=True)

                        # Handle errors
                        for i, result in enumerate(results):
                            if isinstance(result, Exception):
                                logger.error(f"Subscriber error: {result}")
                                self.metrics["processing_errors"] += 1
                            else:
                                self.metrics["messages_delivered"] += 1

                self.message_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Message processing error: {e}")
                self.metrics["processing_errors"] += 1

    async def request_response(
        self, target_service: str, method: str, data: Dict, timeout: float = 30.0
    ) -> Dict:
        """Request-response pattern via message bus"""
        # Create unique correlation ID
        correlation_id = f"{target_service}_{time.time()}_{id(self)}"

        # Create response queue
        response_queue = asyncio.Queue()

        # Subscribe for response
        def response_handler(message):
            if message.get("_correlation_id") == correlation_id:
                response_queue.put_nowait(message)

        self.subscribe(f"{target_service}_response", response_handler)

        # Send request
        await self.publish(
            f"{target_service}_request",
            {"_correlation_id": correlation_id, "method": method, "data": data},
        )

        # Wait for response
        try:
            response = await asyncio.wait_for(response_queue.get(), timeout=timeout)
            return response.get("data", {})
        except asyncio.TimeoutError:
            raise TimeoutError(f"Request to {target_service} timed out")


class ServiceRegistry:
    """Dynamic service registry with health checks"""

    def __init__(self):
        self.services = {}
        self.health_status = {}
        self.load_balancer = RoundRobinLoadBalancer()

    def register(self, config: ServiceConfig):
        """Register a service"""
        self.services[config.name] = config
        self.health_status[config.name] = {
            "status": "healthy",
            "last_check": time.time(),
            "response_time": 0,
        }
        self.load_balancer.add_service(config.name)

    def discover(self, service_name: str) -> Optional[ServiceConfig]:
        """Discover service instances"""
        # Check health status
        if service_name in self.health_status:
            status = self.health_status[service_name]
            if status["status"] == "unhealthy":
                return None

        return self.services.get(service_name)

    async def health_check(self, service_name: str) -> bool:
        """Perform health check on service"""
        config = self.services.get(service_name)
        if not config:
            return False

        try:
            start_time = time.time()
            # Simple health check endpoint
            url = f"{config.protocol}://{config.host}:{config.port}/health/"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        response_time = time.time() - start_time
                        self.health_status[service_name] = {
                            "status": "healthy",
                            "last_check": time.time(),
                            "response_time": response_time,
                        }
                        return True
        except:
            pass

        # Service is unhealthy
        self.health_status[service_name] = {
            "status": "unhealthy",
            "last_check": time.time(),
            "response_time": 0,
        }
        return False


class LoadBalancer:
    """Base class for load balancing strategies"""

    def __init__(self):
        self.services = []
        self.index = 0

    def add_service(self, service_name: str):
        """Add service to load balancer"""
        if service_name not in self.services:
            self.services.append(service_name)

    def remove_service(self, service_name: str):
        """Remove service from load balancer"""
        if service_name in self.services:
            self.services.remove(service_name)

    def get_next(self) -> Optional[str]:
        """Get next service instance"""
        raise NotImplementedError


class RoundRobinLoadBalancer(LoadBalancer):
    """Round-robin load balancing"""

    def get_next(self) -> Optional[str]:
        if not self.services:
            return None

        service = self.services[self.index]
        self.index = (self.index + 1) % len(self.services)
        return service


class WeightedRoundRobinLoadBalancer(LoadBalancer):
    """Weighted round-robin load balancing"""

    def __init__(self):
        super().__init__()
        self.weights = {}
        self.current_weights = {}

    def set_weight(self, service_name: str, weight: int):
        """Set weight for service"""
        self.weights[service_name] = weight
        self.current_weights[service_name] = 0

    def get_next(self) -> Optional[str]:
        if not self.services:
            return None

        # Find service with highest current weight
        best_service = None
        best_weight = -1

        for service in self.services:
            weight = self.weights.get(service, 1)
            self.current_weights[service] += weight

            if self.current_weights[service] > best_weight:
                best_weight = self.current_weights[service]
                best_service = service

        # Decrease selected service's weight
        if best_service:
            total_weight = sum(self.weights.get(s, 1) for s in self.services)
            self.current_weights[best_service] -= total_weight

        return best_service


# Global instances
service_registry = ServiceRegistry()
service_bus = ServiceBus()
communicators = {}


def get_communicator(service_name: str) -> ServiceCommunicator:
    """Get or create service communicator"""
    if service_name not in communicators:
        config = service_registry.discover(service_name)
        if config:
            communicators[service_name] = ServiceCommunicator(config)
        else:
            raise ServiceNotFoundError(f"Service {service_name} not found")
    return communicators[service_name]


async def call_service(
    service_name: str, method: str, endpoint: str, data: Any = None, **kwargs
) -> Dict:
    """Convenience function for service calls"""
    communicator = get_communicator(service_name)
    return await communicator.request(method, endpoint, data, **kwargs)


# Exception classes
class ServiceError(Exception):
    """Base service communication error"""

    pass


class ServiceUnavailableError(ServiceError):
    """Service is unavailable"""

    pass


class ServiceTimeoutError(ServiceError):
    """Service call timed out"""

    pass


class ServiceNotFoundError(ServiceError):
    """Service not found in registry"""

    pass
