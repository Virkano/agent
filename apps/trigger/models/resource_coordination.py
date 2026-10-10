import uuid_utils.compat as uuid
from django.db import models

from common.mixins.app_model_mixin import AppModelMixin
from users.models import User


class ResourcePoolType(models.TextChoices):
    AGENT = "AGENT", "智能体"
    MODEL = "MODEL", "模型"
    TOOL = "TOOL", "工具"
    WORKER = "WORKER", "执行器"


class DispatchTaskSource(models.TextChoices):
    WEBHOOK = "WEBHOOK", "Webhook"
    SCHEDULED = "SCHEDULED", "定时触发"
    USER = "USER", "用户发起"
    SYSTEM = "SYSTEM", "系统事件"


class DispatchTaskStatus(models.TextChoices):
    QUEUED = "QUEUED", "等待资源"
    RUNNING = "RUNNING", "执行中"
    SUCCEEDED = "SUCCEEDED", "已成功"
    FAILED = "FAILED", "已失败"
    CANCELLED = "CANCELLED", "已取消"


class ResourceLeaseStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "占用中"
    RELEASED = "RELEASED", "已释放"
    EXPIRED = "EXPIRED", "已超时回收"


class DispatchEventType(models.TextChoices):
    SUBMITTED = "SUBMITTED", "已提交"
    ALLOCATED = "ALLOCATED", "已分配"
    QUEUED = "QUEUED", "进入等待"
    SUCCEEDED = "SUCCEEDED", "执行成功"
    FAILED = "FAILED", "执行失败"
    CANCELLED = "CANCELLED", "已取消"
    LEASE_EXPIRED = "LEASE_EXPIRED", "租约超时"


class DispatchResourcePool(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    resource_type = models.CharField(max_length=20, choices=ResourcePoolType.choices)
    capacity = models.PositiveIntegerField(default=1)
    max_units_per_task = models.PositiveIntegerField(default=1)
    lease_timeout_seconds = models.PositiveIntegerField(default=300)
    enabled = models.BooleanField(default=True, db_index=True)
    description = models.CharField(max_length=512, blank=True, default="")
    metadata = models.JSONField(default=dict)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_constraint=False)

    class Meta:
        db_table = "dispatch_resource_pool"
        constraints = [
            models.UniqueConstraint(fields=["workspace_id", "code"], name="uniq_dispatch_pool_code"),
            models.CheckConstraint(condition=models.Q(capacity__gte=1), name="dispatch_pool_capacity_gte_1"),
            models.CheckConstraint(condition=models.Q(max_units_per_task__gte=1), name="dispatch_pool_units_gte_1"),
        ]
        indexes = [models.Index(fields=["workspace_id", "enabled"], name="dispatch_pool_ws_enabled")]


class DispatchTask(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    pool = models.ForeignKey(DispatchResourcePool, on_delete=models.PROTECT, related_name="tasks")
    request_id = models.CharField(max_length=128)
    idempotency_key = models.CharField(max_length=128)
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=160)
    source = models.CharField(max_length=20, choices=DispatchTaskSource.choices)
    source_reference = models.CharField(max_length=160, blank=True, default="")
    priority = models.PositiveSmallIntegerField(default=50, db_index=True)
    required_units = models.PositiveIntegerField(default=1)
    mutex_keys = models.JSONField(default=list)
    status = models.CharField(
        max_length=20,
        choices=DispatchTaskStatus.choices,
        default=DispatchTaskStatus.QUEUED,
        db_index=True,
    )
    queue_reason = models.CharField(max_length=256, blank=True, default="")
    payload_snapshot = models.JSONField(default=dict)
    result_summary = models.JSONField(default=dict)
    queued_at = models.DateTimeField()
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_constraint=False)

    class Meta:
        db_table = "dispatch_task"
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "request_id"], name="uniq_dispatch_task_request"
            ),
            models.UniqueConstraint(
                fields=["workspace_id", "idempotency_key"], name="uniq_dispatch_task_idempotency"
            ),
            models.CheckConstraint(
                condition=models.Q(priority__gte=1, priority__lte=100),
                name="dispatch_task_priority_range",
            ),
            models.CheckConstraint(condition=models.Q(required_units__gte=1), name="dispatch_task_units_gte_1"),
        ]
        indexes = [
            models.Index(
                fields=["workspace_id", "status", "-priority", "queued_at"],
                name="dispatch_task_queue_order",
            )
        ]


class DispatchResourceLease(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    pool = models.ForeignKey(DispatchResourcePool, on_delete=models.PROTECT, related_name="leases")
    task = models.OneToOneField(DispatchTask, on_delete=models.CASCADE, related_name="lease")
    units = models.PositiveIntegerField()
    mutex_keys = models.JSONField(default=list)
    status = models.CharField(
        max_length=20,
        choices=ResourceLeaseStatus.choices,
        default=ResourceLeaseStatus.ACTIVE,
        db_index=True,
    )
    acquired_at = models.DateTimeField()
    expires_at = models.DateTimeField(db_index=True)
    released_at = models.DateTimeField(null=True, blank=True)
    release_reason = models.CharField(max_length=256, blank=True, default="")

    class Meta:
        db_table = "dispatch_resource_lease"
        indexes = [
            models.Index(
                fields=["workspace_id", "pool", "status", "expires_at"],
                name="dispatch_lease_active",
            )
        ]


class DispatchTaskEvent(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    task = models.ForeignKey(DispatchTask, on_delete=models.CASCADE, related_name="events")
    sequence_no = models.PositiveIntegerField()
    event_type = models.CharField(max_length=24, choices=DispatchEventType.choices)
    previous_status = models.CharField(max_length=20, blank=True, default="")
    current_status = models.CharField(max_length=20, choices=DispatchTaskStatus.choices)
    detail = models.JSONField(default=dict)
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_constraint=False)

    class Meta:
        db_table = "dispatch_task_event"
        constraints = [
            models.UniqueConstraint(fields=["task", "sequence_no"], name="uniq_dispatch_task_event_seq")
        ]
        ordering = ["sequence_no"]
