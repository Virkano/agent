import uuid_utils.compat as uuid
from common.mixins.app_model_mixin import AppModelMixin
from django.db import models
from models_provider.models import Model
from users.models import User

from .knowledge import Document, Knowledge, Paragraph


class KnowledgeEvaluationRunStatus(models.TextChoices):
    RUNNING = "RUNNING", "执行中"
    SUCCESS = "SUCCESS", "已完成"
    PARTIAL = "PARTIAL", "部分失败"
    FAILED = "FAILED", "执行失败"


class KnowledgeEvaluationCase(AppModelMixin):
    """Expected retrieval target used to evaluate a knowledge base."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, db_index=True, verbose_name="工作空间id")
    knowledge = models.ForeignKey(
        Knowledge,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="evaluation_cases",
        verbose_name="知识库",
    )
    question = models.CharField(max_length=1000, verbose_name="评估问题")
    expected_document = models.ForeignKey(
        Document,
        on_delete=models.SET_NULL,
        db_constraint=False,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="期望命中文档",
    )
    expected_paragraph = models.ForeignKey(
        Paragraph,
        on_delete=models.SET_NULL,
        db_constraint=False,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="期望命中段落",
    )
    expected_answer = models.TextField(default="", blank=True, verbose_name="期望答案")
    enabled = models.BooleanField(default=True, db_index=True, verbose_name="是否启用")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = "knowledge_evaluation_case"
        ordering = ["-update_time"]
        indexes = [
            models.Index(fields=["workspace_id", "knowledge", "enabled"], name="kb_eval_case_ws_kb_enabled"),
        ]


class KnowledgeEvaluationRun(AppModelMixin):
    """One immutable batch evaluation across one or more retrieval modes."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, db_index=True, verbose_name="工作空间id")
    knowledge = models.ForeignKey(
        Knowledge,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="evaluation_runs",
        verbose_name="知识库",
    )
    status = models.CharField(
        max_length=20,
        choices=KnowledgeEvaluationRunStatus.choices,
        default=KnowledgeEvaluationRunStatus.RUNNING,
        db_index=True,
        verbose_name="执行状态",
    )
    search_modes = models.JSONField(default=list, verbose_name="检索模式")
    top_number = models.PositiveIntegerField(default=5, verbose_name="召回数量")
    similarity = models.FloatField(default=0.0, verbose_name="相似度阈值")
    reranker_model = models.ForeignKey(
        Model,
        on_delete=models.SET_NULL,
        db_constraint=False,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="重排模型",
    )
    summary = models.JSONField(default=dict, verbose_name="评估汇总")
    error_message = models.TextField(default="", blank=True, verbose_name="错误信息")
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="开始时间")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="完成时间")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True)
    user_name = models.CharField(max_length=128, default="", blank=True, verbose_name="执行人")

    class Meta:
        db_table = "knowledge_evaluation_run"
        ordering = ["-create_time"]
        indexes = [
            models.Index(fields=["workspace_id", "knowledge", "status"], name="kb_eval_run_ws_kb_status"),
        ]


class KnowledgeEvaluationResult(AppModelMixin):
    """Per-case, per-mode result snapshot retained with its evaluation run."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, db_index=True, verbose_name="工作空间id")
    run = models.ForeignKey(
        KnowledgeEvaluationRun,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="results",
        verbose_name="评估执行",
    )
    case = models.ForeignKey(
        KnowledgeEvaluationCase,
        on_delete=models.SET_NULL,
        db_constraint=False,
        null=True,
        blank=True,
        related_name="results",
        verbose_name="评估样本",
    )
    mode = models.CharField(max_length=20, db_index=True, verbose_name="检索模式")
    question = models.CharField(max_length=1000, verbose_name="问题快照")
    expected_document_id_snapshot = models.CharField(max_length=64, default="", blank=True)
    expected_document_name = models.CharField(max_length=150, default="", blank=True)
    expected_paragraph_id_snapshot = models.CharField(max_length=64, default="", blank=True)
    expected_answer = models.TextField(default="", blank=True)
    hit = models.BooleanField(default=False, db_index=True, verbose_name="是否命中")
    expected_rank = models.PositiveIntegerField(null=True, blank=True, verbose_name="期望结果排名")
    latency_ms = models.PositiveIntegerField(default=0, verbose_name="耗时毫秒")
    top_score = models.FloatField(default=0.0, verbose_name="最高分")
    matches = models.JSONField(default=list, verbose_name="召回结果")
    error_message = models.TextField(default="", blank=True, verbose_name="错误信息")

    class Meta:
        db_table = "knowledge_evaluation_result"
        ordering = ["mode", "create_time"]
        constraints = [
            models.UniqueConstraint(fields=["run", "case", "mode"], name="kb_eval_result_run_case_mode"),
        ]
        indexes = [
            models.Index(fields=["workspace_id", "run", "mode", "hit"], name="kb_eval_result_ws_run_mode"),
        ]

