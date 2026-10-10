"""Run a real two-tower recommendation for the existing local M12 demo workspace."""

import logging

from scripts.m12_linkage_inventory import DEMO_WORKSPACE_ID


def run(workspace_id=DEMO_WORKSPACE_ID):
    logging.disable(logging.DEBUG)
    from marketing.models import (
        MarketingCustomer,
        MarketingTask,
        RecommendationInferenceLog,
        RecommendationModelStatus,
        RecommendationModelVersion,
    )
    from marketing.serializers.recommendation_engine import RecommendationEngineService

    task = MarketingTask.objects.filter(workspace_id=workspace_id).select_related("user").first()
    if task is None or task.user is None:
        raise RuntimeError("Demo task or its operator is missing")
    customers = list(MarketingCustomer.objects.filter(workspace_id=workspace_id, task=task).order_by("id"))
    if not customers:
        raise RuntimeError("Demo task has no customers")
    service = RecommendationEngineService(workspace_id, task.user)
    version = RecommendationModelVersion.objects.filter(
        workspace_id=workspace_id, status=RecommendationModelStatus.PUBLISHED
    ).first()
    if version is None:
        snapshot = service.build_feature_snapshot({"input_dim": 32})
        trained = service.train({
            "name": "M12演示双塔-v1",
            "snapshot_version": snapshot["snapshot_version"],
            "embedding_dim": 8,
            "epochs": 20,
            "learning_rate": 0.05,
            "auto_publish": True,
        })
        if trained["model_version"]["status"] != RecommendationModelStatus.PUBLISHED:
            raise RuntimeError("Demo model did not publish")
    existing = RecommendationInferenceLog.objects.filter(
        workspace_id=workspace_id,
        customer__task=task,
        model_version__status=RecommendationModelStatus.PUBLISHED,
    ).order_by("-create_time").first()
    if existing and existing.candidates:
        print({
            "workspace_id": workspace_id,
            "task_id": str(task.id),
            "customer_id": str(existing.customer_id),
            "inference_id": str(existing.id),
            "candidate_count": len(existing.candidates),
            "model_version_id": str(existing.model_version_id),
            "reused": True,
        })
        return
    for customer in customers:
        recommendation = service.recommend({"customer_id": str(customer.id), "top_k": 3})
        if recommendation.get("candidates"):
            inference = RecommendationInferenceLog.objects.filter(
                workspace_id=workspace_id, customer=customer
            ).order_by("-create_time").first()
            if inference is None or inference.model_version_id is None:
                raise RuntimeError("Recommendation result has no persisted published model version")
            print({
                "workspace_id": workspace_id,
                "task_id": str(task.id),
                "customer_id": str(customer.id),
                "candidate_count": len(recommendation["candidates"]),
                "inference_id": str(inference.id),
                "model_version_id": str(inference.model_version_id),
                "reused": False,
            })
            return
    raise RuntimeError("Published model returned no candidates for demo customers")
