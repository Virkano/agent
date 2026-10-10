# coding=utf-8
import uuid_utils.compat as uuid
from django.db import models

from common.mixins.app_model_mixin import AppModelMixin
from users.models import User


class ModelExperimentStatus(models.TextChoices):
    DRAFT = "DRAFT", "草稿"
    RUNNING = "RUNNING", "运行中"
    SUCCESS = "SUCCESS", "已完成"
    FAILED = "FAILED", "失败"
    CANCELLED = "CANCELLED", "已取消"


class LifecycleModelVersionStatus(models.TextChoices):
    REGISTERED = "REGISTERED", "已注册"
    EVALUATING = "EVALUATING", "评估中"
    APPROVED = "APPROVED", "评估通过"
    REJECTED = "REJECTED", "评估未通过"
    PUBLISHED = "PUBLISHED", "已发布"
    ARCHIVED = "ARCHIVED", "已归档"


class ModelEvaluationStatus(models.TextChoices):
    PENDING = "PENDING", "待评估"
    RUNNING = "RUNNING", "评估中"
    PASSED = "PASSED", "通过"
    FAILED = "FAILED", "未通过"
    ERROR = "ERROR", "执行异常"


class ModelReleaseAction(models.TextChoices):
    PUBLISH = "PUBLISH", "发布"
    ROLLBACK = "ROLLBACK", "回滚"


class ModelReleaseStatus(models.TextChoices):
    SUCCESS = "SUCCESS", "成功"
    FAILED = "FAILED", "失败"


class ModelExperiment(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    name = models.CharField(max_length=128, verbose_name="实验名称")
    description = models.TextField(default="", blank=True, verbose_name="实验说明")
    status = models.CharField(
        max_length=20,
        choices=ModelExperimentStatus.choices,
        default=ModelExperimentStatus.DRAFT,
        db_index=True,
        verbose_name="实验状态",
    )
    source_type = models.CharField(max_length=32, default="MANUAL", verbose_name="实验来源")
    dataset_name = models.CharField(max_length=128, default="", blank=True, verbose_name="数据集名称")
    dataset_version = models.CharField(max_length=64, default="", blank=True, verbose_name="数据集版本")
    parameters = models.JSONField(default=dict, blank=True, verbose_name="实验参数")
    tags = models.JSONField(default=dict, blank=True, verbose_name="实验标签")
    external_run_id = models.CharField(max_length=128, default="", blank=True, db_index=True, verbose_name="外部运行id")
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="model_experiments",
        verbose_name="创建人",
    )
    started_at = models.DateTimeField(blank=True, null=True, verbose_name="开始时间")
    finished_at = models.DateTimeField(blank=True, null=True, verbose_name="结束时间")

    class Meta:
        db_table = "model_lifecycle_experiment"
        ordering = ["-update_time"]
        constraints = [
            models.UniqueConstraint(fields=["workspace_id", "name"], name="model_exp_ws_name"),
        ]


class LifecycleModelVersion(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    registry_name = models.CharField(max_length=128, db_index=True, verbose_name="注册模型名称")
    version = models.PositiveIntegerField(verbose_name="版本号")
    status = models.CharField(
        max_length=20,
        choices=LifecycleModelVersionStatus.choices,
        default=LifecycleModelVersionStatus.REGISTERED,
        db_index=True,
        verbose_name="版本状态",
    )
    experiment = models.ForeignKey(
        ModelExperiment,
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="model_versions",
        verbose_name="来源实验",
    )
    provider_model = models.ForeignKey(
        "models_provider.Model",
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="lifecycle_versions",
        verbose_name="关联在线模型",
    )
    artifact_uri = models.CharField(max_length=512, default="", blank=True, verbose_name="模型产物地址")
    artifact_digest = models.CharField(max_length=128, default="", blank=True, verbose_name="产物摘要")
    dataset_version = models.CharField(max_length=64, default="", blank=True, verbose_name="数据集版本")
    parameters = models.JSONField(default=dict, blank=True, verbose_name="模型参数")
    metrics = models.JSONField(default=dict, blank=True, verbose_name="训练指标")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="created_model_versions",
        verbose_name="注册人",
    )
    published_at = models.DateTimeField(blank=True, null=True, verbose_name="发布时间")

    class Meta:
        db_table = "model_lifecycle_version"
        ordering = ["registry_name", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "registry_name", "version"],
                name="model_version_ws_registry_version",
            ),
        ]
        indexes = [
            models.Index(fields=["workspace_id", "registry_name", "status"], name="model_ver_ws_name_status"),
        ]


class ModelEvaluationRun(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    model_version = models.ForeignKey(
        LifecycleModelVersion,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="evaluations",
        verbose_name="模型版本",
    )
    dataset_name = models.CharField(max_length=128, verbose_name="评估集名称")
    dataset_version = models.CharField(max_length=64, default="", blank=True, verbose_name="评估集版本")
    status = models.CharField(
        max_length=20,
        choices=ModelEvaluationStatus.choices,
        default=ModelEvaluationStatus.PENDING,
        db_index=True,
        verbose_name="评估状态",
    )
    metrics = models.JSONField(default=dict, blank=True, verbose_name="评估指标")
    thresholds = models.JSONField(default=dict, blank=True, verbose_name="准入阈值")
    summary = models.TextField(default="", blank=True, verbose_name="评估说明")
    evaluated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="model_evaluations",
        verbose_name="评估人",
    )
    started_at = models.DateTimeField(blank=True, null=True, verbose_name="开始时间")
    finished_at = models.DateTimeField(blank=True, null=True, verbose_name="结束时间")

    class Meta:
        db_table = "model_lifecycle_evaluation"
        ordering = ["-create_time"]
        indexes = [
            models.Index(fields=["workspace_id", "status"], name="model_eval_ws_status"),
        ]


class ModelReleaseRecord(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    registry_name = models.CharField(max_length=128, db_index=True, verbose_name="注册模型名称")
    action = models.CharField(max_length=20, choices=ModelReleaseAction.choices, verbose_name="发布动作")
    status = models.CharField(
        max_length=20,
        choices=ModelReleaseStatus.choices,
        default=ModelReleaseStatus.SUCCESS,
        db_index=True,
        verbose_name="执行状态",
    )
    from_version = models.ForeignKey(
        LifecycleModelVersion,
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="release_records_as_source",
        verbose_name="原版本",
    )
    target_version = models.ForeignKey(
        LifecycleModelVersion,
        on_delete=models.PROTECT,
        db_constraint=False,
        related_name="release_records_as_target",
        verbose_name="目标版本",
    )
    reason = models.CharField(max_length=512, default="", blank=True, verbose_name="发布或回滚原因")
    details = models.JSONField(default=dict, blank=True, verbose_name="执行详情")
    operator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="model_release_records",
        verbose_name="操作人",
    )

    class Meta:
        db_table = "model_lifecycle_release_record"
        ordering = ["-create_time"]
        indexes = [
            models.Index(fields=["workspace_id", "registry_name", "action"], name="model_rel_ws_name_action"),
        ]
