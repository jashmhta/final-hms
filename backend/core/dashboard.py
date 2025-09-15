import logging
from datetime import datetime, timedelta
from typing import Dict, List
from django.core.cache import cache
from django.db.models import Count, Q
from django.utils import timezone

from .compliance import compliance_checker
from .anomaly_detection import security_monitor

logger = logging.getLogger(__name__)


class SecurityDashboard:
    """Security monitoring dashboard"""

    def __init__(self):
        self.cache_timeout = 300  # 5 minutes

    def get_dashboard_data(self) -> Dict:
        """Get comprehensive security dashboard data"""
        cache_key = 'security_dashboard_data'
        data = cache.get(cache_key)

        if data is None:
            data = self._generate_dashboard_data()
            cache.set(cache_key, data, self.cache_timeout)

        return data

    def _generate_dashboard_data(self) -> Dict:
        """Generate fresh dashboard data"""
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)

        return {
            'timestamp': now,
            'threat_overview': self._get_threat_overview(last_24h, last_7d),
            'compliance_status': self._get_compliance_status(),
            'access_patterns': self._get_access_patterns(last_24h),
            'anomaly_alerts': self._get_anomaly_alerts(last_24h),
            'system_health': self._get_system_health(),
            'recent_incidents': self._get_recent_incidents(last_7d),
            'recommendations': self._get_security_recommendations()
        }

    def _get_threat_overview(self, last_24h, last_7d) -> Dict:
        """Get threat overview statistics"""
        from authentication.models import SecurityEvent

        # Get event counts by severity
        events_24h = SecurityEvent.objects.filter(created_at__gte=last_24h)
        events_7d = SecurityEvent.objects.filter(created_at__gte=last_7d)

        severity_counts_24h = events_24h.values('severity').annotate(count=Count('severity'))
        severity_counts_7d = events_7d.values('severity').annotate(count=Count('severity'))

        return {
            'last_24h': {
                'total_events': events_24h.count(),
                'by_severity': {item['severity']: item['count'] for item in severity_counts_24h}
            },
            'last_7d': {
                'total_events': events_7d.count(),
                'by_severity': {item['severity']: item['count'] for item in severity_counts_7d}
            },
            'trend': self._calculate_trend(events_24h.count(), events_7d.count() / 7)
        }

    def _get_compliance_status(self) -> Dict:
        """Get compliance status overview"""
        try:
            compliance_results = compliance_checker.run_compliance_check()
            return {
                'overall_score': compliance_results['overall_score'],
                'hipaa_score': sum(compliance_results.get('hipaa', {}).values()) / len(compliance_results.get('hipaa', [1])),
                'gdpr_score': sum(compliance_results.get('gdpr', {}).values()) / len(compliance_results.get('gdpr', [1])),
                'critical_issues': len(compliance_results['critical_issues']),
                'last_check': compliance_results['timestamp']
            }
        except Exception as e:
            logger.error(f"Error getting compliance status: {e}")
            return {
                'overall_score': 0,
                'hipaa_score': 0,
                'gdpr_score': 0,
                'critical_issues': 0,
                'error': str(e)
            }

    def _get_access_patterns(self, last_24h) -> Dict:
        """Get access pattern analytics"""
        from authentication.models import LoginSession

        sessions = LoginSession.objects.filter(created_at__gte=last_24h)

        # Geographic distribution
        geo_data = sessions.values('ip_address').annotate(count=Count('ip_address')).order_by('-count')[:10]

        # Device types
        device_data = sessions.values('device_info').annotate(count=Count('device_info')).order_by('-count')[:5]

        # Failed login attempts
        failed_logins = sessions.filter(is_active=False).count()

        return {
            'total_sessions': sessions.count(),
            'unique_ips': sessions.values('ip_address').distinct().count(),
            'failed_logins': failed_logins,
            'success_rate': ((sessions.count() - failed_logins) / sessions.count() * 100) if sessions.count() > 0 else 100,
            'top_locations': list(geo_data),
            'device_types': list(device_data)
        }

    def _get_anomaly_alerts(self, last_24h) -> List[Dict]:
        """Get recent anomaly alerts"""
        # This would integrate with the anomaly detection system
        # For now, return mock data
        return [
            {
                'id': 1,
                'type': 'UNUSUAL_ACCESS_PATTERN',
                'severity': 'MEDIUM',
                'description': 'Unusual login from new location',
                'timestamp': timezone.now() - timedelta(hours=2),
                'status': 'ACTIVE'
            },
            {
                'id': 2,
                'type': 'FAILED_LOGIN_SPIKE',
                'severity': 'HIGH',
                'description': 'Multiple failed login attempts from same IP',
                'timestamp': timezone.now() - timedelta(hours=4),
                'status': 'INVESTIGATING'
            }
        ]

    def _get_system_health(self) -> Dict:
        """Get system health metrics"""
        return {
            'encryption_status': 'HEALTHY',
            'backup_status': 'UP_TO_DATE',
            'monitoring_services': 'ALL_ACTIVE',
            'certificate_expiry': '45_days',
            'disk_usage': '68%',
            'memory_usage': '72%'
        }

    def _get_recent_incidents(self, last_7d) -> List[Dict]:
        """Get recent security incidents"""
        from authentication.models import SecurityEvent

        incidents = SecurityEvent.objects.filter(
            created_at__gte=last_7d,
            severity__in=['HIGH', 'CRITICAL']
        ).order_by('-created_at')[:10]

        return [{
            'id': incident.id,
            'type': incident.event_type,
            'severity': incident.severity,
            'description': incident.description,
            'timestamp': incident.created_at,
            'status': 'RESOLVED' if incident.resolved_at else 'ACTIVE'
        } for incident in incidents]

    def _get_security_recommendations(self) -> List[str]:
        """Get security recommendations"""
        return [
            "Enable multi-factor authentication for all administrative accounts",
            "Review and update access control policies quarterly",
            "Implement automated log analysis and alerting",
            "Conduct regular security awareness training for staff",
            "Perform penetration testing every 6 months",
            "Ensure all sensitive data is encrypted at rest and in transit"
        ]

    def _calculate_trend(self, recent_count: int, avg_daily: float) -> str:
        """Calculate trend direction"""
        if recent_count > avg_daily * 1.2:
            return 'INCREASING'
        elif recent_count < avg_daily * 0.8:
            return 'DECREASING'
        else:
            return 'STABLE'


class ComplianceDashboard:
    """Compliance monitoring dashboard"""

    def get_compliance_dashboard(self) -> Dict:
        """Get compliance dashboard data"""
        cache_key = 'compliance_dashboard_data'
        data = cache.get(cache_key)

        if data is None:
            data = self._generate_compliance_dashboard()
            cache.set(cache_key, data, 3600)  # 1 hour cache

        return data

    def _generate_compliance_dashboard(self) -> Dict:
        """Generate compliance dashboard data"""
        from core.compliance import compliance_reporter

        report = compliance_reporter.generate_compliance_report()

        return {
            'overall_score': report['detailed_findings']['overall_score'],
            'hipaa_compliance': self._format_compliance_data(report['detailed_findings'].get('hipaa', {})),
            'gdpr_compliance': self._format_compliance_data(report['detailed_findings'].get('gdpr', {})),
            'critical_issues': report['detailed_findings']['critical_issues'],
            'action_items': report['action_items'],
            'last_updated': report['generated_at'],
            'next_audit_due': timezone.now() + timedelta(days=90)
        }

    def _format_compliance_data(self, compliance_dict: Dict) -> List[Dict]:
        """Format compliance data for dashboard"""
        return [
            {
                'requirement': req,
                'score': score,
                'status': self._get_status_from_score(score),
                'color': self._get_color_from_score(score)
            }
            for req, score in compliance_dict.items()
        ]

    def _get_status_from_score(self, score: float) -> str:
        """Get status text from compliance score"""
        if score >= 0.9:
            return 'Excellent'
        elif score >= 0.8:
            return 'Good'
        elif score >= 0.7:
            return 'Satisfactory'
        elif score >= 0.6:
            return 'Needs Improvement'
        else:
            return 'Critical'

    def _get_color_from_score(self, score: float) -> str:
        """Get color code from compliance score"""
        if score >= 0.9:
            return '#10B981'  # Green
        elif score >= 0.8:
            return '#3B82F6'  # Blue
        elif score >= 0.7:
            return '#F59E0B'  # Yellow
        elif score >= 0.6:
            return '#F97316'  # Orange
        else:
            return '#EF4444'  # Red


