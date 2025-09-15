#!/usr/bin/env python3
"""
Real-time performance monitoring and alerting for HMS.
"""

import time
import psutil
import redis
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Real-time performance monitoring system."""

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis = redis.from_url(self.redis_url)
        self.metrics_window = 300  # 5 minutes

    def collect_system_metrics(self) -> Dict:
        """Collect system-level performance metrics."""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'network_connections': len(psutil.net_connections()),
            'timestamp': datetime.now().isoformat()
        }

    def collect_application_metrics(self) -> Dict:
        """Collect application-level performance metrics."""
        # This would integrate with Django/Prometheus metrics
        # For now, return placeholder
        return {
            'active_connections': 0,  # From Django
            'response_time_avg': 0.0,  # From Prometheus
            'error_rate': 0.0,         # From Prometheus
            'cache_hit_rate': 0.0,     # From Redis
            'timestamp': datetime.now().isoformat()
        }

    def check_sla_compliance(self, metrics: Dict) -> List[str]:
        """Check SLA compliance and return alerts."""
        alerts = []

        # Response time SLA: 95th percentile < 100ms
        if metrics.get('response_time_95p', 0) > 0.1:
            alerts.append(f"SLA Breach: API response time 95th percentile = {metrics['response_time_95p']:.3f}s")

        # Error rate SLA: < 0.1%
        if metrics.get('error_rate', 0) > 0.001:
            alerts.append(f"SLA Breach: Error rate = {metrics['error_rate']:.3f}%")

        # Uptime SLA: > 99.9%
        if metrics.get('uptime_percent', 100) < 99.9:
            alerts.append(f"SLA Breach: Uptime = {metrics['uptime_percent']:.3f}%")

        return alerts

    def store_metrics(self, metrics: Dict, key_prefix: str = "performance"):
        """Store metrics in Redis with timestamp."""
        timestamp = int(time.time())
        key = f"{key_prefix}:{timestamp}"

        # Store as JSON
        self.redis.setex(key, self.metrics_window, json.dumps(metrics))

        # Maintain time series (keep last 24 hours)
        self.redis.zadd(f"{key_prefix}:timeseries", {timestamp: timestamp})
        self.redis.zremrangebyscore(f"{key_prefix}:timeseries", 0, timestamp - 86400)

    def get_metrics_history(self, key_prefix: str = "performance",
                          hours: int = 1) -> List[Dict]:
        """Retrieve metrics history."""
        cutoff = int(time.time()) - (hours * 3600)

        # Get timestamp keys
        timestamps = self.redis.zrangebyscore(
            f"{key_prefix}:timeseries", cutoff, float('inf')
        )

        metrics = []
        for ts in timestamps:
            key = f"{key_prefix}:{ts.decode()}"
            data = self.redis.get(key)
            if data:
                metrics.append(json.loads(data))

        return metrics

    def generate_performance_report(self) -> str:
        """Generate comprehensive performance report."""
        report = []
        report.append("# HMS Performance Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Current metrics
        current_metrics = self.collect_system_metrics()
        report.append("## Current System Metrics")
        report.append(f"- CPU Usage: {current_metrics['cpu_percent']:.1f}%")
        report.append(f"- Memory Usage: {current_metrics['memory_percent']:.1f}%")
        report.append(f"- Disk Usage: {current_metrics['disk_usage']:.1f}%")
        report.append("")

        # SLA Status
        alerts = self.check_sla_compliance({})
        if alerts:
            report.append("## ⚠️ SLA Alerts")
            for alert in alerts:
                report.append(f"- {alert}")
            report.append("")
        else:
            report.append("## ✅ All SLAs Met")
            report.append("")

        # Historical trends (last 24 hours)
        history = self.get_metrics_history(hours=24)
        if history:
            report.append("## 24-Hour Trends")
            cpu_trend = [m.get('cpu_percent', 0) for m in history if 'cpu_percent' in m]
            memory_trend = [m.get('memory_percent', 0) for m in history if 'memory_percent' in m]

            if cpu_trend:
                report.append(".1f")
            if memory_trend:
                report.append(".1f")
            report.append("")

        # Recommendations
        report.append("## Recommendations")
        if current_metrics['cpu_percent'] > 80:
            report.append("- Consider scaling up CPU resources")
        if current_metrics['memory_percent'] > 85:
            report.append("- Consider scaling up memory resources")
        if current_metrics['disk_usage'] > 90:
            report.append("- Monitor disk space and consider cleanup")

        return "\n".join(report)

    def run_continuous_monitoring(self, interval: int = 60):
        """Run continuous performance monitoring."""
        logger.info(f"Starting continuous performance monitoring (interval: {interval}s)")

        while True:
            try:
                # Collect and store metrics
                system_metrics = self.collect_system_metrics()
                app_metrics = self.collect_application_metrics()

                combined_metrics = {**system_metrics, **app_metrics}
                self.store_metrics(combined_metrics)

                # Check for alerts
                alerts = self.check_sla_compliance(combined_metrics)
                for alert in alerts:
                    logger.warning(f"ALERT: {alert}")

                # Generate periodic report
                if int(time.time()) % 3600 == 0:  # Every hour
                    report = self.generate_performance_report()
                    with open(f'performance_report_{datetime.now().strftime("%Y%m%d_%H%M")}.md', 'w') as f:
                        f.write(report)
                    logger.info("Hourly performance report generated")

                time.sleep(interval)

            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(interval)


def main():
    """Main monitoring execution."""
    monitor = PerformanceMonitor()

    # Run continuous monitoring
    try:
        monitor.run_continuous_monitoring(interval=30)  # 30 second intervals
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")


if __name__ == "__main__":
    main()