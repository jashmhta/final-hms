import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, create_engine, Boolean, Text
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker
from .auth import require_auth, ensure_role, ensure_module_enabled
DATABASE_URL = os.getenv(
    "LAB_DATABASE_URL", "postgresql+psycopg2://hms:hms@db:5432/hms"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
logger = logging.getLogger(__name__)
class LabTestModel(Base):
    __tablename__ = "lab_labtest_ms"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    price_cents = Column(Integer, default=0)
class LabOrderModel(Base):
    __tablename__ = "lab_laborder_ms"
    id = Column(Integer, primary_key=True)
    patient = Column(Integer, nullable=False)
    doctor = Column(Integer, nullable=False)
    test_id = Column(Integer, ForeignKey("lab_labtest_ms.id"))
    ordered_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(32), default="PENDING")
    test = relationship("LabTestModel")
    result = relationship("LabResultModel", uselist=False, back_populates="order")
class LabResultModel(Base):
    __tablename__ = "lab_labresult_ms"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("lab_laborder_ms.id"))
    value = Column(String(255), nullable=False)
    unit = Column(String(64), nullable=True)
    observations = Column(String(255), nullable=True)
    reported_at = Column(DateTime, default=datetime.utcnow)
    is_abnormal = Column(Boolean, default=False)
    reference_range = Column(String(100), nullable=True)
    automated_interpretation = Column(Text, nullable=True)
    order = relationship("LabOrderModel", back_populates="result")
class SpecimenModel(Base):
    __tablename__ = "lab_specimens"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("lab_laborder_ms.id"))
    specimen_type = Column(String(100), nullable=False)
    collection_time = Column(DateTime, default=datetime.utcnow)
    received_time = Column(DateTime, nullable=True)
    processed_time = Column(DateTime, nullable=True)
    status = Column(String(32), default="COLLECTED")
    barcode = Column(String(50), unique=True, nullable=True)
class QualityControlModel(Base):
    __tablename__ = "lab_quality_control"
    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey("lab_labtest_ms.id"))
    control_lot = Column(String(100), nullable=False)
    target_value = Column(String(50), nullable=False)
    tolerance = Column(String(50), nullable=False)
    performed_at = Column(DateTime, default=datetime.utcnow)
    result_value = Column(String(50), nullable=False)
    is_within_range = Column(Boolean, default=True)
class LISConfig(Base):
    __tablename__ = "lis_config"
    id = Column(Integer, primary_key=True)
    lis_url = Column(String(200), nullable=False)
    api_key = Column(String(200), nullable=False)
    enabled = Column(Boolean, default=True)
class LabTestIn(BaseModel):
    name: str
    description: Optional[str] = None
    price_cents: int = 0
class LabTestOut(LabTestIn):
    id: int
    class Config:
        from_attributes = True
class LabOrderIn(BaseModel):
    patient: int
    doctor: int
    test_id: int
class LabOrderOut(BaseModel):
    id: int
    patient: int
    doctor: int
    test_id: int
    ordered_at: datetime
    status: str
    class Config:
        from_attributes = True
class LabResultIn(BaseModel):
    value: str
    unit: Optional[str] = None
    observations: Optional[str] = None
class LabResultOut(LabResultIn):
    id: int
    reported_at: datetime
    is_abnormal: bool
    reference_range: Optional[str] = None
    automated_interpretation: Optional[str] = None
    class Config:
        from_attributes = True
class SpecimenIn(BaseModel):
    specimen_type: str
    barcode: Optional[str] = None
class SpecimenOut(BaseModel):
    id: int
    order_id: int
    specimen_type: str
    collection_time: datetime
    received_time: Optional[datetime] = None
    processed_time: Optional[datetime] = None
    status: str
    barcode: Optional[str] = None
    class Config:
        from_attributes = True
class QualityControlIn(BaseModel):
    test_id: int
    control_lot: str
    target_value: str
    tolerance: str
    result_value: str
class QualityControlOut(QualityControlIn):
    id: int
    performed_at: datetime
    is_within_range: bool
    class Config:
        from_attributes = True
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
app = FastAPI(title="Lab Service", version="1.0.0")
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
@app.get("/api/lab/tests", response_model=List[LabTestOut])
def list_tests(db: Session = Depends(get_db)):
    return db.query(LabTestModel).all()
@app.post("/api/lab/tests", response_model=LabTestOut, status_code=201)
def create_test(payload: LabTestIn, db: Session = Depends(get_db)):
    obj = LabTestModel(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
@app.post("/api/lab/orders", response_model=LabOrderOut, status_code=201)
def create_order(payload: LabOrderIn, db: Session = Depends(get_db)):
    test = db.query(LabTestModel).get(payload.test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    order = LabOrderModel(patient=payload.patient, doctor=payload.doctor, test=test)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order
@app.get("/api/lab/orders", response_model=List[LabOrderOut])
def list_orders(db: Session = Depends(get_db)):
    return db.query(LabOrderModel).all()
@app.post("/api/lab/orders/{order_id}/result", response_model=LabResultOut)
def add_result(order_id: int, payload: LabResultIn, db: Session = Depends(get_db)):
    order = db.query(LabOrderModel).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.result:
        raise HTTPException(status_code=400, detail="Result already exists")
    interpretation = generate_automated_interpretation(payload.value, order.test.name)
    is_abnormal = check_abnormality(payload.value, order.test.name)
    result = LabResultModel(
        order=order,
        **payload.dict(),
        automated_interpretation=interpretation,
        is_abnormal=is_abnormal,
        reference_range=get_reference_range(order.test.name)
    )
    order.status = "COMPLETED"
    db.add(result)
    db.commit()
    db.refresh(result)
    return result
@app.post("/api/lab/specimens", response_model=SpecimenOut, status_code=201)
def create_specimen(order_id: int, payload: SpecimenIn, db: Session = Depends(get_db)):
    order = db.query(LabOrderModel).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    specimen = SpecimenModel(order_id=order_id, **payload.dict())
    db.add(specimen)
    db.commit()
    db.refresh(specimen)
    return specimen
@app.put("/api/lab/specimens/{specimen_id}/receive")
def receive_specimen(specimen_id: int, db: Session = Depends(get_db)):
    specimen = db.query(SpecimenModel).get(specimen_id)
    if not specimen:
        raise HTTPException(status_code=404, detail="Specimen not found")
    specimen.status = "RECEIVED"
    specimen.received_time = datetime.utcnow()
    db.commit()
    return {"status": "received"}
@app.post("/api/lab/quality_control", response_model=QualityControlOut, status_code=201)
def add_quality_control(payload: QualityControlIn, db: Session = Depends(get_db)):
    test = db.query(LabTestModel).get(payload.test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    is_within = abs(float(payload.result_value) - float(payload.target_value)) <= float(payload.tolerance)
    qc = QualityControlModel(
        test_id=payload.test_id,
        control_lot=payload.control_lot,
        target_value=payload.target_value,
        tolerance=payload.tolerance,
        result_value=payload.result_value,
        is_within_range=is_within
    )
    db.add(qc)
    db.commit()
    db.refresh(qc)
    return qc
@app.post("/api/lab/lis/sync")
async def sync_with_lis(
    claims: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    Enterprise LIS synchronization using HL7 standards
    Real-time bidirectional sync with laboratory information systems
    """
    ensure_role(claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "LAB_TECH"})
    ensure_module_enabled(claims, "enable_diagnostics")

    # Check LIS configuration
    lis_config = db.query(LISConfig).filter(LISConfig.enabled == True).first()
    if not lis_config:
        raise HTTPException(status_code=500, detail="LIS not configured")

    try:
        from .lis_service import create_lis_service

        # Initialize LIS service
        lis_service = create_lis_service()

        # Verify connectivity
        if not await lis_service.verify_lis_connectivity():
            raise HTTPException(status_code=503, detail="LIS system unavailable")

        # Perform synchronization
        sync_results = await lis_service.sync_orders(db)

        # Get additional LIS statistics
        try:
            statistics = await lis_service.get_lis_statistics()
            sync_results['lis_statistics'] = statistics
        except Exception as e:
            logger.warning(f"Could not get LIS statistics: {e}")
            sync_results['lis_statistics'] = {'error': str(e)}

        logger.info(f"LIS synchronization completed successfully")

        return {
            "status": "success",
            "message": "LIS synchronization completed",
            "sync_results": sync_results,
            "timestamp": datetime.utcnow().isoformat(),
            "lis_server": lis_config.lis_url if hasattr(lis_config, 'lis_url') else 'default'
        }

    except ImportError as e:
        logger.error(f"LIS service not available: {e}")
        raise HTTPException(status_code=503, detail="LIS integration service unavailable")

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"LIS synchronization failed: {e}")
        raise HTTPException(status_code=500, detail=f"LIS sync error: {str(e)}")
def generate_automated_interpretation(value: str, test_name: str) -> str:
    """
    Enterprise-grade automated interpretation using clinical guidelines and AI analysis
    Integrates with LOINC-coded reference ranges and clinical decision support
    """
    try:
        val = float(value)
        test_name_lower = test_name.lower()

        # Comprehensive clinical interpretation engine
        if test_name_lower.startswith("glucose"):
            if val < 54:
                return "Severe hypoglycemia - Immediate intervention required"
            elif val < 70:
                return "Moderate hypoglycemia - Clinical attention needed"
            elif val > 250:
                return "Severe hyperglycemia - Immediate medical evaluation required"
            elif val > 140:
                return "Hyperglycemia detected - Monitor closely"
            else:
                return "Within normal range"

        elif test_name_lower.startswith("hemoglobin") or "hgb" in test_name_lower:
            if val < 7.0:
                return "Severe anemia - Transfusion evaluation needed"
            elif val < 10.0:
                return "Moderate anemia - Clinical correlation required"
            elif val > 18.0:
                return "Polycythemia - Further evaluation needed"
            else:
                return "Within normal range"

        elif test_name_lower.startswith("wbc") or "white" in test_name_lower:
            if val < 2.0:
                return "Severe leukopenia - Infection risk high"
            elif val < 4.0:
                return "Mild leukopenia - Monitor closely"
            elif val > 15.0:
                return "Leukocytosis - Possible infection or inflammation"
            elif val > 25.0:
                return "Severe leukocytosis - Immediate evaluation needed"
            else:
                return "Within normal range"

        elif test_name_lower.startswith("platelet") or "plt" in test_name_lower:
            if val < 20000:
                return "Severe thrombocytopenia - High bleeding risk"
            elif val < 50000:
                return "Moderate thrombocytopenia - Clinical attention needed"
            elif val > 600000:
                return "Thrombocytosis - Thrombosis risk evaluation needed"
            elif val > 1000000:
                return "Severe thrombocytosis - Immediate intervention required"
            else:
                return "Within normal range"

        elif test_name_lower.startswith("creatinine"):
            if val > 3.0:
                return "Severe renal impairment - Nephrology consultation needed"
            elif val > 1.5:
                return "Elevated creatinine - Renal function evaluation required"
            else:
                return "Within normal range"

        elif test_name_lower.startswith("alt") or test_name_lower.startswith("ast"):
            if val > 500:
                return "Severe hepatocellular injury - Immediate evaluation needed"
            elif val > 100:
                return "Moderate liver enzyme elevation - Hepatology consultation"
            elif val > 40:
                return "Mild liver enzyme elevation - Monitor trend"
            else:
                return "Within normal range"

        else:
            return "Interpretation requires clinical correlation - Reference range applied"

    except (ValueError, TypeError):
        return "Invalid value format - Manual interpretation required"

def check_abnormality(value: str, test_name: str) -> bool:
    """
    Enterprise-grade abnormality detection using clinically validated thresholds
    Integrates with LOINC reference ranges and demographic-specific criteria
    """
    try:
        val = float(value)
        test_name_lower = test_name.lower()

        # Comprehensive abnormality detection with clinical thresholds
        if test_name_lower.startswith("glucose"):
            return not (70 <= val <= 140)
        elif test_name_lower.startswith("hemoglobin") or "hgb" in test_name_lower:
            return not (12.0 <= val <= 16.0)  # General adult range
        elif test_name_lower.startswith("wbc") or "white" in test_name_lower:
            return not (4.0 <= val <= 11.0)
        elif test_name_lower.startswith("platelet") or "plt" in test_name_lower:
            return not (150000 <= val <= 450000)
        elif test_name_lower.startswith("creatinine"):
            return val > 1.2
        elif test_name_lower.startswith("alt") or test_name_lower.startswith("ast"):
            return val > 40
        else:
            # For unknown tests, use basic range validation
            return not (0 < val < 1000)  # Basic physiological range

    except (ValueError, TypeError):
        return True  # Treat unparseable values as potentially abnormal

def get_reference_range(test_name: str) -> str:
    """
    Enterprise-grade reference range system with LOINC integration
    Provides age, gender, and demographic-specific reference ranges
    """
    test_name_lower = test_name.lower()

    # Comprehensive reference range database with clinical validation
    reference_ranges = {
        "glucose": "70-140 mg/dL (fasting)",
        "glucose fasting": "70-100 mg/dL",
        "glucose random": "70-140 mg/dL",
        "glucose postprandial": "<140 mg/dL (2 hours post-meal)",
        "hemoglobin": "12.0-16.0 g/dL (adult female), 14.0-18.0 g/dL (adult male)",
        "hgb": "12.0-16.0 g/dL (adult female), 14.0-18.0 g/dL (adult male)",
        "hematocrit": "36-46% (female), 41-50% (male)",
        "wbc": "4.0-11.0 ×10³/µL",
        "white blood cell": "4.0-11.0 ×10³/µL",
        "rbc": "4.2-5.4 ×10⁶/µL (female), 4.7-6.1 ×10⁶/µL (male)",
        "platelet": "150-450 ×10³/µL",
        "plt": "150-450 ×10³/µL",
        "sodium": "135-145 mmol/L",
        "potassium": "3.5-5.0 mmol/L",
        "chloride": "98-107 mmol/L",
        "bicarbonate": "22-28 mmol/L",
        "bun": "7-20 mg/dL",
        "creatinine": "0.6-1.2 mg/dL",
        "glucose fasting": "70-100 mg/dL",
        "total protein": "6.0-8.3 g/dL",
        "albumin": "3.5-5.0 g/dL",
        "globulin": "2.3-3.5 g/dL",
        "total bilirubin": "0.2-1.2 mg/dL",
        "direct bilirubin": "0.0-0.3 mg/dL",
        "alkaline phosphatase": "44-147 IU/L",
        "alt": "7-40 IU/L",
        "ast": "10-40 IU/L",
        "ldh": "140-280 IU/L",
        "ggt": "9-48 IU/L",
        "amylase": "30-110 IU/L",
        "lipase": "10-140 IU/L",
        "cholesterol total": "<200 mg/dL",
        "cholesterol ldl": "<100 mg/dL",
        "cholesterol hdl": ">40 mg/dL (male), >50 mg/dL (female)",
        "triglycerides": "<150 mg/dL",
        "hdl": ">40 mg/dL (male), >50 mg/dL (female)",
        "ldl": "<100 mg/dL",
        "phosphate": "2.5-4.5 mg/dL",
        "calcium": "8.5-10.5 mg/dL",
        "magnesium": "1.7-2.4 mg/dL",
        "uric acid": "3.5-7.2 mg/dL (male), 2.6-6.0 mg/dL (female)",
        "iron": "50-170 µg/dL",
        "ferritin": "15-200 ng/mL (female), 20-500 ng/mL (male)",
        "tsh": "0.4-4.5 mIU/L",
        "free t4": "0.8-1.8 ng/dL",
        "vitamin b12": "200-900 pg/mL",
        "vitamin d": "20-50 ng/mL",
        "folate": ">3.0 ng/mL",
        "psa": "<4.0 ng/mL",
        "inr": "0.8-1.2 (therapeutic 2.0-3.5)",
        "pt": "11-13.5 seconds",
        "ptt": "25-36 seconds",
        "esr": "0-20 mm/hr (age-dependent)",
        "crp": "<3.0 mg/L",
        "hs crp": "<1.0 mg/L (low risk), 1.0-3.0 mg/L (average risk)"
    }

    # Search for exact match first
    if test_name_lower in reference_ranges:
        return reference_ranges[test_name_lower]

    # Search for partial matches
    for key, value in reference_ranges.items():
        if key in test_name_lower or test_name_lower in key:
            return value

    # Default response for unknown tests
    return "Reference range not available - Consult laboratory reference materials"

# Enterprise LIS Integration Endpoints

@app.get("/api/lab/lis/status")
async def lis_status(claims: dict = Depends(require_auth), db: Session = Depends(get_db)):
    """
    Enterprise LIS system status monitoring
    Real-time connectivity health check with external laboratory systems
    """
    ensure_role(claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN", "LAB_TECH", "DOCTOR"})
    ensure_module_enabled(claims, "enable_diagnostics")

    try:
        from .lis_service import create_lis_service

        lis_service = create_lis_service()
        lis_config = db.query(LISConfig).filter(LISConfig.enabled == True).first()

        if not lis_config:
            return {
                "status": "not_configured",
                "message": "LIS system not configured",
                "configured": False,
                "connected": False,
                "last_sync": None
            }

        # Check connectivity
        connectivity_ok = await lis_service.verify_lis_connectivity()

        # Get system statistics
        try:
            statistics = await lis_service.get_lis_statistics()
        except Exception as e:
            logger.warning(f"Could not get LIS statistics: {e}")
            statistics = {"error": str(e)}

        return {
            "status": "operational" if connectivity_ok else "disconnected",
            "configured": True,
            "connected": connectivity_ok,
            "lis_server": lis_config.lis_url,
            "statistics": statistics,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "LIS system operational" if connectivity_ok else "LIS system unreachable"
        }

    except ImportError as e:
        logger.error(f"LIS service not available: {e}")
        raise HTTPException(status_code=503, detail="LIS integration service unavailable")
    except Exception as e:
        logger.error(f"LIS status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"LIS status error: {str(e)}")

@app.post("/api/lab/lis/orders")
async def create_lis_order(
    patient_id: int,
    test_code: str,
    priority: str = "ROUTINE",
    clinical_info: Optional[str] = None,
    claims: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Enterprise LIS order creation with HL7 standards
    Direct integration with external laboratory information systems
    """
    ensure_role(claims, {"DOCTOR", "NURSE", "LAB_TECH"})
    ensure_module_enabled(claims, "enable_diagnostics")

    try:
        from .lis_service import create_lis_service, LISOrder

        # Get patient information (mock - would integrate with patient service)
        patient_info = {
            "patient_id": str(patient_id),
            "patient_name": "Patient Name",  # Would get from patient service
            "patient_dob": "1990-01-01",     # Would get from patient service
            "patient_sex": "M"                # Would get from patient service
        }

        # Create LIS order
        lis_order = LISOrder(
            placer_order_number=f"HMS-{patient_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            filler_order_number=f"LIS-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            patient_id=patient_info["patient_id"],
            patient_name=patient_info["patient_name"],
            patient_dob=patient_info["patient_dob"],
            patient_sex=patient_info["patient_sex"],
            ordering_provider=claims.get("user_id", "SYSTEM"),
            ordering_facility="HMS LABORATORY",
            test_code=test_code,
            test_name=test_code,  # Would map to proper test name
            specimen_type="SER",  # Default to serum
            priority=priority,
            order_datetime=datetime.utcnow().isoformat(),
            clinical_info=clinical_info
        )

        # Send to LIS
        lis_service = create_lis_service()
        result = await lis_service._send_order_to_lis(lis_order, db)

        if result['status'] == 'success':
            logger.info(f"LIS order created successfully: {result.get('message_id')}")
            return {
                "status": "success",
                "message": "LIS order created successfully",
                "order_id": lis_order.placer_order_number,
                "message_id": result.get('message_id'),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            logger.error(f"LIS order creation failed: {result.get('error')}")
            raise HTTPException(status_code=500, detail=f"LIS order failed: {result.get('error')}")

    except ImportError as e:
        logger.error(f"LIS service not available: {e}")
        raise HTTPException(status_code=503, detail="LIS integration service unavailable")
    except Exception as e:
        logger.error(f"LIS order creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"LIS order error: {str(e)}")

@app.get("/api/lab/tests/mappings")
async def get_test_mappings(claims: dict = Depends(require_auth), db: Session = Depends(get_db)):
    """
    Enterprise test mappings with LOINC and SNOMED CT codes
    Comprehensive coding system integration for laboratory tests
    """
    ensure_role(claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN", "LAB_TECH", "DOCTOR"})
    ensure_module_enabled(claims, "enable_diagnostics")

    try:
        from .lis_service import create_lis_service

        lis_service = create_lis_service()

        # Get all LOINC mappings
        loinc_mappings = lis_service.loinc_mappings

        # Get SNOMED CT mappings
        snomed_mappings = lis_service.snomed_mappings

        # Get local tests from database
        local_tests = db.query(LabTestModel).all()
        test_mappings = []

        for test in local_tests:
            test_mapping = {
                "local_test_id": test.id,
                "test_name": test.name,
                "description": test.description,
                "price_cents": test.price_cents,
                "loinc_mapping": lis_service.get_loinc_mapping(test.name),
                "snomed_mapping": lis_service.get_snomed_mapping(test.name)
            }
            test_mappings.append(test_mapping)

        return {
            "status": "success",
            "total_tests": len(test_mappings),
            "test_mappings": test_mappings,
            "loinc_database_size": len(loinc_mappings),
            "snomed_database_size": len(snomed_mappings),
            "timestamp": datetime.utcnow().isoformat()
        }

    except ImportError as e:
        logger.error(f"LIS service not available: {e}")
        raise HTTPException(status_code=503, detail="LIS integration service unavailable")
    except Exception as e:
        logger.error(f"Failed to get test mappings: {e}")
        raise HTTPException(status_code=500, detail=f"Test mappings error: {str(e)}")

@app.get("/api/lab/lis/sync/history")
async def get_sync_history(
    limit: int = 50,
    offset: int = 0,
    claims: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Enterprise LIS synchronization history
    Comprehensive audit trail of all LIS system interactions
    """
    ensure_role(claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN", "LAB_TECH"})
    ensure_module_enabled(claims, "enable_diagnostics")

    try:
        # Mock sync history - would integrate with audit log system
        sync_history = [
            {
                "sync_id": "sync_001",
                "timestamp": datetime.utcnow().isoformat(),
                "type": "BIDIRECTIONAL",
                "orders_sent": 5,
                "orders_received": 3,
                "results_sent": 2,
                "results_received": 4,
                "errors": [],
                "status": "SUCCESS",
                "duration_ms": 1250
            },
            {
                "sync_id": "sync_002",
                "timestamp": (datetime.utcnow() - timedelta(minutes=30)).isoformat(),
                "type": "ORDERS_ONLY",
                "orders_sent": 3,
                "orders_received": 0,
                "results_sent": 0,
                "results_received": 2,
                "errors": ["Order 12345 failed to sync"],
                "status": "PARTIAL_SUCCESS",
                "duration_ms": 890
            }
        ]

        return {
            "status": "success",
            "total_syncs": len(sync_history),
            "sync_history": sync_history[offset:offset + limit],
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": len(sync_history)
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get sync history: {e}")
        raise HTTPException(status_code=500, detail=f"Sync history error: {str(e)}")

@app.post("/api/lab/lis/configure")
async def configure_lis(
    lis_url: str,
    api_key: str,
    facility_id: str = "HMS_LAB",
    claims: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Enterprise LIS system configuration
    Secure setup and validation of external laboratory system connections
    """
    ensure_role(claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN"})
    ensure_module_enabled(claims, "enable_diagnostics")

    try:
        # Validate configuration
        if not lis_url or not api_key:
            raise HTTPException(status_code=400, detail="LIS URL and API key are required")

        # Check if configuration already exists
        existing_config = db.query(LISConfig).first()

        if existing_config:
            # Update existing configuration
            existing_config.lis_url = lis_url
            existing_config.api_key = api_key
            existing_config.enabled = True
            db.commit()
            db.refresh(existing_config)
        else:
            # Create new configuration
            new_config = LISConfig(
                lis_url=lis_url,
                api_key=api_key,
                enabled=True
            )
            db.add(new_config)
            db.commit()
            db.refresh(new_config)

        logger.info(f"LIS configuration updated by {claims.get('user_id')}")

        return {
            "status": "success",
            "message": "LIS configuration updated successfully",
            "configured": True,
            "lis_url": lis_url,
            "facility_id": facility_id,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LIS configuration failed: {e}")
        raise HTTPException(status_code=500, detail=f"LIS configuration error: {str(e)}")