import json
import math
import re
from collections import Counter
from datetime import timedelta

from django.db import transaction
from django.db.models import Avg, Count, Max, Min
from django.utils import timezone
from rest_framework import serializers

from common.exception.app_exception import AppApiException
from marketing.serializers.notifications import MarketingNotificationService
from users.models import User

from .models import (
    MetricAlertDirection,
    MetricAlertIncident,
    MetricAlertRule,
    MetricAlertRuleVersion,
    MetricBatchStatus,
    MetricCollectionBatch,
    MetricComplianceStatus,
    MetricDataSource,
    MetricDefinition,
    MetricDispatchEventAction,
    MetricDispatchOrder,
    MetricDispatchOrderEvent,
    MetricDutyShift,
    MetricDynamicBaseline,
    MetricIncidentStatus,
    MetricObservation,
    MetricRuleMode,
    MetricSourceType,
    MetricTheme,
    MetricWorkOrderStatus,
    MonitoringMetricStatus,
)


THEME_DEMO_METRICS = (
    (MetricTheme.TROUBLESHOOTING, "fault_recovery_minutes", "故障平均恢复时长", "分钟"),
    (MetricTheme.SECURITY, "security_risk_count", "未闭环安全隐患", "项"),
    (MetricTheme.COST, "resource_cost_efficiency", "资源成本效能", "%"),
    (MetricTheme.DELIVERY, "delivery_on_time_rate", "客户按期交付率", "%"),
    (MetricTheme.NETWORK, "network_availability", "网络可用率", "%"),
    (MetricTheme.CAPABILITY, "service_capacity_usage", "服务能力使用率", "%"),
    (MetricTheme.MAINTENANCE, "maintenance_optimization_rate", "维护优化完成率", "%"),
    (MetricTheme.DATA_RISK, "network_data_risk_count", "涉网涉数风险数", "项"),
)


class MetricDefinitionWriteSerializer(serializers.Serializer):
    metric_key = serializers.RegexField(r"^[a-z][a-z0-9_]{2,95}$")
    name = serializers.CharField(max_length=160)
    theme = serializers.ChoiceField(choices=MetricTheme.choices)
    unit = serializers.CharField(required=False, allow_blank=True, max_length=32, default="")
    description = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")
    dimensions_schema = serializers.ListField(
        child=serializers.CharField(max_length=64), required=False, default=list
    )
    enabled = serializers.BooleanField(default=True)


class MetricDataSourceWriteSerializer(serializers.Serializer):
    source_key = serializers.RegexField(r"^[a-z][a-z0-9_]{2,95}$")
    name = serializers.CharField(max_length=160)
    source_type = serializers.ChoiceField(choices=MetricSourceType.choices, default=MetricSourceType.MANUAL)
    config_snapshot = serializers.DictField(required=False, default=dict)
    enabled = serializers.BooleanField(default=True)

    def validate_config_snapshot(self, value):
        sensitive_keys = {"password", "secret", "token", "api_key", "credential", "credentials"}

        def contains_sensitive_key(item):
            if isinstance(item, dict):
                return any(
                    str(key).lower() in sensitive_keys or contains_sensitive_key(nested)
                    for key, nested in item.items()
                )
            if isinstance(item, list):
                return any(contains_sensitive_key(nested) for nested in item)
            return False

        if contains_sensitive_key(value):
            raise serializers.ValidationError("数据源配置只保存非敏感连接元数据，不得提交密码或密钥")
        return value


class MetricDutyShiftWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=160)
    starts_at = serializers.DateTimeField()
    ends_at = serializers.DateTimeField()
    assignee_id = serializers.UUIDField()
    enabled = serializers.BooleanField(default=True)

    def validate(self, attrs):
        if attrs["starts_at"] >= attrs["ends_at"]:
            raise serializers.ValidationError("值班结束时间必须晚于开始时间")
        return attrs


class MetricOrderOperateSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=("ASSIGN", "TRANSFER", "CLAIM", "START", "COMMENT", "RESOLVE", "CLOSE")
    )
    assignee_id = serializers.UUIDField(required=False)
    note = serializers.CharField(required=False, allow_blank=True, max_length=2000, default="")

    def validate(self, attrs):
        if attrs["action"] in ("ASSIGN", "TRANSFER") and not attrs.get("assignee_id"):
            raise serializers.ValidationError({"assignee_id": "指派或转派必须选择处理人"})
        if attrs["action"] == "COMMENT" and not attrs.get("note", "").strip():
            raise serializers.ValidationError({"note": "备注内容不能为空"})
        return attrs


class MetricRuleWriteSerializer(serializers.Serializer):
    definition_id = serializers.UUIDField()
    name = serializers.CharField(max_length=160)
    mode = serializers.ChoiceField(choices=MetricRuleMode.choices, default=MetricRuleMode.STATIC)
    direction = serializers.ChoiceField(choices=MetricAlertDirection.choices, default=MetricAlertDirection.ABOVE)
    warning_threshold = serializers.FloatField(required=False, allow_null=True)
    critical_threshold = serializers.FloatField(required=False, allow_null=True)
    warning_deviation = serializers.FloatField(min_value=0.1, max_value=20, default=1.5)
    critical_deviation = serializers.FloatField(min_value=0.1, max_value=20, default=2.5)
    baseline_window = serializers.IntegerField(min_value=3, max_value=200, default=5)
    dimension_filter = serializers.DictField(required=False, default=dict)
    active_windows = serializers.ListField(child=serializers.DictField(), required=False, default=list)
    enabled = serializers.BooleanField(default=True)


class MetricImportRowSerializer(serializers.Serializer):
    metric_key = serializers.CharField(max_length=96)
    value = serializers.FloatField()
    dimensions = serializers.DictField(required=False, default=dict)
    observed_at = serializers.DateTimeField(required=False)


class MetricBatchImportSerializer(serializers.Serializer):
    batch_no = serializers.CharField(max_length=96)
    source_key = serializers.CharField(max_length=96, required=False, allow_blank=True, default="")
    rows = serializers.ListField(child=serializers.DictField(), min_length=1, max_length=5000)


class MetricAnalyticsQuerySerializer(serializers.Serializer):
    theme = serializers.ChoiceField(choices=MetricTheme.choices, required=False, allow_blank=True)
    definition_id = serializers.UUIDField(required=False)
    device = serializers.CharField(required=False, allow_blank=True, max_length=160)
    network_element = serializers.CharField(required=False, allow_blank=True, max_length=160)
    time_slot = serializers.CharField(required=False, allow_blank=True, max_length=160)
    start = serializers.DateTimeField(required=False)
    end = serializers.DateTimeField(required=False)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=500, default=200)

    def validate(self, attrs):
        if attrs.get("start") and attrs.get("end") and attrs["start"] > attrs["end"]:
            raise serializers.ValidationError("查询结束时间必须晚于开始时间")
        return attrs


def serialize_definition(row):
    return {
        "id": str(row.id),
        "metric_key": row.metric_key,
        "name": row.name,
        "theme": row.theme,
        "theme_label": row.get_theme_display(),
        "unit": row.unit,
        "description": row.description,
        "dimensions_schema": row.dimensions_schema,
        "enabled": row.enabled,
    }


def serialize_source(row):
    return {
        "id": str(row.id),
        "source_key": row.source_key,
        "name": row.name,
        "source_type": row.source_type,
        "source_type_label": row.get_source_type_display(),
        "config_snapshot": row.config_snapshot,
        "enabled": row.enabled,
        "update_time": row.update_time,
    }


def serialize_duty_shift(row):
    return {
        "id": str(row.id),
        "name": row.name,
        "starts_at": row.starts_at,
        "ends_at": row.ends_at,
        "assignee_id": str(row.assignee_id),
        "assignee_name": row.assignee.nick_name or row.assignee.username,
        "contact_snapshot": row.contact_snapshot,
        "enabled": row.enabled,
    }


def serialize_order_event(row):
    return {
        "id": str(row.id),
        "action": row.action,
        "action_label": row.get_action_display(),
        "from_status": row.from_status,
        "to_status": row.to_status,
        "note": row.note,
        "snapshot": row.snapshot,
        "operator_id": str(row.operator_id) if row.operator_id else None,
        "operator_name": (row.operator.nick_name or row.operator.username) if row.operator else "系统",
        "occurred_at": row.occurred_at,
    }


def serialize_rule(row):
    return {
        "id": str(row.id),
        "definition_id": str(row.definition_id),
        "metric_key": row.definition.metric_key,
        "metric_name": row.definition.name,
        "theme": row.definition.theme,
        "theme_label": row.definition.get_theme_display(),
        "name": row.name,
        "mode": row.mode,
        "mode_label": row.get_mode_display(),
        "direction": row.direction,
        "direction_label": row.get_direction_display(),
        "warning_threshold": row.warning_threshold,
        "critical_threshold": row.critical_threshold,
        "warning_deviation": row.warning_deviation,
        "critical_deviation": row.critical_deviation,
        "baseline_window": row.baseline_window,
        "dimension_filter": row.dimension_filter,
        "active_windows": row.active_windows,
        "config_version": row.config_version,
        "config_snapshot": row.config_snapshot,
        "compliance_status": row.compliance_status,
        "compliance_issues": row.compliance_issues,
        "enabled": row.enabled,
        "update_time": row.update_time,
    }


def serialize_order(row):
    incident = row.incident
    return {
        "id": str(row.id),
        "incident_id": str(incident.id),
        "title": row.title,
        "status": row.status,
        "status_label": row.get_status_display(),
        "severity": incident.severity,
        "metric_name": incident.rule.definition.name,
        "theme_label": incident.rule.definition.get_theme_display(),
        "observed_value": incident.observed_value,
        "threshold_value": incident.threshold_value,
        "assignee_id": str(row.assignee_id) if row.assignee_id else None,
        "assignee_name": row.assignee.nick_name or row.assignee.username if row.assignee else "",
        "assignment_snapshot": row.assignment_snapshot,
        "create_time": row.create_time,
        "claimed_at": row.claimed_at,
        "resolved_at": row.resolved_at,
        "closed_at": row.closed_at,
    }


class MetricFoundationService:
    def __init__(self, workspace_id, user=None):
        self.workspace_id = workspace_id
        self.user = user

    def _definitions(self):
        return MetricDefinition.objects.filter(workspace_id=self.workspace_id)

    def _rules(self):
        return MetricAlertRule.objects.filter(workspace_id=self.workspace_id).select_related("definition")

    def _orders(self):
        return MetricDispatchOrder.objects.filter(workspace_id=self.workspace_id).select_related(
            "incident__rule__definition", "assignee", "duty_shift"
        )

    def _workspace_users(self):
        user_ids = {self.user.id} if self.user and self.user.is_active else set()
        try:
            from xpack_lite.models import WorkspaceUserRoleMapping

            user_ids.update(
                WorkspaceUserRoleMapping.objects.filter(
                    workspace_id=self.workspace_id,
                    user__is_active=True,
                ).values_list("user_id", flat=True)
            )
        except (ImportError, RuntimeError):
            pass
        return User.objects.filter(id__in=user_ids, is_active=True).order_by("nick_name", "username")

    def list_assignees(self):
        return [
            {"id": str(row.id), "name": row.nick_name or row.username, "username": row.username}
            for row in self._workspace_users()
        ]

    def list_definitions(self):
        return [serialize_definition(row) for row in self._definitions()]

    def save_definition(self, data, definition_id=None):
        current = self._definitions().filter(id=definition_id).first() if definition_id else None
        if definition_id and current is None:
            raise AppApiException(404, "指标定义不存在")
        payload = data
        if current is not None:
            payload = {
                "metric_key": current.metric_key,
                "name": current.name,
                "theme": current.theme,
                "unit": current.unit,
                "description": current.description,
                "dimensions_schema": current.dimensions_schema,
                "enabled": current.enabled,
                **data,
            }
        serializer = MetricDefinitionWriteSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        duplicate = self._definitions().filter(metric_key=values["metric_key"])
        if current is not None:
            duplicate = duplicate.exclude(id=current.id)
        if duplicate.exists():
            raise AppApiException(400, "指标编码已存在")
        created = current is None
        row = current or MetricDefinition(workspace_id=self.workspace_id)
        for key, value in values.items():
            setattr(row, key, value)
        row.owner = self.user
        row.save()
        return {**serialize_definition(row), "created": created}

    def list_sources(self):
        rows = MetricDataSource.objects.filter(workspace_id=self.workspace_id)
        return [serialize_source(row) for row in rows]

    def save_source(self, data, source_id=None):
        rows = MetricDataSource.objects.filter(workspace_id=self.workspace_id)
        current = rows.filter(id=source_id).first() if source_id else None
        if source_id and current is None:
            raise AppApiException(404, "指标数据源不存在")
        payload = data
        if current is not None:
            payload = {
                "source_key": current.source_key,
                "name": current.name,
                "source_type": current.source_type,
                "config_snapshot": current.config_snapshot,
                "enabled": current.enabled,
                **data,
            }
        serializer = MetricDataSourceWriteSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        duplicate = rows.filter(source_key=values["source_key"])
        if current is not None:
            duplicate = duplicate.exclude(id=current.id)
        if duplicate.exists():
            raise AppApiException(400, "数据源编码已存在")
        row = current or MetricDataSource(workspace_id=self.workspace_id)
        for key, value in values.items():
            setattr(row, key, value)
        row.save()
        return serialize_source(row)

    def list_duty_shifts(self, params=None):
        params = params or {}
        rows = MetricDutyShift.objects.filter(workspace_id=self.workspace_id).select_related("assignee")
        start = serializers.DateTimeField().run_validation(params["start"]) if params.get("start") else None
        end = serializers.DateTimeField().run_validation(params["end"]) if params.get("end") else None
        if start:
            rows = rows.filter(ends_at__gte=start)
        if end:
            rows = rows.filter(starts_at__lte=end)
        return [serialize_duty_shift(row) for row in rows]

    @transaction.atomic
    def save_duty_shift(self, data, shift_id=None):
        rows = MetricDutyShift.objects.filter(workspace_id=self.workspace_id)
        current = rows.select_for_update().filter(id=shift_id).first() if shift_id else None
        if shift_id and current is None:
            raise AppApiException(404, "值班班次不存在")
        payload = data
        if current is not None:
            payload = {
                "name": current.name,
                "starts_at": current.starts_at,
                "ends_at": current.ends_at,
                "assignee_id": current.assignee_id,
                "enabled": current.enabled,
                **data,
            }
        serializer = MetricDutyShiftWriteSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        assignee = self._workspace_users().filter(id=values.pop("assignee_id")).first()
        if assignee is None:
            raise AppApiException(400, "处理人不属于当前工作空间")
        overlap = rows.filter(
            assignee=assignee,
            enabled=True,
            starts_at__lt=values["ends_at"],
            ends_at__gt=values["starts_at"],
        )
        if current is not None:
            overlap = overlap.exclude(id=current.id)
        if values["enabled"] and overlap.exists():
            raise AppApiException(400, "该处理人在此时段已有值班安排")
        row = current or MetricDutyShift(workspace_id=self.workspace_id)
        for key, value in values.items():
            setattr(row, key, value)
        row.assignee = assignee
        row.contact_snapshot = {"channel": "GLOBAL_BELL", "user_id": str(assignee.id)}
        row.save()
        return serialize_duty_shift(MetricDutyShift.objects.select_related("assignee").get(id=row.id))

    @staticmethod
    def _rule_snapshot(values, definition):
        return {
            "metric_key": definition.metric_key,
            "metric_name": definition.name,
            "theme": definition.theme,
            "mode": values["mode"],
            "direction": values["direction"],
            "warning_threshold": values.get("warning_threshold"),
            "critical_threshold": values.get("critical_threshold"),
            "warning_deviation": values["warning_deviation"],
            "critical_deviation": values["critical_deviation"],
            "baseline_window": values["baseline_window"],
            "dimension_filter": values["dimension_filter"],
            "active_windows": values["active_windows"],
            "enabled": values["enabled"],
        }

    @staticmethod
    def _validate_rule_compliance(values):
        issues = []
        if values["mode"] == MetricRuleMode.STATIC:
            if values.get("warning_threshold") is None and values.get("critical_threshold") is None:
                issues.append("固定阈值模式至少配置一个阈值")
        elif values["warning_deviation"] >= values["critical_deviation"]:
            issues.append("动态基线的紧急偏差必须大于关注偏差")
        for index, window in enumerate(values["active_windows"]):
            if not {"start", "end"}.issubset(window):
                issues.append(f"第 {index + 1} 个生效时段缺少 start 或 end")
            elif not all(re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", str(window[key])) for key in ("start", "end")):
                issues.append(f"第 {index + 1} 个生效时段必须使用 HH:MM 格式")
        return issues

    @transaction.atomic
    def save_rule(self, data, rule_id=None):
        current = self._rules().filter(id=rule_id).first() if rule_id else None
        if rule_id and current is None:
            raise AppApiException(404, "指标预警规则不存在")
        payload = data
        if current is not None:
            payload = {
                "definition_id": current.definition_id,
                "name": current.name,
                "mode": current.mode,
                "direction": current.direction,
                "warning_threshold": current.warning_threshold,
                "critical_threshold": current.critical_threshold,
                "warning_deviation": current.warning_deviation,
                "critical_deviation": current.critical_deviation,
                "baseline_window": current.baseline_window,
                "dimension_filter": current.dimension_filter,
                "active_windows": current.active_windows,
                "enabled": current.enabled,
                **data,
            }
        serializer = MetricRuleWriteSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        definition = self._definitions().filter(id=values.pop("definition_id")).first()
        if definition is None:
            raise AppApiException(404, "指标定义不存在")
        issues = self._validate_rule_compliance(values)
        status = MetricComplianceStatus.FAILED if issues else MetricComplianceStatus.PASSED
        version = (current.config_version + 1) if current else 1
        snapshot = self._rule_snapshot(values, definition)
        row = current or MetricAlertRule(workspace_id=self.workspace_id)
        row.definition = definition
        for key, value in values.items():
            setattr(row, key, value)
        row.config_version = version
        row.config_snapshot = snapshot
        row.compliance_status = status
        row.compliance_issues = issues
        row.updated_by = self.user
        row.save()
        MetricAlertRuleVersion.objects.create(
            workspace_id=self.workspace_id,
            rule=row,
            version=version,
            config_snapshot=snapshot,
            compliance_status=status,
            compliance_issues=issues,
            created_by=self.user,
        )
        return serialize_rule(self._rules().get(id=row.id))

    def list_rules(self):
        return [serialize_rule(row) for row in self._rules()]

    @staticmethod
    def _dimension_key(dimensions):
        return json.dumps(dimensions or {}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def _calculate_baseline(self, rule, observation):
        values = list(
            MetricObservation.objects.filter(
                workspace_id=self.workspace_id,
                definition=observation.definition,
                dimension_key=observation.dimension_key,
                observed_at__lt=observation.observed_at,
            )
            .order_by("-observed_at")
            .values_list("value", flat=True)[: rule.baseline_window]
        )
        if len(values) < 3:
            return None
        mean_value = sum(values) / len(values)
        deviation = math.sqrt(sum((value - mean_value) ** 2 for value in values) / len(values))
        latest_version = (
            MetricDynamicBaseline.objects.filter(
                workspace_id=self.workspace_id,
                definition=observation.definition,
                dimension_key=observation.dimension_key,
            ).aggregate(value=Max("version"))["value"]
            or 0
        )
        return MetricDynamicBaseline.objects.create(
            workspace_id=self.workspace_id,
            definition=observation.definition,
            dimension_key=observation.dimension_key,
            version=latest_version + 1,
            window_size=rule.baseline_window,
            sample_count=len(values),
            mean_value=mean_value,
            standard_deviation=deviation,
            snapshot={"values": list(reversed(values)), "rule_config_version": rule.config_version},
            calculated_at=observation.observed_at,
        )

    @staticmethod
    def _matches_dimensions(rule, observation):
        return all(observation.dimensions.get(key) == value for key, value in rule.dimension_filter.items())

    @staticmethod
    def _within_active_windows(rule, observed_at):
        if not rule.active_windows:
            return True
        local_time = timezone.localtime(observed_at).strftime("%H:%M")
        return any(
            window["start"] <= local_time <= window["end"]
            if window["start"] <= window["end"]
            else local_time >= window["start"] or local_time <= window["end"]
            for window in rule.active_windows
        )

    @staticmethod
    def _thresholds(rule, baseline):
        if rule.mode == MetricRuleMode.STATIC:
            return rule.warning_threshold, rule.critical_threshold
        if baseline is None:
            return None, None
        sign = 1 if rule.direction == MetricAlertDirection.ABOVE else -1
        spread = baseline.standard_deviation or max(abs(baseline.mean_value) * 0.05, 0.01)
        return (
            baseline.mean_value + sign * rule.warning_deviation * spread,
            baseline.mean_value + sign * rule.critical_deviation * spread,
        )

    @staticmethod
    def _breached(value, threshold, direction):
        if threshold is None:
            return False
        return value > threshold if direction == MetricAlertDirection.ABOVE else value < threshold

    def _active_duty_shift(self, observed_at):
        return (
            MetricDutyShift.objects.filter(
                workspace_id=self.workspace_id,
                enabled=True,
                starts_at__lte=observed_at,
                ends_at__gte=observed_at,
            )
            .select_related("assignee")
            .order_by("starts_at")
            .first()
        )

    def _append_order_event(
        self,
        order,
        action,
        from_status="",
        to_status="",
        note="",
        snapshot=None,
        operator=None,
    ):
        return MetricDispatchOrderEvent.objects.create(
            workspace_id=self.workspace_id,
            order=order,
            action=action,
            from_status=from_status,
            to_status=to_status,
            note=note,
            snapshot=snapshot or {},
            operator=operator if operator is not None else self.user,
            occurred_at=timezone.now(),
        )

    def _create_dispatch_order(self, incident):
        shift = self._active_duty_shift(incident.last_triggered_at)
        assignee = shift.assignee if shift else None
        status = MetricWorkOrderStatus.ASSIGNED if assignee else MetricWorkOrderStatus.NEW
        order = MetricDispatchOrder.objects.create(
            workspace_id=self.workspace_id,
            incident=incident,
            duty_shift=shift,
            assignee=assignee,
            title=f"处置：{incident.title}",
            status=status,
            assignment_snapshot={
                "strategy": "ACTIVE_DUTY_SHIFT" if shift else "MANUAL",
                "duty_shift_id": str(shift.id) if shift else None,
                "duty_shift_name": shift.name if shift else "",
                "assignee_id": str(assignee.id) if assignee else None,
                "assignee_name": (assignee.nick_name or assignee.username) if assignee else "",
            },
        )
        self._append_order_event(
            order,
            MetricDispatchEventAction.CREATED,
            to_status=status,
            note="按当前值班快照自动创建派单" if shift else "未匹配值班班次，等待人工指派",
            snapshot=order.assignment_snapshot,
            operator=None,
        )
        MarketingNotificationService(self.workspace_id, self.user).dispatch_metric_order(order)
        return order

    def _evaluate_observation(self, observation):
        created_count = 0
        for rule in self._rules().filter(
            definition=observation.definition,
            enabled=True,
            compliance_status=MetricComplianceStatus.PASSED,
        ):
            if not self._matches_dimensions(rule, observation) or not self._within_active_windows(rule, observation.observed_at):
                continue
            baseline = self._calculate_baseline(rule, observation) if rule.mode == MetricRuleMode.DYNAMIC else None
            warning, critical = self._thresholds(rule, baseline)
            critical_hit = self._breached(observation.value, critical, rule.direction)
            warning_hit = self._breached(observation.value, warning, rule.direction)
            severity = MonitoringMetricStatus.CRITICAL if critical_hit else MonitoringMetricStatus.WARNING if warning_hit else None
            dedupe_key = f"metric:{rule.id}:{observation.dimension_key}"
            incident = MetricAlertIncident.objects.filter(
                workspace_id=self.workspace_id,
                dedupe_key=dedupe_key,
            ).first()
            if severity is None:
                if incident and incident.status not in (MetricIncidentStatus.RESOLVED, MetricIncidentStatus.CLOSED):
                    incident.status = MetricIncidentStatus.RESOLVED
                    incident.resolved_at = observation.observed_at
                    incident.last_triggered_at = observation.observed_at
                    incident.save(update_fields=["status", "resolved_at", "last_triggered_at", "update_time"])
                continue
            threshold = critical if critical_hit else warning
            created = incident is None or incident.status in (MetricIncidentStatus.RESOLVED, MetricIncidentStatus.CLOSED)
            if incident is None:
                incident = MetricAlertIncident(
                    workspace_id=self.workspace_id,
                    rule=rule,
                    dedupe_key=dedupe_key,
                    first_triggered_at=observation.observed_at,
                )
            elif created:
                incident.status = MetricIncidentStatus.OPEN
                incident.first_triggered_at = observation.observed_at
                incident.acknowledged_at = None
                incident.resolved_at = None
            incident.observation = observation
            incident.baseline = baseline
            incident.title = f"{observation.definition.name}{'紧急' if critical_hit else '异常'}"
            incident.message = f"当前值 {observation.value:g}{observation.definition.unit}，阈值 {threshold:g}"
            incident.severity = severity
            incident.observed_value = observation.value
            incident.threshold_value = threshold
            incident.config_version = rule.config_version
            incident.config_snapshot = rule.config_snapshot
            incident.last_triggered_at = observation.observed_at
            incident.save()
            if created:
                self._create_dispatch_order(incident)
                created_count += 1
        return created_count

    @transaction.atomic
    def import_batch(self, data):
        serializer = MetricBatchImportSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        if MetricCollectionBatch.objects.filter(
            workspace_id=self.workspace_id, batch_no=values["batch_no"]
        ).exists():
            raise AppApiException(400, "采集批次号已存在")
        source = None
        if values["source_key"]:
            source = MetricDataSource.objects.filter(
                workspace_id=self.workspace_id,
                source_key=values["source_key"],
                enabled=True,
            ).first()
            if source is None:
                raise AppApiException(404, "指标数据源不存在或已停用")
        now = timezone.now()
        rows = values["rows"]
        batch = MetricCollectionBatch.objects.create(
            workspace_id=self.workspace_id,
            batch_no=values["batch_no"],
            source=source,
            total_rows=len(rows),
            input_snapshot={"source_key": values["source_key"], "metric_keys": sorted({str(row.get("metric_key", "")) for row in rows})},
            collected_at=now,
            operator=self.user,
        )
        accepted = []
        errors = []
        for index, raw_row in enumerate(rows, start=1):
            row_serializer = MetricImportRowSerializer(data=raw_row)
            if not row_serializer.is_valid():
                errors.append({"row": index, "errors": row_serializer.errors})
                continue
            row = row_serializer.validated_data
            definition = self._definitions().filter(metric_key=row["metric_key"], enabled=True).first()
            if definition is None:
                errors.append({"row": index, "errors": {"metric_key": ["指标不存在或已停用"]}})
                continue
            dimensions = row["dimensions"]
            unknown_dimensions = sorted(set(dimensions) - set(definition.dimensions_schema))
            if unknown_dimensions:
                errors.append({"row": index, "errors": {"dimensions": [f"未定义维度：{', '.join(unknown_dimensions)}"]}})
                continue
            observation = MetricObservation.objects.create(
                workspace_id=self.workspace_id,
                definition=definition,
                batch=batch,
                value=row["value"],
                dimensions=dimensions,
                dimension_key=self._dimension_key(dimensions),
                observed_at=row.get("observed_at") or now,
                raw_snapshot={
                    "metric_key": row["metric_key"],
                    "value": row["value"],
                    "dimensions": dimensions,
                },
            )
            accepted.append(observation)
        accepted.sort(key=lambda item: item.observed_at)
        alert_count = sum(self._evaluate_observation(item) for item in accepted)
        batch.accepted_rows = len(accepted)
        batch.rejected_rows = len(errors)
        batch.error_rows = errors
        batch.status = (
            MetricBatchStatus.FAILED if not accepted else MetricBatchStatus.PARTIAL if errors else MetricBatchStatus.IMPORTED
        )
        batch.save(update_fields=["accepted_rows", "rejected_rows", "error_rows", "status", "update_time"])
        return {
            "id": str(batch.id),
            "batch_no": batch.batch_no,
            "status": batch.status,
            "total_rows": batch.total_rows,
            "accepted_rows": batch.accepted_rows,
            "rejected_rows": batch.rejected_rows,
            "error_rows": batch.error_rows,
            "alert_count": alert_count,
        }

    def list_order_events(self, order_id):
        if not self._orders().filter(id=order_id).exists():
            raise AppApiException(404, "派单不存在")
        rows = MetricDispatchOrderEvent.objects.filter(
            workspace_id=self.workspace_id,
            order_id=order_id,
        ).select_related("operator")
        return [serialize_order_event(row) for row in rows]

    @staticmethod
    def _filter_observations(rows, values):
        if values.get("device"):
            rows = rows.filter(dimensions__device=values["device"])
        if values.get("network_element"):
            rows = rows.filter(dimensions__network_element=values["network_element"])
        if values.get("time_slot"):
            rows = rows.filter(dimensions__time_slot=values["time_slot"])
        if values.get("start"):
            rows = rows.filter(observed_at__gte=values["start"])
        if values.get("end"):
            rows = rows.filter(observed_at__lte=values["end"])
        return rows

    def metric_analytics(self, params=None):
        serializer = MetricAnalyticsQuerySerializer(data=params or {})
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        all_definitions = self._definitions().filter(enabled=True)
        definitions = all_definitions
        if values.get("theme"):
            definitions = definitions.filter(theme=values["theme"])
        selected_definition = None
        if values.get("definition_id"):
            selected_definition = definitions.filter(id=values["definition_id"]).first()
            if selected_definition is None:
                raise AppApiException(404, "指标定义不存在或不属于当前主题")

        theme_observations = MetricObservation.objects.filter(
            workspace_id=self.workspace_id,
            definition__in=all_definitions,
        )
        theme_observations = self._filter_observations(theme_observations, values)
        observations = theme_observations.filter(definition__in=definitions)
        if selected_definition is None:
            first_definition_id = (
                observations.order_by("definition__theme", "definition__metric_key")
                .values_list("definition_id", flat=True)
                .first()
            )
            selected_definition = definitions.filter(id=first_definition_id).first() or definitions.first()

        aggregate_rows = {
            row["definition__theme"]: row
            for row in theme_observations.values("definition__theme").annotate(
                observation_count=Count("id"),
                average_value=Avg("value"),
                minimum_value=Min("value"),
                maximum_value=Max("value"),
            )
        }
        theme_metric_counts = Counter(all_definitions.values_list("theme", flat=True))
        theme_stats = []
        for theme, label in MetricTheme.choices:
            theme_rows = theme_observations.filter(definition__theme=theme)
            latest = theme_rows.select_related("definition").order_by("-observed_at").first()
            aggregate = aggregate_rows.get(theme, {})
            theme_stats.append(
                {
                    "theme": theme,
                    "theme_label": label,
                    "metric_count": theme_metric_counts[theme],
                    "observation_count": aggregate.get("observation_count", 0),
                    "average_value": aggregate.get("average_value"),
                    "minimum_value": aggregate.get("minimum_value"),
                    "maximum_value": aggregate.get("maximum_value"),
                    "latest_value": latest.value if latest else None,
                    "latest_unit": latest.definition.unit if latest else "",
                    "latest_observed_at": latest.observed_at if latest else None,
                    "alert_count": MetricAlertIncident.objects.filter(
                        workspace_id=self.workspace_id,
                        observation__in=theme_rows,
                    ).count(),
                }
            )

        selected_rows = observations.none()
        if selected_definition is not None:
            selected_rows = observations.filter(definition=selected_definition)
        selected_rows = list(selected_rows.select_related("batch").order_by("-observed_at")[: values["limit"]])
        selected_rows.reverse()
        dimension_keys = {row.dimension_key for row in selected_rows}
        baseline_rows = MetricDynamicBaseline.objects.filter(
            workspace_id=self.workspace_id,
            definition=selected_definition,
            dimension_key__in=dimension_keys,
        ).order_by("calculated_at", "version") if selected_definition else MetricDynamicBaseline.objects.none()
        baseline_map = {(row.dimension_key, row.calculated_at): row for row in baseline_rows}
        incident_rows = (
            MetricAlertIncident.objects.filter(
                workspace_id=self.workspace_id,
                observation_id__in=[row.id for row in selected_rows],
            )
            .select_related("rule", "baseline")
            .order_by("severity")
        )
        incident_map = {row.observation_id: row for row in incident_rows}
        active_rule = (
            self._rules()
            .filter(
                definition=selected_definition,
                enabled=True,
                compliance_status=MetricComplianceStatus.PASSED,
            )
            .first()
            if selected_definition
            else None
        )
        points = []
        for row in selected_rows:
            baseline = baseline_map.get((row.dimension_key, row.observed_at))
            rule_applies = bool(
                active_rule
                and self._matches_dimensions(active_rule, row)
                and self._within_active_windows(active_rule, row.observed_at)
            )
            warning, critical = self._thresholds(active_rule, baseline) if rule_applies else (None, None)
            incident = incident_map.get(row.id)
            points.append(
                {
                    "id": str(row.id),
                    "value": row.value,
                    "dimensions": row.dimensions,
                    "observed_at": row.observed_at,
                    "batch_no": row.batch.batch_no,
                    "baseline_mean": baseline.mean_value if baseline else None,
                    "baseline_standard_deviation": baseline.standard_deviation if baseline else None,
                    "warning_threshold": warning,
                    "critical_threshold": critical,
                    "alert": (
                        {
                            "id": str(incident.id),
                            "severity": incident.severity,
                            "status": incident.status,
                            "threshold_value": incident.threshold_value,
                            "rule_name": incident.rule.name,
                            "config_version": incident.config_version,
                        }
                        if incident
                        else None
                    ),
                }
            )

        option_rows = MetricObservation.objects.filter(
            workspace_id=self.workspace_id,
            definition__in=self._definitions().filter(enabled=True),
        ).order_by("-observed_at").values_list("dimensions", flat=True)[:5000]
        dimension_options = {"device": set(), "network_element": set(), "time_slot": set()}
        for dimensions in option_rows:
            for key in dimension_options:
                if dimensions.get(key):
                    dimension_options[key].add(str(dimensions[key]))
        summary = selected_rows and {
            "observation_count": len(selected_rows),
            "average_value": sum(row.value for row in selected_rows) / len(selected_rows),
            "minimum_value": min(row.value for row in selected_rows),
            "maximum_value": max(row.value for row in selected_rows),
            "alert_count": sum(1 for point in points if point["alert"]),
        } or {
            "observation_count": 0,
            "average_value": None,
            "minimum_value": None,
            "maximum_value": None,
            "alert_count": 0,
        }
        return {
            "filters": {
                "theme": values.get("theme", ""),
                "definition_id": str(selected_definition.id) if selected_definition else None,
                "device": values.get("device", ""),
                "network_element": values.get("network_element", ""),
                "time_slot": values.get("time_slot", ""),
            },
            "dimension_options": {key: sorted(items) for key, items in dimension_options.items()},
            "definitions": [serialize_definition(row) for row in definitions],
            "selected_definition": serialize_definition(selected_definition) if selected_definition else None,
            "theme_stats": theme_stats,
            "summary": summary,
            "points": points,
        }

    def observation_detail(self, observation_id):
        row = (
            MetricObservation.objects.filter(workspace_id=self.workspace_id, id=observation_id)
            .select_related("definition", "batch", "batch__source", "batch__operator")
            .first()
        )
        if row is None:
            raise AppApiException(404, "指标观测不存在")
        baselines = MetricDynamicBaseline.objects.filter(
            workspace_id=self.workspace_id,
            definition=row.definition,
            dimension_key=row.dimension_key,
            calculated_at=row.observed_at,
        )
        incidents = list(
            MetricAlertIncident.objects.filter(workspace_id=self.workspace_id, observation=row)
            .select_related("rule", "baseline")
            .order_by("-last_triggered_at")
        )
        orders = self._orders().filter(incident_id__in=[incident.id for incident in incidents])
        orders_by_incident = {}
        for order in orders:
            order_payload = serialize_order(order)
            order_payload["events"] = self.list_order_events(str(order.id))
            orders_by_incident.setdefault(order.incident_id, []).append(order_payload)
        return {
            "observation": {
                "id": str(row.id),
                "definition": serialize_definition(row.definition),
                "value": row.value,
                "dimensions": row.dimensions,
                "dimension_key": row.dimension_key,
                "observed_at": row.observed_at,
                "raw_snapshot": row.raw_snapshot,
            },
            "batch": {
                "id": str(row.batch_id),
                "batch_no": row.batch.batch_no,
                "status": row.batch.status,
                "source_name": row.batch.source.name if row.batch.source else "直接导入",
                "total_rows": row.batch.total_rows,
                "accepted_rows": row.batch.accepted_rows,
                "rejected_rows": row.batch.rejected_rows,
                "collected_at": row.batch.collected_at,
                "operator_name": (
                    row.batch.operator.nick_name or row.batch.operator.username
                    if row.batch.operator
                    else "系统"
                ),
            },
            "baselines": [
                {
                    "id": str(item.id),
                    "version": item.version,
                    "algorithm": item.algorithm,
                    "window_size": item.window_size,
                    "sample_count": item.sample_count,
                    "mean_value": item.mean_value,
                    "standard_deviation": item.standard_deviation,
                    "snapshot": item.snapshot,
                    "calculated_at": item.calculated_at,
                }
                for item in baselines
            ],
            "incidents": [
                {
                    "id": str(incident.id),
                    "title": incident.title,
                    "message": incident.message,
                    "severity": incident.severity,
                    "status": incident.status,
                    "observed_value": incident.observed_value,
                    "threshold_value": incident.threshold_value,
                    "config_version": incident.config_version,
                    "config_snapshot": incident.config_snapshot,
                    "rule_name": incident.rule.name,
                    "first_triggered_at": incident.first_triggered_at,
                    "last_triggered_at": incident.last_triggered_at,
                    "orders": orders_by_incident.get(incident.id, []),
                }
                for incident in incidents
            ],
        }

    @transaction.atomic
    def operate_order(self, order_id, data):
        if isinstance(data, str):
            data = {"action": data}
        serializer = MetricOrderOperateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        action = values["action"]
        row = (
            MetricDispatchOrder.objects.select_for_update()
            .filter(workspace_id=self.workspace_id, id=order_id)
            .first()
        )
        if row is None:
            raise AppApiException(404, "派单不存在")
        if action in ("ASSIGN", "TRANSFER"):
            expected = "ASSIGN" if row.status == MetricWorkOrderStatus.NEW else "TRANSFER"
            if action != expected or row.status in (MetricWorkOrderStatus.RESOLVED, MetricWorkOrderStatus.CLOSED):
                raise AppApiException(400, "当前派单状态不支持该操作")
            assignee = self._workspace_users().filter(id=values["assignee_id"]).first()
            if assignee is None:
                raise AppApiException(400, "处理人不属于当前工作空间")
            previous_assignee_id = str(row.assignee_id) if row.assignee_id else None
            from_status = row.status
            row.assignee = assignee
            row.status = MetricWorkOrderStatus.ASSIGNED
            row.assignment_snapshot = {
                "strategy": "MANUAL_TRANSFER" if action == "TRANSFER" else "MANUAL_ASSIGNMENT",
                "assignee_id": str(assignee.id),
                "assignee_name": assignee.nick_name or assignee.username,
                "previous_assignee_id": previous_assignee_id,
            }
            row.claimed_at = None
            row.save()
            event = self._append_order_event(
                row,
                MetricDispatchEventAction.TRANSFERRED if action == "TRANSFER" else MetricDispatchEventAction.ASSIGNED,
                from_status=from_status,
                to_status=row.status,
                note=values["note"],
                snapshot=row.assignment_snapshot,
            )
            MarketingNotificationService(self.workspace_id, self.user).dispatch_metric_order_event(row, event)
            return serialize_order(self._orders().get(id=row.id))
        if action == "COMMENT":
            if row.status == MetricWorkOrderStatus.CLOSED:
                raise AppApiException(400, "已关闭派单不能追加备注")
            event = self._append_order_event(
                row,
                MetricDispatchEventAction.COMMENTED,
                from_status=row.status,
                to_status=row.status,
                note=values["note"].strip(),
            )
            MarketingNotificationService(self.workspace_id, self.user).dispatch_metric_order_event(row, event)
            return serialize_order(self._orders().get(id=row.id))
        transitions = {
            MetricWorkOrderStatus.ASSIGNED: {"CLAIM": MetricWorkOrderStatus.CLAIMED},
            MetricWorkOrderStatus.CLAIMED: {"START": MetricWorkOrderStatus.PROCESSING},
            MetricWorkOrderStatus.PROCESSING: {"RESOLVE": MetricWorkOrderStatus.RESOLVED},
            MetricWorkOrderStatus.RESOLVED: {"CLOSE": MetricWorkOrderStatus.CLOSED},
        }
        target = transitions.get(row.status, {}).get(action)
        if target is None:
            raise AppApiException(400, "当前派单状态不支持该操作")
        now = timezone.now()
        from_status = row.status
        row.status = target
        if target == MetricWorkOrderStatus.CLAIMED:
            row.claimed_at = now
        elif target == MetricWorkOrderStatus.RESOLVED:
            row.resolved_at = now
            row.incident.status = MetricIncidentStatus.RESOLVED
            row.incident.resolved_at = now
            row.incident.save(update_fields=["status", "resolved_at", "update_time"])
        elif target == MetricWorkOrderStatus.CLOSED:
            row.closed_at = now
            row.incident.status = MetricIncidentStatus.CLOSED
            row.incident.save(update_fields=["status", "update_time"])
        row.save()
        event_action = {
            "CLAIM": MetricDispatchEventAction.CLAIMED,
            "START": MetricDispatchEventAction.STARTED,
            "RESOLVE": MetricDispatchEventAction.RESOLVED,
            "CLOSE": MetricDispatchEventAction.CLOSED,
        }[action]
        event = self._append_order_event(
            row,
            event_action,
            from_status=from_status,
            to_status=target,
            note=values["note"],
        )
        if action == "CLOSE":
            MarketingNotificationService(self.workspace_id, self.user).dispatch_metric_order_event(row, event)
        return serialize_order(self._orders().get(id=row.id))

    def overview(self):
        definitions = self._definitions()
        batches = MetricCollectionBatch.objects.filter(workspace_id=self.workspace_id)
        baselines = MetricDynamicBaseline.objects.filter(workspace_id=self.workspace_id)
        incidents = MetricAlertIncident.objects.filter(workspace_id=self.workspace_id)
        orders = self._orders()
        theme_counts = Counter(definitions.values_list("theme", flat=True))
        latest_values = []
        for definition in definitions:
            latest = definition.observations.first()
            latest_values.append(
                {
                    **serialize_definition(definition),
                    "latest_value": latest.value if latest else None,
                    "latest_dimensions": latest.dimensions if latest else {},
                    "observed_at": latest.observed_at if latest else None,
                }
            )
        return {
            "summary": {
                "definition_count": definitions.count(),
                "theme_count": len(theme_counts),
                "batch_count": batches.count(),
                "baseline_count": baselines.count(),
                "rule_count": self._rules().count(),
                "active_incident_count": incidents.exclude(
                    status__in=[MetricIncidentStatus.RESOLVED, MetricIncidentStatus.CLOSED]
                ).count(),
                "open_order_count": orders.exclude(
                    status__in=[MetricWorkOrderStatus.RESOLVED, MetricWorkOrderStatus.CLOSED]
                ).count(),
            },
            "themes": [
                {"theme": value, "theme_label": label, "metric_count": theme_counts[value]}
                for value, label in MetricTheme.choices
            ],
            "definitions": latest_values,
            "sources": self.list_sources(),
            "rules": self.list_rules(),
            "duty_shifts": self.list_duty_shifts(),
            "assignees": self.list_assignees(),
            "orders": [serialize_order(row) for row in orders[:50]],
            "recent_batches": [
                {
                    "id": str(row.id),
                    "batch_no": row.batch_no,
                    "status": row.status,
                    "accepted_rows": row.accepted_rows,
                    "rejected_rows": row.rejected_rows,
                    "collected_at": row.collected_at,
                }
                for row in batches[:20]
            ],
        }

    @transaction.atomic
    def bootstrap_demo(self):
        source, _ = MetricDataSource.objects.get_or_create(
            workspace_id=self.workspace_id,
            source_key="m03_demo_import",
            defaults={
                "name": "M03 验收样例导入",
                "source_type": MetricSourceType.MANUAL,
                "config_snapshot": {"format": "JSON", "version": 1},
            },
        )
        definitions = []
        for theme, metric_key, name, unit in THEME_DEMO_METRICS:
            definition, _ = MetricDefinition.objects.get_or_create(
                workspace_id=self.workspace_id,
                metric_key=metric_key,
                defaults={
                    "name": name,
                    "theme": theme,
                    "unit": unit,
                    "description": "M03 八类主题粗粒度 V1 样例指标",
                    "dimensions_schema": ["device", "network_element", "time_slot"],
                    "owner": self.user,
                },
            )
            definitions.append(definition)
        primary = definitions[0]
        rule = self._rules().filter(name="故障恢复时长动态预警").first()
        if rule is None:
            self.save_rule(
                {
                    "definition_id": str(primary.id),
                    "name": "故障恢复时长动态预警",
                    "mode": MetricRuleMode.DYNAMIC,
                    "direction": MetricAlertDirection.ABOVE,
                    "warning_deviation": 3.0,
                    "critical_deviation": 4.0,
                    "baseline_window": 5,
                    "dimension_filter": {"device": "核心路由器-01"},
                    "active_windows": [{"start": "00:00", "end": "23:59"}],
                    "enabled": True,
                }
            )
        if self.user and not MetricDutyShift.objects.filter(
            workspace_id=self.workspace_id,
            starts_at__lte=timezone.now(),
            ends_at__gte=timezone.now(),
            assignee=self.user,
        ).exists():
            MetricDutyShift.objects.create(
                workspace_id=self.workspace_id,
                name="M03 验收值班",
                starts_at=timezone.now() - timedelta(hours=12),
                ends_at=timezone.now() + timedelta(hours=12),
                assignee=self.user,
                contact_snapshot={"channel": "GLOBAL_BELL", "user_id": str(self.user.id)},
            )
        batch_no = f"M03-DEMO-{timezone.now().strftime('%Y%m%d%H%M%S%f')}"
        rows = []
        base_time = timezone.now() - timedelta(hours=6)
        dimensions = {"device": "核心路由器-01", "network_element": "NE-HZ-001", "time_slot": "全天"}
        for index, value in enumerate((39, 41, 40, 42, 41, 86)):
            rows.append(
                {
                    "metric_key": primary.metric_key,
                    "value": value,
                    "dimensions": dimensions,
                    "observed_at": base_time + timedelta(hours=index),
                }
            )
        for definition_index, definition in enumerate(definitions[1:], start=1):
            base_value = 68 + definition_index * 3
            for point_index, offset in enumerate((0, 2, -1, 3, 1, 4)):
                rows.append(
                    {
                        "metric_key": definition.metric_key,
                        "value": base_value + offset,
                        "dimensions": dimensions,
                        "observed_at": base_time + timedelta(hours=point_index, minutes=definition_index),
                    }
                )
        imported = self.import_batch({"batch_no": batch_no, "source_key": source.source_key, "rows": rows})
        return {"import": imported, "overview": self.overview()}
