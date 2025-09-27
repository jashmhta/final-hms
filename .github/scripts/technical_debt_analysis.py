"""
technical_debt_analysis module
"""

import ast
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import git
import numpy as np
import pandas as pd
from git.repo import Repo


class TechnicalDebtAnalyzer:
    def __init__(self):
        self.debt_categories = {
            "code_complexity": {"weight": 0.3, "threshold": 20},
            "code_duplication": {"weight": 0.25, "threshold": 15},
            "code_smells": {"weight": 0.2, "threshold": 10},
            "test_coverage": {"weight": 0.15, "threshold": 50},
            "documentation": {"weight": 0.1, "threshold": 30},
        }
        self.debt_indicators = {
            "todo_comments": r"#\s*TODO|# FIXME|# XXX",
            "long_functions": r"def\s+\w+\([^)]*\):\s*.*(?:\n\s*.*){50,}",
            "long_classes": r"class\s+\w+.*:\s*.*(?:\n\s*.*){200,}",
            "magic_numbers": r"\b\d{4,}\b(?!\.0)",
            "deep_nesting": r"(?:if|for|while|try).*\n\s*(?:if|for|while|try).*\n\s*(?:if|for|while|try)",
            "large_files": r".*",
            "dead_code": r"import\s+\w+.*\n.*",
        }

    def analyze_code_duplication(self) -> Dict[str, Any]:
        print("Analyzing code duplication...")
        python_files = []
        for root, dirs, files in os.walk("."):
            skip_dirs = [".git", "venv", "__pycache__", "node_modules", ".pytest_cache"]
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))
        duplication_results = {
            "files_analyzed": len(python_files),
            "duplicated_blocks": [],
            "duplication_percentage": 0,
            "total_lines_duplicated": 0,
            "most_duplicated_files": [],
        }
        code_blocks = {}
        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                blocks = self.extract_code_blocks(lines, file_path)
                for block in blocks:
                    normalized_code = self.normalize_code(block["code"])
                    code_hash = hash(normalized_code)
                    if code_hash in code_blocks:
                        duplication_results["duplicated_blocks"].append(
                            {
                                "hash": code_hash,
                                "files": [code_blocks[code_hash]["file"], file_path],
                                "lines": len(block["code"].split("\n")),
                                "similarity": self.calculate_similarity(
                                    normalized_code,
                                    code_blocks[code_hash]["normalized"],
                                ),
                            }
                        )
                    else:
                        code_blocks[code_hash] = {
                            "file": file_path,
                            "normalized": normalized_code,
                            "code": block["code"],
                        }
            except (UnicodeDecodeError, PermissionError):
                continue
        if duplication_results["duplicated_blocks"]:
            duplication_results["total_lines_duplicated"] = sum(
                block["lines"] for block in duplication_results["duplicated_blocks"]
            )
            total_lines = sum(self.count_lines_in_file(f) for f in python_files)
            if total_lines > 0:
                duplication_results["duplication_percentage"] = (
                    duplication_results["total_lines_duplicated"] / total_lines
                ) * 100
            file_duplication_count = {}
            for block in duplication_results["duplicated_blocks"]:
                for file_path in block["files"]:
                    file_duplication_count[file_path] = (
                        file_duplication_count.get(file_path, 0) + 1
                    )
            duplication_results["most_duplicated_files"] = sorted(
                file_duplication_count.items(), key=lambda x: x[1], reverse=True
            )[:10]
        return duplication_results

    def extract_code_blocks(
        self, lines: List[str], file_path: str
    ) -> List[Dict[str, Any]]:
        blocks = []
        current_block = []
        current_line_num = 0
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if stripped_line.startswith(("def ", "class ")):
                if current_block:
                    blocks.append(
                        {
                            "file": file_path,
                            "line": current_line_num,
                            "code": "".join(current_block),
                        }
                    )
                current_block = [line]
                current_line_num = i + 1
            elif stripped_line and not stripped_line.startswith("#"):
                current_block.append(line)
        if current_block:
            blocks.append(
                {
                    "file": file_path,
                    "line": current_line_num,
                    "code": "".join(current_block),
                }
            )
        return blocks

    def normalize_code(self, code: str) -> str:
        code = re.sub(r"#.*", "", code)
        code = re.sub(r"\s+", " ", code)
        code = re.sub(r"\n\s*\n", "\n", code)
        return code.strip().lower()

    def calculate_similarity(self, code1: str, code2: str) -> float:
        words1 = set(code1.split())
        words2 = set(code2.split())
        if not words1 and not words2:
            return 1.0
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        return intersection / union if union > 0 else 0.0

    def count_lines_in_file(self, file_path: str) -> int:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return len(f.readlines())
        except (UnicodeDecodeError, PermissionError):
            return 0

    def analyze_todo_comments(self) -> Dict[str, Any]:
        print("Analyzing TODO comments...")
        todo_results = {
            "total_todos": 0,
            "todos_by_type": {},
            "todos_by_file": {},
            "todos_by_age": {},
            "oldest_todos": [],
        }
        for root, dirs, files in os.walk("."):
            skip_dirs = [".git", "venv", "__pycache__", "node_modules", ".pytest_cache"]
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            lines = f.readlines()
                        for line_num, line in enumerate(lines, 1):
                            if re.search(
                                self.debt_indicators["todo_comments"],
                                line,
                                re.IGNORECASE,
                            ):
                                todo_type = self.classify_todo(line)
                                todo_results["total_todos"] += 1
                                todo_results["todos_by_type"][todo_type] = (
                                    todo_results["todos_by_type"].get(todo_type, 0) + 1
                                )
                                todo_results["todos_by_file"][file_path] = (
                                    todo_results["todos_by_file"].get(file_path, 0) + 1
                                )
                                todo_info = {
                                    "file": file_path,
                                    "line": line_num,
                                    "type": todo_type,
                                    "text": line.strip(),
                                    "age_days": self.estimate_todo_age(
                                        file_path, line_num
                                    ),
                                }
                                if todo_info["age_days"] is not None:
                                    todo_results["todos_by_age"][todo_type] = (
                                        todo_results["todos_by_age"].get(todo_type, [])
                                        + [todo_info["age_days"]]
                                    )
                                todo_results["oldest_todos"].append(todo_info)
                    except (UnicodeDecodeError, PermissionError):
                        continue
        todo_results["oldest_todos"] = sorted(
            todo_results["oldest_todos"],
            key=lambda x: x.get("age_days", 0),
            reverse=True,
        )[:20]
        return todo_results

    def classify_todo(self, line: str) -> str:
        line = line.lower()
        if "fixme" in line:
            return "FIXME"
        elif "hack" in line:
            return "HACK"
        elif "xxx" in line:
            return "XXX"
        else:
            return "TODO"

    def estimate_todo_age(self, file_path: str, line_num: int) -> Optional[int]:
        try:
            repo = Repo(".")
            commits = list(repo.iter_commits(paths=file_path))
            if not commits:
                return None
            for commit in commits:
                try:
                    file_content = (
                        commit.tree[file_path].data_stream.read().decode("utf-8")
                    )
                    lines = file_content.split("\n")
                    if line_num <= len(lines) and re.search(
                        self.debt_indicators["todo_comments"],
                        lines[line_num - 1],
                        re.IGNORECASE,
                    ):
                        commit_date = datetime.fromtimestamp(commit.committed_date)
                        age_days = (datetime.now() - commit_date).days
                        return age_days
                except Exception:
                    continue
            return None
        except Exception:
            return None

    def analyze_code_smells(self) -> Dict[str, Any]:
        print("Analyzing code smells...")
        smell_results = {
            "total_smells": 0,
            "smells_by_type": {},
            "smells_by_file": {},
            "smell_locations": [],
        }
        for root, dirs, files in os.walk("."):
            skip_dirs = [".git", "venv", "__pycache__", "node_modules", ".pytest_cache"]
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        file_smells = self.analyze_file_code_smells(file_path, content)
                        for smell in file_smells:
                            smell_results["total_smells"] += 1
                            smell_type = smell["type"]
                            smell_results["smells_by_type"][smell_type] = (
                                smell_results["smells_by_type"].get(smell_type, 0) + 1
                            )
                            smell_results["smells_by_file"][file_path] = (
                                smell_results["smells_by_file"].get(file_path, 0) + 1
                            )
                            smell_results["smell_locations"].append(smell)
                    except (UnicodeDecodeError, PermissionError):
                        continue
        return smell_results

    def analyze_file_code_smells(
        self, file_path: str, content: str
    ) -> List[Dict[str, Any]]:
        smells = []
        lines = content.split("\n")
        function_blocks = self.extract_function_blocks(content)
        for func_block in function_blocks:
            if len(func_block["lines"]) > 50:
                smells.append(
                    {
                        "type": "long_function",
                        "file": file_path,
                        "line": func_block["start_line"],
                        "description": f"Function '{func_block['name']}' is too long ({len(func_block['lines'])} lines)",
                        "severity": "medium",
                    }
                )
        for line_num, line in enumerate(lines, 1):
            magic_numbers = re.finditer(self.debt_indicators["magic_numbers"], line)
            for match in magic_numbers:
                if match.group() not in ["1000", "2000", "4096", "1024"]:
                    smells.append(
                        {
                            "type": "magic_number",
                            "file": file_path,
                            "line": line_num,
                            "description": f"Magic number found: {match.group()}",
                            "severity": "low",
                        }
                    )
        for line_num, line in enumerate(lines, 1):
            if re.search(self.debt_indicators["deep_nesting"], line):
                smells.append(
                    {
                        "type": "deep_nesting",
                        "file": file_path,
                        "line": line_num,
                        "description": "Deep nesting detected",
                        "severity": "medium",
                    }
                )
        return smells

    def extract_function_blocks(self, content: str) -> List[Dict[str, Any]]:
        blocks = []
        lines = content.split("\n")
        current_block = None
        for i, line in enumerate(lines):
            if line.strip().startswith("def "):
                if current_block:
                    blocks.append(current_block)
                func_name = re.search(r"def\s+(\w+)\s*\(", line)
                current_block = {
                    "name": func_name.group(1) if func_name else "unknown",
                    "start_line": i + 1,
                    "lines": [line],
                    "indent_level": len(line) - len(line.lstrip()),
                }
            elif current_block and line.strip():
                current_indent = len(line) - len(line.lstrip())
                if current_indent > current_block["indent_level"]:
                    current_block["lines"].append(line)
        if current_block:
            blocks.append(current_block)
        return blocks

    def analyze_test_coverage(self) -> Dict[str, Any]:
        print("Analyzing test coverage...")
        coverage_results = {
            "python_files": 0,
            "test_files": 0,
            "coverage_estimate": 0,
            "untested_files": [],
        }
        for root, dirs, files in os.walk("."):
            skip_dirs = [".git", "venv", "__pycache__", "node_modules", ".pytest_cache"]
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    coverage_results["python_files"] += 1
                    if "test" in file.lower() or file.startswith("test_"):
                        coverage_results["test_files"] += 1
                    elif self.is_main_module_file(file_path):
                        test_file = self.find_corresponding_test_file(file_path)
                        if not test_file:
                            coverage_results["untested_files"].append(file_path)
        if coverage_results["python_files"] > 0:
            main_files = (
                coverage_results["python_files"] - coverage_results["test_files"]
            )
            tested_files = main_files - len(coverage_results["untested_files"])
            coverage_results["coverage_estimate"] = (
                (tested_files / main_files) * 100 if main_files > 0 else 0
            )
        return coverage_results

    def is_main_module_file(self, file_path: str) -> bool:
        filename = os.path.basename(file_path)
        return not (
            filename.startswith("test_")
            or filename == "__init__.py"
            or "test" in filename.lower()
        )

    def find_corresponding_test_file(self, file_path: str) -> Optional[str]:
        dirname = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        base_name = filename[:-3]
        test_names = [
            f"test_{base_name}.py",
            f"{base_name}_test.py",
            f"tests/{base_name}_test.py",
            f"tests/test_{base_name}.py",
        ]
        for test_name in test_names:
            test_path = os.path.join(dirname, test_name)
            if os.path.exists(test_path):
                return test_path
        return None

    def calculate_debt_score(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        print("Calculating technical debt score...")
        debt_scores = {}
        dup_score = min(
            100, analysis_results["duplication"]["duplication_percentage"] * 2
        )
        debt_scores["code_duplication"] = dup_score
        todo_count = analysis_results["todo_comments"]["total_todos"]
        todo_score = min(100, todo_count * 5)
        debt_scores["todo_comments"] = todo_score
        smell_count = analysis_results["code_smells"]["total_smells"]
        smell_score = min(100, smell_count * 2)
        debt_scores["code_smells"] = smell_score
        coverage = analysis_results["test_coverage"]["coverage_estimate"]
        coverage_score = max(0, 100 - coverage)
        debt_scores["test_coverage"] = coverage_score
        total_score = 0
        total_weight = 0
        for category, weight_info in self.debt_categories.items():
            if category in debt_scores:
                total_score += debt_scores[category] * weight_info["weight"]
                total_weight += weight_info["weight"]
        if total_weight > 0:
            final_score = total_score / total_weight
        else:
            final_score = 0
        return {
            "category_scores": debt_scores,
            "total_score": final_score,
            "debt_level": self.get_debt_level(final_score),
            "recommendations": self.generate_debt_recommendations(
                debt_scores, analysis_results
            ),
        }

    def get_debt_level(self, score: float) -> str:
        if score >= 70:
            return "critical"
        elif score >= 50:
            return "high"
        elif score >= 30:
            return "medium"
        else:
            return "low"

    def generate_debt_recommendations(
        self, scores: Dict[str, float], results: Dict[str, Any]
    ) -> List[str]:
        recommendations = []
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        for category, score in sorted_scores:
            if score >= 50:
                if category == "code_duplication":
                    recommendations.append(
                        f"🔴 High code duplication ({results['duplication']['duplication_percentage']:.1f}%)"
                    )
                    recommendations.append(
                        "   - Extract common code into shared modules"
                    )
                    recommendations.append(
                        "   - Use inheritance or composition to reduce duplication"
                    )
                elif category == "todo_comments":
                    recommendations.append(
                        f"🔴 {results['todo_comments']['total_todos']} TODO/FIXME comments found"
                    )
                    recommendations.append(
                        "   - Address TODO comments, starting with oldest"
                    )
                    recommendations.append("   - Implement a TODO tracking system")
                elif category == "code_smells":
                    recommendations.append(
                        f"🔴 {results['code_smells']['total_smells']} code smells detected"
                    )
                    recommendations.append("   - Refactor code smells systematically")
                    recommendations.append(
                        "   - Use static analysis tools to prevent new smells"
                    )
                elif category == "test_coverage":
                    recommendations.append(
                        f"🔴 Low test coverage ({results['test_coverage']['coverage_estimate']:.1f}%)"
                    )
                    recommendations.append("   - Write unit tests for untested modules")
                    recommendations.append("   - Aim for at least 80% test coverage")
        if scores.get("total_score", 0) >= 50:
            recommendations.append("📊 General Recommendations:")
            recommendations.append("   - Schedule regular technical debt sprints")
            recommendations.append("   - Implement code review guidelines")
            recommendations.append("   - Use automated tools to monitor technical debt")
            recommendations.append("   - Document architectural decisions")
        return recommendations

    def generate_debt_report(self, results: Dict[str, Any]) -> str:
        debt_score = self.calculate_debt_score(results)
        report = {
            "timestamp": datetime.now().isoformat(),
            "analysis_results": results,
            "debt_score": debt_score,
            "summary": {
                "total_files_analyzed": results["python_files"],
                "total_todos": results["todo_comments"]["total_todos"],
                "total_code_smells": results["code_smells"]["total_smells"],
                "duplication_percentage": results["duplication"][
                    "duplication_percentage"
                ],
                "test_coverage": results["test_coverage"]["coverage_estimate"],
                "overall_debt_score": debt_score["total_score"],
                "debt_level": debt_score["debt_level"],
            },
        }
        return report

    def save_reports(self, report: Dict[str, Any]):
        with open("technical-debt-analysis.json", "w") as f:
            json.dump(report, f, indent=2)
        html_content = self.generate_html_report(report)
        with open("technical-debt-report.html", "w") as f:
            f.write(html_content)
        print("Technical debt reports saved:")
        print("- technical-debt-analysis.json")
        print("- technical-debt-report.html")

    def generate_html_report(self, report: Dict[str, Any]) -> str:
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Technical Debt Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .score { font-size: 24px; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .good { color: green; }
        .warning { color: orange; }
        .danger { color: red; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Technical Debt Analysis Report</h1>
        <p>Generated: {timestamp}</p>
        <div class="score">Overall Score: <span class="{score_color}">{overall_score}/100</span></div>
        <div>Debt Level: {debt_level}</div>
    </div>

    <h2>Summary</h2>
    <ul>
        <li>Total Files Analyzed: {total_files}</li>
        <li>TODO Comments: {total_todos}</li>
        <li>Code Smells: {total_code_smells}</li>
        <li>Code Duplication: {duplication_percentage}%</li>
        <li>Test Coverage: {test_coverage}%</li>
    </ul>

    <h2>Category Scores</h2>
    <table>
        <tr><th>Category</th><th>Score</th><th>Status</th></tr>
        {category_score_rows}
    </table>

    <h2>Oldest TODO Comments</h2>
    <table>
        <tr><th>File</th><th>Line</th><th>Age</th></tr>
        {todo_rows}
    </table>

    <h2>Most Duplicated Files</h2>
    <table>
        <tr><th>File</th><th>Duplications</th></tr>
        {duplication_rows}
    </table>

    <h2>Recommendations</h2>
    <ul>
        {recommendation_items}
    </ul>
</body>
</html>
"""

        def get_score_color(score):
            if score >= 70:
                return "green"
            elif score >= 50:
                return "yellow"
            elif score >= 30:
                return "orange"
            else:
                return "red"

        def generate_category_score_rows(scores):
            rows = ""
            for category, score in scores.items():
                color = get_score_color(score)
                status = (
                    "Critical"
                    if score >= 70
                    else "High" if score >= 50 else "Medium" if score >= 30 else "Good"
                )
                rows += f"<tr><td>{category}</td><td>{score}</td><td style='color:{color}'>{status}</td></tr>"
            return rows

        def generate_todo_rows(todos):
            rows = ""
            for todo in todos[:10]:
                age_text = (
                    f"{todo.get('age_days', 'N/A')} days"
                    if todo.get("age_days") is not None
                    else "Unknown"
                )
                rows += f"<tr><td>{todo['file']}</td><td>{todo['line']}</td><td>{age_text}</td></tr>"
            return rows

        def generate_duplication_rows(dup_files):
            rows = ""
            for file_path, count in dup_files[:10]:
                rows += f"<tr><td>{file_path}</td><td>{count}</td></tr>"
            return rows

        def generate_recommendation_items(recommendations):
            return "".join([f"<li>{rec}</li>" for rec in recommendations])

        summary = report["summary"]
        debt_score = report["debt_score"]
        return html_template.format(
            timestamp=report["timestamp"],
            overall_score=debt_score["total_score"],
            score_color=get_score_color(debt_score["total_score"]),
            debt_level=debt_score["debt_level"],
            total_files=summary["total_files_analyzed"],
            total_todos=summary["total_todos"],
            total_code_smells=summary["total_code_smells"],
            duplication_percentage=summary["duplication_percentage"],
            test_coverage=summary["test_coverage"],
            category_score_rows=generate_category_score_rows(
                debt_score["category_scores"]
            ),
            todo_rows=generate_todo_rows(
                report["analysis_results"]["todo_comments"]["oldest_todos"]
            ),
            duplication_rows=generate_duplication_rows(
                report["analysis_results"]["duplication"]["most_duplicated_files"]
            ),
            recommendation_items=generate_recommendation_items(
                debt_score["recommendations"]
            ),
        )

    def run_analysis(self):
        print("Starting technical debt analysis...")
        print("Running comprehensive technical debt analysis...")
        results = {
            "python_files": 0,
            "duplication": self.analyze_code_duplication(),
            "todo_comments": self.analyze_todo_comments(),
            "code_smells": self.analyze_code_smells(),
            "test_coverage": self.analyze_test_coverage(),
        }
        for root, dirs, files in os.walk("."):
            skip_dirs = [".git", "venv", "__pycache__", "node_modules", ".pytest_cache"]
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for file in files:
                if file.endswith(".py"):
                    results["python_files"] += 1
        report = self.generate_debt_report(results)
        self.save_reports(report)
        print("\n📊 Technical Debt Analysis Summary:")
        print(f"Files analyzed: {results['python_files']}")
        print(f"Overall debt score: {report['debt_score']['total_score']:.1f}/100")
        print(f"Debt level: {report['debt_score']['debt_level']}")
        print(
            f"Code duplication: {results['duplication']['duplication_percentage']:.1f}%"
        )
        print(f"TODO comments: {results['todo_comments']['total_todos']}")
        print(f"Code smells: {results['code_smells']['total_smells']}")
        print(f"Test coverage: {results['test_coverage']['coverage_estimate']:.1f}%")
        print(f"\n📝 Top Recommendations:")
        for rec in report["debt_score"]["recommendations"][:5]:
            print(f"  {rec}")
        return report


def main():
    analyzer = TechnicalDebtAnalyzer()
    results = analyzer.run_analysis()
    if results["debt_score"]["debt_level"] in ["critical", "high"]:
        print("🔴 Critical technical debt detected")
        exit(1)
    else:
        print("✅ Technical debt at acceptable levels")
        exit(0)


if __name__ == "__main__":
    main()
