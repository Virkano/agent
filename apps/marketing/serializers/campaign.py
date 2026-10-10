# coding=utf-8
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from application.models.application_chat import Chat
from common.exception.app_exception import AppApiException
from common.result import Page
from marketing.models import (
    MarketingCampaign,
    MarketingCampaignApprovalStatus,
    MarketingCampaignStatus,
    MarketingCampaignVersion,
    MarketingCustomer,
    MarketingCustomerStatus,
    MarketingTask,
)
from marketing.recommendation import validate_recommendation_policy
from marketing.serializers.touch_batch import MarketingTouchBatchService
from xpack_lite.services import is_workspace_manager


class MarketingCampaignWriteSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, max_length=128)
    code = serializers.CharField(required=True, max_length=64)
    status = serializers.ChoiceField(required=False, choices=MarketingCampaignStatus.choices)
    priority = serializers.IntegerField(required=False, min_value=1, max_value=9999)
    exclusive_group = serializers.CharField(required=False, allow_blank=True, max_length=64)
    benefit = serializers.CharField(required=True, allow_blank=False, max_length=4000)
    fee_note = serializers.CharField(required=False, allow_blank=True, max_length=256)
    contract_note = serializers.CharField(required=False, allow_blank=True, max_length=256)
    plan_keywords = serializers.ListField(required=False, child=serializers.CharField(max_length=64), max_length=50)
    provinces = serializers.ListField(required=False, child=serializers.CharField(max_length=64), max_length=50)
    min_data_usage_gb = serializers.IntegerField(required=False, min_value=0, max_value=99999)
    min_call_usage_minutes = serializers.IntegerField(required=False, min_value=0, max_value=999999)
    effective_start = serializers.DateField(required=False, allow_null=True)
    effective_end = serializers.DateField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if (
            attrs.get("effective_start")
            and attrs.get("effective_end")
            and attrs["effective_start"] > attrs["effective_end"]
        ):
            raise serializers.ValidationError({"effective_end": "结束日期不能早于开始日期"})
        return attrs


class MarketingCampaignListQuerySerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)


class MarketingCampaignApprovalSerializer(serializers.Serializer):
    approval_status = serializers.ChoiceField(
        choices=[MarketingCampaignApprovalStatus.APPROVED, MarketingCampaignApprovalStatus.REJECTED]
    )
    approval_note = serializers.CharField(required=False, allow_blank=True, max_length=2000)

    def validate(self, attrs):
        if (
            attrs["approval_status"] == MarketingCampaignApprovalStatus.REJECTED
            and not attrs.get("approval_note", "").strip()
        ):
            raise serializers.ValidationError({"approval_note": "驳回时必须填写原因"})
        return attrs


class MarketingCampaignActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["EXPAND", "PAUSE"])
    task_id = serializers.UUIDField(required=False, allow_null=True)


CAMPAIGN_SNAPSHOT_FIELDS = (
    "name",
    "code",
    "priority",
    "exclusive_group",
    "benefit",
    "fee_note",
    "contract_note",
    "plan_keywords",
    "provinces",
    "min_data_usage_gb",
    "min_call_usage_minutes",
    "effective_start",
    "effective_end",
    "description",
)


def campaign_snapshot(row: MarketingCampaign):
    snapshot = {field: getattr(row, field) for field in CAMPAIGN_SNAPSHOT_FIELDS}
    for field in ("effective_start", "effective_end"):
        snapshot[field] = snapshot[field].isoformat() if snapshot[field] else None
    return snapshot


def serialize_campaign_version(row: MarketingCampaignVersion, changed_fields=None):
    return {
        "id": str(row.id),
        "campaign_id": str(row.campaign_id),
        "version": row.version,
        "snapshot": row.snapshot or {},
        "change_type": row.change_type,
        "source_version": row.source_version,
        "approval_status": row.approval_status,
        "approval_note": row.approval_note,
        "approver_name": row.approver_name,
        "approved_at": row.approved_at,
        "operator_name": row.user.nick_name or row.user.username if row.user else "",
        "changed_fields": changed_fields or [],
        "create_time": row.create_time,
    }


def serialize_campaign(row: MarketingCampaign, user=None):
    return {
        "id": str(row.id),
        "workspace_id": row.workspace_id,
        "name": row.name,
        "code": row.code,
        "status": row.status,
        "approval_status": row.approval_status,
        "approval_note": row.approval_note,
        "approver_name": row.approver_name,
        "approved_at": row.approved_at,
        "can_approve": can_approve_campaign(row, user),
        "can_submit": can_submit_campaign(row, user),
        "version": row.version,
        "priority": row.priority,
        "exclusive_group": row.exclusive_group,
        "benefit": row.benefit,
        "fee_note": row.fee_note,
        "contract_note": row.contract_note,
        "plan_keywords": row.plan_keywords or [],
        "provinces": row.provinces or [],
        "min_data_usage_gb": row.min_data_usage_gb,
        "min_call_usage_minutes": row.min_call_usage_minutes,
        "effective_start": row.effective_start,
        "effective_end": row.effective_end,
        "description": row.description,
        "create_user": row.user.nick_name if row.user else "",
        "create_time": row.create_time,
        "update_time": row.update_time,
    }


def can_approve_campaign(row: MarketingCampaign, user=None):
    return bool(
        user
        and row.approval_status == MarketingCampaignApprovalStatus.PENDING
        and row.user_id != user.id
        and is_workspace_manager(user.id, row.workspace_id)
    )


def can_submit_campaign(row: MarketingCampaign, user=None):
    return bool(
        user
        and row.user_id == user.id
        and row.approval_status
        in {
            MarketingCampaignApprovalStatus.DRAFT,
            MarketingCampaignApprovalStatus.REJECTED,
        }
    )


def campaign_to_offer(row: MarketingCampaign):
    return {
        "id": str(row.id),
        "campaign_id": str(row.id),
        "campaign_version": row.version,
        "name": row.name,
        "priority": row.priority,
        "exclusive_group": row.exclusive_group,
        "benefit": row.benefit,
        "fee_note": row.fee_note,
        "contract_note": row.contract_note,
        "plan_keywords": row.plan_keywords or [],
        "provinces": row.provinces or [],
        "min_data_usage_gb": row.min_data_usage_gb,
        "min_call_usage_minutes": row.min_call_usage_minutes,
        "effective_start": row.effective_start.isoformat() if row.effective_start else "",
        "effective_end": row.effective_end.isoformat() if row.effective_end else "",
    }


class MarketingCampaignService:
    def __init__(self, workspace_id, user=None):
        self.workspace_id = workspace_id
        self.user = user

    def _queryset(self):
        return (
            MarketingCampaign.objects.filter(workspace_id=self.workspace_id)
            .select_related("user")
            .order_by("-update_time")
        )

    def list(self, params):
        serializer = MarketingCampaignListQuerySerializer(data=params)
        serializer.is_valid(raise_exception=True)
        rows = self._queryset()
        name = serializer.validated_data.get("name")
        status = serializer.validated_data.get("status")
        if name:
            rows = rows.filter(Q(name__icontains=name) | Q(code__icontains=name) | Q(description__icontains=name))
        if status:
            rows = rows.filter(status=status)
        return [serialize_campaign(row, self.user) for row in rows]

    def page(self, current_page, page_size, params):
        rows = self.list(params)
        start = (current_page - 1) * page_size
        return Page(len(rows), rows[start : start + page_size], current_page, page_size)

    def get(self, campaign_id):
        row = self._queryset().filter(id=campaign_id).first()
        if row is None:
            raise AppApiException(404, _("Marketing campaign does not exist"))
        return serialize_campaign(row, self.user)

    def _values(self, data):
        serializer = MarketingCampaignWriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = dict(serializer.validated_data)
        values.setdefault("priority", 100)
        values.setdefault("exclusive_group", "")
        values.setdefault("fee_note", "费用以当地实际可办理方案为准。")
        values.setdefault("contract_note", "办理前会确认优惠期限和合约期。")
        values.setdefault("plan_keywords", [])
        values.setdefault("provinces", [])
        values.setdefault("min_data_usage_gb", 0)
        values.setdefault("min_call_usage_minutes", 0)
        values.setdefault("description", "")
        validate_recommendation_policy({"enabled": True, "offers": [{**values, "id": "validate"}]})
        return values

    def _record_version(self, row, change_type, source_version=None):
        version, _ = MarketingCampaignVersion.objects.update_or_create(
            campaign=row,
            version=row.version,
            defaults={
                "workspace_id": row.workspace_id,
                "snapshot": campaign_snapshot(row),
                "change_type": change_type,
                "source_version": source_version,
                "approval_status": row.approval_status,
                "approval_note": row.approval_note,
                "approver_name": row.approver_name,
                "approved_at": row.approved_at,
                "user": self.user or row.user,
            },
        )
        return version

    def _ensure_current_version(self, row):
        if not row.versions.filter(version=row.version).exists():
            self._record_version(row, "BASELINE")

    def _sync_version_approval(self, row):
        self._ensure_current_version(row)
        row.versions.filter(version=row.version).update(
            approval_status=row.approval_status,
            approval_note=row.approval_note,
            approver_name=row.approver_name,
            approved_at=row.approved_at,
            update_time=timezone.now(),
        )

    @transaction.atomic
    def create(self, data):
        values = self._values(data)
        values["status"] = MarketingCampaignStatus.DRAFT
        values["approval_status"] = MarketingCampaignApprovalStatus.DRAFT
        try:
            row = MarketingCampaign.objects.create(
                workspace_id=self.workspace_id,
                user=self.user,
                **values,
            )
        except IntegrityError:
            raise AppApiException(400, _("Marketing campaign code already exists"))
        self._record_version(row, "CREATE")
        return serialize_campaign(row, self.user)

    @transaction.atomic
    def update(self, campaign_id, data):
        row = MarketingCampaign.objects.filter(id=campaign_id, workspace_id=self.workspace_id).first()
        if row is None:
            raise AppApiException(404, _("Marketing campaign does not exist"))
        self._ensure_current_version(row)
        values = self._values(data)
        values.pop("status", None)
        for field, value in values.items():
            setattr(row, field, value)
        if row.approval_status != MarketingCampaignApprovalStatus.DRAFT:
            row.status = MarketingCampaignStatus.PAUSED
            row.approval_status = MarketingCampaignApprovalStatus.DRAFT
            row.approval_note = ""
            row.approver_name = ""
            row.approved_at = None
        row.version += 1
        try:
            row.save()
        except IntegrityError:
            raise AppApiException(400, _("Marketing campaign code already exists"))
        self._record_version(row, "UPDATE")
        return serialize_campaign(row, self.user)

    def submit(self, campaign_id):
        row = MarketingCampaign.objects.filter(id=campaign_id, workspace_id=self.workspace_id).first()
        if row is None:
            raise AppApiException(404, _("Marketing campaign does not exist"))
        if not can_submit_campaign(row, self.user):
            raise AppApiException(403, "仅活动创建人可提交草稿或已驳回活动")
        row.approval_status = MarketingCampaignApprovalStatus.PENDING
        row.approval_note = ""
        row.save(update_fields=["approval_status", "approval_note", "update_time"])
        self._sync_version_approval(row)
        return serialize_campaign(row, self.user)

    def approve(self, campaign_id, data):
        row = MarketingCampaign.objects.filter(id=campaign_id, workspace_id=self.workspace_id).first()
        if row is None:
            raise AppApiException(404, _("Marketing campaign does not exist"))
        if not can_approve_campaign(row, self.user):
            raise AppApiException(403, "活动审批需要非创建人的工作空间主管")
        serializer = MarketingCampaignApprovalSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        approved = serializer.validated_data["approval_status"] == MarketingCampaignApprovalStatus.APPROVED
        row.approval_status = serializer.validated_data["approval_status"]
        row.approval_note = serializer.validated_data.get("approval_note", "")
        row.approver_name = self.user.nick_name or self.user.username
        row.approved_at = timezone.now()
        row.status = MarketingCampaignStatus.ACTIVE if approved else MarketingCampaignStatus.PAUSED
        row.save(
            update_fields=["approval_status", "approval_note", "approver_name", "approved_at", "status", "update_time"]
        )
        self._sync_version_approval(row)
        return serialize_campaign(row, self.user)

    def versions(self, campaign_id):
        campaign = MarketingCampaign.objects.filter(id=campaign_id, workspace_id=self.workspace_id).first()
        if campaign is None:
            raise AppApiException(404, _("Marketing campaign does not exist"))
        self._ensure_current_version(campaign)
        rows = list(campaign.versions.select_related("user").order_by("version"))
        records = []
        previous_snapshot = {}
        for row in rows:
            snapshot = row.snapshot or {}
            changed_fields = [
                field
                for field in CAMPAIGN_SNAPSHOT_FIELDS
                if previous_snapshot and snapshot.get(field) != previous_snapshot.get(field)
            ]
            record = serialize_campaign_version(row, changed_fields)
            record["can_restore"] = bool(
                self.user
                and campaign.user_id == self.user.id
                and row.version < campaign.version
                and row.approval_status == MarketingCampaignApprovalStatus.APPROVED
            )
            records.append(record)
            previous_snapshot = snapshot
        records.reverse()
        return {
            "campaign": serialize_campaign(campaign, self.user),
            "records": records,
        }

    @transaction.atomic
    def restore(self, campaign_id, version):
        campaign = (
            MarketingCampaign.objects.select_for_update()
            .filter(
                id=campaign_id,
                workspace_id=self.workspace_id,
            )
            .first()
        )
        if campaign is None:
            raise AppApiException(404, _("Marketing campaign does not exist"))
        if not self.user or campaign.user_id != self.user.id:
            raise AppApiException(403, "仅活动创建人可恢复历史版本")
        self._ensure_current_version(campaign)
        source = campaign.versions.filter(
            version=version,
            approval_status=MarketingCampaignApprovalStatus.APPROVED,
        ).first()
        if source is None:
            raise AppApiException(400, "只能恢复已审批通过的历史版本")
        snapshot = self._values(source.snapshot or {})
        for field in CAMPAIGN_SNAPSHOT_FIELDS:
            if field in snapshot:
                setattr(campaign, field, snapshot[field])
        campaign.version += 1
        campaign.status = MarketingCampaignStatus.PAUSED
        campaign.approval_status = MarketingCampaignApprovalStatus.DRAFT
        campaign.approval_note = ""
        campaign.approver_name = ""
        campaign.approved_at = None
        campaign.save()
        self._record_version(campaign, "RESTORE", source_version=version)
        return serialize_campaign(campaign, self.user)

    def effect(self, campaign_id):
        campaign = MarketingCampaign.objects.filter(id=campaign_id, workspace_id=self.workspace_id).first()
        if campaign is None:
            raise AppApiException(404, _("Marketing campaign does not exist"))
        task_ids = [
            task.id
            for task in MarketingTask.objects.filter(workspace_id=self.workspace_id)
            if any(
                item.get("campaign_id") == str(campaign.id)
                for item in ((task.config or {}).get("marketing_campaign_snapshot") or [])
                if isinstance(item, dict)
            )
        ]
        chats = Chat.objects.filter(source__marketing_task_id__in=[str(task_id) for task_id in task_ids])
        matched_chats = []
        customer_ids = set()
        for chat in chats:
            source = chat.source if isinstance(chat.source, dict) else {}
            recommendation = (
                source.get("marketing_recommendation")
                if isinstance(source.get("marketing_recommendation"), dict)
                else {}
            )
            if str(recommendation.get("offer_id")) != str(campaign.id):
                continue
            matched_chats.append(chat)
            if source.get("marketing_customer_id"):
                customer_ids.add(str(source["marketing_customer_id"]))
        customers = MarketingCustomer.objects.filter(
            id__in=customer_ids,
            workspace_id=self.workspace_id,
        )
        total = customers.count()
        intent_count = customers.filter(status=MarketingCustomerStatus.INTENT).count()
        manual_count = customers.filter(status=MarketingCustomerStatus.MANUAL).count()
        converted_count = customers.filter(status=MarketingCustomerStatus.CONVERTED).count()
        no_intent_count = customers.filter(status=MarketingCustomerStatus.NO_INTENT).count()
        intent_rate = round(intent_count / total * 100, 1) if total else 0
        manual_rate = round(manual_count / total * 100, 1) if total else 0

        def segment_by(field):
            segments = {}
            for value, status in customers.values_list(field, "status"):
                name = str(value or "未填写").strip() or "未填写"
                item = segments.setdefault(
                    name,
                    {
                        "name": name,
                        "customer_count": 0,
                        "intent_count": 0,
                        "converted_count": 0,
                        "manual_count": 0,
                        "no_intent_count": 0,
                    },
                )
                item["customer_count"] += 1
                status_field = {
                    MarketingCustomerStatus.INTENT: "intent_count",
                    MarketingCustomerStatus.CONVERTED: "converted_count",
                    MarketingCustomerStatus.MANUAL: "manual_count",
                    MarketingCustomerStatus.NO_INTENT: "no_intent_count",
                }.get(status)
                if status_field:
                    item[status_field] += 1
            records = []
            for item in segments.values():
                count = item["customer_count"]
                item["intent_rate"] = round(item["intent_count"] / count * 100, 1) if count else 0
                item["conversion_rate"] = round(item["converted_count"] / count * 100, 1) if count else 0
                records.append(item)
            return sorted(records, key=lambda item: (-item["customer_count"], item["name"]))

        if total == 0:
            action, reason, next_size = "CONTINUE_GRAY", "暂无命中客户会话，建议继续小批灰度并确认客户匹配条件。", 0
        elif manual_rate >= 30 or no_intent_count / total >= 60 / 100:
            action, reason, next_size = "PAUSE", "转人工率或明确无意向率偏高，建议暂停活动并复核权益、客群和话术。", 0
        elif intent_rate >= 20 or converted_count > 0:
            action, reason, next_size = (
                "EXPAND",
                "首批意向或办理表现达到放量阈值，建议新建下一批次扩大触达。",
                min(max(total * 2, 20), 10000),
            )
        else:
            action, reason, next_size = "CONTINUE_GRAY", "首批反馈尚不足以放量，建议维持当前规模并继续观察。", total
        return {
            "campaign": serialize_campaign(campaign, self.user),
            "scope": "仅统计已在会话归因中命中该活动的客户；历史任务快照不被修改。",
            "metrics": {
                "task_count": len(task_ids),
                "chat_count": len(matched_chats),
                "customer_count": total,
                "intent_count": intent_count,
                "manual_count": manual_count,
                "converted_count": converted_count,
                "no_intent_count": no_intent_count,
                "intent_rate": intent_rate,
                "manual_rate": manual_rate,
            },
            "recommendation": {"action": action, "reason": reason, "suggested_next_batch_size": next_size},
            "eligible_tasks": [
                {"id": str(task_id), "name": MarketingTask.objects.get(id=task_id).name} for task_id in task_ids
            ],
            "breakdowns": {
                "province": segment_by("province"),
                "current_plan": segment_by("current_plan"),
            },
        }

    def execute_recommendation(self, campaign_id, data):
        campaign = MarketingCampaign.objects.filter(id=campaign_id, workspace_id=self.workspace_id).first()
        if campaign is None:
            raise AppApiException(404, _("Marketing campaign does not exist"))
        serializer = MarketingCampaignActionSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]
        if action == "PAUSE":
            campaign.status = MarketingCampaignStatus.PAUSED
            campaign.save(update_fields=["status", "update_time"])
            return {"action": "PAUSE", "campaign": serialize_campaign(campaign, self.user)}
        if (
            campaign.status != MarketingCampaignStatus.ACTIVE
            or campaign.approval_status != MarketingCampaignApprovalStatus.APPROVED
        ):
            raise AppApiException(400, "活动未处于已审批上线状态，不能放量")
        task_id = serializer.validated_data.get("task_id")
        task = MarketingTask.objects.filter(id=task_id, workspace_id=self.workspace_id).first()
        if task is None or not any(
            item.get("campaign_id") == str(campaign.id)
            for item in ((task.config or {}).get("marketing_campaign_snapshot") or [])
            if isinstance(item, dict)
        ):
            raise AppApiException(400, "请选择关联当前活动的营销任务")
        effect = self.effect(campaign_id)
        suggested_size = effect["recommendation"]["suggested_next_batch_size"] or 20
        last_batch = task.touch_batches.order_by("-create_time").first()
        filters = dict(last_batch.filter_config or {}) if last_batch else {}
        filters.update({"name": f"{campaign.name}-放量批次", "max_customers": suggested_size})
        batch = MarketingTouchBatchService(self.workspace_id, self.user).create(str(task.id), filters)
        return {"action": "EXPAND", "batch": batch, "suggested_next_batch_size": suggested_size}

    @transaction.atomic
    def delete(self, campaign_id):
        row = MarketingCampaign.objects.filter(id=campaign_id, workspace_id=self.workspace_id).first()
        if row is None:
            raise AppApiException(404, _("Marketing campaign does not exist"))
        self._ensure_current_version(row)
        row.status = MarketingCampaignStatus.ARCHIVED
        row.version += 1
        row.save(update_fields=["status", "version", "update_time"])
        self._record_version(row, "ARCHIVE")
        return True
