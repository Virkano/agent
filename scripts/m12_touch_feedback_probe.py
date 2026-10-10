"""Record one explicitly simulated M12 touch via an already approved batch.

The local demo record is not evidence of a real outbound call or conversion.
Re-running reuses the same execution and synced recommendation feedback.
"""

import logging

from scripts.m12_linkage_inventory import DEMO_WORKSPACE_ID


NOTE = "M12验收模拟：客户表达办理意向；非真实外呼/非实际转化"


def run(workspace_id=DEMO_WORKSPACE_ID):
    logging.disable(logging.DEBUG)
    from marketing.models import (
        MarketingTask,
        MarketingTouchBatch,
        MarketingTouchBatchApprovalStatus,
        MarketingTouchBatchStatus,
        MarketingTouchExecution,
        RecommendationFeedbackEvent,
        RecommendationRankingRun,
    )
    from marketing.serializers.recommendation_incremental import RecommendationIncrementalService
    from marketing.serializers.touch_batch import MarketingTouchBatchService

    task = MarketingTask.objects.filter(workspace_id=workspace_id).select_related("user").first()
    if task is None or task.user is None:
        raise RuntimeError("Demo task/operator unavailable")
    ranking = RecommendationRankingRun.objects.filter(
        workspace_id=workspace_id,
        customer__task=task,
        fusion_run__model_version__isnull=False,
    ).order_by("-create_time").first()
    if ranking is None or not ranking.ranked_candidates:
        raise RuntimeError("Run m12_recommendation_event_probe first")
    customer_id = str(ranking.customer_id)
    batch = next((row for row in MarketingTouchBatch.objects.filter(
        workspace_id=workspace_id,
        task=task,
        approval_status=MarketingTouchBatchApprovalStatus.APPROVED,
    ) if row.status != MarketingTouchBatchStatus.CLOSED and any(
        str(item.get("customer_id")) == customer_id for item in (row.customer_snapshot or [])
    )), None)
    if batch is None:
        raise RuntimeError("No already-approved batch includes this customer; do not bypass approval")

    execution = MarketingTouchExecution.objects.filter(
        workspace_id=workspace_id, batch=batch, customer_id=ranking.customer_id, note=NOTE
    ).first()
    if execution is None:
        result = MarketingTouchBatchService(workspace_id, task.user).record_execution(
            str(task.id), str(batch.id), {
                "customer_id": customer_id,
                "result": "INTENT",
                "note": NOTE,
            }
        )
        execution = MarketingTouchExecution.objects.get(id=result["id"])
    if execution.result != "INTENT":
        raise RuntimeError("Existing acceptance touch has unexpected result")

    RecommendationIncrementalService(workspace_id, task.user).sync_business_feedback()
    feedback = RecommendationFeedbackEvent.objects.filter(
        workspace_id=workspace_id,
        ranking_run=ranking,
        source_type="TOUCH_EXECUTION",
        source_id=str(execution.id),
        event_type="CLICKED",
    ).first()
    if feedback is None:
        raise RuntimeError("Touch was not attributed to the same ranking run")
    print({
        "workspace_id": workspace_id,
        "task_id": str(task.id),
        "customer_id": customer_id,
        "approved_batch_id": str(batch.id),
        "ranking_run_id": str(ranking.id),
        "touch_execution_id": str(execution.id),
        "feedback_id": str(feedback.id),
        "feedback_type": feedback.event_type,
        "simulated": True,
    })
