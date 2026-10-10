from datetime import timedelta
from pathlib import Path

from django.db import transaction
from django.db.models import Avg, Case, Count, DurationField, ExpressionWrapper, F, IntegerField, Max, Q, Value, When
from django.utils import timezone
from rest_framework import serializers

from common.exception.app_exception import AppApiException
from common.result import Page
from marketing.models import (
    MarketingAlert,
    MarketingAlertAction,
    MarketingAlertActionRecord,
    MarketingAlertAttachment,
    MarketingAlertHandlingRound,
    MarketingAlertResolutionType,
    MarketingAlertRootCause,
    MarketingAlertRule,
    MarketingAlertRuleChange,
    MarketingAlertRuleChangeType,
    MarketingAlertRoundEndReason,
    MarketingAlertSeverity,
    MarketingAlertStatus,
    MarketingAlertSubscriber,
)
from marketing.serializers.operations import MarketingOperationsService
from marketing.serializers.quality_review import validate_or_raise
from users.models import User


DEFAULT_ALERT_RULES = (
    {
        "alert_type": "RUNTIME_ERROR",
        "name": "对话运行错误",
        "severity": MarketingAlertSeverity.CRITICAL,
        "description": "模型调用或对话运行错误达到阈值时触发。",
    },
    {
        "alert_type": "QUALITY_BYPASS",
        "name": "发送前检测旁路",
        "severity": MarketingAlertSeverity.CRITICAL,
        "description": "回答因检测超时或异常直接放行达到阈值时触发。",
    },
    {
        "alert_type": "OVERDUE_BATCH",
        "name": "触达批次逾期",
        "severity": MarketingAlertSeverity.WARNING,
        "description": "未关闭触达批次超过截止时间达到阈值时触发。",
    },
    {
        "alert_type": "PENDING_REVIEW",
        "name": "质检记录待复核",
        "severity": MarketingAlertSeverity.WARNING,
        "description": "问题回答待人工复核数量达到阈值时触发。",
    },
    {
        "alert_type": "SLOW_RESPONSE",
        "name": "对话响应偏慢",
        "severity": MarketingAlertSeverity.WARNING,
        "description": "响应超过十秒的对话数量达到阈值时触发。",
    },
)


class MarketingAlertQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(required=False, allow_blank=True, choices=MarketingAlertStatus.choices)
    severity = serializers.ChoiceField(required=False, allow_blank=True, choices=MarketingAlertSeverity.choices)
    alert_type = serializers.CharField(required=False, allow_blank=True, max_length=64)
    keyword = serializers.CharField(required=False, allow_blank=True, max_length=200)
    assignee_id = serializers.UUIDField(required=False)
    unassigned = serializers.BooleanField(required=False, default=False)
    active_only = serializers.BooleanField(required=False, default=False)
    sla_overdue = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        if attrs.get("assignee_id") and attrs.get("unassigned"):
            raise serializers.ValidationError("负责人和未认领筛选不能同时使用")
        return attrs


class MarketingAlertSyncSerializer(serializers.Serializer):
    days = serializers.ChoiceField(required=False, default=7, choices=(7, 30, 90))


class MarketingAlertPerformanceQuerySerializer(serializers.Serializer):
    days = serializers.ChoiceField(required=False, default=7, choices=(7, 30, 90))


class MarketingAlertRetrospectiveQuerySerializer(serializers.Serializer):
    days = serializers.ChoiceField(required=False, default=30, choices=(7, 30, 90))
    root_cause_category = serializers.ChoiceField(
        required=False,
        allow_blank=True,
        choices=MarketingAlertRootCause.choices,
    )


class MarketingAlertNoiseAnalysisQuerySerializer(serializers.Serializer):
    days = serializers.ChoiceField(required=False, default=7, choices=(7, 30, 90))


class MarketingAlertRuleEffectQuerySerializer(serializers.Serializer):
    days = serializers.ChoiceField(required=False, default=30, choices=(7, 30, 90))


class MarketingAlertHandleSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=("CLAIM", "START", "CLOSE", "REOPEN"))
    note = serializers.CharField(required=False, allow_blank=True, max_length=2000)
    root_cause_category = serializers.ChoiceField(required=False, choices=MarketingAlertRootCause.choices)
    resolution_type = serializers.ChoiceField(required=False, choices=MarketingAlertResolutionType.choices)
    impact_scope = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def validate(self, attrs):
        attrs["note"] = attrs.get("note", "").strip()
        attrs["impact_scope"] = attrs.get("impact_scope", "").strip()
        if attrs["action"] == "CLOSE" and not attrs["note"]:
            raise serializers.ValidationError({"note": "关闭告警时必须填写处理结论"})
        if attrs["action"] == "CLOSE" and not attrs.get("root_cause_category"):
            raise serializers.ValidationError({"root_cause_category": "关闭告警时必须选择根因分类"})
        if attrs["action"] == "CLOSE" and not attrs.get("resolution_type"):
            raise serializers.ValidationError({"resolution_type": "关闭告警时必须选择处置方式"})
        return attrs


class MarketingAlertCollaborateSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=("ASSIGN", "TRANSFER", "COMMENT"))
    assignee_id = serializers.UUIDField(required=False)
    note = serializers.CharField(required=False, allow_blank=True, max_length=2000)

    def validate(self, attrs):
        attrs["note"] = attrs.get("note", "").strip()
        if attrs["action"] in ("ASSIGN", "TRANSFER") and not attrs.get("assignee_id"):
            raise serializers.ValidationError({"assignee_id": "请选择负责人"})
        if attrs["action"] in ("TRANSFER", "COMMENT") and not attrs["note"]:
            message = "转派时必须填写原因" if attrs["action"] == "TRANSFER" else "评论内容不能为空"
            raise serializers.ValidationError({"note": message})
        return attrs


class MarketingAlertSubscriberSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=("ADD", "REMOVE"))
    user_id = serializers.UUIDField()


class MarketingAlertRuleUpdateSerializer(serializers.Serializer):
    enabled = serializers.BooleanField(required=False)
    threshold = serializers.IntegerField(required=False, min_value=1, max_value=100000)
    severity = serializers.ChoiceField(required=False, choices=MarketingAlertSeverity.choices)
    response_sla_minutes = serializers.IntegerField(required=False, min_value=1, max_value=10080)
    resolution_sla_minutes = serializers.IntegerField(required=False, min_value=1, max_value=43200)
    escalation_user_id = serializers.UUIDField(required=False, allow_null=True)
    change_reason = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def validate(self, attrs):
        if not {key for key in attrs if key != "change_reason"}:
            raise serializers.ValidationError("至少需要修改一个规则字段")
        return attrs


class MarketingAlertRuleRollbackSerializer(serializers.Serializer):
    change_id = serializers.UUIDField(required=True)
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)


def _user_name(user):
    if not user:
        return "系统"
    return user.nick_name or user.username


def serialize_alert_action(row):
    return {
        "id": str(row.id),
        "action": row.action,
        "previous_status": row.previous_status,
        "current_status": row.current_status,
        "operator_name": row.operator_name,
        "note": row.note,
        "snapshot": row.snapshot,
        "revision": row.revision,
        "create_time": row.create_time,
    }


def serialize_alert_round(row):
    return {
        "id": str(row.id),
        "sequence": row.sequence,
        "assignee_id": str(row.assignee_id) if row.assignee_id else None,
        "assignee_name": row.assignee_name,
        "assigned_by_name": row.assigned_by_name,
        "assigned_at": row.assigned_at,
        "response_due_at": row.response_due_at,
        "resolution_due_at": row.resolution_due_at,
        "first_responded_at": row.first_responded_at,
        "ended_at": row.ended_at,
        "end_reason": row.end_reason,
        "end_note": row.end_note,
    }


def serialize_alert_subscriber(row):
    return {
        "id": str(row.id),
        "user_id": str(row.user_id),
        "user_name": row.user_name,
        "subscribed_by_name": row.subscribed_by_name,
        "create_time": row.create_time,
    }


def serialize_alert_attachment(row):
    return {
        "id": str(row.id),
        "file_name": row.file_name,
        "content_type": row.content_type,
        "file_size": row.file_size,
        "uploader_name": row.uploader_name,
        "expires_at": row.expires_at,
        "create_time": row.create_time,
        "download_url": (
            f"/workspace/{row.workspace_id}/marketing/alert/{row.alert_id}/attachment/{row.id}/download"
        ),
    }


def serialize_alert(row):
    now = timezone.now()
    response_overdue = bool(
        row.status != MarketingAlertStatus.CLOSED
        and row.source_active
        and not row.first_responded_at
        and row.response_due_at
        and row.response_due_at <= now
    )
    resolution_overdue = bool(
        row.status != MarketingAlertStatus.CLOSED
        and row.source_active
        and row.resolution_due_at
        and row.resolution_due_at <= now
    )
    return {
        "id": str(row.id),
        "alert_type": row.alert_type,
        "title": row.title,
        "description": row.description,
        "severity": row.severity,
        "status": row.status,
        "current_count": row.current_count,
        "source_active": row.source_active,
        "target_route": row.target_route,
        "assignee_id": str(row.assignee_id) if row.assignee_id else None,
        "assignee_name": row.assignee_name,
        "first_triggered_at": row.first_triggered_at,
        "last_triggered_at": row.last_triggered_at,
        "sla_started_at": row.sla_started_at,
        "response_due_at": row.response_due_at,
        "resolution_due_at": row.resolution_due_at,
        "first_responded_at": row.first_responded_at,
        "response_escalated_at": row.response_escalated_at,
        "resolution_escalated_at": row.resolution_escalated_at,
        "response_overdue": response_overdue,
        "resolution_overdue": resolution_overdue,
        "escalation_user_id": str(row.rule.escalation_user_id) if row.rule and row.rule.escalation_user_id else None,
        "escalation_user_name": row.rule.escalation_user_name if row.rule else "",
        "resolved_at": row.resolved_at,
        "closed_at": row.closed_at,
        "close_note": row.close_note,
        "root_cause_category": row.root_cause_category,
        "root_cause_label": row.get_root_cause_category_display() if row.root_cause_category else "",
        "resolution_type": row.resolution_type,
        "resolution_type_label": row.get_resolution_type_display() if row.resolution_type else "",
        "impact_scope": row.impact_scope,
        "revision": row.revision,
        "actions": [serialize_alert_action(action) for action in row.actions.all()],
        "handling_rounds": [serialize_alert_round(round_row) for round_row in row.handling_rounds.all()],
        "subscribers": [serialize_alert_subscriber(item) for item in row.subscribers.all()],
        "attachments": [serialize_alert_attachment(item) for item in row.attachments.all()],
    }


def serialize_alert_rule(row):
    return {
        "id": str(row.id),
        "alert_type": row.alert_type,
        "name": row.name,
        "severity": row.severity,
        "enabled": row.enabled,
        "threshold": row.threshold,
        "response_sla_minutes": row.response_sla_minutes,
        "resolution_sla_minutes": row.resolution_sla_minutes,
        "escalation_user_id": str(row.escalation_user_id) if row.escalation_user_id else None,
        "escalation_user_name": row.escalation_user_name,
        "description": row.description,
        "updated_by_name": row.updated_by_name,
        "update_time": row.update_time,
    }


def serialize_alert_rule_change(row):
    return {
        "id": str(row.id),
        "version": row.version,
        "change_type": row.change_type,
        "change_type_label": row.get_change_type_display(),
        "snapshot": row.snapshot,
        "reason": row.reason,
        "operator_name": row.operator_name,
        "create_time": row.create_time,
    }


class MarketingAlertService:
    def __init__(self, workspace_id, user=None):
        self.workspace_id = workspace_id
        self.user = user

    def _queryset(self):
        return (
            MarketingAlert.objects.filter(workspace_id=self.workspace_id)
            .select_related("rule", "rule__escalation_user", "assignee")
            .prefetch_related("actions", "handling_rounds", "subscribers", "attachments")
        )

    def _serialize_alert(self, alert):
        data = serialize_alert(alert)
        can_manage = self._can_manage()
        data["capabilities"] = {
            "can_assign": bool(can_manage and alert.status != MarketingAlertStatus.CLOSED and not alert.assignee_id),
            "can_transfer": bool(
                alert.status != MarketingAlertStatus.CLOSED
                and alert.assignee_id
                and (can_manage or (self.user and alert.assignee_id == self.user.id))
            ),
            "can_comment": bool(self.user),
            "can_subscribe": bool(self.user),
            "can_attach": bool(self.user),
        }
        data["related_experiences"] = self._historical_experiences(alert)
        return data

    def _historical_experiences(self, alert, limit=3, include_current=False):
        root_cause_labels = dict(MarketingAlertRootCause.choices)
        resolution_labels = dict(MarketingAlertResolutionType.choices)
        rows = (
            MarketingAlertActionRecord.objects.filter(
                workspace_id=self.workspace_id,
                alert__alert_type=alert.alert_type,
                action=MarketingAlertAction.CLOSED,
            )
            .select_related("alert")
            .order_by("-create_time")
        )
        experiences = []
        for row in rows:
            if (
                not include_current
                and alert.status == MarketingAlertStatus.CLOSED
                and row.alert_id == alert.id
                and row.revision == alert.revision
            ):
                continue
            snapshot = row.snapshot or {}
            root_cause = snapshot.get("root_cause_category", "")
            resolution_type = snapshot.get("resolution_type", "")
            if not root_cause or not resolution_type:
                continue
            experiences.append(
                {
                    "id": str(row.id),
                    "alert_id": str(row.alert_id),
                    "title": row.alert.title,
                    "alert_type": row.alert.alert_type,
                    "root_cause_category": root_cause,
                    "root_cause_label": snapshot.get("root_cause_label")
                    or root_cause_labels.get(root_cause, root_cause),
                    "resolution_type": resolution_type,
                    "resolution_type_label": snapshot.get("resolution_type_label")
                    or resolution_labels.get(resolution_type, resolution_type),
                    "close_note": row.note,
                    "impact_scope": snapshot.get("impact_scope", ""),
                    "assignee_name": row.alert.assignee_name,
                    "closed_at": row.create_time,
                }
            )
            if len(experiences) >= limit:
                break
        return experiences

    def _can_manage(self):
        if hasattr(self, "_can_manage_cache"):
            return self._can_manage_cache
        if not self.user:
            return False
        try:
            from xpack_lite.services import is_workspace_manager

            self._can_manage_cache = is_workspace_manager(self.user.id, self.workspace_id)
        except (ImportError, RuntimeError):
            self._can_manage_cache = False
        return self._can_manage_cache

    def ensure_rules(self):
        for item in DEFAULT_ALERT_RULES:
            MarketingAlertRule.objects.get_or_create(
                workspace_id=self.workspace_id,
                alert_type=item["alert_type"],
                defaults={
                    "name": item["name"],
                    "severity": item["severity"],
                    "description": item["description"],
                    "threshold": 1,
                },
            )
        return MarketingAlertRule.objects.filter(workspace_id=self.workspace_id).order_by("alert_type")

    @staticmethod
    def _snapshot(issue, overview):
        return {
            "count": issue["count"],
            "range": overview["range"],
            "generated_at": overview["generated_at"].isoformat(),
        }

    @staticmethod
    def _apply_sla_deadlines(alert, rule, anchor=None, reset=False):
        anchor = anchor or alert.sla_started_at or alert.first_triggered_at or timezone.now()
        alert.sla_started_at = anchor
        if rule is None:
            alert.response_due_at = None
            alert.resolution_due_at = None
        else:
            alert.response_due_at = anchor + timedelta(minutes=rule.response_sla_minutes)
            alert.resolution_due_at = anchor + timedelta(minutes=rule.resolution_sla_minutes)
        if reset:
            alert.first_responded_at = None
            alert.response_escalated_at = None
            alert.resolution_escalated_at = None

    def _workspace_members(self):
        user_ids = set()
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
        if not user_ids:
            from marketing.models import MarketingTask

            user_ids.update(
                MarketingTask.objects.filter(
                    workspace_id=self.workspace_id,
                    user__isnull=False,
                    user__is_active=True,
                ).values_list("user_id", flat=True)
            )
        if self.user and self.user.is_active:
            user_ids.add(self.user.id)
        return User.objects.filter(id__in=user_ids, is_active=True).order_by("nick_name", "username")

    def members(self):
        return [
            {
                "id": str(user.id),
                "name": _user_name(user),
                "username": user.username,
            }
            for user in self._workspace_members()
        ]

    @staticmethod
    def _rule_snapshot(rule):
        return {
            "enabled": rule.enabled,
            "threshold": rule.threshold,
            "severity": rule.severity,
            "response_sla_minutes": rule.response_sla_minutes,
            "resolution_sla_minutes": rule.resolution_sla_minutes,
            "escalation_user_id": str(rule.escalation_user_id) if rule.escalation_user_id else None,
            "escalation_user_name": rule.escalation_user_name,
        }

    def _record_rule_change(self, rule, change_type, reason):
        latest_version = rule.changes.aggregate(value=Max("version"))["value"] or 0
        return MarketingAlertRuleChange.objects.create(
            workspace_id=self.workspace_id,
            rule=rule,
            version=latest_version + 1,
            change_type=change_type,
            snapshot=self._rule_snapshot(rule),
            reason=reason,
            operator=self.user,
            operator_name=_user_name(self.user),
        )

    def _refresh_rule_alert_sla(self, rule):
        for alert in MarketingAlert.objects.filter(
            workspace_id=self.workspace_id,
            rule=rule,
            source_active=True,
        ).exclude(status=MarketingAlertStatus.CLOSED):
            self._apply_sla_deadlines(alert, rule)
            alert.save(update_fields=["sla_started_at", "response_due_at", "resolution_due_at", "update_time"])

    @staticmethod
    def _append_action(alert, action, previous_status, operator, operator_name, note="", snapshot=None):
        alert.revision += 1
        action_snapshot = {
            "count": alert.current_count,
            "source_active": alert.source_active,
            "severity": alert.severity,
        }
        action_snapshot.update(snapshot or {})
        return MarketingAlertActionRecord.objects.create(
            workspace_id=alert.workspace_id,
            alert=alert,
            action=action,
            previous_status=previous_status,
            current_status=alert.status,
            operator=operator,
            operator_name=operator_name,
            note=note,
            snapshot=action_snapshot,
            revision=alert.revision,
        )

    @transaction.atomic
    def update_subscriber(self, alert_id, data):
        values = validate_or_raise(MarketingAlertSubscriberSerializer(data=data))
        alert = (
            MarketingAlert.objects.select_for_update()
            .filter(id=alert_id, workspace_id=self.workspace_id)
            .first()
        )
        if alert is None:
            raise AppApiException(404, "告警不存在")
        target = self._workspace_members().filter(id=values["user_id"]).first()
        if target is None:
            raise AppApiException(400, "关注人不属于当前工作空间")
        operator_name = _user_name(self.user)
        target_name = _user_name(target)
        if values["action"] == "ADD":
            _, created = MarketingAlertSubscriber.objects.get_or_create(
                workspace_id=self.workspace_id,
                alert=alert,
                user=target,
                defaults={
                    "user_name": target_name,
                    "subscribed_by": self.user,
                    "subscribed_by_name": operator_name,
                },
            )
            if not created:
                raise AppApiException(400, "该成员已关注此告警")
            record_action = MarketingAlertAction.SUBSCRIBED
            note = f"添加 {target_name} 为告警关注人"
        else:
            subscriber = MarketingAlertSubscriber.objects.filter(alert=alert, user=target).first()
            if subscriber is None:
                raise AppApiException(400, "该成员尚未关注此告警")
            subscriber.delete()
            record_action = MarketingAlertAction.UNSUBSCRIBED
            note = f"移除告警关注人 {target_name}"
        self._append_action(
            alert,
            record_action,
            alert.status,
            self.user,
            operator_name,
            note,
            {"subscriber_user_id": str(target.id), "subscriber_user_name": target_name},
        )
        alert.save(update_fields=["revision", "update_time"])
        return self._serialize_alert(self._queryset().get(id=alert.id))

    @transaction.atomic
    def upload_attachment(self, alert_id, uploaded_file):
        alert = (
            MarketingAlert.objects.select_for_update()
            .filter(id=alert_id, workspace_id=self.workspace_id)
            .first()
        )
        if alert is None:
            raise AppApiException(404, "告警不存在")
        if uploaded_file is None:
            raise AppApiException(400, "请选择要上传的附件")
        max_size = 10 * 1024 * 1024
        if uploaded_file.size > max_size:
            raise AppApiException(400, "附件不能超过 10 MB")
        file_name = Path(uploaded_file.name).name
        extension = Path(file_name).suffix.lower().lstrip(".")
        allowed_extensions = {"png", "jpg", "jpeg", "webp", "pdf", "txt", "log", "csv", "json", "zip"}
        if extension not in allowed_extensions:
            raise AppApiException(400, "仅支持图片、PDF、文本、日志、CSV、JSON 和 ZIP 文件")

        from knowledge.models import File

        stored_file = File(
            file_name=file_name,
            source_id=str(alert.id),
            source_type="MARKETING",
            meta={"workspace_id": self.workspace_id, "alert_id": str(alert.id)},
        )
        stored_file.save(uploaded_file.read())
        operator_name = _user_name(self.user)
        record = self._append_action(
            alert,
            MarketingAlertAction.ATTACHED,
            alert.status,
            self.user,
            operator_name,
            f"上传附件 {file_name}",
            {"file_id": str(stored_file.id), "file_name": file_name, "file_size": uploaded_file.size},
        )
        MarketingAlertAttachment.objects.create(
            workspace_id=self.workspace_id,
            alert=alert,
            action_record=record,
            file_id=stored_file.id,
            file_name=file_name,
            content_type=uploaded_file.content_type or "application/octet-stream",
            file_size=uploaded_file.size,
            uploader=self.user,
            uploader_name=operator_name,
            expires_at=timezone.now() + timedelta(days=30),
        )
        alert.save(update_fields=["revision", "update_time"])
        return self._serialize_alert(self._queryset().get(id=alert.id))

    def attachment_file(self, alert_id, attachment_id):
        attachment = MarketingAlertAttachment.objects.filter(
            id=attachment_id,
            alert_id=alert_id,
            workspace_id=self.workspace_id,
        ).first()
        if attachment is None:
            raise AppApiException(404, "附件不存在")
        if attachment.expires_at and attachment.expires_at <= timezone.now():
            raise AppApiException(410, "附件已超过保留期限")
        from knowledge.models import File

        stored_file = File.objects.filter(id=attachment.file_id, source_type="MARKETING").first()
        if stored_file is None:
            raise AppApiException(404, "附件文件不存在")
        return attachment, stored_file

    @staticmethod
    def _active_round(alert):
        return (
            MarketingAlertHandlingRound.objects.select_for_update()
            .filter(alert=alert, ended_at__isnull=True)
            .order_by("-sequence")
            .first()
        )

    def _start_round(self, alert, assignee, assigned_by, now, responded=False):
        current = self._active_round(alert)
        if current:
            return current
        sequence = (
            MarketingAlertHandlingRound.objects.filter(alert=alert).aggregate(max_sequence=Max("sequence"))[
                "max_sequence"
            ]
            or 0
        ) + 1
        response_due_at = None
        if alert.rule:
            response_due_at = now + timedelta(minutes=alert.rule.response_sla_minutes)
            if alert.resolution_due_at:
                response_due_at = min(response_due_at, alert.resolution_due_at)
        return MarketingAlertHandlingRound.objects.create(
            workspace_id=alert.workspace_id,
            alert=alert,
            sequence=sequence,
            assignee=assignee,
            assignee_name=_user_name(assignee),
            assigned_by=assigned_by,
            assigned_by_name=_user_name(assigned_by),
            assigned_at=now,
            response_due_at=response_due_at,
            resolution_due_at=alert.resolution_due_at,
            first_responded_at=now if responded else None,
        )

    def _respond_round(self, alert, now):
        round_row = self._active_round(alert)
        if round_row and not round_row.first_responded_at:
            round_row.first_responded_at = now
            round_row.save(update_fields=["first_responded_at", "update_time"])
        return round_row

    def _finish_round(self, alert, reason, note, now):
        round_row = self._active_round(alert)
        if not round_row:
            return None
        round_row.ended_at = now
        round_row.end_reason = reason
        round_row.end_note = note
        round_row.save(update_fields=["ended_at", "end_reason", "end_note", "update_time"])
        return round_row

    def _evaluate_sla(self, now):
        alerts = list(
            MarketingAlert.objects.select_for_update()
            .filter(workspace_id=self.workspace_id, source_active=True)
            .exclude(status=MarketingAlertStatus.CLOSED)
        )
        rules = {
            rule.id: rule
            for rule in MarketingAlertRule.objects.filter(id__in=[alert.rule_id for alert in alerts if alert.rule_id])
        }
        for alert in alerts:
            rule = rules.get(alert.rule_id)
            if rule is None or not rule.enabled:
                continue
            changed = False
            if (
                not alert.first_responded_at
                and alert.response_due_at
                and alert.response_due_at <= now
                and not alert.response_escalated_at
            ):
                alert.response_escalated_at = now
                self._append_action(
                    alert,
                    MarketingAlertAction.RESPONSE_OVERDUE,
                    alert.status,
                    None,
                    "系统",
                    f"告警超过 {rule.response_sla_minutes} 分钟未响应，已升级提醒。",
                )
                changed = True
            if (
                alert.resolution_due_at
                and alert.resolution_due_at <= now
                and not alert.resolution_escalated_at
            ):
                alert.resolution_escalated_at = now
                self._append_action(
                    alert,
                    MarketingAlertAction.RESOLUTION_OVERDUE,
                    alert.status,
                    None,
                    "系统",
                    f"告警超过 {rule.resolution_sla_minutes} 分钟未关闭，已升级提醒。",
                )
                changed = True
            if changed:
                alert.save()

    @transaction.atomic
    def sync(self, data=None):
        values = validate_or_raise(MarketingAlertSyncSerializer(data=data or {}))
        overview = MarketingOperationsService(self.workspace_id, self.user).overview({"days": values["days"]})
        issues = {item["type"]: item for item in overview["issues"]}
        rules = list(self.ensure_rules())
        now = timezone.now()
        triggered_types = set()

        for rule in rules:
            issue = issues.get(rule.alert_type)
            if not rule.enabled or not issue or issue["count"] < rule.threshold:
                continue
            triggered_types.add(rule.alert_type)
            snapshot = self._snapshot(issue, overview)
            alert, created = MarketingAlert.objects.get_or_create(
                workspace_id=self.workspace_id,
                dedupe_key=rule.alert_type,
                defaults={
                    "rule": rule,
                    "alert_type": rule.alert_type,
                    "title": issue["title"],
                    "description": issue["description"],
                    "severity": rule.severity,
                    "status": MarketingAlertStatus.OPEN,
                    "current_count": issue["count"],
                    "source_active": True,
                    "source_snapshot": snapshot,
                    "target_route": issue["route"],
                    "first_triggered_at": now,
                    "last_triggered_at": now,
                    "sla_started_at": now,
                    "response_due_at": now + timedelta(minutes=rule.response_sla_minutes),
                    "resolution_due_at": now + timedelta(minutes=rule.resolution_sla_minutes),
                },
            )
            if created:
                self._append_action(
                    alert,
                    MarketingAlertAction.CREATED,
                    "",
                    None,
                    "系统",
                    "指标达到告警阈值，系统自动创建告警。",
                )
                alert.save(update_fields=["revision", "update_time"])
                continue

            alert = MarketingAlert.objects.select_for_update().get(id=alert.id)

            previous_status = alert.status
            previous_count = alert.current_count
            was_active = alert.source_active
            action = None
            note = ""
            if alert.status == MarketingAlertStatus.CLOSED and not was_active:
                alert.status = MarketingAlertStatus.OPEN
                alert.assignee = None
                alert.assignee_name = ""
                alert.closed_at = None
                alert.close_note = ""
                alert.root_cause_category = ""
                alert.resolution_type = ""
                alert.impact_scope = ""
                self._apply_sla_deadlines(alert, rule, now, reset=True)
                action = MarketingAlertAction.REOPENED
                note = "来源指标恢复后再次达到阈值，系统自动重新打开。"
            elif previous_count != issue["count"] or not was_active or alert.severity != rule.severity:
                action = MarketingAlertAction.REFRESHED
                note = "来源指标发生变化，系统刷新告警快照。"
            alert.rule = rule
            alert.title = issue["title"]
            alert.description = issue["description"]
            alert.severity = rule.severity
            alert.current_count = issue["count"]
            alert.source_active = True
            alert.source_snapshot = snapshot
            alert.target_route = issue["route"]
            alert.last_triggered_at = now
            alert.resolved_at = None
            if not alert.sla_started_at or not alert.response_due_at or not alert.resolution_due_at:
                self._apply_sla_deadlines(alert, rule)
            if action:
                self._append_action(alert, action, previous_status, None, "系统", note)
            alert.save()

        inactive_rows = list(
            MarketingAlert.objects.select_for_update().filter(
                workspace_id=self.workspace_id,
                source_active=True,
            )
        )
        for alert in inactive_rows:
            if alert.alert_type in triggered_types:
                continue
            previous_status = alert.status
            alert.source_active = False
            alert.current_count = 0
            alert.resolved_at = now
            self._append_action(
                alert,
                MarketingAlertAction.REFRESHED,
                previous_status,
                None,
                "系统",
                "来源指标已恢复或低于当前规则阈值。",
            )
            alert.save()

        self._evaluate_sla(now)
        return self.summary()

    def summary(self):
        rows = MarketingAlert.objects.filter(workspace_id=self.workspace_id)
        now = timezone.now()
        return {
            "total_count": rows.count(),
            "active_count": rows.exclude(status=MarketingAlertStatus.CLOSED).count(),
            "open_count": rows.filter(status=MarketingAlertStatus.OPEN).count(),
            "claimed_count": rows.filter(status=MarketingAlertStatus.CLAIMED).count(),
            "processing_count": rows.filter(status=MarketingAlertStatus.PROCESSING).count(),
            "closed_count": rows.filter(status=MarketingAlertStatus.CLOSED).count(),
            "critical_count": rows.exclude(status=MarketingAlertStatus.CLOSED).filter(
                severity=MarketingAlertSeverity.CRITICAL
            ).count(),
            "sla_overdue_count": rows.exclude(status=MarketingAlertStatus.CLOSED)
            .filter(source_active=True)
            .filter(
                Q(first_responded_at__isnull=True, response_due_at__lte=now)
                | Q(resolution_due_at__lte=now)
            )
            .distinct()
            .count(),
        }

    @staticmethod
    def _duration_seconds(value):
        return round(value.total_seconds(), 2) if value else 0

    @staticmethod
    def _percentage(numerator, denominator):
        return round(numerator * 100 / denominator, 2) if denominator else 0

    @classmethod
    def _serialize_performance_metrics(cls, values):
        response_total = values.get("response_total") or 0
        response_met_count = values.get("response_met_count") or 0
        resolution_total = values.get("resolution_total") or 0
        resolution_met_count = values.get("resolution_met_count") or 0
        milestone_total = response_total + resolution_total
        milestone_met_count = response_met_count + resolution_met_count
        return {
            "total_count": values.get("total_count") or 0,
            "active_count": values.get("active_count") or 0,
            "closed_count": values.get("closed_count") or 0,
            "overdue_count": values.get("overdue_count") or 0,
            "avg_response_seconds": cls._duration_seconds(values.get("avg_response_duration")),
            "avg_resolution_seconds": cls._duration_seconds(values.get("avg_resolution_duration")),
            "response_total": response_total,
            "response_met_count": response_met_count,
            "response_sla_rate": cls._percentage(response_met_count, response_total),
            "resolution_total": resolution_total,
            "resolution_met_count": resolution_met_count,
            "resolution_sla_rate": cls._percentage(resolution_met_count, resolution_total),
            "sla_milestone_total": milestone_total,
            "sla_milestone_met_count": milestone_met_count,
            "sla_attainment_rate": cls._percentage(milestone_met_count, milestone_total),
        }

    @staticmethod
    def _performance_annotations(now):
        active_filter = ~Q(status=MarketingAlertStatus.CLOSED)
        response_completed_filter = Q(first_responded_at__isnull=False, sla_started_at__isnull=False)
        resolution_completed_filter = Q(closed_at__isnull=False, sla_started_at__isnull=False)
        response_evaluated_filter = response_completed_filter | Q(
            first_responded_at__isnull=True,
            response_due_at__lte=now,
        )
        resolution_evaluated_filter = resolution_completed_filter | Q(
            closed_at__isnull=True,
            resolution_due_at__lte=now,
        )
        overdue_filter = (
            active_filter
            & Q(source_active=True)
            & (
                Q(first_responded_at__isnull=True, response_due_at__lte=now)
                | Q(resolution_due_at__lte=now)
            )
        )
        response_duration = ExpressionWrapper(
            F("first_responded_at") - F("sla_started_at"),
            output_field=DurationField(),
        )
        resolution_duration = ExpressionWrapper(
            F("closed_at") - F("sla_started_at"),
            output_field=DurationField(),
        )
        return {
            "total_count": Count("id"),
            "active_count": Count("id", filter=active_filter),
            "closed_count": Count("id", filter=Q(status=MarketingAlertStatus.CLOSED)),
            "overdue_count": Count("id", filter=overdue_filter),
            "response_total": Count("id", filter=response_evaluated_filter),
            "response_met_count": Count(
                "id",
                filter=response_completed_filter
                & Q(response_due_at__isnull=False, first_responded_at__lte=F("response_due_at")),
            ),
            "resolution_total": Count("id", filter=resolution_evaluated_filter),
            "resolution_met_count": Count(
                "id",
                filter=resolution_completed_filter
                & Q(resolution_due_at__isnull=False, closed_at__lte=F("resolution_due_at")),
            ),
            "avg_response_duration": Avg(response_duration, filter=response_completed_filter),
            "avg_resolution_duration": Avg(resolution_duration, filter=resolution_completed_filter),
        }

    def performance(self, data=None):
        values = validate_or_raise(MarketingAlertPerformanceQuerySerializer(data=data or {}))
        days = values["days"]
        now = timezone.now()
        start_at = now - timedelta(days=days)
        rows = MarketingAlert.objects.filter(
            workspace_id=self.workspace_id,
            sla_started_at__gte=start_at,
            sla_started_at__lte=now,
        )
        annotations = self._performance_annotations(now)
        summary_values = rows.aggregate(**annotations)
        summary_values["unassigned_count"] = rows.filter(
            assignee__isnull=True,
        ).exclude(status=MarketingAlertStatus.CLOSED).count()
        workload_buckets = {}

        def get_bucket(assignee_id, assignee_name):
            key = str(assignee_id) if assignee_id else "UNASSIGNED"
            if key not in workload_buckets:
                workload_buckets[key] = {
                    "assignee_id": str(assignee_id) if assignee_id else None,
                    "assignee_name": assignee_name or "未认领",
                    "total_count": 0,
                    "active_count": 0,
                    "closed_count": 0,
                    "overdue_count": 0,
                    "response_total": 0,
                    "response_met_count": 0,
                    "resolution_total": 0,
                    "resolution_met_count": 0,
                    "response_durations": [],
                    "resolution_durations": [],
                }
            return workload_buckets[key]

        def add_unit(
            bucket,
            *,
            active,
            closed,
            response_start,
            response_due,
            responded_at,
            resolution_start,
            resolution_due,
            resolved_at,
            evaluation_end,
            source_active,
        ):
            bucket["total_count"] += 1
            bucket["active_count"] += int(active)
            bucket["closed_count"] += int(closed)
            response_evaluated = bool(responded_at or (response_due and response_due <= evaluation_end))
            response_met = bool(responded_at and response_due and responded_at <= response_due)
            resolution_evaluated = bool(resolved_at or (resolution_due and resolution_due <= evaluation_end))
            resolution_met = bool(resolved_at and resolution_due and resolved_at <= resolution_due)
            bucket["response_total"] += int(response_evaluated)
            bucket["response_met_count"] += int(response_met)
            bucket["resolution_total"] += int(resolution_evaluated)
            bucket["resolution_met_count"] += int(resolution_met)
            bucket["overdue_count"] += int(
                active
                and source_active
                and ((response_evaluated and not response_met) or (resolution_evaluated and not resolution_met))
            )
            if responded_at and response_start:
                bucket["response_durations"].append((responded_at - response_start).total_seconds())
            if resolved_at and resolution_start:
                bucket["resolution_durations"].append((resolved_at - resolution_start).total_seconds())

        performance_rows = rows.select_related("assignee").prefetch_related("handling_rounds")
        for alert in performance_rows:
            handling_rounds = list(alert.handling_rounds.all())
            if len(handling_rounds) <= 1:
                bucket = get_bucket(alert.assignee_id, alert.assignee_name)
                add_unit(
                    bucket,
                    active=alert.status != MarketingAlertStatus.CLOSED,
                    closed=alert.status == MarketingAlertStatus.CLOSED,
                    response_start=alert.sla_started_at,
                    response_due=alert.response_due_at,
                    responded_at=alert.first_responded_at,
                    resolution_start=alert.sla_started_at,
                    resolution_due=alert.resolution_due_at,
                    resolved_at=alert.closed_at,
                    evaluation_end=now,
                    source_active=alert.source_active,
                )
                continue
            for round_row in handling_rounds:
                evaluation_end = round_row.ended_at or now
                active = not round_row.ended_at and alert.status != MarketingAlertStatus.CLOSED
                closed = round_row.end_reason == MarketingAlertRoundEndReason.CLOSED
                bucket = get_bucket(round_row.assignee_id, round_row.assignee_name)
                add_unit(
                    bucket,
                    active=active,
                    closed=closed,
                    response_start=round_row.assigned_at,
                    response_due=round_row.response_due_at,
                    responded_at=round_row.first_responded_at,
                    resolution_start=round_row.assigned_at,
                    resolution_due=round_row.resolution_due_at,
                    resolved_at=round_row.ended_at if closed else None,
                    evaluation_end=evaluation_end,
                    source_active=alert.source_active,
                )

        workload = []
        for bucket in workload_buckets.values():
            response_durations = bucket.pop("response_durations")
            resolution_durations = bucket.pop("resolution_durations")
            bucket["avg_response_seconds"] = (
                round(sum(response_durations) / len(response_durations), 2) if response_durations else 0
            )
            bucket["avg_resolution_seconds"] = (
                round(sum(resolution_durations) / len(resolution_durations), 2) if resolution_durations else 0
            )
            bucket["response_sla_rate"] = self._percentage(
                bucket["response_met_count"], bucket["response_total"]
            )
            bucket["resolution_sla_rate"] = self._percentage(
                bucket["resolution_met_count"], bucket["resolution_total"]
            )
            bucket["sla_milestone_total"] = bucket["response_total"] + bucket["resolution_total"]
            bucket["sla_milestone_met_count"] = (
                bucket["response_met_count"] + bucket["resolution_met_count"]
            )
            bucket["sla_attainment_rate"] = self._percentage(
                bucket["sla_milestone_met_count"], bucket["sla_milestone_total"]
            )
            workload.append(bucket)
        workload.sort(
            key=lambda item: (
                item["assignee_id"] is not None,
                -item["active_count"],
                item["assignee_name"],
            )
        )
        summary = self._serialize_performance_metrics(summary_values)
        summary["unassigned_count"] = summary_values["unassigned_count"]
        return {
            "range": {
                "days": days,
                "start_at": start_at,
                "end_at": now,
            },
            "summary": summary,
            "workload": workload,
        }

    def noise_analysis(self, data=None):
        values = validate_or_raise(MarketingAlertNoiseAnalysisQuerySerializer(data=data or {}))
        days = values["days"]
        now = timezone.now()
        start_at = now - timedelta(days=days)
        refresh_filter = Q(
            actions__action=MarketingAlertAction.REFRESHED,
            actions__create_time__gte=start_at,
            actions__create_time__lte=now,
        )
        reopen_filter = Q(
            actions__action=MarketingAlertAction.REOPENED,
            actions__create_time__gte=start_at,
            actions__create_time__lte=now,
        )
        alerts = list(
            MarketingAlert.objects.filter(workspace_id=self.workspace_id)
            .annotate(
                refresh_count=Count("actions", filter=refresh_filter, distinct=True),
                reopen_count=Count("actions", filter=reopen_filter, distinct=True),
            )
            .order_by("-last_triggered_at")
        )

        noise_alerts = []
        for alert in alerts:
            repeat_count = alert.refresh_count + alert.reopen_count
            if repeat_count == 0:
                continue
            noise_score = alert.refresh_count + alert.reopen_count * 2
            if alert.refresh_count >= 5 or alert.reopen_count >= 2 or noise_score >= 5:
                noise_level, noise_label = "HIGH", "高噪声"
            elif repeat_count >= 2:
                noise_level, noise_label = "MEDIUM", "需关注"
            else:
                noise_level, noise_label = "LOW", "轻微重复"
            experience = next(iter(self._historical_experiences(alert, limit=1, include_current=True)), None)
            if experience:
                recommendation = "存在同类历史处置结论，建议复用归因并核对本轮影响范围。"
            elif alert.reopen_count:
                recommendation = "告警曾重新打开，建议先验证上次修复是否彻底。"
            elif alert.refresh_count >= 5:
                recommendation = "短期指标刷新频繁，建议评估提高阈值或延长观测窗口。"
            else:
                recommendation = "继续观察指标变化，避免对单次波动重复处置。"
            noise_alerts.append(
                {
                    "id": str(alert.id),
                    "title": alert.title,
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "status": alert.status,
                    "current_count": alert.current_count,
                    "refresh_count": alert.refresh_count,
                    "reopen_count": alert.reopen_count,
                    "repeat_count": repeat_count,
                    "noise_score": noise_score,
                    "noise_level": noise_level,
                    "noise_label": noise_label,
                    "recommendation": recommendation,
                    "suggested_root_cause_category": (
                        experience["root_cause_category"] if experience else ""
                    ),
                    "suggested_root_cause_label": experience["root_cause_label"] if experience else "",
                    "suggested_resolution_type": experience["resolution_type"] if experience else "",
                    "suggested_resolution_type_label": (
                        experience["resolution_type_label"] if experience else ""
                    ),
                    "suggested_note": experience["close_note"] if experience else "",
                    "last_triggered_at": alert.last_triggered_at,
                }
            )
        noise_alerts.sort(
            key=lambda item: (item["noise_score"], item["last_triggered_at"]),
            reverse=True,
        )

        route_groups = {}
        for alert in alerts:
            if alert.status == MarketingAlertStatus.CLOSED or not alert.target_route:
                continue
            route_key = alert.target_route.split("?", 1)[0]
            route_groups.setdefault(route_key, []).append(alert)
        severity_rank = {
            MarketingAlertSeverity.CRITICAL: 3,
            MarketingAlertSeverity.WARNING: 2,
            MarketingAlertSeverity.INFO: 1,
        }
        merge_suggestions = []
        for route, candidates in route_groups.items():
            if len(candidates) < 2:
                continue
            candidates.sort(
                key=lambda row: (severity_rank.get(row.severity, 0), row.last_triggered_at),
                reverse=True,
            )
            primary = candidates[0]
            merge_suggestions.append(
                {
                    "group_key": route,
                    "primary_alert_id": str(primary.id),
                    "primary_alert_title": primary.title,
                    "alert_count": len(candidates),
                    "total_current_count": sum(row.current_count for row in candidates),
                    "reason": f"{len(candidates)} 条未关闭告警指向同一处理页面，建议合并排查上下文。",
                    "recommendation": "优先处理最高级别主告警，其他告警保留独立状态并共享排查结论。",
                    "candidates": [
                        {
                            "id": str(row.id),
                            "title": row.title,
                            "alert_type": row.alert_type,
                            "severity": row.severity,
                            "status": row.status,
                            "current_count": row.current_count,
                        }
                        for row in candidates
                    ],
                }
            )
        merge_suggestions.sort(
            key=lambda item: (item["alert_count"], item["total_current_count"]),
            reverse=True,
        )

        return {
            "range": {"days": days, "start_at": start_at, "end_at": now},
            "summary": {
                "monitored_alert_count": len(alerts),
                "repeated_alert_count": sum(1 for row in noise_alerts if row["repeat_count"] >= 2),
                "high_noise_count": sum(1 for row in noise_alerts if row["noise_level"] == "HIGH"),
                "deduplicated_event_count": sum(row.refresh_count for row in alerts),
                "merge_suggestion_count": len(merge_suggestions),
            },
            "noise_alerts": noise_alerts[:10],
            "merge_suggestions": merge_suggestions[:8],
        }

    def retrospective(self, data=None):
        values = validate_or_raise(MarketingAlertRetrospectiveQuerySerializer(data=data or {}))
        days = values["days"]
        now = timezone.now()
        start_at = now - timedelta(days=days)
        closed_rows = MarketingAlert.objects.filter(
            workspace_id=self.workspace_id,
            status=MarketingAlertStatus.CLOSED,
            closed_at__gte=start_at,
            closed_at__lte=now,
        )
        if values.get("root_cause_category"):
            closed_rows = closed_rows.filter(root_cause_category=values["root_cause_category"])
        total_count = closed_rows.count()
        duration = ExpressionWrapper(
            F("closed_at") - F("sla_started_at"),
            output_field=DurationField(),
        )
        average_resolution = closed_rows.aggregate(value=Avg(duration))["value"]
        root_cause_labels = dict(MarketingAlertRootCause.choices)
        resolution_labels = dict(MarketingAlertResolutionType.choices)

        def distribution(field, labels):
            rows = (
                closed_rows.exclude(**{field: ""})
                .values(field)
                .annotate(count=Count("id"))
                .order_by("-count", field)
            )
            return [
                {
                    "value": row[field],
                    "label": labels.get(row[field], row[field]),
                    "count": row["count"],
                    "percentage": self._percentage(row["count"], total_count),
                }
                for row in rows
            ]

        recurrence_filter = Q(
            actions__action=MarketingAlertAction.REOPENED,
            actions__create_time__gte=start_at,
            actions__create_time__lte=now,
        )
        recurring_rows = (
            MarketingAlert.objects.filter(workspace_id=self.workspace_id)
            .annotate(recurrence_count=Count("actions", filter=recurrence_filter))
            .filter(recurrence_count__gt=0)
            .order_by("-recurrence_count", "-last_triggered_at")[:8]
        )
        experience_rows = closed_rows.exclude(root_cause_category="").order_by("-closed_at")[:10]
        return {
            "range": {"days": days, "start_at": start_at, "end_at": now},
            "summary": {
                "closed_count": total_count,
                "classified_count": closed_rows.exclude(root_cause_category="").count(),
                "recurrence_count": MarketingAlertActionRecord.objects.filter(
                    workspace_id=self.workspace_id,
                    action=MarketingAlertAction.REOPENED,
                    create_time__gte=start_at,
                    create_time__lte=now,
                ).count(),
                "avg_resolution_seconds": self._duration_seconds(average_resolution),
            },
            "root_causes": distribution("root_cause_category", root_cause_labels),
            "resolution_types": distribution("resolution_type", resolution_labels),
            "recurring_alerts": [
                {
                    "id": str(row.id),
                    "title": row.title,
                    "alert_type": row.alert_type,
                    "recurrence_count": row.recurrence_count,
                    "status": row.status,
                    "last_triggered_at": row.last_triggered_at,
                }
                for row in recurring_rows
            ],
            "experiences": [
                {
                    "id": str(row.id),
                    "title": row.title,
                    "alert_type": row.alert_type,
                    "root_cause_category": row.root_cause_category,
                    "root_cause_label": row.get_root_cause_category_display(),
                    "resolution_type": row.resolution_type,
                    "resolution_type_label": row.get_resolution_type_display(),
                    "impact_scope": row.impact_scope,
                    "close_note": row.close_note,
                    "assignee_name": row.assignee_name,
                    "closed_at": row.closed_at,
                }
                for row in experience_rows
            ],
        }

    def retrospective_export_rows(self, data=None):
        values = validate_or_raise(MarketingAlertRetrospectiveQuerySerializer(data=data or {}))
        now = timezone.now()
        rows = MarketingAlert.objects.filter(
            workspace_id=self.workspace_id,
            status=MarketingAlertStatus.CLOSED,
            closed_at__gte=now - timedelta(days=values["days"]),
            closed_at__lte=now,
        )
        if values.get("root_cause_category"):
            rows = rows.filter(root_cause_category=values["root_cause_category"])
        return [
            {
                "title": row.title,
                "alert_type": row.alert_type,
                "severity": row.get_severity_display(),
                "assignee_name": row.assignee_name,
                "root_cause": row.get_root_cause_category_display() if row.root_cause_category else "未分类",
                "resolution_type": row.get_resolution_type_display() if row.resolution_type else "未分类",
                "impact_scope": row.impact_scope,
                "close_note": row.close_note,
                "first_triggered_at": row.first_triggered_at,
                "closed_at": row.closed_at,
                "resolution_seconds": (
                    round((row.closed_at - row.sla_started_at).total_seconds(), 2)
                    if row.closed_at and row.sla_started_at
                    else 0
                ),
            }
            for row in rows.order_by("-closed_at")
        ]

    def page(self, current_page, page_size, params):
        values = validate_or_raise(MarketingAlertQuerySerializer(data=params))
        rows = self._queryset()
        if values.get("status"):
            rows = rows.filter(status=values["status"])
        if values.get("severity"):
            rows = rows.filter(severity=values["severity"])
        if values.get("alert_type"):
            rows = rows.filter(alert_type=values["alert_type"])
        if values.get("keyword"):
            keyword = values["keyword"]
            rows = rows.filter(
                Q(title__icontains=keyword)
                | Q(description__icontains=keyword)
                | Q(assignee_name__icontains=keyword)
            )
        if values.get("assignee_id"):
            rows = rows.filter(assignee_id=values["assignee_id"])
        if values["unassigned"]:
            rows = rows.filter(assignee__isnull=True)
        if values["active_only"]:
            rows = rows.exclude(status=MarketingAlertStatus.CLOSED)
        if values["sla_overdue"]:
            now = timezone.now()
            rows = (
                rows.exclude(status=MarketingAlertStatus.CLOSED)
                .filter(source_active=True)
                .filter(
                    Q(first_responded_at__isnull=True, response_due_at__lte=now)
                    | Q(resolution_due_at__lte=now)
                )
            )
        rows = rows.annotate(
            status_order=Case(
                When(status=MarketingAlertStatus.OPEN, then=Value(0)),
                When(status=MarketingAlertStatus.CLAIMED, then=Value(1)),
                When(status=MarketingAlertStatus.PROCESSING, then=Value(2)),
                default=Value(3),
                output_field=IntegerField(),
            ),
            severity_order=Case(
                When(severity=MarketingAlertSeverity.CRITICAL, then=Value(0)),
                When(severity=MarketingAlertSeverity.WARNING, then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            ),
        ).order_by("status_order", "severity_order", "-last_triggered_at")
        total = rows.count()
        start = (current_page - 1) * page_size
        page = Page(total, [self._serialize_alert(row) for row in rows[start : start + page_size]], current_page, page_size)
        page["summary"] = self.summary()
        return page

    def rules(self):
        return [serialize_alert_rule(rule) for rule in self.ensure_rules()]

    def rule_effect(self, data=None):
        values = validate_or_raise(MarketingAlertRuleEffectQuerySerializer(data=data or {}))
        days = values["days"]
        now = timezone.now()
        start_at = now - timedelta(days=days)
        rows = []
        for rule in self.ensure_rules():
            actions = list(
                MarketingAlertActionRecord.objects.filter(
                    workspace_id=self.workspace_id,
                    alert__alert_type=rule.alert_type,
                    create_time__gte=start_at,
                    create_time__lte=now,
                ).order_by("create_time")
            )
            signal_actions = [
                action
                for action in actions
                if action.action
                in (MarketingAlertAction.CREATED, MarketingAlertAction.REFRESHED, MarketingAlertAction.REOPENED)
                and (action.snapshot or {}).get("source_active", True)
            ]
            samples = []
            for action in signal_actions:
                try:
                    sample_count = int((action.snapshot or {}).get("count", 0))
                except (TypeError, ValueError):
                    continue
                if sample_count > 0:
                    samples.append(sample_count)
            samples.sort()
            refresh_count = sum(action.action == MarketingAlertAction.REFRESHED for action in actions)
            reopen_count = sum(action.action == MarketingAlertAction.REOPENED for action in actions)
            close_actions = [action for action in actions if action.action == MarketingAlertAction.CLOSED]
            false_positive_count = sum(
                (action.snapshot or {}).get("resolution_type") == MarketingAlertResolutionType.FALSE_POSITIVE
                for action in close_actions
            )
            repeat_count = refresh_count + reopen_count
            repeat_rate = self._percentage(repeat_count, len(signal_actions))
            false_positive_rate = self._percentage(false_positive_count, len(close_actions))
            if samples:
                percentile_index = max(0, ((len(samples) * 75 + 99) // 100) - 1)
                percentile_75 = samples[percentile_index]
            else:
                percentile_75 = rule.threshold
            should_raise = bool(false_positive_rate >= 25 or repeat_rate >= 50 or refresh_count >= 5)
            recommended_threshold = (
                min(100000, max(rule.threshold + 1, percentile_75)) if should_raise else rule.threshold
            )
            if should_raise and recommended_threshold == rule.threshold:
                recommendation_reason = "当前阈值已达到可配置上限，建议保持并排查信号来源。"
            elif should_raise:
                recommendation_reason = "重复或误报比例偏高，建议提高阈值并继续观察一个周期。"
            elif not samples:
                recommendation_reason = "当前周期没有有效触发样本，建议保持现有阈值。"
            else:
                recommendation_reason = "当前触发质量稳定，建议保持现有阈值。"
            candidate_thresholds = sorted(
                {
                    rule.threshold,
                    recommended_threshold,
                    min(100000, max(rule.threshold + 1, (rule.threshold * 5 + 3) // 4)),
                    min(100000, max(rule.threshold + 1, (rule.threshold * 3 + 1) // 2)),
                }
            )
            baseline = len(samples)
            simulations = [
                {
                    "threshold": threshold,
                    "estimated_trigger_count": sum(sample >= threshold for sample in samples),
                    "estimated_reduction_rate": self._percentage(
                        baseline - sum(sample >= threshold for sample in samples),
                        baseline,
                    ),
                    "recommended": threshold == recommended_threshold,
                }
                for threshold in candidate_thresholds
            ]
            resolution_duration = ExpressionWrapper(
                F("ended_at") - F("assigned_at"),
                output_field=DurationField(),
            )
            average_resolution = MarketingAlertHandlingRound.objects.filter(
                workspace_id=self.workspace_id,
                alert__alert_type=rule.alert_type,
                end_reason=MarketingAlertRoundEndReason.CLOSED,
                ended_at__gte=start_at,
                ended_at__lte=now,
            ).aggregate(value=Avg(resolution_duration))["value"]
            if len(samples) >= 10:
                confidence = "HIGH"
            elif len(samples) >= 4:
                confidence = "MEDIUM"
            else:
                confidence = "LOW"
            rows.append(
                {
                    "rule": serialize_alert_rule(rule),
                    "metrics": {
                        "signal_event_count": len(signal_actions),
                        "refresh_count": refresh_count,
                        "reopen_count": reopen_count,
                        "repeat_rate": repeat_rate,
                        "closed_count": len(close_actions),
                        "false_positive_count": false_positive_count,
                        "false_positive_rate": false_positive_rate,
                        "avg_resolution_seconds": self._duration_seconds(average_resolution),
                    },
                    "recommendation": {
                        "threshold": recommended_threshold,
                        "changed": recommended_threshold != rule.threshold,
                        "reason": recommendation_reason,
                        "confidence": confidence,
                        "sample_count": len(samples),
                    },
                    "simulations": simulations,
                    "history": [
                        serialize_alert_rule_change(change)
                        for change in rule.changes.select_related("operator").all()[:10]
                    ],
                }
            )
        return {
            "range": {"days": days, "start_at": start_at, "end_at": now},
            "summary": {
                "rule_count": len(rows),
                "enabled_rule_count": sum(row["rule"]["enabled"] for row in rows),
                "optimization_count": sum(row["recommendation"]["changed"] for row in rows),
                "signal_event_count": sum(row["metrics"]["signal_event_count"] for row in rows),
                "false_positive_count": sum(row["metrics"]["false_positive_count"] for row in rows),
            },
            "rules": rows,
            "simulation_note": "阈值模拟基于当前规则已采集到的触发样本，不包含低于现有阈值的原始指标。",
        }

    def get(self, alert_id):
        alert = self._queryset().filter(id=alert_id).first()
        if alert is None:
            raise AppApiException(404, "告警不存在")
        return self._serialize_alert(alert)

    @transaction.atomic
    def update_rule(self, rule_id, data):
        values = validate_or_raise(MarketingAlertRuleUpdateSerializer(data=data))
        rule = (
            MarketingAlertRule.objects.select_for_update()
            .filter(id=rule_id, workspace_id=self.workspace_id)
            .first()
        )
        if rule is None:
            raise AppApiException(404, "告警规则不存在")
        change_reason = values.pop("change_reason", "").strip() or "人工调整告警规则"
        response_sla_minutes = values.get("response_sla_minutes", rule.response_sla_minutes)
        resolution_sla_minutes = values.get("resolution_sla_minutes", rule.resolution_sla_minutes)
        if resolution_sla_minutes < response_sla_minutes:
            raise AppApiException(400, "处理时限不能小于首次响应时限")
        self._record_rule_change(rule, MarketingAlertRuleChangeType.UPDATED, change_reason)
        if "escalation_user_id" in values:
            escalation_user_id = values.pop("escalation_user_id")
            escalation_user = None
            if escalation_user_id:
                escalation_user = self._workspace_members().filter(id=escalation_user_id).first()
                if escalation_user is None:
                    raise AppApiException(400, "升级接收人不属于当前工作空间")
            rule.escalation_user = escalation_user
            rule.escalation_user_name = _user_name(escalation_user) if escalation_user else ""
        for field, value in values.items():
            setattr(rule, field, value)
        rule.updated_by = self.user
        rule.updated_by_name = _user_name(self.user)
        rule.save()
        self._refresh_rule_alert_sla(rule)
        return serialize_alert_rule(rule)

    @transaction.atomic
    def rollback_rule(self, rule_id, data):
        values = validate_or_raise(MarketingAlertRuleRollbackSerializer(data=data))
        rule = (
            MarketingAlertRule.objects.select_for_update()
            .filter(id=rule_id, workspace_id=self.workspace_id)
            .first()
        )
        if rule is None:
            raise AppApiException(404, "告警规则不存在")
        change = MarketingAlertRuleChange.objects.filter(
            id=values["change_id"],
            rule=rule,
            workspace_id=self.workspace_id,
        ).first()
        if change is None:
            raise AppApiException(404, "规则历史版本不存在")
        snapshot = change.snapshot or {}
        required_fields = {
            "enabled",
            "threshold",
            "severity",
            "response_sla_minutes",
            "resolution_sla_minutes",
        }
        if not required_fields.issubset(snapshot):
            raise AppApiException(400, "规则历史快照不完整，无法回滚")
        reason = values.get("reason", "").strip() or f"回滚至历史版本 V{change.version}"
        self._record_rule_change(rule, MarketingAlertRuleChangeType.ROLLED_BACK, reason)
        for field in required_fields:
            setattr(rule, field, snapshot[field])
        rule.escalation_user_id = snapshot.get("escalation_user_id")
        rule.escalation_user_name = snapshot.get("escalation_user_name", "")
        rule.updated_by = self.user
        rule.updated_by_name = _user_name(self.user)
        rule.save()
        self._refresh_rule_alert_sla(rule)
        return serialize_alert_rule(rule)

    @transaction.atomic
    def handle(self, alert_id, data):
        values = validate_or_raise(MarketingAlertHandleSerializer(data=data))
        alert = (
            MarketingAlert.objects.select_for_update()
            .filter(id=alert_id, workspace_id=self.workspace_id)
            .first()
        )
        if alert is None:
            raise AppApiException(404, "告警不存在")
        action = values["action"]
        note = values.get("note", "")
        previous_status = alert.status
        operator_name = _user_name(self.user)
        now = timezone.now()
        action_snapshot = {}

        if action == "CLAIM":
            if alert.status != MarketingAlertStatus.OPEN:
                raise AppApiException(400, "只有待处理告警可以认领")
            alert.status = MarketingAlertStatus.CLAIMED
            alert.assignee = self.user
            alert.assignee_name = operator_name
            alert.first_responded_at = alert.first_responded_at or now
            self._start_round(alert, self.user, self.user, now, responded=True)
            record_action = MarketingAlertAction.CLAIMED
        elif action == "START":
            if alert.status not in (MarketingAlertStatus.OPEN, MarketingAlertStatus.CLAIMED):
                raise AppApiException(400, "只有待处理或已认领告警可以开始处理")
            if alert.assignee_id and alert.assignee_id != self.user.id:
                raise AppApiException(403, "只能由当前负责人开始处理")
            alert.status = MarketingAlertStatus.PROCESSING
            alert.assignee = self.user
            alert.assignee_name = operator_name
            alert.first_responded_at = alert.first_responded_at or now
            self._start_round(alert, self.user, self.user, now, responded=True)
            self._respond_round(alert, now)
            record_action = MarketingAlertAction.STARTED
        elif action == "CLOSE":
            if alert.status == MarketingAlertStatus.CLOSED:
                raise AppApiException(400, "告警已经关闭")
            if alert.assignee_id and alert.assignee_id != self.user.id and not self._can_manage():
                raise AppApiException(403, "只能由当前负责人或工作空间管理员关闭告警")
            alert.status = MarketingAlertStatus.CLOSED
            alert.assignee = alert.assignee or self.user
            alert.assignee_name = alert.assignee_name or operator_name
            alert.closed_at = now
            alert.close_note = note
            alert.root_cause_category = values["root_cause_category"]
            alert.resolution_type = values["resolution_type"]
            alert.impact_scope = values.get("impact_scope", "")
            alert.first_responded_at = alert.first_responded_at or alert.closed_at
            self._start_round(alert, alert.assignee, self.user, now, responded=True)
            self._respond_round(alert, now)
            self._finish_round(alert, MarketingAlertRoundEndReason.CLOSED, note, now)
            record_action = MarketingAlertAction.CLOSED
            action_snapshot = {
                "root_cause_category": alert.root_cause_category,
                "root_cause_label": alert.get_root_cause_category_display(),
                "resolution_type": alert.resolution_type,
                "resolution_type_label": alert.get_resolution_type_display(),
                "impact_scope": alert.impact_scope,
            }
        else:
            if alert.status != MarketingAlertStatus.CLOSED:
                raise AppApiException(400, "只有已关闭告警可以重新打开")
            self._finish_round(alert, MarketingAlertRoundEndReason.REOPENED, note, now)
            alert.status = MarketingAlertStatus.OPEN
            alert.assignee = None
            alert.assignee_name = ""
            alert.closed_at = None
            alert.close_note = ""
            alert.root_cause_category = ""
            alert.resolution_type = ""
            alert.impact_scope = ""
            self._apply_sla_deadlines(alert, alert.rule, now, reset=True)
            record_action = MarketingAlertAction.REOPENED

        self._append_action(
            alert,
            record_action,
            previous_status,
            self.user,
            operator_name,
            note,
            action_snapshot,
        )
        alert.save()
        return self._serialize_alert(self._queryset().get(id=alert.id))

    @transaction.atomic
    def collaborate(self, alert_id, data):
        values = validate_or_raise(MarketingAlertCollaborateSerializer(data=data))
        alert = (
            MarketingAlert.objects.select_for_update()
            .filter(id=alert_id, workspace_id=self.workspace_id)
            .first()
        )
        if alert is None:
            raise AppApiException(404, "告警不存在")
        action = values["action"]
        note = values.get("note", "")
        previous_status = alert.status
        operator_name = _user_name(self.user)
        now = timezone.now()

        if action == "COMMENT":
            record_action = MarketingAlertAction.COMMENTED
        else:
            if alert.status == MarketingAlertStatus.CLOSED:
                raise AppApiException(400, "已关闭告警不能指派或转派")
            target = self._workspace_members().filter(id=values["assignee_id"]).first()
            if target is None:
                raise AppApiException(400, "负责人不属于当前工作空间")
            previous_assignee_id = str(alert.assignee_id) if alert.assignee_id else None
            previous_assignee_name = alert.assignee_name

            if action == "ASSIGN":
                if not self._can_manage():
                    raise AppApiException(403, "只有工作空间管理员可以指派告警")
                if alert.assignee_id:
                    raise AppApiException(400, "告警已有负责人，请使用转派")
                record_action = MarketingAlertAction.ASSIGNED
            else:
                if not alert.assignee_id:
                    raise AppApiException(400, "未认领告警请先指派")
                if alert.assignee_id == target.id:
                    raise AppApiException(400, "新负责人不能与当前负责人相同")
                if alert.assignee_id != self.user.id and not self._can_manage():
                    raise AppApiException(403, "只有当前负责人或工作空间管理员可以转派告警")
                legacy_assigned_at = alert.first_responded_at or alert.sla_started_at or now
                self._start_round(
                    alert,
                    alert.assignee,
                    self.user,
                    legacy_assigned_at,
                    responded=bool(alert.first_responded_at),
                )
                self._finish_round(alert, MarketingAlertRoundEndReason.TRANSFERRED, note, now)
                record_action = MarketingAlertAction.TRANSFERRED

            alert.status = MarketingAlertStatus.CLAIMED
            alert.assignee = target
            alert.assignee_name = _user_name(target)
            self._start_round(alert, target, self.user, now)
            self._append_action(
                alert,
                record_action,
                previous_status,
                self.user,
                operator_name,
                note,
                {
                    "previous_assignee_id": previous_assignee_id,
                    "previous_assignee_name": previous_assignee_name,
                    "assignee_id": str(target.id),
                    "assignee_name": _user_name(target),
                },
            )
            alert.save()
            return self._serialize_alert(self._queryset().get(id=alert.id))

        self._append_action(alert, record_action, previous_status, self.user, operator_name, note)
        alert.save(update_fields=["revision", "update_time"])
        return self._serialize_alert(self._queryset().get(id=alert.id))
