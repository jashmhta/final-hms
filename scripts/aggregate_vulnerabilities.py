#!/usr/bin/env python3
"""
Aggregate vulnerability reports from multiple security scanning tools.
"""
import argparse
import json
import glob
from pathlib import Path
from typing import Dict, List
from datetime import datetime


def load_json_reports(pattern: str) -> List[Dict]:
    """Load all JSON reports matching pattern"""
    reports = []
    for filepath in glob.glob(pattern, recursive=True):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                reports.append({
                    "source": filepath,
                    "data": data
                })
        except Exception as e:
            print(f"Warning: Could not load {filepath}: {e}")
    return reports


def aggregate_vulnerabilities(
    sast_reports: List[str],
    dast_reports: List[str],
    dependency_reports: List[str],
    secrets_reports: List[str],
    compliance_reports: List[str],
    container_reports: List[str]
) -> Dict:
    """Aggregate all vulnerability reports"""
    
    aggregated = {
        "timestamp": datetime.utcnow().isoformat(),
        "summary": {
            "total_vulnerabilities": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        },
        "by_category": {
            "sast": {"count": 0, "reports": []},
            "dast": {"count": 0, "reports": []},
            "dependencies": {"count": 0, "reports": []},
            "secrets": {"count": 0, "reports": []},
            "compliance": {"count": 0, "reports": []},
            "containers": {"count": 0, "reports": []}
        }
    }
    
    # Load and aggregate SAST reports
    for pattern in sast_reports:
        reports = load_json_reports(pattern)
        aggregated["by_category"]["sast"]["reports"].extend(reports)
        aggregated["by_category"]["sast"]["count"] += len(reports)
    
    # Load and aggregate DAST reports
    for pattern in dast_reports:
        reports = load_json_reports(pattern)
        aggregated["by_category"]["dast"]["reports"].extend(reports)
        aggregated["by_category"]["dast"]["count"] += len(reports)
    
    # Load and aggregate dependency reports
    for pattern in dependency_reports:
        reports = load_json_reports(pattern)
        aggregated["by_category"]["dependencies"]["reports"].extend(reports)
        aggregated["by_category"]["dependencies"]["count"] += len(reports)
    
    # Load and aggregate secrets reports
    for pattern in secrets_reports:
        reports = load_json_reports(pattern)
        aggregated["by_category"]["secrets"]["reports"].extend(reports)
        aggregated["by_category"]["secrets"]["count"] += len(reports)
    
    # Load and aggregate compliance reports
    for pattern in compliance_reports:
        reports = load_json_reports(pattern)
        aggregated["by_category"]["compliance"]["reports"].extend(reports)
        aggregated["by_category"]["compliance"]["count"] += len(reports)
    
    # Load and aggregate container reports
    for pattern in container_reports:
        reports = load_json_reports(pattern)
        aggregated["by_category"]["containers"]["reports"].extend(reports)
        aggregated["by_category"]["containers"]["count"] += len(reports)
    
    # Calculate totals (simplified - would need tool-specific parsing in production)
    for category_data in aggregated["by_category"].values():
        aggregated["summary"]["total_vulnerabilities"] += category_data["count"]
    
    return aggregated


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate vulnerability reports"
    )
    parser.add_argument(
        "--sast-reports",
        nargs="+",
        default=[],
        help="SAST report file patterns"
    )
    parser.add_argument(
        "--dast-reports",
        nargs="+",
        default=[],
        help="DAST report file patterns"
    )
    parser.add_argument(
        "--dependency-reports",
        nargs="+",
        default=[],
        help="Dependency scan report file patterns"
    )
    parser.add_argument(
        "--secrets-reports",
        nargs="+",
        default=[],
        help="Secrets scan report file patterns"
    )
    parser.add_argument(
        "--compliance-reports",
        nargs="+",
        default=[],
        help="Compliance report file patterns"
    )
    parser.add_argument(
        "--container-reports",
        nargs="+",
        default=[],
        help="Container scan report file patterns"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output file path"
    )
    
    args = parser.parse_args()
    
    result = aggregate_vulnerabilities(
        args.sast_reports,
        args.dast_reports,
        args.dependency_reports,
        args.secrets_reports,
        args.compliance_reports,
        args.container_reports
    )
    
    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Aggregated {result['summary']['total_vulnerabilities']} vulnerabilities")
    print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()
