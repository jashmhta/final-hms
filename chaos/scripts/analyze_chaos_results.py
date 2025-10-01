#!/usr/bin/env python3
"""
Chaos Engineering Results Analysis Script
Analyzes chaos experiment results and generates insights
"""

import argparse
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import statistics

class ChaosAnalyzer:
    """Analyzes chaos engineering experiment results"""

    def __init__(self, results_dir: str):
        self.results_dir = results_dir
        self.results: List[Dict[str, Any]] = []
        self.load_results()

    def load_results(self):
        """Load all chaos experiment results"""
        if not os.path.exists(self.results_dir):
            return

        for filename in os.listdir(self.results_dir):
            if filename.startswith("chaos_results_") and filename.endswith(".json"):
                filepath = os.path.join(self.results_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        result = json.load(f)
                        self.results.append(result)
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    print(f"Warning: Could not load {filename}: {e}")

    def analyze_overall_performance(self) -> Dict[str, Any]:
        """Analyze overall chaos testing performance"""
        if not self.results:
            return {"error": "No results to analyze"}

        total_experiments = sum(r.get("total_experiments", 0) for r in self.results)
        total_completed = sum(r.get("completed", 0) for r in self.results)
        total_failed = sum(r.get("failed", 0) for r in self.results)

        success_rate = (total_completed / total_experiments * 100) if total_experiments > 0 else 0

        return {
            "total_experiments": total_experiments,
            "total_completed": total_completed,
            "total_failed": total_failed,
            "success_rate": round(success_rate, 2),
            "analysis_period": self._get_analysis_period()
        }

    def analyze_by_experiment_type(self) -> Dict[str, Any]:
        """Analyze performance by experiment type"""
        experiment_stats = {}

        for result in self.results:
            for exp in result.get("experiments", []):
                exp_type = exp.get("experiment_type", "unknown")
                status = exp.get("status", "unknown")

                if exp_type not in experiment_stats:
                    experiment_stats[exp_type] = {
                        "total": 0,
                        "completed": 0,
                        "failed": 0,
                        "avg_duration": []
                    }

                experiment_stats[exp_type]["total"] += 1
                if status == "completed":
                    experiment_stats[exp_type]["completed"] += 1
                    # Calculate duration if available
                    start = exp.get("start_time")
                    end = exp.get("end_time")
                    if start and end:
                        try:
                            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                            end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                            duration = (end_dt - start_dt).total_seconds()
                            experiment_stats[exp_type]["avg_duration"].append(duration)
                        except (ValueError, AttributeError):
                            pass
                else:
                    experiment_stats[exp_type]["failed"] += 1

        # Calculate averages and success rates
        for exp_type, stats in experiment_stats.items():
            stats["success_rate"] = round((stats["completed"] / stats["total"] * 100), 2) if stats["total"] > 0 else 0
            if stats["avg_duration"]:
                stats["avg_duration_seconds"] = round(statistics.mean(stats["avg_duration"]), 2)
            else:
                stats["avg_duration_seconds"] = 0
            del stats["avg_duration"]  # Remove raw data

        return experiment_stats

    def analyze_by_target_app(self) -> Dict[str, Any]:
        """Analyze performance by target application"""
        app_stats = {}

        for result in self.results:
            for exp in result.get("experiments", []):
                # Extract target app from experiment name
                name = exp.get("name", "")
                target_app = "unknown"
                if "-backend-" in name:
                    target_app = "backend"
                elif "-frontend-" in name:
                    target_app = "frontend"
                elif "-postgres-" in name:
                    target_app = "postgres"
                elif "-redis-" in name:
                    target_app = "redis"

                status = exp.get("status", "unknown")

                if target_app not in app_stats:
                    app_stats[target_app] = {
                        "total": 0,
                        "completed": 0,
                        "failed": 0
                    }

                app_stats[target_app]["total"] += 1
                if status == "completed":
                    app_stats[target_app]["completed"] += 1
                else:
                    app_stats[target_app]["failed"] += 1

        # Calculate success rates
        for app, stats in app_stats.items():
            stats["success_rate"] = round((stats["completed"] / stats["total"] * 100), 2) if stats["total"] > 0 else 0

        return app_stats

    def identify_resilience_issues(self) -> List[Dict[str, Any]]:
        """Identify potential resilience issues from failed experiments"""
        issues = []

        for result in self.results:
            for exp in result.get("experiments", []):
                if exp.get("status") == "failed":
                    issue = {
                        "experiment_name": exp.get("name"),
                        "experiment_type": exp.get("experiment_type"),
                        "failure_reason": exp.get("results", {}).get("error", "Unknown"),
                        "timestamp": exp.get("end_time"),
                        "severity": self._assess_severity(exp)
                    }
                    issues.append(issue)

        return issues

    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []

        overall_perf = self.analyze_overall_performance()
        exp_analysis = self.analyze_by_experiment_type()
        app_analysis = self.analyze_by_target_app()
        issues = self.identify_resilience_issues()

        # Overall recommendations
        if overall_perf.get("success_rate", 0) < 80:
            recommendations.append("Overall chaos testing success rate is below 80%. Review system resilience and fix identified issues.")

        # Experiment type recommendations
        for exp_type, stats in exp_analysis.items():
            if stats.get("success_rate", 0) < 70:
                recommendations.append(f"Low success rate for {exp_type} experiments ({stats['success_rate']}%). Focus on improving {exp_type} resilience.")

        # Application recommendations
        for app, stats in app_analysis.items():
            if stats.get("success_rate", 0) < 75:
                recommendations.append(f"Application {app} shows low resilience ({stats['success_rate']}% success rate). Implement additional safeguards.")

        # Issue-specific recommendations
        if issues:
            recommendations.append(f"Address {len(issues)} identified resilience issues before production deployment.")

        # General recommendations
        recommendations.extend([
            "Implement circuit breakers for external service calls",
            "Add comprehensive monitoring and alerting for chaos scenarios",
            "Regularly review and update chaos experiment scenarios",
            "Consider implementing automated remediation for common failure patterns"
        ])

        return recommendations

    def _assess_severity(self, experiment: Dict[str, Any]) -> str:
        """Assess the severity of a failed experiment"""
        exp_type = experiment.get("experiment_type", "")

        # Pod failures are critical for availability
        if exp_type == "pod_failure":
            return "high"
        # Network issues can cause cascading failures
        elif exp_type == "network_delay":
            return "high"
        # Resource exhaustion can lead to performance degradation
        elif exp_type in ["cpu_stress", "memory_stress", "disk_fill"]:
            return "medium"
        else:
            return "low"

    def _get_analysis_period(self) -> str:
        """Get the time period covered by the analysis"""
        if not self.results:
            return "No data"

        timestamps = []
        for result in self.results:
            for exp in result.get("experiments", []):
                for time_field in ["start_time", "end_time"]:
                    timestamp = exp.get(time_field)
                    if timestamp:
                        try:
                            # Handle different timestamp formats
                            if timestamp.endswith('Z'):
                                timestamp = timestamp[:-1] + '+00:00'
                            dt = datetime.fromisoformat(timestamp)
                            timestamps.append(dt)
                        except (ValueError, AttributeError):
                            continue

        if not timestamps:
            return "Unknown"

        earliest = min(timestamps)
        latest = max(timestamps)

        return f"{earliest.strftime('%Y-%m-%d %H:%M:%S')} to {latest.strftime('%Y-%m-%d %H:%M:%S')}"

    def generate_report(self, output_file: str):
        """Generate a comprehensive analysis report"""
        overall_perf = self.analyze_overall_performance()
        exp_analysis = self.analyze_by_experiment_type()
        app_analysis = self.analyze_by_target_app()
        issues = self.identify_resilience_issues()
        recommendations = self.generate_recommendations()

        report = f"""# Chaos Engineering Analysis Report
Generated: {datetime.now().isoformat()}

## Executive Summary

This report analyzes the results of chaos engineering experiments conducted on the HMS Enterprise system.

### Overall Performance
- **Total Experiments**: {overall_perf.get('total_experiments', 0)}
- **Completed**: {overall_perf.get('completed', 0)}
- **Failed**: {overall_perf.get('failed', 0)}
- **Success Rate**: {overall_perf.get('success_rate', 0)}%
- **Analysis Period**: {overall_perf.get('analysis_period', 'Unknown')}

## Analysis by Experiment Type

| Experiment Type | Total | Completed | Failed | Success Rate | Avg Duration (s) |
|----------------|-------|-----------|--------|--------------|------------------|
"""

        for exp_type, stats in exp_analysis.items():
            report += f"| {exp_type} | {stats['total']} | {stats['completed']} | {stats['failed']} | {stats['success_rate']}% | {stats.get('avg_duration_seconds', 0)} |\n"

        report += "\n## Analysis by Target Application\n\n"
        report += "| Application | Total | Completed | Failed | Success Rate |\n"
        report += "|-------------|-------|-----------|--------|--------------|\n"

        for app, stats in app_analysis.items():
            report += f"| {app} | {stats['total']} | {stats['completed']} | {stats['failed']} | {stats['success_rate']}% |\n"

        if issues:
            report += "\n## Identified Resilience Issues\n\n"
            for issue in issues:
                report += f"### {issue['experiment_name']}\n"
                report += f"- **Type**: {issue['experiment_type']}\n"
                report += f"- **Severity**: {issue['severity']}\n"
                report += f"- **Failure Reason**: {issue['failure_reason']}\n"
                report += f"- **Timestamp**: {issue['timestamp']}\n\n"

        report += "## Recommendations\n\n"
        for i, rec in enumerate(recommendations, 1):
            report += f"{i}. {rec}\n"

        report += "\n## Conclusion\n\n"
        success_rate = overall_perf.get('success_rate', 0)
        if success_rate >= 90:
            report += "The system demonstrates excellent resilience with a high success rate in chaos experiments. Continue regular testing and monitoring."
        elif success_rate >= 75:
            report += "The system shows good resilience but has room for improvement. Address identified issues and implement recommended safeguards."
        else:
            report += "The system requires significant resilience improvements. Address all identified issues before production deployment."

        # Write report to file
        with open(output_file, 'w') as f:
            f.write(report)

        print(f"Analysis report generated: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Analyze chaos engineering results")
    parser.add_argument("--results-dir", default="chaos/results", help="Directory containing chaos results")
    parser.add_argument("--output", default="chaos-analysis-report.md", help="Output report file")

    args = parser.parse_args()

    analyzer = ChaosAnalyzer(args.results_dir)

    if not analyzer.results:
        print("No chaos results found to analyze")
        return

    analyzer.generate_report(args.output)

    # Print summary
    overall = analyzer.analyze_overall_performance()
    print("\nChaos Analysis Summary:")
    print(f"  Total Experiments: {overall.get('total_experiments', 0)}")
    print(f"  Success Rate: {overall.get('success_rate', 0)}%")
    print(f"  Report: {args.output}")

if __name__ == "__main__":
    main()