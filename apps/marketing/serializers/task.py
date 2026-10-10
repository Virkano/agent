# coding=utf-8
from collections import Counter
from datetime import timedelta
from django.db import IntegrityError
from django.db.models import Avg, Q, Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from application.models import Application, ApplicationAccessToken
from application.models.application_chat import Chat, ChatRecord
from common.exception.app_exception import AppApiException
from common.result import Page
from knowledge.models import Knowledge
from marketing.insight import summarize_customer_insights
from marketing.recommendation import validate_recommendation_policy
from marketing.models import (
    MarketingAnswerManualReviewStatus,
    MarketingAnswerQualityStatus,
    MarketingConversionOutcome,
    MarketingConversionRecord,
    MarketingCampaign,
    MarketingCampaignStatus,
    MarketingCustomer,
    MarketingCustomerStatus,
    MarketingScenario,
    MarketingTask,
    MarketingTaskStatus,
    MarketingTouchBatch,
    MarketingTouchBatchApprovalStatus,
    MarketingTouchBatchStatus,
    MarketingTouchExecution,
)
from marketing.quality import RISK_DEFINITIONS, ensure_quality_reviews, serialize_quality_review
from marketing.serializers.campaign import campaign_to_offer


def _approval_sla_hours(task):
    try:
        return min(max(int((task.config or {}).get("approval_sla_hours", 24)), 1), 168)
    except (TypeError, ValueError):
        return 24


class MarketingTaskWriteSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, max_length=128, label=_("Marketing task name"))
    scenario_id = serializers.UUIDField(required=True, label=_("Marketing scenario ID"))
    target_audience = serializers.CharField(
        required=False, allow_blank=True, max_length=256, label=_("Target audience")
    )
    objective = serializers.CharField(required=False, allow_blank=True, max_length=256, label=_("Task objective"))
    channel = serializers.CharField(required=False, allow_blank=True, max_length=64, label=_("Channel"))
    status = serializers.ChoiceField(required=False, choices=MarketingTaskStatus.choices, label=_("Status"))
    application_id = serializers.UUIDField(required=False, allow_null=True, label=_("Application ID"))
    knowledge_id = serializers.UUIDField(required=False, allow_null=True, label=_("Knowledge ID"))
    target_count = serializers.IntegerField(required=False, min_value=0, label=_("Target count"))
    config = serializers.DictField(required=False, label=_("Config"))
    campaign_ids = serializers.ListField(required=False, child=serializers.UUIDField(), max_length=50)
    description = serializers.CharField(required=False, allow_blank=True, label=_("Description"))


class MarketingTaskListQuerySerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)
    scenario_id = serializers.UUIDField(required=False, allow_null=True)


def _task_chat_count(task: MarketingTask):
    if not task.application_id:
        return 0
    return Chat.objects.filter(
        application_id=task.application_id,
        source__marketing_task_id=str(task.id),
    ).count()


def _task_chat_url(task: MarketingTask):
    if not task.application_id:
        return ""
    access_token = ApplicationAccessToken.objects.filter(application_id=task.application_id, is_active=True).first()
    if access_token is None:
        return ""
    return f"/admin/chat/{access_token.access_token}?marketing_task_id={task.id}"


def _customer_funnel(task: MarketingTask, chats=None):
    customer_list = list(MarketingCustomer.objects.filter(workspace_id=task.workspace_id, task_id=task.id))
    latest_conversions = {}
    for conversion in MarketingConversionRecord.objects.filter(workspace_id=task.workspace_id, task_id=task.id):
        latest_conversions.setdefault(str(conversion.customer_id), conversion)
    converted_count = sum(row.outcome == MarketingConversionOutcome.CONVERTED for row in latest_conversions.values())
    lost_count = sum(row.outcome == MarketingConversionOutcome.LOST for row in latest_conversions.values())
    consulted_customer_count = 0
    if chats is not None:
        customer_ids = {
            str(source_customer_id)
            for source_customer_id in chats.exclude(source__marketing_customer_id__isnull=True).values_list(
                "source__marketing_customer_id",
                flat=True,
            )
            if source_customer_id
        }
        consulted_customer_count = len(customer_ids)
    return {
        "customer_count": len(customer_list),
        "pending_count": sum(row.status == MarketingCustomerStatus.PENDING for row in customer_list),
        "touched_count": sum(row.status == MarketingCustomerStatus.TOUCHED for row in customer_list),
        "consulted_customer_count": consulted_customer_count,
        "intent_count": sum(row.status == MarketingCustomerStatus.INTENT for row in customer_list),
        "no_intent_count": sum(row.status == MarketingCustomerStatus.NO_INTENT for row in customer_list),
        "manual_count": sum(row.status == MarketingCustomerStatus.MANUAL for row in customer_list),
        "converted_count": converted_count,
        "lost_count": lost_count,
        "intent_rate": round(
            sum(row.status == MarketingCustomerStatus.INTENT for row in customer_list) / len(customer_list) * 100,
            1,
        )
        if customer_list
        else 0,
        "conversion_rate": round(converted_count / len(customer_list) * 100, 1) if customer_list else 0,
        **summarize_customer_insights(customer_list),
    }


def serialize_task(row: MarketingTask):
    campaign_snapshot = (row.config or {}).get("marketing_campaign_snapshot") or []
    return {
        "id": str(row.id),
        "workspace_id": row.workspace_id,
        "name": row.name,
        "scenario_id": str(row.scenario_id),
        "scenario_name": row.scenario.name if row.scenario else "",
        "target_audience": row.target_audience,
        "objective": row.objective,
        "channel": row.channel,
        "status": row.status,
        "application_id": str(row.application_id) if row.application_id else None,
        "application_name": row.application.name if row.application else "",
        "knowledge_id": str(row.knowledge_id) if row.knowledge_id else None,
        "knowledge_name": row.knowledge.name if row.knowledge else "",
        "target_count": row.target_count,
        "customer_count": row.customers.count(),
        "chat_count": _task_chat_count(row),
        "chat_url": _task_chat_url(row),
        "config": row.config or {},
        "campaign_ids": [
            item.get("campaign_id") for item in campaign_snapshot if isinstance(item, dict) and item.get("campaign_id")
        ],
        "campaign_names": [
            item.get("name") for item in campaign_snapshot if isinstance(item, dict) and item.get("name")
        ],
        "description": row.description,
        "create_user": row.user.nick_name if row.user else "",
        "create_time": row.create_time,
        "update_time": row.update_time,
    }


def serialize_task_record(row: ChatRecord, quality_review=None):
    answer_text = row.answer_text or ""
    quality = serialize_quality_review(quality_review)
    risk_types = set(quality["risk_types"] if quality else [])
    return {
        "id": str(row.id),
        "chat_id": str(row.chat_id),
        "problem_text": row.problem_text,
        "answer_text": answer_text[:800],
        "vote_status": row.vote_status,
        "run_time": row.run_time,
        "message_tokens": row.message_tokens,
        "answer_tokens": row.answer_tokens,
        "total_tokens": (row.message_tokens or 0) + (row.answer_tokens or 0),
        "source": row.source or {},
        "create_time": row.create_time,
        "risk_flags": {
            "suspicious_answer": "OFF_TOPIC" in risk_types,
            "has_runtime_error": "RUNTIME_ERROR" in risk_types,
        },
        "quality_review": quality,
    }


def _recommendation_effect_summary(chats, record_list, task: MarketingTask):
    summary = {}
    customer_offer_map = {}
    for chat in chats:
        source = chat.source if isinstance(chat.source, dict) else {}
        recommendation = (
            source.get("marketing_recommendation") if isinstance(source.get("marketing_recommendation"), dict) else {}
        )
        if recommendation.get("status") != "MATCHED":
            continue
        offer_id = str(recommendation.get("offer_id"))
        entry = summary.setdefault(
            offer_id,
            {
                "offer_id": offer_id,
                "offer_name": recommendation.get("offer_name") or offer_id,
                "priority": recommendation.get("priority", 100),
                "chat_count": 0,
                "record_count": 0,
                "intent_count": 0,
                "manual_count": 0,
                "converted_count": 0,
            },
        )
        entry["priority"] = min(entry["priority"], recommendation.get("priority", 100))
        entry["chat_count"] += 1
        if source.get("marketing_customer_id"):
            customer_offer_map[str(source["marketing_customer_id"])] = offer_id
    for record in record_list:
        offer_id = str((record.source or {}).get("marketing_recommendation", {}).get("offer_id") or "")
        if offer_id in summary:
            summary[offer_id]["record_count"] += 1
    customers = MarketingCustomer.objects.filter(workspace_id=task.workspace_id, task_id=task.id)
    for customer in customers:
        offer_id = customer_offer_map.get(str(customer.id))
        if offer_id not in summary:
            continue
        summary[offer_id]["intent_count"] += customer.status == MarketingCustomerStatus.INTENT
        summary[offer_id]["manual_count"] += customer.status == MarketingCustomerStatus.MANUAL
        summary[offer_id]["converted_count"] += customer.status == MarketingCustomerStatus.CONVERTED
    return sorted(summary.values(), key=lambda item: (item["priority"], item["offer_name"]))


class MarketingTaskService:
    def __init__(self, workspace_id: str, user=None):
        self.workspace_id = workspace_id
        self.user = user

    def _queryset(self):
        return (
            MarketingTask.objects.filter(workspace_id=self.workspace_id)
            .select_related("scenario", "application", "knowledge", "user")
            .order_by("-update_time")
        )

    def list(self, params: dict):
        serializer = MarketingTaskListQuerySerializer(data=params)
        serializer.is_valid(raise_exception=True)
        query_set = self._queryset()
        name = serializer.validated_data.get("name")
        status = serializer.validated_data.get("status")
        scenario_id = serializer.validated_data.get("scenario_id")
        if name:
            query_set = query_set.filter(
                Q(name__icontains=name)
                | Q(target_audience__icontains=name)
                | Q(objective__icontains=name)
                | Q(description__icontains=name)
            )
        if status:
            query_set = query_set.filter(status=status)
        if scenario_id:
            query_set = query_set.filter(scenario_id=scenario_id)
        return [serialize_task(row) for row in query_set]

    def page(self, current_page: int, page_size: int, params: dict):
        records = self.list(params)
        start = (current_page - 1) * page_size
        return Page(len(records), records[start : start + page_size], current_page, page_size)

    def get(self, task_id: str):
        task = self._queryset().filter(id=task_id).first()
        if task is None:
            raise AppApiException(404, _("Marketing task does not exist"))
        return serialize_task(task)

    def _validate_related(self, values: dict):
        scenario = MarketingScenario.objects.filter(
            id=values.get("scenario_id"),
            workspace_id=self.workspace_id,
        ).first()
        if scenario is None:
            raise AppApiException(400, _("Marketing scenario does not exist in current workspace"))

        application_id = values.get("application_id") or scenario.application_id
        knowledge_id = values.get("knowledge_id") or scenario.knowledge_id
        application = None
        knowledge = None
        if application_id:
            application = Application.objects.filter(id=application_id, workspace_id=self.workspace_id).first()
            if application is None:
                raise AppApiException(400, _("Application does not exist in current workspace"))
        if knowledge_id:
            knowledge = Knowledge.objects.filter(id=knowledge_id, workspace_id=self.workspace_id).first()
            if knowledge is None:
                raise AppApiException(400, _("Knowledge does not exist in current workspace"))
        return scenario, application, knowledge

    def _config_with_campaign_snapshot(self, config, campaign_ids, has_campaign_ids):
        config = dict(config or {})
        if not has_campaign_ids:
            return config
        rows = list(
            MarketingCampaign.objects.filter(
                id__in=campaign_ids,
                workspace_id=self.workspace_id,
                status=MarketingCampaignStatus.ACTIVE,
            )
        )
        if len(rows) != len(set(campaign_ids)):
            raise AppApiException(400, "所选活动不存在、未上线或不属于当前工作空间")
        snapshot = [campaign_to_offer(row) for row in rows]
        validate_recommendation_policy({"enabled": bool(snapshot), "offers": snapshot})
        config["marketing_campaign_snapshot"] = snapshot
        config["marketing_campaign_source"] = "ACTIVITY_LIBRARY"
        return config

    def create(self, data: dict):
        serializer = MarketingTaskWriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = dict(serializer.validated_data)
        scenario, application, knowledge = self._validate_related(values)
        config = self._config_with_campaign_snapshot(
            values.get("config"), values.get("campaign_ids", []), "campaign_ids" in values
        )
        try:
            task = MarketingTask.objects.create(
                workspace_id=self.workspace_id,
                user=self.user,
                scenario=scenario,
                application=application,
                knowledge=knowledge,
                name=values["name"],
                target_audience=values.get("target_audience") or scenario.target_audience,
                objective=values.get("objective") or scenario.objective,
                channel=values.get("channel") or scenario.channel or "ONLINE",
                status=values.get("status", MarketingTaskStatus.DRAFT),
                target_count=values.get("target_count", 0),
                config=config,
                description=values.get("description", ""),
            )
        except IntegrityError:
            raise AppApiException(400, _("Marketing task name already exists"))
        return serialize_task(task)

    def update(self, task_id: str, data: dict):
        task = MarketingTask.objects.filter(id=task_id, workspace_id=self.workspace_id).first()
        if task is None:
            raise AppApiException(404, _("Marketing task does not exist"))
        serializer = MarketingTaskWriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = dict(serializer.validated_data)
        scenario, application, knowledge = self._validate_related(values)
        config = self._config_with_campaign_snapshot(
            values.get("config", task.config),
            values.get("campaign_ids", []),
            "campaign_ids" in values,
        )
        for field in [
            "name",
            "target_audience",
            "objective",
            "channel",
            "status",
            "target_count",
            "description",
        ]:
            if field in values:
                setattr(task, field, values[field])
        task.config = config
        task.scenario = scenario
        task.application = application
        task.knowledge = knowledge
        try:
            task.save()
        except IntegrityError:
            raise AppApiException(400, _("Marketing task name already exists"))
        return serialize_task(task)

    def delete(self, task_id: str):
        deleted, _ = MarketingTask.objects.filter(id=task_id, workspace_id=self.workspace_id).delete()
        if deleted == 0:
            raise AppApiException(404, _("Marketing task does not exist"))
        return True

    def effect(self, task_id: str, current_page: int = 1, page_size: int = 10):
        task = self._queryset().filter(id=task_id).first()
        if task is None:
            raise AppApiException(404, _("Marketing task does not exist"))
        if not task.application_id:
            return {
                "task": serialize_task(task),
                "metrics": {
                    "chat_count": 0,
                    "record_count": 0,
                    "star_count": 0,
                    "trample_count": 0,
                    "mark_count": 0,
                    "avg_run_time": 0,
                    "message_tokens": 0,
                    "answer_tokens": 0,
                    "total_tokens": 0,
                    "suspicious_answer_count": 0,
                    "runtime_error_count": 0,
                    "quality_pass_count": 0,
                    "quality_pending_count": 0,
                    "quality_high_risk_count": 0,
                    "quality_pass_rate": 0,
                    "quality_issue_summary": [],
                    "quality_manual_pending_count": 0,
                    "quality_manual_reviewed_count": 0,
                    "quality_manual_revised_count": 0,
                    **_customer_funnel(task),
                },
                "records": Page(0, [], current_page, page_size),
            }

        task_id_text = str(task.id)
        chats = Chat.objects.filter(
            application_id=task.application_id,
            source__marketing_task_id=task_id_text,
        )
        records = (
            ChatRecord.objects.filter(chat_id__in=chats.values("id")).select_related("chat").order_by("-create_time")
        )
        aggregates = records.aggregate(
            avg_run_time=Avg("run_time"),
            message_tokens=Sum("message_tokens"),
            answer_tokens=Sum("answer_tokens"),
        )
        record_list = list(records)
        chat_list = list(chats)
        quality_reviews = ensure_quality_reviews(record_list)
        quality_status_counts = Counter(review.status for review in quality_reviews.values())
        quality_risk_counts = Counter(
            risk_type for review in quality_reviews.values() for risk_type in (review.risk_types or [])
        )
        reviewed_count = len(quality_reviews)
        quality_pass_count = quality_status_counts[MarketingAnswerQualityStatus.PASS]
        problem_quality_reviews = [
            review for review in quality_reviews.values() if review.status != MarketingAnswerQualityStatus.PASS
        ]
        quality_issue_summary = [
            {
                "risk_type": risk_type,
                "reason": RISK_DEFINITIONS[risk_type][2],
                "count": count,
            }
            for risk_type, count in quality_risk_counts.most_common()
            if risk_type in RISK_DEFINITIONS
        ]
        start = (current_page - 1) * page_size
        page_records = record_list[start : start + page_size]
        message_tokens = aggregates.get("message_tokens") or 0
        answer_tokens = aggregates.get("answer_tokens") or 0
        return {
            "task": serialize_task(task),
            "metrics": {
                "chat_count": chats.count(),
                "record_count": len(record_list),
                "star_count": sum(1 for row in record_list if row.vote_status == "0"),
                "trample_count": sum(1 for row in record_list if row.vote_status == "1"),
                "mark_count": sum(len(row.improve_paragraph_id_list or []) for row in record_list),
                "avg_run_time": round(float(aggregates.get("avg_run_time") or 0), 2),
                "message_tokens": message_tokens,
                "answer_tokens": answer_tokens,
                "total_tokens": message_tokens + answer_tokens,
                "suspicious_answer_count": quality_risk_counts["OFF_TOPIC"],
                "runtime_error_count": quality_risk_counts["RUNTIME_ERROR"],
                "quality_pass_count": quality_pass_count,
                "quality_pending_count": quality_status_counts[MarketingAnswerQualityStatus.REVIEW],
                "quality_high_risk_count": quality_status_counts[MarketingAnswerQualityStatus.HIGH_RISK],
                "quality_pass_rate": round(quality_pass_count / reviewed_count * 100, 1) if reviewed_count else 0,
                "quality_issue_summary": quality_issue_summary,
                "quality_manual_pending_count": sum(
                    review.manual_status == MarketingAnswerManualReviewStatus.PENDING
                    for review in problem_quality_reviews
                ),
                "quality_manual_reviewed_count": sum(
                    review.manual_status != MarketingAnswerManualReviewStatus.PENDING
                    for review in problem_quality_reviews
                ),
                "quality_manual_revised_count": sum(
                    review.manual_status == MarketingAnswerManualReviewStatus.REVISED
                    for review in problem_quality_reviews
                ),
                "recommendation_summary": _recommendation_effect_summary(chat_list, record_list, task),
                **_customer_funnel(task, chats),
            },
            "records": Page(
                len(record_list),
                [serialize_task_record(row, quality_reviews.get(str(row.id))) for row in page_records],
                current_page,
                page_size,
            ),
        }

    def dashboard(self, task_id: str):
        task = self._queryset().filter(id=task_id).first()
        if task is None:
            raise AppApiException(404, _("Marketing task does not exist"))
        customers = list(MarketingCustomer.objects.filter(workspace_id=self.workspace_id, task_id=task.id))
        batches = list(MarketingTouchBatch.objects.filter(workspace_id=self.workspace_id, task_id=task.id))
        now = timezone.now()
        approval_sla_hours = _approval_sla_hours(task)
        approval_overdue = [
            row
            for row in batches
            if row.approval_status == MarketingTouchBatchApprovalStatus.PENDING
            and (row.approval_due_at or row.create_time + timedelta(hours=approval_sla_hours)) < now
        ]
        approval_durations = [
            (row.approved_at - row.create_time).total_seconds() / 3600
            for row in batches
            if row.approval_status == MarketingTouchBatchApprovalStatus.APPROVED and row.approved_at
        ]
        executions = list(MarketingTouchExecution.objects.filter(batch_id__in=[row.id for row in batches]))
        latest_execution_ids = set()
        latest_executions = []
        for execution in executions:
            if execution.customer_id not in latest_execution_ids:
                latest_execution_ids.add(execution.customer_id)
                latest_executions.append(execution)
        conversions = list(MarketingConversionRecord.objects.filter(workspace_id=self.workspace_id, task_id=task.id))
        latest_conversions = {}
        for conversion in conversions:
            latest_conversions.setdefault(str(conversion.customer_id), conversion)
        converted_count = sum(
            row.outcome == MarketingConversionOutcome.CONVERTED for row in latest_conversions.values()
        )
        lost_count = sum(row.outcome == MarketingConversionOutcome.LOST for row in latest_conversions.values())
        now = timezone.now()
        priority_map = {
            MarketingCustomerStatus.MANUAL: 0,
            MarketingCustomerStatus.INTENT: 1,
            MarketingCustomerStatus.CONSULTED: 2,
            MarketingCustomerStatus.PENDING: 3,
            MarketingCustomerStatus.TOUCHED: 4,
        }
        priority_customers = sorted(
            (
                row
                for row in customers
                if row.status not in {MarketingCustomerStatus.NO_INTENT, MarketingCustomerStatus.CONVERTED}
            ),
            key=lambda row: (priority_map.get(row.status, 99), -row.update_time.timestamp()),
        )[:10]
        return {
            "task": serialize_task(task),
            "funnel": _customer_funnel(task),
            "batch_summary": {
                "total": len(batches),
                "ready": sum(row.status == MarketingTouchBatchStatus.READY for row in batches),
                "running": sum(row.status == MarketingTouchBatchStatus.RUNNING for row in batches),
                "closed": sum(row.status == MarketingTouchBatchStatus.CLOSED for row in batches),
                "pending_approval": sum(
                    row.approval_status == MarketingTouchBatchApprovalStatus.PENDING for row in batches
                ),
                "rejected_approval": sum(
                    row.approval_status == MarketingTouchBatchApprovalStatus.REJECTED for row in batches
                ),
                "approval_overdue": len(approval_overdue),
                "avg_approval_hours": round(sum(approval_durations) / len(approval_durations), 1)
                if approval_durations
                else 0,
                "overdue": sum(
                    row.deadline is not None and row.deadline < now and row.status != MarketingTouchBatchStatus.CLOSED
                    for row in batches
                ),
                "execution_customer_count": len(latest_executions),
                "converted_count": converted_count,
                "lost_count": lost_count,
                "conversion_rate": round(converted_count / len(customers) * 100, 1) if customers else 0,
            },
            "batches": [
                {
                    **{
                        "id": str(row.id),
                        "name": row.name,
                        "status": row.status,
                        "approval_status": row.approval_status,
                        "owner_name": row.owner_name,
                        "deadline": row.deadline,
                    },
                    "selected_count": row.selected_count,
                    "executed_count": sum(item.batch_id == row.id for item in latest_executions),
                    "converted_count": sum(
                        item.outcome == MarketingConversionOutcome.CONVERTED and item.batch_id == row.id
                        for item in latest_conversions.values()
                    ),
                    "lost_count": sum(
                        item.outcome == MarketingConversionOutcome.LOST and item.batch_id == row.id
                        for item in latest_conversions.values()
                    ),
                    "is_overdue": bool(
                        row.deadline and row.deadline < now and row.status != MarketingTouchBatchStatus.CLOSED
                    ),
                }
                for row in batches
            ],
            "priority_customers": [
                {
                    "name": row.name,
                    "phone_masked": f"{row.phone[:3]}****{row.phone[-4:]}" if len(row.phone or "") >= 7 else row.phone,
                    "status": row.status,
                    "intent": row.intent,
                    "current_plan": row.current_plan,
                }
                for row in priority_customers
            ],
        }
