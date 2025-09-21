"""
Advanced Circuit Breakers and Fault Tolerance Patterns
Implementing sophisticated circuit breakers with health checks and recovery strategies
"""

import asyncio
import time
import random
import logging
from typing import Any, Dict, List, Optional, Callable, Awaitable, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import prometheus_client as prom

logger = logging.getLogger(__name__)

# Metrics
CIRCUIT_BREAKER_STATE = prom.Gauge(
    'circuit_breaker_state',
    'Current circuit breaker state',
    ['name', 'service']
)

CIRCUIT_BREAKER_FAILURES = prom.Counter(
    'circuit_breaker_failures_total',
    'Total circuit breaker failures',
    ['name', 'service', 'state']
)

CIRCUIT_BREAKER_SUCCESSES = prom.Counter(
    'circuit_breaker_successes_total',
    'Total circuit breaker successes',
    ['name', 'service']
)

CIRCUIT_BREAKER_TIMEOUTS = prom.Counter(
    'circuit_breaker_timeouts_total',
    'Total circuit breaker timeouts',
    ['name', 'service']
)

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    name: str
    service: str
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    expected_exception: tuple = (Exception,)
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 0.1
    half_open_max_calls: int = 3
    enable_metrics: bool = True
    fallback_function: Optional[Callable] = None

class CallMetrics:
    """Track call statistics for adaptive behavior"""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.call_times = deque(maxlen=window_size)
        self.failures = deque(maxlen=window_size)
        self.successes = deque(maxlen=window_size)
        self.timeouts = deque(maxlen=window_size)

    def record_success(self, duration: float):
        """Record successful call"""
        self.call_times.append(time.time())
        self.successes.append(time.time())

    def record_failure(self):
        """Record failed call"""
        self.call_times.append(time.time())
        self.failures.append(time.time())

    def record_timeout(self):
        """Record timeout"""
        self.call_times.append(time.time())
        self.timeouts.append(time.time())

    def get_failure_rate(self) -> float:
        """Calculate failure rate in window"""
        if not self.call_times:
            return 0.0

        recent_failures = len([
            t for t in self.failures
            if time.time() - t <= 60  # Last 60 seconds
        ])

        recent_calls = len([
            t for t in self.call_times
            if time.time() - t <= 60
        ])

        return recent_failures / recent_calls if recent_calls > 0 else 0.0

    def get_avg_response_time(self) -> float:
        """Get average response time"""
        if len(self.call_times) < 2:
            return 0.0

        intervals = []
        for i in range(1, len(self.call_times)):
            interval = self.call_times[i] - self.call_times[i-1]
            intervals.append(interval)

        return sum(intervals) / len(intervals) if intervals else 0.0

class AdaptiveCircuitBreaker:
    """Adaptive circuit breaker with dynamic thresholds"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.metrics = CallMetrics()
        self.lock = asyncio.Lock()
        self.dynamic_threshold = config.failure_threshold

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        async with self.lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    logger.info(f"Circuit breaker {self.config.name} moving to HALF_OPEN")
                else:
                    await self._record_call("failure")
                    raise CircuitOpenError(f"Circuit {self.config.name} is open")

        # Execute with retries
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                # Set timeout
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self.config.timeout
                )

                # Success
                await self._on_success()
                return result

            except asyncio.TimeoutError:
                last_error = CircuitTimeoutError("Call timed out")
                await self._record_call("timeout")

            except self.config.expected_exception as e:
                last_error = e
                await self._record_call("failure")

            except Exception as e:
                last_error = e
                await self._record_call("failure")

            # Retry delay with exponential backoff
            if attempt < self.config.max_retries - 1:
                delay = self.config.retry_delay * (2 ** attempt)
                await asyncio.sleep(delay + random.uniform(0, delay * 0.1))

        # All attempts failed
        if self.config.fallback_function:
            try:
                result = await self.config.fallback_function(*args, **kwargs)
                logger.info(f"Fallback function executed for {self.config.name}")
                return result
            except Exception as fallback_error:
                logger.error(f"Fallback function failed: {fallback_error}")

        raise last_error or CircuitBreakerError("Unknown error occurred")

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset"""
        return time.time() - self.last_failure_time > self.config.recovery_timeout

    async def _on_success(self):
        """Handle successful call"""
        async with self.lock:
            self.failure_count = 0
            self.success_count += 1

            if self.state == CircuitState.HALF_OPEN:
                self.half_open_calls += 1
                if self.half_open_calls >= self.config.half_open_max_calls:
                    self.state = CircuitState.CLOSED
                    logger.info(f"Circuit breaker {self.config.name} moved to CLOSED")

            await self._record_call("success")

    async def _record_call(self, result_type: str):
        """Record call result and update metrics"""
        current_time = time.time()

        if result_type == "success":
            self.metrics.record_success(0)
            CIRCUIT_BREAKER_SUCCESSES.labels(
                name=self.config.name,
                service=self.config.service
            ).inc()
        elif result_type == "failure":
            self.failure_count += 1
            self.last_failure_time = current_time
            self.metrics.record_failure()
            CIRCUIT_BREAKER_FAILURES.labels(
                name=self.config.name,
                service=self.config.service,
                state=self.state.value
            ).inc()

            # Check if should open circuit
            if self.state == CircuitState.CLOSED and self.failure_count >= self.dynamic_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker {self.config.name} opened after {self.failure_count} failures")
        elif result_type == "timeout":
            self.metrics.record_timeout()
            CIRCUIT_BREAKER_TIMEOUTS.labels(
                name=self.config.name,
                service=self.config.service
            ).inc()

        # Update metrics
        if self.config.enable_metrics:
            CIRCUIT_BREAKER_STATE.labels(
                name=self.config.name,
                service=self.config.service
            ).set(int(self.state.value))

        # Adapt threshold based on metrics
        self._adapt_threshold()

    def _adapt_threshold(self):
        """Dynamically adjust threshold based on metrics"""
        failure_rate = self.metrics.get_failure_rate()
        avg_response_time = self.metrics.get_avg_response_time()

        # Adjust threshold based on failure rate
        if failure_rate > 0.5:  # More than 50% failure rate
            self.dynamic_threshold = max(1, int(self.config.failure_threshold * 0.5))
        elif failure_rate < 0.1:  # Less than 10% failure rate
            self.dynamic_threshold = int(self.config.failure_threshold * 1.5)
        else:
            self.dynamic_threshold = self.config.failure_threshold

    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'last_failure_time': self.last_failure_time,
            'dynamic_threshold': self.dynamic_threshold,
            'failure_rate': self.metrics.get_failure_rate(),
            'avg_response_time': self.metrics.get_avg_response_time()
        }

class Bulkhead:
    """Bulkhead pattern for fault isolation"""

    def __init__(self, max_concurrent_calls: int, max_queue_size: int = 100):
        self.semaphore = asyncio.Semaphore(max_concurrent_calls)
        self.queue = asyncio.Queue(maxsize=max_queue_size)
        self.metrics = {
            'accepted': 0,
            'rejected': 0,
            'executing': 0,
            'queued': 0
        }

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with bulkhead protection"""
        # Check if we can accept the call
        if self.semaphore.locked() and self.queue.full():
            self.metrics['rejected'] += 1
            raise BulkheadFullError("Bulkhead queue is full")

        # Add to queue if semaphore is locked
        if self.semaphore.locked():
            await self.queue.put(None)
            self.metrics['queued'] += 1

        # Acquire semaphore
        async with self.semaphore:
            # Remove from queue
            if not self.queue.empty():
                self.queue.get_nowait()

            self.metrics['executing'] += 1
            try:
                return await func(*args, **kwargs)
            finally:
                self.metrics['executing'] -= 1

    def get_stats(self) -> Dict[str, int]:
        """Get bulkhead statistics"""
        return {
            'accepted': self.metrics['accepted'],
            'rejected': self.metrics['rejected'],
            'executing': self.metrics['executing'],
            'queued': self.metrics['queued'],
            'queue_size': self.queue.qsize(),
            'semaphore_locked': self.semaphore.locked()
        }

class RetryPolicy:
    """Retry policy configuration"""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 0.1,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: tuple = (Exception,)
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry policy"""
        last_error = None

        for attempt in range(self.max_attempts):
            try:
                return await func(*args, **kwargs)

            except self.retryable_exceptions as e:
                last_error = e

                if attempt < self.max_attempts - 1:
                    # Calculate delay
                    delay = self.base_delay * (self.exponential_base ** attempt)
                    delay = min(delay, self.max_delay)

                    # Add jitter
                    if self.jitter:
                        delay = delay * (0.5 + random.random() * 0.5)

                    logger.debug(f"Retry attempt {attempt + 1}/{self.max_attempts} after {delay:.2f}s")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All retry attempts exhausted for {func.__name__}")

        raise last_error or RetryExhaustedError("Retry attempts exhausted")

class Timeout:
    """Timeout protection for operations"""

    def __init__(self, timeout: float):
        self.timeout = timeout

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with timeout"""
        try:
            return await asyncio.wait_for(func(*args, **kwargs), timeout=self.timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Operation timed out after {self.timeout}s")

class FaultToleranceDecorator:
    """Decorator for applying fault tolerance patterns"""

    def __init__(
        self,
        circuit_breaker: Optional[AdaptiveCircuitBreaker] = None,
        bulkhead: Optional[Bulkhead] = None,
        retry_policy: Optional[RetryPolicy] = None,
        timeout: Optional[Timeout] = None
    ):
        self.circuit_breaker = circuit_breaker
        self.bulkhead = bulkhead
        self.retry_policy = retry_policy
        self.timeout = timeout

    def __call__(self, func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # Apply fault tolerance patterns in order

            # 1. Circuit breaker
            if self.circuit_breaker:
                func = partial(self.circuit_breaker.call, func)

            # 2. Bulkhead
            if self.bulkhead:
                func = partial(self.bulkhead.execute, func)

            # 3. Timeout
            if self.timeout:
                func = partial(self.timeout.execute, func)

            # 4. Retry
            if self.retry_policy:
                func = partial(self.retry_policy.execute, func)

            return await func(*args, **kwargs)

        return wrapper

# Factory functions
def create_circuit_breaker(
    name: str,
    service: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    **kwargs
) -> AdaptiveCircuitBreaker:
    """Create circuit breaker with configuration"""
    config = CircuitBreakerConfig(
        name=name,
        service=service,
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        **kwargs
    )
    return AdaptiveCircuitBreaker(config)

def create_bulkhead(
    max_concurrent_calls: int,
    max_queue_size: int = 100
) -> Bulkhead:
    """Create bulkhead"""
    return Bulkhead(max_concurrent_calls, max_queue_size)

def create_retry_policy(
    max_attempts: int = 3,
    base_delay: float = 0.1,
    **kwargs
) -> RetryPolicy:
    """Create retry policy"""
    return RetryPolicy(max_attempts, base_delay, **kwargs)

def create_timeout(timeout: float) -> Timeout:
    """Create timeout"""
    return Timeout(timeout)

# Decorators
def circuit_breaker(
    name: str,
    service: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    **kwargs
):
    """Circuit breaker decorator"""
    cb = create_circuit_breaker(name, service, failure_threshold, recovery_timeout, **kwargs)
    def decorator(func):
        return FaultToleranceDecorator(circuit_breaker=cb)(func)
    return decorator

def bulkhead(max_concurrent_calls: int, max_queue_size: int = 100):
    """Bulkhead decorator"""
    bh = create_bulkhead(max_concurrent_calls, max_queue_size)
    def decorator(func):
        return FaultToleranceDecorator(bulkhead=bh)(func)
    return decorator

def retry(max_attempts: int = 3, base_delay: float = 0.1, **kwargs):
    """Retry decorator"""
    rp = create_retry_policy(max_attempts, base_delay, **kwargs)
    def decorator(func):
        return FaultToleranceDecorator(retry_policy=rp)(func)
    return decorator

def timeout(timeout: float):
    """Timeout decorator"""
    t = create_timeout(timeout)
    def decorator(func):
        return FaultToleranceDecorator(timeout=t)(func)
    return decorator

# Exception classes
class CircuitBreakerError(Exception):
    """Base circuit breaker error"""
    pass

class CircuitOpenError(CircuitBreakerError):
    """Circuit is open"""
    pass

class BulkheadFullError(Exception):
    """Bulkhead queue is full"""
    pass

class RetryExhaustedError(Exception):
    """Retry attempts exhausted"""
    pass

# Example usage
async def example_usage():
    """Example of fault tolerance patterns"""

    # Create circuit breaker
    patient_circuit = create_circuit_breaker(
        name="patient_service",
        service="patients",
        failure_threshold=5,
        recovery_timeout=60
    )

    # Create bulkhead
    api_bulkhead = create_bulkhead(
        max_concurrent_calls=10,
        max_queue_size=50
    )

    # Decorate function
    @circuit_breaker("payment_service", "payments", failure_threshold=3)
    @bulkhead(5, 20)
    @retry(max_attempts=3, base_delay=0.1)
    @timeout(30.0)
    async def process_payment(amount: float, user_id: str):
        # Simulate payment processing
        await asyncio.sleep(random.uniform(0.1, 1.0))
        if random.random() < 0.1:  # 10% failure rate
            raise ValueError("Payment failed")
        return {"status": "success", "amount": amount}

    # Use the protected function
    try:
        result = await process_payment(100.0, "user123")
        print(f"Payment result: {result}")
    except Exception as e:
        print(f"Payment failed: {e}")

    # Get circuit breaker state
    state = patient_circuit.get_state()
    print(f"Circuit breaker state: {state}")