"""
Advanced Database Backup and Recovery System for HMS Enterprise
Automated backups, point-in-time recovery, and disaster recovery
"""

import gzip
import hashlib
import logging
import os
import shutil
import subprocess
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import boto3
import paramiko
import psycopg2
from psycopg2 import sql

from django.conf import settings
from django.core.cache import cache

from .database_monitoring import database_monitor

logger = logging.getLogger(__name__)


class BackupType(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    WAL = "wal"
    SCHEMA = "schema"
    DATA_ONLY = "data_only"


class BackupStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class RecoveryMethod(Enum):
    POINT_IN_TIME = "point_in_time"
    FULL_RESTORE = "full_restore"
    SELECTIVE_RESTORE = "selective_restore"
    CLONE = "clone"


@dataclass
class BackupJob:
    """Backup job data structure"""

    id: str
    backup_type: BackupType
    status: BackupStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    error_message: Optional[str] = None
    retention_days: int = 30


@dataclass
class BackupConfig:
    """Backup configuration"""

    backup_directory: str
    retention_days: int = 30
    compression_enabled: bool = True
    encryption_enabled: bool = True
    s3_enabled: bool = False
    s3_bucket: Optional[str] = None
    s3_region: Optional[str] = None
    remote_backup_enabled: bool = False
    remote_host: Optional[str] = None
    remote_user: Optional[str] = None
    remote_path: Optional[str] = None
    schedule_full: str = "0 2 * * *"  # Daily at 2 AM
    schedule_incremental: str = "0 */6 * * *"  # Every 6 hours
    schedule_wal: str = "*/15 * * * *"  # Every 15 minutes


class DatabaseBackupManager:
    """Advanced database backup and recovery manager"""

    def __init__(self, config: BackupConfig):
        self.config = config
        self.backup_jobs = {}
        self.s3_client = None
        self.ssh_client = None
        self._file_handles = set()
        self._connections = set()
        self._lock = threading.RLock()

        # Initialize S3 client if enabled
        if self.config.s3_enabled:
            self.s3_client = boto3.client(
                "s3",
                region_name=self.config.s3_region,
                aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY"),
            )

        # Initialize SSH client for remote backups
        if self.config.remote_backup_enabled:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Ensure backup directory exists
        os.makedirs(self.config.backup_directory, exist_ok=True)

    def create_full_backup(self) -> BackupJob:
        """Create a full database backup"""
        backup_id = f"full_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        job = BackupJob(
            id=backup_id,
            backup_type=BackupType.FULL,
            status=BackupStatus.PENDING,
            start_time=datetime.now(),
            retention_days=self.config.retention_days,
        )

        try:
            self.backup_jobs[backup_id] = job
            job.status = BackupStatus.IN_PROGRESS

            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hms_full_backup_{timestamp}.sql"
            filepath = os.path.join(self.config.backup_directory, filename)

            # Build pg_dump command
            db_config = self._get_db_config()
            cmd = [
                "pg_dump",
                f"--host={db_config['host']}",
                f"--port={db_config['port']}",
                f"--username={db_config['user']}",
                "--format=custom",
                "--verbose",
                "--file=" + filepath,
                db_config["dbname"],
            ]

            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = db_config["password"]

            # Execute backup
            logger.info(f"Starting full backup: {filename}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=3600)  # 1 hour timeout

            if result.returncode == 0:
                # Process backup file
                if self.config.compression_enabled:
                    compressed_path = filepath + ".gz"
                    with self._managed_file_open(filepath, "rb") as f_in:
                        with gzip.open(compressed_path, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    os.remove(filepath)
                    filepath = compressed_path

                # Calculate checksum
                checksum = self._calculate_checksum(filepath)
                file_size = os.path.getsize(filepath)

                # Update job
                job.file_path = filepath
                job.file_size = file_size
                job.checksum = checksum
                job.status = BackupStatus.COMPLETED
                job.end_time = datetime.now()

                # Upload to remote locations
                self._upload_to_remote(backup_id, filepath)

                logger.info(f"Full backup completed: {filename} ({file_size} bytes)")
            else:
                raise Exception(f"pg_dump failed: {result.stderr}")

        except Exception as e:
            job.status = BackupStatus.FAILED
            job.error_message = str(e)
            job.end_time = datetime.now()
            logger.error(f"Full backup failed: {e}")

        return job

    def create_incremental_backup(self) -> BackupJob:
        """Create an incremental backup using WAL"""
        backup_id = f"incremental_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        job = BackupJob(
            id=backup_id,
            backup_type=BackupType.INCREMENTAL,
            status=BackupStatus.PENDING,
            start_time=datetime.now(),
            retention_days=self.config.retention_days,
        )

        try:
            self.backup_jobs[backup_id] = job
            job.status = BackupStatus.IN_PROGRESS

            # For PostgreSQL, we use WAL archiving for incremental backups
            # This is a simplified version - in production, use pgBackRest or Barman

            # Force a WAL switch to create new segment
            with self._get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT pg_switch_wal();")
                    wal_segment = cursor.fetchone()[0]

            # Archive the WAL segment
            wal_path = os.path.join(self.config.backup_directory, "wal", wal_segment)
            os.makedirs(os.path.dirname(wal_path), exist_ok=True)

            # Copy WAL file
            data_dir = self._get_pg_data_dir()
            src_wal = os.path.join(data_dir, "pg_wal", wal_segment)
            shutil.copy2(src_wal, wal_path)

            # Compress if enabled
            if self.config.compression_enabled:
                compressed_path = wal_path + ".gz"
                with self._managed_file_open(wal_path, "rb") as f_in:
                    with gzip.open(compressed_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(wal_path)
                wal_path = compressed_path

            # Update job
            job.file_path = wal_path
            job.file_size = os.path.getsize(wal_path)
            job.checksum = self._calculate_checksum(wal_path)
            job.status = BackupStatus.COMPLETED
            job.end_time = datetime.now()

            logger.info(f"Incremental backup completed: {wal_segment}")

        except Exception as e:
            job.status = BackupStatus.FAILED
            job.error_message = str(e)
            job.end_time = datetime.now()
            logger.error(f"Incremental backup failed: {e}")

        return job

    def backup_wal_archive(self) -> BackupJob:
        """Backup WAL archive files"""
        backup_id = f"wal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        job = BackupJob(
            id=backup_id,
            backup_type=BackupType.WAL,
            status=BackupStatus.PENDING,
            start_time=datetime.now(),
            retention_days=7,  # WAL archives kept for 7 days
        )

        try:
            self.backup_jobs[backup_id] = job
            job.status = BackupStatus.IN_PROGRESS

            # Get list of WAL files to archive
            data_dir = self._get_pg_data_dir()
            wal_dir = os.path.join(data_dir, "pg_wal")
            archive_dir = os.path.join(self.config.backup_directory, "wal_archive")
            os.makedirs(archive_dir, exist_ok=True)

            # Archive completed WAL files
            archived_files = []
            for filename in os.listdir(wal_dir):
                if filename.startswith("wal") and not filename.endswith(".partial"):
                    src_path = os.path.join(wal_dir, filename)
                    dst_path = os.path.join(archive_dir, filename)

                    if not os.path.exists(dst_path):
                        shutil.copy2(src_path, dst_path)
                        archived_files.append(filename)

                        # Compress if enabled
                        if self.config.compression_enabled:
                            compressed_path = dst_path + ".gz"
                            with self._managed_file_open(dst_path, "rb") as f_in:
                                with gzip.open(compressed_path, "wb") as f_out:
                                    shutil.copyfileobj(f_in, f_out)
                            os.remove(dst_path)

            # Update job
            job.file_path = archive_dir
            job.status = BackupStatus.COMPLETED
            job.end_time = datetime.now()

            logger.info(f"WAL archive backup completed: {len(archived_files)} files")

        except Exception as e:
            job.status = BackupStatus.FAILED
            job.error_message = str(e)
            job.end_time = datetime.now()
            logger.error(f"WAL archive backup failed: {e}")

        return job

    def restore_database(
        self,
        backup_id: str,
        target_time: Optional[datetime] = None,
        recovery_method: RecoveryMethod = RecoveryMethod.POINT_IN_TIME,
    ) -> Dict[str, Any]:
        """Restore database from backup"""
        result = {"success": False, "message": "", "steps": [], "restored_tables": [], "duration": 0}

        start_time = time.time()

        try:
            # Find backup job
            backup_job = self._find_backup_job(backup_id)
            if not backup_job:
                raise Exception(f"Backup job not found: {backup_id}")

            result["steps"].append(f"Found backup job: {backup_id}")

            # Create restore directory
            restore_dir = os.path.join(self.config.backup_directory, "restore", backup_id)
            os.makedirs(restore_dir, exist_ok=True)

            # Copy backup file to restore directory
            backup_file = backup_job.file_path
            restore_file = os.path.join(restore_dir, os.path.basename(backup_file))
            shutil.copy2(backup_file, restore_file)

            # Decompress if needed
            if restore_file.endswith(".gz"):
                decompressed_file = restore_file[:-3]
                with gzip.open(restore_file, "rb") as f_in:
                    with self._managed_file_open(decompressed_file, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                restore_file = decompressed_file

            # Drop and recreate database (for full restore)
            if recovery_method in [RecoveryMethod.FULL_RESTORE, RecoveryMethod.POINT_IN_TIME]:
                result["steps"].append("Dropping existing database...")
                self._drop_database()

                result["steps"].append("Creating new database...")
                self._create_database()

            # Restore data
            result["steps"].append("Restoring database...")
            db_config = self._get_db_config()

            if recovery_method == RecoveryMethod.POINT_IN_TIME and target_time:
                # Point-in-time recovery using PITR
                result["steps"].append(f"Performing point-in-time recovery to {target_time}")
                self._perform_pitr(restore_file, target_time)
            else:
                # Full restore
                cmd = [
                    "pg_restore",
                    f"--host={db_config['host']}",
                    f"--port={db_config['port']}",
                    f"--username={db_config['user']}",
                    "--dbname=" + db_config["dbname"],
                    "--verbose",
                    "--no-owner",
                    "--no-privileges",
                    restore_file,
                ]

                env = os.environ.copy()
                env["PGPASSWORD"] = db_config["password"]

                restore_result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=3600)

                if restore_result.returncode != 0:
                    raise Exception(f"pg_restore failed: {restore_result.stderr}")

            result["success"] = True
            result["message"] = "Database restored successfully"
            result["duration"] = time.time() - start_time

            logger.info(f"Database restore completed successfully from {backup_id}")

        except Exception as e:
            result["success"] = False
            result["message"] = str(e)
            result["duration"] = time.time() - start_time
            logger.error(f"Database restore failed: {e}")

        return result

    def perform_selective_restore(
        self, backup_id: str, tables: List[str], schema: Optional[str] = None
    ) -> Dict[str, Any]:
        """Restore specific tables from backup"""
        result = {"success": False, "message": "", "restored_tables": [], "duration": 0}

        start_time = time.time()

        try:
            # Find backup job
            backup_job = self._find_backup_job(backup_id)
            if not backup_job:
                raise Exception(f"Backup job not found: {backup_id}")

            # Create restore directory
            restore_dir = os.path.join(self.config.backup_directory, "restore", backup_id)
            os.makedirs(restore_dir, exist_ok=True)

            # Copy and decompress backup
            backup_file = backup_job.file_path
            restore_file = os.path.join(restore_dir, os.path.basename(backup_file))
            shutil.copy2(backup_file, restore_file)

            if restore_file.endswith(".gz"):
                decompressed_file = restore_file[:-3]
                with gzip.open(restore_file, "rb") as f_in:
                    with self._managed_file_open(decompressed_file, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                restore_file = decompressed_file

            # Drop and recreate target tables
            db_config = self._get_db_config()
            with self._get_db_connection() as conn:
                with conn.cursor() as cursor:
                    for table in tables:
                        full_table = f"{schema}.{table}" if schema else table
                        cursor.execute(f"DROP TABLE IF EXISTS {full_table} CASCADE;")
                        cursor.execute(f"CREATE TABLE {full_table} (LIKE {full_table} INCLUDING ALL);")

            # Restore specific tables
            for table in tables:
                cmd = [
                    "pg_restore",
                    f"--host={db_config['host']}",
                    f"--port={db_config['port']}",
                    f"--username={db_config['user']}",
                    "--dbname=" + db_config["dbname"],
                    "--verbose",
                    "--data-only",
                    "--table=" + table,
                ]

                if schema:
                    cmd.append("--schema=" + schema)

                cmd.append(restore_file)

                env = os.environ.copy()
                env["PGPASSWORD"] = db_config["password"]

                restore_result = subprocess.run(
                    cmd, env=env, capture_output=True, text=True, timeout=1800  # 30 minutes
                )

                if restore_result.returncode == 0:
                    result["restored_tables"].append(table)
                else:
                    logger.error(f"Failed to restore table {table}: {restore_result.stderr}")

            result["success"] = len(result["restored_tables"]) == len(tables)
            result["message"] = f"Restored {len(result['restored_tables'])}/{len(tables)} tables"
            result["duration"] = time.time() - start_time

        except Exception as e:
            result["success"] = False
            result["message"] = str(e)
            result["duration"] = time.time() - start_time
            logger.error(f"Selective restore failed: {e}")

        return result

    def create_database_clone(self, source_db: str, target_db: str, backup_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a clone of the database"""
        result = {"success": False, "message": "", "duration": 0}

        start_time = time.time()

        try:
            db_config = self._get_db_config()

            # Create target database
            with self._get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(f"DROP DATABASE IF EXISTS {target_db};")
                    cursor.execute(f"CREATE DATABASE {target_db} TEMPLATE {source_db};")

            # If backup_id provided, perform additional restore
            if backup_id:
                backup_job = self._find_backup_job(backup_id)
                if backup_job:
                    # Apply WAL logs or incremental backups to bring to specific point
                    pass

            result["success"] = True
            result["message"] = f"Database clone created: {target_db} from {source_db}"
            result["duration"] = time.time() - start_time

            logger.info(f"Database clone created successfully")

        except Exception as e:
            result["success"] = False
            result["message"] = str(e)
            result["duration"] = time.time() - start_time
            logger.error(f"Database clone failed: {e}")

        return result

    def cleanup_old_backups(self):
        """Clean up expired backups"""
        cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)

        for backup_id, job in list(self.backup_jobs.items()):
            if job.end_time and job.end_time < cutoff_date:
                try:
                    # Delete backup file
                    if job.file_path and os.path.exists(job.file_path):
                        os.remove(job.file_path)

                    # Delete from remote storage
                    if self.config.s3_enabled:
                        self._delete_from_s3(backup_id)

                    # Update job status
                    job.status = BackupStatus.EXPIRED

                    logger.info(f"Cleaned up expired backup: {backup_id}")

                except Exception as e:
                    logger.error(f"Error cleaning up backup {backup_id}: {e}")

    def verify_backup_integrity(self, backup_id: str) -> Dict[str, Any]:
        """Verify backup file integrity"""
        result = {"valid": False, "message": "", "checksum_verified": False, "tables_count": 0}

        try:
            backup_job = self._find_backup_job(backup_id)
            if not backup_job:
                raise Exception(f"Backup job not found: {backup_id}")

            # Verify checksum
            if backup_job.checksum:
                calculated_checksum = self._calculate_checksum(backup_job.file_path)
                if calculated_checksum == backup_job.checksum:
                    result["checksum_verified"] = True
                else:
                    raise Exception("Checksum verification failed")

            # Verify backup contents
            if backup_job.backup_type in [BackupType.FULL, BackupType.DATA_ONLY]:
                # Use pg_restore to list contents
                cmd = ["pg_restore", "--list", backup_job.file_path]
                list_result = subprocess.run(cmd, capture_output=True, text=True)

                if list_result.returncode == 0:
                    # Count tables
                    tables = [line for line in list_result.stdout.split("\n") if "TABLE" in line]
                    result["tables_count"] = len(tables)
                else:
                    raise Exception(f"Failed to list backup contents: {list_result.stderr}")

            result["valid"] = True
            result["message"] = "Backup integrity verified"

        except Exception as e:
            result["message"] = str(e)
            logger.error(f"Backup verification failed: {e}")

        return result

    def get_backup_status(self) -> Dict[str, Any]:
        """Get current backup status"""
        recent_jobs = sorted(self.backup_jobs.values(), key=lambda x: x.start_time, reverse=True)[:10]  # Last 10 jobs

        stats = {
            "total_backups": len(self.backup_jobs),
            "successful_backups": len([j for j in self.backup_jobs.values() if j.status == BackupStatus.COMPLETED]),
            "failed_backups": len([j for j in self.backup_jobs.values() if j.status == BackupStatus.FAILED]),
            "total_size_gb": sum(
                j.file_size for j in self.backup_jobs.values() if j.file_size and j.status == BackupStatus.COMPLETED
            )
            / (1024**3),
            "last_backup": recent_jobs[0].start_time.isoformat() if recent_jobs else None,
            "recent_jobs": [
                {
                    "id": job.id,
                    "type": job.backup_type.value,
                    "status": job.status.value,
                    "start_time": job.start_time.isoformat(),
                    "size_gb": (job.file_size or 0) / (1024**3) if job.file_size else 0,
                }
                for job in recent_jobs
            ],
        }

        return stats

    def _get_db_config(self) -> Dict[str, str]:
        """Get database configuration"""
        db_config = settings.DATABASES["default"]
        return {
            "host": db_config.get("HOST", "localhost"),
            "port": db_config.get("PORT", "5432"),
            "user": db_config.get("USER", "postgres"),
            "password": db_config.get("PASSWORD", ""),
            "dbname": db_config.get("NAME", "hms"),
        }

    def _get_db_connection(self):
        """Get database connection with proper resource management"""
        config = self._get_db_config()
        conn = psycopg2.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            database="postgres",  # Connect to postgres for admin operations
        )
        self._connections.add(conn)
        return conn

    def _managed_file_open(self, filepath, mode):
        """Managed file opening with proper descriptor tracking"""
        f = open(filepath, mode)
        self._file_handles.add(f)
        return f

    def _cleanup_resources(self):
        """Cleanup all file handles and connections"""
        with self._lock:
            # Close all file handles
            for handle in list(self._file_handles):
                try:
                    handle.close()
                except:
                    pass
            self._file_handles.clear()

            # Close all database connections
            for conn in list(self._connections):
                try:
                    conn.close()
                except:
                    pass
            self._connections.clear()

            # Close SSH client
            if self.ssh_client:
                try:
                    self.ssh_client.close()
                except:
                    pass

    def __del__(self):
        """Cleanup on destruction"""
        self._cleanup_resources()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        self._cleanup_resources()

    def _get_pg_data_dir(self) -> str:
        """Get PostgreSQL data directory"""
        with self._get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SHOW data_directory;")
                return cursor.fetchone()[0]

    def _calculate_checksum(self, filepath: str) -> str:
        """Calculate SHA256 checksum of file"""
        sha256_hash = hashlib.sha256()
        with self._managed_file_open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def _upload_to_remote(self, backup_id: str, filepath: str):
        """Upload backup to remote storage"""
        try:
            # Upload to S3
            if self.config.s3_enabled and self.s3_client:
                s3_key = f"backups/{backup_id}/{os.path.basename(filepath)}"
                self.s3_client.upload_file(filepath, self.config.s3_bucket, s3_key)
                logger.info(f"Uploaded backup to S3: {s3_key}")

            # Upload to remote server
            if self.config.remote_backup_enabled and self.ssh_client:
                self.ssh_client.connect(
                    self.config.remote_host,
                    username=self.config.remote_user,
                    key_filename=getattr(settings, "SSH_PRIVATE_KEY_PATH", None),
                )

                sftp = self.ssh_client.open_sftp()
                remote_path = os.path.join(self.config.remote_path, backup_id)
                sftp.mkdir(remote_path)
                sftp.put(filepath, os.path.join(remote_path, os.path.basename(filepath)))
                sftp.close()
                self.ssh_client.close()

                logger.info(f"Uploaded backup to remote server: {self.config.remote_host}")

        except Exception as e:
            logger.error(f"Failed to upload backup to remote storage: {e}")

    def _delete_from_s3(self, backup_id: str):
        """Delete backup from S3"""
        try:
            if self.s3_client:
                # List objects with backup_id prefix
                objects = self.s3_client.list_objects_v2(Bucket=self.config.s3_bucket, Prefix=f"backups/{backup_id}/")

                # Delete objects
                if "Contents" in objects:
                    delete_keys = [{"Key": obj["Key"]} for obj in objects["Contents"]]
                    self.s3_client.delete_objects(Bucket=self.config.s3_bucket, Delete={"Objects": delete_keys})

        except Exception as e:
            logger.error(f"Failed to delete backup from S3: {e}")

    def _find_backup_job(self, backup_id: str) -> Optional[BackupJob]:
        """Find backup job by ID"""
        return self.backup_jobs.get(backup_id)

    def _drop_database(self):
        """Drop existing database"""
        with self._get_db_connection() as conn:
            conn.autocommit = True
            with conn.cursor() as cursor:
                cursor.execute("DROP DATABASE IF EXISTS hms;")

    def _create_database(self):
        """Create new database"""
        with self._get_db_connection() as conn:
            conn.autocommit = True
            with conn.cursor() as cursor:
                cursor.execute("CREATE DATABASE hms;")

    def _perform_pitr(self, backup_file: str, target_time: datetime):
        """Perform point-in-time recovery"""
        # This is a simplified PITR implementation
        # In production, use proper recovery.conf or postgresql.auto.conf

        recovery_config = f"""
restore_command = 'cp {self.config.backup_directory}/wal_archive/%f %p'
recovery_target_time = '{target_time.isoformat()}'
recovery_target_action = 'promote'
"""

        # Write recovery configuration
        data_dir = self._get_pg_data_dir()
        recovery_file = os.path.join(data_dir, "recovery.conf")
        with self._managed_file_open(recovery_file, "w") as f:
            f.write(recovery_config)

        # Restart PostgreSQL to begin recovery
        subprocess.run(["systemctl", "restart", "postgresql"], check=True)

        # Wait for recovery to complete
        time.sleep(30)

        # Check recovery status
        with self._get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT pg_is_in_recovery();")
                in_recovery = cursor.fetchone()[0]

                if in_recovery:
                    logger.warning("Database still in recovery")


# Global backup manager instance
backup_config = BackupConfig(
    backup_directory="/var/backups/hms_database",
    retention_days=30,
    compression_enabled=True,
    encryption_enabled=True,
    s3_enabled=getattr(settings, "S3_BACKUP_ENABLED", False),
    s3_bucket=getattr(settings, "S3_BACKUP_BUCKET"),
    s3_region=getattr(settings, "AWS_S3_REGION", "us-east-1"),
    remote_backup_enabled=getattr(settings, "REMOTE_BACKUP_ENABLED", False),
    remote_host=getattr(settings, "REMOTE_BACKUP_HOST"),
    remote_user=getattr(settings, "REMOTE_BACKUP_USER"),
    remote_path=getattr(settings, "REMOTE_BACKUP_PATH", "/backups"),
)

backup_manager = DatabaseBackupManager(backup_config)
