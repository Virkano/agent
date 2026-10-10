from common.job.scheduler import scheduler
from common.utils.lock import RedisLock

JOB_ID = "platform_monitoring_collection"
BUSINESS_METRIC_JOB_ID = "business_metric_collection"
LOCK_KEY = "platform_monitoring_collection_lock"


def execute_platform_monitoring_collection():
    from .serializers import collect_all_workspaces

    return collect_all_workspaces()


def execute_business_metric_collection():
    from .business_metric_collectors import collect_recommendation_review_metrics

    return collect_recommendation_review_metrics()


def run():
    lock = RedisLock()
    if not lock.try_lock(LOCK_KEY, timeout=60):
        return
    try:
        if scheduler.get_job(JOB_ID):
            scheduler.remove_job(JOB_ID)
        scheduler.add_job(
            execute_platform_monitoring_collection,
            trigger="interval",
            minutes=5,
            id=JOB_ID,
            replace_existing=True,
        )
        scheduler.add_job(
            execute_business_metric_collection,
            trigger="interval",
            minutes=5,
            id=BUSINESS_METRIC_JOB_ID,
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=120,
        )
    finally:
        lock.un_lock(LOCK_KEY)
