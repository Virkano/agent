# coding=utf-8
from numbers import Real

from django.db import IntegrityError, transaction
from django.db.models import Count
from django.utils import timezone
from rest_framework import serializers

from common.exception.app_exception import AppApiException
from models_provider.lifecycle_tracking import get_lifecycle_tracking_adapter
from models_provider.models import (
    LifecycleModelVersion,
    LifecycleModelVersionStatus,
    Model,
    ModelEvaluationRun,
    ModelEvaluationStatus,
    ModelExperiment,
    ModelExperimentStatus,
    ModelReleaseAction,
    ModelReleaseRecord,
    ModelReleaseStatus,
)


class ModelExperimentWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=128)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    source_type = serializers.CharField(required=False, max_length=32, default="MANUAL")
    dataset_name = serializers.CharField(required=False, allow_blank=True, max_length=128, default="")
    dataset_version = serializers.CharField(required=False, allow_blank=True, max_length=64, default="")
    parameters = serializers.JSONField(required=False, default=dict)
    tags = serializers.JSONField(required=False, default=dict)

    def validate_parameters(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("实验参数必须是对象")
        return value

    def validate_tags(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("实验标签必须是对象")
        return value


class ModelExperimentUpdateSerializer(ModelExperimentWriteSerializer):
    name = serializers.CharField(required=False, max_length=128)
    description = serializers.CharField(required=False, allow_blank=True)
    source_type = serializers.CharField(required=False, max_length=32)
    dataset_name = serializers.CharField(required=False, allow_blank=True, max_length=128)
    dataset_version = serializers.CharField(required=False, allow_blank=True, max_length=64)
    parameters = serializers.JSONField(required=False)
    tags = serializers.JSONField(required=False)
    status = serializers.ChoiceField(required=False, choices=ModelExperimentStatus.choices)


class LifecycleModelVersionWriteSerializer(serializers.Serializer):
    registry_name = serializers.CharField(max_length=128)
    experiment_id = serializers.UUIDField()
    provider_model_id = serializers.UUIDField(required=False, allow_null=True)
    artifact_uri = serializers.CharField(required=False, allow_blank=True, max_length=512, default="")
    artifact_digest = serializers.CharField(required=False, allow_blank=True, max_length=128, default="")
    dataset_version = serializers.CharField(required=False, allow_blank=True, max_length=64, default="")
    parameters = serializers.JSONField(required=False, default=dict)
    metrics = serializers.JSONField(required=False, default=dict)

    def validate_parameters(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("模型参数必须是对象")
        return value

    def validate_metrics(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("训练指标必须是对象")
        return value


class LifecycleModelVersionUpdateSerializer(serializers.Serializer):
    provider_model_id = serializers.UUIDField(required=False, allow_null=True)
    artifact_uri = serializers.CharField(required=False, allow_blank=True, max_length=512)
    artifact_digest = serializers.CharField(required=False, allow_blank=True, max_length=128)
    dataset_version = serializers.CharField(required=False, allow_blank=True, max_length=64)
    parameters = serializers.JSONField(required=False)
    metrics = serializers.JSONField(required=False)


class ModelEvaluationWriteSerializer(serializers.Serializer):
    dataset_name = serializers.CharField(max_length=128)
    dataset_version = serializers.CharField(required=False, allow_blank=True, max_length=64, default="")
    metrics = serializers.JSONField()
    thresholds = serializers.JSONField()
    summary = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_metrics(self, value):
        if not isinstance(value, dict) or not value:
            raise serializers.ValidationError("评估指标必须是非空对象")
        for key, metric in value.items():
            if not isinstance(key, str) or not isinstance(metric, Real) or isinstance(metric, bool):
                raise serializers.ValidationError("评估指标名称必须是字符串，值必须是数字")
        return value

    def validate_thresholds(self, value):
        if not isinstance(value, dict) or not value:
            raise serializers.ValidationError("准入阈值必须是非空对象")
        for key, threshold in value.items():
            if not isinstance(key, str):
                raise serializers.ValidationError("阈值指标名称必须是字符串")
            if isinstance(threshold, Real) and not isinstance(threshold, bool):
                continue
            if not isinstance(threshold, dict) or not set(threshold).issubset({"min", "max"}):
                raise serializers.ValidationError("阈值必须是数字或仅包含 min/max 的对象")
            if not threshold:
                raise serializers.ValidationError("min/max 阈值不能为空")
            if any(not isinstance(item, Real) or isinstance(item, bool) for item in threshold.values()):
                raise serializers.ValidationError("min/max 阈值必须是数字")
        return value


class ModelReleaseWriteSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=512, default="")


def serialize_experiment(row):
    return {
        "id": str(row.id),
        "workspace_id": row.workspace_id,
        "name": row.name,
        "description": row.description,
        "status": row.status,
        "status_label": row.get_status_display(),
        "source_type": row.source_type,
        "dataset_name": row.dataset_name,
        "dataset_version": row.dataset_version,
        "parameters": row.parameters,
        "tags": row.tags,
        "external_run_id": row.external_run_id,
        "user_id": str(row.user_id) if row.user_id else None,
        "started_at": row.started_at,
        "finished_at": row.finished_at,
        "create_time": row.create_time,
        "update_time": row.update_time,
    }


def serialize_evaluation(row):
    return {
        "id": str(row.id),
        "model_version_id": str(row.model_version_id),
        "dataset_name": row.dataset_name,
        "dataset_version": row.dataset_version,
        "status": row.status,
        "status_label": row.get_status_display(),
        "metrics": row.metrics,
        "thresholds": row.thresholds,
        "summary": row.summary,
        "started_at": row.started_at,
        "finished_at": row.finished_at,
        "create_time": row.create_time,
    }


def serialize_version(row, include_evaluations=False):
    data = {
        "id": str(row.id),
        "workspace_id": row.workspace_id,
        "registry_name": row.registry_name,
        "version": row.version,
        "version_label": f"v{row.version}",
        "status": row.status,
        "status_label": row.get_status_display(),
        "experiment_id": str(row.experiment_id) if row.experiment_id else None,
        "experiment_name": row.experiment.name if row.experiment else "",
        "provider_model_id": str(row.provider_model_id) if row.provider_model_id else None,
        "provider_model_name": row.provider_model.name if row.provider_model else "",
        "artifact_uri": row.artifact_uri,
        "artifact_digest": row.artifact_digest,
        "dataset_version": row.dataset_version,
        "parameters": row.parameters,
        "metrics": row.metrics,
        "created_by_id": str(row.created_by_id) if row.created_by_id else None,
        "published_at": row.published_at,
        "create_time": row.create_time,
        "update_time": row.update_time,
    }
    if include_evaluations:
        data["evaluations"] = [serialize_evaluation(item) for item in row.evaluations.all()]
    return data


def serialize_release(row):
    return {
        "id": str(row.id),
        "registry_name": row.registry_name,
        "action": row.action,
        "action_label": row.get_action_display(),
        "status": row.status,
        "status_label": row.get_status_display(),
        "from_version_id": str(row.from_version_id) if row.from_version_id else None,
        "from_version": row.from_version.version if row.from_version else None,
        "target_version_id": str(row.target_version_id),
        "target_version": row.target_version.version,
        "reason": row.reason,
        "details": row.details,
        "operator_id": str(row.operator_id) if row.operator_id else None,
        "create_time": row.create_time,
    }


def _evaluation_passed(metrics, thresholds):
    for key, threshold in thresholds.items():
        metric = metrics.get(key)
        if not isinstance(metric, Real) or isinstance(metric, bool):
            return False
        if isinstance(threshold, dict):
            if "min" in threshold and metric < threshold["min"]:
                return False
            if "max" in threshold and metric > threshold["max"]:
                return False
        elif metric < threshold:
            return False
    return True


class ModelLifecycleService:
    experiment_transitions = {
        ModelExperimentStatus.DRAFT: {ModelExperimentStatus.RUNNING, ModelExperimentStatus.CANCELLED},
        ModelExperimentStatus.RUNNING: {
            ModelExperimentStatus.SUCCESS,
            ModelExperimentStatus.FAILED,
            ModelExperimentStatus.CANCELLED,
        },
        ModelExperimentStatus.FAILED: {ModelExperimentStatus.RUNNING},
        ModelExperimentStatus.SUCCESS: set(),
        ModelExperimentStatus.CANCELLED: set(),
    }

    def __init__(self, workspace_id, user=None):
        self.workspace_id = workspace_id
        self.user = user

    def _experiments(self):
        return ModelExperiment.objects.filter(workspace_id=self.workspace_id).select_related("user")

    def _versions(self):
        return LifecycleModelVersion.objects.filter(workspace_id=self.workspace_id).select_related(
            "experiment", "provider_model", "created_by"
        )

    def overview(self):
        experiment_counts = {
            item["status"]: item["count"]
            for item in self._experiments().values("status").annotate(count=Count("id"))
        }
        version_counts = {
            item["status"]: item["count"]
            for item in self._versions().values("status").annotate(count=Count("id"))
        }
        published = self._versions().filter(status=LifecycleModelVersionStatus.PUBLISHED)
        return {
            "experiment_total": sum(experiment_counts.values()),
            "experiment_counts": experiment_counts,
            "version_total": sum(version_counts.values()),
            "version_counts": version_counts,
            "published_total": published.count(),
            "published_versions": [serialize_version(row) for row in published.order_by("registry_name")],
            "recent_releases": [
                serialize_release(row)
                for row in ModelReleaseRecord.objects.filter(workspace_id=self.workspace_id)
                .select_related("from_version", "target_version", "operator")[:10]
            ],
        }

    def list_experiments(self, filters=None):
        filters = filters or {}
        queryset = self._experiments()
        if filters.get("status"):
            queryset = queryset.filter(status=filters["status"])
        if filters.get("keyword"):
            queryset = queryset.filter(name__icontains=filters["keyword"])
        return [serialize_experiment(row) for row in queryset]

    def get_experiment(self, experiment_id):
        row = self._experiments().filter(id=experiment_id).first()
        if row is None:
            raise AppApiException(404, "模型实验不存在")
        return serialize_experiment(row)

    def create_experiment(self, data):
        serializer = ModelExperimentWriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        tracker = get_lifecycle_tracking_adapter()
        external_run_id = tracker.create_run(
            experiment_name=values["name"],
            parameters=values["parameters"],
            tags=values["tags"],
        )
        try:
            with transaction.atomic():
                row = ModelExperiment.objects.create(
                    workspace_id=self.workspace_id,
                    user=self.user,
                    external_run_id=external_run_id,
                    **values,
                )
        except IntegrityError as exc:
            raise AppApiException(400, "当前工作空间已存在同名实验") from exc
        return serialize_experiment(row)

    @transaction.atomic
    def update_experiment(self, experiment_id, data):
        row = (
            ModelExperiment.objects.select_for_update()
            .filter(workspace_id=self.workspace_id, id=experiment_id)
            .first()
        )
        if row is None:
            raise AppApiException(404, "模型实验不存在")
        serializer = ModelExperimentUpdateSerializer(data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        target_status = values.pop("status", None)
        if target_status and target_status != row.status:
            if target_status not in self.experiment_transitions[row.status]:
                raise AppApiException(400, f"实验不能从{row.get_status_display()}切换到{target_status}")
            row.status = target_status
            if target_status == ModelExperimentStatus.RUNNING:
                row.started_at = timezone.now()
                row.finished_at = None
            elif target_status in {
                ModelExperimentStatus.SUCCESS,
                ModelExperimentStatus.FAILED,
                ModelExperimentStatus.CANCELLED,
            }:
                row.finished_at = timezone.now()
        for field, value in values.items():
            setattr(row, field, value)
        try:
            with transaction.atomic():
                row.save()
        except IntegrityError as exc:
            raise AppApiException(400, "当前工作空间已存在同名实验") from exc
        if target_status in {ModelExperimentStatus.SUCCESS, ModelExperimentStatus.FAILED}:
            get_lifecycle_tracking_adapter().finish_run(
                run_id=row.external_run_id,
                status=target_status,
                metrics={},
            )
        return serialize_experiment(row)

    def delete_experiment(self, experiment_id):
        row = self._experiments().filter(id=experiment_id).first()
        if row is None:
            raise AppApiException(404, "模型实验不存在")
        if row.status != ModelExperimentStatus.DRAFT or row.model_versions.exists():
            raise AppApiException(400, "只有未注册模型版本的草稿实验可以删除")
        row.delete()
        return True

    def list_versions(self, filters=None):
        filters = filters or {}
        queryset = self._versions()
        if filters.get("registry_name"):
            queryset = queryset.filter(registry_name=filters["registry_name"])
        if filters.get("status"):
            queryset = queryset.filter(status=filters["status"])
        return [serialize_version(row) for row in queryset]

    def get_version(self, version_id):
        row = self._versions().prefetch_related("evaluations").filter(id=version_id).first()
        if row is None:
            raise AppApiException(404, "模型版本不存在")
        return serialize_version(row, include_evaluations=True)

    def _resolve_version_relations(self, values):
        experiment = self._experiments().filter(id=values["experiment_id"]).first()
        if experiment is None:
            raise AppApiException(400, "来源实验不存在或不属于当前工作空间")
        if experiment.status != ModelExperimentStatus.SUCCESS:
            raise AppApiException(400, "只有已完成实验可以注册模型版本")
        provider_model = None
        if values.get("provider_model_id"):
            provider_model = Model.objects.filter(
                workspace_id=self.workspace_id,
                id=values["provider_model_id"],
            ).first()
            if provider_model is None:
                raise AppApiException(400, "关联在线模型不存在或不属于当前工作空间")
        return experiment, provider_model

    @transaction.atomic
    def create_version(self, data):
        serializer = LifecycleModelVersionWriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        experiment, provider_model = self._resolve_version_relations(values)
        existing = list(
            LifecycleModelVersion.objects.select_for_update()
            .filter(workspace_id=self.workspace_id, registry_name=values["registry_name"])
            .only("version")
        )
        next_version = max((row.version for row in existing), default=0) + 1
        try:
            with transaction.atomic():
                row = LifecycleModelVersion.objects.create(
                    workspace_id=self.workspace_id,
                    registry_name=values["registry_name"],
                    version=next_version,
                    experiment=experiment,
                    provider_model=provider_model,
                    artifact_uri=values["artifact_uri"],
                    artifact_digest=values["artifact_digest"],
                    dataset_version=values["dataset_version"] or experiment.dataset_version,
                    parameters=values["parameters"] or experiment.parameters,
                    metrics=values["metrics"],
                    created_by=self.user,
                )
        except IntegrityError as exc:
            raise AppApiException(409, "模型版本号发生并发冲突，请重试") from exc
        return serialize_version(row)

    @transaction.atomic
    def update_version(self, version_id, data):
        row = (
            LifecycleModelVersion.objects.select_for_update()
            .filter(workspace_id=self.workspace_id, id=version_id)
            .first()
        )
        if row is None:
            raise AppApiException(404, "模型版本不存在")
        if row.status != LifecycleModelVersionStatus.REGISTERED:
            raise AppApiException(400, "只有未开始评估的模型版本可以编辑")
        serializer = LifecycleModelVersionUpdateSerializer(data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        if "provider_model_id" in values:
            provider_model_id = values.pop("provider_model_id")
            provider_model = None
            if provider_model_id:
                provider_model = Model.objects.filter(
                    workspace_id=self.workspace_id,
                    id=provider_model_id,
                ).first()
                if provider_model is None:
                    raise AppApiException(400, "关联在线模型不存在或不属于当前工作空间")
            row.provider_model = provider_model
        for field, value in values.items():
            setattr(row, field, value)
        row.save()
        return serialize_version(row)

    def delete_version(self, version_id):
        row = self._versions().filter(id=version_id).first()
        if row is None:
            raise AppApiException(404, "模型版本不存在")
        if row.status != LifecycleModelVersionStatus.REGISTERED or row.evaluations.exists():
            raise AppApiException(400, "只有未评估的已注册版本可以删除")
        if row.release_records_as_source.exists() or row.release_records_as_target.exists():
            raise AppApiException(400, "已有发布记录的模型版本不能删除")
        row.delete()
        return True

    @transaction.atomic
    def evaluate_version(self, version_id, data):
        row = (
            LifecycleModelVersion.objects.select_for_update()
            .filter(workspace_id=self.workspace_id, id=version_id)
            .first()
        )
        if row is None:
            raise AppApiException(404, "模型版本不存在")
        if row.status not in {
            LifecycleModelVersionStatus.REGISTERED,
            LifecycleModelVersionStatus.APPROVED,
            LifecycleModelVersionStatus.REJECTED,
        }:
            raise AppApiException(400, "当前模型版本状态不允许评估")
        serializer = ModelEvaluationWriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        passed = _evaluation_passed(values["metrics"], values["thresholds"])
        now = timezone.now()
        evaluation = ModelEvaluationRun.objects.create(
            workspace_id=self.workspace_id,
            model_version=row,
            status=ModelEvaluationStatus.PASSED if passed else ModelEvaluationStatus.FAILED,
            evaluated_by=self.user,
            started_at=now,
            finished_at=now,
            **values,
        )
        row.status = LifecycleModelVersionStatus.APPROVED if passed else LifecycleModelVersionStatus.REJECTED
        row.metrics = values["metrics"]
        row.save(update_fields=["status", "metrics", "update_time"])
        return {
            "evaluation": serialize_evaluation(evaluation),
            "version": serialize_version(row),
        }

    def list_releases(self, registry_name=None):
        queryset = ModelReleaseRecord.objects.filter(workspace_id=self.workspace_id).select_related(
            "from_version", "target_version", "operator"
        )
        if registry_name:
            queryset = queryset.filter(registry_name=registry_name)
        return [serialize_release(row) for row in queryset]

    @transaction.atomic
    def _activate_version(self, version_id, reason, action):
        target = (
            LifecycleModelVersion.objects.select_for_update()
            .filter(workspace_id=self.workspace_id, id=version_id)
            .first()
        )
        if target is None:
            raise AppApiException(404, "模型版本不存在")
        allowed_statuses = (
            {LifecycleModelVersionStatus.APPROVED}
            if action == ModelReleaseAction.PUBLISH
            else {LifecycleModelVersionStatus.APPROVED, LifecycleModelVersionStatus.ARCHIVED}
        )
        if target.status not in allowed_statuses:
            raise AppApiException(400, "目标版本未通过评估或当前状态不允许此操作")
        if not target.evaluations.filter(status=ModelEvaluationStatus.PASSED).exists():
            raise AppApiException(400, "目标版本没有通过准入门槛的评估记录")
        current = (
            LifecycleModelVersion.objects.select_for_update()
            .filter(workspace_id=self.workspace_id)
            .filter(registry_name=target.registry_name, status=LifecycleModelVersionStatus.PUBLISHED)
            .exclude(id=target.id)
            .first()
        )
        if action == ModelReleaseAction.ROLLBACK and current is None:
            raise AppApiException(400, "当前没有可回滚的已发布版本")
        if current:
            current.status = LifecycleModelVersionStatus.ARCHIVED
            current.save(update_fields=["status", "update_time"])
        target.status = LifecycleModelVersionStatus.PUBLISHED
        target.published_at = timezone.now()
        target.save(update_fields=["status", "published_at", "update_time"])
        release = ModelReleaseRecord.objects.create(
            workspace_id=self.workspace_id,
            registry_name=target.registry_name,
            action=action,
            status=ModelReleaseStatus.SUCCESS,
            from_version=current,
            target_version=target,
            reason=reason,
            details={"target_version": target.version, "source_version": current.version if current else None},
            operator=self.user,
        )
        return {"version": serialize_version(target), "release": serialize_release(release)}

    def publish_version(self, version_id, data):
        serializer = ModelReleaseWriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return self._activate_version(version_id, serializer.validated_data["reason"], ModelReleaseAction.PUBLISH)

    def rollback_version(self, version_id, data):
        serializer = ModelReleaseWriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return self._activate_version(version_id, serializer.validated_data["reason"], ModelReleaseAction.ROLLBACK)
