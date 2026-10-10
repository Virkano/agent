"""Read-only linkage inventory for the existing local M12 demo workspace.

Run from the repository root after loading .env.local:
    ./.venv/bin/python apps/manage.py shell -c 'from scripts.m12_linkage_inventory import run; run()'
"""

import logging


DEMO_WORKSPACE_ID = "01a0560c-e867-7cd1-a58b-e1a736996d0a"


def run(workspace_id=DEMO_WORKSPACE_ID):
    logging.disable(logging.DEBUG)
    from application.models import ChatRecord
    from marketing.models import (
        MarketingAlert,
        MarketingAnalysisReport,
        MarketingCampaign,
        MarketingCustomer,
        MarketingTask,
        MarketingTouchExecution,
        RecommendationFusionRun,
        RecommendationInferenceLog,
        RecommendationRankingRun,
    )
    from trigger.models import EventFlowRun, StandardEvent

    tasks = list(MarketingTask.objects.filter(workspace_id=workspace_id).values(
        "id", "application_id", "knowledge_id"
    ))
    task_ids = {str(row["id"]) for row in tasks}
    customers = MarketingCustomer.objects.filter(workspace_id=workspace_id)
    customer_ids = {str(row.id) for row in customers}
    records = ChatRecord.objects.filter(chat__application__workspace_id=workspace_id).only("source")
    linked_chats = sum(
        1 for record in records if isinstance(record.source, dict)
        and str(record.source.get("marketing_task_id")) in task_ids
        and str(record.source.get("marketing_customer_id")) in customer_ids
    )
    linked_chat_customers = {
        str(record.source.get("marketing_customer_id"))
        for record in records if isinstance(record.source, dict)
        and str(record.source.get("marketing_task_id")) in task_ids
        and str(record.source.get("marketing_customer_id")) in customer_ids
    }
    fusion = RecommendationFusionRun.objects.filter(workspace_id=workspace_id)
    ranking = RecommendationRankingRun.objects.filter(workspace_id=workspace_id)
    reports = MarketingAnalysisReport.objects.filter(workspace_id=workspace_id)
    alerts = MarketingAlert.objects.filter(workspace_id=workspace_id)
    print({
        "workspace_id": workspace_id,
        "task_count": len(tasks),
        "task_has_app_and_knowledge": all(row["application_id"] and row["knowledge_id"] for row in tasks),
        "customer_count": len(customer_ids),
        "campaign_count": MarketingCampaign.objects.filter(workspace_id=workspace_id).count(),
        "touch_count": MarketingTouchExecution.objects.filter(workspace_id=workspace_id).count(),
        "recommendation_inference_count": RecommendationInferenceLog.objects.filter(workspace_id=workspace_id).count(),
        "fusion_count": fusion.count(),
        "ranking_count": ranking.count(),
        "ranking_bound_to_fusion_count": ranking.exclude(fusion_run_id=None).count(),
        "linked_customer_chat_count": linked_chats,
        "linked_chat_customer_count": len(linked_chat_customers),
        "ranked_customer_has_chat_count": len({str(row.customer_id) for row in ranking} & linked_chat_customers),
        "ranked_customer_has_touch_count": MarketingTouchExecution.objects.filter(
            workspace_id=workspace_id, customer_id__in=ranking.values_list("customer_id", flat=True)
        ).count(),
        "task_bound_report_count": reports.filter(task_id__in=task_ids).count(),
        "alert_count": alerts.count(),
        "alert_snapshot_key_sets": sorted({
            ",".join(sorted(row.source_snapshot.keys()))
            for row in alerts if isinstance(row.source_snapshot, dict)
        }),
        "event_flow_run_count": EventFlowRun.objects.filter(workspace_id=workspace_id).count(),
        "recommendation_event_count": StandardEvent.objects.filter(
            workspace_id=workspace_id, event_type="marketing.recommendation.exposed"
        ).count(),
    })
