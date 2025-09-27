"""
read_replica_manager module
"""

import logging
import os
import random
import secrets
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from django.conf import settings
from django.core.cache import cache
from django.db import DatabaseError, OperationalError, connections
from django.db.backends.postgresql.base import DatabaseWrapper
from django.utils import timezone

from core.database_optimization import DatabaseOptimizer


class ReadReplicaRole(Enum):
    """Roles for read replicas."""

    PRIMARY = "primary"  # Primary database (write operations)
    REPLICA_READ = "replica_read"  # Read operations only
    REPLICA_ANALYTICS = "replica_analytics"  # Analytics queries
    REPLICA_REPORTING = "replica_reporting"  # Reporting queries


class ConnectionPoolStrategy(Enum):
    """Connection pooling strategies."""

    SIMPLE = "simple"  # Basic connection pooling
    HEALTH_CHECKED = "health_checked"  # Health-checked connections
    LOAD_BALANCED = "load_balanced"  # Load balanced across replicas
    GEO_AWARE = "geo_aware"  # Geographic awareness


class QueryType(Enum):
    """Types of queries for routing decisions."""

    WRITE = "write"  # INSERT, UPDATE, DELETE operations
    READ_TRANSACTIONAL = "read_transactional"  # Transactional reads
    READ_ANALYTICAL = "read_analytical"  # Analytics queries
    READ_REPORTING = "read_reporting"  # Reporting queries
    READ_CONSISTENT = "read_consistent"  # Requires latest data


@dataclass
class ReplicaInfo:
    """Information about a read replica."""

    name: str
    host: str
    port: int
    database: str
    username: str
    password: str
    role: ReadReplicaRole
    region: str = "default"
    max_connections: int = 100
    health_check_interval: int = 30
    last_health_check: datetime = None
    is_healthy: bool = True
    connection_count: int = 0
    response_time_ms: float = 0.0
    error_count: int = 0
    lag_ms: int = 0  # Replication lag in milliseconds


@dataclass
class ConnectionPoolStats:
    """Statistics for connection pooling."""

    pool_name: str
    total_connections: int
    active_connections: int
    idle_connections: int
    waiting_connections: int
    max_connections: int
    hit_rate: float
    average_wait_time_ms: float
    last_reset: datetime


class ReadReplicaManager:
    """Enterprise-grade read replica and connection pooling manager."""

    def __init__(self, database_optimizer: DatabaseOptimizer = None):
        self.logger = logging.getLogger(__name__)
        self.db_optimizer = database_optimizer or DatabaseOptimizer()
        self.is_postgres = self.db_optimizer.is_postgres

        # Connection pools
        self.primary_pool = {}
        self.replica_pools: Dict[str, Dict] = {}
        self.pool_stats: Dict[str, ConnectionPoolStats] = {}

        # Health monitoring
        self.health_check_thread = None
        self.health_check_running = False
        self.health_check_interval = int(
            os.getenv("REPLICA_HEALTH_CHECK_INTERVAL", "30")
        )

        # Load balancing
        self.current_replica_index = 0
        self.replica_weights: Dict[str, float] = {}

        # Performance tracking
        self.query_metrics: Dict[str, List[float]] = {}
        self.connection_metrics: Dict[str, List[Dict]] = {}

        # Configuration
        self.config = self._load_configuration()
        self._setup_read_replicas()

    def _load_configuration(self) -> Dict[str, Any]:
        """Load read replica configuration from environment variables."""
        config = {
            "enabled": os.getenv("READ_REPLICAS_ENABLED", "true").lower() == "true",
            "connection_pool_enabled": os.getenv(
                "CONNECTION_POOL_ENABLED", "true"
            ).lower()
            == "true",
            "health_check_enabled": os.getenv(
                "REPLICA_HEALTH_CHECK_ENABLED", "true"
            ).lower()
            == "true",
            "load_balancing_enabled": os.getenv(
                "LOAD_BALANCING_ENABLED", "true"
            ).lower()
            == "true",
            "max_pool_size": int(os.getenv("DB_MAX_POOL_SIZE", "20")),
            "min_pool_size": int(os.getenv("DB_MIN_POOL_SIZE", "5")),
            "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
            "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
            "strategy": ConnectionPoolStrategy(
                os.getenv("CONNECTION_POOL_STRATEGY", "health_checked")
            ),
        }

        return config

    def _setup_read_replicas(self):
        """Setup read replicas from configuration."""
        if not self.config["enabled"]:
            self.logger.info("Read replicas are disabled")
            return

        replicas = []

        # Load replica configurations from environment
        replica_count = int(os.getenv("READ_REPLICA_COUNT", "0"))

        for i in range(1, replica_count + 1):
            replica_config = {
                "name": f"replica_{i}",
                "host": os.getenv(f"READ_REPLICA_{i}_HOST"),
                "port": int(os.getenv(f"READ_REPLICA_{i}_PORT", "5432")),
                "database": os.getenv(
                    f"READ_REPLICA_{i}_DATABASE", os.getenv("POSTGRES_DB", "hms")
                ),
                "username": os.getenv(
                    f"READ_REPLICA_{i}_USER", os.getenv("POSTGRES_USER", "")
                ),
                "password": os.getenv(
                    f"READ_REPLICA_{i}_PASSWORD", os.getenv("POSTGRES_PASSWORD", "")
                ),
                "role": ReadReplicaRole.REPLICA_READ,
                "region": os.getenv(f"READ_REPLICA_{i}_REGION", "default"),
                "max_connections": int(
                    os.getenv(f"READ_REPLICA_{i}_MAX_CONNECTIONS", "100")
                ),
            }

            if replica_config["host"]:
                replicas.append(ReplicaInfo(**replica_config))

        self.replicas = replicas

        # Initialize connection pools
        if self.config["connection_pool_enabled"]:
            self._initialize_connection_pools()

        # Start health monitoring
        if self.config["health_check_enabled"]:
            self._start_health_monitoring()

        self.logger.info(f"Setup {len(replicas)} read replicas")

    def _initialize_connection_pools(self):
        """Initialize connection pools for primary and replicas."""
        try:
            import psycopg2.pool

            # Primary connection pool
            primary_config = self._get_primary_config()
            self.primary_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=self.config["min_pool_size"],
                maxconn=self.config["max_pool_size"],
                host=primary_config["host"],
                port=primary_config["port"],
                database=primary_config["database"],
                user=primary_config["username"],
                password=primary_config["password"],
                connect_timeout=self.config["pool_timeout"],
            )

            # Replica connection pools
            for replica in self.replicas:
                pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=max(1, self.config["min_pool_size"] // 2),
                    maxconn=max(5, self.config["max_pool_size"] // 2),
                    host=replica.host,
                    port=replica.port,
                    database=replica.database,
                    user=replica.username,
                    password=replica.password,
                    connect_timeout=self.config["pool_timeout"],
                )

                self.replica_pools[replica.name] = pool

            self.logger.info("Initialized connection pools for primary and replicas")

        except ImportError:
            self.logger.warning(
                "psycopg2 not available, using Django connection management"
            )
            self.config["connection_pool_enabled"] = False

    def _get_primary_config(self) -> Dict[str, Any]:
        """Get primary database configuration."""
        primary_config = settings.DATABASES.get("default", {})
        return {
            "host": primary_config.get("HOST", "localhost"),
            "port": int(primary_config.get("PORT", 5432)),
            "database": primary_config.get("NAME", "hms"),
            "username": primary_config.get("USER", ""),
            "password": primary_config.get("PASSWORD", ""),
        }

    def _start_health_monitoring(self):
        """Start background health monitoring for replicas."""
        if self.health_check_thread and self.health_check_thread.is_alive():
            return

        self.health_check_running = True
        self.health_check_thread = threading.Thread(
            target=self._health_monitor_worker, daemon=True
        )
        self.health_check_thread.start()
        self.logger.info("Started replica health monitoring")

    def _health_monitor_worker(self):
        """Background worker for health monitoring."""
        while self.health_check_running:
            try:
                self._check_replica_health()
                time.sleep(self.health_check_interval)
            except Exception as e:
                self.logger.error(f"Error in health monitoring: {e}")
                time.sleep(60)  # Wait before retrying

    def _check_replica_health(self):
        """Check health of all replicas."""
        for replica in self.replicas:
            try:
                start_time = time.time()

                # Test connection
                with self.get_replica_connection(replica.name) as conn:
                    with conn.cursor() as cursor:
                        # Check if replica is accepting connections
                        cursor.execute("SELECT 1")
                        result = cursor.fetchone()
                        if result[0] != 1:
                            raise Exception("Invalid response from replica")

                        # Check replication lag if supported
                        if self.is_postgres:
                            try:
                                cursor.execute("SELECT pg_last_wal_replay_lag()")
                                lag_result = cursor.fetchone()
                                replica.lag_ms = (
                                    int(lag_result[0].total_seconds() * 1000)
                                    if lag_result[0]
                                    else 0
                                )
                            except:
                                replica.lag_ms = 0

                # Update health metrics
                replica.response_time_ms = (time.time() - start_time) * 1000
                replica.last_health_check = timezone.now()
                replica.is_healthy = True
                replica.error_count = 0

            except Exception as e:
                replica.is_healthy = False
                replica.error_count += 1
                replica.last_health_check = timezone.now()
                self.logger.warning(f"Replica {replica.name} health check failed: {e}")

    @contextmanager
    def get_primary_connection(self):
        """Get a connection from the primary database pool."""
        if self.config["connection_pool_enabled"] and hasattr(self, "primary_pool"):
            try:
                conn = self.primary_pool.getconn()
                yield conn
                self.primary_pool.putconn(conn)
            except Exception as e:
                self.logger.error(f"Error getting primary connection: {e}")
                raise DatabaseError("Failed to get primary connection")
        else:
            # Use Django's default connection
            yield connections["default"]

    @contextmanager
    def get_replica_connection(self, replica_name: str = None):
        """Get a connection from a replica pool."""
        if not self.config["enabled"] or not self.replicas:
            # Fall back to primary
            with self.get_primary_connection() as conn:
                yield conn
            return

        # Select replica if not specified
        if replica_name is None:
            replica = self._select_replica_for_read()
            if not replica:
                with self.get_primary_connection() as conn:
                    yield conn
                return
            replica_name = replica.name

        if replica_name not in self.replica_pools:
            # Fall back to primary if replica not found
            with self.get_primary_connection() as conn:
                yield conn
            return

        try:
            if self.config["connection_pool_enabled"]:
                pool = self.replica_pools[replica_name]
                conn = pool.getconn()
                yield conn
                pool.putconn(conn)
            else:
                # Create direct connection
                replica = next(
                    (r for r in self.replicas if r.name == replica_name), None
                )
                if replica:
                    conn = self._create_direct_connection(replica)
                    yield conn
                    conn.close()
                else:
                    with self.get_primary_connection() as conn:
                        yield conn

        except Exception as e:
            self.logger.error(
                f"Error getting replica connection for {replica_name}: {e}"
            )
            # Fall back to primary
            with self.get_primary_connection() as conn:
                yield conn

    def _create_direct_connection(self, replica: ReplicaInfo):
        """Create a direct connection to a replica."""
        import psycopg2

        return psycopg2.connect(
            host=replica.host,
            port=replica.port,
            database=replica.database,
            user=replica.username,
            password=replica.password,
            connect_timeout=self.config["pool_timeout"],
        )

    def route_query(
        self, query: str, query_type: QueryType = QueryType.READ_TRANSACTIONAL
    ) -> str:
        """Route a query to the appropriate database (primary or replica)."""
        if not self.config["enabled"]:
            return "default"

        # Write operations always go to primary
        if query_type == QueryType.WRITE:
            return "default"

        # For read operations, decide based on query type and consistency requirements
        if query_type == QueryType.READ_CONSISTENT:
            # Requires latest data, use primary
            return "default"

        # Route to appropriate replica based on query type
        if query_type == QueryType.READ_ANALYTICAL:
            replica = self._select_replica_for_analytics()
        elif query_type == QueryType.READ_REPORTING:
            replica = self._select_replica_for_reporting()
        else:
            replica = self._select_replica_for_read()

        return replica.name if replica else "default"

    def _select_replica_for_read(self) -> Optional[ReplicaInfo]:
        """Select the best replica for general read operations."""
        if not self.replicas:
            return None

        # Filter healthy replicas with low lag
        healthy_replicas = [
            r
            for r in self.replicas
            if r.is_healthy and r.lag_ms < 1000  # Less than 1 second lag
        ]

        if not healthy_replicas:
            self.logger.warning("No healthy replicas available")
            return None

        # Use weighted selection based on performance
        return self._weighted_replica_selection(healthy_replicas)

    def _select_replica_for_analytics(self) -> Optional[ReplicaInfo]:
        """Select replica for analytics queries."""
        analytics_replicas = [
            r
            for r in self.replicas
            if r.role == ReadReplicaRole.REPLICA_ANALYTICS and r.is_healthy
        ]

        if not analytics_replicas:
            # Fall back to any healthy replica
            return self._select_replica_for_read()

        return self._weighted_replica_selection(analytics_replicas)

    def _select_replica_for_reporting(self) -> Optional[ReplicaInfo]:
        """Select replica for reporting queries."""
        reporting_replicas = [
            r
            for r in self.replicas
            if r.role == ReadReplicaRole.REPLICA_REPORTING and r.is_healthy
        ]

        if not reporting_replicas:
            # Fall back to any healthy replica
            return self._select_replica_for_read()

        return self._weighted_replica_selection(reporting_replicas)

    def _weighted_replica_selection(self, replicas: List[ReplicaInfo]) -> ReplicaInfo:
        """Select replica using weighted random selection."""
        # Calculate weights based on response time and connection count
        weights = []
        for replica in replicas:
            # Lower response time is better
            response_time_weight = 1.0 / max(replica.response_time_ms, 1.0)
            # Lower connection count is better
            connection_weight = 1.0 / max(replica.connection_count, 1.0)
            # Lower error count is better
            error_weight = 1.0 / max(replica.error_count + 1, 1.0)

            total_weight = response_time_weight + connection_weight + error_weight
            weights.append(total_weight)

        # Weighted random selection
        total_weight = sum(weights)
        if total_weight == 0:
            return secrets.choice(replicas)

        r = secrets.uniform(0, total_weight)
        upto = 0
        for replica, weight in zip(replicas, weights):
            if upto + weight >= r:
                return replica
            upto += weight

        return replicas[-1]

    def execute_query(
        self,
        query: str,
        params=None,
        query_type: QueryType = QueryType.READ_TRANSACTIONAL,
    ):
        """Execute a query on the appropriate database."""
        db_alias = self.route_query(query, query_type)

        try:
            with connections[db_alias].cursor() as cursor:
                cursor.execute(query, params)

                if query_type == QueryType.WRITE:
                    return cursor.rowcount  # Return number of affected rows
                else:
                    return cursor.fetchall()  # Return query results

        except Exception as e:
            self.logger.error(f"Error executing query on {db_alias}: {e}")
            # Try fallback to primary for read operations
            if query_type != QueryType.WRITE and db_alias != "default":
                try:
                    with connections["default"].cursor() as cursor:
                        cursor.execute(query, params)
                        return cursor.fetchall()
                except Exception as fallback_error:
                    self.logger.error(
                        f"Fallback to primary also failed: {fallback_error}"
                    )

            raise DatabaseError(f"Query execution failed: {e}")

    def get_replica_stats(self) -> Dict[str, Any]:
        """Get statistics about replica performance and health."""
        stats = {
            "timestamp": timezone.now().isoformat(),
            "config": {
                "enabled": self.config["enabled"],
                "connection_pool_enabled": self.config["connection_pool_enabled"],
                "health_check_enabled": self.config["health_check_enabled"],
                "strategy": self.config["strategy"].value,
            },
            "replicas": [],
        }

        for replica in self.replicas:
            replica_stats = {
                "name": replica.name,
                "host": replica.host,
                "port": replica.port,
                "role": replica.role.value,
                "region": replica.region,
                "is_healthy": replica.is_healthy,
                "response_time_ms": replica.response_time_ms,
                "lag_ms": replica.lag_ms,
                "error_count": replica.error_count,
                "connection_count": replica.connection_count,
                "last_health_check": (
                    replica.last_health_check.isoformat()
                    if replica.last_health_check
                    else None
                ),
            }
            stats["replicas"].append(replica_stats)

        return stats

    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        stats = {"timestamp": timezone.now().isoformat(), "pools": {}}

        # Primary pool stats
        if hasattr(self, "primary_pool"):
            try:
                stats["pools"]["primary"] = {
                    "minconn": self.primary_pool.minconn,
                    "maxconn": self.primary_pool.maxconn,
                    "used_connections": (
                        len(self.primary_pool._pool)
                        if hasattr(self.primary_pool, "_pool")
                        else 0
                    ),
                }
            except:
                stats["pools"]["primary"] = {"error": "Could not get stats"}

        # Replica pool stats
        for replica_name, pool in self.replica_pools.items():
            try:
                stats["pools"][replica_name] = {
                    "minconn": pool.minconn,
                    "maxconn": pool.maxconn,
                    "used_connections": (
                        len(pool._pool) if hasattr(pool, "_pool") else 0
                    ),
                }
            except:
                stats["pools"][replica_name] = {"error": "Could not get stats"}

        return stats

    def optimize_pools(self) -> Dict[str, Any]:
        """Optimize connection pools based on usage patterns."""
        if not self.config["connection_pool_enabled"]:
            return {"error": "Connection pooling not enabled"}

        results = {
            "optimization_timestamp": timezone.now().isoformat(),
            "actions_taken": [],
            "recommendations": [],
        }

        # Analyze pool usage and adjust sizes
        for pool_name, pool in self.replica_pools.items():
            try:
                # Get current usage
                used_connections = len(pool._pool) if hasattr(pool, "_pool") else 0
                usage_rate = used_connections / pool.maxconn

                # Recommendations based on usage
                if usage_rate > 0.8:
                    recommendation = f"Consider increasing max connections for {pool_name} (current usage: {usage_rate:.1%})"
                    results["recommendations"].append(recommendation)
                elif usage_rate < 0.2:
                    recommendation = f"Consider decreasing max connections for {pool_name} (current usage: {usage_rate:.1%})"
                    results["recommendations"].append(recommendation)

            except Exception as e:
                self.logger.warning(f"Could not analyze pool {pool_name}: {e}")

        return results

    def failover_to_primary(self) -> Dict[str, Any]:
        """Perform emergency failover to primary database."""
        self.logger.warning("Emergency failover to primary database initiated")

        results = {
            "failover_timestamp": timezone.now().isoformat(),
            "actions_taken": [],
            "replicas_failed": [],
        }

        # Mark all replicas as unhealthy
        for replica in self.replicas:
            replica.is_healthy = False
            results["replicas_failed"].append(replica.name)

        # Redirect all traffic to primary
        self.config["enabled"] = False
        results["actions_taken"].append("Disabled read replicas")
        results["actions_taken"].append("All traffic redirected to primary")

        # Clear connection pools
        if hasattr(self, "replica_pools"):
            for pool_name, pool in self.replica_pools.items():
                try:
                    pool.closeall()
                    results["actions_taken"].append(
                        f"Closed connection pool for {pool_name}"
                    )
                except:
                    pass

        self.replica_pools.clear()

        self.logger.info("Emergency failover to primary completed")
        return results

    def recovery_from_failover(self) -> Dict[str, Any]:
        """Attempt to recover from failover and re-enable replicas."""
        self.logger.info("Attempting recovery from failover")

        results = {
            "recovery_timestamp": timezone.now().isoformat(),
            "actions_taken": [],
            "replicas_restored": [],
            "replicas_failed": [],
        }

        # Check replica health
        self._check_replica_health()

        # Count healthy replicas
        healthy_replicas = [r for r in self.replicas if r.is_healthy]

        if len(healthy_replicas) >= len(self.replicas) * 0.5:  # At least 50% healthy
            # Re-enable read replicas
            self.config["enabled"] = True
            results["actions_taken"].append("Re-enabled read replicas")

            # Reinitialize connection pools
            if self.config["connection_pool_enabled"]:
                self._initialize_connection_pools()
                results["actions_taken"].append("Reinitialized connection pools")

            results["replicas_restored"] = [r.name for r in healthy_replicas]
            results["replicas_failed"] = [
                r.name for r in self.replicas if not r.is_healthy
            ]

            self.logger.info(
                f"Recovery successful: {len(healthy_replicas)}/{len(self.replicas)} replicas restored"
            )
        else:
            results["actions_taken"].append(
                "Insufficient healthy replicas for recovery"
            )
            results["replicas_failed"] = [r.name for r in self.replicas]

            self.logger.warning(
                f"Recovery failed: only {len(healthy_replicas)}/{len(self.replicas)} replicas healthy"
            )

        return results

    def cleanup(self):
        """Cleanup resources."""
        self.health_check_running = False

        # Close connection pools
        if hasattr(self, "primary_pool"):
            try:
                self.primary_pool.closeall()
            except:
                pass

        for pool in self.replica_pools.values():
            try:
                pool.closeall()
            except:
                pass

        self.replica_pools.clear()


# Singleton instance for easy access
read_replica_manager = ReadReplicaManager()
