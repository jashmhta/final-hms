import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple, BinaryIO
from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import base64
import aiofiles
import aiohttp
import asyncpg
import numpy as np
from fastapi import FastAPI, HTTPException, Depends, Request, Response, File, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, validator
from redis.asyncio import redis
from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer, JSON, ForeignKey, LargeBinary, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from PIL import Image
import pydicom
from pydicom.dataset import Dataset
from pydicom.uid import generate_uid, UID
import cv2
from prometheus_fastapi_instrumentator import Instrumentator
from ..orchestrator import IntegrationOrchestrator
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
Base = declarative_base()
class DICOMServiceType(Enum):
    PACS = "PACS"  
    QIDO_RS = "QIDO_RS"  
    STOW_RS = "STOW_RS"  
    WADO_RS = "WADO_RS"  
    WORKLIST = "WORKLIST"  
    MPPS = "MPPS"  
    STORAGE_COMMITMENT = "STORAGE_COMMITMENT"
class ImageModality(Enum):
    CR = "CR"  
    CT = "CT"  
    MR = "MR"  
    US = "US"  
    DX = "DX"  
    MG = "MG"  
    PT = "PT"  
    NM = "NM"  
    XA = "XA"  
    RF = "RF"  
    RTIMAGE = "RTIMAGE"  
    RTDOSE = "RTDOSE"  
    RTSTRUCT = "RTSTRUCT"  
    RTPLAN = "RTPLAN"  
    RTRECORD = "RTRECORD"  
    HC = "HC"  
    DX = "DX"  
    PX = "PX"  
    SR = "SR"  
    OCT = "OCT"  
class ImageCompression(Enum):
    NONE = "NONE"
    JPEG = "JPEG"
    JPEG2000 = "JPEG2000"
    JPEG_LS = "JPEG_LS"
    RLE = "RLE"
    DEFLATE = "DEFLATE"
class ImageQuality(Enum):
    ORIGINAL = "ORIGINAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    THUMBNAIL = "THUMBNAIL"
@dataclass
class DICOMMetadata:
    study_instance_uid: str
    series_instance_uid: str
    sop_instance_uid: str
    study_id: str
    series_number: int
    instance_number: int
    modality: ImageModality
    patient_id: str
    patient_name: str
    patient_birth_date: str
    patient_sex: str
    study_date: str
    study_time: str
    study_description: str
    series_description: str
    body_part_examined: str
    view_position: Optional[str] = None
    photometric_interpretation: str = "MONOCHROME2"
    samples_per_pixel: int = 1
    rows: int = 512
    columns: int = 512
    bits_allocated: int = 16
    bits_stored: int = 16
    high_bit: int = 15
    pixel_representation: int = 0
    window_center: Optional[float] = None
    window_width: Optional[float] = None
    rescale_intercept: float = 0.0
    rescale_slope: float = 1.0
    institution_name: Optional[str] = None
    station_name: Optional[str] = None
    performing_physician_name: Optional[str] = None
    referring_physician_name: Optional[str] = None
@dataclass
class ImageStorageConfig:
    storage_path: str
    compression: ImageCompression = ImageCompression.JPEG2000
    quality: ImageQuality = ImageQuality.HIGH
    enable_versioning: bool = True
    backup_enabled: bool = True
    backup_retention_days: int = 90
    compression_ratio: float = 0.8
    enable_deduplication: bool = True
class DICOMStudy(Base):
    __tablename__ = "dicom_studies"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    study_instance_uid = Column(String(64), unique=True, nullable=False, index=True)
    study_id = Column(String(32), nullable=False, index=True)
    study_date = Column(String(8), nullable=False)
    study_time = Column(String(6), nullable=False)
    study_description = Column(Text)
    patient_id = Column(String(64), nullable=False, index=True)
    patient_name = Column(String(256), nullable=False)
    patient_birth_date = Column(String(8))
    patient_sex = Column(String(1))
    referring_physician_name = Column(String(256))
    institution_name = Column(String(256))
    accession_number = Column(String(32))
    modalities_in_study = Column(JSON)
    number_of_series = Column(Integer, default=0)
    number_of_instances = Column(Integer, default=0)
    study_size_mb = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
class DICOMSeries(Base):
    __tablename__ = "dicom_series"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    series_instance_uid = Column(String(64), unique=True, nullable=False, index=True)
    study_instance_uid = Column(String(64), nullable=False, index=True)
    series_number = Column(Integer, nullable=False)
    modality = Column(String(16), nullable=False, index=True)
    series_description = Column(Text)
    body_part_examined = Column(String(128))
    series_date = Column(String(8))
    series_time = Column(String(6))
    performing_physician_name = Column(String(256))
    protocol_name = Column(String(128))
    station_name = Column(String(128))
    number_of_instances = Column(Integer, default=0)
    series_size_mb = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    study = relationship("DICOMStudy", back_populates="series")
class DICOMInstance(Base):
    __tablename__ = "dicom_instances"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sop_instance_uid = Column(String(64), unique=True, nullable=False, index=True)
    series_instance_uid = Column(String(64), nullable=False, index=True)
    study_instance_uid = Column(String(64), nullable=False, index=True)
    instance_number = Column(Integer, nullable=False)
    sop_class_uid = Column(String(64), nullable=False)
    sop_class_name = Column(String(128))
    rows = Column(Integer, nullable=False)
    columns = Column(Integer, nullable=False)
    bits_allocated = Column(Integer, nullable=False)
    bits_stored = Column(Integer, nullable=False)
    high_bit = Column(Integer, nullable=False)
    photometric_interpretation = Column(String(32))
    pixel_spacing = Column(JSON)
    slice_thickness = Column(Float)
    slice_location = Column(Float)
    image_position = Column(JSON)
    image_orientation = Column(JSON)
    window_center = Column(Float)
    window_width = Column(Float)
    rescale_intercept = Column(Float)
    rescale_slope = Column(Float)
    file_size_mb = Column(Float, nullable=False)
    file_path = Column(String(512), nullable=False)
    thumbnail_path = Column(String(512))
    compressed_path = Column(String(512))
    checksum = Column(String(64), nullable=False)
    is_anonymized = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    series = relationship("DICOMSeries", back_populates="instances")
    study = relationship("DICOMStudy")
class DICOMAssociation(Base):
    __tablename__ = "dicom_associations"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    association_id = Column(String(64), nullable=False)
    calling_aet = Column(String(16), nullable=False)
    called_aet = Column(String(16), nullable=False)
    remote_host = Column(String(64), nullable=False)
    remote_port = Column(Integer, nullable=False)
    association_time = Column(DateTime, default=datetime.utcnow)
    disconnection_time = Column(DateTime)
    status = Column(String(32), default="ACTIVE")
    accepted_contexts = Column(JSON)
    rejected_contexts = Column(JSON)
    total_instances_sent = Column(Integer, default=0)
    total_instances_received = Column(Integer, default=0)
    total_bytes_sent = Column(Float, default=0.0)
    total_bytes_received = Column(Float, default=0.0)
class DICOMQuery(Base):
    __tablename__ = "dicom_queries"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query_id = Column(String(64), nullable=False)
    query_type = Column(String(32), nullable=False)  
    query_parameters = Column(JSON, nullable=False)
    result_count = Column(Integer, default=0)
    execution_time_ms = Column(Float, default=0.0)
    client_ip = Column(String(45), nullable=False)
    user_id = Column(String(100))
    query_time = Column(DateTime, default=datetime.utcnow)
class DICOMAuditLog(Base):
    __tablename__ = "dicom_audit_log"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(64), nullable=False)
    event_time = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String(100))
    patient_id = Column(String(64))
    study_instance_uid = Column(String(64))
    series_instance_uid = Column(String(64))
    sop_instance_uid = Column(String(64))
    action = Column(String(32), nullable=False)  
    outcome = Column(String(16), nullable=False)  
    description = Column(Text)
    client_ip = Column(String(45))
    user_agent = Column(String(256))
DICOMStudy.series = relationship("DICOMSeries", order_by=DICOMSeries.series_number, back_populates="study")
DICOMSeries.instances = relationship("DICOMInstance", order_by=DICOMInstance.instance_number, back_populates="series")
class DICOMIntegration:
    def __init__(self, orchestrator: IntegrationOrchestrator):
        self.orchestrator = orchestrator
        self.redis_client: Optional[redis.Redis] = None
        self.db_url = os.getenv("DICOM_DB_URL", "postgresql+asyncpg://hms:hms@localhost:5432/dicom")
        self.engine = create_async_engine(self.db_url)
        self.SessionLocal = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        self.storage_config = ImageStorageConfig(
            storage_path=os.getenv("DICOM_STORAGE_PATH", "/var/lib/dicom"),
            compression=ImageCompression.JPEG2000,
            quality=ImageQuality.HIGH
        )
        self.aet_title = os.getenv("DICOM_AET", "HMS_PACS")
        self.dicom_port = int(os.getenv("DICOM_PORT", 11112))
        self.max_pdu_size = int(os.getenv("DICOM_MAX_PDU", 16384))
        self._initialize_storage_paths()
        self.metadata_cache = {}
        self.image_cache = {}
    async def initialize(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = redis.from_url(redis_url)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await self._create_storage_directories()
        asyncio.create_task(self._cleanup_task())
        asyncio.create_task(self._indexing_task())
        asyncio.create_task(self._backup_task())
        logger.info("DICOM Integration System initialized successfully")
    def _initialize_storage_paths(self):
        self.storage_paths = {
            'original': Path(self.storage_config.storage_path) / 'original',
            'compressed': Path(self.storage_config.storage_path) / 'compressed',
            'thumbnails': Path(self.storage_config.storage_path) / 'thumbnails',
            'cache': Path(self.storage_config.storage_path) / 'cache',
            'backup': Path(self.storage_config.storage_path) / 'backup'
        }
    async def _create_storage_directories(self):
        for path_name, path_obj in self.storage_paths.items():
            path_obj.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created storage directory: {path_obj}")
    async def store_dicom_image(self, dicom_file: BinaryIO, metadata: Optional[Dict] = None) -> Dict:
        try:
            dicom_data = pydicom.dcmread(dicom_file)
            dicom_metadata = self._extract_metadata(dicom_data)
            file_paths = self._generate_file_paths(dicom_metadata)
            checksum = await self._calculate_checksum(dicom_file)
            if self.storage_config.enable_deduplication:
                existing_instance = await self._find_duplicate(checksum)
                if existing_instance:
                    logger.info(f"Duplicate image found, using existing: {existing_instance.sop_instance_uid}")
                    return existing_instance.dict()
            await self._store_file(dicom_file, file_paths['original'])
            compressed_path = await self._create_compressed_version(dicom_data, file_paths['compressed'])
            thumbnail_path = await self._create_thumbnail(dicom_data, file_paths['thumbnail'])
            async with self.SessionLocal() as session:
                study = await self._get_or_create_study(session, dicom_metadata)
                series = await self._get_or_create_series(session, dicom_metadata, study)
                instance = DICOMInstance(
                    sop_instance_uid=dicom_metadata.sop_instance_uid,
                    series_instance_uid=dicom_metadata.series_instance_uid,
                    study_instance_uid=dicom_metadata.study_instance_uid,
                    instance_number=dicom_metadata.instance_number,
                    sop_class_uid=dicom_data.SOPClassUID,
                    sop_class_name=dicom_data.SOPClassUID.name if hasattr(dicom_data, 'SOPClassUID') else "Unknown",
                    rows=dicom_metadata.rows,
                    columns=dicom_metadata.columns,
                    bits_allocated=dicom_metadata.bits_allocated,
                    bits_stored=dicom_metadata.bits_stored,
                    high_bit=dicom_metadata.high_bit,
                    photometric_interpretation=dicom_metadata.photometric_interpretation,
                    pixel_spacing=dicom_metadata.pixel_spacing if hasattr(dicom_data, 'PixelSpacing') else None,
                    slice_thickness=dicom_metadata.slice_thickness,
                    slice_location=dicom_metadata.slice_location,
                    image_position=dicom_metadata.image_position,
                    image_orientation=dicom_metadata.image_orientation,
                    window_center=dicom_metadata.window_center,
                    window_width=dicom_metadata.window_width,
                    rescale_intercept=dicom_metadata.rescale_intercept,
                    rescale_slope=dicom_metadata.rescale_slope,
                    file_size_mb=os.path.getsize(file_paths['original']) / (1024 * 1024),
                    file_path=str(file_paths['original']),
                    thumbnail_path=thumbnail_path,
                    compressed_path=compressed_path,
                    checksum=checksum
                )
                session.add(instance)
                await session.commit()
                series.number_of_instances += 1
                series.series_size_mb += instance.file_size_mb
                study.number_of_instances += 1
                study.study_size_mb += instance.file_size_mb
                await session.commit()
                await self._log_audit_event(
                    event_type="IMAGE_STORE",
                    patient_id=dicom_metadata.patient_id,
                    study_instance_uid=dicom_metadata.study_instance_uid,
                    series_instance_uid=dicom_metadata.series_instance_uid,
                    sop_instance_uid=dicom_metadata.sop_instance_uid,
                    action="CREATE",
                    outcome="SUCCESS"
                )
                logger.info(f"Successfully stored DICOM image: {dicom_metadata.sop_instance_uid}")
                return {
                    "sop_instance_uid": dicom_metadata.sop_instance_uid,
                    "study_instance_uid": dicom_metadata.study_instance_uid,
                    "series_instance_uid": dicom_metadata.series_instance_uid,
                    "file_path": str(file_paths['original']),
                    "thumbnail_path": thumbnail_path,
                    "compressed_path": compressed_path,
                    "file_size_mb": instance.file_size_mb,
                    "metadata": dicom_metadata.__dict__
                }
        except Exception as e:
            logger.error(f"Error storing DICOM image: {e}")
            await self._log_audit_event(
                event_type="IMAGE_STORE",
                action="CREATE",
                outcome="FAILURE",
                description=str(e)
            )
            raise
    def _extract_metadata(self, dicom_data: Dataset) -> DICOMMetadata:
        return DICOMMetadata(
            study_instance_uid=dicom_data.StudyInstanceUID,
            series_instance_uid=dicom_data.SeriesInstanceUID,
            sop_instance_uid=dicom_data.SOPInstanceUID,
            study_id=getattr(dicom_data, 'StudyID', ''),
            series_number=int(getattr(dicom_data, 'SeriesNumber', 1)),
            instance_number=int(getattr(dicom_data, 'InstanceNumber', 1)),
            modality=ImageModality(getattr(dicom_data, 'Modality', 'OT')),
            patient_id=dicom_data.PatientID,
            patient_name=str(dicom_data.PatientName),
            patient_birth_date=getattr(dicom_data, 'PatientBirthDate', ''),
            patient_sex=getattr(dicom_data, 'PatientSex', 'U'),
            study_date=getattr(dicom_data, 'StudyDate', ''),
            study_time=getattr(dicom_data, 'StudyTime', ''),
            study_description=getattr(dicom_data, 'StudyDescription', ''),
            series_description=getattr(dicom_data, 'SeriesDescription', ''),
            body_part_examined=getattr(dicom_data, 'BodyPartExamined', ''),
            view_position=getattr(dicom_data, 'ViewPosition', None),
            photometric_interpretation=getattr(dicom_data, 'PhotometricInterpretation', 'MONOCHROME2'),
            samples_per_pixel=int(getattr(dicom_data, 'SamplesPerPixel', 1)),
            rows=int(getattr(dicom_data, 'Rows', 512)),
            columns=int(getattr(dicom_data, 'Columns', 512)),
            bits_allocated=int(getattr(dicom_data, 'BitsAllocated', 16)),
            bits_stored=int(getattr(dicom_data, 'BitsStored', 16)),
            high_bit=int(getattr(dicom_data, 'HighBit', 15)),
            pixel_representation=int(getattr(dicom_data, 'PixelRepresentation', 0)),
            window_center=float(getattr(dicom_data, 'WindowCenter', 0)) if hasattr(dicom_data, 'WindowCenter') else None,
            window_width=float(getattr(dicom_data, 'WindowWidth', 0)) if hasattr(dicom_data, 'WindowWidth') else None,
            rescale_intercept=float(getattr(dicom_data, 'RescaleIntercept', 0)),
            rescale_slope=float(getattr(dicom_data, 'RescaleSlope', 1)),
            institution_name=getattr(dicom_data, 'InstitutionName', None),
            station_name=getattr(dicom_data, 'StationName', None),
            performing_physician_name=getattr(dicom_data, 'PerformingPhysicianName', None),
            referring_physician_name=getattr(dicom_data, 'ReferringPhysicianName', None)
        )
    def _generate_file_paths(self, metadata: DICOMMetadata) -> Dict[str, Path]:
        base_path = self.storage_paths['original']
        study_path = base_path / metadata.study_instance_uid
        series_path = study_path / metadata.series_instance_uid
        study_path.mkdir(exist_ok=True)
        series_path.mkdir(exist_ok=True)
        return {
            'original': series_path / f"{metadata.sop_instance_uid}.dcm",
            'compressed': self.storage_paths['compressed'] / metadata.study_instance_uid / metadata.series_instance_uid / f"{metadata.sop_instance_uid}.jpg",
            'thumbnail': self.storage_paths['thumbnails'] / metadata.study_instance_uid / metadata.series_instance_uid / f"{metadata.sop_instance_uid}_thumb.jpg"
        }
    async def _calculate_checksum(self, file_obj: BinaryIO) -> str:
        file_obj.seek(0)
        file_hash = hashlib.sha256()
        while chunk := file_obj.read(8192):
            file_hash.update(chunk)
        file_obj.seek(0)
        return file_hash.hexdigest()
    async def _find_duplicate(self, checksum: str) -> Optional[DICOMInstance]:
        async with self.SessionLocal() as session:
            result = await session.execute(
                session.query(DICOMInstance).filter(DICOMInstance.checksum == checksum)
            )
            return result.scalar_one_or_none()
    async def _store_file(self, file_obj: BinaryIO, file_path: Path):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_obj.read())
    async def _create_compressed_version(self, dicom_data: Dataset, output_path: Path) -> str:
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            pixel_array = dicom_data.pixel_array
            if hasattr(dicom_data, 'WindowCenter') and hasattr(dicom_data, 'WindowWidth'):
                window_center = float(dicom_data.WindowCenter) if isinstance(dicom_data.WindowCenter, (int, float)) else float(dicom_data.WindowCenter[0])
                window_width = float(dicom_data.WindowWidth) if isinstance(dicom_data.WindowWidth, (int, float)) else float(dicom_data.WindowWidth[0])
                pixel_array = self._apply_window_level(pixel_array, window_center, window_width)
            pixel_array = ((pixel_array - pixel_array.min()) / (pixel_array.max() - pixel_array.min()) * 255).astype(np.uint8)
            image = Image.fromarray(pixel_array)
            image.save(output_path, 'JPEG', quality=85)
            return str(output_path)
        except Exception as e:
            logger.error(f"Error creating compressed version: {e}")
            return ""
    def _apply_window_level(self, pixel_array: np.ndarray, window_center: float, window_width: float) -> np.ndarray:
        window_min = window_center - window_width / 2
        window_max = window_center + window_width / 2
        pixel_array = np.clip(pixel_array, window_min, window_max)
        pixel_array = ((pixel_array - window_min) / (window_max - window_min) * 255)
        return pixel_array
    async def _create_thumbnail(self, dicom_data: Dataset, output_path: Path) -> str:
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            pixel_array = dicom_data.pixel_array
            if hasattr(dicom_data, 'WindowCenter') and hasattr(dicom_data, 'WindowWidth'):
                window_center = float(dicom_data.WindowCenter) if isinstance(dicom_data.WindowCenter, (int, float)) else float(dicom_data.WindowCenter[0])
                window_width = float(dicom_data.WindowWidth) if isinstance(dicom_data.WindowWidth, (int, float)) else float(dicom_data.WindowWidth[0])
                pixel_array = self._apply_window_level(pixel_array, window_center, window_width)
            pixel_array = ((pixel_array - pixel_array.min()) / (pixel_array.max() - pixel_array.min()) * 255).astype(np.uint8)
            image = Image.fromarray(pixel_array)
            image = image.resize((128, 128), Image.Resampling.LANCZOS)
            image.save(output_path, 'JPEG', quality=75)
            return str(output_path)
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            return ""
    async def _get_or_create_study(self, session: AsyncSession, metadata: DICOMMetadata) -> DICOMStudy:
        result = await session.execute(
            session.query(DICOMStudy).filter(DICOMStudy.study_instance_uid == metadata.study_instance_uid)
        )
        study = result.scalar_one_or_none()
        if not study:
            study = DICOMStudy(
                study_instance_uid=metadata.study_instance_uid,
                study_id=metadata.study_id,
                study_date=metadata.study_date,
                study_time=metadata.study_time,
                study_description=metadata.study_description,
                patient_id=metadata.patient_id,
                patient_name=metadata.patient_name,
                patient_birth_date=metadata.patient_birth_date,
                patient_sex=metadata.patient_sex,
                referring_physician_name=metadata.referring_physician_name,
                institution_name=metadata.institution_name,
                modalities_in_study=[metadata.modality.value]
            )
            session.add(study)
            await session.commit()
        return study
    async def _get_or_create_series(self, session: AsyncSession, metadata: DICOMMetadata, study: DICOMStudy) -> DICOMSeries:
        result = await session.execute(
            session.query(DICOMSeries).filter(DICOMSeries.series_instance_uid == metadata.series_instance_uid)
        )
        series = result.scalar_one_or_none()
        if not series:
            series = DICOMSeries(
                series_instance_uid=metadata.series_instance_uid,
                study_instance_uid=metadata.study_instance_uid,
                series_number=metadata.series_number,
                modality=metadata.modality.value,
                series_description=metadata.series_description,
                body_part_examined=metadata.body_part_examined,
                series_date=metadata.study_date,
                series_time=metadata.study_time,
                performing_physician_name=metadata.performing_physician_name,
                station_name=metadata.station_name
            )
            session.add(series)
            await session.commit()
        return series
    async def query_studies(self, query_params: Dict) -> List[Dict]:
        try:
            async with self.SessionLocal() as session:
                query = session.query(DICOMStudy)
                if 'patient_id' in query_params:
                    query = query.filter(DICOMStudy.patient_id.ilike(f"%{query_params['patient_id']}%"))
                if 'patient_name' in query_params:
                    query = query.filter(DICOMStudy.patient_name.ilike(f"%{query_params['patient_name']}%"))
                if 'study_date' in query_params:
                    query = query.filter(DICOMStudy.study_date == query_params['study_date'])
                if 'modality' in query_params:
                    query = query.filter(DICOMStudy.modalities_in_study.contains([query_params['modality']]))
                if 'accession_number' in query_params:
                    query = query.filter(DICOMStudy.accession_number == query_params['accession_number'])
                result = await session.execute(query)
                studies = result.scalars().all()
                await self._log_query(
                    query_type="STUDY",
                    query_parameters=query_params,
                    result_count=len(studies)
                )
                return [study.__dict__ for study in studies]
        except Exception as e:
            logger.error(f"Error querying studies: {e}")
            raise
    async def get_study_instances(self, study_instance_uid: str) -> List[Dict]:
        try:
            async with self.SessionLocal() as session:
                query = session.query(DICOMInstance).filter(
                    DICOMInstance.study_instance_uid == study_instance_uid
                )
                result = await session.execute(query)
                instances = result.scalars().all()
                return [instance.__dict__ for instance in instances]
        except Exception as e:
            logger.error(f"Error getting study instances: {e}")
            raise
    async def get_dicom_image(self, sop_instance_uid: str, quality: ImageQuality = ImageQuality.ORIGINAL) -> StreamingResponse:
        try:
            async with self.SessionLocal() as session:
                result = await session.execute(
                    session.query(DICOMInstance).filter(DICOMInstance.sop_instance_uid == sop_instance_uid)
                )
                instance = result.scalar_one_or_none()
                if not instance:
                    raise HTTPException(status_code=404, detail="Image not found")
                if quality == ImageQuality.THUMBNAIL and instance.thumbnail_path:
                    file_path = instance.thumbnail_path
                elif quality in [ImageQuality.HIGH, ImageQuality.MEDIUM, ImageQuality.LOW] and instance.compressed_path:
                    file_path = instance.compressed_path
                else:
                    file_path = instance.file_path
                if not os.path.exists(file_path):
                    raise HTTPException(status_code=404, detail="Image file not found")
                await self._log_audit_event(
                    event_type="IMAGE_RETRIEVE",
                    patient_id=instance.patient_id,
                    study_instance_uid=instance.study_instance_uid,
                    series_instance_uid=instance.series_instance_uid,
                    sop_instance_uid=instance.sop_instance_uid,
                    action="READ",
                    outcome="SUCCESS"
                )
                async def file_streamer():
                    async with aiofiles.open(file_path, 'rb') as f:
                        yield await f.read()
                media_type = "application/dicom" if quality == ImageQuality.ORIGINAL else "image/jpeg"
                return StreamingResponse(
                    file_streamer(),
                    media_type=media_type,
                    headers={"Content-Disposition": f"inline; filename={os.path.basename(file_path)}"}
                )
        except Exception as e:
            logger.error(f"Error getting DICOM image: {e}")
            raise
    async def anonymize_dicom_image(self, sop_instance_uid: str) -> Dict:
        try:
            async with self.SessionLocal() as session:
                result = await session.execute(
                    session.query(DICOMInstance).filter(DICOMInstance.sop_instance_uid == sop_instance_uid)
                )
                instance = result.scalar_one_or_none()
                if not instance:
                    raise HTTPException(status_code=404, detail="Image not found")
                dicom_data = pydicom.dcmread(instance.file_path)
                anonymized_data = self._anonymize_dataset(dicom_data)
                new_study_uid = generate_uid()
                new_series_uid = generate_uid()
                new_sop_uid = generate_uid()
                anonymized_data.StudyInstanceUID = new_study_uid
                anonymized_data.SeriesInstanceUID = new_series_uid
                anonymized_data.SOPInstanceUID = new_sop_uid
                new_metadata = self._extract_metadata(anonymized_data)
                new_file_paths = self._generate_file_paths(new_metadata)
                anonymized_data.save_as(new_file_paths['original'])
                compressed_path = await self._create_compressed_version(anonymized_data, new_file_paths['compressed'])
                thumbnail_path = await self._create_thumbnail(anonymized_data, new_file_paths['thumbnail'])
                new_instance = DICOMInstance(
                    sop_instance_uid=new_sop_uid,
                    series_instance_uid=new_series_uid,
                    study_instance_uid=new_study_uid,
                    instance_number=instance.instance_number,
                    sop_class_uid=instance.sop_class_uid,
                    sop_class_name=instance.sop_class_name,
                    rows=instance.rows,
                    columns=instance.columns,
                    bits_allocated=instance.bits_allocated,
                    bits_stored=instance.bits_stored,
                    high_bit=instance.high_bit,
                    photometric_interpretation=instance.photometric_interpretation,
                    pixel_spacing=instance.pixel_spacing,
                    slice_thickness=instance.slice_thickness,
                    slice_location=instance.slice_location,
                    image_position=instance.image_position,
                    image_orientation=instance.image_orientation,
                    window_center=instance.window_center,
                    window_width=instance.window_width,
                    rescale_intercept=instance.rescale_intercept,
                    rescale_slope=instance.rescale_slope,
                    file_size_mb=instance.file_size_mb,
                    file_path=str(new_file_paths['original']),
                    thumbnail_path=thumbnail_path,
                    compressed_path=compressed_path,
                    checksum=instance.checksum,
                    is_anonymized=True
                )
                session.add(new_instance)
                await session.commit()
                await self._log_audit_event(
                    event_type="IMAGE_ANONYMIZE",
                    study_instance_uid=instance.study_instance_uid,
                    series_instance_uid=instance.series_instance_uid,
                    sop_instance_uid=instance.sop_instance_uid,
                    action="UPDATE",
                    outcome="SUCCESS"
                )
                logger.info(f"Successfully anonymized DICOM image: {sop_instance_uid} -> {new_sop_uid}")
                return {
                    "original_sop_instance_uid": sop_instance_uid,
                    "new_sop_instance_uid": new_sop_uid,
                    "new_study_instance_uid": new_study_uid,
                    "new_series_instance_uid": new_series_uid,
                    "file_path": str(new_file_paths['original']),
                    "thumbnail_path": thumbnail_path,
                    "compressed_path": compressed_path
                }
        except Exception as e:
            logger.error(f"Error anonymizing DICOM image: {e}")
            raise
    def _anonymize_dataset(self, dataset: Dataset) -> Dataset:
        anonymized = dataset.copy()
        phi_tags = [
            (0x0010, 0x0010),  
            (0x0010, 0x0020),  
            (0x0010, 0x0030),  
            (0x0010, 0x0040),  
            (0x0010, 0x1010),  
            (0x0010, 0x1030),  
            (0x0010, 0x4000),  
            (0x0008, 0x0080),  
            (0x0008, 0x0081),  
            (0x0008, 0x0090),  
            (0x0008, 0x0092),  
            (0x0008, 0x0094),  
            (0x0008, 0x0096),  
            (0x0008, 0x1048),  
            (0x0008, 0x1050),  
            (0x0008, 0x1060),  
            (0x0008, 0x1070),  
            (0x0008, 0x1080),  
            (0x0008, 0x1081),  
            (0x0008, 0x1110),  
            (0x0008, 0x1120),  
            (0x0008, 0x1140),  
            (0x0008, 0x1155),  
        ]
        for tag in phi_tags:
            if tag in anonymized:
                if tag == (0x0010, 0x0010):  
                    anonymized[tag].value = "ANONYMOUS"
                elif tag == (0x0010, 0x0020):  
                    anonymized[tag].value = f"ANON_{uuid.uuid4().hex[:8]}"
                elif tag == (0x0010, 0x0030):  
                    anonymized[tag].value = "19000101"
                elif tag == (0x0010, 0x0040):  
                    anonymized[tag].value = "U"
                else:
                    del anonymized[tag]
        return anonymized
    async def _log_audit_event(self, event_type: str, action: str, outcome: str,
                             patient_id: str = None, study_instance_uid: str = None,
                             series_instance_uid: str = None, sop_instance_uid: str = None,
                             description: str = None):
        async with self.SessionLocal() as session:
            audit_log = DICOMAuditLog(
                event_type=event_type,
                patient_id=patient_id,
                study_instance_uid=study_instance_uid,
                series_instance_uid=series_instance_uid,
                sop_instance_uid=sop_instance_uid,
                action=action,
                outcome=outcome,
                description=description
            )
            session.add(audit_log)
            await session.commit()
    async def _log_query(self, query_type: str, query_parameters: Dict, result_count: int):
        async with self.SessionLocal() as session:
            query_log = DICOMQuery(
                query_id=str(uuid.uuid4()),
                query_type=query_type,
                query_parameters=query_parameters,
                result_count=result_count
            )
            session.add(query_log)
            await session.commit()
    async def _cleanup_task(self):
        while True:
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=90)
                async with self.SessionLocal() as session:
                    await session.execute(
                        session.query(DICOMAuditLog)
                        .filter(DICOMAuditLog.event_time < cutoff_date)
                        .delete()
                    )
                    await session.commit()
                query_cutoff = datetime.utcnow() - timedelta(days=30)
                async with self.SessionLocal() as session:
                    await session.execute(
                        session.query(DICOMQuery)
                        .filter(DICOMQuery.query_time < query_cutoff)
                        .delete()
                    )
                    await session.commit()
                await asyncio.sleep(86400)  
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    async def _indexing_task(self):
        while True:
            try:
                await self._process_indexing_queue()
                await asyncio.sleep(300)  
            except Exception as e:
                logger.error(f"Error in indexing task: {e}")
    async def _process_indexing_queue(self):
        pass
    async def _backup_task(self):
        while True:
            try:
                if self.storage_config.backup_enabled:
                    await self._perform_backup()
                await asyncio.sleep(86400)  
            except Exception as e:
                logger.error(f"Error in backup task: {e}")
    async def _perform_backup(self):
        pass
dicom_app = FastAPI(
    title="HMS DICOM Integration",
    description="DICOM Medical Imaging Integration for Hospital Management System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
Instrumentator().instrument(dicom_app).expose(dicom_app)
dicom_integration: Optional[DICOMIntegration] = None
async def get_dicom_integration() -> DICOMIntegration:
    global dicom_integration
    if dicom_integration is None:
        from ..orchestrator import orchestrator
        dicom_integration = DICOMIntegration(orchestrator)
        await dicom_integration.initialize()
    return dicom_integration
@dicom_app.on_event("startup")
async def startup_event():
    global dicom_integration
    if dicom_integration is None:
        from ..orchestrator import orchestrator
        dicom_integration = DICOMIntegration(orchestrator)
        await dicom_integration.initialize()
@dicom_app.on_event("shutdown")
async def shutdown_event():
    if dicom_integration and dicom_integration.redis_client:
        await dicom_integration.redis_client.close()
@dicom_app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
@dicom_app.post("/dicom/store")
async def store_dicom_image(
    file: UploadFile = File(...),
    dicom_integration: DICOMIntegration = Depends(get_dicom_integration)
):
    try:
        result = await dicom_integration.store_dicom_image(file.file)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@dicom_app.get("/dicom/studies")
async def query_studies(
    patient_id: Optional[str] = None,
    patient_name: Optional[str] = None,
    study_date: Optional[str] = None,
    modality: Optional[str] = None,
    accession_number: Optional[str] = None,
    dicom_integration: DICOMIntegration = Depends(get_dicom_integration)
):
    query_params = {}
    if patient_id:
        query_params['patient_id'] = patient_id
    if patient_name:
        query_params['patient_name'] = patient_name
    if study_date:
        query_params['study_date'] = study_date
    if modality:
        query_params['modality'] = modality
    if accession_number:
        query_params['accession_number'] = accession_number
    try:
        studies = await dicom_integration.query_studies(query_params)
        return {"status": "success", "studies": studies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@dicom_app.get("/dicom/studies/{study_instance_uid}/instances")
async def get_study_instances(
    study_instance_uid: str,
    dicom_integration: DICOMIntegration = Depends(get_dicom_integration)
):
    try:
        instances = await dicom_integration.get_study_instances(study_instance_uid)
        return {"status": "success", "instances": instances}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@dicom_app.get("/dicom/images/{sop_instance_uid}")
async def get_dicom_image(
    sop_instance_uid: str,
    quality: str = "ORIGINAL",
    dicom_integration: DICOMIntegration = Depends(get_dicom_integration)
):
    try:
        image_quality = ImageQuality(quality)
        return await dicom_integration.get_dicom_image(sop_instance_uid, image_quality)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid quality parameter")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@dicom_app.post("/dicom/images/{sop_instance_uid}/anonymize")
async def anonymize_dicom_image(
    sop_instance_uid: str,
    dicom_integration: DICOMIntegration = Depends(get_dicom_integration)
):
    try:
        result = await dicom_integration.anonymize_dicom_image(sop_instance_uid)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(dicom_app, host="0.0.0.0", port=8084)