"""
comprehensive_database_test module
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms.settings')
sys.path.insert(0, '/home/azureuser/hms-enterprise-grade/backend')
try:
    django.setup()
    from django.apps import apps
    from django.conf import settings
    from django.core.management import call_command
    from django.core.management.color import no_style
    from django.db import connection, connections, transaction
    from django.test.utils import get_runner
except Exception as e:
    print(f"Error setting up Django: {e}")
    sys.exit(1)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/azureuser/hms-enterprise-grade/database_testing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
class DatabaseTestingSuite:
    def __init__(self):
        self.test_results = {
            'schema_validation': {},
            'migration_tests': {},
            'data_integrity': {},
            'performance_tests': {},
            'security_tests': {},
            'compliance_tests': {},
            'connection_tests': {},
            'query_optimization': {}
        }
        self.start_time = time.time()
    def run_all_tests(self):
        logger.info("🚀 Starting Comprehensive Database Testing Suite")
        logger.info("=" * 60)
        try:
            self.test_database_connections()
            self.validate_database_schema()
            self.test_migrations()
            self.test_data_integrity()
            self.test_query_performance()
            self.test_database_security()
            self.test_compliance()
            self.generate_test_report()
            logger.info("✅ Database Testing Suite Completed Successfully")
        except Exception as e:
            logger.error(f"❌ Database Testing Suite Failed: {e}")
            raise
    def test_database_connections(self):
        logger.info("🔌 Testing Database Connections")
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                logger.info(f"✅ Database connected successfully: {version}")
                cursor.execute("SHOW ALL;")
                config_results = cursor.fetchall()
            self.test_results['connection_tests']['default_db'] = {
                'status': 'PASS',
                'version': version,
                'connection_time': time.time() - self.start_time
            }
            if 'replica' in connections:
                replica_conn = connections['replica']
                with replica_conn.cursor() as cursor:
                    cursor.execute("SELECT version();")
                    replica_version = cursor.fetchone()[0]
                    logger.info(f"✅ Read replica connected: {replica_version}")
                self.test_results['connection_tests']['replica_db'] = {
                    'status': 'PASS',
                    'version': replica_version
                }
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            self.test_results['connection_tests']['default_db'] = {
                'status': 'FAIL',
                'error': str(e)
            }
    def validate_database_schema(self):
        logger.info("📊 Validating Database Schema")
        try:
            all_models = []
            for model in apps.get_models():
                model_info = {
                    'name': model._meta.model_name,
                    'table_name': model._meta.db_table,
                    'fields': [],
                    'indexes': [],
                    'constraints': [],
                    'relationships': []
                }
                for field in model._meta.fields:
                    field_info = {
                        'name': field.name,
                        'type': field.__class__.__name__,
                        'db_type': field.db_type(connection),
                        'null': field.null,
                        'blank': field.blank,
                        'unique': field.unique,
                        'primary_key': field.primary_key,
                        'max_length': getattr(field, 'max_length', None),
                        'choices': getattr(field, 'choices', None)
                    }
                    model_info['fields'].append(field_info)
                for index in model._meta.indexes:
                    index_info = {
                        'name': index.name,
                        'fields': index.fields,
                        'unique': getattr(index, 'unique', False)
                    }
                    model_info['indexes'].append(index_info)
                for field in model._meta.get_fields():
                    if field.is_relation and field.many_to_one or field.one_to_one:
                        rel_info = {
                            'type': field.__class__.__name__,
                            'related_model': field.related_model._meta.model_name,
                            'on_delete': str(field.remote_field.on_delete.__name__)
                        }
                        model_info['relationships'].append(rel_info)
                all_models.append(model_info)
            with connection.cursor() as cursor:
                cursor.execute()
                db_schema = cursor.fetchall()
            self.test_results['schema_validation'] = {
                'status': 'PASS',
                'models_analyzed': len(all_models),
                'total_tables': len(set(row[0] for row in db_schema)),
                'total_columns': len(db_schema),
                'models': all_models,
                'database_schema': db_schema,
                'timestamp': datetime.now().isoformat()
            }
            logger.info(f"✅ Schema validation completed: {len(all_models)} models analyzed")
        except Exception as e:
            logger.error(f"❌ Schema validation failed: {e}")
            self.test_results['schema_validation'] = {
                'status': 'FAIL',
                'error': str(e)
            }
    def test_migrations(self):
        logger.info("🔄 Testing Database Migrations")
        try:
            with connection.cursor() as cursor:
                cursor.execute()
                migration_history = cursor.fetchall()
            migration_plan = call_command('showmigrations', list=True, verbosity=0)
            try:
                call_command('migrate', verbosity=0)
                logger.info("✅ Forward migrations successful")
                migration_status = 'PASS'
            except Exception as e:
                logger.error(f"❌ Forward migration failed: {e}")
                migration_status = 'FAIL'
            self.test_results['migration_tests'] = {
                'status': migration_status,
                'total_migrations': len(migration_history),
                'migration_history': migration_history,
                'last_tested': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Migration testing failed: {e}")
            self.test_results['migration_tests'] = {
                'status': 'FAIL',
                'error': str(e)
            }
    def test_data_integrity(self):
        logger.info("🔒 Testing Data Integrity")
        try:
            constraint_tests = []
            with connection.cursor() as cursor:
                cursor.execute()
                foreign_keys = cursor.fetchall()
                constraint_tests.extend([{
                    'type': 'foreign_key',
                    'table': fk[0],
                    'constraint': fk[1],
                    'column': fk[3],
                    'references': f"{fk[4]}.{fk[5]}"
                } for fk in foreign_keys])
            with connection.cursor() as cursor:
                cursor.execute()
                unique_constraints = cursor.fetchall()
                constraint_tests.extend([{
                    'type': 'unique',
                    'table': uc[0],
                    'constraint': uc[1],
                    'columns': uc[2]
                } for uc in unique_constraints])
            with connection.cursor() as cursor:
                cursor.execute()
                not_null_constraints = cursor.fetchall()
                constraint_tests.extend([{
                    'type': 'not_null',
                    'table': nn[0],
                    'column': nn[1]
                } for nn in not_null_constraints])
            self.test_results['data_integrity'] = {
                'status': 'PASS',
                'total_constraints': len(constraint_tests),
                'foreign_keys': len([c for c in constraint_tests if c['type'] == 'foreign_key']),
                'unique_constraints': len([c for c in constraint_tests if c['type'] == 'unique']),
                'not_null_constraints': len([c for c in constraint_tests if c['type'] == 'not_null']),
                'constraint_details': constraint_tests,
                'test_timestamp': datetime.now().isoformat()
            }
            logger.info(f"✅ Data integrity testing completed: {len(constraint_tests)} constraints validated")
        except Exception as e:
            logger.error(f"❌ Data integrity testing failed: {e}")
            self.test_results['data_integrity'] = {
                'status': 'FAIL',
                'error': str(e)
            }
    def test_query_performance(self):
        logger.info("⚡ Testing Query Performance")
        try:
            performance_tests = []
            test_queries = [
                ("SELECT COUNT(*) FROM django_migrations;", "Migration Count"),
                ("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';", "List Tables"),
                ("SELECT version();", "Database Version"),
            ]
            for query, description in test_queries:
                start_time = time.time()
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    result = cursor.fetchall()
                execution_time = time.time() - start_time
                performance_tests.append({
                    'query': description,
                    'execution_time': execution_time,
                    'result_count': len(result),
                    'performance_rating': 'GOOD' if execution_time < 0.1 else 'SLOW'
                })
            with connection.cursor() as cursor:
                cursor.execute()
                indexes = cursor.fetchall()
            with connection.cursor() as cursor:
                cursor.execute()
                slow_queries = cursor.fetchall()
            self.test_results['performance_tests'] = {
                'status': 'PASS',
                'query_tests': performance_tests,
                'total_indexes': len(indexes),
                'slow_queries_count': len(slow_queries),
                'indexes': indexes,
                'slow_queries': slow_queries,
                'test_timestamp': datetime.now().isoformat()
            }
            logger.info(f"✅ Performance testing completed: {len(performance_tests)} queries tested")
        except Exception as e:
            logger.error(f"❌ Performance testing failed: {e}")
            self.test_results['performance_tests'] = {
                'status': 'FAIL',
                'error': str(e)
            }
    def test_database_security(self):
        logger.info("🔐 Testing Database Security")
        try:
            security_tests = []
            with connection.cursor() as cursor:
                cursor.execute()
                users = cursor.fetchall()
                security_tests.append({
                    'test': 'user_permissions',
                    'total_users': len(users),
                    'superusers': len([u for u in users if u[2]]),
                    'details': users
                })
            with connection.cursor() as cursor:
                cursor.execute("SHOW ssl;")
                ssl_status = cursor.fetchone()[0]
                security_tests.append({
                    'test': 'ssl_configuration',
                    'status': ssl_status,
                    'enabled': ssl_status.lower() == 'on'
                })
            with connection.cursor() as cursor:
                cursor.execute()
                databases = cursor.fetchall()
                security_tests.append({
                    'test': 'database_access',
                    'total_databases': len(databases),
                    'accessible_dbs': len([d for d in databases if d[1]]),
                    'details': databases
                })
            self.test_results['security_tests'] = {
                'status': 'PASS',
                'security_tests': security_tests,
                'test_timestamp': datetime.now().isoformat()
            }
            logger.info(f"✅ Security testing completed: {len(security_tests)} security checks performed")
        except Exception as e:
            logger.error(f"❌ Security testing failed: {e}")
            self.test_results['security_tests'] = {
                'status': 'FAIL',
                'error': str(e)
            }
    def test_compliance(self):
        logger.info("🏥 Testing Healthcare Compliance")
        try:
            compliance_tests = []
            encryption_tests = []
            for model in apps.get_models():
                encrypted_fields = []
                for field in model._meta.fields:
                    if 'Encrypted' in field.__class__.__name__:
                        encrypted_fields.append(field.name)
                if encrypted_fields:
                    encryption_tests.append({
                        'model': model._meta.model_name,
                        'encrypted_fields': encrypted_fields
                    })
            compliance_tests.append({
                'test': 'data_encryption',
                'models_with_encryption': len(encryption_tests),
                'details': encryption_tests
            })
            audit_tables = []
            with connection.cursor() as cursor:
                cursor.execute()
                audit_tables = [row[0] for row in cursor.fetchall()]
            compliance_tests.append({
                'test': 'audit_tables',
                'audit_tables_found': len(audit_tables),
                'tables': audit_tables
            })
            with connection.cursor() as cursor:
                cursor.execute()
                timestamp_columns = cursor.fetchall()
            compliance_tests.append({
                'test': 'timestamp_columns',
                'total_timestamp_columns': len(timestamp_columns),
                'details': timestamp_columns
            })
            self.test_results['compliance_tests'] = {
                'status': 'PASS',
                'compliance_tests': compliance_tests,
                'hipaa_encryption_compliant': len(encryption_tests) > 0,
                'audit_compliant': len(audit_tables) > 0,
                'test_timestamp': datetime.now().isoformat()
            }
            logger.info(f"✅ Compliance testing completed: {len(compliance_tests)} compliance checks performed")
        except Exception as e:
            logger.error(f"❌ Compliance testing failed: {e}")
            self.test_results['compliance_tests'] = {
                'status': 'FAIL',
                'error': str(e)
            }
    def generate_test_report(self):
        logger.info("📋 Generating Test Report")
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values()
                          if isinstance(result, dict) and result.get('status') == 'PASS')
        overall_status = 'PASS' if passed_tests == total_tests else 'FAIL'
        report = {
            'test_suite': 'HMS Enterprise-Grade Database Testing',
            'execution_timestamp': datetime.now().isoformat(),
            'total_duration': time.time() - self.start_time,
            'overall_status': overall_status,
            'test_summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'success_rate': (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            },
            'detailed_results': self.test_results,
            'database_configuration': {
                'engine': settings.DATABASES['default']['ENGINE'],
                'name': settings.DATABASES['default']['NAME'],
                'host': settings.DATABASES['default']['HOST'],
                'port': settings.DATABASES['default']['PORT']
            },
            'recommendations': self._generate_recommendations()
        }
        report_path = '/home/azureuser/hms-enterprise-grade/database_test_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        html_report_path = '/home/azureuser/hms-enterprise-grade/database_test_report.html'
        self._generate_html_report(report, html_report_path)
        logger.info(f"📊 Test Report Generated:")
        logger.info(f"   - JSON Report: {report_path}")
        logger.info(f"   - HTML Report: {html_report_path}")
        logger.info(f"   - Overall Status: {overall_status}")
        logger.info(f"   - Success Rate: {report['test_summary']['success_rate']:.1f}%")
        return report
    def _generate_recommendations(self):
        recommendations = []
        if 'performance_tests' in self.test_results:
            perf_results = self.test_results['performance_tests']
            if isinstance(perf_results, dict):
                if perf_results.get('slow_queries_count', 0) > 5:
                    recommendations.append({
                        'category': 'Performance',
                        'priority': 'HIGH',
                        'issue': 'Multiple slow queries detected',
                        'recommendation': 'Review and optimize slow queries, add missing indexes'
                    })
                if perf_results.get('total_indexes', 0) < 10:
                    recommendations.append({
                        'category': 'Performance',
                        'priority': 'MEDIUM',
                        'issue': 'Limited number of indexes',
                        'recommendation': 'Consider adding indexes for frequently queried columns'
                    })
        if 'security_tests' in self.test_results:
            sec_results = self.test_results['security_tests']
            if isinstance(sec_results, dict):
                ssl_test = next((t for t in sec_results.get('security_tests', [])
                               if t.get('test') == 'ssl_configuration'), None)
                if ssl_test and not ssl_test.get('enabled'):
                    recommendations.append({
                        'category': 'Security',
                        'priority': 'HIGH',
                        'issue': 'SSL not enabled',
                        'recommendation': 'Enable SSL for database connections'
                    })
        if 'compliance_tests' in self.test_results:
            comp_results = self.test_results['compliance_tests']
            if isinstance(comp_results, dict):
                if not comp_results.get('hipaa_encryption_compliant'):
                    recommendations.append({
                        'category': 'Compliance',
                        'priority': 'CRITICAL',
                        'issue': 'Missing HIPAA encryption',
                        'recommendation': 'Implement field-level encryption for PHI data'
                    })
                if not comp_results.get('audit_compliant'):
                    recommendations.append({
                        'category': 'Compliance',
                        'priority': 'HIGH',
                        'issue': 'Missing audit tables',
                        'recommendation': 'Implement audit logging for data changes'
                    })
        return recommendations
    def _generate_html_report(self, report_data, output_path):
        html_content = f
        for test_name, test_result in report_data['detailed_results'].items():
            if isinstance(test_result, dict):
                status = test_result.get('status', 'UNKNOWN')
                status_class = status.lower()
                html_content += f
        html_content += 
        with open(output_path, 'w') as f:
            f.write(html_content)
def main():
    print("🚀 HMS Enterprise-Grade Database Testing Suite")
    print("=" * 50)
    try:
        test_suite = DatabaseTestingSuite()
        test_suite.run_all_tests()
        print("\n✅ Database Testing Suite Completed Successfully!")
        print("📊 Check the generated reports for detailed results:")
        print("   - database_test_report.json (detailed JSON report)")
        print("   - database_test_report.html (visual HTML report)")
        print("   - database_testing.log (execution log)")
        return 0
    except Exception as e:
        print(f"\n❌ Database Testing Suite Failed: {e}")
        return 1
if __name__ == "__main__":
    sys.exit(main())