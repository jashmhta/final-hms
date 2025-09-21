import asyncio
import json
import logging
import queue
import threading
import time
import weakref
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

import numpy as np
import pandas as pd
import psutil
import redis

from django.conf import settings
from django.core.cache import cache

from .feature_engineering import FeatureEngineeringPipeline
from .model_registry import ModelRegistry

logger = logging.getLogger(__name__)


class InferencePriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    BACKGROUND = "background"


class InferenceMode(Enum):
    REAL_TIME = "real_time"
    BATCH = "batch"
    STREAMING = "streaming"
    ASYNC = "async"


@dataclass
class InferenceRequest:
    request_id: str
    model_id: str
    input_data: Union[Dict, pd.DataFrame]
    priority: InferencePriority
    mode: InferenceMode
    timeout_ms: int
    metadata: Optional[Dict] = None
    callback: Optional[Callable] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class InferenceResponse:
    request_id: str
    model_id: str
    predictions: Any
    confidence: float
    processing_time_ms: float
    metadata: Optional[Dict] = None
    error: Optional[str] = None


class InferenceEngine:
    _instances = weakref.WeakSet()

    def __new__(cls, *args, **kwargs):
        # Singleton pattern with weak references
        instance = super().__new__(cls)
        cls._instances.add(instance)
        return instance

    def __init__(
        self,
        max_workers: int = 10,
        cache_size: int = 10000,
        enable_gpu: bool = True,
        redis_host: str = None,
    ):
        self.model_registry = ModelRegistry()
        self.feature_pipeline = FeatureEngineeringPipeline()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.queues = {
            InferencePriority.CRITICAL: queue.PriorityQueue(maxsize=100),
            InferencePriority.HIGH: queue.PriorityQueue(maxsize=500),
            InferencePriority.NORMAL: queue.PriorityQueue(maxsize=1000),
            InferencePriority.LOW: queue.PriorityQueue(maxsize=2000),
            InferencePriority.BACKGROUND: queue.PriorityQueue(maxsize=5000),
        }
        self.model_cache = {}
        self.cache_size = cache_size
        self.performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }
        self.redis_client = None
        self._redis_pool = None
        if redis_host:
            try:
                self._redis_pool = redis.ConnectionPool(
                    host=redis_host,
                    port=6379,
                    decode_responses=True,
                    max_connections=5
                )
                self.redis_client = redis.Redis(connection_pool=self._redis_pool)
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
                self._redis_pool = None
        self.enable_gpu = enable_gpu and self._check_gpu_availability()
        self.running = True
        self.workers = []
        self._shutdown_event = threading.Event()
        self._cache_lock = threading.RLock()
        self._start_workers()
        self.monitor_thread = threading.Thread(target=self._monitor_performance, daemon=True)
        self.monitor_thread.start()

    def _check_gpu_availability(self) -> bool:
        try:
            import torch

            return torch.cuda.is_available()
        except ImportError:
            return False
        except Exception:
            return False

    def _start_workers(self):
        for priority in InferencePriority:
            worker = threading.Thread(target=self._worker_loop, args=(priority,), daemon=True)
            worker.start()
            self.workers.append(worker)

    def _worker_loop(self, priority: InferencePriority):
        while self.running and not self._shutdown_event.is_set():
            try:
                try:
                    request = self.queues[priority].get(timeout=1.0)
                except queue.Empty:
                    continue

                if request is None or isinstance(request, tuple) and request[1] is None:
                    continue

                # Unpack timestamp and request
                if isinstance(request, tuple):
                    _, request = request

                response = self._process_request(request)
                if request.callback:
                    try:
                        request.callback(response)
                    except Exception as e:
                        logger.error(f"Callback failed for request {request.request_id}: {e}")
                self._update_metrics(response)

            except Exception as e:
                if not self._shutdown_event.is_set():
                    logger.error(f"Worker error for priority {priority}: {e}")

    def predict(
        self,
        model_id: str,
        input_data: Union[Dict, pd.DataFrame],
        priority: InferencePriority = InferencePriority.NORMAL,
        mode: InferenceMode = InferenceMode.REAL_TIME,
        timeout_ms: int = 1000,
        metadata: Optional[Dict] = None,
        async_callback: Optional[Callable] = None,
    ) -> Union[InferenceResponse, str]:
        try:
            request_id = f"req_{int(time.time() * 1000000)}_{hash(str(input_data)) % 10000}"
            request = InferenceRequest(
                request_id=request_id,
                model_id=model_id,
                input_data=input_data,
                priority=priority,
                mode=mode,
                timeout_ms=timeout_ms,
                metadata=metadata or {},
                callback=async_callback,
            )
            if mode == InferenceMode.REAL_TIME:
                cache_key = self._generate_cache_key(model_id, input_data)
                cached_response = self._get_cached_prediction(cache_key)
                if cached_response:
                    self.performance_metrics["cache_hits"] += 1
                    if async_callback:
                        async_callback(cached_response)
                        return request_id
                    else:
                        return cached_response
                else:
                    self.performance_metrics["cache_misses"] += 1
            if not async_callback and mode == InferenceMode.REAL_TIME:
                response = self._process_request(request)
                self._update_metrics(response)
                if not response.error:
                    self._cache_prediction(cache_key, response)
                return response
            # Prevent queue overflow
            try:
                self.queues[priority].put_nowait((time.time(), request))
            except queue.Full:
                logger.warning(f"Queue {priority} is full, dropping request")
                return InferenceResponse(
                    request_id=request.request_id,
                    model_id=model_id,
                    predictions=None,
                    confidence=0.0,
                    processing_time_ms=0,
                    error="Queue full - server overloaded"
                )
            if async_callback:
                return request_id
            else:
                return self._wait_for_completion(request_id, timeout_ms)
        except Exception as e:
            logger.error(f"Prediction request failed: {e}")
            return InferenceResponse(
                request_id="error",
                model_id=model_id,
                predictions=None,
                confidence=0.0,
                processing_time_ms=0,
                error=str(e),
            )

    def predict_batch(
        self,
        model_id: str,
        input_data_list: List[Union[Dict, pd.DataFrame]],
        priority: InferencePriority = InferencePriority.NORMAL,
        timeout_ms: int = 5000,
    ) -> List[InferenceResponse]:
        try:
            if not input_data_list:
                return []
            responses = []
            futures = []
            for i, input_data in enumerate(input_data_list):
                future = self.executor.submit(
                    self.predict,
                    model_id=model_id,
                    input_data=input_data,
                    priority=priority,
                    mode=InferenceMode.BATCH,
                    timeout_ms=timeout_ms,
                )
                futures.append(future)
            for future in as_completed(futures, timeout=timeout_ms / 1000):
                try:
                    response = future.result()
                    responses.append(response)
                except Exception as e:
                    responses.append(
                        InferenceResponse(
                            request_id="batch_error",
                            model_id=model_id,
                            predictions=None,
                            confidence=0.0,
                            processing_time_ms=0,
                            error=str(e),
                        )
                    )
            return responses
        except Exception as e:
            logger.error(f"Batch prediction failed: {e}")
            return [
                InferenceResponse(
                    request_id="batch_error",
                    model_id=model_id,
                    predictions=None,
                    confidence=0.0,
                    processing_time_ms=0,
                    error=str(e),
                )
            ]

    def predict_stream(
        self,
        model_id: str,
        data_generator: callable,
        priority: InferencePriority = InferencePriority.NORMAL,
        callback: Optional[Callable] = None,
    ) -> str:
        stream_id = f"stream_{int(time.time() * 1000000)}"

        def stream_processor():
            try:
                for input_data in data_generator():
                    response = self.predict(
                        model_id=model_id,
                        input_data=input_data,
                        priority=priority,
                        mode=InferenceMode.STREAMING,
                        async_callback=callback,
                    )
                    yield response
            except Exception as e:
                logger.error(f"Stream processing error for {stream_id}: {e}")

        stream_thread = threading.Thread(target=stream_processor, daemon=True)
        stream_thread.start()
        return stream_id

    def _process_request(self, request: InferenceRequest) -> InferenceResponse:
        start_time = time.time()
        try:
            model_info = self._get_cached_model(request.model_id)
            if not model_info:
                raise ValueError(f"Model not found: {request.model_id}")
            model = model_info["model_object"]
            if isinstance(request.input_data, dict):
                features_result = self.feature_pipeline.engineer_features(request.input_data)
                if "error" in features_result:
                    raise ValueError(features_result["error"])
                features_df = features_result["features"]
            else:
                features_df = request.input_data
            if isinstance(features_df, pd.DataFrame):
                features_array = features_df.values
            else:
                features_array = np.array(features_df)
            predictions, confidence = self._make_prediction(model, features_array)
            processing_time = (time.time() - start_time) * 1000
            return InferenceResponse(
                request_id=request.request_id,
                model_id=request.model_id,
                predictions=predictions,
                confidence=confidence,
                processing_time_ms=processing_time,
                metadata=request.metadata,
            )
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Request processing failed for {request.request_id}: {e}")
            return InferenceResponse(
                request_id=request.request_id,
                model_id=request.model_id,
                predictions=None,
                confidence=0.0,
                processing_time_ms=processing_time,
                error=str(e),
            )

    def _make_prediction(self, model: Any, features: np.ndarray) -> tuple:
        try:
            if hasattr(model, "predict_proba"):
                probabilities = model.predict_proba(features)
                predictions = model.predict(features)
                confidence = float(np.max(probabilities))
            elif hasattr(model, "predict"):
                predictions = model.predict(features)
                confidence = 1.0
            elif hasattr(model, "__call__"):
                result = model(features)
                if isinstance(result, tuple):
                    predictions, confidence = result
                else:
                    predictions = result
                    confidence = 1.0
            else:
                raise ValueError("Model does not have prediction method")
            return predictions, confidence
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise

    def _get_cached_model(self, model_id: str) -> Optional[Dict]:
        try:
            if model_id in self.model_cache:
                return self.model_cache[model_id]
            model_result = self.model_registry.get_model(model_id, load_model=True)
            if "error" in model_result:
                return None
            if len(self.model_cache) >= self.cache_size:
                oldest_key = next(iter(self.model_cache))
                del self.model_cache[oldest_key]
            self.model_cache[model_id] = model_result
            return model_result
        except Exception as e:
            logger.error(f"Model loading failed: {e}")
            return None

    def _generate_cache_key(self, model_id: str, input_data: Union[Dict, pd.DataFrame]) -> str:
        import hashlib

        if isinstance(input_data, dict):
            data_str = json.dumps(input_data, sort_keys=True)
        elif isinstance(input_data, pd.DataFrame):
            data_str = input_data.to_json()
        else:
            data_str = str(input_data)
        hash_input = f"{model_id}:{data_str}"
        return hashlib.md5(hash_input.encode()).hexdigest()

    def _get_cached_prediction(self, cache_key: str) -> Optional[InferenceResponse]:
        try:
            cached_data = cache.get(f"prediction_{cache_key}")
            if cached_data:
                return InferenceResponse(**cached_data)
            if self.redis_client:
                cached_data = self.redis_client.get(f"prediction_{cache_key}")
                if cached_data:
                    return InferenceResponse(**json.loads(cached_data))
            return None
        except Exception as e:
            logger.error(f"Cache retrieval failed: {e}")
            return None

    def _cache_prediction(self, cache_key: str, response: InferenceResponse):
        try:
            cache_timeout = 300
            response_dict = {
                "request_id": response.request_id,
                "model_id": response.model_id,
                "predictions": response.predictions,
                "confidence": response.confidence,
                "processing_time_ms": response.processing_time_ms,
                "metadata": response.metadata,
                "error": response.error,
            }
            cache.set(f"prediction_{cache_key}", response_dict, cache_timeout)
            if self.redis_client:
                self.redis_client.setex(
                    f"prediction_{cache_key}",
                    cache_timeout,
                    json.dumps(response_dict, default=str),
                )
        except Exception as e:
            logger.error(f"Cache storage failed: {e}")

    def _wait_for_completion(self, request_id: str, timeout_ms: int) -> InferenceResponse:
        start_time = time.time()
        timeout_seconds = timeout_ms / 1000.0
        while time.time() - start_time < timeout_seconds:
            time.sleep(0.01)
        return InferenceResponse(
            request_id=request_id,
            model_id="unknown",
            predictions=None,
            confidence=0.0,
            processing_time_ms=timeout_ms,
            error="Timeout reached",
        )

    def _update_metrics(self, response: InferenceResponse):
        self.performance_metrics["total_requests"] += 1
        if response.error:
            self.performance_metrics["failed_requests"] += 1
        else:
            self.performance_metrics["successful_requests"] += 1
        total_requests = self.performance_metrics["total_requests"]
        current_avg = self.performance_metrics["average_response_time"]
        new_time = response.processing_time_ms
        self.performance_metrics["average_response_time"] = (
            current_avg * (total_requests - 1) + new_time
        ) / total_requests

    def _monitor_performance(self):
        while self.running:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent
                disk_usage = psutil.disk_usage("/").percent
                logger.info(
                    f"Performance Metrics: "
                    f"CPU: {cpu_percent}%, "
                    f"Memory: {memory_percent}%, "
                    f"Disk: {disk_usage}%, "
                    f"Requests: {self.performance_metrics['total_requests']}, "
                    f"Success Rate: {self.performance_metrics['successful_requests'] / max(1, self.performance_metrics['total_requests']) * 100:.1f}%, "
                    f"Avg Response: {self.performance_metrics['average_response_time']:.1f}ms"
                )
                if cpu_percent > 90 or memory_percent > 90:
                    logger.warning("High resource usage detected")
                    self._handle_performance_degradation()
                time.sleep(60)
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                time.sleep(60)

    def _handle_performance_degradation(self):
        logger.info("Handling performance degradation")
        if psutil.virtual_memory().percent > 90:
            self.model_cache.clear()
            cache.clear()
            if self.redis_client:
                self.redis_client.flushdb()
        for priority, queue in self.queues.items():
            if queue.qsize() > queue.maxsize * 0.8:
                logger.warning(f"Queue size high for priority {priority}: {queue.qsize()}")

    def get_performance_metrics(self) -> Dict:
        return {
            **self.performance_metrics,
            "system_metrics": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
                "active_workers": len([w for w in self.workers if w.is_alive()]),
                "queue_sizes": {priority.name: queue.qsize() for priority, queue in self.queues.items()},
                "model_cache_size": len(self.model_cache),
                "gpu_available": self.enable_gpu,
            },
            "timestamp": datetime.now().isoformat(),
        }

    def clear_cache(self):
        """Safely clear all caches with proper cleanup."""
        with self._cache_lock:
            self.model_cache.clear()
            cache.clear()
            if self.redis_client:
                try:
                    self.redis_client.flushdb()
                except Exception as e:
                    logger.error(f"Redis flush failed: {e}")
        logger.info("Cache cleared")

    def shutdown(self):
        """Graceful shutdown with proper resource cleanup."""
        logger.info("Shutting down inference engine")

        # Signal shutdown to all threads
        self.running = False
        self._shutdown_event.set()

        # Clear queues to unblock workers
        for priority_queue in self.queues.values():
            try:
                while not priority_queue.empty():
                    priority_queue.get_nowait()
            except queue.Empty:
                pass

        # Send shutdown signals to workers
        for priority in InferencePriority:
            try:
                self.queues[priority].put_nowait((time.time(), None))
            except queue.Full:
                pass

        # Wait for workers to finish
        for worker in self.workers:
            try:
                worker.join(timeout=5.0)
                if worker.is_alive():
                    logger.warning(f"Worker thread {worker.name} did not shutdown gracefully")
            except Exception as e:
                logger.error(f"Error joining worker thread: {e}")

        # Shutdown executor
        try:
            self.executor.shutdown(wait=True, cancel_futures=True)
        except Exception as e:
            logger.error(f"Executor shutdown failed: {e}")
            try:
                self.executor.shutdown(wait=False)
            except:
                pass

        # Cleanup Redis connections
        if self._redis_pool:
            try:
                self._redis_pool.disconnect()
            except Exception as e:
                logger.error(f"Redis pool disconnect failed: {e}")

        # Clear caches
        self.clear_cache()

        # Clear worker list
        self.workers.clear()

        logger.info("Inference engine shutdown complete")

    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            if hasattr(self, 'running') and self.running:
                self.shutdown()
        except:
            pass  # Ignore errors during destruction


inference_engine = None


def get_inference_engine() -> InferenceEngine:
    global inference_engine
    if inference_engine is None:
        inference_engine = InferenceEngine()
    return inference_engine


def initialize_inference_engine(**kwargs):
    global inference_engine
    inference_engine = InferenceEngine(**kwargs)
    return inference_engine
