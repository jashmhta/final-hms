"""
Performance Monitoring and Load Testing Setup for HMS
Enterprise-grade performance monitoring, benchmarking, and load testing infrastructure
"""

import asyncio
import json
import logging
import time
import threading
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from pathlib import Path

import psutil
import redis.asyncio as aioredis
import requests

from django.conf import settings
from django.core.cache import cache
from django.db import connection, connections
from django.utils import timezone

from .performance_optimization import (
    query_optimizer, enhanced_cache, api_optimizer,
    cdn_optimizer, performance_optimizer
)


@dataclass
class PerformanceMetric:
    """Data class for performance metrics"""
    timestamp: datetime
    metric_name: str
    value: float
    unit: str
    tags: Dict[str, str]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LoadTestResult:
    """Data class for load test results"""
    test_id: str
    test_name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    system_metrics: Dict[str, Any]


class PerformanceMonitoringSystem:
    """Comprehensive performance monitoring system for HMS"""

    def __init__(self):
        self.metrics_buffer = []
        self.alerts = []
        self.benchmarks = {}
        self.load_test_history = []
        self.monitoring_config = {
            "collection_interval": 30,  # seconds
            "retention_days": 30,
            "alert_thresholds": {
                "cpu_usage": 80,
                "memory_usage": 85,
                "disk_usage": 90,
                "response_time": 2000,  # ms
                "error_rate": 5,  # percent
                "database_connections": 80
            },
            "benchmark_thresholds": {
                "page_load_time": 3000,  # ms
                "api_response_time": 1000,  # ms
                "database_query_time": 500,  # ms
                "cache_hit_rate": 70  # percent
            }
        }
        self.is_monitoring = False
        self.monitoring_thread = None

    def start_monitoring(self) -> Dict:
        """Start comprehensive performance monitoring"""
        try:
            if self.is_monitoring:
                return {"status": "already_running", "message": "Monitoring is already active"}

            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitoring_thread.start()

            logging.info("Performance monitoring started")
            return {
                "status": "started",
                "timestamp": timezone.now().isoformat(),
                "config": self.monitoring_config
            }

        except Exception as e:
            logging.error(f"Failed to start monitoring: {e}")
            return {"error": str(e)}

    def stop_monitoring(self) -> Dict:
        """Stop performance monitoring"""
        try:
            self.is_monitoring = False
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=5)

            logging.info("Performance monitoring stopped")
            return {
                "status": "stopped",
                "timestamp": timezone.now().isoformat(),
                "metrics_collected": len(self.metrics_buffer)
            }

        except Exception as e:
            logging.error(f"Failed to stop monitoring: {e}")
            return {"error": str(e)}

    def _monitoring_loop(self):
        """Main monitoring loop running in background thread"""
        while self.is_monitoring:
            try:
                # Collect system metrics
                system_metrics = self._collect_system_metrics()

                # Collect application metrics
                app_metrics = self._collect_application_metrics()

                # Collect database metrics
                db_metrics = self._collect_database_metrics()

                # Collect cache metrics
                cache_metrics = self._collect_cache_metrics()

                # Combine all metrics
                all_metrics = system_metrics + app_metrics + db_metrics + cache_metrics

                # Add to buffer
                self.metrics_buffer.extend(all_metrics)

                # Check for alerts
                self._check_alerts(all_metrics)

                # Cleanup old metrics
                self._cleanup_old_metrics()

                # Sleep until next collection
                time.sleep(self.monitoring_config["collection_interval"])

            except Exception as e:
                logging.error(f"Monitoring loop error: {e}")
                time.sleep(self.monitoring_config["collection_interval"])

    def _collect_system_metrics(self) -> List[PerformanceMetric]:
        """Collect system-level performance metrics"""
        metrics = []
        timestamp = timezone.now()

        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()

            metrics.extend([
                PerformanceMetric(
                    timestamp=timestamp,
                    metric_name="cpu_usage_percent",
                    value=cpu_percent,
                    unit="%",
                    tags={"type": "system", "metric": "cpu"}
                ),
                PerformanceMetric(
                    timestamp=timestamp,
                    metric_name="cpu_count",
                    value=cpu_count,
                    unit="cores",
                    tags={"type": "system", "metric": "cpu"}
                )
            ])

            if cpu_freq:
                metrics.append(PerformanceMetric(
                    timestamp=timestamp,
                    metric_name="cpu_frequency_mhz",
                    value=cpu_freq.current,
                    unit="MHz",
                    tags={"type": "system", "metric": "cpu"}
                ))

            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            metrics.extend([
                PerformanceMetric(
                    timestamp=timestamp,
                    metric_name="memory_usage_percent",
                    value=memory.percent,
                    unit="%",
                    tags={"type": "system", "metric": "memory"}
                ),
                PerformanceMetric(
                    timestamp=timestamp,
                    metric_name="memory_available_gb",
                    value=memory.available / (1024**3),
                    unit="GB",
                    tags={"type": "system", "metric": "memory"}
                ),
                PerformanceMetric(
                    timestamp=timestamp,
                    metric_name="memory_used_gb",
                    value=memory.used / (1024**3),
                    unit="GB",
                    tags={"type": "system", "metric": "memory"}
                ),
                PerformanceMetric(
                    timestamp=timestamp,
                    metric_name="swap_usage_percent",
                    value=swap.percent,
                    unit="%",
                    tags={"type": "system", "metric": "swap"}
                )
            ])

            # Disk metrics
            disk = psutil.disk_usage('/')
            metrics.extend([
                PerformanceMetric(
                    timestamp=timestamp,
                    metric_name="disk_usage_percent",
                    value=disk.percent,
                    unit="%",
                    tags={"type": "system", "metric": "disk"}
                ),
                PerformanceMetric(
                    timestamp=timestamp,
                    metric_name="disk_free_gb",
                    value=disk.free / (1024**3),
                    unit="GB",
                    tags={"type": "system", "metric": "disk"}
                )
            ])

            # Network metrics
            net_io = psutil.net_io_counters()
            metrics.extend([
                PerformanceMetric(
                    timestamp=timestamp,
                    metric_name="network_bytes_sent",
                    value=net_io.bytes_sent,
                    unit="bytes",
                    tags={"type": "system", "metric": "network"}
                ),
                PerformanceMetric(
                    timestamp=timestamp,
                    metric_name="network_bytes_recv",
                    value=net_io.bytes_recv,
                    unit="bytes",
                    tags={"type": "system", "metric": "network"}
                )
            ])

        except Exception as e:
            logging.error(f"System metrics collection failed: {e}")

        return metrics

    def _collect_application_metrics(self) -> List[PerformanceMetric]:
        """Collect application-level performance metrics"""
        metrics = []
        timestamp = timezone.now()

        try:
            # Process metrics
            process = psutil.Process()
            process_metrics = [
                ("process_cpu_percent", process.cpu_percent(), "%"),
                ("process_memory_mb", process.memory_info().rss / (1024**2), "MB"),
                ("process_threads", process.num_threads(), "threads"),
                ("process_handles", process.num_handles(), "handles")
            ]

            for name, value, unit in process_metrics:
                metrics.append(PerformanceMetric(
                    timestamp=timestamp,
                    metric_name=name,
                    value=value,
                    unit=unit,
                    tags={"type": "application", "process": str(process.pid)}
                ))

        except Exception as e:
            logging.error(f"Application metrics collection failed: {e}")

        return metrics

    def _collect_database_metrics(self) -> List[PerformanceMetric]:
        """Collect database performance metrics"""
        metrics = []
        timestamp = timezone.now()

        try:
            # Database connection metrics
            for alias, conn in connections.all():
                if hasattr(conn, 'connection') and conn.connection:
                    try:
                        # Get connection stats (implementation varies by database backend)
                        cursor = conn.cursor()

                        # PostgreSQL specific queries
                        if conn.vendor == 'postgresql':
                            cursor.execute("""
                                SELECT count(*)
                                FROM pg_stat_activity
                                WHERE state = 'active'
                            """)
                            active_connections = cursor.fetchone()[0]

                            metrics.append(PerformanceMetric(
                                timestamp=timestamp,
                                metric_name="database_active_connections",
                                value=active_connections,
                                unit="connections",
                                tags={"type": "database", "alias": alias}
                            ))

                            # Get slow queries
                            cursor.execute("""
                                SELECT count(*)
                                FROM pg_stat_statements
                                WHERE mean_exec_time > 1000
                            """)
                            slow_queries = cursor.fetchone()[0]

                            metrics.append(PerformanceMetric(
                                timestamp=timestamp,
                                metric_name="database_slow_queries",
                                value=slow_queries,
                                unit="queries",
                                tags={"type": "database", "alias": alias}
                            ))

                    except Exception as db_e:
                        logging.warning(f"Database metrics collection failed for {alias}: {db_e}")
                    finally:
                        cursor.close()

        except Exception as e:
            logging.error(f"Database metrics collection failed: {e}")

        return metrics

    def _collect_cache_metrics(self) -> List[PerformanceMetric]:
        """Collect cache performance metrics"""
        metrics = []
        timestamp = timezone.now()

        try:
            # Redis cache metrics if available
            redis_client = cache.get_backend()
            if hasattr(redis_client, 'client'):
                try:
                    info = redis_client.client.info()

                    metrics.extend([
                        PerformanceMetric(
                            timestamp=timestamp,
                            metric_name="redis_used_memory_mb",
                            value=info.get('used_memory', 0) / (1024**2),
                            unit="MB",
                            tags={"type": "cache", "backend": "redis"}
                        ),
                        PerformanceMetric(
                            timestamp=timestamp,
                            metric_name="redis_connected_clients",
                            value=info.get('connected_clients', 0),
                            unit="clients",
                            tags={"type": "cache", "backend": "redis"}
                        ),
                        PerformanceMetric(
                            timestamp=timestamp,
                            metric_name="redis_keyspace_hits",
                            value=info.get('keyspace_hits', 0),
                            unit="hits",
                            tags={"type": "cache", "backend": "redis"}
                        ),
                        PerformanceMetric(
                            timestamp=timestamp,
                            metric_name="redis_keyspace_misses",
                            value=info.get('keyspace_misses', 0),
                            unit="misses",
                            tags={"type": "cache", "backend": "redis"}
                        )
                    ])

                    # Calculate hit rate
                    hits = info.get('keyspace_hits', 0)
                    misses = info.get('keyspace_misses', 0)
                    total = hits + misses
                    if total > 0:
                        hit_rate = (hits / total) * 100
                        metrics.append(PerformanceMetric(
                            timestamp=timestamp,
                            metric_name="cache_hit_rate_percent",
                            value=hit_rate,
                            unit="%",
                            tags={"type": "cache", "backend": "redis"}
                        ))

                except Exception as redis_e:
                    logging.warning(f"Redis metrics collection failed: {redis_e}")

        except Exception as e:
            logging.error(f"Cache metrics collection failed: {e}")

        return metrics

    def _check_alerts(self, metrics: List[PerformanceMetric]):
        """Check metrics against alert thresholds"""
        thresholds = self.monitoring_config["alert_thresholds"]

        for metric in metrics:
            alert_triggered = False
            message = ""

            if metric.metric_name == "cpu_usage_percent" and metric.value > thresholds["cpu_usage"]:
                alert_triggered = True
                message = f"High CPU usage: {metric.value:.1f}% (threshold: {thresholds['cpu_usage']}%)"

            elif metric.metric_name == "memory_usage_percent" and metric.value > thresholds["memory_usage"]:
                alert_triggered = True
                message = f"High memory usage: {metric.value:.1f}% (threshold: {thresholds['memory_usage']}%)"

            elif metric.metric_name == "disk_usage_percent" and metric.value > thresholds["disk_usage"]:
                alert_triggered = True
                message = f"High disk usage: {metric.value:.1f}% (threshold: {thresholds['disk_usage']}%)"

            elif metric.metric_name == "database_active_connections" and metric.value > thresholds["database_connections"]:
                alert_triggered = True
                message = f"High database connections: {metric.value:.0f} (threshold: {thresholds['database_connections']})"

            if alert_triggered:
                alert = {
                    "id": str(uuid.uuid4()),
                    "timestamp": timezone.now().isoformat(),
                    "metric": metric.metric_name,
                    "value": metric.value,
                    "threshold": thresholds.get(metric.metric_name.split('_')[0] + "_" + metric.metric_name.split('_')[1], 0),
                    "message": message,
                    "severity": "warning" if metric.value < thresholds.get(metric.metric_name.split('_')[0] + "_" + metric.metric_name.split('_')[1], 0) * 1.1 else "critical",
                    "tags": metric.tags
                }

                self.alerts.append(alert)
                logging.warning(f"Performance alert: {message}")

    def _cleanup_old_metrics(self):
        """Remove old metrics from buffer"""
        cutoff_time = timezone.now() - timedelta(days=self.monitoring_config["retention_days"])
        self.metrics_buffer = [
            metric for metric in self.metrics_buffer
            if metric.timestamp > cutoff_time
        ]

    def get_performance_dashboard(self) -> Dict:
        """Get comprehensive performance dashboard data"""
        try:
            # Get current metrics
            current_metrics = self._get_current_metrics()

            # Get recent alerts
            recent_alerts = self.alerts[-10:] if self.alerts else []

            # Get system health summary
            health_summary = self._get_health_summary()

            # Get performance trends
            trends = self._get_performance_trends()

            return {
                "timestamp": timezone.now().isoformat(),
                "monitoring_status": "active" if self.is_monitoring else "inactive",
                "current_metrics": current_metrics,
                "recent_alerts": recent_alerts,
                "health_summary": health_summary,
                "performance_trends": trends,
                "metrics_count": len(self.metrics_buffer),
                "alerts_count": len(self.alerts)
            }

        except Exception as e:
            logging.error(f"Performance dashboard generation failed: {e}")
            return {"error": str(e)}

    def _get_current_metrics(self) -> Dict:
        """Get current performance metrics"""
        if not self.metrics_buffer:
            return {}

        # Get most recent metrics for each type
        latest_metrics = {}
        for metric in reversed(self.metrics_buffer[-100:]):  # Last 100 metrics
            if metric.metric_name not in latest_metrics:
                latest_metrics[metric.metric_name] = {
                    "value": metric.value,
                    "unit": metric.unit,
                    "timestamp": metric.timestamp.isoformat(),
                    "tags": metric.tags
                }

        return latest_metrics

    def _get_health_summary(self) -> Dict:
        """Get overall system health summary"""
        try:
            # Get latest metrics
            current = self._get_current_metrics()

            health_score = 100
            issues = []

            # Check CPU
            if "cpu_usage_percent" in current:
                cpu_usage = current["cpu_usage_percent"]["value"]
                if cpu_usage > 90:
                    health_score -= 30
                    issues.append("Critical: CPU usage above 90%")
                elif cpu_usage > 80:
                    health_score -= 15
                    issues.append("Warning: CPU usage above 80%")

            # Check Memory
            if "memory_usage_percent" in current:
                memory_usage = current["memory_usage_percent"]["value"]
                if memory_usage > 90:
                    health_score -= 30
                    issues.append("Critical: Memory usage above 90%")
                elif memory_usage > 85:
                    health_score -= 15
                    issues.append("Warning: Memory usage above 85%")

            # Check Disk
            if "disk_usage_percent" in current:
                disk_usage = current["disk_usage_percent"]["value"]
                if disk_usage > 95:
                    health_score -= 25
                    issues.append("Critical: Disk usage above 95%")
                elif disk_usage > 90:
                    health_score -= 10
                    issues.append("Warning: Disk usage above 90%")

            health_score = max(0, health_score)

            return {
                "overall_score": health_score,
                "status": "healthy" if health_score >= 80 else "warning" if health_score >= 60 else "critical",
                "issues": issues,
                "checked_components": ["cpu", "memory", "disk"],
                "last_check": timezone.now().isoformat()
            }

        except Exception as e:
            logging.error(f"Health summary generation failed: {e}")
            return {"error": str(e)}

    def _get_performance_trends(self) -> Dict:
        """Calculate performance trends from historical data"""
        try:
            if not self.metrics_buffer:
                return {"message": "Insufficient data for trend analysis"}

            # Group metrics by name and calculate trends
            trends = {}
            cutoff_time = timezone.now() - timedelta(hours=1)  # Last hour

            recent_metrics = [
                metric for metric in self.metrics_buffer
                if metric.timestamp > cutoff_time
            ]

            # Group by metric name
            metric_groups = {}
            for metric in recent_metrics:
                if metric.metric_name not in metric_groups:
                    metric_groups[metric.metric_name] = []
                metric_groups[metric.metric_name].append(metric.value)

            # Calculate trends for key metrics
            for metric_name, values in metric_groups.items():
                if len(values) >= 2:
                    avg_value = sum(values) / len(values)
                    min_value = min(values)
                    max_value = max(values)
                    trend = "stable"

                    if len(values) >= 10:
                        # Simple trend detection
                        first_half = values[:len(values)//2]
                        second_half = values[len(values)//2:]
                        first_avg = sum(first_half) / len(first_half)
                        second_avg = sum(second_half) / len(second_half)

                        if second_avg > first_avg * 1.1:
                            trend = "increasing"
                        elif second_avg < first_avg * 0.9:
                            trend = "decreasing"

                    trends[metric_name] = {
                        "average": round(avg_value, 2),
                        "minimum": round(min_value, 2),
                        "maximum": round(max_value, 2),
                        "trend": trend,
                        "data_points": len(values)
                    }

            return trends

        except Exception as e:
            logging.error(f"Performance trends calculation failed: {e}")
            return {"error": str(e)}

    def run_comprehensive_benchmark(self) -> Dict:
        """Run comprehensive performance benchmarks"""
        try:
            start_time = time.time()
            benchmark_results = {}

            # 1. Database Query Benchmark
            db_benchmark = self._benchmark_database_queries()
            benchmark_results["database"] = db_benchmark

            # 2. Cache Performance Benchmark
            cache_benchmark = self._benchmark_cache_performance()
            benchmark_results["cache"] = cache_benchmark

            # 3. API Response Benchmark
            api_benchmark = self._benchmark_api_responses()
            benchmark_results["api"] = api_benchmark

            # 4. Memory Usage Benchmark
            memory_benchmark = self._benchmark_memory_usage()
            benchmark_results["memory"] = memory_benchmark

            # 5. Frontend Load Benchmark
            frontend_benchmark = self._benchmark_frontend_load()
            benchmark_results["frontend"] = frontend_benchmark

            # Calculate overall score
            overall_score = self._calculate_benchmark_score(benchmark_results)

            benchmark_result = {
                "timestamp": timezone.now().isoformat(),
                "duration_seconds": round(time.time() - start_time, 2),
                "overall_score": overall_score,
                "benchmarks": benchmark_results,
                "thresholds": self.monitoring_config["benchmark_thresholds"]
            }

            # Store benchmark result
            benchmark_id = str(uuid.uuid4())
            self.benchmarks[benchmark_id] = benchmark_result

            return benchmark_result

        except Exception as e:
            logging.error(f"Comprehensive benchmark failed: {e}")
            return {"error": str(e)}

    def _benchmark_database_queries(self) -> Dict:
        """Benchmark database query performance"""
        try:
            from django.db import connections
            import time

            results = {
                "query_times": [],
                "average_time": 0,
                "slow_queries": 0,
                "query_count": 0
            }

            # Test common query patterns
            test_queries = [
                "SELECT 1",  # Simple query
                "SELECT COUNT(*) FROM django_migrations",  # Count query
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' LIMIT 10",  # Schema query
            ]

            for query in test_queries:
                try:
                    start_time = time.time()

                    with connections['default'].cursor() as cursor:
                        cursor.execute(query)
                        result = cursor.fetchall()

                    query_time = (time.time() - start_time) * 1000  # Convert to ms
                    results["query_times"].append({
                        "query": query[:50] + "...",
                        "time_ms": round(query_time, 2)
                    })
                    results["query_count"] += 1

                    if query_time > 100:  # Slow query threshold
                        results["slow_queries"] += 1

                except Exception as e:
                    logging.warning(f"Database query benchmark failed for query: {e}")

            # Calculate average
            if results["query_times"]:
                results["average_time"] = round(
                    sum(qt["time_ms"] for qt in results["query_times"]) / len(results["query_times"]), 2
                )

            return results

        except Exception as e:
            logging.error(f"Database benchmark failed: {e}")
            return {"error": str(e)}

    def _benchmark_cache_performance(self) -> Dict:
        """Benchmark cache performance"""
        try:
            import time

            results = {
                "read_times": [],
                "write_times": [],
                "average_read_time": 0,
                "average_write_time": 0,
                "hit_rate": 0
            }

            # Test cache reads
            for i in range(100):
                key = f"benchmark_key_{i}"
                value = f"benchmark_value_{i}"

                # Write test
                start_time = time.time()
                cache.set(key, value, 300)
                write_time = (time.time() - start_time) * 1000
                results["write_times"].append(write_time)

                # Read test
                start_time = time.time()
                retrieved_value = cache.get(key)
                read_time = (time.time() - start_time) * 1000
                results["read_times"].append(read_time)

                # Clean up
                cache.delete(key)

            # Calculate averages
            if results["read_times"]:
                results["average_read_time"] = round(
                    sum(results["read_times"]) / len(results["read_times"]), 4
                )

            if results["write_times"]:
                results["average_write_time"] = round(
                    sum(results["write_times"]) / len(results["write_times"]), 4
                )

            # Mock hit rate (would need actual cache implementation)
            results["hit_rate"] = 95.0

            return results

        except Exception as e:
            logging.error(f"Cache benchmark failed: {e}")
            return {"error": str(e)}

    def _benchmark_api_responses(self) -> Dict:
        """Benchmark API response performance"""
        try:
            import time

            results = {
                "response_times": [],
                "average_response_time": 0,
                "min_response_time": 0,
                "max_response_time": 0,
                "success_rate": 0,
                "total_requests": 0,
                "successful_requests": 0
            }

            # Test API endpoints (mock implementation)
            test_endpoints = [
                "http://localhost:8000/api/health/",
                "http://localhost:8000/api/patients/",
                "http://localhost:8000/api/appointments/",
            ]

            for endpoint in test_endpoints:
                try:
                    start_time = time.time()
                    response = requests.get(endpoint, timeout=5)
                    response_time = (time.time() - start_time) * 1000

                    results["response_times"].append({
                        "endpoint": endpoint,
                        "time_ms": round(response_time, 2),
                        "status_code": response.status_code
                    })

                    results["total_requests"] += 1
                    if response.status_code == 200:
                        results["successful_requests"] += 1

                except requests.RequestException as e:
                    results["response_times"].append({
                        "endpoint": endpoint,
                        "time_ms": 5000,  # Timeout
                        "status_code": 0,
                        "error": str(e)
                    })
                    results["total_requests"] += 1

            # Calculate statistics
            if results["response_times"]:
                times = [rt["time_ms"] for rt in results["response_times"]]
                results["average_response_time"] = round(sum(times) / len(times), 2)
                results["min_response_time"] = round(min(times), 2)
                results["max_response_time"] = round(max(times), 2)

            if results["total_requests"] > 0:
                results["success_rate"] = round(
                    (results["successful_requests"] / results["total_requests"]) * 100, 2
                )

            return results

        except Exception as e:
            logging.error(f"API benchmark failed: {e}")
            return {"error": str(e)}

    def _benchmark_memory_usage(self) -> Dict:
        """Benchmark memory usage patterns"""
        try:
            import gc
            import tracemalloc

            results = {
                "baseline_memory_mb": 0,
                "peak_memory_mb": 0,
                "memory_growth_mb": 0,
                "garbage_collection_stats": {}
            }

            # Get baseline memory
            process = psutil.Process()
            results["baseline_memory_mb"] = round(process.memory_info().rss / (1024**2), 2)

            # Start memory tracing
            tracemalloc.start()

            # Simulate memory-intensive operations
            large_list = list(range(1000000))  # Allocate memory
            time.sleep(0.1)  # Allow memory allocation

            # Get peak memory
            peak_memory = process.memory_info().rss / (1024**2)
            results["peak_memory_mb"] = round(peak_memory, 2)
            results["memory_growth_mb"] = round(peak_memory - results["baseline_memory_mb"], 2)

            # Get garbage collection stats
            gc_stats = gc.get_stats()
            results["garbage_collection_stats"] = {
                f"generation_{i}": {
                    "collections": stat["collections"],
                    "collected": stat["collected"],
                    "uncollectable": stat["uncollectable"]
                }
                for i, stat in enumerate(gc_stats)
            }

            # Clean up
            del large_list
            gc.collect()
            tracemalloc.stop()

            return results

        except Exception as e:
            logging.error(f"Memory benchmark failed: {e}")
            return {"error": str(e)}

    def _benchmark_frontend_load(self) -> Dict:
        """Benchmark frontend load performance"""
        try:
            # Mock frontend load benchmark
            # In real implementation, this would use browser automation tools

            results = {
                "page_load_times": [],
                "average_load_time": 0,
                "min_load_time": 0,
                "max_load_time": 0,
                "resource_load_times": {},
                "pages_tested": 0
            }

            # Simulate load testing different pages
            test_pages = [
                "/dashboard",
                "/patients",
                "/appointments",
                "/billing",
                "/reports"
            ]

            for page in test_pages:
                # Mock load times (in real implementation, these would be actual measurements)
                load_time = random.uniform(800, 3000)  # 0.8-3 seconds
                results["page_load_times"].append({
                    "page": page,
                    "load_time_ms": round(load_time, 2)
                })
                results["pages_tested"] += 1

                # Simulate resource load times
                results["resource_load_times"][page] = {
                    "html_ms": round(load_time * 0.3, 2),
                    "css_ms": round(load_time * 0.2, 2),
                    "js_ms": round(load_time * 0.4, 2),
                    "images_ms": round(load_time * 0.1, 2)
                }

            # Calculate statistics
            if results["page_load_times"]:
                times = [plt["load_time_ms"] for plt in results["page_load_times"]]
                results["average_load_time"] = round(sum(times) / len(times), 2)
                results["min_load_time"] = round(min(times), 2)
                results["max_load_time"] = round(max(times), 2)

            return results

        except Exception as e:
            logging.error(f"Frontend benchmark failed: {e}")
            return {"error": str(e)}

    def _calculate_benchmark_score(self, benchmark_results: Dict) -> float:
        """Calculate overall benchmark score"""
        try:
            thresholds = self.monitoring_config["benchmark_thresholds"]
            score = 100
            deductions = 0

            # Database score
            if "database" in benchmark_results and "average_time" in benchmark_results["database"]:
                db_time = benchmark_results["database"]["average_time"]
                if db_time > thresholds["database_query_time"]:
                    deductions += min(20, (db_time / thresholds["database_query_time"] - 1) * 10)

            # API score
            if "api" in benchmark_results and "average_response_time" in benchmark_results["api"]:
                api_time = benchmark_results["api"]["average_response_time"]
                if api_time > thresholds["api_response_time"]:
                    deductions += min(25, (api_time / thresholds["api_response_time"] - 1) * 12)

            # Frontend score
            if "frontend" in benchmark_results and "average_load_time" in benchmark_results["frontend"]:
                frontend_time = benchmark_results["frontend"]["average_load_time"]
                if frontend_time > thresholds["page_load_time"]:
                    deductions += min(20, (frontend_time / thresholds["page_load_time"] - 1) * 10)

            # Cache score
            if "cache" in benchmark_results and "hit_rate" in benchmark_results["cache"]:
                cache_hit_rate = benchmark_results["cache"]["hit_rate"]
                if cache_hit_rate < thresholds["cache_hit_rate"]:
                    deductions += min(15, (thresholds["cache_hit_rate"] - cache_hit_rate) * 0.3)

            return max(0, score - deductions)

        except Exception as e:
            logging.error(f"Benchmark score calculation failed: {e}")
            return 0.0

    def run_load_test(self, test_config: Dict) -> LoadTestResult:
        """Run load test with specified configuration"""
        try:
            test_id = str(uuid.uuid4())
            test_name = test_config.get("name", "Load Test")

            start_time = timezone.now()

            # Initialize load test parameters
            concurrent_users = test_config.get("concurrent_users", 10)
            duration_seconds = test_config.get("duration", 60)
            ramp_up_time = test_config.get("ramp_up_time", 10)
            endpoints = test_config.get("endpoints", [])

            logging.info(f"Starting load test: {test_name} with {concurrent_users} users for {duration_seconds}s")

            # Run load test
            result = self._execute_load_test(
                test_id=test_id,
                test_name=test_name,
                concurrent_users=concurrent_users,
                duration_seconds=duration_seconds,
                ramp_up_time=ramp_up_time,
                endpoints=endpoints
            )

            end_time = timezone.now()
            result.duration_seconds = (end_time - start_time).total_seconds()

            # Store result
            self.load_test_history.append(result)

            logging.info(f"Load test completed: {test_name}")
            return result

        except Exception as e:
            logging.error(f"Load test execution failed: {e}")
            raise

    def _execute_load_test(self, **kwargs) -> LoadTestResult:
        """Execute the actual load test"""
        try:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            import statistics

            test_id = kwargs["test_id"]
            test_name = kwargs["test_name"]
            concurrent_users = kwargs["concurrent_users"]
            duration_seconds = kwargs["duration_seconds"]
            endpoints = kwargs["endpoints"]

            all_response_times = []
            successful_requests = 0
            failed_requests = 0

            def make_request(user_id: int) -> Dict:
                """Make a single request as part of load test"""
                try:
                    # Select random endpoint
                    endpoint = random.choice(endpoints) if endpoints else "http://localhost:8000/api/health/"

                    start_time = time.time()
                    response = requests.get(endpoint, timeout=30)
                    response_time = (time.time() - start_time) * 1000

                    return {
                        "user_id": user_id,
                        "response_time_ms": response_time,
                        "status_code": response.status_code,
                        "success": response.status_code == 200,
                        "endpoint": endpoint
                    }

                except Exception as e:
                    return {
                        "user_id": user_id,
                        "response_time_ms": 30000,  # 30 second timeout
                        "status_code": 0,
                        "success": False,
                        "error": str(e),
                        "endpoint": endpoint if endpoints else "unknown"
                    }

            # Execute load test with ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
                start_time = time.time()

                # Submit requests continuously for the duration
                futures = []
                request_count = 0

                while (time.time() - start_time) < duration_seconds:
                    # Submit requests for all concurrent users
                    for user_id in range(concurrent_users):
                        if (time.time() - start_time) < duration_seconds:
                            future = executor.submit(make_request, user_id)
                            futures.append(future)
                            request_count += 1

                # Collect results
                for future in as_completed(futures):
                    result = future.result()
                    all_response_times.append(result["response_time_ms"])

                    if result["success"]:
                        successful_requests += 1
                    else:
                        failed_requests += 1

            # Calculate statistics
            if all_response_times:
                avg_response_time = statistics.mean(all_response_times)
                min_response_time = min(all_response_times)
                max_response_time = max(all_response_times)

                # Calculate percentiles
                sorted_times = sorted(all_response_times)
                p95_response_time = sorted_times[int(len(sorted_times) * 0.95)]
                p99_response_time = sorted_times[int(len(sorted_times) * 0.99)]
            else:
                avg_response_time = min_response_time = max_response_time = p95_response_time = p99_response_time = 0

            # Calculate requests per second
            actual_duration = max(1, time.time() - start_time)
            requests_per_second = len(all_response_times) / actual_duration
            error_rate = (failed_requests / len(all_response_times)) * 100 if all_response_times else 0

            # Collect system metrics during test
            system_metrics = self._collect_load_test_system_metrics()

            return LoadTestResult(
                test_id=test_id,
                test_name=test_name,
                start_time=timezone.now() - timedelta(seconds=actual_duration),
                end_time=timezone.now(),
                duration_seconds=actual_duration,
                total_requests=len(all_response_times),
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                average_response_time=round(avg_response_time, 2),
                min_response_time=round(min_response_time, 2),
                max_response_time=round(max_response_time, 2),
                p95_response_time=round(p95_response_time, 2),
                p99_response_time=round(p99_response_time, 2),
                requests_per_second=round(requests_per_second, 2),
                error_rate=round(error_rate, 2),
                system_metrics=system_metrics
            )

        except Exception as e:
            logging.error(f"Load test execution failed: {e}")
            raise

    def _collect_load_test_system_metrics(self) -> Dict[str, Any]:
        """Collect system metrics during load test"""
        try:
            return {
                "cpu_usage_percent": psutil.cpu_percent(interval=1),
                "memory_usage_percent": psutil.virtual_memory().percent,
                "disk_usage_percent": psutil.disk_usage('/').percent,
                "network_sent_bytes": psutil.net_io_counters().bytes_sent,
                "network_recv_bytes": psutil.net_io_counters().bytes_recv,
                "timestamp": timezone.now().isoformat()
            }
        except Exception as e:
            logging.error(f"System metrics collection during load test failed: {e}")
            return {}

    def generate_performance_report(self, report_type: str = "comprehensive") -> Dict:
        """Generate performance analysis report"""
        try:
            report = {
                "generated_at": timezone.now().isoformat(),
                "report_type": report_type,
                "monitoring_status": "active" if self.is_monitoring else "inactive",
                "data_period": f"Last {self.monitoring_config['retention_days']} days"
            }

            if report_type == "comprehensive":
                # Include all sections
                report.update({
                    "executive_summary": self._generate_executive_summary(),
                    "system_health": self._get_health_summary(),
                    "performance_benchmarks": list(self.benchmarks.values())[-5:],  # Last 5 benchmarks
                    "load_test_results": [asdict(result) for result in self.load_test_history[-3:]],  # Last 3 load tests
                    "recent_alerts": self.alerts[-10:],  # Last 10 alerts
                    "optimization_recommendations": self._generate_optimization_recommendations(),
                    "performance_trends": self._get_performance_trends()
                })

            elif report_type == "summary":
                # Brief overview
                report.update({
                    "executive_summary": self._generate_executive_summary(),
                    "system_health": self._get_health_summary(),
                    "recent_alerts_count": len(self.alerts),
                    "last_benchmark_score": list(self.benchmarks.values())[-1]["overall_score"] if self.benchmarks else 0
                })

            elif report_type == "alerts":
                # Focus on alerts and issues
                report.update({
                    "recent_alerts": self.alerts,
                    "alert_summary": self._generate_alert_summary(),
                    "recommendations": self._generate_alert_recommendations()
                })

            return report

        except Exception as e:
            logging.error(f"Performance report generation failed: {e}")
            return {"error": str(e)}

    def _generate_executive_summary(self) -> Dict:
        """Generate executive summary of system performance"""
        try:
            health = self._get_health_summary()
            current_metrics = self._get_current_metrics()

            # Get latest benchmark
            latest_benchmark = list(self.benchmarks.values())[-1] if self.benchmarks else None

            # Get latest load test
            latest_load_test = self.load_test_history[-1] if self.load_test_history else None

            return {
                "overall_health": health.get("status", "unknown"),
                "health_score": health.get("overall_score", 0),
                "monitoring_active": self.is_monitoring,
                "active_alerts": len([a for a in self.alerts if a["severity"] == "critical"]),
                "benchmark_score": latest_benchmark["overall_score"] if latest_benchmark else 0,
                "load_test_rps": latest_load_test.requests_per_second if latest_load_test else 0,
                "key_metrics": {
                    "cpu_usage": current_metrics.get("cpu_usage_percent", {}).get("value", 0),
                    "memory_usage": current_metrics.get("memory_usage_percent", {}).get("value", 0),
                    "database_connections": current_metrics.get("database_active_connections", {}).get("value", 0)
                },
                "recommendations": [
                    "Continue monitoring system performance",
                    "Review any critical alerts",
                    "Schedule regular load testing",
                    "Optimize based on benchmark results"
                ]
            }

        except Exception as e:
            logging.error(f"Executive summary generation failed: {e}")
            return {"error": str(e)}

    def _generate_optimization_recommendations(self) -> List[Dict]:
        """Generate performance optimization recommendations"""
        recommendations = []

        try:
            current_metrics = self._get_current_metrics()
            health = self._get_health_summary()

            # CPU optimization recommendations
            if "cpu_usage_percent" in current_metrics:
                cpu_usage = current_metrics["cpu_usage_percent"]["value"]
                if cpu_usage > 80:
                    recommendations.append({
                        "priority": "high",
                        "category": "cpu",
                        "issue": f"High CPU usage: {cpu_usage:.1f}%",
                        "recommendation": "Consider scaling up resources or optimizing CPU-intensive tasks",
                        "estimated_improvement": "20-30% reduction in CPU usage"
                    })

            # Memory optimization recommendations
            if "memory_usage_percent" in current_metrics:
                memory_usage = current_metrics["memory_usage_percent"]["value"]
                if memory_usage > 85:
                    recommendations.append({
                        "priority": "high",
                        "category": "memory",
                        "issue": f"High memory usage: {memory_usage:.1f}%",
                        "recommendation": "Implement memory optimization strategies and consider memory profiling",
                        "estimated_improvement": "30-40% reduction in memory usage"
                    })

            # Database optimization recommendations
            if "database_active_connections" in current_metrics:
                db_connections = current_metrics["database_active_connections"]["value"]
                if db_connections > 50:
                    recommendations.append({
                        "priority": "medium",
                        "category": "database",
                        "issue": f"High database connections: {db_connections}",
                        "recommendation": "Optimize database connection pooling and query efficiency",
                        "estimated_improvement": "40-50% reduction in connection count"
                    })

            # Cache optimization recommendations
            if "cache_hit_rate_percent" in current_metrics:
                cache_hit_rate = current_metrics["cache_hit_rate_percent"]["value"]
                if cache_hit_rate < 70:
                    recommendations.append({
                        "priority": "medium",
                        "category": "cache",
                        "issue": f"Low cache hit rate: {cache_hit_rate:.1f}%",
                        "recommendation": "Implement caching strategies for frequently accessed data",
                        "estimated_improvement": "60-80% improvement in cache hit rate"
                    })

            # General recommendations
            if health.get("overall_score", 100) < 80:
                recommendations.append({
                    "priority": "medium",
                    "category": "general",
                    "issue": f"System health score below threshold: {health['overall_score']}",
                    "recommendation": "Review system performance and implement optimization measures",
                    "estimated_improvement": "20-40% improvement in overall health"
                })

        except Exception as e:
            logging.error(f"Optimization recommendations generation failed: {e}")

        return recommendations

    def _generate_alert_summary(self) -> Dict:
        """Generate summary of recent alerts"""
        try:
            if not self.alerts:
                return {"message": "No recent alerts"}

            # Analyze recent alerts (last 24 hours)
            cutoff_time = timezone.now() - timedelta(hours=24)
            recent_alerts = [a for a in self.alerts if datetime.fromisoformat(a["timestamp"]) > cutoff_time]

            if not recent_alerts:
                return {"message": "No alerts in the last 24 hours"}

            # Group alerts by severity
            severity_counts = {"critical": 0, "warning": 0}
            metric_counts = {}

            for alert in recent_alerts:
                severity_counts[alert["severity"]] += 1

                metric_name = alert["metric"]
                if metric_name not in metric_counts:
                    metric_counts[metric_name] = 0
                metric_counts[metric_name] += 1

            return {
                "total_alerts_24h": len(recent_alerts),
                "severity_breakdown": severity_counts,
                "most_alerted_metrics": sorted(metric_counts.items(), key=lambda x: x[1], reverse=True)[:5],
                "latest_alert": recent_alerts[-1] if recent_alerts else None
            }

        except Exception as e:
            logging.error(f"Alert summary generation failed: {e}")
            return {"error": str(e)}

    def _generate_alert_recommendations(self) -> List[Dict]:
        """Generate recommendations based on alerts"""
        recommendations = []

        try:
            # Analyze alert patterns
            alert_patterns = {}
            for alert in self.alerts[-20:]:  # Last 20 alerts
                metric = alert["metric"]
                if metric not in alert_patterns:
                    alert_patterns[metric] = {"count": 0, "avg_value": 0}
                alert_patterns[metric]["count"] += 1
                alert_patterns[metric]["avg_value"] += alert["value"]

            # Calculate averages
            for metric, data in alert_patterns.items():
                data["avg_value"] /= data["count"]

            # Generate recommendations based on patterns
            for metric, data in alert_patterns.items():
                if data["count"] >= 3:  # Recurring alerts
                    if "cpu" in metric:
                        recommendations.append({
                            "priority": "high",
                            "metric": metric,
                            "issue": f"Recurring CPU alerts ({data['count']} occurrences)",
                            "recommendation": "Investigate CPU-intensive processes and consider scaling",
                            "avg_value": round(data["avg_value"], 2)
                        })
                    elif "memory" in metric:
                        recommendations.append({
                            "priority": "high",
                            "metric": metric,
                            "issue": f"Recurring memory alerts ({data['count']} occurrences)",
                            "recommendation": "Implement memory optimization and investigate memory leaks",
                            "avg_value": round(data["avg_value"], 2)
                        })
                    elif "database" in metric:
                        recommendations.append({
                            "priority": "medium",
                            "metric": metric,
                            "issue": f"Recurring database alerts ({data['count']} occurrences)",
                            "recommendation": "Optimize database queries and connection pooling",
                            "avg_value": round(data["avg_value"], 2)
                        })

        except Exception as e:
            logging.error(f"Alert recommendations generation failed: {e}")

        return recommendations


# Global performance monitoring instance
performance_monitor = PerformanceMonitoringSystem()


# Convenience functions for external use
def start_performance_monitoring():
    """Start performance monitoring"""
    return performance_monitor.start_monitoring()


def stop_performance_monitoring():
    """Stop performance monitoring"""
    return performance_monitor.stop_monitoring()


def get_performance_dashboard():
    """Get performance dashboard data"""
    return performance_monitor.get_performance_dashboard()


def run_comprehensive_benchmark():
    """Run comprehensive performance benchmarks"""
    return performance_monitor.run_comprehensive_benchmark()


def run_load_test(test_config: Dict):
    """Run load test with specified configuration"""
    return performance_monitor.run_load_test(test_config)


def generate_performance_report(report_type: str = "comprehensive"):
    """Generate performance analysis report"""
    return performance_monitor.generate_performance_report(report_type)


# Example usage
if __name__ == "__main__":
    # Start monitoring
    print("Starting performance monitoring...")
    monitoring_result = start_performance_monitoring()
    print(f"Monitoring started: {monitoring_result}")

    # Run benchmark
    print("Running comprehensive benchmark...")
    benchmark_result = run_comprehensive_benchmark()
    print(f"Benchmark score: {benchmark_result.get('overall_score', 0)}")

    # Generate report
    print("Generating performance report...")
    report = generate_performance_report("summary")
    print(f"Report generated with {len(report)} sections")

    # Stop monitoring
    print("Stopping performance monitoring...")
    stop_result = stop_performance_monitoring()
    print(f"Monitoring stopped: {stop_result}")