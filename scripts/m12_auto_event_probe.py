"""Verify the live demo workspace publishes recommendation events from ranking itself."""

import logging

from scripts.m12_linkage_inventory import DEMO_WORKSPACE_ID


def run(workspace_id=DEMO_WORKSPACE_ID):
    logging.disable(logging.DEBUG)
    from marketing.models import (
        MarketingTask,
        RecommendationModelStatus,
        RecommendationModelVersion,
        RecommendationRankingRun,
    )
    from marketing.recommendation_events import publish_top_exposure
    from marketing.serializers.recommendation_ranking import RecommendationRankingService
    from trigger.models import EventFlowRun, StandardEvent

    task = MarketingTask.objects.filter(workspace_id=workspace_id).select_related("user").first()
    model = RecommendationModelVersion.objects.filter(
        workspace_id=workspace_id, status=RecommendationModelStatus.PUBLISHED
    ).first()
    if task is None or task.user is None or model is None:
        raise RuntimeError("Demo task/operator/published model unavailable")
    ranking = RecommendationRankingRun.objects.filter(
        workspace_id=workspace_id,
        customer__task=task,
        fusion_run__model_version=model,
    ).order_by("-create_time").first()
    event = None
    if ranking is not None:
        event = StandardEvent.objects.filter(
            workspace_id=workspace_id,
            event_id=f"ranking:{ranking.id}:exposed",
            event_type="marketing.recommendation.exposed",
        ).first()
    if event is None:
        customer = task.customers.order_by("id").first()
        if customer is None:
            raise RuntimeError("Demo task has no customer")
        result = RecommendationRankingService(workspace_id, task.user).infer({
            "customer_id": str(customer.id),
            "model_version_id": str(model.id),
            "top_n": 3,
        })
        ranking = RecommendationRankingRun.objects.get(id=result["ranking_run_id"])
        event = StandardEvent.objects.get(
            workspace_id=workspace_id, event_id=f"ranking:{ranking.id}:exposed"
        )
    result = publish_top_exposure(ranking, task.user)
    if result is None or result["created"]:
        raise RuntimeError("Automated exposure event was not idempotent")
    if event.payload_snapshot.get("ranking_run_id") != str(ranking.id):
        raise RuntimeError("Exposure event is not bound to this ranking run")
    flow_run = EventFlowRun.objects.filter(workspace_id=workspace_id, standard_event=event).first()
    if flow_run is None:
        raise RuntimeError("Automated exposure event has no flow run")
    print({
        "workspace_id": workspace_id,
        "task_id": str(task.id),
        "customer_id": str(ranking.customer_id),
        "model_version_id": str(model.id),
        "ranking_run_id": str(ranking.id),
        "feedback_id": event.payload_snapshot["feedback_id"],
        "standard_event_id": str(event.id),
        "flow_run_id": str(flow_run.id),
        "flow_run_status": flow_run.status,
        "idempotent": True,
    })
