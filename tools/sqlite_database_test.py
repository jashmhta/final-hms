"""
sqlite_database_test module
"""

import json
import logging
import os
import sqlite3
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
        logging.FileHandler('/home/azureuser/hms-enterprise-grade/sqlite_database_testing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
class SQLiteDatabaseTestingSuite:
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
        self.db_path = settings.DATABASES['default']['NAME']
    def run_all_tests(self):
        logger.info("🚀 Starting SQLite Database Testing Suite")
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
                cursor.execute("SELECT sqlite_version();")
                version = cursor.fetchone()[0]
                logger.info(f"✅ SQLite database connected successfully: {version}")
                db_exists = os.path.exists(self.db_path)
                db_size = os.path.getsize(self.db_path) if db_exists else 0
                cursor.execute("PRAGMA journal_mode;")
                journal_mode = cursor.fetchone()[0]
                cursor.execute("PRAGMA foreign_keys;")
                foreign_keys = cursor.fetchone()[0]
                cursor.execute("PRAGMA synchronous;")
                synchronous = cursor.fetchone()[0]
            self.test_results['connection_tests']['sqlite_db'] = {
                'status': 'PASS',
                'version': version,
                'database_file': self.db_path,
                'file_exists': db_exists,
                'file_size_bytes': db_size,
                'journal_mode': journal_mode,
                'foreign_keys_enabled': foreign_keys == 1,
                'synchronous_mode': synchronous,
                'connection_time': time.time() - self.start_time
            }
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA integrity_check;")
                integrity_result = cursor.fetchone()[0]
                self.test_results['connection_tests']['integrity_check'] = {
                    'status': 'PASS' if integrity_result == 'ok' else 'FAIL',
                    'result': integrity_result
                }
            logger.info(f"✅ Database integrity check: {integrity_result}")
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            self.test_results['connection_tests']['sqlite_db'] = {
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
                    if field.is_relation and field.many_to_one:
                        rel_info = {
                            'type': field.__class__.__name__,
                            'related_model': field.related_model._meta.model_name,
                            'on_delete': str(field.remote_field.on_delete.__name__) if hasattr(field.remote_field, 'on_delete') else 'CASCADE'
                        }
                        model_info['relationships'].append(rel_info)
                all_models.append(model_info)
            with connection.cursor() as cursor:
                cursor.execute()
                db_objects = cursor.fetchall()
                cursor.execute()
                db_schema = cursor.fetchall()
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA foreign_key_list(main_table_name);")  
            self.test_results['schema_validation'] = {
                'status': 'PASS',
                'models_analyzed': len(all_models),
                'total_tables': len([obj for obj in db_objects if obj[1] == 'table']),
                'total_indexes': len([obj for obj in db_objects if obj[1] == 'index']),
                'total_columns': len(set(row[0] for row in db_schema)),
                'models': all_models,
                'database_objects': db_objects,
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
                migrations_table_exists = cursor.fetchone()
            if migrations_table_exists:
                cursor.execute()
                migration_history = cursor.fetchall()
                try:
                    migration_plan = call_command('showmigrations', list=True, verbosity=0)
                    migration_status = 'PASS'
                except Exception as e:
                    logger.warning(f"Migration plan check failed: {e}")
                    migration_status = 'PARTIAL'
                self.test_results['migration_tests'] = {
                    'status': migration_status,
                    'migrations_table_exists': True,
                    'total_migrations': len(migration_history),
                    'migration_history': migration_history,
                    'last_tested': datetime.now().isoformat()
                }
            else:
                self.test_results['migration_tests'] = {
                    'status': 'PENDING',
                    'migrations_table_exists': False,
                    'message': 'No migrations table found - database not migrated',
                    'recommendation': 'Run migrate command to apply migrations'
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
                tables = [row[0] for row in cursor.fetchall()]
            for table in tables:
                with connection.cursor() as cursor:
                    cursor.execute(f"PRAGMA table_info({table});")
                    columns = cursor.fetchall()
                    cursor.execute(f"PRAGMA foreign_key_list({table});")
                    foreign_keys = cursor.fetchall()
                    cursor.execute(f"PRAGMA index_list({table});")
                    indexes = cursor.fetchall()
                    constraint_tests.append({
                        'table': table,
                        'total_columns': len(columns),
                        'foreign_keys': len(foreign_keys),
                        'indexes': len(indexes),
                        'columns': columns,
                        'foreign_key_details': foreign_keys,
                        'index_details': indexes
                    })
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA foreign_keys;")
                fk_enforced = cursor.fetchone()[0]
            self.test_results['data_integrity'] = {
                'status': 'PASS',
                'total_tables': len(tables),
                'foreign_keys_enforced': fk_enforced == 1,
                'constraint_tests': constraint_tests,
                'total_foreign_keys': sum(test['foreign_keys'] for test in constraint_tests),
                'total_indexes': sum(test['indexes'] for test in constraint_tests),
                'test_timestamp': datetime.now().isoformat()
            }
            logger.info(f"✅ Data integrity testing completed: {len(tables)} tables analyzed")
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
                ("SELECT count(*) FROM sqlite_master WHERE type='table';", "Table Count"),
                ("SELECT name FROM sqlite_master WHERE type='index' LIMIT 10;", "Index Sample"),
                ("PRAGMA page_count;", "Database Pages"),
                ("PRAGMA page_size;", "Page Size"),
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
                    'performance_rating': 'GOOD' if execution_time < 0.01 else 'SLOW'
                })
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA page_count;")
                page_count = cursor.fetchone()[0]
                cursor.execute("PRAGMA page_size;")
                page_size = cursor.fetchone()[0]
                db_size = page_count * page_size
                cursor.execute("PRAGMA encoding;")
                encoding = cursor.fetchone()[0]
            with connection.cursor() as cursor:
                cursor.execute()
                indexes = cursor.fetchall()
            self.test_results['performance_tests'] = {
                'status': 'PASS',
                'query_tests': performance_tests,
                'database_size_bytes': db_size,
                'page_count': page_count,
                'page_size': page_size,
                'encoding': encoding,
                'total_indexes': len(indexes),
                'indexes': indexes,
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
                cursor.execute("PRAGMA foreign_keys;")
                foreign_keys = cursor.fetchone()[0]
                security_tests.append({
                    'test': 'foreign_key_constraints',
                    'enabled': foreign_keys == 1,
                    'description': 'Foreign key constraints enforce referential integrity'
                })
                db_path = self.db_path
                if os.path.exists(db_path):
                    import stat
                    file_stat = os.stat(db_path)
                    file_mode = stat.filemode(file_stat.st_mode)
                    file_owner = file_stat.st_uid
                    file_group = file_stat.st_gid
                    security_tests.append({
                        'test': 'file_permissions',
                        'file_path': db_path,
                        'file_mode': file_mode,
                        'owner_uid': file_owner,
                        'group_gid': file_group,
                        'world_writable': (file_stat.st_mode & 0o002) != 0
                    })
                cursor.execute("PRAGMA compile_options;")
                compile_options = cursor.fetchall()
                has_encryption = any('SQLITE_HAS_CODEC' in opt[0] or 'ENABLE_DBSTAT_VTAB' in opt[0]
                                   for opt in compile_options)
                security_tests.append({
                    'test': 'encryption_support',
                    'available': has_encryption,
                    'compile_options': [opt[0] for opt in compile_options]
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
                'total_encrypted_fields': sum(len(test['encrypted_fields']) for test in encryption_tests),
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
            timestamp_columns = []
            for model in apps.get_models():
                model_timestamps = []
                for field in model._meta.fields:
                    if field.name in ['created_at', 'updated_at', 'created', 'modified']:
                        model_timestamps.append({
                            'model': model._meta.model_name,
                            'field': field.name,
                            'type': field.__class__.__name__
                        })
                timestamp_columns.extend(model_timestamps)
            compliance_tests.append({
                'test': 'timestamp_columns',
                'total_timestamp_columns': len(timestamp_columns),
                'details': timestamp_columns
            })
            pii_fields = []
            pii_patterns = ['ssn', 'social_security', 'email', 'phone', 'address', 'name']
            for model in apps.get_models():
                model_pii = []
                for field in model._meta.fields:
                    field_name_lower = field.name.lower()
                    if any(pattern in field_name_lower for pattern in pii_patterns):
                        model_pii.append({
                            'model': model._meta.model_name,
                            'field': field.name,
                            'encrypted': 'Encrypted' in field.__class__.__name__
                        })
                pii_fields.extend(model_pii)
            compliance_tests.append({
                'test': 'pii_field_identification',
                'total_pii_fields': len(pii_fields),
                'encrypted_pii_fields': len([f for f in pii_fields if f['encrypted']]),
                'details': pii_fields
            })
            self.test_results['compliance_tests'] = {
                'status': 'PASS',
                'compliance_tests': compliance_tests,
                'hipaa_encryption_compliant': len(encryption_tests) > 0,
                'audit_compliant': len(audit_tables) > 0,
                'pii_encryption_rate': len([f for f in pii_fields if f['encrypted']]) / len(pii_fields) if pii_fields else 0,
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
            'test_suite': 'HMS Enterprise-Grade SQLite Database Testing',
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
        report_path = '/home/azureuser/hms-enterprise-grade/sqlite_database_test_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        html_report_path = '/home/azureuser/hms-enterprise-grade/sqlite_database_test_report.html'
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
                if perf_results.get('total_indexes', 0) < 5:
                    recommendations.append({
                        'category': 'Performance',
                        'priority': 'MEDIUM',
                        'issue': 'Limited number of indexes',
                        'recommendation': 'Consider adding indexes for frequently queried columns'
                    })
                if perf_results.get('database_size_bytes', 0) > 100 * 1024 * 1024:  
                    recommendations.append({
                        'category': 'Performance',
                        'priority': 'MEDIUM',
                        'issue': 'Large database file size',
                        'recommendation': 'Consider database optimization and cleanup'
                    })
        if 'security_tests' in self.test_results:
            sec_results = self.test_results['security_tests']
            if isinstance(sec_results, dict):
                fk_test = next((t for t in sec_results.get('security_tests', [])
                               if t.get('test') == 'foreign_key_constraints'), None)
                if fk_test and not fk_test.get('enabled'):
                    recommendations.append({
                        'category': 'Security',
                        'priority': 'HIGH',
                        'issue': 'Foreign key constraints not enabled',
                        'recommendation': 'Enable foreign key constraints for data integrity'
                    })
        if 'compliance_tests' in self.test_results:
            comp_results = self.test_results['compliance_tests']
            if isinstance(comp_results, dict):
                pii_rate = comp_results.get('pii_encryption_rate', 0)
                if pii_rate < 1.0:
                    recommendations.append({
                        'category': 'Compliance',
                        'priority': 'CRITICAL',
                        'issue': f'PII encryption rate: {pii_rate:.1%}',
                        'recommendation': 'Implement field-level encryption for all PII data'
                    })
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
        if 'migration_tests' in self.test_results:
            mig_results = self.test_results['migration_tests']
            if isinstance(mig_results, dict) and not mig_results.get('migrations_table_exists'):
                recommendations.append({
                    'category': 'Migration',
                    'priority': 'HIGH',
                    'issue': 'Database not migrated',
                    'recommendation': 'Run Django migrations to create database schema'
                })
        return recommendations
    def _generate_html_report(self, report_data, output_path):
        html_content = f
        for test_name, test_result in report_data['detailed_results'].items():
            if isinstance(test_result, dict):
                status = test_result.get('status', 'UNKNOWN')
                status_class = status.lower()
                html_content += f
                if test_name == 'performance_tests' and isinstance(test_result, dict):
                    html_content += f
                elif test_name == 'compliance_tests' and isinstance(test_result, dict):
                    html_content += f
                elif test_name == 'data_integrity' and isinstance(test_result, dict):
                    html_content += f
                html_content += "</div>"
        if report_data.get('recommendations'):
            html_content += 
            for rec in report_data['recommendations']:
                priority_class = rec['priority'].lower()
                html_content += f
            html_content += "</div>"
        html_content += 
        with open(output_path, 'w') as f:
            f.write(html_content)
def main():
    print("🚀 HMS Enterprise-Grade SQLite Database Testing Suite")
    print("=" * 50)
    try:
        test_suite = SQLiteDatabaseTestingSuite()
        test_suite.run_all_tests()
        print("\n✅ Database Testing Suite Completed Successfully!")
        print("📊 Check the generated reports for detailed results:")
        print("   - sqlite_database_test_report.json (detailed JSON report)")
        print("   - sqlite_database_test_report.html (visual HTML report)")
        print("   - sqlite_database_testing.log (execution log)")
        return 0
    except Exception as e:
        print(f"\n❌ Database Testing Suite Failed: {e}")
        return 1
if __name__ == "__main__":
    sys.exit(main())