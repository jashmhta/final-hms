"""
ui_ux_agent module
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class UIUXAgent:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.frontend_dir = self.project_root / "frontend"
        self.reports_dir = self.project_root / "reports"
        self.iterations = 0
        self.max_iterations = 10

    def run_command(
        self, command: str, cwd: Optional[Path] = None
    ) -> Tuple[int, str, str]:
        """Run a shell command and return exit code, stdout, stderr."""
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd or self.frontend_dir,
            capture_output=True,
            text=True,
        )
        return result.returncode, result.stdout, result.stderr

    def check_material_design_compliance(self) -> Tuple[bool, List[str]]:
        """Check Material Design compliance by analyzing component usage."""
        issues = []
        compliant = True

        # Check if MUI components are used consistently
        component_files = list(self.frontend_dir.glob("src/components/**/*.tsx"))
        for file_path in component_files:
            with open(file_path, "r") as f:
                content = f.read()
                # Check for non-MUI components that should be MUI
                if "Button" in content and "@mui/material" not in content:
                    issues.append(f"Non-MUI Button found in {file_path}")
                    compliant = False
                # Add more checks as needed

        return compliant, issues

    def check_wcag_accessibility(self) -> Tuple[bool, List[str]]:
        """Run accessibility tests using jest-axe."""
        issues = []
        compliant = True

        exit_code, stdout, stderr = self.run_command(
            "npm run test:frontend:accessibility"
        )
        if exit_code != 0:
            issues.append("Accessibility tests failed")
            compliant = False
            issues.extend(stderr.split("\n"))

        return compliant, issues

    def check_responsive_design(self) -> Tuple[bool, List[str]]:
        """Run responsive design tests."""
        issues = []
        compliant = True

        exit_code, stdout, stderr = self.run_command("npm run test:frontend:responsive")
        if exit_code != 0:
            issues.append("Responsive design tests failed")
            compliant = False
            issues.extend(stderr.split("\n"))

        return compliant, issues

    def check_healthcare_ui_patterns(self) -> Tuple[bool, List[str]]:
        """Check for healthcare-specific UI patterns."""
        issues = []
        compliant = True

        # Check if healthcare components exist and are used
        healthcare_components = [
            "PatientCard",
            "VitalSignsMonitor",
            "AppointmentCalendar",
            "MedicalRecordViewer",
        ]

        for component in healthcare_components:
            files = list(
                self.frontend_dir.glob(f"src/components/healthcare/{component}.tsx")
            )
            if not files:
                issues.append(f"Healthcare component {component} not found")
                compliant = False

        return compliant, issues

    def check_visual_consistency(self) -> Tuple[bool, List[str]]:
        """Run visual design tests."""
        issues = []
        compliant = True

        exit_code, stdout, stderr = self.run_command("npm run test:frontend:visual")
        if exit_code != 0:
            issues.append("Visual consistency tests failed")
            compliant = False
            issues.extend(stderr.split("\n"))

        return compliant, issues

    def generate_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive UI/UX report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "iteration": self.iterations,
            "material_design_compliant": results["material_design"][0],
            "wcag_accessible": results["wcag"][0],
            "responsive": results["responsive"][0],
            "healthcare_patterns": results["healthcare"][0],
            "visual_consistent": results["visual"][0],
            "issues": {
                "material_design": results["material_design"][1],
                "wcag": results["wcag"][1],
                "responsive": results["responsive"][1],
                "healthcare": results["healthcare"][1],
                "visual": results["visual"][1],
            },
            "overall_compliant": all(
                [
                    results["material_design"][0],
                    results["wcag"][0],
                    results["responsive"][0],
                    results["healthcare"][0],
                    results["visual"][0],
                ]
            ),
        }
        return report

    def save_report(self, report: Dict[str, Any]):
        """Save the report to a file."""
        self.reports_dir.mkdir(exist_ok=True)
        report_file = self.reports_dir / f"ui_ux_report_{self.iterations}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

    def run_ui_ux_checks(self) -> Dict[str, Any]:
        """Run all UI/UX checks."""
        results = {
            "material_design": self.check_material_design_compliance(),
            "wcag": self.check_wcag_accessibility(),
            "responsive": self.check_responsive_design(),
            "healthcare": self.check_healthcare_ui_patterns(),
            "visual": self.check_visual_consistency(),
        }
        return results

    def deploy(self):
        """Main deployment loop for UI/UX improvements."""
        while self.iterations < self.max_iterations:
            self.iterations += 1
            print(f"Starting UI/UX iteration {self.iterations}")

            results = self.run_ui_ux_checks()
            report = self.generate_report(results)
            self.save_report(report)

            if report["overall_compliant"]:
                print("All UI/UX standards achieved!")
                break
            else:
                print("Issues found, continuing improvements...")
                # Here you could add logic to fix issues automatically
                # For now, just report

        print(f"UI/UX deployment completed after {self.iterations} iterations")


if __name__ == "__main__":
    agent = UIUXAgent()
    agent.deploy()
