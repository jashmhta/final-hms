import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from .dicom_integration import ImageCompression, ImageQuality
class DICOMNetworkConfig(Enum):
    DEFAULT = "DEFAULT"
    HIGH_PERFORMANCE = "HIGH_PERFORMANCE"
    SECURE = "SECURE"
    LEGACY = "LEGACY"
class DICOMSecurityLevel(Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    RESTRICTED = "RESTRICTED"
    CONFIDENTIAL = "CONFIDENTIAL"
    HIGHLY_RESTRICTED = "HIGHLY_RESTRICTED"
class StoragePolicy(Enum):
    STANDARD = "STANDARD"
    OPTIMIZED = "OPTIMIZED"
    HIGH_DENSITY = "HIGH_DENSITY"
    ARCHIVAL = "ARCHIVAL"
@dataclass
class DICOMServerConfig:
    aet_title: str = "HMS_PACS"
    port: int = 11112
    max_pdu_size: int = 16384
    timeout: int = 30
    max_associations: int = 50
    supported_transfer_syntaxes: List[str] = field(default_factory=lambda: [
        "1.2.840.10008.1.2.1",  
        "1.2.840.10008.1.2.2",  
        "1.2.840.10008.1.2.5",  
        "1.2.840.10008.1.2.4.50",  
        "1.2.840.10008.1.2.4.57",  
        "1.2.840.10008.1.2.4.70",  
        "1.2.840.10008.1.2.4.80",  
        "1.2.840.10008.1.2.4.90",  
        "1.2.840.10008.1.2.4.91",  
    ])
    supported_sop_classes: List[str] = field(default_factory=lambda: [
        "1.2.840.10008.5.1.4.1.1.2",  
        "1.2.840.10008.5.1.4.1.1.4",  
        "1.2.840.10008.5.1.4.1.1.6.1",  
        "1.2.840.10008.5.1.4.1.1.7",  
        "1.2.840.10008.5.1.4.1.1.88.67",  
        "1.2.840.10008.5.1.4.1.1.88.11",  
        "1.2.840.10008.5.1.4.1.1.88.22",  
        "1.2.840.10008.5.1.4.1.1.88.33",  
        "1.2.840.10008.5.1.4.1.1.9.1.1",  
        "1.2.840.10008.5.1.4.1.1.9.1.3",  
        "1.2.840.10008.5.1.4.1.1.9.2.1",  
        "1.2.840.10008.5.1.4.1.1.9.3.1",  
        "1.2.840.10008.5.1.4.1.1.9.4.1",  
        "1.2.840.10008.5.1.4.1.1.9.5.1",  
        "1.2.840.10008.5.1.4.1.1.9.6.1",  
        "1.2.840.10008.5.1.4.1.1.9.7.1",  
        "1.2.840.10008.5.1.4.1.1.9.8.1",  
        "1.2.840.10008.5.1.4.1.1.9.9.1",  
        "1.2.840.10008.5.1.4.1.1.9.10.1",  
        "1.2.840.10008.5.1.4.1.1.9.11.1",  
        "1.2.840.10008.5.1.4.1.1.9.12.1",  
        "1.2.840.10008.5.1.4.1.1.9.13.1",  
        "1.2.840.10008.5.1.4.1.1.9.14.1",  
        "1.2.840.10008.5.1.4.1.1.9.15.1",  
        "1.2.840.10008.5.1.4.1.1.9.16.1",  
        "1.2.840.10008.5.1.4.1.1.9.17.1",  
        "1.2.840.10008.5.1.4.1.1.9.18.1",  
        "1.2.840.10008.5.1.4.1.1.9.19.1",  
        "1.2.840.10008.5.1.4.1.1.9.20.1",  
        "1.2.840.10008.5.1.4.1.1.9.21.1",  
        "1.2.840.10008.5.1.4.1.1.9.22.1",  
        "1.2.840.10008.5.1.4.1.1.9.23.1",  
        "1.2.840.10008.5.1.4.1.1.9.24.1",  
    ])
    enabled_services: List[str] = field(default_factory=lambda: [
        "verification_scp",
        "storage_scp",
        "query_retrieve_scp",
        "worklist_scp",
        "mpps_scp",
        "storage_commitment_scp"
    ])
@dataclass
class DICOMStorageConfig:
    base_path: str = "/var/lib/dicom"
    compression: ImageCompression = ImageCompression.JPEG2000
    quality: ImageQuality = ImageQuality.HIGH
    storage_policy: StoragePolicy = StoragePolicy.OPTIMIZED
    enable_versioning: bool = True
    enable_deduplication: bool = True
    enable_compression: bool = True
    enable_thumbnails: bool = True
    compression_ratio: float = 0.8
    thumbnail_size: tuple = (128, 128)
    max_file_size_mb: int = 1000
    max_study_size_gb: int = 10
    retention_days: int = 3650
    backup_enabled: bool = True
    backup_retention_days: int = 90
    archive_enabled: bool = True
    archive_retention_days: int = 3650
@dataclass
class DICOMSecurityConfig:
    security_level: DICOMSecurityLevel = DICOMSecurityLevel.RESTRICTED
    enable_encryption: bool = True
    enable_audit_logging: bool = True
    enable_access_control: bool = True
    allowed_ip_ranges: List[str] = field(default_factory=lambda: ["127.0.0.1", "::1"])
    max_connection_attempts: int = 5
    connection_timeout: int = 30
    session_timeout: int = 3600
    require_authentication: bool = True
    require_authorization: bool = True
    audit_log_retention_days: int = 90
    tls_enabled: bool = True
    tls_cert_path: str = "/etc/ssl/certs/dicom.crt"
    tls_key_path: str = "/etc/ssl/private/dicom.key"
    tls_ca_path: str = "/etc/ssl/certs/ca.crt"
@dataclass
class DICOMIntegrationConfig:
    fhir_integration: bool = True
    fhir_server_url: str = "http://localhost:8080/fhir"
    hl7_integration: bool = True
    hl7_server_url: str = "http://localhost:8081"
    enable_web_services: bool = True
    web_services_port: int = 8084
    enable_pacs_integration: bool = True
    pacs_servers: List[Dict] = field(default_factory=list)
    enable_ris_integration: bool = True
    ris_server_url: str = "http://localhost:8085"
    enable_lis_integration: bool = True
    lis_server_url: str = "http://localhost:8083"
    enable_his_integration: bool = True
    his_server_url: str = "http://localhost:8000"
    enable_emr_integration: bool = True
    emr_server_url: str = "http://localhost:8002"
    enable_viewer_integration: bool = True
    viewer_url: str = "http://localhost:8086"
    enable_ai_integration: bool = True
    ai_server_url: str = "http://localhost:8087"
@dataclass
class DICOMPerformanceConfig:
    max_concurrent_connections: int = 100
    max_concurrent_transfers: int = 20
    transfer_chunk_size: int = 8192
    cache_size_mb: int = 1024
    cache_ttl: int = 3600
    enable_caching: bool = True
    enable_compression: bool = True
    enable_async_processing: bool = True
    worker_threads: int = 4
    io_threads: int = 2
    network_timeout: int = 30
    disk_io_timeout: int = 60
    max_processing_time: int = 300
    enable_load_balancing: bool = True
    load_balancer_strategy: str = "round_robin"
@dataclass
class DICOMMonitoringConfig:
    enable_health_checks: bool = True
    health_check_interval: int = 30
    enable_metrics_collection: bool = True
    metrics_collection_interval: int = 60
    enable_performance_monitoring: bool = True
    enable_error_tracking: bool = True
    enable_alerting: bool = True
    alert_email: str = "admin@hms.com"
    alert_webhook: str = ""
    max_alerts_per_hour: int = 10
    log_level: str = "INFO"
    log_retention_days: int = 30
    enable_real_time_monitoring: bool = True
    monitoring_dashboard_url: str = "http://localhost:3000"
@dataclass
class DICOMFullConfig:
    server: DICOMServerConfig = field(default_factory=DICOMServerConfig)
    storage: DICOMStorageConfig = field(default_factory=DICOMStorageConfig)
    security: DICOMSecurityConfig = field(default_factory=DICOMSecurityConfig)
    integration: DICOMIntegrationConfig = field(default_factory=DICOMIntegrationConfig)
    performance: DICOMPerformanceConfig = field(default_factory=DICOMPerformanceConfig)
    monitoring: DICOMMonitoringConfig = field(default_factory=DICOMMonitoringConfig)
class DICOMConfigurationManager:
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or os.getenv("DICOM_CONFIG_FILE", "/etc/dicom/config.yaml")
        self.config = DICOMFullConfig()
        self.load_configuration()
    def load_configuration(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                        config_data = yaml.safe_load(f)
                    else:
                        config_data = json.load(f)
                self.config = self._parse_config_data(config_data)
                logger.info(f"Configuration loaded from {self.config_file}")
            else:
                logger.info(f"Configuration file not found, using defaults")
                self.save_configuration()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
    def save_configuration(self):
        try:
            config_data = self._config_to_dict()
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                    yaml.dump(config_data, f, default_flow_style=False, indent=2)
                else:
                    json.dump(config_data, f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise
    def _parse_config_data(self, config_data: Dict) -> DICOMFullConfig:
        config = DICOMFullConfig()
        if 'server' in config_data:
            server_data = config_data['server']
            config.server = DICOMServerConfig(
                aet_title=server_data.get('aet_title', 'HMS_PACS'),
                port=server_data.get('port', 11112),
                max_pdu_size=server_data.get('max_pdu_size', 16384),
                timeout=server_data.get('timeout', 30),
                max_associations=server_data.get('max_associations', 50),
                supported_transfer_syntaxes=server_data.get('supported_transfer_syntaxes', config.server.supported_transfer_syntaxes),
                supported_sop_classes=server_data.get('supported_sop_classes', config.server.supported_sop_classes),
                enabled_services=server_data.get('enabled_services', config.server.enabled_services)
            )
        if 'storage' in config_data:
            storage_data = config_data['storage']
            config.storage = DICOMStorageConfig(
                base_path=storage_data.get('base_path', '/var/lib/dicom'),
                compression=ImageCompression(storage_data.get('compression', 'JPEG2000')),
                quality=ImageQuality(storage_data.get('quality', 'HIGH')),
                storage_policy=StoragePolicy(storage_data.get('storage_policy', 'OPTIMIZED')),
                enable_versioning=storage_data.get('enable_versioning', True),
                enable_deduplication=storage_data.get('enable_deduplication', True),
                enable_compression=storage_data.get('enable_compression', True),
                enable_thumbnails=storage_data.get('enable_thumbnails', True),
                compression_ratio=storage_data.get('compression_ratio', 0.8),
                thumbnail_size=tuple(storage_data.get('thumbnail_size', [128, 128])),
                max_file_size_mb=storage_data.get('max_file_size_mb', 1000),
                max_study_size_gb=storage_data.get('max_study_size_gb', 10),
                retention_days=storage_data.get('retention_days', 3650),
                backup_enabled=storage_data.get('backup_enabled', True),
                backup_retention_days=storage_data.get('backup_retention_days', 90),
                archive_enabled=storage_data.get('archive_enabled', True),
                archive_retention_days=storage_data.get('archive_retention_days', 3650)
            )
        if 'security' in config_data:
            security_data = config_data['security']
            config.security = DICOMSecurityConfig(
                security_level=DICOMSecurityLevel(security_data.get('security_level', 'RESTRICTED')),
                enable_encryption=security_data.get('enable_encryption', True),
                enable_audit_logging=security_data.get('enable_audit_logging', True),
                enable_access_control=security_data.get('enable_access_control', True),
                allowed_ip_ranges=security_data.get('allowed_ip_ranges', ['127.0.0.1', '::1']),
                max_connection_attempts=security_data.get('max_connection_attempts', 5),
                connection_timeout=security_data.get('connection_timeout', 30),
                session_timeout=security_data.get('session_timeout', 3600),
                require_authentication=security_data.get('require_authentication', True),
                require_authorization=security_data.get('require_authorization', True),
                audit_log_retention_days=security_data.get('audit_log_retention_days', 90),
                tls_enabled=security_data.get('tls_enabled', True),
                tls_cert_path=security_data.get('tls_cert_path', '/etc/ssl/certs/dicom.crt'),
                tls_key_path=security_data.get('tls_key_path', '/etc/ssl/private/dicom.key'),
                tls_ca_path=security_data.get('tls_ca_path', '/etc/ssl/certs/ca.crt')
            )
        if 'integration' in config_data:
            integration_data = config_data['integration']
            config.integration = DICOMIntegrationConfig(
                fhir_integration=integration_data.get('fhir_integration', True),
                fhir_server_url=integration_data.get('fhir_server_url', 'http://localhost:8080/fhir'),
                hl7_integration=integration_data.get('hl7_integration', True),
                hl7_server_url=integration_data.get('hl7_server_url', 'http://localhost:8081'),
                enable_web_services=integration_data.get('enable_web_services', True),
                web_services_port=integration_data.get('web_services_port', 8084),
                enable_pacs_integration=integration_data.get('enable_pacs_integration', True),
                pacs_servers=integration_data.get('pacs_servers', []),
                enable_ris_integration=integration_data.get('enable_ris_integration', True),
                ris_server_url=integration_data.get('ris_server_url', 'http://localhost:8085'),
                enable_lis_integration=integration_data.get('enable_lis_integration', True),
                lis_server_url=integration_data.get('lis_server_url', 'http://localhost:8083'),
                enable_his_integration=integration_data.get('enable_his_integration', True),
                his_server_url=integration_data.get('his_server_url', 'http://localhost:8000'),
                enable_emr_integration=integration_data.get('enable_emr_integration', True),
                emr_server_url=integration_data.get('emr_server_url', 'http://localhost:8002'),
                enable_viewer_integration=integration_data.get('enable_viewer_integration', True),
                viewer_url=integration_data.get('viewer_url', 'http://localhost:8086'),
                enable_ai_integration=integration_data.get('enable_ai_integration', True),
                ai_server_url=integration_data.get('ai_server_url', 'http://localhost:8087')
            )
        if 'performance' in config_data:
            performance_data = config_data['performance']
            config.performance = DICOMPerformanceConfig(
                max_concurrent_connections=performance_data.get('max_concurrent_connections', 100),
                max_concurrent_transfers=performance_data.get('max_concurrent_transfers', 20),
                transfer_chunk_size=performance_data.get('transfer_chunk_size', 8192),
                cache_size_mb=performance_data.get('cache_size_mb', 1024),
                cache_ttl=performance_data.get('cache_ttl', 3600),
                enable_caching=performance_data.get('enable_caching', True),
                enable_compression=performance_data.get('enable_compression', True),
                enable_async_processing=performance_data.get('enable_async_processing', True),
                worker_threads=performance_data.get('worker_threads', 4),
                io_threads=performance_data.get('io_threads', 2),
                network_timeout=performance_data.get('network_timeout', 30),
                disk_io_timeout=performance_data.get('disk_io_timeout', 60),
                max_processing_time=performance_data.get('max_processing_time', 300),
                enable_load_balancing=performance_data.get('enable_load_balancing', True),
                load_balancer_strategy=performance_data.get('load_balancer_strategy', 'round_robin')
            )
        if 'monitoring' in config_data:
            monitoring_data = config_data['monitoring']
            config.monitoring = DICOMMonitoringConfig(
                enable_health_checks=monitoring_data.get('enable_health_checks', True),
                health_check_interval=monitoring_data.get('health_check_interval', 30),
                enable_metrics_collection=monitoring_data.get('enable_metrics_collection', True),
                metrics_collection_interval=monitoring_data.get('metrics_collection_interval', 60),
                enable_performance_monitoring=monitoring_data.get('enable_performance_monitoring', True),
                enable_error_tracking=monitoring_data.get('enable_error_tracking', True),
                enable_alerting=monitoring_data.get('enable_alerting', True),
                alert_email=monitoring_data.get('alert_email', 'admin@hms.com'),
                alert_webhook=monitoring_data.get('alert_webhook', ''),
                max_alerts_per_hour=monitoring_data.get('max_alerts_per_hour', 10),
                log_level=monitoring_data.get('log_level', 'INFO'),
                log_retention_days=monitoring_data.get('log_retention_days', 30),
                enable_real_time_monitoring=monitoring_data.get('enable_real_time_monitoring', True),
                monitoring_dashboard_url=monitoring_data.get('monitoring_dashboard_url', 'http://localhost:3000')
            )
        return config
    def _config_to_dict(self) -> Dict:
        return {
            'server': {
                'aet_title': self.config.server.aet_title,
                'port': self.config.server.port,
                'max_pdu_size': self.config.server.max_pdu_size,
                'timeout': self.config.server.timeout,
                'max_associations': self.config.server.max_associations,
                'supported_transfer_syntaxes': self.config.server.supported_transfer_syntaxes,
                'supported_sop_classes': self.config.server.supported_sop_classes,
                'enabled_services': self.config.server.enabled_services
            },
            'storage': {
                'base_path': self.config.storage.base_path,
                'compression': self.config.storage.compression.value,
                'quality': self.config.storage.quality.value,
                'storage_policy': self.config.storage.storage_policy.value,
                'enable_versioning': self.config.storage.enable_versioning,
                'enable_deduplication': self.config.storage.enable_deduplication,
                'enable_compression': self.config.storage.enable_compression,
                'enable_thumbnails': self.config.storage.enable_thumbnails,
                'compression_ratio': self.config.storage.compression_ratio,
                'thumbnail_size': list(self.config.storage.thumbnail_size),
                'max_file_size_mb': self.config.storage.max_file_size_mb,
                'max_study_size_gb': self.config.storage.max_study_size_gb,
                'retention_days': self.config.storage.retention_days,
                'backup_enabled': self.config.storage.backup_enabled,
                'backup_retention_days': self.config.storage.backup_retention_days,
                'archive_enabled': self.config.storage.archive_enabled,
                'archive_retention_days': self.config.storage.archive_retention_days
            },
            'security': {
                'security_level': self.config.security.security_level.value,
                'enable_encryption': self.config.security.enable_encryption,
                'enable_audit_logging': self.config.security.enable_audit_logging,
                'enable_access_control': self.config.security.enable_access_control,
                'allowed_ip_ranges': self.config.security.allowed_ip_ranges,
                'max_connection_attempts': self.config.security.max_connection_attempts,
                'connection_timeout': self.config.security.connection_timeout,
                'session_timeout': self.config.security.session_timeout,
                'require_authentication': self.config.security.require_authentication,
                'require_authorization': self.config.security.require_authorization,
                'audit_log_retention_days': self.config.security.audit_log_retention_days,
                'tls_enabled': self.config.security.tls_enabled,
                'tls_cert_path': self.config.security.tls_cert_path,
                'tls_key_path': self.config.security.tls_key_path,
                'tls_ca_path': self.config.security.tls_ca_path
            },
            'integration': {
                'fhir_integration': self.config.integration.fhir_integration,
                'fhir_server_url': self.config.integration.fhir_server_url,
                'hl7_integration': self.config.integration.hl7_integration,
                'hl7_server_url': self.config.integration.hl7_server_url,
                'enable_web_services': self.config.integration.enable_web_services,
                'web_services_port': self.config.integration.web_services_port,
                'enable_pacs_integration': self.config.integration.enable_pacs_integration,
                'pacs_servers': self.config.integration.pacs_servers,
                'enable_ris_integration': self.config.integration.enable_ris_integration,
                'ris_server_url': self.config.integration.ris_server_url,
                'enable_lis_integration': self.config.integration.enable_lis_integration,
                'lis_server_url': self.config.integration.lis_server_url,
                'enable_his_integration': self.config.integration.enable_his_integration,
                'his_server_url': self.config.integration.his_server_url,
                'enable_emr_integration': self.config.integration.enable_emr_integration,
                'emr_server_url': self.config.integration.emr_server_url,
                'enable_viewer_integration': self.config.integration.enable_viewer_integration,
                'viewer_url': self.config.integration.viewer_url,
                'enable_ai_integration': self.config.integration.enable_ai_integration,
                'ai_server_url': self.config.integration.ai_server_url
            },
            'performance': {
                'max_concurrent_connections': self.config.performance.max_concurrent_connections,
                'max_concurrent_transfers': self.config.performance.max_concurrent_transfers,
                'transfer_chunk_size': self.config.performance.transfer_chunk_size,
                'cache_size_mb': self.config.performance.cache_size_mb,
                'cache_ttl': self.config.performance.cache_ttl,
                'enable_caching': self.config.performance.enable_caching,
                'enable_compression': self.config.performance.enable_compression,
                'enable_async_processing': self.config.performance.enable_async_processing,
                'worker_threads': self.config.performance.worker_threads,
                'io_threads': self.config.performance.io_threads,
                'network_timeout': self.config.performance.network_timeout,
                'disk_io_timeout': self.config.performance.disk_io_timeout,
                'max_processing_time': self.config.performance.max_processing_time,
                'enable_load_balancing': self.config.performance.enable_load_balancing,
                'load_balancer_strategy': self.config.performance.load_balancer_strategy
            },
            'monitoring': {
                'enable_health_checks': self.config.monitoring.enable_health_checks,
                'health_check_interval': self.config.monitoring.health_check_interval,
                'enable_metrics_collection': self.config.monitoring.enable_metrics_collection,
                'metrics_collection_interval': self.config.monitoring.metrics_collection_interval,
                'enable_performance_monitoring': self.config.monitoring.enable_performance_monitoring,
                'enable_error_tracking': self.config.monitoring.enable_error_tracking,
                'enable_alerting': self.config.monitoring.enable_alerting,
                'alert_email': self.config.monitoring.alert_email,
                'alert_webhook': self.config.monitoring.alert_webhook,
                'max_alerts_per_hour': self.config.monitoring.max_alerts_per_hour,
                'log_level': self.config.monitoring.log_level,
                'log_retention_days': self.config.monitoring.log_retention_days,
                'enable_real_time_monitoring': self.config.monitoring.enable_real_time_monitoring,
                'monitoring_dashboard_url': self.config.monitoring.monitoring_dashboard_url
            }
        }
    def get_config(self) -> DICOMFullConfig:
        return self.config
    def update_config(self, config_data: Dict):
        try:
            new_config = self._parse_config_data(config_data)
            self.config = new_config
            self.save_configuration()
            logger.info("Configuration updated successfully")
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            raise
    def get_environment_config(self) -> Dict:
        return {
            'DICOM_AET': self.config.server.aet_title,
            'DICOM_PORT': self.config.server.port,
            'DICOM_STORAGE_PATH': self.config.storage.base_path,
            'DICOM_DB_URL': os.getenv('DICOM_DB_URL', 'postgresql+asyncpg://hms:hms@localhost:5432/dicom'),
            'REDIS_URL': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
            'DICOM_CONFIG_FILE': self.config_file,
            'DICOM_SECURITY_LEVEL': self.config.security.security_level.value,
            'DICOM_LOG_LEVEL': self.config.monitoring.log_level
        }
    def validate_configuration(self) -> bool:
        try:
            if not os.path.exists(self.config.storage.base_path):
                logger.warning(f"Storage path does not exist: {self.config.storage.base_path}")
            if not (1 <= self.config.server.port <= 65535):
                raise ValueError(f"Invalid port number: {self.config.server.port}")
            if self.config.security.tls_enabled:
                if not os.path.exists(self.config.security.tls_cert_path):
                    logger.warning(f"TLS certificate file not found: {self.config.security.tls_cert_path}")
                if not os.path.exists(self.config.security.tls_key_path):
                    logger.warning(f"TLS key file not found: {self.config.security.tls_key_path}")
            if not (0.1 <= self.config.storage.compression_ratio <= 1.0):
                raise ValueError(f"Invalid compression ratio: {self.config.storage.compression_ratio}")
            if self.config.security.connection_timeout <= 0:
                raise ValueError(f"Invalid connection timeout: {self.config.security.connection_timeout}")
            if self.config.performance.max_concurrent_connections <= 0:
                raise ValueError(f"Invalid max concurrent connections: {self.config.performance.max_concurrent_connections}")
            logger.info("Configuration validation passed")
            return True
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    def create_default_config_file(self):
        default_config = DICOMFullConfig()
        config_data = self._config_to_dict()
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            else:
                json.dump(config_data, f, indent=2)
        logger.info(f"Default configuration file created: {self.config_file}")
config_manager = None
def get_config_manager() -> DICOMConfigurationManager:
    global config_manager
    if config_manager is None:
        config_manager = DICOMConfigurationManager()
    return config_manager
def get_config() -> DICOMFullConfig:
    return get_config_manager().get_config()
import logging
logger = logging.getLogger(__name__)