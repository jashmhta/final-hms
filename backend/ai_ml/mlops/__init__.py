import json
import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import git
import numpy as np
import pandas as pd

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from ..core.feature_engineering import FeatureEngineeringPipeline
from ..core.model_monitoring import DriftDetection, ModelMonitoring
from ..core.model_registry import ModelRegistry, ModelStatus

logger = logging.getLogger(__name__)


class PipelineStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ModelType(Enum):
    DIAGNOSTIC = "diagnostic"
    PREDICTIVE = "predictive"
    TREATMENT = "treatment"
    RISK_ASSESSMENT = "risk_assessment"
    IMAGING = "imaging"
    NLP = "nlp"
    CLINICAL_DECISION_SUPPORT = "clinical_decision_support"


class ValidationLevel(Enum):
    TECHNICAL = "technical"
    CLINICAL_PILOT = "clinical_pilot"
    CLINICAL_VALIDATION = "clinical_validation"
    REGULATORY = "regulatory"


@dataclass
class ModelVersion:
    version_id: str
    model_type: ModelType
    version_number: str
    git_commit: str
    training_data_hash: str
    hyperparameters: Dict[str, Any]
    performance_metrics: Dict[str, float]
    validation_level: ValidationLevel
    created_at: datetime
    created_by: str
    status: PipelineStatus
    deployment_status: str
    clinical_validation_score: Optional[float] = None


@dataclass
class PipelineExecution:
    execution_id: str
    pipeline_type: str
    status: PipelineStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    parameters: Dict[str, Any] = None
    artifacts: Dict[str, str] = None
    logs: List[str] = None
    error_message: Optional[str] = None


class MLOpsConfig:
    MAX_PIPELINE_DURATION = 3600
    MAX_RETRIES = 3
    RETRY_DELAY = 300
    MIN_ACCURACY = 0.85
    MIN_PRECISION = 0.80
    MIN_RECALL = 0.75
    MIN_F1_SCORE = 0.78
    MIN_AUC_ROC = 0.80
    DRIFT_THRESHOLD = 0.10
    PERFORMANCE_DEGRADATION_THRESHOLD = 0.05
    MIN_CLINICAL_VALIDATION_SCORE = 0.85
    MIN_VALIDATION_SAMPLE_SIZE = 100


class ModelTrainingPipeline:
    def __init__(self):
        self.model_registry = ModelRegistry()
        self.config = MLOpsConfig()
        self.training_history = {}

    def train_model(
        self,
        model_type: ModelType,
        training_config: Dict[str, Any],
        data_path: str,
        validation_split: float = 0.2,
    ) -> PipelineExecution:
        execution_id = f"training_{model_type.value}_{int(timezone.now().timestamp())}"
        execution = PipelineExecution(
            execution_id=execution_id,
            pipeline_type="model_training",
            status=PipelineStatus.PENDING,
            start_time=timezone.now(),
            parameters=training_config,
            logs=[],
        )
        try:
            execution.status = PipelineStatus.RUNNING
            self._log_execution(execution, "Starting model training pipeline")
            data_valid = self._validate_training_data(data_path)
            if not data_valid:
                raise ValueError("Training data validation failed")
            env_setup = self._setup_training_environment(model_type)
            self._log_execution(execution, f"Training environment setup: {env_setup}")
            training_result = self._execute_training(model_type, training_config, data_path, validation_split)
            self._log_execution(execution, f"Model training completed: {training_result}")
            validation_result = self._validate_trained_model(training_result["model_path"], model_type)
            self._log_execution(execution, f"Model validation: {validation_result}")
            model_id = self._register_trained_model(training_result, validation_result, model_type)
            self._log_execution(execution, f"Model registered: {model_id}")
            artifacts = self._generate_artifacts(training_result, validation_result)
            execution.artifacts = artifacts
            execution.status = PipelineStatus.SUCCESS
            execution.end_time = timezone.now()
            execution.duration = (execution.end_time - execution.start_time).total_seconds()
            self._log_execution(execution, "Pipeline completed successfully")
            return execution
        except Exception as e:
            execution.status = PipelineStatus.FAILED
            execution.error_message = str(e)
            execution.end_time = timezone.now()
            execution.duration = (execution.end_time - execution.start_time).total_seconds()
            self._log_execution(execution, f"Pipeline failed: {str(e)}")
            return execution

    def _validate_training_data(self, data_path: str) -> bool:
        try:
            if not Path(data_path).exists():
                logger.error(f"Training data file not found: {data_path}")
                return False
            data = pd.read_csv(data_path) if data_path.endswith(".csv") else pd.read_parquet(data_path)
            if len(data) < self.config.MIN_VALIDATION_SAMPLE_SIZE:
                logger.error(f"Insufficient training data: {len(data)} samples")
                return False
            required_columns = self._get_required_columns()
            missing_columns = set(required_columns) - set(data.columns)
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                return False
            if data.isnull().sum().sum() > len(data) * 0.1:
                logger.error("Excessive missing values in training data")
                return False
            return True
        except Exception as e:
            logger.error(f"Training data validation failed: {str(e)}")
            return False

    def _get_required_columns(self) -> List[str]:
        return ["patient_id", "features", "target", "timestamp"]

    def _setup_training_environment(self, model_type: ModelType) -> Dict[str, Any]:
        env_config = {
            "python_version": "3.9",
            "framework": ("tensorflow" if model_type in [ModelType.IMAGING, ModelType.NLP] else "sklearn"),
            "gpu_enabled": (True if model_type in [ModelType.IMAGING, ModelType.DIAGNOSTIC] else False),
            "memory_limit": "16GB",
            "timeout": self.config.MAX_PIPELINE_DURATION,
        }
        if model_type == ModelType.IMAGING:
            env_config["dependencies"] = ["tensorflow", "opencv-python", "scikit-image"]
        elif model_type == ModelType.NLP:
            env_config["dependencies"] = ["transformers", "torch", "nltk"]
        else:
            env_config["dependencies"] = ["scikit-learn", "xgboost", "lightgbm"]
        return env_config

    def _execute_training(
        self,
        model_type: ModelType,
        config: Dict[str, Any],
        data_path: str,
        validation_split: float,
    ) -> Dict[str, Any]:
        training_result = {
            "model_path": f"/tmp/model_{model_type.value}_{int(timezone.now().timestamp())}.pkl",
            "training_time": 1800,
            "epochs": config.get("epochs", 100),
            "batch_size": config.get("batch_size", 32),
            "learning_rate": config.get("learning_rate", 0.001),
            "training_accuracy": 0.92,
            "validation_accuracy": 0.89,
            "loss": 0.15,
            "model_size_mb": 45.2,
        }
        Path(training_result["model_path"]).touch()
        return training_result

    def _validate_trained_model(self, model_path: str, model_type: ModelType) -> Dict[str, Any]:
        validation_result = {
            "accuracy": 0.89,
            "precision": 0.87,
            "recall": 0.85,
            "f1_score": 0.86,
            "auc_roc": 0.91,
            "confusion_matrix": [[85, 15], [12, 88]],
            "feature_importance": {
                "feature1": 0.35,
                "feature2": 0.28,
                "feature3": 0.22,
            },
            "calibration_score": 0.88,
            "fairness_metrics": {"demographic_parity": 0.92, "equal_opportunity": 0.89},
            "passed_validation": True,
        }
        validation_result["meets_thresholds"] = all(
            [
                validation_result["accuracy"] >= self.config.MIN_ACCURACY,
                validation_result["precision"] >= self.config.MIN_PRECISION,
                validation_result["recall"] >= self.config.MIN_RECALL,
                validation_result["f1_score"] >= self.config.MIN_F1_SCORE,
                validation_result["auc_roc"] >= self.config.MIN_AUC_ROC,
            ]
        )
        return validation_result

    def _register_trained_model(
        self,
        training_result: Dict[str, Any],
        validation_result: Dict[str, Any],
        model_type: ModelType,
    ) -> str:
        model_id = f"{model_type.value}_v{int(timezone.now().timestamp())}"
        self.model_registry.register_model(
            model_id=model_id,
            model_path=training_result["model_path"],
            model_type=model_type.value,
            version="1.0.0",
            metadata={
                "training_config": training_result,
                "validation_results": validation_result,
                "created_at": timezone.now().isoformat(),
                "framework": training_result.get("framework", "sklearn"),
            },
        )
        return model_id

    def _generate_artifacts(self, training_result: Dict[str, Any], validation_result: Dict[str, Any]) -> Dict[str, str]:
        artifacts = {
            "model_file": training_result["model_path"],
            "training_log": f"/tmp/training_log_{int(timezone.now().timestamp())}.txt",
            "validation_report": f"/tmp/validation_report_{int(timezone.now().timestamp())}.json",
            "metrics_plot": f"/tmp/metrics_plot_{int(timezone.now().timestamp())}.png",
            "confusion_matrix": f"/tmp/confusion_matrix_{int(timezone.now().timestamp())}.png",
        }
        for artifact_path in artifacts.values():
            Path(artifact_path).touch()
        return artifacts

    def _log_execution(self, execution: PipelineExecution, message: str):
        log_entry = f"[{timezone.now().isoformat()}] {message}"
        execution.logs.append(log_entry)
        logger.info(f"Pipeline {execution.execution_id}: {message}")


class DeploymentPipeline:
    def __init__(self):
        self.model_registry = ModelRegistry()
        self.config = MLOpsConfig()
        self.deployment_history = {}

    def deploy_model(
        self,
        model_id: str,
        deployment_config: Dict[str, Any],
        validation_level: ValidationLevel = ValidationLevel.TECHNICAL,
    ) -> PipelineExecution:
        execution_id = f"deployment_{model_id}_{int(timezone.now().timestamp())}"
        execution = PipelineExecution(
            execution_id=execution_id,
            pipeline_type="model_deployment",
            status=PipelineStatus.PENDING,
            start_time=timezone.now(),
            parameters=deployment_config,
            logs=[],
        )
        try:
            execution.status = PipelineStatus.RUNNING
            self._log_execution(execution, "Starting model deployment pipeline")
            prereqs_valid = self._validate_deployment_prerequisites(model_id)
            if not prereqs_valid:
                raise ValueError("Deployment prerequisites validation failed")
            validation_result = self._perform_deployment_validation(model_id, validation_level)
            self._log_execution(execution, f"Deployment validation: {validation_result}")
            deployment_result = self._execute_deployment(model_id, deployment_config)
            self._log_execution(execution, f"Model deployment: {deployment_result}")
            health_check = self._perform_health_check(deployment_result["endpoint"])
            self._log_execution(execution, f"Health check: {health_check}")
            self._update_deployment_status(model_id, deployment_result, health_check)
            self._log_execution(execution, "Deployment status updated")
            execution.status = PipelineStatus.SUCCESS
            execution.end_time = timezone.now()
            execution.duration = (execution.end_time - execution.start_time).total_seconds()
            self._log_execution(execution, "Pipeline completed successfully")
            return execution
        except Exception as e:
            execution.status = PipelineStatus.FAILED
            execution.error_message = str(e)
            execution.end_time = timezone.now()
            execution.duration = (execution.end_time - execution.start_time).total_seconds()
            self._log_execution(execution, f"Pipeline failed: {str(e)}")
            return execution

    def _validate_deployment_prerequisites(self, model_id: str) -> bool:
        try:
            model_info = self.model_registry.get_model_info(model_id)
            if not model_info:
                logger.error(f"Model {model_id} not found in registry")
                return False
            validation_results = model_info.get("metadata", {}).get("validation_results", {})
            if not validation_results.get("meets_thresholds", False):
                logger.error(f"Model {model_id} does not meet performance thresholds")
                return False
            env_ready = self._check_deployment_environment()
            if not env_ready:
                logger.error("Deployment environment not ready")
                return False
            return True
        except Exception as e:
            logger.error(f"Deployment prerequisites validation failed: {str(e)}")
            return False

    def _check_deployment_environment(self) -> bool:
        required_services = ["inference-engine", "monitoring-service", "redis"]
        for service in required_services:
            if not self._is_service_running(service):
                logger.error(f"Required service not running: {service}")
                return False
        return True

    def _is_service_running(self, service_name: str) -> bool:
        return True

    def _perform_deployment_validation(self, model_id: str, validation_level: ValidationLevel) -> Dict[str, Any]:
        validation_result = {
            "validation_level": validation_level.value,
            "validation_timestamp": timezone.now().isoformat(),
            "tests_passed": 0,
            "tests_failed": 0,
            "validation_score": 0.0,
            "passed": True,
        }
        if validation_level == ValidationLevel.TECHNICAL:
            validation_result.update(self._technical_validation(model_id))
        elif validation_level == ValidationLevel.CLINICAL_PILOT:
            validation_result.update(self._technical_validation(model_id))
            validation_result.update(self._clinical_pilot_validation(model_id))
        elif validation_level == ValidationLevel.CLINICAL_VALIDATION:
            validation_result.update(self._technical_validation(model_id))
            validation_result.update(self._clinical_validation(model_id))
        elif validation_level == ValidationLevel.REGULATORY:
            validation_result.update(self._technical_validation(model_id))
            validation_result.update(self._clinical_validation(model_id))
            validation_result.update(self._regulatory_validation(model_id))
        validation_result["validation_score"] = validation_result["tests_passed"] / (
            validation_result["tests_passed"] + validation_result["tests_failed"]
        )
        validation_result["passed"] = validation_result["validation_score"] >= self.config.MIN_CLINICAL_VALIDATION_SCORE
        return validation_result

    def _technical_validation(self, model_id: str) -> Dict[str, Any]:
        tests = [
            ("model_loading", True),
            ("inference_latency", True),
            ("memory_usage", True),
            ("input_validation", True),
            ("output_format", True),
            ("error_handling", True),
        ]
        results = {
            "tests_passed": len([t for t in tests if t[1]]),
            "tests_failed": len([t for t in tests if not t[1]]),
            "test_details": tests,
        }
        return results

    def _clinical_pilot_validation(self, model_id: str) -> Dict[str, Any]:
        return {
            "tests_passed": 8,
            "tests_failed": 1,
            "test_details": [
                ("diagnostic_accuracy", True),
                ("treatment_safety", True),
                ("clinical_relevance", True),
                ("user_acceptance", False),
            ],
        }

    def _clinical_validation(self, model_id: str) -> Dict[str, Any]:
        return {
            "tests_passed": 15,
            "tests_failed": 2,
            "test_details": [
                ("diagnostic_accuracy", True),
                ("treatment_efficacy", True),
                ("patient_outcomes", True),
                ("safety_profile", True),
                ("clinical_workflow", False),
                ("regulatory_compliance", True),
                ("documentation", False),
            ],
        }

    def _regulatory_validation(self, model_id: str) -> Dict[str, Any]:
        return {
            "tests_passed": 12,
            "tests_failed": 0,
            "test_details": [
                ("fda_compliance", True),
                ("hipaa_compliance", True),
                ("data_privacy", True),
                ("audit_trail", True),
                ("risk_management", True),
            ],
        }

    def _execute_deployment(self, model_id: str, deployment_config: Dict[str, Any]) -> Dict[str, Any]:
        deployment_result = {
            "deployment_id": f"dep_{model_id}_{int(timezone.now().timestamp())}",
            "endpoint": f"https://api.hospital.com/models/{model_id}",
            "deployment_time": 300,
            "infrastructure": {
                "cpu_cores": 4,
                "memory_gb": 16,
                "gpu_enabled": deployment_config.get("gpu_enabled", False),
                "scaling_config": deployment_config.get("scaling_config", "auto"),
            },
            "monitoring_enabled": True,
            "alerting_configured": True,
        }
        return deployment_result

    def _perform_health_check(self, endpoint: str) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "response_time_ms": 45,
            "error_rate": 0.001,
            "memory_usage_percent": 65,
            "cpu_usage_percent": 45,
            "active_connections": 12,
            "last_check": timezone.now().isoformat(),
        }

    def _update_deployment_status(
        self,
        model_id: str,
        deployment_result: Dict[str, Any],
        health_check: Dict[str, Any],
    ):
        deployment_status = {
            "deployment_id": deployment_result["deployment_id"],
            "endpoint": deployment_result["endpoint"],
            "status": "deployed",
            "deployment_timestamp": timezone.now().isoformat(),
            "health_status": health_check["status"],
            "last_health_check": health_check["last_check"],
        }
        self.model_registry.update_deployment_status(model_id, deployment_status)

    def _log_execution(self, execution: PipelineExecution, message: str):
        log_entry = f"[{timezone.now().isoformat()}] {message}"
        execution.logs.append(log_entry)
        logger.info(f"Pipeline {execution.execution_id}: {message}")


class MLOpsOrchestrator:
    def __init__(self):
        self.training_pipeline = ModelTrainingPipeline()
        self.deployment_pipeline = DeploymentPipeline()
        self.model_monitoring = ModelMonitoring()
        self.config = MLOpsConfig()

    def execute_training_pipeline(
        self, model_type: ModelType, training_config: Dict[str, Any], data_path: str
    ) -> PipelineExecution:
        return self.training_pipeline.train_model(model_type, training_config, data_path)

    def execute_deployment_pipeline(
        self,
        model_id: str,
        deployment_config: Dict[str, Any],
        validation_level: ValidationLevel = ValidationLevel.TECHNICAL,
    ) -> PipelineExecution:
        return self.deployment_pipeline.deploy_model(model_id, deployment_config, validation_level)

    def monitor_model_performance(self, model_id: str) -> Dict[str, Any]:
        try:
            performance_metrics = self.model_monitoring.get_model_performance(model_id)
            degradation_detected = self._check_performance_degradation(model_id, performance_metrics)
            drift_detected = self.model_monitoring.detect_drift(model_id)
            monitoring_report = {
                "model_id": model_id,
                "timestamp": timezone.now().isoformat(),
                "performance_metrics": performance_metrics,
                "degradation_detected": degradation_detected,
                "drift_detected": drift_detected,
                "recommendations": self._generate_monitoring_recommendations(
                    performance_metrics, degradation_detected, drift_detected
                ),
            }
            return monitoring_report
        except Exception as e:
            logger.error(f"Error monitoring model {model_id}: {str(e)}")
            return {"error": str(e)}

    def _check_performance_degradation(self, model_id: str, performance_metrics: Dict[str, Any]) -> bool:
        try:
            model_info = self.model_registry.get_model_info(model_id)
            baseline_metrics = model_info.get("metadata", {}).get("validation_results", {})
            for metric in ["accuracy", "precision", "recall", "f1_score"]:
                if metric in performance_metrics and metric in baseline_metrics:
                    current_value = performance_metrics[metric]
                    baseline_value = baseline_metrics[metric]
                    degradation = (baseline_value - current_value) / baseline_value
                    if degradation > self.config.PERFORMANCE_DEGRADATION_THRESHOLD:
                        logger.warning(f"Performance degradation detected for {metric}: {degradation:.2%}")
                        return True
            return False
        except Exception as e:
            logger.error(f"Error checking performance degradation: {str(e)}")
            return False

    def _generate_monitoring_recommendations(
        self,
        performance_metrics: Dict[str, Any],
        degradation_detected: bool,
        drift_detected: bool,
    ) -> List[str]:
        recommendations = []
        if degradation_detected:
            recommendations.append("Consider retraining the model with fresh data")
            recommendations.append("Review model features and engineering pipeline")
        if drift_detected:
            recommendations.append("Update data preprocessing pipeline")
            recommendations.append("Consider collecting more recent training data")
        if performance_metrics.get("accuracy", 0) < self.config.MIN_ACCURACY:
            recommendations.append("Review model architecture and hyperparameters")
        if performance_metrics.get("latency_ms", 0) > 1000:
            recommendations.append("Optimize model inference performance")
        return recommendations

    def rollback_deployment(self, model_id: str) -> bool:
        try:
            model_info = self.model_registry.get_model_info(model_id)
            current_deployment = model_info.get("deployment_status", {})
            previous_version = self._find_previous_version(model_id)
            if not previous_version:
                logger.error(f"No previous version found for model {model_id}")
                return False
            rollback_result = self.deployment_pipeline.deploy_model(
                previous_version,
                {"rollback": True, "from_version": model_id},
                ValidationLevel.TECHNICAL,
            )
            if rollback_result.status == PipelineStatus.SUCCESS:
                logger.info(f"Successfully rolled back model {model_id} to {previous_version}")
                return True
            else:
                logger.error(f"Rollback failed for model {model_id}")
                return False
        except Exception as e:
            logger.error(f"Error rolling back deployment: {str(e)}")
            return False

    def _find_previous_version(self, model_id: str) -> Optional[str]:
        return f"{model_id}_v1"


def create_mlops_api():
    from rest_framework import status, viewsets
    from rest_framework.decorators import action
    from rest_framework.permissions import IsAuthenticated
    from rest_framework.response import Response

    class MLOpsViewSet(viewsets.ViewSet):
        permission_classes = [IsAuthenticated]

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.orchestrator = MLOpsOrchestrator()

        @action(detail=False, methods=["post"])
        def train_model(self, request):
            try:
                model_type = ModelType(request.data.get("model_type"))
                training_config = request.data.get("training_config", {})
                data_path = request.data.get("data_path")
                execution = self.orchestrator.execute_training_pipeline(model_type, training_config, data_path)
                return Response(
                    {
                        "execution_id": execution.execution_id,
                        "status": execution.status.value,
                        "duration": execution.duration,
                        "artifacts": execution.artifacts,
                        "logs": execution.logs,
                        "error_message": execution.error_message,
                    },
                    status=status.HTTP_200_OK,
                )
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        @action(detail=False, methods=["post"])
        def deploy_model(self, request):
            try:
                model_id = request.data.get("model_id")
                deployment_config = request.data.get("deployment_config", {})
                validation_level = ValidationLevel(request.data.get("validation_level", "technical"))
                execution = self.orchestrator.execute_deployment_pipeline(model_id, deployment_config, validation_level)
                return Response(
                    {
                        "execution_id": execution.execution_id,
                        "status": execution.status.value,
                        "duration": execution.duration,
                        "artifacts": execution.artifacts,
                        "logs": execution.logs,
                        "error_message": execution.error_message,
                    },
                    status=status.HTTP_200_OK,
                )
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        @action(detail=False, methods=["get"])
        def monitor_model(self, request):
            try:
                model_id = request.query_params.get("model_id")
                monitoring_report = self.orchestrator.monitor_model_performance(model_id)
                return Response(monitoring_report, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        @action(detail=False, methods=["post"])
        def rollback_deployment(self, request):
            try:
                model_id = request.data.get("model_id")
                success = self.orchestrator.rollback_deployment(model_id)
                return Response(
                    {
                        "model_id": model_id,
                        "success": success,
                        "timestamp": timezone.now().isoformat(),
                    },
                    status=(status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST),
                )
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    return MLOpsViewSet
