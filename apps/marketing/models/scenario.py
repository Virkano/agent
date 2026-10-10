# coding=utf-8
import uuid_utils.compat as uuid
from django.db import models

from application.models import Application, ChatRecord
from common.mixins.app_model_mixin import AppModelMixin
from knowledge.models import Knowledge
from users.models import User


class MarketingScenarioStatus(models.TextChoices):
    DRAFT = "DRAFT", "草稿"
    ACTIVE = "ACTIVE", "启用"
    PAUSED = "PAUSED", "停用"


class MarketingTaskStatus(models.TextChoices):
    DRAFT = "DRAFT", "草稿"
    RUNNING = "RUNNING", "进行中"
    PAUSED = "PAUSED", "已暂停"
    FINISHED = "FINISHED", "已结束"


class MarketingCampaignStatus(models.TextChoices):
    DRAFT = "DRAFT", "草稿"
    ACTIVE = "ACTIVE", "已上线"
    PAUSED = "PAUSED", "已暂停"
    ARCHIVED = "ARCHIVED", "已归档"


class MarketingCampaignApprovalStatus(models.TextChoices):
    DRAFT = "DRAFT", "未提交"
    PENDING = "PENDING", "待审批"
    APPROVED = "APPROVED", "已通过"
    REJECTED = "REJECTED", "已驳回"


class MarketingCustomerStatus(models.TextChoices):
    PENDING = "PENDING", "待触达"
    TOUCHED = "TOUCHED", "已触达"
    CONSULTED = "CONSULTED", "已咨询"
    INTENT = "INTENT", "有意向"
    NO_INTENT = "NO_INTENT", "无意向"
    MANUAL = "MANUAL", "转人工"
    CONVERTED = "CONVERTED", "已办理"


class MarketingAnswerQualityStatus(models.TextChoices):
    PASS = "PASS", "正常"
    REVIEW = "REVIEW", "需复核"
    HIGH_RISK = "HIGH_RISK", "高风险"


class MarketingAnswerManualReviewStatus(models.TextChoices):
    PENDING = "PENDING", "待处理"
    CONFIRMED_PASS = "CONFIRMED_PASS", "确认正常"
    CONFIRMED_ISSUE = "CONFIRMED_ISSUE", "确认问题"
    REVISED = "REVISED", "已修订"


class MarketingAnswerManualReviewAction(models.TextChoices):
    CONFIRM_PASS = "CONFIRM_PASS", "确认正常"
    CONFIRM_ISSUE = "CONFIRM_ISSUE", "确认问题"
    REVISE = "REVISE", "提交修订"


class MarketingQualityPolicyMode(models.TextChoices):
    OFF = "OFF", "关闭"
    SHADOW = "SHADOW", "影子检测"
    INTERCEPT = "INTERCEPT", "灰度拦截"


class MarketingPreflightAction(models.TextChoices):
    OBSERVED = "OBSERVED", "仅观察"
    SAFEGUARD_REWRITTEN = "SAFEGUARD_REWRITTEN", "安全规则已改写"
    INTERCEPTED = "INTERCEPTED", "灰度拦截"
    BYPASSED = "BYPASSED", "检测旁路"


class MarketingTouchBatchStatus(models.TextChoices):
    READY = "READY", "待执行"
    RUNNING = "RUNNING", "执行中"
    CLOSED = "CLOSED", "已关闭"


class MarketingTouchBatchApprovalStatus(models.TextChoices):
    PENDING = "PENDING", "待审批"
    APPROVED = "APPROVED", "已通过"
    REJECTED = "REJECTED", "已驳回"


class MarketingTouchBatchApprovalAction(models.TextChoices):
    SUBMITTED = "SUBMITTED", "提交审批"
    APPROVED = "APPROVED", "审批通过"
    REJECTED = "REJECTED", "审批驳回"
    RESUBMITTED = "RESUBMITTED", "修改后重提"


class MarketingTouchExecutionResult(models.TextChoices):
    CONTACTED = "CONTACTED", "已联系"
    NO_ANSWER = "NO_ANSWER", "未接通"
    REJECTED = "REJECTED", "明确拒绝"
    INTENT = "INTENT", "有办理意向"
    MANUAL = "MANUAL", "转人工处理"


class MarketingConversionOutcome(models.TextChoices):
    CONVERTED = "CONVERTED", "确认办理"
    LOST = "LOST", "确认流失"


class MarketingAlertSeverity(models.TextChoices):
    INFO = "INFO", "提示"
    WARNING = "WARNING", "关注"
    CRITICAL = "CRITICAL", "紧急"


class MarketingAlertStatus(models.TextChoices):
    OPEN = "OPEN", "待处理"
    CLAIMED = "CLAIMED", "已认领"
    PROCESSING = "PROCESSING", "处理中"
    CLOSED = "CLOSED", "已关闭"


class MarketingAlertRootCause(models.TextChoices):
    MODEL = "MODEL", "模型服务"
    DATA = "DATA", "客户数据"
    KNOWLEDGE = "KNOWLEDGE", "知识内容"
    SYSTEM = "SYSTEM", "系统资源"
    PROCESS = "PROCESS", "运营流程"
    OTHER = "OTHER", "其他"


class MarketingAlertResolutionType(models.TextChoices):
    CONFIG_CHANGE = "CONFIG_CHANGE", "调整配置"
    DATA_FIX = "DATA_FIX", "修复数据"
    KNOWLEDGE_UPDATE = "KNOWLEDGE_UPDATE", "更新知识"
    RETRY_RECOVERY = "RETRY_RECOVERY", "重试恢复"
    MANUAL_INTERVENTION = "MANUAL_INTERVENTION", "人工处置"
    FALSE_POSITIVE = "FALSE_POSITIVE", "确认误报"
    OTHER = "OTHER", "其他"


class MarketingAlertAction(models.TextChoices):
    CREATED = "CREATED", "系统创建"
    REFRESHED = "REFRESHED", "系统刷新"
    CLAIMED = "CLAIMED", "认领"
    STARTED = "STARTED", "开始处理"
    CLOSED = "CLOSED", "关闭"
    REOPENED = "REOPENED", "重新打开"
    RESPONSE_OVERDUE = "RESPONSE_OVERDUE", "首次响应超时"
    RESOLUTION_OVERDUE = "RESOLUTION_OVERDUE", "处理超时"
    ASSIGNED = "ASSIGNED", "指派"
    TRANSFERRED = "TRANSFERRED", "转派"
    COMMENTED = "COMMENTED", "协作评论"
    SUBSCRIBED = "SUBSCRIBED", "添加关注人"
    UNSUBSCRIBED = "UNSUBSCRIBED", "移除关注人"
    ATTACHED = "ATTACHED", "上传附件"


class MarketingAlertRoundEndReason(models.TextChoices):
    TRANSFERRED = "TRANSFERRED", "已转派"
    CLOSED = "CLOSED", "已关闭"
    REOPENED = "REOPENED", "已重新打开"


class MarketingAlertRuleChangeType(models.TextChoices):
    UPDATED = "UPDATED", "规则调整"
    ROLLED_BACK = "ROLLED_BACK", "规则回滚"


class MarketingNotificationStatus(models.TextChoices):
    UNREAD = "UNREAD", "未读"
    READ = "READ", "已读"


class MarketingScenario(AppModelMixin):
    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, verbose_name="工作空间id", default="default", db_index=True)
    name = models.CharField(max_length=128, verbose_name="营销场景名称", db_index=True)
    target_audience = models.CharField(max_length=256, verbose_name="目标客群", default="", blank=True)
    objective = models.CharField(max_length=256, verbose_name="营销目标", default="", blank=True)
    channel = models.CharField(max_length=64, verbose_name="触达渠道", default="ONLINE", blank=True)
    status = models.CharField(
        verbose_name="状态",
        choices=MarketingScenarioStatus.choices,
        default=MarketingScenarioStatus.DRAFT,
        max_length=32,
        db_index=True,
    )
    application = models.ForeignKey(
        Application,
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        verbose_name="关联智能体",
    )
    knowledge = models.ForeignKey(
        Knowledge,
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        verbose_name="关联知识库",
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)
    config = models.JSONField(verbose_name="场景配置", default=dict, blank=True)
    description = models.TextField(verbose_name="说明", default="", blank=True)

    class Meta:
        db_table = "marketing_scenario"
        unique_together = ["workspace_id", "name"]
        ordering = ["-update_time"]


class MarketingCampaign(AppModelMixin):
    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, verbose_name="工作空间id", default="default", db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)
    name = models.CharField(max_length=128, verbose_name="活动名称", db_index=True)
    code = models.CharField(max_length=64, verbose_name="活动编码", db_index=True)
    status = models.CharField(
        max_length=32, choices=MarketingCampaignStatus.choices, default=MarketingCampaignStatus.DRAFT, db_index=True
    )
    approval_status = models.CharField(
        max_length=32,
        choices=MarketingCampaignApprovalStatus.choices,
        default=MarketingCampaignApprovalStatus.APPROVED,
        db_index=True,
    )
    approval_note = models.TextField(default="", blank=True, verbose_name="审批意见")
    approver_name = models.CharField(max_length=64, default="", blank=True, verbose_name="审批人")
    approved_at = models.DateTimeField(blank=True, null=True, verbose_name="审批时间")
    version = models.IntegerField(default=1, verbose_name="版本号")
    priority = models.IntegerField(default=100, verbose_name="推荐优先级")
    exclusive_group = models.CharField(max_length=64, default="", blank=True, verbose_name="互斥组")
    benefit = models.TextField(default="", blank=True, verbose_name="客户可见权益")
    fee_note = models.CharField(
        max_length=256, default="费用以当地实际可办理方案为准。", blank=True, verbose_name="费用说明"
    )
    contract_note = models.CharField(
        max_length=256, default="办理前会确认优惠期限和合约期。", blank=True, verbose_name="合约说明"
    )
    plan_keywords = models.JSONField(default=list, blank=True, verbose_name="适用套餐关键词")
    provinces = models.JSONField(default=list, blank=True, verbose_name="适用省份")
    min_data_usage_gb = models.IntegerField(default=0, verbose_name="最低近月流量GB")
    min_call_usage_minutes = models.IntegerField(default=0, verbose_name="最低近月通话分钟")
    effective_start = models.DateField(blank=True, null=True, verbose_name="生效开始日期")
    effective_end = models.DateField(blank=True, null=True, verbose_name="生效结束日期")
    description = models.TextField(default="", blank=True, verbose_name="活动说明")

    class Meta:
        db_table = "marketing_campaign"
        unique_together = ["workspace_id", "code"]
        ordering = ["-update_time"]


class MarketingCampaignVersion(AppModelMixin):
    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, verbose_name="工作空间id", default="default", db_index=True)
    campaign = models.ForeignKey(
        MarketingCampaign,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="versions",
        verbose_name="营销活动",
    )
    version = models.IntegerField(verbose_name="版本号")
    snapshot = models.JSONField(default=dict, verbose_name="活动配置快照")
    change_type = models.CharField(max_length=32, default="UPDATE", verbose_name="变更类型")
    source_version = models.IntegerField(blank=True, null=True, verbose_name="恢复来源版本")
    approval_status = models.CharField(
        max_length=32,
        choices=MarketingCampaignApprovalStatus.choices,
        default=MarketingCampaignApprovalStatus.DRAFT,
        db_index=True,
    )
    approval_note = models.TextField(default="", blank=True, verbose_name="审批意见")
    approver_name = models.CharField(max_length=64, default="", blank=True, verbose_name="审批人")
    approved_at = models.DateTimeField(blank=True, null=True, verbose_name="审批时间")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)

    class Meta:
        db_table = "marketing_campaign_version"
        unique_together = ["campaign", "version"]
        ordering = ["-version"]


class MarketingTask(AppModelMixin):
    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, verbose_name="工作空间id", default="default", db_index=True)
    name = models.CharField(max_length=128, verbose_name="营销任务名称", db_index=True)
    scenario = models.ForeignKey(
        MarketingScenario,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="tasks",
        verbose_name="营销场景",
    )
    application = models.ForeignKey(
        Application,
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        verbose_name="关联智能体",
    )
    knowledge = models.ForeignKey(
        Knowledge,
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        verbose_name="关联知识库",
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)
    target_audience = models.CharField(max_length=256, verbose_name="目标客群", default="", blank=True)
    objective = models.CharField(max_length=256, verbose_name="任务目标", default="", blank=True)
    channel = models.CharField(max_length=64, verbose_name="触达渠道", default="ONLINE", blank=True)
    status = models.CharField(
        verbose_name="状态",
        choices=MarketingTaskStatus.choices,
        default=MarketingTaskStatus.DRAFT,
        max_length=32,
        db_index=True,
    )
    target_count = models.IntegerField(verbose_name="计划触达人数", default=0)
    config = models.JSONField(verbose_name="任务配置", default=dict, blank=True)
    description = models.TextField(verbose_name="说明", default="", blank=True)

    class Meta:
        db_table = "marketing_task"
        unique_together = ["workspace_id", "name"]
        ordering = ["-update_time"]


class MarketingCustomer(AppModelMixin):
    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, verbose_name="工作空间id", default="default", db_index=True)
    task = models.ForeignKey(
        MarketingTask,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="customers",
        verbose_name="营销任务",
    )
    name = models.CharField(max_length=128, verbose_name="客户名称", default="", blank=True)
    phone = models.CharField(max_length=64, verbose_name="手机号/客户标识", default="", blank=True)
    province = models.CharField(max_length=64, verbose_name="省份", default="", blank=True)
    current_plan = models.CharField(max_length=128, verbose_name="当前套餐", default="", blank=True)
    monthly_data_usage = models.CharField(max_length=64, verbose_name="近月流量", default="", blank=True)
    monthly_call_usage = models.CharField(max_length=64, verbose_name="近月通话", default="", blank=True)
    status = models.CharField(
        verbose_name="触达状态",
        choices=MarketingCustomerStatus.choices,
        default=MarketingCustomerStatus.PENDING,
        max_length=32,
        db_index=True,
    )
    intent = models.CharField(max_length=64, verbose_name="意向状态", default="", blank=True)
    remark = models.TextField(verbose_name="备注", default="", blank=True)
    config = models.JSONField(verbose_name="扩展配置", default=dict, blank=True)

    class Meta:
        db_table = "marketing_customer"
        ordering = ["-update_time"]


class MarketingCustomerImportBatch(AppModelMixin):
    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, verbose_name="工作空间id", default="default", db_index=True)
    task = models.ForeignKey(
        MarketingTask,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="customer_import_batches",
        verbose_name="营销任务",
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)
    file_name = models.CharField(max_length=256, verbose_name="导入文件名")
    total_count = models.IntegerField(default=0, verbose_name="源数据行数")
    valid_count = models.IntegerField(default=0, verbose_name="校验可导入数")
    imported_count = models.IntegerField(default=0, verbose_name="实际导入数")
    skipped_count = models.IntegerField(default=0, verbose_name="跳过数")
    error_count = models.IntegerField(default=0, verbose_name="错误数")
    mapping = models.JSONField(default=dict, blank=True, verbose_name="字段映射")
    error_rows = models.JSONField(default=list, blank=True, verbose_name="异常行摘要")

    class Meta:
        db_table = "marketing_customer_import_batch"
        ordering = ["-create_time"]


class MarketingTouchBatch(AppModelMixin):
    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, verbose_name="工作空间id", default="default", db_index=True)
    task = models.ForeignKey(
        MarketingTask,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="touch_batches",
        verbose_name="营销任务",
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)
    name = models.CharField(max_length=128, verbose_name="触达批次名称")
    owner_name = models.CharField(max_length=64, verbose_name="负责人", default="", blank=True)
    deadline = models.DateTimeField(verbose_name="执行截止时间", blank=True, null=True)
    approval_status = models.CharField(
        choices=MarketingTouchBatchApprovalStatus.choices,
        default=MarketingTouchBatchApprovalStatus.APPROVED,
        max_length=32,
        db_index=True,
    )
    approval_note = models.TextField(default="", blank=True)
    approver_name = models.CharField(max_length=64, default="", blank=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    approval_due_at = models.DateTimeField(blank=True, null=True, db_index=True)
    status = models.CharField(
        verbose_name="批次状态",
        choices=MarketingTouchBatchStatus.choices,
        default=MarketingTouchBatchStatus.READY,
        max_length=32,
        db_index=True,
    )
    filter_config = models.JSONField(verbose_name="筛选条件快照", default=dict, blank=True)
    customer_snapshot = models.JSONField(verbose_name="入选客户快照", default=list, blank=True)
    excluded_snapshot = models.JSONField(verbose_name="排除客户快照", default=list, blank=True)
    selected_count = models.IntegerField(verbose_name="入选人数", default=0)
    excluded_count = models.IntegerField(verbose_name="排除人数", default=0)

    class Meta:
        db_table = "marketing_touch_batch"
        ordering = ["-create_time"]


class MarketingTouchBatchApprovalRecord(AppModelMixin):
    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, verbose_name="工作空间id", default="default", db_index=True)
    batch = models.ForeignKey(
        MarketingTouchBatch,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="approval_records",
        verbose_name="触达批次",
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)
    action = models.CharField(max_length=32, choices=MarketingTouchBatchApprovalAction.choices, db_index=True)
    note = models.TextField(default="", blank=True)

    class Meta:
        db_table = "marketing_touch_batch_approval_record"
        ordering = ["create_time"]


class MarketingTouchExecution(AppModelMixin):
    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, verbose_name="工作空间id", default="default", db_index=True)
    batch = models.ForeignKey(
        MarketingTouchBatch,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="executions",
        verbose_name="触达批次",
    )
    customer = models.ForeignKey(
        MarketingCustomer,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="touch_executions",
        verbose_name="营销客户",
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)
    result = models.CharField(
        verbose_name="触达结果",
        choices=MarketingTouchExecutionResult.choices,
        max_length=32,
        db_index=True,
    )
    note = models.TextField(verbose_name="执行记录", default="", blank=True)
    next_follow_up_at = models.DateTimeField(verbose_name="下次跟进时间", blank=True, null=True)

    class Meta:
        db_table = "marketing_touch_execution"
        ordering = ["-create_time"]


class MarketingConversionRecord(AppModelMixin):
    """A confirmed business outcome attributed to a marketing task and optional touch batch."""

    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, verbose_name="工作空间id", default="default", db_index=True)
    task = models.ForeignKey(
        MarketingTask,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="conversion_records",
        verbose_name="营销任务",
    )
    customer = models.ForeignKey(
        MarketingCustomer,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="conversion_records",
        verbose_name="营销客户",
    )
    batch = models.ForeignKey(
        MarketingTouchBatch,
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="conversion_records",
        blank=True,
        null=True,
        verbose_name="归因触达批次",
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)
    outcome = models.CharField(
        verbose_name="转化结果", choices=MarketingConversionOutcome.choices, max_length=32, db_index=True
    )
    product_name = models.CharField(verbose_name="办理产品/套餐", max_length=128, default="", blank=True)
    note = models.TextField(verbose_name="结果说明", default="", blank=True)

    class Meta:
        db_table = "marketing_conversion_record"
        ordering = ["-create_time"]


class MarketingAnswerQualityReview(AppModelMixin):
    """Deterministic, auditable quality result for one marketing answer."""

    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, verbose_name="工作空间id", default="default", db_index=True)
    task = models.ForeignKey(
        MarketingTask,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="answer_quality_reviews",
        verbose_name="营销任务",
    )
    customer = models.ForeignKey(
        MarketingCustomer,
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="answer_quality_reviews",
        blank=True,
        null=True,
        verbose_name="营销客户",
    )
    record = models.OneToOneField(
        ChatRecord,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="marketing_quality_review",
        verbose_name="对话记录",
    )
    status = models.CharField(
        max_length=32,
        choices=MarketingAnswerQualityStatus.choices,
        default=MarketingAnswerQualityStatus.PASS,
        db_index=True,
        verbose_name="质检状态",
    )
    score = models.IntegerField(default=100, verbose_name="质量分")
    risk_types = models.JSONField(default=list, blank=True, verbose_name="风险类型")
    reasons = models.JSONField(default=list, blank=True, verbose_name="风险原因")
    suggestion = models.TextField(default="", blank=True, verbose_name="处理建议")
    evidence = models.JSONField(default=dict, blank=True, verbose_name="判断依据")
    rule_version = models.CharField(max_length=32, default="marketing-quality-v1", verbose_name="规则版本")
    manual_status = models.CharField(
        max_length=32,
        choices=MarketingAnswerManualReviewStatus.choices,
        default=MarketingAnswerManualReviewStatus.PENDING,
        db_index=True,
        verbose_name="人工复核状态",
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="+",
        blank=True,
        null=True,
        verbose_name="最近复核人",
    )
    reviewer_name = models.CharField(max_length=128, default="", blank=True, verbose_name="最近复核人名称")
    reviewed_at = models.DateTimeField(blank=True, null=True, verbose_name="最近复核时间")
    review_note = models.TextField(default="", blank=True, verbose_name="最近复核意见")
    revised_answer = models.TextField(default="", blank=True, verbose_name="当前修订答案")
    manual_revision = models.PositiveIntegerField(default=0, verbose_name="人工修订版本")

    class Meta:
        db_table = "marketing_answer_quality_review"
        ordering = ["-create_time"]
        indexes = [
            models.Index(fields=["workspace_id", "task", "status"], name="mkt_q_ws_task_status"),
            models.Index(fields=["workspace_id", "manual_status"], name="mkt_q_ws_manual_status"),
        ]


class MarketingAnswerQualityReviewActionRecord(AppModelMixin):
    """Append-only audit record for one human quality-review action."""

    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, verbose_name="工作空间id", default="default", db_index=True)
    review = models.ForeignKey(
        MarketingAnswerQualityReview,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="manual_actions",
        verbose_name="回答质检记录",
    )
    task = models.ForeignKey(
        MarketingTask,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="answer_quality_review_actions",
        verbose_name="营销任务",
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)
    reviewer_name = models.CharField(max_length=128, default="", blank=True, verbose_name="复核人名称")
    action = models.CharField(max_length=32, choices=MarketingAnswerManualReviewAction.choices, db_index=True)
    previous_status = models.CharField(max_length=32, default="", blank=True, verbose_name="处理前状态")
    current_status = models.CharField(max_length=32, verbose_name="处理后状态")
    original_answer = models.TextField(default="", blank=True, verbose_name="原回答快照")
    revised_answer = models.TextField(default="", blank=True, verbose_name="修订答案快照")
    note = models.TextField(default="", blank=True, verbose_name="复核意见")
    revision = models.PositiveIntegerField(default=1, verbose_name="人工操作版本")

    class Meta:
        db_table = "marketing_answer_quality_review_action"
        ordering = ["-create_time"]
        indexes = [
            models.Index(fields=["workspace_id", "task", "action"], name="mkt_q_action_ws_task"),
            models.Index(fields=["review", "revision"], name="mkt_q_action_revision"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["review", "revision"], name="mkt_q_unique_action_revision"),
        ]


class MarketingQualityPolicy(AppModelMixin):
    """Workspace-level switch for answer checks executed around the send pipeline."""

    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, unique=True, verbose_name="工作空间id")
    mode = models.CharField(
        max_length=32,
        choices=MarketingQualityPolicyMode.choices,
        default=MarketingQualityPolicyMode.SHADOW,
        db_index=True,
        verbose_name="发送前质检模式",
    )
    rule_version = models.CharField(max_length=32, default="marketing-quality-v1", verbose_name="规则版本")
    intercept_rule_types = models.JSONField(default=list, blank=True, verbose_name="灰度拦截规则")
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="+",
        blank=True,
        null=True,
        verbose_name="最近更新人",
    )
    updated_by_name = models.CharField(max_length=128, default="", blank=True, verbose_name="最近更新人名称")

    class Meta:
        db_table = "marketing_quality_policy"
        ordering = ["workspace_id"]


class MarketingAnswerPreflightRecord(AppModelMixin):
    """Auditable observation of an answer around the customer-send boundary."""

    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, verbose_name="工作空间id", default="default", db_index=True)
    task = models.ForeignKey(
        MarketingTask,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="answer_preflight_records",
        verbose_name="营销任务",
    )
    customer = models.ForeignKey(
        MarketingCustomer,
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="answer_preflight_records",
        blank=True,
        null=True,
        verbose_name="营销客户",
    )
    record = models.OneToOneField(
        ChatRecord,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="marketing_preflight_record",
        verbose_name="对话记录",
    )
    policy_mode = models.CharField(max_length=32, choices=MarketingQualityPolicyMode.choices, db_index=True)
    action = models.CharField(max_length=32, choices=MarketingPreflightAction.choices, db_index=True)
    generated_answer = models.TextField(default="", blank=True, verbose_name="模型原始生成回答")
    final_answer = models.TextField(default="", blank=True, verbose_name="最终发送回答")
    status = models.CharField(
        max_length=32,
        choices=MarketingAnswerQualityStatus.choices,
        default=MarketingAnswerQualityStatus.PASS,
        db_index=True,
        verbose_name="发送前质检状态",
    )
    score = models.IntegerField(default=100, verbose_name="质量分")
    risk_types = models.JSONField(default=list, blank=True, verbose_name="风险类型")
    reasons = models.JSONField(default=list, blank=True, verbose_name="风险原因")
    suggestion = models.TextField(default="", blank=True, verbose_name="处理建议")
    evidence = models.JSONField(default=dict, blank=True, verbose_name="判断依据")
    rule_version = models.CharField(max_length=32, default="marketing-quality-v1", verbose_name="规则版本")
    evaluation_ms = models.PositiveIntegerField(default=0, verbose_name="检测耗时毫秒")

    class Meta:
        db_table = "marketing_answer_preflight_record"
        ordering = ["-create_time"]
        indexes = [
            models.Index(fields=["workspace_id", "status", "create_time"], name="mkt_pf_ws_status_time"),
            models.Index(fields=["workspace_id", "task", "action"], name="mkt_pf_ws_task_action"),
        ]


class MarketingAlertRule(AppModelMixin):
    """Workspace-level threshold and severity configuration for one operations signal."""

    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, verbose_name="工作空间id", db_index=True)
    alert_type = models.CharField(max_length=64, verbose_name="告警类型", db_index=True)
    name = models.CharField(max_length=128, verbose_name="规则名称")
    severity = models.CharField(
        max_length=32,
        choices=MarketingAlertSeverity.choices,
        default=MarketingAlertSeverity.WARNING,
        verbose_name="告警级别",
    )
    enabled = models.BooleanField(default=True, verbose_name="是否启用")
    threshold = models.PositiveIntegerField(default=1, verbose_name="触发阈值")
    response_sla_minutes = models.PositiveIntegerField(default=30, verbose_name="首次响应时限（分钟）")
    resolution_sla_minutes = models.PositiveIntegerField(default=240, verbose_name="处理时限（分钟）")
    escalation_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="+",
        blank=True,
        null=True,
        verbose_name="升级接收人",
    )
    escalation_user_name = models.CharField(max_length=128, default="", blank=True, verbose_name="升级接收人名称")
    description = models.CharField(max_length=256, default="", blank=True, verbose_name="规则说明")
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="+",
        blank=True,
        null=True,
        verbose_name="最近更新人",
    )
    updated_by_name = models.CharField(max_length=128, default="", blank=True, verbose_name="最近更新人名称")

    class Meta:
        db_table = "marketing_alert_rule"
        ordering = ["alert_type"]
        constraints = [
            models.UniqueConstraint(fields=["workspace_id", "alert_type"], name="mkt_alert_rule_ws_type"),
        ]


class MarketingAlertRuleChange(AppModelMixin):
    """Recoverable snapshot captured before an alert rule changes."""

    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, verbose_name="工作空间id", db_index=True)
    rule = models.ForeignKey(
        MarketingAlertRule,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="changes",
        verbose_name="告警规则",
    )
    version = models.PositiveIntegerField(default=1, verbose_name="变更版本")
    change_type = models.CharField(
        max_length=32,
        choices=MarketingAlertRuleChangeType.choices,
        default=MarketingAlertRuleChangeType.UPDATED,
        verbose_name="变更类型",
    )
    snapshot = models.JSONField(default=dict, verbose_name="变更前规则快照")
    reason = models.CharField(max_length=500, default="", blank=True, verbose_name="变更原因")
    operator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="+",
        blank=True,
        null=True,
        verbose_name="操作人",
    )
    operator_name = models.CharField(max_length=128, default="", blank=True, verbose_name="操作人名称")

    class Meta:
        db_table = "marketing_alert_rule_change"
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(fields=["rule", "version"], name="mkt_alert_rule_change_version"),
        ]


class MarketingAlert(AppModelMixin):
    """Persistent operations alert deduplicated by workspace and source signal."""

    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, verbose_name="工作空间id", db_index=True)
    rule = models.ForeignKey(
        MarketingAlertRule,
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="alerts",
        blank=True,
        null=True,
        verbose_name="告警规则",
    )
    alert_type = models.CharField(max_length=64, verbose_name="告警类型", db_index=True)
    dedupe_key = models.CharField(max_length=160, verbose_name="去重键")
    title = models.CharField(max_length=128, verbose_name="告警标题")
    description = models.TextField(default="", blank=True, verbose_name="告警说明")
    severity = models.CharField(
        max_length=32,
        choices=MarketingAlertSeverity.choices,
        default=MarketingAlertSeverity.WARNING,
        db_index=True,
        verbose_name="告警级别",
    )
    status = models.CharField(
        max_length=32,
        choices=MarketingAlertStatus.choices,
        default=MarketingAlertStatus.OPEN,
        db_index=True,
        verbose_name="处理状态",
    )
    current_count = models.PositiveIntegerField(default=0, verbose_name="当前异常数")
    source_active = models.BooleanField(default=True, db_index=True, verbose_name="来源是否仍异常")
    source_snapshot = models.JSONField(default=dict, blank=True, verbose_name="来源快照")
    target_route = models.CharField(max_length=256, default="", blank=True, verbose_name="处理页面")
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="+",
        blank=True,
        null=True,
        verbose_name="负责人",
    )
    assignee_name = models.CharField(max_length=128, default="", blank=True, verbose_name="负责人名称")
    first_triggered_at = models.DateTimeField(verbose_name="首次触发时间")
    last_triggered_at = models.DateTimeField(verbose_name="最近触发时间")
    sla_started_at = models.DateTimeField(blank=True, null=True, verbose_name="本轮SLA开始时间")
    response_due_at = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name="首次响应截止时间")
    resolution_due_at = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name="处理截止时间")
    first_responded_at = models.DateTimeField(blank=True, null=True, verbose_name="首次响应时间")
    response_escalated_at = models.DateTimeField(blank=True, null=True, verbose_name="响应超时升级时间")
    resolution_escalated_at = models.DateTimeField(blank=True, null=True, verbose_name="处理超时升级时间")
    resolved_at = models.DateTimeField(blank=True, null=True, verbose_name="来源恢复时间")
    closed_at = models.DateTimeField(blank=True, null=True, verbose_name="关闭时间")
    close_note = models.TextField(default="", blank=True, verbose_name="关闭说明")
    root_cause_category = models.CharField(
        max_length=32,
        choices=MarketingAlertRootCause.choices,
        default="",
        blank=True,
        db_index=True,
        verbose_name="根因分类",
    )
    resolution_type = models.CharField(
        max_length=32,
        choices=MarketingAlertResolutionType.choices,
        default="",
        blank=True,
        db_index=True,
        verbose_name="处置方式",
    )
    impact_scope = models.CharField(max_length=500, default="", blank=True, verbose_name="影响范围")
    revision = models.PositiveIntegerField(default=0, verbose_name="操作版本")

    class Meta:
        db_table = "marketing_alert"
        ordering = ["-last_triggered_at", "-create_time"]
        indexes = [
            models.Index(fields=["workspace_id", "status"], name="mkt_alert_ws_status"),
            models.Index(fields=["workspace_id", "severity"], name="mkt_alert_ws_severity"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["workspace_id", "dedupe_key"], name="mkt_alert_ws_dedupe"),
        ]


class MarketingAlertActionRecord(AppModelMixin):
    """Append-only action history for one persistent marketing alert."""

    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, verbose_name="工作空间id", db_index=True)
    alert = models.ForeignKey(
        MarketingAlert,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="actions",
        verbose_name="告警",
    )
    action = models.CharField(max_length=32, choices=MarketingAlertAction.choices, db_index=True)
    previous_status = models.CharField(max_length=32, default="", blank=True, verbose_name="处理前状态")
    current_status = models.CharField(max_length=32, verbose_name="处理后状态")
    operator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="+",
        blank=True,
        null=True,
        verbose_name="操作人",
    )
    operator_name = models.CharField(max_length=128, default="", blank=True, verbose_name="操作人名称")
    note = models.TextField(default="", blank=True, verbose_name="操作说明")
    snapshot = models.JSONField(default=dict, blank=True, verbose_name="操作快照")
    revision = models.PositiveIntegerField(default=1, verbose_name="操作版本")

    class Meta:
        db_table = "marketing_alert_action"
        ordering = ["-revision"]
        indexes = [models.Index(fields=["workspace_id", "action"], name="mkt_alert_action_ws")]
        constraints = [
            models.UniqueConstraint(fields=["alert", "revision"], name="mkt_alert_action_revision"),
        ]


class MarketingAlertHandlingRound(AppModelMixin):
    """One assignee's immutable ownership window for an alert."""

    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, verbose_name="工作空间id", db_index=True)
    alert = models.ForeignKey(
        MarketingAlert,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="handling_rounds",
        verbose_name="告警",
    )
    sequence = models.PositiveIntegerField(default=1, verbose_name="处理轮次")
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="+",
        blank=True,
        null=True,
        verbose_name="本轮负责人",
    )
    assignee_name = models.CharField(max_length=128, default="", blank=True, verbose_name="本轮负责人名称")
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="+",
        blank=True,
        null=True,
        verbose_name="指派人",
    )
    assigned_by_name = models.CharField(max_length=128, default="", blank=True, verbose_name="指派人名称")
    assigned_at = models.DateTimeField(verbose_name="指派时间")
    response_due_at = models.DateTimeField(blank=True, null=True, verbose_name="本轮响应截止时间")
    resolution_due_at = models.DateTimeField(blank=True, null=True, verbose_name="全局处理截止时间")
    first_responded_at = models.DateTimeField(blank=True, null=True, verbose_name="本轮首次响应时间")
    ended_at = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name="本轮结束时间")
    end_reason = models.CharField(
        max_length=32,
        choices=MarketingAlertRoundEndReason.choices,
        default="",
        blank=True,
        verbose_name="结束原因",
    )
    end_note = models.TextField(default="", blank=True, verbose_name="结束说明")

    class Meta:
        db_table = "marketing_alert_handling_round"
        ordering = ["-sequence"]
        indexes = [
            models.Index(fields=["workspace_id", "assignee", "assigned_at"], name="mkt_alert_round_owner"),
            models.Index(fields=["alert", "ended_at"], name="mkt_alert_round_active"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["alert", "sequence"], name="mkt_alert_round_sequence"),
        ]


class MarketingAlertSubscriber(AppModelMixin):
    """A workspace member receiving directed updates for one alert."""

    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, verbose_name="工作空间id", db_index=True)
    alert = models.ForeignKey(
        MarketingAlert,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="subscribers",
        verbose_name="告警",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="+",
        verbose_name="关注人",
    )
    user_name = models.CharField(max_length=128, default="", blank=True, verbose_name="关注人名称")
    subscribed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="+",
        blank=True,
        null=True,
        verbose_name="添加人",
    )
    subscribed_by_name = models.CharField(max_length=128, default="", blank=True, verbose_name="添加人名称")

    class Meta:
        db_table = "marketing_alert_subscriber"
        ordering = ["create_time"]
        indexes = [models.Index(fields=["workspace_id", "user"], name="mkt_alert_subscriber_ws")]
        constraints = [models.UniqueConstraint(fields=["alert", "user"], name="mkt_alert_subscriber_user")]


class MarketingAlertAttachment(AppModelMixin):
    """Metadata for a private alert attachment stored in the shared file repository."""

    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, verbose_name="工作空间id", db_index=True)
    alert = models.ForeignKey(
        MarketingAlert,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="attachments",
        verbose_name="告警",
    )
    action_record = models.ForeignKey(
        MarketingAlertActionRecord,
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="attachments",
        blank=True,
        null=True,
        verbose_name="时间线操作",
    )
    file_id = models.UUIDField(verbose_name="文件仓库id", unique=True)
    file_name = models.CharField(max_length=256, verbose_name="原始文件名")
    content_type = models.CharField(max_length=128, default="application/octet-stream", verbose_name="内容类型")
    file_size = models.PositiveIntegerField(default=0, verbose_name="原始文件大小")
    uploader = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="+",
        blank=True,
        null=True,
        verbose_name="上传人",
    )
    uploader_name = models.CharField(max_length=128, default="", blank=True, verbose_name="上传人名称")
    expires_at = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name="保留截止时间")

    class Meta:
        db_table = "marketing_alert_attachment"
        ordering = ["-create_time"]
        indexes = [models.Index(fields=["workspace_id", "alert"], name="mkt_alert_attachment_ws")]


class MarketingNotification(AppModelMixin):
    """Global in-app notification emitted from alerts, reports and other workspace events."""

    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, verbose_name="工作空间id", db_index=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="marketing_notifications",
        verbose_name="接收人",
    )
    alert = models.ForeignKey(
        MarketingAlert,
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="notifications",
        blank=True,
        null=True,
        verbose_name="关联告警",
    )
    action_record = models.ForeignKey(
        MarketingAlertActionRecord,
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="notifications",
        blank=True,
        null=True,
        verbose_name="关联告警操作",
    )
    source_type = models.CharField(max_length=32, default="ALERT", db_index=True, verbose_name="通知来源类型")
    source_id = models.CharField(max_length=128, default="", blank=True, db_index=True, verbose_name="来源业务id")
    title = models.CharField(max_length=160, verbose_name="通知标题")
    content = models.TextField(default="", blank=True, verbose_name="通知内容")
    severity = models.CharField(
        max_length=32,
        choices=MarketingAlertSeverity.choices,
        default=MarketingAlertSeverity.WARNING,
        db_index=True,
        verbose_name="通知级别",
    )
    status = models.CharField(
        max_length=32,
        choices=MarketingNotificationStatus.choices,
        default=MarketingNotificationStatus.UNREAD,
        db_index=True,
        verbose_name="阅读状态",
    )
    target_route = models.CharField(max_length=256, default="/marketing-operations", verbose_name="跳转页面")
    read_at = models.DateTimeField(blank=True, null=True, verbose_name="阅读时间")

    class Meta:
        db_table = "marketing_notification"
        ordering = ["-create_time"]
        indexes = [
            models.Index(fields=["workspace_id", "user", "status"], name="mkt_notice_ws_user_status"),
            models.Index(fields=["workspace_id", "source_type", "source_id"], name="mkt_notice_ws_source"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["user", "action_record"], name="mkt_notice_user_action"),
        ]
