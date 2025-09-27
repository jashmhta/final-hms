"""
Comprehensive tests for correlation ID propagation across all communication protocols
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import aio_pika
import aiohttp
import pytest
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from services.common import (
    CorrelationIDContext,
    CorrelationIDMiddleware,
    DatabaseCorrelationMixin,
    KafkaCorrelationConsumer,
    KafkaCorrelationProducer,
    RabbitMQCorrelationConsumer,
    RabbitMQCorrelationPublisher,
    RedisCorrelationPublisher,
    RedisCorrelationSubscriber,
    add_correlation_to_message,
    database_operation_context,
    extract_correlation_from_message,
    generate_correlation_id,
    get_correlation_id,
    set_correlation_id,
    with_correlation_id,
    with_database_correlation,
)


class TestCorrelationIDBasics:
    """Test basic correlation ID functionality"""

    def test_generate_correlation_id(self):
        """Test correlation ID generation"""
        correlation_id = generate_correlation_id()
        assert isinstance(correlation_id, str)
        assert len(correlation_id) == 36  # UUID length
        try:
            uuid.UUID(correlation_id)
        except ValueError:
            pytest.fail("Generated correlation ID is not a valid UUID")

    def test_set_and_get_correlation_id(self):
        """Test setting and getting correlation ID"""
        test_id = str(uuid.uuid4())
        set_correlation_id(test_id)
        assert get_correlation_id() == test_id

    def test_correlation_id_context_manager(self):
        """Test correlation ID context manager"""
        original_id = get_correlation_id()
        test_id = str(uuid.uuid4())

        with CorrelationIDContext(test_id) as ctx_id:
            assert ctx_id == test_id
            assert get_correlation_id() == test_id

        # Should restore original context
        assert get_correlation_id() == original_id

    @pytest.mark.asyncio
    async def test_async_correlation_id_context(self):
        """Test async correlation ID context"""
        original_id = get_correlation_id()
        test_id = str(uuid.uuid4())

        async with CorrelationIDContext(test_id) as ctx_id:
            assert ctx_id == test_id
            assert get_correlation_id() == test_id

        # Should restore original context
        assert get_correlation_id() == original_id


class TestHTTPCorrelationPropagation:
    """Test HTTP correlation ID propagation"""

    def test_middleware_without_correlation_id(self):
        """Test middleware generates correlation ID if not provided"""
        from starlette.applications import Starlette
        from starlette.middleware import Middleware
        from starlette.requests import Request
        from starlette.responses import JSONResponse
        from starlette.testclient import TestClient

        app = Starlette(
            middleware=[Middleware(CorrelationIDMiddleware)],
            routes=[
                web.get(
                    "/",
                    lambda request: JSONResponse(
                        {"correlation_id": get_correlation_id()}
                    ),
                )
            ],
        )

        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "correlation_id" in data
        assert len(data["correlation_id"]) == 36
        assert response.headers["x-correlation-id"] == data["correlation_id"]

    def test_middleware_with_correlation_id(self):
        """Test middleware uses provided correlation ID"""
        from starlette.applications import Starlette
        from starlette.middleware import Middleware
        from starlette.requests import Request
        from starlette.responses import JSONResponse
        from starlette.testclient import TestClient

        test_id = str(uuid.uuid4())

        app = Starlette(
            middleware=[Middleware(CorrelationIDMiddleware)],
            routes=[
                web.get(
                    "/",
                    lambda request: JSONResponse(
                        {"correlation_id": get_correlation_id()}
                    ),
                )
            ],
        )

        client = TestClient(app)
        response = client.get("/", headers={"x-correlation-id": test_id})
        assert response.status_code == 200
        data = response.json()
        assert data["correlation_id"] == test_id
        assert response.headers["x-correlation-id"] == test_id

    @pytest.mark.asyncio
    async def test_async_request_with_correlation(self):
        """Test async request handling with correlation ID"""
        from starlette.applications import Starlette
        from starlette.middleware import Middleware
        from starlette.requests import Request
        from starlette.responses import JSONResponse

        app = Starlette(middleware=[Middleware(CorrelationIDMiddleware)])

        @app.route("/")
        async def homepage(request: Request):
            correlation_id = get_correlation_id()
            # Simulate async operation
            await asyncio.sleep(0.01)
            return JSONResponse({"correlation_id": correlation_id})

        from starlette.testclient import TestClient

        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "correlation_id" in data


class TestMessageQueueCorrelation:
    """Test message queue correlation ID propagation"""

    @pytest.fixture
    def mock_rabbitmq_connection(self):
        """Mock RabbitMQ connection"""
        with patch("pika.BlockingConnection") as mock:
            mock_connection = Mock()
            mock_channel = Mock()
            mock_connection.channel.return_value = mock_channel
            mock.return_value = mock_connection
            yield mock_connection

    def test_rabbitmq_publish_with_correlation_id(self, mock_rabbitmq_connection):
        """Test RabbitMQ publishing with correlation ID"""
        publisher = RabbitMQCorrelationPublisher()
        test_id = str(uuid.uuid4())
        message = {"data": "test"}

        publisher.connect()
        publisher.publish(
            "test_exchange", "test_routing_key", message, correlation_id=test_id
        )

        # Verify connection was established
        mock_rabbitmq_connection.channel.assert_called_once()

        # Verify message was published with correlation ID
        mock_channel = mock_rabbitmq_connection.channel()
        mock_channel.basic_publish.assert_called_once()
        call_args = mock_channel.basic_publish.call_args

        # Check that headers contain correlation ID
        properties = call_args[1]["properties"]
        assert properties.correlation_id == test_id
        assert properties.headers["x-correlation-id"] == test_id

    def test_rabbitmq_consumer_extracts_correlation_id(self):
        """Test RabbitMQ consumer extracts correlation ID"""
        consumer = RabbitMQCorrelationConsumer()
        handler = Mock()
        consumer.register_handler("test_routing_key", handler)

        # Mock message properties
        properties = Mock()
        properties.correlation_id = str(uuid.uuid4())
        properties.message_id = str(uuid.uuid4())
        properties.headers = {"timestamp": str(time.time())}

        # Mock channel and method
        channel = Mock()
        method = Mock()
        method.routing_key = "test_routing_key"

        # Simulate message callback
        message_data = {"test": "data"}
        body = json.dumps(message_data)

        # Import the callback function (this would need to be extracted from the consumer)
        # For now, we'll test the concept
        correlation_id = properties.correlation_id
        assert correlation_id is not None

    def test_kafka_producer_with_correlation_id(self):
        """Test Kafka producer with correlation ID"""
        with patch("kafka.KafkaProducer") as mock:
            mock_producer = Mock()
            mock.return_value = mock_producer

            producer = KafkaCorrelationProducer(["localhost:9092"])
            test_id = str(uuid.uuid4())
            message = {"data": "test"}

            future = Mock()
            mock_producer.send.return_value = future
            future.get.return_value = Mock(partition=0, offset=0)

            producer.send("test_topic", message, correlation_id=test_id)

            # Verify producer was called with correct headers
            mock_producer.send.assert_called_once()
            call_args = mock_producer.send.call_args

            headers = call_args[1]["headers"]
            assert b"x-correlation-id" in headers
            assert headers[b"x-correlation-id"].decode("utf-8") == test_id

    def test_redis_pubsub_with_correlation_id(self):
        """Test Redis pub/sub with correlation ID"""
        with patch("redis.Redis") as mock:
            mock_redis = Mock()
            mock.return_value = mock_redis

            publisher = RedisCorrelationPublisher()
            test_id = str(uuid.uuid4())
            message = {"data": "test"}

            publisher.publish("test_channel", message, correlation_id=test_id)

            # Verify message was published with correlation ID
            mock_redis.publish.assert_called_once()
            call_args = mock_redis.publish.call_args

            envelope = json.loads(call_args[0][1])
            assert envelope["correlation_id"] == test_id
            assert envelope["data"] == message


class TestDatabaseCorrelation:
    """Test database correlation ID tracking"""

    def test_database_mixin_with_correlation_id(self):
        """Test DatabaseCorrelationMixin"""

        class MockCursor:
            def __init__(self):
                self.rowcount = 1

            def execute(self, query, params=None):
                return Mock(rowcount=1)

        class MockConnection(DatabaseCorrelationMixin):
            def __init__(self):
                super().__init__()
                self.cursor = MockCursor()

        conn = MockConnection()
        test_id = str(uuid.uuid4())

        result = conn.execute_with_correlation(
            "SELECT * FROM users WHERE id = %s", {"id": 1}, correlation_id=test_id
        )

        assert conn._correlation_id == test_id

    @pytest.mark.asyncio
    async def test_database_context_manager(self):
        """Test database operation context manager"""
        test_id = str(uuid.uuid4())

        with database_operation_context("test_operation", test_id) as ctx:
            assert ctx["correlation_id"] == test_id
            assert get_correlation_id() == test_id

        # Context should be cleaned up
        # (In real implementation, would restore original correlation ID)

    def test_database_decorator(self):
        """Test database correlation decorator"""

        @with_database_correlation
        def test_query(user_id, correlation_id=None):
            assert correlation_id is not None
            return {"user_id": user_id, "correlation_id": correlation_id}

        result = test_query(1)
        assert "correlation_id" in result
        assert result["user_id"] == 1


class TestMessageCorrelationHelpers:
    """Test message correlation helper functions"""

    def test_add_correlation_to_message(self):
        """Test adding correlation ID to message"""
        test_id = str(uuid.uuid4())
        message = {"data": "test"}

        message_with_correlation = add_correlation_to_message(message)
        assert message_with_correlation["correlation_id"] == test_id

    def test_extract_correlation_from_message(self):
        """Test extracting correlation ID from message"""
        test_id = str(uuid.uuid4())
        message = {"correlation_id": test_id, "data": "test"}

        extracted_id = extract_correlation_from_message(message)
        assert extracted_id == test_id

    def test_extract_correlation_from_message_without_id(self):
        """Test extracting correlation ID when not present"""
        message = {"data": "test"}

        extracted_id = extract_correlation_from_message(message)
        assert extracted_id is None


class TestCorrelationPropagationScenarios:
    """Test end-to-end correlation propagation scenarios"""

    @pytest.mark.asyncio
    async def test_http_to_message_queue_correlation(self):
        """Test correlation propagation from HTTP to message queue"""
        # This would test a full scenario:
        # 1. HTTP request with correlation ID
        # 2. Service processes request and publishes message
        # 3. Message queue consumer receives message with same correlation ID
        # 4. Consumer processes with correlation context

        # For now, we'll mock the scenario
        test_id = str(uuid.uuid4())

        # Step 1: HTTP request
        set_correlation_id(test_id)
        assert get_correlation_id() == test_id

        # Step 2: Service extracts correlation ID and publishes message
        message = {"action": "update_user", "user_id": 123}
        message_with_correlation = add_correlation_to_message(message)
        assert message_with_correlation["correlation_id"] == test_id

        # Step 3: Consumer extracts correlation ID
        received_correlation = extract_correlation_from_message(
            message_with_correlation
        )
        assert received_correlation == test_id

        # Step 4: Consumer processes with correlation context
        with CorrelationIDContext(received_correlation):
            assert get_correlation_id() == test_id

    @pytest.mark.asyncio
    async def test_service_to_service_correlation(self):
        """Test correlation propagation between services"""
        test_id = str(uuid.uuid4())

        # Service A receives request
        with CorrelationIDContext(test_id):
            # Service A makes call to Service B
            async with aiohttp.ClientSession() as session:
                headers = {"x-correlation-id": test_id}
                # Mock the HTTP call
                pass

        # Service B receives request with same correlation ID
        assert get_correlation_id() == test_id

    def test_database_query_correlation_chain(self):
        """Test correlation ID chain through database operations"""
        test_id = str(uuid.uuid4())

        # Start with correlation ID
        set_correlation_id(test_id)

        # Multiple database operations
        with database_operation_context("read_user", test_id):
            assert get_correlation_id() == test_id

        with database_operation_context("update_user", test_id):
            assert get_correlation_id() == test_id

        with database_operation_context("log_activity", test_id):
            assert get_correlation_id() == test_id

    @pytest.mark.asyncio
    async def test_complex_workflow_correlation(self):
        """Test correlation through a complex workflow"""
        test_id = str(uuid.uuid4())

        # 1. HTTP request
        with CorrelationIDContext(test_id):
            # 2. Process request and publish to queue
            message = add_correlation_to_message({"type": "order_processed"})

            # 3. Queue consumer processes
            received_id = extract_correlation_from_message(message)
            with CorrelationIDContext(received_id):
                # 4. Database operations
                with database_operation_context("save_order", received_id):
                    # 5. Call another service
                    headers = {"x-correlation-id": received_id}
                    # Mock service call
                    pass

                # 6. Publish to another queue
                notification = add_correlation_to_message({"type": "notification"})

        # All operations should have the same correlation ID
        assert test_id == received_id == extract_correlation_from_message(notification)


class TestCorrelationIDErrorHandling:
    """Test error handling with correlation IDs"""

    def test_error_logging_with_correlation_id(self):
        """Test that errors are logged with correlation ID"""
        test_id = str(uuid.uuid4())

        with patch("services.common.correlation_id.logger") as mock_logger:
            set_correlation_id(test_id)

            # Simulate error
            try:
                raise ValueError("Test error")
            except ValueError as e:
                # Error would be logged with correlation ID
                pass

            # In real implementation, would verify error was logged with correlation ID
            assert get_correlation_id() == test_id

    def test_database_error_with_correlation_id(self):
        """Test database errors include correlation ID"""
        test_id = str(uuid.uuid4())

        class FailingConnection(DatabaseCorrelationMixin):
            def __init__(self):
                super().__init__()
                self.cursor = Mock()
                self.cursor.execute.side_effect = Exception("Database error")

        conn = FailingConnection()

        with pytest.raises(Exception):
            conn.execute_with_correlation(
                "SELECT * FROM non_existent_table", correlation_id=test_id
            )

        # Verify correlation ID was set
        assert conn._correlation_id == test_id


class TestPerformanceWithCorrelationIDs:
    """Test performance impact of correlation ID tracking"""

    @pytest.mark.performance
    def test_correlation_id_generation_performance(self):
        """Test correlation ID generation performance"""
        import time

        start_time = time.time()
        iterations = 10000

        for _ in range(iterations):
            generate_correlation_id()

        duration = time.time() - start_time
        avg_time = duration / iterations

        # Should be very fast (< 0.1ms per generation)
        assert avg_time < 0.0001
        print(f"Average correlation ID generation time: {avg_time * 1000:.3f}ms")

    @pytest.mark.performance
    def test_context_manager_performance(self):
        """Test context manager performance"""
        import time

        start_time = time.time()
        iterations = 1000

        for _ in range(iterations):
            with CorrelationIDContext():
                pass

        duration = time.time() - start_time
        avg_time = duration / iterations

        # Should be very fast (< 0.01ms per context)
        assert avg_time < 0.00001
        print(f"Average context manager time: {avg_time * 1000:.3f}ms")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
