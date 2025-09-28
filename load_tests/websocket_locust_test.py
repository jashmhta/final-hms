"""
WebSocket Load Testing with Locust for HMS
"""

import json
import asyncio
import time
from locust import User, task, events
from locust.exception import StopUser
import websockets
from websockets.exceptions import ConnectionClosedError, WebSocketException


class WebSocketUser(User):
    """WebSocket user for Locust load testing"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.websocket = None
        self.client_id = f"locust_user_{id(self)}"
        self.connected = False
        self.message_count = 0

    async def connect(self):
        """Establish WebSocket connection"""
        try:
            ws_url = f"ws://localhost:8000/ws/{self.client_id}"
            self.websocket = await websockets.connect(
                ws_url,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5
            )
            self.connected = True

            # Subscribe to events
            subscribe_msg = {
                "type": "subscribe",
                "events": ["patient_update", "emergency_alert", "appointment_reminder"]
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

    async def disconnect(self):
        """Close WebSocket connection"""
        if self.websocket:
            try:
                await self.websocket.close()
            except:
                pass
            self.websocket = None
            self.connected = False

    @task
    def websocket_interaction(self):
        """Main WebSocket interaction task"""
        if not self.connected:
            asyncio.create_task(self.connect())
            return

        try:
            # Send ping for latency measurement
            ping_start = time.time()
            ping_msg = {
                "type": "ping",
                "client_id": self.client_id,
                "timestamp": ping_start
            }

            asyncio.create_task(self.send_and_receive(ping_start))

        except Exception as e:
            events.request.fire(
                request_type="WebSocket",
                name="interaction",
                response_time=0,
                response_length=0,
                exception=e,
            )

    async def send_and_receive(self, ping_start):
        """Send message and handle response"""
        try:
            # Send ping
            ping_msg = {
                "type": "ping",
                "client_id": self.client_id,
                "timestamp": ping_start
            }
            await self.websocket.send(json.dumps(ping_msg))

            # Wait for pong
            response = await asyncio.wait_for(self.websocket.recv(), timeout=2.0)
            pong_time = time.time()
            data = json.loads(response)

            if data.get("type") == "pong":
                latency = (pong_time - ping_start) * 1000  # Convert to ms
                events.request.fire(
                    request_type="WebSocket",
                    name="ping_pong",
                    response_time=latency,
                    response_length=len(response),
                    exception=None,
                )

                # Check if latency meets requirements
                if latency > 200:
                    events.request.fire(
                        request_type="WebSocket",
                        name="slow_response",
                        response_time=latency,
                        response_length=0,
                        exception=Exception(f"Response time {latency:.2f}ms exceeds 200ms target"),
                    )

            # Send broadcast message occasionally
            if self.message_count % 10 == 0:
                broadcast_msg = {
                    "type": "broadcast",
                    "event": "patient_update",
                    "data": {
                        "patient_id": f"patient_{self.message_count}",
                        "action": "status_update",
                        "timestamp": time.time()
                    }
                }
                await self.websocket.send(json.dumps(broadcast_msg))

                events.request.fire(
                    request_type="WebSocket",
                    name="broadcast",
                    response_time=0,
                    response_length=len(json.dumps(broadcast_msg)),
                    exception=None,
                )

            self.message_count += 1

            # Listen for incoming messages
            try:
                incoming = await asyncio.wait_for(self.websocket.recv(), timeout=0.1)
                events.request.fire(
                    request_type="WebSocket",
                    name="receive",
                    response_time=0,
                    response_length=len(incoming),
                    exception=None,
                )
            except asyncio.TimeoutError:
                pass  # No message received

        except (ConnectionClosedError, WebSocketException) as e:
            events.request.fire(
                request_type="WebSocket",
                name="connection_error",
                response_time=0,
                response_length=0,
                exception=e,
            )
            self.connected = False
            raise StopUser()
        except Exception as e:
            events.request.fire(
                request_type="WebSocket",
                name="operation_error",
                response_time=0,
                response_length=0,
                exception=e,
            )


class HospitalWebSocketUser(WebSocketUser):
    """Hospital-specific WebSocket user simulating different roles"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role = self._assign_role()

    def _assign_role(self):
        """Assign a role based on user ID for realistic simulation"""
        user_num = int(self.client_id.split('_')[-1])
        if user_num % 10 == 0:
            return "doctor"
        elif user_num % 5 == 0:
            return "nurse"
        else:
            return "staff"

    async def connect(self):
        """Establish connection with role-specific subscriptions"""
        await super().connect()

        # Role-specific event subscriptions
        role_events = {
            "doctor": ["emergency_alert", "patient_critical", "consultation_request"],
            "nurse": ["patient_monitoring", "medication_alert", "vital_signs"],
            "staff": ["appointment_reminder", "patient_update", "general_alert"]
        }

        subscribe_msg = {
            "type": "subscribe",
            "events": role_events.get(self.role, ["general_update"])
        }
        await self.websocket.send(json.dumps(subscribe_msg))

    @task(3)
    def role_specific_interaction(self):
        """Role-specific WebSocket interactions"""
        if not self.connected:
            return

        try:
            if self.role == "doctor":
                # Doctors send more critical updates
                msg = {
                    "type": "broadcast",
                    "event": "patient_critical",
                    "data": {
                        "patient_id": f"patient_{self.message_count}",
                        "condition": "critical",
                        "doctor_id": self.client_id,
                        "timestamp": time.time()
                    }
                }
            elif self.role == "nurse":
                # Nurses monitor vitals
                msg = {
                    "type": "broadcast",
                    "event": "vital_signs",
                    "data": {
                        "patient_id": f"patient_{self.message_count}",
                        "vitals": {"hr": 75, "bp": "120/80", "temp": 98.6},
                        "nurse_id": self.client_id,
                        "timestamp": time.time()
                    }
                }
            else:
                # Staff handle general updates
                msg = {
                    "type": "broadcast",
                    "event": "patient_update",
                    "data": {
                        "patient_id": f"patient_{self.message_count}",
                        "status": "updated",
                        "staff_id": self.client_id,
                        "timestamp": time.time()
                    }
                }

            asyncio.create_task(self.send_message(msg))

        except Exception as e:
            events.request.fire(
                request_type="WebSocket",
                name="role_interaction",
                response_time=0,
                response_length=0,
                exception=e,
            )

    async def send_message(self, msg):
        """Send role-specific message"""
        try:
            start_time = time.time()
            await self.websocket.send(json.dumps(msg))

            # Wait for acknowledgment or response
            try:
                response = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                response_time = (time.time() - start_time) * 1000

                events.request.fire(
                    request_type="WebSocket",
                    name=f"{self.role}_message",
                    response_time=response_time,
                    response_length=len(response),
                    exception=None,
                )
            except asyncio.TimeoutError:
                events.request.fire(
                    request_type="WebSocket",
                    name=f"{self.role}_message_timeout",
                    response_time=1000,  # 1 second timeout
                    response_length=0,
                    exception=Exception("Response timeout"),
                )

        except Exception as e:
            events.request.fire(
                request_type="WebSocket",
                name=f"{self.role}_send_error",
                response_time=0,
                response_length=0,
                exception=e,
            )