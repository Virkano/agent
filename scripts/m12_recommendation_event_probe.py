"""Link a published two-tower ranking to its exposure and a versioned event run.

Run from the repository root with the project's Django environment loaded.
This is an acceptance probe: it does not claim to perform customer touch or
automatically deliver a report/notification. Re-running reuses the same facts.
"""

import logging

from scripts.m12_linkage_inventory import DEMO_WORKSPACE_ID


def run(workspace_id=DEMO_WORKSPACE_ID):
    logging.disable(logging.DEBUG)
    from marketing.models import (
        MarketingTask,
        RecommendationFeedbackEvent,
        RecommendationFusionRun,
        RecommendationInferenceLog,
        RecommendationModelStatus,
        RecommendationRankingRun,
    )
    from marketing.serializers.recommendation_ranking import RecommendationRankingService
    from trigger.event_orchestration import EventOrchestrationService
    from trigger.models import EventFlowVersion, FlowVersionStatus, StandardEvent

    task = MarketingTask.objects.filter(workspace_id=workspace_id).select_related("user").first()
    if task is None or task.user is None:
        raise RuntimeError("Demo task/operator unavailable")
    inference = RecommendationInferenceLog.objects.filter(
        workspace_id=workspace_id,
        customer__task=task,
        model_version__status=RecommendationModelStatus.PUBLISHED,
    ).order_by("-create_time").first()
    if inference is None or not inference.candidates:
        raise RuntimeError("Run m12_recommendation_probe first")

    ranking = RecommendationRankingRun.objects.filter(
        workspace_id=workspace_id,
        customer_id=inference.customer_id,
        fusion_run__model_version_id=inference.model_version_id,
    ).order_by("-create_time").first()
    if ranking is None:
        result = RecommendationRankingService(workspace_id, task.user).infer({
            "customer_id": str(inference.customer_id),
            "model_version_id": str(inference.model_version_id),
            "top_n": 3,
        })
        ranking = RecommendationRankingRun.objects.get(id=result["ranking_run_id"])
    fusion = RecommendationFusionRun.objects.get(id=ranking.fusion_run_id)
    if fusion.model_version_id != inference.model_version_id or not ranking.ranked_candidates:
        raise RuntimeError("Ranking has no candidates from the published model")
    exposure = RecommendationFeedbackEvent.objects.filter(
        workspace_id=workspace_id, ranking_run=ranking, event_type="EXPOSED"
    ).first()
    if exposure is None:
        raise RuntimeError("Ranking did not persist exposure feedback")

    orchestration = EventOrchestrationService(workspace_id, task.user)
    flow = EventFlowVersion.objects.filter(
        workspace_id=workspace_id, code="M12_RECOMMENDATION_REVIEW",
        status=FlowVersionStatus.PUBLISHED,
    ).first()
    if flow is None:
        flow = orchestration.create_flow({
            "code": "M12_RECOMMENDATION_REVIEW",
            "name": "M12 推荐反馈人工复核",
            "description": "验收用版本化契约；触达、报告和通知不由本流程自动执行",
            "event_type": "marketing.recommendation.exposed",
            "source_types": ["SYSTEM"],
            "event_schema": {"required": ["task_id", "customer_id", "ranking_run_id", "feedback_id"]},
            "nodes": [{"code": "REVIEW", "name": "人工复核推荐曝光", "node_type": "MANUAL"}],
            "publish": True,
        })
    event_key = f"m12-ranking-exposure-{exposure.id}"
    event = StandardEvent.objects.filter(workspace_id=workspace_id, event_id=event_key).first()
    if event is not None:
        expected = event.payload_snapshot or {}
        if expected.get("ranking_run_id") != str(ranking.id) or expected.get("feedback_id") != str(exposure.id):
            raise RuntimeError("Existing event key refers to a different feedback fact")
    result = orchestration.receive_event({
        "event_id": event_key,
        "idempotency_key": event_key,
        "source_type": "SYSTEM",
        "event_type": "marketing.recommendation.exposed",
        "subject": "推荐曝光待复核",
        "payload": {
            "task_id": str(task.id),
            "customer_id": str(inference.customer_id),
            "model_version_id": str(inference.model_version_id),
            "inference_id": str(inference.id),
            "fusion_run_id": str(fusion.id),
            "ranking_run_id": str(ranking.id),
            "feedback_id": str(exposure.id),
        },
    })
    if len(result["runs"]) != 1:
        raise RuntimeError("Expected exactly one versioned orchestration run")
    print({
        "workspace_id": workspace_id,
        "task_id": str(task.id),
        "customer_id": str(inference.customer_id),
        "model_version_id": str(inference.model_version_id),
        "inference_id": str(inference.id),
        "fusion_run_id": str(fusion.id),
        "ranking_run_id": str(ranking.id),
        "feedback_id": str(exposure.id),
        "flow_version_id": str(flow.id if hasattr(flow, "id") else flow["id"]),
        "standard_event_id": result["event"]["id"],
        "flow_run_id": result["runs"][0]["id"],
        "flow_run_status": result["runs"][0]["status"],
        "reused_event": not result["created"],
    })
