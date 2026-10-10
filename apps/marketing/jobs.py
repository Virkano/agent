from common.job.scheduler import scheduler
from common.utils.lock import RedisLock
from common.utils.logger import telecom_ai_logger
from marketing.tasks import run_due_report_subscriptions_task, scan_all_marketing_alerts_task


JOB_ID = "marketing_alert_scan"
REPORT_SUBSCRIPTION_JOB_ID = "marketing_report_subscription_scan"


def enqueue_marketing_alert_scan():
    scan_all_marketing_alerts_task.delay(7)


def enqueue_due_report_subscriptions():
    run_due_report_subscriptions_task.delay()


def run():
    rlock = RedisLock()
    if not rlock.try_lock("marketing_alert_scan_register", 30 * 30):
        return
    try:
        existing_job = scheduler.get_job(job_id=JOB_ID)
        if existing_job is not None:
            existing_job.remove()
        scheduler.add_job(
            enqueue_marketing_alert_scan,
            "interval",
            minutes=5,
            id=JOB_ID,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=120,
        )
        existing_report_job = scheduler.get_job(job_id=REPORT_SUBSCRIPTION_JOB_ID)
        if existing_report_job is not None:
            existing_report_job.remove()
        scheduler.add_job(
            enqueue_due_report_subscriptions,
            "interval",
            minutes=5,
            id=REPORT_SUBSCRIPTION_JOB_ID,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=120,
        )
        telecom_ai_logger.info("Registered marketing alert scan job: every 5 minutes")
        telecom_ai_logger.info("Registered marketing report subscription scan job: every 5 minutes")
    finally:
        rlock.un_lock("marketing_alert_scan_register")
