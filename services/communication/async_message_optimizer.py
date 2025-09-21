"""
Asynchronous Message Optimization for Microservices
High-performance message queue implementation with various backends
"""

import asyncio
import json
import time
import logging
from typing import Any, Dict, List, Optional, Callable, Awaitable, Union
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager
import aiohttp
import aiohttp.web
import orjson
import msgpack
import pickle
import zlib
import snappy
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
import redis.asyncio as aioredis
from redis.exceptions import RedisError
import prometheus_client as prom

logger = logging.getLogger(__name__)

# Metrics
MESSAGE_QUEUE_SIZE = prom.Gauge(
    'message_queue_size',
    'Current message queue size',
    ['queue_name', 'service']
)

MESSAGE_PROCESSED = prom.Counter(
    'message_processed_total',
    'Total messages processed',
    ['queue_name', 'status', 'service']
)

MESSAGE_LATENCY = prom.Histogram(
    'message_processing_latency_seconds',
    'Message processing latency',
    ['queue_name', 'service']
)

class MessagePriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Message:
    """Message structure"""
    id: str
    topic: str
    data: Any
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    retry_count: int = 0
    max_retries: int = 3
    delay: float = 0.0
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    headers: Dict[str, Any] = field(default_factory=dict)

@dataclass
class QueueConfig:
    """Queue configuration"""
    name: str
    max_size: int = 10000
    retention_seconds: int = 86400  # 24 hours
    priority_levels: int = 4
    batch_size: int = 100
    batch_timeout: float = 1.0
    dead_letter_queue: Optional[str] = None
    compression: str = "snappy"  # none, gzip, snappy
    serializer: str = "orjson"  # json, orjson, msgpack, pickle
    enable_metrics: bool = True

class PriorityQueue:
    """Priority-based message queue implementation"""

    def __init__(self, config: QueueConfig):
        self.config = config
        self.queues = {
            MessagePriority.CRITICAL: asyncio.Queue(maxsize=config.max_size // 4),
            MessagePriority.HIGH: asyncio.Queue(maxsize=config.max_size // 4),
            MessagePriority.NORMAL: asyncio.Queue(maxsize=config.max_size // 2),
            MessagePriority.LOW: asyncio.Queue(maxsize=config.max_size // 4)
        }
        self.metrics = {
            'enqueued': 0,
            'dequeued': 0,
            'retries': 0,
            'dead_lettered': 0
        }

    async def put(self, message: Message):
        """Put message in queue with priority"""
        try:
            await self.queues[message.priority].put(message)
            self.metrics['enqueued'] += 1
            MESSAGE_QUEUE_SIZE.labels(
                queue_name=self.config.name,
                service=message.headers.get('source_service', 'unknown')
            ).inc()
        except asyncio.QueueFull:
            logger.error(f"Queue {self.config.name} is full")
            if self.config.dead_letter_queue:
                await self._dead_letter(message, "queue_full")
            raise QueueFullError(f"Queue {self.config.name} is full")

    async def get(self) -> Message:
        """Get highest priority message"""
        # Check queues in priority order
        for priority in [MessagePriority.CRITICAL, MessagePriority.HIGH,
                         MessagePriority.NORMAL, MessagePriority.LOW]:
            try:
                message = await self.queues[priority].get()
                self.metrics['dequeued'] += 1
                MESSAGE_QUEUE_SIZE.labels(
                    queue_name=self.config.name,
                    service=message.headers.get('source_service', 'unknown')
                ).dec()
                return message
            except asyncio.QueueEmpty:
                continue

        # All queues empty
        raise asyncio.QueueEmpty()

    async def get_batch(self, batch_size: int = None) -> List[Message]:
        """Get batch of messages"""
        batch_size = batch_size or self.config.batch_size
        messages = []
        timeout = self.config.batch_timeout

        start_time = time.time()
        while len(messages) < batch_size and (time.time() - start_time) < timeout:
            try:
                message = await asyncio.wait_for(self.get(), timeout=0.1)
                messages.append(message)
            except asyncio.TimeoutError:
                break

        return messages

    def size(self) -> int:
        """Get total queue size"""
        return sum(q.qsize() for q in self.queues.values())

    async def _dead_letter(self, message: Message, reason: str):
        """Send message to dead letter queue"""
        message.headers['dead_letter_reason'] = reason
        message.headers['dead_letter_time'] = time.time()
        self.metrics['dead_lettered'] += 1
        logger.warning(f"Message {message.id} sent to dead letter queue: {reason}")

class RedisQueueBackend:
    """Redis-based queue backend for distributed message processing"""

    def __init__(self, config: QueueConfig):
        self.config = config
        self.redis = None
        self.subscribers = {}
        self.serializers = {
            'json': (json.dumps, json.loads),
            'orjson': (orjson.dumps, orjson.loads),
            'msgpack': (msgpack.packb, msgpack.unpackb),
            'pickle': (pickle.dumps, pickle.loads)
        }
        self.compressors = {
            'none': (lambda x: x, lambda x: x),
            'gzip': (zlib.compress, zlib.decompress),
            'snappy': (snappy.compress, snappy.decompress)
        }

    async def connect(self, url: str):
        """Connect to Redis"""
        self.redis = aioredis.from_url(url, decode_responses=False)

    async def publish(self, topic: str, message: Message):
        """Publish message to topic"""
        if not self.redis:
            raise ConnectionError("Redis not connected")

        # Serialize and compress
        serialize, _ = self.serializers[self.config.serializer]
        compress, _ = self.compressors[self.config.compression]

        data = message.__dict__
        serialized = serialize(data)
        compressed = compress(serialized)

        # Publish to Redis stream
        await self.redis.xadd(
            f"stream:{topic}",
            {
                'message': compressed,
                'priority': message.priority.value,
                'timestamp': message.timestamp
            }
        )

    async def subscribe(self, topic: str, handler: Callable[[Message], Awaitable[None]]):
        """Subscribe to topic"""
        if not self.redis:
            raise ConnectionError("Redis not connected")

        # Create consumer group
        try:
            await self.redis.xgroup_create(
                f"stream:{topic}",
                "consumer_group",
                id="0",
                mkstream=True
            )
        except aioredis.ResponseError:
            # Group already exists
            pass

        # Start consuming
        while True:
            try:
                # Read messages
                messages = await self.redis.xreadgroup(
                    "consumer_group",
                    f"consumer_{time.time()}",
                    {f"stream:{topic}": ">"},
                    count=self.config.batch_size,
                    block=1000
                )

                # Process messages
                for stream, msgs in messages:
                    _, decompress = self.compressors[self.config.compression]
                    _, deserialize = self.serializers[self.config.serializer]

                    for msg_id, fields in msgs:
                        try:
                            # Deserialize message
                            compressed = fields['message']
                            serialized = decompress(compressed)
                            data = deserialize(serialized)

                            # Create message object
                            message = Message(**data)
                            message.id = msg_id

                            # Process message
                            await handler(message)

                            # Acknowledge message
                            await self.redis.xack(f"stream:{topic}", "consumer_group", msg_id)

                        except Exception as e:
                            logger.error(f"Error processing message {msg_id}: {e}")
                            # Move to dead letter if max retries reached
                            if message.retry_count >= message.max_retries:
                                await self._dead_letter(message, str(e))
                            else:
                                # Retry
                                message.retry_count += 1
                                await self.redis.xack(f"stream:{topic}", "consumer_group", msg_id)
                                await asyncio.sleep(message.delay)
                                await self.publish(topic, message)

            except Exception as e:
                logger.error(f"Error in subscriber: {e}")
                await asyncio.sleep(1)

    async def _dead_letter(self, message: Message, error: str):
        """Send to dead letter queue"""
        dlq_topic = f"{self.config.name}_dlq"
        message.headers['dead_letter_reason'] = error
        message.headers['dead_letter_time'] = time.time()
        await self.publish(dlq_topic, message)

class MessageProcessor:
    """High-performance message processor with optimizations"""

    def __init__(self, queue_config: QueueConfig):
        self.queue = PriorityQueue(queue_config)
        self.handlers = {}
        self.workers = []
        self.batch_processor = None
        self.running = False
        self.metrics = {
            'processed': 0,
            'errors': 0,
            'avg_processing_time': 0
        }

    def register_handler(self, topic: str, handler: Callable[[Message], Awaitable[None]]):
        """Register message handler for topic"""
        self.handlers[topic] = handler

    async def start(self, num_workers: int = 4, enable_batch_processing: bool = True):
        """Start message processor"""
        self.running = True

        # Start individual workers
        for i in range(num_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)

        # Start batch processor if enabled
        if enable_batch_processing:
            self.batch_processor = asyncio.create_task(self._batch_worker())

        logger.info(f"Started {num_workers} workers and batch processor")

    async def stop(self):
        """Stop message processor"""
        self.running = False

        # Cancel workers
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)

        # Cancel batch processor
        if self.batch_processor:
            self.batch_processor.cancel()
            await self.batch_processor

        logger.info("Message processor stopped")

    async def _worker(self, worker_id: str):
        """Individual message worker"""
        while self.running:
            try:
                message = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                await self._process_message(message, worker_id)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                self.metrics['errors'] += 1

    async def _batch_worker(self):
        """Batch message processor"""
        while self.running:
            try:
                messages = await self.queue.get_batch()
                if messages:
                    # Group by topic for batch processing
                    topic_batches = {}
                    for msg in messages:
                        if msg.topic not in topic_batches:
                            topic_batches[msg.topic] = []
                        topic_batches[msg.topic].append(msg)

                    # Process each topic batch
                    for topic, batch in topic_batches.items():
                        await self._process_batch(topic, batch)

            except Exception as e:
                logger.error(f"Batch worker error: {e}")

    async def _process_message(self, message: Message, worker_id: str):
        """Process individual message"""
        start_time = time.time()

        try:
            # Get handler
            handler = self.handlers.get(message.topic)
            if not handler:
                logger.warning(f"No handler for topic: {message.topic}")
                return

            # Process message
            await handler(message)

            # Update metrics
            processing_time = time.time() - start_time
            self._update_metrics(processing_time)

            MESSAGE_PROCESSED.labels(
                queue_name=self.queue.config.name,
                status='success',
                service=message.headers.get('source_service', 'unknown')
            ).inc()
            MESSAGE_LATENCY.labels(
                queue_name=self.queue.config.name,
                service=message.headers.get('source_service', 'unknown')
            ).observe(processing_time)

        except Exception as e:
            logger.error(f"Error processing message {message.id}: {e}")
            self.metrics['errors'] += 1

            # Retry logic
            if message.retry_count < message.max_retries:
                message.retry_count += 1
                await asyncio.sleep(message.delay or (2 ** message.retry_count))
                await self.queue.put(message)
            else:
                # Dead letter
                await self.queue._dead_letter(message, str(e))

    async def _process_batch(self, topic: str, messages: List[Message]):
        """Process batch of messages"""
        start_time = time.time()

        try:
            handler = self.handlers.get(topic)
            if not handler:
                return

            # Call batch handler if available
            if hasattr(handler, '__batch_handler__'):
                await handler(messages)
            else:
                # Process messages in parallel
                tasks = [handler(msg) for msg in messages]
                await asyncio.gather(*tasks, return_exceptions=True)

            # Update metrics
            processing_time = time.time() - start_time
            self._update_metrics(processing_time / len(messages))

        except Exception as e:
            logger.error(f"Error processing batch for {topic}: {e}")

    def _update_metrics(self, processing_time: float):
        """Update processing metrics"""
        self.metrics['processed'] += 1

        # Calculate running average
        if self.metrics['avg_processing_time'] == 0:
            self.metrics['avg_processing_time'] = processing_time
        else:
            self.metrics['avg_processing_time'] = (
                self.metrics['avg_processing_time'] * 0.9 + processing_time * 0.1
            )

class EventSourcing:
    """Event sourcing for reliable message processing"""

    def __init__(self, storage_backend: str = "redis"):
        self.backend = storage_backend
        self.event_log = []
        self.snapshots = {}

    async def save_event(self, aggregate_id: str, event_type: str, data: Dict):
        """Save event to log"""
        event = {
            'id': f"{aggregate_id}_{len(self.event_log)}",
            'aggregate_id': aggregate_id,
            'type': event_type,
            'data': data,
            'timestamp': time.time()
        }

        if self.backend == "redis":
            # Save to Redis stream
            pass
        else:
            self.event_log.append(event)

    async def get_events(self, aggregate_id: str) -> List[Dict]:
        """Get all events for aggregate"""
        if self.backend == "redis":
            # Query Redis stream
            pass
        else:
            return [e for e in self.event_log if e['aggregate_id'] == aggregate_id]

    async def create_snapshot(self, aggregate_id: str, state: Dict):
        """Create snapshot of aggregate state"""
        self.snapshots[aggregate_id] = {
            'state': state,
            'version': len([e for e in self.event_log if e['aggregate_id'] == aggregate_id]),
            'timestamp': time.time()
        }

    async def get_state(self, aggregate_id: str) -> Dict:
        """Reconstruct state from events"""
        # Check for snapshot
        snapshot = self.snapshots.get(aggregate_id)
        if snapshot:
            state = snapshot['state']
            start_version = snapshot['version']
        else:
            state = {}
            start_version = 0

        # Apply events since snapshot
        events = await self.get_events(aggregate_id)
        for event in events[start_version:]:
            state = self._apply_event(state, event)

        return state

    def _apply_event(self, state: Dict, event: Dict) -> Dict:
        """Apply event to state"""
        # Event handlers would be defined here
        return state

# Exception classes
class QueueFullError(Exception):
    """Queue is full"""
    pass

class MessageProcessingError(Exception):
    """Error processing message"""
    pass

class ConnectionError(Exception):
    """Connection error"""
    pass

# Decorators
def message_handler(topic: str):
    """Decorator for message handlers"""
    def decorator(func):
        func.__message_handler_topic__ = topic
        return func
    return decorator

def batch_handler(topic: str):
    """Decorator for batch message handlers"""
    def decorator(func):
        func.__message_handler_topic__ = topic
        func.__batch_handler__ = True
        return func
    return decorator

# Utility functions
async def publish_message(
    topic: str,
    data: Any,
    priority: MessagePriority = MessagePriority.NORMAL,
    **kwargs
) -> str:
    """Publish message to topic"""
    message = Message(
        id=f"{topic}_{time.time()}_{id(data)}",
        topic=topic,
        data=data,
        priority=priority,
        **kwargs
    )

    # Publish via message bus or queue
    from .service_communication_optimizer import service_bus
    await service_bus.publish(topic, message.__dict__)

    return message.id

def create_message_queue(
    name: str,
    max_size: int = 10000,
    **kwargs
) -> MessageProcessor:
    """Create and configure message queue"""
    config = QueueConfig(name=name, max_size=max_size, **kwargs)
    processor = MessageProcessor(config)
    return processor