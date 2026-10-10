import uuid_utils.compat as uuid
from django.db import models

from common.mixins.app_model_mixin import AppModelMixin
from users.models import User

from .resource_coordination import DispatchResourcePool, DispatchTask


class EventSourceType(models.TextChoices):
    WEBHOOK = "WEBHOOK", "Webhook"
    SCHEDULED = "SCHEDULED", "定时事件"
    USER = "USER", "用户行为"
    SYSTEM = "SYSTEM", "系统状态"


class FlowVersionStatus(models.TextChoices):
    DRAFT = "DRAFT", "草稿"
    PUBLISHED = "PUBLISHED", "已发布"
    ARCHIVED = "ARCHIVED", "已归档"


class FlowNodeType(models.TextChoices):
    DATA_QUERY = "DATA_QUERY", "数据查询"
    AGENT = "AGENT", "智能体分析"
    REPORT = "REPORT", "报告生成"
    NOTIFICATION = "NOTIFICATION", "告警通知"
    TOOL = "TOOL", "工具调用"
    MANUAL = "MANUAL", "人工节点"


class FlowRunStatus(models.TextChoices):
    PENDING = "PENDING", "待启动"
    RUNNING = "RUNNING", "执行中"
    WAITING = "WAITING", "等待处理"
    SUCCEEDED = "SUCCEEDED", "已成功"
    FAILED = "FAILED", "已失败"
    CANCELLED = "CANCELLED", "已取消"


class FlowNodeRunStatus(models.TextChoices):
    PENDING = "PENDING", "等待依赖"
    READY = "READY", "可执行"
    WAITING_RESOURCE = "WAITING_RESOURCE", "等待资源"
    RUNNING = "RUNNING", "执行中"
    WAITING_MANUAL = "WAITING_MANUAL", "等待人工"
    SUCCEEDED = "SUCCEEDED", "已成功"
    FAILED = "FAILED", "已失败"
    SKIPPED = "SKIPPED", "已跳过"
    CANCELLED = "CANCELLED", "已取消"


class NodeDependencyMode(models.TextChoices):
    ALL_SUCCESS = "ALL_SUCCESS", "全部成功"
    ANY_SUCCESS = "ANY_SUCCESS", "任一成功"
    ALL_TERMINAL = "ALL_TERMINAL", "全部结束"


class NodeActivationMode(models.TextChoices):
    NORMAL = "NORMAL", "常规执行"
    FALLBACK_ONLY = "FALLBACK_ONLY", "仅降级激活"


class NodeFailureStrategy(models.TextChoices):
    FAIL_RUN = "FAIL_RUN", "终止流程"
    FALLBACK = "FALLBACK", "切换备用路径"
    CONTINUE = "CONTINUE", "记录失败并继续"


class NodeAttemptStatus(models.TextChoices):
    RUNNING = "RUNNING", "执行中"
    SUCCEEDED = "SUCCEEDED", "已成功"
    FAILED = "FAILED", "已失败"
    TIMED_OUT = "TIMED_OUT", "已超时"


class FlowRunEventType(models.TextChoices):
    RUN_CREATED = "RUN_CREATED", "运行已创建"
    NODE_READY = "NODE_READY", "节点已就绪"
    NODE_QUEUED = "NODE_QUEUED", "节点等待资源"
    NODE_STARTED = "NODE_STARTED", "节点开始执行"
    NODE_SUCCEEDED = "NODE_SUCCEEDED", "节点执行成功"
    NODE_FAILED = "NODE_FAILED", "节点执行失败"
    NODE_SKIPPED = "NODE_SKIPPED", "节点已跳过"
    NODE_RETRYING = "NODE_RETRYING", "节点准备重试"
    NODE_TIMED_OUT = "NODE_TIMED_OUT", "节点执行超时"
    NODE_FALLBACK = "NODE_FALLBACK", "备用路径已激活"
    NODE_RECOVERED = "NODE_RECOVERED", "自愈动作已执行"
    MANUAL_WAITING = "MANUAL_WAITING", "等待人工处理"
    MANUAL_APPROVED = "MANUAL_APPROVED", "人工已通过"
    MANUAL_REJECTED = "MANUAL_REJECTED", "人工已拒绝"
    RUN_SUCCEEDED = "RUN_SUCCEEDED", "运行成功"
    RUN_FAILED = "RUN_FAILED", "运行失败"
    RUN_REPLAYED = "RUN_REPLAYED", "运行已重放"


class EventFlowVersion(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=160)
    description = models.CharField(max_length=512, blank=True, default="")
    version_no = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=FlowVersionStatus.choices,
        default=FlowVersionStatus.DRAFT,
        db_index=True,
    )
    event_type = models.CharField(max_length=128, db_index=True)
    source_types = models.JSONField(default=list)
    event_schema = models.JSONField(default=dict)
    nodes_snapshot = models.JSONField(default=list)
    published_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_constraint=False)

    class Meta:
        db_table = "event_flow_version"
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "code", "version_no"], name="uniq_event_flow_version"
            )
        ]
        indexes = [
            models.Index(
                fields=["workspace_id", "status", "event_type"], name="event_flow_match"
            )
        ]


class StandardEvent(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    event_id = models.CharField(max_length=128)
    idempotency_key = models.CharField(max_length=128)
    source_type = models.CharField(max_length=20, choices=EventSourceType.choices)
    event_type = models.CharField(max_length=128, db_index=True)
    subject = models.CharField(max_length=160, blank=True, default="")
    payload_snapshot = models.JSONField(default=dict)
    metadata_snapshot = models.JSONField(default=dict)
    occurred_at = models.DateTimeField()
    received_at = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_constraint=False)

    class Meta:
        db_table = "standard_event"
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "event_id"], name="uniq_standard_event_id"
            ),
            models.UniqueConstraint(
                fields=["workspace_id", "idempotency_key"], name="uniq_standard_event_idempotency"
            ),
        ]
        indexes = [
            models.Index(
                fields=["workspace_id", "event_type", "-occurred_at"], name="standard_event_lookup"
            )
        ]


class EventFlowRun(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    code = models.CharField(max_length=64, unique=True)
    flow_version = models.ForeignKey(EventFlowVersion, on_delete=models.PROTECT, related_name="runs")
    standard_event = models.ForeignKey(StandardEvent, on_delete=models.PROTECT, related_name="runs")
    status = models.CharField(
        max_length=20,
        choices=FlowRunStatus.choices,
        default=FlowRunStatus.PENDING,
        db_index=True,
    )
    context_snapshot = models.JSONField(default=dict)
    result_summary = models.JSONField(default=dict)
    trace_id = models.CharField(max_length=64, db_index=True, default="")
    replay_of = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replays",
    )
    replay_sequence = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "event_flow_run"
        constraints = [
            models.UniqueConstraint(
                fields=["flow_version", "standard_event"], name="uniq_event_flow_run"
            )
        ]
        indexes = [
            models.Index(
                fields=["workspace_id", "status", "-create_time"], name="event_flow_run_status"
            )
        ]


class EventFlowNodeRun(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    run = models.ForeignKey(EventFlowRun, on_delete=models.CASCADE, related_name="node_runs")
    node_code = models.CharField(max_length=64)
    node_name = models.CharField(max_length=160)
    node_type = models.CharField(max_length=24, choices=FlowNodeType.choices)
    sequence_no = models.PositiveIntegerField()
    dependencies = models.JSONField(default=list)
    dependency_mode = models.CharField(
        max_length=20,
        choices=NodeDependencyMode.choices,
        default=NodeDependencyMode.ALL_SUCCESS,
    )
    activation_mode = models.CharField(
        max_length=20,
        choices=NodeActivationMode.choices,
        default=NodeActivationMode.NORMAL,
    )
    condition_snapshot = models.JSONField(default=dict)
    max_retries = models.PositiveSmallIntegerField(default=0)
    timeout_seconds = models.PositiveIntegerField(default=300)
    failure_strategy = models.CharField(
        max_length=20,
        choices=NodeFailureStrategy.choices,
        default=NodeFailureStrategy.FAIL_RUN,
    )
    fallback_node_code = models.CharField(max_length=64, blank=True, default="")
    recovery_action = models.CharField(max_length=64, blank=True, default="")
    active_attempt_no = models.PositiveSmallIntegerField(default=0)
    failure_handled = models.BooleanField(default=False)
    fallback_activated = models.BooleanField(default=False)
    span_id = models.CharField(max_length=64, blank=True, default="")
    resource_pool = models.ForeignKey(
        DispatchResourcePool,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="flow_node_runs",
    )
    priority = models.PositiveSmallIntegerField(default=50)
    required_units = models.PositiveIntegerField(default=1)
    mutex_keys = models.JSONField(default=list)
    status = models.CharField(
        max_length=24,
        choices=FlowNodeRunStatus.choices,
        default=FlowNodeRunStatus.PENDING,
        db_index=True,
    )
    dispatch_task = models.ForeignKey(
        DispatchTask,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="flow_node_runs",
    )
    input_snapshot = models.JSONField(default=dict)
    output_snapshot = models.JSONField(default=dict)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "event_flow_node_run"
        constraints = [
            models.UniqueConstraint(fields=["run", "node_code"], name="uniq_event_flow_node_run")
        ]
        ordering = ["sequence_no"]


class EventFlowNodeAttempt(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    run = models.ForeignKey(EventFlowRun, on_delete=models.CASCADE, related_name="attempts")
    node_run = models.ForeignKey(
        EventFlowNodeRun, on_delete=models.CASCADE, related_name="attempts"
    )
    attempt_no = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=20, choices=NodeAttemptStatus.choices)
    dispatch_task = models.ForeignKey(
        DispatchTask,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="flow_node_attempts",
    )
    trace_id = models.CharField(max_length=64, db_index=True)
    span_id = models.CharField(max_length=64)
    timeout_seconds = models.PositiveIntegerField(default=300)
    input_snapshot = models.JSONField(default=dict)
    output_snapshot = models.JSONField(default=dict)
    error_snapshot = models.JSONField(default=dict)
    recovery_action = models.CharField(max_length=64, blank=True, default="")
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "event_flow_node_attempt"
        constraints = [
            models.UniqueConstraint(
                fields=["node_run", "attempt_no"], name="uniq_event_flow_node_attempt"
            )
        ]
        ordering = ["attempt_no"]


class EventFlowRunEvent(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    run = models.ForeignKey(EventFlowRun, on_delete=models.CASCADE, related_name="events")
    node_run = models.ForeignKey(
        EventFlowNodeRun,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )
    sequence_no = models.PositiveIntegerField()
    event_type = models.CharField(max_length=24, choices=FlowRunEventType.choices)
    detail = models.JSONField(default=dict)
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_constraint=False)

    class Meta:
        db_table = "event_flow_run_event"
        constraints = [
            models.UniqueConstraint(fields=["run", "sequence_no"], name="uniq_event_flow_run_event_seq")
        ]
        ordering = ["sequence_no"]
