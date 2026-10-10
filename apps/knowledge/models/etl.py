# coding=utf-8
import uuid_utils.compat as uuid
from django.db import models

from common.mixins.app_model_mixin import AppModelMixin
from users.models import User

from .knowledge import Knowledge


class KnowledgeEtlRunTrigger(models.TextChoices):
    MANUAL = "MANUAL", "手动执行"
    RETRY = "RETRY", "失败重试"


class KnowledgeEtlRunStatus(models.TextChoices):
    PENDING = "PENDING", "等待执行"
    RUNNING = "RUNNING", "执行中"
    WAITING_RELEASE = "WAITING_RELEASE", "等待发布"
    SUCCESS = "SUCCESS", "已发布"
    FAILED = "FAILED", "执行失败"


class KnowledgeEtlStage(models.TextChoices):
    PARSE = "PARSE", "文档解析"
    CLEAN = "CLEAN", "数据清洗"
    SPLIT = "SPLIT", "文本切分"
    VECTORIZE = "VECTORIZE", "向量化"
    QUALITY = "QUALITY", "质量门禁"
    VERSION = "VERSION", "索引版本"


class KnowledgeEtlStageStatus(models.TextChoices):
    PENDING = "PENDING", "等待执行"
    RUNNING = "RUNNING", "执行中"
    SUCCESS = "SUCCESS", "执行成功"
    FAILED = "FAILED", "执行失败"
    SKIPPED = "SKIPPED", "已跳过"


class KnowledgeIndexVersionStatus(models.TextChoices):
    CANDIDATE = "CANDIDATE", "候选版本"
    PUBLISHED = "PUBLISHED", "已发布"
    ARCHIVED = "ARCHIVED", "历史版本"


class KnowledgeIndexReleaseAction(models.TextChoices):
    PUBLISH = "PUBLISH", "发布"
    ROLLBACK = "ROLLBACK", "回滚"


class KnowledgeEtlRun(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    knowledge = models.ForeignKey(
        Knowledge,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="etl_runs",
        verbose_name="知识库",
    )
    run_number = models.PositiveIntegerField(verbose_name="运行序号")
    trigger = models.CharField(max_length=16, choices=KnowledgeEtlRunTrigger.choices, verbose_name="触发方式")
    status = models.CharField(
        max_length=24,
        choices=KnowledgeEtlRunStatus.choices,
        default=KnowledgeEtlRunStatus.PENDING,
        db_index=True,
        verbose_name="运行状态",
    )
    current_stage = models.CharField(
        max_length=16,
        choices=KnowledgeEtlStage.choices,
        default=KnowledgeEtlStage.PARSE,
        verbose_name="当前阶段",
    )
    document_ids = models.JSONField(default=list, verbose_name="文档范围")
    config_snapshot = models.JSONField(default=dict, verbose_name="配置快照")
    quality_result = models.JSONField(default=dict, verbose_name="质量结果")
    error_message = models.TextField(default="", blank=True, verbose_name="错误信息")
    retry_of = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        db_constraint=False,
        null=True,
        blank=True,
        related_name="retries",
        verbose_name="重试来源",
    )
    operator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        db_constraint=False,
        null=True,
        blank=True,
        related_name="knowledge_etl_runs",
        verbose_name="执行人",
    )
    operator_name = models.CharField(max_length=128, default="", blank=True, verbose_name="执行人名称")
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="开始时间")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="完成时间")

    class Meta:
        db_table = "knowledge_etl_run"
        ordering = ["-create_time"]
        constraints = [
            models.UniqueConstraint(fields=["knowledge", "run_number"], name="kb_etl_run_number"),
        ]
        indexes = [
            models.Index(fields=["workspace_id", "knowledge", "status"], name="kb_etl_ws_kb_status"),
        ]


class KnowledgeEtlStageRun(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    etl_run = models.ForeignKey(
        KnowledgeEtlRun,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="stage_runs",
        verbose_name="ETL运行",
    )
    stage = models.CharField(max_length=16, choices=KnowledgeEtlStage.choices, verbose_name="执行阶段")
    sequence = models.PositiveSmallIntegerField(verbose_name="执行顺序")
    status = models.CharField(
        max_length=16,
        choices=KnowledgeEtlStageStatus.choices,
        default=KnowledgeEtlStageStatus.PENDING,
        db_index=True,
        verbose_name="阶段状态",
    )
    input_snapshot = models.JSONField(default=dict, verbose_name="阶段输入")
    output_snapshot = models.JSONField(default=dict, verbose_name="阶段输出")
    error_message = models.TextField(default="", blank=True, verbose_name="错误信息")
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="开始时间")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="完成时间")

    class Meta:
        db_table = "knowledge_etl_stage_run"
        ordering = ["sequence"]
        constraints = [
            models.UniqueConstraint(fields=["etl_run", "stage"], name="kb_etl_run_stage"),
        ]


class KnowledgeIndexVersion(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    knowledge = models.ForeignKey(
        Knowledge,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="index_versions",
        verbose_name="知识库",
    )
    version = models.PositiveIntegerField(verbose_name="版本号")
    status = models.CharField(
        max_length=16,
        choices=KnowledgeIndexVersionStatus.choices,
        default=KnowledgeIndexVersionStatus.CANDIDATE,
        db_index=True,
        verbose_name="版本状态",
    )
    source_run = models.OneToOneField(
        KnowledgeEtlRun,
        on_delete=models.PROTECT,
        db_constraint=False,
        related_name="index_version",
        verbose_name="来源运行",
    )
    document_ids = models.JSONField(default=list, verbose_name="文档范围")
    document_count = models.PositiveIntegerField(default=0, verbose_name="文档数")
    paragraph_count = models.PositiveIntegerField(default=0, verbose_name="段落数")
    embedding_count = models.PositiveIntegerField(default=0, verbose_name="向量数")
    embedding_model_id_snapshot = models.CharField(max_length=64, default="", blank=True, verbose_name="向量模型快照")
    embedding_model_name = models.CharField(max_length=128, default="", blank=True, verbose_name="向量模型名称")
    content_digest = models.CharField(max_length=64, db_index=True, verbose_name="内容摘要")
    quality_result = models.JSONField(default=dict, verbose_name="质量结果")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="发布时间")

    class Meta:
        db_table = "knowledge_index_version"
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(fields=["knowledge", "version"], name="kb_index_version_number"),
        ]
        indexes = [
            models.Index(fields=["workspace_id", "knowledge", "status"], name="kb_index_ws_kb_status"),
        ]


class KnowledgeIndexReleaseRecord(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    knowledge = models.ForeignKey(
        Knowledge,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="index_releases",
        verbose_name="知识库",
    )
    action = models.CharField(max_length=16, choices=KnowledgeIndexReleaseAction.choices, verbose_name="发布动作")
    from_version = models.ForeignKey(
        KnowledgeIndexVersion,
        on_delete=models.SET_NULL,
        db_constraint=False,
        null=True,
        blank=True,
        related_name="releases_from",
        verbose_name="原版本",
    )
    target_version = models.ForeignKey(
        KnowledgeIndexVersion,
        on_delete=models.PROTECT,
        db_constraint=False,
        related_name="releases_to",
        verbose_name="目标版本",
    )
    reason = models.CharField(max_length=512, default="", blank=True, verbose_name="操作原因")
    operator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        db_constraint=False,
        null=True,
        blank=True,
        related_name="knowledge_index_releases",
        verbose_name="操作人",
    )
    operator_name = models.CharField(max_length=128, default="", blank=True, verbose_name="操作人名称")

    class Meta:
        db_table = "knowledge_index_release_record"
        ordering = ["-create_time"]
        indexes = [
            models.Index(fields=["workspace_id", "knowledge", "action"], name="kb_index_release_ws_kb"),
        ]
