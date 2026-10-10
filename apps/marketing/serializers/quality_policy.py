from django.db.models import Q
from rest_framework import serializers

from common.exception.app_exception import AppApiException
from common.result import Page
from marketing.models import (
    MarketingAnswerPreflightRecord,
    MarketingAnswerQualityStatus,
    MarketingPreflightAction,
    MarketingQualityPolicy,
    MarketingQualityPolicyMode,
)
from marketing.preflight import get_workspace_quality_policy
from marketing.quality import RISK_DEFINITIONS, RULE_VERSION
from marketing.serializers.quality_effect import MarketingQualityRuleEffectService, RISK_LABELS
from marketing.serializers.quality_review import validate_or_raise


class MarketingQualityPolicySerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=MarketingQualityPolicyMode.choices)
    intercept_rule_types = serializers.ListField(
        child=serializers.ChoiceField(choices=list(RISK_DEFINITIONS)),
        required=False,
        allow_empty=True,
    )


class MarketingPreflightQuerySerializer(serializers.Serializer):
    task_id = serializers.UUIDField(required=False, allow_null=True)
    status = serializers.ChoiceField(required=False, allow_blank=True, choices=MarketingAnswerQualityStatus.choices)
    action = serializers.ChoiceField(required=False, allow_blank=True, choices=MarketingPreflightAction.choices)
    keyword = serializers.CharField(required=False, allow_blank=True, max_length=200)


def serialize_preflight_record(row):
    return {
        "id": str(row.id),
        "task_id": str(row.task_id),
        "task_name": row.task.name,
        "customer_id": str(row.customer_id) if row.customer_id else None,
        "customer_name": row.customer.name if row.customer else "",
        "record_id": str(row.record_id),
        "problem_text": row.record.problem_text,
        "policy_mode": row.policy_mode,
        "action": row.action,
        "generated_answer": row.generated_answer,
        "final_answer": row.final_answer,
        "status": row.status,
        "score": row.score,
        "risk_types": row.risk_types or [],
        "reasons": row.reasons or [],
        "suggestion": row.suggestion,
        "evidence": row.evidence or {},
        "rule_version": row.rule_version,
        "evaluation_ms": row.evaluation_ms,
        "create_time": row.create_time,
    }


class MarketingQualityPolicyService:
    def __init__(self, workspace_id, user=None):
        self.workspace_id = workspace_id
        self.user = user

    @staticmethod
    def _available_modes():
        return [
            {"value": MarketingQualityPolicyMode.OFF, "label": "关闭"},
            {"value": MarketingQualityPolicyMode.SHADOW, "label": "影子检测"},
            {"value": MarketingQualityPolicyMode.INTERCEPT, "label": "灰度拦截"},
        ]

    def _eligible_rules(self):
        analysis = MarketingQualityRuleEffectService(self.workspace_id, self.user).analyze({})
        return [row for row in analysis["rules"] if row["eligible"]]

    def _response(self, policy, eligible_rules):
        return {
            **policy,
            "available_modes": self._available_modes(),
            "interception_available": bool(eligible_rules),
            "eligible_rule_options": [{"value": row["risk_type"], "label": row["label"]} for row in eligible_rules],
            "interception_guard": "只有通过样本量、问题确认率和误报率门槛的高风险规则可以启用",
        }

    def get(self):
        policy = get_workspace_quality_policy(self.workspace_id)
        return self._response(policy, self._eligible_rules())

    def update(self, data):
        serializer = MarketingQualityPolicySerializer(data=data)
        values = validate_or_raise(serializer)
        existing = MarketingQualityPolicy.objects.filter(workspace_id=self.workspace_id).first()
        intercept_rule_types = list(
            dict.fromkeys(values.get("intercept_rule_types", existing.intercept_rule_types if existing else []))
        )
        eligible_rules = self._eligible_rules()
        eligible_rule_types = {row["risk_type"] for row in eligible_rules}
        if values["mode"] == MarketingQualityPolicyMode.INTERCEPT:
            if not intercept_rule_types:
                raise AppApiException(400, "至少选择一条已准入的高风险规则")
            unavailable = [risk_type for risk_type in intercept_rule_types if risk_type not in eligible_rule_types]
            if unavailable:
                labels = "、".join(RISK_LABELS.get(risk_type, risk_type) for risk_type in unavailable)
                raise AppApiException(400, f"以下规则尚未通过灰度准入门槛：{labels}")
        updater_name = ""
        if self.user:
            updater_name = self.user.nick_name or self.user.username
        policy, _ = MarketingQualityPolicy.objects.update_or_create(
            workspace_id=self.workspace_id,
            defaults={
                "mode": values["mode"],
                "rule_version": RULE_VERSION,
                "intercept_rule_types": intercept_rule_types,
                "updated_by": self.user,
                "updated_by_name": updater_name,
            },
        )
        return self._response(
            {
                "mode": policy.mode,
                "rule_version": policy.rule_version,
                "intercept_rule_types": list(policy.intercept_rule_types or []),
                "updated_by_name": policy.updated_by_name,
                "update_time": policy.update_time,
            },
            eligible_rules,
        )

    def _queryset(self):
        return MarketingAnswerPreflightRecord.objects.filter(workspace_id=self.workspace_id).select_related(
            "task", "customer", "record"
        )

    def page(self, current_page, page_size, params):
        serializer = MarketingPreflightQuerySerializer(data=params)
        values = validate_or_raise(serializer)
        rows = self._queryset()
        if values.get("task_id"):
            rows = rows.filter(task_id=values["task_id"])
        if values.get("status"):
            rows = rows.filter(status=values["status"])
        if values.get("action"):
            rows = rows.filter(action=values["action"])
        if values.get("keyword"):
            keyword = values["keyword"]
            rows = rows.filter(
                Q(task__name__icontains=keyword)
                | Q(customer__name__icontains=keyword)
                | Q(record__problem_text__icontains=keyword)
                | Q(generated_answer__icontains=keyword)
                | Q(final_answer__icontains=keyword)
            )
        rows = rows.order_by("-create_time")
        total = rows.count()
        start = (current_page - 1) * page_size
        page = Page(
            total,
            [serialize_preflight_record(row) for row in rows[start : start + page_size]],
            current_page,
            page_size,
        )
        all_rows = self._queryset()
        page["summary"] = {
            "total_count": all_rows.count(),
            "pass_count": all_rows.filter(status=MarketingAnswerQualityStatus.PASS).count(),
            "review_count": all_rows.filter(status=MarketingAnswerQualityStatus.REVIEW).count(),
            "high_risk_count": all_rows.filter(status=MarketingAnswerQualityStatus.HIGH_RISK).count(),
            "safeguard_rewritten_count": all_rows.filter(action=MarketingPreflightAction.SAFEGUARD_REWRITTEN).count(),
            "intercepted_count": all_rows.filter(action=MarketingPreflightAction.INTERCEPTED).count(),
            "bypassed_count": all_rows.filter(action=MarketingPreflightAction.BYPASSED).count(),
        }
        page["risk_definitions"] = {
            key: {"reason": value[2], "suggestion": value[3]} for key, value in RISK_DEFINITIONS.items()
        }
        return page


def reconcile_quality_policy_eligibility(workspace_id):
    """Remove degraded rules and fail back to shadow mode when none remain eligible."""

    policy = MarketingQualityPolicy.objects.filter(
        workspace_id=workspace_id,
        mode=MarketingQualityPolicyMode.INTERCEPT,
    ).first()
    if policy is None:
        return None
    service = MarketingQualityPolicyService(workspace_id)
    eligible_rule_types = {row["risk_type"] for row in service._eligible_rules()}
    active_rule_types = [
        risk_type for risk_type in (policy.intercept_rule_types or []) if risk_type in eligible_rule_types
    ]
    if active_rule_types == list(policy.intercept_rule_types or []):
        return policy
    policy.intercept_rule_types = active_rule_types
    if not active_rule_types:
        policy.mode = MarketingQualityPolicyMode.SHADOW
    policy.updated_by = None
    policy.updated_by_name = "系统自动回退"
    policy.save(
        update_fields=[
            "mode",
            "intercept_rule_types",
            "updated_by",
            "updated_by_name",
            "update_time",
        ]
    )
    return policy
