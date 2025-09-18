"""
Comprehensive Monitoring and Observability Framework
Enterprise-grade monitoring for healthcare systems with real-time alerts and analytics
"""

import asyncio
import json
import logging
import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import asyncio
from prometheus_client import Counter, Gauge, Histogram, start_http_server
from prometheus_client.core import REGISTRY
import redis.asyncio as aioredis
import aiohttp
from django.conf import settings
from django.core.cache import cache
from django.db import connections
from django.utils import timezone

class MonitoringLevel(Enum):
    """Monitoring levels for different components"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class ComponentType(Enum):
    """Component types being monitored"""
    API = "api"
    DATABASE = "database"
    CACHE = "cache"
    MESSAGE_QUEUE = "message_queue"
    MICROSERVICE = "microservice"
    EXTERNAL_SERVICE = "external_service"
    SYSTEM = "system"

@dataclass
class SystemMetrics:
    """System-level metrics"""
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_io_bytes_sent: int
    network_io_bytes_recv: int
    process_count: int
    load_average: float
    timestamp: datetime

@dataclass
class ApplicationMetrics:
    """Application-level metrics"""
    request_count: int
    response_time_avg: float
    error_rate: float
    active_connections: int
    cache_hit_rate: float
    database_connections: int
    timestamp: datetime

@dataclass
class Alert:
    """Alert structure"""
    id: str
    component: str
    component_type: ComponentType
    severity: AlertSeverity
    title: str
    description: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict = None

class MetricsCollector:
    """Collect metrics from various sources"""

    def __init__(self):
        self.system_metrics_history = deque(maxlen=1000)
        self.app_metrics_history = deque(maxlen=1000)
        self.custom_metrics = defaultdict(list)

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect system-level metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0

            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent

            # Network metrics
            network = psutil.net_io_counters()
            network_io_bytes_sent = network.bytes_sent
            network_io_bytes_recv = network.bytes_recv

            # Process count
            process_count = len(psutil.pids())

            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_usage_percent=disk_usage_percent,
                network_io_bytes_sent=network_io_bytes_sent,
                network_io_bytes_recv=network_io_bytes_recv,
                process_count=process_count,
                load_average=load_avg,
                timestamp=datetime.now()
            )

            self.system_metrics_history.append(metrics)
            return metrics

        except Exception as e:
            logging.error(f"Failed to collect system metrics: {e}")
            return None

    def collect_application_metrics(self) -> ApplicationMetrics:
        """Collect application-level metrics"""
        try:
            # Database metrics
            db_connections = 0
            for alias in connections.databases:
                try:
                    with connections[alias].cursor() as cursor:
                        cursor.execute("SELECT count(*) FROM pg_stat_activity")
                        db_connections += cursor.fetchone()[0]
                except:
                    pass

            # Cache metrics
            cache_hit_rate = 0.0
            if hasattr(cache, 'get_stats'):
                stats = cache.get_stats()
                hits = stats.get('hits', 0)
                misses = stats.get('misses', 0)
                total = hits + misses
                if total > 0:
                    cache_hit_rate = (hits / total) * 100

            metrics = ApplicationMetrics(
                request_count=0,  # Would be tracked by API middleware
                response_time_avg=0.0,  # Would be tracked by API middleware
                error_rate=0.0,  # Would be tracked by API middleware
                active_connections=0,  # Would be tracked by connection tracking
                cache_hit_rate=cache_hit_rate,
                database_connections=db_connections,
                timestamp=datetime.now()
            )

            self.app_metrics_history.append(metrics)
            return metrics

        except Exception as e:
            logging.error(f"Failed to collect application metrics: {e}")
            return None

    def add_custom_metric(self, name: str, value: float, tags: Dict = None):
        """Add custom metric"""
        metric = {
            "name": name,
            "value": value,
            "timestamp": datetime.now(),
            "tags": tags or {}
        }
        self.custom_metrics[name].append(metric)

    def get_metrics_summary(self) -> Dict:
        """Get summary of all metrics"""
        return {
            "system": {
                "current": self.system_metrics_history[-1] if self.system_metrics_history else None,
                "history_size": len(self.system_metrics_history)
            },
            "application": {
                "current": self.app_metrics_history[-1] if self.app_metrics_history else None,
                "history_size": len(self.app_metrics_history)
            },
            "custom": {name: len(metrics) for name, metrics in self.custom_metrics.items()}
        }

class AlertManager:
    """Manage alerts and notifications"""

    def __init__(self):
        self.alerts: List[Alert] = []
        self.alert_rules: List[Dict] = []
        self.notification_channels: List[Dict] = []
        self.alert_history = deque(maxlen=10000)

    def add_alert_rule(self, name: str, condition: str, severity: AlertSeverity,
                      component: str, component_type: ComponentType,
                      description: str = None):
        """Add alert rule"""
        rule = {
            "name": name,
            "condition": condition,
            "severity": severity,
            "component": component,
            "component_type": component_type,
            "description": description or f"Alert rule: {name}",
            "enabled": True,
            "created_at": datetime.now()
        }
        self.alert_rules.append(rule)
        logging.info(f"Added alert rule: {name}")

    def add_notification_channel(self, name: str, channel_type: str,
                                config: Dict):
        """Add notification channel"""
        channel = {
            "name": name,
            "type": channel_type,
            "config": config,
            "enabled": True
        }
        self.notification_channels.append(channel)
        logging.info(f"Added notification channel: {name}")

    def evaluate_alert_rules(self, metrics: Dict) -> List[Alert]:
        """Evaluate alert rules against metrics"""
        triggered_alerts = []

        for rule in self.alert_rules:
            if not rule.get("enabled", True):
                continue

            try:
                # Evaluate condition (simplified for demo)
                # In production, this would use a proper expression evaluator
                condition_met = self._evaluate_condition(rule["condition"], metrics)

                if condition_met:
                    # Check if alert already exists and is not resolved
                    existing_alert = self._find_existing_alert(rule["name"])
                    if not existing_alert:
                        alert = Alert(
                            id=f"alert_{int(time.time())}_{len(self.alerts)}",
                            component=rule["component"],
                            component_type=rule["component_type"],
                            severity=rule["severity"],
                            title=rule["name"],
                            description=rule["description"],
                            timestamp=datetime.now()
                        )
                        self.alerts.append(alert)
                        self.alert_history.append(alert)
                        triggered_alerts.append(alert)

                        # Send notifications
                        asyncio.create_task(self._send_notifications(alert))

            except Exception as e:
                logging.error(f"Failed to evaluate alert rule {rule['name']}: {e}")

        return triggered_alerts

    def _evaluate_condition(self, condition: str, metrics: Dict) -> bool:
        """Evaluate alert condition (simplified)"""
        # This is a very simplified condition evaluator
        # In production, use a proper expression evaluator
        if "cpu_percent >" in condition:
            threshold = float(condition.split(">")[1].strip())
            system_metrics = metrics.get("system", {}).get("current")
            return system_metrics and system_metrics.cpu_percent > threshold

        elif "memory_percent >" in condition:
            threshold = float(condition.split(">")[1].strip())
            system_metrics = metrics.get("system", {}).get("current")
            return system_metrics and system_metrics.memory_percent > threshold

        elif "error_rate >" in condition:
            threshold = float(condition.split(">")[1].strip())
            app_metrics = metrics.get("application", {}).get("current")
            return app_metrics and app_metrics.error_rate > threshold

        return False

    def _find_existing_alert(self, rule_name: str) -> Optional[Alert]:
        """Find existing unresolved alert for rule"""
        for alert in self.alerts:
            if (alert.title == rule_name and not alert.resolved and
                alert.timestamp > datetime.now() - timedelta(hours=1)):
                return alert
        return None

    async def _send_notifications(self, alert: Alert):
        """Send alert notifications"""
        for channel in self.notification_channels:
            if not channel.get("enabled", True):
                continue

            try:
                if channel["type"] == "webhook":
                    await self._send_webhook_notification(channel, alert)
                elif channel["type"] == "email":
                    await self._send_email_notification(channel, alert)
                elif channel["type"] == "slack":
                    await self._send_slack_notification(channel, alert)
            except Exception as e:
                logging.error(f"Failed to send notification via {channel['name']}: {e}")

    async def _send_webhook_notification(self, channel: Dict, alert: Alert):
        """Send webhook notification"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "alert_id": alert.id,
                "title": alert.title,
                "description": alert.description,
                "severity": alert.severity.value,
                "component": alert.component,
                "timestamp": alert.timestamp.isoformat()
            }

            async with session.post(
                channel["config"]["url"],
                json=payload,
                headers=channel["config"].get("headers", {})
            ) as response:
                if response.status == 200:
                    logging.info(f"Webhook notification sent for alert {alert.id}")
                else:
                    logging.error(f"Webhook notification failed: {response.status}")

    async def _send_email_notification(self, channel: Dict, alert: Alert):
        """Send email notification (placeholder)"""
        # In production, implement email sending
        logging.info(f"Email notification would be sent for alert {alert.id}")

    async def _send_slack_notification(self, channel: Dict, alert: Alert):
        """Send Slack notification"""
        webhook_url = channel["config"]["webhook_url"]
        color = {
            AlertSeverity.CRITICAL: "danger",
            AlertSeverity.HIGH: "warning",
            AlertSeverity.MEDIUM: "warning",
            AlertSeverity.LOW: "good",
            AlertSeverity.INFO: "good"
        }[alert.severity]

        payload = {
            "text": f"Alert: {alert.title}",
            "attachments": [{
                "color": color,
                "title": alert.title,
                "text": alert.description,
                "fields": [
                    {"title": "Severity", "value": alert.severity.value, "short": True},
                    {"title": "Component", "value": alert.component, "short": True},
                    {"title": "Time", "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"), "short": True}
                ]
            }]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status == 200:
                    logging.info(f"Slack notification sent for alert {alert.id}")
                else:
                    logging.error(f"Slack notification failed: {response.status}")

    def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                logging.info(f"Alert {alert_id} resolved")
                return True
        return False

class HealthChecker:
    """Health check for various components"""

    def __init__(self):
        self.health_checks: Dict[str, Dict] = {}
        self.health_history = deque(maxlen=1000)

    def add_health_check(self, name: str, check_func: callable,
                        component_type: ComponentType, timeout: int = 30):
        """Add health check"""
        self.health_checks[name] = {
            "function": check_func,
            "component_type": component_type,
            "timeout": timeout,
            "last_check": None,
            "last_status": None
        }

    async def run_health_checks(self) -> Dict[str, Dict]:
        """Run all health checks"""
        results = {}

        for name, check_config in self.health_checks.items():
            try:
                # Run health check with timeout
                result = await asyncio.wait_for(
                    check_config["function"](),
                    timeout=check_config["timeout"]
                )

                health_result = {
                    "name": name,
                    "component_type": check_config["component_type"].value,
                    "status": "healthy" if result.get("healthy", False) else "unhealthy",
                    "details": result.get("details", {}),
                    "timestamp": datetime.now(),
                    "response_time": result.get("response_time", 0)
                }

                # Update health check config
                check_config["last_check"] = datetime.now()
                check_config["last_status"] = health_result["status"]

                results[name] = health_result
                self.health_history.append(health_result)

            except asyncio.TimeoutError:
                results[name] = {
                    "name": name,
                    "component_type": check_config["component_type"].value,
                    "status": "timeout",
                    "details": {"error": "Health check timed out"},
                    "timestamp": datetime.now(),
                    "response_time": check_config["timeout"]
                }
            except Exception as e:
                results[name] = {
                    "name": name,
                    "component_type": check_config["component_type"].value,
                    "status": "error",
                    "details": {"error": str(e)},
                    "timestamp": datetime.now(),
                    "response_time": 0
                }

        return results

    def get_overall_health(self) -> Dict:
        """Get overall system health"""
        if not self.health_history:
            return {"status": "unknown", "checks": 0}

        recent_checks = [
            check for check in self.health_history
            if check["timestamp"] > datetime.now() - timedelta(minutes=5)
        ]

        if not recent_checks:
            return {"status": "unknown", "checks": 0}

        healthy_count = sum(1 for check in recent_checks if check["status"] == "healthy")
        total_count = len(recent_checks)

        if healthy_count == total_count:
            status = "healthy"
        elif healthy_count >= total_count * 0.8:
            status = "degraded"
        else:
            status = "unhealthy"

        return {
            "status": status,
            "healthy_checks": healthy_count,
            "total_checks": total_count,
            "percentage": (healthy_count / total_count * 100) if total_count > 0 else 0
        }

class MetricsExporter:
    """Export metrics to external systems"""

    def __init__(self):
        self.prometheus_metrics = {}
        self._setup_prometheus_metrics()

    def _setup_prometheus_metrics(self):
        """Setup Prometheus metrics"""
        # System metrics
        self.prometheus_metrics["system_cpu_percent"] = Gauge(
            "system_cpu_percent", "System CPU usage percentage"
        )
        self.prometheus_metrics["system_memory_percent"] = Gauge(
            "system_memory_percent", "System memory usage percentage"
        )
        self.prometheus_metrics["system_disk_percent"] = Gauge(
            "system_disk_percent", "System disk usage percentage"
        )

        # Application metrics
        self.prometheus_metrics["app_requests_total"] = Counter(
            "app_requests_total", "Total number of requests"
        )
        self.prometheus_metrics["app_response_time_seconds"] = Histogram(
            "app_response_time_seconds", "Response time in seconds"
        )
        self.prometheus_metrics["app_errors_total"] = Counter(
            "app_errors_total", "Total number of errors"
        )

        # Database metrics
        self.prometheus_metrics["db_connections_active"] = Gauge(
            "db_connections_active", "Active database connections"
        )

        # Custom metrics
        self.prometheus_metrics["custom_metric"] = Gauge(
            "custom_metric", "Custom metric", ["name", "tag"]
        )

    def update_prometheus_metrics(self, metrics: Dict):
        """Update Prometheus metrics"""
        try:
            # Update system metrics
            system_metrics = metrics.get("system", {}).get("current")
            if system_metrics:
                self.prometheus_metrics["system_cpu_percent"].set(system_metrics.cpu_percent)
                self.prometheus_metrics["system_memory_percent"].set(system_metrics.memory_percent)
                self.prometheus_metrics["system_disk_percent"].set(system_metrics.disk_usage_percent)

            # Update database metrics
            app_metrics = metrics.get("application", {}).get("current")
            if app_metrics:
                self.prometheus_metrics["db_connections_active"].set(app_metrics.database_connections)

        except Exception as e:
            logging.error(f"Failed to update Prometheus metrics: {e}")

    def start_prometheus_server(self, port: int = 8000):
        """Start Prometheus metrics server"""
        try:
            start_http_server(port)
            logging.info(f"Prometheus metrics server started on port {port}")
        except Exception as e:
            logging.error(f"Failed to start Prometheus server: {e}")

class MonitoringDashboard:
    """Generate monitoring dashboard data"""

    def __init__(self, metrics_collector: MetricsCollector, alert_manager: AlertManager,
                 health_checker: HealthChecker):
        self.metrics_collector = metrics_collector
        self.alert_manager = alert_manager
        self.health_checker = health_checker

    def get_dashboard_data(self) -> Dict:
        """Get comprehensive dashboard data"""
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": self.metrics_collector.get_metrics_summary(),
            "alerts": {
                "active": len([a for a in self.alert_manager.alerts if not a.resolved]),
                "total": len(self.alert_manager.alerts),
                "recent": [
                    asdict(alert) for alert in sorted(
                        self.alert_manager.alerts,
                        key=lambda x: x.timestamp,
                        reverse=True
                    )[:10]
                ]
            },
            "health": {
                "overall": self.health_checker.get_overall_health(),
                "checks": {
                    name: {
                        "status": check["last_status"],
                        "last_check": check["last_check"].isoformat() if check["last_check"] else None
                    }
                    for name, check in self.health_checker.health_checks.items()
                }
            },
            "system": {
                "uptime": time.time() - psutil.boot_time(),
                "platform": platform.platform(),
                "python_version": platform.python_version()
            }
        }

class MonitoringService:
    """Main monitoring service"""

    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.health_checker = HealthChecker()
        self.metrics_exporter = MetricsExporter()
        self.dashboard = MonitoringDashboard(
            self.metrics_collector, self.alert_manager, self.health_checker
        )
        self.is_running = False
        self.monitoring_tasks = []

    async def start(self):
        """Start monitoring service"""
        if self.is_running:
            return

        self.is_running = True
        logging.info("Starting monitoring service")

        # Setup default alert rules
        self._setup_default_alert_rules()

        # Setup default health checks
        await self._setup_default_health_checks()

        # Start Prometheus server
        self.metrics_exporter.start_prometheus_server()

        # Start monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._metrics_collection_loop()),
            asyncio.create_task(self._health_check_loop()),
            asyncio.create_task(self._alert_evaluation_loop())
        ]

        logging.info("Monitoring service started successfully")

    async def stop(self):
        """Stop monitoring service"""
        if not self.is_running:
            return

        self.is_running = False
        logging.info("Stopping monitoring service")

        # Cancel monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)

        logging.info("Monitoring service stopped")

    def _setup_default_alert_rules(self):
        """Setup default alert rules"""
        # System alerts
        self.alert_manager.add_alert_rule(
            "High CPU Usage",
            "cpu_percent > 80",
            AlertSeverity.HIGH,
            "system",
            ComponentType.SYSTEM,
            "CPU usage is above 80%"
        )

        self.alert_manager.add_alert_rule(
            "High Memory Usage",
            "memory_percent > 85",
            AlertSeverity.HIGH,
            "system",
            ComponentType.SYSTEM,
            "Memory usage is above 85%"
        )

        self.alert_manager.add_alert_rule(
            "High Disk Usage",
            "disk_usage_percent > 90",
            AlertSeverity.CRITICAL,
            "system",
            ComponentType.SYSTEM,
            "Disk usage is above 90%"
        )

        # Application alerts
        self.alert_manager.add_alert_rule(
            "High Error Rate",
            "error_rate > 5",
            AlertSeverity.HIGH,
            "api",
            ComponentType.API,
            "API error rate is above 5%"
        )

    async def _setup_default_health_checks(self):
        """Setup default health checks"""
        # Database health check
        async def check_database():
            try:
                start_time = time.time()
                with connections["default"].cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                response_time = time.time() - start_time
                return {
                    "healthy": True,
                    "details": {"response_time": response_time},
                    "response_time": response_time
                }
            except Exception as e:
                return {
                    "healthy": False,
                    "details": {"error": str(e)},
                    "response_time": 0
                }

        self.health_checker.add_health_check(
            "database",
            check_database,
            ComponentType.DATABASE
        )

        # Cache health check
        async def check_cache():
            try:
                start_time = time.time()
                cache.set("health_check", "test", 1)
                result = cache.get("health_check")
                response_time = time.time() - start_time
                return {
                    "healthy": result == "test",
                    "details": {"response_time": response_time},
                    "response_time": response_time
                }
            except Exception as e:
                return {
                    "healthy": False,
                    "details": {"error": str(e)},
                    "response_time": 0
                }

        self.health_checker.add_health_check(
            "cache",
            check_cache,
            ComponentType.CACHE
        )

        # API health check
        async def check_api():
            try:
                start_time = time.time()
                # This would check actual API endpoints
                response_time = time.time() - start_time
                return {
                    "healthy": True,
                    "details": {"response_time": response_time},
                    "response_time": response_time
                }
            except Exception as e:
                return {
                    "healthy": False,
                    "details": {"error": str(e)},
                    "response_time": 0
                }

        self.health_checker.add_health_check(
            "api",
            check_api,
            ComponentType.API
        )

    async def _metrics_collection_loop(self):
        """Metrics collection loop"""
        while self.is_running:
            try:
                # Collect system metrics
                system_metrics = self.metrics_collector.collect_system_metrics()
                if system_metrics:
                    self.metrics_collector.add_custom_metric(
                        "system.cpu_percent", system_metrics.cpu_percent
                    )
                    self.metrics_collector.add_custom_metric(
                        "system.memory_percent", system_metrics.memory_percent
                    )

                # Collect application metrics
                app_metrics = self.metrics_collector.collect_application_metrics()

                # Update Prometheus metrics
                metrics_summary = self.metrics_collector.get_metrics_summary()
                self.metrics_exporter.update_prometheus_metrics(metrics_summary)

                await asyncio.sleep(30)  # Collect metrics every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Metrics collection error: {e}")
                await asyncio.sleep(30)

    async def _health_check_loop(self):
        """Health check loop"""
        while self.is_running:
            try:
                await self.health_checker.run_health_checks()
                await asyncio.sleep(60)  # Run health checks every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Health check error: {e}")
                await asyncio.sleep(60)

    async def _alert_evaluation_loop(self):
        """Alert evaluation loop"""
        while self.is_running:
            try:
                metrics_summary = self.metrics_collector.get_metrics_summary()
                triggered_alerts = self.alert_manager.evaluate_alert_rules(metrics_summary)

                if triggered_alerts:
                    logging.warning(f"Triggered {len(triggered_alerts)} alerts")

                await asyncio.sleep(60)  # Evaluate alerts every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Alert evaluation error: {e}")
                await asyncio.sleep(60)

    def get_dashboard_data(self) -> Dict:
        """Get dashboard data"""
        return self.dashboard.get_dashboard_data()

    def add_custom_metric(self, name: str, value: float, tags: Dict = None):
        """Add custom metric"""
        self.metrics_collector.add_custom_metric(name, value, tags)

# Global monitoring service instance
monitoring_service = MonitoringService()

# Convenience functions for use in other modules
def record_metric(name: str, value: float, tags: Dict = None):
    """Record a custom metric"""
    monitoring_service.add_custom_metric(name, value, tags)

async def start_monitoring():
    """Start the monitoring service"""
    await monitoring_service.start()

async def stop_monitoring():
    """Stop the monitoring service"""
    await monitoring_service.stop()