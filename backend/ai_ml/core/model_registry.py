"""
model_registry module
"""

import hashlib
import json
import logging
import os
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import boto3
import mlflow
import mlflow.pyfunc
import mlflow.sklearn
from botocore.exceptions import ClientError

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class ModelRegistry:
    def __init__(self, registry_path: Optional[str] = None):
        self.registry_path = registry_path or os.path.join(
            settings.BASE_DIR, "ml_models"
        )
        self.models_db_path = os.path.join(self.registry_path, "models_registry.json")
        self.registry_cache = {}
        self._initialize_registry()
        self._setup_mlflow()

    def _initialize_registry(self):
        os.makedirs(self.registry_path, exist_ok=True)
        os.makedirs(os.path.join(self.registry_path, "production"), exist_ok=True)
        os.makedirs(os.path.join(self.registry_path, "staging"), exist_ok=True)
        os.makedirs(os.path.join(self.registry_path, "development"), exist_ok=True)
        if not os.path.exists(self.models_db_path):
            self._create_models_database()

    def _create_models_database(self):
        initial_db = {
            "models": {},
            "deployments": {},
            "last_updated": datetime.now().isoformat(),
            "version": "1.0",
        }
        self._save_models_database(initial_db)

    def _load_models_database(self) -> Dict:
        try:
            with open(self.models_db_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._create_models_database()
            return self._load_models_database()

    def _save_models_database(self, db_data: Dict):
        with open(self.models_db_path, "w") as f:
            json.dump(db_data, f, indent=2)

    def _setup_mlflow(self):
        try:
            mlflow.set_tracking_uri(f"file://{self.registry_path}/mlruns")
        except Exception as e:
            logger.warning(f"MLflow setup failed: {e}")

    def register_model(
        self,
        model_name: str,
        model: Any,
        model_type: str,
        model_version: str,
        environment: str = "development",
        metadata: Optional[Dict] = None,
        model_file: Optional[str] = None,
    ) -> Dict:
        try:
            if environment not in ["development", "staging", "production"]:
                raise ValueError(f"Invalid environment: {environment}")
            model_id = self._generate_model_id(model_name, model_version)
            if model_file is None:
                model_file = self._save_model_file(model, model_name, model_version)
            model_hash = self._calculate_model_hash(model_file)
            model_metadata = {
                "model_id": model_id,
                "model_name": model_name,
                "model_type": model_type,
                "model_version": model_version,
                "environment": environment,
                "model_file": model_file,
                "model_hash": model_hash,
                "registered_at": datetime.now().isoformat(),
                "registered_by": "system",
                "status": "active",
                "metadata": metadata or {},
                "performance_metrics": {},
                "deployment_info": {},
            }
            registry_db = self._load_models_database()
            registry_db["models"][model_id] = model_metadata
            self._save_models_database(registry_db)
            self._log_to_mlflow(model_name, model_metadata)
            logger.info(f"Model registered successfully: {model_id}")
            return {
                "model_id": model_id,
                "status": "success",
                "message": "Model registered successfully",
            }
        except Exception as e:
            logger.error(f"Model registration failed: {e}")
            return {"status": "error", "message": str(e)}

    def get_model(self, model_id: str, load_model: bool = True) -> Dict:
        try:
            cache_key = f"model_{model_id}"
            cached_result = cache.get(cache_key)
            if cached_result and not load_model:
                return cached_result
            registry_db = self._load_models_database()
            model_info = registry_db["models"].get(model_id)
            if not model_info:
                raise ValueError(f"Model not found: {model_id}")
            result = {"model_info": model_info, "model_object": None}
            if load_model:
                model_object = self._load_model_file(model_info["model_file"])
                result["model_object"] = model_object
            cache.set(cache_key, result, timeout=3600)
            return result
        except Exception as e:
            logger.error(f"Model retrieval failed: {e}")
            return {"error": str(e)}

    def list_models(
        self,
        model_type: Optional[str] = None,
        environment: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict]:
        try:
            registry_db = self._load_models_database()
            models = list(registry_db["models"].values())
            if model_type:
                models = [m for m in models if m["model_type"] == model_type]
            if environment:
                models = [m for m in models if m["environment"] == environment]
            if status:
                models = [m for m in models if m["status"] == status]
            models.sort(key=lambda x: x["registered_at"], reverse=True)
            return models
        except Exception as e:
            logger.error(f"Model listing failed: {e}")
            return []

    def update_model_status(
        self, model_id: str, status: str, deployment_info: Optional[Dict] = None
    ) -> Dict:
        try:
            registry_db = self._load_models_database()
            model_info = registry_db["models"].get(model_id)
            if not model_info:
                raise ValueError(f"Model not found: {model_id}")
            model_info["status"] = status
            model_info["updated_at"] = datetime.now().isoformat()
            if deployment_info:
                model_info["deployment_info"].update(deployment_info)
            self._save_models_database(registry_db)
            cache_key = f"model_{model_id}"
            cache.delete(cache_key)
            logger.info(f"Model status updated: {model_id} -> {status}")
            return {
                "model_id": model_id,
                "status": "success",
                "message": "Model status updated successfully",
            }
        except Exception as e:
            logger.error(f"Model status update failed: {e}")
            return {"status": "error", "message": str(e)}

    def deploy_model(self, model_id: str, target_environment: str) -> Dict:
        try:
            if target_environment not in ["staging", "production"]:
                raise ValueError(f"Invalid target environment: {target_environment}")
            model_result = self.get_model(model_id)
            if "error" in model_result:
                raise ValueError(model_result["error"])
            model_info = model_result["model_info"]
            target_path = os.path.join(self.registry_path, target_environment)
            os.makedirs(target_path, exist_ok=True)
            target_file = os.path.join(
                target_path, os.path.basename(model_info["model_file"])
            )
            import shutil

            shutil.copy2(model_info["model_file"], target_file)
            deployment_info = {
                "deployed_at": datetime.now().isoformat(),
                "deployed_to": target_environment,
                "deployment_status": "active",
                "deployment_path": target_file,
            }
            update_result = self.update_model_status(
                model_id, "active", deployment_info
            )
            registry_db = self._load_models_database()
            registry_db["deployments"][model_id] = deployment_info
            self._save_models_database(registry_db)
            logger.info(
                f"Model deployed successfully: {model_id} -> {target_environment}"
            )
            return {
                "model_id": model_id,
                "deployment_status": "success",
                "target_environment": target_environment,
                "deployment_info": deployment_info,
            }
        except Exception as e:
            logger.error(f"Model deployment failed: {e}")
            return {"status": "error", "message": str(e)}

    def _generate_model_id(self, model_name: str, model_version: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{model_name}_{model_version}_{timestamp}"

    def _save_model_file(self, model: Any, model_name: str, model_version: str) -> str:
        filename = f"{model_name}_{model_version}.pkl"
        filepath = os.path.join(self.registry_path, filename)
        with open(filepath, "wb") as f:
            pickle.dump(model, f)
        return filepath

    def _load_model_file(self, filepath: str) -> Any:
        with open(filepath, "rb") as f:
            return pickle.load(f)

    def _calculate_model_hash(self, filepath: str) -> str:
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def _log_to_mlflow(self, model_name: str, model_metadata: Dict):
        try:
            with mlflow.start_run(experiment_id=model_name):
                mlflow.log_params(
                    {
                        "model_type": model_metadata["model_type"],
                        "model_version": model_metadata["model_version"],
                        "environment": model_metadata["environment"],
                        "model_hash": model_metadata["model_hash"],
                    }
                )
                mlflow.set_tag("model_id", model_metadata["model_id"])
                mlflow.set_tag("status", model_metadata["status"])
        except Exception as e:
            logger.warning(f"MLflow logging failed: {e}")

    def validate_model_integrity(self, model_id: str) -> Dict:
        try:
            model_result = self.get_model(model_id, load_model=False)
            if "error" in model_result:
                raise ValueError(model_result["error"])
            model_info = model_result["model_info"]
            if not os.path.exists(model_info["model_file"]):
                return {
                    "model_id": model_id,
                    "integrity_check": "failed",
                    "reason": "Model file not found",
                }
            current_hash = self._calculate_model_hash(model_info["model_file"])
            stored_hash = model_info["model_hash"]
            is_valid = current_hash == stored_hash
            return {
                "model_id": model_id,
                "integrity_check": "passed" if is_valid else "failed",
                "current_hash": current_hash,
                "stored_hash": stored_hash,
                "is_valid": is_valid,
            }
        except Exception as e:
            logger.error(f"Model integrity validation failed: {e}")
            return {"model_id": model_id, "integrity_check": "error", "reason": str(e)}

    def get_deployment_history(self, model_id: str) -> List[Dict]:
        try:
            registry_db = self._load_models_database()
            deployments = []
            model_info = registry_db["models"].get(model_id, {})
            if model_info and "deployment_info" in model_info:
                deployments.append(model_info["deployment_info"])
            deployment_registry = registry_db["deployments"].get(model_id, {})
            if deployment_registry:
                deployments.append(deployment_registry)
            return deployments
        except Exception as e:
            logger.error(f"Deployment history retrieval failed: {e}")
            return []

    def cleanup_old_models(self, days_old: int = 30) -> Dict:
        try:
            cutoff_date = datetime.now().timestamp() - (days_old * 24 * 3600)
            registry_db = self._load_models_database()
            cleaned_models = []
            cleaned_files = []
            for model_id, model_info in list(registry_db["models"].items()):
                model_date = datetime.fromisoformat(
                    model_info["registered_at"]
                ).timestamp()
                if model_date < cutoff_date and model_info["status"] == "inactive":
                    if os.path.exists(model_info["model_file"]):
                        os.remove(model_info["model_file"])
                        cleaned_files.append(model_info["model_file"])
                    del registry_db["models"][model_id]
                    cleaned_models.append(model_id)
            self._save_models_database(registry_db)
            logger.info(f"Cleaned up {len(cleaned_models)} old models")
            return {
                "models_cleaned": len(cleaned_models),
                "files_cleaned": len(cleaned_files),
                "cleaned_models": cleaned_models,
            }
        except Exception as e:
            logger.error(f"Model cleanup failed: {e}")
            return {"error": str(e)}
