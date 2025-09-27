"""
Database Monitoring and Alerting System for HMS Enterprise
Real-time monitoring, performance metrics, and intelligent alerting
"""

import json
import logging
import smtplib
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from email.mime.text import MimeText
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import psycopg2
import redis
import requests
from django_prometheus import metrics
from psycopg2 import sql

from django.conf import settings
from django.core.cache import cache
from django.db import connection, connections

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class MetricType(Enum):
    GAUGE = "gauge"
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    PERCENTILE = "percentile"


@dataclass
class DatabaseMetric:
    """Database metric data structure"""

    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    tags: Dict[str, str] = None
    threshold: Optional[float] = None


@dataclass
class Alert:
    """Alert data structure"""

    id: str
    name: str
    severity: AlertSeverity
    message: str
    metric_name: str
    current_value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None


class DatabaseMonitor:
    """Comprehensive database monitoring system"""

    def __init__(self):
        self.redis_client = None
        self._redis_pool = None
        self._redis_lock = threading.RLock()
        self.metrics_history = defaultdict(lambda: deque(maxlen=1000))
        self.active_alerts = {}
        self.alert_handlers = {}
        self.collection_interval = 30  # seconds
        self.running = False
        self.collection_thread = None
        self._initialize_redis()

    def _initialize_redis(self):
        """Initialize Redis connection with connection pooling"""
        with self._redis_lock:
            if self.redis_client is not None:
                return

            try:
                redis_host = getattr(settings, "REDIS_HOST", "localhost")
                redis_port = getattr(settings, "REDIS_PORT", 6379)

                # Create connection pool
                self._redis_pool = redis.ConnectionPool(
                    host=redis_host,
                    port=redis_port,
                    db=2,  # Separate DB for monitoring
                    max_connections=5,  # Limited to prevent leaks
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                )

                self.redis_client = redis.Redis(connection_pool=self._redis_pool)
                # Test connection
                self.redis_client.ping()
                logger.info("Redis connection initialized for database monitoring")
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                self.redis_client = None
                self._redis_pool = None

    def cleanup_redis(self):
        """Cleanup Redis connections"""
        with self._redis_lock:
            if self._redis_pool:
                try:
                    self._redis_pool.disconnect()
                except Exception:
                    pass
                self._redis_pool = None
            self.redis_client = None

    def __del__(self):
        """Cleanup on destruction"""
        self.cleanup_redis()

    def stop_monitoring(self):
        """Stop the monitoring service"""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        self.cleanup_redis()
        logger.info("Database monitoring stopped")

        # Prometheus metrics
        self.prometheus_metrics = {
            "connections_active": metrics.Gauge(
                "hms_database_connections_active",
                "Number of active database connections",
            ),
            "connections_idle": metrics.Gauge(
                "hms_database_connections_idle", "Number of idle database connections"
            ),
            "query_duration_avg": metrics.Gauge(
                "hms_database_query_duration_avg_seconds",
                "Average query duration in seconds",
            ),
            "slow_queries_count": metrics.Counter(
                "hms_database_slow_queries_total", "Total number of slow queries"
            ),
            "cache_hit_ratio": metrics.Gauge(
                "hms_database_cache_hit_ratio", "Database cache hit ratio (0-1)"
            ),
            "deadlocks_count": metrics.Counter(
                "hms_database_deadlocks_total", "Total number of deadlocks detected"
            ),
            "replication_lag": metrics.Gauge(
                "hms_database_replication_lag_seconds",
                "Database replication lag in seconds",
            ),
            "table_bloat_ratio": metrics.Gauge(
                "hms_database_table_bloat_ratio", "Table bloat ratio (0-1)"
            ),
            "index_usage_ratio": metrics.Gauge(
                "hms_database_index_usage_ratio", "Index usage ratio (0-1)"
            ),
        }

        # Alert thresholds
        self.thresholds = {
            "slow_query_count": {"warning": 10, "critical": 50},
            "connection_usage": {"warning": 0.8, "critical": 0.95},
            "cache_hit_ratio": {"warning": 0.7, "critical": 0.5},
            "replication_lag": {"warning": 30, "critical": 300},
            "deadlock_rate": {"warning": 0.1, "critical": 1.0},
            "table_bloat": {"warning": 0.2, "critical": 0.5},
            "query_duration": {"warning": 1.0, "critical": 5.0},
        }

    def start_monitoring(self):
        """Start the monitoring service"""
        if not self.running:
            self.running = True
            self.collection_thread = threading.Thread(target=self._collect_metrics_loop)
            self.collection_thread.daemon = True
            self.collection_thread.start()
            logger.info("Database monitoring started")

    def stop_monitoring(self):
        """Stop the monitoring service"""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        logger.info("Database monitoring stopped")

    def _collect_metrics_loop(self):
        """Main metrics collection loop"""
        while self.running:
            try:
                self._collect_all_metrics()
                self._check_alerts()
                time.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                time.sleep(5)  # Wait before retrying

    def _collect_all_metrics(self):
        """Collect all database metrics"""
        timestamp = datetime.now()

        # Connection metrics
        self._collect_connection_metrics(timestamp)

        # Query performance metrics
        self._collect_query_metrics(timestamp)

        # Cache metrics
        self._collect_cache_metrics(timestamp)

        # Replication metrics
        self._collect_replication_metrics(timestamp)

        # Table and index metrics
        self._collect_table_index_metrics(timestamp)

        # Deadlock metrics
        self._collect_deadlock_metrics(timestamp)

    def _collect_connection_metrics(self, timestamp: datetime):
        """Collect connection-related metrics"""
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        count(*) FILTER (WHERE state = 'active') as active,
                        count(*) FILTER (WHERE state = 'idle') as idle,
                        count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction,
                        count(*) as total
                    FROM pg_stat_activity;
                """
                )
                row = cursor.fetchone()

                metrics = [
                    DatabaseMetric(
                        name="connections_active",
                        value=row[0],
                        metric_type=MetricType.GAUGE,
                        timestamp=timestamp,
                        tags={"database": "default"},
                    ),
                    DatabaseMetric(
                        name="connections_idle",
                        value=row[1],
                        metric_type=MetricType.GAUGE,
                        timestamp=timestamp,
                        tags={"database": "default"},
                    ),
                    DatabaseMetric(
                        name="connections_idle_in_transaction",
                        value=row[2],
                        metric_type=MetricType.GAUGE,
                        timestamp=timestamp,
                        tags={"database": "default"},
                    ),
                    DatabaseMetric(
                        name="connections_total",
                        value=row[3],
                        metric_type=MetricType.GAUGE,
                        timestamp=timestamp,
                        tags={"database": "default"},
                    ),
                ]

                # Update Prometheus metrics
                self.prometheus_metrics["connections_active"].set(row[0])
                self.prometheus_metrics["connections_idle"].set(row[1])

                # Store metrics
                self._store_metrics(metrics)

        except Exception as e:
            logger.error(f"Error collecting connection metrics: {e}")

    def _collect_query_metrics(self, timestamp: datetime):
        """Collect query performance metrics"""
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        count(*) as total_queries,
                        sum(calls) as total_calls,
                        sum(total_exec_time) as total_time,
                        avg(mean_exec_time) as avg_time,
                        count(*) FILTER (WHERE mean_exec_time > 1) as slow_queries
                    FROM pg_stat_statements;
                """
                )
                row = cursor.fetchone()

                if row:
                    metrics = [
                        DatabaseMetric(
                            name="queries_total",
                            value=row[0],
                            metric_type=MetricType.COUNTER,
                            timestamp=timestamp,
                        ),
                        DatabaseMetric(
                            name="query_duration_avg",
                            value=row[3] if row[3] else 0,
                            metric_type=MetricType.GAUGE,
                            timestamp=timestamp,
                        ),
                        DatabaseMetric(
                            name="slow_queries_count",
                            value=row[4] if row[4] else 0,
                            metric_type=MetricType.COUNTER,
                            timestamp=timestamp,
                        ),
                    ]

                    # Update Prometheus metrics
                    self.prometheus_metrics["query_duration_avg"].set(row[3] or 0)
                    if row[4]:
                        self.prometheus_metrics["slow_queries_count"].inc(row[4])

                    self._store_metrics(metrics)

        except Exception as e:
            logger.error(f"Error collecting query metrics: {e}")

    def _collect_cache_metrics(self, timestamp: datetime):
        """Collect cache performance metrics"""
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        sum(heap_blks_hit) as hits,
                        sum(heap_blks_read) as reads,
                        CASE
                            WHEN sum(heap_blks_hit + heap_blks_read) = 0 THEN 0
                            ELSE sum(heap_blks_hit)::float / (sum(heap_blks_hit + heap_blks_read))
                        END as hit_ratio
                    FROM pg_statio_user_tables;
                """
                )
                row = cursor.fetchone()

                if row:
                    metrics = [
                        DatabaseMetric(
                            name="cache_hits",
                            value=row[0] if row[0] else 0,
                            metric_type=MetricType.COUNTER,
                            timestamp=timestamp,
                        ),
                        DatabaseMetric(
                            name="cache_reads",
                            value=row[1] if row[1] else 0,
                            metric_type=MetricType.COUNTER,
                            timestamp=timestamp,
                        ),
                        DatabaseMetric(
                            name="cache_hit_ratio",
                            value=row[2] if row[2] else 0,
                            metric_type=MetricType.GAUGE,
                            timestamp=timestamp,
                        ),
                    ]

                    # Update Prometheus metrics
                    self.prometheus_metrics["cache_hit_ratio"].set(row[2] or 0)

                    self._store_metrics(metrics)

        except Exception as e:
            logger.error(f"Error collecting cache metrics: {e}")

    def _collect_replication_metrics(self, timestamp: datetime):
        """Collect replication metrics"""
        try:
            with connection.cursor() as cursor:
                # Check if this is a replica
                cursor.execute("SELECT pg_is_in_recovery();")
                is_replica = cursor.fetchone()[0]

                if is_replica:
                    cursor.execute(
                        """
                        SELECT
                            EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) as lag_seconds
                    """
                    )
                    lag = cursor.fetchone()[0] or 0

                    metrics = [
                        DatabaseMetric(
                            name="replication_lag",
                            value=lag,
                            metric_type=MetricType.GAUGE,
                            timestamp=timestamp,
                            tags={"role": "replica"},
                        )
                    ]

                    # Update Prometheus metrics
                    self.prometheus_metrics["replication_lag"].set(lag)

                    self._store_metrics(metrics)

        except Exception as e:
            logger.error(f"Error collecting replication metrics: {e}")

    def _collect_table_index_metrics(self, timestamp: datetime):
        """Collect table and index bloat metrics"""
        try:
            with connection.cursor() as cursor:
                # Get table bloat information
                cursor.execute(
                    """
                    WITH bloat_info AS (
                        SELECT
                            current_database(),
                            schemaname,
                            tablename,
                            bs.table_size,
                            bs.heap_size,
                            bs.bloat_size,
                            bs.bloat_percentage
                        FROM pg_stat_user_tables t
                        LEFT JOIN (
                            SELECT
                                schemaname,
                                tablename,
                                pg_total_relation_size(schemaname||'.'||tablename) as table_size,
                                pg_relation_size(schemaname||'.'||tablename) as heap_size,
                                pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename) as bloat_size,
                                CASE
                                    WHEN pg_total_relation_size(schemaname||'.'||tablename) = 0 THEN 0
                                    ELSE (pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename))::float / pg_total_relation_size(schemaname||'.'||tablename) * 100
                                END as bloat_percentage
                            FROM pg_tables
                            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                        ) bs ON t.schemaname = bs.schemaname AND t.relname = bs.tablename
                        WHERE t.schemaname NOT IN ('pg_catalog', 'information_schema')
                    )
                    SELECT
                        avg(bloat_percentage) as avg_bloat,
                        count(*) FILTER (WHERE bloat_percentage > 20) as bloated_tables
                    FROM bloat_info;
                """
                )
                row = cursor.fetchone()

                if row:
                    metrics = [
                        DatabaseMetric(
                            name="table_bloat_ratio",
                            value=(row[0] or 0) / 100,
                            metric_type=MetricType.GAUGE,
                            timestamp=timestamp,
                        ),
                        DatabaseMetric(
                            name="bloated_tables_count",
                            value=row[1] or 0,
                            metric_type=MetricType.GAUGE,
                            timestamp=timestamp,
                        ),
                    ]

                    # Update Prometheus metrics
                    self.prometheus_metrics["table_bloat_ratio"].set(
                        (row[0] or 0) / 100
                    )

                    self._store_metrics(metrics)

                # Index usage metrics
                cursor.execute(
                    """
                    SELECT
                        sum(idx_scan) as total_scans,
                        sum(idx_tup_read) as tuples_read,
                        count(*) as total_indexes,
                        count(*) FILTER (WHERE idx_scan = 0) as unused_indexes
                    FROM pg_stat_user_indexes;
                """
                )
                idx_row = cursor.fetchone()

                if idx_row:
                    usage_ratio = 1 - (idx_row[3] / idx_row[2]) if idx_row[2] > 0 else 1
                    metrics.append(
                        DatabaseMetric(
                            name="index_usage_ratio",
                            value=usage_ratio,
                            metric_type=MetricType.GAUGE,
                            timestamp=timestamp,
                        )
                    )

                    # Update Prometheus metrics
                    self.prometheus_metrics["index_usage_ratio"].set(usage_ratio)

                    self._store_metrics([metrics[-1]])

        except Exception as e:
            logger.error(f"Error collecting table/index metrics: {e}")

    def _collect_deadlock_metrics(self, timestamp: datetime):
        """Collect deadlock metrics"""
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT count(*)
                    FROM pg_locks l
                    JOIN pg_stat_activity a ON l.pid = a.pid
                    WHERE l.granted = false
                    AND l.mode LIKE '%ExclusiveLock%';
                """
                )
                blocked_queries = cursor.fetchone()[0]

                metrics = [
                    DatabaseMetric(
                        name="blocked_queries",
                        value=blocked_queries,
                        metric_type=MetricType.GAUGE,
                        timestamp=timestamp,
                    )
                ]

                self._store_metrics(metrics)

        except Exception as e:
            logger.error(f"Error collecting deadlock metrics: {e}")

    def _store_metrics(self, metrics: List[DatabaseMetric]):
        """Store metrics in Redis and local history"""
        for metric in metrics:
            # Store in Redis for quick access
            key = f"metric:{metric.name}"
            data = {
                "value": metric.value,
                "timestamp": metric.timestamp.isoformat(),
                "tags": metric.tags or {},
            }
            self.redis_client.lpush(key, json.dumps(data))
            self.redis_client.ltrim(key, 0, 999)  # Keep last 1000 values

            # Store in local history
            self.metrics_history[metric.name].append(metric)

    def _check_alerts(self):
        """Check all metrics against thresholds"""
        for metric_name, history in self.metrics_history.items():
            if history and metric_name in self.thresholds:
                latest_metric = history[-1]
                thresholds = self.thresholds[metric_name]

                # Check if value exceeds thresholds
                if latest_metric.value > thresholds["critical"]:
                    self._trigger_alert(
                        metric_name=metric_name,
                        current_value=latest_metric.value,
                        threshold=thresholds["critical"],
                        severity=AlertSeverity.CRITICAL,
                        message=f"Critical: {metric_name} is {latest_metric.value:.2f} (threshold: {thresholds['critical']})",
                    )
                elif latest_metric.value > thresholds["warning"]:
                    self._trigger_alert(
                        metric_name=metric_name,
                        current_value=latest_metric.value,
                        threshold=thresholds["warning"],
                        severity=AlertSeverity.HIGH,
                        message=f"Warning: {metric_name} is {latest_metric.value:.2f} (threshold: {thresholds['warning']})",
                    )

    def _trigger_alert(
        self,
        metric_name: str,
        current_value: float,
        threshold: float,
        severity: AlertSeverity,
        message: str,
    ):
        """Trigger an alert"""
        alert_id = f"{metric_name}_{int(time.time())}"

        # Check if similar alert already exists and not resolved
        existing_alert = None
        for alert in self.active_alerts.values():
            if (
                alert.metric_name == metric_name
                and not alert.resolved
                and alert.severity == severity
            ):
                existing_alert = alert
                break

        if existing_alert:
            # Update existing alert
            existing_alert.current_value = current_value
            existing_alert.timestamp = datetime.now()
            logger.info(f"Updated alert: {existing_alert.name}")
        else:
            # Create new alert
            alert = Alert(
                id=alert_id,
                name=f"{metric_name}_alert",
                severity=severity,
                message=message,
                metric_name=metric_name,
                current_value=current_value,
                threshold=threshold,
                timestamp=datetime.now(),
            )

            self.active_alerts[alert_id] = alert
            logger.warning(f"New alert triggered: {alert.message}")

            # Send notifications
            self._send_alert_notifications(alert)

    def _send_alert_notifications(self, alert: Alert):
        """Send alert notifications via configured channels"""
        # Email notification
        if hasattr(settings, "ALERT_EMAILS"):
            self._send_email_alert(alert)

        # Slack notification
        if hasattr(settings, "SLACK_WEBHOOK_URL"):
            self._send_slack_alert(alert)

        # PagerDuty notification
        if alert.severity == AlertSeverity.CRITICAL and hasattr(
            settings, "PAGERDUTY_API_KEY"
        ):
            self._send_pagerduty_alert(alert)

    def _send_email_alert(self, alert: Alert):
        """Send alert via email"""
        try:
            if not settings.ALERT_EMAILS:
                return

            msg = MimeText(
                f"""
Database Alert: {alert.name}

Severity: {alert.severity.value}
Message: {alert.message}
Current Value: {alert.current_value}
Threshold: {alert.threshold}
Timestamp: {alert.timestamp}

Please check the database monitoring dashboard for details.
            """
            )

            msg["Subject"] = f"[HMS DB Alert] {alert.severity.value}: {alert.name}"
            msg["From"] = settings.DEFAULT_FROM_EMAIL
            msg["To"] = ", ".join(settings.ALERT_EMAILS)

            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                if settings.EMAIL_USE_TLS:
                    server.starttls()
                if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
                    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                server.send_message(msg)

            logger.info(f"Email alert sent for {alert.name}")

        except Exception as e:
            logger.error(f"Error sending email alert: {e}")

    def _send_slack_alert(self, alert: Alert):
        """Send alert to Slack"""
        try:
            if not settings.SLACK_WEBHOOK_URL:
                return

            color = {
                AlertSeverity.CRITICAL: "danger",
                AlertSeverity.HIGH: "warning",
                AlertSeverity.MEDIUM: "#ff9500",
                AlertSeverity.LOW: "good",
                AlertSeverity.INFO: "#36a64f",
            }.get(alert.severity, "#36a64f")

            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": f"Database Alert: {alert.name}",
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.value,
                                "short": True,
                            },
                            {
                                "title": "Current Value",
                                "value": str(alert.current_value),
                                "short": True,
                            },
                            {
                                "title": "Threshold",
                                "value": str(alert.threshold),
                                "short": True,
                            },
                            {
                                "title": "Timestamp",
                                "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                                "short": True,
                            },
                        ],
                        "footer": "HMS Database Monitor",
                    }
                ]
            }

            response = requests.post(
                settings.SLACK_WEBHOOK_URL, json=payload, timeout=10
            )

            if response.status_code == 200:
                logger.info(f"Slack alert sent for {alert.name}")
            else:
                logger.error(f"Failed to send Slack alert: {response.text}")

        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")

    def _send_pagerduty_alert(self, alert: Alert):
        """Send alert to PagerDuty"""
        try:
            if not settings.PAGERDUTY_API_KEY:
                return

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Token token={settings.PAGERDUTY_API_KEY}",
            }

            payload = {
                "payload": {
                    "summary": alert.message,
                    "source": "hms-database-monitor",
                    "severity": (
                        "critical"
                        if alert.severity == AlertSeverity.CRITICAL
                        else "error"
                    ),
                    "timestamp": alert.timestamp.isoformat(),
                    "custom_details": {
                        "metric_name": alert.metric_name,
                        "current_value": alert.current_value,
                        "threshold": alert.threshold,
                    },
                }
            }

            response = requests.post(
                "https://events.pagerduty.com/v2/enqueue",
                headers=headers,
                json=payload,
                timeout=10,
            )

            if response.status_code == 202:
                logger.info(f"PagerDuty alert sent for {alert.name}")
            else:
                logger.error(f"Failed to send PagerDuty alert: {response.text}")

        except Exception as e:
            logger.error(f"Error sending PagerDuty alert: {e}")

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of current metrics"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "metrics": {},
            "active_alerts": len(self.active_alerts),
            "critical_alerts": len(
                [
                    a
                    for a in self.active_alerts.values()
                    if a.severity == AlertSeverity.CRITICAL
                ]
            ),
        }

        # Get latest values for key metrics
        for metric_name in [
            "connections_active",
            "query_duration_avg",
            "cache_hit_ratio",
            "replication_lag",
        ]:
            if (
                metric_name in self.metrics_history
                and self.metrics_history[metric_name]
            ):
                latest = self.metrics_history[metric_name][-1]
                summary["metrics"][metric_name] = {
                    "value": latest.value,
                    "timestamp": latest.timestamp.isoformat(),
                }

        return summary

    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alert history for specified period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # Get from Redis
        history_key = f"alert_history:{hours}h"
        alert_history = self.redis_client.lrange(history_key, 0, -1) or []

        # Convert to list of dicts
        alerts = []
        for alert_data in alert_history:
            alert_dict = json.loads(alert_data)
            alert_dict["timestamp"] = datetime.fromisoformat(alert_dict["timestamp"])
            if alert_dict["timestamp"] >= cutoff_time:
                alerts.append(alert_dict)

        return sorted(alerts, key=lambda x: x["timestamp"], reverse=True)

    def acknowledge_alert(self, alert_id: str, user: str):
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.acknowledged_by = user
            alert.acknowledged_at = datetime.now()
            logger.info(f"Alert {alert_id} acknowledged by {user}")
            return True
        return False

    def resolve_alert(self, alert_id: str, user: str):
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            logger.info(f"Alert {alert_id} resolved by {user}")

            # Move to history
            self.redis_client.lpush(f"alert_history:24h", json.dumps(asdict(alert)))

            # Remove from active alerts
            del self.active_alerts[alert_id]
            return True
        return False

    def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive database health report"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "overall_health": "GOOD",
            "metrics": {},
            "alerts": {
                "active": len(self.active_alerts),
                "critical": len(
                    [
                        a
                        for a in self.active_alerts.values()
                        if a.severity == AlertSeverity.CRITICAL
                    ]
                ),
                "high": len(
                    [
                        a
                        for a in self.active_alerts.values()
                        if a.severity == AlertSeverity.HIGH
                    ]
                ),
                "medium": len(
                    [
                        a
                        for a in self.active_alerts.values()
                        if a.severity == AlertSeverity.MEDIUM
                    ]
                ),
            },
            "recommendations": [],
        }

        # Analyze metrics
        if (
            "cache_hit_ratio" in self.metrics_history
            and self.metrics_history["cache_hit_ratio"]
        ):
            latest_cache_ratio = self.metrics_history["cache_hit_ratio"][-1].value
            report["metrics"]["cache_hit_ratio"] = latest_cache_ratio
            if latest_cache_ratio < 0.7:
                report["recommendations"].append(
                    "Low cache hit ratio detected. Consider increasing shared_buffers or optimizing queries."
                )

        if (
            "query_duration_avg" in self.metrics_history
            and self.metrics_history["query_duration_avg"]
        ):
            latest_query_time = self.metrics_history["query_duration_avg"][-1].value
            report["metrics"]["avg_query_duration"] = latest_query_time
            if latest_query_time > 1.0:
                report["recommendations"].append(
                    "Slow average query time detected. Review and optimize slow queries."
                )

        # Determine overall health
        if report["alerts"]["critical"] > 0:
            report["overall_health"] = "CRITICAL"
        elif report["alerts"]["high"] > 2:
            report["overall_health"] = "WARNING"
        elif report["alerts"]["medium"] > 5:
            report["overall_health"] = "DEGRADED"

        return report


# Global monitor instance
database_monitor = DatabaseMonitor()
