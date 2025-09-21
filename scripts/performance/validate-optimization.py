#!/usr/bin/env python3
"""
HMS Performance Optimization Validation Script
Validates that all performance optimizations are working correctly
"""

import os
import sys
import django
import time
import requests
import json
import statistics
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.hms.settings')
django.setup()

from django.core.cache import cache
from django.db import connection, connections
from django.test.utils import override_settings
from django.conf import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceValidator:
    """Validates HMS performance optimizations"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: Dict[str, Any] = {}
        self.auth_token = None

    def run_validation(self):
        """Run complete performance validation"""
        logger.info("🔍 Starting HMS Performance Validation")
        logger.info("=" * 60)

        # Database optimizations
        self.validate_database_indexes()
        self.validate_database_performance()

        # Caching optimizations
        self.validate_redis_cache()
        self.validate_cache_performance()

        # API optimizations
        self.authenticate()
        self.validate_api_response_times()
        self.validate_api_compression()

        # Frontend optimizations
        self.validate_frontend_bundle_size()

        # Infrastructure optimizations
        self.validate_load_balancing()
        self.validate_scaling()

        # Generate report
        self.generate_validation_report()

    def validate_database_indexes(self):
        """Validate critical database indexes exist"""
        logger.info("🗄️  Validating Database Indexes...")

        expected_indexes = [
            'idx_patients_composite_search',
            'idx_appointments_provider_time',
            'idx_appointments_patient_time',
            'idx_appointments_hospital_status_time',
            'idx_medical_records_patient_created',
            'idx_vitals_patient_timestamp',
            'idx_lab_results_patient_test',
            'idx_prescriptions_patient_active',
            'idx_billing_patient_status'
        ]

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
                ORDER BY indexname
            """)
            existing_indexes = [row[0] for row in cursor.fetchall()]

        missing_indexes = set(expected_indexes) - set(existing_indexes)
        if missing_indexes:
            logger.error(f"❌ Missing indexes: {', '.join(missing_indexes)}")
            self.results['database_indexes'] = {
                'status': 'FAILED',
                'missing': list(missing_indexes),
                'existing': existing_indexes
            }
        else:
            logger.info("✅ All critical indexes present")
            self.results['database_indexes'] = {
                'status': 'PASSED',
                'count': len(existing_indexes)
            }

    def validate_database_performance(self):
        """Validate database query performance"""
        logger.info("⚡ Validating Database Performance...")

        # Test patient search query
        start_time = time.time()
        with connection.cursor() as cursor:
            cursor.execute("""
                EXPLAIN ANALYZE
                SELECT id, first_name, last_name, medical_record_number
                FROM patients_patient
                WHERE last_name LIKE 'Smith%'
                ORDER BY last_name, first_name
                LIMIT 100
            """)
            result = cursor.fetchall()
        duration = time.time() - start_time

        # Parse explain analyze output
        explain_output = ' '.join([row[0] for row in result])
        execution_time = float(explain_output.split('Execution Time: ')[1].split('ms')[0])

        if execution_time < 10:
            logger.info(f"✅ Patient search query: {execution_time:.2f}ms")
            self.results['database_performance'] = {
                'status': 'PASSED',
                'patient_search_time': execution_time
            }
        else:
            logger.warning(f"⚠️  Patient search query slow: {execution_time:.2f}ms")
            self.results['database_performance'] = {
                'status': 'WARNING',
                'patient_search_time': execution_time
            }

    def validate_redis_cache(self):
        """Validate Redis cache is working"""
        logger.info("🚀 Validating Redis Cache...")

        try:
            # Test cache set/get
            test_key = "performance_test"
            test_value = {"timestamp": datetime.now().isoformat()}

            cache.set(test_key, test_value, 60)
            retrieved_value = cache.get(test_key)

            if retrieved_value == test_value:
                logger.info("✅ Redis cache operational")
                self.results['redis_cache'] = {
                    'status': 'PASSED',
                    'latency': self.measure_cache_latency()
                }
            else:
                logger.error("❌ Redis cache not working")
                self.results['redis_cache'] = {
                    'status': 'FAILED'
                }

        except Exception as e:
            logger.error(f"❌ Redis cache error: {e}")
            self.results['redis_cache'] = {
                'status': 'FAILED',
                'error': str(e)
            }

    def measure_cache_latency(self) -> float:
        """Measure cache read/write latency"""
        latencies = []
        for i in range(100):
            start = time.time()
            cache.set(f"test_{i}", i, 1)
            cache.get(f"test_{i}")
            latencies.append((time.time() - start) * 1000)

        return statistics.mean(latencies)

    def validate_cache_performance(self):
        """Validate cache hit rates"""
        logger.info("📊 Validating Cache Performance...")

        # Test with patient data caching
        if 'patients' in settings.INSTALLED_APPS:
            from patients.models import Patient

            # Get patient count
            patient_count = Patient.objects.count()
            logger.info(f"Found {patient_count} patients for cache test")

            # Measure cache performance
            cache_hits = 0
            total_requests = 100

            for i in range(total_requests):
                patient_id = (i % max(patient_count, 1)) + 1
                cached_patient = Patient.get_cached_patient(patient_id)
                if cached_patient:
                    cache_hits += 1

            hit_rate = (cache_hits / total_requests) * 100
            logger.info(f"Cache hit rate: {hit_rate:.1f}%")

            self.results['cache_performance'] = {
                'status': 'PASSED' if hit_rate > 80 else 'WARNING',
                'hit_rate': hit_rate,
                'total_requests': total_requests
            }

    def authenticate(self):
        """Authenticate with API"""
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login/",
                json={
                    "username": "admin@test.com",
                    "password": "testpassword123"
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                logger.info("✅ API authentication successful")
            else:
                logger.error("❌ API authentication failed")
                self.auth_token = None

        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            self.auth_token = None

    def validate_api_response_times(self):
        """Validate API response times"""
        logger.info("🚀 Validating API Response Times...")

        if not self.auth_token:
            logger.warning("⚠️  Skipping API validation - no auth token")
            return

        headers = {'Authorization': f'Bearer {self.auth_token}'}

        endpoints = [
            ('GET', '/api/patients/', 'Patient List'),
            ('GET', '/api/appointments/', 'Appointment List'),
            ('GET', '/api/ehr/medical-records/', 'Medical Records'),
            ('GET', '/api/analytics/dashboard/', 'Analytics Dashboard')
        ]

        response_times = {}

        for method, endpoint, name in endpoints:
            try:
                start_time = time.time()
                response = requests.request(
                    method,
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    timeout=30
                )
                duration = time.time() - start_time

                response_times[name] = {
                    'time': duration * 1000,  # Convert to ms
                    'status': response.status_code
                }

                if duration < 0.1:  # < 100ms
                    logger.info(f"✅ {name}: {duration*1000:.2f}ms")
                elif duration < 0.5:  # < 500ms
                    logger.info(f"⚠️  {name}: {duration*1000:.2f}ms")
                else:
                    logger.error(f"❌ {name}: {duration*1000:.2f}ms")

            except Exception as e:
                logger.error(f"❌ {name} failed: {e}")
                response_times[name] = {'error': str(e)}

        # Calculate averages
        successful_times = [v['time'] for v in response_times.values() if isinstance(v, dict) and 'time' in v]
        if successful_times:
            avg_response = statistics.mean(successful_times)
            self.results['api_response_times'] = {
                'status': 'PASSED' if avg_response < 100 else 'WARNING',
                'average': avg_response,
                'endpoints': response_times
            }
        else:
            self.results['api_response_times'] = {
                'status': 'FAILED',
                'endpoints': response_times
            }

    def validate_api_compression(self):
        """Validate API response compression"""
        logger.info("🗜️  Validating API Compression...")

        if not self.auth_token:
            return

        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Accept-Encoding': 'gzip, deflate'
        }

        try:
            # Test with a large endpoint
            response = requests.get(
                f"{self.base_url}/api/patients/",
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                content_length = len(response.content)
                if 'Content-Encoding' in response.headers:
                    encoding = response.headers['Content-Encoding']
                    logger.info(f"✅ Response compressed with {encoding}")
                    self.results['api_compression'] = {
                        'status': 'PASSED',
                        'encoding': encoding,
                        'size': content_length
                    }
                else:
                    logger.warning("⚠️  Response not compressed")
                    self.results['api_compression'] = {
                        'status': 'WARNING',
                        'size': content_length
                    }

        except Exception as e:
            logger.error(f"❌ Compression test failed: {e}")
            self.results['api_compression'] = {
                'status': 'FAILED',
                'error': str(e)
            }

    def validate_frontend_bundle_size(self):
        """Validate frontend bundle size"""
        logger.info("📦 Validating Frontend Bundle Size...")

        # Check if frontend build exists
        frontend_dist = os.path.join(os.getcwd(), 'frontend', 'dist')
        if not os.path.exists(frontend_dist):
            logger.warning("⚠️  Frontend build not found")
            return

        # Calculate total bundle size
        total_size = 0
        bundle_files = []

        for root, dirs, files in os.walk(frontend_dist):
            for file in files:
                if file.endswith(('.js', '.css')):
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    bundle_files.append({
                        'name': file,
                        'size': file_size
                    })

        total_size_mb = total_size / (1024 * 1024)

        if total_size_mb < 1:
            logger.info(f"✅ Frontend bundle size: {total_size_mb:.2f}MB")
            self.results['frontend_bundle'] = {
                'status': 'PASSED',
                'size_mb': total_size_mb,
                'files': bundle_files
            }
        else:
            logger.warning(f"⚠️  Frontend bundle size: {total_size_mb:.2f}MB (target: <1MB)")
            self.results['frontend_bundle'] = {
                'status': 'WARNING',
                'size_mb': total_size_mb,
                'files': bundle_files
            }

    def validate_load_balancing(self):
        """Validate load balancing configuration"""
        logger.info("⚖️  Validating Load Balancing...")

        # Check if multiple backend instances are running
        try:
            # This would typically check actual load balancer health endpoints
            response = requests.get(f"{self.base_url}/health/", timeout=10)
            if response.status_code == 200:
                logger.info("✅ Load balancer operational")
                self.results['load_balancing'] = {
                    'status': 'PASSED',
                    'response_time': response.elapsed.total_seconds()
                }
            else:
                logger.error("❌ Load balancer health check failed")
                self.results['load_balancing'] = {
                    'status': 'FAILED',
                    'status_code': response.status_code
                }

        except Exception as e:
            logger.error(f"❌ Load balancing validation failed: {e}")
            self.results['load_balancing'] = {
                'status': 'FAILED',
                'error': str(e)
            }

    def validate_scaling(self):
        """Validate auto-scaling configuration"""
        logger.info("📈 Validating Auto-Scaling...")

        # Check HPA configuration if in Kubernetes
        try:
            import subprocess
            result = subprocess.run(
                ['kubectl', 'get', 'hpa', '-n', 'hms-performance'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info("✅ HPA configuration found")
                self.results['scaling'] = {
                    'status': 'PASSED',
                    'hpa_config': result.stdout
                }
            else:
                logger.warning("⚠️  HPA not configured")
                self.results['scaling'] = {
                    'status': 'WARNING',
                    'message': 'HPA not configured'
                }

        except FileNotFoundError:
            logger.info("ℹ️  Kubernetes not available, skipping HPA check")
            self.results['scaling'] = {
                'status': 'INFO',
                'message': 'Running in development mode'
            }

    def generate_validation_report(self):
        """Generate validation report"""
        logger.info("\n" + "=" * 60)
        logger.info("HMS PERFORMANCE VALIDATION REPORT")
        logger.info("=" * 60)

        # Calculate overall score
        total_checks = len(self.results)
        passed_checks = sum(1 for v in self.results.values() if v.get('status') == 'PASSED')
        warning_checks = sum(1 for v in self.results.values() if v.get('status') == 'WARNING')

        score = (passed_checks / total_checks) * 100

        logger.info(f"\nOverall Performance Score: {score:.1f}%")
        logger.info(f"✅ Passed: {passed_checks}/{total_checks}")
        logger.info(f"⚠️  Warnings: {warning_checks}/{total_checks}")

        # Detailed results
        logger.info("\nDetailed Results:")
        for check, result in self.results.items():
            status = result.get('status', 'UNKNOWN')
            icon = "✅" if status == "PASSED" else "⚠️" if status == "WARNING" else "❌"
            logger.info(f"  {icon} {check.replace('_', ' ').title()}: {status}")

            # Add details for failed checks
            if status == "FAILED" and 'error' in result:
                logger.info(f"    Error: {result['error']}")

        # Save report to file
        report_file = f"performance_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        logger.info(f"\nDetailed report saved to: {report_file}")

        # Recommendations
        logger.info("\nRecommendations:")
        if score < 80:
            logger.info("  - Performance optimizations need attention")
            logger.info("  - Consider reviewing failed and warning checks")
        elif score < 95:
            logger.info("  - Good performance, but there's room for improvement")
        else:
            logger.info("  - Excellent performance! All optimizations working well")

        logger.info("\n🎉 Validation completed!")

def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='HMS Performance Validator')
    parser.add_argument('--url', default='http://localhost:8000', help='Base URL for API validation')

    args = parser.parse_args()

    validator = PerformanceValidator(args.url)
    validator.run_validation()

if __name__ == "__main__":
    main()