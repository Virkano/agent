"""Persist and handle metadata-only review decisions for knowledge answers."""

from django.db import transaction

from application.models import ChatRecord, ServiceAnswerReview, ServiceAnswerReviewAction
from common.exception.app_exception import AppApiException


def capture_pending_review(record: ChatRecord, workspace_id: str):
    audit = ((record.details or {}).get("chat_step") or {}).get("compliance") or {}
    if audit.get("manual_review_status") != "PENDING" or not record.pk:
        return None
    if record.chat.application.workspace_id != workspace_id:
        raise AppApiException(400, "复核工作空间不匹配")
    return ServiceAnswerReview.objects.get_or_create(
        record_id=record.pk,
        defaults={
            "workspace_id": workspace_id,
            "risk_types": list(audit.get("risk_types") or []),
            "delivery_action": str(audit.get("action") or "BLOCKED"),
            "reference_count": int(audit.get("reference_count") or 0),
            "rule_version": str(audit.get("rule_version") or "unknown"),
        },
    )[0]


def _serialize(review: ServiceAnswerReview):
    return {
        "id": str(review.id),
        "record_id": str(review.record_id),
        "chat_id": str(review.record.chat_id),
        "application_id": str(review.record.chat.application_id),
        "status": review.status,
        "risk_types": review.risk_types,
        "delivery_action": review.delivery_action,
        "reference_count": review.reference_count,
        "rule_version": review.rule_version,
        "revision": review.revision,
        "delivered_answer": review.record.answer_text,
        "create_time": review.create_time.isoformat(),
        "update_time": review.update_time.isoformat(),
    }


def page_reviews(workspace_id: str, current_page: int, page_size: int, status: str = "PENDING"):
    if current_page < 1 or not 1 <= page_size <= 100:
        raise AppApiException(400, "分页参数无效")
    if status not in {*ServiceAnswerReview.Status.values, "ALL"}:
        raise AppApiException(400, "复核状态无效")
    reviews = ServiceAnswerReview.objects.filter(
        workspace_id=workspace_id, record__chat__application__workspace_id=workspace_id
    )
    if status != "ALL":
        reviews = reviews.filter(status=status)
    total = reviews.count()
    start = (current_page - 1) * page_size
    records = reviews.select_related("record__chat").order_by("-create_time", "-id")[start:start + page_size]
    return {"total": total, "records": [_serialize(review) for review in records]}


@transaction.atomic
def handle_review(workspace_id: str, review_id: str, action: str, note: str, reviewer):
    if action not in {"CONFIRMED", "DISMISSED"}:
        raise AppApiException(400, "复核动作无效")
    note = (note or "").strip()
    if not note or len(note) > 2000:
        raise AppApiException(400, "请填写不超过 2000 字的复核说明")
    # Lock only the review main table; read relations after the lock.
    review = ServiceAnswerReview.objects.select_for_update().filter(
        id=review_id, workspace_id=workspace_id
    ).first()
    if review is None or review.record.chat.application.workspace_id != workspace_id:
        raise AppApiException(404, "复核记录不存在")
    if review.status != ServiceAnswerReview.Status.PENDING:
        raise AppApiException(409, "该记录已完成复核")
    review.status = action
    review.revision += 1
    review.save(update_fields=["status", "revision", "update_time"])
    ServiceAnswerReviewAction.objects.create(
        review=review,
        revision=review.revision,
        previous_status=ServiceAnswerReview.Status.PENDING,
        current_status=action,
        reviewer_id=str(reviewer.pk),
        reviewer_name=str(getattr(reviewer, "username", "") or ""),
        note=note,
    )
    return _serialize(review)
