# coding=utf-8
from collections import defaultdict
from datetime import timedelta

from django.db import transaction
from django.db.models import Count, Max, Q
from django.utils import timezone
from rest_framework import serializers

from common.exception.app_exception import AppApiException
from marketing.models import (
    ChangeCommunicationAudience,
    ChangeCommunicationChannel,
    ChangeCommunicationKind,
    ChangeCommunicationPhase,
    ChangeCommunicationStatus,
    ChangeConfirmationStatus,
    ChangeControlAction,
    ChangeControlActionRecord,
    ChangeControlStatus,
    ChangeOperation,
    ChangeOperationCommunication,
    ChangeOperationStatus,
    ChangeQualityReport,
    ChangeRiskLevel,
)
from marketing.serializers.change_operation import serialize_change_operation


class ChangeCommunicationCreateSerializer(serializers.Serializer):
    request_id = serializers.CharField(required=False, allow_blank=True, max_length=160)
    kind = serializers.ChoiceField(choices=ChangeCommunicationKind.choices)
    phase = serializers.ChoiceField(choices=ChangeCommunicationPhase.choices)
    audience = serializers.ChoiceField(choices=ChangeCommunicationAudience.choices)
    channel = serializers.ChoiceField(choices=ChangeCommunicationChannel.choices)
    subject = serializers.CharField(max_length=160)
    content = serializers.CharField(max_length=4000)
    scheduled_at = serializers.DateTimeField(required=False, allow_null=True)


class ChangeCommunicationStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=(
            ChangeCommunicationStatus.SENT,
            ChangeCommunicationStatus.ACKNOWLEDGED,
            ChangeCommunicationStatus.FAILED,
        )
    )
    failure_reason = serializers.CharField(required=False, allow_blank=True, max_length=2000)

    def validate(self, attrs):
        if attrs["status"] == ChangeCommunicationStatus.FAILED and not attrs.get("failure_reason", "").strip():
            raise serializers.ValidationError({"failure_reason": "标记发送失败时必须填写原因"})
        return attrs


class ChangeControlActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=ChangeControlAction.choices)
    note = serializers.CharField(required=False, allow_blank=True, max_length=2000)


class ChangeQualityReportGenerateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True, max_length=160)
    period_start = serializers.DateField()
    period_end = serializers.DateField()

    def validate(self, attrs):
        if attrs["period_end"] < attrs["period_start"]:
            raise serializers.ValidationError({"period_end": "统计结束日期不能早于开始日期"})
        if (attrs["period_end"] - attrs["period_start"]).days > 366:
            raise serializers.ValidationError({"period_end": "单次报告统计周期不能超过 366 天"})
        return attrs


def serialize_change_communication(row):
    return {
        "id": str(row.id),
        "operation_id": str(row.operation_id),
        "request_id": row.request_id,
        "kind": row.kind,
        "kind_label": row.get_kind_display(),
        "phase": row.phase,
        "phase_label": row.get_phase_display(),
        "audience": row.audience,
        "audience_label": row.get_audience_display(),
        "channel": row.channel,
        "channel_label": row.get_channel_display(),
        "subject": row.subject,
        "content": row.content,
        "status": row.status,
        "status_label": row.get_status_display(),
        "scheduled_at": row.scheduled_at,
        "sent_at": row.sent_at,
        "acknowledged_at": row.acknowledged_at,
        "failure_reason": row.failure_reason,
        "operator_name": row.user.nick_name if row.user else "",
        "create_time": row.create_time,
        "update_time": row.update_time,
    }


def serialize_change_control_action(row):
    return {
        "id": str(row.id),
        "revision": row.revision,
        "action": row.action,
        "action_label": row.get_action_display(),
        "previous_status": row.previous_status,
        "previous_status_label": row.get_previous_status_display(),
        "current_status": row.current_status,
        "current_status_label": row.get_current_status_display(),
        "note": row.note,
        "operator_name": row.user.nick_name if row.user else "",
        "create_time": row.create_time,
    }


def serialize_change_quality_report(row, *, include_snapshot=True):
    data = {
        "id": str(row.id),
        "title": row.title,
        "period_start": row.period_start,
        "period_end": row.period_end,
        "metrics": row.metrics or {},
        "generated_at": row.generated_at,
        "generator_name": row.user.nick_name if row.user else "",
    }
    if include_snapshot:
        data["daily_trend"] = row.daily_trend or []
        data["operations"] = row.operation_snapshot or []
    return data


def serialize_control_operation(row, *, include_history=False):
    data = serialize_change_operation(row, include_history=include_history)
    data.update(
        {
            "control_status": row.control_status,
            "control_status_label": row.get_control_status_display(),
            "actual_start_at": row.actual_start_at,
            "completed_at": row.completed_at,
            "communication_count": getattr(row, "communication_count", 0),
            "pending_communication_count": getattr(row, "pending_communication_count", 0),
        }
    )
    if include_history:
        data["communications"] = [serialize_change_communication(item) for item in row.communications.all()]
        data["control_actions"] = [serialize_change_control_action(item) for item in row.control_actions.all()]
    return data


class ChangeOperationControlService:
    def __init__(self, workspace_id, user=None):
        self.workspace_id = workspace_id
        self.user = user

    def _operation_queryset(self):
        return (
            ChangeOperation.objects.filter(workspace_id=self.workspace_id)
            .select_related("ivr_session", "user")
            .annotate(
                communication_count=Count("communications", distinct=True),
                pending_communication_count=Count(
                    "communications",
                    filter=Q(communications__status=ChangeCommunicationStatus.PENDING),
                    distinct=True,
                ),
            )
        )

    def _get_operation(self, operation_id, *, lock=False):
        queryset = ChangeOperation.objects.filter(workspace_id=self.workspace_id)
        if lock:
            queryset = queryset.select_for_update()
        operation = queryset.filter(id=operation_id).first()
        if operation is None:
            raise AppApiException(404, "变更操作不存在")
        return operation

    def _get_communication(self, communication_id, *, lock=False):
        queryset = ChangeOperationCommunication.objects.filter(workspace_id=self.workspace_id)
        if lock:
            queryset = queryset.select_for_update()
            row = queryset.filter(id=communication_id).first()
        else:
            row = queryset.select_related("operation", "user").filter(id=communication_id).first()
        if row is None:
            raise AppApiException(404, "提醒或告知记录不存在")
        return row

    def dashboard(self):
        operations = self._operation_queryset().order_by("-update_time")[:30]
        operation_rows = ChangeOperation.objects.filter(workspace_id=self.workspace_id)
        communications = ChangeOperationCommunication.objects.filter(workspace_id=self.workspace_id)
        reports = ChangeQualityReport.objects.filter(workspace_id=self.workspace_id).select_related("user")[:10]
        return {
            "summary": {
                "operation_count": operation_rows.count(),
                "not_started_count": operation_rows.filter(control_status=ChangeControlStatus.NOT_STARTED).count(),
                "in_progress_count": operation_rows.filter(control_status=ChangeControlStatus.IN_PROGRESS).count(),
                "completed_count": operation_rows.filter(control_status=ChangeControlStatus.COMPLETED).count(),
                "aborted_count": operation_rows.filter(control_status=ChangeControlStatus.ABORTED).count(),
                "pending_communication_count": communications.filter(status=ChangeCommunicationStatus.PENDING).count(),
                "failed_communication_count": communications.filter(status=ChangeCommunicationStatus.FAILED).count(),
                "report_count": ChangeQualityReport.objects.filter(workspace_id=self.workspace_id).count(),
            },
            "communication_counts": {
                value: communications.filter(status=value).count() for value in ChangeCommunicationStatus.values
            },
            "operations": [serialize_control_operation(row) for row in operations],
            "reports": [serialize_change_quality_report(row, include_snapshot=False) for row in reports],
        }

    def detail(self, operation_id):
        operation = (
            self._operation_queryset()
            .prefetch_related(
                "assessments__user",
                "confirmations__assessment",
                "confirmations__confirmer",
                "communications__user",
                "control_actions__user",
            )
            .filter(id=operation_id)
            .first()
        )
        if operation is None:
            raise AppApiException(404, "变更操作不存在")
        return serialize_control_operation(operation, include_history=True)

    @transaction.atomic
    def create_communication(self, operation_id, data):
        serializer = ChangeCommunicationCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        operation = self._get_operation(operation_id, lock=True)
        request_id = values.get("request_id", "").strip() or f"change-communication:{timezone.now().timestamp()}"
        existing = (
            ChangeOperationCommunication.objects.filter(workspace_id=self.workspace_id, request_id=request_id)
            .select_related("operation", "user")
            .first()
        )
        if existing:
            if existing.operation_id != operation.id:
                raise AppApiException(400, "通信事件幂等键已被其他变更操作使用")
            return {"created": False, "communication": serialize_change_communication(existing)}
        communication = ChangeOperationCommunication.objects.create(
            workspace_id=self.workspace_id,
            operation=operation,
            request_id=request_id,
            kind=values["kind"],
            phase=values["phase"],
            audience=values["audience"],
            channel=values["channel"],
            subject=values["subject"].strip(),
            content=values["content"].strip(),
            scheduled_at=values.get("scheduled_at"),
            user=self.user,
        )
        return {"created": True, "communication": serialize_change_communication(communication)}

    @transaction.atomic
    def update_communication_status(self, communication_id, data):
        serializer = ChangeCommunicationStatusSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        communication = self._get_communication(communication_id, lock=True)
        target = values["status"]
        if communication.status == target:
            return {"changed": False, "communication": serialize_change_communication(communication)}
        transitions = {
            ChangeCommunicationStatus.PENDING: {
                ChangeCommunicationStatus.SENT,
                ChangeCommunicationStatus.FAILED,
            },
            ChangeCommunicationStatus.SENT: {
                ChangeCommunicationStatus.ACKNOWLEDGED,
                ChangeCommunicationStatus.FAILED,
            },
            ChangeCommunicationStatus.FAILED: {ChangeCommunicationStatus.SENT},
            ChangeCommunicationStatus.ACKNOWLEDGED: set(),
        }
        if target not in transitions[communication.status]:
            raise AppApiException(400, "提醒或告知状态不能按当前顺序变更")
        now = timezone.now()
        communication.status = target
        if target == ChangeCommunicationStatus.SENT:
            communication.sent_at = now
            communication.failure_reason = ""
        elif target == ChangeCommunicationStatus.ACKNOWLEDGED:
            communication.acknowledged_at = now
        else:
            communication.failure_reason = values.get("failure_reason", "").strip()
        communication.save(update_fields=["status", "sent_at", "acknowledged_at", "failure_reason", "update_time"])
        notification_count = 0
        if target == ChangeCommunicationStatus.SENT:
            from marketing.serializers.notifications import MarketingNotificationService

            notification_count = MarketingNotificationService(
                self.workspace_id, self.user
            ).dispatch_change_communication(communication)
        return {
            "changed": True,
            "notification_count": notification_count,
            "communication": serialize_change_communication(communication),
        }

    @transaction.atomic
    def control(self, operation_id, data):
        serializer = ChangeControlActionSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        operation = self._get_operation(operation_id, lock=True)
        action = values["action"]
        previous_status = operation.control_status
        if action == ChangeControlAction.START:
            if operation.risk_revision == 0:
                raise AppApiException(400, "变更操作尚未完成风险评估")
            if (
                operation.status == ChangeOperationStatus.REJECTED
                or operation.confirmation_status == ChangeConfirmationStatus.PENDING
            ):
                raise AppApiException(400, "变更操作尚未获准执行")
            if operation.control_status != ChangeControlStatus.NOT_STARTED:
                raise AppApiException(400, "只有未开始的变更可以进入执行中")
            has_before_notice = ChangeOperationCommunication.objects.filter(
                operation=operation,
                phase=ChangeCommunicationPhase.BEFORE,
                status__in=(ChangeCommunicationStatus.SENT, ChangeCommunicationStatus.ACKNOWLEDGED),
            ).exists()
            if not has_before_notice:
                raise AppApiException(400, "开始执行前必须至少发送一条变更前提醒或告知")
            operation.control_status = ChangeControlStatus.IN_PROGRESS
            operation.actual_start_at = timezone.now()
            operation.completed_at = None
        elif action == ChangeControlAction.COMPLETE:
            if operation.control_status != ChangeControlStatus.IN_PROGRESS:
                raise AppApiException(400, "只有执行中的变更可以完成")
            has_during_notice = ChangeOperationCommunication.objects.filter(
                operation=operation,
                phase=ChangeCommunicationPhase.DURING,
                status__in=(ChangeCommunicationStatus.SENT, ChangeCommunicationStatus.ACKNOWLEDGED),
            ).exists()
            if not has_during_notice:
                raise AppApiException(400, "完成前必须至少发送一条执行中提醒或告知")
            operation.control_status = ChangeControlStatus.COMPLETED
            operation.completed_at = timezone.now()
        else:
            if operation.control_status not in (
                ChangeControlStatus.NOT_STARTED,
                ChangeControlStatus.IN_PROGRESS,
            ):
                raise AppApiException(400, "当前变更已经结束，不能再次终止")
            operation.control_status = ChangeControlStatus.ABORTED
            operation.completed_at = timezone.now()
        operation.save(update_fields=["control_status", "actual_start_at", "completed_at", "update_time"])
        revision = (
            ChangeControlActionRecord.objects.filter(operation=operation).aggregate(value=Max("revision"))["value"] or 0
        ) + 1
        record = ChangeControlActionRecord.objects.create(
            workspace_id=self.workspace_id,
            operation=operation,
            revision=revision,
            action=action,
            previous_status=previous_status,
            current_status=operation.control_status,
            note=values.get("note", "").strip(),
            user=self.user,
        )
        return {
            "operation": serialize_control_operation(self._operation_queryset().get(id=operation.id)),
            "action_record": serialize_change_control_action(record),
        }

    def _build_report_snapshot(self, period_start, period_end):
        operations = list(
            ChangeOperation.objects.filter(
                workspace_id=self.workspace_id,
                create_time__date__range=(period_start, period_end),
            ).order_by("create_time")
        )
        operation_ids = [item.id for item in operations]
        communications = list(
            ChangeOperationCommunication.objects.filter(operation_id__in=operation_ids).order_by("create_time")
        )
        communications_by_operation = defaultdict(list)
        for communication in communications:
            communications_by_operation[communication.operation_id].append(communication)
        evaluated = [item for item in operations if item.risk_revision > 0]
        confirmed = [item for item in operations if item.evaluated_at and item.decided_at]
        average_confirmation_seconds = (
            round(
                sum((item.decided_at - item.evaluated_at).total_seconds() for item in confirmed) / len(confirmed),
                2,
            )
            if confirmed
            else 0
        )
        communicated_operation_count = sum(
            bool(
                [
                    row
                    for row in communications_by_operation[item.id]
                    if row.status in (ChangeCommunicationStatus.SENT, ChangeCommunicationStatus.ACKNOWLEDGED)
                ]
            )
            for item in operations
        )
        controlled = [
            item
            for item in operations
            if item.control_status
            in (ChangeControlStatus.IN_PROGRESS, ChangeControlStatus.COMPLETED, ChangeControlStatus.ABORTED)
        ]
        metrics = {
            "operation_count": len(operations),
            "evaluated_count": len(evaluated),
            "green_count": sum(
                item.risk_level == ChangeRiskLevel.GREEN and item.risk_revision > 0 for item in operations
            ),
            "yellow_count": sum(item.risk_level == ChangeRiskLevel.YELLOW for item in operations),
            "red_count": sum(item.risk_level == ChangeRiskLevel.RED for item in operations),
            "approved_count": sum(item.status == ChangeOperationStatus.APPROVED for item in operations),
            "rejected_count": sum(item.status == ChangeOperationStatus.REJECTED for item in operations),
            "pending_confirmation_count": sum(
                item.confirmation_status == ChangeConfirmationStatus.PENDING for item in operations
            ),
            "in_progress_count": sum(item.control_status == ChangeControlStatus.IN_PROGRESS for item in operations),
            "completed_count": sum(item.control_status == ChangeControlStatus.COMPLETED for item in operations),
            "aborted_count": sum(item.control_status == ChangeControlStatus.ABORTED for item in operations),
            "communication_count": len(communications),
            "sent_communication_count": sum(
                row.status in (ChangeCommunicationStatus.SENT, ChangeCommunicationStatus.ACKNOWLEDGED)
                for row in communications
            ),
            "acknowledged_communication_count": sum(
                row.status == ChangeCommunicationStatus.ACKNOWLEDGED for row in communications
            ),
            "failed_communication_count": sum(row.status == ChangeCommunicationStatus.FAILED for row in communications),
            "communication_coverage_rate": round(
                communicated_operation_count / len(operations) * 100 if operations else 0,
                2,
            ),
            "control_completion_rate": round(
                sum(item.control_status == ChangeControlStatus.COMPLETED for item in controlled) / len(controlled) * 100
                if controlled
                else 0,
                2,
            ),
            "average_confirmation_seconds": average_confirmation_seconds,
        }
        operation_snapshot = []
        for item in operations:
            operation_snapshot.append(
                {
                    "id": str(item.id),
                    "date": timezone.localtime(item.create_time).date().isoformat(),
                    "code": item.code,
                    "name": item.name,
                    "risk_level": item.risk_level,
                    "risk_level_label": item.get_risk_level_display(),
                    "risk_score": item.risk_score,
                    "status": item.status,
                    "status_label": item.get_status_display(),
                    "control_status": item.control_status,
                    "control_status_label": item.get_control_status_display(),
                    "communication_count": len(communications_by_operation[item.id]),
                    "actual_start_at": item.actual_start_at.isoformat() if item.actual_start_at else None,
                    "completed_at": item.completed_at.isoformat() if item.completed_at else None,
                }
            )
        daily_trend = []
        current_date = period_start
        while current_date <= period_end:
            date_string = current_date.isoformat()
            date_operations = [item for item in operation_snapshot if item["date"] == date_string]
            date_communications = [
                item for item in communications if timezone.localtime(item.create_time).date() == current_date
            ]
            daily_trend.append(
                {
                    "date": date_string,
                    "operation_count": len(date_operations),
                    "red_count": sum(item["risk_level"] == ChangeRiskLevel.RED for item in date_operations),
                    "communication_count": len(date_communications),
                    "completed_count": sum(
                        item["control_status"] == ChangeControlStatus.COMPLETED for item in date_operations
                    ),
                }
            )
            current_date += timedelta(days=1)
        return metrics, daily_trend, operation_snapshot

    def generate_report(self, data):
        serializer = ChangeQualityReportGenerateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        metrics, daily_trend, operation_snapshot = self._build_report_snapshot(
            values["period_start"], values["period_end"]
        )
        title = values.get("title", "").strip() or (
            f"变更操作质量报告 {values['period_start'].isoformat()} 至 {values['period_end'].isoformat()}"
        )
        report = ChangeQualityReport.objects.create(
            workspace_id=self.workspace_id,
            title=title,
            period_start=values["period_start"],
            period_end=values["period_end"],
            metrics=metrics,
            daily_trend=daily_trend,
            operation_snapshot=operation_snapshot,
            generated_at=timezone.now(),
            user=self.user,
        )
        return serialize_change_quality_report(report)

    def get_report(self, report_id):
        report = (
            ChangeQualityReport.objects.filter(workspace_id=self.workspace_id, id=report_id)
            .select_related("user")
            .first()
        )
        if report is None:
            raise AppApiException(404, "变更操作质量报告不存在")
        return report

    def report_detail(self, report_id):
        return serialize_change_quality_report(self.get_report(report_id))

    def report_drilldown(self, report_id, date_value):
        report = self.get_report(report_id)
        try:
            target_date = serializers.DateField().to_internal_value(date_value)
        except serializers.ValidationError as exc:
            raise AppApiException(400, "下钻日期格式必须为 YYYY-MM-DD") from exc
        if target_date < report.period_start or target_date > report.period_end:
            raise AppApiException(400, "下钻日期不在报告统计周期内")
        date_string = target_date.isoformat()
        trend = next((item for item in report.daily_trend if item["date"] == date_string), None)
        return {
            "date": target_date,
            "summary": trend
            or {
                "date": date_string,
                "operation_count": 0,
                "red_count": 0,
                "communication_count": 0,
                "completed_count": 0,
            },
            "operations": [item for item in report.operation_snapshot if item["date"] == date_string],
        }
