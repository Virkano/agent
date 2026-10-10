"""Generate one clearly labelled in-app demo report from the same M12 task.

The report includes simulated touch data. It does not prove real conversion or
an automatic dispatch-order-to-report trigger.
"""

import logging
from datetime import timedelta

from django.utils import timezone

from scripts.m12_linkage_inventory import DEMO_WORKSPACE_ID


TEMPLATE_NAME = "M12验收模拟经营报告模板"
SUBSCRIPTION_NAME = "M12验收模拟-同任务站内日报"


def run(workspace_id=DEMO_WORKSPACE_ID):
    logging.disable(logging.DEBUG)
    from marketing.models import (
        MarketingAnalysisReport,
        MarketingNotification,
        MarketingReportDelivery,
        MarketingReportSubscription,
        MarketingReportTemplate,
        MarketingTask,
        MarketingTouchExecution,
    )
    from marketing.serializers.report import MarketingAnalysisReportService
    from marketing.serializers.report_subscription import MarketingReportSubscriptionService

    task = MarketingTask.objects.filter(workspace_id=workspace_id).select_related("user").first()
    if task is None or task.user is None:
        raise RuntimeError("Demo task/operator unavailable")
    touch = MarketingTouchExecution.objects.filter(
        workspace_id=workspace_id,
        customer__task=task,
        note__startswith="M12验收模拟：",
    ).order_by("-create_time").first()
    if touch is None:
        raise RuntimeError("Run m12_touch_feedback_probe first")

    reports = MarketingAnalysisReportService(workspace_id, task.user)
    subscriptions = MarketingReportSubscriptionService(workspace_id, task.user)
    template = MarketingReportTemplate.objects.filter(workspace_id=workspace_id, name=TEMPLATE_NAME).first()
    if template is None:
        result = reports.create_template({
            "name": TEMPLATE_NAME,
            "description": "本地 M12 验收模拟；触达结果不代表真实客户反馈",
            "title_template": "M12验收模拟：{task_name} {start_date} 至 {end_date}",
        })
        template = MarketingReportTemplate.objects.get(id=result["id"])
    subscription = MarketingReportSubscription.objects.filter(
        workspace_id=workspace_id, name=SUBSCRIPTION_NAME
    ).first()
    if subscription is None:
        result = subscriptions.save({
            "name": SUBSCRIPTION_NAME,
            "template_id": str(template.id),
            "task_id": str(task.id),
            "frequency": "DAILY",
            "run_time": "09:00:00",
            "period_days": 30,
            "use_llm": False,
            "email_enabled": False,
            "enabled": True,
        })
        subscription = MarketingReportSubscription.objects.get(id=result["id"])
    if subscription.task_id != task.id or subscription.template_id != template.id or subscription.email_enabled:
        raise RuntimeError("Existing acceptance subscription does not match the task/template")

    report = MarketingAnalysisReport.objects.filter(
        workspace_id=workspace_id,
        task=task,
        template=template,
        title__startswith="M12验收模拟：",
        status="SUCCESS",
    ).order_by("-create_time").first()
    if report is None or report.generated_at < touch.create_time:
        result = subscriptions.run_now(str(subscription.id))
        report = MarketingAnalysisReport.objects.get(id=result["report_id"])
    if report.status != "SUCCESS":
        raise RuntimeError("Acceptance report generation failed")
    if report.period_start > timezone.localdate(touch.create_time) or report.period_end < timezone.localdate(touch.create_time):
        raise RuntimeError("Report period does not include the acceptance touch")
    if int((report.metrics or {}).get("touch_count", 0)) < 1:
        raise RuntimeError("Report did not count the acceptance touch")
    if report.generated_at < touch.create_time - timedelta(seconds=1):
        raise RuntimeError("Report predates the acceptance touch")
    delivery = MarketingReportDelivery.objects.filter(
        workspace_id=workspace_id, report=report, channel="IN_APP", status="SUCCESS"
    ).first()
    notification_count = MarketingNotification.objects.filter(
        workspace_id=workspace_id, source_type="REPORT_GENERATED", source_id=f"{report.id}:{report.retry_count}"
    ).count()
    if delivery is None or notification_count < 1:
        raise RuntimeError("Report did not reach in-app delivery and notification")
    print({
        "workspace_id": workspace_id,
        "task_id": str(task.id),
        "touch_execution_id": str(touch.id),
        "subscription_id": str(subscription.id),
        "report_id": str(report.id),
        "report_touch_count": report.metrics["touch_count"],
        "in_app_delivery_id": str(delivery.id),
        "report_notification_count": notification_count,
        "simulated": True,
    })
