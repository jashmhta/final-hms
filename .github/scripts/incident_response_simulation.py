"""
incident_response_simulation module
"""

import hashlib
import json
import os
import random
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

import requests


class IncidentResponseSimulator:
    def __init__(self):
        self.incident_types = [
            "data_breach",
            "unauthorized_access",
            "malware_detection",
            "phishing_attempt",
            "ddos_attack",
            "insider_threat",
            "system_compromise",
            "data_exfiltration",
        ]
        self.severity_levels = ["low", "medium", "high", "critical"]
        self.incident_scenarios = {
            "data_breach": {
                "description": "Unauthorized access to patient data",
                "indicators": [
                    "unusual_db_access",
                    "data_export",
                    "large_file_transfers",
                ],
                "response_steps": [
                    "isolate_system",
                    "analyze_logs",
                    "notify_authorities",
                    "contact_patients",
                ],
            },
            "unauthorized_access": {
                "description": "Unauthorized user login attempts",
                "indicators": ["failed_logins", "suspicious_ip", "unusual_login_times"],
                "response_steps": [
                    "lock_account",
                    "investigate_source",
                    "reset_credentials",
                    "monitor_activity",
                ],
            },
            "malware_detection": {
                "description": "Malicious software detected on system",
                "indicators": [
                    "antivirus_alert",
                    "suspicious_processes",
                    "network_anomalies",
                ],
                "response_steps": [
                    "isolate_system",
                    "remove_malware",
                    "restore_backup",
                    "update_defenses",
                ],
            },
            "phishing_attempt": {
                "description": "Phishing email targeting staff",
                "indicators": ["suspicious_email", "user_reports", "link_analysis"],
                "response_steps": [
                    "block_sender",
                    "educate_users",
                    "monitor_clicks",
                    "update_filters",
                ],
            },
        }

    def generate_incident_scenario(self) -> Dict[str, Any]:
        incident_type = random.choice(self.incident_types)
        severity = random.choice(self.severity_levels)
        scenario = {
            "incident_id": f"INC-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
            "incident_type": incident_type,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
            "status": "detected",
            "affected_systems": self.select_affected_systems(),
            "indicators": self.generate_indicators(incident_type),
            "response_procedures": self.get_response_procedures(incident_type),
            "estimated_impact": self.estimate_impact(severity),
            "required_actions": self.get_required_actions(severity),
        }
        return scenario

    def select_affected_systems(self) -> List[str]:
        systems = [
            "patient_database",
            "electronic_health_records",
            "appointment_system",
            "billing_system",
            "pharmacy_system",
            "laboratory_system",
            "radiology_system",
            "admission_system",
            "emergency_system",
            "telemedicine_platform",
        ]
        return random.sample(systems, random.randint(1, 3))

    def generate_indicators(self, incident_type: str) -> List[Dict[str, Any]]:
        if incident_type in self.incident_scenarios:
            base_indicators = self.incident_scenarios[incident_type]["indicators"]
        else:
            base_indicators = [
                "suspicious_activity",
                "system_anomaly",
                "unusual_behavior",
            ]
        indicators = []
        for indicator in base_indicators:
            indicators.append(
                {
                    "indicator_type": indicator,
                    "value": self.generate_indicator_value(indicator),
                    "confidence": random.uniform(0.6, 0.95),
                    "first_observed": (
                        datetime.now() - timedelta(hours=random.randint(1, 24))
                    ).isoformat(),
                    "last_observed": datetime.now().isoformat(),
                }
            )
        return indicators

    def generate_indicator_value(self, indicator_type: str) -> str:
        if indicator_type == "unusual_db_access":
            return f"SELECT * FROM patients WHERE id = {random.randint(1000, 9999)}"
        elif indicator_type == "data_export":
            return f"Exported {random.randint(100, 10000)} records"
        elif indicator_type == "failed_logins":
            return f"Failed login attempts from IP: {self.generate_random_ip()}"
        elif indicator_type == "suspicious_ip":
            return self.generate_random_ip()
        elif indicator_type == "suspicious_email":
            return (
                f"phishing@{random.choice(['gmail.com', 'yahoo.com', 'outlook.com'])}"
            )
        else:
            return f"Anomalous {indicator_type} detected"

    def generate_random_ip(self) -> str:
        return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"

    def get_response_procedures(self, incident_type: str) -> List[str]:
        if incident_type in self.incident_scenarios:
            return self.incident_scenarios[incident_type]["response_steps"]
        else:
            return [
                "investigate_incident",
                "contain_threat",
                "eradicate_cause",
                "recover_systems",
            ]

    def estimate_impact(self, severity: str) -> Dict[str, Any]:
        impact_multipliers = {"low": 1, "medium": 2, "high": 3, "critical": 5}
        multiplier = impact_multipliers.get(severity, 1)
        return {
            "patients_affected": random.randint(10 * multiplier, 1000 * multiplier),
            "systems_affected": random.randint(1, 5),
            "estimated_downtime_hours": random.randint(1 * multiplier, 24 * multiplier),
            "data_records_compromised": random.randint(
                100 * multiplier, 10000 * multiplier
            ),
            "financial_impact_estimate": random.randint(
                10000 * multiplier, 1000000 * multiplier
            ),
        }

    def get_required_actions(self, severity: str) -> List[str]:
        base_actions = [
            "document_incident",
            "preserve_evidence",
            "notify_security_team",
            "initiate_investigation",
        ]
        if severity in ["high", "critical"]:
            base_actions.extend(
                [
                    "notify_management",
                    "notify_legal_team",
                    "consider_external_notification",
                    "activate_incident_response_team",
                ]
            )
        if severity == "critical":
            base_actions.extend(
                [
                    "notify_regulatory_authorities",
                    "prepare_for_public_notification",
                    "activate_business_continuity_plan",
                ]
            )
        return base_actions

    def simulate_incident_detection(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        print(f"🚨 SIMULATED INCIDENT DETECTED: {scenario['incident_type']}")
        print(f"Severity: {scenario['severity'].upper()}")
        print(f"Affected Systems: {', '.join(scenario['affected_systems'])}")
        detection_time = random.uniform(30, 300)
        print(f"Detection Time: {detection_time:.1f} seconds")
        analysis_results = {
            "confirmed_threat": random.choice([True, False]),
            "threat_source": self.identify_threat_source(),
            "attack_vector": self.identify_attack_vector(),
            "mitigation_possible": random.choice([True, False]),
            "estimated_resolution_time": random.randint(30, 480),
        }
        return analysis_results

    def identify_threat_source(self) -> str:
        sources = [
            "external_attacker",
            "insider_threat",
            "compromised_account",
            "malware_infection",
            "phishing_attack",
            "supply_chain_compromise",
            "zero_day_exploit",
        ]
        return random.choice(sources)

    def identify_attack_vector(self) -> str:
        vectors = [
            "sql_injection",
            "cross_site_scripting",
            "weak_credentials",
            "unpatched_vulnerability",
            "social_engineering",
            "misconfigured_service",
            "insufficient_access_controls",
        ]
        return random.choice(vectors)

    def simulate_containment_actions(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        print("🔒 Initiating containment procedures...")
        containment_actions = [
            "isolate_affected_systems",
            "block_malicious_ips",
            "disable_compromised_accounts",
            "patch_vulnerabilities",
            "monitor_network_traffic",
            "preserve_evidence",
        ]
        selected_actions = random.sample(
            containment_actions, random.randint(3, len(containment_actions))
        )
        action_results = {}
        for action in selected_actions:
            success = random.choice([True, True, True, False])
            execution_time = random.uniform(10, 300)
            action_results[action] = {
                "success": success,
                "execution_time_seconds": execution_time,
                "details": f"{'Successfully' if success else 'Failed to'} execute {action.replace('_', ' ')}",
            }
            print(
                f"  {'✅' if success else '❌'} {action.replace('_', ' ').title()}: {execution_time:.1f}s"
            )
        return action_results

    def simulate_eradication(
        self, scenario: Dict[str, Any], containment_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        print("🧹 Initiating eradication procedures...")
        eradication_actions = [
            "remove_malware",
            "patch_systems",
            "reset_credentials",
            "restore_from_backup",
            "update_security_controls",
            "conduct_forensic_analysis",
        ]
        action_results = {}
        for action in eradication_actions:
            success = random.choice([True, True, False])
            execution_time = random.uniform(60, 600)
            action_results[action] = {
                "success": success,
                "execution_time_seconds": execution_time,
                "details": f"{'Successfully' if success else 'Failed to'} {action.replace('_', ' ')}",
            }
            print(
                f"  {'✅' if success else '❌'} {action.replace('_', ' ').title()}: {execution_time:.1f}s"
            )
        return action_results

    def simulate_recovery(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        print("🔄 Initiating recovery procedures...")
        recovery_actions = [
            "restore_systems",
            "validate_integrity",
            "monitor_for_reinfection",
            "update_incident_documentation",
            "conduct_post_incident_review",
            "implement_prevention_measures",
        ]
        action_results = {}
        for action in recovery_actions:
            success = random.choice([True, True, True, False])
            execution_time = random.uniform(120, 3600)
            action_results[action] = {
                "success": success,
                "execution_time_seconds": execution_time,
                "details": f"{'Successfully' if success else 'Failed to'} {action.replace('_', ' ')}",
            }
            print(
                f"  {'✅' if success else '❌'} {action.replace('_', ' ').title()}: {execution_time:.1f}s"
            )
        return action_results

    def generate_incident_report(
        self,
        scenario: Dict[str, Any],
        detection_results: Dict[str, Any],
        containment_results: Dict[str, Any],
        eradication_results: Dict[str, Any],
        recovery_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        total_actions = (
            len(containment_results) + len(eradication_results) + len(recovery_results)
        )
        successful_actions = sum(
            1
            for results in [containment_results, eradication_results, recovery_results]
            for action in results.values()
            if action["success"]
        )
        success_rate = (
            (successful_actions / total_actions) * 100 if total_actions > 0 else 0
        )
        total_time = sum(
            action["execution_time_seconds"]
            for results in [containment_results, eradication_results, recovery_results]
            for action in results.values()
        )
        report = {
            "incident_summary": scenario,
            "detection_analysis": detection_results,
            "containment_results": containment_results,
            "eradication_results": eradication_results,
            "recovery_results": recovery_results,
            "metrics": {
                "total_actions": total_actions,
                "successful_actions": successful_actions,
                "success_rate": success_rate,
                "total_response_time_seconds": total_time,
                "total_response_time_hours": total_time / 3600,
            },
            "lessons_learned": self.generate_lessons_learned(scenario, success_rate),
            "recommendations": self.generate_recommendations(scenario, success_rate),
            "report_generated_at": datetime.now().isoformat(),
        }
        return report

    def generate_lessons_learned(
        self, scenario: Dict[str, Any], success_rate: float
    ) -> List[str]:
        lessons = []
        if success_rate < 70:
            lessons.append(
                "Low success rate indicates need for improved incident response procedures"
            )
        if scenario["severity"] in ["high", "critical"]:
            lessons.append(
                "Critical incidents require faster detection and response times"
            )
        lessons.append(
            "Regular incident response training is essential for effective handling"
        )
        lessons.append("Documentation of procedures needs improvement for consistency")
        lessons.append(
            "Consider implementing automated response mechanisms for common threats"
        )
        return lessons

    def generate_recommendations(
        self, scenario: Dict[str, Any], success_rate: float
    ) -> List[str]:
        recommendations = []
        if success_rate < 80:
            recommendations.append("Review and update incident response procedures")
            recommendations.append("Conduct additional incident response training")
        recommendations.append("Implement automated detection and alerting systems")
        recommendations.append("Establish regular incident response drills")
        recommendations.append("Improve documentation and communication protocols")
        recommendations.append(
            "Consider investing in incident response automation tools"
        )
        if scenario["severity"] in ["high", "critical"]:
            recommendations.append("Enhance monitoring and detection capabilities")
            recommendations.append("Establish dedicated incident response team")
        return recommendations

    def save_incident_report(self, report: Dict[str, Any]):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"incident_response_report_{timestamp}.json"
        with open(json_filename, "w") as f:
            json.dump(report, f, indent=2)
        html_filename = f"incident_response_report_{timestamp}.html"
        html_content = self.generate_html_report(report)
        with open(html_filename, "w") as f:
            f.write(html_content)
        print(f"📄 Incident reports saved:")
        print(f"  - JSON: {json_filename}")
        print(f"  - HTML: {html_filename}")

    def generate_html_report(self, report: Dict[str, Any]) -> str:
        html_template = """<!DOCTYPE html>
<html>
<head>
    <title>Incident Response Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1, h2 { color: #333; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .success { color: green; }
        .failure { color: red; }
        .critical { background-color: #ffcccc; }
        .high { background-color: #ffe6cc; }
        .medium { background-color: #ffffcc; }
        .low { background-color: #ccffcc; }
    </style>
</head>
<body>
    <h1>Incident Response Report</h1>
    <p><strong>Generated at:</strong> {report_generated_at}</p>

    <h2>Incident Summary</h2>
    <p><strong>ID:</strong> {incident_id}</p>
    <p><strong>Type:</strong> {incident_type}</p>
    <p><strong>Severity:</strong> <span class="{severity_class}">{severity}</span></p>
    <p><strong>Affected Systems:</strong> {affected_systems}</p>
    <p><strong>Timestamp:</strong> {timestamp}</p>

    <h2>Metrics</h2>
    <p><strong>Success Rate:</strong> {success_rate}%</p>
    <p><strong>Total Response Time:</strong> {total_response_time_hours} hours</p>
    <p><strong>Successful Actions:</strong> {successful_actions}/{total_actions}</p>

    <h2>Containment Results</h2>
    <table>
        <tr><th>Action</th><th>Status</th></tr>
        {containment_rows}
    </table>

    <h2>Eradication Results</h2>
    <table>
        <tr><th>Action</th><th>Status</th></tr>
        {eradication_rows}
    </table>

    <h2>Recovery Results</h2>
    <table>
        <tr><th>Action</th><th>Status</th></tr>
        {recovery_rows}
    </table>

    <h2>Lessons Learned</h2>
    <ul>{lessons_learned_items}</ul>

    <h2>Recommendations</h2>
    <ul>{recommendation_items}</ul>
</body>
</html>"""

        def generate_action_rows(actions):
            rows = ""
            for action, result in actions.items():
                status_class = "success" if result["success"] else "failure"
                status_text = "✅ Success" if result["success"] else "❌ Failed"
                rows += f"<tr><td>{action}</td><td class='{status_class}'>{status_text}</td></tr>"
            return rows

        def generate_list_items(items):
            return "".join([f"<li>{item}</li>" for item in items])

        severity_class = report["incident_summary"]["severity"]
        return html_template.format(
            report_generated_at=report["report_generated_at"],
            incident_id=report["incident_summary"]["incident_id"],
            incident_type=report["incident_summary"]["incident_type"],
            severity_class=severity_class,
            severity=report["incident_summary"]["severity"].upper(),
            affected_systems=", ".join(report["incident_summary"]["affected_systems"]),
            timestamp=report["incident_summary"]["timestamp"],
            success_rate=report["metrics"]["success_rate"],
            total_response_time_hours=report["metrics"]["total_response_time_hours"],
            successful_actions=report["metrics"]["successful_actions"],
            total_actions=report["metrics"]["total_actions"],
            containment_rows=generate_action_rows(report["containment_results"]),
            eradication_rows=generate_action_rows(report["eradication_results"]),
            recovery_rows=generate_action_rows(report["recovery_results"]),
            lessons_learned_items=generate_list_items(report["lessons_learned"]),
            recommendation_items=generate_list_items(report["recommendations"]),
        )

    def run_simulation(self):
        print("🚨 Starting Incident Response Simulation")
        print("=" * 50)
        scenario = self.generate_incident_scenario()
        print(f"\n📡 Phase 1: Detection")
        detection_results = self.simulate_incident_detection(scenario)
        print(f"\n🔒 Phase 2: Containment")
        containment_results = self.simulate_containment_actions(scenario)
        print(f"\n🧹 Phase 3: Eradication")
        eradication_results = self.simulate_eradication(scenario, containment_results)
        print(f"\n🔄 Phase 4: Recovery")
        recovery_results = self.simulate_recovery(scenario)
        print(f"\n📊 Generating Report...")
        report = self.generate_incident_report(
            scenario,
            detection_results,
            containment_results,
            eradication_results,
            recovery_results,
        )
        self.save_incident_report(report)
        print(f"\n📈 Simulation Summary:")
        print(f"  Incident Type: {scenario['incident_type']}")
        print(f"  Severity: {scenario['severity']}")
        print(f"  Success Rate: {report['metrics']['success_rate']:.1f}%")
        print(
            f"  Total Response Time: {report['metrics']['total_response_time_hours']:.2f} hours"
        )
        return report


def main():
    simulator = IncidentResponseSimulator()
    num_simulations = 3
    for i in range(num_simulations):
        print(f"\n{'='*60}")
        print(f"SIMULATION {i+1}/{num_simulations}")
        print(f"{'='*60}")
        report = simulator.run_simulation()
        if i < num_simulations - 1:
            print(f"\n⏳ Waiting 30 seconds before next simulation...")
            import time

            time.sleep(30)
    print(f"\n✅ All {num_simulations} simulations completed!")


if __name__ == "__main__":
    main()
