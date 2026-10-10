# coding=utf-8
import uuid_utils.compat as uuid
from django.db import models

from common.mixins.app_model_mixin import AppModelMixin
from users.models import User


class RecommendationFeatureType(models.TextChoices):
    USER = "USER", "用户特征"
    ITEM = "ITEM", "物料特征"


class RecommendationTrainingStatus(models.TextChoices):
    PENDING = "PENDING", "待训练"
    RUNNING = "RUNNING", "训练中"
    SUCCESS = "SUCCESS", "已完成"
    FAILED = "FAILED", "失败"


class RecommendationModelStatus(models.TextChoices):
    TRAINED = "TRAINED", "待发布"
    PUBLISHED = "PUBLISHED", "已发布"
    ARCHIVED = "ARCHIVED", "已归档"


class RecommendationRankingStatus(models.TextChoices):
    DRAFT = "DRAFT", "草稿"
    PUBLISHED = "PUBLISHED", "已发布"
    ARCHIVED = "ARCHIVED", "已归档"


class RecommendationFeedbackType(models.TextChoices):
    EXPOSED = "EXPOSED", "已曝光"
    CLICKED = "CLICKED", "已点击"
    CONVERTED = "CONVERTED", "已转化"
    NEGATIVE = "NEGATIVE", "负反馈"


class RecommendationIncrementalStatus(models.TextChoices):
    RUNNING = "RUNNING", "训练中"
    SUCCESS = "SUCCESS", "已完成"
    FAILED = "FAILED", "失败"


class RecommendationFeatureSnapshot(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    snapshot_version = models.PositiveIntegerField(db_index=True, verbose_name="快照版本")
    feature_type = models.CharField(max_length=16, choices=RecommendationFeatureType.choices, db_index=True)
    source_id = models.CharField(max_length=64, db_index=True, verbose_name="来源对象id")
    source_name = models.CharField(max_length=128, default="", blank=True, verbose_name="来源对象名称")
    feature_payload = models.JSONField(default=dict, verbose_name="原始特征")
    input_vector = models.JSONField(default=list, verbose_name="哈希输入向量")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)

    class Meta:
        db_table = "recommendation_feature_snapshot"
        ordering = ["feature_type", "source_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "snapshot_version", "feature_type", "source_id"],
                name="rec_feature_ws_ver_type_source",
            )
        ]
        indexes = [
            models.Index(
                fields=["workspace_id", "feature_type", "snapshot_version"],
                name="rec_feature_ws_type_ver",
            )
        ]


class RecommendationTrainingRun(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    name = models.CharField(max_length=128, verbose_name="训练任务名称")
    snapshot_version = models.PositiveIntegerField(verbose_name="特征快照版本")
    status = models.CharField(
        max_length=16,
        choices=RecommendationTrainingStatus.choices,
        default=RecommendationTrainingStatus.PENDING,
        db_index=True,
    )
    input_dim = models.PositiveIntegerField(default=64, verbose_name="输入维度")
    embedding_dim = models.PositiveIntegerField(default=16, verbose_name="向量维度")
    epochs = models.PositiveIntegerField(default=40, verbose_name="训练轮数")
    learning_rate = models.FloatField(default=0.03, verbose_name="学习率")
    user_count = models.PositiveIntegerField(default=0, verbose_name="用户数")
    item_count = models.PositiveIntegerField(default=0, verbose_name="物料数")
    sample_count = models.PositiveIntegerField(default=0, verbose_name="样本数")
    positive_count = models.PositiveIntegerField(default=0, verbose_name="正样本数")
    initial_loss = models.FloatField(blank=True, null=True, verbose_name="初始损失")
    final_loss = models.FloatField(blank=True, null=True, verbose_name="最终损失")
    metrics = models.JSONField(default=dict, blank=True, verbose_name="训练指标")
    model_artifact = models.JSONField(default=dict, blank=True, verbose_name="模型参数")
    error_message = models.TextField(default="", blank=True, verbose_name="错误信息")
    started_at = models.DateTimeField(blank=True, null=True, verbose_name="开始时间")
    finished_at = models.DateTimeField(blank=True, null=True, verbose_name="结束时间")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)

    class Meta:
        db_table = "recommendation_training_run"
        ordering = ["-create_time"]


class RecommendationModelVersion(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    version = models.PositiveIntegerField(verbose_name="模型版本")
    name = models.CharField(max_length=128, verbose_name="模型名称")
    status = models.CharField(
        max_length=16,
        choices=RecommendationModelStatus.choices,
        default=RecommendationModelStatus.TRAINED,
        db_index=True,
    )
    training_run = models.OneToOneField(
        RecommendationTrainingRun,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="model_version",
    )
    snapshot_version = models.PositiveIntegerField(verbose_name="特征快照版本")
    embedding_dim = models.PositiveIntegerField(default=16, verbose_name="向量维度")
    metrics = models.JSONField(default=dict, blank=True, verbose_name="模型指标")
    model_artifact = models.JSONField(default=dict, verbose_name="模型参数")
    published_at = models.DateTimeField(blank=True, null=True, verbose_name="发布时间")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)

    class Meta:
        db_table = "recommendation_model_version"
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(fields=["workspace_id", "version"], name="rec_model_ws_version"),
        ]


class RecommendationItemEmbedding(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    model_version = models.ForeignKey(
        RecommendationModelVersion,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="item_embeddings",
    )
    campaign = models.ForeignKey(
        "marketing.MarketingCampaign",
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="recommendation_embeddings",
    )
    feature_snapshot = models.ForeignKey(
        RecommendationFeatureSnapshot,
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
    )
    vector = models.JSONField(default=list, verbose_name="物料向量")
    vector_norm = models.FloatField(default=0, verbose_name="向量范数")

    class Meta:
        db_table = "recommendation_item_embedding"
        ordering = ["campaign__name"]
        constraints = [
            models.UniqueConstraint(fields=["model_version", "campaign"], name="rec_embedding_model_campaign"),
        ]


class RecommendationInferenceLog(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    model_version = models.ForeignKey(
        RecommendationModelVersion,
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="inference_logs",
    )
    customer = models.ForeignKey(
        "marketing.MarketingCustomer",
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="recommendation_inference_logs",
    )
    top_k = models.PositiveIntegerField(default=5, verbose_name="召回数量")
    latency_ms = models.PositiveIntegerField(default=0, verbose_name="推理耗时毫秒")
    user_snapshot = models.JSONField(default=dict, verbose_name="用户特征快照")
    candidates = models.JSONField(default=list, verbose_name="召回结果")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)

    class Meta:
        db_table = "recommendation_inference_log"
        ordering = ["-create_time"]
        indexes = [models.Index(fields=["workspace_id", "create_time"], name="rec_infer_ws_created")]


class RecommendationFusionConfig(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, unique=True, verbose_name="工作空间id")
    weights = models.JSONField(default=dict, verbose_name="召回通道权重")
    enabled_channels = models.JSONField(default=list, verbose_name="启用的召回通道")
    candidate_pool_size = models.PositiveIntegerField(default=50, verbose_name="单通道候选池大小")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)

    class Meta:
        db_table = "recommendation_fusion_config"
        ordering = ["workspace_id"]


class RecommendationFusionRun(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    customer = models.ForeignKey(
        "marketing.MarketingCustomer",
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="recommendation_fusion_runs",
    )
    model_version = models.ForeignKey(
        RecommendationModelVersion,
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="fusion_runs",
    )
    top_k = models.PositiveIntegerField(default=5, verbose_name="召回数量")
    latency_ms = models.PositiveIntegerField(default=0, verbose_name="融合耗时毫秒")
    config_snapshot = models.JSONField(default=dict, verbose_name="融合配置快照")
    channel_results = models.JSONField(default=dict, verbose_name="各通道召回结果")
    fused_candidates = models.JSONField(default=list, verbose_name="融合召回结果")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)

    class Meta:
        db_table = "recommendation_fusion_run"
        ordering = ["-create_time"]
        indexes = [models.Index(fields=["workspace_id", "create_time"], name="rec_fusion_ws_created")]


class RecommendationRankingVersion(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    version = models.PositiveIntegerField(verbose_name="精排版本")
    name = models.CharField(max_length=128, verbose_name="策略名称")
    status = models.CharField(
        max_length=16,
        choices=RecommendationRankingStatus.choices,
        default=RecommendationRankingStatus.DRAFT,
        db_index=True,
    )
    feature_weights = models.JSONField(default=dict, verbose_name="特征权重")
    feature_schema = models.JSONField(default=list, verbose_name="特征定义")
    metrics = models.JSONField(default=dict, blank=True, verbose_name="离线指标")
    published_at = models.DateTimeField(blank=True, null=True, verbose_name="发布时间")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)

    class Meta:
        db_table = "recommendation_ranking_version"
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(fields=["workspace_id", "version"], name="rec_rank_ws_version"),
        ]


class RecommendationRankingRun(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    customer = models.ForeignKey(
        "marketing.MarketingCustomer",
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="recommendation_ranking_runs",
    )
    fusion_run = models.ForeignKey(
        RecommendationFusionRun,
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="ranking_runs",
    )
    ranking_version = models.ForeignKey(
        RecommendationRankingVersion,
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="ranking_runs",
    )
    top_n = models.PositiveIntegerField(default=5, verbose_name="精排数量")
    candidate_count = models.PositiveIntegerField(default=0, verbose_name="候选数量")
    latency_ms = models.PositiveIntegerField(default=0, verbose_name="精排耗时毫秒")
    config_snapshot = models.JSONField(default=dict, verbose_name="精排配置快照")
    input_candidates = models.JSONField(default=list, verbose_name="输入候选")
    ranked_candidates = models.JSONField(default=list, verbose_name="精排结果")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)

    class Meta:
        db_table = "recommendation_ranking_run"
        ordering = ["-create_time"]
        indexes = [models.Index(fields=["workspace_id", "create_time"], name="rec_rank_ws_created")]


class RecommendationFeedbackEvent(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    customer = models.ForeignKey(
        "marketing.MarketingCustomer",
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="recommendation_feedback_events",
    )
    campaign = models.ForeignKey(
        "marketing.MarketingCampaign",
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="recommendation_feedback_events",
    )
    ranking_run = models.ForeignKey(
        RecommendationRankingRun,
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="feedback_events",
    )
    event_type = models.CharField(max_length=16, choices=RecommendationFeedbackType.choices, db_index=True)
    label = models.FloatField(default=0, verbose_name="训练标签")
    source_type = models.CharField(max_length=32, default="MANUAL", db_index=True, verbose_name="事件来源")
    source_id = models.CharField(max_length=64, default="", blank=True, verbose_name="来源记录id")
    event_key = models.CharField(max_length=160, default="", blank=True, db_index=True, verbose_name="幂等键")
    feature_snapshot = models.JSONField(default=dict, blank=True, verbose_name="精排特征快照")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="事件扩展信息")
    occurred_at = models.DateTimeField(verbose_name="事件发生时间")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)

    class Meta:
        db_table = "recommendation_feedback_event"
        ordering = ["-occurred_at", "-create_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "event_key"],
                condition=~models.Q(event_key=""),
                name="rec_feedback_ws_event_key",
            )
        ]
        indexes = [
            models.Index(fields=["workspace_id", "event_type", "occurred_at"], name="rec_feedback_ws_type_at"),
        ]


class RecommendationIncrementalRun(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    name = models.CharField(max_length=128, verbose_name="增量任务名称")
    status = models.CharField(
        max_length=16,
        choices=RecommendationIncrementalStatus.choices,
        default=RecommendationIncrementalStatus.RUNNING,
        db_index=True,
    )
    base_ranking_version = models.ForeignKey(
        RecommendationRankingVersion,
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="base_incremental_runs",
    )
    generated_ranking_version = models.ForeignKey(
        RecommendationRankingVersion,
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="generated_incremental_runs",
    )
    learning_rate = models.FloatField(default=0.25, verbose_name="增量学习率")
    sample_count = models.PositiveIntegerField(default=0, verbose_name="样本数")
    positive_count = models.PositiveIntegerField(default=0, verbose_name="正样本数")
    negative_count = models.PositiveIntegerField(default=0, verbose_name="负样本数")
    event_snapshot = models.JSONField(default=list, blank=True, verbose_name="事件快照")
    weight_delta = models.JSONField(default=dict, blank=True, verbose_name="权重变化")
    metrics = models.JSONField(default=dict, blank=True, verbose_name="新旧版本指标")
    error_message = models.TextField(default="", blank=True, verbose_name="失败信息")
    started_at = models.DateTimeField(blank=True, null=True, verbose_name="开始时间")
    finished_at = models.DateTimeField(blank=True, null=True, verbose_name="结束时间")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)

    class Meta:
        db_table = "recommendation_incremental_run"
        ordering = ["-create_time"]
        indexes = [models.Index(fields=["workspace_id", "create_time"], name="rec_increment_ws_created")]
