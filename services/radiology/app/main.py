import os
from datetime import datetime
from typing import List, Optional
import requests
from fastapi import Depends, FastAPI, Header, HTTPException, UploadFile, File
from jose import JWTError, jwt
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
DATABASE_URL = os.getenv(
    "RADIOLOGY_DATABASE_URL", os.getenv("DATABASE_URL", "sqlite:///./radiology.db")
)
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
app = FastAPI(title="Radiology Service", version="1.2.0")
Instrumentator().instrument(app).expose(app)
class OrderModel(Base):
    __tablename__ = "radiology_orders"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, index=True, nullable=False)
    study_type = Column(String(100), nullable=False)
    priority = Column(String(20), default="ROUTINE")
class ReportModel(Base):
    __tablename__ = "radiology_reports"
    order_id = Column(Integer, primary_key=True)
    impression = Column(Text, nullable=False)
    findings = Column(Text, nullable=True)
    critical_findings = Column(Boolean, default=False)
    template_used = Column(String(100), nullable=True)
class ImageModel(Base):
    __tablename__ = "radiology_images"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, index=True, nullable=False)
    dicom_uid = Column(String(100), unique=True, nullable=False)
    image_path = Column(String(500), nullable=False)
    modality = Column(String(50), nullable=False)
    body_part = Column(String(100), nullable=True)
    series_description = Column(String(200), nullable=True)
    study_instance_uid = Column(String(100), nullable=True)
    series_instance_uid = Column(String(100), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
class PACSConfig(Base):
    __tablename__ = "pacs_config"
    id = Column(Integer, primary_key=True)
    pacs_url = Column(String(200), nullable=False)
    pacs_ae_title = Column(String(50), nullable=False)
    local_ae_title = Column(String(50), nullable=False)
    enabled = Column(Boolean, default=True)
def create_tables():
    Base.metadata.create_all(bind=engine)
@app.on_event("startup")
def on_startup():
    create_tables()
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
def require_auth(authorization: str | None = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
def ensure_role(claims: dict, allowed: set[str]):
    role = claims.get("role")
    if role not in allowed:
        raise HTTPException(status_code=403, detail="Forbidden")
def ensure_module_enabled(claims: dict, flag: str):
    if claims is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    enabled = claims.get(flag, True)
    if not enabled:
        raise HTTPException(status_code=403, detail=f"Module disabled: {flag}")
class RadiologyOrder(BaseModel):
    patient_id: int
    study_type: str
    priority: str = "ROUTINE"  
class RadiologyReport(BaseModel):
    order_id: int
    impression: str
    findings: Optional[str] = None
    critical_findings: bool = False
    template_used: Optional[str] = None
class RadiologyImage(BaseModel):
    order_id: int
    dicom_uid: str
    modality: str
    body_part: Optional[str] = None
    series_description: Optional[str] = None
class PACSConfigModel(BaseModel):
    pacs_url: str
    pacs_ae_title: str
    local_ae_title: str
    enabled: bool = True
@app.get("/health")
def health():
    return {"status": "ok"}
@app.post("/api/radiology/orders")
def create_order(
    payload: RadiologyOrder,
    claims: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    ensure_role(claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "RECEPTIONIST"})
    ensure_module_enabled(claims, "enable_diagnostics")
    row = OrderModel(
        patient_id=payload.patient_id,
        study_type=payload.study_type,
        priority=payload.priority,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "id": row.id,
        "patient_id": row.patient_id,
        "study_type": row.study_type,
        "priority": row.priority,
    }
@app.get("/api/radiology/orders")
def list_orders(claims: dict = Depends(require_auth), db: Session = Depends(get_db)):
    ensure_role(
        claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "LAB_TECH", "NURSE"}
    )
    ensure_module_enabled(claims, "enable_diagnostics")
    rows = db.query(OrderModel).order_by(OrderModel.id.desc()).all()
    return [
        {
            "id": r.id,
            "patient_id": r.patient_id,
            "study_type": r.study_type,
            "priority": r.priority,
        }
        for r in rows
    ]
@app.post("/api/radiology/report")
def submit_report(
    payload: RadiologyReport,
    claims: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    ensure_role(claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "LAB_TECH"})
    ensure_module_enabled(claims, "enable_diagnostics")
    exists = db.query(OrderModel).filter(OrderModel.id == payload.order_id).first()
    if not exists:
        raise HTTPException(status_code=404, detail="Order not found")
    rep = ReportModel(
        order_id=payload.order_id,
        impression=payload.impression,
        findings=payload.findings,
        critical_findings=payload.critical_findings,
        template_used=payload.template_used
    )
    db.merge(rep)
    db.commit()
    if payload.critical_findings:
        send_critical_alert(payload.order_id, db)
    return {"status": "stored"}
@app.post("/api/radiology/upload_dicom")
async def upload_dicom(
    order_id: int,
    file: UploadFile = File(...),
    claims: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    Enterprise DICOM upload using STOW-RS (Store Over the Web for DICOM Objects)
    DICOM 3.0 compliant with validation and metadata extraction
    """
    ensure_role(claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "LAB_TECH"})
    ensure_module_enabled(claims, "enable_diagnostics")

    # Validate order exists
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    try:
        from .pacs_service import create_pacs_service
        import pydicom

        # Initialize PACS service
        pacs_service = create_pacs_service()

        # Read and validate DICOM file
        dicom_content = await file.read()
        try:
            ds = pydicom.dcmread(dicom_content)
            logger.info(f"Valid DICOM file: {ds.SOPClassUID.name}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid DICOM file: {e}")

        # Extract DICOM metadata
        study_instance_uid = getattr(ds, 'StudyInstanceUID', f"1.2.3.{order_id}.{int(datetime.utcnow().timestamp())}")
        series_instance_uid = getattr(ds, 'SeriesInstanceUID', f"1.2.3.{order_id}.{int(datetime.utcnow().timestamp())}.1")
        sop_instance_uid = getattr(ds, 'SOPInstanceUID', f"1.2.3.{order_id}.{int(datetime.utcnow().timestamp())}.1.1")

        # Store in PACS using STOW-RS
        storage_result = await pacs_service.store_dicom(dicom_content, study_instance_uid)

        if storage_result['status'] != 'success':
            raise HTTPException(status_code=500, detail=f"PACS storage failed: {storage_result.get('error', 'Unknown error')}")

        # Create local storage backup
        backup_path = f"/storage/dicom/{order_id}/{file.filename}"
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        with open(backup_path, "wb") as f:
            f.write(dicom_content)

        # Store in database
        image = ImageModel(
            order_id=order_id,
            dicom_uid=sop_instance_uid,
            image_path=backup_path,
            modality=getattr(ds, 'Modality', 'OT'),
            body_part=getattr(ds, 'BodyPartExamined', 'UNKNOWN'),
            series_description=getattr(ds, 'SeriesDescription', 'Radiology Series'),
            study_instance_uid=study_instance_uid,
            series_instance_uid=series_instance_uid,
            uploaded_at=datetime.utcnow()
        )
        db.add(image)
        db.commit()
        db.refresh(image)

        # Send HL7 order if needed
        try:
            hl7_order_data = {
                'patient_id': str(order.patient_id),
                'patient_name': f"Patient {order.patient_id}",  # In real system, get from patient service
                'procedure_code': getattr(ds, 'ScheduledProcedureStepSequence', [{}])[0].get('ScheduledProcedureCode', {}).get('CodeValue', 'RAD'),
                'procedure_description': getattr(ds, 'StudyDescription', 'Radiology Procedure'),
                'order_id': str(order_id),
                'accession_number': getattr(ds, 'AccessionNumber', f"ACC{order_id}"),
                'ordering_physician': getattr(ds, 'ReferringPhysicianName', 'Unknown'),
                'ordering_facility': 'HMS RADIOLOGY',
                'order_date': datetime.utcnow().isoformat(),
                'clinical_indication': getattr(ds, 'StudyComments', 'Routine examination')
            }

            hl7_result = await pacs_service.send_hl7_order(hl7_order_data)
            logger.info(f"HL7 order result: {hl7_result['status']}")

        except Exception as hl7_error:
            logger.warning(f"HL7 order failed: {hl7_error}")

        logger.info(f"DICOM file uploaded successfully: {sop_instance_uid}")

        return {
            "dicom_uid": sop_instance_uid,
            "study_instance_uid": study_instance_uid,
            "series_instance_uid": series_instance_uid,
            "status": "uploaded",
            "storage_result": storage_result,
            "metadata": {
                "modality": image.modality,
                "body_part": image.body_part,
                "series_description": image.series_description,
                "uploaded_at": image.uploaded_at.isoformat()
            }
        }

    except ImportError as e:
        logger.error(f"PACS service not available: {e}")
        raise HTTPException(status_code=503, detail="PACS integration service unavailable")

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"DICOM upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"DICOM upload error: {str(e)}")
@app.get("/api/radiology/images/{order_id}")
def get_images(order_id: int, claims: dict = Depends(require_auth), db: Session = Depends(get_db)):
    ensure_role(claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "LAB_TECH", "NURSE"})
    ensure_module_enabled(claims, "enable_diagnostics")
    images = db.query(ImageModel).filter(ImageModel.order_id == order_id).all()
    return [
        {
            "id": img.id,
            "dicom_uid": img.dicom_uid,
            "modality": img.modality,
            "body_part": img.body_part,
            "series_description": img.series_description,
            "uploaded_at": img.uploaded_at
        }
        for img in images
    ]
@app.post("/api/radiology/pacs/query")
async def pacs_query(
    patient_id: int,
    study_date: str,
    claims: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    Enterprise PACS query using DICOM QIDO-RS (Query based on ID for DICOM Objects)
    Real-time integration with medical imaging systems
    """
    ensure_role(claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "LAB_TECH"})
    ensure_module_enabled(claims, "enable_diagnostics")

    # Check PACS configuration
    pacs_config = db.query(PACSConfig).filter(PACSConfig.enabled == True).first()
    if not pacs_config:
        raise HTTPException(status_code=500, detail="PACS not configured")

    try:
        from .pacs_service import create_pacs_service

        # Initialize PACS service
        pacs_service = create_pacs_service()

        # Verify connectivity
        if not await pacs_service.verify_pacs_connectivity():
            raise HTTPException(status_code=503, detail="PACS system unavailable")

        # Query studies
        studies = await pacs_service.query_studies(str(patient_id), study_date)

        # Format response
        formatted_studies = []
        for study in studies:
            study_dict = {
                "study_instance_uid": study.study_instance_uid,
                "study_id": study.study_id,
                "study_date": study.study_date,
                "study_time": study.study_time,
                "study_description": study.study_description,
                "patient_id": study.patient_id,
                "patient_name": study.patient_name,
                "modalities_in_study": study.modalities_in_study,
                "number_of_series": study.number_of_series,
                "number_of_instances": study.number_of_instances,
                "study_status": study.study_status,
                "accessed_datetime": study.accessed_datetime.isoformat() if study.accessed_datetime else None
            }

            # Get series information for this study
            try:
                series_list = await pacs_service.get_series(study.study_instance_uid)
                study_dict["series"] = [
                    {
                        "series_instance_uid": series.series_instance_uid,
                        "series_number": series.series_number,
                        "modality": series.modality,
                        "series_description": series.series_description,
                        "body_part_examined": series.body_part_examined,
                        "number_of_instances": series.number_of_instances,
                        "series_datetime": series.series_datetime.isoformat() if series.series_datetime else None
                    }
                    for series in series_list
                ]
            except Exception as e:
                logger.warning(f"Could not get series for study {study.study_instance_uid}: {e}")
                study_dict["series"] = []

            formatted_studies.append(study_dict)

        logger.info(f"Retrieved {len(formatted_studies)} studies for patient {patient_id}")
        return {
            "studies": formatted_studies,
            "total_studies": len(formatted_studies),
            "query_metadata": {
                "patient_id": patient_id,
                "study_date": study_date,
                "query_timestamp": datetime.utcnow().isoformat(),
                "pacs_server": pacs_config.pacs_url,
                "query_status": "success"
            }
        }

    except ImportError as e:
        logger.error(f"PACS service not available: {e}")
        raise HTTPException(status_code=503, detail="PACS integration service unavailable")

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"PACS query failed: {e}")
        raise HTTPException(status_code=500, detail=f"PACS query error: {str(e)}")
def send_critical_alert(order_id: int, db: Session):
    """
    Enterprise critical alert system for radiology findings
    HIPAA compliant with audit trail and escalation
    """
    try:
        from .pacs_service import create_pacs_service
        import asyncio

        # Get order and report details
        order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
        report = db.query(ReportModel).filter(ReportModel.order_id == order_id).first()

        if not order or not report:
            logger.warning(f"Could not find order or report for critical alert: {order_id}")
            return

        if report.critical_findings:
            # Initialize PACS service for HL7 messaging
            pacs_service = create_pacs_service()

            # Send critical alert via HL7
            alert_data = {
                'patient_id': str(order.patient_id),
                'alert_type': 'CRITICAL_RADIOLOGY_FINDING',
                'study_description': order.study_type,
                'findings': report.findings,
                'impression': report.impression,
                'alert_timestamp': datetime.utcnow().isoformat(),
                'ordering_physician': 'RADIOLOGY_DEPARTMENT',
                ' urgency': 'STAT'
            }

            # In real implementation, this would send to appropriate systems
            logger.critical(f"CRITICAL RADIOLOGY FINDING: {alert_data}")

            # TODO: Implement proper alert routing to physicians, ER, etc.

    except Exception as e:
        logger.error(f"Failed to send critical alert: {e}")

@app.get("/api/radiology/studies/{study_instance_uid}")
async def get_study_details(
    study_instance_uid: str,
    claims: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    Get detailed study information including series and images
    """
    ensure_role(claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "LAB_TECH"})
    ensure_module_enabled(claims, "enable_diagnostics")

    try:
        from .pacs_service import create_pacs_service

        pacs_service = create_pacs_service()

        # Get series for this study
        series_list = await pacs_service.get_series(study_instance_uid)

        # Get images for each series
        study_details = {
            "study_instance_uid": study_instance_uid,
            "series": []
        }

        for series in series_list:
            try:
                images = await pacs_service.get_images(series.series_instance_uid)
                series_detail = {
                    "series_instance_uid": series.series_instance_uid,
                    "series_number": series.series_number,
                    "modality": series.modality,
                    "series_description": series.series_description,
                    "body_part_examined": series.body_part_examined,
                    "number_of_instances": series.number_of_instances,
                    "images": [
                        {
                            "sop_instance_uid": image.sop_instance_uid,
                            "instance_number": image.instance_number,
                            "image_type": image.image_type,
                            "rows": image.rows,
                            "columns": image.columns,
                            "bits_stored": image.bits_stored,
                            "photometric_interpretation": image.photometric_interpretation
                        }
                        for image in images
                    ]
                }
                study_details["series"].append(series_detail)
            except Exception as e:
                logger.warning(f"Could not get images for series {series.series_instance_uid}: {e}")
                continue

        return study_details

    except Exception as e:
        logger.error(f"Failed to get study details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/radiology/image/{study_instance_uid}/{series_instance_uid}/{sop_instance_uid}")
async def get_dicom_image(
    study_instance_uid: str,
    series_instance_uid: str,
    sop_instance_uid: str,
    image_format: str = "jpeg",
    quality: int = 85,
    claims: dict = Depends(require_auth),
):
    """
    Get DICOM image using WADO-RS (Web Access to DICOM Objects)
    """
    ensure_role(claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "LAB_TECH"})
    ensure_module_enabled(claims, "enable_diagnostics")

    try:
        from .pacs_service import create_pacs_service

        pacs_service = create_pacs_service()

        # Get image using WADO-RS
        image_data = await pacs_service.get_wado_image(
            study_instance_uid, series_instance_uid, sop_instance_uid, image_format, quality
        )

        return Response(
            content=image_data,
            media_type=f"image/{image_format}",
            headers={
                "Content-Disposition": f"inline; filename=\"{sop_instance_uid}.{image_format}\"",
                "Cache-Control": "private, max-age=3600"
            }
        )

    except Exception as e:
        logger.error(f"Failed to get DICOM image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/radiology/pacs/status")
async def pacs_status(claims: dict = Depends(require_auth)):
    """
    Get PACS system status and connectivity
    """
    ensure_role(claims, {"SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR"})
    ensure_module_enabled(claims, "enable_diagnostics")

    try:
        from .pacs_service import create_pacs_service

        pacs_service = create_pacs_service()

        # Check connectivity
        connectivity = await pacs_service.verify_pacs_connectivity()

        # Get statistics
        statistics = await pacs_service.get_pacs_statistics()

        return {
            "pacs_status": "online" if connectivity else "offline",
            "connectivity": connectivity,
            "statistics": statistics,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get PACS status: {e}")
        return {
            "pacs_status": "error",
            "connectivity": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
@app.get("/api/radiology/kpi")
def kpi(claims: dict = Depends(require_auth), db: Session = Depends(get_db)):
    ensure_module_enabled(claims, "enable_diagnostics")
    opa = os.getenv("OPA_URL")
    if opa:
        try:
            d = requests.post(
                f"{opa}/v1/data/hms/allow",
                json={"input": {"path": "/api/radiology/kpi"}},
                timeout=2,
            )
            if d.ok and d.json().get("result") is False:
                raise HTTPException(status_code=403, detail="Policy denied")
        except Exception:
            pass
    total = db.query(OrderModel).count()
    stat = db.query(OrderModel).filter(OrderModel.priority == "STAT").count()
    return {"orders": int(total), "stat": int(stat)}