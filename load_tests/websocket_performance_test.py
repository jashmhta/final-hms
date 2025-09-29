"""
Comprehensive WebSocket Performance Testing for HMS
Tests concurrent WebSocket connections, message throughput, and latency
"""

import asyncio
import json
import time
import statistics
from typing import List, Dict, Any
import websockets
from websockets.exceptions import ConnectionClosedError
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import threading


class WebSocketPerformanceTest:
    """Comprehensive WebSocket performance testing suite"""

    def __init__(self, base_url: str = "ws://localhost:8000", num_clients: int = 100):
        self.base_url = base_url
        self.num_clients = num_clients
        self.connections = []
        self.latencies = []
        self.errors = []
        self.messages_sent = 0
        self.messages_received = 0
        self.test_duration = 60  # seconds

    async def connect_client(
        self, client_id: int
    ) -> websockets.WebSocketServerProtocol:
        """Connect a single WebSocket client"""
        try:
            ws_url = f"{self.base_url}/ws/client_{client_id}"
            websocket = await websockets.connect(ws_url)

            # Subscribe to events
            subscribe_msg = {
                "type": "subscribe",
                "events": ["patient_update", "emergency_alert", "monitoring"],
            }
            await websocket.send(json.dumps(subscribe_msg))

            return websocket
        except Exception as e:
            self.errors.append(f"Connection error for client {client_id}: {e}")
            return None

    async def run_client_operations(
        self, websocket: websockets.WebSocketServerProtocol, client_id: int
    ):
        """Run operations for a single client"""
        try:
            start_time = time.time()

            while time.time() - start_time < self.test_duration:
                # Send ping for latency measurement
                ping_start = time.time()
                ping_msg = {
                    "type": "ping",
                    "client_id": client_id,
                    "timestamp": ping_start,
                }
                await websocket.send(json.dumps(ping_msg))

                # Wait for pong
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    pong_time = time.time()
                    data = json.loads(response)

                    if data.get("type") == "pong":
                        latency = (pong_time - ping_start) * 1000  # ms
                        self.latencies.append(latency)
                        self.messages_sent += 1
                        self.messages_received += 1

                    # Send broadcast message
                    broadcast_msg = {
                        "type": "broadcast",
                        "event": "patient_update",
                        "data": {
                            "patient_id": f"patient_{client_id}",
                            "status": "monitoring",
                            "timestamp": time.time(),
                        },
                    }
                    await websocket.send(json.dumps(broadcast_msg))
                    self.messages_sent += 1

                except asyncio.TimeoutError:
                    self.errors.append(f"Timeout for client {client_id}")
                    break

                # Listen for broadcast messages
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                    self.messages_received += 1
                except asyncio.TimeoutError:
                    pass  # No message, continue

                await asyncio.sleep(0.1)  # Small delay between operations

        except Exception as e:
            self.errors.append(f"Client {client_id} error: {e}")
        finally:
            try:
                await websocket.close()
            except:
                pass

    async def run_load_test(self) -> Dict[str, Any]:
        """Run the comprehensive WebSocket load test"""
        print(f"Starting WebSocket performance test with {self.num_clients} clients...")

        # Connect all clients
        connect_tasks = []
        for i in range(self.num_clients):
            connect_tasks.append(self.connect_client(i))

        connection_results = await asyncio.gather(
            *connect_tasks, return_exceptions=True
        )
        self.connections = [
            conn
            for conn in connection_results
            if conn is not None and not isinstance(conn, Exception)
        ]

        successful_connections = len(self.connections)
        print(
            f"Successfully connected {successful_connections}/{self.num_clients} clients"
        )

        if successful_connections == 0:
            return {"error": "No connections established"}

        # Run client operations
        operation_tasks = []
        for i, websocket in enumerate(self.connections):
            operation_tasks.append(self.run_client_operations(websocket, i))

        print(f"Running operations for {self.test_duration} seconds...")
        await asyncio.gather(*operation_tasks, return_exceptions=True)

        # Calculate statistics
        results = self.calculate_statistics(successful_connections)

        print("WebSocket performance test completed!")
        print(f"Results: {results}")

        return results

    def calculate_statistics(self, successful_connections: int) -> Dict[str, Any]:
        """Calculate performance statistics"""
        total_messages = self.messages_sent + self.messages_received

        results = {
            "total_clients": self.num_clients,
            "successful_connections": successful_connections,
            "connection_success_rate": successful_connections / self.num_clients * 100,
            "total_messages_sent": self.messages_sent,
            "total_messages_received": self.messages_received,
            "total_messages": total_messages,
            "messages_per_second": (
                total_messages / self.test_duration if self.test_duration > 0 else 0
            ),
            "errors": len(self.errors),
            "error_rate": (
                len(self.errors) / (successful_connections * self.test_duration) * 100
                if successful_connections > 0
                else 0
            ),
        }

        if self.latencies:
            results.update(
                {
                    "latency_stats": {
                        "min_ms": min(self.latencies),
                        "max_ms": max(self.latencies),
                        "mean_ms": statistics.mean(self.latencies),
                        "median_ms": statistics.median(self.latencies),
                        "p95_ms": statistics.quantiles(self.latencies, n=20)[
                            18
                        ],  # 95th percentile
                        "p99_ms": statistics.quantiles(self.latencies, n=100)[
                            98
                        ],  # 99th percentile
                    },
                    "sub_200ms_responses": sum(1 for lat in self.latencies if lat < 200)
                    / len(self.latencies)
                    * 100,
                    "sub_500ms_responses": sum(1 for lat in self.latencies if lat < 500)
                    / len(self.latencies)
                    * 100,
                }
            )

        return results


class HospitalLoadSimulator:
    """Simulate hospital load with WebSocket connections"""

    def __init__(self, base_url: str = "ws://localhost:8000"):
        self.base_url = base_url
        self.departments = {
            "emergency": 50,  # 50 concurrent connections
            "icu": 30,  # 30 concurrent connections
            "wards": 100,  # 100 concurrent connections
            "outpatient": 75,  # 75 concurrent connections
        }

    async def simulate_department(self, department: str, num_clients: int):
        """Simulate WebSocket load for a specific department"""
        print(f"Simulating {department} with {num_clients} clients...")

        test = WebSocketPerformanceTest(base_url=self.base_url, num_clients=num_clients)

        # Customize events based on department
        if department == "emergency":
            test.test_duration = 120  # Longer test for emergency
        elif department == "icu":
            test.test_duration = 180  # Even longer for ICU monitoring

        results = await test.run_load_test()

        return {"department": department, "results": results}

    async def run_hospital_simulation(self) -> Dict[str, Any]:
        """Run full hospital load simulation"""
        print("Starting hospital WebSocket load simulation...")

        tasks = []
        for department, clients in self.departments.items():
            tasks.append(self.simulate_department(department, clients))

        department_results = await asyncio.gather(*tasks)

        # Aggregate results
        total_clients = sum(self.departments.values())
        total_messages = sum(
            r["results"].get("total_messages", 0) for r in department_results
        )
        avg_latency = (
            statistics.mean(
                [
                    r["results"].get("latency_stats", {}).get("mean_ms", 0)
                    for r in department_results
                    if "latency_stats" in r["results"]
                ]
            )
            if any("latency_stats" in r["results"] for r in department_results)
            else 0
        )

        hospital_results = {
            "simulation_type": "hospital_load",
            "departments": {r["department"]: r["results"] for r in department_results},
            "aggregate": {
                "total_departments": len(self.departments),
                "total_clients": total_clients,
                "total_messages": total_messages,
                "messages_per_second": total_messages / 60,  # Assuming 60 second tests
                "average_latency_ms": avg_latency,
                "meets_200ms_target": avg_latency < 200 if avg_latency > 0 else False,
            },
        }

        print("Hospital simulation completed!")
        print(f"Aggregate results: {hospital_results['aggregate']}")

        return hospital_results


async def main():
    """Main test runner"""
    import argparse

    parser = argparse.ArgumentParser(
        description="WebSocket Performance Testing for HMS"
    )
    parser.add_argument(
        "--url", default="ws://localhost:8000", help="WebSocket base URL"
    )
    parser.add_argument(
        "--clients", type=int, default=100, help="Number of concurrent clients"
    )
    parser.add_argument(
        "--duration", type=int, default=60, help="Test duration in seconds"
    )
    parser.add_argument(
        "--hospital",
        action="store_true",
        help="Run hospital simulation instead of basic test",
    )

    args = parser.parse_args()

    if args.hospital:
        simulator = HospitalLoadSimulator(args.url)
        results = await simulator.run_hospital_simulation()
    else:
        test = WebSocketPerformanceTest(args.url, args.clients)
        test.test_duration = args.duration
        results = await test.run_load_test()

    # Save results to file
    import json

    with open("websocket_performance_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("Results saved to websocket_performance_results.json")


if __name__ == "__main__":
    asyncio.run(main())
