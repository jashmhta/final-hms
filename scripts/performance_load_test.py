#!/usr/bin/env python3
"""
Enterprise-Grade HMS Performance Load Testing and Certification System
Comprehensive performance assessment for healthcare management systems
"""

import asyncio
import aiohttp
import time
import statistics
import json
import logging
import sys
import os
import psutil
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

class PerformanceMetric(Enum):
    RESPONSE_TIME = "Response Time"
    THROUGHPUT = "Throughput"
    ERROR_RATE = "Error Rate"
    MEMORY_USAGE = "Memory Usage"
    CPU_USAGE = "CPU Usage"
    DATABASE_CONNECTIONS = "Database Connections"
    CACHE_HIT_RATE = "Cache Hit Rate"

class TestPhase(Enum):
    RAMP_UP = "Ramp Up"
    SUSTAINED_LOAD = "Sustained Load"
    SPIKE_TEST = "Spike Test"
    DEGRADATION_TEST = "Degradation Test"
    RECOVERY_TEST = "Recovery Test"

@dataclass
class PerformanceResult:
    metric: PerformanceMetric
    value: float
    unit: str
    threshold: float
    status: str  # PASS, FAIL, WARNING
    timestamp: datetime
    details: Dict[str, Any] = None

@dataclass
class LoadTestScenario:
    name: str
    concurrent_users: int
    duration_seconds: int
    requests_per_second: int
    test_phases: List[TestPhase]
    success_criteria: Dict[str, float]

class PerformanceLoadTester:
    """Comprehensive performance load testing for HMS"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[PerformanceResult] = []
        self.logger = self._setup_logger()
        self.system_metrics = []

        # Performance thresholds (enterprise-grade requirements)
        self.thresholds = {
            PerformanceMetric.RESPONSE_TIME: 0.1,  # 100ms
            PerformanceMetric.THROUGHPUT: 1000,   # 1000 RPS
            PerformanceMetric.ERROR_RATE: 0.01,   # 1%
            PerformanceMetric.MEMORY_USAGE: 80,    # 80%
            PerformanceMetric.CPU_USAGE: 70,       # 70%
            PerformanceMetric.DATABASE_CONNECTIONS: 100,  # 100 connections
            PerformanceMetric.CACHE_HIT_RATE: 0.9   # 90%
        }

        # Test scenarios
        self.scenarios = [
            LoadTestScenario(
                name="Baseline Performance",
                concurrent_users=1000,
                duration_seconds=300,
                requests_per_second=100,
                test_phases=[TestPhase.RAMP_UP, TestPhase.SUSTAINED_LOAD],
                success_criteria={
                    "avg_response_time": 0.1,
                    "p95_response_time": 0.2,
                    "error_rate": 0.01,
                    "throughput": 100
                }
            ),
            LoadTestScenario(
                name="High Load Test",
                concurrent_users=10000,
                duration_seconds=600,
                requests_per_second=500,
                test_phases=[TestPhase.RAMP_UP, TestPhase.SUSTAINED_LOAD],
                success_criteria={
                    "avg_response_time": 0.2,
                    "p95_response_time": 0.5,
                    "error_rate": 0.02,
                    "throughput": 500
                }
            ),
            LoadTestScenario(
                name="Peak Load Test",
                concurrent_users=50000,
                duration_seconds=300,
                requests_per_second=1000,
                test_phases=[TestPhase.RAMP_UP, TestPhase.SUSTAINED_LOAD, TestPhase.SPIKE_TEST],
                success_criteria={
                    "avg_response_time": 0.3,
                    "p95_response_time": 1.0,
                    "error_rate": 0.05,
                    "throughput": 1000
                }
            ),
            LoadTestScenario(
                name="Enterprise Scale Test",
                concurrent_users=100000,
                duration_seconds=1200,
                requests_per_second=2000,
                test_phases=[TestPhase.RAMP_UP, TestPhase.SUSTAINED_LOAD, TestPhase.SPIKE_TEST, TestPhase.DEGRADATION_TEST, TestPhase.RECOVERY_TEST],
                success_criteria={
                    "avg_response_time": 0.5,
                    "p95_response_time": 2.0,
                    "error_rate": 0.1,
                    "throughput": 2000
                }
            )
        ]

    def _setup_logger(self):
        """Setup logging for performance testing"""
        logger = logging.getLogger('PerformanceLoadTester')
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '[%(asctime)s] %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    async def simulate_user_session(self, session: aiohttp.ClientSession, user_id: int, scenario: LoadTestScenario) -> Dict[str, Any]:
        """Simulate a complete user session"""
        start_time = time.time()
        session_results = {
            "user_id": user_id,
            "requests_made": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "errors": [],
            "total_time": 0
        }

        try:
            # User login
            login_start = time.time()
            login_data = {
                "username": f"perf_test_user_{user_id}",
                "password": "test_password_123"
            }

            async with session.post(f"{self.base_url}/api/auth/login/", json=login_data) as response:
                login_time = time.time() - login_start
                session_results["response_times"].append(login_time)
                session_results["requests_made"] += 1

                if response.status == 200:
                    session_results["successful_requests"] += 1
                    data = await response.json()
                    token = data.get("access")
                    headers = {"Authorization": f"Bearer {token}"}
                else:
                    session_results["failed_requests"] += 1
                    session_results["errors"].append(f"Login failed: {response.status}")
                    return session_results

            # Simulate typical user workflow
            workflow_steps = [
                ("get_patients", f"{self.base_url}/api/patients/"),
                ("get_appointments", f"{self.base_url}/api/appointments/"),
                ("get_labs", f"{self.base_url}/api/lab/"),
                ("get_pharmacy", f"{self.base_url}/api/pharmacy/"),
                ("get_billing", f"{self.base_url}/api/billing/")
            ]

            for step_name, endpoint in workflow_steps:
                request_start = time.time()
                try:
                    async with session.get(endpoint, headers=headers) as response:
                        response_time = time.time() - request_start
                        session_results["response_times"].append(response_time)
                        session_results["requests_made"] += 1

                        if response.status == 200:
                            session_results["successful_requests"] += 1
                        else:
                            session_results["failed_requests"] += 1
                            session_results["errors"].append(f"{step_name} failed: {response.status}")

                except Exception as e:
                    session_results["failed_requests"] += 1
                    session_results["errors"].append(f"{step_name} error: {str(e)}")

            # Create appointment (write operation)
            appointment_start = time.time()
            appointment_data = {
                "patient_id": 1,
                "appointment_date": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                "department": "General Practice",
                "reason": "Performance test appointment"
            }

            try:
                async with session.post(f"{self.base_url}/api/appointments/", json=appointment_data, headers=headers) as response:
                    response_time = time.time() - appointment_start
                    session_results["response_times"].append(response_time)
                    session_results["requests_made"] += 1

                    if response.status in [200, 201]:
                        session_results["successful_requests"] += 1
                    else:
                        session_results["failed_requests"] += 1
                        session_results["errors"].append(f"Appointment creation failed: {response.status}")

            except Exception as e:
                session_results["failed_requests"] += 1
                session_results["errors"].append(f"Appointment creation error: {str(e)}")

        except Exception as e:
            session_results["errors"].append(f"Session error: {str(e)}")

        session_results["total_time"] = time.time() - start_time
        return session_results

    async def collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_metrics.append({
                "timestamp": datetime.utcnow(),
                "cpu_percent": cpu_percent,
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "network_sent": psutil.net_io_counters().bytes_sent,
                "network_recv": psutil.net_io_counters().bytes_recv
            })

            # Database metrics (if PostgreSQL is available)
            try:
                result = subprocess.run(
                    ["psql", "-h", "localhost", "-U", "hms_user", "-d", "hms_enterprise", "-c", "SELECT count(*) FROM pg_stat_activity;"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    db_connections = int(result.stdout.strip().split('\n')[-2])
                    self.system_metrics[-1]["db_connections"] = db_connections
            except:
                pass

        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")

    async def run_load_test_scenario(self, scenario: LoadTestScenario) -> Dict[str, Any]:
        """Run a specific load test scenario"""
        self.logger.info(f"Starting load test scenario: {scenario.name}")
        self.logger.info(f"Concurrent users: {scenario.concurrent_users}")
        self.logger.info(f"Duration: {scenario.duration_seconds} seconds")

        # Start system metrics collection
        metrics_task = asyncio.create_task(self._continuous_metrics_collection(scenario.duration_seconds))

        # Create connection pool
        connector = aiohttp.TCPConnector(
            limit=scenario.concurrent_users,
            limit_per_host=scenario.concurrent_users,
            ttl_dns_cache=300,
            use_dns_cache=True
        )

        timeout = aiohttp.ClientTimeout(total=scenario.duration_seconds + 60)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Start user sessions
            tasks = []
            for i in range(scenario.concurrent_users):
                task = asyncio.create_task(self.simulate_user_session(session, i, scenario))
                tasks.append(task)

            # Wait for all sessions to complete
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

        # Stop metrics collection
        metrics_task.cancel()

        # Analyze results
        analysis = self._analyze_load_test_results(results, scenario, start_time, end_time)

        return analysis

    async def _continuous_metrics_collection(self, duration_seconds: int):
        """Continuously collect system metrics"""
        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            await self.collect_system_metrics()
            await asyncio.sleep(5)  # Collect metrics every 5 seconds

    def _analyze_load_test_results(self, results, scenario: LoadTestScenario, start_time: float, end_time: float) -> Dict[str, Any]:
        """Analyze load test results"""
        # Filter out exceptions and extract valid results
        valid_results = [r for r in results if isinstance(r, dict)]
        failed_sessions = [r for r in results if isinstance(r, Exception)]

        # Calculate response time statistics
        all_response_times = []
        for result in valid_results:
            all_response_times.extend(result.get("response_times", []))

        if all_response_times:
            avg_response_time = statistics.mean(all_response_times)
            p95_response_time = statistics.quantiles(all_response_times, n=20)[18]  # 95th percentile
            p99_response_time = statistics.quantiles(all_response_times, n=100)[98]  # 99th percentile
            max_response_time = max(all_response_times)
            min_response_time = min(all_response_times)
        else:
            avg_response_time = p95_response_time = p99_response_time = max_response_time = min_response_time = 0

        # Calculate success rate
        total_requests = sum(r.get("requests_made", 0) for r in valid_results)
        successful_requests = sum(r.get("successful_requests", 0) for r in valid_results)
        failed_requests = sum(r.get("failed_requests", 0) for r in valid_results)

        success_rate = successful_requests / total_requests if total_requests > 0 else 0
        error_rate = failed_requests / total_requests if total_requests > 0 else 0

        # Calculate throughput
        test_duration = end_time - start_time
        throughput = total_requests / test_duration if test_duration > 0 else 0

        # System metrics analysis
        if self.system_metrics:
            avg_cpu = statistics.mean([m.get("cpu_percent", 0) for m in self.system_metrics])
            max_cpu = max([m.get("cpu_percent", 0) for m in self.system_metrics])
            avg_memory = statistics.mean([m.get("memory_percent", 0) for m in self.system_metrics])
            max_memory = max([m.get("memory_percent", 0) for m in self.system_metrics])
            avg_db_connections = statistics.mean([m.get("db_connections", 0) for m in self.system_metrics if "db_connections" in m])
        else:
            avg_cpu = max_cpu = avg_memory = max_memory = avg_db_connections = 0

        # Evaluate against criteria
        criteria_results = {}
        for criteria, threshold in scenario.success_criteria.items():
            if criteria == "avg_response_time":
                criteria_results[criteria] = avg_response_time <= threshold
            elif criteria == "p95_response_time":
                criteria_results[criteria] = p95_response_time <= threshold
            elif criteria == "error_rate":
                criteria_results[criteria] = error_rate <= threshold
            elif criteria == "throughput":
                criteria_results[criteria] = throughput >= threshold

        # Overall scenario status
        scenario_passed = all(criteria_results.values())

        # Create performance results
        performance_results = [
            PerformanceResult(
                metric=PerformanceMetric.RESPONSE_TIME,
                value=avg_response_time,
                unit="seconds",
                threshold=self.thresholds[PerformanceMetric.RESPONSE_TIME],
                status="PASS" if avg_response_time <= self.thresholds[PerformanceMetric.RESPONSE_TIME] else "FAIL",
                timestamp=datetime.utcnow(),
                details={
                    "p95": p95_response_time,
                    "p99": p99_response_time,
                    "min": min_response_time,
                    "max": max_response_time
                }
            ),
            PerformanceResult(
                metric=PerformanceMetric.THROUGHPUT,
                value=throughput,
                unit="requests/second",
                threshold=self.thresholds[PerformanceMetric.THROUGHPUT],
                status="PASS" if throughput >= self.thresholds[PerformanceMetric.THROUGHPUT] else "FAIL",
                timestamp=datetime.utcnow(),
                details={
                    "total_requests": total_requests,
                    "test_duration": test_duration
                }
            ),
            PerformanceResult(
                metric=PerformanceMetric.ERROR_RATE,
                value=error_rate,
                unit="percentage",
                threshold=self.thresholds[PerformanceMetric.ERROR_RATE],
                status="PASS" if error_rate <= self.thresholds[PerformanceMetric.ERROR_RATE] else "FAIL",
                timestamp=datetime.utcnow(),
                details={
                    "successful_requests": successful_requests,
                    "failed_requests": failed_requests,
                    "failed_sessions": len(failed_sessions)
                }
            ),
            PerformanceResult(
                metric=PerformanceMetric.CPU_USAGE,
                value=avg_cpu,
                unit="percentage",
                threshold=self.thresholds[PerformanceMetric.CPU_USAGE],
                status="PASS" if avg_cpu <= self.thresholds[PerformanceMetric.CPU_USAGE] else "FAIL",
                timestamp=datetime.utcnow(),
                details={
                    "max_cpu": max_cpu
                }
            ),
            PerformanceResult(
                metric=PerformanceMetric.MEMORY_USAGE,
                value=avg_memory,
                unit="percentage",
                threshold=self.thresholds[PerformanceMetric.MEMORY_USAGE],
                status="PASS" if avg_memory <= self.thresholds[PerformanceMetric.MEMORY_USAGE] else "FAIL",
                timestamp=datetime.utcnow(),
                details={
                    "max_memory": max_memory
                }
            ),
            PerformanceResult(
                metric=PerformanceMetric.DATABASE_CONNECTIONS,
                value=avg_db_connections,
                unit="connections",
                threshold=self.thresholds[PerformanceMetric.DATABASE_CONNECTIONS],
                status="PASS" if avg_db_connections <= self.thresholds[PerformanceMetric.DATABASE_CONNECTIONS] else "FAIL",
                timestamp=datetime.utcnow(),
                details={}
            )
        ]

        self.results.extend(performance_results)

        return {
            "scenario": scenario.name,
            "duration": test_duration,
            "concurrent_users": scenario.concurrent_users,
            "results": {
                "response_times": {
                    "avg": avg_response_time,
                    "p95": p95_response_time,
                    "p99": p99_response_time,
                    "min": min_response_time,
                    "max": max_response_time
                },
                "throughput": throughput,
                "success_rate": success_rate,
                "error_rate": error_rate,
                "system_metrics": {
                    "cpu_usage": {"avg": avg_cpu, "max": max_cpu},
                    "memory_usage": {"avg": avg_memory, "max": max_memory},
                    "db_connections": avg_db_connections
                },
                "requests": {
                    "total": total_requests,
                    "successful": successful_requests,
                    "failed": failed_requests,
                    "failed_sessions": len(failed_sessions)
                }
            },
            "criteria_results": criteria_results,
            "scenario_passed": scenario_passed,
            "performance_results": [asdict(r) for r in performance_results]
        }

    async def run_comprehensive_performance_test(self) -> Dict[str, Any]:
        """Run comprehensive performance testing"""
        self.logger.info("Starting comprehensive performance load testing")

        scenario_results = []

        for scenario in self.scenarios:
            try:
                result = await self.run_load_test_scenario(scenario)
                scenario_results.append(result)
                self.logger.info(f"Scenario '{scenario.name}' completed: {'PASSED' if result['scenario_passed'] else 'FAILED'}")

                # Add delay between scenarios to allow system to recover
                await asyncio.sleep(30)

            except Exception as e:
                self.logger.error(f"Error running scenario '{scenario.name}': {e}")
                scenario_results.append({
                    "scenario": scenario.name,
                    "error": str(e),
                    "scenario_passed": False
                })

        # Generate performance report
        performance_report = self.generate_performance_report(scenario_results)

        self.logger.info(f"Performance testing completed. {sum(1 for s in scenario_results if s.get('scenario_passed', False))}/{len(scenario_results)} scenarios passed")

        return performance_report

    def generate_performance_report(self, scenario_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        # Calculate overall metrics
        total_scenarios = len(scenario_results)
        passed_scenarios = sum(1 for s in scenario_results if s.get('scenario_passed', False))

        # Aggregate performance metrics
        all_response_times = []
        all_throughput = []
        all_error_rates = []

        for result in scenario_results:
            if 'results' in result:
                all_response_times.append(result['results']['response_times']['avg'])
                all_throughput.append(result['results']['throughput'])
                all_error_rates.append(result['results']['error_rate'])

        overall_avg_response_time = statistics.mean(all_response_times) if all_response_times else 0
        overall_max_throughput = max(all_throughput) if all_throughput else 0
        overall_avg_error_rate = statistics.mean(all_error_rates) if all_error_rates else 0

        # Calculate performance score
        response_time_score = max(0, 100 - (overall_avg_response_time / self.thresholds[PerformanceMetric.RESPONSE_TIME] * 100))
        throughput_score = min(100, (overall_max_throughput / self.thresholds[PerformanceMetric.THROUGHPUT] * 100))
        error_rate_score = max(0, 100 - (overall_avg_error_rate / self.thresholds[PerformanceMetric.ERROR_RATE] * 100))

        overall_performance_score = (response_time_score + throughput_score + error_rate_score) / 3

        # Determine certification status
        certification_status = "PASS"
        if passed_scenarios < total_scenarios * 0.8:  # 80% of scenarios must pass
            certification_status = "FAIL"
        elif overall_performance_score < 80:
            certification_status = "FAIL"

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "test_summary": {
                "total_scenarios": total_scenarios,
                "passed_scenarios": passed_scenarios,
                "failed_scenarios": total_scenarios - passed_scenarios,
                "success_rate": (passed_scenarios / total_scenarios * 100) if total_scenarios > 0 else 0
            },
            "performance_metrics": {
                "overall_avg_response_time": overall_avg_response_time,
                "overall_max_throughput": overall_max_throughput,
                "overall_avg_error_rate": overall_avg_error_rate,
                "performance_score": overall_performance_score,
                "response_time_score": response_time_score,
                "throughput_score": throughput_score,
                "error_rate_score": error_rate_score
            },
            "certification_criteria": {
                "response_time_threshold": self.thresholds[PerformanceMetric.RESPONSE_TIME],
                "throughput_threshold": self.thresholds[PerformanceMetric.THROUGHPUT],
                "error_rate_threshold": self.thresholds[PerformanceMetric.ERROR_RATE],
                "max_concurrent_users": 100000,
                "certification_status": certification_status
            },
            "scenario_results": scenario_results,
            "detailed_results": [asdict(r) for r in self.results],
            "system_metrics": self.system_metrics,
            "recommendations": self.generate_performance_recommendations(scenario_results),
            "next_benchmark_date": (datetime.utcnow() + timedelta(days=30)).isoformat()
        }

    def generate_performance_recommendations(self, scenario_results: List[Dict[str, Any]]) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []

        # Analyze response times
        slow_scenarios = [s for s in scenario_results if s.get('results', {}).get('response_times', {}).get('avg', 0) > 0.1]
        if slow_scenarios:
            recommendations.append("PERFORMANCE: Implement database query optimization and indexing")
            recommendations.append("PERFORMANCE: Add caching layer for frequently accessed data")
            recommendations.append("PERFORMANCE: Optimize API response payloads")

        # Analyze throughput
        low_throughput_scenarios = [s for s in scenario_results if s.get('results', {}).get('throughput', 0) < 500]
        if low_throughput_scenarios:
            recommendations.append("SCALABILITY: Implement horizontal scaling with load balancing")
            recommendations.append("SCALABILITY: Optimize application server configuration")
            recommendations.append("SCALABILITY: Consider implementing database read replicas")

        # Analyze error rates
        high_error_scenarios = [s for s in scenario_results if s.get('results', {}).get('error_rate', 0) > 0.05]
        if high_error_scenarios:
            recommendations.append("RELIABILITY: Implement circuit breaker pattern")
            recommendations.append("RELIABILITY: Add proper error handling and retry logic")
            recommendations.append("RELIABILITY: Increase connection pool sizes")

        # Analyze system resources
        high_cpu_scenarios = [s for s in scenario_results if s.get('results', {}).get('system_metrics', {}).get('cpu_usage', {}).get('avg', 0) > 70]
        if high_cpu_scenarios:
            recommendations.append("INFRASTRUCTURE: Scale up server resources or optimize CPU usage")
            recommendations.append("INFRASTRUCTURE: Implement CPU-intensive task offloading")

        high_memory_scenarios = [s for s in scenario_results if s.get('results', {}).get('system_metrics', {}).get('memory_usage', {}).get('avg', 0) > 80]
        if high_memory_scenarios:
            recommendations.append("INFRASTRUCTURE: Optimize memory usage and garbage collection")
            recommendations.append("INFRASTRUCTURE: Consider memory optimization or scaling")

        # General recommendations
        recommendations.append("MONITORING: Implement comprehensive application monitoring")
        recommendations.append("MONITORING: Set up alerting for performance thresholds")
        recommendations.append("OPTIMIZATION: Implement database query optimization")
        recommendations.append("SCALABILITY: Test auto-scaling configurations")
        recommendations.append("PERFORMANCE: Conduct regular performance benchmarks")

        return recommendations

    def generate_performance_charts(self, report_data: Dict[str, Any]):
        """Generate performance visualization charts"""
        try:
            # Create performance metrics comparison chart
            scenarios = [s['scenario'] for s in report_data['scenario_results']]
            response_times = [s['results']['response_times']['avg'] for s in report_data['scenario_results']]
            throughputs = [s['results']['throughput'] for s in report_data['scenario_results']]
            error_rates = [s['results']['error_rate'] * 100 for s in report_data['scenario_results']]

            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

            # Response times
            ax1.bar(scenarios, response_times, color='skyblue')
            ax1.set_title('Average Response Time by Scenario')
            ax1.set_ylabel('Response Time (seconds)')
            ax1.axhline(y=0.1, color='red', linestyle='--', label='Threshold')
            ax1.legend()
            ax1.tick_params(axis='x', rotation=45)

            # Throughput
            ax2.bar(scenarios, throughputs, color='lightgreen')
            ax2.set_title('Throughput by Scenario')
            ax2.set_ylabel('Requests per Second')
            ax2.axhline(y=1000, color='red', linestyle='--', label='Threshold')
            ax2.legend()
            ax2.tick_params(axis='x', rotation=45)

            # Error rates
            ax3.bar(scenarios, error_rates, color='salmon')
            ax3.set_title('Error Rate by Scenario')
            ax3.set_ylabel('Error Rate (%)')
            ax3.axhline(y=1, color='red', linestyle='--', label='Threshold')
            ax3.legend()
            ax3.tick_params(axis='x', rotation=45)

            # Performance score
            scores = [100 if s['scenario_passed'] else 0 for s in report_data['scenario_results']]
            ax4.bar(scenarios, scores, color=['green' if s > 0 else 'red' for s in scores])
            ax4.set_title('Scenario Pass/Fail Status')
            ax4.set_ylabel('Pass (100) / Fail (0)')
            ax4.set_ylim(0, 100)
            ax4.tick_params(axis='x', rotation=45)

            plt.tight_layout()
            chart_path = "/home/azureuser/helli/enterprise-grade-hms/performance_charts.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()

            self.logger.info(f"Performance charts saved to: {chart_path}")

        except Exception as e:
            self.logger.error(f"Error generating performance charts: {e}")


async def main():
    """Main execution function"""
    print("⚡ Enterprise-Grade HMS Performance Certification")
    print("=" * 50)

    # Initialize performance tester
    tester = PerformanceLoadTester()

    # Run comprehensive performance test
    performance_report = await tester.run_comprehensive_performance_test()

    # Generate performance charts
    tester.generate_performance_charts(performance_report)

    # Print summary
    print(f"\n📊 Performance Assessment Summary:")
    print(f"Total Scenarios: {performance_report['test_summary']['total_scenarios']}")
    print(f"Passed Scenarios: {performance_report['test_summary']['passed_scenarios']}")
    print(f"Success Rate: {performance_report['test_summary']['success_rate']:.1f}%")
    print(f"Overall Performance Score: {performance_report['performance_metrics']['performance_score']:.1f}/100")
    print(f"Max Throughput: {performance_report['performance_metrics']['overall_max_throughput']:.1f} RPS")
    print(f"Avg Response Time: {performance_report['performance_metrics']['overall_avg_response_time']:.3f}s")
    print(f"Certification Status: {performance_report['certification_criteria']['certification_status']}")

    # Save detailed report
    report_path = "/home/azureuser/helli/enterprise-grade-hms/performance_certification_report.json"
    with open(report_path, 'w') as f:
        json.dump(performance_report, f, indent=2, default=str)

    print(f"\n📄 Detailed performance report saved to: {report_path}")

    # Return certification status
    return performance_report['certification_criteria']['certification_status'] == "PASS"


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)