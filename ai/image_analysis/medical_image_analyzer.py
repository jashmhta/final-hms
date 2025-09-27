"""
Medical Image Analysis AI Service
Provides AI-powered analysis of medical images (X-ray, MRI, CT, etc.)
"""

import asyncio
import base64
import io
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
import prometheus_client
import pydicom
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image
from pydantic import BaseModel
from torchvision import models

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
IMAGE_ANALYSIS_COUNT = prometheus_client.Counter(
    "hms_image_analysis_total",
    "Total number of medical images analyzed",
    ["image_type", "model"],
)

ANALYSIS_LATENCY = prometheus_client.Histogram(
    "hms_image_analysis_latency_seconds",
    "Medical image analysis latency",
    ["image_type"],
)

DETECTION_ACCURACY = prometheus_client.Gauge(
    "hms_detection_accuracy",
    "Detection accuracy for medical image analysis",
    ["condition"],
)


# Pydantic models for API
class ImageAnalysisRequest(BaseModel):
    patient_id: str
    image_type: str
    study_type: str  # 'xray', 'mri', 'ct', 'ultrasound'
    body_part: str
    clinical_context: Optional[str] = None


class DetectionResult(BaseModel):
    condition: str
    confidence: float
    bounding_box: Optional[List[float]] = None  # [x1, y1, x2, y2]
    severity: Optional[str] = None
    description: str


class ImageAnalysisResponse(BaseModel):
    patient_id: str
    image_id: str
    analysis_timestamp: str
    image_type: str
    study_type: str
    findings: List[DetectionResult]
    overall_assessment: str
    recommendations: List[str]
    confidence_score: float
    model_version: str


class MedicalImageAnalyzer:
    """
    AI-powered medical image analysis system
    """

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")

        # Load pre-trained models
        self.models = self._load_models()

        # Image transformations
        self.transform = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )

        # Condition mappings
        self.condition_mappings = {
            "xray_chest": {
                "normal": "Normal chest X-ray",
                "pneumonia": "Pneumonia",
                "tuberculosis": "Tuberculosis",
                "lung_opacity": "Lung opacity/consolidation",
                "pleural_effusion": "Pleural effusion",
                "pneumothorax": "Pneumothorax",
                "cardiomegaly": "Cardiomegaly",
                "lung_lesion": "Lung lesion",
            },
            "ct_brain": {
                "normal": "Normal brain CT",
                "hemorrhage": "Intracranial hemorrhage",
                "ischemia": "Cerebral ischemia",
                "mass": "Brain mass/tumor",
                "edema": "Cerebral edema",
                "fracture": "Skull fracture",
                "hydrocephalus": "Hydrocephalus",
            },
            "mri_brain": {
                "normal": "Normal brain MRI",
                "tumor": "Brain tumor",
                "stroke": "Stroke",
                "ms_lesions": "Multiple sclerosis lesions",
                "atrophy": "Cerebral atrophy",
                "meningitis": "Meningitis/encephalitis",
            },
        }

    def _load_models(self):
        """Load pre-trained medical image analysis models"""
        models = {}

        # Chest X-ray model (using DenseNet121)
        models["chest_xray"] = models.densenet121(pretrained=True)
        num_ftrs = models["chest_xray"].classifier.in_features
        models["chest_xray"].classifier = nn.Linear(num_ftrs, 8)  # 8 chest conditions
        models["chest_xray"] = models["chest_xray"].to(self.device)
        models["chest_xray"].eval()

        # Brain CT model (using ResNet50)
        models["brain_ct"] = models.resnet50(pretrained=True)
        num_ftrs = models["brain_ct"].fc.in_features
        models["brain_ct"].fc = nn.Linear(num_ftrs, 7)  # 7 brain conditions
        models["brain_ct"] = models["brain_ct"].to(self.device)
        models["brain_ct"].eval()

        # Object detection model for localizations
        # In production, you would load a pre-trained object detection model
        # models['detection'] = ...

        return models

    def preprocess_image(
        self, image: Union[str, np.ndarray, Image.Image]
    ) -> torch.Tensor:
        """
        Preprocess medical image for analysis

        Args:
            image: Input image (file path, numpy array, or PIL Image)

        Returns:
            Preprocessed tensor
        """
        if isinstance(image, str):
            if image.endswith(".dcm"):
                # Handle DICOM files
                ds = pydicom.dcmread(image)
                pixel_array = ds.pixel_array
                # Normalize to 0-255
                pixel_array = (
                    (pixel_array - pixel_array.min())
                    / (pixel_array.max() - pixel_array.min())
                    * 255
                ).astype(np.uint8)
                image = Image.fromarray(pixel_array)
            else:
                image = Image.open(image)
        elif isinstance(image, np.ndarray):
            image = Image.fromarray(image)

        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Apply transformations
        image_tensor = self.transform(image)
        return image_tensor.unsqueeze(0).to(self.device)

    def analyze_xray_chest(self, image: torch.Tensor) -> Dict:
        """
        Analyze chest X-ray for abnormalities

        Args:
            image: Preprocessed image tensor

        Returns:
            Analysis results
        """
        with torch.no_grad():
            outputs = self.models["chest_xray"](image)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]

        # Get top predictions
        top_probs, top_indices = torch.topk(probabilities, 3)

        findings = []
        conditions = list(self.condition_mappings["xray_chest"].keys())

        for i in range(len(top_indices)):
            condition = conditions[top_indices[i]]
            confidence = float(top_probs[i])
            description = self.condition_mappings["xray_chest"][condition]

            finding = DetectionResult(
                condition=description,
                confidence=confidence,
                severity=self._get_severity_level(condition, confidence),
                description=self._generate_description(condition, confidence),
            )
            findings.append(finding)

        # Generate overall assessment
        normal_confidence = float(probabilities[0])  # Assuming 'normal' is first class
        if normal_confidence > 0.8:
            overall_assessment = "No significant abnormalities detected"
        else:
            # Find the most significant abnormality
            abnormal_findings = [
                f for f in findings if f.condition != "Normal chest X-ray"
            ]
            if abnormal_findings:
                top_finding = max(abnormal_findings, key=lambda x: x.confidence)
                overall_assessment = f"Suspicious for {top_finding.condition}"
            else:
                overall_assessment = "Inconclusive - recommend clinical correlation"

        return {
            "findings": findings,
            "overall_assessment": overall_assessment,
            "recommendations": self._generate_recommendations(findings, "xray_chest"),
            "confidence_score": max(top_probs).item(),
        }

    def analyze_ct_brain(self, image: torch.Tensor) -> Dict:
        """
        Analyze brain CT for abnormalities

        Args:
            image: Preprocessed image tensor

        Returns:
            Analysis results
        """
        with torch.no_grad():
            outputs = self.models["brain_ct"](image)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]

        # Get top predictions
        top_probs, top_indices = torch.topk(probabilities, 3)

        findings = []
        conditions = list(self.condition_mappings["ct_brain"].keys())

        for i in range(len(top_indices)):
            condition = conditions[top_indices[i]]
            confidence = float(top_probs[i])
            description = self.condition_mappings["ct_brain"][condition]

            finding = DetectionResult(
                condition=description,
                confidence=confidence,
                severity=self._get_severity_level(condition, confidence),
                description=self._generate_description(condition, confidence),
            )
            findings.append(finding)

        # Generate overall assessment
        normal_confidence = float(probabilities[0])
        if normal_confidence > 0.85:
            overall_assessment = "Normal brain CT scan"
        else:
            abnormal_findings = [
                f for f in findings if f.condition != "Normal brain CT"
            ]
            if abnormal_findings:
                top_finding = max(abnormal_findings, key=lambda x: x.confidence)
                overall_assessment = f"{top_finding.condition} detected"
            else:
                overall_assessment = (
                    "Indeterminate findings - recommend further evaluation"
                )

        return {
            "findings": findings,
            "overall_assessment": overall_assessment,
            "recommendations": self._generate_recommendations(findings, "ct_brain"),
            "confidence_score": max(top_probs).item(),
        }

    def detect_abnormalities(self, image: np.ndarray) -> List[Dict]:
        """
        Detect and localize abnormalities in medical images

        Args:
            image: Input image as numpy array

        Returns:
            List of detected abnormalities with bounding boxes
        """
        # This is a placeholder for object detection
        # In production, you would use a model like YOLO, Faster R-CNN, or Detectron2
        abnormalities = []

        # Example: Simple thresholding for lung opacity detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

        # Find contours
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 1000:  # Minimum area threshold
                x, y, w, h = cv2.boundingRect(contour)
                abnormalities.append(
                    {
                        "condition": "Opacity",
                        "confidence": 0.7,  # Placeholder
                        "bounding_box": [x, y, x + w, y + h],
                        "area": area,
                    }
                )

        return abnormalities

    def _get_severity_level(self, condition: str, confidence: float) -> str:
        """Determine severity level based on condition and confidence"""
        severe_conditions = ["hemorrhage", "stroke", "pneumothorax", "tumor"]
        moderate_conditions = ["pneumonia", "pleural_effusion", "edema"]

        if any(severe in condition.lower() for severe in severe_conditions):
            return "critical" if confidence > 0.8 else "high"
        elif any(moderate in condition.lower() for moderate in moderate_conditions):
            return "moderate" if confidence > 0.7 else "mild"
        else:
            return "low"

    def _generate_description(self, condition: str, confidence: float) -> str:
        """Generate description for detected condition"""
        descriptions = {
            "pneumonia": f"Findings suggestive of pneumonia with {confidence:.0%} confidence",
            "tuberculosis": f"Features consistent with tuberculosis ({confidence:.0%} confidence)",
            "lung_opacity": f"Area of lung opacity/consolidation detected ({confidence:.0%} confidence)",
            "pleural_effusion": f"Pleural effusion present ({confidence:.0%} confidence)",
            "pneumothorax": f"Pneumothorax detected ({confidence:.0%} confidence)",
            "cardiomegaly": f"Cardiomegaly noted ({confidence:.0%} confidence)",
            "hemorrhage": f"Intracranial hemorrhage detected ({confidence:.0%} confidence)",
            "ischemia": f"Cerebral ischemia suspected ({confidence:.0%} confidence)",
            "tumor": f"Mass lesion suggestive of tumor ({confidence:.0%} confidence)",
        }
        return descriptions.get(
            condition, f"{condition} detected with {confidence:.0%} confidence"
        )

    def _generate_recommendations(
        self, findings: List[DetectionResult], study_type: str
    ) -> List[str]:
        """Generate clinical recommendations based on findings"""
        recommendations = []

        for finding in findings:
            condition = finding.condition.lower()
            confidence = finding.confidence

            if "pneumonia" in condition and confidence > 0.7:
                recommendations.extend(
                    [
                        "Consider chest X-ray in 48-72 hours to monitor resolution",
                        "Appropriate antibiotic therapy recommended",
                        "Consider sputum culture and sensitivity",
                    ]
                )
            elif "tuberculosis" in condition and confidence > 0.6:
                recommendations.extend(
                    [
                        "Immediate TB infection control measures",
                        "AFB smear and culture required",
                        "Chest X-ray follow-up in 2 weeks",
                    ]
                )
            elif "pleural_effusion" in condition and confidence > 0.7:
                recommendations.extend(
                    [
                        "Consider thoracentesis if symptomatic",
                        "Underlying cause investigation needed",
                        "Follow-up chest X-ray in 1 week",
                    ]
                )
            elif "pneumothorax" in condition and confidence > 0.8:
                recommendations.extend(
                    [
                        "Immediate chest tube placement if tension pneumothorax",
                        "Chest tube size selection based on pneumothorax size",
                        "Continuous monitoring required",
                    ]
                )
            elif "hemorrhage" in condition and confidence > 0.7:
                recommendations.extend(
                    [
                        "Immediate neurosurgical consultation",
                        "CT angiography recommended",
                        "ICU admission for monitoring",
                    ]
                )
            elif "ischemia" in condition and confidence > 0.6:
                recommendations.extend(
                    [
                        "Stroke protocol activation",
                        "Consider thrombolytic therapy if appropriate",
                        "Neurology consultation required",
                    ]
                )

        # Add general recommendations
        if not recommendations:
            recommendations.append("Correlate with clinical findings")
            recommendations.append("Consider follow-up imaging if clinically indicated")

        # Remove duplicates
        return list(set(recommendations))

    def compare_with_previous(
        self, current_image: np.ndarray, previous_image: np.ndarray
    ) -> Dict:
        """
        Compare current image with previous study

        Args:
            current_image: Current image
            previous_image: Previous image

        Returns:
            Comparison results
        """
        # Calculate image similarity
        current_gray = cv2.cvtColor(current_image, cv2.COLOR_BGR2GRAY)
        previous_gray = cv2.cvtColor(previous_image, cv2.COLOR_BGR2GRAY)

        # Resize to same size if needed
        if current_gray.shape != previous_gray.shape:
            previous_gray = cv2.resize(
                previous_gray, (current_gray.shape[1], current_gray.shape[0])
            )

        # Calculate structural similarity
        similarity = cv2.matchTemplate(
            current_gray, previous_gray, cv2.TM_CCOEFF_NORMED
        )[0][0]

        # Find differences
        diff = cv2.absdiff(current_gray, previous_gray)
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

        # Count different pixels
        diff_percentage = (np.count_nonzero(thresh) / thresh.size) * 100

        return {
            "similarity_score": similarity,
            "difference_percentage": diff_percentage,
            "assessment": (
                "Significant change detected"
                if diff_percentage > 5
                else "Minimal change"
            ),
            "recommendations": [
                (
                    "Clinical correlation recommended"
                    if diff_percentage > 5
                    else "Stable appearance"
                )
            ],
        }

    async def analyze_image_async(
        self, image_data: bytes, request: ImageAnalysisRequest
    ) -> ImageAnalysisResponse:
        """
        Asynchronously analyze medical image

        Args:
            image_data: Raw image bytes
            request: Analysis request details

        Returns:
            Analysis response
        """
        start_time = time.time()

        try:
            # Decode image
            image = Image.open(io.BytesIO(image_data))

            # Preprocess
            image_tensor = self.preprocess_image(image)

            # Analyze based on study type
            if request.study_type == "xray" and request.body_part == "chest":
                results = self.analyze_xray_chest(image_tensor)
            elif request.study_type == "ct" and request.body_part == "brain":
                results = self.analyze_ct_brain(image_tensor)
            else:
                raise HTTPException(status_code=400, detail="Unsupported image type")

            # Update metrics
            ANALYSIS_LATENCY.labels(image_type=request.image_type).observe(
                time.time() - start_time
            )
            IMAGE_ANALYSIS_COUNT.labels(
                image_type=request.image_type, model="densenet121"
            ).inc()

            # Create response
            response = ImageAnalysisResponse(
                patient_id=request.patient_id,
                image_id=f"IMG_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{request.patient_id}",
                analysis_timestamp=datetime.utcnow().isoformat(),
                image_type=request.image_type,
                study_type=request.study_type,
                findings=results["findings"],
                overall_assessment=results["overall_assessment"],
                recommendations=results["recommendations"],
                confidence_score=results["confidence_score"],
                model_version="1.0.0",
            )

            return response

        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            raise HTTPException(status_code=500, detail=str(e))


# FastAPI app
app = FastAPI(title="HMS Medical Image Analysis API", version="1.0.0")

# Initialize analyzer
analyzer = MedicalImageAnalyzer()


@app.post("/analyze/image", response_model=ImageAnalysisResponse)
async def analyze_medical_image(
    file: UploadFile = File(...),
    patient_id: str = None,
    image_type: str = None,
    study_type: str = None,
    body_part: str = None,
    clinical_context: str = None,
):
    """
    Analyze medical image using AI

    Args:
        file: Medical image file
        patient_id: Patient identifier
        image_type: Type of image (e.g., 'chest_xray', 'brain_ct')
        study_type: Modality (xray, ct, mri)
        body_part: Anatomical region
        clinical_context: Clinical context for analysis

    Returns:
        Image analysis results
    """
    # Read file
    image_data = await file.read()

    # Create request
    request = ImageAnalysisRequest(
        patient_id=patient_id,
        image_type=image_type,
        study_type=study_type,
        body_part=body_part,
        clinical_context=clinical_context,
    )

    # Analyze
    return await analyzer.analyze_image_async(image_data, request)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/metrics")
async def get_metrics():
    """Get Prometheus metrics"""
    return prometheus_client.generate_latest()


# Example usage
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
