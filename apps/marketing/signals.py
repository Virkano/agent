from django.db.models.signals import post_save
from django.dispatch import receiver

from application.models.application_chat import ChatRecord
from common.utils.logger import telecom_ai_logger
from marketing.quality import audit_and_save_quality_review


@receiver(post_save, sender=ChatRecord, dispatch_uid="marketing_answer_quality_review")
def audit_marketing_answer_after_save(sender, instance, **kwargs):
    try:
        audit_and_save_quality_review(instance)
    except Exception:
        telecom_ai_logger.exception(
            "Marketing answer quality audit failed for chat record %s",
            instance.id,
        )
