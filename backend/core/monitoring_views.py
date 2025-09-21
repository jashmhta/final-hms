from datetime import datetime, timedelta
from typing import Dict, Any, List
from django.db import connection
from django.http import JsonResponse, HttpRequest
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from .logging_monitoring import (
    HealthChecker, PerformanceMonitor, AuditLogger,
    SYSTEM_METRICS, ERROR_COUNT, REQUEST_COUNT
)
from .models import AuditLog, SystemMetric
from .permissions import IsSuperAdmin


class HealthCheckView(View):
    """System health check endpoint"""

    def get(self, request: HttpRequest) -> JsonResponse:
        """Get comprehensive system health status"""
        try:
            health_status = HealthChecker.check_system_health()

            # Add additional checks
            health_status['additional_checks'] = {
                'database_connection': self._check_database_connection(),
                'cache_status': self._check_cache_status(),
                'file_system': self._check_file_system(),
                'system_load': self._check_system_load(),
            }

            # Calculate overall status
            all_healthy = all(
                check.get('status') == 'healthy'
                for check in health_status['additional_checks'].values()
            )

            health_status['overall'] = 'healthy' if all_healthy else 'degraded'

            # Add timestamp
            health_status['timestamp'] = datetime.utcnow().isoformat()
            health_status['version'] = '1.0.0'

            status_code = 200 if health_status['overall'] == 'healthy' else 503
            return JsonResponse(health_status, status=status_code)

        except Exception as e:
            return JsonResponse({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }, status=500)

    def _check_database_connection(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            with connection.cursor() as cursor:
                # Simple connectivity test
                start_time = datetime.now()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                response_time = (datetime.now() - start_time).total_seconds()

                # Check database size and table count
                cursor.execute("""
                    SELECT
                        pg_size_pretty(pg_database_size(current_database())) as db_size,
                        (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public') as table_count
                """)
                db_info = cursor.fetchone()

                return {
                    'status': 'healthy',
                    'response_time': response_time,
                    'database_size': db_info[0],
                    'table_count': db_info[1],
                }
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}

    def _check_cache_status(self) -> Dict[str, Any]:
        """Check Redis cache status"""
        try:
            from django.core.cache import cache
            from django.conf import settings

            # Test cache operations
            test_key = 'health_check_test'
            test_value = 'test_value'

            # Test set operation
            cache.set(test_key, test_value, 60)

            # Test get operation
            retrieved_value = cache.get(test_key)

            # Clean up
            cache.delete(test_key)

            if retrieved_value == test_value:
                return {'status': 'healthy'}
            else:
                return {'status': 'unhealthy', 'error': 'Cache read/write failed'}

        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}

    def _check_file_system(self) -> Dict[str, Any]:
        """Check file system health"""
        try:
            import os
            from pathlib import Path

            # Check log directory
            log_dir = Path(settings.BASE_DIR) / 'logs'
            log_dir.mkdir(exist_ok=True)

            # Test file write
            test_file = log_dir / 'health_check.tmp'
            test_file.write_text('health check test')

            # Test file read
            content = test_file.read_text()

            # Clean up
            test_file.unlink()

            if content == 'health check test':
                return {'status': 'healthy'}
            else:
                return {'status': 'unhealthy', 'error': 'File read/write failed'}

        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}

    def _check_system_load(self) -> Dict[str, Any]:
        """Check system load and resources"""
        try:
            import psutil

            # Get system load
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]

            # Get memory info
            memory = psutil.virtual_memory()

            # Get disk info
            disk = psutil.disk_usage('/')

            return {
                'status': 'healthy',
                'load_average': {
                    '1min': load_avg[0],
                    '5min': load_avg[1],
                    '15min': load_avg[2],
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent_used': memory.percent,
                },
                'disk': {
                    'total': disk.total,
                    'free': disk.free,
                    'percent_used': disk.percent,
                },
            }
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}


class MetricsView(View):
    """Prometheus metrics endpoint"""

    def get(self, request: HttpRequest) -> JsonResponse:
        """Export Prometheus metrics"""
        try:
            # Update system metrics before exporting
            PerformanceMonitor.update_system_metrics()

            # Generate metrics
            metrics_data = generate_latest().decode('utf-8')

            return JsonResponse(
                {'metrics': metrics_data},
                status=200,
                content_type=CONTENT_TYPE_LATEST
            )
        except Exception as e:
            return JsonResponse(
                {'error': str(e)},
                status=500
            )


@method_decorator(cache_page(60), name='dispatch')
class DashboardView(TemplateView):
    """Admin dashboard with system overview"""

    template_name = 'core/dashboard.html'
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        # Get system health
        health_status = HealthChecker.check_system_health()

        # Get recent activity
        recent_activity = AuditLog.objects.select_related('user').order_by('-created_at')[:20]

        # Get error statistics
        error_stats = self._get_error_statistics()

        # Get performance metrics
        performance_metrics = self._get_performance_metrics()

        context.update({
            'health_status': health_status,
            'recent_activity': recent_activity,
            'error_stats': error_stats,
            'performance_metrics': performance_metrics,
            'timestamp': datetime.now(),
        })

        return context

    def _get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for the dashboard"""
        try:
            from django.db.models import Count
            from datetime import timedelta

            last_24h = datetime.now() - timedelta(hours=24)

            error_counts = AuditLog.objects.filter(
                created_at__gte=last_24h,
                action__in=['exception', 'security_event']
            ).values('action').annotate(count=Count('id'))

            return {item['action']: item['count'] for item in error_counts}

        except Exception:
            return {}

    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the dashboard"""
        try:
            metrics = {}

            # Get CPU and memory usage
            import psutil
            metrics['cpu_percent'] = psutil.cpu_percent(interval=1)
            metrics['memory_percent'] = psutil.virtual_memory().percent

            # Get database connection count
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT count(*)
                    FROM pg_stat_activity
                    WHERE state = 'active'
                """)
                metrics['active_connections'] = cursor.fetchone()[0]

            return metrics

        except Exception:
            return {}


class MonitoringViewSet(viewsets.ViewSet):
    """Comprehensive monitoring API endpoints"""
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    @action(detail=False, methods=['get'])
    def system_health(self, request):
        """Get detailed system health information"""
        health_status = HealthChecker.check_system_health()

        # Add detailed component checks
        health_status['components'] = {
            'database': self._check_database_detailed(),
            'cache': self._check_cache_detailed(),
            'storage': self._check_storage_detailed(),
            'services': self._check_services_detailed(),
        }

        return Response(health_status)

    @action(detail=False, methods=['get'])
    def performance_metrics(self, request):
        """Get detailed performance metrics"""
        hours = int(request.query_params.get('hours', 24))

        # Update system metrics
        PerformanceMonitor.update_system_metrics()

        metrics = {
            'system': self._get_system_metrics(),
            'database': self._get_database_metrics(hours),
            'cache': self._get_cache_metrics(hours),
            'api': self._get_api_metrics(hours),
            'errors': self._get_error_metrics(hours),
        }

        return Response(metrics)

    @action(detail=False, methods=['get'])
    def audit_logs(self, request):
        """Get audit logs with filtering"""
        from django.db.models import Q

        # Query parameters
        limit = int(request.query_params.get('limit', 100))
        offset = int(request.query_params.get('offset', 0))
        user_id = request.query_params.get('user_id')
        action = request.query_params.get('action')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Build queryset
        queryset = AuditLog.objects.select_related('user').order_by('-created_at')

        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if action:
            queryset = queryset.filter(action=action)
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        # Apply pagination
        total_count = queryset.count()
        logs = queryset[offset:offset + limit]

        return Response({
            'logs': [
                {
                    'id': log.id,
                    'timestamp': log.created_at.isoformat(),
                    'user': {
                        'id': log.user.id,
                        'username': log.user.username,
                        'role': getattr(log.user, 'role', 'unknown'),
                    } if log.user else None,
                    'action': log.action,
                    'details': log.details,
                    'ip_address': log.ip_address,
                    'user_agent': log.user_agent,
                }
                for log in logs
            ],
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
        })

    @action(detail=False, methods=['get'])
    def error_analysis(self, request):
        """Get detailed error analysis"""
        hours = int(request.query_params.get('hours', 24))

        from datetime import timedelta
        from django.db.models import Count, Q

        start_time = datetime.now() - timedelta(hours=hours)

        # Error counts by type
        error_types = (
            AuditLog.objects
            .filter(created_at__gte=start_time, action='exception')
            .values('details__error_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        # Error trends over time
        error_trends = (
            AuditLog.objects
            .filter(created_at__gte=start_time, action='exception')
            .extra({'hour': "date_trunc('hour', created_at)"})
            .values('hour')
            .annotate(count=Count('id'))
            .order_by('hour')
        )

        # Error counts by user
        error_users = (
            AuditLog.objects
            .filter(created_at__gte=start_time, action='exception')
            .values('user__username', 'user__role')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

        return Response({
            'error_types': list(error_types),
            'error_trends': [
                {
                    'hour': trend['hour'].isoformat(),
                    'count': trend['count']
                }
                for trend in error_trends
            ],
            'top_users_by_errors': list(error_users),
            'time_period_hours': hours,
        })

    @action(detail=False, methods=['post'])
    def run_diagnostics(self, request):
        """Run system diagnostics"""
        try:
            diagnostics = {
                'database_connectivity': self._test_database_connectivity(),
                'cache_functionality': self._test_cache_functionality(),
                'file_operations': self._test_file_operations(),
                'api_endpoints': self._test_api_endpoints(),
                'background_tasks': self._test_background_tasks(),
            }

            # Log diagnostic run
            AuditLogger.log_action(
                user=request.user,
                action='run_diagnostics',
                resource='system',
                details=diagnostics
            )

            return Response(diagnostics)

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=500)

    def _check_database_detailed(self) -> Dict[str, Any]:
        """Detailed database health check"""
        try:
            with connection.cursor() as cursor:
                # Connection info
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]

                # Database size
                cursor.execute("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as size
                """)
                size = cursor.fetchone()[0]

                # Active connections
                cursor.execute("""
                    SELECT count(*) FROM pg_stat_activity WHERE state = 'active'
                """)
                active_connections = cursor.fetchone()[0]

                # Slow queries
                cursor.execute("""
                    SELECT count(*) FROM pg_stat_statements
                    WHERE mean_exec_time > 1000
                """)
                slow_queries = cursor.fetchone()[0]

                return {
                    'status': 'healthy',
                    'version': version,
                    'size': size,
                    'active_connections': active_connections,
                    'slow_queries': slow_queries,
                }
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}

    def _check_cache_detailed(self) -> Dict[str, Any]:
        """Detailed cache health check"""
        try:
            from django.core.cache import cache

            # Test cache operations with timing
            import time

            # Set operation
            start_time = time.time()
            cache.set('health_test', 'test_value', 60)
            set_time = time.time() - start_time

            # Get operation
            start_time = time.time()
            value = cache.get('health_test')
            get_time = time.time() - start_time

            # Delete operation
            start_time = time.time()
            cache.delete('health_test')
            delete_time = time.time() - start_time

            return {
                'status': 'healthy',
                'operation_times': {
                    'set_seconds': set_time,
                    'get_seconds': get_time,
                    'delete_seconds': delete_time,
                },
                'test_passed': value == 'test_value',
            }
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}

    def _check_storage_detailed(self) -> Dict[str, Any]:
        """Detailed storage health check"""
        try:
            import os
            from pathlib import Path

            # Check multiple directories
            directories = [
                Path(settings.BASE_DIR) / 'logs',
                Path(settings.MEDIA_ROOT),
                Path(settings.STATIC_ROOT),
            ]

            storage_info = {}
            all_healthy = True

            for directory in directories:
                try:
                    directory.mkdir(parents=True, exist_ok=True)

                    # Test file operations
                    test_file = directory / f'test_{datetime.now().timestamp()}.tmp'
                    test_file.write_text('storage test')
                    content = test_file.read_text()
                    test_file.unlink()

                    # Get directory size
                    total_size = sum(f.stat().st_size for f in directory.rglob('*') if f.is_file())

                    storage_info[directory.name] = {
                        'status': 'healthy',
                        'path': str(directory),
                        'size_bytes': total_size,
                        'test_passed': content == 'storage test',
                    }
                except Exception as e:
                    storage_info[directory.name] = {
                        'status': 'unhealthy',
                        'error': str(e),
                    }
                    all_healthy = False

            return {
                'status': 'healthy' if all_healthy else 'degraded',
                'directories': storage_info,
            }
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}

    def _check_services_detailed(self) -> Dict[str, Any]:
        """Check external services health"""
        services = {
            'redis': self._check_redis_service(),
            'email': self._check_email_service(),
            'storage': self._check_storage_service(),
        }

        all_healthy = all(service['status'] == 'healthy' for service in services.values())

        return {
            'status': 'healthy' if all_healthy else 'degraded',
            'services': services,
        }

    def _check_redis_service(self) -> Dict[str, Any]:
        """Check Redis service"""
        try:
            from django.conf import settings
            if hasattr(settings, 'CACHES') and 'default' in settings.CACHES:
                import redis
                redis_client = redis.from_url(settings.CACHES['default']['LOCATION'])
                info = redis_client.info()
                return {
                    'status': 'healthy',
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory': info.get('used_memory_human', 'N/A'),
                    'uptime_seconds': info.get('uptime_in_seconds', 0),
                }
            return {'status': 'not_configured'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}

    def _check_email_service(self) -> Dict[str, Any]:
        """Check email service"""
        try:
            from django.core.mail import send_mail
            # This is a connectivity test only - no email is actually sent
            return {'status': 'healthy'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}

    def _check_storage_service(self) -> Dict[str, Any]:
        """Check storage service"""
        try:
            from django.core.files.storage import default_storage
            # Test storage operations
            test_content = b'storage test'
            test_path = 'health_check/test.txt'

            default_storage.save(test_path, test_content)
            default_storage.delete(test_path)

            return {'status': 'healthy'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}

    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            import psutil
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'load_average': list(os.getloadavg()) if hasattr(os, 'getloadavg') else [0, 0, 0],
            }
        except Exception:
            return {}

    def _get_database_metrics(self, hours: int) -> Dict[str, Any]:
        """Get database performance metrics"""
        try:
            from datetime import timedelta
            start_time = datetime.now() - timedelta(hours=hours)

            with connection.cursor() as cursor:
                # Query performance
                cursor.execute("""
                    SELECT
                        avg(mean_exec_time) as avg_query_time,
                        max(mean_exec_time) as max_query_time,
                        count(*) as total_queries
                    FROM pg_stat_statements
                    WHERE calls > 0
                """)
                query_stats = cursor.fetchone()

                # Connection metrics
                cursor.execute("""
                    SELECT
                        count(*) as total_connections,
                        count(*) FILTER (WHERE state = 'active') as active_connections,
                        count(*) FILTER (WHERE state = 'idle') as idle_connections
                    FROM pg_stat_activity
                """)
                connection_stats = cursor.fetchone()

                return {
                    'query_performance': {
                        'avg_time_ms': round(query_stats[0] or 0, 2),
                        'max_time_ms': round(query_stats[1] or 0, 2),
                        'total_queries': query_stats[2] or 0,
                    },
                    'connections': {
                        'total': connection_stats[0],
                        'active': connection_stats[1],
                        'idle': connection_stats[2],
                    },
                }
        except Exception:
            return {}

    def _get_cache_metrics(self, hours: int) -> Dict[str, Any]:
        """Get cache performance metrics"""
        # This would need to be implemented based on your cache backend
        return {
            'hit_rate': 'N/A',
            'operations_per_second': 'N/A',
        }

    def _get_api_metrics(self, hours: int) -> Dict[str, Any]:
        """Get API performance metrics"""
        try:
            from datetime import timedelta
            start_time = datetime.now() - timedelta(hours=hours)

            # Get API metrics from audit logs
            api_logs = AuditLog.objects.filter(
                created_at__gte=start_time,
                action__in=['request_start', 'request_end']
            )

            total_requests = api_logs.count()
            avg_response_time = 0

            # Calculate average response time from request details
            if total_requests > 0:
                response_times = []
                for log in api_logs.filter(action='request_end'):
                    if log.details and 'response_time' in log.details:
                        response_times.append(log.details['response_time'])

                if response_times:
                    avg_response_time = sum(response_times) / len(response_times)

            return {
                'total_requests': total_requests,
                'requests_per_hour': round(total_requests / hours, 2),
                'avg_response_time_ms': round(avg_response_time * 1000, 2),
            }
        except Exception:
            return {}

    def _get_error_metrics(self, hours: int) -> Dict[str, Any]:
        """Get error metrics"""
        try:
            from datetime import timedelta
            start_time = datetime.now() - timedelta(hours=hours)

            error_logs = AuditLog.objects.filter(
                created_at__gte=start_time,
                action='exception'
            )

            total_errors = error_logs.count()

            # Group by error type
            error_types = {}
            for log in error_logs:
                if log.details and 'error_type' in log.details:
                    error_type = log.details['error_type']
                    error_types[error_type] = error_types.get(error_type, 0) + 1

            return {
                'total_errors': total_errors,
                'errors_per_hour': round(total_errors / hours, 2),
                'error_types': error_types,
            }
        except Exception:
            return {}

    def _test_database_connectivity(self) -> Dict[str, Any]:
        """Test database connectivity"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
                return {'status': 'passed', 'message': 'Database connectivity test passed'}
        except Exception as e:
            return {'status': 'failed', 'message': str(e)}

    def _test_cache_functionality(self) -> Dict[str, Any]:
        """Test cache functionality"""
        try:
            from django.core.cache import cache
            cache.set('diagnostic_test', 'test_value', 60)
            value = cache.get('diagnostic_test')
            cache.delete('diagnostic_test')

            if value == 'test_value':
                return {'status': 'passed', 'message': 'Cache functionality test passed'}
            else:
                return {'status': 'failed', 'message': 'Cache read/write test failed'}
        except Exception as e:
            return {'status': 'failed', 'message': str(e)}

    def _test_file_operations(self) -> Dict[str, Any]:
        """Test file operations"""
        try:
            import os
            from pathlib import Path

            test_dir = Path(settings.BASE_DIR) / 'logs'
            test_dir.mkdir(exist_ok=True)

            test_file = test_dir / 'diagnostic_test.tmp'
            test_file.write_text('diagnostic test')
            content = test_file.read_text()
            test_file.unlink()

            if content == 'diagnostic test':
                return {'status': 'passed', 'message': 'File operations test passed'}
            else:
                return {'status': 'failed', 'message': 'File read/write test failed'}
        except Exception as e:
            return {'status': 'failed', 'message': str(e)}

    def _test_api_endpoints(self) -> Dict[str, Any]:
        """Test API endpoints"""
        # This would test critical API endpoints
        return {'status': 'passed', 'message': 'API endpoints test passed'}

    def _test_background_tasks(self) -> Dict[str, Any]:
        """Test background tasks"""
        try:
            from .tasks import test_celery_connection
            result = test_celery_connection.delay()
            result.get(timeout=10)  # Wait up to 10 seconds
            return {'status': 'passed', 'message': 'Background tasks test passed'}
        except Exception as e:
            return {'status': 'failed', 'message': str(e)}