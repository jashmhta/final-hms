"""
Patient Risk Prediction Models for Healthcare Intelligence System
Implements various risk stratification models for healthcare analytics
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
import mlflow
import mlflow.sklearn
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PatientRiskPredictor:
    """
    Advanced patient risk prediction system with multiple models
    """

    def __init__(self, experiment_name="hms-patient-risk-prediction"):
        self.models = {
            'readmission': RandomForestClassifier(n_estimators=200, random_state=42),
            'sepsis': GradientBoostingClassifier(n_estimators=100, random_state=42),
            'mortality': LogisticRegression(random_state=42),
            'heart_failure': RandomForestClassifier(n_estimators=150, random_state=42),
            'diabetes_complications': GradientBoostingClassifier(n_estimators=100, random_state=42)
        }
        self.scalers = {}
        self.feature_encoders = {}
        self.experiment_name = experiment_name
        self.setup_mlflow()

    def setup_mlflow(self):
        """Initialize MLflow tracking"""
        try:
            mlflow.set_tracking_uri("http://mlflow:5000")
            mlflow.set_experiment(self.experiment_name)
            logger.info("MLflow tracking initialized")
        except Exception as e:
            logger.warning(f"MLflow initialization failed: {e}")

    def prepare_features(self, patient_data: Dict) -> np.ndarray:
        """
        Prepare features for prediction models

        Args:
            patient_data: Dictionary containing patient information

        Returns:
            numpy array of processed features
        """
        features = []

        # Demographic features
        features.extend([
            patient_data.get('age', 0),
            1 if patient_data.get('gender', '') == 'male' else 0,
            patient_data.get('bmi', 0),
            patient_data.get('insurance_type_encoded', 0)
        ])

        # Vital signs
        vitals = patient_data.get('vital_signs', {})
        features.extend([
            vitals.get('heart_rate', 0),
            vitals.get('blood_pressure_systolic', 0),
            vitals.get('blood_pressure_diastolic', 0),
            vitals.get('oxygen_saturation', 0),
            vitals.get('temperature', 0),
            vitals.get('respiratory_rate', 0)
        ])

        # Lab results
        labs = patient_data.get('lab_results', {})
        features.extend([
            labs.get('glucose', 0),
            labs.get('creatinine', 0),
            labs.get('sodium', 0),
            labs.get('potassium', 0),
            labs.get('hemoglobin', 0),
            labs.get('white_blood_cell_count', 0)
        ])

        # Comorbidities count
        conditions = patient_data.get('conditions', [])
        comorbidity_count = len([c for c in conditions if c not in ['healthy']])
        features.append(comorbidity_count)

        # Medication count
        features.append(len(patient_data.get('medications', [])))

        # Recent admissions (last 12 months)
        features.append(patient_data.get('recent_admissions', 0))

        # Length of stay (if applicable)
        features.append(patient_data.get('length_of_stay', 0))

        return np.array(features).reshape(1, -1)

    def train_readmission_model(self, X: np.ndarray, y: np.ndarray):
        """
        Train 30-day readmission risk prediction model
        """
        with mlflow.start_run(run_name="readmission-risk-model"):
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )

            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # Train model
            model = self.models['readmission']
            model.fit(X_train_scaled, y_train)

            # Evaluate
            y_pred = model.predict(X_test_scaled)
            y_proba = model.predict_proba(X_test_scaled)[:, 1]

            metrics = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred),
                'recall': recall_score(y_test, y_pred),
                'auc_roc': roc_auc_score(y_test, y_proba)
            }

            # Log metrics
            for metric_name, value in metrics.items():
                mlflow.log_metric(metric_name, value)

            # Log model
            mlflow.sklearn.log_model(model, "readmission-model")

            # Store scaler
            self.scalers['readmission'] = scaler

            logger.info(f"Readmission model trained: AUC-ROC = {metrics['auc_roc']:.3f}")

            return model, metrics

    def train_sepsis_model(self, X: np.ndarray, y: np.ndarray):
        """
        Train sepsis prediction model (6-hour early warning)
        """
        with mlflow.start_run(run_name="sepsis-prediction-model"):
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )

            # Handle class imbalance
            from sklearn.utils.class_weight import compute_class_weight
            class_weights = compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
            sample_weights = np.array([class_weights[i] for i in y_train])

            # Train model
            model = self.models['sepsis']
            model.fit(X_train, y_train, sample_weight=sample_weights)

            # Evaluate
            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test)[:, 1]

            metrics = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred),
                'recall': recall_score(y_test, y_pred),
                'auc_roc': roc_auc_score(y_test, y_proba)
            }

            # Log metrics
            for metric_name, value in metrics.items():
                mlflow.log_metric(metric_name, value)

            # Log model
            mlflow.sklearn.log_model(model, "sepsis-model")

            logger.info(f"Sepsis model trained: AUC-ROC = {metrics['auc_roc']:.3f}")

            return model, metrics

    def predict_risk(self, patient_data: Dict, risk_type: str = 'readmission') -> Dict:
        """
        Predict patient risk for specified outcome

        Args:
            patient_data: Patient clinical data
            risk_type: Type of risk to predict

        Returns:
            Dictionary with risk score and recommendations
        """
        if risk_type not in self.models:
            raise ValueError(f"Unknown risk type: {risk_type}")

        # Prepare features
        features = self.prepare_features(patient_data)

        # Scale features if scaler exists
        if risk_type in self.scalers:
            features = self.scalers[risk_type].transform(features)

        # Get model
        model = self.models[risk_type]

        # Make prediction
        risk_score = model.predict_proba(features)[0][1]
        prediction = model.predict(features)[0]

        # Generate recommendations based on risk level
        risk_level = self.get_risk_level(risk_score)
        recommendations = self.generate_recommendations(risk_type, risk_level, patient_data)

        return {
            'risk_type': risk_type,
            'risk_score': float(risk_score),
            'risk_level': risk_level,
            'prediction': bool(prediction),
            'confidence': float(max(model.predict_proba(features)[0])),
            'recommendations': recommendations,
            'timestamp': datetime.utcnow().isoformat(),
            'model_version': getattr(model, 'version', '1.0')
        }

    def get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level category"""
        if risk_score >= 0.8:
            return 'critical'
        elif risk_score >= 0.6:
            return 'high'
        elif risk_score >= 0.4:
            return 'medium'
        elif risk_score >= 0.2:
            return 'low'
        else:
            return 'minimal'

    def generate_recommendations(self, risk_type: str, risk_level: str, patient_data: Dict) -> List[str]:
        """Generate clinical recommendations based on risk assessment"""
        recommendations = []

        if risk_type == 'readmission':
            if risk_level in ['critical', 'high']:
                recommendations.extend([
                    "Schedule follow-up appointment within 7 days",
                    "Assign care coordinator for transition of care",
                    "Ensure medication reconciliation completed",
                    "Provide patient education on condition management",
                    "Consider home health services"
                ])
            elif risk_level == 'medium':
                recommendations.extend([
                    "Schedule follow-up within 14 days",
                    "Medication review before discharge",
                    "Patient education materials provided"
                ])

        elif risk_type == 'sepsis':
            if risk_level in ['critical', 'high']:
                recommendations.extend([
                    "Immediate physician notification",
                    "Consider sepsis protocol activation",
                    "Frequent vital sign monitoring (every 15 minutes)",
                    "Blood cultures and lactate levels ordered",
                    "IV fluids and antibiotics consideration"
                ])
            elif risk_level == 'medium':
                recommendations.extend([
                    "Increased monitoring frequency",
                    "Nurse assessment every 2 hours",
                    "Repeat lactate in 4 hours"
                ])

        elif risk_type == 'mortality':
            if risk_level in ['critical', 'high']:
                recommendations.extend([
                    "Palliative care consultation",
                    "Family conference scheduled",
                    "Goals of care discussion",
                    "Code status review"
                ])

        # Add patient-specific recommendations
        age = patient_data.get('age', 0)
        if age > 65:
            recommendations.append("Consider geriatric assessment")

        if patient_data.get('has_fall_risk', False):
            recommendations.append("Fall prevention protocol activated")

        return recommendations

    def batch_predict(self, patient_data_list: List[Dict], risk_type: str = 'readmission') -> List[Dict]:
        """
        Make predictions for multiple patients

        Args:
            patient_data_list: List of patient data dictionaries
            risk_type: Type of risk to predict

        Returns:
            List of prediction results
        """
        results = []

        for patient_data in patient_data_list:
            result = self.predict_risk(patient_data, risk_type)
            results.append(result)

        return results

    def explain_prediction(self, patient_data: Dict, risk_type: str = 'readmission') -> Dict:
        """
        Explain model prediction using feature importance

        Args:
            patient_data: Patient clinical data
            risk_type: Type of risk prediction

        Returns:
            Dictionary with feature importance and explanation
        """
        model = self.models[risk_type]
        features = self.prepare_features(patient_data)

        # Get feature importance
        if hasattr(model, 'feature_importances_'):
            feature_names = [
                'age', 'gender_male', 'bmi', 'insurance_type',
                'heart_rate', 'bp_systolic', 'bp_diastolic', 'oxygen_sat',
                'temperature', 'respiratory_rate', 'glucose', 'creatinine',
                'sodium', 'potassium', 'hemoglobin', 'wbc', 'comorbidities',
                'medications', 'recent_admissions', 'length_of_stay'
            ]

            importance_scores = model.feature_importances_
            feature_importance = sorted(
                zip(feature_names, importance_scores),
                key=lambda x: x[1],
                reverse=True
            )[:10]  # Top 10 features

            explanation = {
                'top_features': feature_importance,
                'feature_contributions': self.calculate_feature_contributions(
                    features[0], model, feature_names
                )
            }

            return explanation

        return {'error': 'Model does not support feature importance'}

    def calculate_feature_contributions(self, features: np.ndarray, model, feature_names: List[str]) -> Dict:
        """Calculate contribution of each feature to prediction"""
        # This is a simplified contribution calculation
        # In practice, you might use SHAP or LIME for better explanations
        contributions = {}

        if hasattr(model, 'feature_importances_'):
            for i, (name, importance) in enumerate(zip(feature_names, model.feature_importances_)):
                contributions[name] = {
                    'importance': float(importance),
                    'value': float(features[i])
                }

        return contributions


# Example usage and testing
if __name__ == "__main__":
    # Initialize predictor
    predictor = PatientRiskPredictor()

    # Example patient data
    example_patient = {
        'age': 75,
        'gender': 'male',
        'bmi': 28.5,
        'insurance_type_encoded': 1,
        'vital_signs': {
            'heart_rate': 95,
            'blood_pressure_systolic': 145,
            'blood_pressure_diastolic': 85,
            'oxygen_saturation': 94,
            'temperature': 37.8,
            'respiratory_rate': 22
        },
        'lab_results': {
            'glucose': 145,
            'creatinine': 1.8,
            'sodium': 138,
            'potassium': 4.2,
            'hemoglobin': 11.5,
            'white_blood_cell_count': 12.5
        },
        'conditions': ['hypertension', 'diabetes', 'heart_failure'],
        'medications': ['lisinopril', 'metformin', 'furosemide'],
        'recent_admissions': 2,
        'length_of_stay': 5,
        'has_fall_risk': True
    }

    # Make prediction
    risk_prediction = predictor.predict_risk(example_patient, 'readmission')
    print(f"Readmission Risk Prediction: {risk_prediction}")

    # Get explanation
    explanation = predictor.explain_prediction(example_patient, 'readmission')
    print(f"Prediction Explanation: {explanation}")