import secrets

#!/usr/bin/env python3
"""
Comprehensive load testing script for HMS performance validation
Tests API endpoints under various load conditions
"""
import argparse
import asyncio
import csv
import json
import logging
import statistics
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    endpoint: str
    method: str
    status_code: int
    response_time: float
    error: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class TestConfig:
    base_url: str
    concurrent_users: int
    requests_per_user: int
    ramp_up_time: int
    duration: int
    endpoints: List[Dict[str, Any]]


class PerformanceTester:
    def __init__(self, config: TestConfig):
        self.config = config
        self.results: List[TestResult] = []
        self.session: Optional[aiohttp.ClientSession] = None
        self.auth_token: Optional[str] = None

    async def setup(self):
        """Setup test environment"""
        # Create HTTP session
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
        self.session = aiohttp.ClientSession(timeout=timeout, connector=connector)

        # Get authentication token
        await self.authenticate()

    async def authenticate(self):
        """Authenticate and get JWT token"""
        auth_data = {"username": "admin@test.com", "password": "testpassword123"}

        try:
            async with self.session.post(
                f"{self.config.base_url}/api/auth/login/", json=auth_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get("access_token")
                    logger.info("Authentication successful")
                else:
                    logger.error("Authentication failed")
                    raise Exception("Authentication failed")
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise

    async def make_request(self, endpoint: Dict[str, Any]) -> TestResult:
        """Make a single request to endpoint"""
        url = f"{self.config.base_url}{endpoint['path']}"
        method = endpoint.get("method", "GET")
        headers = {"Authorization": f"Bearer {self.auth_token}"}

        start_time = time.time()

        try:
            async with self.session.request(
                method, url, headers=headers, json=endpoint.get("payload")
            ) as response:
                response_time = time.time() - start_time

                result = TestResult(
                    endpoint=endpoint["path"],
                    method=method,
                    status_code=response.status,
                    response_time=response_time,
                )

                # Log slow responses
                if response_time > 1.0:
                    logger.warning(
                        f"Slow response: {method} {url} - {response_time:.2f}s"
                    )

                return result

        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Request failed: {method} {url} - {str(e)}")

            return TestResult(
                endpoint=endpoint["path"],
                method=method,
                status_code=0,
                response_time=response_time,
                error=str(e),
            )

    async def user_scenario(self, user_id: int):
        """Simulate user behavior"""
        start_time = time.time()
        requests_made = 0

        logger.info(f"User {user_id} starting scenario")

        # Warm-up period
        if self.config.ramp_up_time > 0:
            ramp_up_delay = self.config.ramp_up_time / self.config.concurrent_users
            await asyncio.sleep(user_id * ramp_up_delay)

        while requests_made < self.config.requests_per_user:
            # Select endpoint based on realistic usage patterns
            endpoint = self.select_endpoint()
            result = await self.make_request(endpoint)
            self.results.append(result)
            requests_made += 1

            # Think time between requests
            think_time = endpoint.get("think_time", 1.0)
            await asyncio.sleep(think_time)

        duration = time.time() - start_time
        logger.info(
            f"User {user_id} completed {requests_made} requests in {duration:.2f}s"
        )

    def select_endpoint(self) -> Dict[str, Any]:
        """Select endpoint based on usage distribution"""
        # Realistic healthcare system usage patterns
        usage_distribution = [
            (0.3, {"path": "/api/patients/", "method": "GET", "think_time": 2.0}),
            (0.2, {"path": "/api/appointments/", "method": "GET", "think_time": 1.5}),
            (
                0.15,
                {
                    "path": "/api/ehr/medical-records/",
                    "method": "GET",
                    "think_time": 3.0,
                },
            ),
            (0.1, {"path": "/api/lab/results/", "method": "GET", "think_time": 2.5}),
            (
                0.1,
                {
                    "path": "/api/patients/",
                    "method": "POST",
                    "payload": {
                        "first_name": "Test",
                        "last_name": f"User_{int(time.time())}",
                        "date_of_birth": "1990-01-01",
                        "gender": "MALE",
                    },
                    "think_time": 1.0,
                },
            ),
            (
                0.1,
                {
                    "path": "/api/appointments/",
                    "method": "POST",
                    "payload": {
                        "patient_id": 1,
                        "primary_provider_id": 1,
                        "start_at": "2024-01-01T10:00:00Z",
                        "end_at": "2024-01-01T10:30:00Z",
                        "appointment_type": "ROUTINE",
                    },
                    "think_time": 1.0,
                },
            ),
            (
                0.05,
                {
                    "path": "/api/analytics/dashboard/",
                    "method": "GET",
                    "think_time": 5.0,
                },
            ),
        ]

        import random

        rand_val = secrets.random()
        cumulative = 0

        for probability, endpoint in usage_distribution:
            cumulative += probability
            if rand_val <= cumulative:
                return endpoint

        return usage_distribution[-1][1]

    async def run_test(self):
        """Execute load test"""
        logger.info("Starting load test...")
        logger.info(
            f"Configuration: {self.config.concurrent_users} users, "
            f"{self.config.requests_per_user} requests each"
        )

        start_time = time.time()

        # Create user tasks
        tasks = [self.user_scenario(i) for i in range(self.config.concurrent_users)]

        # Run all users concurrently
        await asyncio.gather(*tasks)

        total_duration = time.time() - start_time
        logger.info(f"Load test completed in {total_duration:.2f} seconds")

    def analyze_results(self):
        """Analyze test results"""
        if not self.results:
            logger.warning("No results to analyze")
            return

        logger.info("\n" + "=" * 60)
        logger.info("PERFORMANCE TEST RESULTS")
        logger.info("=" * 60)

        # Overall statistics
        total_requests = len(self.results)
        successful_requests = sum(1 for r in self.results if r.status_code == 200)
        failed_requests = total_requests - successful_requests

        response_times = [r.response_time for r in self.results if r.status_code == 200]

        logger.info(f"\nOverall Statistics:")
        logger.info(f"  Total Requests: {total_requests}")
        logger.info(
            f"  Successful Requests: {successful_requests} ({successful_requests/total_requests*100:.1f}%)"
        )
        logger.info(
            f"  Failed Requests: {failed_requests} ({failed_requests/total_requests*100:.1f}%)"
        )
        logger.info(
            f"  Total Test Duration: {self.results[-1].timestamp - self.results[0].timestamp}"
        )

        if response_times:
            logger.info(f"\nResponse Time Statistics:")
            logger.info(f"  Average: {statistics.mean(response_times):.3f}s")
            logger.info(f"  Median: {statistics.median(response_times):.3f}s")
            logger.info(f"  Min: {min(response_times):.3f}s")
            logger.info(f"  Max: {max(response_times):.3f}s")
            logger.info(
                f"  95th Percentile: {statistics.quantiles(response_times, n=20)[18]:.3f}s"
            )
            logger.info(
                f"  99th Percentile: {statistics.quantiles(response_times, n=100)[98]:.3f}s"
            )

            # Target metrics check
            avg_response = statistics.mean(response_times)
            p95_response = statistics.quantiles(response_times, n=20)[18]

            logger.info(f"\nPerformance Targets:")
            logger.info(
                f"  Average Response Time: {avg_response:.3f}s {'✓' if avg_response < 0.1 else '✗'} (Target: <100ms)"
            )
            logger.info(
                f"  95th Percentile: {p95_response:.3f}s {'✓' if p95_response < 0.5 else '✗'} (Target: <500ms)"
            )
            logger.info(
                f"  Success Rate: {successful_requests/total_requests*100:.1f}% {'✓' if successful_requests/total_requests > 0.99 else '✗'} (Target: >99%)"
            )

        # Endpoint breakdown
        logger.info(f"\nEndpoint Breakdown:")
        endpoint_stats = {}

        for result in self.results:
            endpoint = result.endpoint
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {
                    "requests": 0,
                    "successful": 0,
                    "response_times": [],
                }

            endpoint_stats[endpoint]["requests"] += 1
            if result.status_code == 200:
                endpoint_stats[endpoint]["successful"] += 1
                endpoint_stats[endpoint]["response_times"].append(result.response_time)

        for endpoint, stats in endpoint_stats.items():
            if stats["response_times"]:
                avg_time = statistics.mean(stats["response_times"])
                logger.info(f"  {endpoint}:")
                logger.info(f"    Requests: {stats['requests']}")
                logger.info(
                    f"    Success Rate: {stats['successful']/stats['requests']*100:.1f}%"
                )
                logger.info(f"    Avg Response: {avg_time:.3f}s")

        # Throughput
        if response_times:
            total_duration = (
                self.results[-1].timestamp - self.results[0].timestamp
            ).total_seconds()
            throughput = (
                len(response_times) / total_duration if total_duration > 0 else 0
            )
            logger.info(f"\nThroughput: {throughput:.1f} requests/second")

    def save_results(self, filename: str = None):
        """Save results to CSV"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_results_{timestamp}.csv"

        with open(filename, "w", newline="") as csvfile:
            fieldnames = [
                "timestamp",
                "endpoint",
                "method",
                "status_code",
                "response_time",
                "error",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for result in self.results:
                writer.writerow(
                    {
                        "timestamp": result.timestamp.isoformat(),
                        "endpoint": result.endpoint,
                        "method": result.method,
                        "status_code": result.status_code,
                        "response_time": result.response_time,
                        "error": result.error or "",
                    }
                )

        logger.info(f"Results saved to {filename}")

    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()


async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="HMS Performance Load Tester")
    parser.add_argument(
        "--url", default="http://localhost:8000", help="Base URL for testing"
    )
    parser.add_argument(
        "--users", type=int, default=100, help="Number of concurrent users"
    )
    parser.add_argument("--requests", type=int, default=10, help="Requests per user")
    parser.add_argument(
        "--ramp-up", type=int, default=30, help="Ramp up time in seconds"
    )
    parser.add_argument(
        "--duration", type=int, default=300, help="Test duration in seconds"
    )
    parser.add_argument("--output", help="Output CSV filename")

    args = parser.parse_args()

    # Test configuration
    config = TestConfig(
        base_url=args.url,
        concurrent_users=args.users,
        requests_per_user=args.requests,
        ramp_up_time=args.ramp_up,
        duration=args.duration,
        endpoints=[],
    )

    # Create and run tester
    tester = PerformanceTester(config)

    try:
        await tester.setup()
        await tester.run_test()
        tester.analyze_results()

        if args.output:
            tester.save_results(args.output)
        else:
            tester.save_results()

        logger.info("\nLoad test completed successfully!")

    except Exception as e:
        logger.error(f"Load test failed: {e}")
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
