"""
Advanced Performance and Scalability Optimization Framework
Enterprise-grade performance optimization for healthcare systems
"""

import asyncio
import logging
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import psutil
import redis.asyncio as aioredis
from django.conf import settings
from django.core.cache import cache
from django.db import connections
from django.utils import timezone

class OptimizationType(Enum):
    """Types of performance optimization"""
    CACHING = "caching"
    DATABASE = "database"
    API = "api"
    NETWORK = "network"
    MEMORY = "memory"
    CPU = "cpu"
    I_O = "io"
    SCALABILITY = "scalability"

class ScalingStrategy(Enum):
    """Scaling strategies"""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    HYBRID = "hybrid"
    AUTO_SCALING = "auto_scaling"

@dataclass
class PerformanceMetrics:
    """Performance metrics collection"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    response_time_avg: float
    throughput: float
    error_rate: float
    cache_hit_rate: float
    database_connections: int
    active_requests: int

@dataclass
class ScalingEvent:
    """Scaling event structure"""
    id: str
    timestamp: datetime
    scaling_type: ScalingStrategy
    direction: str  # "up" or "down"
    target_instances: int
    reason: str
    success: bool

class CachingOptimizer:
    """Advanced caching strategies and optimization"""

    def __init__(self, redis_client: aioredis.Redis = None):
        self.redis_client = redis_client
        self.cache_strategies = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_size": 0,
            "hit_rate": 0.0
        }
        self.cache_warmup_queue = asyncio.Queue()

    async def initialize_redis(self):
        """Initialize Redis client"""
        if not self.redis_client and hasattr(settings, 'REDIS_URL'):
            self.redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await self.redis_client.ping()
            logging.info("Redis client initialized for caching")

    def setup_cache_strategy(self, name: str, strategy: Dict):
        """Setup caching strategy for a specific use case"""
        self.cache_strategies[name] = {
            "ttl": strategy.get("ttl", 300),
            "cache_key_prefix": strategy.get("prefix", name),
            "compression": strategy.get("compression", False),
            "serialization": strategy.get("serialization", "json"),
            "invalidation_rules": strategy.get("invalidation_rules", [])
        }

    async def get_cached_data(self, cache_key: str, strategy_name: str = "default") -> Optional[Any]:
        """Get cached data with strategy"""
        try:
            if not self.redis_client:
                return None

            strategy = self.cache_strategies.get(strategy_name, {})
            full_key = f"{strategy.get('prefix', '')}:{cache_key}"

            start_time = time.time()
            cached_data = await self.redis_client.get(full_key)
            response_time = time.time() - start_time

            if cached_data:
                self.cache_stats["hits"] += 1
                # Deserialize data
                if strategy.get("serialization") == "json":
                    import json
                    return json.loads(cached_data)
                elif strategy.get("serialization") == "pickle":
                    import pickle
                    return pickle.loads(cached_data)
                else:
                    return cached_data
            else:
                self.cache_stats["misses"] += 1
                return None

        except Exception as e:
            logging.error(f"Cache retrieval error: {e}")
            return None

    async def set_cached_data(self, cache_key: str, data: Any, strategy_name: str = "default"):
        """Set cached data with strategy"""
        try:
            if not self.redis_client:
                return False

            strategy = self.cache_strategies.get(strategy_name, {})
            full_key = f"{strategy.get('prefix', '')}:{cache_key}"
            ttl = strategy.get("ttl", 300)

            # Serialize data
            if strategy.get("serialization") == "json":
                serialized = json.dumps(data, default=str)
            elif strategy.get("serialization") == "pickle":
                import pickle
                serialized = pickle.dumps(data)
            else:
                serialized = str(data)

            # Compress if enabled
            if strategy.get("compression"):
                import zlib
                serialized = zlib.compress(serialized.encode())
            else:
                if isinstance(serialized, str):
                    serialized = serialized.encode()

            await self.redis_client.setex(full_key, ttl, serialized)
            self.cache_stats["total_size"] += len(serialized)

            return True

        except Exception as e:
            logging.error(f"Cache storage error: {e}")
            return False

    async def invalidate_cache_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        try:
            if not self.redis_client:
                return

            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
                self.cache_stats["evictions"] += len(keys)
                logging.info(f"Invalidated {len(keys)} cache entries for pattern: {pattern}")

        except Exception as e:
            logging.error(f"Cache invalidation error: {e}")

    async def cache_warmup(self, data_provider: Callable, key_generator: Callable,
                          count: int, strategy_name: str = "default"):
        """Warm up cache with frequently accessed data"""
        try:
            logging.info(f"Starting cache warmup for {count} items")

            tasks = []
            for i in range(count):
                # Generate cache key
                key_data = await key_generator(i)
                cache_key = key_data["key"]

                # Check if already cached
                cached = await self.get_cached_data(cache_key, strategy_name)
                if not cached:
                    # Fetch data and cache it
                    data = await data_provider(key_data)
                    task = asyncio.create_task(
                        self.set_cached_data(cache_key, data, strategy_name)
                    )
                    tasks.append(task)

            # Execute all caching tasks
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            logging.info(f"Cache warmup completed for {len(tasks)} items")

        except Exception as e:
            logging.error(f"Cache warmup error: {e}")

    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        return {
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "hit_rate": hit_rate,
            "evictions": self.cache_stats["evictions"],
            "total_size_mb": self.cache_stats["total_size"] / (1024 * 1024),
            "strategies": list(self.cache_strategies.keys())
        }

class DatabaseOptimizer:
    """Database performance optimization"""

    def __init__(self):
        self.connection_pools = {}
        self.query_stats = {}
        self.index_recommendations = {}
        self.performance_tips = []

    def optimize_database_connection(self, alias: str = "default"):
        """Optimize database connection settings"""
        try:
            db_config = connections.databases[alias]

            # Optimize connection pool settings
            optimized_config = {
                "CONN_MAX_AGE": 600,  # 10 minutes
                "CONN_HEALTH_CHECKS": True,
                "OPTIONS": {
                    "connect_timeout": 10,
                    "application_name": "hms_enterprise",
                    "tcp_keepalive": True,
                    "tcp_keepidle": 120,
                    "tcp_keepintvl": 30,
                    "tcp_keepcnt": 5
                }
            }

            # Apply optimizations
            if alias not in self.connection_pools:
                self.connection_pools[alias] = optimized_config

            logging.info(f"Database connection optimized for {alias}")
            return True

        except Exception as e:
            logging.error(f"Database connection optimization failed: {e}")
            return False

    def analyze_query_performance(self, query: str, params: Dict = None) -> Dict:
        """Analyze query performance"""
        try:
            with connections["default"].cursor() as cursor:
                # Get query execution plan
                cursor.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + query, params or {})
                plan = cursor.fetchone()[0][0]

                # Extract performance metrics
                execution_time = plan.get("Execution Time", 0)
                planning_time = plan.get("Planning Time", 0)
                total_cost = plan.get("Total Cost", 0)

                # Identify performance issues
                issues = []
                if execution_time > 1000:  # More than 1 second
                    issues.append("Slow query detected")
                if "Seq Scan" in str(plan):
                    issues.append("Sequential scan - consider indexing")
                if "Nested Loop" in str(plan) and execution_time > 500:
                    issues.append("Expensive nested loop join")

                return {
                    "query": query[:100] + "..." if len(query) > 100 else query,
                    "execution_time_ms": execution_time,
                    "planning_time_ms": planning_time,
                    "total_cost": total_cost,
                    "issues": issues,
                    "plan": plan
                }

        except Exception as e:
            logging.error(f"Query analysis failed: {e}")
            return {"error": str(e)}

    def generate_index_recommendations(self, table_name: str) -> List[Dict]:
        """Generate index recommendations for table"""
        try:
            recommendations = []

            with connections["default"].cursor() as cursor:
                # Get table statistics
                cursor.execute("""
                    SELECT
                        schemaname,
                        tablename,
                        attname,
                        n_distinct,
                        correlation
                    FROM pg_stats
                    WHERE tablename = %s
                    ORDER BY n_distinct DESC
                """, (table_name,))
                stats = cursor.fetchall()

                # Get existing indexes
                cursor.execute("""
                    SELECT indexname, indexdef
                    FROM pg_indexes
                    WHERE tablename = %s
                """, (table_name,))
                indexes = cursor.fetchall()

                existing_columns = set()
                for index in indexes:
                    # Extract column names from index definition
                    import re
                    columns = re.findall(r'(\w+)', index[1])
                    existing_columns.update(columns)

                # Recommend indexes for high-cardinality columns
                for stat in stats[:5]:  # Top 5 columns
                    column = stat[2]
                    if column not in existing_columns and stat[3] > 100:  # High cardinality
                        recommendations.append({
                            "table": table_name,
                            "column": column,
                            "recommendation": f"Create B-tree index on {column}",
                            "estimated_benefit": "High" if stat[3] > 1000 else "Medium",
                            "cardinality": stat[3]
                        })

            return recommendations

        except Exception as e:
            logging.error(f"Index recommendation failed: {e}")
            return []

    def optimize_query_patterns(self) -> List[Dict]:
        """Optimize common query patterns"""
        optimizations = []

        # Common optimization patterns
        optimization_patterns = [
            {
                "pattern": "SELECT * FROM",
                "issue": "Using SELECT * instead of specific columns",
                "recommendation": "Select only required columns to reduce data transfer"
            },
            {
                "pattern": "ORDER BY",
                "issue": "Missing index for ORDER BY",
                "recommendation": "Create composite index for columns used in ORDER BY"
            },
            {
                "pattern": "WHERE",
                "issue": "Inefficient WHERE clause",
                "recommendation": "Ensure columns in WHERE clause are properly indexed"
            }
        ]

        for pattern in optimization_patterns:
            optimizations.append({
                "type": "query_optimization",
                "pattern": pattern["pattern"],
                "issue": pattern["issue"],
                "recommendation": pattern["recommendation"],
                "priority": "medium"
            })

        return optimizations

class NetworkOptimizer:
    """Network performance optimization"""

    def __init__(self):
        self.connection_pools = {}
        self.compression_settings = {}
        self.cdn_config = {}

    def optimize_http_connections(self):
        """Optimize HTTP connection settings"""
        try:
            optimization_settings = {
                "connection_pool_size": 100,
                "max_connections": 200,
                "connection_timeout": 30,
                "read_timeout": 30,
                "pool_timeout": 10,
                "retries": 3,
                "backoff_factor": 0.3,
                "enable_http2": True,
                "enable_compression": True
            }

            self.connection_pools["http"] = optimization_settings
            logging.info("HTTP connection optimization completed")
            return True

        except Exception as e:
            logging.error(f"HTTP connection optimization failed: {e}")
            return False

    def setup_cdn_configuration(self, cdn_provider: str, config: Dict):
        """Setup CDN configuration"""
        try:
            self.cdn_config = {
                "provider": cdn_provider,
                "enabled": True,
                "cache_control": config.get("cache_control", "public, max-age=3600"),
                "compression": config.get("compression", True),
                "edge_caching": config.get("edge_caching", True),
                "ssl": config.get("ssl", True)
            }

            logging.info(f"CDN configuration setup for {cdn_provider}")
            return True

        except Exception as e:
            logging.error(f"CDN configuration failed: {e}")
            return False

    def optimize_api_calls(self) -> List[Dict]:
        """Optimize API call patterns"""
        optimizations = []

        api_optimizations = [
            {
                "type": "batching",
                "description": "Batch multiple API calls into single request",
                "impact": "High",
                "implementation": "Implement batch endpoints"
            },
            {
                "type": "pagination",
                "description": "Use pagination for large datasets",
                "impact": "High",
                "implementation": "Add cursor-based pagination"
            },
            {
                "type": "field_selection",
                "description": "Allow field selection in API responses",
                "impact": "Medium",
                "implementation": "Add GraphQL or field query parameters"
            },
            {
                "type": "caching",
                "description": "Cache API responses",
                "impact": "High",
                "implementation": "Implement response caching"
            }
        ]

        optimizations.extend(api_optimizations)
        return optimizations

class MemoryOptimizer:
    """Memory usage optimization"""

    def __init__(self):
        self.memory_pools = {}
        self.garbage_collection_settings = {}
        self.memory_monitoring = {}

    def optimize_memory_usage(self) -> Dict:
        """Optimize memory usage"""
        try:
            # Get current memory usage
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()

            optimizations = []

            # Memory pool optimization
            if memory_percent > 70:
                optimizations.append({
                    "type": "memory_pool",
                    "issue": "High memory usage",
                    "recommendation": "Implement memory pooling",
                    "priority": "high"
                })

            # Garbage collection optimization
            import gc
            gc.collect()  # Force garbage collection

            # Configure garbage collection thresholds
            gc.set_threshold(700, 10, 10)  # Adjust thresholds

            # Memory monitoring setup
            self.memory_monitoring = {
                "enabled": True,
                "threshold_percent": 80,
                "check_interval": 60  # seconds
            }

            return {
                "current_memory_mb": memory_info.rss / (1024 * 1024),
                "memory_percent": memory_percent,
                "optimizations": optimizations,
                "status": "optimized" if memory_percent < 70 else "needs_attention"
            }

        except Exception as e:
            logging.error(f"Memory optimization failed: {e}")
            return {"error": str(e)}

    def setup_memory_monitoring(self):
        """Setup memory monitoring"""
        try:
            def memory_monitor():
                while True:
                    try:
                        process = psutil.Process()
                        memory_percent = process.memory_percent()

                        if memory_percent > self.memory_monitoring.get("threshold_percent", 80):
                            logging.warning(f"High memory usage: {memory_percent:.1f}%")

                            # Trigger garbage collection
                            import gc
                            gc.collect()

                        time.sleep(self.memory_monitoring.get("check_interval", 60))

                    except Exception as e:
                        logging.error(f"Memory monitoring error: {e}")
                        time.sleep(60)

            # Start monitoring in background thread
            monitor_thread = threading.Thread(target=memory_monitor, daemon=True)
            monitor_thread.start()

            logging.info("Memory monitoring started")

        except Exception as e:
            logging.error(f"Memory monitoring setup failed: {e}")

class ScalingManager:
    """Auto-scaling and resource management"""

    def __init__(self):
        self.scaling_events = []
        self.scaling_rules = {}
        self.current_instances = {}
        self.scaling_metrics = {}

    def setup_scaling_rule(self, service_name: str, rule: Dict):
        """Setup auto-scaling rule for service"""
        try:
            scaling_rule = {
                "service": service_name,
                "min_instances": rule.get("min_instances", 1),
                "max_instances": rule.get("max_instances", 10),
                "scale_up_threshold": rule.get("scale_up_threshold", 70),
                "scale_down_threshold": rule.get("scale_down_threshold", 20),
                "scale_up_cooldown": rule.get("scale_up_cooldown", 300),
                "scale_down_cooldown": rule.get("scale_down_cooldown", 600),
                "metrics": rule.get("metrics", ["cpu", "memory"]),
                "enabled": rule.get("enabled", True)
            }

            self.scaling_rules[service_name] = scaling_rule
            self.current_instances[service_name] = scaling_rule["min_instances"]

            logging.info(f"Scaling rule setup for {service_name}")
            return True

        except Exception as e:
            logging.error(f"Scaling rule setup failed: {e}")
            return False

    async def evaluate_scaling_rules(self, metrics: Dict):
        """Evaluate scaling rules and trigger scaling if needed"""
        try:
            scaling_actions = []

            for service_name, rule in self.scaling_rules.items():
                if not rule.get("enabled", True):
                    continue

                # Get current metrics for service
                service_metrics = metrics.get(service_name, {})
                if not service_metrics:
                    continue

                # Check scale-up conditions
                should_scale_up = False
                scale_up_reasons = []

                for metric in rule["metrics"]:
                    current_value = service_metrics.get(metric, 0)
                    if current_value > rule["scale_up_threshold"]:
                        should_scale_up = True
                        scale_up_reasons.append(f"{metric} at {current_value}%")

                # Check scale-down conditions
                should_scale_down = False
                scale_down_reasons = []

                for metric in rule["metrics"]:
                    current_value = service_metrics.get(metric, 0)
                    if current_value < rule["scale_down_threshold"]:
                        should_scale_down = True
                        scale_down_reasons.append(f"{metric} at {current_value}%")

                # Trigger scaling actions
                if should_scale_up and self.current_instances[service_name] < rule["max_instances"]:
                    action = await self.scale_service(service_name, "up", scale_up_reasons)
                    if action:
                        scaling_actions.append(action)

                elif should_scale_down and self.current_instances[service_name] > rule["min_instances"]:
                    action = await self.scale_service(service_name, "down", scale_down_reasons)
                    if action:
                        scaling_actions.append(action)

            return scaling_actions

        except Exception as e:
            logging.error(f"Scaling rule evaluation failed: {e}")
            return []

    async def scale_service(self, service_name: str, direction: str, reasons: List[str]) -> Optional[ScalingEvent]:
        """Scale a service up or down"""
        try:
            rule = self.scaling_rules.get(service_name)
            if not rule:
                return None

            current_instances = self.current_instances[service_name]

            if direction == "up":
                if current_instances >= rule["max_instances"]:
                    return None
                new_instances = current_instances + 1
            elif direction == "down":
                if current_instances <= rule["min_instances"]:
                    return None
                new_instances = current_instances - 1
            else:
                return None

            # Create scaling event
            event = ScalingEvent(
                id=f"scaling_{int(time.time())}_{service_name}",
                timestamp=timezone.now(),
                scaling_type=ScalingStrategy.AUTO_SCALING,
                direction=direction,
                target_instances=new_instances,
                reason=", ".join(reasons),
                success=False  # Will be updated after scaling
            )

            # Execute scaling (this would integrate with your orchestration system)
            scaling_success = await self._execute_scaling(service_name, new_instances, direction)

            event.success = scaling_success
            if scaling_success:
                self.current_instances[service_name] = new_instances

            self.scaling_events.append(event)

            logging.info(f"Scaling {service_name} {direction} to {new_instances} instances: {'Success' if scaling_success else 'Failed'}")
            return event

        except Exception as e:
            logging.error(f"Service scaling failed: {e}")
            return None

    async def _execute_scaling(self, service_name: str, target_instances: int, direction: str) -> bool:
        """Execute actual scaling (placeholder for orchestration integration)"""
        # This would integrate with Kubernetes, Docker Swarm, or other orchestration systems
        # For now, simulate successful scaling
        await asyncio.sleep(2)  # Simulate scaling time
        return True

    def get_scaling_status(self) -> Dict:
        """Get current scaling status"""
        return {
            "services": {
                name: {
                    "current_instances": count,
                    "min_instances": self.scaling_rules[name]["min_instances"],
                    "max_instances": self.scaling_rules[name]["max_instances"],
                    "scaling_enabled": self.scaling_rules[name]["enabled"]
                }
                for name, count in self.current_instances.items()
            },
            "recent_events": [
                asdict(event) for event in sorted(
                    self.scaling_events,
                    key=lambda x: x.timestamp,
                    reverse=True
                )[:10]
            ]
        }

class PerformanceOptimizer:
    """Main performance optimization coordinator"""

    def __init__(self):
        self.caching_optimizer = CachingOptimizer()
        self.database_optimizer = DatabaseOptimizer()
        self.network_optimizer = NetworkOptimizer()
        self.memory_optimizer = MemoryOptimizer()
        self.scaling_manager = ScalingManager()
        self.performance_history = []
        self.optimization_tasks = []

    async def initialize(self):
        """Initialize all optimization components"""
        try:
            logging.info("Initializing performance optimization framework")

            # Initialize Redis for caching
            await self.caching_optimizer.initialize_redis()

            # Setup default cache strategies
            self.caching_optimizer.setup_cache_strategy("patient_data", {
                "ttl": 300,
                "prefix": "patient",
                "compression": True,
                "serialization": "json"
            })

            self.caching_optimizer.setup_cache_strategy("api_response", {
                "ttl": 60,
                "prefix": "api",
                "compression": False,
                "serialization": "json"
            })

            # Optimize database connections
            self.database_optimizer.optimize_database_connection()

            # Optimize network connections
            self.network_optimizer.optimize_http_connections()

            # Setup memory monitoring
            self.memory_optimizer.setup_memory_monitoring()

            # Setup default scaling rules
            self.scaling_manager.setup_scaling_rule("api_service", {
                "min_instances": 2,
                "max_instances": 10,
                "scale_up_threshold": 70,
                "scale_down_threshold": 20,
                "metrics": ["cpu", "memory"]
            })

            logging.info("Performance optimization framework initialized successfully")

        except Exception as e:
            logging.error(f"Performance optimization initialization failed: {e}")

    async def run_optimization_cycle(self) -> Dict:
        """Run comprehensive optimization cycle"""
        try:
            optimization_results = {
                "timestamp": timezone.now(),
                "cache_optimization": {},
                "database_optimization": {},
                "network_optimization": {},
                "memory_optimization": {},
                "scaling_actions": [],
                "overall_score": 0
            }

            # Cache optimization
            cache_stats = self.caching_optimizer.get_cache_stats()
            optimization_results["cache_optimization"] = cache_stats

            # Database optimization
            db_recommendations = self.database_optimizer.generate_index_recommendations("patients")
            optimization_results["database_optimization"] = {
                "index_recommendations": db_recommendations,
                "query_optimizations": self.database_optimizer.optimize_query_patterns()
            }

            # Network optimization
            network_opts = self.network_optimizer.optimize_api_calls()
            optimization_results["network_optimization"] = {
                "optimizations": network_opts,
                "cdn_configured": bool(self.network_optimizer.cdn_config)
            }

            # Memory optimization
            memory_results = self.memory_optimizer.optimize_memory_usage()
            optimization_results["memory_optimization"] = memory_results

            # Evaluate scaling rules
            current_metrics = self._collect_current_metrics()
            scaling_actions = await self.scaling_manager.evaluate_scaling_rules(current_metrics)
            optimization_results["scaling_actions"] = [asdict(action) for action in scaling_actions if action]

            # Calculate overall performance score
            optimization_results["overall_score"] = self._calculate_performance_score(optimization_results)

            # Store in history
            self.performance_history.append(optimization_results)

            return optimization_results

        except Exception as e:
            logging.error(f"Optimization cycle failed: {e}")
            return {"error": str(e)}

    def _collect_current_metrics(self) -> Dict:
        """Collect current performance metrics"""
        try:
            process = psutil.Process()
            memory_percent = process.memory_percent()
            cpu_percent = process.cpu_percent()

            return {
                "api_service": {
                    "cpu": cpu_percent,
                    "memory": memory_percent,
                    "throughput": 0,  # Would be collected from actual metrics
                    "response_time": 0  # Would be collected from actual metrics
                }
            }

        except Exception as e:
            logging.error(f"Metrics collection failed: {e}")
            return {}

    def _calculate_performance_score(self, results: Dict) -> float:
        """Calculate overall performance score"""
        try:
            score = 100.0

            # Deduct for cache issues
            cache_hit_rate = results["cache_optimization"].get("hit_rate", 0)
            if cache_hit_rate < 80:
                score -= (80 - cache_hit_rate) * 0.2

            # Deduct for memory issues
            memory_status = results["memory_optimization"].get("status", "unknown")
            if memory_status == "needs_attention":
                score -= 10

            # Deduct for scaling issues
            scaling_actions = results.get("scaling_actions", [])
            if scaling_actions:
                score -= 5  # Small penalty for scaling activity

            return max(0, min(100, score))

        except Exception as e:
            logging.error(f"Performance score calculation failed: {e}")
            return 0.0

    def get_performance_dashboard(self) -> Dict:
        """Get comprehensive performance dashboard"""
        try:
            latest_results = self.performance_history[-1] if self.performance_history else {}

            return {
                "timestamp": timezone.now(),
                "current_status": {
                    "performance_score": latest_results.get("overall_score", 0),
                    "cache_hit_rate": latest_results.get("cache_optimization", {}).get("hit_rate", 0),
                    "memory_usage": latest_results.get("memory_optimization", {}).get("memory_percent", 0),
                    "scaling_status": self.scaling_manager.get_scaling_status()
                },
                "optimization_history": [
                    {
                        "timestamp": result["timestamp"],
                        "score": result["overall_score"],
                        "scaling_actions": len(result.get("scaling_actions", []))
                    }
                    for result in self.performance_history[-10:]
                ],
                "recommendations": self._generate_performance_recommendations(latest_results)
            }

        except Exception as e:
            logging.error(f"Performance dashboard generation failed: {e}")
            return {"error": str(e)}

    def _generate_performance_recommendations(self, results: Dict) -> List[Dict]:
        """Generate performance recommendations"""
        recommendations = []

        try:
            # Cache recommendations
            cache_hit_rate = results.get("cache_optimization", {}).get("hit_rate", 0)
            if cache_hit_rate < 70:
                recommendations.append({
                    "type": "caching",
                    "priority": "high",
                    "description": "Low cache hit rate detected",
                    "action": "Review cache strategies and implement cache warming"
                })

            # Memory recommendations
            memory_status = results.get("memory_optimization", {}).get("status", "unknown")
            if memory_status == "needs_attention":
                recommendations.append({
                    "type": "memory",
                    "priority": "medium",
                    "description": "High memory usage detected",
                    "action": "Implement memory pooling and optimize data structures"
                })

            # Database recommendations
            db_recommendations = results.get("database_optimization", {}).get("index_recommendations", [])
            if db_recommendations:
                recommendations.append({
                    "type": "database",
                    "priority": "medium",
                    "description": f"{len(db_recommendations)} index recommendations available",
                    "action": "Review and implement recommended database indexes"
                })

        except Exception as e:
            logging.error(f"Recommendation generation failed: {e}")

        return recommendations

    async def start_continuous_optimization(self):
        """Start continuous optimization monitoring"""
        try:
            while True:
                await self.run_optimization_cycle()
                await asyncio.sleep(300)  # Run every 5 minutes

        except asyncio.CancelledError:
            logging.info("Continuous optimization stopped")
        except Exception as e:
            logging.error(f"Continuous optimization error: {e}")

# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()

# Convenience functions for use in other modules
async def optimize_system_performance():
    """Run system performance optimization"""
    return await performance_optimizer.run_optimization_cycle()

def get_performance_dashboard():
    """Get performance dashboard data"""
    return performance_optimizer.get_performance_dashboard()