"""
comprehensive_performance_test module
"""

import asyncio
import json
import os
import random
import secrets
import sqlite3
import statistics
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psutil
import requests


@dataclass
class PerformanceMetrics:
    timestamp: str
    test_name: str
    response_times: List[float]
    success_rate: float
    error_rate: float
    throughput: float
    cpu_usage: float
    memory_usage: float
    concurrent_users: int
    total_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
class HMSPerformanceTestSuite:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results = []
        self.config = self._load_config()
        self._setup_database()
    def _load_config(self) -> Dict[str, Any]:
        return {
            "endpoints": [
                "/api/auth/login/",
                "/api/patients/",
                "/api/appointments/",
                "/api/ehr/",
                "/api/pharmacy/",
                "/api/lab/",
                "/api/billing/"
            ],
            "load_levels": [10, 50, 100, 250, 500],
            "test_duration": 60,
            "thresholds": {
                "max_response_time": 2.0,
                "min_success_rate": 0.95,
                "max_error_rate": 0.05
            }
        }
    def _setup_database(self):
        conn = sqlite3.connect('performance_results.db')
        cursor = conn.cursor()
        cursor.execute()
        conn.commit()
        conn.close()
    def _monitor_system_resources(self, test_name: str, duration: int) -> Dict[str, float]:
        cpu_usage = []
        memory_usage = []
        def monitor():
            start_time = time.time()
            while time.time() - start_time < duration:
                cpu_usage.append(psutil.cpu_percent(interval=1))
                memory = psutil.virtual_memory()
                memory_usage.append(memory.percent)
                time.sleep(1)
        monitor_thread = threading.Thread(target=monitor)
        monitor_thread.daemon = True
        monitor_thread.start()
        monitor_thread.join(timeout=duration + 5)
        return {
            "avg_cpu": statistics.mean(cpu_usage) if cpu_usage else 0,
            "avg_memory": statistics.mean(memory_usage) if memory_usage else 0,
            "max_cpu": max(cpu_usage) if cpu_usage else 0,
            "max_memory": max(memory_usage) if memory_usage else 0
        }
    def _make_request(self, endpoint: str, user_id: int) -> Dict[str, Any]:
        start_time = time.time()
        result = {
            'user_id': user_id,
            'endpoint': endpoint,
            'start_time': start_time,
            'response_time': 0,
            'status_code': None,
            'success': False,
            'error': None
        }
        try:
            url = f"{self.base_url}{endpoint}"
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': f'HMS-Performance-Test-{user_id}'
            }
            payload = self._generate_payload(endpoint)
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30
            )
            result['response_time'] = time.time() - start_time
            result['status_code'] = response.status_code
            result['success'] = response.status_code < 400
        except Exception as e:
            result['response_time'] = time.time() - start_time
            result['error'] = str(e)
            result['success'] = False
        return result
    def _generate_payload(self, endpoint: str) -> Dict[str, Any]:
        import random
        import uuid
        payloads = {
            "/api/auth/login/": {
                "username": f"doctor{secrets.secrets.randbelow(1, 100)}@hospital.com",
                "password": "securepassword123"
            },
            "/api/patients/": {
                "first_name": f"Patient{secrets.secrets.randbelow(1, 1000)}",
                "last_name": f"Test{secrets.secrets.randbelow(1, 1000)}",
                "date_of_birth": "1990-01-01",
                "gender": secrets.choice(["M", "F"]),
                "email": f"patient{secrets.secrets.randbelow(1, 1000)}@example.com"
            },
            "/api/appointments/": {
                "patient_id": secrets.secrets.randbelow(1, 1000),
                "doctor_id": secrets.secrets.randbelow(1, 100),
                "appointment_date": "2024-01-15T10:00:00Z",
                "appointment_type": secrets.choice(["CONSULTATION", "FOLLOW_UP", "EMERGENCY"])
            },
            "/api/ehr/": {
                "patient_id": secrets.secrets.randbelow(1, 1000),
                "diagnosis": f"Diagnosis {secrets.secrets.randbelow(1, 50)}",
                "treatment": f"Treatment {secrets.secrets.randbelow(1, 30)}",
                "notes": "Patient condition stable"
            },
            "/api/pharmacy/": {
                "patient_id": secrets.secrets.randbelow(1, 1000),
                "medication": f"Medication {secrets.secrets.randbelow(1, 100)}",
                "dosage": f"{secrets.secrets.randbelow(1, 10)}mg",
                "frequency": secrets.choice(["daily", "twice_daily", "three_times_daily"])
            },
            "/api/lab/": {
                "patient_id": secrets.secrets.randbelow(1, 1000),
                "test_type": secrets.choice(["CBC", "CMP", "LIPID_PANEL", "TSH", "HBA1C"]),
                "test_date": "2024-01-15",
                "status": "COMPLETED"
            },
            "/api/billing/": {
                "patient_id": secrets.secrets.randbelow(1, 1000),
                "amount": round(secrets.uniform(100, 1000), 2),
                "billing_status": secrets.choice(["PENDING", "APPROVED", "PAID"])
            }
        }
        return payloads.get(endpoint, {"test": "data"})
    def run_load_test(self, test_name: str, concurrent_users: int, duration: int) -> PerformanceMetrics:
        print(f"🚀 Running {test_name} with {concurrent_users} concurrent users for {duration} seconds")
        resource_monitor = threading.Thread(
            target=self._monitor_resources_bg,
            args=(test_name, duration)
        )
        resource_monitor.daemon = True
        resource_monitor.start()
        start_time = time.time()
        results = []
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            while time.time() - start_time < duration:
                for user_id in range(concurrent_users):
                    endpoint = secrets.choice(self.config["endpoints"])
                    future = executor.submit(self._make_request, endpoint, user_id)
                    futures.append(future)
                    time.sleep(0.1)
                for future in as_completed(futures[:100]):  
                    try:
                        result = future.result(timeout=30)
                        results.append(result)
                    except Exception as e:
                        print(f"Request failed: {e}")
                futures = futures[100:]  
        metrics = self._calculate_metrics(results, test_name, concurrent_users, duration)
        self.results.append(metrics)
        self._store_metrics(metrics)
        print(f"✅ {test_name} completed: {metrics.avg_response_time:.2f}s avg, {metrics.p95_response_time:.2f}s p95")
        return metrics
    def _monitor_resources_bg(self, test_name: str, duration: int):
        resource_data = self._monitor_system_resources(test_name, duration)
        print(f"📊 Resource usage for {test_name}: CPU {resource_data['avg_cpu']:.1f}%, Memory {resource_data['avg_memory']:.1f}%")
    def _calculate_metrics(self, results: List[Dict[str, Any]], test_name: str,
                          concurrent_users: int, duration: int) -> PerformanceMetrics:
        if not results:
            return PerformanceMetrics(
                timestamp=datetime.now().isoformat(),
                test_name=test_name,
                response_times=[],
                success_rate=0,
                error_rate=1,
                throughput=0,
                cpu_usage=0,
                memory_usage=0,
                concurrent_users=concurrent_users,
                total_requests=0,
                failed_requests=0,
                avg_response_time=0,
                min_response_time=0,
                max_response_time=0,
                p50_response_time=0,
                p95_response_time=0,
                p99_response_time=0
            )
        response_times = [r['response_time'] for r in results if r['response_time'] is not None]
        successful_requests = [r for r in results if r['success']]
        failed_requests = [r for r in results if not r['success']]
        total_requests = len(results)
        success_count = len(successful_requests)
        failed_count = len(failed_requests)
        success_rate = success_count / total_requests if total_requests > 0 else 0
        error_rate = failed_count / total_requests if total_requests > 0 else 0
        throughput = total_requests / duration if duration > 0 else 0
        return PerformanceMetrics(
            timestamp=datetime.now().isoformat(),
            test_name=test_name,
            response_times=response_times,
            success_rate=success_rate,
            error_rate=error_rate,
            throughput=throughput,
            cpu_usage=0,  
            memory_usage=0,  
            concurrent_users=concurrent_users,
            total_requests=total_requests,
            failed_requests=failed_count,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            p50_response_time=np.percentile(response_times, 50) if response_times else 0,
            p95_response_time=np.percentile(response_times, 95) if response_times else 0,
            p99_response_time=np.percentile(response_times, 99) if response_times else 0
        )
    def _store_metrics(self, metrics: PerformanceMetrics):
        conn = sqlite3.connect('performance_results.db')
        cursor = conn.cursor()
        cursor.execute(, (
            metrics.timestamp, metrics.test_name, metrics.concurrent_users,
            metrics.avg_response_time, metrics.p95_response_time, metrics.p99_response_time,
            metrics.success_rate, metrics.error_rate, metrics.throughput, metrics.cpu_usage,
            metrics.memory_usage, metrics.total_requests, metrics.failed_requests,
            json.dumps(asdict(metrics))
        ))
        conn.commit()
        conn.close()
    def run_healthcare_scenarios(self) -> Dict[str, PerformanceMetrics]:
        print("🏥 Running healthcare-specific scenarios")
        scenarios = {
            "emergency_surge": self._run_emergency_surge(),
            "pharmacy_peak": self._run_pharmacy_peak(),
            "lab_processing": self._run_lab_processing(),
            "mass_casualty": self._run_mass_casualty()
        }
        return scenarios
    def _run_emergency_surge(self) -> PerformanceMetrics:
        print("🚨 Simulating emergency department surge (100 patients/hour)")
        return self.run_load_test("emergency_surge", 50, 120)
    def _run_pharmacy_peak(self) -> PerformanceMetrics:
        print("💊 Simulating pharmacy peak load (200 prescriptions/hour)")
        return self.run_load_test("pharmacy_peak", 80, 120)
    def _run_lab_processing(self) -> PerformanceMetrics:
        print("🔬 Simulating laboratory result processing (150 tests/hour)")
        return self.run_load_test("lab_processing", 60, 120)
    def _run_mass_casualty(self) -> PerformanceMetrics:
        print("🚑 Simulating mass casualty incident (500 patients in 2 hours)")
        return self.run_load_test("mass_casualty", 200, 180)
    def run_stress_test(self) -> List[PerformanceMetrics]:
        print("💥 Running stress test to find system limits")
        stress_results = []
        current_users = 100
        while current_users <= 2000:
            try:
                metrics = self.run_load_test(f"stress_{current_users}users", current_users, 30)
                stress_results.append(metrics)
                if (metrics.error_rate > self.config["thresholds"]["max_error_rate"] or
                    metrics.p95_response_time > self.config["thresholds"]["max_response_time"]):
                    print(f"⚠️  Thresholds exceeded at {current_users} users")
                    break
                current_users += 100
            except Exception as e:
                print(f"❌ Stress test failed at {current_users} users: {e}")
                break
        return stress_results
    def generate_report(self) -> Dict[str, Any]:
        print("📊 Generating comprehensive performance report")
        report = {
            "test_summary": {
                "total_tests": len(self.results),
                "timestamp": datetime.now().isoformat(),
                "system_status": self._evaluate_system_status()
            },
            "baseline_metrics": self._get_baseline_metrics(),
            "load_test_results": self._get_load_test_results(),
            "healthcare_scenarios": self._get_healthcare_results(),
            "stress_test_results": self._get_stress_test_results(),
            "bottlenecks": self._identify_bottlenecks(),
            "recommendations": self._generate_recommendations(),
            "scalability_analysis": self._analyze_scalability()
        }
        return report
    def _evaluate_system_status(self) -> str:
        if not self.results:
            return "UNKNOWN"
        latest = self.results[-1]
        thresholds = self.config["thresholds"]
        if (latest.error_rate <= thresholds["max_error_rate"] and
            latest.p95_response_time <= thresholds["max_response_time"] and
            latest.success_rate >= thresholds["min_success_rate"]):
            return "OPTIMAL"
        else:
            return "DEGRADED"
    def _get_baseline_metrics(self) -> Dict[str, Any]:
        baseline = [r for r in self.results if "baseline" in r.test_name]
        if baseline:
            return asdict(baseline[0])
        return {}
    def _get_load_test_results(self) -> List[Dict[str, Any]]:
        load_tests = [r for r in self.results if "load_test" in r.test_name]
        return [asdict(r) for r in load_tests]
    def _get_healthcare_results(self) -> List[Dict[str, Any]]:
        healthcare_tests = [r for r in self.results if r.test_name in
                          ["emergency_surge", "pharmacy_peak", "lab_processing", "mass_casualty"]]
        return [asdict(r) for r in healthcare_tests]
    def _get_stress_test_results(self) -> List[Dict[str, Any]]:
        stress_tests = [r for r in self.results if "stress" in r.test_name]
        return [asdict(r) for r in stress_tests]
    def _identify_bottlenecks(self) -> List[Dict[str, Any]]:
        bottlenecks = []
        thresholds = self.config["thresholds"]
        for metrics in self.results:
            if metrics.p95_response_time > thresholds["max_response_time"]:
                bottlenecks.append({
                    "type": "RESPONSE_TIME",
                    "test": metrics.test_name,
                    "severity": "HIGH",
                    "value": metrics.p95_response_time,
                    "threshold": thresholds["max_response_time"],
                    "description": f"95th percentile response time exceeds threshold in {metrics.test_name}"
                })
            if metrics.error_rate > thresholds["max_error_rate"]:
                bottlenecks.append({
                    "type": "ERROR_RATE",
                    "test": metrics.test_name,
                    "severity": "HIGH",
                    "value": metrics.error_rate,
                    "threshold": thresholds["max_error_rate"],
                    "description": f"Error rate exceeds threshold in {metrics.test_name}"
                })
        return bottlenecks
    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        recommendations = [
            {
                "priority": "HIGH",
                "category": "DATABASE_OPTIMIZATION",
                "description": "Implement database query optimization and indexing",
                "expected_improvement": "30-50% reduction in response times",
                "implementation_complexity": "HIGH"
            },
            {
                "priority": "HIGH",
                "category": "CACHING",
                "description": "Implement Redis caching for frequently accessed data",
                "expected_improvement": "40-60% reduction in database load",
                "implementation_complexity": "MEDIUM"
            },
            {
                "priority": "MEDIUM",
                "category": "LOAD_BALANCING",
                "description": "Implement horizontal scaling with load balancers",
                "expected_improvement": "Improved scalability and availability",
                "implementation_complexity": "MEDIUM"
            },
            {
                "priority": "MEDIUM",
                "category": "MONITORING",
                "description": "Implement comprehensive monitoring and alerting",
                "expected_improvement": "Better visibility into performance issues",
                "implementation_complexity": "LOW"
            }
        ]
        return recommendations
    def _analyze_scalability(self) -> Dict[str, Any]:
        if not self.results:
            return {}
        load_tests = [r for r in self.results if "load_test" in r.test_name]
        if not load_tests:
            return {}
        max_users = max(r.concurrent_users for r in load_tests)
        baseline = load_tests[0]
        peak = max(load_tests, key=lambda x: x.concurrent_users)
        scaling_efficiency = (peak.throughput / baseline.throughput) / (peak.concurrent_users / baseline.concurrent_users)
        return {
            "current_capacity": max_users,
            "scaling_efficiency": scaling_efficiency,
            "maximum_sustainable_users": max_users if scaling_efficiency > 0.7 else int(max_users * 0.7),
            "recommendation": "Good scaling efficiency" if scaling_efficiency > 0.8 else "Scaling optimization needed"
        }
    def export_results(self, format_type: str = "json") -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report = self.generate_report()
        if format_type == "json":
            filename = f"hms_performance_report_{timestamp}.json"
            with open(filename, "w") as f:
                json.dump(report, f, indent=2, default=str)
        elif format_type == "html":
            filename = f"hms_performance_report_{timestamp}.html"
            self._generate_html_report(report, filename)
        print(f"📄 Report exported to {filename}")
        return filename
    def _generate_html_report(self, report: Dict[str, Any], filename: str):
        html_content = f
        with open(filename, "w") as f:
            f.write(html_content)
    def _format_summary_metrics(self, report: Dict[str, Any]) -> str:
        if not self.results:
            return "<p>No test results available</p>"
        latest = self.results[-1]
        return f
    def _format_bottlenecks(self, bottlenecks: List[Dict[str, Any]]) -> str:
        if not bottlenecks:
            return "<p>No bottlenecks identified</p>"
        html = ""
        for bottleneck in bottlenecks:
            html += f
        return html
    def _format_recommendations(self, recommendations: List[Dict[str, Any]]) -> str:
        html = ""
        for rec in recommendations:
            html += f
        return html
    def _format_scalability(self, scalability: Dict[str, Any]) -> str:
        if not scalability:
            return "<p>No scalability data available</p>"
        return f
    def _format_healthcare_scenarios(self, scenarios: List[Dict[str, Any]]) -> str:
        if not scenarios:
            return "<p>No healthcare scenario data available</p>"
        html = "<table><tr><th>Scenario</th><th>Response Time</th><th>Success Rate</th><th>Throughput</th></tr>"
        for scenario in scenarios:
            html += f
        html += "</table>"
        return html
def main():
    print("🚀 Starting HMS Enterprise-Grade Performance Testing Suite")
    test_suite = HMSPerformanceTestSuite()
    try:
        print("\n📊 Phase 1: Baseline Performance Testing")
        baseline = test_suite.run_load_test("baseline", 10, 60)
        print("\n🔥 Phase 2: Load Testing")
        for users in [50, 100, 250, 500]:
            test_suite.run_load_test(f"load_test_{users}users", users, 120)
        print("\n🏥 Phase 3: Healthcare-Specific Scenarios")
        test_suite.run_healthcare_scenarios()
        print("\n💥 Phase 4: Stress Testing")
        stress_results = test_suite.run_stress_test()
        print("\n📋 Generating Reports")
        json_report = test_suite.export_results("json")
        html_report = test_suite.export_results("html")
        report = test_suite.generate_report()
        print(f"\n🎯 Performance Testing Complete!")
        print(f"📊 Total Tests: {report['test_summary']['total_tests']}")
        print(f"📈 System Status: {report['test_summary']['system_status']}")
        print(f"⚠️ Bottlenecks: {len(report['bottlenecks'])}")
        print(f"💡 Recommendations: {len(report['recommendations'])}")
        print(f"📄 Reports: {json_report}, {html_report}")
        return True
    except Exception as e:
        print(f"❌ Performance testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)