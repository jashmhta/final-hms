"""
hl7_processor module
"""

import asyncio
import json
import logging
import re
import socket
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import aiofiles
import aiohttp
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
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

from ..orchestrator import IntegrationOrchestrator, IntegrationStandards

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
Base = declarative_base()


class HL7MessageType(Enum):
    ADT = "ADT"
    ORM = "ORM"
    ORU = "ORU"
    SIU = "SIU"
    MFN = "MFN"
    MDN = "MDN"
    QRY = "QRY"
    DSR = "DSR"
    RAS = "RAS"
    RDE = "RDE"
    RGV = "RGV"
    VXU = "VXU"


class HL7EventCode(Enum):
    A01 = "A01"
    A02 = "A02"
    A03 = "A03"
    A04 = "A04"
    A05 = "A05"
    A06 = "A06"
    A07 = "A07"
    A08 = "A08"
    A09 = "A09"
    A10 = "A10"
    A11 = "A11"
    A12 = "A12"
    A13 = "A13"
    A14 = "A14"
    A15 = "A15"
    A16 = "A16"
    A17 = "A17"
    A18 = "A18"
    A19 = "A19"
    A20 = "A20"
    A21 = "A21"
    A22 = "A22"
    A24 = "A24"
    A25 = "A25"
    A26 = "A26"
    A27 = "A27"
    A28 = "A28"
    A29 = "A29"
    A30 = "A30"
    A31 = "A31"
    A32 = "A32"
    A33 = "A33"
    A34 = "A34"
    A35 = "A35"
    A36 = "A36"
    A37 = "A37"
    A38 = "A38"
    A39 = "A39"
    A40 = "A40"
    A41 = "A41"
    A42 = "A42"
    A44 = "A44"
    A45 = "A45"
    A46 = "A46"
    A47 = "A47"
    A48 = "A48"
    A49 = "A49"
    A50 = "A50"
    A51 = "A51"


class HL7ProcessingStatus(Enum):
    RECEIVED = "RECEIVED"
    PARSING = "PARSING"
    VALIDATED = "VALIDATED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ERROR = "ERROR"


@dataclass
class HL7Message:
    message_type: HL7MessageType
    event_code: HL7EventCode
    message_control_id: str
    processing_id: str
    version_id: str
    sending_application: str
    sending_facility: str
    receiving_application: str
    receiving_facility: str
    message_datetime: datetime
    security: Optional[str] = None
    message_structure: Optional[str] = None
    segments: List[Dict] = field(default_factory=list)
    raw_message: str = ""
    fhir_mapping: Optional[Dict] = None


class HL7Segment(BaseModel):
    segment_type: str
    fields: List[str]
    sequence_number: Optional[int] = None


class HL7Field(BaseModel):
    value: str
    components: Optional[List[str]] = None
    subcomponents: Optional[List[str]] = None


class HL7AckCode(Enum):
    AA = "AA"
    AR = "AR"
    AE = "AE"
    CA = "CA"
    CE = "CE"
    CR = "CR"


class HL7MessageLog(Base):
    __tablename__ = "hl7_message_log"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_control_id = Column(String(50), nullable=False, index=True)
    message_type = Column(String(10), nullable=False, index=True)
    event_code = Column(String(10), nullable=False, index=True)
    processing_status = Column(String(20), nullable=False, index=True)
    raw_message = Column(Text, nullable=False)
    parsed_message = Column(JSON)
    fhir_mapping = Column(JSON)
    error_message = Column(Text)
    acknowledgment = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    source_system = Column(String(100))
    destination_system = Column(String(100))


class HL7Parser:
    def __init__(self):
        self.field_separator = "|"
        self.component_separator = "^"
        self.subcomponent_separator = "&"
        self.repetition_separator = "~"
        self.escape_character = "\\"

    def parse_message(self, raw_message: str) -> HL7Message:
        try:
            raw_message = self._remove_mllp_wrapping(raw_message)
            segments = raw_message.split("\r")
            segments = [seg.strip() for seg in segments if seg.strip()]
            if not segments:
                raise ValueError("Empty HL7 message")
            msh_segment = segments[0]
            if not msh_segment.startswith("MSH"):
                raise ValueError("MSH segment not found or not first")
            msh_fields = self._parse_segment(msh_segment)
            message = HL7Message(
                message_type=HL7MessageType(msh_fields[8][:3]),
                event_code=HL7EventCode(msh_fields[8][3:]),
                message_control_id=msh_fields[9],
                processing_id=msh_fields[10],
                version_id=msh_fields[11],
                sending_application=msh_fields[2],
                sending_facility=msh_fields[3],
                receiving_application=msh_fields[4],
                receiving_facility=msh_fields[5],
                message_datetime=self._parse_hl7_datetime(msh_fields[6]),
                security=msh_fields[7] if len(msh_fields) > 7 else None,
                message_structure=msh_fields[8] if len(msh_fields) > 8 else None,
                raw_message=raw_message,
            )
            for i, segment_data in enumerate(segments):
                segment_type = segment_data[:3]
                fields = self._parse_segment(segment_data)
                message.segments.append(
                    {
                        "segment_type": segment_type,
                        "sequence": i + 1,
                        "fields": fields,
                        "raw_data": segment_data,
                    }
                )
            return message
        except Exception as e:
            logger.error(f"Error parsing HL7 message: {e}")
            raise

    def _remove_mllp_wrapping(self, message: str) -> str:
        start_char = chr(0x0B)
        end_chars = chr(0x1C) + chr(0x0D)
        if message.startswith(start_char) and message.endswith(end_chars):
            return message[1:-2]
        return message

    def _parse_segment(self, segment: str) -> List[str]:
        if len(segment) < 3:
            return []
        segment_type = segment[:3]
        fields_str = segment[3:]
        if not fields_str:
            return [segment_type]
        fields = [segment_type] + fields_str.split(self.field_separator)
        return fields

    def _parse_hl7_datetime(self, datetime_str: str) -> datetime:
        try:
            if len(datetime_str) < 8:
                raise ValueError("Invalid datetime format")
            year = int(datetime_str[0:4])
            month = int(datetime_str[4:6])
            day = int(datetime_str[6:8])
            hour = 0
            minute = 0
            second = 0
            microsecond = 0
            if len(datetime_str) >= 12:
                hour = int(datetime_str[8:10])
                minute = int(datetime_str[10:12])
            if len(datetime_str) >= 14:
                second = int(datetime_str[12:14])
            if len(datetime_str) >= 15 and datetime_str[14] == ".":
                frac_end = 15
                while frac_end < len(datetime_str) and datetime_str[frac_end].isdigit():
                    frac_end += 1
                frac_seconds = datetime_str[15:frac_end]
                microsecond = int(frac_seconds.ljust(6, "0")[:6])
            tz_offset = None
            if len(datetime_str) > 14:
                if "+" in datetime_str or "-" in datetime_str:
                    tz_sign = (
                        datetime_str[14] if datetime_str[14] in ["+", "-"] else None
                    )
                    if tz_sign:
                        tz_hour = int(datetime_str[15:17])
                        tz_minute = int(datetime_str[17:19])
                        tz_offset = f"{tz_sign}{tz_hour:02d}:{tz_minute:02d}"
            return datetime(year, month, day, hour, minute, second, microsecond)
        except Exception as e:
            logger.warning(f"Error parsing HL7 datetime '{datetime_str}': {e}")
            return datetime.utcnow()

    def create_acknowledgment(
        self,
        original_message: HL7Message,
        ack_code: HL7AckCode,
        error_message: Optional[str] = None,
    ) -> str:
        msh_fields = [
            "MSH",
            self.field_separator,
            self.component_separator
            + self.repetition_separator
            + self.escape_character
            + self.subcomponent_separator,
            original_message.receiving_application,
            original_message.receiving_facility,
            original_message.sending_application,
            original_message.sending_facility,
            datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            "",
            "ACK",
            original_message.message_control_id,
            original_message.processing_id,
            original_message.version_id,
        ]
        msa_fields = [
            "MSA",
            ack_code.value,
            original_message.message_control_id,
            error_message or "",
        ]
        msh_segment = self.field_separator.join(msh_fields)
        msa_segment = self.field_separator.join(msa_fields)
        return f"{msh_segment}\r{msa_segment}\r"


class HL7Processor:
    def __init__(self, orchestrator: IntegrationOrchestrator):
        self.orchestrator = orchestrator
        self.parser = HL7Parser()
        self.db_url = os.getenv(
            "HL7_DB_URL", "postgresql+asyncpg://hms:hms@localhost:5432/hl7"
        )
        self.engine = create_async_engine(self.db_url)
        self.SessionLocal = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.fhir_converter = FHIRConverter()

    async def process_message(
        self, raw_message: str, source_system: str = "Unknown"
    ) -> Dict:
        async with self.SessionLocal() as session:
            try:
                hl7_message = self.parser.parse_message(raw_message)
                message_log = HL7MessageLog(
                    message_control_id=hl7_message.message_control_id,
                    message_type=hl7_message.message_type.value,
                    event_code=hl7_message.event_code.value,
                    processing_status=HL7ProcessingStatus.RECEIVED.value,
                    raw_message=raw_message,
                    parsed_message=hl7_message.segments,
                    source_system=source_system,
                )
                session.add(message_log)
                await session.commit()
                await session.refresh(message_log)
                await self._validate_message(hl7_message)
                result = await self._process_by_type(hl7_message, session)
                fhir_mapping = await self.fhir_converter.convert_hl7_to_fhir(
                    hl7_message
                )
                message_log.processing_status = HL7ProcessingStatus.COMPLETED.value
                message_log.fhir_mapping = fhir_mapping
                message_log.processed_at = datetime.utcnow()
                message_log.parsed_message = hl7_message.segments
                await session.commit()
                ack_message = self.parser.create_acknowledgment(
                    hl7_message, HL7AckCode.AA
                )
                return {
                    "status": "success",
                    "message_control_id": hl7_message.message_control_id,
                    "acknowledgment": ack_message,
                    "fhir_mapping": fhir_mapping,
                    "processed_at": datetime.utcnow().isoformat(),
                }
            except Exception as e:
                logger.error(f"Error processing HL7 message: {e}")
                if "message_log" in locals():
                    message_log.processing_status = HL7ProcessingStatus.FAILED.value
                    message_log.error_message = str(e)
                    await session.commit()
                try:
                    hl7_message = self.parser.parse_message(raw_message)
                    ack_message = self.parser.create_acknowledgment(
                        hl7_message, HL7AckCode.AE, str(e)
                    )
                except:
                    ack_message = "MSH|^~\\&|ERROR|||ERROR||202401011200||ACK|ERROR|P|2.5\rMSA|AE|ERROR|Processing failed"
                return {
                    "status": "error",
                    "error": str(e),
                    "acknowledgment": ack_message,
                    "processed_at": datetime.utcnow().isoformat(),
                }

    async def _validate_message(self, message: HL7Message):
        required_segments = {"MSH"}
        segment_types = {seg["segment_type"] for seg in message.segments}
        missing_segments = required_segments - segment_types
        if missing_segments:
            raise ValueError(f"Missing required segments: {missing_segments}")
        message_structure_validators = {
            (HL7MessageType.ADT, HL7EventCode.A01): self._validate_adt_a01,
            (HL7MessageType.ORM, HL7EventCode.O01): self._validate_orm_o01,
            (HL7MessageType.ORU, HL7EventCode.R01): self._validate_oru_r01,
        }
        validator = message_structure_validators.get(
            (message.message_type, message.event_code)
        )
        if validator:
            validator(message)

    async def _process_by_type(
        self, message: HL7Message, session: AsyncSession
    ) -> Dict:
        processors = {
            (HL7MessageType.ADT, HL7EventCode.A01): self._process_adt_a01,
            (HL7MessageType.ADT, HL7EventCode.A03): self._process_adt_a03,
            (HL7MessageType.ADT, HL7EventCode.A04): self._process_adt_a04,
            (HL7MessageType.ADT, HL7EventCode.A08): self._process_adt_a08,
            (HL7MessageType.ORM, HL7EventCode.O01): self._process_orm_o01,
            (HL7MessageType.ORU, HL7EventCode.R01): self._process_oru_r01,
        }
        processor = processors.get((message.message_type, message.event_code))
        if processor:
            return await processor(message, session)
        else:
            logger.warning(
                f"No processor for message type: {message.message_type.value}_{message.event_code.value}"
            )
            return {
                "status": "no_processor",
                "message": "No processor configured for this message type",
            }

    async def _process_adt_a01(
        self, message: HL7Message, session: AsyncSession
    ) -> Dict:
        pid_segment = next(
            (seg for seg in message.segments if seg["segment_type"] == "PID"), None
        )
        if not pid_segment:
            raise ValueError("PID segment not found in ADT^A01 message")
        patient_data = self._extract_patient_data(pid_segment)
        return {
            "action": "admit_patient",
            "patient_data": patient_data,
            "encounter_id": message.message_control_id,
        }

    async def _process_oru_r01(
        self, message: HL7Message, session: AsyncSession
    ) -> Dict:
        obx_segments = [seg for seg in message.segments if seg["segment_type"] == "OBX"]
        results = []
        for obx in obx_segments:
            observation_data = self._extract_observation_data(obx)
            results.append(observation_data)
        return {
            "action": "observation_results",
            "results": results,
            "message_control_id": message.message_control_id,
        }

    def _extract_patient_data(self, pid_segment: Dict) -> Dict:
        fields = pid_segment["fields"]
        return {
            "patient_id": fields[2] if len(fields) > 2 else None,
            "patient_name": (
                self._parse_patient_name(fields[5]) if len(fields) > 5 else None
            ),
            "date_of_birth": (
                self._parser._parse_hl7_datetime(fields[7]) if len(fields) > 7 else None
            ),
            "gender": fields[8] if len(fields) > 8 else None,
            "address": self._parse_address(fields[11]) if len(fields) > 11 else None,
            "phone_number": (
                self._parse_phone_number(fields[13]) if len(fields) > 13 else None
            ),
        }

    def _extract_observation_data(self, obx_segment: Dict) -> Dict:
        fields = obx_segment["fields"]
        return {
            "observation_id": fields[3] if len(fields) > 3 else None,
            "observation_value": fields[5] if len(fields) > 5 else None,
            "units": fields[6] if len(fields) > 6 else None,
            "reference_range": fields[7] if len(fields) > 7 else None,
            "abnormal_flag": fields[8] if len(fields) > 8 else None,
            "result_status": fields[11] if len(fields) > 11 else None,
        }

    def _parse_patient_name(self, name_field: str) -> Dict:
        if not name_field:
            return {}
        components = name_field.split(self.parser.component_separator)
        return {
            "family_name": components[0] if len(components) > 0 else None,
            "given_name": components[1] if len(components) > 1 else None,
            "middle_name": components[2] if len(components) > 2 else None,
            "suffix": components[3] if len(components) > 3 else None,
            "prefix": components[4] if len(components) > 4 else None,
        }

    def _parse_address(self, address_field: str) -> Dict:
        if not address_field:
            return {}
        components = address_field.split(self.parser.component_separator)
        return {
            "street": components[0] if len(components) > 0 else None,
            "city": components[1] if len(components) > 1 else None,
            "state": components[2] if len(components) > 2 else None,
            "postal_code": components[3] if len(components) > 3 else None,
            "country": components[4] if len(components) > 4 else None,
        }

    def _parse_phone_number(self, phone_field: str) -> Dict:
        if not phone_field:
            return {}
        components = phone_field.split(self.parser.component_separator)
        return {
            "phone_number": components[0] if len(components) > 0 else None,
            "phone_type": components[1] if len(components) > 1 else None,
        }


class FHIRConverter:
    async def convert_hl7_to_fhir(self, hl7_message: HL7Message) -> Dict:
        converters = {
            HL7MessageType.ADT: self._convert_adt_to_fhir,
            HL7MessageType.ORM: self._convert_orm_to_fhir,
            HL7MessageType.ORU: self._convert_oru_to_fhir,
        }
        converter = converters.get(hl7_message.message_type)
        if converter:
            return await converter(hl7_message)
        else:
            return {"error": f"No FHIR converter for {hl7_message.message_type.value}"}

    async def _convert_adt_to_fhir(self, hl7_message: HL7Message) -> Dict:
        fhir_resources = []
        pid_segment = next(
            (seg for seg in hl7_message.segments if seg["segment_type"] == "PID"), None
        )
        if pid_segment:
            patient_resource = await self._convert_pid_to_patient(pid_segment)
            fhir_resources.append(patient_resource)
        pv1_segment = next(
            (seg for seg in hl7_message.segments if seg["segment_type"] == "PV1"), None
        )
        if pv1_segment:
            encounter_resource = await self._convert_pv1_to_encounter(
                pv1_segment, hl7_message
            )
            fhir_resources.append(encounter_resource)
        return {
            "converted_resources": fhir_resources,
            "message_type": hl7_message.message_type.value,
            "event_code": hl7_message.event_code.value,
        }

    async def _convert_pid_to_patient(self, pid_segment: Dict) -> Dict:
        fields = pid_segment["fields"]
        identifiers = []
        if len(fields) > 2 and fields[2]:
            identifiers.append(
                {"system": "http://hl7.org/fhir/sid/patient-id", "value": fields[2]}
            )
        name = {}
        if len(fields) > 5 and fields[5]:
            name_components = fields[5].split("^")
            if len(name_components) > 0:
                name["family"] = name_components[0]
            if len(name_components) > 1:
                name["given"] = [name_components[1]]
        patient_resource = {
            "resourceType": "Patient",
            "identifier": identifiers,
            "active": True,
            "name": [name] if name else [],
        }
        if len(fields) > 7 and fields[7]:
            patient_resource["birthDate"] = fields[7][:8]
        if len(fields) > 8 and fields[8]:
            patient_resource["gender"] = fields[8].lower()
        return patient_resource

    async def _convert_pv1_to_encounter(
        self, pv1_segment: Dict, hl7_message: HL7Message
    ) -> Dict:
        fields = pv1_segment["fields"]
        encounter_resource = {
            "resourceType": "Encounter",
            "status": "in-progress",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "IMP",
                "display": "inpatient encounter",
            },
        }
        if len(fields) > 2 and fields[2]:
            encounter_resource["subject"] = {"reference": f"Patient/{fields[2]}"}
        if len(fields) > 3 and fields[3]:
            encounter_resource["participant"] = [
                {
                    "type": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                                    "code": "ATND",
                                    "display": "attender",
                                }
                            ]
                        }
                    ],
                    "individual": {"reference": f"Practitioner/{fields[3]}"},
                }
            ]
        return encounter_resource


class MLLPServer:
    def __init__(
        self, host: str = "0.0.0.0", port: int = 2575, processor: HL7Processor = None
    ):
        self.host = host
        self.port = port
        self.processor = processor
        self.server_socket = None
        self.running = False

    async def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        logger.info(f"MLLP Server started on {self.host}:{self.port}")
        while self.running:
            try:
                client_socket, address = await asyncio.get_event_loop().sock_accept(
                    self.server_socket
                )
                asyncio.create_task(self.handle_client(client_socket, address))
            except Exception as e:
                logger.error(f"Error accepting connection: {e}")

    async def handle_client(
        self, client_socket: socket.socket, address: Tuple[str, int]
    ):
        logger.info(f"MLLP connection from {address}")
        try:
            start_char = client_socket.recv(1)
            if start_char != b"\x0b":
                logger.warning(f"Invalid MLLP start character from {address}")
                client_socket.close()
                return
            data = b""
            while True:
                chunk = client_socket.recv(1024)
                if not chunk:
                    break
                data += chunk
                if b"\x1c\x0d" in data:
                    break
            message_end = data.find(b"\x1c\x0d")
            if message_end != -1:
                message_data = data[1:message_end].decode("utf-8")
                if self.processor:
                    result = await self.processor.process_message(
                        message_data, f"MLLP:{address[0]}"
                    )
                    ack_message = result.get("acknowledgment", "")
                    if ack_message:
                        ack_data = f"\x0b{ack_message}\x1c\x0d".encode("utf-8")
                        client_socket.send(ack_data)
        except Exception as e:
            logger.error(f"Error handling MLLP client {address}: {e}")
        finally:
            client_socket.close()

    def stop_server(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        logger.info("MLLP Server stopped")


hl7_app = FastAPI(
    title="HMS HL7 Processor",
    description="HL7 v2.x message processing system",
    version="1.0.0",
)
hl7_processor: Optional[HL7Processor] = None


async def get_hl7_processor() -> HL7Processor:
    global hl7_processor
    if hl7_processor is None:
        from ..orchestrator import orchestrator

        hl7_processor = HL7Processor(orchestrator)
    return hl7_processor


@hl7_app.post("/hl7/process")
async def process_hl7_message(
    message: str,
    source_system: str = "Unknown",
    processor: HL7Processor = Depends(get_hl7_processor),
):
    return await processor.process_message(message, source_system)


@hl7_app.get("/hl7/messages")
async def get_hl7_messages(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    message_type: Optional[str] = Query(None),
    processor: HL7Processor = Depends(get_hl7_processor),
):
    pass


if __name__ == "__main__":
    import os

    import uvicorn

    uvicorn.run(hl7_app, host="0.0.0.0", port=8081)
