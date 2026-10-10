# coding=utf-8
import time

from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from rest_framework import serializers

from common.exception.app_exception import AppApiException
from marketing.models import (
    MarketingCampaign,
    MarketingCustomer,
    RecommendationFeedbackEvent,
    RecommendationFeedbackType,
    RecommendationFusionRun,
    RecommendationRankingRun,
    RecommendationRankingStatus,
    RecommendationRankingVersion,
)
from marketing.serializers.recommendation_engine import _item_payload, _matches_campaign, _to_number, _user_payload
from marketing.serializers.recommendation_fusion import RecommendationFusionService


RANKING_FEATURES = (
    "RECALL_SCORE",
    "BUSINESS_MATCH",
    "REGION_FIT",
    "PLAN_FIT",
    "USAGE_FIT",
    "CHANNEL_COVERAGE",
    "PRIORITY_SCORE",
)
DEFAULT_RANKING_WEIGHTS = {
    "RECALL_SCORE": 0.40,
    "BUSINESS_MATCH": 0.16,
    "REGION_FIT": 0.10,
    "PLAN_FIT": 0.10,
    "USAGE_FIT": 0.08,
    "CHANNEL_COVERAGE": 0.10,
    "PRIORITY_SCORE": 0.06,
}
FEATURE_LABELS = {
    "RECALL_SCORE": "融合召回分",
    "BUSINESS_MATCH": "业务规则适配",
    "REGION_FIT": "地域适配",
    "PLAN_FIT": "套餐适配",
    "USAGE_FIT": "用量门槛",
    "CHANNEL_COVERAGE": "召回通道覆盖",
    "PRIORITY_SCORE": "活动优先级",
}


class RecommendationRankingVersionSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True, max_length=128)
    feature_weights = serializers.DictField(child=serializers.FloatField(min_value=0, max_value=10))
    auto_publish = serializers.BooleanField(default=False)

    def validate_feature_weights(self, value):
        unknown = set(value) - set(RANKING_FEATURES)
        if unknown:
            raise serializers.ValidationError(f"包含未知精排特征：{', '.join(sorted(unknown))}")
        merged = {**DEFAULT_RANKING_WEIGHTS, **value}
        if sum(merged.values()) <= 0:
            raise serializers.ValidationError("精排特征权重之和必须大于 0")
        return {feature: round(float(merged[feature]), 4) for feature in RANKING_FEATURES}


class RecommendationRankingInferSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField()
    top_n = serializers.IntegerField(min_value=1, max_value=50, default=5)
    candidate_pool_size = serializers.IntegerField(min_value=5, max_value=100, default=30)
    ranking_version_id = serializers.UUIDField(required=False)
    model_version_id = serializers.UUIDField(required=False)


def ranking_feature_schema():
    return [{"value": feature, "label": FEATURE_LABELS[feature]} for feature in RANKING_FEATURES]


def serialize_ranking_version(row):
    return {
        "id": str(row.id),
        "version": row.version,
        "name": row.name,
        "status": row.status,
        "status_label": row.get_status_display(),
        "feature_weights": {**DEFAULT_RANKING_WEIGHTS, **(row.feature_weights or {})},
        "feature_schema": row.feature_schema or ranking_feature_schema(),
        "metrics": row.metrics or {},
        "published_at": row.published_at,
        "create_time": row.create_time,
    }


def serialize_ranking_run(row):
    return {
        "id": str(row.id),
        "customer": {
            "id": str(row.customer_id) if row.customer_id else None,
            "name": row.customer.name if row.customer else "已删除客户",
        },
        "fusion_run_id": str(row.fusion_run_id) if row.fusion_run_id else None,
        "ranking_version": row.ranking_version.version if row.ranking_version else None,
        "top_n": row.top_n,
        "candidate_count": row.candidate_count,
        "latency_ms": row.latency_ms,
        "config_snapshot": row.config_snapshot or {},
        "ranked_candidates": row.ranked_candidates or [],
        "create_time": row.create_time,
    }


class RecommendationRankingService:
    def __init__(self, workspace_id, user=None):
        self.workspace_id = workspace_id
        self.user = user

    @transaction.atomic
    def _default_version(self):
        existing = (
            RecommendationRankingVersion.objects.filter(workspace_id=self.workspace_id).order_by("version").first()
        )
        if existing:
            return existing
        return RecommendationRankingVersion.objects.create(
            workspace_id=self.workspace_id,
            version=1,
            name="可解释加权精排基线-v1",
            status=RecommendationRankingStatus.PUBLISHED,
            feature_weights=DEFAULT_RANKING_WEIGHTS,
            feature_schema=ranking_feature_schema(),
            metrics={"baseline": "weighted_linear", "feature_count": len(RANKING_FEATURES), "weight_sum": 1.0},
            published_at=timezone.now(),
            user=self.user,
        )

    def _resolve_version(self, version_id=None):
        self._default_version()
        versions = RecommendationRankingVersion.objects.filter(workspace_id=self.workspace_id)
        if version_id:
            version = versions.filter(id=version_id).first()
            if version is None:
                raise AppApiException(404, "精排策略版本不存在")
            return version
        version = versions.filter(status=RecommendationRankingStatus.PUBLISHED).order_by("-version").first()
        if version is None:
            raise AppApiException(400, "当前工作空间没有已发布的精排策略")
        return version

    @transaction.atomic
    def create_version(self, data):
        serializer = RecommendationRankingVersionSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        self._default_version()
        next_version = (
            RecommendationRankingVersion.objects.filter(workspace_id=self.workspace_id).aggregate(Max("version"))[
                "version__max"
            ]
            or 0
        ) + 1
        version = RecommendationRankingVersion.objects.create(
            workspace_id=self.workspace_id,
            version=next_version,
            name=values.get("name") or f"可解释加权精排-v{next_version}",
            status=RecommendationRankingStatus.DRAFT,
            feature_weights=values["feature_weights"],
            feature_schema=ranking_feature_schema(),
            metrics={
                "baseline": "weighted_linear",
                "feature_count": len(RANKING_FEATURES),
                "weight_sum": round(sum(values["feature_weights"].values()), 4),
            },
            user=self.user,
        )
        if values["auto_publish"]:
            return self.publish(str(version.id))
        return serialize_ranking_version(version)

    @transaction.atomic
    def publish(self, version_id):
        version = (
            RecommendationRankingVersion.objects.select_for_update()
            .filter(
                workspace_id=self.workspace_id,
                id=version_id,
            )
            .first()
        )
        if version is None:
            raise AppApiException(404, "精排策略版本不存在")
        RecommendationRankingVersion.objects.filter(
            workspace_id=self.workspace_id,
            status=RecommendationRankingStatus.PUBLISHED,
        ).exclude(id=version.id).update(status=RecommendationRankingStatus.ARCHIVED)
        version.status = RecommendationRankingStatus.PUBLISHED
        version.published_at = timezone.now()
        version.user = self.user
        version.save(update_fields=["status", "published_at", "user", "update_time"])
        return serialize_ranking_version(version)

    @staticmethod
    def _feature_values(customer, campaign, candidate, enabled_channel_count):
        user_payload = _user_payload(customer)
        item_payload = _item_payload(campaign)
        provinces = campaign.provinces or []
        keywords = campaign.plan_keywords or []
        region_fit = 1.0 if customer.province and customer.province in provinces else (0.6 if not provinces else 0.0)
        plan_fit = (
            1.0
            if keywords and any(keyword in customer.current_plan for keyword in keywords)
            else (0.6 if not keywords else 0.0)
        )
        data_fit = _to_number(customer.monthly_data_usage) >= campaign.min_data_usage_gb
        call_fit = _to_number(customer.monthly_call_usage) >= campaign.min_call_usage_minutes
        return {
            "RECALL_SCORE": min(1.0, max(0.0, float(candidate.get("score") or 0))),
            "BUSINESS_MATCH": 1.0 if _matches_campaign(user_payload, item_payload) else 0.0,
            "REGION_FIT": region_fit,
            "PLAN_FIT": plan_fit,
            "USAGE_FIT": (int(data_fit) + int(call_fit)) / 2,
            "CHANNEL_COVERAGE": min(1.0, int(candidate.get("source_count") or 0) / max(1, enabled_channel_count)),
            "PRIORITY_SCORE": 1 / (1 + max(0, campaign.priority) / 10),
        }

    @staticmethod
    def _feature_reason(feature, value, customer, campaign, candidate, enabled_channel_count):
        if feature == "RECALL_SCORE":
            return f"多路融合召回分 {float(candidate.get('score') or 0):.3f}"
        if feature == "BUSINESS_MATCH":
            return "全部业务准入条件满足" if value == 1 else "存在业务准入条件未满足"
        if feature == "REGION_FIT":
            return f"活动地域与客户 {customer.province or '未知地域'} 的适配程度"
        if feature == "PLAN_FIT":
            return f"活动套餐关键词与 {customer.current_plan or '未知套餐'} 的适配程度"
        if feature == "USAGE_FIT":
            return "近月流量与通话门槛的满足比例"
        if feature == "CHANNEL_COVERAGE":
            return f"命中 {candidate.get('source_count') or 0}/{max(1, enabled_channel_count)} 个启用召回通道"
        return f"活动优先级 {campaign.priority}，数值越小优先级越高"

    def _rank(self, customer, fusion_result, version, campaigns, top_n, enabled_channel_count):
        weights = {**DEFAULT_RANKING_WEIGHTS, **(version.feature_weights or {})}
        total_weight = sum(weights.values())
        ranked = []
        for candidate in fusion_result["candidates"]:
            campaign = campaigns.get(candidate["campaign_id"])
            if campaign is None:
                continue
            values = self._feature_values(customer, campaign, candidate, enabled_channel_count)
            details = []
            score = 0.0
            for feature in RANKING_FEATURES:
                contribution = values[feature] * weights[feature] / total_weight
                score += contribution
                details.append(
                    {
                        "feature": feature,
                        "label": FEATURE_LABELS[feature],
                        "value": round(values[feature], 6),
                        "weight": round(weights[feature], 4),
                        "contribution": round(contribution, 6),
                        "reason": self._feature_reason(
                            feature,
                            values[feature],
                            customer,
                            campaign,
                            candidate,
                            enabled_channel_count,
                        ),
                    }
                )
            details.sort(key=lambda row: (-row["contribution"], row["feature"]))
            ranked.append(
                {
                    **candidate,
                    "recall_score": candidate["score"],
                    "score": round(score, 6),
                    "rank_score": round(score, 6),
                    "feature_details": details,
                }
            )
        ranked.sort(key=lambda row: (-row["rank_score"], -row["recall_score"], row["campaign_name"]))
        for index, candidate in enumerate(ranked[:top_n], start=1):
            candidate["rank"] = index
        return ranked[:top_n]

    @transaction.atomic
    def infer(self, data):
        serializer = RecommendationRankingInferSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        customer = MarketingCustomer.objects.filter(
            workspace_id=self.workspace_id,
            id=values["customer_id"],
        ).first()
        if customer is None:
            raise AppApiException(404, "营销客户不存在")
        version = self._resolve_version(values.get("ranking_version_id"))
        fusion_payload = {
            "customer_id": str(customer.id),
            "top_k": values["candidate_pool_size"],
        }
        if values.get("model_version_id"):
            fusion_payload["model_version_id"] = str(values["model_version_id"])
        fusion_result = RecommendationFusionService(self.workspace_id, self.user).infer(fusion_payload)
        fusion_run = RecommendationFusionRun.objects.get(id=fusion_result["fusion_run_id"])
        campaigns = {
            str(row.id): row
            for row in MarketingCampaign.objects.filter(
                workspace_id=self.workspace_id,
                id__in=[row["campaign_id"] for row in fusion_result["candidates"]],
            )
        }
        started = time.perf_counter()
        enabled_channel_count = len(fusion_run.config_snapshot.get("enabled_channels") or []) or 1
        candidates = self._rank(
            customer,
            fusion_result,
            version,
            campaigns,
            values["top_n"],
            enabled_channel_count,
        )
        latency_ms = max(1, round((time.perf_counter() - started) * 1000))
        config_snapshot = {
            "version": version.version,
            "name": version.name,
            "feature_weights": {**DEFAULT_RANKING_WEIGHTS, **(version.feature_weights or {})},
            "feature_schema": version.feature_schema or ranking_feature_schema(),
        }
        run = RecommendationRankingRun.objects.create(
            workspace_id=self.workspace_id,
            customer=customer,
            fusion_run=fusion_run,
            ranking_version=version,
            top_n=values["top_n"],
            candidate_count=len(fusion_result["candidates"]),
            latency_ms=latency_ms,
            config_snapshot=config_snapshot,
            input_candidates=fusion_result["candidates"],
            ranked_candidates=candidates,
            user=self.user,
        )
        RecommendationFeedbackEvent.objects.bulk_create(
            [
                RecommendationFeedbackEvent(
                    workspace_id=self.workspace_id,
                    customer=customer,
                    campaign=campaigns.get(candidate["campaign_id"]),
                    ranking_run=run,
                    event_type=RecommendationFeedbackType.EXPOSED,
                    label=0,
                    source_type="RANKING_RUN",
                    source_id=str(run.id),
                    event_key=f"ranking:{run.id}:exposed:{candidate['campaign_id']}",
                    feature_snapshot={
                        row["feature"]: float(row.get("value") or 0)
                        for row in candidate.get("feature_details") or []
                        if row.get("feature") in RANKING_FEATURES
                    },
                    occurred_at=run.create_time,
                    user=self.user,
                )
                for candidate in candidates
                if campaigns.get(candidate["campaign_id"])
            ],
            ignore_conflicts=True,
        )
        from marketing.recommendation_events import publish_top_exposure

        publish_top_exposure(run, self.user)
        return {
            "ranking_run_id": str(run.id),
            "fusion_run_id": str(fusion_run.id),
            "ranking_version": version.version,
            "ranking_version_name": version.name,
            "customer": {"id": str(customer.id), "name": customer.name, "phone": customer.phone},
            "top_n": values["top_n"],
            "candidate_count": len(fusion_result["candidates"]),
            "fusion_latency_ms": fusion_result["latency_ms"],
            "ranking_latency_ms": latency_ms,
            "candidates": candidates,
        }

    def dashboard(self):
        self._default_version()
        versions = RecommendationRankingVersion.objects.filter(workspace_id=self.workspace_id)[:20]
        runs = RecommendationRankingRun.objects.filter(workspace_id=self.workspace_id).select_related(
            "customer", "fusion_run", "ranking_version"
        )[:20]
        published = next((row for row in versions if row.status == RecommendationRankingStatus.PUBLISHED), None)
        return {
            "summary": {
                "ranking_version_count": RecommendationRankingVersion.objects.filter(
                    workspace_id=self.workspace_id
                ).count(),
                "published_version": published.version if published else None,
                "ranking_run_count": RecommendationRankingRun.objects.filter(workspace_id=self.workspace_id).count(),
                "latest_latency_ms": runs[0].latency_ms if runs else None,
            },
            "feature_schema": ranking_feature_schema(),
            "versions": [serialize_ranking_version(row) for row in versions],
            "recent_runs": [serialize_ranking_run(row) for row in runs],
        }
