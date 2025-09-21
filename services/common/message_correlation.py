"""
Message queue correlation ID propagation utilities
Support for RabbitMQ, Kafka, Redis, and Celery
"""

import json
import logging
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager
import pika
import redis
import kafka
import kafka.errors
from celery import Celery
from celery.app.task import Task
from celery.signals import (
    before_task_publish, after_task_publish,
    task_prerun, task_postrun, task_failure
)

from .correlation_id import get_correlation_id, set_correlation_id, generate_correlation_id
from .otel_config import get_tracer

logger = logging.getLogger(__name__)

class RabbitMQCorrelationPublisher:
    """RabbitMQ publisher with correlation ID support"""

    def __init__(self, host: str = 'localhost', port: int = 5672):
        self.host = host
        self.port = port
        self.connection = None
        self.channel = None

    def connect(self):
        """Establish connection to RabbitMQ"""
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host, port=self.port)
        )
        self.channel = self.connection.channel()

    def close(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()

    def publish(
        self,
        exchange: str,
        routing_key: str,
        body: Dict[str, Any],
        correlation_id: Optional[str] = None,
        message_type: str = None
    ):
        """Publish message with correlation ID"""
        if not self.channel:
            self.connect()

        # Get or generate correlation ID
        if not correlation_id:
            correlation_id = get_correlation_id() or generate_correlation_id()

        # Prepare message headers
        headers = {
            'x-correlation-id': correlation_id,
            'message-type': message_type or 'default',
            'timestamp': str(time.time())
        }

        # Add tracing context if available
        tracer = get_tracer()
        if tracer:
            current_span = tracer.get_current_span()
            if current_span:
                headers.update({
                    'x-trace-id': current_span.context.trace_id,
                    'x-span-id': current_span.context.span_id
                })

        # Publish message
        self.channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=json.dumps(body),
            properties=pika.BasicProperties(
                headers=headers,
                correlation_id=correlation_id,
                delivery_mode=2,  # Persistent message
                message_id=str(uuid.uuid4())
            )
        )

        logger.info(f"Published message to {exchange}:{routing_key}",
                   correlation_id=correlation_id, message_id=headers['message_id'])

class RabbitMQCorrelationConsumer:
    """RabbitMQ consumer with correlation ID extraction"""

    def __init__(self, host: str = 'localhost', port: int = 5672):
        self.host = host
        self.port = port
        self.connection = None
        self.channel = None
        self.message_handlers = {}

    def connect(self):
        """Establish connection to RabbitMQ"""
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host, port=self.port)
        )
        self.channel = self.connection.channel()

    def register_handler(self, routing_key: str, handler: Callable):
        """Register message handler for routing key"""
        self.message_handlers[routing_key] = handler

    def start_consuming(self, queue: str):
        """Start consuming messages with correlation ID propagation"""
        if not self.channel:
            self.connect()

        def callback(ch, method, properties, body):
            try:
                # Extract correlation ID
                correlation_id = properties.correlation_id

                # Extract from headers if not in correlation_id
                if not correlation_id and properties.headers:
                    correlation_id = properties.headers.get('x-correlation-id')

                if not correlation_id:
                    correlation_id = generate_correlation_id()

                # Set correlation ID in context
                set_correlation_id(correlation_id)

                # Parse message
                message_data = json.loads(body)

                # Add metadata
                message_data['_metadata'] = {
                    'correlation_id': correlation_id,
                    'message_id': properties.message_id,
                    'timestamp': properties.headers.get('timestamp'),
                    'exchange': method.exchange,
                    'routing_key': method.routing_key
                }

                # Find and call handler
                handler = self.message_handlers.get(method.routing_key)
                if handler:
                    logger.info(f"Processing message from {method.routing_key}",
                              correlation_id=correlation_id)

                    # Handle in correlation context
                    with CorrelationIDContext(correlation_id):
                        handler(message_data)
                else:
                    logger.warning(f"No handler for routing key: {method.routing_key}")

                # Acknowledge message
                ch.basic_ack(delivery_tag=method.delivery_tag)

            except Exception as e:
                logger.error(f"Failed to process message: {e}",
                           correlation_id=correlation_id)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        # Setup QoS
        self.channel.basic_qos(prefetch_count=1)

        # Start consuming
        self.channel.basic_consume(queue=queue, on_message_callback=callback)

        logger.info("Started consuming messages", queue=queue)
        self.channel.start_consuming()

class KafkaCorrelationProducer:
    """Kafka producer with correlation ID support"""

    def __init__(self, bootstrap_servers: list):
        self.bootstrap_servers = bootstrap_servers
        self.producer = kafka.KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None
        )

    def send(
        self,
        topic: str,
        value: Dict[str, Any],
        key: Optional[str] = None,
        correlation_id: Optional[str] = None,
        headers: Optional[Dict] = None
    ):
        """Send message with correlation ID in headers"""
        # Get or generate correlation ID
        if not correlation_id:
            correlation_id = get_correlation_id() or generate_correlation_id()

        # Prepare headers
        message_headers = {
            'x-correlation-id': correlation_id.encode('utf-8'),
            'message-type': b'default',
            'timestamp': str(time.time()).encode('utf-8')
        }

        # Add custom headers
        if headers:
            for k, v in headers.items():
                message_headers[k.encode('utf-8')] = str(v).encode('utf-8')

        # Add tracing context if available
        tracer = get_tracer()
        if tracer:
            current_span = tracer.get_current_span()
            if current_span:
                message_headers.update({
                    b'x-trace-id': str(current_span.context.trace_id).encode('utf-8'),
                    b'x-span-id': str(current_span.context.span_id).encode('utf-8')
                })

        # Send message
        future = self.producer.send(
            topic,
            value=value,
            key=key,
            headers=message_headers
        )

        # Wait for confirmation (optional)
        try:
            record_metadata = future.get(timeout=10)
            logger.info(f"Sent message to {topic}",
                       correlation_id=correlation_id,
                       partition=record_metadata.partition,
                       offset=record_metadata.offset)
        except kafka.errors.KafkaError as e:
            logger.error(f"Failed to send message: {e}")
            raise

        return future

class KafkaCorrelationConsumer:
    """Kafka consumer with correlation ID extraction"""

    def __init__(self, bootstrap_servers: list, group_id: str):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.consumer = None
        self.message_handlers = {}

    def register_handler(self, topic: str, handler: Callable):
        """Register message handler for topic"""
        self.message_handlers[topic] = handler

    def start_consuming(self, topics: list):
        """Start consuming messages"""
        self.consumer = kafka.KafkaConsumer(
            *topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            consumer_timeout_ms=1000
        )

        logger.info("Started consuming from topics", topics=topics)

        for message in self.consumer:
            try:
                # Extract correlation ID from headers
                correlation_id = None
                if message.headers:
                    for key, value in message.headers:
                        if key == 'x-correlation-id':
                            correlation_id = value.decode('utf-8')
                            break

                if not correlation_id:
                    correlation_id = generate_correlation_id()

                # Set correlation ID in context
                set_correlation_id(correlation_id)

                # Parse message
                message_data = json.loads(message.value.decode('utf-8'))

                # Add metadata
                message_data['_metadata'] = {
                    'correlation_id': correlation_id,
                    'topic': message.topic,
                    'partition': message.partition,
                    'offset': message.offset,
                    'timestamp': message.timestamp
                }

                # Find and call handler
                handler = self.message_handlers.get(message.topic)
                if handler:
                    logger.info(f"Processing message from {message.topic}",
                              correlation_id=correlation_id)

                    # Handle in correlation context
                    with CorrelationIDContext(correlation_id):
                        handler(message_data)
                else:
                    logger.warning(f"No handler for topic: {message.topic}")

            except Exception as e:
                logger.error(f"Failed to process Kafka message: {e}",
                           correlation_id=correlation_id)

class RedisCorrelationPublisher:
    """Redis pub/sub with correlation ID support"""

    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        self.redis_client = redis.Redis(host=host, port=port, db=db)

    def publish(
        self,
        channel: str,
        message: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        """Publish message with correlation ID"""
        # Get or generate correlation ID
        if not correlation_id:
            correlation_id = get_correlation_id() or generate_correlation_id()

        # Add correlation ID to message
        envelope = {
            'correlation_id': correlation_id,
            'timestamp': time.time(),
            'data': message
        }

        # Add tracing context if available
        tracer = get_tracer()
        if tracer:
            current_span = tracer.get_current_span()
            if current_span:
                envelope.update({
                    'trace_id': current_span.context.trace_id,
                    'span_id': current_span.context.span_id
                })

        # Publish message
        self.redis_client.publish(channel, json.dumps(envelope))

        logger.info(f"Published to Redis channel {channel}",
                   correlation_id=correlation_id)

class RedisCorrelationSubscriber:
    """Redis subscriber with correlation ID extraction"""

    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        self.redis_client = redis.Redis(host=host, port=port, db=db)
        self.pubsub = None
        self.message_handlers = {}

    def register_handler(self, channel: str, handler: Callable):
        """Register message handler for channel"""
        self.message_handlers[channel] = handler

    def start_listening(self, channels: list):
        """Start listening to channels"""
        self.pubsub = self.redis_client.pubsub()
        self.pubsub.subscribe(*channels)

        logger.info("Started listening to Redis channels", channels=channels)

        for message in self.pubsub.listen():
            if message['type'] == 'message':
                try:
                    # Parse message
                    envelope = json.loads(message['data'])
                    correlation_id = envelope.get('correlation_id')

                    if not correlation_id:
                        correlation_id = generate_correlation_id()

                    # Set correlation ID in context
                    set_correlation_id(correlation_id)

                    # Add metadata
                    envelope['data']['_metadata'] = {
                        'correlation_id': correlation_id,
                        'channel': message['channel'],
                        'timestamp': envelope.get('timestamp')
                    }

                    # Find and call handler
                    handler = self.message_handlers.get(message['channel'])
                    if handler:
                        logger.info(f"Processing message from {message['channel']}",
                                  correlation_id=correlation_id)

                        # Handle in correlation context
                        with CorrelationIDContext(correlation_id):
                            handler(envelope['data'])
                    else:
                        logger.warning(f"No handler for channel: {message['channel']}")

                except Exception as e:
                    logger.error(f"Failed to process Redis message: {e}",
                               correlation_id=correlation_id)

# Celery integration
class CorrelationTask(Task):
    """Base class for Celery tasks with correlation ID support"""

    def __call__(self, *args, **kwargs):
        # Extract correlation ID from kwargs
        correlation_id = kwargs.pop('correlation_id', None)

        if not correlation_id:
            correlation_id = generate_correlation_id()

        # Set correlation ID in context
        set_correlation_id(correlation_id)

        # Log task start
        logger.info(f"Starting task {self.name}",
                   correlation_id=correlation_id,
                   task_id=self.request.id if hasattr(self, 'request') else None)

        try:
            # Execute task with correlation context
            with CorrelationIDContext(correlation_id):
                result = self.run(*args, **kwargs)

            logger.info(f"Completed task {self.name}",
                       correlation_id=correlation_id)
            return result

        except Exception as e:
            logger.error(f"Task {self.name} failed",
                       error=str(e),
                       correlation_id=correlation_id)
            raise

# Celery signal handlers
@before_task_publish.connect
def before_task_publish_handler(sender=None, headers=None, body=None, **kwargs):
    """Add correlation ID to task before publishing"""
    correlation_id = get_correlation_id() or generate_correlation_id()

    # Add to headers
    if 'headers' not in sender:
        sender['headers'] = {}
    sender['headers']['correlation_id'] = correlation_id

    # Add to body for older Celery versions
    if isinstance(body, dict) and 'correlation_id' not in body:
        body['correlation_id'] = correlation_id

@after_task_publish.connect
def after_task_publish_handler(sender=None, headers=None, body=None, **kwargs):
    """Log task publication"""
    correlation_id = headers.get('correlation_id') if headers else None
    if correlation_id:
        logger.info(f"Task published",
                   task_id=kwargs.get('task_id'),
                   correlation_id=correlation_id)

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Set correlation ID before task runs"""
    # Extract correlation ID from headers or kwargs
    correlation_id = None

    if sender.request.headers:
        correlation_id = sender.request.headers.get('correlation_id')

    if not correlation_id and 'correlation_id' in kwargs:
        correlation_id = kwargs.pop('correlation_id', None)

    if not correlation_id:
        correlation_id = generate_correlation_id()

    # Set correlation ID in context
    set_correlation_id(correlation_id)

    # Store on task for later access
    sender.correlation_id = correlation_id

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """Log task completion"""
    correlation_id = getattr(sender, 'correlation_id', None)
    if correlation_id:
        logger.info(f"Task completed",
                   task_id=task_id,
                   state=state,
                   correlation_id=correlation_id)

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, einfo=None, **kwargs):
    """Log task failure"""
    correlation_id = getattr(sender, 'correlation_id', None)
    if correlation_id:
        logger.error(f"Task failed",
                    task_id=task_id,
                    exception=str(exception),
                    correlation_id=correlation_id)

# Decorator for easy correlation ID in message handlers
def with_message_correlation(func):
    """Decorator to ensure correlation ID in message handlers"""
    import functools

    @functools.wraps(func)
    def wrapper(message, *args, **kwargs):
        # Extract correlation ID from message
        correlation_id = None

        if isinstance(message, dict):
            # Check various possible locations
            correlation_id = (
                message.get('correlation_id') or
                message.get('_metadata', {}).get('correlation_id') or
                message.get('headers', {}).get('x-correlation-id')
            )

        if not correlation_id:
            correlation_id = generate_correlation_id()

        # Set correlation ID in context
        set_correlation_id(correlation_id)

        # Execute with correlation context
        with CorrelationIDContext(correlation_id):
            logger.info("Processing message",
                       handler=func.__name__,
                       correlation_id=correlation_id)

            try:
                result = func(message, *args, **kwargs)
                logger.info("Message processed",
                           handler=func.__name__,
                           correlation_id=correlation_id)
                return result
            except Exception as e:
                logger.error("Message processing failed",
                           handler=func.__name__,
                           error=str(e),
                           correlation_id=correlation_id)
                raise

    return wrapper

# Context manager for message processing
@contextmanager
def message_processing_context(message_data: Dict[str, Any]):
    """Context manager for processing messages with correlation ID"""
    correlation_id = None

    # Extract correlation ID from various possible locations
    if isinstance(message_data, dict):
        correlation_id = (
            message_data.get('correlation_id') or
            message_data.get('_metadata', {}).get('correlation_id') or
            message_data.get('headers', {}).get('x-correlation-id')
        )

    if not correlation_id:
        correlation_id = generate_correlation_id()

    with CorrelationIDContext(correlation_id):
        yield correlation_id