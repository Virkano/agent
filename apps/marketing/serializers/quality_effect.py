from django.db.models import Count, Max, Q
from django.utils import timezone
from rest_framework import serializers

from marketing.models import (
    MarketingAnswerManualReviewStatus,
    MarketingAnswerPreflightRecord,
    MarketingAnswerQualityReview,
    MarketingAnswerQualityStatus,
)
from marketing.quality import RISK_DEFINITIONS
from marketing.serializers.quality_review import validate_or_raise


MIN_REVIEWED_SAMPLES = 20
MIN_ISSUE_CONFIRMATION_RATE = 90.0
MAX_FALSE_POSITIVE_RATE = 5.0

RISK_LABELS = {
    "RUNTIME_ERROR": "运行错误",
    "OFF_TOPIC": "答非所问",
    "INTERNAL_EXPOSURE": "内部话术暴露",
    "UNVERIFIED_PRICE": "未确认资费",
    "UNVERIFIED_COMMITMENT": "未确认承诺",
    "PROVINCE_MISMATCH": "省份不一致",
    "REPEATED_ANSWER": "重复回答",
    "MISSING_MATCHED_BENEFIT": "缺少活动权益",
    "MISSING_REFERENCE": "缺少知识依据",
    "EMPTY_OR_TOO_SHORT": "回答过短",
}


class MarketingQualityRuleEffectQuerySerializer(serializers.Serializer):
    task_id = serializers.UUIDField(required=False, allow_null=True)
    risk_type = serializers.ChoiceField(required=False, allow_blank=True, choices=list(RISK_DEFINITIONS))
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)

    def validate(self, attrs):
        if attrs.get("date_from") and attrs.get("date_to") and attrs["date_from"] > attrs["date_to"]:
            raise serializers.ValidationError({"date_to": "结束日期不能早于开始日期"})
        return attrs


def _percentage(value, total):
    return round(value * 100 / total, 1) if total else None


def _gate_result(is_high_risk, reviewed_count, issue_confirmation_rate, false_positive_rate):
    blockers = []
    if not is_high_risk:
        blockers.append({"code": "NOT_HIGH_RISK", "message": "仅高风险规则可进入拦截候选"})
    if reviewed_count < MIN_REVIEWED_SAMPLES:
        blockers.append(
            {
                "code": "INSUFFICIENT_SAMPLE",
                "message": f"人工样本还差 {MIN_REVIEWED_SAMPLES - reviewed_count} 条",
            }
        )
    if issue_confirmation_rate is not None and issue_confirmation_rate < MIN_ISSUE_CONFIRMATION_RATE:
        blockers.append(
            {
                "code": "LOW_CONFIRMATION_RATE",
                "message": f"问题确认率需达到 {MIN_ISSUE_CONFIRMATION_RATE:g}%",
            }
        )
    if false_positive_rate is not None and false_positive_rate > MAX_FALSE_POSITIVE_RATE:
        blockers.append(
            {
                "code": "HIGH_FALSE_POSITIVE_RATE",
                "message": f"误报率需不高于 {MAX_FALSE_POSITIVE_RATE:g}%",
            }
        )
    if not blockers:
        return True, "ELIGIBLE", "可进入灰度候选", []
    status = blockers[0]["code"]
    labels = {
        "NOT_HIGH_RISK": "非拦截规则",
        "INSUFFICIENT_SAMPLE": "样本不足",
        "LOW_CONFIRMATION_RATE": "确认率不足",
        "HIGH_FALSE_POSITIVE_RATE": "误报率过高",
    }
    return False, status, labels[status], blockers


class MarketingQualityRuleEffectService:
    def __init__(self, workspace_id, user=None):
        self.workspace_id = workspace_id
        self.user = user

    def _filter_querysets(self, values):
        reviews = MarketingAnswerQualityReview.objects.filter(workspace_id=self.workspace_id)
        preflights = MarketingAnswerPreflightRecord.objects.filter(workspace_id=self.workspace_id)
        task_id = values.get("task_id")
        risk_type = values.get("risk_type")
        if task_id:
            reviews = reviews.filter(task_id=task_id)
            preflights = preflights.filter(task_id=task_id)
        if risk_type:
            reviews = reviews.filter(risk_types__contains=[risk_type])
            preflights = preflights.filter(risk_types__contains=[risk_type])
        if values.get("date_from"):
            reviews = reviews.filter(record__create_time__date__gte=values["date_from"])
            preflights = preflights.filter(create_time__date__gte=values["date_from"])
        if values.get("date_to"):
            reviews = reviews.filter(record__create_time__date__lte=values["date_to"])
            preflights = preflights.filter(create_time__date__lte=values["date_to"])
        return reviews, preflights

    def analyze(self, params):
        serializer = MarketingQualityRuleEffectQuerySerializer(data=params)
        values = validate_or_raise(serializer)
        reviews, preflights = self._filter_querysets(values)
        reviewed_statuses = [
            MarketingAnswerManualReviewStatus.CONFIRMED_PASS,
            MarketingAnswerManualReviewStatus.CONFIRMED_ISSUE,
            MarketingAnswerManualReviewStatus.REVISED,
        ]
        issue_statuses = [
            MarketingAnswerManualReviewStatus.CONFIRMED_ISSUE,
            MarketingAnswerManualReviewStatus.REVISED,
        ]
        risk_types = [values["risk_type"]] if values.get("risk_type") else list(RISK_DEFINITIONS)
        rules = []
        for risk_type in risk_types:
            definition = RISK_DEFINITIONS[risk_type]
            rule_reviews = reviews.filter(risk_types__contains=[risk_type])
            metrics = rule_reviews.aggregate(
                hit_count=Count("id"),
                pending_count=Count("id", filter=Q(manual_status=MarketingAnswerManualReviewStatus.PENDING)),
                reviewed_count=Count("id", filter=Q(manual_status__in=reviewed_statuses)),
                confirmed_issue_count=Count("id", filter=Q(manual_status__in=issue_statuses)),
                false_positive_count=Count(
                    "id", filter=Q(manual_status=MarketingAnswerManualReviewStatus.CONFIRMED_PASS)
                ),
                revised_count=Count("id", filter=Q(manual_status=MarketingAnswerManualReviewStatus.REVISED)),
                latest_hit_at=Max("record__create_time"),
            )
            shadow_metrics = preflights.filter(risk_types__contains=[risk_type]).aggregate(
                shadow_hit_count=Count("id"),
                latest_shadow_hit_at=Max("create_time"),
            )
            issue_confirmation_rate = _percentage(metrics["confirmed_issue_count"], metrics["reviewed_count"])
            false_positive_rate = _percentage(metrics["false_positive_count"], metrics["reviewed_count"])
            eligible, gate_status, gate_label, blockers = _gate_result(
                definition[1],
                metrics["reviewed_count"],
                issue_confirmation_rate,
                false_positive_rate,
            )
            latest_hit_at = metrics["latest_hit_at"]
            latest_shadow_hit_at = shadow_metrics["latest_shadow_hit_at"]
            if latest_shadow_hit_at and (not latest_hit_at or latest_shadow_hit_at > latest_hit_at):
                latest_hit_at = latest_shadow_hit_at
            rules.append(
                {
                    "risk_type": risk_type,
                    "label": RISK_LABELS[risk_type],
                    "is_high_risk": definition[1],
                    "reason": definition[2],
                    "suggestion": definition[3],
                    **{key: value for key, value in metrics.items() if key != "latest_hit_at"},
                    "shadow_hit_count": shadow_metrics["shadow_hit_count"],
                    "manual_review_rate": _percentage(metrics["reviewed_count"], metrics["hit_count"]),
                    "issue_confirmation_rate": issue_confirmation_rate,
                    "false_positive_rate": false_positive_rate,
                    "eligible": eligible,
                    "gate_status": gate_status,
                    "gate_label": gate_label,
                    "blockers": blockers,
                    "latest_hit_at": latest_hit_at,
                }
            )
        rules.sort(
            key=lambda row: (
                not row["eligible"],
                not row["is_high_risk"],
                -row["reviewed_count"],
                -row["hit_count"],
                row["risk_type"],
            )
        )
        problem_statuses = [MarketingAnswerQualityStatus.REVIEW, MarketingAnswerQualityStatus.HIGH_RISK]
        summary = reviews.aggregate(
            hit_record_count=Count("id", filter=Q(status__in=problem_statuses)),
            pending_record_count=Count(
                "id",
                filter=Q(
                    status__in=problem_statuses,
                    manual_status=MarketingAnswerManualReviewStatus.PENDING,
                ),
            ),
            manually_reviewed_record_count=Count(
                "id",
                filter=Q(status__in=problem_statuses, manual_status__in=reviewed_statuses),
            ),
        )
        summary.update(
            preflight_record_count=preflights.count(),
            preflight_risk_record_count=preflights.exclude(status=MarketingAnswerQualityStatus.PASS).count(),
            eligible_rule_count=sum(1 for row in rules if row["eligible"]),
            displayed_rule_count=len(rules),
        )
        return {
            "summary": summary,
            "thresholds": {
                "min_reviewed_samples": MIN_REVIEWED_SAMPLES,
                "min_issue_confirmation_rate": MIN_ISSUE_CONFIRMATION_RATE,
                "max_false_positive_rate": MAX_FALSE_POSITIVE_RATE,
                "high_risk_only": True,
            },
            "risk_type_options": [
                {"value": risk_type, "label": RISK_LABELS[risk_type]} for risk_type in RISK_DEFINITIONS
            ],
            "rules": rules,
            "generated_at": timezone.now(),
        }
