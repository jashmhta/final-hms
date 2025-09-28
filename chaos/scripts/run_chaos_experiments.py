#!/usr/bin/env python3
"""
Chaos Engineering Framework for HMS Enterprise System
Implements automated fault injection testing using LitmusChaos
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ChaosExperiment:
    """Represents a chaos engineering experiment"""

    def __init__(self, name: str, experiment_type: str, config: Dict[str, Any]):
        self.name = name
        self.experiment_type = experiment_type
        self.config = config
        self.status = "pending"
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.results = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "experiment_type": self.experiment_type,
            "config": self.config,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "results": self.results,
        }


class ChaosFramework:
    """Main chaos engineering framework"""

    def __init__(self, namespace: str = "chaos"):
        self.namespace = namespace
        self.experiments: List[ChaosExperiment] = []
        self.results_dir = "chaos/results"
        os.makedirs(self.results_dir, exist_ok=True)

    def add_experiment(self, experiment: ChaosExperiment) -> None:
        """Add an experiment to the framework"""
        self.experiments.append(experiment)
        logger.info(f"Added experiment: {experiment.name}")

    def create_pod_failure_experiment(
        self, name: str, target_app: str, duration: str = "60s"
    ) -> ChaosExperiment:
        """Create a pod failure experiment"""
        config = {
            "apiVersion": "litmuschaos.io/v1alpha1",
            "kind": "ChaosEngine",
            "metadata": {"name": f"{name}-chaos", "namespace": self.namespace},
            "spec": {
                "appinfo": {
                    "appns": "hms",
                    "applabel": f"app={target_app}",
                    "appkind": "deployment",
                },
                "chaosServiceAccount": "litmus-admin",
                "experiments": [
                    {
                        "name": "pod-delete",
                        "spec": {
                            "components": {
                                "env": [
                                    {"name": "TOTAL_CHAOS_DURATION", "value": duration},
                                    {"name": "CHAOS_INTERVAL", "value": "10s"},
                                    {"name": "FORCE", "value": "true"},
                                ]
                            }
                        },
                    }
                ],
                "jobCleanUpPolicy": "delete",
            },
        }
        return ChaosExperiment(name, "pod_failure", config)

    def create_network_delay_experiment(
        self, name: str, target_app: str, delay: str = "2000ms", duration: str = "60s"
    ) -> ChaosExperiment:
        """Create a network delay experiment"""
        config = {
            "apiVersion": "litmuschaos.io/v1alpha1",
            "kind": "ChaosEngine",
            "metadata": {"name": f"{name}-chaos", "namespace": self.namespace},
            "spec": {
                "appinfo": {
                    "appns": "hms",
                    "applabel": f"app={target_app}",
                    "appkind": "deployment",
                },
                "chaosServiceAccount": "litmus-admin",
                "experiments": [
                    {
                        "name": "network-chaos",
                        "spec": {
                            "components": {
                                "env": [
                                    {"name": "TOTAL_CHAOS_DURATION", "value": duration},
                                    {"name": "NETWORK_INTERFACE", "value": "eth0"},
                                    {"name": "TARGET_CONTAINER", "value": target_app},
                                    {"name": "NETWORK_LATENCY", "value": delay},
                                    {"name": "JITTER", "value": "0ms"},
                                ]
                            }
                        },
                    }
                ],
                "jobCleanUpPolicy": "delete",
            },
        }
        return ChaosExperiment(name, "network_delay", config)

    def create_cpu_stress_experiment(
        self, name: str, target_app: str, cpu_load: str = "100", duration: str = "60s"
    ) -> ChaosExperiment:
        """Create a CPU stress experiment"""
        config = {
            "apiVersion": "litmuschaos.io/v1alpha1",
            "kind": "ChaosEngine",
            "metadata": {"name": f"{name}-chaos", "namespace": self.namespace},
            "spec": {
                "appinfo": {
                    "appns": "hms",
                    "applabel": f"app={target_app}",
                    "appkind": "deployment",
                },
                "chaosServiceAccount": "litmus-admin",
                "experiments": [
                    {
                        "name": "stress-chaos",
                        "spec": {
                            "components": {
                                "env": [
                                    {"name": "TOTAL_CHAOS_DURATION", "value": duration},
                                    {"name": "CPU_CORES", "value": cpu_load},
                                    {"name": "STRESS_TYPE", "value": "cpu-stress"},
                                ]
                            }
                        },
                    }
                ],
                "jobCleanUpPolicy": "delete",
            },
        }
        return ChaosExperiment(name, "cpu_stress", config)

    def create_memory_stress_experiment(
        self, name: str, target_app: str, memory_mb: str = "512", duration: str = "60s"
    ) -> ChaosExperiment:
        """Create a memory stress experiment"""
        config = {
            "apiVersion": "litmuschaos.io/v1alpha1",
            "kind": "ChaosEngine",
            "metadata": {"name": f"{name}-chaos", "namespace": self.namespace},
            "spec": {
                "appinfo": {
                    "appns": "hms",
                    "applabel": f"app={target_app}",
                    "appkind": "deployment",
                },
                "chaosServiceAccount": "litmus-admin",
                "experiments": [
                    {
                        "name": "stress-chaos",
                        "spec": {
                            "components": {
                                "env": [
                                    {"name": "TOTAL_CHAOS_DURATION", "value": duration},
                                    {
                                        "name": "MEMORY_CONSUMPTION",
                                        "value": f"{memory_mb}MB",
                                    },
                                    {"name": "STRESS_TYPE", "value": "memory-stress"},
                                ]
                            }
                        },
                    }
                ],
                "jobCleanUpPolicy": "delete",
            },
        }
        return ChaosExperiment(name, "memory_stress", config)

    def create_disk_fill_experiment(
        self,
        name: str,
        target_app: str,
        fill_percentage: str = "80",
        duration: str = "60s",
    ) -> ChaosExperiment:
        """Create a disk fill experiment"""
        config = {
            "apiVersion": "litmuschaos.io/v1alpha1",
            "kind": "ChaosEngine",
            "metadata": {"name": f"{name}-chaos", "namespace": self.namespace},
            "spec": {
                "appinfo": {
                    "appns": "hms",
                    "applabel": f"app={target_app}",
                    "appkind": "deployment",
                },
                "chaosServiceAccount": "litmus-admin",
                "experiments": [
                    {
                        "name": "disk-fill",
                        "spec": {
                            "components": {
                                "env": [
                                    {"name": "TOTAL_CHAOS_DURATION", "value": duration},
                                    {
                                        "name": "EPHEMERAL_STORAGE_MEBIBYTES",
                                        "value": "1024",
                                    },
                                    {
                                        "name": "FILL_PERCENTAGE",
                                        "value": fill_percentage,
                                    },
                                    {"name": "TARGET_CONTAINER", "value": target_app},
                                ]
                            }
                        },
                    }
                ],
                "jobCleanUpPolicy": "delete",
            },
        }
        return ChaosExperiment(name, "disk_fill", config)

    def run_experiment(self, experiment: ChaosExperiment) -> Dict[str, Any]:
        """Run a single chaos experiment"""
        logger.info(f"Running experiment: {experiment.name}")

        experiment.start_time = datetime.now()
        experiment.status = "running"

        try:
            # Create experiment YAML file
            experiment_file = f"/tmp/{experiment.name}.yaml"
            with open(experiment_file, "w") as f:
                json.dump(experiment.config, f, indent=2)

            # Apply the experiment
            result = subprocess.run(
                ["kubectl", "apply", "-f", experiment_file],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise Exception(f"Failed to apply experiment: {result.stderr}")

            # Wait for experiment to complete
            experiment_name = experiment.config["metadata"]["name"]
            self._wait_for_experiment_completion(experiment_name)

            # Get experiment results
            results = self._get_experiment_results(experiment_name)
            experiment.results = results
            experiment.status = "completed"
            experiment.end_time = datetime.now()

            # Cleanup
            os.remove(experiment_file)
            subprocess.run(
                [
                    "kubectl",
                    "delete",
                    "chaosengine",
                    experiment_name,
                    "-n",
                    self.namespace,
                ],
                capture_output=True,
            )

            logger.info(f"Experiment {experiment.name} completed successfully")
            return results

        except Exception as e:
            logger.error(f"Experiment {experiment.name} failed: {str(e)}")
            experiment.status = "failed"
            experiment.end_time = datetime.now()
            experiment.results = {"error": str(e)}
            return experiment.results

    def _wait_for_experiment_completion(
        self, experiment_name: str, timeout: int = 300
    ) -> None:
        """Wait for chaos experiment to complete"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            result = subprocess.run(
                [
                    "kubectl",
                    "get",
                    "chaosengine",
                    experiment_name,
                    "-n",
                    self.namespace,
                    "-o",
                    "jsonpath={.status.experimentStatus.phase}",
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                phase = result.stdout.strip()
                if phase in ["Completed", "Failed", "Stopped"]:
                    return
            time.sleep(10)

        raise TimeoutError(
            f"Experiment {experiment_name} did not complete within {timeout} seconds"
        )

    def _get_experiment_results(self, experiment_name: str) -> Dict[str, Any]:
        """Get results from completed experiment"""
        result = subprocess.run(
            [
                "kubectl",
                "get",
                "chaosresult",
                "-n",
                self.namespace,
                "-l",
                f"name={experiment_name}",
                "-o",
                "json",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            try:
                chaos_result: Dict[str, Any] = json.loads(result.stdout)
                return chaos_result
            except json.JSONDecodeError:
                pass

        return {"status": "unknown", "message": "Could not retrieve detailed results"}

    def run_all_experiments(self) -> Dict[str, Any]:
        """Run all configured experiments"""
        results = {
            "total_experiments": len(self.experiments),
            "completed": 0,
            "failed": 0,
            "experiments": [],
        }

        for experiment in self.experiments:
            self.run_experiment(experiment)
            results["experiments"].append(experiment.to_dict())

            if experiment.status == "completed":
                results["completed"] += 1  # type: ignore
            else:
                results["failed"] += 1  # type: ignore

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(self.results_dir, f"chaos_results_{timestamp}.json")
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Chaos testing completed. Results saved to {results_file}")
        return results

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive chaos engineering report"""
        report = f"""
# Chaos Engineering Report - HMS Enterprise System
Generated: {datetime.now().isoformat()}

## Summary
- Total Experiments: {results['total_experiments']}
- Completed: {results['completed']}
- Failed: {results['failed']}
- Success Rate: {(results['completed'] / results['total_experiments'] * 100):.1f}%

## Experiment Details
"""

        for exp in results["experiments"]:
            report += f"""
### {exp['name']} ({exp['experiment_type']})
- Status: {exp['status']}
- Start Time: {exp['start_time']}
- End Time: {exp['end_time']}
- Duration: {self._calculate_duration(exp['start_time'], exp['end_time'])}
"""

            if exp["results"].get("error"):
                report += f"- Error: {exp['results']['error']}\n"
            else:
                report += f"- Results: {json.dumps(exp['results'], indent=2)}\n"

        return report

    def _calculate_duration(self, start: Optional[str], end: Optional[str]) -> str:
        """Calculate experiment duration"""
        if not start or not end:
            return "N/A"

        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        duration = end_dt - start_dt
        return f"{duration.total_seconds():.1f}s"


def main() -> None:
    parser = argparse.ArgumentParser(description="Chaos Engineering Framework for HMS")
    parser.add_argument(
        "--namespace",
        default="chaos",
        help="Kubernetes namespace for chaos experiments",
    )
    parser.add_argument(
        "--target-apps",
        nargs="+",
        default=["backend", "frontend", "postgres", "redis"],
        help="Target applications for chaos experiments",
    )
    parser.add_argument(
        "--duration", default="60s", help="Duration for each experiment"
    )
    parser.add_argument(
        "--experiment-types",
        nargs="+",
        choices=[
            "pod_failure",
            "network_delay",
            "cpu_stress",
            "memory_stress",
            "disk_fill",
            "all",
        ],
        default=["all"],
        help="Types of chaos experiments to run",
    )

    args = parser.parse_args()

    # Initialize chaos framework
    framework = ChaosFramework(namespace=args.namespace)

    # Create experiments based on types
    experiment_types = args.experiment_types
    if "all" in experiment_types:
        experiment_types = [
            "pod_failure",
            "network_delay",
            "cpu_stress",
            "memory_stress",
            "disk_fill",
        ]

    for app in args.target_apps:
        for exp_type in experiment_types:
            exp = None
            if exp_type == "pod_failure":
                exp = framework.create_pod_failure_experiment(
                    f"{app}-pod-failure", app, args.duration
                )
            elif exp_type == "network_delay":
                exp = framework.create_network_delay_experiment(
                    f"{app}-network-delay", app, "2000ms", args.duration
                )
            elif exp_type == "cpu_stress":
                exp = framework.create_cpu_stress_experiment(
                    f"{app}-cpu-stress", app, "2", args.duration
                )
            elif exp_type == "memory_stress":
                exp = framework.create_memory_stress_experiment(
                    f"{app}-memory-stress", app, "256", args.duration
                )
            elif exp_type == "disk_fill":
                exp = framework.create_disk_fill_experiment(
                    f"{app}-disk-fill", app, "50", args.duration
                )

            if exp:
                framework.add_experiment(exp)

    # Run experiments
    logger.info(
        f"Starting chaos engineering with {len(framework.experiments)} experiments"
    )
    results = framework.run_all_experiments()

    # Generate and save report
    report = framework.generate_report(results)
    report_file = os.path.join(
        framework.results_dir,
        f"chaos_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
    )
    with open(report_file, "w") as f:
        f.write(report)

    logger.info(f"Chaos engineering report saved to {report_file}")

    # Exit with appropriate code
    if results["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
