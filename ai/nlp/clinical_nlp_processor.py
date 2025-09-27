"""
Clinical NLP Service for Medical Notes Processing
Implements advanced NLP capabilities for extracting insights from clinical documentation
"""

import json
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union

import nltk
import numpy as np
import pandas as pd
import prometheus_client
import spacy
import torch
from fastapi import FastAPI, HTTPException
from nltk.chunk import ne_chunk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tag import pos_tag
from nltk.tokenize import sent_tokenize, word_tokenize
from pydantic import BaseModel
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download required NLTK data
nltk.download("punkt", quiet=True)
nltk.download("stopwords", quiet=True)
nltk.download("averaged_perceptron_tagger", quiet=True)
nltk.download("maxent_ne_chunker", quiet=True)
nltk.download("words", quiet=True)
nltk.download("wordnet", quiet=True)

# Prometheus metrics
NLP_PROCESSED_NOTES = prometheus_client.Counter(
    "hms_nlp_processed_notes_total",
    "Total number of clinical notes processed",
    ["note_type", "extraction_type"],
)

ENTITY_EXTRACTION_COUNT = prometheus_client.Counter(
    "hms_entity_extraction_total", "Total entities extracted", ["entity_type"]
)

NLP_PROCESSING_LATENCY = prometheus_client.Histogram(
    "hms_nlp_processing_latency_seconds", "NLP processing latency", ["note_type"]
)


# Pydantic models
class ClinicalNote(BaseModel):
    note_id: str
    patient_id: str
    note_type: str  # 'progress_note', 'discharge_summary', 'consultation', etc.
    note_date: str
    author: str
    content: str


class ExtractedEntity(BaseModel):
    text: str
    entity_type: str
    start_pos: int
    end_pos: int
    confidence: float
    normalized_value: Optional[str] = None


class MedicationEntity(BaseModel):
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    duration: Optional[str] = None
    indication: Optional[str] = None


class ConditionEntity(BaseModel):
    condition: str
    status: str  # 'active', 'resolved', 'chronic'
    severity: Optional[str] = None
    onset_date: Optional[str] = None
    body_system: Optional[str] = None


class NLPExtractionResult(BaseModel):
    note_id: str
    patient_id: str
    processing_timestamp: str
    entities: List[ExtractedEntity]
    medications: List[MedicationEntity]
    conditions: List[ConditionEntity]
    procedures: List[Dict]
    lab_values: List[Dict]
    vital_signs: List[Dict]
    allergies: List[Dict]
    social_history: Dict
    family_history: List[Dict]
    assessment: Dict
    plan: List[str]
    sentiment: Dict
    readability_score: float
    quality_metrics: Dict


class ClinicalNLPProcessor:
    """
    Advanced clinical NLP processor for medical notes
    """

    def __init__(self):
        # Load spaCy medical model
        try:
            self.nlp = spacy.load("en_core_medical_lg")
        except OSError:
            logger.warning("Medical spaCy model not found, using base model")
            self.nlp = spacy.load("en_core_web_lg")
            self.add_medical_patterns()

        # Load BioClinicalBERT for clinical text classification
        self.tokenizer = AutoTokenizer.from_pretrained(
            "emilyalsentzer/Bio_ClinicalBERT"
        )
        self.classifier = AutoModelForSequenceClassification.from_pretrained(
            "emilyalsentzer/Bio_ClinicalBERT"
        )

        # Initialize specialized pipelines
        self.medication_extractor = self._create_medication_extractor()
        self.condition_extractor = self._create_condition_extractor()
        self.sentiment_analyzer = pipeline(
            "sentiment-analysis", model="siebert/sentiment-roberta-large-english"
        )

        # Initialize text processing utilities
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words("english"))

        # Medical patterns and dictionaries
        self.medical_patterns = self._load_medical_patterns()
        self.medications_db = self._load_medications_database()
        self.conditions_db = self._load_conditions_database()

    def add_medical_patterns(self):
        """Add medical entity patterns to spaCy pipeline"""
        patterns = [
            {
                "label": "MEDICATION",
                "pattern": [{"LOWER": {"REGEX": r"^[a-z]+(ol|in|one|ium|ide|pine)$"}}],
            },
            {
                "label": "DOSAGE",
                "pattern": [{"SHAPE": "dd"}, {"LOWER": "mg"}, {"LOWER": "daily"}],
            },
            {
                "label": "CONDITION",
                "pattern": [
                    {
                        "LOWER": {
                            "REGEX": r"^(diabetes|hypertension|asthma|copd|heart failure|pneumonia)$"
                        }
                    }
                ],
            },
        ]
        ruler = self.nlp.add_pipe("entity_ruler", before="ner")
        ruler.add_patterns(patterns)

    def _create_medication_extractor(self):
        """Create medication extraction pipeline"""
        # This would typically use a specialized medication extraction model
        return pipeline("ner", model="samrawal/bert-base-uncased-clinical-ner")

    def _create_condition_extractor(self):
        """Create condition extraction pipeline"""
        # This would typically use a specialized condition extraction model
        return pipeline("ner", model="samrawal/bert-base-uncased-clinical-ner")

    def _load_medical_patterns(self):
        """Load medical regex patterns"""
        return {
            "dosage": r"(\d+(?:\.\d+)?)\s*(mg|g|mcg|ml|units?|tabs?|caps?)\s*(?:q(\d+)h|(?:once|twice|three times)\s*daily|daily|bid|tid|qid)?",
            "vital_signs": r"(BP|HR|RR|Temp|O2Sat|SpO2):\s*(\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?)",
            "lab_value": r"(\w+)\s*[:=]\s*(\d+(?:\.\d+)?)\s*([a-zA-Z/]+)",
            "date": r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})",
            "allergy": r"(?:allergy|allergic to)\s*:\s*([^,.;]+)",
            "family_history": r"(?:mother|father|sister|brother|maternal|paternal)\s*(?:with|history of|hx)\s*([^,.;]+)",
        }

    def _load_medications_database(self):
        """Load medications database for normalization"""
        # In production, this would load from a proper medications database
        return {
            "aspirin": {"generic_name": "acetylsalicylic acid", "class": "NSAID"},
            "lisinopril": {"generic_name": "lisinopril", "class": "ACE inhibitor"},
            "metformin": {"generic_name": "metformin", "class": "biguanide"},
            "atorvastatin": {"generic_name": "atorvastatin", "class": "statin"},
            "amlodipine": {
                "generic_name": "amlodipine",
                "class": "calcium channel blocker",
            },
        }

    def _load_conditions_database(self):
        """Load conditions database for normalization"""
        return {
            "htn": {"full_name": "hypertension", "icd10": "I10"},
            "dm": {"full_name": "diabetes mellitus", "icd10": "E11"},
            "copd": {
                "full_name": "chronic obstructive pulmonary disease",
                "icd10": "J44",
            },
            "chf": {"full_name": "congestive heart failure", "icd10": "I50"},
            "cad": {"full_name": "coronary artery disease", "icd10": "I25"},
        }

    def process_clinical_note(self, note: ClinicalNote) -> NLPExtractionResult:
        """
        Process clinical note and extract all relevant information

        Args:
            note: Clinical note object

        Returns:
            Structured extraction result
        """
        start_time = time.time()

        # Process with spaCy
        doc = self.nlp(note.content)

        # Extract entities
        entities = self._extract_entities(doc)

        # Extract specific clinical concepts
        medications = self._extract_medications(note.content)
        conditions = self._extract_conditions(note.content)
        procedures = self._extract_procedures(note.content)
        lab_values = self._extract_lab_values(note.content)
        vital_signs = self._extract_vital_signs(note.content)
        allergies = self._extract_allergies(note.content)

        # Extract narrative sections
        social_history = self._extract_social_history(note.content)
        family_history = self._extract_family_history(note.content)
        assessment = self._extract_assessment(note.content)
        plan = self._extract_plan(note.content)

        # Analyze sentiment
        sentiment = self._analyze_sentiment(note.content)

        # Calculate readability score
        readability_score = self._calculate_readability(note.content)

        # Quality metrics
        quality_metrics = self._assess_note_quality(note.content)

        # Update metrics
        NLP_PROCESSED_NOTES.labels(
            note_type=note.note_type, extraction_type="full"
        ).inc()
        NLP_PROCESSING_LATENCY.labels(note_type=note.note_type).observe(
            time.time() - start_time
        )

        return NLPExtractionResult(
            note_id=note.note_id,
            patient_id=note.patient_id,
            processing_timestamp=datetime.utcnow().isoformat(),
            entities=entities,
            medications=medications,
            conditions=conditions,
            procedures=procedures,
            lab_values=lab_values,
            vital_signs=vital_signs,
            allergies=allergies,
            social_history=social_history,
            family_history=family_history,
            assessment=assessment,
            plan=plan,
            sentiment=sentiment,
            readability_score=readability_score,
            quality_metrics=quality_metrics,
        )

    def _extract_entities(self, doc) -> List[ExtractedEntity]:
        """Extract named entities from document"""
        entities = []

        for ent in doc.ents:
            # Normalize entity value
            normalized_value = self._normalize_entity(ent.text, ent.label_)

            entity = ExtractedEntity(
                text=ent.text,
                entity_type=ent.label_,
                start_pos=ent.start_char,
                end_pos=ent.end_char,
                confidence=0.8,  # Placeholder confidence
                normalized_value=normalized_value,
            )
            entities.append(entity)

            # Update metrics
            ENTITY_EXTRACTION_COUNT.labels(entity_type=ent.label_).inc()

        return entities

    def _normalize_entity(self, text: str, entity_type: str) -> Optional[str]:
        """Normalize entity value to standard form"""
        text = text.lower().strip()

        if entity_type == "MEDICATION":
            # Check medications database
            for med, details in self.medications_db.items():
                if med in text or details["generic_name"] in text:
                    return details["generic_name"]

        elif entity_type == "CONDITION":
            # Check conditions database
            for cond, details in self.conditions_db.items():
                if cond in text or details["full_name"] in text:
                    return details["full_name"]

        return text

    def _extract_medications(self, text: str) -> List[MedicationEntity]:
        """Extract medication information"""
        medications = []

        # Use regex patterns for basic extraction
        med_patterns = [
            r"(\w+)\s+(\d+(?:\.\d+)?)\s*(mg|g|mcg)\s*(?:q(\d+)h|daily|bid|tid|qid)?",
            r"(\w+)\s+(\d+)\s*(tabs?|caps?)\s*(?:q(\d+)h|daily|bid|tid|qid)?",
        ]

        for pattern in med_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                med = MedicationEntity(
                    name=match.group(1),
                    dosage=f"{match.group(2)} {match.group(3)}",
                    frequency=self._normalize_frequency(match.group(4)),
                    route=self._infer_route(match.group(1)),
                )
                medications.append(med)

        return medications

    def _extract_conditions(self, text: str) -> List[ConditionEntity]:
        """Extract medical conditions"""
        conditions = []

        # Use spaCy and additional patterns
        doc = self.nlp(text)

        # Look for condition patterns
        condition_patterns = [
            (r"(?:history of|hx)\s+(?:\w+\s+)*(\w+)", "resolved"),
            (r"(\w+)\s+(?:improved|resolved)", "resolved"),
            (r"(?:active|current)\s+(\w+)", "active"),
            (r"(\w+)\s+(?:worsening|severe|acute)", "active"),
        ]

        for pattern, status in condition_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                condition = ConditionEntity(
                    condition=match.group(1),
                    status=status,
                    body_system=self._infer_body_system(match.group(1)),
                )
                conditions.append(condition)

        return conditions

    def _extract_procedures(self, text: str) -> List[Dict]:
        """Extract medical procedures"""
        procedures = []

        # Common procedure keywords
        procedure_keywords = [
            "surgery",
            "operation",
            "procedure",
            "biopsy",
            "endoscopy",
            "colonoscopy",
            "catheterization",
            "intubation",
            "ventilation",
        ]

        sentences = sent_tokenize(text)
        for sentence in sentences:
            for keyword in procedure_keywords:
                if keyword in sentence.lower():
                    procedures.append(
                        {
                            "procedure": sentence.strip(),
                            "date": self._extract_date(sentence),
                            "context": "procedure",
                        }
                    )

        return procedures

    def _extract_lab_values(self, text: str) -> List[Dict]:
        """Extract laboratory values"""
        lab_values = []

        # Use medical patterns
        matches = re.finditer(self.medical_patterns["lab_value"], text)
        for match in matches:
            lab_values.append(
                {
                    "test_name": match.group(1),
                    "value": float(match.group(2)),
                    "unit": match.group(3),
                    "context": match.group(0),
                }
            )

        return lab_values

    def _extract_vital_signs(self, text: str) -> List[Dict]:
        """Extract vital signs"""
        vital_signs = []

        matches = re.finditer(self.medical_patterns["vital_signs"], text)
        for match in matches:
            vital_type = match.group(1)
            value = match.group(2)

            # Parse different vital sign formats
            if vital_type.lower() == "bp" and "/" in value:
                systolic, diastolic = value.split("/")
                vital_signs.append(
                    {
                        "type": "blood_pressure",
                        "systolic": float(systolic),
                        "diastolic": float(diastolic),
                        "context": match.group(0),
                    }
                )
            else:
                vital_signs.append(
                    {
                        "type": vital_type.lower(),
                        "value": float(value),
                        "context": match.group(0),
                    }
                )

        return vital_signs

    def _extract_allergies(self, text: str) -> List[Dict]:
        """Extract patient allergies"""
        allergies = []

        matches = re.finditer(self.medical_patterns["allergy"], text, re.IGNORECASE)
        for match in matches:
            allergies.append(
                {
                    "allergen": match.group(1).strip(),
                    "reaction": "unknown",  # Would need more sophisticated parsing
                    "severity": "unknown",
                    "context": match.group(0),
                }
            )

        return allergies

    def _extract_social_history(self, text: str) -> Dict:
        """Extract social history"""
        social_history = {
            "smoking": self._extract_smoking_status(text),
            "alcohol": self._extract_alcohol_use(text),
            "substance_use": self._extract_substance_use(text),
            "occupation": self._extract_occupation(text),
            "living_situation": self._extract_living_situation(text),
        }

        return social_history

    def _extract_family_history(self, text: str) -> List[Dict]:
        """Extract family medical history"""
        family_history = []

        matches = re.finditer(
            self.medical_patterns["family_history"], text, re.IGNORECASE
        )
        for match in matches:
            family_history.append(
                {
                    "relation": match.group(1),
                    "condition": match.group(2),
                    "context": match.group(0),
                }
            )

        return family_history

    def _extract_assessment(self, text: str) -> Dict:
        """Extract assessment section"""
        assessment = {
            "primary_diagnosis": [],
            "secondary_diagnoses": [],
            "differential_diagnoses": [],
            "summary": "",
        }

        # Look for assessment section headers
        sections = self._split_into_sections(text)
        if "assessment" in sections:
            assessment_text = sections["assessment"]
            assessment["summary"] = assessment_text

            # Extract diagnoses
            primary_patterns = [
                r"primary diagnosis:\s*([^,.;]+)",
                r"chief complaint:\s*([^,.;]+)",
                r"admitting diagnosis:\s*([^,.;]+)",
            ]

            for pattern in primary_patterns:
                matches = re.finditer(pattern, assessment_text, re.IGNORECASE)
                for match in matches:
                    assessment["primary_diagnosis"].append(match.group(1).strip())

        return assessment

    def _extract_plan(self, text: str) -> List[str]:
        """Extract treatment plan"""
        plan_items = []

        sections = self._split_into_sections(text)
        if "plan" in sections:
            plan_text = sections["plan"]

            # Extract numbered or bulleted items
            items = re.findall(r"(?:\d+\.|[-*•])\s*([^\n]+)", plan_text)
            plan_items.extend([item.strip() for item in items])

            # Extract action items
            actions = re.findall(
                r"(will|plan to|recommend|suggest|order)\s+([^\.;]+)",
                plan_text,
                re.IGNORECASE,
            )
            plan_items.extend([f"{action[0]} {action[1]}" for action in actions])

        return plan_items

    def _analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of clinical note"""
        # Process in chunks due to model limitations
        chunk_size = 512
        chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

        sentiments = []
        for chunk in chunks:
            if chunk.strip():
                result = self.sentiment_analyzer(chunk)[0]
                sentiments.append(result)

        # Aggregate sentiments
        if sentiments:
            avg_score = np.mean(
                [
                    s["score"] if s["label"] == "POSITIVE" else -s["score"]
                    for s in sentiments
                ]
            )
            overall_sentiment = (
                "positive"
                if avg_score > 0.1
                else "negative" if avg_score < -0.1 else "neutral"
            )
        else:
            avg_score = 0
            overall_sentiment = "neutral"

        return {
            "overall": overall_sentiment,
            "score": float(avg_score),
            "chunks": sentiments,
        }

    def _calculate_readability(self, text: str) -> float:
        """Calculate Flesch Reading Ease score"""
        sentences = sent_tokenize(text)
        words = word_tokenize(text)

        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        avg_syllables_per_word = (
            np.mean([self._count_syllables(word) for word in words]) if words else 0
        )

        # Flesch Reading Ease formula
        score = (
            206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        )
        return max(0, min(100, score))

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (simplified)"""
        word = word.lower()
        if word.endswith("e"):
            word = word[:-1]
        vowels = "aeiouy"
        count = 0
        prev_char_was_vowel = False
        for char in word:
            if char in vowels and not prev_char_was_vowel:
                count += 1
                prev_char_was_vowel = True
            else:
                prev_char_was_vowel = False
        return max(1, count)

    def _assess_note_quality(self, text: str) -> Dict:
        """Assess quality of clinical note"""
        quality_metrics = {
            "completeness": 0,
            "structure": 0,
            "clarity": 0,
            "specificity": 0,
            "timeliness": 0,
        }

        # Check for required sections
        sections = self._split_into_sections(text)
        required_sections = ["subjective", "objective", "assessment", "plan"]
        quality_metrics["structure"] = (
            len([s for s in required_sections if s in sections])
            / len(required_sections)
            * 100
        )

        # Check completeness
        if len(text) < 100:
            quality_metrics["completeness"] = 30
        elif len(text) < 500:
            quality_metrics["completeness"] = 60
        else:
            quality_metrics["completeness"] = 90

        # Check clarity (based on sentence length)
        sentences = sent_tokenize(text)
        avg_sentence_length = (
            np.mean([len(word_tokenize(s)) for s in sentences]) if sentences else 0
        )
        quality_metrics["clarity"] = 100 - min(50, abs(avg_sentence_length - 15) * 2)

        # Check specificity (look for specific values)
        specific_values = len(re.findall(r"\d+(?:\.\d+)?", text))
        quality_metrics["specificity"] = min(100, specific_values * 2)

        return quality_metrics

    def _split_into_sections(self, text: str) -> Dict[str, str]:
        """Split clinical note into sections"""
        sections = {}
        section_patterns = [
            (
                r"subjective[:\-]?\s*(.*?)(?=objective[:\-]|assessment[:\-]|plan[:\-]|$)",
                "subjective",
            ),
            (
                r"objective[:\-]?\s*(.*?)(?=subjective[:\-]|assessment[:\-]|plan[:\-]|$)",
                "objective",
            ),
            (
                r"assessment[:\-]?\s*(.*?)(?=subjective[:\-]|objective[:\-]|plan[:\-]|$)",
                "assessment",
            ),
            (
                r"plan[:\-]?\s*(.*?)(?=subjective[:\-]|objective[:\-]|assessment[:\-]|$)",
                "plan",
            ),
        ]

        for pattern, section_name in section_patterns:
            matches = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                sections[section_name] = matches.group(1).strip()

        return sections

    def _normalize_frequency(self, freq: str) -> str:
        """Normalize medication frequency"""
        freq_mapping = {
            "1": "daily",
            "2": "twice daily",
            "3": "three times daily",
            "4": "four times daily",
            "6": "every 6 hours",
            "8": "every 8 hours",
            "12": "every 12 hours",
        }
        return freq_mapping.get(freq, freq)

    def _infer_route(self, medication: str) -> str:
        """Infer medication route from name"""
        route_indicators = {
            "inhaler": "inhalation",
            "spray": "nasal",
            "drops": "ophthalmic/otic",
            "patch": "transdermal",
            "injection": "injectable",
        }

        for indicator, route in route_indicators.items():
            if indicator in medication.lower():
                return route
        return "oral"

    def _infer_body_system(self, condition: str) -> str:
        """Infer body system from condition"""
        system_mapping = {
            "cardiac": ["heart", "cardiac", "coronary", "hypertension"],
            "respiratory": ["lung", "pulmonary", "asthma", "copd"],
            "endocrine": ["diabetes", "thyroid", "hormone"],
            "neurological": ["brain", "neuro", "seizure", "stroke"],
            "gastrointestinal": ["stomach", "gastric", "colon", "liver"],
        }

        condition_lower = condition.lower()
        for system, keywords in system_mapping.items():
            if any(keyword in condition_lower for keyword in keywords):
                return system
        return "general"

    def _extract_smoking_status(self, text: str) -> str:
        """Extract smoking status"""
        smoking_patterns = [
            (r"never smoked?", "never"),
            (r"former smoker|quit smoking|ex-smoker", "former"),
            (r"current smoker|smokes? \d+ packs?/day", "current"),
            (r"pack(?: |-)years?\s*:\s*(\d+)", "pack_years"),
        ]

        for pattern, status in smoking_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return (
                    status if status != "pack_years" else f"{match.group(1)} pack-years"
                )
        return "unknown"

    def _extract_alcohol_use(self, text: str) -> str:
        """Extract alcohol use"""
        patterns = [
            (r"no alcohol|doesn\'t drink|non-drinker", "none"),
            (r"social drinker|occasional alcohol", "social"),
            (r"\d+ drinks?/day|alcohol abuse|alcoholism", "heavy"),
        ]

        for pattern, use in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return use
        return "unknown"

    def _extract_substance_use(self, text: str) -> str:
        """Extract substance use"""
        if re.search(r"no illicit drugs|no substance use", text, re.IGNORECASE):
            return "none"
        elif re.search(
            r"heroin|cocaine|marijuana|methamphetamine", text, re.IGNORECASE
        ):
            return "positive"
        return "unknown"

    def _extract_occupation(self, text: str) -> str:
        """Extract occupation"""
        match = re.search(r"occupation[:\-]?\s*([^\.;]+)", text, re.IGNORECASE)
        return match.group(1).strip() if match else "unknown"

    def _extract_living_situation(self, text: str) -> str:
        """Extract living situation"""
        match = re.search(
            r"(?:lives? with|living situation)[:\-]?\s*([^\.;]+)", text, re.IGNORECASE
        )
        return match.group(1).strip() if match else "unknown"

    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date from text"""
        match = re.search(self.medical_patterns["date"], text)
        return match.group(1) if match else None


# FastAPI app
app = FastAPI(title="HMS Clinical NLP Service", version="1.0.0")

# Initialize processor
processor = ClinicalNLPProcessor()


@app.post("/process/note", response_model=NLPExtractionResult)
async def process_note(note: ClinicalNote):
    """Process clinical note and extract information"""
    try:
        return processor.process_clinical_note(note)
    except Exception as e:
        logger.error(f"Error processing note: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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

    uvicorn.run(app, host="0.0.0.0", port=8002)
