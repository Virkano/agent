from django.utils import timezone
from django.db.models import Q
from rest_framework import serializers

from common.exception.app_exception import AppApiException
from common.result import Page
from common.utils.logger import telecom_ai_logger
from marketing.models import (
    MarketingAlert,
    MarketingAlertAction,
    MarketingAlertActionRecord,
    MarketingAlertRule,
    MarketingAlertSeverity,
    MarketingNotification,
    MarketingNotificationStatus,
    MarketingTask,
)
from marketing.serializers.alerts import MarketingAlertService
from marketing.serializers.quality_review import validate_or_raise
from users.models import User


class MarketingNotificationQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(required=False, allow_blank=True, choices=MarketingNotificationStatus.choices)
    severity = serializers.ChoiceField(required=False, allow_blank=True, choices=MarketingAlertSeverity.choices)
    action = serializers.ChoiceField(required=False, allow_blank=True, choices=MarketingAlertAction.choices)


def serialize_notification(row):
    return {
        "id": str(row.id),
        "alert_id": str(row.alert_id) if row.alert_id else None,
        "alert_type": row.alert.alert_type if row.alert else "",
        "source_type": row.source_type,
        "source_id": row.source_id,
        "action": row.action_record.action if row.action_record else row.source_type,
        "title": row.title,
        "content": row.content,
        "severity": row.severity,
        "status": row.status,
        "target_route": row.target_route,
        "read_at": row.read_at,
        "create_time": row.create_time,
    }


class MarketingNotificationService:
    NOTIFY_ACTIONS = (
        MarketingAlertAction.CREATED,
        MarketingAlertAction.REOPENED,
        MarketingAlertAction.RESPONSE_OVERDUE,
        MarketingAlertAction.RESOLUTION_OVERDUE,
        MarketingAlertAction.ASSIGNED,
        MarketingAlertAction.TRANSFERRED,
        MarketingAlertAction.COMMENTED,
        MarketingAlertAction.CLOSED,
        MarketingAlertAction.SUBSCRIBED,
        MarketingAlertAction.UNSUBSCRIBED,
        MarketingAlertAction.ATTACHED,
    )
    SLA_ACTIONS = (MarketingAlertAction.RESPONSE_OVERDUE, MarketingAlertAction.RESOLUTION_OVERDUE)

    def __init__(self, workspace_id, user=None):
        self.workspace_id = workspace_id
        self.user = user

    def _recipient_ids(self):
        recipient_ids = set()
        if self.user and self.user.is_active:
            recipient_ids.add(self.user.id)
        try:
            from xpack_lite.models import WorkspaceUserRoleMapping

            recipient_ids.update(
                WorkspaceUserRoleMapping.objects.filter(
                    workspace_id=self.workspace_id,
                    user__is_active=True,
                ).values_list("user_id", flat=True)
            )
        except (ImportError, RuntimeError):
            pass
        if not recipient_ids:
            recipient_ids.update(
                MarketingTask.objects.filter(
                    workspace_id=self.workspace_id,
                    user__isnull=False,
                    user__is_active=True,
                ).values_list("user_id", flat=True)
            )
        if self.workspace_id == "default" and not recipient_ids:
            recipient_ids.update(
                User.objects.filter(is_active=True, role__contains="ADMIN").values_list("id", flat=True)
            )
        return recipient_ids

    def dispatch(self):
        recipient_ids = self._recipient_ids()
        if not recipient_ids:
            return 0
        actions = (
            MarketingAlertActionRecord.objects.filter(
                workspace_id=self.workspace_id,
                action__in=self.NOTIFY_ACTIONS,
            )
            .select_related("alert", "alert__rule", "alert__rule__escalation_user")
            .prefetch_related("alert__subscribers")
            .order_by("create_time")
        )
        created_count = 0
        for action in actions:
            alert = action.alert
            action_recipient_ids = set(recipient_ids)
            if (
                action.action in self.SLA_ACTIONS
                and alert.rule
                and alert.rule.escalation_user
                and alert.rule.escalation_user.is_active
            ):
                action_recipient_ids = {alert.rule.escalation_user_id}
            elif action.action in (MarketingAlertAction.ASSIGNED, MarketingAlertAction.TRANSFERRED):
                action_recipient_ids = {action.snapshot.get("assignee_id")}
            elif action.action in (MarketingAlertAction.SUBSCRIBED, MarketingAlertAction.UNSUBSCRIBED):
                action_recipient_ids = {action.snapshot.get("subscriber_user_id")}
            elif action.action in (
                MarketingAlertAction.COMMENTED,
                MarketingAlertAction.CLOSED,
                MarketingAlertAction.ATTACHED,
            ):
                action_recipient_ids = {item.user_id for item in alert.subscribers.all()}
                if alert.assignee_id:
                    action_recipient_ids.add(alert.assignee_id)
                if action.operator_id:
                    action_recipient_ids.discard(action.operator_id)
            action_recipient_ids.discard(None)
            recipients = list(User.objects.filter(id__in=action_recipient_ids, is_active=True))
            prefix_map = {
                MarketingAlertAction.REOPENED: "告警重新打开",
                MarketingAlertAction.RESPONSE_OVERDUE: "首次响应超时",
                MarketingAlertAction.RESOLUTION_OVERDUE: "告警处理超时",
                MarketingAlertAction.ASSIGNED: "告警已指派给你",
                MarketingAlertAction.TRANSFERRED: "告警已转派给你",
                MarketingAlertAction.COMMENTED: "告警有新评论",
                MarketingAlertAction.CLOSED: "告警已关闭",
                MarketingAlertAction.SUBSCRIBED: "你已成为告警关注人",
                MarketingAlertAction.UNSUBSCRIBED: "你已被移出告警关注人",
                MarketingAlertAction.ATTACHED: "告警有新附件",
            }
            prefix = prefix_map.get(action.action, "新告警")
            for recipient in recipients:
                _, created = MarketingNotification.objects.get_or_create(
                    user=recipient,
                    action_record=action,
                    defaults={
                        "workspace_id": self.workspace_id,
                        "alert": alert,
                        "title": f"{prefix}：{alert.title}",
                        "content": action.note or alert.description,
                        "severity": alert.severity,
                        "target_route": f"/marketing-operations?alert_id={alert.id}",
                    },
                )
                created_count += int(created)
        return created_count

    def sync_and_notify(self, data=None):
        summary = MarketingAlertService(self.workspace_id, self.user).sync(data)
        return {**summary, "notification_count": self.dispatch()}

    def dispatch_report(self, report):
        recipient = self.user or report.user
        if recipient is None or not recipient.is_active:
            return 0
        succeeded = report.status == "SUCCESS"
        source_type = "REPORT_GENERATED" if succeeded else "REPORT_FAILED"
        _, created = MarketingNotification.objects.get_or_create(
            workspace_id=self.workspace_id,
            user=recipient,
            source_type=source_type,
            source_id=f"{report.id}:{report.retry_count}",
            defaults={
                "title": f"报告{'已生成' if succeeded else '生成失败'}：{report.title}",
                "content": (
                    "营销分析报告已进入报告库，可查看指标、归因和经营建议。" if succeeded else report.error_message
                ),
                "severity": "INFO" if succeeded else "WARNING",
                "target_route": f"/analysis-report?report_id={report.id}",
            },
        )
        return int(created)

    def dispatch_platform_alert(self, alert):
        """Route platform-wide monitoring alerts into the existing global bell."""
        recipients = User.objects.filter(id__in=self._recipient_ids(), is_active=True)
        created_count = 0
        for recipient in recipients:
            _, created = MarketingNotification.objects.get_or_create(
                workspace_id=self.workspace_id,
                user=recipient,
                source_type="PLATFORM_ALERT",
                source_id=str(alert.id),
                defaults={
                    "title": alert.title,
                    "content": alert.message,
                    "severity": "CRITICAL" if alert.severity == "CRITICAL" else "WARNING",
                    "target_route": f"/platform-monitoring?alert_id={alert.id}",
                },
            )
            created_count += int(created)
        return created_count

    def dispatch_metric_order(self, order):
        """Route generic metric incidents and their duty assignment into the global bell."""
        recipient_ids = {order.assignee_id} if order.assignee_id else self._recipient_ids()
        recipients = User.objects.filter(id__in=recipient_ids, is_active=True)
        created_count = 0
        incident = order.incident
        for recipient in recipients:
            _, created = MarketingNotification.objects.get_or_create(
                workspace_id=self.workspace_id,
                user=recipient,
                source_type="METRIC_DISPATCH_ORDER",
                source_id=str(order.id),
                defaults={
                    "title": order.title,
                    "content": incident.message,
                    "severity": "CRITICAL" if incident.severity == "CRITICAL" else "WARNING",
                    "target_route": f"/metric-operations?order_id={order.id}",
                },
            )
            created_count += int(created)
        return created_count

    def dispatch_metric_order_event(self, order, event):
        """Publish assignment and disposition changes through the same global bell."""
        recipient_ids = {order.assignee_id} if order.assignee_id else self._recipient_ids()
        if event.action == "COMMENTED" and event.operator_id:
            recipient_ids.discard(event.operator_id)
        recipients = User.objects.filter(id__in=recipient_ids, is_active=True)
        prefix = {
            "ASSIGNED": "指标派单已指派给你",
            "TRANSFERRED": "指标派单已转派给你",
            "COMMENTED": "指标派单有新备注",
            "CLOSED": "指标派单已关闭",
        }.get(event.action, "指标派单状态已更新")
        created_count = 0
        for recipient in recipients:
            _, created = MarketingNotification.objects.get_or_create(
                workspace_id=self.workspace_id,
                user=recipient,
                source_type="METRIC_DISPATCH_ORDER",
                source_id=f"{order.id}:{event.id}",
                defaults={
                    "title": f"{prefix}：{order.title}",
                    "content": event.note or event.get_action_display(),
                    "severity": "CRITICAL" if order.incident.severity == "CRITICAL" else "WARNING",
                    "target_route": f"/metric-operations?order_id={order.id}",
                },
            )
            created_count += int(created)
        return created_count

    def dispatch_change_communication(self, communication):
        """Send change reminders and cutover notices through the existing global bell."""
        recipients = User.objects.filter(id__in=self._recipient_ids(), is_active=True)
        source_type = "CHANGE_CONTROL_REMINDER" if communication.kind == "CONTROL_REMINDER" else "CHANGE_CUTOVER_NOTICE"
        risk_level = communication.operation.risk_level
        severity = "CRITICAL" if risk_level == "RED" else "WARNING" if risk_level == "YELLOW" else "INFO"
        created_count = 0
        for recipient in recipients:
            _, created = MarketingNotification.objects.get_or_create(
                workspace_id=self.workspace_id,
                user=recipient,
                source_type=source_type,
                source_id=str(communication.id),
                defaults={
                    "title": communication.subject,
                    "content": communication.content,
                    "severity": severity,
                    "target_route": f"/ivr-simulator?operation_id={communication.operation_id}",
                },
            )
            created_count += int(created)
        return created_count

    def _queryset(self):
        if not self.user:
            return MarketingNotification.objects.none()
        return MarketingNotification.objects.filter(
            workspace_id=self.workspace_id,
            user=self.user,
        ).select_related("alert", "action_record")

    def unread_count(self):
        return self._queryset().filter(status=MarketingNotificationStatus.UNREAD).count()

    def page(self, current_page, page_size, params):
        values = validate_or_raise(MarketingNotificationQuerySerializer(data=params))
        rows = self._queryset()
        if values.get("status"):
            rows = rows.filter(status=values["status"])
        if values.get("severity"):
            rows = rows.filter(severity=values["severity"])
        if values.get("action"):
            rows = rows.filter(Q(action_record__action=values["action"]) | Q(source_type=values["action"]))
        rows = rows.order_by("-create_time")
        total = rows.count()
        start = (current_page - 1) * page_size
        page = Page(
            total,
            [serialize_notification(row) for row in rows[start : start + page_size]],
            current_page,
            page_size,
        )
        page["unread_count"] = self.unread_count()
        return page

    def mark_read(self, notification_id):
        notification = self._queryset().filter(id=notification_id).first()
        if notification is None:
            raise AppApiException(404, "站内通知不存在")
        if notification.status != MarketingNotificationStatus.READ:
            notification.status = MarketingNotificationStatus.READ
            notification.read_at = timezone.now()
            notification.save(update_fields=["status", "read_at", "update_time"])
        return serialize_notification(notification)

    def mark_all_read(self):
        now = timezone.now()
        updated = (
            self._queryset()
            .filter(status=MarketingNotificationStatus.UNREAD)
            .update(
                status=MarketingNotificationStatus.READ,
                read_at=now,
                update_time=now,
            )
        )
        return {"updated_count": updated, "unread_count": 0}


def scan_all_marketing_alerts(days=7):
    workspace_ids = set(MarketingTask.objects.values_list("workspace_id", flat=True))
    workspace_ids.update(MarketingAlertRule.objects.values_list("workspace_id", flat=True))
    workspace_ids.update(MarketingAlert.objects.values_list("workspace_id", flat=True))
    scanned = []
    errors = []
    for workspace_id in sorted(workspace_ids):
        try:
            result = MarketingNotificationService(workspace_id).sync_and_notify({"days": days})
            scanned.append(
                {
                    "workspace_id": workspace_id,
                    "active_count": result["active_count"],
                    "notification_count": result["notification_count"],
                }
            )
        except Exception as exc:
            telecom_ai_logger.exception("Marketing alert scan failed for workspace %s", workspace_id)
            errors.append({"workspace_id": workspace_id, "error": type(exc).__name__})
    return {
        "workspace_count": len(workspace_ids),
        "scanned": scanned,
        "errors": errors,
    }
