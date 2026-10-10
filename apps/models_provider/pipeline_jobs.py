# coding=utf-8
from common.job.scheduler import scheduler
from common.utils.lock import RedisLock

JOB_ID = "model_training_pipeline_schedule"
LOCK_KEY = "model_training_pipeline_schedule_lock"


def execute_due_training_pipelines():
    from models_provider.serializers.pipeline import run_due_training_pipelines

    return run_due_training_pipelines()


def run():
    lock = RedisLock()
    if not lock.try_lock(LOCK_KEY, timeout=60):
        return
    try:
        if scheduler.get_job(JOB_ID):
            scheduler.remove_job(JOB_ID)
        scheduler.add_job(
            execute_due_training_pipelines,
            trigger="interval",
            minutes=1,
            id=JOB_ID,
            replace_existing=True,
        )
    finally:
        lock.un_lock(LOCK_KEY)
