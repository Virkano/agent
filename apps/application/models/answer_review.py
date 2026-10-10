"""Workspace-scoped human review of customer-safe answer decisions."""

import uuid_utils.compat as uuid
from django.db import models


class ServiceAnswerReview(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "待复核"
        CONFIRMED = "CONFIRMED", "确认问题"
        DISMISSED = "DISMISSED", "排除问题"

    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=128, db_index=True)
    record = models.OneToOneField("application.ChatRecord", on_delete=models.CASCADE, related_name="service_answer_review")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    risk_types = models.JSONField(default=list)
    delivery_action = models.CharField(max_length=32)
    reference_count = models.PositiveIntegerField(default=0)
    rule_version = models.CharField(max_length=64)
    revision = models.PositiveIntegerField(default=0)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "service_answer_review"
        indexes = [models.Index(fields=["workspace_id", "status", "create_time"], name="service_review_queue")]


class ServiceAnswerReviewAction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    review = models.ForeignKey(ServiceAnswerReview, on_delete=models.CASCADE, related_name="actions")
    revision = models.PositiveIntegerField()
    previous_status = models.CharField(max_length=16)
    current_status = models.CharField(max_length=16)
    reviewer_id = models.CharField(max_length=128)
    reviewer_name = models.CharField(max_length=128)
    note = models.TextField()
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "service_answer_review_action"
        constraints = [models.UniqueConstraint(fields=["review", "revision"], name="service_review_action_revision")]
