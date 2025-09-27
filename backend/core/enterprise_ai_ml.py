"""
Enterprise-Grade AI/ML Healthcare Intelligence Framework
Implements predictive analytics, medical image analysis, and clinical decision support
"""

import json
import logging
import pickle
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import joblib
import numpy as np
import pandas as pd
import pytesseract
import redis
import spacy
import tensorflow as tf
from PIL import Image
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from tensorflow import keras
from tensorflow.keras import layers
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

from django.conf import settings
from django.db import connection


class AIModelType(Enum):
    """AI model types"""

    PREDICTIVE = "predictive"
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    NLP = "nlp"
    COMPUTER_VISION = "computer_vision"
    RECOMMENDATION = "recommendation"


class PredictionType(Enum):
    """Prediction types for healthcare"""

    PATIENT_OUTCOME = "patient_outcome"
    DISEASE_RISK = "disease_risk"
    READMISSION_RISK = "readmission_risk"
    TREATMENT_RESPONSE = "treatment_response"
    DRUG_INTERACTION = "drug_interaction"
    MORTALITY_RISK = "mortality_risk"


@dataclass
class PatientData:
    """Patient data structure for AI models"""

    patient_id: str
    age: int
    gender: str
    medical_history: List[str]
    current_medications: List[str]
    lab_results: Dict[str, float]
    vital_signs: Dict[str, float]
    symptoms: List[str]
    diagnosis: List[str]
    treatment_plan: List[str]
    outcomes: Dict[str, Any]


@dataclass
class PredictionResult:
    """Prediction result structure"""

    prediction: Any
    confidence: float
    model_version: str
    timestamp: datetime
    features_used: List[str]
    interpretation: str
    recommendations: List[str]


class HealthcareAIManager:
    """
    Enterprise AI/ML manager for healthcare applications
    Coordinates all AI models and provides unified interface
    """

    def __init__(self):
        self.logger = logging.getLogger("healthcare.ai")
        self.redis_client = redis.from_url(settings.REDIS_URL)

        # Initialize model registry
        self.model_registry = {}
        self.model_versions = {}

        # Initialize prediction cache
        self.prediction_cache_ttl = 3600  # 1 hour

        # Load pre-trained models
        self._load_models()

        # Initialize NLP pipelines
        self._initialize_nlp_pipelines()

    def _load_models(self):
        """Load pre-trained AI models"""
        try:
            # Load predictive models
            self._load_predictive_models()

            # Load classification models
            self._load_classification_models()

            # Load NLP models
            self._load_nlp_models()

            # Load computer vision models
            self._load_computer_vision_models()

            self.logger.info("AI models loaded successfully")

        except Exception as e:
            self.logger.error(f"Model loading error: {e}")

    def _initialize_nlp_pipelines(self):
        """Initialize NLP processing pipelines"""
        try:
            # Medical text analysis
            self.medical_nlp = spacy.load("en_core_medical_lg")  # Medical NLP model

            # Clinical notes analysis
            self.clinical_notes_analyzer = pipeline(
                "text-classification", model="emilyalsentzer/Bio_ClinicalBERT"
            )

            # Drug interaction detection
            self.drug_interaction_analyzer = pipeline(
                "text-classification",
                model="samrawal/bert-base-uncased-drug-interaction",
            )

        except Exception as e:
            self.logger.error(f"NLP initialization error: {e}")

    def predict_patient_outcome(self, patient_data: PatientData) -> PredictionResult:
        """Predict patient outcome using ensemble of AI models"""
        try:
            # Check cache first
            cache_key = f"outcome_prediction:{patient_data.patient_id}"
            cached_result = self._get_cached_prediction(cache_key)
            if cached_result:
                return cached_result

            # Prepare features
            features = self._extract_outcome_features(patient_data)

            # Get predictions from multiple models
            predictions = []
            confidences = []

            # Predictive model
            pred_outcome = self._predict_with_model(
                "patient_outcome_predictor", features
            )
            predictions.append(pred_outcome["prediction"])
            confidences.append(pred_outcome["confidence"])

            # Risk assessment model
            risk_assessment = self._predict_with_model("risk_assessment", features)
            predictions.append(risk_assessment["prediction"])
            confidences.append(risk_assessment["confidence"])

            # Ensemble prediction
            final_prediction = self._ensemble_predictions(predictions, confidences)

            # Generate interpretation
            interpretation = self._generate_outcome_interpretation(
                final_prediction, features, patient_data
            )

            # Generate recommendations
            recommendations = self._generate_outcome_recommendations(
                final_prediction, patient_data
            )

            result = PredictionResult(
                prediction=final_prediction,
                confidence=max(confidences),
                model_version="1.0.0",
                timestamp=datetime.now(),
                features_used=list(features.keys()),
                interpretation=interpretation,
                recommendations=recommendations,
            )

            # Cache result
            self._cache_prediction(cache_key, result)

            return result

        except Exception as e:
            self.logger.error(f"Patient outcome prediction error: {e}")
            raise

    def predict_disease_risk(
        self, patient_data: PatientData, disease: str
    ) -> PredictionResult:
        """Predict disease risk for specific conditions"""
        try:
            # Check cache first
            cache_key = f"disease_risk:{patient_data.patient_id}:{disease}"
            cached_result = self._get_cached_prediction(cache_key)
            if cached_result:
                return cached_result

            # Prepare disease-specific features
            features = self._extract_disease_features(patient_data, disease)

            # Get risk prediction
            risk_prediction = self._predict_with_model(
                f"disease_risk_{disease}", features
            )

            # Generate interpretation
            interpretation = self._generate_disease_risk_interpretation(
                risk_prediction["prediction"], disease, features, patient_data
            )

            # Generate recommendations
            recommendations = self._generate_disease_risk_recommendations(
                risk_prediction["prediction"], disease, patient_data
            )

            result = PredictionResult(
                prediction=risk_prediction["prediction"],
                confidence=risk_prediction["confidence"],
                model_version="1.0.0",
                timestamp=datetime.now(),
                features_used=list(features.keys()),
                interpretation=interpretation,
                recommendations=recommendations,
            )

            # Cache result
            self._cache_prediction(cache_key, result)

            return result

        except Exception as e:
            self.logger.error(f"Disease risk prediction error: {e}")
            raise

    def analyze_medical_image(self, image_path: str, image_type: str) -> Dict[str, Any]:
        """Analyze medical images (X-ray, MRI, CT scan, etc.)"""
        try:
            # Load and preprocess image
            image = self._preprocess_medical_image(image_path)

            # Analyze based on image type
            if image_type == "xray":
                return self._analyze_xray(image)
            elif image_type == "mri":
                return self._analyze_mri(image)
            elif image_type == "ct":
                return self._analyze_ct_scan(image)
            elif image_type == "ultrasound":
                return self._analyze_ultrasound(image)
            else:
                raise ValueError(f"Unsupported image type: {image_type}")

        except Exception as e:
            self.logger.error(f"Medical image analysis error: {e}")
            raise

    def analyze_clinical_notes(self, clinical_notes: str) -> Dict[str, Any]:
        """Analyze clinical notes using NLP"""
        try:
            results = {
                "entities": [],
                "sentiment": None,
                "key_findings": [],
                "recommendations": [],
                "urgency_level": "low",
            }

            # Extract medical entities
            doc = self.medical_nlp(clinical_notes)
            for ent in doc.ents:
                results["entities"].append(
                    {
                        "text": ent.text,
                        "label": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char,
                    }
                )

            # Analyze sentiment and urgency
            sentiment_result = self.clinical_notes_analyzer(clinical_notes)
            results["sentiment"] = sentiment_result[0]

            # Extract key findings
            results["key_findings"] = self._extract_key_findings(clinical_notes)

            # Determine urgency
            results["urgency_level"] = self._determine_urgency_level(clinical_notes)

            # Generate recommendations
            results["recommendations"] = self._generate_note_recommendations(results)

            return results

        except Exception as e:
            self.logger.error(f"Clinical notes analysis error: {e}")
            raise

    def detect_drug_interactions(
        self, medications: List[str], patient_data: PatientData
    ) -> Dict[str, Any]:
        """Detect potential drug interactions"""
        try:
            interactions = []

            # Check pairwise interactions
            for i, med1 in enumerate(medications):
                for j, med2 in enumerate(medications[i + 1 :], i + 1):
                    interaction = self._check_drug_interaction(med1, med2)
                    if interaction:
                        interactions.append(interaction)

            # Check interactions with patient conditions
            condition_interactions = self._check_condition_interactions(
                medications, patient_data
            )

            # Check dosage interactions
            dosage_interactions = self._check_dosage_interactions(
                medications, patient_data
            )

            return {
                "drug_interactions": interactions,
                "condition_interactions": condition_interactions,
                "dosage_interactions": dosage_interactions,
                "severity_score": self._calculate_interaction_severity(interactions),
                "recommendations": self._generate_interaction_recommendations(
                    interactions
                ),
            }

        except Exception as e:
            self.logger.error(f"Drug interaction detection error: {e}")
            raise

    def generate_treatment_recommendations(
        self, patient_data: PatientData
    ) -> Dict[str, Any]:
        """Generate AI-powered treatment recommendations"""
        try:
            recommendations = {
                "primary_treatment": None,
                "alternative_treatments": [],
                "lifestyle_changes": [],
                "follow_up_schedule": None,
                "monitoring_parameters": [],
                "risk_factors": [],
                "contraindications": [],
            }

            # Analyze patient data
            features = self._extract_treatment_features(patient_data)

            # Get treatment predictions
            treatment_prediction = self._predict_with_model(
                "treatment_recommender", features
            )

            # Generate primary treatment recommendation
            recommendations["primary_treatment"] = treatment_prediction["prediction"]

            # Generate alternative treatments
            recommendations["alternative_treatments"] = (
                self._generate_alternative_treatments(
                    patient_data, treatment_prediction["prediction"]
                )
            )

            # Generate lifestyle recommendations
            recommendations["lifestyle_changes"] = (
                self._generate_lifestyle_recommendations(patient_data)
            )

            # Generate follow-up schedule
            recommendations["follow_up_schedule"] = self._generate_follow_up_schedule(
                patient_data
            )

            # Generate monitoring parameters
            recommendations["monitoring_parameters"] = (
                self._generate_monitoring_parameters(patient_data)
            )

            # Identify risk factors
            recommendations["risk_factors"] = self._identify_risk_factors(patient_data)

            # Identify contraindications
            recommendations["contraindications"] = self._identify_contraindications(
                patient_data
            )

            return recommendations

        except Exception as e:
            self.logger.error(f"Treatment recommendation error: {e}")
            raise

    def _extract_outcome_features(self, patient_data: PatientData) -> Dict[str, float]:
        """Extract features for outcome prediction"""
        features = {}

        # Demographic features
        features["age"] = patient_data.age
        features["gender_male"] = 1 if patient_data.gender == "male" else 0
        features["gender_female"] = 1 if patient_data.gender == "female" else 0

        # Medical history features
        chronic_conditions = len(
            [h for h in patient_data.medical_history if self._is_chronic_condition(h)]
        )
        features["chronic_condition_count"] = chronic_conditions

        # Medication features
        features["medication_count"] = len(patient_data.current_medications)

        # Lab result features
        if patient_data.lab_results:
            features["abnormal_labs"] = len(
                [
                    lab
                    for lab, value in patient_data.lab_results.items()
                    if not self._is_normal_lab_value(lab, value)
                ]
            )

        # Vital signs features
        if patient_data.vital_signs:
            features["bp_systolic"] = patient_data.vital_signs.get(
                "blood_pressure_systolic", 120
            )
            features["bp_diastolic"] = patient_data.vital_signs.get(
                "blood_pressure_diastolic", 80
            )
            features["heart_rate"] = patient_data.vital_signs.get("heart_rate", 70)
            features["temperature"] = patient_data.vital_signs.get("temperature", 98.6)

        # Symptom features
        features["symptom_count"] = len(patient_data.symptoms)
        features["severe_symptoms"] = len(
            [s for s in patient_data.symptoms if self._is_severe_symptom(s)]
        )

        return features

    def _extract_disease_features(
        self, patient_data: PatientData, disease: str
    ) -> Dict[str, float]:
        """Extract disease-specific features"""
        features = self._extract_outcome_features(patient_data)

        # Add disease-specific features
        disease_features = self._get_disease_specific_features(disease)
        features.update(disease_features)

        return features

    def _extract_treatment_features(
        self, patient_data: PatientData
    ) -> Dict[str, float]:
        """Extract features for treatment recommendation"""
        features = self._extract_outcome_features(patient_data)

        # Add treatment-specific features
        features["treatment_history"] = len(patient_data.treatment_plan)
        features["treatment_adherence"] = self._calculate_treatment_adherence(
            patient_data
        )

        return features

    def _predict_with_model(
        self, model_name: str, features: Dict[str, float]
    ) -> Dict[str, Any]:
        """Make prediction with specified model"""
        try:
            model = self.model_registry.get(model_name)
            if not model:
                raise ValueError(f"Model {model_name} not found")

            # Prepare feature vector
            feature_vector = self._prepare_feature_vector(features, model_name)

            # Make prediction
            if hasattr(model, "predict_proba"):
                prediction = model.predict([feature_vector])[0]
                confidence = model.predict_proba([feature_vector])[0].max()
            else:
                prediction = model.predict([feature_vector])[0]
                confidence = 0.8  # Default confidence

            return {"prediction": prediction, "confidence": float(confidence)}

        except Exception as e:
            self.logger.error(f"Model prediction error: {e}")
            raise

    def _ensemble_predictions(
        self, predictions: List[Any], confidences: List[float]
    ) -> Any:
        """Ensemble multiple predictions"""
        # Simple weighted average based on confidence
        if isinstance(predictions[0], (int, float)):
            return sum(p * c for p, c in zip(predictions, confidences)) / sum(
                confidences
            )
        else:
            # For classification, use weighted voting
            vote_counts = {}
            for pred, conf in zip(predictions, confidences):
                vote_counts[pred] = vote_counts.get(pred, 0) + conf
            return max(vote_counts, key=vote_counts.get)

    def _preprocess_medical_image(self, image_path: str) -> np.ndarray:
        """Preprocess medical image for analysis"""
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Resize to standard size
        image = cv2.resize(image, (224, 224))

        # Normalize
        image = image.astype(np.float32) / 255.0

        return image

    def _analyze_xray(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze X-ray image"""
        try:
            # Load X-ray analysis model
            model = self.model_registry.get("xray_analyzer")
            if not model:
                return {"error": "X-ray analysis model not available"}

            # Make prediction
            prediction = model.predict(np.expand_dims(image, axis=0))[0]

            return {
                "findings": self._interpret_xray_prediction(prediction),
                "confidence": float(prediction.max()),
                "recommendations": self._generate_xray_recommendations(prediction),
            }

        except Exception as e:
            self.logger.error(f"X-ray analysis error: {e}")
            return {"error": str(e)}

    def _analyze_mri(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze MRI image"""
        try:
            # Load MRI analysis model
            model = self.model_registry.get("mri_analyzer")
            if not model:
                return {"error": "MRI analysis model not available"}

            # Make prediction
            prediction = model.predict(np.expand_dims(image, axis=0))[0]

            return {
                "findings": self._interpret_mri_prediction(prediction),
                "confidence": float(prediction.max()),
                "recommendations": self._generate_mri_recommendations(prediction),
            }

        except Exception as e:
            self.logger.error(f"MRI analysis error: {e}")
            return {"error": str(e)}

    def _analyze_ct_scan(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze CT scan image"""
        try:
            # Load CT analysis model
            model = self.model_registry.get("ct_analyzer")
            if not model:
                return {"error": "CT analysis model not available"}

            # Make prediction
            prediction = model.predict(np.expand_dims(image, axis=0))[0]

            return {
                "findings": self._interpret_ct_prediction(prediction),
                "confidence": float(prediction.max()),
                "recommendations": self._generate_ct_recommendations(prediction),
            }

        except Exception as e:
            self.logger.error(f"CT scan analysis error: {e}")
            return {"error": str(e)}

    def _analyze_ultrasound(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze ultrasound image"""
        try:
            # Load ultrasound analysis model
            model = self.model_registry.get("ultrasound_analyzer")
            if not model:
                return {"error": "Ultrasound analysis model not available"}

            # Make prediction
            prediction = model.predict(np.expand_dims(image, axis=0))[0]

            return {
                "findings": self._interpret_ultrasound_prediction(prediction),
                "confidence": float(prediction.max()),
                "recommendations": self._generate_ultrasound_recommendations(
                    prediction
                ),
            }

        except Exception as e:
            self.logger.error(f"Ultrasound analysis error: {e}")
            return {"error": str(e)}

    def _check_drug_interaction(self, med1: str, med2: str) -> Optional[Dict[str, Any]]:
        """Check for interaction between two drugs"""
        try:
            # Use drug interaction database or model
            interaction_key = f"interaction:{med1}:{med2}"
            cached_interaction = self.redis_client.get(interaction_key)

            if cached_interaction:
                return json.loads(cached_interaction)

            # For now, return mock interaction data
            # In practice, this would query a drug interaction database
            interaction = {
                "drug1": med1,
                "drug2": med2,
                "severity": "moderate",  # mild, moderate, severe
                "description": f"Potential interaction between {med1} and {med2}",
                "effects": ["increased risk of side effects"],
                "recommendations": [
                    "Monitor patient closely",
                    "Consider alternative medications",
                ],
            }

            # Cache result
            self.redis_client.setex(interaction_key, 86400, json.dumps(interaction))

            return interaction

        except Exception as e:
            self.logger.error(f"Drug interaction check error: {e}")
            return None

    def _generate_outcome_interpretation(
        self, prediction: Any, features: Dict[str, float], patient_data: PatientData
    ) -> str:
        """Generate interpretation for outcome prediction"""
        if isinstance(prediction, dict):
            outcome = prediction.get("outcome", "unknown")
            probability = prediction.get("probability", 0.5)
        else:
            outcome = prediction
            probability = 0.8

        interpretations = {
            "positive": f"Patient has a {probability:.1%} probability of positive outcome based on current condition and treatment plan.",
            "negative": f"Patient has a {(1-probability):.1%} probability of negative outcome. Consider alternative treatments.",
            "recovery": f"Patient shows {probability:.1%} probability of full recovery within expected timeframe.",
            "complications": f"Patient has {probability:.1%} risk of developing complications. Close monitoring recommended.",
        }

        return interpretations.get(
            outcome, f"Prediction: {outcome} with {probability:.1%} confidence"
        )

    def _generate_outcome_recommendations(
        self, prediction: Any, patient_data: PatientData
    ) -> List[str]:
        """Generate recommendations based on outcome prediction"""
        recommendations = []

        # General health recommendations
        recommendations.append("Continue regular monitoring of vital signs")
        recommendations.append("Maintain current medication regimen")

        # Age-specific recommendations
        if patient_data.age > 65:
            recommendations.append("Schedule more frequent follow-up appointments")
            recommendations.append("Monitor for age-related complications")

        # Condition-specific recommendations
        if "diabetes" in patient_data.medical_history:
            recommendations.append("Monitor blood glucose levels regularly")
            recommendations.append("Maintain diabetic diet")

        # Medication-specific recommendations
        if len(patient_data.current_medications) > 5:
            recommendations.append("Review medication list for potential interactions")
            recommendations.append("Consider medication reconciliation")

        return recommendations

    def _load_predictive_models(self):
        """Load predictive AI models"""
        try:
            # Patient outcome predictor
            outcome_model = self._load_or_create_model(
                "patient_outcome_predictor", "predictive"
            )
            if outcome_model:
                self.model_registry["patient_outcome_predictor"] = outcome_model

            # Risk assessment model
            risk_model = self._load_or_create_model("risk_assessment", "predictive")
            if risk_model:
                self.model_registry["risk_assessment"] = risk_model

        except Exception as e:
            self.logger.error(f"Predictive model loading error: {e}")

    def _load_classification_models(self):
        """Load classification AI models"""
        try:
            # Disease risk models
            diseases = ["diabetes", "heart_disease", "cancer", "respiratory"]
            for disease in diseases:
                model = self._load_or_create_model(
                    f"disease_risk_{disease}", "classification"
                )
                if model:
                    self.model_registry[f"disease_risk_{disease}"] = model

        except Exception as e:
            self.logger.error(f"Classification model loading error: {e}")

    def _load_nlp_models(self):
        """Load NLP models"""
        try:
            # Clinical notes analyzer
            self.model_registry["clinical_notes_analyzer"] = (
                self.clinical_notes_analyzer
            )

        except Exception as e:
            self.logger.error(f"NLP model loading error: {e}")

    def _load_computer_vision_models(self):
        """Load computer vision models"""
        try:
            # X-ray analyzer
            xray_model = self._load_or_create_model("xray_analyzer", "computer_vision")
            if xray_model:
                self.model_registry["xray_analyzer"] = xray_model

            # MRI analyzer
            mri_model = self._load_or_create_model("mri_analyzer", "computer_vision")
            if mri_model:
                self.model_registry["mri_analyzer"] = mri_model

        except Exception as e:
            self.logger.error(f"Computer vision model loading error: {e}")

    def _load_or_create_model(self, model_name: str, model_type: str) -> Optional[Any]:
        """Load model from file or create new one"""
        try:
            model_path = f"/models/{model_name}.pkl"
            if Path(model_path).exists():
                return joblib.load(model_path)
            else:
                return self._create_default_model(model_type)
        except Exception as e:
            self.logger.error(f"Model loading error for {model_name}: {e}")
            return None

    def _create_default_model(self, model_type: str) -> Any:
        """Create default model based on type"""
        if model_type == "predictive":
            return RandomForestClassifier(n_estimators=100, random_state=42)
        elif model_type == "classification":
            return LogisticRegression(random_state=42)
        elif model_type == "computer_vision":
            return self._create_default_cv_model()
        else:
            return RandomForestClassifier(random_state=42)

    def _create_default_cv_model(self) -> Any:
        """Create default computer vision model"""
        model = keras.Sequential(
            [
                layers.Conv2D(32, (3, 3), activation="relu", input_shape=(224, 224, 1)),
                layers.MaxPooling2D((2, 2)),
                layers.Conv2D(64, (3, 3), activation="relu"),
                layers.MaxPooling2D((2, 2)),
                layers.Conv2D(64, (3, 3), activation="relu"),
                layers.Flatten(),
                layers.Dense(64, activation="relu"),
                layers.Dense(10, activation="softmax"),
            ]
        )

        model.compile(
            optimizer="adam",
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )

        return model

    def _prepare_feature_vector(
        self, features: Dict[str, float], model_name: str
    ) -> List[float]:
        """Prepare feature vector for model input"""
        # This would handle feature scaling and ordering
        return list(features.values())

    def _get_cached_prediction(self, cache_key: str) -> Optional[PredictionResult]:
        """Get cached prediction"""
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                return PredictionResult(
                    prediction=data["prediction"],
                    confidence=data["confidence"],
                    model_version=data["model_version"],
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    features_used=data["features_used"],
                    interpretation=data["interpretation"],
                    recommendations=data["recommendations"],
                )
        except Exception as e:
            self.logger.error(f"Cache retrieval error: {e}")
        return None

    def _cache_prediction(self, cache_key: str, result: PredictionResult):
        """Cache prediction result"""
        try:
            data = {
                "prediction": result.prediction,
                "confidence": result.confidence,
                "model_version": result.model_version,
                "timestamp": result.timestamp.isoformat(),
                "features_used": result.features_used,
                "interpretation": result.interpretation,
                "recommendations": result.recommendations,
            }

            self.redis_client.setex(
                cache_key, self.prediction_cache_ttl, json.dumps(data)
            )

        except Exception as e:
            self.logger.error(f"Cache storage error: {e}")

    def _is_chronic_condition(self, condition: str) -> bool:
        """Check if condition is chronic"""
        chronic_conditions = [
            "diabetes",
            "hypertension",
            "heart_disease",
            "asthma",
            "copd",
        ]
        return condition.lower() in chronic_conditions

    def _is_normal_lab_value(self, lab: str, value: float) -> bool:
        """Check if lab value is within normal range"""
        normal_ranges = {
            "glucose": (70, 100),
            "blood_pressure_systolic": (90, 120),
            "blood_pressure_diastolic": (60, 80),
            "heart_rate": (60, 100),
            "temperature": (97.0, 99.0),
        }

        if lab in normal_ranges:
            min_val, max_val = normal_ranges[lab]
            return min_val <= value <= max_val

        return True  # Assume normal if not defined

    def _is_severe_symptom(self, symptom: str) -> bool:
        """Check if symptom is severe"""
        severe_symptoms = [
            "chest_pain",
            "shortness_of_breath",
            "severe_headache",
            "unconsciousness",
        ]
        return symptom.lower() in severe_symptoms

    def _get_disease_specific_features(self, disease: str) -> Dict[str, float]:
        """Get disease-specific features"""
        # This would return disease-specific features
        return {}

    def _interpret_xray_prediction(self, prediction: np.ndarray) -> List[str]:
        """Interpret X-ray prediction"""
        # This would interpret X-ray model output
        return ["Normal chest X-ray"]

    def _interpret_mri_prediction(self, prediction: np.ndarray) -> List[str]:
        """Interpret MRI prediction"""
        # This would interpret MRI model output
        return ["Normal brain MRI"]

    def _interpret_ct_prediction(self, prediction: np.ndarray) -> List[str]:
        """Interpret CT prediction"""
        # This would interpret CT model output
        return ["Normal CT scan"]

    def _interpret_ultrasound_prediction(self, prediction: np.ndarray) -> List[str]:
        """Interpret ultrasound prediction"""
        # This would interpret ultrasound model output
        return ["Normal ultrasound"]

    def _generate_xray_recommendations(self, prediction: np.ndarray) -> List[str]:
        """Generate X-ray recommendations"""
        return ["No follow-up required"]

    def _generate_mri_recommendations(self, prediction: np.ndarray) -> List[str]:
        """Generate MRI recommendations"""
        return ["No follow-up required"]

    def _generate_ct_recommendations(self, prediction: np.ndarray) -> List[str]:
        """Generate CT recommendations"""
        return ["No follow-up required"]

    def _generate_ultrasound_recommendations(self, prediction: np.ndarray) -> List[str]:
        """Generate ultrasound recommendations"""
        return ["No follow-up required"]

    def _extract_key_findings(self, clinical_notes: str) -> List[str]:
        """Extract key findings from clinical notes"""
        # This would use NLP to extract key findings
        return ["Patient reports feeling better"]

    def _determine_urgency_level(self, clinical_notes: str) -> str:
        """Determine urgency level from clinical notes"""
        # This would analyze text for urgency indicators
        return "low"

    def _generate_note_recommendations(
        self, analysis_results: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations from clinical notes analysis"""
        return ["Continue current treatment plan"]

    def _check_condition_interactions(
        self, medications: List[str], patient_data: PatientData
    ) -> List[Dict[str, Any]]:
        """Check interactions with patient conditions"""
        return []

    def _check_dosage_interactions(
        self, medications: List[str], patient_data: PatientData
    ) -> List[Dict[str, Any]]:
        """Check dosage interactions"""
        return []

    def _calculate_interaction_severity(
        self, interactions: List[Dict[str, Any]]
    ) -> float:
        """Calculate interaction severity score"""
        if not interactions:
            return 0.0

        severity_scores = {"mild": 1, "moderate": 2, "severe": 3}
        total_score = sum(
            severity_scores.get(interaction.get("severity", "mild"), 1)
            for interaction in interactions
        )
        return total_score / len(interactions)

    def _generate_interaction_recommendations(
        self, interactions: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations for drug interactions"""
        recommendations = []
        for interaction in interactions:
            recommendations.extend(interaction.get("recommendations", []))
        return list(set(recommendations))

    def _generate_alternative_treatments(
        self, patient_data: PatientData, primary_treatment: str
    ) -> List[str]:
        """Generate alternative treatment options"""
        return []

    def _generate_lifestyle_recommendations(
        self, patient_data: PatientData
    ) -> List[str]:
        """Generate lifestyle recommendations"""
        return ["Exercise regularly", "Maintain healthy diet"]

    def _generate_follow_up_schedule(self, patient_data: PatientData) -> Dict[str, Any]:
        """Generate follow-up schedule"""
        return {
            "initial_follow_up": "1 week",
            "subsequent_follow_ups": "1 month",
            "monitoring_frequency": "weekly",
        }

    def _generate_monitoring_parameters(self, patient_data: PatientData) -> List[str]:
        """Generate monitoring parameters"""
        return ["Blood pressure", "Heart rate", "Temperature"]

    def _identify_risk_factors(self, patient_data: PatientData) -> List[str]:
        """Identify patient risk factors"""
        risk_factors = []
        if patient_data.age > 65:
            risk_factors.append("Advanced age")
        if "diabetes" in patient_data.medical_history:
            risk_factors.append("Diabetes")
        return risk_factors

    def _identify_contraindications(self, patient_data: PatientData) -> List[str]:
        """Identify treatment contraindications"""
        return []

    def _calculate_treatment_adherence(self, patient_data: PatientData) -> float:
        """Calculate treatment adherence score"""
        # This would calculate adherence based on historical data
        return 0.8


# Global AI manager instance
ai_manager = HealthcareAIManager()
