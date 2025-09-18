import ast
import os
import sys
import subprocess
import json
import yaml
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('complexity_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
class ComplexityLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    NEEDS_IMPROVEMENT = "needs_improvement"
    POOR = "poor"
    CRITICAL = "critical"
@dataclass
class ComplexityMetrics:
    file_path: str
    function_name: Optional[str] = None
    nloc: int = 0  
    ccn: int = 0   
    ccn_max: int = 0  
    token_count: int = 0
    parameter_count: int = 0
    length: int = 0
    difficulty: float = 0.0
    volume: float = 0.0
    effort: float = 0.0
    bugs: float = 0.0
    time: float = 0.0
    maintainability_index: float = 0.0
    halstead_volume: float = 0.0
    halstead_difficulty: float = 0.0
    halstead_effort: float = 0.0
    halstead_bugs: float = 0.0
    halstead_time: float = 0.0
    mi_raw: float = 0.0
    mi_visual: float = 0.0
    mi_maintainability: float = 0.0
    def get_complexity_level(self) -> ComplexityLevel:
        if self.ccn <= 5 and self.maintainability_index >= 85:
            return ComplexityLevel.EXCELLENT
        elif self.ccn <= 10 and self.maintainability_index >= 70:
            return ComplexityLevel.GOOD
        elif self.ccn <= 15 and self.maintainability_index >= 60:
            return ComplexityLevel.ACCEPTABLE
        elif self.ccn <= 20 and self.maintainability_index >= 50:
            return ComplexityLevel.NEEDS_IMPROVEMENT
        elif self.ccn <= 25:
            return ComplexityLevel.POOR
        else:
            return ComplexityLevel.CRITICAL
class ComplexityAnalyzer:
    def __init__(self, root_dir: str = None):
        self.root_dir = root_dir or os.getcwd()
        self.excluded_dirs = [
            'node_modules', '.venv', 'venv', 'env', '__pycache__',
            'migrations', 'static', 'media', 'build', 'dist',
            'coverage', 'tests', 'test', 'spec'
        ]
        self.excluded_files = [
            '__init__.py', 'conftest.py', 'fixtures.py'
        ]
        self.complexity_results: List[ComplexityMetrics] = []
        self.thresholds = {
            'max_cyclomatic_complexity': 10,
            'max_function_length': 50,
            'max_parameter_count': 5,
            'max_file_length': 500,
            'min_maintainability_index': 70,
            'max_halstead_volume': 1000,
            'max_halstead_difficulty': 15,
            'max_halstead_effort': 15000
        }
    def should_analyze_file(self, file_path: str) -> bool:
        path = Path(file_path)
        for excluded_dir in self.excluded_dirs:
            if excluded_dir in path.parts:
                return False
        if path.name in self.excluded_files:
            return False
        return path.suffix == '.py'
    def run_lizard_analysis(self) -> List[Dict[str, Any]]:
        logger.info("Running Lizard complexity analysis...")
        cmd = [
            'lizard',
            '-w', str(self.thresholds['max_cyclomatic_complexity']),
            '-l', 'python',
            '--length', str(self.thresholds['max_function_length']),
            '--arguments', str(self.thresholds['max_parameter_count']),
            '--extension', 'py',
            '--json',
            self.root_dir
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"Lizard analysis failed: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Lizard output: {e}")
            return []
    def run_radon_analysis(self) -> Dict[str, Any]:
        logger.info("Running Radon complexity analysis...")
        radon_results = {}
        cc_cmd = ['radon', 'cc', self.root_dir, '-a', '-nb', '-j']
        try:
            result = subprocess.run(cc_cmd, capture_output=True, text=True, check=True)
            radon_results['cyclomatic_complexity'] = json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error(f"Radon cyclomatic complexity analysis failed: {e}")
            radon_results['cyclomatic_complexity'] = {}
        mi_cmd = ['radon', 'mi', self.root_dir, '-j']
        try:
            result = subprocess.run(mi_cmd, capture_output=True, text=True, check=True)
            radon_results['maintainability_index'] = json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error(f"Radon maintainability index analysis failed: {e}")
            radon_results['maintainability_index'] = {}
        raw_cmd = ['radon', 'raw', self.root_dir, '-j']
        try:
            result = subprocess.run(raw_cmd, capture_output=True, text=True, check=True)
            radon_results['raw_metrics'] = json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error(f"Radon raw metrics analysis failed: {e}")
            radon_results['raw_metrics'] = {}
        return radon_results
    def analyze_halstead_metrics(self, file_path: str) -> Dict[str, float]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            tree = ast.parse(source_code)
            operators = set()
            operands = set()
            total_operators = 0
            total_operands = 0
            for node in ast.walk(tree):
                if isinstance(node, (ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare)):
                    operators.add(type(node).__name__)
                    total_operators += 1
                elif isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                    operators.add(type(node).__name__)
                    total_operators += 1
                if isinstance(node, ast.Name):
                    operands.add(node.id)
                    total_operands += 1
                elif isinstance(node, ast.Constant):
                    operands.add(str(node.value))
                    total_operands += 1
            n1 = len(operators)  
            n2 = len(operands)   
            N1 = total_operators  
            N2 = total_operands   
            if n1 > 0 and n2 > 0:
                N = N1 + N2
                n = n1 + n2
                volume = N * (n.bit_length() / (2 ** 0.5)) if n > 0 else 0
                difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
                effort = difficulty * volume
                time = effort / 18
                bugs = volume / 3000
                return {
                    'halstead_volume': volume,
                    'halstead_difficulty': difficulty,
                    'halstead_effort': effort,
                    'halstead_time': time,
                    'halstead_bugs': bugs,
                    'unique_operators': n1,
                    'unique_operands': n2,
                    'total_operators': N1,
                    'total_operands': N2
                }
            else:
                return {
                    'halstead_volume': 0,
                    'halstead_difficulty': 0,
                    'halstead_effort': 0,
                    'halstead_time': 0,
                    'halstead_bugs': 0,
                    'unique_operators': 0,
                    'unique_operands': 0,
                    'total_operators': 0,
                    'total_operands': 0
                }
        except Exception as e:
            logger.error(f"Error analyzing Halstead metrics for {file_path}: {e}")
            return {
                'halstead_volume': 0,
                'halstead_difficulty': 0,
                'halstead_effort': 0,
                'halstead_time': 0,
                'halstead_bugs': 0,
                'unique_operators': 0,
                'unique_operands': 0,
                'total_operators': 0,
                'total_operands': 0
            }
    def analyze_file_complexity(self, file_path: str) -> List[ComplexityMetrics]:
        metrics_list = []
        try:
            halstead_metrics = self.analyze_halstead_metrics(file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            tree = ast.parse(source_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    lines = source_code.split('\n')
                    start_line = node.lineno - 1
                    end_line = node.end_lineno if node.end_lineno else start_line + 1
                    function_lines = lines[start_line:end_line]
                    nloc = len([line for line in function_lines if line.strip() and not line.strip().startswith('
                    parameter_count = len(node.args.args)
                    ccn = 1  
                    for child in ast.walk(node):
                        if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                            ccn += 1
                        elif isinstance(child, ast.BoolOp):
                            ccn += len(child.values) - 1
                    maintainability_index = max(0, 171 - 5.2 * math.log(ccn) - 0.23 * math.log(nloc) - 16.2 * math.log(parameter_count))
                    metrics = ComplexityMetrics(
                        file_path=file_path,
                        function_name=node.name,
                        nloc=nloc,
                        ccn=ccn,
                        parameter_count=parameter_count,
                        length=len(function_lines),
                        maintainability_index=maintainability_index,
                        **halstead_metrics
                    )
                    metrics_list.append(metrics)
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
        return metrics_list
    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        logger.info("Starting comprehensive complexity analysis...")
        results = {
            'summary': {},
            'lizard_results': {},
            'radon_results': {},
            'file_results': [],
            'healthcare_compliance': {},
            'recommendations': []
        }
        lizard_results = self.run_lizard_analysis()
        results['lizard_results'] = lizard_results
        radon_results = self.run_radon_analysis()
        results['radon_results'] = radon_results
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]
            for file in files:
                file_path = os.path.join(root, file)
                if self.should_analyze_file(file_path):
                    file_metrics = self.analyze_file_complexity(file_path)
                    if file_metrics:
                        results['file_results'].extend(file_metrics)
        if results['file_results']:
            self.calculate_summary_statistics(results)
        self.check_healthcare_compliance(results)
        self.generate_recommendations(results)
        return results
    def calculate_summary_statistics(self, results: Dict[str, Any]):
        metrics = results['file_results']
        if not metrics:
            return
        total_functions = len(metrics)
        total_nloc = sum(m.nloc for m in metrics)
        avg_nloc = total_nloc / total_functions if total_functions > 0 else 0
        avg_ccn = sum(m.ccn for m in metrics) / total_functions if total_functions > 0 else 0
        avg_maintainability = sum(m.maintainability_index for m in metrics) / total_functions if total_functions > 0 else 0
        complexity_distribution = {}
        for metric in metrics:
            level = metric.get_complexity_level()
            complexity_distribution[level.value] = complexity_distribution.get(level.value, 0) + 1
        violations = {
            'cyclomatic_complexity': sum(1 for m in metrics if m.ccn > self.thresholds['max_cyclomatic_complexity']),
            'function_length': sum(1 for m in metrics if m.length > self.thresholds['max_function_length']),
            'parameter_count': sum(1 for m in metrics if m.parameter_count > self.thresholds['max_parameter_count']),
            'maintainability_index': sum(1 for m in metrics if m.maintainability_index < self.thresholds['min_maintainability_index']),
        }
        results['summary'] = {
            'total_functions': total_functions,
            'total_lines_of_code': total_nloc,
            'average_function_length': avg_nloc,
            'average_cyclomatic_complexity': avg_ccn,
            'average_maintainability_index': avg_maintainability,
            'complexity_distribution': complexity_distribution,
            'threshold_violations': violations,
            'overall_quality_score': self.calculate_quality_score(metrics)
        }
    def calculate_quality_score(self, metrics: List[ComplexityMetrics]) -> float:
        if not metrics:
            return 0.0
        score = 100.0
        high_complexity = sum(1 for m in metrics if m.ccn > 15)
        score -= (high_complexity / len(metrics)) * 20
        low_maintainability = sum(1 for m in metrics if m.maintainability_index < 60)
        score -= (low_maintainability / len(metrics)) * 30
        long_functions = sum(1 for m in metrics if m.length > 100)
        score -= (long_functions / len(metrics)) * 15
        many_parameters = sum(1 for m in metrics if m.parameter_count > 7)
        score -= (many_parameters / len(metrics)) * 10
        return max(0, score)
    def check_healthcare_compliance(self, results: Dict[str, Any]):
        compliance = {
            'patient_data_functions': [],
            'security_critical_functions': [],
            'compliance_violations': [],
            'risk_assessment': {}
        }
        patient_data_keywords = ['patient', 'medical', 'health', 'clinical', 'diagnosis', 'treatment']
        security_keywords = ['auth', 'encrypt', 'decrypt', 'token', 'password', 'secure']
        for metric in results['file_results']:
            function_name = metric.function_name or ''
            file_path = metric.file_path
            if any(keyword in function_name.lower() for keyword in patient_data_keywords):
                compliance['patient_data_functions'].append({
                    'function': function_name,
                    'file': file_path,
                    'complexity': metric.ccn,
                    'maintainability': metric.maintainability_index
                })
                if metric.ccn > 8:
                    compliance['compliance_violations'].append({
                        'type': 'patient_data_complexity',
                        'function': function_name,
                        'file': file_path,
                        'severity': 'high' if metric.ccn > 15 else 'medium',
                        'message': f"Patient data function has high complexity: {metric.ccn}"
                    })
            if any(keyword in function_name.lower() for keyword in security_keywords):
                compliance['security_critical_functions'].append({
                    'function': function_name,
                    'file': file_path,
                    'complexity': metric.ccn,
                    'maintainability': metric.maintainability_index
                })
                if metric.ccn > 5:
                    compliance['compliance_violations'].append({
                        'type': 'security_complexity',
                        'function': function_name,
                        'file': file_path,
                        'severity': 'critical' if metric.ccn > 10 else 'high',
                        'message': f"Security function has excessive complexity: {metric.ccn}"
                    })
        total_violations = len(compliance['compliance_violations'])
        if total_violations == 0:
            risk_level = 'low'
        elif total_violations <= 5:
            risk_level = 'medium'
        elif total_violations <= 10:
            risk_level = 'high'
        else:
            risk_level = 'critical'
        compliance['risk_assessment'] = {
            'risk_level': risk_level,
            'total_violations': total_violations,
            'patient_data_violations': len([v for v in compliance['compliance_violations'] if v['type'] == 'patient_data_complexity']),
            'security_violations': len([v for v in compliance['compliance_violations'] if v['type'] == 'security_complexity']),
            'recommendation': self.get_risk_recommendation(risk_level)
        }
        results['healthcare_compliance'] = compliance
    def get_risk_recommendation(self, risk_level: str) -> str:
        recommendations = {
            'low': 'System meets healthcare complexity standards. Continue monitoring.',
            'medium': 'Some complexity issues detected. Review and refactor critical functions.',
            'high': 'Significant complexity issues. Immediate refactoring required for healthcare compliance.',
            'critical': 'Critical complexity violations. System may not meet healthcare regulatory requirements.'
        }
        return recommendations.get(risk_level, 'Unknown risk level.')
    def generate_recommendations(self, results: Dict[str, Any]):
        recommendations = []
        summary = results.get('summary', {})
        violations = summary.get('threshold_violations', {})
        if violations.get('cyclomatic_complexity', 0) > 0:
            recommendations.append({
                'priority': 'high',
                'category': 'complexity',
                'title': 'Reduce Cyclomatic Complexity',
                'description': f"Found {violations['cyclomatic_complexity']} functions with cyclomatic complexity > {self.thresholds['max_cyclomatic_complexity']}",
                'action': 'Refactor complex functions into smaller, more manageable functions'
            })
        if violations.get('function_length', 0) > 0:
            recommendations.append({
                'priority': 'medium',
                'category': 'maintainability',
                'title': 'Reduce Function Length',
                'description': f"Found {violations['function_length']} functions longer than {self.thresholds['max_function_length']} lines",
                'action': 'Break down large functions into smaller, focused functions'
            })
        if violations.get('parameter_count', 0) > 0:
            recommendations.append({
                'priority': 'medium',
                'category': 'design',
                'title': 'Reduce Parameter Count',
                'description': f"Found {violations['parameter_count']} functions with > {self.thresholds['max_parameter_count']} parameters",
                'action': 'Use parameter objects or data classes to reduce parameter count'
            })
        if violations.get('maintainability_index', 0) > 0:
            recommendations.append({
                'priority': 'high',
                'category': 'maintainability',
                'title': 'Improve Maintainability',
                'description': f"Found {violations['maintainability_index']} functions with maintainability index < {self.thresholds['min_maintainability_index']}",
                'action': 'Refactor functions to improve maintainability and reduce technical debt'
            })
        compliance = results.get('healthcare_compliance', {})
        if compliance.get('risk_assessment', {}).get('risk_level') in ['high', 'critical']:
            recommendations.append({
                'priority': 'critical',
                'category': 'healthcare_compliance',
                'title': 'Healthcare Compliance Issues',
                'description': 'Critical complexity violations in patient data or security functions',
                'action': 'Immediate refactoring required for healthcare regulatory compliance'
            })
        results['recommendations'] = recommendations
    def generate_report(self, results: Dict[str, Any], output_format: str = 'json') -> str:
        if output_format == 'json':
            return json.dumps(results, indent=2, default=str)
        elif output_format == 'html':
            return self.generate_html_report(results)
        else:
            return str(results)
    def generate_html_report(self, results: Dict[str, Any]) -> str:
        html = f
        return html
    def _generate_recommendations_html(self, recommendations: List[Dict]) -> str:
        if not recommendations:
            return "<p>No recommendations found.</p>"
        html = ""
        for rec in recommendations:
            html += f
        return html
    def _generate_detailed_results_html(self, results: List[ComplexityMetrics]) -> str:
        if not results:
            return "<p>No results found.</p>"
        html = 
        for metric in results[:50]:  
            level = metric.get_complexity_level().value
            html += f
        html += 
        if len(results) > 50:
            html += f"<p>Showing 50 of {len(results)} results. See JSON report for complete results.</p>"
        return html
def main():
    import math
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = os.getcwd()
    analyzer = ComplexityAnalyzer(root_dir)
    results = analyzer.run_comprehensive_analysis()
    with open('complexity_analysis_report.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    html_report = analyzer.generate_html_report(results)
    with open('complexity_analysis_report.html', 'w') as f:
        f.write(html_report)
    summary = results.get('summary', {})
    print(f"\n=== HMS Complexity Analysis Report ===")
    print(f"Total Functions: {summary.get('total_functions', 0)}")
    print(f"Average Cyclomatic Complexity: {summary.get('average_cyclomatic_complexity', 0):.2f}")
    print(f"Average Maintainability Index: {summary.get('average_maintainability_index', 0):.2f}")
    print(f"Overall Quality Score: {summary.get('overall_quality_score', 0):.1f}%")
    compliance = results.get('healthcare_compliance', {}).get('risk_assessment', {})
    print(f"Healthcare Compliance Risk: {compliance.get('risk_level', 'unknown').upper()}")
    print(f"\nReports saved:")
    print(f"- complexity_analysis_report.json")
    print(f"- complexity_analysis_report.html")
    if summary.get('overall_quality_score', 0) < 70:
        sys.exit(1)
    elif compliance.get('risk_level') in ['high', 'critical']:
        sys.exit(1)
    else:
        sys.exit(0)
if __name__ == '__main__':
    main()