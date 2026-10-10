import uuid_utils.compat as uuid
from django.db import models

from common.mixins.app_model_mixin import AppModelMixin
from users.models import User


class RehearsalCustomerScope(models.TextChoices):
    PUBLIC = "PUBLIC", "公众客户"
    ENTERPRISE = "ENTERPRISE", "政企客户"
    MIXED = "MIXED", "公客与政企"


class RehearsalScenarioStatus(models.TextChoices):
    DRAFT = "DRAFT", "草稿"
    READY = "READY", "可预演"
    ARCHIVED = "ARCHIVED", "已归档"


class RehearsalInstanceStatus(models.TextChoices):
    DRAFT = "DRAFT", "数据准备中"
    READY = "READY", "待启动"
    RUNNING = "RUNNING", "预演中"
    COMPLETED = "COMPLETED", "已完成"
    CANCELLED = "CANCELLED", "已取消"
    FAILED = "FAILED", "失败"


class RehearsalInstanceAction(models.TextChoices):
    PREPARE = "PREPARE", "完成数据准备"
    START = "START", "启动预演"
    COMPLETE = "COMPLETE", "完成预演"
    CANCEL = "CANCEL", "取消预演"


class RehearsalEventType(models.TextChoices):
    CREATED = "CREATED", "创建实例"
    DATA_GENERATED = "DATA_GENERATED", "生成申告数据"
    DATA_IMPORTED = "DATA_IMPORTED", "导入申告数据"
    DATA_SIMULATED = "DATA_SIMULATED", "生成模拟数据"
    CAPABILITY_CALLED = "CAPABILITY_CALLED", "调用模拟能力"
    FAULT_CONFIGURATION_APPLIED = "FAULT_CONFIG_APPLIED", "应用故障模拟配置"
    FAULT_REPORT_UPDATED = "FAULT_REPORT_UPDATED", "更新故障上报"
    AUXILIARY_SIMULATED = "AUXILIARY_SIMULATED", "执行辅助模拟"
    PREPARED = "PREPARED", "完成数据准备"
    STARTED = "STARTED", "启动预演"
    COMPLETED = "COMPLETED", "完成预演"
    CANCELLED = "CANCELLED", "取消预演"


class ComplaintDataSource(models.TextChoices):
    GENERATED = "GENERATED", "系统生成"
    IMPORTED = "IMPORTED", "人工导入"


class ComplaintBatchStatus(models.TextChoices):
    READY = "READY", "校验通过"
    PARTIAL = "PARTIAL", "部分通过"
    FAILED = "FAILED", "校验失败"


class ComplaintValidationStatus(models.TextChoices):
    VALID = "VALID", "有效"
    INVALID = "INVALID", "无效"


class ComplaintSeverity(models.TextChoices):
    LOW = "LOW", "一般"
    MEDIUM = "MEDIUM", "关注"
    HIGH = "HIGH", "严重"
    CRITICAL = "CRITICAL", "紧急"


class ComplaintStatus(models.TextChoices):
    OPEN = "OPEN", "待处理"
    PROCESSING = "PROCESSING", "处理中"
    RESOLVED = "RESOLVED", "已解决"


class ProcessRunStatus(models.TextChoices):
    PENDING = "PENDING", "待执行"
    RUNNING = "RUNNING", "执行中"
    BLOCKED = "BLOCKED", "已阻塞"
    COMPLETED = "COMPLETED", "已完成"
    CANCELLED = "CANCELLED", "已取消"
    FAILED = "FAILED", "失败"


class ProcessStepStatus(models.TextChoices):
    PENDING = "PENDING", "待执行"
    RUNNING = "RUNNING", "执行中"
    BLOCKED = "BLOCKED", "已阻塞"
    COMPLETED = "COMPLETED", "已完成"
    SKIPPED = "SKIPPED", "已跳过"
    FAILED = "FAILED", "失败"


class ProcessRunAction(models.TextChoices):
    START = "START", "启动流程"
    COMPLETE_STEP = "COMPLETE_STEP", "完成当前步骤"
    AUTO_ADVANCE = "AUTO_ADVANCE", "自动推进"
    BLOCK = "BLOCK", "阻塞当前步骤"
    RESUME = "RESUME", "恢复当前步骤"
    SKIP = "SKIP", "跳过当前步骤"
    FAIL = "FAIL", "标记失败"
    CANCEL = "CANCEL", "取消流程"


class DataSimulationKind(models.TextChoices):
    METRIC = "METRIC", "指标趋势"
    SENTIMENT = "SENTIMENT", "舆情趋势"


class DataSimulationStatus(models.TextChoices):
    READY = "READY", "生成完成"
    FAILED = "FAILED", "生成失败"


class DataDistribution(models.TextChoices):
    LINEAR = "LINEAR", "线性趋势"
    WAVE = "WAVE", "周期波动"
    RANDOM = "RANDOM", "随机分布"
    STEP = "STEP", "阶跃变化"


class DataModelBuildStrategy(models.TextChoices):
    FULL_INSTANCE = "FULL_INSTANCE", "全量实例构建"
    SCENE_LINKED = "SCENE_LINKED", "场景关联构建"
    FAULT_CHAIN = "FAULT_CHAIN", "故障链路构建"


class DataModelQualityStatus(models.TextChoices):
    PASS = "PASS", "校验通过"
    WARN = "WARN", "存在提醒"
    FAIL = "FAIL", "校验失败"


class DataModelLoadStatus(models.TextChoices):
    LOADED = "LOADED", "加载完成"
    PARTIAL = "PARTIAL", "部分加载"
    FAILED = "FAILED", "加载失败"


class TracebackScope(models.TextChoices):
    FULL_INSTANCE = "FULL_INSTANCE", "全量实例"
    INCIDENT_WINDOW = "INCIDENT_WINDOW", "故障窗口"
    CUSTOM = "CUSTOM", "自定义窗口"


class TracebackStatus(models.TextChoices):
    READY = "READY", "已生成"
    EMPTY = "EMPTY", "无回溯数据"
    ARCHIVED = "ARCHIVED", "已归档"


class SceneReplayStatus(models.TextChoices):
    READY = "READY", "可回放"
    EMPTY = "EMPTY", "无流量数据"


class FaultReportTemplateStatus(models.TextChoices):
    READY = "READY", "可使用"
    ARCHIVED = "ARCHIVED", "已归档"


class FaultReportLevel(models.TextChoices):
    LEVEL_1 = "LEVEL_1", "一级重大故障"
    LEVEL_2 = "LEVEL_2", "二级重大故障"
    LEVEL_3 = "LEVEL_3", "三级重大故障"
    LEVEL_4 = "LEVEL_4", "一般故障"


class FaultReportStatus(models.TextChoices):
    DRAFT = "DRAFT", "待上报"
    REPORTED = "REPORTED", "已上报"
    PROCESSING = "PROCESSING", "处置中"
    RECOVERED = "RECOVERED", "已恢复"
    CLOSED = "CLOSED", "已关闭"


class FaultReportAction(models.TextChoices):
    CREATED = "CREATED", "创建上报"
    SUBMITTED = "SUBMITTED", "正式上报"
    ACCEPTED = "ACCEPTED", "受理处置"
    STAGE_ADVANCED = "STAGE_ADVANCED", "推进阶段"
    ESCALATED = "ESCALATED", "升级故障"
    ATTACHMENT_ADDED = "ATTACHMENT_ADDED", "添加附件"
    RECOVERED = "RECOVERED", "确认恢复"
    CLOSED = "CLOSED", "关闭上报"


class AuxiliarySimulationStatus(models.TextChoices):
    COMPLETED = "COMPLETED", "模拟完成"
    ATTENTION = "ATTENTION", "存在异常点"


class RandomFactorCategory(models.TextChoices):
    NETWORK = "NETWORK", "网络类"
    FAULT = "FAULT", "故障类"
    TRAFFIC = "TRAFFIC", "流量类"


class RandomFactorDistribution(models.TextChoices):
    UNIFORM = "UNIFORM", "均匀分布"
    NORMAL = "NORMAL", "正态分布"


class SceneRunStatus(models.TextChoices):
    PENDING = "PENDING", "待执行"
    RUNNING = "RUNNING", "执行中"
    COMPLETED = "COMPLETED", "已完成"
    CANCELLED = "CANCELLED", "已取消"
    FAILED = "FAILED", "失败"


class SceneStepStatus(models.TextChoices):
    PENDING = "PENDING", "待执行"
    RUNNING = "RUNNING", "执行中"
    COMPLETED = "COMPLETED", "已完成"
    SKIPPED = "SKIPPED", "已跳过"
    FAILED = "FAILED", "失败"


class SceneRunAction(models.TextChoices):
    START = "START", "启动场景"
    COMPLETE_STEP = "COMPLETE_STEP", "完成当前步骤"
    SKIP_STEP = "SKIP_STEP", "跳过当前步骤"
    FAIL = "FAIL", "标记失败"
    CANCEL = "CANCEL", "取消场景"


class SceneLibraryStatus(models.TextChoices):
    DRAFT = "DRAFT", "草稿"
    READY = "READY", "可复用"
    ARCHIVED = "ARCHIVED", "已归档"


class SceneLibraryVisibility(models.TextChoices):
    WORKSPACE = "WORKSPACE", "工作空间可用"
    PRIVATE = "PRIVATE", "仅创建人可用"


class SceneLibraryAction(models.TextChoices):
    CREATED = "CREATED", "创建场景库"
    CLONED = "CLONED", "克隆版本"
    PUBLISHED = "PUBLISHED", "发布场景库"
    ARCHIVED = "ARCHIVED", "归档场景库"
    RUN_CREATED = "RUN_CREATED", "创建场景执行"


class WorkOrderPriority(models.TextChoices):
    LOW = "LOW", "一般"
    MEDIUM = "MEDIUM", "关注"
    HIGH = "HIGH", "高"
    CRITICAL = "CRITICAL", "紧急"


class WorkOrderStatus(models.TextChoices):
    OPEN = "OPEN", "待受理"
    PROCESSING = "PROCESSING", "处理中"
    RESOLVED = "RESOLVED", "已解决"
    CLOSED = "CLOSED", "已关闭"


class WorkOrderAction(models.TextChoices):
    ACCEPT = "ACCEPT", "受理工单"
    RESOLVE = "RESOLVE", "解决工单"
    CLOSE = "CLOSE", "关闭工单"
    REOPEN = "REOPEN", "重新打开"


class AlertSeverity(models.TextChoices):
    LOW = "LOW", "一般"
    MEDIUM = "MEDIUM", "关注"
    HIGH = "HIGH", "严重"
    CRITICAL = "CRITICAL", "紧急"


class AlertStatus(models.TextChoices):
    PENDING = "PENDING", "待上报"
    ACTIVE = "ACTIVE", "活动告警"
    ACKNOWLEDGED = "ACKNOWLEDGED", "已确认"
    RECOVERED = "RECOVERED", "已恢复"


class AlertAction(models.TextChoices):
    REPORT = "REPORT", "上报告警"
    ACKNOWLEDGE = "ACKNOWLEDGE", "确认告警"
    RECOVER = "RECOVER", "恢复告警"


class CapabilityMockKind(models.TextChoices):
    API = "API", "API Mock"
    ATOMIC = "ATOMIC", "原子能力"


class CapabilityCallStatus(models.TextChoices):
    SUCCEEDED = "SUCCEEDED", "调用成功"
    FAILED = "FAILED", "调用失败"
    TIMEOUT = "TIMEOUT", "调用超时"


class FaultConfigurationStatus(models.TextChoices):
    DRAFT = "DRAFT", "待校验"
    READY = "READY", "可应用"
    ARCHIVED = "ARCHIVED", "已归档"


class FaultConfigurationAction(models.TextChoices):
    CREATED = "CREATED", "创建配置"
    VALIDATED = "VALIDATED", "校验配置"
    CLONED = "CLONED", "克隆版本"
    APPLIED = "APPLIED", "应用到实例"
    ARCHIVED = "ARCHIVED", "归档配置"


class RehearsalScenario(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=500, default="", blank=True)
    customer_scope = models.CharField(
        max_length=16,
        choices=RehearsalCustomerScope.choices,
        default=RehearsalCustomerScope.MIXED,
    )
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=16,
        choices=RehearsalScenarioStatus.choices,
        default=RehearsalScenarioStatus.READY,
        db_index=True,
    )
    configuration = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_scenario"
        ordering = ["-update_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "code", "version"],
                name="rehearsal_scenario_ws_code_ver",
            )
        ]


class RehearsalComplaintTemplate(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    customer_type = models.CharField(max_length=16, choices=RehearsalCustomerScope.choices)
    version = models.PositiveIntegerField(default=1)
    enabled = models.BooleanField(default=True, db_index=True)
    profile_schema = models.JSONField(default=dict, blank=True)
    complaint_schema = models.JSONField(default=dict, blank=True)
    categories = models.JSONField(default=list, blank=True)
    content_patterns = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_complaint_template"
        ordering = ["customer_type", "code", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "code", "version"],
                name="rehearsal_template_ws_code_ver",
            )
        ]


class RehearsalInstance(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    scenario = models.ForeignKey(RehearsalScenario, on_delete=models.PROTECT, related_name="instances")
    request_id = models.CharField(max_length=160)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    status = models.CharField(
        max_length=16,
        choices=RehearsalInstanceStatus.choices,
        default=RehearsalInstanceStatus.DRAFT,
        db_index=True,
    )
    planned_start_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    fault_configuration = models.ForeignKey(
        "RehearsalFaultConfiguration",
        on_delete=models.SET_NULL,
        related_name="bound_instances",
        null=True,
        blank=True,
    )
    fault_configuration_snapshot = models.JSONField(default=dict, blank=True)
    parameters = models.JSONField(default=dict, blank=True)
    summary = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_instance"
        ordering = ["-update_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "request_id"],
                name="rehearsal_instance_ws_request",
            ),
            models.UniqueConstraint(fields=["workspace_id", "code"], name="rehearsal_instance_ws_code"),
        ]


class RehearsalComplaintBatch(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    instance = models.ForeignKey(RehearsalInstance, on_delete=models.CASCADE, related_name="batches")
    template = models.ForeignKey(
        RehearsalComplaintTemplate,
        on_delete=models.SET_NULL,
        related_name="batches",
        null=True,
        blank=True,
    )
    request_id = models.CharField(max_length=160)
    source = models.CharField(max_length=16, choices=ComplaintDataSource.choices)
    status = models.CharField(max_length=16, choices=ComplaintBatchStatus.choices, db_index=True)
    version = models.PositiveIntegerField(default=1)
    filename = models.CharField(max_length=255, default="", blank=True)
    total_count = models.PositiveIntegerField(default=0)
    valid_count = models.PositiveIntegerField(default=0)
    invalid_count = models.PositiveIntegerField(default=0)
    time_start = models.DateTimeField(null=True, blank=True)
    time_end = models.DateTimeField(null=True, blank=True)
    error_summary = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_complaint_batch"
        ordering = ["-create_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "request_id"],
                name="rehearsal_batch_ws_request",
            )
        ]


class RehearsalComplaint(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    instance = models.ForeignKey(RehearsalInstance, on_delete=models.CASCADE, related_name="complaints")
    batch = models.ForeignKey(RehearsalComplaintBatch, on_delete=models.CASCADE, related_name="complaints")
    sequence_no = models.PositiveIntegerField()
    customer_type = models.CharField(max_length=16, choices=RehearsalCustomerScope.choices, db_index=True)
    customer_ref = models.CharField(max_length=64, default="", blank=True)
    customer_name = models.CharField(max_length=128, default="", blank=True)
    contact_masked = models.CharField(max_length=64, default="", blank=True)
    customer_segment = models.CharField(max_length=64, default="", blank=True)
    occurred_at = models.DateTimeField(null=True, blank=True, db_index=True)
    region = models.CharField(max_length=64, default="", blank=True)
    channel = models.CharField(max_length=32, default="", blank=True)
    category = models.CharField(max_length=64, default="", blank=True)
    severity = models.CharField(max_length=16, choices=ComplaintSeverity.choices, db_index=True)
    status = models.CharField(
        max_length=16,
        choices=ComplaintStatus.choices,
        default=ComplaintStatus.OPEN,
        db_index=True,
    )
    title = models.CharField(max_length=160, default="", blank=True)
    content = models.TextField(default="", blank=True)
    validation_status = models.CharField(
        max_length=16,
        choices=ComplaintValidationStatus.choices,
        db_index=True,
    )
    validation_errors = models.JSONField(default=list, blank=True)
    raw_data = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "rehearsal_complaint"
        ordering = ["occurred_at", "sequence_no"]
        constraints = [models.UniqueConstraint(fields=["batch", "sequence_no"], name="rehearsal_complaint_batch_seq")]
        indexes = [
            models.Index(fields=["workspace_id", "instance", "occurred_at"], name="rehearsal_comp_ws_inst_time"),
            models.Index(fields=["workspace_id", "severity", "status"], name="rehearsal_comp_ws_sev_stat"),
        ]


class RehearsalInstanceEvent(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    instance = models.ForeignKey(RehearsalInstance, on_delete=models.CASCADE, related_name="events")
    sequence_no = models.PositiveIntegerField()
    event_type = models.CharField(max_length=24, choices=RehearsalEventType.choices)
    previous_status = models.CharField(max_length=16, choices=RehearsalInstanceStatus.choices)
    current_status = models.CharField(max_length=16, choices=RehearsalInstanceStatus.choices)
    detail = models.JSONField(default=dict, blank=True)
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_instance_event"
        ordering = ["sequence_no"]
        constraints = [models.UniqueConstraint(fields=["instance", "sequence_no"], name="rehearsal_event_instance_seq")]


class RehearsalProcessTemplate(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=500, default="", blank=True)
    customer_scope = models.CharField(
        max_length=16,
        choices=RehearsalCustomerScope.choices,
        default=RehearsalCustomerScope.MIXED,
    )
    version = models.PositiveIntegerField(default=1)
    enabled = models.BooleanField(default=True, db_index=True)
    auto_advance = models.BooleanField(default=False)
    steps = models.JSONField(default=list)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_process_template"
        ordering = ["customer_scope", "code", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "code", "version"],
                name="rehearsal_process_tpl_ws_code_ver",
            )
        ]


class RehearsalProcessRun(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    instance = models.ForeignKey(RehearsalInstance, on_delete=models.CASCADE, related_name="process_runs")
    template = models.ForeignKey(RehearsalProcessTemplate, on_delete=models.PROTECT, related_name="runs")
    request_id = models.CharField(max_length=160)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    status = models.CharField(
        max_length=16,
        choices=ProcessRunStatus.choices,
        default=ProcessRunStatus.PENDING,
        db_index=True,
    )
    auto_advance = models.BooleanField(default=False)
    current_step_index = models.PositiveIntegerField(default=0)
    current_step_code = models.CharField(max_length=64, default="", blank=True)
    total_steps = models.PositiveIntegerField(default=0)
    completed_steps = models.PositiveIntegerField(default=0)
    progress_percent = models.PositiveSmallIntegerField(default=0)
    blocked_reason = models.CharField(max_length=500, default="", blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    template_snapshot = models.JSONField(default=dict)
    summary = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_process_run"
        ordering = ["-update_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "request_id"],
                name="rehearsal_process_run_ws_request",
            ),
            models.UniqueConstraint(fields=["workspace_id", "code"], name="rehearsal_process_run_ws_code"),
        ]
        indexes = [models.Index(fields=["workspace_id", "status"], name="rehearsal_proc_ws_status")]


class RehearsalProcessStep(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    run = models.ForeignKey(RehearsalProcessRun, on_delete=models.CASCADE, related_name="steps")
    sequence_no = models.PositiveIntegerField()
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=500, default="", blank=True)
    owner_role = models.CharField(max_length=64, default="处置人员")
    planned_minutes = models.PositiveIntegerField(default=30)
    status = models.CharField(
        max_length=16,
        choices=ProcessStepStatus.choices,
        default=ProcessStepStatus.PENDING,
        db_index=True,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    note = models.CharField(max_length=500, default="", blank=True)
    output_snapshot = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "rehearsal_process_step"
        ordering = ["sequence_no"]
        constraints = [
            models.UniqueConstraint(fields=["run", "sequence_no"], name="rehearsal_process_step_run_seq"),
            models.UniqueConstraint(fields=["run", "code"], name="rehearsal_process_step_run_code"),
        ]


class RehearsalProcessEvent(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    run = models.ForeignKey(RehearsalProcessRun, on_delete=models.CASCADE, related_name="events")
    step = models.ForeignKey(
        RehearsalProcessStep,
        on_delete=models.SET_NULL,
        related_name="events",
        null=True,
        blank=True,
    )
    sequence_no = models.PositiveIntegerField()
    action = models.CharField(max_length=24)
    previous_status = models.CharField(max_length=16, choices=ProcessRunStatus.choices)
    current_status = models.CharField(max_length=16, choices=ProcessRunStatus.choices)
    detail = models.JSONField(default=dict, blank=True)
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_process_event"
        ordering = ["sequence_no"]
        constraints = [models.UniqueConstraint(fields=["run", "sequence_no"], name="rehearsal_process_event_run_seq")]


class RehearsalDataTemplate(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=500, default="", blank=True)
    kind = models.CharField(max_length=16, choices=DataSimulationKind.choices, db_index=True)
    version = models.PositiveIntegerField(default=1)
    enabled = models.BooleanField(default=True, db_index=True)
    default_rules = models.JSONField(default=list)
    default_tags = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_data_template"
        ordering = ["kind", "code", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "code", "version"],
                name="rehearsal_data_tpl_ws_code_ver",
            )
        ]


class RehearsalDataBatch(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    instance = models.ForeignKey(RehearsalInstance, on_delete=models.CASCADE, related_name="data_batches")
    template = models.ForeignKey(RehearsalDataTemplate, on_delete=models.PROTECT, related_name="batches")
    request_id = models.CharField(max_length=160)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    kind = models.CharField(max_length=16, choices=DataSimulationKind.choices, db_index=True)
    status = models.CharField(
        max_length=16,
        choices=DataSimulationStatus.choices,
        default=DataSimulationStatus.READY,
        db_index=True,
    )
    version = models.PositiveIntegerField(default=1)
    point_count = models.PositiveIntegerField(default=0)
    interval_minutes = models.PositiveIntegerField(default=5)
    time_start = models.DateTimeField()
    time_end = models.DateTimeField()
    rules_snapshot = models.JSONField(default=list)
    tags = models.JSONField(default=list, blank=True)
    summary = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_data_batch"
        ordering = ["-update_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "request_id"],
                name="rehearsal_data_batch_ws_request",
            ),
            models.UniqueConstraint(fields=["workspace_id", "code"], name="rehearsal_data_batch_ws_code"),
        ]
        indexes = [models.Index(fields=["workspace_id", "kind", "status"], name="rehearsal_data_ws_kind_stat")]


class RehearsalDataPoint(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    instance = models.ForeignKey(RehearsalInstance, on_delete=models.CASCADE, related_name="data_points")
    batch = models.ForeignKey(RehearsalDataBatch, on_delete=models.CASCADE, related_name="points")
    sequence_no = models.PositiveIntegerField()
    occurred_at = models.DateTimeField(db_index=True)
    values = models.JSONField(default=dict)
    tags = models.JSONField(default=list, blank=True)
    narrative = models.CharField(max_length=500, default="", blank=True)

    class Meta:
        db_table = "rehearsal_data_point"
        ordering = ["occurred_at", "sequence_no"]
        constraints = [models.UniqueConstraint(fields=["batch", "sequence_no"], name="rehearsal_data_point_batch_seq")]
        indexes = [models.Index(fields=["workspace_id", "instance", "occurred_at"], name="rehearsal_data_ws_inst_time")]


class RehearsalDataModel(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    instance = models.ForeignKey(RehearsalInstance, on_delete=models.CASCADE, related_name="data_models")
    scenario = models.ForeignKey(RehearsalScenario, on_delete=models.PROTECT, related_name="data_models")
    scene_run = models.ForeignKey(
        "RehearsalSceneRun",
        on_delete=models.SET_NULL,
        related_name="data_models",
        null=True,
        blank=True,
    )
    request_id = models.CharField(max_length=160)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=500, default="", blank=True)
    build_strategy = models.CharField(
        max_length=24,
        choices=DataModelBuildStrategy.choices,
        default=DataModelBuildStrategy.FULL_INSTANCE,
        db_index=True,
    )
    transformer_code = models.CharField(max_length=64, default="CANONICAL_V1")
    version_count = models.PositiveIntegerField(default=0)
    current_version = models.PositiveIntegerField(default=0)
    quality_status = models.CharField(
        max_length=16,
        choices=DataModelQualityStatus.choices,
        default=DataModelQualityStatus.WARN,
        db_index=True,
    )
    source_scope = models.JSONField(default=dict, blank=True)
    summary = models.JSONField(default=dict, blank=True)
    lineage = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_data_model"
        ordering = ["-update_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "request_id"],
                name="rehearsal_data_model_ws_request",
            ),
            models.UniqueConstraint(fields=["workspace_id", "code"], name="rehearsal_data_model_ws_code"),
        ]
        indexes = [
            models.Index(fields=["workspace_id", "instance", "quality_status"], name="rehearsal_dm_ws_inst_q"),
            models.Index(fields=["workspace_id", "build_strategy"], name="rehearsal_dm_ws_strategy"),
        ]


class RehearsalDataModelVersion(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    data_model = models.ForeignKey(RehearsalDataModel, on_delete=models.CASCADE, related_name="versions")
    version = models.PositiveIntegerField()
    build_strategy = models.CharField(max_length=24, choices=DataModelBuildStrategy.choices)
    transformer_code = models.CharField(max_length=64, default="CANONICAL_V1")
    source_counts = models.JSONField(default=dict, blank=True)
    entity_schema = models.JSONField(default=dict, blank=True)
    snapshot = models.JSONField(default=dict, blank=True)
    quality_report = models.JSONField(default=dict, blank=True)
    lineage = models.JSONField(default=dict, blank=True)
    checksum = models.CharField(max_length=64)
    loaded_at = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_data_model_version"
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(fields=["data_model", "version"], name="rehearsal_dm_version_model_ver")
        ]
        indexes = [models.Index(fields=["workspace_id", "loaded_at"], name="rehearsal_dmv_ws_loaded")]


class RehearsalDataModelLoad(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    data_model = models.ForeignKey(RehearsalDataModel, on_delete=models.CASCADE, related_name="loads")
    version = models.ForeignKey(
        RehearsalDataModelVersion,
        on_delete=models.CASCADE,
        related_name="loads",
        null=True,
        blank=True,
    )
    request_id = models.CharField(max_length=160)
    status = models.CharField(
        max_length=16,
        choices=DataModelLoadStatus.choices,
        default=DataModelLoadStatus.LOADED,
        db_index=True,
    )
    source_counts = models.JSONField(default=dict, blank=True)
    note = models.CharField(max_length=500, default="", blank=True)
    message = models.CharField(max_length=500, default="", blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_data_model_load"
        ordering = ["-create_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "request_id"],
                name="rehearsal_data_model_load_ws_req",
            )
        ]
        indexes = [models.Index(fields=["workspace_id", "status"], name="rehearsal_dml_ws_status")]


class RehearsalTracebackSnapshot(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    instance = models.ForeignKey(RehearsalInstance, on_delete=models.CASCADE, related_name="traceback_snapshots")
    scenario = models.ForeignKey(RehearsalScenario, on_delete=models.PROTECT, related_name="traceback_snapshots")
    scene_run = models.ForeignKey(
        "RehearsalSceneRun",
        on_delete=models.SET_NULL,
        related_name="traceback_snapshots",
        null=True,
        blank=True,
    )
    data_model = models.ForeignKey(
        RehearsalDataModel,
        on_delete=models.SET_NULL,
        related_name="traceback_snapshots",
        null=True,
        blank=True,
    )
    request_id = models.CharField(max_length=160)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=500, default="", blank=True)
    scope = models.CharField(
        max_length=24,
        choices=TracebackScope.choices,
        default=TracebackScope.FULL_INSTANCE,
        db_index=True,
    )
    status = models.CharField(
        max_length=16,
        choices=TracebackStatus.choices,
        default=TracebackStatus.READY,
        db_index=True,
    )
    kind_scope = models.JSONField(default=list, blank=True)
    window_start = models.DateTimeField(null=True, blank=True)
    window_end = models.DateTimeField(null=True, blank=True)
    total_events = models.PositiveIntegerField(default=0)
    kind_counts = models.JSONField(default=dict, blank=True)
    pivot_counts = models.JSONField(default=dict, blank=True)
    summary = models.JSONField(default=dict, blank=True)
    snapshot = models.JSONField(default=dict, blank=True)
    checksum = models.CharField(max_length=64)
    generated_at = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_traceback_snapshot"
        ordering = ["-generated_at", "-update_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "request_id"],
                name="rehearsal_traceback_ws_request",
            ),
            models.UniqueConstraint(fields=["workspace_id", "code"], name="rehearsal_traceback_ws_code"),
        ]
        indexes = [
            models.Index(fields=["workspace_id", "instance", "generated_at"], name="rehearsal_tb_ws_inst_time"),
            models.Index(fields=["workspace_id", "status"], name="rehearsal_tb_ws_status"),
            models.Index(fields=["workspace_id", "scope"], name="rehearsal_tb_ws_scope"),
        ]


class RehearsalSceneScript(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    scenario = models.ForeignKey(
        RehearsalScenario,
        on_delete=models.PROTECT,
        related_name="scene_scripts",
    )
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=500, default="", blank=True)
    version = models.PositiveIntegerField(default=1)
    enabled = models.BooleanField(default=True, db_index=True)
    steps = models.JSONField(default=list)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_scene_script"
        ordering = ["code", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "code", "version"],
                name="rehearsal_scene_script_ws_code_ver",
            )
        ]


class RehearsalSceneLibrary(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    scenario = models.ForeignKey(RehearsalScenario, on_delete=models.PROTECT, related_name="scene_libraries")
    script = models.ForeignKey(RehearsalSceneScript, on_delete=models.PROTECT, related_name="scene_libraries")
    default_instance = models.ForeignKey(
        RehearsalInstance,
        on_delete=models.SET_NULL,
        related_name="scene_libraries",
        null=True,
        blank=True,
    )
    process_template = models.ForeignKey(
        RehearsalProcessTemplate,
        on_delete=models.SET_NULL,
        related_name="scene_libraries",
        null=True,
        blank=True,
    )
    data_model = models.ForeignKey(
        RehearsalDataModel,
        on_delete=models.SET_NULL,
        related_name="scene_libraries",
        null=True,
        blank=True,
    )
    source_library = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="cloned_versions",
        null=True,
        blank=True,
    )
    request_id = models.CharField(max_length=160)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=500, default="", blank=True)
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=16,
        choices=SceneLibraryStatus.choices,
        default=SceneLibraryStatus.READY,
        db_index=True,
    )
    visibility = models.CharField(
        max_length=16,
        choices=SceneLibraryVisibility.choices,
        default=SceneLibraryVisibility.WORKSPACE,
        db_index=True,
    )
    permission_roles = models.JSONField(default=list, blank=True)
    linked_config = models.JSONField(default=dict, blank=True)
    run_count = models.PositiveIntegerField(default=0)
    last_run_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_scene_library"
        ordering = ["code", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "request_id"],
                name="rehearsal_scene_lib_ws_request",
            ),
            models.UniqueConstraint(
                fields=["workspace_id", "code", "version"],
                name="rehearsal_scene_lib_ws_code_ver",
            ),
        ]
        indexes = [
            models.Index(fields=["workspace_id", "status"], name="rehearsal_sl_ws_status"),
            models.Index(fields=["workspace_id", "visibility"], name="rehearsal_sl_ws_visibility"),
        ]


class RehearsalSceneLibraryEvent(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    library = models.ForeignKey(RehearsalSceneLibrary, on_delete=models.CASCADE, related_name="events")
    sequence_no = models.PositiveIntegerField()
    action = models.CharField(max_length=24, choices=SceneLibraryAction.choices)
    previous_status = models.CharField(max_length=16, choices=SceneLibraryStatus.choices)
    current_status = models.CharField(max_length=16, choices=SceneLibraryStatus.choices)
    detail = models.JSONField(default=dict, blank=True)
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_scene_library_event"
        ordering = ["sequence_no"]
        constraints = [
            models.UniqueConstraint(fields=["library", "sequence_no"], name="rehearsal_sl_event_lib_seq")
        ]


class RehearsalSceneRun(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    instance = models.ForeignKey(RehearsalInstance, on_delete=models.CASCADE, related_name="scene_runs")
    script = models.ForeignKey(RehearsalSceneScript, on_delete=models.PROTECT, related_name="runs")
    library = models.ForeignKey(
        RehearsalSceneLibrary,
        on_delete=models.SET_NULL,
        related_name="scene_runs",
        null=True,
        blank=True,
    )
    request_id = models.CharField(max_length=160)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    status = models.CharField(
        max_length=16,
        choices=SceneRunStatus.choices,
        default=SceneRunStatus.PENDING,
        db_index=True,
    )
    current_step_index = models.PositiveIntegerField(default=0)
    current_step_code = models.CharField(max_length=64, default="", blank=True)
    total_steps = models.PositiveIntegerField(default=0)
    completed_steps = models.PositiveIntegerField(default=0)
    progress_percent = models.PositiveSmallIntegerField(default=0)
    script_snapshot = models.JSONField(default=dict)
    injected_snapshot = models.JSONField(default=dict)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    summary = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_scene_run"
        ordering = ["-update_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "request_id"],
                name="rehearsal_scene_run_ws_request",
            ),
            models.UniqueConstraint(fields=["workspace_id", "code"], name="rehearsal_scene_run_ws_code"),
        ]
        indexes = [models.Index(fields=["workspace_id", "status"], name="rehearsal_scene_ws_status")]


class RehearsalSceneStep(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    run = models.ForeignKey(RehearsalSceneRun, on_delete=models.CASCADE, related_name="steps")
    sequence_no = models.PositiveIntegerField()
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=500, default="", blank=True)
    expected_result = models.CharField(max_length=500, default="", blank=True)
    status = models.CharField(
        max_length=16,
        choices=SceneStepStatus.choices,
        default=SceneStepStatus.PENDING,
        db_index=True,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    note = models.CharField(max_length=500, default="", blank=True)
    output_snapshot = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "rehearsal_scene_step"
        ordering = ["sequence_no"]
        constraints = [
            models.UniqueConstraint(fields=["run", "sequence_no"], name="rehearsal_scene_step_run_seq"),
            models.UniqueConstraint(fields=["run", "code"], name="rehearsal_scene_step_run_code"),
        ]


class RehearsalSceneEvent(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    run = models.ForeignKey(RehearsalSceneRun, on_delete=models.CASCADE, related_name="events")
    step = models.ForeignKey(
        RehearsalSceneStep,
        on_delete=models.SET_NULL,
        related_name="events",
        null=True,
        blank=True,
    )
    sequence_no = models.PositiveIntegerField()
    action = models.CharField(max_length=24)
    previous_status = models.CharField(max_length=16, choices=SceneRunStatus.choices)
    current_status = models.CharField(max_length=16, choices=SceneRunStatus.choices)
    detail = models.JSONField(default=dict, blank=True)
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_scene_event"
        ordering = ["sequence_no"]
        constraints = [
            models.UniqueConstraint(fields=["run", "sequence_no"], name="rehearsal_scene_event_run_seq")
        ]


class RehearsalWorkOrder(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    scene_run = models.ForeignKey(RehearsalSceneRun, on_delete=models.CASCADE, related_name="work_orders")
    request_id = models.CharField(max_length=160)
    code = models.CharField(max_length=64)
    title = models.CharField(max_length=160)
    description = models.CharField(max_length=1000, default="", blank=True)
    priority = models.CharField(
        max_length=16,
        choices=WorkOrderPriority.choices,
        default=WorkOrderPriority.MEDIUM,
        db_index=True,
    )
    status = models.CharField(
        max_length=16,
        choices=WorkOrderStatus.choices,
        default=WorkOrderStatus.OPEN,
        db_index=True,
    )
    assignee = models.CharField(max_length=128, default="", blank=True)
    resolution = models.CharField(max_length=1000, default="", blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_work_order"
        ordering = ["-update_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "request_id"],
                name="rehearsal_work_order_ws_request",
            ),
            models.UniqueConstraint(fields=["workspace_id", "code"], name="rehearsal_work_order_ws_code"),
        ]
        indexes = [models.Index(fields=["workspace_id", "status"], name="rehearsal_order_ws_status")]


class RehearsalWorkOrderEvent(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    work_order = models.ForeignKey(RehearsalWorkOrder, on_delete=models.CASCADE, related_name="events")
    sequence_no = models.PositiveIntegerField()
    action = models.CharField(max_length=24)
    previous_status = models.CharField(max_length=16, choices=WorkOrderStatus.choices)
    current_status = models.CharField(max_length=16, choices=WorkOrderStatus.choices)
    detail = models.JSONField(default=dict, blank=True)
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_work_order_event"
        ordering = ["sequence_no"]
        constraints = [
            models.UniqueConstraint(
                fields=["work_order", "sequence_no"],
                name="rehearsal_work_order_event_order_seq",
            )
        ]


class RehearsalAlertTemplate(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    scenario = models.ForeignKey(
        RehearsalScenario,
        on_delete=models.PROTECT,
        related_name="alert_templates",
    )
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=500, default="", blank=True)
    version = models.PositiveIntegerField(default=1)
    enabled = models.BooleanField(default=True, db_index=True)
    default_severity = models.CharField(
        max_length=16,
        choices=AlertSeverity.choices,
        default=AlertSeverity.HIGH,
    )
    rules = models.JSONField(default=list)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_alert_template"
        ordering = ["code", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "code", "version"],
                name="rehearsal_alert_tpl_ws_code_ver",
            )
        ]


class RehearsalAlert(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    instance = models.ForeignKey(RehearsalInstance, on_delete=models.CASCADE, related_name="alerts")
    template = models.ForeignKey(RehearsalAlertTemplate, on_delete=models.PROTECT, related_name="alerts")
    scene_run = models.ForeignKey(
        RehearsalSceneRun,
        on_delete=models.SET_NULL,
        related_name="alerts",
        null=True,
        blank=True,
    )
    data_batch = models.ForeignKey(
        RehearsalDataBatch,
        on_delete=models.SET_NULL,
        related_name="alerts",
        null=True,
        blank=True,
    )
    request_id = models.CharField(max_length=160)
    code = models.CharField(max_length=64)
    title = models.CharField(max_length=160)
    description = models.CharField(max_length=1000, default="", blank=True)
    severity = models.CharField(
        max_length=16,
        choices=AlertSeverity.choices,
        default=AlertSeverity.HIGH,
        db_index=True,
    )
    status = models.CharField(
        max_length=16,
        choices=AlertStatus.choices,
        default=AlertStatus.PENDING,
        db_index=True,
    )
    source_system = models.CharField(max_length=64, default="预演模拟器")
    resource_type = models.CharField(max_length=64, default="网络设备")
    resource_id = models.CharField(max_length=128, default="", blank=True)
    resource_name = models.CharField(max_length=160, default="", blank=True)
    metric_code = models.CharField(max_length=64, default="", blank=True)
    metric_name = models.CharField(max_length=128, default="", blank=True)
    metric_value = models.FloatField(null=True, blank=True)
    threshold = models.FloatField(null=True, blank=True)
    occurred_at = models.DateTimeField(db_index=True)
    reported_at = models.DateTimeField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    recovered_at = models.DateTimeField(null=True, blank=True)
    template_snapshot = models.JSONField(default=dict)
    context = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_alert"
        ordering = ["-occurred_at", "-update_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "request_id"],
                name="rehearsal_alert_ws_request",
            ),
            models.UniqueConstraint(fields=["workspace_id", "code"], name="rehearsal_alert_ws_code"),
        ]
        indexes = [
            models.Index(fields=["workspace_id", "status", "severity"], name="rehearsal_alert_ws_stat_sev"),
            models.Index(fields=["workspace_id", "instance", "occurred_at"], name="rehearsal_alert_ws_inst_time"),
        ]


class RehearsalAlertEvent(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    alert = models.ForeignKey(RehearsalAlert, on_delete=models.CASCADE, related_name="events")
    sequence_no = models.PositiveIntegerField()
    action = models.CharField(max_length=24)
    previous_status = models.CharField(max_length=16, choices=AlertStatus.choices)
    current_status = models.CharField(max_length=16, choices=AlertStatus.choices)
    occurred_at = models.DateTimeField(db_index=True)
    detail = models.JSONField(default=dict, blank=True)
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_alert_event"
        ordering = ["occurred_at", "sequence_no"]
        constraints = [
            models.UniqueConstraint(fields=["alert", "sequence_no"], name="rehearsal_alert_event_alert_seq")
        ]
        indexes = [
            models.Index(fields=["workspace_id", "occurred_at"], name="rehearsal_alert_event_ws_time")
        ]


class RehearsalCapabilityMock(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    scenario = models.ForeignKey(
        RehearsalScenario,
        on_delete=models.PROTECT,
        related_name="capability_mocks",
    )
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=500, default="", blank=True)
    kind = models.CharField(max_length=16, choices=CapabilityMockKind.choices, db_index=True)
    version = models.PositiveIntegerField(default=1)
    enabled = models.BooleanField(default=True, db_index=True)
    method = models.CharField(max_length=12, default="POST")
    endpoint = models.CharField(max_length=255)
    request_schema = models.JSONField(default=dict, blank=True)
    response_template = models.JSONField(default=dict, blank=True)
    failure_template = models.JSONField(default=dict, blank=True)
    default_status = models.CharField(
        max_length=16,
        choices=CapabilityCallStatus.choices,
        default=CapabilityCallStatus.SUCCEEDED,
    )
    default_latency_ms = models.PositiveIntegerField(default=120)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_capability_mock"
        ordering = ["kind", "code", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "code", "version"],
                name="rehearsal_cap_mock_ws_code_ver",
            )
        ]


class RehearsalCapabilityCall(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    instance = models.ForeignKey(
        RehearsalInstance,
        on_delete=models.CASCADE,
        related_name="capability_calls",
    )
    capability = models.ForeignKey(
        RehearsalCapabilityMock,
        on_delete=models.PROTECT,
        related_name="calls",
    )
    replay_of = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="replays",
        null=True,
        blank=True,
    )
    request_id = models.CharField(max_length=160)
    call_no = models.PositiveIntegerField()
    status = models.CharField(max_length=16, choices=CapabilityCallStatus.choices, db_index=True)
    source = models.CharField(max_length=16, default="SANDBOX")
    warroom_group = models.CharField(max_length=64, default="默认战情室", db_index=True)
    request_payload = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    capability_snapshot = models.JSONField(default=dict)
    http_status = models.PositiveSmallIntegerField(default=200)
    latency_ms = models.PositiveIntegerField(default=0)
    error_message = models.CharField(max_length=1000, default="", blank=True)
    started_at = models.DateTimeField(db_index=True)
    finished_at = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_capability_call"
        ordering = ["-started_at", "-create_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "request_id"],
                name="rehearsal_cap_call_ws_request",
            ),
            models.UniqueConstraint(
                fields=["instance", "capability", "call_no"],
                name="rehearsal_cap_call_inst_no",
            ),
        ]
        indexes = [
            models.Index(
                fields=["workspace_id", "status", "started_at"],
                name="rehearsal_cap_call_ws_stat",
            ),
            models.Index(
                fields=["workspace_id", "warroom_group", "started_at"],
                name="rehearsal_cap_call_ws_room",
            ),
        ]


class RehearsalFaultConfiguration(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    scenario = models.ForeignKey(
        RehearsalScenario,
        on_delete=models.PROTECT,
        related_name="fault_configurations",
    )
    source_configuration = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="derived_versions",
        null=True,
        blank=True,
    )
    request_id = models.CharField(max_length=160)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=500, default="", blank=True)
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=16,
        choices=FaultConfigurationStatus.choices,
        default=FaultConfigurationStatus.DRAFT,
        db_index=True,
    )
    alert_rules = models.JSONField(default=list)
    timeout_policy = models.JSONField(default=dict)
    active_window = models.JSONField(default=dict)
    topology_snapshot = models.JSONField(default=dict)
    emergency_plan = models.JSONField(default=dict)
    validation_report = models.JSONField(default=dict, blank=True)
    validated_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_fault_configuration"
        ordering = ["code", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "request_id"],
                name="rehearsal_fault_cfg_ws_request",
            ),
            models.UniqueConstraint(
                fields=["workspace_id", "code", "version"],
                name="rehearsal_fault_cfg_ws_code_ver",
            ),
        ]
        indexes = [
            models.Index(
                fields=["workspace_id", "status", "scenario"],
                name="rehearsal_fault_cfg_ws_stat",
            )
        ]


class RehearsalFaultConfigurationEvent(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    configuration = models.ForeignKey(
        RehearsalFaultConfiguration,
        on_delete=models.CASCADE,
        related_name="events",
    )
    instance = models.ForeignKey(
        RehearsalInstance,
        on_delete=models.SET_NULL,
        related_name="fault_configuration_events",
        null=True,
        blank=True,
    )
    sequence_no = models.PositiveIntegerField()
    action = models.CharField(max_length=16, choices=FaultConfigurationAction.choices)
    previous_status = models.CharField(max_length=16, choices=FaultConfigurationStatus.choices)
    current_status = models.CharField(max_length=16, choices=FaultConfigurationStatus.choices)
    detail = models.JSONField(default=dict, blank=True)
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_fault_configuration_event"
        ordering = ["sequence_no"]
        constraints = [
            models.UniqueConstraint(
                fields=["configuration", "sequence_no"],
                name="rehearsal_fault_cfg_event_seq",
            )
        ]


class RehearsalSceneReplay(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    instance = models.ForeignKey(
        RehearsalInstance,
        on_delete=models.CASCADE,
        related_name="scene_replays",
    )
    scene_run = models.ForeignKey(
        RehearsalSceneRun,
        on_delete=models.SET_NULL,
        related_name="scene_replays",
        null=True,
        blank=True,
    )
    fault_configuration = models.ForeignKey(
        RehearsalFaultConfiguration,
        on_delete=models.SET_NULL,
        related_name="scene_replays",
        null=True,
        blank=True,
    )
    request_id = models.CharField(max_length=160)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=500, default="", blank=True)
    status = models.CharField(
        max_length=16,
        choices=SceneReplayStatus.choices,
        default=SceneReplayStatus.READY,
        db_index=True,
    )
    window_start = models.DateTimeField(null=True, blank=True)
    window_end = models.DateTimeField(null=True, blank=True)
    traffic_frames = models.JSONField(default=list)
    topology_before = models.JSONField(default=dict)
    topology_after = models.JSONField(default=dict)
    node_traces = models.JSONField(default=list)
    mirror_comparison = models.JSONField(default=dict)
    summary = models.JSONField(default=dict, blank=True)
    checksum = models.CharField(max_length=64)
    generated_at = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_scene_replay"
        ordering = ["-generated_at", "-update_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "request_id"],
                name="rehearsal_scene_replay_ws_req",
            ),
            models.UniqueConstraint(
                fields=["workspace_id", "code"],
                name="rehearsal_scene_replay_ws_code",
            ),
        ]
        indexes = [
            models.Index(fields=["workspace_id", "instance", "generated_at"], name="rehearsal_sr_ws_inst_time"),
            models.Index(fields=["workspace_id", "status"], name="rehearsal_sr_ws_status"),
        ]


class RehearsalFaultReportTemplate(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    scenario = models.ForeignKey(
        RehearsalScenario,
        on_delete=models.PROTECT,
        related_name="fault_report_templates",
        null=True,
        blank=True,
    )
    request_id = models.CharField(max_length=160)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=500, default="", blank=True)
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=16,
        choices=FaultReportTemplateStatus.choices,
        default=FaultReportTemplateStatus.READY,
        db_index=True,
    )
    default_level = models.CharField(
        max_length=16,
        choices=FaultReportLevel.choices,
        default=FaultReportLevel.LEVEL_3,
    )
    stage_definitions = models.JSONField(default=list)
    required_fields = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_fault_report_template"
        ordering = ["code", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "request_id"],
                name="rehearsal_fault_rpt_tpl_ws_req",
            ),
            models.UniqueConstraint(
                fields=["workspace_id", "code", "version"],
                name="rehearsal_fault_rpt_tpl_ws_ver",
            ),
        ]
        indexes = [
            models.Index(
                fields=["workspace_id", "status"],
                name="rehearsal_fr_tpl_ws_stat",
            )
        ]


class RehearsalFaultReport(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    instance = models.ForeignKey(
        RehearsalInstance,
        on_delete=models.CASCADE,
        related_name="fault_reports",
    )
    template = models.ForeignKey(
        RehearsalFaultReportTemplate,
        on_delete=models.SET_NULL,
        related_name="reports",
        null=True,
        blank=True,
    )
    scene_run = models.ForeignKey(
        RehearsalSceneRun,
        on_delete=models.SET_NULL,
        related_name="fault_reports",
        null=True,
        blank=True,
    )
    request_id = models.CharField(max_length=160)
    code = models.CharField(max_length=64)
    title = models.CharField(max_length=160)
    description = models.CharField(max_length=1000, default="", blank=True)
    impact_scope = models.CharField(max_length=500, default="", blank=True)
    level = models.CharField(max_length=16, choices=FaultReportLevel.choices, db_index=True)
    status = models.CharField(
        max_length=16,
        choices=FaultReportStatus.choices,
        default=FaultReportStatus.DRAFT,
        db_index=True,
    )
    current_stage_code = models.CharField(max_length=64)
    current_stage_name = models.CharField(max_length=128)
    occurred_at = models.DateTimeField(db_index=True)
    reported_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    recovered_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    stage_started_at = models.DateTimeField()
    stage_deadline_at = models.DateTimeField(db_index=True)
    attachments = models.JSONField(default=list, blank=True)
    template_snapshot = models.JSONField(default=dict)
    summary = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_fault_report"
        ordering = ["-occurred_at", "-create_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "request_id"],
                name="rehearsal_fault_report_ws_req",
            ),
            models.UniqueConstraint(
                fields=["workspace_id", "code"],
                name="rehearsal_fault_report_ws_code",
            ),
        ]
        indexes = [
            models.Index(
                fields=["workspace_id", "status", "level"],
                name="rehearsal_fr_ws_stat_level",
            ),
            models.Index(
                fields=["workspace_id", "stage_deadline_at"],
                name="rehearsal_fr_ws_deadline",
            ),
        ]


class RehearsalFaultReportEvent(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    report = models.ForeignKey(
        RehearsalFaultReport,
        on_delete=models.CASCADE,
        related_name="events",
    )
    sequence_no = models.PositiveIntegerField()
    action = models.CharField(max_length=24, choices=FaultReportAction.choices)
    previous_status = models.CharField(max_length=16, choices=FaultReportStatus.choices)
    current_status = models.CharField(max_length=16, choices=FaultReportStatus.choices)
    previous_stage_code = models.CharField(max_length=64, default="", blank=True)
    current_stage_code = models.CharField(max_length=64, default="", blank=True)
    detail = models.JSONField(default=dict, blank=True)
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_fault_report_event"
        ordering = ["sequence_no"]
        constraints = [
            models.UniqueConstraint(
                fields=["report", "sequence_no"],
                name="rehearsal_fault_report_event_seq",
            )
        ]


class RehearsalAuxiliarySimulation(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    instance = models.ForeignKey(
        RehearsalInstance,
        on_delete=models.CASCADE,
        related_name="auxiliary_simulations",
    )
    request_id = models.CharField(max_length=160)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=160)
    seed = models.PositiveBigIntegerField()
    duration_minutes = models.PositiveIntegerField(default=60)
    status = models.CharField(
        max_length=16,
        choices=AuxiliarySimulationStatus.choices,
        default=AuxiliarySimulationStatus.COMPLETED,
        db_index=True,
    )
    factor_snapshot = models.JSONField(default=list)
    result_snapshot = models.JSONField(default=dict)
    checksum = models.CharField(max_length=64)
    started_at = models.DateTimeField(db_index=True)
    completed_at = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "rehearsal_auxiliary_simulation"
        ordering = ["-started_at", "-create_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "request_id"],
                name="rehearsal_aux_sim_ws_req",
            ),
            models.UniqueConstraint(
                fields=["workspace_id", "code"],
                name="rehearsal_aux_sim_ws_code",
            ),
        ]
        indexes = [
            models.Index(fields=["workspace_id", "status", "started_at"], name="rehearsal_aux_ws_stat"),
            models.Index(fields=["workspace_id", "instance", "started_at"], name="rehearsal_aux_ws_inst"),
        ]
