"""
Enterprise-grade PACS (Picture Archiving and Communication System) Integration
DICOM 3.0 compliant with HL7 integration and real-time image management
"""

import asyncio
import hashlib
import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pydicom
import requests
from fastapi import File, HTTPException, UploadFile
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class Modality(Enum):
    """DICOM imaging modalities"""

    CR = "CR"  # Computed Radiography
    CT = "CT"  # Computed Tomography
    DX = "DX"  # Digital Radiography
    ES = "ES"  # Endoscopy
    MG = "MG"  # Mammography
    MR = "MR"  # Magnetic Resonance
    NM = "NM"  # Nuclear Medicine
    OT = "OT"  # Other
    PT = "PT"  # Positron Emission Tomography
    RF = "RF"  # Radio Fluoroscopy
    SC = "SC"  # Secondary Capture
    US = "US"  # Ultrasound
    XA = "XA"  # X-Ray Angiography


class SOPClass(Enum):
    """DICOM Service-Object Pair Classes"""

    CR_IMAGE_STORAGE = "1.2.840.10008.5.1.4.1.1.1"
    CT_IMAGE_STORAGE = "1.2.840.10008.5.1.4.1.1.2"
    MR_IMAGE_STORAGE = "1.2.840.10008.5.1.4.1.1.4"
    RT_DOSE_STORAGE = "1.2.840.10008.5.1.4.1.1.481.2"
    RT_PLAN_STORAGE = "1.2.840.10008.5.1.4.1.1.481.5"
    RT_STRUCTURE_SET_STORAGE = "1.2.840.10008.5.1.4.1.1.481.3"


@dataclass
class PACSStudy:
    """PACS Study information"""

    study_instance_uid: str
    study_id: str
    study_date: str
    study_time: str
    study_description: str
    patient_id: str
    patient_name: str
    modalities_in_study: List[str]
    number_of_series: int
    number_of_instances: int
    study_status: str
    accessed_datetime: Optional[datetime] = None


@dataclass
class PACSSeries:
    """PACS Series information"""

    series_instance_uid: str
    series_number: int
    modality: str
    series_description: str
    body_part_examined: str
    study_instance_uid: str
    number_of_instances: int
    series_datetime: Optional[datetime] = None


@dataclass
class PACSImage:
    """PACS Image information"""

    sop_instance_uid: str
    sop_class_uid: str
    instance_number: int
    series_instance_uid: str
    study_instance_uid: str
    image_type: List[str]
    rows: int
    columns: int
    bits_allocated: int
    bits_stored: int
    high_bit: int
    photometric_interpretation: str
    pixel_spacing: Optional[List[float]] = None
    slice_thickness: Optional[float] = None
    window_center: Optional[float] = None
    window_width: Optional[float] = None


class PACSService:
    """
    Enterprise PACS service with DICOM 3.0 compliance
    """

    def __init__(self):
        self.pacs_url = os.getenv("PACS_URL", "http://localhost:8042")
        self.pacs_aet = os.getenv("PACS_AET", "HMS-RADIOLOGY")
        self.pacs_aec = os.getenv("PACS_AEC", "ORTHANC")
        self.pacs_username = os.getenv("PACS_USERNAME")
        self.pacs_password = os.getenv("PACS_PASSWORD")
        self.dicom_dir = os.getenv("DICOM_STORAGE_DIR", "/var/lib/dicom")
        self.hl7_url = os.getenv("HL7_URL", "http://localhost:8080")

        # Configure DICOM networking
        self._configure_dicom_network()

    def _configure_dicom_network(self):
        """Configure DICOM network parameters"""
        try:
            # Import pynetdicom for DICOM networking
            from pynetdicom import AE, build_context, evt
            from pynetdicom.sop_class import VerificationSOPClass

            # Create Application Entity
            self.ae = AE(ae_title=self.pacs_aet)
            self.ae.add_requested_context(VerificationSOPClass)
            self.ae.add_requested_context(
                build_context("1.2.840.10008.5.1.4.1.1.2")
            )  # CT Image Storage
            self.ae.add_requested_context(
                build_context("1.2.840.10008.5.1.4.1.1.4")
            )  # MR Image Storage

            logger.info(f"PACS network configured with AET: {self.pacs_aet}")

        except ImportError:
            logger.warning("pynetdicom not available - using HTTP REST API only")
            self.ae = None

    async def query_studies(
        self, patient_id: str, study_date: Optional[str] = None
    ) -> List[PACSStudy]:
        """
        Query PACS for studies using QIDO-RS (Query based on ID for DICOM Objects)
        """
        try:
            # Build QIDO-RS query parameters
            params = {"PatientID": patient_id, "includefield": "all"}

            if study_date:
                params["StudyDate"] = study_date

            # Make QIDO-RS request
            response = await self._make_pacs_request("GET", "/studies", params=params)

            if response.status_code == 200:
                studies_data = response.json()
                studies = []

                for study_data in studies_data:
                    study = PACSStudy(
                        study_instance_uid=study_data.get("0020000D", {}).get(
                            "Value", [""]
                        )[0],
                        study_id=study_data.get("00200010", {}).get("Value", [""])[0],
                        study_date=study_data.get("00080020", {}).get("Value", [""])[0],
                        study_time=study_data.get("00080030", {}).get("Value", [""])[0],
                        study_description=study_data.get("00081030", {}).get(
                            "Value", [""]
                        )[0],
                        patient_id=study_data.get("00100020", {}).get("Value", [""])[0],
                        patient_name=study_data.get("00100010", {})
                        .get("Value", [{"Alphabetic": ""}])[0]
                        .get("Alphabetic", ""),
                        modalities_in_study=study_data.get("00080061", {}).get(
                            "Value", []
                        ),
                        number_of_series=study_data.get("00201206", {}).get(
                            "Value", [0]
                        )[0],
                        number_of_instances=study_data.get("00201208", {}).get(
                            "Value", [0]
                        )[0],
                        study_status=study_data.get("00550010", {}).get("Value", [""])[
                            0
                        ],
                        accessed_datetime=datetime.now(timezone.utc),
                    )
                    studies.append(study)

                logger.info(f"Found {len(studies)} studies for patient {patient_id}")
                return studies

            else:
                logger.error(
                    f"PACS query failed: {response.status_code} - {response.text}"
                )
                return []

        except Exception as e:
            logger.error(f"Error querying PACS studies: {e}")
            return []

    async def get_series(self, study_instance_uid: str) -> List[PACSSeries]:
        """
        Get series for a specific study
        """
        try:
            response = await self._make_pacs_request(
                "GET", f"/studies/{study_instance_uid}/series"
            )

            if response.status_code == 200:
                series_data = response.json()
                series_list = []

                for series_info in series_data:
                    series = PACSSeries(
                        series_instance_uid=series_info.get("0020000E", {}).get(
                            "Value", [""]
                        )[0],
                        series_number=series_info.get("00200011", {}).get("Value", [0])[
                            0
                        ],
                        modality=series_info.get("00080060", {}).get("Value", [""])[0],
                        series_description=series_info.get("0008103E", {}).get(
                            "Value", [""]
                        )[0],
                        body_part_examined=series_info.get("00180015", {}).get(
                            "Value", [""]
                        )[0],
                        study_instance_uid=study_instance_uid,
                        number_of_instances=series_info.get("00201209", {}).get(
                            "Value", [0]
                        )[0],
                        series_datetime=(
                            datetime.fromisoformat(
                                series_info.get("0008002A", {}).get("Value", [""])[0]
                            )
                            if series_info.get("0008002A")
                            else None
                        ),
                    )
                    series_list.append(series)

                return series_list

            else:
                logger.error(
                    f"Failed to get series: {response.status_code} - {response.text}"
                )
                return []

        except Exception as e:
            logger.error(f"Error getting series: {e}")
            return []

    async def get_images(self, series_instance_uid: str) -> List[PACSImage]:
        """
        Get images for a specific series
        """
        try:
            response = await self._make_pacs_request(
                "GET", f"/series/{series_instance_uid}/instances"
            )

            if response.status_code == 200:
                instances_data = response.json()
                images = []

                for instance in instances_data:
                    # Get detailed DICOM metadata
                    metadata_response = await self._make_pacs_request(
                        "GET", f'/instances/{instance["ID"]}/metadata'
                    )
                    metadata = (
                        metadata_response.json()
                        if metadata_response.status_code == 200
                        else {}
                    )

                    image = PACSImage(
                        sop_instance_uid=instance.get("ID", ""),
                        sop_class_uid=instance.get("00080016", {}).get("Value", [""])[
                            0
                        ],
                        instance_number=instance.get("00200013", {}).get("Value", [0])[
                            0
                        ],
                        series_instance_uid=series_instance_uid,
                        study_instance_uid=instance.get("0020000D", {}).get(
                            "Value", [""]
                        )[0],
                        image_type=metadata.get("00080008", {}).get("Value", []),
                        rows=metadata.get("00280010", {}).get("Value", [0])[0],
                        columns=metadata.get("00280011", {}).get("Value", [0])[0],
                        bits_allocated=metadata.get("00280100", {}).get("Value", [16])[
                            0
                        ],
                        bits_stored=metadata.get("00280101", {}).get("Value", [16])[0],
                        high_bit=metadata.get("00280102", {}).get("Value", [15])[0],
                        photometric_interpretation=metadata.get("00280004", {}).get(
                            "Value", ["MONOCHROME2"]
                        )[0],
                        pixel_spacing=metadata.get("00280030", {}).get("Value"),
                        slice_thickness=metadata.get("00180050", {}).get(
                            "Value", [None]
                        )[0],
                        window_center=metadata.get("00281050", {}).get("Value", [None])[
                            0
                        ],
                        window_width=metadata.get("00281051", {}).get("Value", [None])[
                            0
                        ],
                    )
                    images.append(image)

                return images

            else:
                logger.error(
                    f"Failed to get images: {response.status_code} - {response.text}"
                )
                return []

        except Exception as e:
            logger.error(f"Error getting images: {e}")
            return []

    async def store_dicom(
        self, dicom_file: bytes, study_instance_uid: str
    ) -> Dict[str, Any]:
        """
        Store DICOM file using STOW-RS (Store Over the Web for DICOM Objects)
        """
        try:
            # Validate DICOM file
            try:
                ds = pydicom.dcmread(dicom_file)
                logger.info(f"Valid DICOM file: {ds.SOPClassUID.name}")
            except Exception as e:
                raise ValueError(f"Invalid DICOM file: {e}")

            # Prepare STOW-RS request
            files = {"file": ("study.dcm", dicom_file, "application/dicom")}

            headers = {
                "Content-Type": 'multipart/related; type="application/dicom"',
                "Accept": "application/dicom+json",
            }

            response = await self._make_pacs_request(
                "POST", "/studies", files=files, headers=headers
            )

            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(
                    f"DICOM file stored successfully: {result.get('00081199', {}).get('Value', [''])[0]}"
                )
                return {
                    "status": "success",
                    "study_instance_uid": study_instance_uid,
                    "response": result,
                }
            else:
                logger.error(
                    f"Failed to store DICOM: {response.status_code} - {response.text}"
                )
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}: {response.text}",
                }

        except Exception as e:
            logger.error(f"Error storing DICOM: {e}")
            return {"status": "error", "error": str(e)}

    async def get_wado_image(
        self,
        study_instance_uid: str,
        series_instance_uid: str,
        sop_instance_uid: str,
        image_format: str = "jpeg",
        quality: int = 85,
    ) -> bytes:
        """
        Get image using WADO-RS (Web Access to DICOM Objects for RESTful Services)
        """
        try:
            params = {
                "requestType": "WADO",
                "studyUID": study_instance_uid,
                "seriesUID": series_instance_uid,
                "objectUID": sop_instance_uid,
                "contentType": f"image/{image_format}",
                "quality": quality,
            }

            response = await self._make_pacs_request(
                "GET", "/wado", params=params, return_raw=True
            )

            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"Failed to get WADO image: {response.status_code}")
                raise HTTPException(
                    status_code=response.status_code, detail="Failed to retrieve image"
                )

        except Exception as e:
            logger.error(f"Error getting WADO image: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def send_hl7_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send HL7 order to RIS/HIS
        """
        try:
            # Create HL7 ORM message (Order message)
            hl7_message = self._create_hl7_orm_message(order_data)

            headers = {
                "Content-Type": "application/hl7-v2+json",
                "Accept": "application/json",
            }

            response = await self._make_hl7_request(
                "POST", "/orders", json=hl7_message, headers=headers
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(
                    f"HL7 order sent successfully: {result.get('messageControlId')}"
                )
                return {
                    "status": "success",
                    "message_control_id": result.get("messageControlId"),
                    "response": result,
                }
            else:
                logger.error(
                    f"Failed to send HL7 order: {response.status_code} - {response.text}"
                )
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}: {response.text}",
                }

        except Exception as e:
            logger.error(f"Error sending HL7 order: {e}")
            return {"status": "error", "error": str(e)}

    async def _make_pacs_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
        files: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        return_raw: bool = False,
    ):
        """Make HTTP request to PACS server"""
        try:
            url = f"{self.pacs_url}{endpoint}"

            auth = None
            if self.pacs_username and self.pacs_password:
                auth = (self.pacs_username, self.pacs_password)

            response = requests.request(
                method=method,
                url=url,
                params=params,
                json=json,
                files=files,
                headers=headers,
                auth=auth,
                timeout=30,
            )

            return response

        except Exception as e:
            logger.error(f"PACS request failed: {e}")
            raise

    async def _make_hl7_request(self, method: str, endpoint: str, **kwargs):
        """Make HTTP request to HL7 server"""
        try:
            url = f"{self.hl7_url}{endpoint}"
            response = requests.request(method, url, timeout=30, **kwargs)
            return response
        except Exception as e:
            logger.error(f"HL7 request failed: {e}")
            raise

    def _create_hl7_orm_message(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create HL7 ORM (Order) message"""
        message_control_id = hashlib.hashlib.sha256(
            str(order_data).encode()
        ).hexdigest()[:16]

        return {
            "messageType": "ORM^O01",
            "messageControlId": message_control_id,
            "processingId": "P",
            "versionId": "2.5",
            "patient": {
                "id": order_data.get("patient_id"),
                "name": order_data.get("patient_name"),
                "dateOfBirth": order_data.get("patient_dob"),
                "sex": order_data.get("patient_sex"),
            },
            "order": {
                "placerOrderNumber": order_data.get("order_id"),
                "fillerOrderNumber": order_data.get("accession_number"),
                "orderControl": "NW",  # New order
                "orderCode": {
                    "identifier": order_data.get("procedure_code"),
                    "text": order_data.get("procedure_description"),
                },
                "orderingProvider": order_data.get("ordering_physician"),
                "orderingFacility": order_data.get(
                    "ordering_facility", "HMS RADIOLOGY"
                ),
                "observationDateTime": order_data.get("order_date"),
                "specimen": order_data.get("specimen"),
                "clinicalInfo": order_data.get("clinical_indication"),
            },
        }

    async def verify_pacs_connectivity(self) -> bool:
        """Verify PACS server connectivity using DICOM Echo"""
        try:
            if self.ae is None:
                # Fallback to HTTP health check
                response = await self._make_pacs_request("GET", "/system")
                return response.status_code == 200

            # Use DICOM C-ECHO (Verification)
            assoc = self.ae.associate(self.pacs_aec, self.pacs_url.split(":")[1])
            if assoc.is_established:
                # Send C-ECHO request
                status = assoc.send_c_echo()
                assoc.release()
                return status.Status == 0x0000  # Success
            else:
                logger.error("Failed to establish DICOM association")
                return False

        except Exception as e:
            logger.error(f"PACS connectivity check failed: {e}")
            return False

    async def get_pacs_statistics(self) -> Dict[str, Any]:
        """Get PACS system statistics"""
        try:
            response = await self._make_pacs_request("GET", "/statistics")
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"Failed to get statistics: {response.status_code}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }


# Factory function for easy instantiation
def create_pacs_service() -> PACSService:
    """Create configured PACS service instance"""
    return PACSService()
