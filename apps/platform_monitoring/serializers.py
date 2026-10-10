import socket
from collections import Counter, defaultdict
from urllib.request import Request, urlopen

from django.core.cache import cache
from django.db import connection, transaction
from django.db.models import Max
from django.utils import timezone
from rest_framework import serializers

from common.exception.app_exception import AppApiException
from knowledge.models import (
    Document,
    Knowledge,
    KnowledgeEtlRun,
    KnowledgeEtlRunStatus,
    KnowledgeEvaluationRun,
    KnowledgeEvaluationRunStatus,
    KnowledgeIndexVersion,
    KnowledgeIndexVersionStatus,
)
from marketing.serializers.notifications import MarketingNotificationService
from models_provider.models import (
    LifecycleModelVersion,
    LifecycleModelVersionStatus,
    ModelEvaluationRun,
    ModelEvaluationStatus,
    ModelPipelineRun,
    ModelPipelineRunStatus,
)
from telecom_ai_agent.const import CONFIG

from .models import (
    MonitoringAlertStatus,
    MonitoringAutoAction,
    MonitoringMetricStatus,
    MonitoringOperator,
    MonitoringRunStatus,
    MonitoringScope,
    PlatformMetricSnapshot,
    PlatformMonitoringAlert,
    PlatformMonitoringRule,
    PlatformMonitoringRun,
)


METRIC_CATALOG = {
    "model_pipeline_success_rate": (MonitoringScope.MODEL, "训练流水线成功率", "%"),
    "model_pipeline_failure_count": (MonitoringScope.MODEL, "训练流水线失败数", "次"),
    "model_evaluation_pass_rate": (MonitoringScope.MODEL, "模型评估通过率", "%"),
    "published_model_count": (MonitoringScope.MODEL, "已发布模型版本", "个"),
    "etl_success_rate": (MonitoringScope.DATA, "ETL 成功率", "%"),
    "etl_failure_count": (MonitoringScope.DATA, "ETL 失败数", "次"),
    "etl_quality_score": (MonitoringScope.DATA, "ETL 平均质量分", "分"),
    "index_embedding_coverage": (MonitoringScope.DATA, "索引向量覆盖率", "%"),
    "knowledge_active_document_count": (MonitoringScope.KNOWLEDGE, "有效知识文档", "篇"),
    "knowledge_stale_days": (MonitoringScope.KNOWLEDGE, "知识最长未更新时间", "天"),
    "knowledge_retrieval_hit_rate": (MonitoringScope.KNOWLEDGE, "检索评估命中率", "%"),
    "published_index_count": (MonitoringScope.KNOWLEDGE, "已发布索引版本", "个"),
    "backend_available": (MonitoringScope.RESOURCE, "后端服务", ""),
    "database_available": (MonitoringScope.RESOURCE, "PostgreSQL", ""),
    "redis_available": (MonitoringScope.RESOURCE, "Redis", ""),
    "ollama_available": (MonitoringScope.RESOURCE, "Ollama", ""),
    "vector_service_available": (MonitoringScope.RESOURCE, "向量服务", ""),
}


DEFAULT_RULES = (
    ("训练失败自动重试", "model_pipeline_failure_count", "GTE", 1, 3, "RETRY_FAILED_RUN"),
    ("模型评估质量门禁", "model_evaluation_pass_rate", "LT", 80, 50, "CREATE_ROLLBACK_TASK"),
    ("ETL 失败自动重试", "etl_failure_count", "GTE", 1, 3, "RETRY_FAILED_RUN"),
    ("ETL 数据质量门禁", "etl_quality_score", "LT", 80, 60, "CREATE_ROLLBACK_TASK"),
    ("知识内容时效", "knowledge_stale_days", "GT", 30, 90, "NONE"),
    ("知识检索效果", "knowledge_retrieval_hit_rate", "LT", 70, 50, "NONE"),
    ("PostgreSQL 可用性", "database_available", "LT", 1, 0.5, "NONE"),
    ("Redis 可用性", "redis_available", "LT", 1, 0.5, "NONE"),
    ("Ollama 可用性", "ollama_available", "LT", 1, 0.5, "NONE"),
    ("向量服务可用性", "vector_service_available", "LT", 1, 0.5, "NONE"),
)


class MonitoringRuleWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=128)
    metric_key = serializers.ChoiceField(choices=tuple(METRIC_CATALOG))
    operator = serializers.ChoiceField(choices=MonitoringOperator.choices, default=MonitoringOperator.GTE)
    warning_threshold = serializers.FloatField(required=False, allow_null=True)
    critical_threshold = serializers.FloatField(required=False, allow_null=True)
    enabled = serializers.BooleanField(default=True)
    auto_action = serializers.ChoiceField(choices=MonitoringAutoAction.choices, default=MonitoringAutoAction.NONE)
    cooldown_minutes = serializers.IntegerField(min_value=1, max_value=10080, default=30)
    description = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")

    def validate(self, attrs):
        if attrs.get("warning_threshold") is None and attrs.get("critical_threshold") is None:
            raise serializers.ValidationError("关注阈值和紧急阈值至少填写一项")
        return attrs


def _percentage(part, total):
    return round(part * 100 / total, 2) if total else 100.0


def _metric(metric_key, value, details=None, status=MonitoringMetricStatus.HEALTHY):
    scope, name, unit = METRIC_CATALOG[metric_key]
    return {
        "scope": scope,
        "metric_key": metric_key,
        "metric_name": name,
        "value": round(float(value), 2),
        "unit": unit,
        "status": status,
        "details": details or {},
    }


def serialize_metric(row):
    return {
        "id": str(row.id),
        "scope": row.scope,
        "scope_label": row.get_scope_display(),
        "metric_key": row.metric_key,
        "metric_name": row.metric_name,
        "value": row.value,
        "unit": row.unit,
        "status": row.status,
        "status_label": row.get_status_display(),
        "details": row.details,
        "collected_at": row.collected_at,
    }


def serialize_rule(row):
    return {
        "id": str(row.id),
        "name": row.name,
        "scope": row.scope,
        "scope_label": row.get_scope_display(),
        "metric_key": row.metric_key,
        "metric_name": METRIC_CATALOG.get(row.metric_key, ("", row.metric_key, ""))[1],
        "operator": row.operator,
        "operator_label": row.get_operator_display(),
        "warning_threshold": row.warning_threshold,
        "critical_threshold": row.critical_threshold,
        "enabled": row.enabled,
        "auto_action": row.auto_action,
        "auto_action_label": row.get_auto_action_display(),
        "cooldown_minutes": row.cooldown_minutes,
        "description": row.description,
        "update_time": row.update_time,
    }


def serialize_alert(row):
    return {
        "id": str(row.id),
        "rule_id": str(row.rule_id) if row.rule_id else None,
        "scope": row.scope,
        "scope_label": row.get_scope_display(),
        "metric_key": row.metric_key,
        "metric_name": METRIC_CATALOG.get(row.metric_key, ("", row.metric_key, ""))[1],
        "title": row.title,
        "message": row.message,
        "severity": row.severity,
        "status": row.status,
        "status_label": row.get_status_display(),
        "observed_value": row.observed_value,
        "threshold_value": row.threshold_value,
        "auto_action": row.auto_action,
        "response_status": row.response_status,
        "response_detail": row.response_detail,
        "first_triggered_at": row.first_triggered_at,
        "last_triggered_at": row.last_triggered_at,
        "acknowledged_at": row.acknowledged_at,
        "resolved_at": row.resolved_at,
    }


class PlatformMonitoringService:
    def __init__(self, workspace_id, user=None):
        self.workspace_id = workspace_id
        self.user = user

    def _rules(self):
        return PlatformMonitoringRule.objects.filter(workspace_id=self.workspace_id)

    def _alerts(self):
        return PlatformMonitoringAlert.objects.filter(workspace_id=self.workspace_id).select_related("rule", "metric")

    def ensure_default_rules(self):
        created = 0
        for name, metric_key, operator, warning, critical, auto_action in DEFAULT_RULES:
            scope = METRIC_CATALOG[metric_key][0]
            _, was_created = PlatformMonitoringRule.objects.get_or_create(
                workspace_id=self.workspace_id,
                metric_key=metric_key,
                name=name,
                defaults={
                    "scope": scope,
                    "operator": operator,
                    "warning_threshold": warning,
                    "critical_threshold": critical,
                    "auto_action": auto_action,
                    "updated_by": self.user,
                    "description": "平台监控 V1 默认规则",
                },
            )
            created += int(was_created)
        return created

    def list_rules(self):
        return [serialize_rule(row) for row in self._rules()]

    def save_rule(self, data, rule_id=None):
        row = self._rules().filter(id=rule_id).first() if rule_id else None
        if rule_id and row is None:
            raise AppApiException(404, "监控规则不存在")
        payload = data
        if row is not None:
            payload = {
                "name": row.name,
                "metric_key": row.metric_key,
                "operator": row.operator,
                "warning_threshold": row.warning_threshold,
                "critical_threshold": row.critical_threshold,
                "enabled": row.enabled,
                "auto_action": row.auto_action,
                "cooldown_minutes": row.cooldown_minutes,
                "description": row.description,
            }
            payload.update(data)
        serializer = MonitoringRuleWriteSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        if row is None:
            metric_key = values["metric_key"]
            row = PlatformMonitoringRule(workspace_id=self.workspace_id, scope=METRIC_CATALOG[metric_key][0])
        elif "metric_key" in values:
            row.scope = METRIC_CATALOG[values["metric_key"]][0]
        for key, value in values.items():
            setattr(row, key, value)
        row.updated_by = self.user
        row.save()
        return serialize_rule(row)

    def _collect_model_metrics(self):
        pipeline_runs = ModelPipelineRun.objects.filter(workspace_id=self.workspace_id)
        pipeline_terminal = pipeline_runs.filter(
            status__in=[ModelPipelineRunStatus.SUCCESS, ModelPipelineRunStatus.FAILED, ModelPipelineRunStatus.REJECTED]
        )
        pipeline_success = pipeline_terminal.filter(status=ModelPipelineRunStatus.SUCCESS).count()
        pipeline_failed = pipeline_terminal.exclude(status=ModelPipelineRunStatus.SUCCESS).count()
        evaluations = ModelEvaluationRun.objects.filter(workspace_id=self.workspace_id)
        evaluation_terminal = evaluations.filter(
            status__in=[ModelEvaluationStatus.PASSED, ModelEvaluationStatus.FAILED, ModelEvaluationStatus.ERROR]
        )
        evaluation_passed = evaluation_terminal.filter(status=ModelEvaluationStatus.PASSED).count()
        published = LifecycleModelVersion.objects.filter(
            workspace_id=self.workspace_id,
            status=LifecycleModelVersionStatus.PUBLISHED,
        ).count()
        return [
            _metric(
                "model_pipeline_success_rate",
                _percentage(pipeline_success, pipeline_terminal.count()),
                {"success": pipeline_success, "terminal": pipeline_terminal.count()},
            ),
            _metric("model_pipeline_failure_count", pipeline_failed, {"terminal": pipeline_terminal.count()}),
            _metric(
                "model_evaluation_pass_rate",
                _percentage(evaluation_passed, evaluation_terminal.count()),
                {"passed": evaluation_passed, "terminal": evaluation_terminal.count()},
            ),
            _metric("published_model_count", published),
        ]

    def _collect_data_metrics(self):
        runs = KnowledgeEtlRun.objects.filter(workspace_id=self.workspace_id)
        terminal = runs.filter(status__in=[KnowledgeEtlRunStatus.SUCCESS, KnowledgeEtlRunStatus.FAILED])
        success = terminal.filter(status=KnowledgeEtlRunStatus.SUCCESS).count()
        failed = terminal.filter(status=KnowledgeEtlRunStatus.FAILED).count()
        quality_scores = [
            float(value)
            for value in terminal.exclude(quality_result={}).values_list("quality_result__score", flat=True)
            if value is not None
        ]
        versions = KnowledgeIndexVersion.objects.filter(workspace_id=self.workspace_id)
        paragraph_total = sum(versions.values_list("paragraph_count", flat=True))
        embedding_total = sum(versions.values_list("embedding_count", flat=True))
        coverage = _percentage(min(embedding_total, paragraph_total), paragraph_total)
        return [
            _metric("etl_success_rate", _percentage(success, terminal.count()), {"success": success, "terminal": terminal.count()}),
            _metric("etl_failure_count", failed, {"terminal": terminal.count()}),
            _metric("etl_quality_score", sum(quality_scores) / len(quality_scores) if quality_scores else 100),
            _metric(
                "index_embedding_coverage",
                coverage,
                {"paragraph_count": paragraph_total, "embedding_count": embedding_total},
            ),
        ]

    def _collect_knowledge_metrics(self):
        knowledge = Knowledge.objects.filter(workspace_id=self.workspace_id)
        documents = Document.objects.filter(knowledge__in=knowledge, is_active=True)
        latest_update = documents.aggregate(value=Max("update_time"))["value"]
        stale_days = (timezone.now() - latest_update).days if latest_update else 0
        latest_evaluation = (
            KnowledgeEvaluationRun.objects.filter(
                workspace_id=self.workspace_id,
                status__in=[KnowledgeEvaluationRunStatus.SUCCESS, KnowledgeEvaluationRunStatus.PARTIAL],
            )
            .order_by("-finished_at", "-create_time")
            .first()
        )
        hit_rate = float((latest_evaluation.summary or {}).get("best_hit_rate", 100)) if latest_evaluation else 100
        published_indexes = KnowledgeIndexVersion.objects.filter(
            workspace_id=self.workspace_id,
            status=KnowledgeIndexVersionStatus.PUBLISHED,
        ).count()
        return [
            _metric("knowledge_active_document_count", documents.count(), {"knowledge_count": knowledge.count()}),
            _metric("knowledge_stale_days", stale_days, {"latest_update": latest_update.isoformat() if latest_update else None}),
            _metric(
                "knowledge_retrieval_hit_rate",
                hit_rate,
                {"evaluation_run_id": str(latest_evaluation.id) if latest_evaluation else None},
            ),
            _metric("published_index_count", published_indexes),
        ]

    @staticmethod
    def _http_available(url):
        try:
            request = Request(url, headers={"User-Agent": "telecom-ai-monitor/1.0"})
            with urlopen(request, timeout=2) as response:
                return response.status < 500, {"status_code": response.status}
        except Exception as exc:
            code = getattr(exc, "code", None)
            if code is not None and code < 500:
                return True, {"status_code": code}
            return False, {"error": exc.__class__.__name__}

    def _collect_resource_metrics(self):
        results = [_metric("backend_available", 1, {"message": "采集接口响应正常"})]
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            results.append(_metric("database_available", 1))
        except Exception as exc:
            results.append(_metric("database_available", 0, {"error": exc.__class__.__name__}, MonitoringMetricStatus.CRITICAL))
        try:
            key = f"platform-monitoring:{self.workspace_id}:health"
            cache.set(key, "ok", 10)
            available = cache.get(key) == "ok"
            results.append(
                _metric("redis_available", int(available), {}, MonitoringMetricStatus.HEALTHY if available else MonitoringMetricStatus.CRITICAL)
            )
        except Exception as exc:
            results.append(_metric("redis_available", 0, {"error": exc.__class__.__name__}, MonitoringMetricStatus.CRITICAL))
        ollama_ok, ollama_details = self._http_available("http://127.0.0.1:11434/api/tags")
        results.append(
            _metric(
                "ollama_available",
                int(ollama_ok),
                ollama_details,
                MonitoringMetricStatus.HEALTHY if ollama_ok else MonitoringMetricStatus.CRITICAL,
            )
        )
        vector_host = str(CONFIG.get("LOCAL_MODEL_HOST") or "127.0.0.1")
        vector_port = int(CONFIG.get("LOCAL_MODEL_PORT") or 11636)
        try:
            with socket.create_connection((vector_host, vector_port), timeout=2):
                pass
            vector_ok, vector_details = True, {"probe": "tcp", "port": vector_port}
        except OSError as exc:
            vector_ok, vector_details = False, {"probe": "tcp", "port": vector_port, "error": exc.__class__.__name__}
        results.append(
            _metric(
                "vector_service_available",
                int(vector_ok),
                vector_details,
                MonitoringMetricStatus.HEALTHY if vector_ok else MonitoringMetricStatus.CRITICAL,
            )
        )
        return results

    @staticmethod
    def _breached(value, threshold, operator):
        if threshold is None:
            return False
        return {
            MonitoringOperator.GT: value > threshold,
            MonitoringOperator.GTE: value >= threshold,
            MonitoringOperator.LT: value < threshold,
            MonitoringOperator.LTE: value <= threshold,
        }[operator]

    def _execute_auto_action(self, alert, execute=False):
        if alert.auto_action == MonitoringAutoAction.NONE:
            return "NOT_REQUIRED", {}
        if alert.auto_action == MonitoringAutoAction.CREATE_ROLLBACK_TASK:
            return "TASK_CREATED", {
                "task_type": "ROLLBACK_REVIEW",
                "message": "已生成回滚评审任务，待确认安全版本后执行",
                "target_route": "/model/lifecycle",
            }
        if not execute:
            if alert.metric_key == "model_pipeline_failure_count":
                failed = (
                    ModelPipelineRun.objects.filter(
                        workspace_id=self.workspace_id,
                        status__in=[ModelPipelineRunStatus.FAILED, ModelPipelineRunStatus.REJECTED],
                    )
                    .order_by("-create_time")
                    .first()
                )
            elif alert.metric_key == "etl_failure_count":
                failed = (
                    KnowledgeEtlRun.objects.filter(workspace_id=self.workspace_id, status=KnowledgeEtlRunStatus.FAILED)
                    .order_by("-create_time")
                    .first()
                )
            else:
                failed = None
            if failed:
                return "TASK_CREATED", {
                    "task_type": "RETRY_FAILED_RUN",
                    "source_run_id": str(failed.id),
                    "message": "已生成失败任务重试项，确认后执行",
                }
            return "SKIPPED", {"message": "当前没有可重试的失败任务"}
        try:
            if alert.metric_key == "model_pipeline_failure_count":
                failed = (
                    ModelPipelineRun.objects.filter(
                        workspace_id=self.workspace_id,
                        status__in=[ModelPipelineRunStatus.FAILED, ModelPipelineRunStatus.REJECTED],
                    )
                    .order_by("-create_time")
                    .first()
                )
                if failed:
                    from models_provider.serializers.pipeline import ModelPipelineService

                    retried = ModelPipelineService(self.workspace_id, self.user).retry_run(str(failed.id))
                    return "SUCCEEDED", {"source_run_id": str(failed.id), "retry_run_id": retried["id"]}
            if alert.metric_key == "etl_failure_count":
                failed = (
                    KnowledgeEtlRun.objects.filter(workspace_id=self.workspace_id, status=KnowledgeEtlRunStatus.FAILED)
                    .order_by("-create_time")
                    .first()
                )
                if failed:
                    from knowledge.serializers.etl import KnowledgeEtlService

                    retried = KnowledgeEtlService(self.workspace_id, str(failed.knowledge_id), self.user).retry_run(
                        str(failed.id)
                    )
                    return "SUCCEEDED", {"source_run_id": str(failed.id), "retry_run_id": retried["id"]}
            return "SKIPPED", {"message": "当前没有可重试的失败任务"}
        except Exception as exc:
            return "FAILED", {"error": str(exc)[:500] or exc.__class__.__name__}

    def _evaluate_rules(self, metrics):
        rules_by_key = defaultdict(list)
        for rule in self._rules().filter(enabled=True):
            rules_by_key[rule.metric_key].append(rule)
        alert_changes = {"created": 0, "refreshed": 0, "resolved": 0, "notifications": 0}
        now = timezone.now()
        for metric in metrics:
            strongest_status = metric.status
            for rule in rules_by_key.get(metric.metric_key, []):
                severity = None
                threshold = None
                if self._breached(metric.value, rule.critical_threshold, rule.operator):
                    severity, threshold = MonitoringMetricStatus.CRITICAL, rule.critical_threshold
                elif self._breached(metric.value, rule.warning_threshold, rule.operator):
                    severity, threshold = MonitoringMetricStatus.WARNING, rule.warning_threshold
                dedupe_key = f"platform:{rule.id}"
                existing = self._alerts().filter(dedupe_key=dedupe_key).first()
                if severity:
                    if severity == MonitoringMetricStatus.CRITICAL or strongest_status == MonitoringMetricStatus.HEALTHY:
                        strongest_status = severity
                    title = f"{metric.metric_name}{'紧急' if severity == MonitoringMetricStatus.CRITICAL else '异常'}"
                    message = f"当前值 {metric.value:g}{metric.unit}，触发{rule.get_operator_display()} {threshold:g} 阈值"
                    created = existing is None or existing.status == MonitoringAlertStatus.RESOLVED
                    if existing is None:
                        existing = PlatformMonitoringAlert(
                            workspace_id=self.workspace_id,
                            rule=rule,
                            dedupe_key=dedupe_key,
                            first_triggered_at=now,
                        )
                    elif existing.status == MonitoringAlertStatus.RESOLVED:
                        existing.status = MonitoringAlertStatus.OPEN
                        existing.first_triggered_at = now
                        existing.resolved_at = None
                        existing.acknowledged_at = None
                    existing.metric = metric
                    existing.scope = rule.scope
                    existing.metric_key = rule.metric_key
                    existing.title = title
                    existing.message = message
                    existing.severity = severity
                    existing.observed_value = metric.value
                    existing.threshold_value = threshold
                    existing.auto_action = rule.auto_action
                    existing.last_triggered_at = now
                    existing.operator = self.user
                    if created:
                        existing.response_status, existing.response_detail = self._execute_auto_action(existing)
                    existing.save()
                    if created:
                        alert_changes["created"] += 1
                        alert_changes["notifications"] += MarketingNotificationService(
                            self.workspace_id, self.user
                        ).dispatch_platform_alert(existing)
                    else:
                        alert_changes["refreshed"] += 1
                elif existing and existing.status != MonitoringAlertStatus.RESOLVED:
                    existing.status = MonitoringAlertStatus.RESOLVED
                    existing.resolved_at = now
                    existing.metric = metric
                    existing.last_triggered_at = now
                    existing.save(update_fields=["status", "resolved_at", "metric", "last_triggered_at", "update_time"])
                    alert_changes["resolved"] += 1
            if metric.status != strongest_status:
                metric.status = strongest_status
                metric.save(update_fields=["status", "update_time"])
        return alert_changes

    @transaction.atomic
    def collect(self, trigger="MANUAL"):
        self.ensure_default_rules()
        run = PlatformMonitoringRun.objects.create(
            workspace_id=self.workspace_id,
            trigger=trigger,
            operator=self.user,
        )
        now = timezone.now()
        collectors = (
            self._collect_model_metrics,
            self._collect_data_metrics,
            self._collect_knowledge_metrics,
            self._collect_resource_metrics,
        )
        errors = []
        payloads = []
        for collector in collectors:
            try:
                payloads.extend(collector())
            except Exception as exc:
                errors.append(f"{collector.__name__}: {exc.__class__.__name__}")
        metrics = [
            PlatformMetricSnapshot.objects.create(
                workspace_id=self.workspace_id,
                run=run,
                collected_at=now,
                **payload,
            )
            for payload in payloads
        ]
        alert_changes = self._evaluate_rules(metrics)
        run.status = (
            MonitoringRunStatus.FAILED
            if not metrics
            else MonitoringRunStatus.PARTIAL
            if errors
            else MonitoringRunStatus.SUCCESS
        )
        status_counts = Counter(item.status for item in metrics)
        run.summary = {
            "metric_count": len(metrics),
            "healthy_count": status_counts[MonitoringMetricStatus.HEALTHY],
            "warning_count": status_counts[MonitoringMetricStatus.WARNING],
            "critical_count": status_counts[MonitoringMetricStatus.CRITICAL],
            "alert_changes": alert_changes,
        }
        run.error_message = "；".join(errors)
        run.finished_at = now
        run.save(update_fields=["status", "summary", "error_message", "finished_at", "update_time"])
        return self.dashboard()

    def dashboard(self):
        latest_run = PlatformMonitoringRun.objects.filter(workspace_id=self.workspace_id).first()
        metrics = list(latest_run.metrics.all()) if latest_run else []
        grouped = {scope: [] for scope in MonitoringScope.values}
        for metric in metrics:
            grouped[metric.scope].append(serialize_metric(metric))
        recent_rows = PlatformMetricSnapshot.objects.filter(workspace_id=self.workspace_id).order_by("-collected_at")[:170]
        trend_map = defaultdict(list)
        for row in recent_rows:
            if len(trend_map[row.metric_key]) < 10:
                trend_map[row.metric_key].append({"value": row.value, "collected_at": row.collected_at})
        active_alerts = self._alerts().exclude(status=MonitoringAlertStatus.RESOLVED)
        return {
            "latest_run": {
                "id": str(latest_run.id),
                "status": latest_run.status,
                "summary": latest_run.summary,
                "error_message": latest_run.error_message,
                "finished_at": latest_run.finished_at,
            }
            if latest_run
            else None,
            "scopes": [
                {"scope": scope, "scope_label": label, "metrics": grouped[scope]}
                for scope, label in MonitoringScope.choices
            ],
            "trends": trend_map,
            "summary": {
                "metric_count": len(metrics),
                "active_alert_count": active_alerts.count(),
                "critical_alert_count": active_alerts.filter(severity=MonitoringMetricStatus.CRITICAL).count(),
                "rule_count": self._rules().count(),
            },
        }

    def list_alerts(self, status=""):
        rows = self._alerts()
        if status:
            rows = rows.filter(status=status)
        return [serialize_alert(row) for row in rows[:100]]

    def operate_alert(self, alert_id, action):
        row = self._alerts().filter(id=alert_id).first()
        if row is None:
            raise AppApiException(404, "平台监控告警不存在")
        now = timezone.now()
        if action == "ACKNOWLEDGE":
            if row.status == MonitoringAlertStatus.RESOLVED:
                raise AppApiException(400, "已恢复告警无需确认")
            row.status = MonitoringAlertStatus.ACKNOWLEDGED
            row.acknowledged_at = now
        elif action == "RESOLVE":
            row.status = MonitoringAlertStatus.RESOLVED
            row.resolved_at = now
        elif action == "RETRY_RESPONSE":
            row.response_status, row.response_detail = self._execute_auto_action(row, execute=True)
        else:
            raise AppApiException(400, "不支持的告警操作")
        row.operator = self.user
        row.save()
        return serialize_alert(row)


def collect_all_workspaces():
    workspace_ids = set(Knowledge.objects.values_list("workspace_id", flat=True))
    workspace_ids.update(ModelPipelineRun.objects.values_list("workspace_id", flat=True))
    workspace_ids.update(PlatformMonitoringRule.objects.values_list("workspace_id", flat=True))
    workspace_ids.discard("")
    results = []
    for workspace_id in sorted(workspace_ids or {"default"}):
        try:
            dashboard = PlatformMonitoringService(workspace_id).collect(trigger="SCHEDULED")
            results.append({"workspace_id": workspace_id, "status": dashboard["latest_run"]["status"]})
        except Exception as exc:
            results.append({"workspace_id": workspace_id, "status": "FAILED", "error": exc.__class__.__name__})
    return results
