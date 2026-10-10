# coding=utf-8
import uuid_utils.compat as uuid
from django.db import models

from common.mixins.app_model_mixin import AppModelMixin
from marketing.models.ivr import IvrSession
from users.models import User


class ChangeOperationType(models.TextChoices):
    PLAN_CHANGE = "PLAN_CHANGE", "套餐变更"
    CONFIG_CHANGE = "CONFIG_CHANGE", "配置变更"
    DATA_MIGRATION = "DATA_MIGRATION", "数据迁移"
    NETWORK_CUTOVER = "NETWORK_CUTOVER", "网络割接"
    OTHER = "OTHER", "其他变更"


class ChangeOperationStatus(models.TextChoices):
    DRAFT = "DRAFT", "待评估"
    RISK_EVALUATED = "RISK_EVALUATED", "已评估"
    CONFIRMATION_PENDING = "CONFIRMATION_PENDING", "待人工确认"
    APPROVED = "APPROVED", "已放行"
    REJECTED = "REJECTED", "已驳回"


class ChangeRiskLevel(models.TextChoices):
    GREEN = "GREEN", "绿灯"
    YELLOW = "YELLOW", "黄灯"
    RED = "RED", "红灯"


class ChangeConfirmationStatus(models.TextChoices):
    NOT_REQUIRED = "NOT_REQUIRED", "无需确认"
    PENDING = "PENDING", "待确认"
    APPROVED = "APPROVED", "已确认放行"
    REJECTED = "REJECTED", "已确认驳回"


class ChangeConfirmationDecision(models.TextChoices):
    APPROVE = "APPROVE", "确认放行"
    REJECT = "REJECT", "确认驳回"


class ChangeControlStatus(models.TextChoices):
    NOT_STARTED = "NOT_STARTED", "未开始"
    IN_PROGRESS = "IN_PROGRESS", "执行中"
    COMPLETED = "COMPLETED", "已完成"
    ABORTED = "ABORTED", "已终止"


class ChangeControlAction(models.TextChoices):
    START = "START", "开始执行"
    COMPLETE = "COMPLETE", "完成变更"
    ABORT = "ABORT", "终止变更"


class ChangeCommunicationKind(models.TextChoices):
    CONTROL_REMINDER = "CONTROL_REMINDER", "管控提醒"
    CUTOVER_NOTICE = "CUTOVER_NOTICE", "割接告知"


class ChangeCommunicationPhase(models.TextChoices):
    BEFORE = "BEFORE", "变更前"
    DURING = "DURING", "执行中"
    AFTER = "AFTER", "完成后"


class ChangeCommunicationAudience(models.TextChoices):
    OPERATOR = "OPERATOR", "操作人员"
    CUSTOMER = "CUSTOMER", "受影响客户"


class ChangeCommunicationChannel(models.TextChoices):
    IN_APP = "IN_APP", "站内通知"
    IVR = "IVR", "IVR 播报"
    SMS = "SMS", "短信"
    MANUAL = "MANUAL", "人工告知"


class ChangeCommunicationStatus(models.TextChoices):
    PENDING = "PENDING", "待发送"
    SENT = "SENT", "已发送"
    ACKNOWLEDGED = "ACKNOWLEDGED", "已确认"
    FAILED = "FAILED", "发送失败"


class ChangeOperation(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    code = models.CharField(max_length=96, verbose_name="变更编号")
    name = models.CharField(max_length=160, verbose_name="变更名称")
    operation_type = models.CharField(
        max_length=32,
        choices=ChangeOperationType.choices,
        default=ChangeOperationType.CONFIG_CHANGE,
        verbose_name="变更类型",
    )
    description = models.TextField(default="", blank=True, verbose_name="变更说明")
    planned_start_at = models.DateTimeField(blank=True, null=True, verbose_name="计划开始时间")
    ivr_session = models.ForeignKey(
        IvrSession,
        on_delete=models.SET_NULL,
        related_name="change_operations",
        blank=True,
        null=True,
        verbose_name="关联IVR会话",
    )
    status = models.CharField(
        max_length=32,
        choices=ChangeOperationStatus.choices,
        default=ChangeOperationStatus.DRAFT,
        db_index=True,
    )
    risk_level = models.CharField(
        max_length=16,
        choices=ChangeRiskLevel.choices,
        default=ChangeRiskLevel.GREEN,
        db_index=True,
    )
    risk_score = models.PositiveIntegerField(default=0, verbose_name="风险分")
    risk_revision = models.PositiveIntegerField(default=0, verbose_name="评估版本")
    risk_snapshot = models.JSONField(default=dict, blank=True, verbose_name="最近风险输入快照")
    risk_reasons = models.JSONField(default=list, blank=True, verbose_name="最近风险原因")
    confirmation_status = models.CharField(
        max_length=24,
        choices=ChangeConfirmationStatus.choices,
        default=ChangeConfirmationStatus.NOT_REQUIRED,
        db_index=True,
    )
    evaluated_at = models.DateTimeField(blank=True, null=True, verbose_name="最近评估时间")
    decided_at = models.DateTimeField(blank=True, null=True, verbose_name="最近决策时间")
    control_status = models.CharField(
        max_length=24,
        choices=ChangeControlStatus.choices,
        default=ChangeControlStatus.NOT_STARTED,
        db_index=True,
        verbose_name="执行管控状态",
    )
    actual_start_at = models.DateTimeField(blank=True, null=True, verbose_name="实际开始时间")
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name="完成或终止时间")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)

    class Meta:
        db_table = "change_operation"
        ordering = ["-update_time"]
        constraints = [models.UniqueConstraint(fields=["workspace_id", "code"], name="change_operation_ws_code")]
        indexes = [
            models.Index(
                fields=["workspace_id", "risk_level", "status", "update_time"],
                name="change_operation_ws_risk",
            )
        ]


class ChangeRiskAssessment(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    operation = models.ForeignKey(ChangeOperation, on_delete=models.CASCADE, related_name="assessments")
    revision = models.PositiveIntegerField(verbose_name="评估版本")
    risk_level = models.CharField(max_length=16, choices=ChangeRiskLevel.choices, db_index=True)
    risk_score = models.PositiveIntegerField(verbose_name="风险分")
    input_snapshot = models.JSONField(default=dict, verbose_name="评估输入快照")
    reasons = models.JSONField(default=list, verbose_name="风险原因")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)

    class Meta:
        db_table = "change_risk_assessment"
        ordering = ["-revision"]
        constraints = [
            models.UniqueConstraint(fields=["operation", "revision"], name="change_assessment_operation_revision")
        ]
        indexes = [models.Index(fields=["workspace_id", "risk_level", "create_time"], name="change_assessment_ws_risk")]


class ChangeConfirmation(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    operation = models.ForeignKey(ChangeOperation, on_delete=models.CASCADE, related_name="confirmations")
    assessment = models.ForeignKey(ChangeRiskAssessment, on_delete=models.PROTECT, related_name="confirmations")
    request_id = models.CharField(max_length=160, verbose_name="确认幂等键")
    decision = models.CharField(max_length=16, choices=ChangeConfirmationDecision.choices)
    comment = models.TextField(default="", blank=True, verbose_name="确认意见")
    risk_level = models.CharField(max_length=16, choices=ChangeRiskLevel.choices)
    risk_score = models.PositiveIntegerField(verbose_name="确认时风险分")
    confirmer = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)

    class Meta:
        db_table = "change_confirmation"
        ordering = ["-create_time"]
        constraints = [
            models.UniqueConstraint(fields=["workspace_id", "request_id"], name="change_confirmation_ws_request")
        ]
        indexes = [models.Index(fields=["workspace_id", "decision", "create_time"], name="change_confirm_ws_decision")]


class ChangeOperationCommunication(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    operation = models.ForeignKey(ChangeOperation, on_delete=models.CASCADE, related_name="communications")
    request_id = models.CharField(max_length=160, verbose_name="通信事件幂等键")
    kind = models.CharField(max_length=32, choices=ChangeCommunicationKind.choices, db_index=True)
    phase = models.CharField(max_length=16, choices=ChangeCommunicationPhase.choices, db_index=True)
    audience = models.CharField(max_length=16, choices=ChangeCommunicationAudience.choices, db_index=True)
    channel = models.CharField(max_length=16, choices=ChangeCommunicationChannel.choices)
    subject = models.CharField(max_length=160, verbose_name="提醒或告知主题")
    content = models.TextField(verbose_name="提醒或告知内容")
    status = models.CharField(
        max_length=24,
        choices=ChangeCommunicationStatus.choices,
        default=ChangeCommunicationStatus.PENDING,
        db_index=True,
    )
    scheduled_at = models.DateTimeField(blank=True, null=True, verbose_name="计划发送时间")
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name="实际发送时间")
    acknowledged_at = models.DateTimeField(blank=True, null=True, verbose_name="确认时间")
    failure_reason = models.TextField(default="", blank=True, verbose_name="失败原因")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)

    class Meta:
        db_table = "change_operation_communication"
        ordering = ["-create_time"]
        constraints = [models.UniqueConstraint(fields=["workspace_id", "request_id"], name="change_comm_ws_request")]
        indexes = [
            models.Index(
                fields=["workspace_id", "phase", "status", "create_time"],
                name="change_comm_ws_phase_status",
            )
        ]


class ChangeControlActionRecord(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    operation = models.ForeignKey(ChangeOperation, on_delete=models.CASCADE, related_name="control_actions")
    revision = models.PositiveIntegerField(verbose_name="管控操作版本")
    action = models.CharField(max_length=16, choices=ChangeControlAction.choices, db_index=True)
    previous_status = models.CharField(max_length=24, choices=ChangeControlStatus.choices)
    current_status = models.CharField(max_length=24, choices=ChangeControlStatus.choices)
    note = models.TextField(default="", blank=True, verbose_name="操作说明")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)

    class Meta:
        db_table = "change_control_action_record"
        ordering = ["-revision"]
        constraints = [models.UniqueConstraint(fields=["operation", "revision"], name="change_control_action_revision")]
        indexes = [models.Index(fields=["workspace_id", "action", "create_time"], name="change_action_ws_type")]


class ChangeQualityReport(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    title = models.CharField(max_length=160, verbose_name="报告标题")
    period_start = models.DateField(verbose_name="统计开始日期")
    period_end = models.DateField(verbose_name="统计结束日期")
    metrics = models.JSONField(default=dict, verbose_name="质量指标快照")
    daily_trend = models.JSONField(default=list, verbose_name="每日趋势快照")
    operation_snapshot = models.JSONField(default=list, verbose_name="变更明细快照")
    generated_at = models.DateTimeField(verbose_name="生成时间")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)

    class Meta:
        db_table = "change_quality_report"
        ordering = ["-generated_at"]
        indexes = [
            models.Index(
                fields=["workspace_id", "period_start", "period_end"],
                name="change_quality_ws_period",
            )
        ]
