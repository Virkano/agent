"""Complete the M12 manual review and metric order as labelled acceptance actions."""

import logging

from scripts.m12_linkage_inventory import DEMO_WORKSPACE_ID


NOTE = "M12验收模拟处置：验证状态链，不代表真实客户或生产工单操作"


def run(workspace_id=DEMO_WORKSPACE_ID):
    logging.disable(logging.DEBUG)
    from platform_monitoring.business_metric_collectors import collect_recommendation_review_metrics
    from platform_monitoring.metric_foundation import MetricFoundationService
    from platform_monitoring.models import (
        MetricAlertIncident,
        MetricDispatchOrder,
        MetricDispatchOrderEvent,
        MetricWorkOrderStatus,
    )
    from trigger.event_orchestration import EventOrchestrationService
    from trigger.models import EventFlowRun, FlowNodeRunStatus, FlowRunStatus
    from xpack_lite.models import WorkspaceUserRoleMapping

    flow_run = EventFlowRun.objects.filter(
        workspace_id=workspace_id,
        standard_event__event_id__startswith="ranking:",
    ).select_related("flow_version__created_by").order_by("-create_time").first()
    if flow_run is None:
        raise RuntimeError("Run m12_auto_event_probe first")
    flow_operator = flow_run.flow_version.created_by
    if flow_operator is None:
        raise RuntimeError("Acceptance flow has no operator")
    flow_service = EventOrchestrationService(workspace_id, flow_operator)
    if flow_run.status == FlowRunStatus.WAITING:
        review = flow_run.node_runs.filter(status=FlowNodeRunStatus.WAITING_MANUAL).first()
        if review is None:
            raise RuntimeError("Waiting flow has no manual-review node")
        flow_service.operate_node(
            str(flow_run.id), str(review.id),
            {"action": "APPROVE", "note": NOTE, "output": {"acceptance_simulated": True}},
        )
        flow_run.refresh_from_db()
    if flow_run.status != FlowRunStatus.SUCCEEDED:
        raise RuntimeError("Acceptance review did not finish successfully")

    collection = collect_recommendation_review_metrics()
    order = MetricDispatchOrder.objects.filter(
        workspace_id=workspace_id,
        incident__observation__dimensions__flow_run_id=str(flow_run.id),
    ).select_related("incident").order_by("-create_time").first()
    if order is None:
        raise RuntimeError("Automatic metric order is missing")
    manager_id = WorkspaceUserRoleMapping.objects.filter(
        workspace_id=workspace_id,
        user__is_active=True,
        role__type="WORKSPACE_MANAGE",
    ).values_list("user_id", flat=True).first()
    workspace_mapping = WorkspaceUserRoleMapping.objects.filter(
        workspace_id=workspace_id,
        user__is_active=True,
    ).select_related("user").first()
    operator = order.assignee or (workspace_mapping.user if workspace_mapping else flow_operator)
    assignee_id = manager_id or operator.id
    order_service = MetricFoundationService(workspace_id, operator)
    action_by_status = {
        MetricWorkOrderStatus.NEW: ("ASSIGN", {"assignee_id": str(assignee_id)}),
        MetricWorkOrderStatus.ASSIGNED: ("CLAIM", {}),
        MetricWorkOrderStatus.CLAIMED: ("START", {}),
        MetricWorkOrderStatus.PROCESSING: ("RESOLVE", {}),
        MetricWorkOrderStatus.RESOLVED: ("CLOSE", {}),
    }
    while order.status != MetricWorkOrderStatus.CLOSED:
        action, extra = action_by_status[order.status]
        order_service.operate_order(str(order.id), {"action": action, "note": NOTE, **extra})
        order.refresh_from_db()
    incident = MetricAlertIncident.objects.get(id=order.incident_id)
    actions = list(MetricDispatchOrderEvent.objects.filter(order=order).values_list("action", flat=True))
    expected = {"CREATED", "ASSIGNED", "CLAIMED", "STARTED", "RESOLVED", "CLOSED"}
    if incident.status != "CLOSED" or not expected.issubset(set(actions)):
        raise RuntimeError("Acceptance disposition fact chain is incomplete")
    print({
        "workspace_id": workspace_id,
        "flow_run_id": str(flow_run.id),
        "flow_status": flow_run.status,
        "dispatch_order_id": str(order.id),
        "dispatch_status": order.status,
        "incident_status": incident.status,
        "order_actions": actions,
        "collector_created_count": collection["created_count"],
        "simulated": True,
    })
