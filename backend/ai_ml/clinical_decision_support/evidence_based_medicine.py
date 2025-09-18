import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import requests
from dataclasses import dataclass
from enum import Enum
import numpy as np
import pandas as pd
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
logger = logging.getLogger(__name__)
class EvidenceType(Enum):
    CLINICAL_GUIDELINE = "clinical_guideline"
    RANDOMIZED_TRIAL = "randomized_trial"
    META_ANALYSIS = "meta_analysis"
    SYSTEMATIC_REVIEW = "systematic_review"
    OBSERVATIONAL_STUDY = "observational_study"
    EXPERT_OPINION = "expert_opinion"
    CASE_REPORT = "case_report"
class EvidenceQuality(Enum):
    HIGH = "high"  
    MODERATE = (
        "moderate"  
    )
    LOW = "low"  
    VERY_LOW = "very_low"  
class RecommendationStrength(Enum):
    STRONG = "strong"  
    MODERATE = "moderate"  
    WEAK = "weak"  
@dataclass
class EvidenceSource:
    source_id: str
    title: str
    authors: List[str]
    journal: str
    publication_date: datetime
    evidence_type: EvidenceType
    quality: EvidenceQuality
    doi: Optional[str] = None
    pmid: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
@dataclass
class ClinicalGuideline:
    guideline_id: str
    title: str
    organization: str
    publication_date: datetime
    last_updated: datetime
    condition: str
    target_population: str
    recommendations: List[Dict[str, Any]]
    evidence_sources: List[EvidenceSource]
    strength: RecommendationStrength
    quality: EvidenceQuality
@dataclass
class EvidenceSynthesis:
    synthesis_id: str
    clinical_question: str
    population: str
    intervention: str
    comparison: str
    outcomes: List[str]
    findings: Dict[str, Any]
    evidence_sources: List[EvidenceSource]
    quality_assessment: EvidenceQuality
    confidence_interval: Optional[Tuple[float, float]] = None
    number_of_studies: int = 0
    sample_size: int = 0
class EvidenceBasedMedicineEngine:
    def __init__(self):
        self.guideline_cache = {}
        self.evidence_cache = {}
        self.pubmed_api_key = getattr(settings, "PUBMED_API_KEY", None)
        self.cochrane_api_key = getattr(settings, "COCHRANE_API_KEY", None)
    def search_medical_literature(
        self,
        query: str,
        max_results: int = 10,
        evidence_types: List[EvidenceType] = None,
    ) -> List[EvidenceSource]:
        try:
            cache_key = f"literature_search_{hash(query)}_{max_results}"
            cached_results = cache.get(cache_key)
            if cached_results:
                return cached_results
            pubmed_results = self._search_pubmed(query, max_results)
            if evidence_types:
                pubmed_results = [
                    result
                    for result in pubmed_results
                    if result.evidence_type in evidence_types
                ]
            cache.set(cache_key, pubmed_results, timeout=3600)  
            return pubmed_results
        except Exception as e:
            logger.error(f"Error searching medical literature: {str(e)}")
            return []
    def _search_pubmed(self, query: str, max_results: int) -> List[EvidenceSource]:
        return [
            EvidenceSource(
                source_id="pmid123456",
                title=f"Clinical study on {query}",
                authors=["Smith J", "Johnson A"],
                journal="New England Journal of Medicine",
                publication_date=datetime.now() - timedelta(days=365),
                evidence_type=EvidenceType.RANDOMIZED_TRIAL,
                quality=EvidenceQuality.HIGH,
                pmid="123456",
                abstract=f"This study investigated {query} in a randomized controlled trial...",
            )
        ]
    def get_clinical_guidelines(
        self, condition: str, organization: str = None
    ) -> List[ClinicalGuideline]:
        try:
            cache_key = f"guidelines_{condition}_{organization or 'all'}"
            cached_guidelines = cache.get(cache_key)
            if cached_guidelines:
                return cached_guidelines
            guidelines = self._query_guideline_database(condition, organization)
            cache.set(cache_key, guidelines, timeout=86400)  
            return guidelines
        except Exception as e:
            logger.error(f"Error retrieving clinical guidelines: {str(e)}")
            return []
    def _query_guideline_database(
        self, condition: str, organization: str = None
    ) -> List[ClinicalGuideline]:
        return [
            ClinicalGuideline(
                guideline_id="guideline_001",
                title=f"Management Guidelines for {condition}",
                organization="American Medical Association",
                publication_date=datetime.now() - timedelta(days=180),
                last_updated=datetime.now() - timedelta(days=30),
                condition=condition,
                target_population="Adult patients",
                recommendations=[
                    {
                        "recommendation": "First-line treatment for mild cases",
                        "strength": "strong",
                        "evidence_level": "high",
                    }
                ],
                evidence_sources=[],
                strength=RecommendationStrength.STRONG,
                quality=EvidenceQuality.HIGH,
            )
        ]
    def synthesize_evidence(
        self,
        clinical_question: str,
        population: str,
        intervention: str,
        comparison: str = None,
        outcomes: List[str] = None,
    ) -> EvidenceSynthesis:
        try:
            query = f"{population} {intervention}"
            if comparison:
                query += f" vs {comparison}"
            if outcomes:
                query += f" {' '.join(outcomes)}"
            evidence_sources = self.search_medical_literature(query, max_results=20)
            quality_assessment = self._assess_evidence_quality(evidence_sources)
            findings = self._synthesize_findings(evidence_sources)
            confidence_interval = self._calculate_confidence_interval(evidence_sources)
            return EvidenceSynthesis(
                synthesis_id=f"synthesis_{hash(clinical_question)}",
                clinical_question=clinical_question,
                population=population,
                intervention=intervention,
                comparison=comparison or "standard care",
                outcomes=outcomes or [],
                findings=findings,
                evidence_sources=evidence_sources,
                quality_assessment=quality_assessment,
                confidence_interval=confidence_interval,
                number_of_studies=len(evidence_sources),
                sample_size=sum(
                    self._extract_sample_size(source) for source in evidence_sources
                ),
            )
        except Exception as e:
            logger.error(f"Error synthesizing evidence: {str(e)}")
            return None
    def _assess_evidence_quality(
        self, evidence_sources: List[EvidenceSource]
    ) -> EvidenceQuality:
        if not evidence_sources:
            return EvidenceQuality.VERY_LOW
        quality_scores = []
        for source in evidence_sources:
            score = self._calculate_quality_score(source)
            quality_scores.append(score)
        average_score = np.mean(quality_scores)
        if average_score >= 0.8:
            return EvidenceQuality.HIGH
        elif average_score >= 0.6:
            return EvidenceQuality.MODERATE
        elif average_score >= 0.4:
            return EvidenceQuality.LOW
        else:
            return EvidenceQuality.VERY_LOW
    def _calculate_quality_score(self, source: EvidenceSource) -> float:
        type_scores = {
            EvidenceType.RANDOMIZED_TRIAL: 0.9,
            EvidenceType.META_ANALYSIS: 0.95,
            EvidenceType.SYSTEMATIC_REVIEW: 0.85,
            EvidenceType.CLINICAL_GUIDELINE: 0.8,
            EvidenceType.OBSERVATIONAL_STUDY: 0.6,
            EvidenceType.EXPERT_OPINION: 0.3,
            EvidenceType.CASE_REPORT: 0.2,
        }
        quality_scores = {
            EvidenceQuality.HIGH: 0.9,
            EvidenceQuality.MODERATE: 0.7,
            EvidenceQuality.LOW: 0.5,
            EvidenceQuality.VERY_LOW: 0.3,
        }
        type_score = type_scores.get(source.evidence_type, 0.5)
        quality_score = quality_scores.get(source.quality, 0.5)
        return (type_score + quality_score) / 2
    def _synthesize_findings(
        self, evidence_sources: List[EvidenceSource]
    ) -> Dict[str, Any]:
        positive_findings = len(
            [s for s in evidence_sources if "effective" in s.abstract.lower()]
        )
        negative_findings = len(
            [s for s in evidence_sources if "ineffective" in s.abstract.lower()]
        )
        mixed_findings = len(evidence_sources) - positive_findings - negative_findings
        return {
            "total_studies": len(evidence_sources),
            "positive_findings": positive_findings,
            "negative_findings": negative_findings,
            "mixed_findings": mixed_findings,
            "consensus": (
                "positive"
                if positive_findings > negative_findings
                else "negative" if negative_findings > positive_findings else "mixed"
            ),
        }
    def _calculate_confidence_interval(
        self, evidence_sources: List[EvidenceSource]
    ) -> Tuple[float, float]:
        if not evidence_sources:
            return (0.0, 1.0)
        base_effect = 0.65
        margin = 0.15 / len(evidence_sources)  
        return (base_effect - margin, base_effect + margin)
    def _extract_sample_size(self, source: EvidenceSource) -> int:
        return 1000  
    def get_evidence_based_recommendation(
        self,
        condition: str,
        patient_characteristics: Dict[str, Any],
        treatment_options: List[str],
    ) -> Dict[str, Any]:
        try:
            recommendations = []
            for treatment in treatment_options:
                synthesis = self.synthesize_evidence(
                    clinical_question=f"What is the effectiveness of {treatment} for {condition}?",
                    population=self._describe_population(patient_characteristics),
                    intervention=treatment,
                    outcomes=["efficacy", "safety", "quality_of_life"],
                )
                if synthesis:
                    guidelines = self.get_clinical_guidelines(condition)
                    recommendation = {
                        "treatment": treatment,
                        "evidence_synthesis": synthesis,
                        "guideline_support": len(guidelines),
                        "recommendation_strength": self._determine_recommendation_strength(
                            synthesis
                        ),
                        "confidence": synthesis.findings.get("consensus", "mixed"),
                        "key_evidence": [
                            {
                                "source": source.title,
                                "quality": source.quality.value,
                                "type": source.evidence_type.value,
                            }
                            for source in synthesis.evidence_sources[
                                :3
                            ]  
                        ],
                    }
                    recommendations.append(recommendation)
            recommendations.sort(
                key=lambda x: x["recommendation_strength"].value, reverse=True
            )
            return {
                "condition": condition,
                "patient_characteristics": patient_characteristics,
                "recommendations": recommendations,
                "timestamp": timezone.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error generating evidence-based recommendation: {str(e)}")
            return {"error": str(e)}
    def _describe_population(self, characteristics: Dict[str, Any]) -> str:
        age = characteristics.get("age", "adult")
        gender = characteristics.get("gender", "")
        comorbidities = characteristics.get("comorbidities", [])
        description = f"{age} patients"
        if gender:
            description += f" ({gender})"
        if comorbidities:
            description += f" with {', '.join(comorbidities)}"
        return description
    def _determine_recommendation_strength(
        self, synthesis: EvidenceSynthesis
    ) -> RecommendationStrength:
        quality_score = self._calculate_quality_score(synthesis.quality_assessment)
        if quality_score >= 0.8 and synthesis.findings.get("consensus") == "positive":
            return RecommendationStrength.STRONG
        elif quality_score >= 0.6:
            return RecommendationStrength.MODERATE
        else:
            return RecommendationStrength.WEAK
class GuidelineEngine:
    def __init__(self):
        self.evidence_engine = EvidenceBasedMedicineEngine()
    def apply_guidelines(
        self, patient_data: Dict[str, Any], condition: str
    ) -> List[Dict[str, Any]]:
        try:
            guidelines = self.evidence_engine.get_clinical_guidelines(condition)
            recommendations = []
            for guideline in guidelines:
                if self._patient_fits_population(
                    patient_data, guideline.target_population
                ):
                    for rec in guideline.recommendations:
                        recommendation = {
                            "guideline_id": guideline.guideline_id,
                            "guideline_title": guideline.title,
                            "organization": guideline.organization,
                            "recommendation": rec["recommendation"],
                            "strength": rec["strength"],
                            "evidence_level": rec["evidence_level"],
                            "applicability": self._assess_applicability(
                                patient_data, rec
                            ),
                        }
                        recommendations.append(recommendation)
            return recommendations
        except Exception as e:
            logger.error(f"Error applying guidelines: {str(e)}")
            return []
    def _patient_fits_population(
        self, patient_data: Dict[str, Any], target_population: str
    ) -> bool:
        age = patient_data.get("demographics", {}).get("age", 0)
        if "adult" in target_population.lower() and age >= 18:
            return True
        elif "pediatric" in target_population.lower() and age < 18:
            return True
        elif "elderly" in target_population.lower() and age >= 65:
            return True
        return False
    def _assess_applicability(
        self, patient_data: Dict[str, Any], recommendation: Dict[str, Any]
    ) -> str:
        contraindications = patient_data.get("contraindications", [])
        allergies = patient_data.get("allergies", [])
        if any(
            contraindication in recommendation["recommendation"].lower()
            for contraindication in contraindications
        ):
            return "contraindicated"
        elif any(
            allergy in recommendation["recommendation"].lower() for allergy in allergies
        ):
            return "use_with_caution"
        else:
            return "applicable"
def create_evidence_based_medicine_api():
    from rest_framework import viewsets, status
    from rest_framework.decorators import action
    from rest_framework.response import Response
    from rest_framework.permissions import IsAuthenticated
    class EvidenceBasedMedicineViewSet(viewsets.ViewSet):
        permission_classes = [IsAuthenticated]
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.ebm_engine = EvidenceBasedMedicineEngine()
            self.guideline_engine = GuidelineEngine()
        @action(detail=False, methods=["post"])
        def search_literature(self, request):
            try:
                query = request.data.get("query")
                max_results = request.data.get("max_results", 10)
                evidence_types = request.data.get("evidence_types")
                if evidence_types:
                    evidence_types = [EvidenceType(t) for t in evidence_types]
                results = self.ebm_engine.search_medical_literature(
                    query, max_results, evidence_types
                )
                return Response(
                    {
                        "query": query,
                        "results": [
                            {
                                "source_id": r.source_id,
                                "title": r.title,
                                "authors": r.authors,
                                "journal": r.journal,
                                "publication_date": r.publication_date.isoformat(),
                                "evidence_type": r.evidence_type.value,
                                "quality": r.quality.value,
                                "doi": r.doi,
                                "pmid": r.pmid,
                                "url": r.url,
                                "abstract": r.abstract,
                            }
                            for r in results
                        ],
                        "timestamp": timezone.now().isoformat(),
                    },
                    status=status.HTTP_200_OK,
                )
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        @action(detail=False, methods=["post"])
        def get_guidelines(self, request):
            try:
                condition = request.data.get("condition")
                organization = request.data.get("organization")
                guidelines = self.ebm_engine.get_clinical_guidelines(
                    condition, organization
                )
                return Response(
                    {
                        "condition": condition,
                        "guidelines": [
                            {
                                "guideline_id": g.guideline_id,
                                "title": g.title,
                                "organization": g.organization,
                                "publication_date": g.publication_date.isoformat(),
                                "last_updated": g.last_updated.isoformat(),
                                "condition": g.condition,
                                "target_population": g.target_population,
                                "recommendations": g.recommendations,
                                "strength": g.strength.value,
                                "quality": g.quality.value,
                            }
                            for g in guidelines
                        ],
                        "timestamp": timezone.now().isoformat(),
                    },
                    status=status.HTTP_200_OK,
                )
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        @action(detail=False, methods=["post"])
        def get_recommendation(self, request):
            try:
                condition = request.data.get("condition")
                patient_characteristics = request.data.get(
                    "patient_characteristics", {}
                )
                treatment_options = request.data.get("treatment_options", [])
                recommendation = self.ebm_engine.get_evidence_based_recommendation(
                    condition, patient_characteristics, treatment_options
                )
                return Response(recommendation, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return EvidenceBasedMedicineViewSet