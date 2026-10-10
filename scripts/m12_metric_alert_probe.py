"""Import a fact-derived demo metric for the pending M12 review and verify dispatch.

This is a labelled local acceptance sample, not a production scheduled collector.
"""

import logging

from scripts.m12_linkage_inventory import DEMO_WORKSPACE_ID


METRIC_KEY = "m12_recommendation_review_pending"
RULE_NAME = "M12验收模拟-推荐待人工复核"


def run(workspace_id=DEMO_WORKSPACE_ID):
    logging.disable(logging.DEBUG)
    from marketing.models import MarketingNotification, MarketingTask, MarketingTouchExecution
    from platform_monitoring.metric_foundation import MetricFoundationService
    from platform_monitoring.models import (
        MetricAlertIncident,
        MetricAlertRule,
        MetricCollectionBatch,
        MetricDefinition,
        MetricDispatchOrder,
        MetricObservation,
    )
    from trigger.models import EventFlowRun, FlowNodeRunStatus, FlowRunStatus

    task = MarketingTask.objects.filter(workspace_id=workspace_id).select_related("user").first()
    if task is None or task.user is None:
        raise RuntimeError("Demo task/operator unavailable")
    run = EventFlowRun.objects.filter(
        workspace_id=workspace_id,
        flow_version__code="M12_RECOMMENDATION_REVIEW",
        status=FlowRunStatus.WAITING,
    ).order_by("-create_time").first()
    if run is None:
        raise RuntimeError("No pending recommendation review run")
    payload = run.standard_event.payload_snapshot or {}
    if payload.get("task_id") != str(task.id):
        raise RuntimeError("Review event does not belong to the demo task")
    if not MarketingTouchExecution.objects.filter(
        workspace_id=workspace_id,
        customer_id=payload.get("customer_id"),
        note__startswith="M12验收模拟：",
    ).exists():
        raise RuntimeError("Run m12_touch_feedback_probe first")
    pending_count = run.node_runs.filter(status=FlowNodeRunStatus.WAITING_MANUAL).count()
    if pending_count < 1:
        raise RuntimeError("Run has no waiting manual node")

    service = MetricFoundationService(workspace_id, task.user)
    definition = MetricDefinition.objects.filter(workspace_id=workspace_id, metric_key=METRIC_KEY).first()
    if definition is None:
        saved = service.save_definition({
            "metric_key": METRIC_KEY,
            "name": "M12验收模拟-推荐待复核节点数",
            "theme": "DELIVERY",
            "unit": "个",
            "description": "来自本地推荐反馈编排运行的待人工复核节点；非生产采集",
            "dimensions_schema": ["task_id", "ranking_run_id", "flow_run_id"],
        })
        definition = MetricDefinition.objects.get(id=saved["id"])
    rule = MetricAlertRule.objects.filter(workspace_id=workspace_id, name=RULE_NAME).first()
    if rule is None:
        saved = service.save_rule({
            "definition_id": str(definition.id),
            "name": RULE_NAME,
            "mode": "STATIC",
            "direction": "ABOVE",
            "warning_threshold": 0,
            "critical_threshold": 5,
            "dimension_filter": {"flow_run_id": str(run.id)},
        })
        rule = MetricAlertRule.objects.get(id=saved["id"])
    if rule.compliance_status != "PASSED" or rule.definition_id != definition.id:
        raise RuntimeError("Metric rule is not compliant or targets a different definition")

    batch_no = f"M12-REVIEW-{run.id}"
    batch = MetricCollectionBatch.objects.filter(workspace_id=workspace_id, batch_no=batch_no).first()
    if batch is None:
        service.import_batch({
            "batch_no": batch_no,
            "rows": [{
                "metric_key": METRIC_KEY,
                "value": pending_count,
                "dimensions": {
                    "task_id": str(task.id),
                    "ranking_run_id": payload["ranking_run_id"],
                    "flow_run_id": str(run.id),
                },
            }],
        })
        batch = MetricCollectionBatch.objects.get(workspace_id=workspace_id, batch_no=batch_no)
    observation = MetricObservation.objects.get(workspace_id=workspace_id, batch=batch)
    incident = MetricAlertIncident.objects.filter(
        workspace_id=workspace_id, rule=rule, observation=observation
    ).first()
    if incident is None:
        raise RuntimeError("Pending-review metric did not trigger an incident")
    order = MetricDispatchOrder.objects.filter(workspace_id=workspace_id, incident=incident).first()
    if order is None:
        raise RuntimeError("Metric incident did not create a dispatch order")
    notification_count = MarketingNotification.objects.filter(
        workspace_id=workspace_id,
        source_type="METRIC_DISPATCH_ORDER",
        source_id=str(order.id),
    ).count()
    if notification_count < 1:
        raise RuntimeError("Dispatch order did not appear in the global notification bell")
    print({
        "workspace_id": workspace_id,
        "task_id": str(task.id),
        "ranking_run_id": payload["ranking_run_id"],
        "flow_run_id": str(run.id),
        "pending_manual_nodes": pending_count,
        "metric_batch_id": str(batch.id),
        "observation_id": str(observation.id),
        "rule_version": rule.config_version,
        "incident_id": str(incident.id),
        "dispatch_order_id": str(order.id),
        "dispatch_status": order.status,
        "global_notification_count": notification_count,
        "simulated": True,
    })
