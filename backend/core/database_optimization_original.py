"""
database_optimization_original module
"""

import asyncio
import logging
import os
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import psycopg2
import redis
from psycopg2 import pool, sql
from psycopg2.extras import DictCursor, RealDictCursor

from django.conf import settings
from django.core.cache import cache
from django.db import connections, transaction
from django.db.backends.postgresql.base import DatabaseWrapper


class DatabaseOptimizationLevel(Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    ENTERPRISE = "enterprise"


class DatabaseStrategy(Enum):
    SINGLE_INSTANCE = "single_instance"
    READ_REPLICAS = "read_replicas"
    SHARDING = "sharding"
    MULTI_TENANT = "multi_tenant"
    HYBRID = "hybrid"


@dataclass
class DatabaseMetrics:
    query_time_ms: float
    rows_affected: int
    connection_time_ms: float
    cache_hit_rate: float
    index_usage: float
    memory_usage_mb: float
    disk_usage_mb: float
    active_connections: int
    max_connections: int
    slow_query_count: int
    total_query_count: int


class DatabaseConnectionPool:
    def __init__(self, min_connections: int = 2, max_connections: int = 20):
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.pools: Dict[str, pool.SimpleConnectionPool] = {}
        self.metrics: Dict[str, DatabaseMetrics] = {}
        self._lock = threading.Lock()

    def create_pool(self, alias: str, **kwargs):
        try:
            if alias in self.pools:
                return self.pools[alias]
            db_config = connections.databases[alias]
            host = db_config.get("HOST", "localhost")
            port = db_config.get("PORT", 5432)
            database = db_config.get("NAME")
            user = db_config.get("USER")
            password = db_config.get("PASSWORD")
            connection_pool = pool.SimpleConnectionPool(
                minconn=self.min_connections,
                maxconn=self.max_connections,
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                cursor_factory=DictCursor,
                options="-c default_transaction_isolation=read_committed",
            )
            with self._lock:
                self.pools[alias] = connection_pool
                self.metrics[alias] = DatabaseMetrics(
                    query_time_ms=0.0,
                    rows_affected=0,
                    connection_time_ms=0.0,
                    cache_hit_rate=0.0,
                    index_usage=0.0,
                    memory_usage_mb=0.0,
                    disk_usage_mb=0.0,
                    active_connections=0,
                    max_connections=self.max_connections,
                    slow_query_count=0,
                    total_query_count=0,
                )
            logging.info(
                f"Created connection pool for {alias} with {self.min_connections}-{self.max_connections} connections"
            )
            return connection_pool
        except Exception as e:
            logging.error(f"Failed to create connection pool for {alias}: {e}")
            raise

    def get_connection(self, alias: str):
        if alias not in self.pools:
            self.create_pool(alias)
        return self.pools[alias].getconn()

    def return_connection(self, alias: str, connection):
        if alias in self.pools:
            self.pools[alias].putconn(connection)

    @contextmanager
    def get_cursor(self, alias: str):
        conn = None
        try:
            conn = self.get_connection(alias)
            cursor = conn.cursor()
            yield cursor
        finally:
            if conn:
                self.return_connection(alias, conn)

    def close_all(self):
        for alias, pool in self.pools.items():
            pool.closeall()
        self.pools.clear()


class DatabaseIndexManager:
    def __init__(self):
        self.index_recommendations: Dict[str, List[Dict]] = {}
        self.index_stats: Dict[str, Dict] = {}

    def analyze_table_indexes(self, alias: str, table_name: str) -> Dict:
        try:
            with connection_pool.get_cursor(alias) as cursor:
                cursor.execute(
                    "SELECT indexname, indexdef FROM pg_indexes WHERE tablename = %s",
                    (table_name,),
                )
                indexes = cursor.fetchall()
                cursor.execute(
                    "SELECT schemaname, tablename, attname, n_distinct FROM pg_stats WHERE tablename = %s",
                    (table_name,),
                )
                stats = cursor.fetchall()
                cursor.execute(
                    "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = %s",
                    (table_name,),
                )
                table_info = cursor.fetchall()
                return {
                    "table": table_name,
                    "indexes": indexes,
                    "index_stats": stats,
                    "table_info": table_info,
                }
        except Exception as e:
            logging.error(f"Failed to analyze indexes for {table_name}: {e}")
            return {}

    def recommend_indexes(
        self, alias: str, table_name: str, query_patterns: List[str]
    ) -> List[Dict]:
        recommendations = []
        for pattern in query_patterns:
            if "WHERE" in pattern:
                conditions = self._extract_where_conditions(pattern)
                for condition in conditions:
                    recommendations.append(
                        {
                            "table": table_name,
                            "column": condition,
                            "index_type": "btree",
                            "reason": "WHERE clause condition",
                            "query_pattern": pattern,
                        }
                    )
        fk_recommendations = self._check_foreign_key_indexes(alias, table_name)
        recommendations.extend(fk_recommendations)
        return recommendations

    def _extract_where_conditions(self, query: str) -> List[str]:
        import re

        where_match = re.search(
            r"WHERE\s+(.*?)(?:\s+ORDER\s+BY|\s+GROUP\s+BY|\s+LIMIT|$)",
            query,
            re.IGNORECASE,
        )
        if where_match:
            conditions = where_match.group(1)
            columns = re.findall(r"(\w+)\s*[=<>]", conditions)
            return columns
        return []

    def _check_foreign_key_indexes(self, alias: str, table_name: str) -> List[Dict]:
        recommendations = []
        try:
            with connection_pool.get_cursor(alias) as cursor:
                cursor.execute(
                    """
                    SELECT
                        tc.table_name,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name
                    FROM
                        information_schema.table_constraints AS tc
                        JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                        JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE
                        tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_name = %s
                """,
                    (table_name,),
                )
                fks = cursor.fetchall()
                for fk in fks:
                    cursor.execute(
                        """
                        SELECT 1
                        FROM pg_indexes
                        WHERE tablename = %s
                        AND indexdef LIKE %s
                    """,
                        (table_name, f'%{fk["column_name"]}%'),
                    )
                    has_index = cursor.fetchone()
                    if not has_index:
                        recommendations.append(
                            {
                                "table": table_name,
                                "column": fk["column_name"],
                                "index_type": "btree",
                                "reason": "Foreign key relationship",
                                "foreign_table": fk["foreign_table_name"],
                            }
                        )
        except Exception as e:
            logging.error(f"Failed to check foreign key indexes for {table_name}: {e}")
        return recommendations

    def create_index(
        self, alias: str, table_name: str, column_name: str, index_type: str = "btree"
    ):
        try:
            index_name = f"idx_{table_name}_{column_name}"
            with connection_pool.get_cursor(alias) as cursor:
                cursor.execute(
                    f"CREATE INDEX {index_name} ON {table_name} ({column_name}) USING {index_type}"
                )
                logging.info(
                    f"Created index {index_name} on {table_name}.{column_name}"
                )
        except Exception as e:
            logging.error(f"Failed to create index on {table_name}.{column_name}: {e}")


class DatabaseQueryOptimizer:
    def __init__(self):
        self.query_history: List[Dict] = []
        self.slow_queries: List[Dict] = []
        self.query_plans: Dict[str, Dict] = {}

    def analyze_query(self, alias: str, query: str, params: Dict = None) -> Dict:
        try:
            with connection_pool.get_cursor(alias) as cursor:
                cursor.execute(
                    "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + query, params or {}
                )
                plan = cursor.fetchone()[0][0]
                execution_time = plan.get("Execution Time", 0)
                planning_time = plan.get("Planning Time", 0)
                total_cost = plan.get("Total Cost", 0)
                expensive_operations = []
                for node in plan.get("Plan", {}).get("Plans", []):
                    if (
                        "Seq Scan" in node.get("Node Type", "")
                        and node.get("Actual Rows", 0) > 10000
                    ):
                        expensive_operations.append(
                            f"Sequential scan on {node.get('Relation Name')}"
                        )
                    elif (
                        "Nested Loop" in node.get("Node Type", "")
                        and node.get("Actual Rows", 0) > 1000
                    ):
                        expensive_operations.append("Expensive nested loop")
                return {
                    "query": query,
                    "execution_time_ms": execution_time,
                    "planning_time_ms": planning_time,
                    "total_cost": total_cost,
                    "expensive_operations": expensive_operations,
                    "plan": plan,
                }
        except Exception as e:
            logging.error(f"Failed to analyze query: {e}")
            return {"error": str(e)}

    def optimize_query(self, alias: str, query: str) -> List[str]:
        optimizations = []
        if "WHERE" in query:
            conditions = self._extract_conditions(query)
            for condition in conditions:
                optimizations.append(f"Consider adding index on {condition}")
        if "SELECT *" in query:
            optimizations.append("Replace SELECT * with specific columns")
        if "LIMIT" not in query.upper() and "UPDATE" not in query.upper():
            optimizations.append("Consider adding LIMIT for large result sets")
        if "ORDER BY" in query.upper():
            order_columns = self._extract_order_columns(query)
            for column in order_columns:
                optimizations.append(f"Consider adding index on {column} for ORDER BY")
        return optimizations

    def _extract_conditions(self, query: str) -> List[str]:
        import re

        where_match = re.search(
            r"WHERE\s+(.*?)(?:\s+ORDER\s+BY|\s+GROUP\s+BY|\s+LIMIT|$)",
            query,
            re.IGNORECASE,
        )
        if where_match:
            conditions = where_match.group(1)
            columns = re.findall(r"(\w+)\s*[=<>]", conditions)
            return columns
        return []

    def _extract_order_columns(self, query: str) -> List[str]:
        import re

        order_match = re.search(
            r"ORDER\s+BY\s+(.*?)(?:\s+LIMIT|$)", query, re.IGNORECASE
        )
        if order_match:
            columns = order_match.group(1).split(",")
            return [col.strip().split()[0] for col in columns]
        return []


class DatabaseCacheManager:
    def __init__(self):
        self.redis_client = None
        self.cache_stats = {"hits": 0, "misses": 0, "evictions": 0, "total_size": 0}

    def initialize_redis(self, url: str):
        try:
            self.redis_client = redis.from_url(url, decode_responses=True)
            self.redis_client.ping()
            logging.info("Redis cache initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Redis: {e}")

    def cache_query_result(self, cache_key: str, result: Any, ttl: int = 300):
        if not self.redis_client:
            return False
        try:
            import json

            serialized = json.dumps(result, default=str)
            self.redis_client.setex(cache_key, ttl, serialized)
            self.cache_stats["total_size"] += len(serialized)
            return True
        except Exception as e:
            logging.error(f"Failed to cache query result: {e}")
            return False

    def get_cached_result(self, cache_key: str) -> Optional[Any]:
        if not self.redis_client:
            return None
        try:
            result = self.redis_client.get(cache_key)
            if result:
                self.cache_stats["hits"] += 1
                import json

                return json.loads(result)
            else:
                self.cache_stats["misses"] += 1
                return None
        except Exception as e:
            logging.error(f"Failed to get cached result: {e}")
            return None

    def invalidate_cache(self, pattern: str):
        if not self.redis_client:
            return
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                self.cache_stats["evictions"] += len(keys)
                logging.info(
                    f"Invalidated {len(keys)} cache entries for pattern: {pattern}"
                )
        except Exception as e:
            logging.error(f"Failed to invalidate cache: {e}")


class DatabaseShardingManager:
    def __init__(self):
        self.shard_configs: Dict[str, Dict] = {}
        self.shard_connections: Dict[str, DatabaseConnectionPool] = {}

    def configure_sharding(self, table_name: str, shard_key: str, shard_count: int):
        self.shard_configs[table_name] = {
            "shard_key": shard_key,
            "shard_count": shard_count,
            "shards": {},
        }
        for i in range(shard_count):
            shard_name = f"{table_name}_shard_{i}"
            self.shard_configs[table_name]["shards"][i] = {
                "name": shard_name,
                "min_value": i * (1000 // shard_count),
                "max_value": (i + 1) * (1000 // shard_count) - 1,
            }
        logging.info(f"Configured sharding for {table_name} with {shard_count} shards")

    def get_shard_for_value(self, table_name: str, shard_value: Any) -> int:
        if table_name not in self.shard_configs:
            raise ValueError(f"No sharding configured for table {table_name}")
        config = self.shard_configs[table_name]
        shard_count = config["shard_count"]
        if isinstance(shard_value, int):
            return shard_value % shard_count
        elif isinstance(shard_value, str):
            return hash(shard_value) % shard_count
        else:
            return hash(str(shard_value)) % shard_count

    def execute_on_shard(
        self, table_name: str, shard_value: Any, query: str, params: Dict = None
    ):
        shard_num = self.get_shard_for_value(table_name, shard_value)
        shard_config = self.shard_configs[table_name]["shards"][shard_num]
        shard_name = shard_config["name"]
        modified_query = query.replace(table_name, shard_name)
        try:
            with connection_pool.get_cursor("default") as cursor:
                cursor.execute(modified_query, params or {})
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Failed to execute query on shard {shard_name}: {e}")
            raise


class DatabaseBackupManager:
    def __init__(self):
        self.backup_schedules: Dict[str, Dict] = {}
        self.backup_history: List[Dict] = []

    def schedule_backup(self, alias: str, schedule: str, retention_days: int = 30):
        self.backup_schedules[alias] = {
            "schedule": schedule,
            "retention_days": retention_days,
            "last_backup": None,
            "next_backup": None,
        }

    def create_backup(self, alias: str, backup_type: str = "full") -> str:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{alias}_{backup_type}_{timestamp}.dump"
            db_config = connections.databases[alias]
            host = db_config.get("HOST", "localhost")
            port = db_config.get("PORT", 5432)
            database = db_config.get("NAME")
            user = db_config.get("USER")
            import subprocess

            command = [
                "pg_dump",
                f"--host={host}",
                f"--port={port}",
                f"--username={user}",
                f"--format=custom",
                f"--file={backup_name}",
                database,
            ]
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                backup_info = {
                    "alias": alias,
                    "backup_type": backup_type,
                    "filename": backup_name,
                    "timestamp": timestamp,
                    "size": (
                        os.path.getsize(backup_name)
                        if os.path.exists(backup_name)
                        else 0
                    ),
                }
                self.backup_history.append(backup_info)
                logging.info(f"Backup created successfully: {backup_name}")
                return backup_name
            else:
                logging.error(f"Backup failed: {result.stderr}")
                raise Exception(f"Backup failed: {result.stderr}")
        except Exception as e:
            logging.error(f"Failed to create backup: {e}")
            raise

    def restore_backup(self, alias: str, backup_file: str):
        try:
            db_config = connections.databases[alias]
            host = db_config.get("HOST", "localhost")
            port = db_config.get("PORT", 5432)
            database = db_config.get("NAME")
            user = db_config.get("USER")
            import subprocess

            command = [
                "pg_restore",
                f"--host={host}",
                f"--port={port}",
                f"--username={user}",
                f"--dbname={database}",
                f"--clean",
                f"--if-exists",
                backup_file,
            ]
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                logging.info(f"Backup restored successfully from {backup_file}")
            else:
                logging.error(f"Restore failed: {result.stderr}")
                raise Exception(f"Restore failed: {result.stderr}")
        except Exception as e:
            logging.error(f"Failed to restore backup: {e}")
            raise


class DatabasePerformanceMonitor:
    def __init__(self):
        self.metrics_history: List[DatabaseMetrics] = []
        self.alert_thresholds = {
            "query_time_ms": 1000,
            "connection_time_ms": 100,
            "memory_usage_mb": 1024,
            "disk_usage_mb": 10240,
            "active_connections": 80,
        }

    def collect_metrics(self, alias: str) -> DatabaseMetrics:
        try:
            with connection_pool.get_cursor(alias) as cursor:
                cursor.execute(
                    """
                    SELECT
                        pg_stat_database.datname,
                        pg_stat_database.numbackends,
                        pg_stat_database.xact_commit,
                        pg_stat_database.xact_rollback,
                        pg_stat_database.blks_read,
                        pg_stat_database.blks_hit,
                        pg_database_size(pg_stat_database.datname) as size
                    FROM pg_stat_database
                    JOIN pg_database ON pg_stat_database.datname = pg_database.datname
                    WHERE pg_stat_database.datname = current_database()
                """
                )
                db_stats = cursor.fetchone()
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM pg_stat_activity
                    WHERE state = 'active'
                    AND query_start < NOW() - INTERVAL '%s milliseconds'
                """,
                    (self.alert_thresholds["query_time_ms"],),
                )
                slow_query_count = cursor.fetchone()[0]
                metrics = DatabaseMetrics(
                    query_time_ms=0.0,
                    rows_affected=0,
                    connection_time_ms=0.0,
                    cache_hit_rate=(
                        (
                            db_stats["blks_hit"]
                            / (db_stats["blks_hit"] + db_stats["blks_read"])
                        )
                        * 100
                        if (db_stats["blks_hit"] + db_stats["blks_read"]) > 0
                        else 0
                    ),
                    index_usage=0.0,
                    memory_usage_mb=0,
                    disk_usage_mb=self._parse_size(db_stats["size"]),
                    active_connections=db_stats["numbackends"],
                    max_connections=100,
                    slow_query_count=slow_query_count,
                    total_query_count=db_stats["xact_commit"]
                    + db_stats["xact_rollback"],
                )
                self.metrics_history.append(metrics)
                return metrics
        except Exception as e:
            logging.error(f"Failed to collect database metrics: {e}")
            return DatabaseMetrics(
                query_time_ms=0.0,
                rows_affected=0,
                connection_time_ms=0.0,
                cache_hit_rate=0.0,
                index_usage=0.0,
                memory_usage_mb=0.0,
                disk_usage_mb=0.0,
                active_connections=0,
                max_connections=100,
                slow_query_count=0,
                total_query_count=0,
            )

    def _parse_size(self, size_str: str) -> int:
        try:
            import re

            match = re.match(r"(\d+)\s*(\w+)", size_str)
            if match:
                size = int(match.group(1))
                unit = match.group(2).upper()
                if unit == "KB":
                    return size // 1024
                elif unit == "MB":
                    return size
                elif unit == "GB":
                    return size * 1024
                elif unit == "TB":
                    return size * 1024 * 1024
            return 0
        except:
            return 0

    def check_alerts(self, metrics: DatabaseMetrics) -> List[str]:
        alerts = []
        if metrics.query_time_ms > self.alert_thresholds["query_time_ms"]:
            alerts.append(f"High query time: {metrics.query_time_ms}ms")
        if metrics.connection_time_ms > self.alert_thresholds["connection_time_ms"]:
            alerts.append(f"High connection time: {metrics.connection_time_ms}ms")
        if metrics.memory_usage_mb > self.alert_thresholds["memory_usage_mb"]:
            alerts.append(f"High memory usage: {metrics.memory_usage_mb}MB")
        if metrics.disk_usage_mb > self.alert_thresholds["disk_usage_mb"]:
            alerts.append(f"High disk usage: {metrics.disk_usage_mb}MB")
        if metrics.active_connections > self.alert_thresholds["active_connections"]:
            alerts.append(f"High active connections: {metrics.active_connections}")
        return alerts


connection_pool = DatabaseConnectionPool()
index_manager = DatabaseIndexManager()
query_optimizer = DatabaseQueryOptimizer()
cache_manager = DatabaseCacheManager()
sharding_manager = DatabaseShardingManager()
backup_manager = DatabaseBackupManager()
performance_monitor = DatabasePerformanceMonitor()


class DatabaseOptimizer:
    def __init__(self):
        self.optimization_level = DatabaseOptimizationLevel.ADVANCED
        self.strategy = DatabaseStrategy.HYBRID

    def optimize_database(self, alias: str = "default"):
        try:
            logging.info(f"Starting database optimization for {alias}")
            connection_pool.create_pool(alias)
            self._optimize_indexes(alias)
            self._optimize_queries(alias)
            if hasattr(settings, "REDIS_URL") and settings.REDIS_URL:
                cache_manager.initialize_redis(settings.REDIS_URL)
            metrics = performance_monitor.collect_metrics(alias)
            alerts = performance_monitor.check_alerts(metrics)
            if alerts:
                logging.warning(f"Database alerts for {alias}: {alerts}")
            logging.info(f"Database optimization completed for {alias}")
            return {
                "status": "success",
                "alias": alias,
                "metrics": metrics,
                "alerts": alerts,
            }
        except Exception as e:
            logging.error(f"Database optimization failed for {alias}: {e}")
            return {"status": "error", "error": str(e)}

    def _optimize_indexes(self, alias: str):
        try:
            with connection_pool.get_cursor(alias) as cursor:
                cursor.execute()
                tables = cursor.fetchall()
                for table in tables:
                    table_name = table[0]
                    logging.info(f"Analyzing indexes for table {table_name}")
                    index_analysis = index_manager.analyze_table_indexes(
                        alias, table_name
                    )
                    query_patterns = self._get_query_patterns_for_table(table_name)
                    recommendations = index_manager.recommend_indexes(
                        alias, table_name, query_patterns
                    )
                    if recommendations:
                        logging.info(
                            f"Index recommendations for {table_name}: {recommendations}"
                        )
        except Exception as e:
            logging.error(f"Failed to optimize indexes: {e}")

    def _optimize_queries(self, alias: str):
        try:
            with connection_pool.get_cursor(alias) as cursor:
                cursor.execute()
                slow_queries = cursor.fetchall()
                for query_info in slow_queries:
                    query = query_info[0]
                    mean_time = query_info[3]
                    if mean_time > 100:
                        logging.info(
                            f"Analyzing slow query (avg {mean_time:.2f}ms): {query[:100]}..."
                        )
                        optimizations = query_optimizer.optimize_query(alias, query)
                        if optimizations:
                            logging.info(
                                f"Optimizations for slow query: {optimizations}"
                            )
        except Exception as e:
            logging.error(f"Failed to optimize queries: {e}")

    def _get_query_patterns_for_table(self, table_name: str) -> List[str]:
        return [
            f"SELECT * FROM {table_name} WHERE id = %s",
            f"SELECT * FROM {table_name} WHERE created_at > %s",
            f"SELECT * FROM {table_name} ORDER BY created_at DESC LIMIT 10",
            f"SELECT COUNT(*) FROM {table_name} WHERE status = %s",
        ]

    def get_database_health(self, alias: str = "default") -> Dict:
        try:
            metrics = performance_monitor.collect_metrics(alias)
            alerts = performance_monitor.check_alerts(metrics)
            with connection_pool.get_cursor(alias) as cursor:
                cursor.execute()
                health_info = cursor.fetchone()
            return {
                "status": "healthy" if not alerts else "warning",
                "metrics": metrics,
                "alerts": alerts,
                "health_info": health_info,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logging.error(f"Failed to get database health: {e}")
            return {"status": "error", "error": str(e)}


database_optimizer = DatabaseOptimizer()
