# coding=utf-8
import re
from datetime import timedelta

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import serializers

from common.exception.app_exception import AppApiException
from marketing.serializers.customer import serialize_conversion_record
from marketing.models import (
    MarketingConversionOutcome,
    MarketingConversionRecord,
    MarketingCustomer,
    MarketingCustomerStatus,
    MarketingTask,
    MarketingTouchBatch,
    MarketingTouchBatchApprovalAction,
    MarketingTouchBatchApprovalRecord,
    MarketingTouchBatchApprovalStatus,
    MarketingTouchBatchStatus,
    MarketingTouchExecution,
    MarketingTouchExecutionResult,
)
from xpack_lite.services import is_workspace_manager


DEFAULT_APPROVAL_SLA_HOURS = 24


def _approval_sla_hours(task):
    value = (task.config or {}).get("approval_sla_hours", DEFAULT_APPROVAL_SLA_HOURS)
    try:
        return min(max(int(value), 1), 168)
    except (TypeError, ValueError):
        return DEFAULT_APPROVAL_SLA_HOURS


def _approval_due_at(task, now):
    return now + timedelta(hours=_approval_sla_hours(task))


class MarketingTouchBatchCreateSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, allow_blank=False, max_length=128)
    plan_keyword = serializers.CharField(required=False, allow_blank=True, max_length=128)
    province = serializers.CharField(required=False, allow_blank=True, max_length=64)
    min_data_usage_gb = serializers.FloatField(required=False, min_value=0, default=0)
    min_call_usage_minutes = serializers.FloatField(required=False, min_value=0, default=0)
    statuses = serializers.ListField(
        child=serializers.ChoiceField(choices=MarketingCustomerStatus.choices),
        required=False,
        default=[MarketingCustomerStatus.PENDING],
    )
    cooldown_days = serializers.IntegerField(required=False, min_value=0, max_value=365, default=7)
    max_customers = serializers.IntegerField(required=False, min_value=1, max_value=10000)


class MarketingTouchBatchUpdateSerializer(serializers.Serializer):
    owner_name = serializers.CharField(required=False, allow_blank=True, max_length=64)
    deadline = serializers.DateTimeField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=MarketingTouchBatchStatus.choices, required=False)


class MarketingTouchExecutionCreateSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField(required=True)
    result = serializers.ChoiceField(choices=MarketingTouchExecutionResult.choices, required=True)
    note = serializers.CharField(required=True, allow_blank=False, max_length=2000)
    next_follow_up_at = serializers.DateTimeField(required=False, allow_null=True)


class MarketingTouchBatchApprovalSerializer(serializers.Serializer):
    approval_status = serializers.ChoiceField(
        choices=[MarketingTouchBatchApprovalStatus.APPROVED, MarketingTouchBatchApprovalStatus.REJECTED]
    )
    approval_note = serializers.CharField(required=False, allow_blank=True, max_length=2000)

    def validate(self, attrs):
        if (
            attrs["approval_status"] == MarketingTouchBatchApprovalStatus.REJECTED
            and not attrs.get("approval_note", "").strip()
        ):
            raise serializers.ValidationError({"approval_note": "Rejection reason is required"})
        return attrs


class MarketingTouchBatchResubmitSerializer(MarketingTouchBatchCreateSerializer):
    resubmit_note = serializers.CharField(required=True, allow_blank=False, max_length=2000)


def _usage_number(value) -> float:
    matched = re.search(r"\d+(?:\.\d+)?", str(value or ""))
    return float(matched.group()) if matched else 0


def serialize_touch_batch(row: MarketingTouchBatch, *, can_approve=False, can_resubmit=False):
    approval_due_at = row.approval_due_at or row.create_time + timedelta(hours=_approval_sla_hours(row.task))
    return {
        "id": str(row.id),
        "task_id": str(row.task_id),
        "name": row.name,
        "status": row.status,
        "owner_name": row.owner_name,
        "deadline": row.deadline,
        "approval_status": row.approval_status,
        "approval_note": row.approval_note,
        "approver_name": row.approver_name,
        "approved_at": row.approved_at,
        "approval_due_at": approval_due_at,
        "is_approval_overdue": bool(
            row.approval_status == MarketingTouchBatchApprovalStatus.PENDING and approval_due_at < timezone.now()
        ),
        "creator_name": row.user.nick_name or row.user.username if row.user else "",
        "can_approve": can_approve,
        "can_resubmit": can_resubmit,
        "filter_config": row.filter_config or {},
        "selected_count": row.selected_count,
        "excluded_count": row.excluded_count,
        "customer_snapshot": row.customer_snapshot or [],
        "excluded_snapshot": row.excluded_snapshot or [],
        "create_time": row.create_time,
        "update_time": row.update_time,
    }


def serialize_touch_batch_approval_record(row: MarketingTouchBatchApprovalRecord):
    return {
        "id": str(row.id),
        "action": row.action,
        "note": row.note,
        "operator_name": row.user.nick_name or row.user.username if row.user else "",
        "create_time": row.create_time,
    }


def serialize_touch_execution(row: MarketingTouchExecution):
    customer = row.customer
    return {
        "id": str(row.id),
        "batch_id": str(row.batch_id),
        "customer_id": str(row.customer_id),
        "customer_name": customer.name,
        "phone_masked": f"{customer.phone[:3]}****{customer.phone[-4:]}"
        if len(customer.phone or "") >= 7
        else customer.phone,
        "result": row.result,
        "note": row.note,
        "next_follow_up_at": row.next_follow_up_at,
        "operator_name": row.user.nick_name or row.user.username if row.user else "",
        "create_time": row.create_time,
    }


class MarketingTouchBatchService:
    def __init__(self, workspace_id: str, user=None):
        self.workspace_id = workspace_id
        self.user = user

    def _get_task(self, task_id: str):
        task = MarketingTask.objects.filter(id=task_id, workspace_id=self.workspace_id).first()
        if task is None:
            raise AppApiException(404, "Marketing task does not exist")
        return task

    def list(self, task_id: str):
        self._get_task(task_id)
        rows = MarketingTouchBatch.objects.filter(task_id=task_id, workspace_id=self.workspace_id)
        return [self._serialize_batch(row) for row in rows]

    def approval_queue(self):
        rows = (
            MarketingTouchBatch.objects.filter(
                workspace_id=self.workspace_id,
                approval_status=MarketingTouchBatchApprovalStatus.PENDING,
            )
            .select_related("task", "user")
            .order_by("approval_due_at", "create_time")
        )
        records = [
            {
                **self._serialize_batch(row),
                "task_name": row.task.name,
                "approval_sla_hours": _approval_sla_hours(row.task),
            }
            for row in rows
        ]
        return {
            "summary": {
                "pending_count": len(records),
                "overdue_count": sum(row["is_approval_overdue"] for row in records),
            },
            "records": records,
            "generated_at": timezone.now(),
        }

    def get(self, task_id: str, batch_id: str):
        batch = self._get_batch(task_id, batch_id)
        executions = MarketingTouchExecution.objects.filter(batch_id=batch.id).select_related("customer", "user")
        conversions = MarketingConversionRecord.objects.filter(batch_id=batch.id).select_related(
            "batch", "customer", "user"
        )
        return {
            "batch": serialize_touch_batch(batch),
            "metrics": self._metrics(batch, executions, conversions),
            "executions": [serialize_touch_execution(row) for row in executions],
            "conversions": [serialize_conversion_record(row) for row in conversions],
            "approval_records": [
                serialize_touch_batch_approval_record(row)
                for row in batch.approval_records.select_related("user").all()
            ],
        }

    def update(self, task_id: str, batch_id: str, data: dict):
        batch = self._get_batch(task_id, batch_id)
        serializer = MarketingTouchBatchUpdateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        if (
            serializer.validated_data.get("status") == MarketingTouchBatchStatus.RUNNING
            and batch.approval_status != MarketingTouchBatchApprovalStatus.APPROVED
        ):
            raise AppApiException(400, "Touch batch requires approval before execution")
        for field, value in serializer.validated_data.items():
            setattr(batch, field, value)
        if serializer.validated_data:
            batch.save(update_fields=[*serializer.validated_data.keys(), "update_time"])
        return serialize_touch_batch(batch)

    def approve(self, task_id: str, batch_id: str, data: dict):
        batch = self._get_batch(task_id, batch_id)
        self._require_approver(batch)
        if batch.approval_status != MarketingTouchBatchApprovalStatus.PENDING:
            raise AppApiException(400, "Only pending touch batch can be approved")
        serializer = MarketingTouchBatchApprovalSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        batch.approval_status = serializer.validated_data["approval_status"]
        batch.approval_note = serializer.validated_data.get("approval_note", "")
        batch.approver_name = (self.user.nick_name or self.user.username) if self.user else ""
        batch.approved_at = timezone.now()
        batch.save(update_fields=["approval_status", "approval_note", "approver_name", "approved_at", "update_time"])
        self._record_approval(
            batch,
            MarketingTouchBatchApprovalAction.APPROVED
            if batch.approval_status == MarketingTouchBatchApprovalStatus.APPROVED
            else MarketingTouchBatchApprovalAction.REJECTED,
            batch.approval_note,
        )
        return self._serialize_batch(batch)

    def resubmit(self, task_id: str, batch_id: str, data: dict):
        batch = self._get_batch(task_id, batch_id)
        if not self.user or batch.user_id != self.user.id:
            raise AppApiException(403, "Only batch creator can resubmit")
        if batch.approval_status != MarketingTouchBatchApprovalStatus.REJECTED:
            raise AppApiException(400, "Only rejected touch batch can be resubmitted")
        if batch.status != MarketingTouchBatchStatus.READY:
            raise AppApiException(400, "Executed touch batch cannot be resubmitted")
        serializer = MarketingTouchBatchResubmitSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        filters = {key: value for key, value in serializer.validated_data.items() if key != "resubmit_note"}
        now = timezone.now()
        selected, excluded = self._build_snapshot(batch.task, filters, now, batch.id)
        batch.name = filters["name"]
        batch.filter_config = filters
        batch.customer_snapshot = selected
        batch.excluded_snapshot = excluded
        batch.selected_count = len(selected)
        batch.excluded_count = len(excluded)
        batch.approval_status = MarketingTouchBatchApprovalStatus.PENDING
        batch.approval_note = ""
        batch.approver_name = ""
        batch.approved_at = None
        batch.approval_due_at = _approval_due_at(batch.task, now)
        batch.save(
            update_fields=[
                "name",
                "filter_config",
                "customer_snapshot",
                "excluded_snapshot",
                "selected_count",
                "excluded_count",
                "approval_status",
                "approval_note",
                "approver_name",
                "approved_at",
                "approval_due_at",
                "update_time",
            ]
        )
        self._mark_customer_batch_history(batch, selected, now)
        self._record_approval(
            batch, MarketingTouchBatchApprovalAction.RESUBMITTED, serializer.validated_data["resubmit_note"]
        )
        return self._serialize_batch(batch)

    def record_execution(self, task_id: str, batch_id: str, data: dict):
        batch = self._get_batch(task_id, batch_id)
        if batch.approval_status != MarketingTouchBatchApprovalStatus.APPROVED:
            raise AppApiException(400, "Touch batch requires approval before execution")
        if batch.status == MarketingTouchBatchStatus.CLOSED:
            raise AppApiException(400, "Closed touch batch cannot receive new execution records")
        serializer = MarketingTouchExecutionCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        selected_ids = {str(row.get("customer_id")) for row in (batch.customer_snapshot or [])}
        customer_id = str(payload["customer_id"])
        if customer_id not in selected_ids:
            raise AppApiException(400, "Customer is not included in this touch batch")
        customer = MarketingCustomer.objects.filter(
            id=payload["customer_id"], task_id=batch.task_id, workspace_id=self.workspace_id
        ).first()
        if customer is None:
            raise AppApiException(404, "Marketing customer does not exist")
        if customer.status == MarketingCustomerStatus.CONVERTED:
            raise AppApiException(400, "Converted customer cannot receive new touch execution records")
        execution = MarketingTouchExecution.objects.create(
            workspace_id=self.workspace_id,
            batch=batch,
            customer=customer,
            user=self.user,
            result=payload["result"],
            note=payload["note"],
            next_follow_up_at=payload.get("next_follow_up_at"),
        )
        self._sync_customer_after_execution(customer, execution)
        if batch.status == MarketingTouchBatchStatus.READY:
            batch.status = MarketingTouchBatchStatus.RUNNING
            batch.save(update_fields=["status", "update_time"])
        return serialize_touch_execution(execution)

    def _get_batch(self, task_id: str, batch_id: str):
        self._get_task(task_id)
        batch = MarketingTouchBatch.objects.filter(
            id=batch_id,
            task_id=task_id,
            workspace_id=self.workspace_id,
        ).first()
        if batch is None:
            raise AppApiException(404, "Marketing touch batch does not exist")
        return batch

    def create(self, task_id: str, data: dict):
        task = self._get_task(task_id)
        serializer = MarketingTouchBatchCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        filters = dict(serializer.validated_data)
        if not filters.get("max_customers"):
            pilot_size = (task.config or {}).get("pilot_size", 0)
            try:
                pilot_size = int(pilot_size)
            except (TypeError, ValueError):
                pilot_size = 0
            if pilot_size > 0 and not MarketingTouchBatch.objects.filter(task_id=task.id).exists():
                filters["max_customers"] = pilot_size
        now = timezone.now()
        selected, excluded = self._build_snapshot(task, filters, now)
        batch = MarketingTouchBatch.objects.create(
            workspace_id=self.workspace_id,
            task=task,
            user=self.user,
            name=filters["name"],
            approval_status=MarketingTouchBatchApprovalStatus.PENDING,
            approval_due_at=_approval_due_at(task, now),
            filter_config=filters,
            customer_snapshot=selected,
            excluded_snapshot=excluded,
            selected_count=len(selected),
            excluded_count=len(excluded),
        )
        self._mark_customer_batch_history(batch, selected, now)
        self._record_approval(batch, MarketingTouchBatchApprovalAction.SUBMITTED, "")
        return self._serialize_batch(batch)

    def _serialize_batch(self, batch):
        can_approve = bool(
            self.user
            and batch.approval_status == MarketingTouchBatchApprovalStatus.PENDING
            and batch.user_id != self.user.id
            and is_workspace_manager(self.user.id, self.workspace_id)
        )
        can_resubmit = bool(
            self.user
            and batch.approval_status == MarketingTouchBatchApprovalStatus.REJECTED
            and batch.user_id == self.user.id
        )
        return serialize_touch_batch(batch, can_approve=can_approve, can_resubmit=can_resubmit)

    def _require_approver(self, batch):
        if not self.user or not is_workspace_manager(self.user.id, self.workspace_id):
            raise AppApiException(403, "Marketing approval requires workspace manager role")
        if batch.user_id == self.user.id:
            raise AppApiException(403, "Batch creator cannot approve own batch")

    def _record_approval(self, batch, action, note):
        MarketingTouchBatchApprovalRecord.objects.create(
            workspace_id=self.workspace_id, batch=batch, user=self.user, action=action, note=note
        )

    def _build_snapshot(self, task, filters, now, ignore_batch_id=None):
        selected, excluded = [], []
        max_customers = filters.get("max_customers")
        for customer in MarketingCustomer.objects.filter(task_id=task.id, workspace_id=self.workspace_id).order_by(
            "id"
        ):
            reason = self._exclude_reason(customer, filters, now, ignore_batch_id)
            snapshot = {
                "customer_id": str(customer.id),
                "name": customer.name,
                "phone_masked": f"{customer.phone[:3]}****{customer.phone[-4:]}"
                if len(customer.phone or "") >= 7
                else customer.phone,
                "status": customer.status,
                "current_plan": customer.current_plan,
                "province": customer.province,
                "monthly_data_usage": customer.monthly_data_usage,
                "monthly_call_usage": customer.monthly_call_usage,
            }
            if not reason and max_customers and len(selected) >= max_customers:
                reason = f"灰度上限 {max_customers} 人"
            (excluded if reason else selected).append({**snapshot, "reason": reason or "符合本批次筛选条件"})
        return selected, excluded

    def _mark_customer_batch_history(self, batch, selected, now):
        selected_ids = {row["customer_id"] for row in selected}
        for customer in MarketingCustomer.objects.filter(id__in=selected_ids):
            config = dict(customer.config or {})
            history = [
                row
                for row in (config.get("marketing_touch_batch_history") or [])
                if row.get("batch_id") != str(batch.id)
            ][-19:]
            history.append({"batch_id": str(batch.id), "batch_name": batch.name, "selected_at": now.isoformat()})
            config["marketing_touch_batch_history"] = history
            config["marketing_latest_touch_batch"] = {
                "id": str(batch.id),
                "name": batch.name,
                "selected_at": now.isoformat(),
            }
            customer.config = config
            customer.save(update_fields=["config", "update_time"])

    def queue(self, task_id: str):
        self._get_task(task_id)
        priority = {
            MarketingCustomerStatus.MANUAL: 0,
            MarketingCustomerStatus.INTENT: 1,
            MarketingCustomerStatus.CONSULTED: 2,
            MarketingCustomerStatus.PENDING: 3,
            MarketingCustomerStatus.TOUCHED: 4,
            MarketingCustomerStatus.NO_INTENT: 5,
        }
        customers = list(MarketingCustomer.objects.filter(task_id=task_id, workspace_id=self.workspace_id))
        customers.sort(key=lambda row: (priority.get(row.status, 99), -row.update_time.timestamp()))
        return [
            {
                "customer_id": str(row.id),
                "name": row.name,
                "phone_masked": f"{row.phone[:3]}****{row.phone[-4:]}" if len(row.phone or "") >= 7 else row.phone,
                "status": row.status,
                "intent": row.intent,
                "current_plan": row.current_plan,
                "queue_reason": self._queue_reason(row),
                "latest_batch": (row.config or {}).get("marketing_latest_touch_batch"),
            }
            for row in customers
            if row.status not in {MarketingCustomerStatus.NO_INTENT, MarketingCustomerStatus.CONVERTED}
        ]

    @staticmethod
    def _metrics(batch, executions, conversions=()):
        latest_by_customer = {}
        for execution in executions:
            latest_by_customer.setdefault(str(execution.customer_id), execution)
        outcome_counts = {result: 0 for result, _ in MarketingTouchExecutionResult.choices}
        for execution in latest_by_customer.values():
            outcome_counts[execution.result] = outcome_counts.get(execution.result, 0) + 1
        latest_conversion_by_customer = {}
        for conversion in conversions:
            latest_conversion_by_customer.setdefault(str(conversion.customer_id), conversion)
        converted_count = sum(
            row.outcome == MarketingConversionOutcome.CONVERTED for row in latest_conversion_by_customer.values()
        )
        lost_count = sum(
            row.outcome == MarketingConversionOutcome.LOST for row in latest_conversion_by_customer.values()
        )
        return {
            "selected_count": batch.selected_count,
            "executed_count": len(latest_by_customer),
            "waiting_count": max(batch.selected_count - len(latest_by_customer), 0),
            "contacted_count": outcome_counts[MarketingTouchExecutionResult.CONTACTED],
            "no_answer_count": outcome_counts[MarketingTouchExecutionResult.NO_ANSWER],
            "rejected_count": outcome_counts[MarketingTouchExecutionResult.REJECTED],
            "intent_count": outcome_counts[MarketingTouchExecutionResult.INTENT],
            "manual_count": outcome_counts[MarketingTouchExecutionResult.MANUAL],
            "converted_count": converted_count,
            "lost_count": lost_count,
            "conversion_rate": round(converted_count / batch.selected_count * 100, 1) if batch.selected_count else 0,
        }

    @staticmethod
    def _sync_customer_after_execution(customer, execution):
        status_mapping = {
            MarketingTouchExecutionResult.CONTACTED: MarketingCustomerStatus.TOUCHED,
            MarketingTouchExecutionResult.NO_ANSWER: MarketingCustomerStatus.TOUCHED,
            MarketingTouchExecutionResult.REJECTED: MarketingCustomerStatus.NO_INTENT,
            MarketingTouchExecutionResult.INTENT: MarketingCustomerStatus.INTENT,
            MarketingTouchExecutionResult.MANUAL: MarketingCustomerStatus.MANUAL,
        }
        customer.status = status_mapping[execution.result]
        if execution.result == MarketingTouchExecutionResult.INTENT:
            customer.intent = "有办理意向"
        elif execution.result == MarketingTouchExecutionResult.REJECTED:
            customer.intent = "明确拒绝"
        elif execution.result == MarketingTouchExecutionResult.MANUAL:
            customer.intent = "需人工处理"
        config = dict(customer.config or {})
        history = list(config.get("marketing_touch_execution_history") or [])[-19:]
        history.append(
            {
                "batch_id": str(execution.batch_id),
                "result": execution.result,
                "note": execution.note,
                "next_follow_up_at": execution.next_follow_up_at.isoformat() if execution.next_follow_up_at else None,
                "created_at": execution.create_time.isoformat(),
            }
        )
        config["marketing_touch_execution_history"] = history
        customer.config = config
        customer.save(update_fields=["status", "intent", "config", "update_time"])

    @staticmethod
    def _exclude_reason(customer, filters, now, ignore_batch_id=None):
        if customer.status not in filters["statuses"]:
            return "客户当前状态不在本批次范围内"
        if filters.get("plan_keyword") and filters["plan_keyword"] not in (customer.current_plan or ""):
            return "当前套餐不匹配"
        if filters.get("province") and filters["province"] != (customer.province or ""):
            return "省份不匹配"
        if _usage_number(customer.monthly_data_usage) < filters["min_data_usage_gb"]:
            return "近月流量未达到门槛"
        if _usage_number(customer.monthly_call_usage) < filters["min_call_usage_minutes"]:
            return "近月通话未达到门槛"
        history = [
            row
            for row in ((customer.config or {}).get("marketing_touch_batch_history") or [])
            if row.get("batch_id") != str(ignore_batch_id)
        ]
        if history and filters["cooldown_days"]:
            latest = history[-1].get("selected_at")
            last_selected = parse_datetime(latest) if isinstance(latest, str) else None
            if last_selected:
                if timezone.is_naive(last_selected):
                    last_selected = timezone.make_aware(last_selected)
                if last_selected >= now - timedelta(days=filters["cooldown_days"]):
                    return f"最近 {filters['cooldown_days']} 天已进入触达批次"
        return ""

    @staticmethod
    def _queue_reason(customer):
        if customer.status == MarketingCustomerStatus.MANUAL:
            return "需要人工处理"
        if customer.status == MarketingCustomerStatus.INTENT:
            return "客户已有明确办理意向"
        if customer.status == MarketingCustomerStatus.CONSULTED:
            return "客户已咨询，建议继续跟进"
        return "待首次触达"
