import asyncio
import json
import logging
import time
import statistics
import threading
import tracemalloc
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import requests
import psutil
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from dataclasses import dataclass, asdict
import sqlite3
import os
import sys
import subprocess
import multiprocessing
import timeit
from contextlib import contextmanager
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
    disk_io: Dict[str, float]
    network_io: Dict[str, float]
    database_connections: int
    cache_hit_rate: float
    concurrent_users: int
    total_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
class PerformanceTestSuite:
    def __init__(self, config_file: str = "performance_config.json"):
        self.config = self._load_config(config_file)
        self.results_db = "performance_results.db"
        self.metrics_history = []
        self.setup_logging()
        self.setup_database()
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        default_config = {
            "base_url": "http://localhost:8000",
            "frontend_url": "http://localhost:3000",
            "max_concurrent_users": 1000,
            "test_duration": 300,
            "ramp_up_time": 60,
            "think_time": 1,
            "monitoring_interval": 5,
            "thresholds": {
                "max_response_time": 2.0,
                "min_success_rate": 0.95,
                "max_cpu_usage": 0.8,
                "max_memory_usage": 0.8,
                "max_error_rate": 0.05
            },
            "endpoints": {
                "authentication": "/api/auth/login/",
                "patients": "/api/patients/",
                "appointments": "/api/appointments/",
                "ehr": "/api/ehr/",
                "pharmacy": "/api/pharmacy/",
                "lab": "/api/lab/",
                "billing": "/api/billing/"
            },
            "healthcare_scenarios": {
                "emergency_surge": {
                    "patients_per_hour": 100,
                    "duration": 60,
                    "critical_path": True
                },
                "pharmacy_peak": {
                    "prescriptions_per_hour": 200,
                    "duration": 120,
                    "critical_path": True
                },
                "lab_results": {
                    "tests_per_hour": 150,
                    "duration": 90,
                    "critical_path": True
                }
            }
        }
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        return default_config
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('performance_testing.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    def setup_database(self):
        conn = sqlite3.connect(self.results_db)
        cursor = conn.cursor()
        cursor.execute()
        cursor.execute()
        conn.commit()
        conn.close()
    @contextmanager
    def monitor_resources(self, test_name: str):
        resource_monitor = ResourceMonitor(test_name)
        resource_monitor.start()
        try:
            yield resource_monitor
        finally:
            resource_monitor.stop()
            self.logger.info(f"Resource monitoring completed for {test_name}")
    async def run_load_test(self, test_name: str, concurrent_users: int, duration: int) -> PerformanceMetrics:
        self.logger.info(f"Starting load test: {test_name} with {concurrent_users} concurrent users")
        with self.monitor_resources(test_name) as monitor:
            start_time = time.time()
            results = await self._execute_load_test(concurrent_users, duration)
            end_time = time.time()
            metrics = self._calculate_metrics(results, test_name, concurrent_users, end_time - start_time)
            metrics.cpu_usage = monitor.get_avg_cpu()
            metrics.memory_usage = monitor.get_avg_memory()
            metrics.disk_io = monitor.get_disk_io()
            metrics.network_io = monitor.get_network_io()
            metrics.database_connections = monitor.get_db_connections()
            metrics.cache_hit_rate = monitor.get_cache_hit_rate()
            self._store_metrics(metrics)
            self.metrics_history.append(metrics)
            self.logger.info(f"Load test completed: {test_name}")
            return metrics
    async def _execute_load_test(self, concurrent_users: int, duration: int) -> List[Dict[str, Any]]:
        results = []
        end_time = time.time() + duration
        async def make_request(user_id: int) -> Dict[str, Any]:
            request_start = time.time()
            result = {
                'user_id': user_id,
                'start_time': request_start,
                'end_time': None,
                'response_time': None,
                'status_code': None,
                'success': False,
                'error': None
            }
            try:
                endpoint = self._select_realistic_endpoint()
                url = f"{self.config['base_url']}{endpoint}"
                headers = {
                    'Content-Type': 'application/json',
                    'User-Agent': f'HMS-Performance-Test-User-{user_id}'
                }
                response = requests.post(
                    url,
                    json=self._generate_realistic_payload(endpoint),
                    headers=headers,
                    timeout=30
                )
                result['end_time'] = time.time()
                result['response_time'] = result['end_time'] - result['start_time']
                result['status_code'] = response.status_code
                result['success'] = response.status_code < 400
            except Exception as e:
                result['end_time'] = time.time()
                result['response_time'] = result['end_time'] - result['start_time']
                result['error'] = str(e)
                result['success'] = False
            return result
        tasks = []
        for user_id in range(concurrent_users):
            if time.time() < end_time:
                task = asyncio.create_task(make_request(user_id))
                tasks.append(task)
                await asyncio.sleep(self.config['think_time'])
        completed_results = await asyncio.gather(*tasks, return_exceptions=True)
        valid_results = []
        for result in completed_results:
            if isinstance(result, dict):
                valid_results.append(result)
            else:
                self.logger.error(f"Request failed with exception: {result}")
        return valid_results
    def _select_realistic_endpoint(self) -> str:
        endpoints = [
            ('/api/auth/login/', 0.15),
            ('/api/patients/', 0.25),
            ('/api/appointments/', 0.20),
            ('/api/ehr/', 0.15),
            ('/api/pharmacy/', 0.10),
            ('/api/lab/', 0.10),
            ('/api/billing/', 0.05)
        ]
        import random
        rand_val = random.random()
        cumulative = 0
        for endpoint, probability in endpoints:
            cumulative += probability
            if rand_val <= cumulative:
                return endpoint
        return endpoints[0][0]
    def _generate_realistic_payload(self, endpoint: str) -> Dict[str, Any]:
        import random
        import uuid
        payloads = {
            '/api/auth/login/': {
                'username': f'doctor{random.randint(1, 100)}@hospital.com',
                'password': 'securepassword123'
            },
            '/api/patients/': {
                'first_name': f'Patient{random.randint(1, 1000)}',
                'last_name': f'Test{random.randint(1, 1000)}',
                'date_of_birth': '1990-01-01',
                'gender': random.choice(['M', 'F']),
                'phone': f'555-{random.randint(100, 999)}-{random.randint(1000, 9999)}',
                'email': f'patient{random.randint(1, 1000)}@example.com'
            },
            '/api/appointments/': {
                'patient_id': random.randint(1, 1000),
                'doctor_id': random.randint(1, 100),
                'appointment_date': '2024-01-15T10:00:00Z',
                'appointment_type': random.choice(['CONSULTATION', 'FOLLOW_UP', 'EMERGENCY']),
                'reason': 'Regular checkup'
            },
            '/api/ehr/': {
                'patient_id': random.randint(1, 1000),
                'diagnosis': f'Diagnosis {random.randint(1, 50)}',
                'treatment': f'Treatment {random.randint(1, 30)}',
                'notes': 'Patient condition stable'
            },
            '/api/pharmacy/': {
                'patient_id': random.randint(1, 1000),
                'medication': f'Medication {random.randint(1, 100)}',
                'dosage': f'{random.randint(1, 10)}mg',
                'frequency': random.choice(['daily', 'twice_daily', 'three_times_daily']),
                'duration': f'{random.randint(1, 30)} days'
            },
            '/api/lab/': {
                'patient_id': random.randint(1, 1000),
                'test_type': random.choice(['CBC', 'CMP', 'LIPID_PANEL', 'TSH', 'HBA1C']),
                'test_date': '2024-01-15',
                'results': 'Normal range',
                'status': 'COMPLETED'
            },
            '/api/billing/': {
                'patient_id': random.randint(1, 1000),
                'appointment_id': random.randint(1, 500),
                'amount': round(random.uniform(100, 1000), 2),
                'insurance_provider': random.choice(['BLUE_CROSS', 'AETNA', 'UNITED', 'CIGNA']),
                'billing_status': random.choice(['PENDING', 'APPROVED', 'PAID'])
            }
        }
        return payloads.get(endpoint, {'test': 'data'})
    def _calculate_metrics(self, results: List[Dict[str, Any]], test_name: str,
                          concurrent_users: int, duration: float) -> PerformanceMetrics:
        if not results:
            raise ValueError("No results to calculate metrics from")
        response_times = [r['response_time'] for r in results if r['response_time']]
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
            cpu_usage=0.0,  
            memory_usage=0.0,  
            disk_io={},
            network_io={},
            database_connections=0,
            cache_hit_rate=0.0,
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
        conn = sqlite3.connect(self.results_db)
        cursor = conn.cursor()
        cursor.execute(, (
            metrics.timestamp, metrics.test_name, metrics.avg_response_time,
            metrics.min_response_time, metrics.max_response_time, metrics.p50_response_time,
            metrics.p95_response_time, metrics.p99_response_time, metrics.success_rate,
            metrics.error_rate, metrics.throughput, metrics.cpu_usage, metrics.memory_usage,
            metrics.concurrent_users, metrics.total_requests, metrics.failed_requests,
            len(metrics.response_times), json.dumps(asdict(metrics))
        ))
        conn.commit()
        conn.close()
    async def run_stress_test(self, test_name: str, max_users: int, step_size: int = 50) -> List[PerformanceMetrics]:
        self.logger.info(f"Starting stress test: {test_name}")
        results = []
        current_users = step_size
        while current_users <= max_users:
            try:
                metrics = await self.run_load_test(
                    f"{test_name}_{current_users}_users",
                    current_users,
                    60  
                )
                results.append(metrics)
                if (metrics.error_rate > self.config['thresholds']['max_error_rate'] or
                    metrics.p95_response_time > self.config['thresholds']['max_response_time']):
                    self.logger.warning(f"Thresholds exceeded at {current_users} users")
                    break
                current_users += step_size
            except Exception as e:
                self.logger.error(f"Stress test failed at {current_users} users: {e}")
                break
        return results
    async def run_healthcare_specific_tests(self) -> Dict[str, PerformanceMetrics]:
        self.logger.info("Starting healthcare-specific performance tests")
        healthcare_results = {}
        healthcare_results['emergency_surge'] = await self._simulate_emergency_surge()
        healthcare_results['pharmacy_peak'] = await self._simulate_pharmacy_peak()
        healthcare_results['lab_results'] = await self._simulate_lab_processing()
        healthcare_results['mass_casualty'] = await self._simulate_mass_casualty()
        return healthcare_results
    async def _simulate_emergency_surge(self) -> PerformanceMetrics:
        self.logger.info("Simulating emergency department patient surge")
        surge_config = self.config['healthcare_scenarios']['emergency_surge']
        patients_per_hour = surge_config['patients_per_hour']
        duration = surge_config['duration']
        concurrent_users = int(patients_per_hour / 60 * 10)  
        return await self.run_load_test(
            "emergency_surge",
            concurrent_users,
            duration * 60  
        )
    async def _simulate_pharmacy_peak(self) -> PerformanceMetrics:
        self.logger.info("Simulating pharmacy peak load")
        peak_config = self.config['healthcare_scenarios']['pharmacy_peak']
        prescriptions_per_hour = peak_config['prescriptions_per_hour']
        duration = peak_config['duration']
        concurrent_users = int(prescriptions_per_hour / 60 * 5)  
        return await self.run_load_test(
            "pharmacy_peak",
            concurrent_users,
            duration * 60
        )
    async def _simulate_lab_processing(self) -> PerformanceMetrics:
        self.logger.info("Simulating laboratory result processing")
        lab_config = self.config['healthcare_scenarios']['lab_results']
        tests_per_hour = lab_config['tests_per_hour']
        duration = lab_config['duration']
        concurrent_users = int(tests_per_hour / 60 * 3)  
        return await self.run_load_test(
            "lab_processing",
            concurrent_users,
            duration * 60
        )
    async def _simulate_mass_casualty(self) -> PerformanceMetrics:
        self.logger.info("Simulating mass casualty incident response")
        patients_per_hour = 250
        duration = 120  
        concurrent_users = int(patients_per_hour / 60 * 15)  
        return await self.run_load_test(
            "mass_casualty",
            concurrent_users,
            duration * 60
        )
    def generate_performance_report(self) -> Dict[str, Any]:
        report = {
            'test_summary': {
                'total_tests': len(self.metrics_history),
                'timestamp': datetime.now().isoformat(),
                'system_status': 'OPTIMAL' if self._check_system_health() else 'DEGRADED'
            },
            'performance_metrics': {},
            'bottlenecks': self._identify_bottlenecks(),
            'recommendations': self._generate_recommendations(),
            'healthcare_scenarios': {},
            'scalability_analysis': self._analyze_scalability()
        }
        for metrics in self.metrics_history:
            test_type = metrics.test_name.split('_')[0]
            if test_type not in report['performance_metrics']:
                report['performance_metrics'][test_type] = []
            report['performance_metrics'][test_type].append(asdict(metrics))
        return report
    def _check_system_health(self) -> bool:
        if not self.metrics_history:
            return True
        latest_metrics = self.metrics_history[-1]
        thresholds = self.config['thresholds']
        return (
            latest_metrics.error_rate <= thresholds['max_error_rate'] and
            latest_metrics.p95_response_time <= thresholds['max_response_time'] and
            latest_metrics.success_rate >= thresholds['min_success_rate']
        )
    def _identify_bottlenecks(self) -> List[Dict[str, Any]]:
        bottlenecks = []
        if not self.metrics_history:
            return bottlenecks
        latest_metrics = self.metrics_history[-1]
        thresholds = self.config['thresholds']
        if latest_metrics.p95_response_time > thresholds['max_response_time']:
            bottlenecks.append({
                'type': 'RESPONSE_TIME',
                'severity': 'HIGH',
                'description': f'95th percentile response time ({latest_metrics.p95_response_time:.2f}s) exceeds threshold ({thresholds["max_response_time"]}s)',
                'recommendation': 'Optimize database queries and implement caching'
            })
        if latest_metrics.error_rate > thresholds['max_error_rate']:
            bottlenecks.append({
                'type': 'ERROR_RATE',
                'severity': 'HIGH',
                'description': f'Error rate ({latest_metrics.error_rate:.2%}) exceeds threshold ({thresholds["max_error_rate"]:.2%})',
                'recommendation': 'Implement better error handling and retry mechanisms'
            })
        if latest_metrics.cpu_usage > thresholds['max_cpu_usage']:
            bottlenecks.append({
                'type': 'CPU_USAGE',
                'severity': 'MEDIUM',
                'description': f'CPU usage ({latest_metrics.cpu_usage:.2%}) exceeds threshold ({thresholds["max_cpu_usage"]:.2%})',
                'recommendation': 'Scale horizontally or optimize CPU-intensive operations'
            })
        if latest_metrics.memory_usage > thresholds['max_memory_usage']:
            bottlenecks.append({
                'type': 'MEMORY_USAGE',
                'severity': 'MEDIUM',
                'description': f'Memory usage ({latest_metrics.memory_usage:.2%}) exceeds threshold ({thresholds["max_memory_usage"]:.2%})',
                'recommendation': 'Implement memory optimization and garbage collection'
            })
        return bottlenecks
    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        recommendations = []
        recommendations.append({
            'priority': 'HIGH',
            'category': 'CACHING',
            'description': 'Implement Redis caching for frequently accessed data',
            'expected_improvement': '30-50% reduction in response times',
            'implementation_complexity': 'MEDIUM'
        })
        recommendations.append({
            'priority': 'HIGH',
            'category': 'DATABASE',
            'description': 'Optimize database queries and add proper indexing',
            'expected_improvement': '20-40% improvement in database performance',
            'implementation_complexity': 'HIGH'
        })
        recommendations.append({
            'priority': 'MEDIUM',
            'category': 'LOAD_BALANCING',
            'description': 'Implement load balancing for backend services',
            'expected_improvement': 'Improved scalability and availability',
            'implementation_complexity': 'MEDIUM'
        })
        recommendations.append({
            'priority': 'MEDIUM',
            'category': 'MONITORING',
            'description': 'Implement comprehensive monitoring and alerting',
            'expected_improvement': 'Better visibility into performance issues',
            'implementation_complexity': 'LOW'
        })
        return recommendations
    def _analyze_scalability(self) -> Dict[str, Any]:
        scalability_analysis = {
            'current_capacity': 0,
            'maximum_capacity': 0,
            'scaling_efficiency': 0.0,
            'recommendations': []
        }
        if not self.metrics_history:
            return scalability_analysis
        max_users = max(metrics.concurrent_users for metrics in self.metrics_history)
        scalability_analysis['current_capacity'] = max_users
        for metrics in sorted(self.metrics_history, key=lambda x: x.concurrent_users):
            if metrics.error_rate > 0.05 or metrics.p95_response_time > 2.0:
                scalability_analysis['maximum_capacity'] = metrics.concurrent_users
                break
        if len(self.metrics_history) > 1:
            baseline_metrics = self.metrics_history[0]
            peak_metrics = max(self.metrics_history, key=lambda x: x.concurrent_users)
            scaling_efficiency = (
                peak_metrics.throughput / baseline_metrics.throughput
            ) / (peak_metrics.concurrent_users / baseline_metrics.concurrent_users)
            scalability_analysis['scaling_efficiency'] = scaling_efficiency
        return scalability_analysis
    def export_results(self, format_type: str = 'json'):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if format_type == 'json':
            filename = f'performance_results_{timestamp}.json'
            with open(filename, 'w') as f:
                json.dump(self.generate_performance_report(), f, indent=2)
        elif format_type == 'csv':
            filename = f'performance_results_{timestamp}.csv'
            df = pd.DataFrame([asdict(metrics) for metrics in self.metrics_history])
            df.to_csv(filename, index=False)
        elif format_type == 'html':
            filename = f'performance_report_{timestamp}.html'
            self._generate_html_report(filename)
        self.logger.info(f"Results exported to {filename}")
        return filename
    def _generate_html_report(self, filename: str):
        report = self.generate_performance_report()
        html_content = f
        with open(filename, 'w') as f:
            f.write(html_content)
    def _format_bottlenecks_html(self, bottlenecks: List[Dict[str, Any]]) -> str:
        if not bottlenecks:
            return "<p>No bottlenecks identified</p>"
        html = ""
        for bottleneck in bottlenecks:
            html += f
        return html
    def _format_recommendations_html(self, recommendations: List[Dict[str, Any]]) -> str:
        html = ""
        for rec in recommendations:
            html += f
        return html
    def _format_scalability_html(self, scalability: Dict[str, Any]) -> str:
        return f
class ResourceMonitor:
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.running = False
        self.cpu_usage = []
        self.memory_usage = []
        self.disk_io = []
        self.network_io = []
        self.database_connections = []
        self.cache_hit_rate = []
        self.start_time = None
        self.end_time = None
    def start(self):
        self.running = True
        self.start_time = time.time()
        self.thread = threading.Thread(target=self._monitor_resources)
        self.thread.daemon = True
        self.thread.start()
    def stop(self):
        self.running = False
        self.end_time = time.time()
        if hasattr(self, 'thread'):
            self.thread.join(timeout=5)
    def _monitor_resources(self):
        while self.running:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                self.cpu_usage.append(cpu_percent)
                memory = psutil.virtual_memory()
                self.memory_usage.append(memory.percent)
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    self.disk_io.append({
                        'read_bytes': disk_io.read_bytes,
                        'write_bytes': disk_io.write_bytes,
                        'read_count': disk_io.read_count,
                        'write_count': disk_io.write_count
                    })
                net_io = psutil.net_io_counters()
                if net_io:
                    self.network_io.append({
                        'bytes_sent': net_io.bytes_sent,
                        'bytes_recv': net_io.bytes_recv,
                        'packets_sent': net_io.packets_sent,
                        'packets_recv': net_io.packets_recv
                    })
                self.database_connections.append(self._get_db_connections())
                self.cache_hit_rate.append(self._get_cache_hit_rate())
                time.sleep(1)  
            except Exception as e:
                print(f"Resource monitoring error: {e}")
                time.sleep(5)  
    def _get_db_connections(self) -> int:
        try:
            import psycopg2
            conn = psycopg2.connect(
                host="localhost",
                database="hms_enterprise",
                user="hms_user",
                password="password"
            )
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM pg_stat_activity;")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except:
            return 0
    def _get_cache_hit_rate(self) -> float:
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            info = r.info()
            hits = info.get('keyspace_hits', 0)
            misses = info.get('keyspace_misses', 0)
            total = hits + misses
            return hits / total if total > 0 else 0.0
        except:
            return 0.0
    def get_avg_cpu(self) -> float:
        return statistics.mean(self.cpu_usage) if self.cpu_usage else 0.0
    def get_avg_memory(self) -> float:
        return statistics.mean(self.memory_usage) if self.memory_usage else 0.0
    def get_disk_io(self) -> Dict[str, float]:
        if not self.disk_io:
            return {}
        total_read = sum(io['read_bytes'] for io in self.disk_io)
        total_write = sum(io['write_bytes'] for io in self.disk_io)
        duration = max(1, (self.end_time or time.time()) - self.start_time)
        return {
            'read_mb_per_sec': total_read / (1024 * 1024) / duration,
            'write_mb_per_sec': total_write / (1024 * 1024) / duration
        }
    def get_network_io(self) -> Dict[str, float]:
        if not self.network_io:
            return {}
        total_sent = sum(io['bytes_sent'] for io in self.network_io)
        total_recv = sum(io['bytes_recv'] for io in self.network_io)
        duration = max(1, (self.end_time or time.time()) - self.start_time)
        return {
            'sent_mb_per_sec': total_sent / (1024 * 1024) / duration,
            'recv_mb_per_sec': total_recv / (1024 * 1024) / duration
        }
    def get_db_connections(self) -> int:
        return int(statistics.mean(self.database_connections)) if self.database_connections else 0
    def get_cache_hit_rate(self) -> float:
        return statistics.mean(self.cache_hit_rate) if self.cache_hit_rate else 0.0
async def main():
    print("🚀 Starting HMS Enterprise-Grade Performance Testing Suite")
    test_suite = PerformanceTestSuite()
    try:
        print("\n📊 Phase 1: Establishing Baseline Performance Metrics")
        baseline_metrics = await test_suite.run_load_test("baseline", 10, 60)
        print(f"✅ Baseline established: {baseline_metrics.avg_response_time:.2f}s avg response time")
        print("\n🔥 Phase 2: Load Testing with Increasing Concurrency")
        load_test_results = []
        for users in [50, 100, 250, 500]:
            metrics = await test_suite.run_load_test(f"load_test_{users}users", users, 120)
            load_test_results.append(metrics)
            print(f"✅ Load test completed for {users} users: {metrics.p95_response_time:.2f}s 95th percentile")
        print("\n⚡ Phase 3: Stress Testing to System Limits")
        stress_results = await test_suite.run_stress_test("stress_test", 2000, 100)
        print(f"✅ Stress testing completed: {len(stress_results)} load levels tested")
        print("\� Phase 4: Healthcare-Specific Performance Testing")
        healthcare_results = await test_suite.run_healthcare_specific_tests()
        for scenario, metrics in healthcare_results.items():
            print(f"✅ {scenario}: {metrics.avg_response_time:.2f}s avg response time")
        print("\n📋 Generating Performance Report")
        report = test_suite.generate_performance_report()
        json_file = test_suite.export_results('json')
        csv_file = test_suite.export_results('csv')
        html_file = test_suite.export_results('html')
        print(f"\n🎯 Performance Testing Complete!")
        print(f"📊 Results saved to:")
        print(f"   - JSON: {json_file}")
        print(f"   - CSV: {csv_file}")
        print(f"   - HTML: {html_file}")
        print(f"\n📈 Performance Summary:")
        print(f"   - Total Tests: {len(test_suite.metrics_history)}")
        print(f"   - Bottlenecks: {len(report['bottlenecks'])}")
        print(f"   - Recommendations: {len(report['recommendations'])}")
        print(f"   - System Status: {report['test_summary']['system_status']}")
    except Exception as e:
        print(f"❌ Performance testing failed: {e}")
        raise
if __name__ == "__main__":
    asyncio.run(main())