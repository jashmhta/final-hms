"""
fhir_server module
"""

import json
import logging
import uuid
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from .orchestrator import IntegrationOrchestrator, IntegrationStandards

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
Base = declarative_base()


class FHIRResourceType(Enum):
    PATIENT = "Patient"
    PRACTITIONER = "Practitioner"
    ORGANIZATION = "Organization"
    ENCOUNTER = "Encounter"
    OBSERVATION = "Observation"
    CONDITION = "Condition"
    PROCEDURE = "Procedure"
    MEDICATION = "Medication"
    MEDICATION_REQUEST = "MedicationRequest"
    ALLERGY_INTOLERANCE = "AllergyIntolerance"
    IMMUNIZATION = "Immunization"
    DIAGNOSTIC_REPORT = "DiagnosticReport"
    SERVICE_REQUEST = "ServiceRequest"
    LOCATION = "Location"
    SCHEDULE = "Schedule"
    APPOINTMENT = "Appointment"
    CLAIM = "Claim"
    COVERAGE = "Coverage"
    EXPLANATION_OF_BENEFIT = "ExplanationOfBenefit"


class FHIRResource(Base):
    __tablename__ = "fhir_resources"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(50), nullable=False, index=True)
    version_id = Column(String(50), nullable=False)
    content = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    __table_args__ = {"extend_existing": True}


class FHIRPatient(Base):
    __tablename__ = "fhir_patients"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fhir_resource_id = Column(
        String(36), ForeignKey("fhir_resources.id"), nullable=False
    )
    identifier = Column(JSON)
    name = Column(JSON)
    telecom = Column(JSON)
    gender = Column(String(20))
    birth_date = Column(Date)
    deceased_boolean = Column(Boolean)
    deceased_datetime = Column(DateTime)
    address = Column(JSON)
    marital_status = Column(JSON)
    multiple_birth_boolean = Column(Boolean)
    multiple_birth_integer = Column(Integer)
    photo = Column(JSON)
    contact = Column(JSON)
    communication = Column(JSON)
    general_practitioner = Column(JSON)
    managing_organization = Column(JSON)
    link = Column(JSON)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FHIREncounter(Base):
    __tablename__ = "fhir_encounters"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fhir_resource_id = Column(
        String(36), ForeignKey("fhir_resources.id"), nullable=False
    )
    identifier = Column(JSON)
    status = Column(String(20), nullable=False)
    status_history = Column(JSON)
    class_codes = Column(JSON)
    subject = Column(JSON)
    episode_of_care = Column(JSON)
    participant = Column(JSON)
    appointment = Column(JSON)
    period = Column(JSON)
    length = Column(JSON)
    reason_code = Column(JSON)
    reason_reference = Column(JSON)
    diagnosis = Column(JSON)
    account = Column(JSON)
    hospitalization = Column(JSON)
    location = Column(JSON)
    service_provider = Column(JSON)
    part_of = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FHIRIdentifier(BaseModel):
    system: Optional[str] = None
    value: Optional[str] = None
    use: Optional[str] = None
    type: Optional[Dict] = None
    period: Optional[Dict] = None
    assigner: Optional[Dict] = None


class FHIRHumanName(BaseModel):
    use: Optional[str] = None
    text: Optional[str] = None
    family: Optional[str] = None
    given: Optional[List[str]] = None
    prefix: Optional[List[str]] = None
    suffix: Optional[List[str]] = None
    period: Optional[Dict] = None


class FHIRContactPoint(BaseModel):
    system: Optional[str] = None
    value: Optional[str] = None
    use: Optional[str] = None
    rank: Optional[int] = None
    period: Optional[Dict] = None


class FHIRAddress(BaseModel):
    use: Optional[str] = None
    type: Optional[str] = None
    text: Optional[str] = None
    line: Optional[List[str]] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    period: Optional[Dict] = None


class FHIRPatientModel(BaseModel):
    resourceType: str = Field("Patient", const=True)
    id: Optional[str] = None
    meta: Optional[Dict] = None
    implicitRules: Optional[str] = None
    language: Optional[str] = None
    text: Optional[Dict] = None
    contained: Optional[List[Dict]] = None
    extension: Optional[List[Dict]] = None
    modifierExtension: Optional[List[Dict]] = None
    identifier: Optional[List[FHIRIdentifier]] = None
    active: Optional[bool] = None
    name: Optional[List[FHIRHumanName]] = None
    telecom: Optional[List[FHIRContactPoint]] = None
    gender: Optional[str] = None
    birthDate: Optional[date] = None
    deceasedBoolean: Optional[bool] = None
    deceasedDateTime: Optional[datetime] = None
    address: Optional[List[FHIRAddress]] = None
    maritalStatus: Optional[Dict] = None
    multipleBirthBoolean: Optional[bool] = None
    multipleBirthInteger: Optional[int] = None
    photo: Optional[List[Dict]] = None
    contact: Optional[List[Dict]] = None
    communication: Optional[List[Dict]] = None
    generalPractitioner: Optional[List[Dict]] = None
    managingOrganization: Optional[Dict] = None
    link: Optional[List[Dict]] = None


class FHIREncounterModel(BaseModel):
    resourceType: str = Field("Encounter", const=True)
    id: Optional[str] = None
    meta: Optional[Dict] = None
    implicitRules: Optional[str] = None
    language: Optional[str] = None
    text: Optional[Dict] = None
    contained: Optional[List[Dict]] = None
    extension: Optional[List[Dict]] = None
    modifierExtension: Optional[List[Dict]] = None
    identifier: Optional[List[FHIRIdentifier]] = None
    status: str
    statusHistory: Optional[List[Dict]] = None
    class_codes: Optional[List[Dict]] = None
    subject: Optional[Dict] = None
    episodeOfCare: Optional[List[Dict]] = None
    participant: Optional[List[Dict]] = None
    appointment: Optional[List[Dict]] = None
    period: Optional[Dict] = None
    length: Optional[Dict] = None
    reasonCode: Optional[List[Dict]] = None
    reasonReference: Optional[List[Dict]] = None
    diagnosis: Optional[List[Dict]] = None
    account: Optional[List[Dict]] = None
    hospitalization: Optional[Dict] = None
    location: Optional[List[Dict]] = None
    serviceProvider: Optional[Dict] = None
    partOf: Optional[Dict] = None


class FHIRObservationModel(BaseModel):
    resourceType: str = Field("Observation", const=True)
    id: Optional[str] = None
    meta: Optional[Dict] = None
    implicitRules: Optional[str] = None
    language: Optional[str] = None
    text: Optional[Dict] = None
    contained: Optional[List[Dict]] = None
    extension: Optional[List[Dict]] = None
    modifierExtension: Optional[List[Dict]] = None
    identifier: Optional[List[FHIRIdentifier]] = None
    basedOn: Optional[List[Dict]] = None
    partOf: Optional[List[Dict]] = None
    status: str
    category: Optional[List[Dict]] = None
    code: Dict
    subject: Optional[Dict] = None
    focus: Optional[List[Dict]] = None
    encounter: Optional[Dict] = None
    effectiveDateTime: Optional[datetime] = None
    effectivePeriod: Optional[Dict] = None
    issued: Optional[datetime] = None
    performer: Optional[List[Dict]] = None
    valueQuantity: Optional[Dict] = None
    valueCodeableConcept: Optional[Dict] = None
    valueString: Optional[str] = None
    valueBoolean: Optional[bool] = None
    valueInteger: Optional[int] = None
    valueRange: Optional[Dict] = None
    valueRatio: Optional[Dict] = None
    valueSampledData: Optional[Dict] = None
    valueTime: Optional[str] = None
    valueDateTime: Optional[datetime] = None
    valuePeriod: Optional[Dict] = None
    dataAbsentReason: Optional[Dict] = None
    interpretation: Optional[List[Dict]] = None
    note: Optional[List[Dict]] = None
    bodySite: Optional[Dict] = None
    method: Optional[Dict] = None
    specimen: Optional[Dict] = None
    device: Optional[Dict] = None
    referenceRange: Optional[List[Dict]] = None
    hasMember: Optional[List[Dict]] = None
    derivedFrom: Optional[List[Dict]] = None
    component: Optional[List[Dict]] = None


class FHIRServer:
    def __init__(self, orchestrator: IntegrationOrchestrator):
        self.orchestrator = orchestrator
        self.db_url = os.getenv(
            "FHIR_DB_URL", "postgresql+asyncpg://hms:hms@localhost:5432/fhir"
        )
        self.engine = create_async_engine(self.db_url)
        self.SessionLocal = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def create_patient(self, patient_data: FHIRPatientModel) -> Dict:
        async with self.SessionLocal() as session:
            try:
                resource_id = str(uuid.uuid4())
                version_id = "1"
                resource = FHIRResource(
                    id=resource_id,
                    resource_type=FHIRResourceType.PATIENT.value,
                    resource_id=patient_data.id or resource_id,
                    version_id=version_id,
                    content=patient_data.dict(exclude_none=True),
                )
                session.add(resource)
                patient = FHIRPatient(
                    fhir_resource_id=resource_id,
                    identifier=patient_data.identifier,
                    name=patient_data.name,
                    telecom=patient_data.telecom,
                    gender=patient_data.gender,
                    birth_date=patient_data.birthDate,
                    deceased_boolean=patient_data.deceasedBoolean,
                    deceased_datetime=patient_data.deceasedDateTime,
                    address=patient_data.address,
                    active=patient_data.active,
                )
                session.add(patient)
                await session.commit()
                return {
                    "resourceType": "Patient",
                    "id": resource_id,
                    "meta": {
                        "versionId": version_id,
                        "lastUpdated": datetime.utcnow().isoformat(),
                    },
                    **patient_data.dict(exclude_none=True),
                }
            except Exception as e:
                await session.rollback()
                logger.error(f"Error creating FHIR patient: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Failed to create patient: {str(e)}"
                )

    async def get_patient(self, patient_id: str) -> Dict:
        async with self.SessionLocal() as session:
            try:
                patient = await session.execute(
                    session.query(FHIRPatient)
                    .join(FHIRResource)
                    .filter(FHIRResource.resource_id == patient_id)
                    .filter(
                        FHIRResource.resource_type == FHIRResourceType.PATIENT.value
                    )
                    .filter(FHIRResource.is_active == True)
                )
                patient_result = patient.scalar_one_or_none()
                if not patient_result:
                    raise HTTPException(status_code=404, detail="Patient not found")
                return {
                    "resourceType": "Patient",
                    "id": patient_id,
                    "meta": {
                        "versionId": patient_result.fhir_resource.version_id,
                        "lastUpdated": patient_result.updated_at.isoformat(),
                    },
                    **patient_result.fhir_resource.content,
                }
            except Exception as e:
                logger.error(f"Error getting FHIR patient {patient_id}: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Failed to get patient: {str(e)}"
                )

    async def search_patients(self, **kwargs) -> Dict:
        async with self.SessionLocal() as session:
            try:
                query = (
                    session.query(FHIRPatient)
                    .join(FHIRResource)
                    .filter(
                        FHIRResource.resource_type == FHIRResourceType.PATIENT.value,
                        FHIRResource.is_active == True,
                    )
                )
                if "name" in kwargs:
                    name_filter = kwargs["name"].lower()
                    query = query.filter(FHIRPatient.name.ilike(f"%{name_filter}%"))
                if "identifier" in kwargs:
                    identifier_filter = kwargs["identifier"]
                    query = query.filter(
                        FHIRPatient.identifier.ilike(f"%{identifier_filter}%")
                    )
                if "birth_date" in kwargs:
                    query = query.filter(FHIRPatient.birth_date == kwargs["birth_date"])
                if "gender" in kwargs:
                    query = query.filter(FHIRPatient.gender == kwargs["gender"])
                page = kwargs.get("page", 1)
                per_page = kwargs.get("_count", 50)
                offset = (page - 1) * per_page
                results = await session.execute(query.offset(offset).limit(per_page))
                patients = results.scalars().all()
                total_count = await session.execute(query)
                total = len(total_count.scalars().all())
                return {
                    "resourceType": "Bundle",
                    "id": str(uuid.uuid4()),
                    "type": "searchset",
                    "total": total,
                    "link": [
                        {
                            "relation": "self",
                            "url": f"/fhir/Patient?{'&'.join(f'{k}={v}' for k, v in kwargs.items())}",
                        }
                    ],
                    "entry": [
                        {
                            "fullUrl": f"/fhir/Patient/{patient.fhir_resource.resource_id}",
                            "resource": {
                                "resourceType": "Patient",
                                "id": patient.fhir_resource.resource_id,
                                "meta": {
                                    "versionId": patient.fhir_resource.version_id,
                                    "lastUpdated": patient.updated_at.isoformat(),
                                },
                                **patient.fhir_resource.content,
                            },
                        }
                        for patient in patients
                    ],
                }
            except Exception as e:
                logger.error(f"Error searching FHIR patients: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Failed to search patients: {str(e)}"
                )

    async def create_encounter(self, encounter_data: FHIREncounterModel) -> Dict:
        async with self.SessionLocal() as session:
            try:
                resource_id = str(uuid.uuid4())
                version_id = "1"
                resource = FHIRResource(
                    id=resource_id,
                    resource_type=FHIRResourceType.ENCOUNTER.value,
                    resource_id=encounter_data.id or resource_id,
                    version_id=version_id,
                    content=encounter_data.dict(exclude_none=True),
                )
                session.add(resource)
                encounter = FHIREncounter(
                    fhir_resource_id=resource_id,
                    identifier=encounter_data.identifier,
                    status=encounter_data.status,
                    status_history=encounter_data.statusHistory,
                    class_codes=encounter_data.class_codes,
                    subject=encounter_data.subject,
                    period=encounter_data.period,
                    reason_code=encounter_data.reasonCode,
                    location=encounter_data.location,
                )
                session.add(encounter)
                await session.commit()
                return {
                    "resourceType": "Encounter",
                    "id": resource_id,
                    "meta": {
                        "versionId": version_id,
                        "lastUpdated": datetime.utcnow().isoformat(),
                    },
                    **encounter_data.dict(exclude_none=True),
                }
            except Exception as e:
                await session.rollback()
                logger.error(f"Error creating FHIR encounter: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Failed to create encounter: {str(e)}"
                )

    async def get_conformance_statement(self) -> Dict:
        return {
            "resourceType": "CapabilityStatement",
            "id": "hms-fhir-server",
            "url": "https://api.hms-enterprise.com/fhir/metadata",
            "version": "1.0.0",
            "name": "HMS Enterprise FHIR Server",
            "title": "Hospital Management System FHIR R4 Server",
            "status": "active",
            "date": datetime.utcnow().isoformat(),
            "publisher": "HMS Enterprise",
            "contact": [
                {
                    "name": "HMS Integration Team",
                    "telecom": [
                        {"system": "email", "value": "integration@hms-enterprise.com"}
                    ],
                }
            ],
            "description": "FHIR R4 compliant server for Hospital Management System",
            "kind": "instance",
            "software": {"name": "HMS FHIR Server", "version": "1.0.0"},
            "implementation": {
                "description": "HMS Enterprise FHIR Server",
                "url": "https://api.hms-enterprise.com/fhir",
            },
            "fhirVersion": "4.0.1",
            "format": ["application/fhir+json", "application/fhir+xml"],
            "rest": [
                {
                    "mode": "server",
                    "documentation": "FHIR RESTful API for HMS Enterprise",
                    "security": {
                        "cors": True,
                        "service": [
                            {
                                "coding": [
                                    {
                                        "system": "http://terminology.hl7.org/CodeSystem/restful-security-service",
                                        "code": "OAuth",
                                        "display": "OAuth",
                                    }
                                ],
                                "text": "OAuth2 using SMART on FHIR",
                            }
                        ],
                    },
                    "resource": [
                        {
                            "type": "Patient",
                            "profile": "http://hl7.org/fhir/StructureDefinition/Patient",
                            "interaction": [
                                {"code": "read"},
                                {"code": "vread"},
                                {"code": "update"},
                                {"code": "delete"},
                                {"code": "create"},
                                {"code": "search-type"},
                            ],
                            "searchParam": [
                                {
                                    "name": "identifier",
                                    "type": "token",
                                    "documentation": "Patient identifier",
                                },
                                {
                                    "name": "name",
                                    "type": "string",
                                    "documentation": "Patient name",
                                },
                                {
                                    "name": "birth-date",
                                    "type": "date",
                                    "documentation": "Patient birth date",
                                },
                                {
                                    "name": "gender",
                                    "type": "token",
                                    "documentation": "Patient gender",
                                },
                            ],
                        },
                        {
                            "type": "Encounter",
                            "profile": "http://hl7.org/fhir/StructureDefinition/Encounter",
                            "interaction": [
                                {"code": "read"},
                                {"code": "vread"},
                                {"code": "update"},
                                {"code": "delete"},
                                {"code": "create"},
                                {"code": "search-type"},
                            ],
                        },
                        {
                            "type": "Observation",
                            "profile": "http://hl7.org/fhir/StructureDefinition/Observation",
                            "interaction": [
                                {"code": "read"},
                                {"code": "vread"},
                                {"code": "update"},
                                {"code": "delete"},
                                {"code": "create"},
                                {"code": "search-type"},
                            ],
                        },
                    ],
                }
            ],
        }


fhir_app = FastAPI(
    title="HMS FHIR R4 Server",
    description="FHIR R4 compliant server for Hospital Management System",
    version="1.0.0",
    docs_url="/fhir/docs",
    redoc_url="/fhir/redoc",
)
fhir_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
fhir_server: Optional[FHIRServer] = None


async def get_fhir_server() -> FHIRServer:
    global fhir_server
    if fhir_server is None:
        from .orchestrator import orchestrator

        fhir_server = FHIRServer(orchestrator)
    return fhir_server


@fhir_app.get("/fhir/metadata")
async def get_conformance_statement(fhir_server: FHIRServer = Depends(get_fhir_server)):
    return await fhir_server.get_conformance_statement()


@fhir_app.post("/fhir/Patient", response_model=Dict)
async def create_patient(
    patient: FHIRPatientModel, fhir_server: FHIRServer = Depends(get_fhir_server)
):
    return await fhir_server.create_patient(patient)


@fhir_app.get("/fhir/Patient/{patient_id}", response_model=Dict)
async def get_patient(
    patient_id: str = Path(..., description="Patient ID"),
    fhir_server: FHIRServer = Depends(get_fhir_server),
):
    return await fhir_server.get_patient(patient_id)


@fhir_app.get("/fhir/Patient", response_model=Dict)
async def search_patients(
    name: Optional[str] = Query(None, description="Patient name"),
    identifier: Optional[str] = Query(None, description="Patient identifier"),
    birth_date: Optional[date] = Query(None, description="Birth date"),
    gender: Optional[str] = Query(None, description="Gender"),
    page: int = Query(1, ge=1, description="Page number"),
    _count: int = Query(50, ge=1, le=1000, description="Items per page"),
    fhir_server: FHIRServer = Depends(get_fhir_server),
):
    search_params = {
        "name": name,
        "identifier": identifier,
        "birth_date": birth_date,
        "gender": gender,
        "page": page,
        "_count": _count,
    }
    return await fhir_server.search_patients(
        **{k: v for k, v in search_params.items() if v is not None}
    )


@fhir_app.post("/fhir/Encounter", response_model=Dict)
async def create_encounter(
    encounter: FHIREncounterModel, fhir_server: FHIRServer = Depends(get_fhir_server)
):
    return await fhir_server.create_encounter(encounter)


@fhir_app.get("/fhir/Encounter/{encounter_id}", response_model=Dict)
async def get_encounter(
    encounter_id: str = Path(..., description="Encounter ID"),
    fhir_server: FHIRServer = Depends(get_fhir_server),
):
    pass


@fhir_app.get("/fhir/Encounter", response_model=Dict)
async def search_encounters(
    patient: Optional[str] = Query(None, description="Patient reference"),
    status: Optional[str] = Query(None, description="Encounter status"),
    date: Optional[str] = Query(None, description="Encounter date"),
    page: int = Query(1, ge=1, description="Page number"),
    _count: int = Query(50, ge=1, le=1000, description="Items per page"),
    fhir_server: FHIRServer = Depends(get_fhir_server),
):
    pass


@fhir_app.get("/fhir")
async def fhir_root():
    return {
        "resourceType": "Bundle",
        "id": str(uuid.uuid4()),
        "type": "collection",
        "link": [{"relation": "self", "url": "/fhir"}],
        "entry": [
            {
                "fullUrl": "/fhir/metadata",
                "resource": {
                    "resourceType": "OperationOutcome",
                    "text": {
                        "status": "generated",
                        "div": "<div>FHIR Server is operational</div>",
                    },
                },
            }
        ],
    }


if __name__ == "__main__":
    import os

    import uvicorn

    uvicorn.run(fhir_app, host="0.0.0.0", port=8080)
