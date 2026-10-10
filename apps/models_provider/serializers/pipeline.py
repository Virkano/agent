# coding=utf-8
import json
from numbers import Real

from apscheduler.triggers.cron import CronTrigger
from django.db import IntegrityError, transaction
from django.db.models import Max
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from rest_framework import serializers

from common.exception.app_exception import AppApiException
from models_provider.models import (
    ModelPipelineApprovalMode,
    ModelPipelineRun,
    ModelPipelineRunStatus,
    ModelPipelineRunTrigger,
    ModelPipelineStage,
    ModelPipelineStageRun,
    ModelPipelineStageStatus,
    ModelTrainingPipeline,
)
from models_provider.pipeline_runner import get_model_pipeline_runner
from models_provider.serializers.lifecycle import ModelLifecycleService


class ModelPipelineWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=128)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    registry_name = serializers.CharField(max_length=128)
    dataset_name = serializers.CharField(max_length=128)
    dataset_version = serializers.CharField(required=False, allow_blank=True, max_length=64, default="")
    parameters = serializers.JSONField(required=False, default=dict)
    evaluation_metrics = serializers.JSONField()
    thresholds = serializers.JSONField()
    artifact_uri_template = serializers.CharField(
        required=False,
        max_length=512,
        default="local://model-pipeline/{pipeline_id}/run-{run_number}",
    )
    approval_mode = serializers.ChoiceField(
        required=False,
        choices=ModelPipelineApprovalMode.choices,
        default=ModelPipelineApprovalMode.MANUAL,
    )
    auto_deploy = serializers.BooleanField(required=False, default=True)
    active = serializers.BooleanField(required=False, default=True)
    schedule_enabled = serializers.BooleanField(required=False, default=False)
    cron_expression = serializers.CharField(required=False, allow_blank=True, max_length=128, default="")

    def validate_parameters(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("训练参数必须是对象")
        return value

    def validate_evaluation_metrics(self, value):
        if not isinstance(value, dict) or not value:
            raise serializers.ValidationError("默认评估指标必须是非空对象")
        if any(not isinstance(item, Real) or isinstance(item, bool) for item in value.values()):
            raise serializers.ValidationError("评估指标值必须是数字")
        return value

    def validate_thresholds(self, value):
        if not isinstance(value, dict) or not value:
            raise serializers.ValidationError("发布准入阈值必须是非空对象")
        for threshold in value.values():
            if isinstance(threshold, Real) and not isinstance(threshold, bool):
                continue
            if not isinstance(threshold, dict) or not threshold or not set(threshold).issubset({"min", "max"}):
                raise serializers.ValidationError("阈值必须是数字或仅包含 min/max 的对象")
            if any(not isinstance(item, Real) or isinstance(item, bool) for item in threshold.values()):
                raise serializers.ValidationError("min/max 阈值必须是数字")
        return value

    def validate_artifact_uri_template(self, value):
        if "{pipeline_id}" not in value or "{run_number}" not in value:
            raise serializers.ValidationError("产物地址模板必须包含 {pipeline_id} 和 {run_number}")
        return value

    def validate(self, attrs):
        if attrs.get("schedule_enabled"):
            expression = attrs.get("cron_expression", "").strip()
            if not expression:
                raise serializers.ValidationError({"cron_expression": "启用定时重训时必须填写 Cron 表达式"})
            try:
                CronTrigger.from_crontab(expression)
            except ValueError as exc:
                raise serializers.ValidationError({"cron_expression": "Cron 表达式无效"}) from exc
        return attrs


class ModelPipelineUpdateSerializer(ModelPipelineWriteSerializer):
    name = serializers.CharField(required=False, max_length=128)
    registry_name = serializers.CharField(required=False, max_length=128)
    dataset_name = serializers.CharField(required=False, max_length=128)
    evaluation_metrics = serializers.JSONField(required=False)
    thresholds = serializers.JSONField(required=False)


class ModelPipelineRunSerializer(serializers.Serializer):
    evaluation_metrics = serializers.JSONField(required=False)

    def validate_evaluation_metrics(self, value):
        if not isinstance(value, dict) or not value:
            raise serializers.ValidationError("评估指标必须是非空对象")
        if any(not isinstance(item, Real) or isinstance(item, bool) for item in value.values()):
            raise serializers.ValidationError("评估指标值必须是数字")
        return value


class ModelPipelineApprovalSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["APPROVE", "REJECT"])
    comment = serializers.CharField(required=False, allow_blank=True, max_length=512, default="")


def _next_run_at(expression, now=None):
    if not expression:
        return None
    now = now or timezone.now()
    return CronTrigger.from_crontab(expression).get_next_fire_time(None, now)


def _json_safe(value):
    return json.loads(json.dumps(value, cls=DjangoJSONEncoder))


def serialize_stage(row):
    return {
        "id": str(row.id),
        "stage": row.stage,
        "stage_label": row.get_stage_display(),
        "sequence": row.sequence,
        "status": row.status,
        "status_label": row.get_status_display(),
        "input_snapshot": row.input_snapshot,
        "output_snapshot": row.output_snapshot,
        "error_message": row.error_message,
        "started_at": row.started_at,
        "finished_at": row.finished_at,
    }


def serialize_run(row, include_stages=False):
    data = {
        "id": str(row.id),
        "pipeline_id": str(row.pipeline_id),
        "pipeline_name": row.pipeline.name,
        "run_number": row.run_number,
        "trigger": row.trigger,
        "trigger_label": row.get_trigger_display(),
        "status": row.status,
        "status_label": row.get_status_display(),
        "current_stage": row.current_stage,
        "current_stage_label": row.get_current_stage_display(),
        "config_snapshot": row.config_snapshot,
        "error_message": row.error_message,
        "experiment_id": str(row.experiment_id) if row.experiment_id else None,
        "model_version_id": str(row.model_version_id) if row.model_version_id else None,
        "model_version_label": f"v{row.model_version.version}" if row.model_version else "",
        "approved_by_id": str(row.approved_by_id) if row.approved_by_id else None,
        "approval_comment": row.approval_comment,
        "approved_at": row.approved_at,
        "started_at": row.started_at,
        "finished_at": row.finished_at,
        "create_time": row.create_time,
    }
    if include_stages:
        data["stages"] = [serialize_stage(item) for item in row.stage_runs.all()]
    return data


def serialize_pipeline(row):
    return {
        "id": str(row.id),
        "workspace_id": row.workspace_id,
        "name": row.name,
        "description": row.description,
        "registry_name": row.registry_name,
        "dataset_name": row.dataset_name,
        "dataset_version": row.dataset_version,
        "parameters": row.parameters,
        "evaluation_metrics": row.evaluation_metrics,
        "thresholds": row.thresholds,
        "artifact_uri_template": row.artifact_uri_template,
        "approval_mode": row.approval_mode,
        "approval_mode_label": row.get_approval_mode_display(),
        "auto_deploy": row.auto_deploy,
        "active": row.active,
        "schedule_enabled": row.schedule_enabled,
        "cron_expression": row.cron_expression,
        "next_run_at": row.next_run_at,
        "last_run_at": row.last_run_at,
        "created_by_id": str(row.created_by_id) if row.created_by_id else None,
        "create_time": row.create_time,
        "update_time": row.update_time,
    }


class ModelPipelineService:
    stage_order = [
        ModelPipelineStage.FEATURE,
        ModelPipelineStage.TRAIN,
        ModelPipelineStage.EVALUATE,
        ModelPipelineStage.APPROVE,
        ModelPipelineStage.DEPLOY,
    ]

    def __init__(self, workspace_id, user=None):
        self.workspace_id = workspace_id
        self.user = user

    def _pipelines(self):
        return ModelTrainingPipeline.objects.filter(workspace_id=self.workspace_id).select_related("created_by")

    def _runs(self):
        return ModelPipelineRun.objects.filter(workspace_id=self.workspace_id).select_related(
            "pipeline", "experiment", "model_version", "operator", "approved_by"
        )

    def list_pipelines(self, filters=None):
        filters = filters or {}
        queryset = self._pipelines()
        if filters.get("active") in {"true", "false"}:
            queryset = queryset.filter(active=filters["active"] == "true")
        if filters.get("keyword"):
            queryset = queryset.filter(name__icontains=filters["keyword"])
        return [serialize_pipeline(row) for row in queryset]

    def get_pipeline(self, pipeline_id):
        row = self._pipelines().filter(id=pipeline_id).first()
        if row is None:
            raise AppApiException(404, "训练流水线不存在")
        return serialize_pipeline(row)

    def create_pipeline(self, data):
        serializer = ModelPipelineWriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        if values["schedule_enabled"]:
            values["next_run_at"] = _next_run_at(values["cron_expression"])
        try:
            with transaction.atomic():
                row = ModelTrainingPipeline.objects.create(
                    workspace_id=self.workspace_id,
                    created_by=self.user,
                    **values,
                )
        except IntegrityError as exc:
            raise AppApiException(400, "当前工作空间已存在同名流水线") from exc
        return serialize_pipeline(row)

    @transaction.atomic
    def update_pipeline(self, pipeline_id, data):
        row = (
            ModelTrainingPipeline.objects.select_for_update()
            .filter(workspace_id=self.workspace_id, id=pipeline_id)
            .first()
        )
        if row is None:
            raise AppApiException(404, "训练流水线不存在")
        serializer = ModelPipelineUpdateSerializer(data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        schedule_enabled = values.get("schedule_enabled", row.schedule_enabled)
        cron_expression = values.get("cron_expression", row.cron_expression)
        if schedule_enabled:
            if not cron_expression:
                raise AppApiException(400, "启用定时重训时必须填写 Cron 表达式")
            try:
                values["next_run_at"] = _next_run_at(cron_expression)
            except ValueError as exc:
                raise AppApiException(400, "Cron 表达式无效") from exc
        else:
            values["next_run_at"] = None
        for field, value in values.items():
            setattr(row, field, value)
        try:
            with transaction.atomic():
                row.save()
        except IntegrityError as exc:
            raise AppApiException(400, "当前工作空间已存在同名流水线") from exc
        return serialize_pipeline(row)

    def delete_pipeline(self, pipeline_id):
        row = self._pipelines().filter(id=pipeline_id).first()
        if row is None:
            raise AppApiException(404, "训练流水线不存在")
        if row.runs.exists():
            raise AppApiException(400, "已有运行记录的流水线不能删除，可将其停用")
        row.delete()
        return True

    def list_runs(self, filters=None):
        filters = filters or {}
        queryset = self._runs()
        if filters.get("pipeline_id"):
            queryset = queryset.filter(pipeline_id=filters["pipeline_id"])
        if filters.get("status"):
            queryset = queryset.filter(status=filters["status"])
        return [serialize_run(row) for row in queryset]

    def get_run(self, run_id):
        row = self._runs().prefetch_related("stage_runs").filter(id=run_id).first()
        if row is None:
            raise AppApiException(404, "流水线运行不存在")
        return serialize_run(row, include_stages=True)

    def _set_stage(self, run, stage, status, input_snapshot=None, output_snapshot=None, error_message=""):
        now = timezone.now()
        stage_run, _ = ModelPipelineStageRun.objects.get_or_create(
            workspace_id=self.workspace_id,
            pipeline_run=run,
            stage=stage,
            defaults={"sequence": self.stage_order.index(stage) + 1},
        )
        stage_run.status = status
        if input_snapshot is not None:
            stage_run.input_snapshot = _json_safe(input_snapshot)
        if output_snapshot is not None:
            stage_run.output_snapshot = _json_safe(output_snapshot)
        stage_run.error_message = error_message
        if status == ModelPipelineStageStatus.RUNNING and stage_run.started_at is None:
            stage_run.started_at = now
        if status in {
            ModelPipelineStageStatus.SUCCESS,
            ModelPipelineStageStatus.FAILED,
            ModelPipelineStageStatus.SKIPPED,
        }:
            stage_run.started_at = stage_run.started_at or now
            stage_run.finished_at = now
        stage_run.save()
        run.current_stage = stage
        run.save(update_fields=["current_stage", "update_time"])
        return stage_run

    def _mark_run_failed(self, run, message):
        run.status = ModelPipelineRunStatus.FAILED
        run.error_message = str(message)
        run.finished_at = timezone.now()
        run.save(update_fields=["status", "error_message", "finished_at", "update_time"])

    def _skip_remaining_stages(self, run, after_stage):
        start = self.stage_order.index(after_stage) + 1
        for stage in self.stage_order[start:]:
            self._set_stage(run, stage, ModelPipelineStageStatus.SKIPPED)

    def _pipeline_snapshot(self, pipeline, override=None):
        override = override or {}
        return {
            "pipeline_id": str(pipeline.id),
            "pipeline_name": pipeline.name,
            "registry_name": pipeline.registry_name,
            "dataset_name": pipeline.dataset_name,
            "dataset_version": pipeline.dataset_version,
            "parameters": pipeline.parameters,
            "evaluation_metrics": override.get("evaluation_metrics", pipeline.evaluation_metrics),
            "thresholds": pipeline.thresholds,
            "artifact_uri_template": pipeline.artifact_uri_template,
            "approval_mode": pipeline.approval_mode,
            "auto_deploy": pipeline.auto_deploy,
        }

    @transaction.atomic
    def _create_run(self, pipeline_id, data, trigger):
        pipeline = (
            ModelTrainingPipeline.objects.select_for_update()
            .filter(workspace_id=self.workspace_id, id=pipeline_id)
            .first()
        )
        if pipeline is None:
            raise AppApiException(404, "训练流水线不存在")
        if not pipeline.active:
            raise AppApiException(400, "训练流水线已停用")
        if ModelPipelineRun.objects.filter(
            pipeline=pipeline,
            status__in=[ModelPipelineRunStatus.RUNNING, ModelPipelineRunStatus.WAITING_APPROVAL],
        ).exists():
            raise AppApiException(409, "训练流水线已有未完成的运行")

        serializer = ModelPipelineRunSerializer(data=data or {})
        serializer.is_valid(raise_exception=True)
        run_number = (
            ModelPipelineRun.objects.filter(pipeline=pipeline).aggregate(max_number=Max("run_number"))["max_number"]
            or 0
        ) + 1
        snapshot = self._pipeline_snapshot(pipeline, serializer.validated_data)
        snapshot["run_number"] = run_number
        now = timezone.now()
        run = ModelPipelineRun.objects.create(
            workspace_id=self.workspace_id,
            pipeline=pipeline,
            run_number=run_number,
            trigger=trigger,
            config_snapshot=snapshot,
            operator=self.user,
        )
        ModelPipelineStageRun.objects.bulk_create(
            [
                ModelPipelineStageRun(
                    workspace_id=self.workspace_id,
                    pipeline_run=run,
                    stage=stage,
                    sequence=index,
                )
                for index, stage in enumerate(self.stage_order, start=1)
            ]
        )
        pipeline.last_run_at = now
        pipeline.next_run_at = (
            _next_run_at(pipeline.cron_expression, now) if pipeline.schedule_enabled else None
        )
        pipeline.save(update_fields=["last_run_at", "next_run_at", "update_time"])
        return run.id

    def start_run(self, pipeline_id, data=None, trigger=ModelPipelineRunTrigger.MANUAL):
        run_id = self._create_run(pipeline_id, data or {}, trigger)
        self._execute_run(run_id)
        return self.get_run(run_id)

    def _deploy_run(self, run):
        if not run.pipeline.auto_deploy:
            self._set_stage(
                run,
                ModelPipelineStage.DEPLOY,
                ModelPipelineStageStatus.SKIPPED,
                output_snapshot={"reason": "流水线未启用自动部署"},
            )
        else:
            self._set_stage(
                run,
                ModelPipelineStage.DEPLOY,
                ModelPipelineStageStatus.RUNNING,
                input_snapshot={"model_version_id": str(run.model_version_id)},
            )
            release = ModelLifecycleService(self.workspace_id, self.user).publish_version(
                run.model_version_id,
                {"reason": f"训练流水线 {run.pipeline.name} 第 {run.run_number} 次运行自动发布"},
            )
            self._set_stage(
                run,
                ModelPipelineStage.DEPLOY,
                ModelPipelineStageStatus.SUCCESS,
                output_snapshot={"release": release["release"]},
            )
        run.status = ModelPipelineRunStatus.SUCCESS
        run.error_message = ""
        run.finished_at = timezone.now()
        run.save(update_fields=["status", "error_message", "finished_at", "update_time"])

    def _execute_run(self, run_id):
        run = self._runs().filter(id=run_id).first()
        if run is None:
            raise AppApiException(404, "流水线运行不存在")
        lifecycle = ModelLifecycleService(self.workspace_id, self.user)
        runner = get_model_pipeline_runner()
        current_stage = ModelPipelineStage.FEATURE
        experiment_id = None
        try:
            run.status = ModelPipelineRunStatus.RUNNING
            run.started_at = timezone.now()
            run.save(update_fields=["status", "started_at", "update_time"])
            experiment = lifecycle.create_experiment(
                {
                    "name": f"{run.pipeline.name}-run-{run.run_number}",
                    "description": "由自动训练流水线创建",
                    "source_type": "PIPELINE",
                    "dataset_name": run.config_snapshot["dataset_name"],
                    "dataset_version": run.config_snapshot.get("dataset_version", ""),
                    "parameters": run.config_snapshot.get("parameters", {}),
                    "tags": {"pipeline_id": str(run.pipeline_id), "run_number": run.run_number},
                }
            )
            experiment_id = experiment["id"]
            lifecycle.update_experiment(experiment_id, {"status": "RUNNING"})
            run.experiment_id = experiment_id
            run.save(update_fields=["experiment", "update_time"])

            self._set_stage(
                run,
                current_stage,
                ModelPipelineStageStatus.RUNNING,
                input_snapshot={
                    "dataset_name": run.config_snapshot["dataset_name"],
                    "dataset_version": run.config_snapshot.get("dataset_version", ""),
                },
            )
            feature_output = runner.build_features(run.config_snapshot)
            self._set_stage(run, current_stage, ModelPipelineStageStatus.SUCCESS, output_snapshot=feature_output)

            current_stage = ModelPipelineStage.TRAIN
            self._set_stage(
                run,
                current_stage,
                ModelPipelineStageStatus.RUNNING,
                input_snapshot={"feature_set": feature_output["feature_set"]},
            )
            train_output = runner.train(run.config_snapshot)
            self._set_stage(run, current_stage, ModelPipelineStageStatus.SUCCESS, output_snapshot=train_output)
            lifecycle.update_experiment(experiment_id, {"status": "SUCCESS"})
            version = lifecycle.create_version(
                {
                    "registry_name": run.config_snapshot["registry_name"],
                    "experiment_id": experiment_id,
                    "artifact_uri": train_output["artifact_uri"],
                    "artifact_digest": train_output["artifact_digest"],
                    "dataset_version": run.config_snapshot.get("dataset_version", ""),
                    "parameters": train_output["parameters"],
                    "metrics": run.config_snapshot["evaluation_metrics"],
                }
            )
            run.model_version_id = version["id"]
            run.save(update_fields=["model_version", "update_time"])

            current_stage = ModelPipelineStage.EVALUATE
            self._set_stage(
                run,
                current_stage,
                ModelPipelineStageStatus.RUNNING,
                input_snapshot={
                    "metrics": run.config_snapshot["evaluation_metrics"],
                    "thresholds": run.config_snapshot["thresholds"],
                },
            )
            evaluation = lifecycle.evaluate_version(
                run.model_version_id,
                {
                    "dataset_name": run.config_snapshot["dataset_name"],
                    "dataset_version": run.config_snapshot.get("dataset_version", ""),
                    "metrics": run.config_snapshot["evaluation_metrics"],
                    "thresholds": run.config_snapshot["thresholds"],
                    "summary": "训练流水线自动评估",
                },
            )
            self._set_stage(
                run,
                current_stage,
                ModelPipelineStageStatus.SUCCESS,
                output_snapshot={"evaluation": evaluation["evaluation"]},
            )
            if evaluation["evaluation"]["status"] != "PASSED":
                self._mark_run_failed(run, "模型评估未通过发布准入门槛")
                self._skip_remaining_stages(run, current_stage)
                return

            current_stage = ModelPipelineStage.APPROVE
            if run.pipeline.approval_mode == ModelPipelineApprovalMode.MANUAL:
                run.status = ModelPipelineRunStatus.WAITING_APPROVAL
                run.save(update_fields=["status", "update_time"])
                return

            self._set_stage(run, current_stage, ModelPipelineStageStatus.RUNNING)
            run.approved_by = self.user
            run.approved_at = timezone.now()
            run.approval_comment = "自动审批通过"
            run.save(update_fields=["approved_by", "approved_at", "approval_comment", "update_time"])
            self._set_stage(
                run,
                current_stage,
                ModelPipelineStageStatus.SUCCESS,
                output_snapshot={"action": "APPROVE", "comment": run.approval_comment},
            )
            self._deploy_run(run)
        except Exception as exc:
            message = exc.message if isinstance(exc, AppApiException) else str(exc)
            message = message or "流水线执行异常"
            self._set_stage(run, current_stage, ModelPipelineStageStatus.FAILED, error_message=message)
            self._skip_remaining_stages(run, current_stage)
            self._mark_run_failed(run, message)
            if experiment_id:
                try:
                    lifecycle.update_experiment(experiment_id, {"status": "FAILED"})
                except Exception:
                    pass

    def approve_run(self, run_id, data):
        serializer = ModelPipelineApprovalSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        with transaction.atomic():
            run = (
                ModelPipelineRun.objects.select_for_update()
                .filter(workspace_id=self.workspace_id, id=run_id)
                .first()
            )
            if run is None:
                raise AppApiException(404, "流水线运行不存在")
            if run.status != ModelPipelineRunStatus.WAITING_APPROVAL:
                raise AppApiException(400, "只有等待审批的流水线运行可以审批")
            run.approved_by = self.user
            run.approved_at = timezone.now()
            run.approval_comment = values["comment"]
            if values["action"] == "REJECT":
                self._set_stage(
                    run,
                    ModelPipelineStage.APPROVE,
                    ModelPipelineStageStatus.FAILED,
                    output_snapshot=values,
                    error_message=values["comment"] or "审批拒绝",
                )
                self._skip_remaining_stages(run, ModelPipelineStage.APPROVE)
                run.status = ModelPipelineRunStatus.REJECTED
                run.finished_at = timezone.now()
                run.save(
                    update_fields=[
                        "approved_by",
                        "approved_at",
                        "approval_comment",
                        "status",
                        "finished_at",
                        "update_time",
                    ]
                )
                return self.get_run(run.id)
            self._set_stage(
                run,
                ModelPipelineStage.APPROVE,
                ModelPipelineStageStatus.SUCCESS,
                output_snapshot=values,
            )
            run.save(update_fields=["approved_by", "approved_at", "approval_comment", "update_time"])
        run = self._runs().filter(id=run_id).first()
        try:
            self._deploy_run(run)
        except Exception as exc:
            message = exc.message if isinstance(exc, AppApiException) else str(exc)
            message = message or "模型部署异常"
            self._set_stage(run, ModelPipelineStage.DEPLOY, ModelPipelineStageStatus.FAILED, error_message=message)
            self._mark_run_failed(run, message)
        return self.get_run(run_id)

    def retry_run(self, run_id):
        run = self._runs().filter(id=run_id).first()
        if run is None:
            raise AppApiException(404, "流水线运行不存在")
        if run.status not in {ModelPipelineRunStatus.FAILED, ModelPipelineRunStatus.REJECTED}:
            raise AppApiException(400, "只有失败或审批拒绝的流水线运行可以重试")
        return self.start_run(
            run.pipeline_id,
            {"evaluation_metrics": run.config_snapshot["evaluation_metrics"]},
            ModelPipelineRunTrigger.RETRY,
        )


def run_due_training_pipelines(now=None):
    now = now or timezone.now()
    due_rows = list(
        ModelTrainingPipeline.objects.filter(
            active=True,
            schedule_enabled=True,
            next_run_at__lte=now,
        ).values_list("id", "workspace_id")
    )
    results = []
    for pipeline_id, workspace_id in due_rows:
        service = ModelPipelineService(workspace_id)
        try:
            results.append(service.start_run(pipeline_id, {}, ModelPipelineRunTrigger.SCHEDULED))
        except AppApiException as exc:
            pipeline = ModelTrainingPipeline.objects.filter(id=pipeline_id).first()
            if pipeline:
                pipeline.next_run_at = _next_run_at(pipeline.cron_expression, now)
                pipeline.save(update_fields=["next_run_at", "update_time"])
            results.append({"pipeline_id": str(pipeline_id), "status": "SKIPPED", "message": exc.message})
    return results
