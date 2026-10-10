import uuid_utils.compat as uuid
from django.db import models

from common.mixins.app_model_mixin import AppModelMixin
from users.models import User


class MonitoringScope(models.TextChoices):
    MODEL = "MODEL", "模型性能"
    DATA = "DATA", "数据质量"
    KNOWLEDGE = "KNOWLEDGE", "知识时效"
    RESOURCE = "RESOURCE", "系统资源"


class MonitoringRunStatus(models.TextChoices):
    RUNNING = "RUNNING", "采集中"
    SUCCESS = "SUCCESS", "采集成功"
    PARTIAL = "PARTIAL", "部分成功"
    FAILED = "FAILED", "采集失败"


class MonitoringMetricStatus(models.TextChoices):
    HEALTHY = "HEALTHY", "正常"
    WARNING = "WARNING", "关注"
    CRITICAL = "CRITICAL", "紧急"
    UNKNOWN = "UNKNOWN", "未知"


class MonitoringOperator(models.TextChoices):
    GT = "GT", "大于"
    GTE = "GTE", "大于等于"
    LT = "LT", "小于"
    LTE = "LTE", "小于等于"


class MonitoringAutoAction(models.TextChoices):
    NONE = "NONE", "仅告警"
    RETRY_FAILED_RUN = "RETRY_FAILED_RUN", "重试最近失败任务"
    CREATE_ROLLBACK_TASK = "CREATE_ROLLBACK_TASK", "生成回滚任务"


class MonitoringAlertStatus(models.TextChoices):
    OPEN = "OPEN", "待处理"
    ACKNOWLEDGED = "ACKNOWLEDGED", "已确认"
    RESOLVED = "RESOLVED", "已恢复"


class PlatformMonitoringRun(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    status = models.CharField(max_length=16, choices=MonitoringRunStatus.choices, default=MonitoringRunStatus.RUNNING)
    trigger = models.CharField(max_length=16, default="MANUAL")
    summary = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(default="", blank=True)
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "platform_monitoring_run"
        ordering = ["-create_time"]


class PlatformMetricSnapshot(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    run = models.ForeignKey(PlatformMonitoringRun, on_delete=models.CASCADE, related_name="metrics")
    scope = models.CharField(max_length=16, choices=MonitoringScope.choices, db_index=True)
    metric_key = models.CharField(max_length=64, db_index=True)
    metric_name = models.CharField(max_length=128)
    value = models.FloatField(default=0)
    unit = models.CharField(max_length=32, default="", blank=True)
    status = models.CharField(
        max_length=16,
        choices=MonitoringMetricStatus.choices,
        default=MonitoringMetricStatus.HEALTHY,
        db_index=True,
    )
    details = models.JSONField(default=dict, blank=True)
    collected_at = models.DateTimeField(db_index=True)

    class Meta:
        db_table = "platform_metric_snapshot"
        ordering = ["scope", "metric_key"]
        indexes = [models.Index(fields=["workspace_id", "scope", "metric_key"], name="plat_metric_ws_scope_key")]


class PlatformMonitoringRule(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    name = models.CharField(max_length=128)
    scope = models.CharField(max_length=16, choices=MonitoringScope.choices, db_index=True)
    metric_key = models.CharField(max_length=64, db_index=True)
    operator = models.CharField(max_length=8, choices=MonitoringOperator.choices, default=MonitoringOperator.GTE)
    warning_threshold = models.FloatField(null=True, blank=True)
    critical_threshold = models.FloatField(null=True, blank=True)
    enabled = models.BooleanField(default=True, db_index=True)
    auto_action = models.CharField(
        max_length=32,
        choices=MonitoringAutoAction.choices,
        default=MonitoringAutoAction.NONE,
    )
    cooldown_minutes = models.PositiveIntegerField(default=30)
    description = models.CharField(max_length=500, default="", blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "platform_monitoring_rule"
        ordering = ["scope", "metric_key", "name"]
        constraints = [
            models.UniqueConstraint(fields=["workspace_id", "metric_key", "name"], name="plat_rule_ws_key_name")
        ]


class PlatformMonitoringAlert(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    rule = models.ForeignKey(PlatformMonitoringRule, on_delete=models.SET_NULL, null=True, related_name="alerts")
    metric = models.ForeignKey(PlatformMetricSnapshot, on_delete=models.SET_NULL, null=True, related_name="alerts")
    dedupe_key = models.CharField(max_length=160)
    scope = models.CharField(max_length=16, choices=MonitoringScope.choices, db_index=True)
    metric_key = models.CharField(max_length=64, db_index=True)
    title = models.CharField(max_length=160)
    message = models.TextField(default="", blank=True)
    severity = models.CharField(max_length=16, choices=MonitoringMetricStatus.choices, db_index=True)
    status = models.CharField(
        max_length=16,
        choices=MonitoringAlertStatus.choices,
        default=MonitoringAlertStatus.OPEN,
        db_index=True,
    )
    observed_value = models.FloatField(default=0)
    threshold_value = models.FloatField(default=0)
    auto_action = models.CharField(max_length=32, choices=MonitoringAutoAction.choices, default=MonitoringAutoAction.NONE)
    response_status = models.CharField(max_length=24, default="NOT_REQUIRED")
    response_detail = models.JSONField(default=dict, blank=True)
    first_triggered_at = models.DateTimeField()
    last_triggered_at = models.DateTimeField()
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "platform_monitoring_alert"
        ordering = ["-last_triggered_at"]
        constraints = [
            models.UniqueConstraint(fields=["workspace_id", "dedupe_key"], name="plat_alert_ws_dedupe")
        ]
        indexes = [models.Index(fields=["workspace_id", "status", "severity"], name="plat_alert_ws_status_sev")]


class MetricTheme(models.TextChoices):
    TROUBLESHOOTING = "TROUBLESHOOTING", "监控排障"
    SECURITY = "SECURITY", "安全隐患"
    COST = "COST", "成本效能"
    DELIVERY = "DELIVERY", "客户交付"
    NETWORK = "NETWORK", "网络运行"
    CAPABILITY = "CAPABILITY", "能力指标"
    MAINTENANCE = "MAINTENANCE", "维护优化"
    DATA_RISK = "DATA_RISK", "涉网涉数风险"


class MetricSourceType(models.TextChoices):
    MANUAL = "MANUAL", "手工导入"
    API = "API", "接口采集"
    DATABASE = "DATABASE", "数据库采集"


class MetricBatchStatus(models.TextChoices):
    IMPORTED = "IMPORTED", "导入成功"
    PARTIAL = "PARTIAL", "部分成功"
    FAILED = "FAILED", "导入失败"


class MetricRuleMode(models.TextChoices):
    STATIC = "STATIC", "固定阈值"
    DYNAMIC = "DYNAMIC", "动态基线"


class MetricAlertDirection(models.TextChoices):
    ABOVE = "ABOVE", "高于阈值"
    BELOW = "BELOW", "低于阈值"


class MetricComplianceStatus(models.TextChoices):
    PASSED = "PASSED", "校验通过"
    FAILED = "FAILED", "校验失败"


class MetricIncidentStatus(models.TextChoices):
    OPEN = "OPEN", "待处理"
    ACKNOWLEDGED = "ACKNOWLEDGED", "已确认"
    RESOLVED = "RESOLVED", "已恢复"
    CLOSED = "CLOSED", "已关闭"


class MetricWorkOrderStatus(models.TextChoices):
    NEW = "NEW", "待派单"
    ASSIGNED = "ASSIGNED", "已派单"
    CLAIMED = "CLAIMED", "已认领"
    PROCESSING = "PROCESSING", "处理中"
    RESOLVED = "RESOLVED", "已解决"
    CLOSED = "CLOSED", "已关闭"


class MetricDispatchEventAction(models.TextChoices):
    CREATED = "CREATED", "创建派单"
    ASSIGNED = "ASSIGNED", "人工指派"
    TRANSFERRED = "TRANSFERRED", "转派"
    CLAIMED = "CLAIMED", "认领"
    STARTED = "STARTED", "开始处理"
    COMMENTED = "COMMENTED", "添加备注"
    RESOLVED = "RESOLVED", "标记解决"
    CLOSED = "CLOSED", "关闭派单"


class MetricDefinition(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    metric_key = models.CharField(max_length=96)
    name = models.CharField(max_length=160)
    theme = models.CharField(max_length=24, choices=MetricTheme.choices, db_index=True)
    unit = models.CharField(max_length=32, default="", blank=True)
    description = models.CharField(max_length=500, default="", blank=True)
    dimensions_schema = models.JSONField(default=list, blank=True)
    enabled = models.BooleanField(default=True, db_index=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "metric_definition"
        ordering = ["theme", "metric_key"]
        constraints = [
            models.UniqueConstraint(fields=["workspace_id", "metric_key"], name="metric_def_ws_key")
        ]


class MetricDataSource(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    source_key = models.CharField(max_length=96)
    name = models.CharField(max_length=160)
    source_type = models.CharField(max_length=16, choices=MetricSourceType.choices, default=MetricSourceType.MANUAL)
    config_snapshot = models.JSONField(default=dict, blank=True)
    enabled = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "metric_data_source"
        ordering = ["source_key"]
        constraints = [
            models.UniqueConstraint(fields=["workspace_id", "source_key"], name="metric_src_ws_key")
        ]


class MetricCollectionBatch(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    batch_no = models.CharField(max_length=96)
    source = models.ForeignKey(MetricDataSource, on_delete=models.SET_NULL, null=True, blank=True, related_name="batches")
    status = models.CharField(max_length=16, choices=MetricBatchStatus.choices, default=MetricBatchStatus.IMPORTED)
    total_rows = models.PositiveIntegerField(default=0)
    accepted_rows = models.PositiveIntegerField(default=0)
    rejected_rows = models.PositiveIntegerField(default=0)
    error_rows = models.JSONField(default=list, blank=True)
    input_snapshot = models.JSONField(default=dict, blank=True)
    collected_at = models.DateTimeField(db_index=True)
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "metric_collection_batch"
        ordering = ["-collected_at"]
        constraints = [
            models.UniqueConstraint(fields=["workspace_id", "batch_no"], name="metric_batch_ws_no")
        ]


class MetricObservation(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    definition = models.ForeignKey(MetricDefinition, on_delete=models.PROTECT, related_name="observations")
    batch = models.ForeignKey(MetricCollectionBatch, on_delete=models.PROTECT, related_name="observations")
    value = models.FloatField()
    dimensions = models.JSONField(default=dict, blank=True)
    dimension_key = models.CharField(max_length=256, default="", blank=True, db_index=True)
    observed_at = models.DateTimeField(db_index=True)
    raw_snapshot = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "metric_observation"
        ordering = ["-observed_at"]
        indexes = [
            models.Index(fields=["workspace_id", "definition", "dimension_key", "observed_at"], name="metric_obs_lookup")
        ]


class MetricDynamicBaseline(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    definition = models.ForeignKey(MetricDefinition, on_delete=models.PROTECT, related_name="baselines")
    dimension_key = models.CharField(max_length=256, default="", blank=True)
    version = models.PositiveIntegerField(default=1)
    algorithm = models.CharField(max_length=32, default="MOVING_AVERAGE")
    window_size = models.PositiveIntegerField(default=5)
    sample_count = models.PositiveIntegerField(default=0)
    mean_value = models.FloatField(default=0)
    standard_deviation = models.FloatField(default=0)
    snapshot = models.JSONField(default=dict, blank=True)
    calculated_at = models.DateTimeField(db_index=True)

    class Meta:
        db_table = "metric_dynamic_baseline"
        ordering = ["-calculated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "definition", "dimension_key", "version"],
                name="metric_base_ws_def_dim_ver",
            )
        ]


class MetricAlertRule(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    definition = models.ForeignKey(MetricDefinition, on_delete=models.PROTECT, related_name="alert_rules")
    name = models.CharField(max_length=160)
    mode = models.CharField(max_length=16, choices=MetricRuleMode.choices, default=MetricRuleMode.STATIC)
    direction = models.CharField(max_length=16, choices=MetricAlertDirection.choices, default=MetricAlertDirection.ABOVE)
    warning_threshold = models.FloatField(null=True, blank=True)
    critical_threshold = models.FloatField(null=True, blank=True)
    warning_deviation = models.FloatField(default=1.5)
    critical_deviation = models.FloatField(default=2.5)
    baseline_window = models.PositiveIntegerField(default=5)
    dimension_filter = models.JSONField(default=dict, blank=True)
    active_windows = models.JSONField(default=list, blank=True)
    config_version = models.PositiveIntegerField(default=1)
    config_snapshot = models.JSONField(default=dict, blank=True)
    compliance_status = models.CharField(
        max_length=16,
        choices=MetricComplianceStatus.choices,
        default=MetricComplianceStatus.PASSED,
    )
    compliance_issues = models.JSONField(default=list, blank=True)
    enabled = models.BooleanField(default=True, db_index=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "metric_alert_rule"
        ordering = ["definition__theme", "definition__metric_key", "name"]
        constraints = [
            models.UniqueConstraint(fields=["workspace_id", "name"], name="metric_rule_ws_name")
        ]


class MetricAlertRuleVersion(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    rule = models.ForeignKey(MetricAlertRule, on_delete=models.PROTECT, related_name="versions")
    version = models.PositiveIntegerField()
    config_snapshot = models.JSONField(default=dict)
    compliance_status = models.CharField(max_length=16, choices=MetricComplianceStatus.choices)
    compliance_issues = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "metric_alert_rule_version"
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(fields=["rule", "version"], name="metric_rule_version_unique")
        ]


class MetricAlertIncident(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    rule = models.ForeignKey(MetricAlertRule, on_delete=models.PROTECT, related_name="incidents")
    observation = models.ForeignKey(MetricObservation, on_delete=models.PROTECT, related_name="incidents")
    baseline = models.ForeignKey(
        MetricDynamicBaseline,
        on_delete=models.PROTECT,
        related_name="incidents",
        null=True,
        blank=True,
    )
    dedupe_key = models.CharField(max_length=256)
    title = models.CharField(max_length=200)
    message = models.TextField(default="", blank=True)
    severity = models.CharField(max_length=16, choices=MonitoringMetricStatus.choices)
    status = models.CharField(max_length=16, choices=MetricIncidentStatus.choices, default=MetricIncidentStatus.OPEN)
    observed_value = models.FloatField()
    threshold_value = models.FloatField()
    config_version = models.PositiveIntegerField()
    config_snapshot = models.JSONField(default=dict)
    first_triggered_at = models.DateTimeField()
    last_triggered_at = models.DateTimeField()
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "metric_alert_incident"
        ordering = ["-last_triggered_at"]
        constraints = [
            models.UniqueConstraint(fields=["workspace_id", "dedupe_key"], name="metric_incident_ws_dedupe")
        ]
        indexes = [models.Index(fields=["workspace_id", "status", "severity"], name="metric_inc_ws_status_sev")]


class MetricDutyShift(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    name = models.CharField(max_length=160)
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField(db_index=True)
    assignee = models.ForeignKey(User, on_delete=models.PROTECT, db_constraint=False, related_name="metric_duty_shifts")
    contact_snapshot = models.JSONField(default=dict, blank=True)
    enabled = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "metric_duty_shift"
        ordering = ["starts_at"]


class MetricDispatchOrder(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    incident = models.ForeignKey(MetricAlertIncident, on_delete=models.PROTECT, related_name="dispatch_orders")
    duty_shift = models.ForeignKey(
        MetricDutyShift,
        on_delete=models.SET_NULL,
        related_name="dispatch_orders",
        null=True,
        blank=True,
    )
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="metric_dispatch_orders",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=16, choices=MetricWorkOrderStatus.choices, default=MetricWorkOrderStatus.NEW)
    assignment_snapshot = models.JSONField(default=dict, blank=True)
    claimed_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "metric_dispatch_order"
        ordering = ["-create_time"]
        indexes = [models.Index(fields=["workspace_id", "status"], name="metric_order_ws_status")]


class MetricDispatchOrderEvent(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    order = models.ForeignKey(MetricDispatchOrder, on_delete=models.PROTECT, related_name="events")
    action = models.CharField(max_length=16, choices=MetricDispatchEventAction.choices)
    from_status = models.CharField(max_length=16, choices=MetricWorkOrderStatus.choices, default="", blank=True)
    to_status = models.CharField(max_length=16, choices=MetricWorkOrderStatus.choices, default="", blank=True)
    note = models.TextField(default="", blank=True)
    snapshot = models.JSONField(default=dict, blank=True)
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)
    occurred_at = models.DateTimeField(db_index=True)

    class Meta:
        db_table = "metric_dispatch_order_event"
        ordering = ["occurred_at", "create_time"]
        indexes = [models.Index(fields=["workspace_id", "order", "occurred_at"], name="metric_event_order_time")]
