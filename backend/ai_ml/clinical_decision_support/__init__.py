"""
__init__ module
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.utils import timezone

from ..core.feature_engineering import FeatureEngineeringPipeline, FeatureType
from ..core.inference_engine import InferenceEngine, InferencePriority
from ..core.model_monitoring import ModelMonitoring
from ..core.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


class ClinicalPriority(Enum):
    EMERGENCY = "emergency"
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DecisionType(Enum):
    DIAGNOSTIC = "diagnostic"
    TREATMENT = "treatment"
    MONITORING = "monitoring"
    PREVENTION = "prevention"
    DRUG_INTERACTION = "drug_interaction"
    CLINICAL_PATHWAY = "clinical_pathway"


class AlertSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ClinicalData:
    patient_id: str
    demographics: Dict[str, Any]
    vital_signs: Dict[str, Any]
    laboratory_results: Dict[str, Any]
    medical_history: List[Dict[str, Any]]
    current_medications: List[Dict[str, Any]]
    allergies: List[str]
    symptoms: List[Dict[str, Any]]
    imaging_studies: List[Dict[str, Any]]
    social_determinants: Optional[Dict[str, Any]] = None

    def to_feature_dict(self) -> Dict[str, Any]:
        return {
            "demographics": self.demographics,
            "vital_signs": self.vital_signs,
            "laboratory_results": self.laboratory_results,
            "medical_history": self.medical_history,
            "current_medications": self.current_medications,
            "allergies": self.allergies,
            "symptoms": self.symptoms,
            "imaging_studies": self.imaging_studies,
            "social_determinants": self.social_determinants or {},
        }


@dataclass
class ClinicalDecision:
    decision_id: str
    decision_type: DecisionType
    priority: ClinicalPriority
    recommendation: str
    confidence: float
    evidence: List[Dict[str, Any]]
    alternatives: List[Dict[str, Any]]
    risks: List[Dict[str, Any]]
    contraindications: List[Dict[str, Any]]
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "decision_type": self.decision_type.value,
            "priority": self.priority.value,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "alternatives": self.alternatives,
            "risks": self.risks,
            "contraindications": self.contraindications,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ClinicalAlert:
    alert_id: str
    patient_id: str
    severity: AlertSeverity
    alert_type: str
    message: str
    action_required: str
    evidence: List[Dict[str, Any]]
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "patient_id": self.patient_id,
            "severity": self.severity.value,
            "alert_type": self.alert_type,
            "message": self.message,
            "action_required": self.action_required,
            "evidence": self.evidence,
            "timestamp": self.timestamp.isoformat(),
        }


class DiagnosticAssistanceSystem:
    def __init__(self):
        self.inference_engine = InferenceEngine()
        self.model_registry = ModelRegistry()
        self.feature_engineering = FeatureEngineeringPipeline()
        self.model_monitoring = ModelMonitoring()

    def analyze_symptoms(self, clinical_data: ClinicalData) -> List[ClinicalDecision]:
        try:
            features = self.feature_engineering.engineer_features(
                clinical_data.to_feature_dict(),
                [
                    FeatureType.DEMOGRAPHICS,
                    FeatureType.VITAL_SIGNS,
                    FeatureType.LABORATORY,
                    FeatureType.SYMPTOMS,
                ],
            )
            diagnosis_model_id = "differential_diagnosis_v2"
            predictions = self.inference_engine.predict(
                diagnosis_model_id, features, priority=InferencePriority.HIGH
            )
            decisions = []
            for i, prediction in enumerate(predictions.get("predictions", [])):
                decision = ClinicalDecision(
                    decision_id=f"diag_{clinical_data.patient_id}_{i}",
                    decision_type=DecisionType.DIAGNOSTIC,
                    priority=self._determine_diagnosis_priority(
                        prediction["probability"]
                    ),
                    recommendation=prediction.get("condition", "Unknown condition"),
                    confidence=prediction.get("probability", 0.0),
                    evidence=prediction.get("evidence", []),
                    alternatives=prediction.get("alternatives", []),
                    risks=prediction.get("risks", []),
                    contraindications=prediction.get("contraindications", []),
                    timestamp=timezone.now(),
                )
                decisions.append(decision)
                self.model_monitoring.log_prediction(
                    diagnosis_model_id,
                    features,
                    prediction,
                    None,
                )
            return decisions
        except Exception as e:
            logger.error(f"Error in symptom analysis: {str(e)}")
            return []

    def _determine_diagnosis_priority(self, probability: float) -> ClinicalPriority:
        if probability >= 0.9:
            return ClinicalPriority.HIGH
        elif probability >= 0.7:
            return ClinicalPriority.MEDIUM
        else:
            return ClinicalPriority.LOW


class TreatmentOptimizationEngine:
    def __init__(self):
        self.inference_engine = InferenceEngine()
        self.model_registry = ModelRegistry()
        self.feature_engineering = FeatureEngineeringPipeline()

    def recommend_treatment(
        self,
        clinical_data: ClinicalData,
        diagnosis: str,
        comorbidities: List[str] = None,
    ) -> List[ClinicalDecision]:
        try:
            features = self.feature_engineering.engineer_features(
                clinical_data.to_feature_dict(),
                [
                    FeatureType.DEMOGRAPHICS,
                    FeatureType.VITAL_SIGNS,
                    FeatureType.LABORATORY,
                    FeatureType.TREATMENT_HISTORY,
                ],
            )
            features["diagnosis"] = diagnosis
            features["comorbidities"] = comorbidities or []
            treatment_model_id = "treatment_optimization_v1"
            predictions = self.inference_engine.predict(
                treatment_model_id, features, priority=InferencePriority.HIGH
            )
            decisions = []
            for i, prediction in enumerate(predictions.get("treatments", [])):
                decision = ClinicalDecision(
                    decision_id=f"tx_{clinical_data.patient_id}_{i}",
                    decision_type=DecisionType.TREATMENT,
                    priority=ClinicalPriority.HIGH,
                    recommendation=prediction.get(
                        "treatment_plan", "Standard treatment"
                    ),
                    confidence=prediction.get("efficacy_score", 0.0),
                    evidence=prediction.get("evidence", []),
                    alternatives=prediction.get("alternatives", []),
                    risks=prediction.get("adverse_effects", []),
                    contraindications=prediction.get("contraindications", []),
                    timestamp=timezone.now(),
                )
                decisions.append(decision)
            return decisions
        except Exception as e:
            logger.error(f"Error in treatment recommendation: {str(e)}")
            return []


class DrugInteractionChecker:
    def __init__(self):
        self.interaction_database = self._load_interaction_database()

    def _load_interaction_database(self) -> Dict[str, List[Dict]]:
        return {
            "warfarin": [
                {
                    "drug": "aspirin",
                    "severity": "high",
                    "effect": "increased bleeding risk",
                },
                {
                    "drug": "ibuprofen",
                    "severity": "high",
                    "effect": "increased bleeding risk",
                },
                {
                    "drug": "amiodarone",
                    "severity": "moderate",
                    "effect": "increased INR",
                },
            ],
            "lisinopril": [
                {
                    "drug": "potassium_supplements",
                    "severity": "high",
                    "effect": "hyperkalemia",
                },
                {
                    "drug": "nsaids",
                    "severity": "moderate",
                    "effect": "reduced efficacy",
                },
            ],
        }

    def check_interactions(
        self, medications: List[Dict[str, Any]], patient_data: Dict[str, Any] = None
    ) -> List[ClinicalAlert]:
        alerts = []
        medication_names = [med.get("name", "").lower() for med in medications]
        for i, med1 in enumerate(medication_names):
            if med1 in self.interaction_database:
                for interaction in self.interaction_database[med1]:
                    if interaction["drug"] in medication_names:
                        severity = self._map_severity(interaction["severity"])
                        alert = ClinicalAlert(
                            alert_id=f"drug_interaction_{hash(med1 + interaction['drug'])}",
                            patient_id=(
                                patient_data.get("patient_id", "unknown")
                                if patient_data
                                else "unknown"
                            ),
                            severity=severity,
                            alert_type="drug_interaction",
                            message=f"Potential interaction between {med1} and {interaction['drug']}: {interaction['effect']}",
                            action_required=self._get_action_recommendation(severity),
                            evidence=[interaction],
                            timestamp=timezone.now(),
                        )
                        alerts.append(alert)
        return alerts

    def _map_severity(self, severity_str: str) -> AlertSeverity:
        mapping = {
            "high": AlertSeverity.HIGH,
            "moderate": AlertSeverity.MEDIUM,
            "low": AlertSeverity.LOW,
            "critical": AlertSeverity.CRITICAL,
        }
        return mapping.get(severity_str.lower(), AlertSeverity.MEDIUM)

    def _get_action_recommendation(self, severity: AlertSeverity) -> str:
        recommendations = {
            AlertSeverity.CRITICAL: "Immediate medical attention required",
            AlertSeverity.HIGH: "Consult physician immediately",
            AlertSeverity.MEDIUM: "Monitor patient closely",
            AlertSeverity.LOW: "Consider alternative medications",
        }
        return recommendations.get(severity, "Monitor patient")


class ClinicalPathwayOptimizer:
    def __init__(self):
        self.inference_engine = InferenceEngine()
        self.feature_engineering = FeatureEngineeringPipeline()

    def optimize_pathway(
        self, patient_data: ClinicalData, condition: str, current_pathway: str = None
    ) -> List[ClinicalDecision]:
        try:
            features = self.feature_engineering.engineer_features(
                patient_data.to_feature_dict(),
                [
                    FeatureType.DEMOGRAPHICS,
                    FeatureType.VITAL_SIGNS,
                    FeatureType.LABORATORY,
                    FeatureType.SOCIAL_DETERMINANTS,
                ],
            )
            features["condition"] = condition
            features["current_pathway"] = current_pathway
            pathway_model_id = "pathway_optimization_v1"
            predictions = self.inference_engine.predict(
                pathway_model_id, features, priority=InferencePriority.MEDIUM
            )
            decisions = []
            for i, prediction in enumerate(predictions.get("pathways", [])):
                decision = ClinicalDecision(
                    decision_id=f"pathway_{patient_data.patient_id}_{i}",
                    decision_type=DecisionType.CLINICAL_PATHWAY,
                    priority=ClinicalPriority.MEDIUM,
                    recommendation=prediction.get(
                        "optimized_pathway", "Standard pathway"
                    ),
                    confidence=prediction.get("optimization_score", 0.0),
                    evidence=prediction.get("evidence", []),
                    alternatives=prediction.get("alternative_pathways", []),
                    risks=prediction.get("risks", []),
                    contraindications=prediction.get("contraindications", []),
                    timestamp=timezone.now(),
                )
                decisions.append(decision)
            return decisions
        except Exception as e:
            logger.error(f"Error in pathway optimization: {str(e)}")
            return []


class ClinicalDecisionSupportSystem:
    def __init__(self):
        self.diagnostic_system = DiagnosticAssistanceSystem()
        self.treatment_engine = TreatmentOptimizationEngine()
        self.drug_checker = DrugInteractionChecker()
        self.pathway_optimizer = ClinicalPathwayOptimizer()

    def analyze_patient(self, clinical_data: ClinicalData) -> Dict[str, Any]:
        try:
            results = {
                "patient_id": clinical_data.patient_id,
                "timestamp": timezone.now().isoformat(),
                "diagnoses": [],
                "treatments": [],
                "alerts": [],
                "pathway_recommendations": [],
            }
            diagnoses = self.diagnostic_system.analyze_symptoms(clinical_data)
            results["diagnoses"] = [d.to_dict() for d in diagnoses]
            alerts = self.drug_checker.check_interactions(
                clinical_data.current_medications,
                {"patient_id": clinical_data.patient_id},
            )
            results["alerts"] = [a.to_dict() for a in alerts]
            if diagnoses:
                for diagnosis in diagnoses[:3]:
                    treatments = self.treatment_engine.recommend_treatment(
                        clinical_data,
                        diagnosis.recommendation,
                        [d.recommendation for d in diagnoses[1:]],
                    )
                    results["treatments"].extend([t.to_dict() for t in treatments])
            if diagnoses:
                pathway_recs = self.pathway_optimizer.optimize_pathway(
                    clinical_data, diagnoses[0].recommendation
                )
                results["pathway_recommendations"] = [p.to_dict() for p in pathway_recs]
            results["summary"] = self._generate_summary(results)
            return results
        except Exception as e:
            logger.error(f"Error in comprehensive patient analysis: {str(e)}")
            return {"error": str(e), "timestamp": timezone.now().isoformat()}

    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        summary = {
            "critical_alerts": len(
                [a for a in results.get("alerts", []) if a["severity"] == "critical"]
            ),
            "high_alerts": len(
                [a for a in results.get("alerts", []) if a["severity"] == "high"]
            ),
            "top_diagnosis": results.get("diagnoses", [{}])[0].get(
                "recommendation", "Unknown"
            ),
            "treatment_recommendations": len(results.get("treatments", [])),
            "pathway_optimizations": len(results.get("pathway_recommendations", [])),
        }
        return summary


def create_clinical_decision_support_api():
    from rest_framework import status, viewsets
    from rest_framework.decorators import action
    from rest_framework.permissions import IsAuthenticated
    from rest_framework.response import Response

    class ClinicalDecisionSupportViewSet(viewsets.ViewSet):
        permission_classes = [IsAuthenticated]

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.cdss = ClinicalDecisionSupportSystem()

        @action(detail=False, methods=["post"])
        def analyze_patient(self, request):
            try:
                clinical_data = ClinicalData(
                    patient_id=request.data.get("patient_id"),
                    demographics=request.data.get("demographics", {}),
                    vital_signs=request.data.get("vital_signs", {}),
                    laboratory_results=request.data.get("laboratory_results", {}),
                    medical_history=request.data.get("medical_history", []),
                    current_medications=request.data.get("current_medications", []),
                    allergies=request.data.get("allergies", []),
                    symptoms=request.data.get("symptoms", []),
                    imaging_studies=request.data.get("imaging_studies", []),
                    social_determinants=request.data.get("social_determinants"),
                )
                results = self.cdss.analyze_patient(clinical_data)
                return Response(results, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        @action(detail=False, methods=["post"])
        def check_drug_interactions(self, request):
            try:
                medications = request.data.get("medications", [])
                patient_id = request.data.get("patient_id")
                alerts = self.cdss.drug_checker.check_interactions(
                    medications, {"patient_id": patient_id}
                )
                return Response(
                    {
                        "alerts": [a.to_dict() for a in alerts],
                        "patient_id": patient_id,
                        "timestamp": timezone.now().isoformat(),
                    },
                    status=status.HTTP_200_OK,
                )
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    return ClinicalDecisionSupportViewSet
