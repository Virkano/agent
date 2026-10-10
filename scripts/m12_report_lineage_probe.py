"""Verify a subscribed M12 demo report freezes related source-fact IDs."""

import logging

from scripts.m12_linkage_inventory import DEMO_WORKSPACE_ID
from scripts.m12_report_subscription_probe import SUBSCRIPTION_NAME


def run(workspace_id=DEMO_WORKSPACE_ID):
    logging.disable(logging.DEBUG)
    from marketing.models import (
        MarketingAnalysisReport,
        MarketingReportSubscription,
        MarketingTouchExecution,
    )
    from marketing.serializers.report_subscription import MarketingReportSubscriptionService
    from platform_monitoring.models import MetricDispatchOrder
    from trigger.models import EventFlowRun

    subscription = MarketingReportSubscription.objects.filter(
        workspace_id=workspace_id, name=SUBSCRIPTION_NAME
    ).first()
    if subscription is None or subscription.task_id is None:
        raise RuntimeError("Run m12_report_subscription_probe first")
    task_id = str(subscription.task_id)
    touch = MarketingTouchExecution.objects.filter(
        workspace_id=workspace_id,
        batch__task_id=task_id,
        note__startswith="M12验收模拟：",
    ).order_by("-create_time").first()
    order = MetricDispatchOrder.objects.filter(
        workspace_id=workspace_id,
        incident__rule__name="M12验收模拟-推荐待人工复核",
        incident__observation__dimensions__task_id=task_id,
    ).order_by("-create_time").first()
    flow_run = EventFlowRun.objects.filter(
        workspace_id=workspace_id,
        standard_event__payload_snapshot__task_id=task_id,
        standard_event__event_id__startswith="ranking:",
    ).order_by("-create_time").first()
    if touch is None or order is None or flow_run is None:
        raise RuntimeError("Run touch, metric and automatic event probes first")
    ranking_id = flow_run.standard_event.payload_snapshot["ranking_run_id"]

    def contains_sources(report):
        if report is None or report.status != "SUCCESS":
            return False
        lineage = (report.input_snapshot or {}).get("source_lineage") or {}
        required = {
            "touch_executions": str(touch.id),
            "recommendation_rankings": ranking_id,
            "metric_dispatch_orders": str(order.id),
            "event_flow_runs": str(flow_run.id),
        }
        return lineage.get("task_id") == task_id and all(
            identifier in (lineage.get(kind) or {}).get("ids", [])
            for kind, identifier in required.items()
        )

    report = subscription.last_report
    if not contains_sources(report):
        result = MarketingReportSubscriptionService(workspace_id, subscription.user).run_now(str(subscription.id))
        report = MarketingAnalysisReport.objects.get(id=result["report_id"])
    if not contains_sources(report):
        raise RuntimeError("Subscribed report did not freeze all four related fact IDs")
    lineage = report.input_snapshot["source_lineage"]
    print({
        "workspace_id": workspace_id,
        "task_id": task_id,
        "subscription_id": str(subscription.id),
        "report_id": str(report.id),
        "lineage_scope": lineage["scope"],
        "touch_execution_id": str(touch.id),
        "ranking_run_id": ranking_id,
        "metric_dispatch_order_id": str(order.id),
        "event_flow_run_id": str(flow_run.id),
        "simulated": True,
    })
