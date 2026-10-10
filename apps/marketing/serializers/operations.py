from datetime import datetime, time, timedelta

from django.db.models import Avg, Count, Max, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import serializers

from application.models.application_chat import ChatRecord
from common.exception.app_exception import AppApiException
from marketing.models import (
    MarketingAnswerManualReviewStatus,
    MarketingAnswerPreflightRecord,
    MarketingAnswerQualityReview,
    MarketingAnswerQualityStatus,
    MarketingConversionOutcome,
    MarketingConversionRecord,
    MarketingCustomer,
    MarketingCustomerStatus,
    MarketingPreflightAction,
    MarketingTask,
    MarketingTaskStatus,
    MarketingTouchBatch,
    MarketingTouchBatchStatus,
)


class MarketingOperationsQuerySerializer(serializers.Serializer):
    days = serializers.ChoiceField(required=False, default=7, choices=(7, 30, 90))
    task_id = serializers.UUIDField(required=False, allow_null=True)


def _percent(numerator, denominator):
    return round(numerator / denominator * 100, 1) if denominator else 0.0


def _period_start(days):
    today = timezone.localdate()
    start_date = today - timedelta(days=days - 1)
    start = timezone.make_aware(datetime.combine(start_date, time.min), timezone.get_current_timezone())
    return today, start_date, start


def _daily_counts(queryset, date_field, value_name="count"):
    return {
        row["day"].isoformat(): row[value_name]
        for row in queryset.annotate(day=TruncDate(date_field)).values("day").annotate(**{value_name: Count("id")})
        if row["day"]
    }


class MarketingOperationsService:
    SLOW_RESPONSE_SECONDS = 10

    def __init__(self, workspace_id, user=None):
        self.workspace_id = workspace_id
        self.user = user

    def _validated_query(self, params):
        serializer = MarketingOperationsQuerySerializer(data=params)
        if not serializer.is_valid():
            field, errors = next(iter(serializer.errors.items()))
            message = errors[0] if isinstance(errors, list) and errors else errors
            raise AppApiException(400, f"{field}: {message}")
        values = serializer.validated_data
        task_id = values.get("task_id")
        if task_id and not MarketingTask.objects.filter(id=task_id, workspace_id=self.workspace_id).exists():
            raise AppApiException(404, "营销任务不存在")
        return int(values["days"]), str(task_id) if task_id else None

    def overview(self, params):
        days, selected_task_id = self._validated_query(params)
        today, start_date, start = _period_start(days)
        task_rows = MarketingTask.objects.filter(workspace_id=self.workspace_id)
        if selected_task_id:
            task_rows = task_rows.filter(id=selected_task_id)
        task_list = list(task_rows.order_by("-update_time"))
        task_ids = [str(row.id) for row in task_list]

        customers = MarketingCustomer.objects.filter(workspace_id=self.workspace_id, task_id__in=task_ids)
        batches = MarketingTouchBatch.objects.filter(workspace_id=self.workspace_id, task_id__in=task_ids)
        records = ChatRecord.objects.filter(
            chat__source__marketing_task_id__in=task_ids,
            create_time__gte=start,
        )
        reviews = MarketingAnswerQualityReview.objects.filter(
            workspace_id=self.workspace_id,
            task_id__in=task_ids,
            record__create_time__gte=start,
        )
        preflights = MarketingAnswerPreflightRecord.objects.filter(
            workspace_id=self.workspace_id,
            task_id__in=task_ids,
            create_time__gte=start,
        )
        conversions = MarketingConversionRecord.objects.filter(
            workspace_id=self.workspace_id,
            task_id__in=task_ids,
            create_time__gte=start,
        )

        record_count = records.count()
        record_totals = records.aggregate(
            avg_response_seconds=Avg("run_time"),
            message_tokens=Sum("message_tokens"),
            answer_tokens=Sum("answer_tokens"),
        )
        runtime_error_count = reviews.filter(risk_types__contains=["RUNTIME_ERROR"]).count()
        quality_total = reviews.count()
        quality_pass_count = reviews.filter(status=MarketingAnswerQualityStatus.PASS).count()
        quality_issue_count = quality_total - quality_pass_count
        pending_review_count = (
            reviews.exclude(status=MarketingAnswerQualityStatus.PASS)
            .filter(manual_status=MarketingAnswerManualReviewStatus.PENDING)
            .count()
        )
        intercepted_count = preflights.filter(action=MarketingPreflightAction.INTERCEPTED).count()
        bypassed_count = preflights.filter(action=MarketingPreflightAction.BYPASSED).count()
        slow_conversation_count = records.filter(run_time__gt=self.SLOW_RESPONSE_SECONDS).count()
        overdue_batch_count = (
            batches.filter(deadline__lt=timezone.now()).exclude(status=MarketingTouchBatchStatus.CLOSED).count()
        )
        customer_count = customers.count()
        converted_customer_count = customers.filter(status=MarketingCustomerStatus.CONVERTED).count()
        conversion_count = conversions.filter(outcome=MarketingConversionOutcome.CONVERTED).count()
        total_tokens = (record_totals["message_tokens"] or 0) + (record_totals["answer_tokens"] or 0)

        metrics = {
            "active_task_count": task_rows.filter(status=MarketingTaskStatus.RUNNING).count(),
            "task_count": len(task_list),
            "customer_count": customer_count,
            "conversation_count": record_count,
            "conversation_success_rate": _percent(max(record_count - runtime_error_count, 0), record_count),
            "avg_response_seconds": round(record_totals["avg_response_seconds"] or 0, 2),
            "slow_conversation_count": slow_conversation_count,
            "total_tokens": total_tokens,
            "quality_review_count": quality_total,
            "quality_pass_rate": _percent(quality_pass_count, quality_total),
            "quality_issue_count": quality_issue_count,
            "pending_review_count": pending_review_count,
            "preflight_count": preflights.count(),
            "intercepted_count": intercepted_count,
            "bypassed_count": bypassed_count,
            "runtime_error_count": runtime_error_count,
            "overdue_batch_count": overdue_batch_count,
            "converted_customer_count": converted_customer_count,
            "conversion_count": conversion_count,
            "conversion_rate": _percent(converted_customer_count, customer_count),
        }

        issues = self._issues(metrics)
        return {
            "range": {
                "days": days,
                "start_date": start_date.isoformat(),
                "end_date": today.isoformat(),
                "task_id": selected_task_id,
            },
            "health": self._health(issues),
            "metrics": metrics,
            "trend": self._trend(start_date, today, records, reviews, preflights, conversions),
            "issues": issues,
            "task_health": self._task_health(task_list, customers, records, reviews, conversions),
            "generated_at": timezone.now(),
        }

    def _issues(self, metrics):
        issues = []
        if metrics["runtime_error_count"]:
            issues.append(
                {
                    "type": "RUNTIME_ERROR",
                    "severity": "CRITICAL",
                    "title": "对话运行错误",
                    "description": f"当前周期发现 {metrics['runtime_error_count']} 条模型或对话运行错误。",
                    "count": metrics["runtime_error_count"],
                    "route": "/marketing-quality",
                }
            )
        if metrics["bypassed_count"]:
            issues.append(
                {
                    "type": "QUALITY_BYPASS",
                    "severity": "CRITICAL",
                    "title": "发送前检测发生旁路",
                    "description": f"有 {metrics['bypassed_count']} 条回答因检测超时或异常直接放行。",
                    "count": metrics["bypassed_count"],
                    "route": "/marketing-quality",
                }
            )
        if metrics["overdue_batch_count"]:
            issues.append(
                {
                    "type": "OVERDUE_BATCH",
                    "severity": "WARNING",
                    "title": "触达批次已逾期",
                    "description": f"有 {metrics['overdue_batch_count']} 个未关闭批次超过截止时间。",
                    "count": metrics["overdue_batch_count"],
                    "route": "/marketing-task",
                }
            )
        if metrics["pending_review_count"]:
            issues.append(
                {
                    "type": "PENDING_REVIEW",
                    "severity": "WARNING",
                    "title": "质检记录待复核",
                    "description": f"当前还有 {metrics['pending_review_count']} 条问题回答等待人工处理。",
                    "count": metrics["pending_review_count"],
                    "route": "/marketing-quality",
                }
            )
        if metrics["slow_conversation_count"]:
            issues.append(
                {
                    "type": "SLOW_RESPONSE",
                    "severity": "WARNING",
                    "title": "对话响应偏慢",
                    "description": (
                        f"有 {metrics['slow_conversation_count']} 条对话响应超过 {self.SLOW_RESPONSE_SECONDS} 秒。"
                    ),
                    "count": metrics["slow_conversation_count"],
                    "route": "/marketing-task",
                }
            )
        if not metrics["active_task_count"]:
            issues.append(
                {
                    "type": "NO_ACTIVE_TASK",
                    "severity": "INFO",
                    "title": "当前没有进行中的营销任务",
                    "description": "如需继续试点，请检查任务状态或新建营销任务。",
                    "count": 0,
                    "route": "/marketing-task",
                }
            )
        severity_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
        return sorted(issues, key=lambda item: (severity_order[item["severity"]], -item["count"]))

    @staticmethod
    def _health(issues):
        critical_count = sum(item["severity"] == "CRITICAL" for item in issues)
        warning_count = sum(item["severity"] == "WARNING" for item in issues)
        if critical_count:
            return {
                "status": "CRITICAL",
                "label": "存在高优先级异常",
                "summary": "请优先处理运行错误或检测旁路，避免问题回答影响客户。",
                "critical_count": critical_count,
                "warning_count": warning_count,
            }
        if warning_count:
            return {
                "status": "WARNING",
                "label": "有事项需要关注",
                "summary": "系统仍可运行，但存在待复核、逾期或慢响应事项。",
                "critical_count": 0,
                "warning_count": warning_count,
            }
        return {
            "status": "HEALTHY",
            "label": "运行正常",
            "summary": "当前周期未发现高优先级运行异常。",
            "critical_count": 0,
            "warning_count": 0,
        }

    @staticmethod
    def _trend(start_date, today, records, reviews, preflights, conversions):
        conversations = _daily_counts(records, "create_time")
        quality_issues = _daily_counts(
            reviews.exclude(status=MarketingAnswerQualityStatus.PASS),
            "record__create_time",
        )
        runtime_errors = _daily_counts(reviews.filter(risk_types__contains=["RUNTIME_ERROR"]), "record__create_time")
        intercepted = _daily_counts(preflights.filter(action=MarketingPreflightAction.INTERCEPTED), "create_time")
        bypassed = _daily_counts(preflights.filter(action=MarketingPreflightAction.BYPASSED), "create_time")
        converted = _daily_counts(
            conversions.filter(outcome=MarketingConversionOutcome.CONVERTED),
            "create_time",
        )
        rows = []
        current = start_date
        while current <= today:
            key = current.isoformat()
            rows.append(
                {
                    "date": key,
                    "conversation_count": conversations.get(key, 0),
                    "quality_issue_count": quality_issues.get(key, 0),
                    "runtime_error_count": runtime_errors.get(key, 0),
                    "intercepted_count": intercepted.get(key, 0),
                    "bypassed_count": bypassed.get(key, 0),
                    "conversion_count": converted.get(key, 0),
                }
            )
            current += timedelta(days=1)
        return rows

    @staticmethod
    def _task_health(task_list, customers, records, reviews, conversions):
        customer_stats = {
            str(row["task_id"]): row
            for row in customers.values("task_id").annotate(
                customer_count=Count("id"),
                converted_customer_count=Count("id", filter=Q(status=MarketingCustomerStatus.CONVERTED)),
            )
        }
        record_stats = {
            str(row["chat__source__marketing_task_id"]): row
            for row in records.values("chat__source__marketing_task_id").annotate(
                conversation_count=Count("id"),
                avg_response_seconds=Avg("run_time"),
                last_activity_at=Max("create_time"),
            )
        }
        review_stats = {
            str(row["task_id"]): row
            for row in reviews.values("task_id").annotate(
                quality_issue_count=Count("id", filter=~Q(status=MarketingAnswerQualityStatus.PASS)),
                pending_review_count=Count(
                    "id",
                    filter=(
                        ~Q(status=MarketingAnswerQualityStatus.PASS)
                        & Q(manual_status=MarketingAnswerManualReviewStatus.PENDING)
                    ),
                ),
                runtime_error_count=Count("id", filter=Q(risk_types__contains=["RUNTIME_ERROR"])),
            )
        }
        conversion_stats = {
            str(row["task_id"]): row
            for row in conversions.filter(outcome=MarketingConversionOutcome.CONVERTED)
            .values("task_id")
            .annotate(conversion_count=Count("id"))
        }
        rows = []
        for task in task_list:
            task_id = str(task.id)
            customer = customer_stats.get(task_id, {})
            record = record_stats.get(task_id, {})
            review = review_stats.get(task_id, {})
            conversion = conversion_stats.get(task_id, {})
            customer_count = customer.get("customer_count", 0)
            converted_customer_count = customer.get("converted_customer_count", 0)
            runtime_error_count = review.get("runtime_error_count", 0)
            pending_review_count = review.get("pending_review_count", 0)
            if runtime_error_count:
                health_status = "ERROR"
            elif pending_review_count or review.get("quality_issue_count", 0):
                health_status = "ATTENTION"
            else:
                health_status = "HEALTHY"
            rows.append(
                {
                    "task_id": task_id,
                    "task_name": task.name,
                    "task_status": task.status,
                    "health_status": health_status,
                    "customer_count": customer_count,
                    "conversation_count": record.get("conversation_count", 0),
                    "avg_response_seconds": round(record.get("avg_response_seconds") or 0, 2),
                    "quality_issue_count": review.get("quality_issue_count", 0),
                    "pending_review_count": pending_review_count,
                    "runtime_error_count": runtime_error_count,
                    "converted_customer_count": converted_customer_count,
                    "conversion_count": conversion.get("conversion_count", 0),
                    "conversion_rate": _percent(converted_customer_count, customer_count),
                    "last_activity_at": record.get("last_activity_at"),
                }
            )
        health_order = {"ERROR": 0, "ATTENTION": 1, "HEALTHY": 2}
        return sorted(rows, key=lambda item: (health_order[item["health_status"]], item["task_name"]))
