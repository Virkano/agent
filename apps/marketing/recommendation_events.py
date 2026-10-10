"""Publish a ranking's top exposure into a configured event flow.

No flow means no orchestration side effect. The event payload contains only
internal identifiers; customer names, phone numbers and model features stay out.
"""

from marketing.models import RecommendationFeedbackEvent, RecommendationFeedbackType


EXPOSURE_EVENT_TYPE = "marketing.recommendation.exposed"


def publish_top_exposure(run, user=None):
    from trigger.event_orchestration import EventOrchestrationService
    from trigger.models import EventFlowVersion, EventSourceType, FlowVersionStatus

    configured = EventFlowVersion.objects.filter(
        workspace_id=run.workspace_id,
        status=FlowVersionStatus.PUBLISHED,
        event_type=EXPOSURE_EVENT_TYPE,
        source_types__contains=[EventSourceType.SYSTEM],
    ).exists()
    if not configured or not run.ranked_candidates:
        return None
    top = run.ranked_candidates[0]
    feedback = RecommendationFeedbackEvent.objects.filter(
        workspace_id=run.workspace_id,
        ranking_run=run,
        campaign_id=top["campaign_id"],
        event_type=RecommendationFeedbackType.EXPOSED,
    ).first()
    if feedback is None:
        raise RuntimeError("Top-ranked exposure feedback is missing")
    task_id = str(run.customer.task_id)
    event_key = f"ranking:{run.id}:exposed"
    return EventOrchestrationService(run.workspace_id, user).receive_event({
        "event_id": event_key,
        "idempotency_key": event_key,
        "source_type": EventSourceType.SYSTEM,
        "event_type": EXPOSURE_EVENT_TYPE,
        "subject": "推荐曝光待复核",
        "payload": {
            "task_id": task_id,
            "customer_id": str(run.customer_id),
            "model_version_id": str(run.fusion_run.model_version_id) if run.fusion_run.model_version_id else None,
            "fusion_run_id": str(run.fusion_run_id),
            "ranking_run_id": str(run.id),
            "feedback_id": str(feedback.id),
        },
    })
