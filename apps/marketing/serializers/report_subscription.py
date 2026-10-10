# coding=utf-8
from datetime import datetime, timedelta

from django.core.mail import EmailMultiAlternatives
from django.core.mail.backends.smtp import EmailBackend
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import serializers

from common.exception.app_exception import AppApiException
from common.utils.logger import telecom_ai_logger
from marketing.models import (
    MarketingAnalysisReport,
    MarketingAttributionMethod,
    MarketingReportDelivery,
    MarketingReportDeliveryChannel,
    MarketingReportDeliveryStatus,
    MarketingReportStatus,
    MarketingReportSubscription,
    MarketingReportSubscriptionFrequency,
    MarketingReportTemplate,
    MarketingTask,
)
from marketing.report_exports import build_html_export, safe_report_filename
from marketing.serializers.report import MarketingAnalysisReportService
from models_provider.base_model_provider import ModelTypeConst
from models_provider.models import Model, Status as ModelStatus
from system_manage.models import SettingType, SystemSetting


class MarketingReportSubscriptionWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=128)
    template_id = serializers.UUIDField()
    task_id = serializers.UUIDField(required=False, allow_null=True)
    model_id = serializers.UUIDField(required=False, allow_null=True)
    frequency = serializers.ChoiceField(choices=MarketingReportSubscriptionFrequency.choices)
    run_time = serializers.TimeField()
    weekday = serializers.IntegerField(required=False, default=0, min_value=0, max_value=6)
    month_day = serializers.IntegerField(required=False, default=1, min_value=1, max_value=28)
    period_days = serializers.IntegerField(required=False, default=7, min_value=1, max_value=365)
    attribution_method = serializers.ChoiceField(
        required=False,
        default=MarketingAttributionMethod.LAST_TOUCH,
        choices=MarketingAttributionMethod.choices,
    )
    use_llm = serializers.BooleanField(required=False, default=False)
    email_enabled = serializers.BooleanField(required=False, default=False)
    recipient_emails = serializers.ListField(
        child=serializers.EmailField(), required=False, default=list, allow_empty=True, max_length=20
    )
    enabled = serializers.BooleanField(required=False, default=True)

    def validate(self, attrs):
        if attrs.get("use_llm") and not attrs.get("model_id"):
            raise serializers.ValidationError({"model_id": "启用智能解读时必须选择模型"})
        if attrs.get("email_enabled") and not attrs.get("recipient_emails"):
            raise serializers.ValidationError({"recipient_emails": "启用邮件时至少填写一个接收地址"})
        return attrs


def calculate_next_run(subscription, now=None):
    now = timezone.localtime(now or timezone.now())
    candidate = timezone.make_aware(
        datetime.combine(now.date(), subscription.run_time),
        timezone.get_current_timezone(),
    )
    if subscription.frequency == MarketingReportSubscriptionFrequency.DAILY:
        if candidate <= now:
            candidate += timedelta(days=1)
    elif subscription.frequency == MarketingReportSubscriptionFrequency.WEEKLY:
        candidate += timedelta(days=(subscription.weekday - candidate.weekday()) % 7)
        if candidate <= now:
            candidate += timedelta(days=7)
    else:
        candidate = candidate.replace(day=subscription.month_day)
        if candidate <= now:
            year = candidate.year + int(candidate.month == 12)
            month = 1 if candidate.month == 12 else candidate.month + 1
            candidate = candidate.replace(year=year, month=month, day=subscription.month_day)
    return candidate


def serialize_subscription(row):
    return {
        "id": str(row.id),
        "name": row.name,
        "template_id": str(row.template_id),
        "template_name": row.template.name,
        "task_id": str(row.task_id) if row.task_id else None,
        "task_name": row.task.name if row.task else "全部营销任务",
        "model_id": str(row.model_id) if row.model_id else None,
        "model_name": row.model.name if row.model else "规则分析",
        "frequency": row.frequency,
        "run_time": row.run_time,
        "weekday": row.weekday,
        "month_day": row.month_day,
        "period_days": row.period_days,
        "attribution_method": row.attribution_method,
        "use_llm": row.use_llm,
        "email_enabled": row.email_enabled,
        "recipient_emails": row.recipient_emails or [],
        "enabled": row.enabled,
        "next_run_at": row.next_run_at,
        "last_run_at": row.last_run_at,
        "last_status": row.last_status,
        "last_error": row.last_error,
        "last_report_id": str(row.last_report_id) if row.last_report_id else None,
        "update_time": row.update_time,
    }


class MarketingReportSubscriptionService:
    def __init__(self, workspace_id, user=None):
        self.workspace_id = workspace_id
        self.user = user

    def _queryset(self):
        return (
            MarketingReportSubscription.objects.filter(workspace_id=self.workspace_id)
            .select_related("template", "task", "model", "last_report")
            .order_by("-enabled", "name")
        )

    def list(self):
        return [serialize_subscription(row) for row in self._queryset()]

    def _validate_related(self, values):
        template = MarketingReportTemplate.objects.filter(
            workspace_id=self.workspace_id, id=values["template_id"], active=True
        ).first()
        if template is None:
            raise AppApiException(400, "报告模板不存在或已停用")
        task = None
        if values.get("task_id"):
            task = MarketingTask.objects.filter(workspace_id=self.workspace_id, id=values["task_id"]).first()
            if task is None:
                raise AppApiException(400, "营销任务不存在")
        model = None
        if values.get("model_id"):
            model = Model.objects.filter(
                workspace_id=self.workspace_id,
                id=values["model_id"],
                model_type=ModelTypeConst.LLM.name,
                status=ModelStatus.SUCCESS,
            ).first()
            if model is None:
                raise AppApiException(400, "智能解读模型不存在或不可用")
        return template, task, model

    def save(self, data, subscription_id=None):
        serializer = MarketingReportSubscriptionWriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        template, task, model = self._validate_related(values)
        row = self._queryset().filter(id=subscription_id).first() if subscription_id else None
        if subscription_id and row is None:
            raise AppApiException(404, "报告订阅不存在")
        if row is None:
            row = MarketingReportSubscription(workspace_id=self.workspace_id, user=self.user)
        for field in (
            "name",
            "frequency",
            "run_time",
            "weekday",
            "month_day",
            "period_days",
            "attribution_method",
            "use_llm",
            "email_enabled",
            "recipient_emails",
            "enabled",
        ):
            setattr(row, field, values[field])
        row.template = template
        row.task = task
        row.model = model
        row.next_run_at = calculate_next_run(row) if row.enabled else None
        try:
            row.save()
        except IntegrityError as exc:
            raise AppApiException(400, "当前工作空间已存在同名订阅") from exc
        return serialize_subscription(row)

    def delete(self, subscription_id):
        row = self._queryset().filter(id=subscription_id).first()
        if row is None:
            raise AppApiException(404, "报告订阅不存在")
        row.delete()
        return True

    def run_now(self, subscription_id):
        row = self._queryset().filter(id=subscription_id).first()
        if row is None:
            raise AppApiException(404, "报告订阅不存在")
        report = execute_report_subscription(row)
        return {
            "subscription": serialize_subscription(self._queryset().get(id=row.id)),
            "report_id": str(report.id),
            "report_status": report.status,
        }


def _deliver_email(subscription, report, recipient):
    delivery = MarketingReportDelivery.objects.create(
        workspace_id=subscription.workspace_id,
        report=report,
        subscription=subscription,
        user=subscription.user,
        channel=MarketingReportDeliveryChannel.EMAIL,
        status=MarketingReportDeliveryStatus.FAILED,
        recipient=recipient,
    )
    setting = SystemSetting.objects.filter(type=SettingType.EMAIL.value).first()
    if setting is None:
        delivery.error_message = "邮件服务未配置"
        delivery.save(update_fields=["error_message", "update_time"])
        return False
    try:
        meta = setting.meta or {}
        connection = EmailBackend(
            meta.get("email_host"),
            meta.get("email_port"),
            meta.get("email_host_user"),
            meta.get("email_host_password"),
            meta.get("email_use_tls"),
            False,
            meta.get("email_use_ssl"),
        )
        html_bytes = build_html_export(report)
        filename = safe_report_filename(report, "html")
        message = EmailMultiAlternatives(
            subject=f"营销分析报告：{report.title}",
            body=report.narrative,
            from_email=meta.get("from_email"),
            to=[recipient],
            connection=connection,
        )
        message.attach_alternative(html_bytes.decode("utf-8"), "text/html")
        message.attach(filename, html_bytes, "text/html")
        message.send(fail_silently=False)
        delivery.status = MarketingReportDeliveryStatus.SUCCESS
        delivery.file_name = filename
        delivery.content_type = "text/html"
        delivery.error_message = ""
        delivery.sent_at = timezone.now()
        delivery.save()
        return True
    except Exception:
        telecom_ai_logger.exception("Marketing report email delivery failed")
        delivery.error_message = "邮件发送失败，请检查邮件服务配置"
        delivery.save(update_fields=["error_message", "update_time"])
        return False


def execute_report_subscription(subscription):
    today = timezone.localdate()
    payload = {
        "template_id": str(subscription.template_id),
        "task_id": str(subscription.task_id) if subscription.task_id else None,
        "model_id": str(subscription.model_id) if subscription.model_id else None,
        "period_start": (today - timedelta(days=subscription.period_days - 1)).isoformat(),
        "period_end": today.isoformat(),
        "attribution_method": subscription.attribution_method,
        "attributed_revenue": "0",
        "marketing_cost": "0",
        "variable_cost": "0",
        "use_llm": subscription.use_llm,
    }
    result = MarketingAnalysisReportService(subscription.workspace_id, subscription.user).generate(payload)
    report = MarketingAnalysisReport.objects.get(id=result["id"])
    now = timezone.now()
    error_message = "" if report.status == MarketingReportStatus.SUCCESS else report.error_message
    with transaction.atomic():
        MarketingReportSubscription.objects.filter(id=subscription.id).update(
            last_run_at=now,
            last_status=report.status,
            last_error=error_message,
            last_report=report,
        )
        subscription.last_run_at = now
        subscription.next_run_at = calculate_next_run(subscription, now)
        MarketingReportSubscription.objects.filter(id=subscription.id).update(next_run_at=subscription.next_run_at)
    if report.status == MarketingReportStatus.SUCCESS and subscription.email_enabled:
        for recipient in subscription.recipient_emails or []:
            _deliver_email(subscription, report, recipient)
    return report


def run_due_report_subscriptions(now=None):
    now = now or timezone.now()
    ids = list(
        MarketingReportSubscription.objects.filter(enabled=True, next_run_at__lte=now)
        .order_by("next_run_at")
        .values_list("id", flat=True)[:100]
    )
    success_count = 0
    error_count = 0
    for subscription_id in ids:
        try:
            with transaction.atomic():
                subscription = (
                    MarketingReportSubscription.objects.select_for_update()
                    .select_related("template", "task", "model", "user")
                    .get(id=subscription_id)
                )
                if not subscription.enabled or not subscription.next_run_at or subscription.next_run_at > now:
                    continue
                subscription.next_run_at = calculate_next_run(subscription, now)
                subscription.save(update_fields=["next_run_at", "update_time"])
            execute_report_subscription(subscription)
            success_count += 1
        except Exception:
            error_count += 1
            telecom_ai_logger.exception("Scheduled marketing report generation failed")
            MarketingReportSubscription.objects.filter(id=subscription_id).update(
                last_run_at=now,
                last_status=MarketingReportStatus.FAILED,
                last_error="定时报告生成失败，请检查报告和模型配置",
            )
    return {"processed_count": len(ids), "success_count": success_count, "error_count": error_count}
