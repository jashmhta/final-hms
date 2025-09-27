"""
model_monitoring module
"""

import json
import logging
import warnings
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from scipy.spatial.distance import jensenshannon
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class DriftType(Enum):
    CONCEPT_DRIFT = "concept_drift"
    DATA_DRIFT = "data_drift"
    PREDICTION_DRIFT = "prediction_drift"
    PERFORMANCE_DRIFT = "performance_drift"


class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MonitoringMetrics:
    model_id: str
    timestamp: datetime
    performance_metrics: Dict[str, float]
    data_quality_metrics: Dict[str, float]
    drift_metrics: Dict[str, Dict[str, float]]
    system_metrics: Dict[str, float]
    prediction_metrics: Dict[str, Any]
    sample_count: int
    latency_ms: float


@dataclass
class DriftAlert:
    alert_id: str
    model_id: str
    drift_type: DriftType
    severity: AlertSeverity
    drift_score: float
    threshold: float
    detected_at: datetime
    description: str
    recommendations: List[str]
    metadata: Optional[Dict] = None


class ModelMonitoring:
    def __init__(
        self,
        alert_thresholds: Optional[Dict] = None,
        monitoring_window: int = 1000,
        baseline_window: int = 5000,
    ):
        self.alert_thresholds = alert_thresholds or self._default_thresholds()
        self.monitoring_window = monitoring_window
        self.baseline_window = baseline_window
        self.baseline_data = {}
        self.monitoring_data = {}
        self.performance_history = {}
        self.alerts = []
        self.drift_detectors = {
            DriftType.DATA_DRIFT: self._detect_data_drift,
            DriftType.CONCEPT_DRIFT: self._detect_concept_drift,
            DriftType.PREDICTION_DRIFT: self._detect_prediction_drift,
            DriftType.PERFORMANCE_DRIFT: self._detect_performance_drift,
        }
        self.performance_tracking = {
            "accuracy": [],
            "precision": [],
            "recall": [],
            "f1_score": [],
            "roc_auc": [],
            "latency": [],
            "throughput": [],
        }

    def _default_thresholds(self) -> Dict:
        return {
            "data_drift": 0.1,
            "concept_drift": 0.15,
            "prediction_drift": 0.1,
            "performance_drift": 0.1,
            "latency_threshold": 1000,
            "error_rate_threshold": 0.05,
            "data_quality_threshold": 0.1,
        }

    def log_prediction(
        self,
        model_id: str,
        input_data: Union[Dict, np.ndarray],
        prediction: Any,
        ground_truth: Optional[Any] = None,
        prediction_time: float = None,
        metadata: Optional[Dict] = None,
    ):
        try:
            timestamp = timezone.now()
            if model_id not in self.monitoring_data:
                self.monitoring_data[model_id] = {
                    "predictions": [],
                    "inputs": [],
                    "ground_truths": [],
                    "timestamps": [],
                    "latencies": [],
                    "metadata": [],
                }
            self.monitoring_data[model_id]["predictions"].append(prediction)
            self.monitoring_data[model_id]["inputs"].append(input_data)
            self.monitoring_data[model_id]["ground_truths"].append(ground_truth)
            self.monitoring_data[model_id]["timestamps"].append(timestamp)
            self.monitoring_data[model_id]["latencies"].append(prediction_time or 0)
            self.monitoring_data[model_id]["metadata"].append(metadata or {})
            if (
                len(self.monitoring_data[model_id]["predictions"])
                > self.monitoring_window
            ):
                for key in self.monitoring_data[model_id]:
                    self.monitoring_data[model_id][key] = self.monitoring_data[
                        model_id
                    ][key][-self.monitoring_window :]
            if len(self.monitoring_data[model_id]["predictions"]) % 100 == 0:
                self.analyze_model_health(model_id)
        except Exception as e:
            logger.error(f"Failed to log prediction for model {model_id}: {e}")

    def analyze_model_health(self, model_id: str) -> MonitoringMetrics:
        try:
            model_data = self.monitoring_data.get(model_id, {})
            if not model_data or len(model_data["predictions"]) < 10:
                return self._create_empty_metrics(model_id)
            performance_metrics = self._calculate_performance_metrics(model_id)
            data_quality_metrics = self._calculate_data_quality_metrics(model_id)
            drift_metrics = self._detect_all_drift(model_id)
            system_metrics = self._calculate_system_metrics(model_id)
            prediction_metrics = self._calculate_prediction_metrics(model_id)
            monitoring_metrics = MonitoringMetrics(
                model_id=model_id,
                timestamp=timezone.now(),
                performance_metrics=performance_metrics,
                data_quality_metrics=data_quality_metrics,
                drift_metrics=drift_metrics,
                system_metrics=system_metrics,
                prediction_metrics=prediction_metrics,
                sample_count=len(model_data["predictions"]),
                latency_ms=np.mean(model_data["latencies"]),
            )
            self._check_for_alerts(monitoring_metrics)
            if model_id not in self.performance_history:
                self.performance_history[model_id] = []
            self.performance_history[model_id].append(monitoring_metrics)
            cache_key = f"monitoring_{model_id}"
            cache.set(cache_key, asdict(monitoring_metrics), timeout=3600)
            return monitoring_metrics
        except Exception as e:
            logger.error(f"Model health analysis failed for {model_id}: {e}")
            return self._create_empty_metrics(model_id)

    def _calculate_performance_metrics(self, model_id: str) -> Dict[str, float]:
        model_data = self.monitoring_data.get(model_id, {})
        predictions = model_data.get("predictions", [])
        ground_truths = model_data.get("ground_truths", [])
        valid_indices = [i for i, gt in enumerate(ground_truths) if gt is not None]
        if len(valid_indices) < 5:
            return {}
        valid_predictions = [predictions[i] for i in valid_indices]
        valid_ground_truths = [ground_truths[i] for i in valid_indices]
        metrics = {}
        try:
            if len(set(valid_ground_truths)) <= 10:
                metrics["accuracy"] = accuracy_score(
                    valid_ground_truths, valid_predictions
                )
                metrics["precision"] = precision_score(
                    valid_ground_truths, valid_predictions, average="weighted"
                )
                metrics["recall"] = recall_score(
                    valid_ground_truths, valid_predictions, average="weighted"
                )
                metrics["f1_score"] = f1_score(
                    valid_ground_truths, valid_predictions, average="weighted"
                )
                if len(set(valid_ground_truths)) == 2:
                    try:
                        metrics["roc_auc"] = roc_auc_score(
                            valid_ground_truths, valid_predictions
                        )
                    except:
                        metrics["roc_auc"] = 0.0
            else:
                from sklearn.metrics import (
                    mean_absolute_error,
                    mean_squared_error,
                    r2_score,
                )

                metrics["mse"] = mean_squared_error(
                    valid_ground_truths, valid_predictions
                )
                metrics["mae"] = mean_absolute_error(
                    valid_ground_truths, valid_predictions
                )
                metrics["r2_score"] = r2_score(valid_ground_truths, valid_predictions)
        except Exception as e:
            logger.error(f"Performance metric calculation failed: {e}")
        return metrics

    def _calculate_data_quality_metrics(self, model_id: str) -> Dict[str, float]:
        model_data = self.monitoring_data.get(model_id, {})
        inputs = model_data.get("inputs", [])
        if not inputs:
            return {}
        metrics = {}
        try:
            if isinstance(inputs[0], dict):
                df = pd.DataFrame(inputs)
            elif isinstance(inputs[0], (list, np.ndarray)):
                df = pd.DataFrame(inputs)
            else:
                return {}
            missing_rate = df.isnull().sum().sum() / (df.shape[0] * df.shape[1])
            metrics["missing_value_rate"] = missing_rate
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            outlier_count = 0
            total_count = 0
            for col in numeric_cols:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                outliers = df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]
                outlier_count += len(outliers)
                total_count += len(df[col])
            metrics["outlier_rate"] = (
                outlier_count / total_count if total_count > 0 else 0
            )
            type_consistency = 1.0
            for col in df.columns:
                unique_types = df[col].apply(type).nunique()
                if unique_types > 1:
                    type_consistency *= (unique_types - 1) / unique_types
            metrics["type_consistency"] = type_consistency
        except Exception as e:
            logger.error(f"Data quality calculation failed: {e}")
        return metrics

    def _detect_all_drift(self, model_id: str) -> Dict[str, Dict[str, float]]:
        drift_metrics = {}
        for drift_type, detector in self.drift_detectors.items():
            try:
                drift_result = detector(model_id)
                if drift_result:
                    drift_metrics[drift_type.value] = drift_result
            except Exception as e:
                logger.error(f"Drift detection failed for {drift_type}: {e}")
        return drift_metrics

    def _detect_data_drift(self, model_id: str) -> Dict[str, float]:
        model_data = self.monitoring_data.get(model_id, {})
        inputs = model_data.get("inputs", [])
        if len(inputs) < 100 or model_id not in self.baseline_data:
            return {}
        try:
            if isinstance(inputs[0], dict):
                current_df = pd.DataFrame(inputs)
                baseline_df = pd.DataFrame(self.baseline_data[model_id]["inputs"])
            else:
                current_df = pd.DataFrame(inputs)
                baseline_df = pd.DataFrame(self.baseline_data[model_id]["inputs"])
            drift_scores = {}
            numeric_cols = current_df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if col in baseline_df.columns:
                    ks_stat, ks_pvalue = stats.ks_2samp(
                        baseline_df[col].dropna(), current_df[col].dropna()
                    )
                    drift_scores[f"{col}_ks_stat"] = ks_stat
                    drift_scores[f"{col}_ks_pvalue"] = ks_pvalue
                    try:
                        js_divergence = self._calculate_js_divergence(
                            baseline_df[col].dropna(), current_df[col].dropna()
                        )
                        drift_scores[f"{col}_js_divergence"] = js_divergence
                    except:
                        drift_scores[f"{col}_js_divergence"] = 0.0
            overall_drift = np.mean(
                [score for key, score in drift_scores.items() if "js_divergence" in key]
            )
            drift_scores["overall_data_drift"] = overall_drift
            return drift_scores
        except Exception as e:
            logger.error(f"Data drift detection failed: {e}")
            return {}

    def _detect_concept_drift(self, model_id: str) -> Dict[str, float]:
        model_data = self.monitoring_data.get(model_id, {})
        predictions = model_data.get("predictions", [])
        ground_truths = model_data.get("ground_truths", [])
        valid_indices = [i for i, gt in enumerate(ground_truths) if gt is not None]
        if len(valid_indices) < 50:
            return {}
        try:
            recent_predictions = [predictions[i] for i in valid_indices[-100:]]
            recent_ground_truths = [ground_truths[i] for i in valid_indices[-100:]]
            recent_accuracy = accuracy_score(recent_ground_truths, recent_predictions)
            if len(valid_indices) > 200:
                baseline_predictions = [predictions[i] for i in valid_indices[:-100]]
                baseline_ground_truths = [
                    ground_truths[i] for i in valid_indices[:-100]
                ]
                baseline_accuracy = accuracy_score(
                    baseline_ground_truths, baseline_predictions
                )
                performance_drop = baseline_accuracy - recent_accuracy
                concept_drift_score = max(0, performance_drop)
                return {
                    "baseline_accuracy": baseline_accuracy,
                    "recent_accuracy": recent_accuracy,
                    "performance_drop": performance_drop,
                    "concept_drift_score": concept_drift_score,
                }
        except Exception as e:
            logger.error(f"Concept drift detection failed: {e}")
        return {}

    def _detect_prediction_drift(self, model_id: str) -> Dict[str, float]:
        model_data = self.monitoring_data.get(model_id, {})
        predictions = model_data.get("predictions", [])
        if len(predictions) < 100 or model_id not in self.baseline_data:
            return {}
        try:
            baseline_predictions = self.baseline_data[model_id]["predictions"]
            if isinstance(predictions[0], (int, float, np.integer, np.floating)):
                baseline_dist = np.histogram(baseline_predictions, bins=20)[0]
                current_dist = np.histogram(predictions, bins=20)[0]
                baseline_dist = baseline_dist / baseline_dist.sum()
                current_dist = current_dist / current_dist.sum()
                js_divergence = jensenshannon(baseline_dist, current_dist)
                return {
                    "prediction_drift_js": js_divergence,
                    "baseline_mean": np.mean(baseline_predictions),
                    "current_mean": np.mean(predictions),
                    "baseline_std": np.std(baseline_predictions),
                    "current_std": np.std(predictions),
                }
            else:
                baseline_unique, baseline_counts = np.unique(
                    baseline_predictions, return_counts=True
                )
                current_unique, current_counts = np.unique(
                    predictions, return_counts=True
                )
                all_categories = np.union1d(baseline_unique, current_unique)
                baseline_probs = np.zeros(len(all_categories))
                current_probs = np.zeros(len(all_categories))
                for i, cat in enumerate(all_categories):
                    if cat in baseline_unique:
                        baseline_probs[i] = baseline_counts[
                            np.where(baseline_unique == cat)[0][0]
                        ] / len(baseline_predictions)
                    if cat in current_unique:
                        current_probs[i] = current_counts[
                            np.where(current_unique == cat)[0][0]
                        ] / len(predictions)
                js_divergence = jensenshannon(baseline_probs, current_probs)
                return {
                    "prediction_drift_js": js_divergence,
                    "prediction_distribution_shift": js_divergence
                    > self.alert_thresholds["prediction_drift"],
                }
        except Exception as e:
            logger.error(f"Prediction drift detection failed: {e}")
        return {}

    def _detect_performance_drift(self, model_id: str) -> Dict[str, float]:
        if (
            model_id not in self.performance_history
            or len(self.performance_history[model_id]) < 10
        ):
            return {}
        try:
            history = self.performance_history[model_id]
            recent_metrics = history[-10:]
            older_metrics = history[-50:-10] if len(history) >= 50 else history[:-10]
            if not older_metrics:
                return {}
            performance_changes = {}
            for metric in ["accuracy", "precision", "recall", "f1_score"]:
                recent_values = [
                    m.performance_metrics.get(metric, 0)
                    for m in recent_metrics
                    if m.performance_metrics
                ]
                older_values = [
                    m.performance_metrics.get(metric, 0)
                    for m in older_metrics
                    if m.performance_metrics
                ]
                if recent_values and older_values:
                    recent_avg = np.mean(recent_values)
                    older_avg = np.mean(older_values)
                    change = older_avg - recent_avg
                    relative_change = change / older_avg if older_avg != 0 else 0
                    performance_changes[f"{metric}_change"] = change
                    performance_changes[f"{metric}_relative_change"] = relative_change
            overall_drift = np.mean(
                [
                    abs(change)
                    for key, change in performance_changes.items()
                    if "relative_change" in key
                ]
            )
            performance_changes["overall_performance_drift"] = overall_drift
            return performance_changes
        except Exception as e:
            logger.error(f"Performance drift detection failed: {e}")
        return {}

    def _calculate_system_metrics(self, model_id: str) -> Dict[str, float]:
        model_data = self.monitoring_data.get(model_id, {})
        latencies = model_data.get("latencies", [])
        timestamps = model_data.get("timestamps", [])
        if not latencies:
            return {}
        try:
            metrics = {
                "avg_latency_ms": np.mean(latencies),
                "p95_latency_ms": np.percentile(latencies, 95),
                "p99_latency_ms": np.percentile(latencies, 99),
                "throughput_per_second": self._calculate_throughput(timestamps),
                "error_rate": self._calculate_error_rate(model_id),
            }
            return metrics
        except Exception as e:
            logger.error(f"System metrics calculation failed: {e}")
        return {}

    def _calculate_prediction_metrics(self, model_id: str) -> Dict[str, Any]:
        model_data = self.monitoring_data.get(model_id, {})
        predictions = model_data.get("predictions", [])
        if not predictions:
            return {}
        try:
            if isinstance(predictions[0], (int, float, np.integer, np.floating)):
                return {
                    "prediction_mean": np.mean(predictions),
                    "prediction_std": np.std(predictions),
                    "prediction_min": np.min(predictions),
                    "prediction_max": np.max(predictions),
                    "prediction_median": np.median(predictions),
                }
            else:
                unique, counts = np.unique(predictions, return_counts=True)
                return {
                    "prediction_distribution": dict(zip(unique, counts)),
                    "most_common_prediction": unique[np.argmax(counts)],
                    "prediction_entropy": self._calculate_entropy(
                        counts / len(predictions)
                    ),
                }
        except Exception as e:
            logger.error(f"Prediction metrics calculation failed: {e}")
        return {}

    def _calculate_js_divergence(self, p: np.ndarray, q: np.ndarray) -> float:
        p_hist, _ = np.histogram(p, bins=20, density=True)
        q_hist, _ = np.histogram(q, bins=20, density=True)
        p_hist = p_hist / p_hist.sum()
        q_hist = q_hist / q_hist.sum()
        m = 0.5 * (p_hist + q_hist)
        js_divergence = 0.5 * (stats.entropy(p_hist, m) + stats.entropy(q_hist, m))
        return js_divergence

    def _calculate_entropy(self, probabilities: np.ndarray) -> float:
        probabilities = probabilities[probabilities > 0]
        return -np.sum(probabilities * np.log2(probabilities))

    def _calculate_throughput(self, timestamps: List[datetime]) -> float:
        if len(timestamps) < 2:
            return 0.0
        time_span = (timestamps[-1] - timestamps[0]).total_seconds()
        if time_span > 0:
            return len(timestamps) / time_span
        return 0.0

    def _calculate_error_rate(self, model_id: str) -> float:
        model_data = self.monitoring_data.get(model_id, {})
        ground_truths = model_data.get("ground_truths", [])
        predictions = model_data.get("predictions", [])
        valid_indices = [i for i, gt in enumerate(ground_truths) if gt is not None]
        if not valid_indices:
            return 0.0
        valid_predictions = [predictions[i] for i in valid_indices]
        valid_ground_truths = [ground_truths[i] for i in valid_indices]
        errors = sum(
            1
            for pred, true_val in zip(valid_predictions, valid_ground_truths)
            if pred != true_val
        )
        return errors / len(valid_predictions)

    def _check_for_alerts(self, metrics: MonitoringMetrics):
        alerts = []
        if "data_drift" in metrics.drift_metrics:
            data_drift_score = metrics.drift_metrics["data_drift"].get(
                "overall_data_drift", 0
            )
            if data_drift_score > self.alert_thresholds["data_drift"]:
                alerts.append(
                    DriftAlert(
                        alert_id=f"data_drift_{int(timezone.now().timestamp())}",
                        model_id=metrics.model_id,
                        drift_type=DriftType.DATA_DRIFT,
                        severity=self._calculate_severity(
                            data_drift_score, self.alert_thresholds["data_drift"]
                        ),
                        drift_score=data_drift_score,
                        threshold=self.alert_thresholds["data_drift"],
                        detected_at=timezone.now(),
                        description=f"Data drift detected with score {data_drift_score:.3f}",
                        recommendations=[
                            "Investigate data pipeline for changes",
                            "Check data quality and preprocessing",
                            "Consider model retraining",
                        ],
                    )
                )
        if "performance_drift" in metrics.drift_metrics:
            perf_drift_score = metrics.drift_metrics["performance_drift"].get(
                "overall_performance_drift", 0
            )
            if perf_drift_score > self.alert_thresholds["performance_drift"]:
                alerts.append(
                    DriftAlert(
                        alert_id=f"perf_drift_{int(timezone.now().timestamp())}",
                        model_id=metrics.model_id,
                        drift_type=DriftType.PERFORMANCE_DRIFT,
                        severity=self._calculate_severity(
                            perf_drift_score, self.alert_thresholds["performance_drift"]
                        ),
                        drift_score=perf_drift_score,
                        threshold=self.alert_thresholds["performance_drift"],
                        detected_at=timezone.now(),
                        description=f"Performance drift detected with score {perf_drift_score:.3f}",
                        recommendations=[
                            "Review model performance metrics",
                            "Check for concept drift",
                            "Schedule model retraining",
                        ],
                    )
                )
        if (
            metrics.system_metrics.get("avg_latency_ms", 0)
            > self.alert_thresholds["latency_threshold"]
        ):
            alerts.append(
                DriftAlert(
                    alert_id=f"latency_{int(timezone.now().timestamp())}",
                    model_id=metrics.model_id,
                    drift_type=DriftType.PERFORMANCE_DRIFT,
                    severity=AlertSeverity.HIGH,
                    drift_score=metrics.system_metrics["avg_latency_ms"],
                    threshold=self.alert_thresholds["latency_threshold"],
                    detected_at=timezone.now(),
                    description=f"High latency detected: {metrics.system_metrics['avg_latency_ms']:.1f}ms",
                    recommendations=[
                        "Check system resources",
                        "Optimize model inference",
                        "Scale infrastructure if needed",
                    ],
                )
            )
        if (
            metrics.system_metrics.get("error_rate", 0)
            > self.alert_thresholds["error_rate_threshold"]
        ):
            alerts.append(
                DriftAlert(
                    alert_id=f"error_rate_{int(timezone.now().timestamp())}",
                    model_id=metrics.model_id,
                    drift_type=DriftType.PERFORMANCE_DRIFT,
                    severity=AlertSeverity.HIGH,
                    drift_score=metrics.system_metrics["error_rate"],
                    threshold=self.alert_thresholds["error_rate_threshold"],
                    detected_at=timezone.now(),
                    description=f"High error rate detected: {metrics.system_metrics['error_rate']:.3f}",
                    recommendations=[
                        "Investigate prediction errors",
                        "Check input data quality",
                        "Review model calibration",
                    ],
                )
            )
        self.alerts.extend(alerts)
        for alert in alerts:
            if alert.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
                logger.warning(f"ALERT: {alert.description} for model {alert.model_id}")

    def _calculate_severity(self, score: float, threshold: float) -> AlertSeverity:
        ratio = score / threshold
        if ratio >= 3.0:
            return AlertSeverity.CRITICAL
        elif ratio >= 2.0:
            return AlertSeverity.HIGH
        elif ratio >= 1.5:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW

    def _create_empty_metrics(self, model_id: str) -> MonitoringMetrics:
        return MonitoringMetrics(
            model_id=model_id,
            timestamp=timezone.now(),
            performance_metrics={},
            data_quality_metrics={},
            drift_metrics={},
            system_metrics={},
            prediction_metrics={},
            sample_count=0,
            latency_ms=0,
        )

    def set_baseline(self, model_id: str, baseline_data: Dict):
        self.baseline_data[model_id] = baseline_data
        logger.info(f"Baseline set for model {model_id}")

    def get_model_health_dashboard(self, model_id: str) -> Dict:
        try:
            cache_key = f"monitoring_{model_id}"
            cached_metrics = cache.get(cache_key)
            if cached_metrics:
                metrics = MonitoringMetrics(**cached_metrics)
            else:
                metrics = self.analyze_model_health(model_id)
            recent_alerts = [
                alert
                for alert in self.alerts
                if alert.model_id == model_id
                and (timezone.now() - alert.detected_at).days <= 7
            ]
            performance_trends = self._get_performance_trends(model_id)
            health_score = self._calculate_health_score(metrics)
            return {
                "model_id": model_id,
                "health_score": health_score,
                "overall_status": self._get_health_status(health_score),
                "current_metrics": asdict(metrics),
                "recent_alerts": [asdict(alert) for alert in recent_alerts],
                "performance_trends": performance_trends,
                "recommendations": self._generate_health_recommendations(
                    metrics, health_score
                ),
                "last_updated": timezone.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Health dashboard generation failed for {model_id}: {e}")
            return {"error": str(e)}

    def _get_performance_trends(self, model_id: str) -> Dict:
        if model_id not in self.performance_history:
            return {}
        history = self.performance_history[model_id]
        if len(history) < 2:
            return {}
        try:
            trends = {}
            metrics_to_track = [
                "accuracy",
                "precision",
                "recall",
                "f1_score",
                "latency_ms",
            ]
            for metric in metrics_to_track:
                values = []
                timestamps = []
                for metrics_point in history:
                    if metric in metrics_point.performance_metrics:
                        values.append(metrics_point.performance_metrics[metric])
                        timestamps.append(metrics_point.timestamp)
                if len(values) >= 2:
                    x = np.arange(len(values))
                    slope, intercept = np.polyfit(x, values, 1)
                    trends[metric] = {
                        "trend": "improving" if slope > 0 else "declining",
                        "slope": slope,
                        "current_value": values[-1],
                        "change_from_baseline": (
                            values[-1] - values[0] if len(values) > 1 else 0
                        ),
                        "timeline": [
                            {"timestamp": ts.isoformat(), "value": val}
                            for ts, val in zip(timestamps, values)
                        ],
                    }
            return trends
        except Exception as e:
            logger.error(f"Performance trends calculation failed: {e}")
            return {}

    def _calculate_health_score(self, metrics: MonitoringMetrics) -> float:
        score = 100.0
        if metrics.performance_metrics:
            accuracy = metrics.performance_metrics.get("accuracy", 1.0)
            score -= (1 - accuracy) * 30
        for drift_type, drift_data in metrics.drift_metrics.items():
            if "overall_" + drift_type in drift_data:
                drift_score = drift_data["overall_" + drift_type]
                score -= min(drift_score * 50, 20)
        if (
            metrics.system_metrics.get("avg_latency_ms", 0)
            > self.alert_thresholds["latency_threshold"]
        ):
            score -= 10
        if metrics.data_quality_metrics.get("missing_value_rate", 0) > 0.1:
            score -= 10
        return max(0, min(100, score))

    def _get_health_status(self, health_score: float) -> str:
        if health_score >= 90:
            return "Excellent"
        elif health_score >= 80:
            return "Good"
        elif health_score >= 70:
            return "Fair"
        elif health_score >= 60:
            return "Poor"
        else:
            return "Critical"

    def _generate_health_recommendations(
        self, metrics: MonitoringMetrics, health_score: float
    ) -> List[str]:
        recommendations = []
        if health_score < 70:
            recommendations.append(
                "Model performance is suboptimal - consider retraining"
            )
        if metrics.system_metrics.get("avg_latency_ms", 0) > 500:
            recommendations.append(
                "High latency detected - optimize inference pipeline"
            )
        if metrics.data_quality_metrics.get("missing_value_rate", 0) > 0.1:
            recommendations.append("High missing data rate - improve data quality")
        for drift_type, drift_data in metrics.drift_metrics.items():
            if "overall_" + drift_type in drift_data:
                drift_score = drift_data["overall_" + drift_type]
                if drift_score > self.alert_thresholds["data_drift"]:
                    recommendations.append(
                        f"Significant {drift_type} detected - investigate data changes"
                    )
        return recommendations

    def get_monitoring_report(self, model_id: str, days: int = 30) -> Dict:
        try:
            dashboard = self.get_model_health_dashboard(model_id)
            cutoff_date = timezone.now() - timedelta(days=days)
            historical_data = [
                metrics
                for metrics in self.performance_history.get(model_id, [])
                if metrics.timestamp > cutoff_date
            ]
            report = {
                "model_id": model_id,
                "report_period": f"Last {days} days",
                "summary": dashboard,
                "statistics": self._calculate_monitoring_statistics(historical_data),
                "alert_summary": self._summarize_alerts(model_id, days),
                "recommendations": self._generate_monitoring_recommendations(
                    dashboard, historical_data
                ),
                "generated_at": timezone.now().isoformat(),
            }
            return report
        except Exception as e:
            logger.error(f"Monitoring report generation failed: {e}")
            return {"error": str(e)}

    def _calculate_monitoring_statistics(
        self, historical_data: List[MonitoringMetrics]
    ) -> Dict:
        if not historical_data:
            return {}
        stats = {}
        performance_metrics = ["accuracy", "precision", "recall", "f1_score"]
        for metric in performance_metrics:
            values = [
                m.performance_metrics.get(metric, 0)
                for m in historical_data
                if metric in m.performance_metrics
            ]
            if values:
                stats[f"{metric}_stats"] = {
                    "mean": np.mean(values),
                    "std": np.std(values),
                    "min": np.min(values),
                    "max": np.max(values),
                    "trend": self._calculate_trend(values),
                }
        latencies = [m.latency_ms for m in historical_data]
        if latencies:
            stats["latency_stats"] = {
                "mean": np.mean(latencies),
                "p95": np.percentile(latencies, 95),
                "p99": np.percentile(latencies, 99),
                "max": np.max(latencies),
            }
        return stats

    def _calculate_trend(self, values: List[float]) -> str:
        if len(values) < 2:
            return "stable"
        x = np.arange(len(values))
        slope, _ = np.polyfit(x, values, 1)
        if slope > 0.01:
            return "improving"
        elif slope < -0.01:
            return "declining"
        else:
            return "stable"

    def _summarize_alerts(self, model_id: str, days: int) -> Dict:
        cutoff_date = timezone.now() - timedelta(days=days)
        recent_alerts = [
            alert
            for alert in self.alerts
            if alert.model_id == model_id and alert.detected_at > cutoff_date
        ]
        summary = {
            "total_alerts": len(recent_alerts),
            "by_severity": {},
            "by_type": {},
            "most_common_issue": None,
        }
        for alert in recent_alerts:
            severity = alert.severity.value
            summary["by_severity"][severity] = (
                summary["by_severity"].get(severity, 0) + 1
            )
            drift_type = alert.drift_type.value
            summary["by_type"][drift_type] = summary["by_type"].get(drift_type, 0) + 1
        if summary["by_type"]:
            summary["most_common_issue"] = max(
                summary["by_type"].items(), key=lambda x: x[1]
            )[0]
        return summary

    def _generate_monitoring_recommendations(
        self, dashboard: Dict, historical_data: List[MonitoringMetrics]
    ) -> List[str]:
        recommendations = []
        if "health_score" in dashboard:
            health_score = dashboard["health_score"]
            if health_score < 70:
                recommendations.append(
                    "Model health is poor - immediate attention required"
                )
        if "alert_summary" in dashboard:
            total_alerts = dashboard["alert_summary"].get("total_alerts", 0)
            if total_alerts > 10:
                recommendations.append(
                    f"High alert frequency ({total_alerts} alerts) - investigate root causes"
                )
        if "statistics" in dashboard:
            for metric, stats in dashboard["statistics"].items():
                if "trend" in stats and stats["trend"] == "declining":
                    recommendations.append(
                        f"Declining trend in {metric} - investigate and address"
                    )
        recommendations.append("Continue regular monitoring and maintenance")
        recommendations.append(
            "Schedule periodic model retraining based on performance"
        )
        return recommendations

    def clear_monitoring_data(self, model_id: str):
        if model_id in self.monitoring_data:
            del self.monitoring_data[model_id]
        if model_id in self.performance_history:
            del self.performance_history[model_id]
        if model_id in self.baseline_data:
            del self.baseline_data[model_id]
        cache_key = f"monitoring_{model_id}"
        cache.delete(cache_key)
        logger.info(f"Monitoring data cleared for model {model_id}")


model_monitor = None


def get_model_monitor() -> ModelMonitoring:
    global model_monitor
    if model_monitor is None:
        model_monitor = ModelMonitoring()
    return model_monitor


def initialize_model_monitor(**kwargs):
    global model_monitor
    model_monitor = ModelMonitoring(**kwargs)
    return model_monitor
