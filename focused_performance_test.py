"""
focused_performance_test module
"""

import json
import random
import sqlite3
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List

import numpy as np
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
class FocusedPerformanceTestSuite:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results = []
        self.test_scenarios = [
            {"name": "baseline", "users": 10, "duration": 30},
            {"name": "light_load", "users": 50, "duration": 60},
            {"name": "moderate_load", "users": 100, "duration": 60},
            {"name": "heavy_load", "users": 250, "duration": 60},
            {"name": "peak_load", "users": 500, "duration": 30},
        ]
        self.healthcare_scenarios = [
            {"name": "emergency_surge", "users": 80, "duration": 60},
            {"name": "pharmacy_peak", "users": 120, "duration": 60},
            {"name": "lab_processing", "users": 60, "duration": 60},
            {"name": "mass_casualty", "users": 150, "duration": 90},
        ]
    def _monitor_resources(self, duration: int) -> Dict[str, float]:
        cpu_samples = []
        memory_samples = []
        def monitor():
            start_time = time.time()
            while time.time() - start_time < duration:
                cpu_samples.append(psutil.cpu_percent(interval=1))
                memory = psutil.virtual_memory()
                memory_samples.append(memory.percent)
                time.sleep(1)
        monitor_thread = threading.Thread(target=monitor)
        monitor_thread.daemon = True
        monitor_thread.start()
        monitor_thread.join(timeout=duration + 5)
        return {
            "avg_cpu": statistics.mean(cpu_samples) if cpu_samples else 0,
            "avg_memory": statistics.mean(memory_samples) if memory_samples else 0,
            "max_cpu": max(cpu_samples) if cpu_samples else 0,
            "max_memory": max(memory_samples) if memory_samples else 0
        }
    def _make_request(self, user_id: int) -> Dict[str, Any]:
        start_time = time.time()
        result = {
            'user_id': user_id,
            'start_time': start_time,
            'response_time': 0,
            'status_code': 0,
            'success': False,
            'error': None
        }
        try:
            response = requests.get(self.base_url, timeout=30)
            result['response_time'] = time.time() - start_time
            result['status_code'] = response.status_code
            result['success'] = response.status_code == 200
        except Exception as e:
            result['response_time'] = time.time() - start_time
            result['error'] = str(e)
            result['success'] = False
        return result
    def run_test_scenario(self, scenario: Dict[str, Any]) -> PerformanceMetrics:
        name = scenario["name"]
        users = scenario["users"]
        duration = scenario["duration"]
        print(f"🚀 Running {name} with {users} concurrent users for {duration} seconds")
        resource_monitor = threading.Thread(
            target=self._monitor_resources_bg,
            args=(name, duration)
        )
        resource_monitor.daemon = True
        resource_monitor.start()
        start_time = time.time()
        results = []
        request_count = 0
        with ThreadPoolExecutor(max_workers=users) as executor:
            futures = []
            while time.time() - start_time < duration:
                for user_id in range(users):
                    future = executor.submit(self._make_request, user_id)
                    futures.append(future)
                    request_count += 1
                completed_futures = []
                for future in as_completed(futures[:100]):  
                    try:
                        result = future.result(timeout=30)
                        results.append(result)
                        completed_futures.append(future)
                    except Exception as e:
                        print(f"Request failed: {e}")
                futures = [f for f in futures if f not in completed_futures]
                time.sleep(0.01)
        for future in futures:
            try:
                result = future.result(timeout=30)
                results.append(result)
            except Exception as e:
                print(f"Final request failed: {e}")
        metrics = self._calculate_metrics(results, name, users, duration)
        self.results.append(metrics)
        print(f"✅ {name} completed: {metrics.avg_response_time:.3f}s avg, {metrics.p95_response_time:.3f}s p95, {metrics.success_rate:.1%} success rate")
        return metrics
    def _monitor_resources_bg(self, test_name: str, duration: int):
        resource_data = self._monitor_resources(duration)
        print(f"📊 {test_name} resources: CPU {resource_data['avg_cpu']:.1f}%, Memory {resource_data['avg_memory']:.1f}%")
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
    def run_comprehensive_test(self) -> Dict[str, Any]:
        print("🎯 Starting Comprehensive Performance Testing")
        print("\n📊 Phase 1: Standard Load Testing")
        load_results = []
        for scenario in self.test_scenarios:
            metrics = self.run_test_scenario(scenario)
            load_results.append(metrics)
        print("\n🏥 Phase 2: Healthcare-Specific Scenarios")
        healthcare_results = []
        for scenario in self.healthcare_scenarios:
            metrics = self.run_test_scenario(scenario)
            healthcare_results.append(metrics)
        print("\n💥 Phase 3: Stress Testing")
        stress_results = self._run_stress_test()
        report = self._generate_comprehensive_report(load_results, healthcare_results, stress_results)
        return report
    def _run_stress_test(self) -> List[PerformanceMetrics]:
        stress_results = []
        stress_levels = [750, 1000, 1500]
        for users in stress_levels:
            try:
                print(f"🔥 Stress testing with {users} users")
                metrics = self.run_test_scenario({
                    "name": f"stress_{users}users",
                    "users": users,
                    "duration": 30
                })
                stress_results.append(metrics)
                if metrics.error_rate > 0.1 or metrics.p95_response_time > 5.0:
                    print(f"⚠️ System overloaded at {users} users")
                    break
            except Exception as e:
                print(f"❌ Stress test failed at {users} users: {e}")
                break
        return stress_results
    def _generate_comprehensive_report(self, load_results: List[PerformanceMetrics],
                                     healthcare_results: List[PerformanceMetrics],
                                     stress_results: List[PerformanceMetrics]) -> Dict[str, Any]:
        print("\n📋 Generating Performance Report")
        all_results = load_results + healthcare_results + stress_results
        latest_result = all_results[-1] if all_results else None
        system_status = "OPTIMAL"
        if latest_result and (latest_result.error_rate > 0.05 or latest_result.p95_response_time > 2.0):
            system_status = "DEGRADED"
        bottlenecks = []
        for result in all_results:
            if result.p95_response_time > 2.0:
                bottlenecks.append({
                    "type": "HIGH_RESPONSE_TIME",
                    "test": result.test_name,
                    "value": result.p95_response_time,
                    "threshold": 2.0
                })
            if result.error_rate > 0.05:
                bottlenecks.append({
                    "type": "HIGH_ERROR_RATE",
                    "test": result.test_name,
                    "value": result.error_rate,
                    "threshold": 0.05
                })
        recommendations = [
            {
                "priority": "HIGH",
                "category": "CACHING",
                "description": "Implement Redis caching for static content",
                "expected_improvement": "40-60% faster response times",
                "complexity": "MEDIUM"
            },
            {
                "priority": "MEDIUM",
                "category": "DATABASE",
                "description": "Optimize database queries and add indexing",
                "expected_improvement": "20-30% better performance",
                "complexity": "HIGH"
            },
            {
                "priority": "MEDIUM",
                "category": "SCALING",
                "description": "Implement horizontal scaling with load balancers",
                "expected_improvement": "Better handling of high traffic",
                "complexity": "MEDIUM"
            }
        ]
        max_sustainable_users = 500
        if stress_results:
            successful_stress = [r for r in stress_results if r.error_rate <= 0.05]
            if successful_stress:
                max_sustainable_users = max(r.concurrent_users for r in successful_stress)
        report = {
            "test_summary": {
                "total_tests": len(all_results),
                "timestamp": datetime.now().isoformat(),
                "system_status": system_status,
                "max_sustainable_users": max_sustainable_users
            },
            "load_test_results": [asdict(r) for r in load_results],
            "healthcare_scenarios": [asdict(r) for r in healthcare_results],
            "stress_test_results": [asdict(r) for r in stress_results],
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "performance_summary": {
                "best_response_time": min(r.avg_response_time for r in all_results) if all_results else 0,
                "worst_response_time": max(r.avg_response_time for r in all_results) if all_results else 0,
                "average_response_time": statistics.mean(r.avg_response_time for r in all_results) if all_results else 0,
                "best_success_rate": max(r.success_rate for r in all_results) if all_results else 0,
                "worst_success_rate": min(r.success_rate for r in all_results) if all_results else 0
            }
        }
        return report
    def export_report(self, report: Dict[str, Any], format_type: str = "json") -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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
        for result in report["load_test_results"]:
            status_class = "success" if result["success_rate"] > 0.95 else "warning" if result["success_rate"] > 0.9 else "error"
            html_content += f
        html_content += 
        for result in report["healthcare_scenarios"]:
            status_class = "success" if result["success_rate"] > 0.95 else "warning" if result["success_rate"] > 0.9 else "error"
            html_content += f
        html_content += 
        if report["bottlenecks"]:
            for bottleneck in report["bottlenecks"]:
                html_content += f
        else:
            html_content += "<p>No critical bottlenecks identified</p>"
        html_content += 
        for rec in report["recommendations"]:
            html_content += f
        html_content += 
        with open(filename, "w") as f:
            f.write(html_content)
def main():
    print("🚀 Starting Focused Performance Testing Suite for HMS Enterprise-Grade")
    test_suite = FocusedPerformanceTestSuite()
    try:
        report = test_suite.run_comprehensive_test()
        json_file = test_suite.export_report(report, "json")
        html_file = test_suite.export_report(report, "html")
        print("\n🎯 Performance Testing Complete!")
        print(f"📊 Total Tests: {report['test_summary']['total_tests']}")
        print(f"📈 System Status: {report['test_summary']['system_status']}")
        print(f"⚠️ Bottlenecks: {len(report['bottlenecks'])}")
        print(f"💡 Recommendations: {len(report['recommendations'])}")
        print(f"👥 Max Sustainable Users: {report['test_summary']['max_sustainable_users']}")
        print(f"📄 Reports: {json_file}, {html_file}")
        return True
    except Exception as e:
        print(f"❌ Performance testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)