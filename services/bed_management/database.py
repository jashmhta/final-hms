"""
database module
"""

import logging
import os
import ssl
from urllib.parse import urlparse

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)


def get_database_url():
    db_url = os.getenv("BED_MANAGEMENT_DATABASE_URL")
    if not db_url:
        db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError(
            "BED_MANAGEMENT_DATABASE_URL or DATABASE_URL environment variable must be set"
        )
    parsed = urlparse(db_url)
    if parsed.scheme not in ["postgresql", "postgresql+psycopg2", "postgresql+psycopg"]:
        raise ValueError("Only PostgreSQL with SSL/TLS is supported")
    if parsed.password and len(parsed.password) < 16:
        raise ValueError("Database password must be at least 16 characters")
    if "sslmode" not in db_url.lower():
        separator = "&" if "?" in db_url else "?"
        db_url = f"{db_url}{separator}sslmode=require"
    logger.info("Database configuration validated successfully")
    return db_url


def configure_ssl():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    return ssl_context


DATABASE_URL = get_database_url()
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_timeout=30,
    connect_args={
        "ssl": configure_ssl(),
        "connect_timeout": 10,
        "application_name": "hms-bed-management",
        "tcp_keepalive": True,
    },
)


@event.listens_for(engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    logger.info("Database connection established")
    cursor = dbapi_connection.cursor()
    cursor.execute("SET statement_timeout TO '30s'")
    cursor.execute("SET lock_timeout TO '15s'")
    cursor.execute("SET default_transaction_isolation TO 'read committed'")
    cursor.close()


@event.listens_for(engine, "close")
def receive_close(dbapi_connection, connection_record):
    logger.info("Database connection closed")


SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        db.execute("SET TIME ZONE 'UTC'")
        db.execute("SET work_mem TO '16MB'")
        logger.debug("Database session created")
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        logger.debug("Database session closed")


def validate_database_health():
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT version()")
            version = result.fetchone()[0]
            logger.info(f"Database health check passed - PostgreSQL version: {version}")
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
