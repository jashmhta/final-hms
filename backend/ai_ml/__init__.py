__version__ = "1.0.0"
__author__ = "Healthcare AI Innovation Team"
__email__ = "ai-innovation@hms-enterprise.com"
try:
    from .clinical.clinical_pathways import ClinicalPathwayOptimizer
    from .clinical.diagnostic_assistance import DiagnosticAssistant
    from .clinical.drug_interaction_engine import DrugInteractionEngine
    from .clinical.treatment_recommendation import TreatmentOptimizer
    from .computer_vision.medical_imaging import MedicalImagingAI
    from .core.feature_engineering import FeatureEngineeringPipeline
    from .core.inference_engine import InferenceEngine
    from .core.model_monitoring import ModelMonitoring
    from .core.model_registry import ModelRegistry
    from .ethics.bias_detection import BiasDetector
    from .ethics.compliance_monitoring import ComplianceMonitor
    from .ethics.explainability import ModelExplainer
    from .nlp.medical_record_analysis import MedicalNLPProcessor
    from .nlp.speech_recognition import MedicalSpeechRecognition
    from .predictive.deterioration_detection import PatientDeteriorationDetector
    from .predictive.patient_risk_models import PatientRiskPredictor
    from .predictive.readmission_prediction import ReadmissionPredictor
    from .predictive.resource_optimization import ResourceOptimizationEngine

    model_registry = ModelRegistry()
    feature_pipeline = FeatureEngineeringPipeline()
    inference_engine = InferenceEngine()
    model_monitor = ModelMonitoring()
    AI_ML_AVAILABLE = True
except ImportError as e:
    AI_ML_AVAILABLE = False
    print(f"AI/ML features disabled: {e}")
if AI_ML_AVAILABLE:
    __all__ = [
        "ModelRegistry",
        "FeatureEngineeringPipeline",
        "InferenceEngine",
        "ModelMonitoring",
        "PatientRiskPredictor",
        "ReadmissionPredictor",
        "PatientDeteriorationDetector",
        "ResourceOptimizationEngine",
        "DiagnosticAssistant",
        "TreatmentOptimizer",
        "DrugInteractionEngine",
        "ClinicalPathwayOptimizer",
        "MedicalNLPProcessor",
        "MedicalSpeechRecognition",
        "MedicalImagingAI",
        "BiasDetector",
        "ModelExplainer",
        "ComplianceMonitor",
        "AI_ML_AVAILABLE",
    ]
else:
    __all__ = ["AI_ML_AVAILABLE"]
