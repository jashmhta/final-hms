from .dicom_integration import (
    DICOMIntegration,
    DICOMServiceType,
    ImageModality,
    ImageCompression,
    ImageQuality,
    DICOMMetadata,
    ImageStorageConfig,
    DICOMStudy,
    DICOMSeries,
    DICOMInstance,
    DICOMAssociation,
    DICOMQuery,
    DICOMAuditLog
)
from .dicom_config import (
    DICOMConfigurationManager,
    DICOMFullConfig,
    DICOMServerConfig,
    DICOMStorageConfig,
    DICOMSecurityConfig,
    DICOMIntegrationConfig,
    DICOMPerformanceConfig,
    DICOMMonitoringConfig,
    get_config_manager,
    get_config
)
__version__ = "1.0.0"
__author__ = "Integration Specialist"
__email__ = "integration@hms-enterprise.com"
__all__ = [
    "DICOMIntegration",
    "DICOMServiceType",
    "ImageModality",
    "ImageCompression",
    "ImageQuality",
    "DICOMMetadata",
    "ImageStorageConfig",
    "DICOMStudy",
    "DICOMSeries",
    "DICOMInstance",
    "DICOMAssociation",
    "DICOMQuery",
    "DICOMAuditLog",
    "DICOMConfigurationManager",
    "DICOMFullConfig",
    "DICOMServerConfig",
    "DICOMStorageConfig",
    "DICOMSecurityConfig",
    "DICOMIntegrationConfig",
    "DICOMPerformanceConfig",
    "DICOMMonitoringConfig",
    "get_config_manager",
    "get_config"
]
import logging
def configure_logging(log_level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('/var/log/hms/dicom.log')
        ]
    )
configure_logging()
logger = logging.getLogger(__name__)
logger.info(f"DICOM Integration Package initialized (v{__version__})")