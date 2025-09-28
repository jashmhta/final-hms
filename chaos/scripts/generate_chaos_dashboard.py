#!/usr/bin/env python3
"""
Chaos Engineering Dashboard Generator
Generates HTML dashboard for chaos experiment results
"""

import argparse
import json
import os
from datetime import datetime
from typing import Dict, List, Any

class ChaosDashboardGenerator:
    """Generates HTML dashboard for chaos results"""

    def __init__(self, results_dir: str, output_file: str):
        self.results_dir = results_dir
        self.output_file = output_file
        self.results: List[Dict[str, Any]] = []
        self.load_results()

    def load_results(self):
        """Load chaos results"""
        if not os.path.exists(self.results_dir):
            return

        for filename in os.listdir(self.results_dir):
            if filename.startswith("chaos_results_") and filename.endswith(".json"):
                filepath = os.path.join(self.results_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        result = json.load(f)
                        self.results.append(result)
                except (json.JSONDecodeError, FileNotFoundError):
                    pass

    def generate_dashboard(self):
        """Generate HTML dashboard"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Chaos Engineering Dashboard - HMS</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .metric {{ background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 5px; }}
        .success {{ color: green; }}
        .failure {{ color: red; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>🚀 Chaos Engineering Dashboard - HMS Enterprise System</h1>
    <p>Generated: {datetime.now().isoformat()}</p>

    <div class="metric">
        <h2>Overall Statistics</h2>
"""

        if self.results:
            total_exp = sum(r.get("total_experiments", 0) for r in self.results)
            completed = sum(r.get("completed", 0) for r in self.results)
            failed = sum(r.get("failed", 0) for r in self.results)
            success_rate = (completed / total_exp * 100) if total_exp > 0 else 0

            html += f"""
        <p>Total Experiments: {total_exp}</p>
        <p>Completed: <span class="success">{completed}</span></p>
        <p>Failed: <span class="failure">{failed}</span></p>
        <p>Success Rate: {success_rate:.1f}%</p>
"""

        html += """
    </div>

    <h2>Experiment Details</h2>
    <table>
        <tr>
            <th>Experiment Name</th>
            <th>Type</th>
            <th>Status</th>
            <th>Duration</th>
        </tr>
"""

        for result in self.results:
            for exp in result.get("experiments", []):
                status_class = "success" if exp.get("status") == "completed" else "failure"
                html += f"""
        <tr>
            <td>{exp.get("name", "N/A")}</td>
            <td>{exp.get("experiment_type", "N/A")}</td>
            <td class="{status_class}">{exp.get("status", "N/A")}</td>
            <td>{exp.get("end_time", "N/A")}</td>
        </tr>
"""

        html += """
    </table>
</body>
</html>
"""

        with open(self.output_file, 'w') as f:
            f.write(html)

        print(f"Dashboard generated: {self.output_file}")

def main():
    parser = argparse.ArgumentParser(description="Generate Chaos Engineering Dashboard")
    parser.add_argument("--results-dir", required=True, help="Directory containing chaos results")
    parser.add_argument("--output", required=True, help="Output HTML file")

    args = parser.parse_args()

    generator = ChaosDashboardGenerator(args.results_dir, args.output)
    generator.generate_dashboard()

if __name__ == "__main__":
    main()