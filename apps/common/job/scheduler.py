from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
import sys

scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), "default")

# Test discovery imports job modules, but must not start a background worker
# against the test database while transactional fixtures are being exercised.
if "test" not in sys.argv[1:]:
    try:
        scheduler.start()
    except Exception as e:
        from common.utils.logger import telecom_ai_logger

        telecom_ai_logger.error(f"Failed to start scheduler: {e}")
