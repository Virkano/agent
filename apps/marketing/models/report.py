# coding=utf-8
import uuid_utils.compat as uuid
from django.db import models

from common.mixins.app_model_mixin import AppModelMixin
from users.models import User


class MarketingReportStatus(models.TextChoices):
    PENDING = "PENDING", "待生成"
    RUNNING = "RUNNING", "生成中"
    SUCCESS = "SUCCESS", "已完成"
    FAILED = "FAILED", "生成失败"


class MarketingAttributionMethod(models.TextChoices):
    LAST_TOUCH = "LAST_TOUCH", "最终点击"
    LINEAR = "LINEAR", "线性归因"


class MarketingReportSubscriptionFrequency(models.TextChoices):
    DAILY = "DAILY", "每天"
    WEEKLY = "WEEKLY", "每周"
    MONTHLY = "MONTHLY", "每月"


class MarketingReportDeliveryChannel(models.TextChoices):
    IN_APP = "IN_APP", "站内通知"
    EMAIL = "EMAIL", "邮件"


class MarketingReportDeliveryStatus(models.TextChoices):
    SUCCESS = "SUCCESS", "成功"
    FAILED = "FAILED", "失败"


class MarketingReportTemplate(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)
    name = models.CharField(max_length=128, verbose_name="模板名称")
    description = models.TextField(default="", blank=True, verbose_name="模板说明")
    title_template = models.CharField(
        max_length=256,
        default="{start_date} 至 {end_date} 营销分析报告",
        verbose_name="标题模板",
    )
    narrative_prompt = models.TextField(
        default=(
            "你是电信营销分析师。请根据指标数据输出一段简洁、客观、可执行的中文经营分析，"
            "依次说明核心表现、主要问题和下一步建议。不要虚构数据。"
        ),
        verbose_name="智能解读提示词",
    )
    config = models.JSONField(default=dict, blank=True, verbose_name="模板配置")
    active = models.BooleanField(default=True, db_index=True, verbose_name="是否启用")
    version = models.PositiveIntegerField(default=1, verbose_name="模板版本")

    class Meta:
        db_table = "marketing_report_template"
        ordering = ["-update_time"]
        constraints = [
            models.UniqueConstraint(fields=["workspace_id", "name"], name="mkt_report_tpl_ws_name"),
        ]


class MarketingAnalysisReport(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    template = models.ForeignKey(
        MarketingReportTemplate,
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="reports",
        blank=True,
        null=True,
        verbose_name="报告模板",
    )
    task = models.ForeignKey(
        "marketing.MarketingTask",
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="analysis_reports",
        blank=True,
        null=True,
        verbose_name="营销任务",
    )
    model = models.ForeignKey(
        "models_provider.Model",
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="marketing_analysis_reports",
        blank=True,
        null=True,
        verbose_name="分析模型",
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)
    title = models.CharField(max_length=256, verbose_name="报告标题")
    period_start = models.DateField(verbose_name="统计开始日期", db_index=True)
    period_end = models.DateField(verbose_name="统计结束日期", db_index=True)
    attribution_method = models.CharField(
        max_length=32,
        choices=MarketingAttributionMethod.choices,
        default=MarketingAttributionMethod.LAST_TOUCH,
        db_index=True,
        verbose_name="归因方式",
    )
    status = models.CharField(
        max_length=32,
        choices=MarketingReportStatus.choices,
        default=MarketingReportStatus.PENDING,
        db_index=True,
        verbose_name="生成状态",
    )
    input_snapshot = models.JSONField(default=dict, blank=True, verbose_name="生成参数快照")
    metrics = models.JSONField(default=dict, blank=True, verbose_name="指标快照")
    narrative = models.TextField(default="", blank=True, verbose_name="智能解读")
    html_content = models.TextField(default="", blank=True, verbose_name="HTML报告内容")
    error_message = models.TextField(default="", blank=True, verbose_name="失败原因")
    retry_count = models.PositiveIntegerField(default=0, verbose_name="重试次数")
    generated_at = models.DateTimeField(blank=True, null=True, verbose_name="生成完成时间")

    class Meta:
        db_table = "marketing_analysis_report"
        ordering = ["-create_time"]
        indexes = [
            models.Index(fields=["workspace_id", "status", "create_time"], name="mkt_report_ws_status_time"),
            models.Index(fields=["workspace_id", "task", "period_end"], name="mkt_report_ws_task_period"),
        ]


class MarketingReportGenerationRun(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    report = models.ForeignKey(
        MarketingAnalysisReport,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="runs",
        verbose_name="分析报告",
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)
    attempt = models.PositiveIntegerField(default=1, verbose_name="尝试次数")
    status = models.CharField(
        max_length=32,
        choices=MarketingReportStatus.choices,
        default=MarketingReportStatus.RUNNING,
        db_index=True,
        verbose_name="运行状态",
    )
    input_snapshot = models.JSONField(default=dict, blank=True, verbose_name="输入快照")
    metrics_snapshot = models.JSONField(default=dict, blank=True, verbose_name="指标快照")
    prompt = models.TextField(default="", blank=True, verbose_name="模型提示词")
    raw_output = models.TextField(default="", blank=True, verbose_name="模型原始输出")
    error_message = models.TextField(default="", blank=True, verbose_name="失败原因")
    started_at = models.DateTimeField(blank=True, null=True, verbose_name="开始时间")
    finished_at = models.DateTimeField(blank=True, null=True, verbose_name="结束时间")

    class Meta:
        db_table = "marketing_report_generation_run"
        ordering = ["-attempt"]
        constraints = [
            models.UniqueConstraint(fields=["report", "attempt"], name="mkt_report_run_attempt"),
        ]


class MarketingReportAttributionDetail(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    report = models.ForeignKey(
        MarketingAnalysisReport,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="attribution_details",
        verbose_name="分析报告",
    )
    conversion = models.ForeignKey(
        "marketing.MarketingConversionRecord",
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="report_attributions",
        verbose_name="确认转化",
    )
    customer = models.ForeignKey(
        "marketing.MarketingCustomer",
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="report_attributions",
        verbose_name="营销客户",
    )
    batch = models.ForeignKey(
        "marketing.MarketingTouchBatch",
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="report_attributions",
        blank=True,
        null=True,
        verbose_name="归因触达批次",
    )
    method = models.CharField(max_length=32, choices=MarketingAttributionMethod.choices, db_index=True)
    channel = models.CharField(max_length=64, default="", blank=True, verbose_name="归因渠道")
    weight = models.DecimalField(max_digits=9, decimal_places=6, default=0, verbose_name="归因权重")
    attributed_revenue = models.DecimalField(max_digits=16, decimal_places=2, default=0, verbose_name="归因收入")
    touch_time = models.DateTimeField(blank=True, null=True, verbose_name="归因触达时间")

    class Meta:
        db_table = "marketing_report_attribution_detail"
        ordering = ["conversion_id", "-weight", "touch_time"]
        indexes = [models.Index(fields=["workspace_id", "report", "method"], name="mkt_attr_ws_report_method")]


class MarketingReportSubscription(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="marketing_report_subscriptions",
        verbose_name="订阅人",
    )
    name = models.CharField(max_length=128, verbose_name="订阅名称")
    template = models.ForeignKey(
        MarketingReportTemplate,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="subscriptions",
        verbose_name="报告模板",
    )
    task = models.ForeignKey(
        "marketing.MarketingTask",
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="report_subscriptions",
        blank=True,
        null=True,
        verbose_name="营销任务",
    )
    model = models.ForeignKey(
        "models_provider.Model",
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="marketing_report_subscriptions",
        blank=True,
        null=True,
        verbose_name="智能解读模型",
    )
    frequency = models.CharField(
        max_length=16,
        choices=MarketingReportSubscriptionFrequency.choices,
        default=MarketingReportSubscriptionFrequency.WEEKLY,
        db_index=True,
    )
    run_time = models.TimeField(default="09:00", verbose_name="执行时间")
    weekday = models.PositiveSmallIntegerField(default=0, verbose_name="周几执行")
    month_day = models.PositiveSmallIntegerField(default=1, verbose_name="每月几号执行")
    period_days = models.PositiveSmallIntegerField(default=7, verbose_name="报告统计天数")
    attribution_method = models.CharField(
        max_length=32,
        choices=MarketingAttributionMethod.choices,
        default=MarketingAttributionMethod.LAST_TOUCH,
        verbose_name="归因方式",
    )
    use_llm = models.BooleanField(default=False, verbose_name="启用智能解读")
    email_enabled = models.BooleanField(default=False, verbose_name="启用邮件")
    recipient_emails = models.JSONField(default=list, blank=True, verbose_name="邮件接收人")
    enabled = models.BooleanField(default=True, db_index=True, verbose_name="是否启用")
    next_run_at = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name="下次执行时间")
    last_run_at = models.DateTimeField(blank=True, null=True, verbose_name="最近执行时间")
    last_status = models.CharField(max_length=32, default="", blank=True, verbose_name="最近执行状态")
    last_error = models.TextField(default="", blank=True, verbose_name="最近错误")
    last_report = models.ForeignKey(
        MarketingAnalysisReport,
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="generated_by_subscriptions",
        blank=True,
        null=True,
        verbose_name="最近报告",
    )

    class Meta:
        db_table = "marketing_report_subscription"
        ordering = ["-update_time"]
        constraints = [
            models.UniqueConstraint(fields=["workspace_id", "name"], name="mkt_report_sub_ws_name"),
        ]


class MarketingReportDelivery(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    report = models.ForeignKey(
        MarketingAnalysisReport,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="deliveries",
        verbose_name="分析报告",
    )
    subscription = models.ForeignKey(
        MarketingReportSubscription,
        on_delete=models.SET_NULL,
        db_constraint=False,
        related_name="deliveries",
        blank=True,
        null=True,
        verbose_name="报告订阅",
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)
    channel = models.CharField(max_length=16, choices=MarketingReportDeliveryChannel.choices, db_index=True)
    status = models.CharField(max_length=16, choices=MarketingReportDeliveryStatus.choices, db_index=True)
    recipient = models.CharField(max_length=256, default="", blank=True, verbose_name="接收人")
    file_name = models.CharField(max_length=256, default="", blank=True, verbose_name="文件名")
    content_type = models.CharField(max_length=128, default="", blank=True, verbose_name="内容类型")
    error_message = models.TextField(default="", blank=True, verbose_name="失败原因")
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name="发送时间")

    class Meta:
        db_table = "marketing_report_delivery"
        ordering = ["-create_time"]
        indexes = [models.Index(fields=["workspace_id", "report", "channel"], name="mkt_delivery_ws_report")]
