"""
feature_engineering module
"""

import logging
import re
import secrets
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, StandardScaler

logger = logging.getLogger(__name__)


class FeatureType(Enum):
    DEMOGRAPHIC = "demographic"
    CLINICAL = "clinical"
    TEMPORAL = "temporal"
    LABORATORY = "laboratory"
    MEDICATION = "medication"
    VITAL_SIGNS = "vital_signs"
    SOCIAL = "social"
    UTILIZATION = "utilization"


class FeatureEngineeringPipeline:
    def __init__(self):
        self.scalers = {}
        self.encoders = {}
        self.feature_metadata = {}
        self.feature_importance = {}
        self.feature_engineering_rules = self._load_feature_rules()

    def _load_feature_rules(self) -> Dict:
        return {
            "age_normalization": {
                "method": "min_max",
                "range": (0, 120),
                "special_handling": "pediatric_adult_elderly",
            },
            "vital_signs": {
                "normal_ranges": {
                    "blood_pressure_systolic": (90, 140),
                    "blood_pressure_diastolic": (60, 90),
                    "heart_rate": (60, 100),
                    "temperature": (36.1, 37.2),
                    "oxygen_saturation": (95, 100),
                    "respiratory_rate": (12, 20),
                },
                "abnormality_flags": True,
                "trend_features": True,
            },
            "lab_values": {
                "reference_ranges": True,
                "abnormality_indicators": True,
                "trend_analysis": True,
                "critical_values": True,
            },
            "medications": {
                "drug_class_encoding": True,
                "interaction_features": True,
                "adherence_features": True,
                "duration_features": True,
            },
            "comorbidities": {
                "charlson_comorbidity_index": True,
                "comorbidity_count": True,
                "organ_system_involvement": True,
            },
        }

    def engineer_features(
        self,
        raw_data: Union[pd.DataFrame, Dict],
        feature_types: Optional[List[FeatureType]] = None,
        target_variable: Optional[str] = None,
    ) -> Dict:
        try:
            if feature_types is None:
                feature_types = list(FeatureType)
            if isinstance(raw_data, dict):
                data = pd.DataFrame([raw_data])
            else:
                data = raw_data.copy()
            engineered_features = {}
            feature_metadata = {}
            for feature_type in feature_types:
                if feature_type == FeatureType.DEMOGRAPHIC:
                    demo_features = self._engineer_demographic_features(data)
                    engineered_features.update(demo_features)
                    feature_metadata["demographic"] = list(demo_features.keys())
                elif feature_type == FeatureType.CLINICAL:
                    clinical_features = self._engineer_clinical_features(data)
                    engineered_features.update(clinical_features)
                    feature_metadata["clinical"] = list(clinical_features.keys())
                elif feature_type == FeatureType.TEMPORAL:
                    temporal_features = self._engineer_temporal_features(data)
                    engineered_features.update(temporal_features)
                    feature_metadata["temporal"] = list(temporal_features.keys())
                elif feature_type == FeatureType.LABORATORY:
                    lab_features = self._engineer_laboratory_features(data)
                    engineered_features.update(lab_features)
                    feature_metadata["laboratory"] = list(lab_features.keys())
                elif feature_type == FeatureType.MEDICATION:
                    med_features = self._engineer_medication_features(data)
                    engineered_features.update(med_features)
                    feature_metadata["medication"] = list(med_features.keys())
                elif feature_type == FeatureType.VITAL_SIGNS:
                    vital_features = self._engineer_vital_signs_features(data)
                    engineered_features.update(vital_features)
                    feature_metadata["vital_signs"] = list(vital_features.keys())
                elif feature_type == FeatureType.SOCIAL:
                    social_features = self._engineer_social_features(data)
                    engineered_features.update(social_features)
                    feature_metadata["social"] = list(social_features.keys())
                elif feature_type == FeatureType.UTILIZATION:
                    util_features = self._engineer_utilization_features(data)
                    engineered_features.update(util_features)
                    feature_metadata["utilization"] = list(util_features.keys())
            features_df = pd.DataFrame(engineered_features)
            features_df = self._handle_missing_values(features_df)
            features_df, scaling_info = self._scale_features(features_df)
            if target_variable and target_variable in data.columns:
                features_df, selected_features = self._select_features(
                    features_df, data[target_variable]
                )
                feature_metadata["selected_features"] = selected_features
            interaction_features = self._create_interaction_features(features_df)
            features_df = pd.concat([features_df, interaction_features], axis=1)
            feature_metadata["interactions"] = list(interaction_features.columns)
            return {
                "features": features_df,
                "feature_metadata": feature_metadata,
                "feature_importance": self.feature_importance,
                "scaling_info": scaling_info,
                "original_shape": data.shape,
                "engineered_shape": features_df.shape,
            }
        except Exception as e:
            logger.error(f"Feature engineering failed: {e}")
            return {"error": str(e)}

    def _engineer_demographic_features(self, data: pd.DataFrame) -> Dict:
        features = {}
        try:
            if "date_of_birth" in data.columns:
                ages = self._calculate_age(data["date_of_birth"])
                features["age"] = ages
                features["age_normalized"] = self._normalize_age(ages)
                features["age_group"] = self._create_age_groups(ages)
                features["is_pediatric"] = (ages < 18).astype(int)
                features["is_elderly"] = (ages >= 65).astype(int)
            if "gender" in data.columns:
                gender_encoded = self._encode_categorical(data["gender"])
                for key, value in gender_encoded.items():
                    features[f"gender_{key}"] = value
            if "ethnicity" in data.columns:
                ethnicity_encoded = self._encode_categorical(data["ethnicity"])
                for key, value in ethnicity_encoded.items():
                    features[f"ethnicity_{key}"] = value
            if "preferred_language" in data.columns:
                features["is_english_speaking"] = (
                    data["preferred_language"] == "EN"
                ).astype(int)
                features["needs_interpreter"] = data.get(
                    "interpreter_needed", 0
                ).astype(int)
            if "insurance_type" in data.columns:
                insurance_encoded = self._encode_categorical(data["insurance_type"])
                for key, value in insurance_encoded.items():
                    features[f"insurance_{key}"] = value
            if "marital_status" in data.columns:
                features["is_married"] = (data["marital_status"] == "MARRIED").astype(
                    int
                )
                features["social_support_score"] = self._calculate_social_support_score(
                    data
                )
            return features
        except Exception as e:
            logger.error(f"Demographic feature engineering failed: {e}")
            return {}

    def _engineer_clinical_features(self, data: pd.DataFrame) -> Dict:
        features = {}
        try:
            if "chronic_conditions" in data.columns:
                features["comorbidity_count"] = data["chronic_conditions"].apply(len)
                features["charlson_index"] = data["chronic_conditions"].apply(
                    self._calculate_charlson_index
                )
                features["organ_system_count"] = data["chronic_conditions"].apply(
                    self._count_organ_systems
                )
            if "allergies" in data.columns:
                features["allergy_count"] = data["allergies"].apply(len)
                features["has_severe_allergies"] = (
                    data["allergies"]
                    .apply(
                        lambda x: any(
                            allergy.get("severity", "") in ["SEVERE", "LIFE_THREAT"]
                            for allergy in x
                        )
                    )
                    .astype(int)
                )
            if "previous_surgeries" in data.columns:
                features["surgery_count"] = data["previous_surgeries"].apply(len)
                features["has_major_surgery"] = (
                    data["previous_surgeries"]
                    .apply(
                        lambda x: any(
                            surgery.get("type", "") in ["MAJOR", "EMERGENCY"]
                            for surgery in x
                        )
                    )
                    .astype(int)
                )
            if "family_history" in data.columns:
                features["family_history_count"] = data["family_history"].apply(len)
                features["hereditary_risk_score"] = data["family_history"].apply(
                    self._calculate_hereditary_risk
                )
            features["fall_risk_score"] = self._calculate_fall_risk_score(data)
            features["malnutrition_risk"] = self._calculate_malnutrition_risk(data)
            features["pressure_ulcer_risk"] = self._calculate_pressure_ulcer_risk(data)
            return features
        except Exception as e:
            logger.error(f"Clinical feature engineering failed: {e}")
            return {}

    def _engineer_vital_signs_features(self, data: pd.DataFrame) -> Dict:
        features = {}
        try:
            vital_rules = self.feature_engineering_rules["vital_signs"]
            if "systolic_bp" in data.columns and "diastolic_bp" in data.columns:
                systolic = data["systolic_bp"]
                diastolic = data["diastolic_bp"]
                features["bp_category"] = self._categorize_blood_pressure(
                    systolic, diastolic
                )
                features["bp_normalized"] = self._normalize_vital_sign(
                    systolic, "blood_pressure_systolic"
                )
                features["pulse_pressure"] = systolic - diastolic
                features["mean_arterial_pressure"] = (systolic + 2 * diastolic) / 3
                features["hypertensive"] = (
                    (systolic >= 140) | (diastolic >= 90)
                ).astype(int)
                features["hypotensive"] = ((systolic < 90) | (diastolic < 60)).astype(
                    int
                )
            if "heart_rate" in data.columns:
                hr = data["heart_rate"]
                features["hr_normalized"] = self._normalize_vital_sign(hr, "heart_rate")
                features["tachycardia"] = (hr > 100).astype(int)
                features["bradycardia"] = (hr < 60).astype(int)
                features["hr_category"] = self._categorize_heart_rate(hr)
            if "temperature" in data.columns:
                temp = data["temperature"]
                features["temp_normalized"] = self._normalize_vital_sign(
                    temp, "temperature"
                )
                features["fever"] = (temp > 38.0).astype(int)
                features["hypothermia"] = (temp < 36.0).astype(int)
                features["temp_category"] = self._categorize_temperature(temp)
            if "oxygen_saturation" in data.columns:
                o2sat = data["oxygen_saturation"]
                features["o2sat_normalized"] = self._normalize_vital_sign(
                    o2sat, "oxygen_saturation"
                )
                features["hypoxemic"] = (o2sat < 95).astype(int)
                features["severe_hypoxemia"] = (o2sat < 90).astype(int)
            if "respiratory_rate" in data.columns:
                rr = data["respiratory_rate"]
                features["rr_normalized"] = self._normalize_vital_sign(
                    rr, "respiratory_rate"
                )
                features["tachypnea"] = (rr > 20).astype(int)
                features["bradypnea"] = (rr < 12).astype(int)
            if "pain_score" in data.columns:
                pain = data["pain_score"]
                features["pain_normalized"] = pain / 10.0
                features["severe_pain"] = (pain >= 7).astype(int)
                features["moderate_pain"] = ((pain >= 4) & (pain < 7)).astype(int)
            return features
        except Exception as e:
            logger.error(f"Vital signs feature engineering failed: {e}")
            return {}

    def _engineer_laboratory_features(self, data: pd.DataFrame) -> Dict:
        features = {}
        try:
            lab_values = [
                "creatinine",
                "sodium",
                "potassium",
                "hemoglobin",
                "glucose",
                "white_blood_cell",
                "platelet",
                "albumin",
                "bilirubin",
            ]
            for lab in lab_values:
                if lab in data.columns:
                    lab_data = data[lab]
                    features[f"{lab}_normalized"] = self._normalize_lab_value(
                        lab_data, lab
                    )
                    features[f"{lab}_abnormal"] = self._is_abnormal_lab_value(
                        lab_data, lab
                    ).astype(int)
                    features[f"{lab}_critical"] = self._is_critical_lab_value(
                        lab_data, lab
                    ).astype(int)
            if "creatinine" in data.columns and "age" in data.columns:
                features["egfr"] = self._calculate_egfr(data["creatinine"], data["age"])
                features["renal_impairment"] = (data["creatinine"] > 1.5).astype(int)
            if "ast" in data.columns and "alt" in data.columns:
                features["ast_alt_ratio"] = data["ast"] / (data["alt"] + 1)
                features["liver_disease_indicator"] = (
                    (data["ast"] > 40) | (data["alt"] > 40)
                ).astype(int)
            if "sodium" in data.columns and "potassium" in data.columns:
                features["electrolyte_imbalance"] = (
                    self._is_abnormal_lab_value(data["sodium"], "sodium")
                    | self._is_abnormal_lab_value(data["potassium"], "potassium")
                ).astype(int)
            if "hemoglobin" in data.columns:
                features["anemia"] = self._is_abnormal_lab_value(
                    data["hemoglobin"], "hemoglobin"
                ).astype(int)
                features["anemia_severity"] = data["hemoglobin"].apply(
                    self._classify_anemia_severity
                )
            return features
        except Exception as e:
            logger.error(f"Laboratory feature engineering failed: {e}")
            return {}

    def _engineer_temporal_features(self, data: pd.DataFrame) -> Dict:
        features = {}
        try:
            if "admission_date" in data.columns:
                admission_dates = pd.to_datetime(data["admission_date"])
                features["admission_hour"] = admission_dates.dt.hour
                features["admission_day_of_week"] = admission_dates.dt.dayofweek
                features["admission_month"] = admission_dates.dt.month
                features["is_weekend_admission"] = (
                    admission_dates.dt.dayofweek >= 5
                ).astype(int)
                features["is_night_admission"] = (
                    (admission_dates.dt.hour >= 20) | (admission_dates.dt.hour < 6)
                ).astype(int)
            if "length_of_stay" in data.columns:
                los = data["length_of_stay"]
                features["los_normalized"] = self._normalize_length_of_stay(los)
                features["prolonged_stay"] = (los > 7).astype(int)
                features["short_stay"] = (los <= 1).astype(int)
            if "last_admission_date" in data.columns:
                last_admission = pd.to_datetime(data["last_admission_date"])
                features["days_since_last_admission"] = (
                    datetime.now() - last_admission
                ).dt.days
                features["readmission_within_30_days"] = (
                    features["days_since_last_admission"] <= 30
                ).astype(int)
            return features
        except Exception as e:
            logger.error(f"Temporal feature engineering failed: {e}")
            return {}

    def _engineer_medication_features(self, data: pd.DataFrame) -> Dict:
        features = {}
        try:
            if "medications" in data.columns:
                medications = data["medications"]
                features["medication_count"] = medications.apply(len)
                features["high_risk_medications"] = medications.apply(
                    lambda x: sum(1 for med in x if self._is_high_risk_medication(med))
                )
                features["anticoagulant_count"] = medications.apply(
                    lambda x: sum(1 for med in x if self._is_anticoagulant(med))
                )
                features["opioid_count"] = medications.apply(
                    lambda x: sum(1 for med in x if self._is_opioid(med))
                )
                features["polypharmacy"] = (features["medication_count"] >= 5).astype(
                    int
                )
                features["severe_polypharmacy"] = (
                    features["medication_count"] >= 10
                ).astype(int)
                features["medication_adherence_score"] = medications.apply(
                    self._calculate_adherence_score
                )
            return features
        except Exception as e:
            logger.error(f"Medication feature engineering failed: {e}")
            return {}

    def _engineer_social_features(self, data: pd.DataFrame) -> Dict:
        features = {}
        try:
            if "living_situation" in data.columns:
                features["lives_alone"] = (data["living_situation"] == "ALONE").astype(
                    int
                )
                features["has_caregiver"] = (
                    data["living_situation"].isin(["WITH_FAMILY", "WITH_CAREGIVER"])
                ).astype(int)
            if "income_level" in data.columns:
                features["low_income"] = (
                    data["income_level"].isin(["LOW", "VERY_LOW"])
                ).astype(int)
                features["uninsured"] = (
                    data.get("insurance_status", "") == "UNINSURED"
                ).astype(int)
            if "education_level" in data.columns:
                features["low_education"] = (
                    data["education_level"].isin(
                        ["LESS_THAN_HIGH_SCHOOL", "HIGH_SCHOOL"]
                    )
                ).astype(int)
            if "zip_code" in data.columns:
                features["rural_resident"] = data["zip_code"].apply(
                    self._is_rural_zip_code
                )
                features["distance_to_hospital"] = data["zip_code"].apply(
                    self._calculate_distance_to_hospital
                )
            if "substance_use" in data.columns:
                features["smoker"] = (data["substance_use"] == "TOBACCO").astype(int)
                features["alcohol_use"] = (
                    data["substance_use"]
                    .apply(
                        lambda x: (
                            x in ["ALCOHOL", "BOTH"] if isinstance(x, str) else False
                        )
                    )
                    .astype(int)
                )
            return features
        except Exception as e:
            logger.error(f"Social feature engineering failed: {e}")
            return {}

    def _engineer_utilization_features(self, data: pd.DataFrame) -> Dict:
        features = {}
        try:
            if "previous_admissions" in data.columns:
                features["total_admissions"] = data["previous_admissions"].apply(len)
                features["admissions_last_year"] = data["previous_admissions"].apply(
                    lambda x: sum(
                        1
                        for admission in x
                        if self._is_within_last_year(admission.get("date", ""))
                    )
                )
                features["emergency_visits_last_year"] = data[
                    "previous_admissions"
                ].apply(
                    lambda x: sum(
                        1
                        for admission in x
                        if admission.get("type") == "EMERGENCY"
                        and self._is_within_last_year(admission.get("date", ""))
                    )
                )
            if "icu_admissions" in data.columns:
                features["icu_admission_count"] = data["icu_admissions"].apply(len)
                features["previous_icu_stay"] = (
                    features["icu_admission_count"] > 0
                ).astype(int)
            if "previous_costs" in data.columns:
                features["total_healthcare_costs"] = data["previous_costs"].apply(sum)
                features["high_cost_patient"] = (
                    features["total_healthcare_costs"] > 50000
                ).astype(int)
            return features
        except Exception as e:
            logger.error(f"Utilization feature engineering failed: {e}")
            return {}

    def _calculate_age(self, dates_of_birth: pd.Series) -> pd.Series:
        today = datetime.now()
        ages = []
        for dob in dates_of_birth:
            if pd.isna(dob):
                ages.append(0)
            else:
                if isinstance(dob, str):
                    dob = datetime.strptime(dob, "%Y-%m-%d")
                age = (
                    today.year
                    - dob.year
                    - ((today.month, today.day) < (dob.month, dob.day))
                )
                ages.append(age)
        return pd.Series(ages)

    def _normalize_age(self, ages: pd.Series) -> pd.Series:
        return ages.clip(0, 120) / 120.0

    def _create_age_groups(self, ages: pd.Series) -> pd.Series:
        return pd.cut(
            ages,
            bins=[0, 18, 40, 65, 120],
            labels=["pediatric", "adult", "middle_age", "elderly"],
        )

    def _encode_categorical(self, series: pd.Series) -> Dict:
        encoded = {}
        for category in series.unique():
            if pd.notna(category):
                encoded[str(category).lower().replace(" ", "_")] = (
                    series == category
                ).astype(int)
        return encoded

    def _categorize_blood_pressure(
        self, systolic: pd.Series, diastolic: pd.Series
    ) -> pd.Series:
        categories = []
        for sys, dia in zip(systolic, diastolic):
            if sys < 120 and dia < 80:
                categories.append("normal")
            elif sys < 130 and dia < 80:
                categories.append("elevated")
            elif sys < 140 or dia < 90:
                categories.append("stage1_hypertension")
            else:
                categories.append("stage2_hypertension")
        return pd.Series(categories)

    def _normalize_vital_sign(self, values: pd.Series, vital_type: str) -> pd.Series:
        normal_ranges = self.feature_engineering_rules["vital_signs"]["normal_ranges"]
        if vital_type in normal_ranges:
            min_val, max_val = normal_ranges[vital_type]
            return values.clip(min_val, max_val) / max_val
        return values / values.max()

    def _normalize_lab_value(self, values: pd.Series, lab_type: str) -> pd.Series:
        reference_ranges = {
            "creatinine": (0.6, 1.2),
            "sodium": (135, 145),
            "potassium": (3.5, 5.0),
            "hemoglobin": (12, 16),
            "glucose": (70, 100),
        }
        if lab_type in reference_ranges:
            min_val, max_val = reference_ranges[lab_type]
            return values.clip(min_val, max_val) / max_val
        return values / values.max()

    def _is_abnormal_lab_value(self, values: pd.Series, lab_type: str) -> pd.Series:
        reference_ranges = {
            "creatinine": (0.6, 1.2),
            "sodium": (135, 145),
            "potassium": (3.5, 5.0),
            "hemoglobin": (12, 16),
            "glucose": (70, 100),
        }
        if lab_type in reference_ranges:
            min_val, max_val = reference_ranges[lab_type]
            return (values < min_val) | (values > max_val)
        return pd.Series([False] * len(values))

    def _is_critical_lab_value(self, values: pd.Series, lab_type: str) -> pd.Series:
        critical_ranges = {
            "creatinine": (0.1, 3.0),
            "sodium": (120, 160),
            "potassium": (2.5, 6.5),
            "hemoglobin": (7, 20),
            "glucose": (40, 250),
        }
        if lab_type in critical_ranges:
            min_val, max_val = critical_ranges[lab_type]
            return (values < min_val) | (values > max_val)
        return pd.Series([False] * len(values))

    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        numerical_cols = df.select_dtypes(include=[np.number]).columns
        for col in numerical_cols:
            if df[col].isnull().sum() > 0:
                df[col] = df[col].fillna(df[col].median())
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns
        for col in categorical_cols:
            if df[col].isnull().sum() > 0:
                df[col] = df[col].fillna(
                    df[col].mode().iloc[0] if not df[col].mode().empty else "unknown"
                )
        return df

    def _scale_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        scaling_info = {}
        numerical_cols = df.select_dtypes(include=[np.number]).columns
        if len(numerical_cols) > 0:
            scaler = StandardScaler()
            df[numerical_cols] = scaler.fit_transform(df[numerical_cols])
            scaling_info = {
                "scaler_type": "StandardScaler",
                "numerical_columns": list(numerical_cols),
                "fitted": True,
            }
        return df, scaling_info

    def _create_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        interaction_features = pd.DataFrame(index=df.index)
        if "age_normalized" in df.columns and "comorbidity_count" in df.columns:
            interaction_features["age_comorbidity_interaction"] = (
                df["age_normalized"] * df["comorbidity_count"]
            )
        if "charlson_index" in df.columns and "medication_count" in df.columns:
            interaction_features["severity_medication_interaction"] = (
                df["charlson_index"] * df["medication_count"]
            )
        if "bp_normalized" in df.columns and "hr_normalized" in df.columns:
            interaction_features["bp_hr_interaction"] = (
                df["bp_normalized"] * df["hr_normalized"]
            )
        return interaction_features

    def _select_features(
        self, features: pd.DataFrame, target: pd.Series, k: int = 20
    ) -> Tuple[pd.DataFrame, List[str]]:
        from sklearn.feature_selection import SelectKBest, f_classif

        selector = SelectKBest(score_func=f_classif, k=min(k, features.shape[1]))
        selected_features = selector.fit_transform(features, target)
        feature_scores = selector.scores_
        selected_indices = selector.get_support(indices=True)
        feature_names = features.columns
        for idx, score in zip(selected_indices, feature_scores[selected_indices]):
            self.feature_importance[feature_names[idx]] = score
        selected_feature_names = [feature_names[i] for i in selected_indices]
        return (
            pd.DataFrame(selected_features, columns=selected_feature_names),
            selected_feature_names,
        )

    def _calculate_charlson_index(self, conditions: list) -> int:
        weights = {
            "myocardial_infarction": 1,
            "congestive_heart_failure": 1,
            "peripheral_vascular_disease": 1,
            "cerebrovascular_disease": 1,
            "dementia": 1,
            "chronic_pulmonary_disease": 1,
            "rheumatic_disease": 1,
            "peptic_ulcer_disease": 1,
            "mild_liver_disease": 1,
            "diabetes": 1,
            "diabetes_with_complications": 2,
            "hemiplegia": 2,
            "renal_disease": 2,
            "any_malignancy": 2,
            "moderate_severe_liver_disease": 3,
            "metastatic_solid_tumor": 6,
            "aids": 6,
        }
        charlson_score = 0
        for condition in conditions:
            if isinstance(condition, dict):
                condition_name = condition.get("name", "").lower().replace(" ", "_")
            else:
                condition_name = str(condition).lower().replace(" ", "_")
            charlson_score += weights.get(condition_name, 0)
        return charlson_score

    def _calculate_egfr(self, creatinine: pd.Series, age: pd.Series) -> pd.Series:
        return 144 * (creatinine / 0.7) ** (-0.601) * (0.993) ** age

    def _calculate_fall_risk_score(self, data: pd.DataFrame) -> pd.Series:
        risk_score = 0
        if "age" in data.columns:
            risk_score += (data["age"] >= 65).astype(int) * 1
        if "medications" in data.columns:
            risk_score += data["medications"].apply(
                lambda x: sum(1 for med in x if self._is_fall_risk_medication(med))
            )
        if "previous_falls" in data.columns:
            risk_score += data["previous_falls"].apply(len) * 2
        return risk_score

    def _is_high_risk_medication(self, medication: dict) -> bool:
        high_risk_meds = ["warfarin", "insulin", "opioid", "anticoagulant"]
        med_name = medication.get("name", "").lower()
        return any(risk in med_name for risk in high_risk_meds)

    def _is_anticoagulant(self, medication: dict) -> bool:
        anticoagulants = [
            "warfarin",
            "heparin",
            "enoxaparin",
            "rivaroxaban",
            "apixaban",
        ]
        med_name = medication.get("name", "").lower()
        return any(anticoag in med_name for anticoag in anticoagulants)

    def _is_opioid(self, medication: dict) -> bool:
        opioids = ["morphine", "oxycodone", "hydrocodone", "fentanyl", "codeine"]
        med_name = medication.get("name", "").lower()
        return any(opioid in med_name for opioid in opioids)

    def _is_fall_risk_medication(self, medication: dict) -> bool:
        fall_risk_meds = [
            "benzodiazepine",
            "opioid",
            "sedative",
            "hypnotic",
            "antipsychotic",
        ]
        med_name = medication.get("name", "").lower()
        return any(risk in med_name for risk in fall_risk_meds)

    def _normalize_length_of_stay(self, los: pd.Series) -> pd.Series:
        return los.clip(0, 30) / 30.0

    def _is_within_last_year(self, date_str: str) -> bool:
        try:
            if isinstance(date_str, str):
                date = datetime.strptime(date_str, "%Y-%m-%d")
            else:
                date = date_str
            return (datetime.now() - date).days <= 365
        except:
            return False

    def _is_rural_zip_code(self, zip_code: str) -> bool:
        try:
            zip_prefix = int(str(zip_code)[:3])
            return zip_prefix in [
                598,
                599,
                820,
                823,
                824,
                825,
                826,
                827,
                828,
                829,
                830,
                831,
            ]
        except:
            return False

    def _calculate_distance_to_hospital(self, zip_code: str) -> float:
        return np.secrets.uniform(1, 50)

    def _classify_anemia_severity(self, hemoglobin: float) -> str:
        if hemoglobin >= 12:
            return "none"
        elif hemoglobin >= 10:
            return "mild"
        elif hemoglobin >= 8:
            return "moderate"
        else:
            return "severe"

    def _categorize_heart_rate(self, hr: pd.Series) -> pd.Series:
        categories = []
        for rate in hr:
            if rate < 60:
                categories.append("bradycardia")
            elif rate > 100:
                categories.append("tachycardia")
            else:
                categories.append("normal")
        return pd.Series(categories)

    def _categorize_temperature(self, temp: pd.Series) -> pd.Series:
        categories = []
        for t in temp:
            if t < 36.0:
                categories.append("hypothermia")
            elif t > 38.0:
                categories.append("fever")
            elif t > 37.5:
                categories.append("low_grade_fever")
            else:
                categories.append("normal")
        return pd.Series(categories)

    def _count_organ_systems(self, conditions: list) -> int:
        organ_systems = {
            "cardiovascular": [
                "hypertension",
                "heart_failure",
                "coronary_artery_disease",
            ],
            "respiratory": ["copd", "asthma", "pulmonary_fibrosis"],
            "renal": ["chronic_kidney_disease", "renal_failure"],
            "neurological": ["stroke", "dementia", "parkinsons"],
            "endocrine": ["diabetes", "thyroid_disorder"],
            "gastrointestinal": ["crohns_disease", "ulcerative_colitis"],
            "musculoskeletal": ["arthritis", "osteoporosis"],
        }
        involved_systems = set()
        for condition in conditions:
            if isinstance(condition, dict):
                condition_name = condition.get("name", "").lower()
            else:
                condition_name = str(condition).lower()
            for system, related_conditions in organ_systems.items():
                if any(related in condition_name for related in related_conditions):
                    involved_systems.add(system)
        return len(involved_systems)

    def _calculate_social_support_score(self, data: pd.DataFrame) -> pd.Series:
        score = 0
        if "marital_status" in data.columns:
            score += (data["marital_status"] == "MARRIED").astype(int)
        if "living_situation" in data.columns:
            score += (data["living_situation"] == "WITH_FAMILY").astype(int)
        if "emergency_contacts" in data.columns:
            score += data["emergency_contacts"].apply(len)
        return score

    def _calculate_hereditary_risk(self, family_history: list) -> float:
        hereditary_conditions = {
            "breast_cancer": 2.0,
            "colon_cancer": 1.5,
            "heart_disease": 1.2,
            "diabetes": 1.1,
            "alzheimers": 1.3,
            "stroke": 1.2,
        }
        risk_score = 0
        for condition in family_history:
            if isinstance(condition, dict):
                condition_name = (
                    condition.get("condition", "").lower().replace(" ", "_")
                )
            else:
                condition_name = str(condition).lower().replace(" ", "_")
            risk_score += hereditary_conditions.get(condition_name, 0)
        return risk_score

    def _calculate_malnutrition_risk(self, data: pd.DataFrame) -> pd.Series:
        risk_score = 0
        if "albumin" in data.columns:
            risk_score += (data["albumin"] < 3.5).astype(int)
        if "bmi" in data.columns:
            risk_score += (data["bmi"] < 18.5).astype(int)
        if "weight_loss" in data.columns:
            risk_score += (data["weight_loss"] > 10).astype(int)
        return risk_score

    def _calculate_pressure_ulcer_risk(self, data: pd.DataFrame) -> pd.Series:
        risk_score = 0
        if "mobility" in data.columns:
            risk_score += (data["mobility"].isin(["bedridden", "chairbound"])).astype(
                int
            )
        if "incontinence" in data.columns:
            risk_score += (data["incontinence"] == "yes").astype(int)
        if "nutrition_status" in data.columns:
            risk_score += (data["nutrition_status"] == "poor").astype(int)
        return risk_score

    def _calculate_adherence_score(self, medications: list) -> float:
        if not medications:
            return 0.0
        adherence_indicators = 0
        total_indicators = len(medications)
        for med in medications:
            if isinstance(med, dict):
                if med.get("adherence", "").lower() in ["good", "excellent"]:
                    adherence_indicators += 1
        return adherence_indicators / total_indicators if total_indicators > 0 else 0.0
