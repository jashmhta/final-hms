"""
HMS Load Test Module with WebSocket Performance Testing
"""

import json
import asyncio
import websockets
from locust import HttpUser, between, task, events
from locust.exception import StopUser


class HMSUser(HttpUser):
    wait_time = between(1, 3)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.websocket_connections = []
        self.client_id = f"user_{id(self)}"

    @task
    def health_check(self):
        self.client.get("/health/")

    @task(3)
    def login(self):
        self.client.post(
            "/api/auth/token/", json={"username": "testuser", "password": "testpass"}
        )

    @task(2)
    def get_patients(self):
        self.client.get("/api/patients/")

    @task(1)
    def create_appointment(self):
        self.client.post(
            "/api/appointments/", json={"patient": 1, "doctor": 1, "date": "2025-01-01"}
        )

    @task(4)
    def websocket_performance_test(self):
        """Test WebSocket connections under load"""
        try:
            # Connect to WebSocket
            ws_url = f"ws://localhost:8000/ws/{self.client_id}"
            websocket = await websockets.connect(ws_url)

            # Subscribe to events
            subscribe_msg = {
                "type": "subscribe",
                "events": ["patient_update", "appointment_alert", "emergency"]
            }
            await websocket.send(json.dumps(subscribe_msg))

            # Send ping to test latency
            ping_msg = {"type": "ping"}
            start_time = self.environment.runner.stats.start_time
            await websocket.send(json.dumps(ping_msg))

            # Listen for responses
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)

            if data.get("type") == "pong":
                latency = self.environment.runner.stats.start_time - start_time
                # Record latency metric
                events.request.fire(
                    request_type="WebSocket",
                    name="ping_pong",
                    response_time=latency * 1000,  # Convert to ms
                    response_length=len(response),
                    exception=None,
                )

            # Keep connection alive briefly
            await asyncio.sleep(1)

            # Send broadcast message
            broadcast_msg = {
                "type": "broadcast",
                "event": "patient_update",
                "data": {"patient_id": 123, "status": "updated"}
            }
            await websocket.send(json.dumps(broadcast_msg))

            await websocket.close()

        except Exception as e:
            events.request.fire(
                request_type="WebSocket",
                name="websocket_connection",
                response_time=0,
                response_length=0,
                exception=e,
            )


class WebSocketLoadTest(HttpUser):
    """Dedicated WebSocket load testing user"""
    wait_time = between(0.1, 1.0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.websocket = None
        self.client_id = f"ws_user_{id(self)}"

    async def connect_websocket(self):
        """Establish WebSocket connection"""
        try:
            ws_url = f"ws://localhost:8000/ws/{self.client_id}"
            self.websocket = await websockets.connect(ws_url)

            # Subscribe to events
            subscribe_msg = {
                "type": "subscribe",
                "events": ["patient_monitoring", "alerts", "updates"]
            }
            await self.websocket.send(json.dumps(subscribe_msg))

        except Exception as e:
            events.request.fire(
                request_type="WebSocket",
                name="connect",
                response_time=0,
                response_length=0,
                exception=e,
            )
            raise StopUser()

    async def disconnect_websocket(self):
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()

    @task
    def websocket_operations(self):
        """Perform WebSocket operations under load"""
        if not self.websocket:
            asyncio.create_task(self.connect_websocket())
            return

        try:
            # Send ping for latency measurement
            ping_msg = {"type": "ping"}
            start_time = asyncio.get_event_loop().time()
            await self.websocket.send(json.dumps(ping_msg))

            # Wait for pong
            response = await asyncio.wait_for(self.websocket.recv(), timeout=2.0)
            data = json.loads(response)

            if data.get("type") == "pong":
                latency = (asyncio.get_event_loop().time() - start_time) * 1000
                events.request.fire(
                    request_type="WebSocket",
                    name="ping_latency",
                    response_time=latency,
                    response_length=len(response),
                    exception=None,
                )

            # Send broadcast message
            broadcast_msg = {
                "type": "broadcast",
                "event": "patient_monitoring",
                "data": {
                    "patient_id": self.client_id,
                    "vitals": {"hr": 75, "bp": "120/80", "temp": 98.6}
                }
            }
            await self.websocket.send(json.dumps(broadcast_msg))

            # Listen for any incoming messages
            try:
                msg = await asyncio.wait_for(self.websocket.recv(), timeout=0.1)
                events.request.fire(
                    request_type="WebSocket",
                    name="receive_message",
                    response_time=0,
                    response_length=len(msg),
                    exception=None,
                )
            except asyncio.TimeoutError:
                pass  # No message received, that's ok

        except Exception as e:
            events.request.fire(
                request_type="WebSocket",
                name="operation",
                response_time=0,
                response_length=0,
                exception=e,
            )
            # Reconnect on error
            await self.disconnect_websocket()
            self.websocket = None
