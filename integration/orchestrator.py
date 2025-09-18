import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
import aiohttp
import asyncpg
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/hms_integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
class IntegrationStandards(Enum):
    FHIR_R4 = "FHIR_R4"
    HL7_V2 = "HL7_V2"
    HL7_V3 = "HL7_V3"
    DICOM = "DICOM"
    ICD_10 = "ICD_10"
    SNOMED_CT = "SNOMED_CT"
    LOINC = "LOINC"
    CPT = "CPT"
    NDC = "NDC"
class IntegrationType(Enum):
    API_BASED = "API_BASED"
    MESSAGE_QUEUE = "MESSAGE_QUEUE"
    FILE_TRANSFER = "FILE_TRANSFER"
    DATABASE_SYNC = "DATABASE_SYNC"
    WEBHOOK = "WEBHOOK"
    EVENT_DRIVEN = "EVENT_DRIVEN"
    BATCH_PROCESSING = "BATCH_PROCESSING"
class DataFormat(Enum):
    JSON = "JSON"
    XML = "XML"
    HL7 = "HL7"
    DICOM = "DICOM"
    CSV = "CSV"
    PDF = "PDF"
    FHIR_JSON = "FHIR_JSON"
    FHIR_XML = "FHIR_XML"
@dataclass
class IntegrationConfig:
    name: str
    integration_type: IntegrationType
    base_url: str
    auth_method: str = "bearer_token"
    timeout: int = 30
    retry_attempts: int = 3
    rate_limit: int = 1000  
    standards: List[IntegrationStandards] = field(default_factory=list)
    data_formats: List[DataFormat] = field(default_factory=list)
    enabled: bool = True
    health_check_endpoint: Optional[str] = None
    circuit_breaker_threshold: int = 5
class IntegrationHealthStatus(Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"
@dataclass
class IntegrationHealth:
    endpoint_name: str
    status: IntegrationHealthStatus
    response_time: float
    last_check: datetime
    error_message: Optional[str] = None
    success_rate: float = 1.0
class IntegrationOrchestrator:
    def __init__(self):
        self.integrations: Dict[str, IntegrationConfig] = {}
        self.health_status: Dict[str, IntegrationHealth] = {}
        self.circuit_breakers: Dict[str, Dict] = {}
        self.rate_limiters: Dict[str, Dict] = {}
        self.redis_client: Optional[redis.Redis] = None
        self.db_engine: Optional[Any] = None
    async def initialize(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = redis.from_url(redis_url)
        db_url = os.getenv("INTEGRATION_DB_URL", "postgresql+asyncpg://hms:hms@localhost:5432/integration")
        self.db_engine = create_async_engine(db_url)
        await self._load_integrations()
        asyncio.create_task(self._health_monitor_loop())
        logger.info("Integration Orchestrator initialized successfully")
    async def _load_integrations(self):
        self.integrations = {
            "fhir_server": IntegrationConfig(
                name="FHIR Server",
                integration_type=IntegrationType.API_BASED,
                base_url=os.getenv("FHIR_SERVER_URL", "http://localhost:8080/fhir"),
                standards=[IntegrationStandards.FHIR_R4],
                data_formats=[DataFormat.FHIR_JSON, DataFormat.FHIR_XML],
                health_check_endpoint="/fhir/metadata"
            ),
            "hl7_interface": IntegrationConfig(
                name="HL7 Interface Engine",
                integration_type=IntegrationType.MESSAGE_QUEUE,
                base_url=os.getenv("HL7_INTERFACE_URL", "http://localhost:8081"),
                standards=[IntegrationStandards.HL7_V2],
                data_formats=[DataFormat.HL7]
            ),
            "pacs_server": IntegrationConfig(
                name="PACS Server",
                integration_type=IntegrationType.API_BASED,
                base_url=os.getenv("PACS_SERVER_URL", "http://localhost:8082"),
                standards=[IntegrationStandards.DICOM],
                data_formats=[DataFormat.DICOM],
                health_check_endpoint="/dicom/qido"
            ),
            "lis_system": IntegrationConfig(
                name="Laboratory Information System",
                integration_type=IntegrationType.DATABASE_SYNC,
                base_url=os.getenv("LIS_SYSTEM_URL", "http://localhost:8083"),
                standards=[IntegrationStandards.HL7_V2, IntegrationStandards.LOINC],
                data_formats=[DataFormat.HL7, DataFormat.JSON]
            ),
            "ris_system": IntegrationConfig(
                name="Radiology Information System",
                integration_type=IntegrationType.API_BASED,
                base_url=os.getenv("RIS_SYSTEM_URL", "http://localhost:8084"),
                standards=[IntegrationStandards.HL7_V2, IntegrationStandards.DICOM],
                data_formats=[DataFormat.HL7, DataFormat.JSON]
            ),
            "emr_interface": IntegrationConfig(
                name="External EMR Interface",
                integration_type=IntegrationType.EVENT_DRIVEN,
                base_url=os.getenv("EMR_INTERFACE_URL", "http://localhost:8085"),
                standards=[IntegrationStandards.FHIR_R4, IntegrationStandards.HL7_V2],
                data_formats=[DataFormat.FHIR_JSON, DataFormat.HL7]
            ),
            "billing_interface": IntegrationConfig(
                name="Billing System Interface",
                integration_type=IntegrationType.API_BASED,
                base_url=os.getenv("BILLING_INTERFACE_URL", "http://localhost:8086"),
                standards=[IntegrationStandards.HL7_V2],
                data_formats=[DataFormat.JSON, DataFormat.HL7]
            ),
            "pharmacy_interface": IntegrationConfig(
                name="Pharmacy Management System",
                integration_type=IntegrationType.MESSAGE_QUEUE,
                base_url=os.getenv("PHARMACY_INTERFACE_URL", "http://localhost:8087"),
                standards=[IntegrationStandards.HL7_V2, IntegrationStandards.NDC],
                data_formats=[DataFormat.HL7, DataFormat.JSON]
            )
        }
        for name, config in self.integrations.items():
            self.health_status[name] = IntegrationHealth(
                endpoint_name=name,
                status=IntegrationHealthStatus.UNKNOWN,
                response_time=0.0,
                last_check=datetime.now()
            )
            self.circuit_breakers[name] = {
                "failure_count": 0,
                "last_failure": None,
                "state": "CLOSED"  
            }
            self.rate_limiters[name] = {
                "requests": 0,
                "reset_time": datetime.now() + timedelta(hours=1)
            }
    async def _health_monitor_loop(self):
        while True:
            try:
                await self._check_all_integrations_health()
                await asyncio.sleep(60)  
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(30)
    async def _check_all_integrations_health(self):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for name, config in self.integrations.items():
                if config.enabled and config.health_check_endpoint:
                    tasks.append(self._check_integration_health(session, name, config))
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    async def _check_integration_health(self, session: aiohttp.ClientSession, name: str, config: IntegrationConfig):
        try:
            start_time = datetime.now()
            health_url = config.base_url + config.health_check_endpoint
            async with session.get(health_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response_time = (datetime.now() - start_time).total_seconds()
                if response.status == 200:
                    self.health_status[name] = IntegrationHealth(
                        endpoint_name=name,
                        status=IntegrationHealthStatus.HEALTHY,
                        response_time=response_time,
                        last_check=datetime.now()
                    )
                    if self.circuit_breakers[name]["state"] == "HALF_OPEN":
                        self.circuit_breakers[name]["state"] = "CLOSED"
                        self.circuit_breakers[name]["failure_count"] = 0
                else:
                    self.health_status[name] = IntegrationHealth(
                        endpoint_name=name,
                        status=IntegrationHealthStatus.UNHEALTHY,
                        response_time=response_time,
                        last_check=datetime.now(),
                        error_message=f"HTTP {response.status}"
                    )
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            self.health_status[name] = IntegrationHealth(
                endpoint_name=name,
                status=IntegrationHealthStatus.UNHEALTHY,
                response_time=response_time,
                last_check=datetime.now(),
                error_message=str(e)
            )
            self.circuit_breakers[name]["failure_count"] += 1
            self.circuit_breakers[name]["last_failure"] = datetime.now()
            if self.circuit_breakers[name]["failure_count"] >= config.circuit_breaker_threshold:
                self.circuit_breakers[name]["state"] = "OPEN"
    async def check_rate_limit(self, integration_name: str) -> bool:
        if integration_name not in self.rate_limiters:
            return True
        limiter = self.rate_limiters[integration_name]
        config = self.integrations[integration_name]
        if datetime.now() > limiter["reset_time"]:
            limiter["requests"] = 0
            limiter["reset_time"] = datetime.now() + timedelta(hours=1)
        if limiter["requests"] >= config.rate_limit:
            return False
        limiter["requests"] += 1
        return True
    async def execute_integration_request(self, integration_name: str, method: str,
                                        endpoint: str, data: Optional[Dict] = None,
                                        headers: Optional[Dict] = None) -> Dict:
        if integration_name not in self.integrations:
            raise HTTPException(status_code=404, detail=f"Integration {integration_name} not found")
        config = self.integrations[integration_name]
        if not config.enabled:
            raise HTTPException(status_code=503, detail=f"Integration {integration_name} is disabled")
        circuit_state = self.circuit_breakers[integration_name]["state"]
        if circuit_state == "OPEN":
            raise HTTPException(status_code=503, detail=f"Integration {integration_name} is temporarily unavailable")
        if not await self.check_rate_limit(integration_name):
            raise HTTPException(status_code=429, detail=f"Rate limit exceeded for {integration_name}")
        try:
            async with aiohttp.ClientSession() as session:
                url = config.base_url + endpoint
                request_headers = {"Content-Type": "application/json"}
                if headers:
                    request_headers.update(headers)
                start_time = datetime.now()
                if method.upper() == "GET":
                    async with session.get(url, headers=request_headers, timeout=aiohttp.ClientTimeout(total=config.timeout)) as response:
                        result = await response.json()
                        response_time = (datetime.now() - start_time).total_seconds()
                elif method.upper() == "POST":
                    async with session.post(url, json=data, headers=request_headers, timeout=aiohttp.ClientTimeout(total=config.timeout)) as response:
                        result = await response.json()
                        response_time = (datetime.now() - start_time).total_seconds()
                elif method.upper() == "PUT":
                    async with session.put(url, json=data, headers=request_headers, timeout=aiohttp.ClientTimeout(total=config.timeout)) as response:
                        result = await response.json()
                        response_time = (datetime.now() - start_time).total_seconds()
                else:
                    raise HTTPException(status_code=400, detail=f"Unsupported method: {method}")
                self.health_status[integration_name] = IntegrationHealth(
                    endpoint_name=integration_name,
                    status=IntegrationHealthStatus.HEALTHY,
                    response_time=response_time,
                    last_check=datetime.now()
                )
                if circuit_state == "HALF_OPEN":
                    self.circuit_breakers[integration_name]["state"] = "CLOSED"
                    self.circuit_breakers[integration_name]["failure_count"] = 0
                return result
        except Exception as e:
            self.circuit_breakers[integration_name]["failure_count"] += 1
            self.circuit_breakers[integration_name]["last_failure"] = datetime.now()
            if self.circuit_breakers[integration_name]["failure_count"] >= config.circuit_breaker_threshold:
                self.circuit_breakers[integration_name]["state"] = "OPEN"
            logger.error(f"Integration request failed: {integration_name} - {str(e)}")
            raise HTTPException(status_code=502, detail=f"Integration request failed: {str(e)}")
    def get_integration_status(self) -> Dict[str, Any]:
        return {
            "integrations": {
                name: {
                    "config": {
                        "name": config.name,
                        "type": config.integration_type.value,
                        "enabled": config.enabled,
                        "standards": [s.value for s in config.standards],
                        "base_url": config.base_url
                    },
                    "health": {
                        "status": health.status.value,
                        "response_time": health.response_time,
                        "last_check": health.last_check.isoformat(),
                        "error_message": health.error_message
                    },
                    "circuit_breaker": self.circuit_breakers[name],
                    "rate_limit": {
                        "requests": self.rate_limiters[name]["requests"],
                        "limit": self.integrations[name].rate_limit,
                        "reset_time": self.rate_limiters[name]["reset_time"].isoformat()
                    }
                }
                for name, config in self.integrations.items()
                for health in [self.health_status[name]]
            },
            "summary": {
                "total_integrations": len(self.integrations),
                "healthy": sum(1 for h in self.health_status.values() if h.status == IntegrationHealthStatus.HEALTHY),
                "unhealthy": sum(1 for h in self.health_status.values() if h.status == IntegrationHealthStatus.UNHEALTHY),
                "degraded": sum(1 for h in self.health_status.values() if h.status == IntegrationHealthStatus.DEGRADED)
            }
        }
    async def graceful_shutdown(self):
        if self.redis_client:
            await self.redis_client.close()
        if self.db_engine:
            await self.db_engine.dispose()
        logger.info("Integration Orchestrator shutdown complete")
orchestrator = IntegrationOrchestrator()
async def get_orchestrator() -> IntegrationOrchestrator:
    return orchestrator
integration_app = FastAPI(
    title="HMS Integration Orchestrator",
    description="Comprehensive healthcare integration management system",
    version="1.0.0"
)
integration_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@integration_app.on_event("startup")
async def startup_event():
    await orchestrator.initialize()
@integration_app.on_event("shutdown")
async def shutdown_event():
    await orchestrator.graceful_shutdown()
@integration_app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
@integration_app.get("/integrations/status")
async def get_integrations_status():
    return orchestrator.get_integration_status()
@integration_app.post("/integrations/{integration_name}/execute")
async def execute_integration(
    integration_name: str,
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    orchestrator: IntegrationOrchestrator = Depends(get_orchestrator)
):
    return await orchestrator.execute_integration_request(
        integration_name, method, endpoint, data, headers
    )
@integration_app.post("/integrations/{integration_name}/reset-circuit-breaker")
async def reset_circuit_breaker(
    integration_name: str,
    orchestrator: IntegrationOrchestrator = Depends(get_orchestrator)
):
    if integration_name not in orchestrator.circuit_breakers:
        raise HTTPException(status_code=404, detail="Integration not found")
    orchestrator.circuit_breakers[integration_name] = {
        "failure_count": 0,
        "last_failure": None,
        "state": "CLOSED"
    }
    return {"status": "circuit breaker reset"}
@integration_app.get("/integrations/{integration_name}/health")
async def get_integration_health(
    integration_name: str,
    orchestrator: IntegrationOrchestrator = Depends(get_orchestrator)
):
    if integration_name not in orchestrator.health_status:
        raise HTTPException(status_code=404, detail="Integration not found")
    health = orchestrator.health_status[integration_name]
    return {
        "name": integration_name,
        "status": health.status.value,
        "response_time": health.response_time,
        "last_check": health.last_check.isoformat(),
        "error_message": health.error_message
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(integration_app, host="0.0.0.0", port=8000)