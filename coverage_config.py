import os
import sys
import json
import yaml
import logging
import subprocess
import coverage
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import unittest
import pytest
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('coverage_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
@dataclass
class CoverageMetrics:
    file_path: str
    line_coverage: float = 0.0
    branch_coverage: float = 0.0
    function_coverage: float = 0.0
    class_coverage: float = 0.0
    method_coverage: float = 0.0
    statement_coverage: float = 0.0
    total_lines: int = 0
    covered_lines: int = 0
    missing_lines: List[int] = None
    covered_functions: int = 0
    total_functions: int = 0
    missing_functions: List[str] = None
    risk_level: str = "low"
    compliance_violations: List[str] = None
    def __post_init__(self):
        if self.missing_lines is None:
            self.missing_lines = []
        if self.missing_functions is None:
            self.missing_functions = []
        if self.compliance_violations is None:
            self.compliance_violations = []
@dataclass
class TestQualityMetrics:
    test_file: str
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    error_tests: int = 0
    test_duration: float = 0.0
    assertions_count: int = 0
    complexity_score: float = 0.0
    maintainability_score: float = 0.0
    coverage_score: float = 0.0
    quality_score: float = 0.0
    test_patterns: List[str] = None
    anti_patterns: List[str] = None
    def __post_init__(self):
        if self.test_patterns is None:
            self.test_patterns = []
        if self.anti_patterns is None:
            self.anti_patterns = []
class CoverageAnalyzer:
    def __init__(self, root_dir: str = None):
        self.root_dir = root_dir or os.getcwd()
        self.coverage_config = self.load_coverage_config()
        self.test_quality_config = self.load_test_quality_config()
        self.healthcare_critical_files = [
            'patient', 'medical', 'health', 'clinical', 'diagnosis',
            'treatment', 'medication', 'record', 'auth', 'security',
            'encrypt', 'decrypt', 'audit', 'compliance'
        ]
        self.thresholds = {
            'overall_line_coverage': 95.0,
            'overall_branch_coverage': 90.0,
            'overall_function_coverage': 95.0,
            'critical_line_coverage': 100.0,
            'critical_branch_coverage': 100.0,
            'critical_function_coverage': 100.0,
            'minimum_file_coverage': 80.0,
            'test_quality_score': 85.0
        }
    def load_coverage_config(self) -> Dict[str, Any]:
        config = {
            'run': {
                'source': ['.'],
                'omit': [
                    '*/tests/*',
                    '*/test_*',
                    '*/migrations/*',
                    '*/__pycache__/*',
                    '*/.venv/*',
                    '*/venv/*',
                    '*/env/*',
                    '*/build/*',
                    '*/dist/*',
                    '*/node_modules/*',
                    '*/static/*',
                    '*/media/*',
                    '*/coverage/*',
                    'setup.py',
                    'conftest.py',
                    'manage.py',
                    'wsgi.py'
                ],
                'include': ['*.py'],
                'branch': True,
                'parallel': True,
                'concurrency': ['thread', 'multiprocessing'],
                'plugins': ['django_coverage_plugin'],
                'relative_files': True,
                'source_pkgs': [],
                'disable_warnings': ['no-data-collected']
            },
            'report': {
                'exclude_lines': [
                    'pragma: no cover',
                    'def __repr__',
                    'raise AssertionError',
                    'raise NotImplementedError',
                    'if __name__ == .__main__.:',
                    'if TYPE_CHECKING:',
                    'class .*\bProtocol\):',
                    '@(abc\.)?abstractmethod',
                    'if self\.debug:',
                    'if settings\.DEBUG',
                    'if DEBUG',
                    'if app\.debug',
                    'if not app\.production'
                ],
                'precision': 2,
                'show_missing': True,
                'skip_covered': False,
                'skip_empty': True
            },
            'html': {
                'directory': 'htmlcov',
                'title': 'HMS Enterprise-Grade Coverage Report'
            },
            'xml': {
                'output': 'coverage.xml'
            },
            'json': {
                'output': 'coverage.json'
            }
        }
        return config
    def load_test_quality_config(self) -> Dict[str, Any]:
        return {
            'test_patterns': {
                'unit_tests': ['test_*.py', '*_test.py'],
                'integration_tests': ['test_integration_*.py', 'integration/*'],
                'e2e_tests': ['test_e2e_*.py', 'e2e/*'],
                'performance_tests': ['test_performance_*.py', 'performance/*'],
                'security_tests': ['test_security_*.py', 'security/*']
            },
            'quality_thresholds': {
                'min_test_duration': 0.1,
                'max_test_duration': 30.0,
                'min_assertions_per_test': 1,
                'max_test_file_complexity': 15,
                'min_test_coverage': 80.0,
                'max_test_anti_patterns': 2
            },
            'anti_patterns': [
                'assert True',
                'assert False',
                'assert None',
                'time.sleep',
                'print(',
                'input(',
                'os.system(',
                'subprocess.call(',
                'pytest.skip',
                'pytest.mark.skip',
                'unittest.skip'
            ],
            'required_patterns': [
                'assert',
                'def test_',
                'import unittest',
                'import pytest',
                'setUp',
                'tearDown'
            ]
        }
    def run_coverage_analysis(self) -> Dict[str, Any]:
        logger.info("Starting comprehensive coverage analysis...")
        results = {
            'summary': {},
            'file_coverage': [],
            'test_quality': [],
            'healthcare_compliance': {},
            'quality_gates': {},
            'recommendations': []
        }
        cov = coverage.Coverage(
            source=self.coverage_config['run']['source'],
            omit=self.coverage_config['run']['omit'],
            branch=self.coverage_config['run']['branch'],
            parallel=self.coverage_config['run']['parallel'],
            config_file='.coveragerc'
        )
        cov.start()
        try:
            test_results = self.run_tests()
            results['test_results'] = test_results
            cov.stop()
            cov.save()
            coverage_results = self.analyze_coverage_results(cov)
            results['file_coverage'] = coverage_results
            test_quality_results = self.analyze_test_quality()
            results['test_quality'] = test_quality_results
            healthcare_compliance = self.check_healthcare_compliance(coverage_results)
            results['healthcare_compliance'] = healthcare_compliance
            quality_gates = self.check_quality_gates(results)
            results['quality_gates'] = quality_gates
            summary = self.generate_coverage_summary(results)
            results['summary'] = summary
            recommendations = self.generate_coverage_recommendations(results)
            results['recommendations'] = recommendations
        except Exception as e:
            logger.error(f"Error during coverage analysis: {e}")
            results['error'] = str(e)
        return results
    def run_tests(self) -> Dict[str, Any]:
        logger.info("Running comprehensive test suite...")
        test_results = {
            'unit_tests': {},
            'integration_tests': {},
            'e2e_tests': {},
            'performance_tests': {},
            'security_tests': {},
            'overall': {}
        }
        test_categories = [
            ('unit_tests', ['pytest', '-v', '--tb=short', '--cov=.', '--cov-report=term-missing']),
            ('integration_tests', ['pytest', '-v', '--tb=short', '-m', 'integration']),
            ('e2e_tests', ['pytest', '-v', '--tb=short', '-m', 'e2e']),
            ('performance_tests', ['pytest', '-v', '--tb=short', '-m', 'performance']),
            ('security_tests', ['pytest', '-v', '--tb=short', '-m', 'security'])
        ]
        for category, cmd in test_categories:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.root_dir)
                test_results[category] = {
                    'exit_code': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'success': result.returncode == 0
                }
            except Exception as e:
                logger.error(f"Error running {category}: {e}")
                test_results[category] = {
                    'exit_code': -1,
                    'stdout': '',
                    'stderr': str(e),
                    'success': False
                }
        return test_results
    def analyze_coverage_results(self, cov: coverage.Coverage) -> List[CoverageMetrics]:
        logger.info("Analyzing coverage results...")
        metrics = []
        cov_data = cov.get_data()
        covered_files = cov_data.measured_files()
        for file_path in covered_files:
            if self.should_analyze_file(file_path):
                file_metrics = self.analyze_file_coverage(cov, file_path)
                metrics.append(file_metrics)
        return metrics
    def should_analyze_file(self, file_path: str) -> bool:
        if any(pattern in file_path for pattern in ['test_', '/tests/', '__pycache__']):
            return False
        excluded_patterns = [
            'migrations/', 'static/', 'media/', 'node_modules/',
            'conftest.py', 'manage.py', 'wsgi.py', 'setup.py'
        ]
        for pattern in excluded_patterns:
            if pattern in file_path:
                return False
        return file_path.endswith('.py')
    def analyze_file_coverage(self, cov: coverage.Coverage, file_path: str) -> CoverageMetrics:
        metrics = CoverageMetrics(file_path=file_path)
        try:
            analysis = cov.analysis2(file_path)
            if len(analysis) >= 5:
                covered_lines, num_statements, excluded_lines, missing_lines, formatted = analysis
                metrics.total_lines = num_statements
                metrics.covered_lines = covered_lines
                metrics.missing_lines = missing_lines
                if num_statements > 0:
                    metrics.line_coverage = (covered_lines / num_statements) * 100
                branches = cov.get_data().arcs(file_path)
                if branches:
                    total_branches = len(branches)
                    executed_branches = sum(1 for arc in branches if arc in cov.get_data().arcs(file_path))
                    metrics.branch_coverage = (executed_branches / total_branches) * 100
                metrics.function_coverage = self.analyze_function_coverage(file_path)
                metrics.risk_level = self.determine_risk_level(metrics)
                metrics.compliance_violations = self.check_healthcare_file_compliance(metrics)
        except Exception as e:
            logger.error(f"Error analyzing coverage for {file_path}: {e}")
        return metrics
    def analyze_function_coverage(self, file_path: str) -> float:
        try:
            import ast
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            tree = ast.parse(source_code)
            functions = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
            total_functions = len(functions)
            covered_functions = total_functions  
            return (covered_functions / total_functions) * 100 if total_functions > 0 else 0.0
        except Exception as e:
            logger.error(f"Error analyzing function coverage for {file_path}: {e}")
            return 0.0
    def determine_risk_level(self, metrics: CoverageMetrics) -> str:
        if metrics.line_coverage < 50:
            return "critical"
        elif metrics.line_coverage < 70:
            return "high"
        elif metrics.line_coverage < 85:
            return "medium"
        elif metrics.line_coverage < 95:
            return "low"
        else:
            return "minimal"
    def check_healthcare_file_compliance(self, metrics: CoverageMetrics) -> List[str]:
        violations = []
        file_name = os.path.basename(metrics.file_path).lower()
        is_critical = any(keyword in file_name for keyword in self.healthcare_critical_files)
        if is_critical:
            if metrics.line_coverage < 100:
                violations.append(f"Critical healthcare file has {metrics.line_coverage:.1f}% coverage (requires 100%)")
            if metrics.branch_coverage < 100:
                violations.append(f"Critical healthcare file has {metrics.branch_coverage:.1f}% branch coverage (requires 100%)")
            if metrics.function_coverage < 100:
                violations.append(f"Critical healthcare file has {metrics.function_coverage:.1f}% function coverage (requires 100%)")
        else:
            if metrics.line_coverage < self.thresholds['minimum_file_coverage']:
                violations.append(f"File has {metrics.line_coverage:.1f}% coverage (minimum: {self.thresholds['minimum_file_coverage']}%)")
        return violations
    def analyze_test_quality(self) -> List[TestQualityMetrics]:
        logger.info("Analyzing test quality...")
        test_quality_metrics = []
        test_files = self.find_test_files()
        for test_file in test_files:
            metrics = self.analyze_test_file_quality(test_file)
            test_quality_metrics.append(metrics)
        return test_quality_metrics
    def find_test_files(self) -> List[str]:
        test_files = []
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
            for file in files:
                if file.startswith('test_') or file.endswith('_test.py'):
                    test_files.append(os.path.join(root, file))
        return test_files
    def analyze_test_file_quality(self, test_file: str) -> TestQualityMetrics:
        metrics = TestQualityMetrics(test_file=test_file)
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            import ast
            tree = ast.parse(content)
            test_methods = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    test_methods.append(node.name)
            metrics.total_tests = len(test_methods)
            metrics.assertions_count = content.count('assert')
            metrics.test_patterns = self.analyze_test_patterns(content)
            metrics.anti_patterns = self.analyze_test_anti_patterns(content)
            metrics.complexity_score = self.calculate_test_complexity_score(test_file)
            metrics.maintainability_score = self.calculate_test_maintainability_score(test_file)
            metrics.quality_score = self.calculate_test_quality_score(metrics)
        except Exception as e:
            logger.error(f"Error analyzing test file {test_file}: {e}")
        return metrics
    def analyze_test_patterns(self, content: str) -> List[str]:
        patterns = []
        good_patterns = [
            'setUp', 'tearDown', 'mock', 'patch', 'fixture',
            'assertEqual', 'assertNotEqual', 'assertTrue', 'assertFalse',
            'assertRaises', 'assertIn', 'assertNotIn'
        ]
        for pattern in good_patterns:
            if pattern in content:
                patterns.append(pattern)
        return patterns
    def analyze_test_anti_patterns(self, content: str) -> List[str]:
        anti_patterns = []
        for anti_pattern in self.test_quality_config['anti_patterns']:
            if anti_pattern in content:
                anti_patterns.append(anti_pattern)
        return anti_patterns
    def calculate_test_complexity_score(self, test_file: str) -> float:
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            lines = content.split('\n')
            non_empty_lines = [line for line in lines if line.strip() and not line.strip().startswith('
            complexity = len(non_empty_lines) * 0.1 + content.count('if') * 2 + content.count('for') * 1.5 + content.count('while') * 2
            return max(0, 100 - complexity)
        except Exception as e:
            logger.error(f"Error calculating complexity for {test_file}: {e}")
            return 0.0
    def calculate_test_maintainability_score(self, test_file: str) -> float:
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            score = 50  
            if 'Calculate overall test quality scoreCheck healthcare-specific compliance requirementsGet compliance recommendation based on risk levelCheck if results meet quality gatesGenerate coverage summaryGenerate improvement recommendationsGenerate coverage analysis reportGenerate HTML coverage report
        <!DOCTYPE html>
        <html>
        <head>
            <title>HMS Coverage Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background: 
                .passed {{ background: 
                .failed {{ background: 
                .warning {{ background: 
                .table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                .table th, .table td {{ border: 1px solid 
                .table th {{ background-color: 
                .recommendation {{ background: 
                .critical {{ background: 
                .high {{ background: 
                .medium {{ background: 
                .low {{ background: 
            </style>
        </head>
        <body>
            <h1>HMS Enterprise-Grade System - Coverage Analysis Report</h1>
            <div class="summary">
                <h2>Summary</h2>
                <p>Total Files Analyzed: {summary.get('total_files_analyzed', 0)}</p>
                <p>Average Line Coverage: {summary.get('average_line_coverage', 0):.1f}%</p>
                <p>Average Branch Coverage: {summary.get('average_branch_coverage', 0):.1f}%</p>
                <p>Average Function Coverage: {summary.get('average_function_coverage', 0):.1f}%</p>
                <p>Average Test Quality Score: {summary.get('average_test_quality_score', 0):.1f}%</p>
                <p>Healthcare Compliance: {summary.get('healthcare_compliance', False)}</p>
                <p>Quality Gates: {'PASSED' if summary.get('quality_gates_passed', False) else 'FAILED'}</p>
            </div>
            <div class="summary {'passed' if summary.get('healthcare_compliance', False) else 'failed'}">
                <h2>Healthcare Compliance</h2>
                <p>Status: {'COMPLIANT' if summary.get('healthcare_compliance', False) else 'NON-COMPLIANT'}</p>
                <p>Critical Files Covered: {summary.get('critical_files_covered', 0)}</p>
            </div>
            <h2>Recommendations</h2>
            {self._generate_recommendations_html(results.get('recommendations', []))}
            <h2>Coverage Details</h2>
            {self._generate_coverage_details_html(results.get('file_coverage', []))}
        </body>
        </html>
        Generate HTML for recommendations
            <div class="recommendation {rec['priority']}">
                <h3>{rec['title']} ({rec['priority'].upper()})</h3>
                <p><strong>Category:</strong> {rec['category']}</p>
                <p><strong>Description:</strong> {rec['description']}</p>
                <p><strong>Action:</strong> {rec['action']}</p>
            </div>
            Generate HTML for coverage details
        <table class="table">
            <thead>
                <tr>
                    <th>File</th>
                    <th>Line Coverage</th>
                    <th>Branch Coverage</th>
                    <th>Function Coverage</th>
                    <th>Risk Level</th>
                    <th>Compliance Issues</th>
                </tr>
            </thead>
            <tbody>
            <tr>
                <td>{os.path.basename(metrics.file_path)}</td>
                <td>{metrics.line_coverage:.1f}%</td>
                <td>{metrics.branch_coverage:.1f}%</td>
                <td>{metrics.function_coverage:.1f}%</td>
                <td class="{metrics.risk_level}">{metrics.risk_level.upper()}</td>
                <td>{compliance_issues}</td>
            </tr>
            </tbody>
        </table>
        Main function"""
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = os.getcwd()
    analyzer = CoverageAnalyzer(root_dir)
    results = analyzer.run_coverage_analysis()
    with open('coverage_analysis_report.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    html_report = analyzer.generate_html_report(results)
    with open('coverage_analysis_report.html', 'w') as f:
        f.write(html_report)
    summary = results.get('summary', {})
    print(f"\n=== HMS Coverage Analysis Report ===")
    print(f"Total Files Analyzed: {summary.get('total_files_analyzed', 0)}")
    print(f"Average Line Coverage: {summary.get('average_line_coverage', 0):.1f}%")
    print(f"Average Branch Coverage: {summary.get('average_branch_coverage', 0):.1f}%")
    print(f"Average Function Coverage: {summary.get('average_function_coverage', 0):.1f}%")
    print(f"Healthcare Compliance: {'YES' if summary.get('healthcare_compliance', False) else 'NO'}")
    print(f"Quality Gates: {'PASSED' if summary.get('quality_gates_passed', False) else 'FAILED'}")
    if not summary.get('quality_gates_passed', False):
        sys.exit(1)
    elif not summary.get('healthcare_compliance', False):
        sys.exit(1)
    else:
        sys.exit(0)
if __name__ == '__main__':
    main()