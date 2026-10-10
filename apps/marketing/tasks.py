from celery import shared_task

from common.utils.logger import telecom_ai_logger
from marketing.serializers import run_due_report_subscriptions, scan_all_marketing_alerts


@shared_task(name="marketing.scan_all_alerts", ignore_result=True)
def scan_all_marketing_alerts_task(days=7):
    result = scan_all_marketing_alerts(days)
    telecom_ai_logger.info(
        "Marketing alert scan completed: workspaces=%s errors=%s",
        result["workspace_count"],
        len(result["errors"]),
    )
    return result


@shared_task(name="marketing.run_due_report_subscriptions", ignore_result=True)
def run_due_report_subscriptions_task():
    result = run_due_report_subscriptions()
    telecom_ai_logger.info(
        "Marketing report subscription scan completed: processed=%s errors=%s",
        result["processed_count"],
        result["error_count"],
    )
    return result
