# coding=utf-8
import hashlib
import json
from typing import Protocol


class ModelPipelineRunner(Protocol):
    def build_features(self, config: dict) -> dict: ...

    def train(self, config: dict) -> dict: ...


class LocalModelPipelineRunner:
    """本地粗粒度执行器；后续可替换为真实训练平台或 MLflow Project。"""

    def build_features(self, config: dict) -> dict:
        return {
            "dataset_name": config["dataset_name"],
            "dataset_version": config.get("dataset_version", ""),
            "feature_set": f"{config['registry_name']}-features",
            "quality_check": "PASSED",
        }

    def train(self, config: dict) -> dict:
        digest_source = json.dumps(config, ensure_ascii=False, sort_keys=True, default=str).encode()
        artifact_digest = f"sha256:{hashlib.sha256(digest_source).hexdigest()}"
        artifact_uri = config["artifact_uri_template"].format(
            pipeline_id=config["pipeline_id"],
            run_number=config["run_number"],
        )
        return {
            "artifact_uri": artifact_uri,
            "artifact_digest": artifact_digest,
            "parameters": config.get("parameters", {}),
        }


def get_model_pipeline_runner() -> ModelPipelineRunner:
    return LocalModelPipelineRunner()
