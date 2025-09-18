import json
import os
import ast
import subprocess
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from pathlib import Path
class ComplexityAnalyzer:
    def __init__(self):
        self.complexity_thresholds = {
            'cyclomatic_complexity': 10,
            'maintainability_index': 20,
            'halstead_volume': 1000,
            'loc_per_function': 50,
            'parameters_per_function': 5
        }
        self.severity_levels = {
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        }
    def run_radon_analysis(self) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                ['radon', 'cc', '.', '-a', '-nb', '-j'],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return {}
    def run_lizard_analysis(self) -> pd.DataFrame:
        try:
            result = subprocess.run(
                ['lizard', '.', '--csv'],
                capture_output=True,
                text=True,
                check=True
            )
            from io import StringIO
            return pd.read_csv(StringIO(result.stdout))
        except subprocess.CalledProcessError:
            return pd.DataFrame()
    def analyze_function_complexity(self, file_path: str) -> List[Dict[str, Any]]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content)
            analyzer = FunctionComplexityAnalyzer()
            analyzer.visit(tree)
            return analyzer.results
        except (SyntaxError, FileNotFoundError, UnicodeDecodeError):
            return []
    def calculate_maintainability_index(self, file_path: str) -> float:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            lines = content.split('\n')
            loc = len([line for line in lines if line.strip() and not line.strip().startswith('
            operators = len([char for char in content if char in '+-*/%=<>!&|^~'])
            operands = len([word for word in content.split() if word.isalnum()])
            if loc == 0:
                return 0
            mi = 171 - 5.2 * np.log(max(1, operators + operands)) - 0.23 * np.log(max(1, loc))
            return max(0, min(100, mi))
        except (FileNotFoundError, UnicodeDecodeError):
            return 0
    def analyze_codebase_complexity(self) -> Dict[str, Any]:
        print("Analyzing codebase complexity...")
        results = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'files_analyzed': 0,
            'total_functions': 0,
            'complexity_metrics': {},
            'high_complexity_functions': [],
            'maintainability_issues': [],
            'recommendations': []
        }
        python_files = []
        for root, dirs, files in os.walk('.'):
            skip_dirs = ['.git', 'venv', '__pycache__', 'node_modules', '.pytest_cache']
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        print(f"Found {len(python_files)} Python files to analyze")
        for file_path in python_files:
            try:
                functions = self.analyze_function_complexity(file_path)
                results['total_functions'] += len(functions)
                mi = self.calculate_maintainability_index(file_path)
                if mi < self.complexity_thresholds['maintainability_index']:
                    results['maintainability_issues'].append({
                        'file': file_path,
                        'maintainability_index': mi,
                        'severity': self.get_severity_level(mi, 'maintainability_index')
                    })
                for func in functions:
                    complexity = func.get('cyclomatic_complexity', 0)
                    if complexity > self.complexity_thresholds['cyclomatic_complexity']:
                        results['high_complexity_functions'].append({
                            'file': file_path,
                            'function': func.get('name', 'unknown'),
                            'complexity': complexity,
                            'line': func.get('line', 0),
                            'severity': self.get_severity_level(complexity, 'cyclomatic_complexity')
                        })
                results['files_analyzed'] += 1
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
        radon_results = self.run_radon_analysis()
        if radon_results:
            results['radon_analysis'] = radon_results
        lizard_df = self.run_lizard_analysis()
        if not lizard_df.empty:
            results['lizard_analysis'] = lizard_df.to_dict('records')
        results['complexity_metrics'] = self.calculate_aggregate_metrics(results)
        results['recommendations'] = self.generate_recommendations(results)
        return results
    def get_severity_level(self, value: float, metric_type: str) -> str:
        thresholds = {
            'cyclomatic_complexity': [10, 20, 30],
            'maintainability_index': [40, 20, 10],
            'halstead_volume': [1000, 2000, 3000],
            'loc_per_function': [50, 100, 150],
            'parameters_per_function': [5, 8, 12]
        }
        if metric_type in thresholds:
            levels = thresholds[metric_type]
            if metric_type == 'maintainability_index':
                if value < levels[2]:
                    return 'critical'
                elif value < levels[1]:
                    return 'high'
                elif value < levels[0]:
                    return 'medium'
                else:
                    return 'low'
            else:
                if value > levels[2]:
                    return 'critical'
                elif value > levels[1]:
                    return 'high'
                elif value > levels[0]:
                    return 'medium'
                else:
                    return 'low'
        return 'low'
    def calculate_aggregate_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        metrics = {
            'total_files': results['files_analyzed'],
            'total_functions': results['total_functions'],
            'high_complexity_functions': len(results['high_complexity_functions']),
            'maintainability_issues': len(results['maintainability_issues']),
            'average_complexity': 0,
            'complexity_distribution': {},
            'maintainability_distribution': {}
        }
        if results['high_complexity_functions']:
            avg_complexity = np.mean([f['complexity'] for f in results['high_complexity_functions']])
            metrics['average_complexity'] = avg_complexity
        complexity_counts = {}
        for func in results['high_complexity_functions']:
            severity = func['severity']
            complexity_counts[severity] = complexity_counts.get(severity, 0) + 1
        metrics['complexity_distribution'] = complexity_counts
        maintainability_counts = {}
        for issue in results['maintainability_issues']:
            severity = issue['severity']
            maintainability_counts[severity] = maintainability_counts.get(severity, 0) + 1
        metrics['maintainability_distribution'] = maintainability_counts
        return metrics
    def generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        recommendations = []
        critical_functions = [f for f in results['high_complexity_functions'] if f['severity'] == 'critical']
        if critical_functions:
            recommendations.append(f"🔴 CRITICAL: {len(critical_functions)} functions have critical complexity levels")
            recommendations.append("   - Refactor critical functions immediately")
            recommendations.append("   - Break down complex functions into smaller, focused functions")
        high_functions = [f for f in results['high_complexity_functions'] if f['severity'] == 'high']
        if high_functions:
            recommendations.append(f"🟠 HIGH: {len(high_functions)} functions have high complexity levels")
            recommendations.append("   - Consider refactoring high complexity functions")
            recommendations.append("   - Apply design patterns to simplify complex logic")
        critical_maintainability = [i for i in results['maintainability_issues'] if i['severity'] == 'critical']
        if critical_maintainability:
            recommendations.append(f"🔴 CRITICAL: {len(critical_maintainability)} files have critical maintainability issues")
            recommendations.append("   - Refactor files with poor maintainability")
            recommendations.append("   - Improve code organization and documentation")
        if results['high_complexity_functions']:
            recommendations.append("📊 General Recommendations:")
            recommendations.append("   - Implement code review process focusing on complexity")
            recommendations.append("   - Use automated complexity tools in CI/CD pipeline")
            recommendations.append("   - Consider extracting complex logic into separate modules")
            recommendations.append("   - Add comprehensive documentation for complex functions")
        if results['complexity_metrics']['average_complexity'] > 20:
            recommendations.append("⚠️  High average complexity detected - consider architectural refactoring")
        return recommendations
    def generate_html_report(self, results: Dict[str, Any]) -> str:
        html_template = 
        def generate_distribution_rows(distribution):
            rows = ""
            for severity, count in distribution.items():
                rows += f
            return rows
        def generate_complexity_rows(functions):
            rows = ""
            for func in functions[:20]:  
                rows += f
            return rows
        def generate_maintainability_rows(issues):
            rows = ""
            for issue in issues[:20]:  
                rows += f
            return rows
        def generate_recommendation_items(recommendations):
            return "".join([f"<li>{rec}</li>" for rec in recommendations])
        metrics = results['complexity_metrics']
        return html_template.format(
            timestamp=results['timestamp'],
            total_files=metrics['total_files'],
            total_functions=metrics['total_functions'],
            high_complexity_functions=metrics['high_complexity_functions'],
            maintainability_issues=metrics['maintainability_issues'],
            average_complexity=metrics['average_complexity'],
            complexity_distribution_rows=generate_distribution_rows(metrics['complexity_distribution']),
            maintainability_distribution_rows=generate_distribution_rows(metrics['maintainability_distribution']),
            complexity_function_rows=generate_complexity_rows(results['high_complexity_functions']),
            maintainability_issue_rows=generate_maintainability_rows(results['maintainability_issues']),
            recommendation_items=generate_recommendation_items(results['recommendations'])
        )
    def save_reports(self, results: Dict[str, Any]):
        with open('complexity-analysis.json', 'w') as f:
            json.dump(results, f, indent=2)
        html_content = self.generate_html_report(results)
        with open('complexity-analysis.html', 'w') as f:
            f.write(html_content)
        print("Complexity analysis reports saved:")
        print("- complexity-analysis.json")
        print("- complexity-analysis.html")
    def run_analysis(self):
        print("Starting code complexity analysis...")
        results = self.analyze_codebase_complexity()
        self.save_reports(results)
        print("\n📊 Complexity Analysis Summary:")
        print(f"Files analyzed: {results['files_analyzed']}")
        print(f"Total functions: {results['total_functions']}")
        print(f"High complexity functions: {len(results['high_complexity_functions'])}")
        print(f"Maintainability issues: {len(results['maintainability_issues'])}")
        if results['high_complexity_functions']:
            print(f"\n🔴 Top 5 most complex functions:")
            sorted_functions = sorted(results['high_complexity_functions'],
                                    key=lambda x: x['complexity'], reverse=True)
            for i, func in enumerate(sorted_functions[:5], 1):
                print(f"  {i}. {func['function']} in {func['file']} (complexity: {func['complexity']})")
        print(f"\n📝 Recommendations:")
        for rec in results['recommendations'][:5]:  
            print(f"  {rec}")
        return results
class FunctionComplexityAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.results = []
        self.current_function = None
        self.complexity = 1
    def visit_FunctionDef(self, node):
        self.current_function = node.name
        self.complexity = 1  
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                self.complexity += 1
            elif isinstance(child, ast.BoolOp):
                self.complexity += len(child.values) - 1
        param_count = len(node.args.args)
        self.results.append({
            'name': node.name,
            'line': node.lineno,
            'cyclomatic_complexity': self.complexity,
            'parameters': param_count,
            'loc': self.count_lines(node)
        })
        self.generic_visit(node)
    def count_lines(self, node):
        if hasattr(node, 'end_lineno'):
            return node.end_lineno - node.lineno + 1
        return 0
def main():
    analyzer = ComplexityAnalyzer()
    results = analyzer.run_analysis()
    critical_functions = [f for f in results['high_complexity_functions'] if f['severity'] == 'critical']
    critical_maintainability = [i for i in results['maintainability_issues'] if i['severity'] == 'critical']
    if critical_functions or critical_maintainability:
        print("🔴 Critical complexity issues found")
        exit(1)
    else:
        print("✅ No critical complexity issues found")
        exit(0)
if __name__ == "__main__":
    main()