"""Verify scheduled-style collection for the live M12 recommendation flow."""

import logging

from scripts.m12_linkage_inventory import DEMO_WORKSPACE_ID


def run(workspace_id=DEMO_WORKSPACE_ID):
    logging.disable(logging.DEBUG)
    from marketing.models import MarketingNotification
    from platform_monitoring.business_metric_collectors import (
        RECOMMENDATION_REVIEW_METRIC_KEY,
        collect_recommendation_review_metrics,
    )
    from platform_monitoring.metric_foundation import MetricFoundationService
    from platform_monitoring.models import (
        MetricAlertIncident,
        MetricAlertRule,
        MetricDefinition,
        MetricDispatchOrder,
        MetricObservation,
    )
    from trigger.models import EventFlowRun, FlowRunStatus

    flow_run = EventFlowRun.objects.filter(
        workspace_id=workspace_id,
        standard_event__event_id__startswith="ranking:",
        status=FlowRunStatus.WAITING,
    ).select_related("flow_version__created_by").order_by("-create_time").first()
    definition = MetricDefinition.objects.filter(
        workspace_id=workspace_id, metric_key=RECOMMENDATION_REVIEW_METRIC_KEY
    ).first()
    rule = MetricAlertRule.objects.filter(
        workspace_id=workspace_id, definition=definition
    ).order_by("create_time").first() if definition else None
    if flow_run is None or definition is None or rule is None:
        raise RuntimeError("Run automatic event and metric acceptance setup first")
    if rule.dimension_filter:
        operator = definition.owner or flow_run.flow_version.created_by
        MetricFoundationService(workspace_id, operator).save_rule(
            {"dimension_filter": {}}, str(rule.id)
        )
        rule.refresh_from_db()

    collect_recommendation_review_metrics()
    replay = collect_recommendation_review_metrics()
    observation = MetricObservation.objects.filter(
        workspace_id=workspace_id,
        definition=definition,
        dimensions__flow_run_id=str(flow_run.id),
    ).order_by("-observed_at").first()
    if observation is None or observation.value != 1:
        raise RuntimeError("Automatic collector did not persist the waiting-manual observation")
    incident = MetricAlertIncident.objects.filter(
        workspace_id=workspace_id, observation=observation
    ).first()
    order = MetricDispatchOrder.objects.filter(
        workspace_id=workspace_id, incident=incident
    ).first() if incident else None
    if order is None:
        raise RuntimeError("Automatic observation did not produce a dispatch order")
    notification_count = MarketingNotification.objects.filter(
        workspace_id=workspace_id,
        source_type="METRIC_DISPATCH_ORDER",
        source_id=str(order.id),
    ).count()
    if notification_count < 1:
        raise RuntimeError("Automatic dispatch did not reach the global notification bell")
    print({
        "workspace_id": workspace_id,
        "flow_run_id": str(flow_run.id),
        "ranking_run_id": flow_run.standard_event.payload_snapshot["ranking_run_id"],
        "rule_version": rule.config_version,
        "observation_id": str(observation.id),
        "incident_id": str(incident.id),
        "dispatch_order_id": str(order.id),
        "global_notification_count": notification_count,
        "replay_created_count": replay["created_count"],
        "automatic": True,
    })
