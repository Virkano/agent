from django.db import transaction
from django.db.models import Case, IntegerField, Q, Value, When
from django.utils import timezone
from rest_framework import serializers

from application.models.application_chat import ChatRecord
from common.exception.app_exception import AppApiException
from common.result import Page
from marketing.models import (
    MarketingAnswerManualReviewAction,
    MarketingAnswerManualReviewStatus,
    MarketingAnswerQualityReview,
    MarketingAnswerQualityReviewActionRecord,
    MarketingAnswerQualityStatus,
    MarketingTask,
)
from marketing.quality import RISK_DEFINITIONS, ensure_quality_reviews, serialize_quality_review


def validate_or_raise(serializer):
    if serializer.is_valid():
        return serializer.validated_data
    field, errors = next(iter(serializer.errors.items()))
    message = errors[0] if isinstance(errors, list) and errors else errors
    raise AppApiException(400, f"{field}: {message}")


class MarketingQualityReviewQuerySerializer(serializers.Serializer):
    task_id = serializers.UUIDField(required=False, allow_null=True)
    quality_status = serializers.ChoiceField(
        required=False,
        allow_blank=True,
        choices=MarketingAnswerQualityStatus.choices,
    )
    manual_status = serializers.ChoiceField(
        required=False,
        allow_blank=True,
        choices=MarketingAnswerManualReviewStatus.choices,
    )
    risk_type = serializers.ChoiceField(required=False, allow_blank=True, choices=list(RISK_DEFINITIONS))
    keyword = serializers.CharField(required=False, allow_blank=True, max_length=200)


class MarketingQualityReviewHandleSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=MarketingAnswerManualReviewAction.choices)
    note = serializers.CharField(required=False, allow_blank=True, max_length=2000)
    revised_answer = serializers.CharField(required=False, allow_blank=True, max_length=20000)

    def validate(self, attrs):
        action = attrs["action"]
        note = attrs.get("note", "").strip()
        revised_answer = attrs.get("revised_answer", "").strip()
        if action == MarketingAnswerManualReviewAction.CONFIRM_ISSUE and not note:
            raise serializers.ValidationError({"note": "确认存在问题时必须填写复核意见"})
        if action == MarketingAnswerManualReviewAction.REVISE and not revised_answer:
            raise serializers.ValidationError({"revised_answer": "提交修订时必须填写修订答案"})
        attrs["note"] = note
        attrs["revised_answer"] = revised_answer
        return attrs


def serialize_manual_action(row):
    return {
        "id": str(row.id),
        "action": row.action,
        "previous_status": row.previous_status,
        "current_status": row.current_status,
        "reviewer_name": row.reviewer_name,
        "note": row.note,
        "original_answer": row.original_answer,
        "revised_answer": row.revised_answer,
        "revision": row.revision,
        "create_time": row.create_time,
    }


def serialize_quality_workbench_record(row):
    actions = list(row.manual_actions.all())
    return {
        **serialize_quality_review(row),
        "task_id": str(row.task_id),
        "task_name": row.task.name,
        "customer_id": str(row.customer_id) if row.customer_id else None,
        "customer_name": row.customer.name if row.customer else "",
        "record_id": str(row.record_id),
        "problem_text": row.record.problem_text,
        "original_answer": row.record.answer_text,
        "record_create_time": row.record.create_time,
        "manual_actions": [serialize_manual_action(action) for action in actions],
    }


class MarketingQualityReviewService:
    BACKFILL_LIMIT = 500

    def __init__(self, workspace_id, user=None):
        self.workspace_id = workspace_id
        self.user = user

    def _queryset(self):
        return (
            MarketingAnswerQualityReview.objects.filter(workspace_id=self.workspace_id)
            .select_related("task", "customer", "record", "reviewer")
            .prefetch_related("manual_actions")
        )

    def _backfill_recent_records(self):
        task_ids = [
            str(task_id)
            for task_id in MarketingTask.objects.filter(workspace_id=self.workspace_id).values_list("id", flat=True)
        ]
        if not task_ids:
            return
        records = list(
            ChatRecord.objects.filter(chat__source__marketing_task_id__in=task_ids)
            .filter(marketing_quality_review__isnull=True)
            .select_related("chat")
            .order_by("-create_time")[: self.BACKFILL_LIMIT]
        )
        ensure_quality_reviews(records)

    def _summary(self):
        problem_reviews = self._queryset().exclude(status=MarketingAnswerQualityStatus.PASS)
        return {
            "total_count": problem_reviews.count(),
            "pending_count": problem_reviews.filter(manual_status=MarketingAnswerManualReviewStatus.PENDING).count(),
            "reviewed_count": problem_reviews.exclude(manual_status=MarketingAnswerManualReviewStatus.PENDING).count(),
            "revised_count": problem_reviews.filter(manual_status=MarketingAnswerManualReviewStatus.REVISED).count(),
            "high_risk_count": problem_reviews.filter(status=MarketingAnswerQualityStatus.HIGH_RISK).count(),
        }

    def page(self, current_page, page_size, params):
        serializer = MarketingQualityReviewQuerySerializer(data=params)
        values = validate_or_raise(serializer)
        self._backfill_recent_records()
        rows = self._queryset()
        task_id = values.get("task_id")
        quality_status = values.get("quality_status")
        manual_status = values.get("manual_status")
        risk_type = values.get("risk_type")
        keyword = values.get("keyword")
        if task_id:
            rows = rows.filter(task_id=task_id)
        if quality_status:
            rows = rows.filter(status=quality_status)
        else:
            rows = rows.exclude(status=MarketingAnswerQualityStatus.PASS)
        if manual_status:
            rows = rows.filter(manual_status=manual_status)
        if risk_type:
            rows = rows.filter(risk_types__contains=[risk_type])
        if keyword:
            rows = rows.filter(
                Q(task__name__icontains=keyword)
                | Q(customer__name__icontains=keyword)
                | Q(record__problem_text__icontains=keyword)
                | Q(record__answer_text__icontains=keyword)
                | Q(revised_answer__icontains=keyword)
            )
        rows = rows.annotate(
            pending_order=Case(
                When(manual_status=MarketingAnswerManualReviewStatus.PENDING, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
            risk_order=Case(
                When(status=MarketingAnswerQualityStatus.HIGH_RISK, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
        ).order_by("pending_order", "risk_order", "-record__create_time")
        total = rows.count()
        start = (current_page - 1) * page_size
        page = Page(
            total,
            [serialize_quality_workbench_record(row) for row in rows[start : start + page_size]],
            current_page,
            page_size,
        )
        page["summary"] = self._summary()
        return page

    @transaction.atomic
    def handle(self, review_id, data):
        serializer = MarketingQualityReviewHandleSerializer(data=data)
        values = validate_or_raise(serializer)
        review = (
            MarketingAnswerQualityReview.objects.select_for_update()
            .filter(id=review_id, workspace_id=self.workspace_id)
            .first()
        )
        if review is None:
            raise AppApiException(404, "回答质检记录不存在")
        action = values["action"]
        revised_answer = values.get("revised_answer", "")
        if action == MarketingAnswerManualReviewAction.REVISE:
            if revised_answer.strip() == (review.record.answer_text or "").strip():
                raise AppApiException(400, "修订答案不能与原回答完全相同")
            current_status = MarketingAnswerManualReviewStatus.REVISED
        elif action == MarketingAnswerManualReviewAction.CONFIRM_PASS:
            current_status = MarketingAnswerManualReviewStatus.CONFIRMED_PASS
        else:
            current_status = MarketingAnswerManualReviewStatus.CONFIRMED_ISSUE
        reviewer_name = ""
        if self.user:
            reviewer_name = self.user.nick_name or self.user.username
        previous_status = review.manual_status
        revision = review.manual_revision + 1
        if action == MarketingAnswerManualReviewAction.REVISE:
            review.revised_answer = revised_answer
        review.manual_status = current_status
        review.reviewer = self.user
        review.reviewer_name = reviewer_name
        review.reviewed_at = timezone.now()
        review.review_note = values.get("note", "")
        review.manual_revision = revision
        review.save(
            update_fields=[
                "manual_status",
                "reviewer",
                "reviewer_name",
                "reviewed_at",
                "review_note",
                "revised_answer",
                "manual_revision",
                "update_time",
            ]
        )
        MarketingAnswerQualityReviewActionRecord.objects.create(
            workspace_id=self.workspace_id,
            review=review,
            task=review.task,
            user=self.user,
            reviewer_name=reviewer_name,
            action=action,
            previous_status=previous_status,
            current_status=current_status,
            original_answer=review.record.answer_text or "",
            revised_answer=review.revised_answer,
            note=review.review_note,
            revision=revision,
        )
        from marketing.serializers.quality_policy import reconcile_quality_policy_eligibility

        reconcile_quality_policy_eligibility(self.workspace_id)
        return serialize_quality_workbench_record(self._queryset().get(id=review.id))
