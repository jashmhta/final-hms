"""
ultimate_codebase_analyzer module
"""

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class UltimateCodebaseAnalyzer:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.results = {
            'file_analysis': {},
            'architecture': {},
            'code_quality': {},
            'security': {},
            'performance': {},
            'dependencies': {},
            'microservices': {},
            'database': {},
            'frontend': {},
            'infrastructure': {},
            'business_logic': {},
            'summary': {}
        }
        self.start_time = time.time()
    def analyze_file_system(self) -> Dict[str, Any]:
        print("🔍 PHASE 1: File System Analysis Started")
        file_types = defaultdict(int)
        file_sizes = defaultdict(list)
        directories = set()
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git']]
            current_dir = Path(root)
            directories.add(str(current_dir))
            for file in files:
                file_path = current_dir / file
                try:
                    file_size = file_path.stat().st_size
                    ext = file_path.suffix.lower()
                    file_types[ext] += 1
                    file_sizes[ext].append(file_size)
                    rel_path = str(file_path.relative_to(self.root_path))
                    self.results['file_analysis'][rel_path] = {
                        'size': file_size,
                        'extension': ext,
                        'directory': str(current_dir.relative_to(self.root_path)),
                        'modified': file_path.stat().st_mtime
                    }
                except (OSError, PermissionError):
                    continue
        stats = {}
        for ext, sizes in file_sizes.items():
            if sizes:
                stats[ext] = {
                    'count': len(sizes),
                    'total_size': sum(sizes),
                    'avg_size': sum(sizes) / len(sizes),
                    'max_size': max(sizes),
                    'min_size': min(sizes)
                }
        self.results['file_analysis']['statistics'] = {
            'total_files': sum(file_types.values()),
            'total_directories': len(directories),
            'file_types': dict(file_types),
            'file_size_stats': stats
        }
        print(f"📊 Analyzed {sum(file_types.values())} files across {len(directories)} directories")
        return self.results['file_analysis']
    def analyze_python_code(self, file_path: Path) -> Dict[str, Any]:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            lines = content.split('\n')
            total_lines = len(lines)
            code_lines = len([l for l in lines if l.strip() and not l.strip().startswith('
            comment_lines = len([l for l in lines if l.strip().startswith('
            blank_lines = len([l for l in lines if not l.strip()])
            tree = ast.parse(content)
            classes = []
            functions = []
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    classes.append({
                        'name': node.name,
                        'line_start': node.lineno,
                        'line_end': getattr(node, 'end_lineno', node.lineno),
                        'methods': methods,
                        'method_count': len(methods)
                    })
                elif isinstance(node, ast.FunctionDef):
                    functions.append({
                        'name': node.name,
                        'line_start': node.lineno,
                        'line_end': getattr(node, 'end_lineno', node.lineno),
                        'args_count': len(node.args.args)
                    })
                elif isinstance(node, ast.Import):
                    imports.extend([alias.name for alias in node.names])
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    imports.extend([f"{module}.{alias.name}" for alias in node.names])
            complexity_markers = ['if ', 'elif ', 'else:', 'for ', 'while ', 'with ', 'try:', 'except ', 'finally:']
            complexity = sum(content.count(marker) for marker in complexity_markers) + 1
            return {
                'total_lines': total_lines,
                'code_lines': code_lines,
                'comment_lines': comment_lines,
                'blank_lines': blank_lines,
                'classes': classes,
                'functions': functions,
                'imports': list(set(imports)),
                'complexity': complexity,
                'class_count': len(classes),
                'function_count': len(functions),
                'import_count': len(set(imports))
            }
        except (SyntaxError, UnicodeDecodeError, PermissionError) as e:
            return {'error': str(e)}
    def analyze_architecture(self) -> Dict[str, Any]:
        print("🏗️ PHASE 2: Architectural Analysis Started")
        django_apps = []
        backend_path = self.root_path / 'backend'
        if backend_path.exists():
            for item in backend_path.iterdir():
                if item.is_dir() and not item.name.startswith('_'):
                    if (item / 'models.py').exists() or (item / 'apps.py').exists():
                        django_apps.append(item.name)
        services_path = self.root_path / 'services'
        microservices = {}
        if services_path.exists():
            for service_dir in services_path.iterdir():
                if service_dir.is_dir() and not service_dir.name.startswith('_'):
                    service_info = self.analyze_microservice(service_dir)
                    if service_info:
                        microservices[service_dir.name] = service_info
        frontend_path = self.root_path / 'frontend'
        frontend_structure = {}
        if frontend_path.exists():
            frontend_structure = self.analyze_frontend(frontend_path)
        self.results['architecture'] = {
            'django_apps': django_apps,
            'microservices': microservices,
            'frontend_structure': frontend_structure,
            'architecture_type': 'Hybrid (Django Monolith + Microservices)',
            'total_microservices': len(microservices)
        }
        print(f"🏗️ Found {len(django_apps)} Django apps and {len(microservices)} microservices")
        return self.results['architecture']
    def analyze_microservice(self, service_path: Path) -> Optional[Dict[str, Any]]:
        try:
            main_files = list(service_path.glob('main.py'))
            requirements_files = list(service_path.glob('requirements*.txt'))
            models_files = list(service_path.glob('models.py'))
            python_files = list(service_path.rglob('*.py'))
            main_info = {}
            if main_files:
                main_info = self.analyze_python_code(main_files[0])
            return {
                'main_file_exists': len(main_files) > 0,
                'requirements_exists': len(requirements_files) > 0,
                'models_exists': len(models_files) > 0,
                'python_files_count': len(python_files),
                'main_analysis': main_info,
                'service_type': self.detect_service_type(service_path)
            }
        except Exception as e:
            return None
    def detect_service_type(self, service_path: Path) -> str:
        service_name = service_path.name.lower()
        clinical_services = ['lab', 'pharmacy', 'radiology', 'blood_bank', 'emergency']
        administrative_services = ['billing', 'hr', 'facilities', 'erp', 'accounting']
        patient_services = ['appointments', 'patients', 'triage', 'consent']
        if any(service in service_name for service in clinical_services):
            return 'clinical'
        elif any(service in service_name for service in administrative_services):
            return 'administrative'
        elif any(service in service_name for service in patient_services):
            return 'patient_care'
        else:
            return 'support'
    def analyze_frontend(self, frontend_path: Path) -> Dict[str, Any]:
        try:
            package_json = frontend_path / 'package.json'
            if package_json.exists():
                return self.analyze_node_frontend(frontend_path)
            src_dirs = [d for d in frontend_path.iterdir() if d.is_dir() and d.name == 'src']
            if src_dirs:
                return self.analyze_modular_frontend(frontend_path)
            return {'type': 'unknown', 'structure': 'basic'}
        except Exception as e:
            return {'error': str(e)}
    def analyze_node_frontend(self, frontend_path: Path) -> Dict[str, Any]:
        try:
            with open(frontend_path / 'package.json', 'r') as f:
                package_data = json.load(f)
            dependencies = package_data.get('dependencies', {})
            dev_dependencies = package_data.get('devDependencies', {})
            frameworks = ['react', 'vue', 'angular', 'svelte', 'next', 'nuxt']
            detected_framework = 'unknown'
            all_deps = {**dependencies, **dev_dependencies}
            for framework in frameworks:
                if framework in all_deps:
                    detected_framework = framework
                    break
            ts_files = list(frontend_path.rglob('*.ts'))
            tsx_files = list(frontend_path.rglob('*.tsx'))
            js_files = list(frontend_path.rglob('*.js'))
            jsx_files = list(frontend_path.rglob('*.jsx'))
            css_files = list(frontend_path.rglob('*.css'))
            return {
                'type': 'node_frontend',
                'framework': detected_framework,
                'dependencies_count': len(dependencies),
                'dev_dependencies_count': len(dev_dependencies),
                'total_dependencies': len(all_deps),
                'file_counts': {
                    'typescript': len(ts_files),
                    'tsx': len(tsx_files),
                    'javascript': len(js_files),
                    'jsx': len(jsx_files),
                    'css': len(css_files)
                }
            }
        except Exception as e:
            return {'error': str(e)}
    def analyze_modular_frontend(self, frontend_path: Path) -> Dict[str, Any]:
        try:
            src_dir = frontend_path / 'src'
            if not src_dir.exists():
                return {'error': 'src directory not found'}
            components = list(src_dir.rglob('*component*'))
            pages = list(src_dir.rglob('*page*'))
            services = list(src_dir.rglob('*service*'))
            return {
                'type': 'modular_frontend',
                'components_count': len(components),
                'pages_count': len(pages),
                'services_count': len(services),
                'structure_type': 'component_based'
            }
        except Exception as e:
            return {'error': str(e)}
    def analyze_code_quality(self) -> Dict[str, Any]:
        print("🔬 PHASE 3: Code Quality Analysis Started")
        python_files = list(self.root_path.rglob('*.py'))
        quality_metrics = {
            'total_python_files': len(python_files),
            'analyzed_files': 0,
            'total_lines': 0,
            'total_code_lines': 0,
            'complexity_distribution': defaultdict(int),
            'class_count': 0,
            'function_count': 0,
            'files_with_errors': 0,
            'quality_score': 0
        }
        complexity_scores = []
        for i, py_file in enumerate(python_files):
            if i % 1000 == 0:
                print(f"  Analyzing file {i+1}/{len(python_files)}")
            if 'node_modules' in str(py_file) or '__pycache__' in str(py_file):
                continue
            analysis = self.analyze_python_code(py_file)
            if 'error' not in analysis:
                quality_metrics['analyzed_files'] += 1
                quality_metrics['total_lines'] += analysis['total_lines']
                quality_metrics['total_code_lines'] += analysis['code_lines']
                quality_metrics['class_count'] += analysis['class_count']
                quality_metrics['function_count'] += analysis['function_count']
                complexity = analysis['complexity']
                complexity_scores.append(complexity)
                if complexity <= 5:
                    quality_metrics['complexity_distribution']['simple'] += 1
                elif complexity <= 10:
                    quality_metrics['complexity_distribution']['moderate'] += 1
                elif complexity <= 20:
                    quality_metrics['complexity_distribution']['complex'] += 1
                else:
                    quality_metrics['complexity_distribution']['very_complex'] += 1
            else:
                quality_metrics['files_with_errors'] += 1
        if quality_metrics['analyzed_files'] > 0:
            avg_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0
            quality_metrics['average_complexity'] = avg_complexity
            complexity_penalty = min(avg_complexity / 10, 1.0)
            error_penalty = quality_metrics['files_with_errors'] / max(quality_metrics['total_python_files'], 1)
            quality_metrics['quality_score'] = max(0, 100 - (complexity_penalty * 30 + error_penalty * 40))
        self.results['code_quality'] = quality_metrics
        print(f"🔬 Analyzed {quality_metrics['analyzed_files']} Python files")
        return quality_metrics
    def analyze_security(self) -> Dict[str, Any]:
        print("🔒 PHASE 4: Security Analysis Started")
        security_issues = {
            'total_issues': 0,
            'critical_issues': 0,
            'high_issues': 0,
            'medium_issues': 0,
            'low_issues': 0,
            'issues_by_type': defaultdict(int),
            'files_with_issues': set(),
            'compliance_status': 'unknown'
        }
        security_patterns = {
            'sql_injection': [r'execute\s*\(\s*[\'"][^\'"]*\s*\+\s*[^\'"]*[\'"]', r'cursor\.execute\s*\(\s*[\'"]%s[\'"]'],
            'command_injection': [r'os\.system\s*\(', r'subprocess\.call\s*\(', r'eval\s*\('],
            'insecure_deserialization': [r'pickle\.load\s*\(', r'marshal\.load\s*\('],
            'weak_crypto': [r'md5\s*\(', r'sha1\s*\('],
        }
        python_files = list(self.root_path.rglob('*.py'))
        for py_file in python_files:
            if 'node_modules' in str(py_file) or '__pycache__' in str(py_file):
                continue
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                file_issues = []
                for issue_type, patterns in security_patterns.items():
                    for pattern in patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            security_issues['issues_by_type'][issue_type] += len(matches)
                            file_issues.append(issue_type)
                if file_issues:
                    security_issues['files_with_issues'].add(str(py_file))
                    security_issues['total_issues'] += len(file_issues)
                critical_types = ['sql_injection', 'command_injection']
                medium_types = ['insecure_deserialization', 'weak_crypto']
                for issue_type in file_issues:
                    if issue_type in critical_types:
                        security_issues['critical_issues'] += 1
                    elif issue_type in high_types:
                        security_issues['high_issues'] += 1
                    elif issue_type in medium_types:
                        security_issues['medium_issues'] += 1
                    else:
                        security_issues['low_issues'] += 1
            except Exception as e:
                continue
        security_issues['files_with_issues_count'] = len(security_issues['files_with_issues'])
        security_issues['hipaa_compliance'] = self.check_hipaa_compliance()
        self.results['security'] = security_issues
        print(f"🔒 Found {security_issues['total_issues']} security issues")
        return security_issues
    def check_hipaa_compliance(self) -> Dict[str, Any]:
        compliance_checks = {
            'data_encryption': False,
            'audit_logging': False,
            'access_controls': False,
            'user_authentication': False,
            'data_backup': False,
            'disaster_recovery': False,
            'privacy_policies': False,
            'breach_notification': False
        }
        encryption_files = list(self.root_path.rglob('*encryption*'))
        if encryption_files:
            compliance_checks['data_encryption'] = True
        audit_files = list(self.root_path.rglob('*audit*'))
        if audit_files:
            compliance_checks['audit_logging'] = True
        auth_files = list(self.root_path.rglob('*auth*'))
        if auth_files:
            compliance_checks['user_authentication'] = True
        backup_files = list(self.root_path.rglob('*backup*'))
        if backup_files:
            compliance_checks['data_backup'] = True
        dr_files = list(self.root_path.rglob('*disaster*'))
        if dr_files:
            compliance_checks['disaster_recovery'] = True
        settings_files = list(self.root_path.rglob('settings.py'))
        for settings_file in settings_files:
            try:
                with open(settings_file, 'r') as f:
                    content = f.read()
                if 'HIPAA' in content.upper():
                    compliance_checks['privacy_policies'] = True
                if 'ACCESS_CONTROL' in content.upper():
                    compliance_checks['access_controls'] = True
                if 'ENCRYPTION' in content.upper():
                    compliance_checks['data_encryption'] = True
            except Exception:
                continue
        compliance_score = sum(compliance_checks.values()) / len(compliance_checks) * 100
        return {
            'checks': compliance_checks,
            'compliance_score': compliance_score,
            'status': 'compliant' if compliance_score >= 80 else 'partial' if compliance_score >= 50 else 'non_compliant'
        }
    def analyze_dependencies(self) -> Dict[str, Any]:
        print("📦 PHASE 5: Dependency Analysis Started")
        dependencies = {
            'python_requirements': {},
            'node_packages': {},
            'total_dependencies': 0,
            'vulnerabilities': [],
            'outdated_packages': [],
            'dependency_tree': {}
        }
        requirements_files = list(self.root_path.rglob('requirements*.txt'))
        for req_file in requirements_files:
            try:
                with open(req_file, 'r') as f:
                    lines = f.readlines()
                req_deps = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('
                        req_deps.append(line)
                dependencies['python_requirements'][str(req_file)] = req_deps
                dependencies['total_dependencies'] += len(req_deps)
            except Exception:
                continue
        package_files = list(self.root_path.rglob('package.json'))
        for pkg_file in package_files:
            try:
                with open(pkg_file, 'r') as f:
                    package_data = json.load(f)
                deps = package_data.get('dependencies', {})
                dev_deps = package_data.get('devDependencies', {})
                dependencies['node_packages'][str(pkg_file)] = {
                    'dependencies': list(deps.keys()),
                    'dev_dependencies': list(dev_deps.keys())
                }
                dependencies['total_dependencies'] += len(deps) + len(dev_deps)
            except Exception:
                continue
        self.results['dependencies'] = dependencies
        print(f"📦 Analyzed {dependencies['total_dependencies']} total dependencies")
        return dependencies
    def analyze_database(self) -> Dict[str, Any]:
        print("🗄️ PHASE 6: Database Analysis Started")
        database_info = {
            'django_models': {},
            'total_models': 0,
            'model_relationships': [],
            'migration_files': [],
            'sql_files': [],
            'database_type': 'unknown'
        }
        backend_path = self.root_path / 'backend'
        if backend_path.exists():
            for app_dir in backend_path.iterdir():
                if app_dir.is_dir() and not app_dir.name.startswith('_'):
                    models_file = app_dir / 'models.py'
                    if models_file.exists():
                        models_analysis = self.analyze_django_models(models_file)
                        if models_analysis:
                            database_info['django_models'][app_dir.name] = models_analysis
                            database_info['total_models'] += len(models_analysis.get('models', []))
        migration_files = list(self.root_path.rglob('migrations/*.py'))
        database_info['migration_files'] = [str(f) for f in migration_files if not f.name.endswith('__init__.py')]
        sql_files = list(self.root_path.rglob('*.sql'))
        database_info['sql_files'] = [str(f) for f in sql_files]
        settings_files = list(self.root_path.rglob('settings.py'))
        for settings_file in settings_files:
            try:
                with open(settings_file, 'r') as f:
                    content = f.read()
                if 'postgresql' in content.lower():
                    database_info['database_type'] = 'postgresql'
                elif 'mysql' in content.lower():
                    database_info['database_type'] = 'mysql'
                elif 'sqlite' in content.lower():
                    database_info['database_type'] = 'sqlite'
                break
            except Exception:
                continue
        self.results['database'] = database_info
        print(f"🗄️ Found {database_info['total_models']} Django models")
        return database_info
    def analyze_django_models(self, models_file: Path) -> Optional[Dict[str, Any]]:
        try:
            with open(models_file, 'r') as f:
                content = f.read()
            tree = ast.parse(content)
            models = []
            relationships = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if any(base.id == 'Model' for base in node.bases if isinstance(base, ast.Name)):
                        model_info = {
                            'name': node.name,
                            'fields': [],
                            'methods': [],
                            'line_start': node.lineno
                        }
                        for item in node.body:
                            if isinstance(item, ast.Assign):
                                for target in item.targets:
                                    if isinstance(target, ast.Name):
                                        field_type = 'unknown'
                                        if isinstance(item.value, ast.Call):
                                            if isinstance(item.value.func, ast.Name):
                                                field_type = item.value.func.id
                                            elif isinstance(item.value.func, ast.Attribute):
                                                field_type = item.value.func.attr
                                        model_info['fields'].append({
                                            'name': target.id,
                                            'type': field_type
                                        })
                            elif isinstance(item, ast.FunctionDef):
                                model_info['methods'].append(item.name)
                        models.append(model_info)
            return {
                'models': models,
                'relationships': relationships,
                'file_path': str(models_file)
            }
        except Exception as e:
            return None
    def analyze_infrastructure(self) -> Dict[str, Any]:
        print("🏗️ PHASE 7: Infrastructure Analysis Started")
        infrastructure = {
            'docker_files': [],
            'kubernetes_files': [],
            'ci_cd_files': [],
            'configuration_files': [],
            'monitoring_files': [],
            'infrastructure_type': 'docker_compose'
        }
        docker_files = list(self.root_path.rglob('Dockerfile*'))
        infrastructure['docker_files'] = [str(f) for f in docker_files]
        k8s_files = list(self.root_path.rglob('*.yaml')) + list(self.root_path.rglob('*.yml'))
        k8s_files = [str(f) for f in k8s_files if 'k8s' in str(f) or 'kubernetes' in str(f)]
        infrastructure['kubernetes_files'] = k8s_files
        ci_cd_files = list(self.root_path.rglob('.github/workflows/*.yml')) + \
                     list(self.root_path.rglob('.github/workflows/*.yaml'))
        infrastructure['ci_cd_files'] = [str(f) for f in ci_cd_files]
        config_files = list(self.root_path.rglob('docker-compose*.yml')) + \
                      list(self.root_path.rglob('docker-compose*.yaml')) + \
                      list(self.root_path.rglob('.env*'))
        infrastructure['configuration_files'] = [str(f) for f in config_files]
        monitoring_files = list(self.root_path.rglob('*prometheus*')) + \
                           list(self.root_path.rglob('*grafana*')) + \
                           list(self.root_path.rglob('*monitoring*'))
        infrastructure['monitoring_files'] = [str(f) for f in monitoring_files]
        if infrastructure['kubernetes_files']:
            infrastructure['infrastructure_type'] = 'kubernetes'
        elif infrastructure['docker_files']:
            infrastructure['infrastructure_type'] = 'docker'
        self.results['infrastructure'] = infrastructure
        print(f"🏗️ Found {len(infrastructure['docker_files'])} Docker files and {len(infrastructure['kubernetes_files'])} Kubernetes files")
        return infrastructure
    def generate_summary(self) -> Dict[str, Any]:
        print("📊 Generating Summary")
        analysis_time = time.time() - self.start_time
        summary = {
            'analysis_duration_seconds': analysis_time,
            'analysis_duration_formatted': f"{analysis_time:.2f} seconds",
            'codebase_health_score': 0,
            'total_findings': 0,
            'critical_issues': 0,
            'recommendations': [],
            'key_metrics': {}
        }
        scores = []
        if 'code_quality' in self.results and 'quality_score' in self.results['code_quality']:
            scores.append(self.results['code_quality']['quality_score'])
        if 'security' in self.results:
            security_score = 100
            security_issues = self.results['security']
            if security_issues['total_issues'] > 0:
                security_score = max(0, 100 - (security_issues['critical_issues'] * 20 +
                                                 security_issues['high_issues'] * 10 +
                                                 security_issues['medium_issues'] * 5))
            scores.append(security_score)
        if 'architecture' in self.results:
            arch_score = 80  
            if self.results['architecture'].get('total_microservices', 0) > 20:
                arch_score += 10
            scores.append(arch_score)
        if scores:
            summary['codebase_health_score'] = sum(scores) / len(scores)
        if 'security' in self.results:
            summary['critical_issues'] = self.results['security'].get('critical_issues', 0)
            summary['total_findings'] += self.results['security'].get('total_issues', 0)
        recommendations = []
        if summary['critical_issues'] > 0:
            recommendations.append({
                'priority': 'critical',
                'category': 'security',
                'issue': f'{summary["critical_issues"]} critical security issues found',
                'recommendation': 'Address critical security vulnerabilities immediately'
            })
        if 'code_quality' in self.results:
            complexity_dist = self.results['code_quality'].get('complexity_distribution', {})
            if complexity_dist.get('very_complex', 0) > 0:
                recommendations.append({
                    'priority': 'high',
                    'category': 'performance',
                    'issue': f'{complexity_dist.get("very_complex", 0)} highly complex files',
                    'recommendation': 'Refactor complex files to improve maintainability'
                })
        if 'architecture' in self.results:
            if self.results['architecture'].get('total_microservices', 0) < 10:
                recommendations.append({
                    'priority': 'medium',
                    'category': 'architecture',
                    'issue': 'Limited microservice architecture',
                    'recommendation': 'Consider breaking down monolithic components into microservices'
                })
        summary['recommendations'] = recommendations
            'total_files': self.results['file_analysis'].get('statistics', {}).get('total_files', 0),
            'total_python_files': self.results['code_quality'].get('total_python_files', 0),
            'total_microservices': self.results['architecture'].get('total_microservices', 0),
            'total_models': self.results['database'].get('total_models', 0),
            'total_dependencies': self.results['dependencies'].get('total_dependencies', 0)
        }
        self.results['summary'] = summary
        return summary
    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        print("🚀 STARTING ULTIMATE COMPREHENSIVE CODEBASE ANALYSIS")
        print("=" * 80)
        self.analyze_file_system()
        self.analyze_architecture()
        self.analyze_code_quality()
        self.analyze_security()
        self.analyze_dependencies()
        self.analyze_database()
        self.analyze_infrastructure()
        self.generate_summary()
        print("=" * 80)
        print("✅ COMPREHENSIVE ANALYSIS COMPLETED")
        print(f"⏱️  Total analysis time: {self.results['summary']['analysis_duration_formatted']}")
        print(f"📊 Codebase Health Score: {self.results['summary']['codebase_health_score']:.1f}/100")
        print(f"🔍 Total findings: {self.results['summary']['total_findings']}")
        print(f"⚠️  Critical issues: {self.results['summary']['critical_issues']}")
        return self.results
def main():
    import argparse
    parser = argparse.ArgumentParser(description='Ultimate Codebase Analysis Tool')
    parser.add_argument('--path', '-p', default='/home/azureuser/hms-enterprise-grade',
                       help='Path to codebase root')
    parser.add_argument('--output', '-o', default='ultimate_analysis_report.json',
                       help='Output file for analysis results')
    args = parser.parse_args()
    analyzer = UltimateCodebaseAnalyzer(args.path)
    results = analyzer.run_comprehensive_analysis()
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n📄 Analysis report saved to: {args.output}")
    summary = results.get('summary', {})
    print("\n" + "="*80)
    print("🎯 EXECUTIVE SUMMARY")
    print("="*80)
    print(f"🏥 System: HMS Enterprise-Grade Healthcare Management")
    print(f"📊 Health Score: {summary.get('codebase_health_score', 0):.1f}/100")
    print(f"📁 Total Files: {summary.get('key_metrics', {}).get('total_files', 0):,}")
    print(f"🐍 Python Files: {summary.get('key_metrics', {}).get('total_python_files', 0):,}")
    print(f"⚡ Microservices: {summary.get('key_metrics', {}).get('total_microservices', 0)}")
    print(f"🗄️ Database Models: {summary.get('key_metrics', {}).get('total_models', 0)}")
    print(f"📦 Dependencies: {summary.get('key_metrics', {}).get('total_dependencies', 0)}")
    print(f"⚠️  Critical Issues: {summary.get('critical_issues', 0)}")
    print(f"📈 Total Findings: {summary.get('total_findings', 0)}")
    print("\n🔧 TOP RECOMMENDATIONS:")
    for i, rec in enumerate(summary.get('recommendations', [])[:3], 1):
        print(f"  {i}. [{rec['priority'].upper()}] {rec['recommendation']}")
if __name__ == "__main__":
    main()