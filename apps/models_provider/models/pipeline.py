# coding=utf-8
import uuid_utils.compat as uuid
from django.db import models

from common.mixins.app_model_mixin import AppModelMixin
from users.models import User


class ModelPipelineApprovalMode(models.TextChoices):
    AUTO = "AUTO", "自动审批"
    MANUAL = "MANUAL", "人工审批"


class ModelPipelineRunTrigger(models.TextChoices):
    MANUAL = "MANUAL", "手动运行"
    SCHEDULED = "SCHEDULED", "定时重训"
    RETRY = "RETRY", "失败重试"


class ModelPipelineRunStatus(models.TextChoices):
    PENDING = "PENDING", "等待执行"
    RUNNING = "RUNNING", "运行中"
    WAITING_APPROVAL = "WAITING_APPROVAL", "等待审批"
    SUCCESS = "SUCCESS", "执行成功"
    FAILED = "FAILED", "执行失败"
    REJECTED = "REJECTED", "审批拒绝"


class ModelPipelineStage(models.TextChoices):
    FEATURE = "FEATURE", "特征处理"
    TRAIN = "TRAIN", "模型训练"
    EVALUATE = "EVALUATE", "模型评估"
    APPROVE = "APPROVE", "发布审批"
    DEPLOY = "DEPLOY", "模型部署"


class ModelPipelineStageStatus(models.TextChoices):
    PENDING = "PENDING", "等待执行"
    RUNNING = "RUNNING", "运行中"
    SUCCESS = "SUCCESS", "执行成功"
    FAILED = "FAILED", "执行失败"
    SKIPPED = "SKIPPED", "已跳过"


class ModelTrainingPipeline(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    name = models.CharField(max_length=128, verbose_name="流水线名称")
    description = models.TextField(default="", blank=True, verbose_name="流水线说明")
    registry_name = models.CharField(max_length=128, db_index=True, verbose_name="注册模型名称")
    dataset_name = models.CharField(max_length=128, verbose_name="数据集名称")
    dataset_version = models.CharField(max_length=64, default="", blank=True, verbose_name="数据集版本")
    parameters = models.JSONField(default=dict, blank=True, verbose_name="训练参数")
    evaluation_metrics = models.JSONField(default=dict, blank=True, verbose_name="默认评估指标")
    thresholds = models.JSONField(default=dict, blank=True, verbose_name="发布准入阈值")
    artifact_uri_template = models.CharField(
        max_length=512,
        default="local://model-pipeline/{pipeline_id}/run-{run_number}",
        verbose_name="模型产物地址模板",
    )
    approval_mode = models.CharField(
        max_length=16,
        choices=ModelPipelineApprovalMode.choices,
        default=ModelPipelineApprovalMode.MANUAL,
        verbose_name="审批模式",
    )
    auto_deploy = models.BooleanField(default=True, verbose_name="审批后自动部署")
    active = models.BooleanField(default=True, db_index=True, verbose_name="是否启用")
    schedule_enabled = models.BooleanField(default=False, db_index=True, verbose_name="是否启用定时重训")
    cron_expression = models.CharField(max_length=128, default="", blank=True, verbose_name="Cron表达式")
    next_run_at = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name="下次执行时间")
    last_run_at = models.DateTimeField(blank=True, null=True, verbose_name="最近执行时间")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="created_model_pipelines",
        verbose_name="创建人",
    )

    class Meta:
        db_table = "model_training_pipeline"
        ordering = ["-update_time"]
        constraints = [
            models.UniqueConstraint(fields=["workspace_id", "name"], name="model_pipeline_ws_name"),
        ]


class ModelPipelineRun(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    pipeline = models.ForeignKey(
        ModelTrainingPipeline,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="runs",
        verbose_name="训练流水线",
    )
    run_number = models.PositiveIntegerField(verbose_name="运行序号")
    trigger = models.CharField(max_length=16, choices=ModelPipelineRunTrigger.choices, verbose_name="触发方式")
    status = models.CharField(
        max_length=24,
        choices=ModelPipelineRunStatus.choices,
        default=ModelPipelineRunStatus.PENDING,
        db_index=True,
        verbose_name="运行状态",
    )
    current_stage = models.CharField(
        max_length=16,
        choices=ModelPipelineStage.choices,
        default=ModelPipelineStage.FEATURE,
        verbose_name="当前阶段",
    )
    config_snapshot = models.JSONField(default=dict, blank=True, verbose_name="运行配置快照")
    error_message = models.TextField(default="", blank=True, verbose_name="错误信息")
    experiment = models.ForeignKey(
        "models_provider.ModelExperiment",
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="pipeline_runs",
        verbose_name="模型实验",
    )
    model_version = models.ForeignKey(
        "models_provider.LifecycleModelVersion",
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="pipeline_runs",
        verbose_name="模型版本",
    )
    operator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="model_pipeline_runs",
        verbose_name="触发人",
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="approved_model_pipeline_runs",
        verbose_name="审批人",
    )
    approval_comment = models.CharField(max_length=512, default="", blank=True, verbose_name="审批意见")
    approved_at = models.DateTimeField(blank=True, null=True, verbose_name="审批时间")
    started_at = models.DateTimeField(blank=True, null=True, verbose_name="开始时间")
    finished_at = models.DateTimeField(blank=True, null=True, verbose_name="完成时间")

    class Meta:
        db_table = "model_pipeline_run"
        ordering = ["-create_time"]
        constraints = [
            models.UniqueConstraint(fields=["pipeline", "run_number"], name="model_pipeline_run_number"),
        ]
        indexes = [
            models.Index(fields=["workspace_id", "status"], name="model_pipe_run_ws_status"),
        ]


class ModelPipelineStageRun(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    pipeline_run = models.ForeignKey(
        ModelPipelineRun,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="stage_runs",
        verbose_name="流水线运行",
    )
    stage = models.CharField(max_length=16, choices=ModelPipelineStage.choices, verbose_name="流水线阶段")
    sequence = models.PositiveSmallIntegerField(verbose_name="执行顺序")
    status = models.CharField(
        max_length=16,
        choices=ModelPipelineStageStatus.choices,
        default=ModelPipelineStageStatus.PENDING,
        db_index=True,
        verbose_name="阶段状态",
    )
    input_snapshot = models.JSONField(default=dict, blank=True, verbose_name="阶段输入")
    output_snapshot = models.JSONField(default=dict, blank=True, verbose_name="阶段输出")
    error_message = models.TextField(default="", blank=True, verbose_name="错误信息")
    started_at = models.DateTimeField(blank=True, null=True, verbose_name="开始时间")
    finished_at = models.DateTimeField(blank=True, null=True, verbose_name="完成时间")

    class Meta:
        db_table = "model_pipeline_stage_run"
        ordering = ["sequence"]
        constraints = [
            models.UniqueConstraint(fields=["pipeline_run", "stage"], name="model_pipe_run_stage"),
        ]
