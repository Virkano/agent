# coding=utf-8
import math
import re
import time
from collections import defaultdict

from django.db import transaction
from rest_framework import serializers

from common.exception.app_exception import AppApiException
from marketing.models import (
    MarketingCampaign,
    MarketingCampaignApprovalStatus,
    MarketingCampaignStatus,
    MarketingConversionOutcome,
    MarketingConversionRecord,
    MarketingCustomer,
    RecommendationFusionConfig,
    RecommendationFusionRun,
    RecommendationInferenceLog,
    RecommendationModelStatus,
    RecommendationModelVersion,
)
from marketing.serializers.recommendation_engine import (
    RecommendationEngineService,
    _hash_vector,
    _item_payload,
    _matches_campaign,
    _normalise_token,
    _user_payload,
    _user_tokens,
)


RECALL_CHANNELS = ("TWO_TOWER", "RULE", "COLLABORATIVE", "CONTENT", "HOT", "REGION")
DEFAULT_FUSION_WEIGHTS = {
    "TWO_TOWER": 0.35,
    "RULE": 0.20,
    "COLLABORATIVE": 0.15,
    "CONTENT": 0.15,
    "HOT": 0.10,
    "REGION": 0.05,
}
CHANNEL_LABELS = {
    "TWO_TOWER": "双塔召回",
    "RULE": "业务规则",
    "COLLABORATIVE": "协同过滤",
    "CONTENT": "内容相似",
    "HOT": "全局热度",
    "REGION": "地域召回",
}


class RecommendationFusionConfigSerializer(serializers.Serializer):
    weights = serializers.DictField(child=serializers.FloatField(min_value=0, max_value=10))
    enabled_channels = serializers.ListField(
        child=serializers.ChoiceField(choices=RECALL_CHANNELS),
        min_length=1,
    )
    candidate_pool_size = serializers.IntegerField(min_value=5, max_value=200)

    def validate_enabled_channels(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("召回通道不能重复")
        return value

    def validate(self, attrs):
        unknown = set(attrs["weights"]) - set(RECALL_CHANNELS)
        if unknown:
            raise serializers.ValidationError({"weights": f"包含未知召回通道：{', '.join(sorted(unknown))}"})
        merged = {**DEFAULT_FUSION_WEIGHTS, **attrs["weights"]}
        if sum(merged[channel] for channel in attrs["enabled_channels"]) <= 0:
            raise serializers.ValidationError({"weights": "启用通道的权重之和必须大于 0"})
        attrs["weights"] = {channel: round(float(merged[channel]), 4) for channel in RECALL_CHANNELS}
        return attrs


class RecommendationFusionInferSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField()
    top_k = serializers.IntegerField(min_value=1, max_value=50, default=5)
    model_version_id = serializers.UUIDField(required=False)


def serialize_fusion_config(row):
    return {
        "weights": {**DEFAULT_FUSION_WEIGHTS, **(row.weights or {})},
        "enabled_channels": row.enabled_channels or list(RECALL_CHANNELS),
        "candidate_pool_size": row.candidate_pool_size,
        "channels": [{"value": channel, "label": CHANNEL_LABELS[channel]} for channel in RECALL_CHANNELS],
        "update_time": row.update_time,
    }


def serialize_fusion_run(row):
    return {
        "id": str(row.id),
        "customer": {
            "id": str(row.customer_id) if row.customer_id else None,
            "name": row.customer.name if row.customer else "已删除客户",
        },
        "model_version": row.model_version.version if row.model_version else None,
        "top_k": row.top_k,
        "latency_ms": row.latency_ms,
        "config_snapshot": row.config_snapshot or {},
        "fused_candidates": row.fused_candidates or [],
        "create_time": row.create_time,
    }


class RecommendationFusionService:
    def __init__(self, workspace_id, user=None):
        self.workspace_id = workspace_id
        self.user = user

    def _config(self):
        config, _ = RecommendationFusionConfig.objects.get_or_create(
            workspace_id=self.workspace_id,
            defaults={
                "weights": DEFAULT_FUSION_WEIGHTS,
                "enabled_channels": list(RECALL_CHANNELS),
                "candidate_pool_size": 50,
                "user": self.user,
            },
        )
        return config

    def get_config(self):
        return serialize_fusion_config(self._config())

    @transaction.atomic
    def save_config(self, data):
        serializer = RecommendationFusionConfigSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        config = self._config()
        config.weights = values["weights"]
        config.enabled_channels = values["enabled_channels"]
        config.candidate_pool_size = values["candidate_pool_size"]
        config.user = self.user
        config.save()
        return serialize_fusion_config(config)

    def _campaigns(self):
        return list(
            MarketingCampaign.objects.filter(
                workspace_id=self.workspace_id,
                status=MarketingCampaignStatus.ACTIVE,
                approval_status=MarketingCampaignApprovalStatus.APPROVED,
            ).order_by("priority", "name")
        )

    def _resolve_model(self, model_version_id=None):
        versions = RecommendationModelVersion.objects.filter(workspace_id=self.workspace_id)
        if model_version_id:
            model = versions.filter(id=model_version_id).first()
            if model is None:
                raise AppApiException(404, "推荐模型版本不存在")
            return model
        return versions.filter(status=RecommendationModelStatus.PUBLISHED).order_by("-version").first()

    @staticmethod
    def _channel_row(campaign, score, reason):
        return {
            "campaign_id": str(campaign.id),
            "campaign_name": campaign.name,
            "score": round(max(0.0, float(score)), 6),
            "reason": reason,
        }

    def _two_tower(self, customer, campaigns, model):
        if model is None:
            return []
        artifact = model.model_artifact or {}
        input_dim = int(artifact.get("input_dim") or 0)
        if not input_dim or not artifact.get("user_weight"):
            return []
        input_vector = _hash_vector(_user_tokens(_user_payload(customer)), input_dim)
        user_vector = RecommendationEngineService._project(input_vector, artifact["user_weight"])
        campaign_by_id = {str(row.id): row for row in campaigns}
        rows = []
        for embedding in model.item_embeddings.filter(campaign_id__in=campaign_by_id):
            campaign = campaign_by_id.get(str(embedding.campaign_id))
            if campaign is None:
                continue
            similarity = sum(left * right for left, right in zip(user_vector, embedding.vector, strict=True))
            score = 1 / (1 + math.exp(-similarity * 5))
            rows.append(self._channel_row(campaign, score, f"双塔向量相似度 {similarity:.3f}"))
        return rows

    def _rule(self, customer, campaigns):
        user_payload = _user_payload(customer)
        rows = []
        for campaign in campaigns:
            if _matches_campaign(user_payload, _item_payload(campaign)):
                score = 1 + 1 / (1 + max(0, campaign.priority))
                rows.append(self._channel_row(campaign, score, "地域、套餐与使用门槛均满足"))
        return rows

    @staticmethod
    def _text_tokens(value):
        normalised = _normalise_token(value)
        latin = set(re.findall(r"[a-z0-9]+", normalised))
        han = "".join(re.findall(r"[\u4e00-\u9fff]", normalised))
        return latin | {han[index : index + 2] for index in range(max(0, len(han) - 1))}

    def _content(self, customer, campaigns):
        user_text = f"{customer.province} {customer.current_plan} {customer.intent} {customer.remark}"
        user_tokens = self._text_tokens(user_text)
        rows = []
        for campaign in campaigns:
            item_text = " ".join(
                [campaign.name, campaign.code, campaign.benefit, campaign.description, *campaign.provinces, *campaign.plan_keywords]
            )
            item_tokens = self._text_tokens(item_text)
            union = user_tokens | item_tokens
            score = len(user_tokens & item_tokens) / len(union) if union else 0
            if score > 0:
                rows.append(self._channel_row(campaign, score, f"用户与物料文本命中 {len(user_tokens & item_tokens)} 个特征"))
        return rows

    def _region(self, customer, campaigns):
        rows = []
        for campaign in campaigns:
            if customer.province and customer.province in (campaign.provinces or []):
                rows.append(self._channel_row(campaign, 1, f"活动覆盖客户所在地域 {customer.province}"))
            elif not campaign.provinces:
                rows.append(self._channel_row(campaign, 0.45, "全国通用活动"))
        return rows

    def _hot(self, campaigns):
        scores = defaultdict(float)
        campaign_by_id = {str(row.id): row for row in campaigns}
        logs = RecommendationInferenceLog.objects.filter(workspace_id=self.workspace_id).order_by("-create_time")[:500]
        for log in logs:
            for candidate in log.candidates or []:
                campaign_id = str(candidate.get("campaign_id") or "")
                if campaign_id in campaign_by_id:
                    scores[campaign_id] += 1 + float(candidate.get("score") or 0)
        conversions = MarketingConversionRecord.objects.filter(
            workspace_id=self.workspace_id,
            outcome=MarketingConversionOutcome.CONVERTED,
        ).values_list("product_name", flat=True)
        for product_name in conversions:
            normalised = _normalise_token(product_name)
            for campaign_id, campaign in campaign_by_id.items():
                if normalised and (
                    _normalise_token(campaign.name) in normalised or _normalise_token(campaign.code) in normalised
                ):
                    scores[campaign_id] += 5
        return [
            self._channel_row(campaign_by_id[campaign_id], math.log1p(score), "历史曝光与转化热度")
            for campaign_id, score in scores.items()
            if score > 0
        ]

    @staticmethod
    def _profile_similarity(customer, peer):
        score = 0.0
        if customer.province and customer.province == peer.province:
            score += 0.5
        if customer.current_plan and customer.current_plan == peer.current_plan:
            score += 0.3
        if customer.intent and customer.intent == peer.intent:
            score += 0.2
        return score

    def _collaborative(self, customer, campaigns):
        campaign_by_id = {str(row.id): row for row in campaigns}
        peers = MarketingCustomer.objects.filter(workspace_id=self.workspace_id).exclude(id=customer.id)
        similarities = {str(peer.id): self._profile_similarity(customer, peer) for peer in peers}
        similarities = {peer_id: score for peer_id, score in similarities.items() if score > 0}
        if not similarities:
            return []
        scores = defaultdict(float)
        logs = RecommendationInferenceLog.objects.filter(
            workspace_id=self.workspace_id,
            customer_id__in=similarities,
        ).order_by("-create_time")[:500]
        for log in logs:
            similarity = similarities.get(str(log.customer_id), 0)
            for candidate in log.candidates or []:
                campaign_id = str(candidate.get("campaign_id") or "")
                if campaign_id in campaign_by_id:
                    scores[campaign_id] += similarity * float(candidate.get("score") or 0)
        return [
            self._channel_row(campaign_by_id[campaign_id], score, "相似客户的历史召回偏好")
            for campaign_id, score in scores.items()
            if score > 0
        ]

    @staticmethod
    def _normalise(rows):
        maximum = max((row["score"] for row in rows), default=0)
        if maximum <= 0:
            return {}
        return {row["campaign_id"]: {**row, "normalised_score": row["score"] / maximum} for row in rows}

    def _fuse(self, campaigns, channel_results, config, top_k):
        campaign_by_id = {str(row.id): row for row in campaigns}
        enabled = config.enabled_channels or list(RECALL_CHANNELS)
        weights = {**DEFAULT_FUSION_WEIGHTS, **(config.weights or {})}
        total_weight = sum(float(weights[channel]) for channel in enabled)
        normalised = {channel: self._normalise(channel_results.get(channel, [])) for channel in enabled}
        candidate_ids = set().union(*(set(rows) for rows in normalised.values())) if normalised else set()
        fused = []
        for campaign_id in candidate_ids:
            campaign = campaign_by_id.get(campaign_id)
            if campaign is None:
                continue
            source_details = []
            fused_score = 0.0
            for channel in enabled:
                row = normalised[channel].get(campaign_id)
                if row is None or row["normalised_score"] <= 0:
                    continue
                contribution = row["normalised_score"] * float(weights[channel]) / total_weight
                fused_score += contribution
                source_details.append(
                    {
                        "channel": channel,
                        "channel_label": CHANNEL_LABELS[channel],
                        "score": round(row["normalised_score"], 6),
                        "weight": round(float(weights[channel]), 4),
                        "contribution": round(contribution, 6),
                        "reason": row["reason"],
                    }
                )
            source_details.sort(key=lambda row: (-row["contribution"], row["channel"]))
            fused.append(
                {
                    "campaign_id": campaign_id,
                    "campaign_name": campaign.name,
                    "campaign_code": campaign.code,
                    "benefit": campaign.benefit,
                    "score": round(fused_score, 6),
                    "source_count": len(source_details),
                    "source_details": source_details,
                }
            )
        fused.sort(key=lambda row: (-row["score"], campaign_by_id[row["campaign_id"]].priority, row["campaign_name"]))
        return fused[:top_k]

    def infer(self, data):
        serializer = RecommendationFusionInferSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        customer = MarketingCustomer.objects.filter(
            workspace_id=self.workspace_id,
            id=values["customer_id"],
        ).first()
        if customer is None:
            raise AppApiException(404, "营销客户不存在")
        campaigns = self._campaigns()
        if not campaigns:
            raise AppApiException(400, "当前工作空间没有已上线且审批通过的营销活动")
        config = self._config()
        model = self._resolve_model(values.get("model_version_id"))
        started = time.perf_counter()
        channel_results = {
            "TWO_TOWER": self._two_tower(customer, campaigns, model),
            "RULE": self._rule(customer, campaigns),
            "COLLABORATIVE": self._collaborative(customer, campaigns),
            "CONTENT": self._content(customer, campaigns),
            "HOT": self._hot(campaigns),
            "REGION": self._region(customer, campaigns),
        }
        pool_size = config.candidate_pool_size
        for channel, rows in channel_results.items():
            rows.sort(key=lambda row: (-row["score"], row["campaign_name"]))
            channel_results[channel] = rows[:pool_size]
        candidates = self._fuse(campaigns, channel_results, config, values["top_k"])
        latency_ms = max(1, round((time.perf_counter() - started) * 1000))
        config_snapshot = {
            "weights": {**DEFAULT_FUSION_WEIGHTS, **(config.weights or {})},
            "enabled_channels": config.enabled_channels or list(RECALL_CHANNELS),
            "candidate_pool_size": config.candidate_pool_size,
        }
        run = RecommendationFusionRun.objects.create(
            workspace_id=self.workspace_id,
            customer=customer,
            model_version=model,
            top_k=values["top_k"],
            latency_ms=latency_ms,
            config_snapshot=config_snapshot,
            channel_results=channel_results,
            fused_candidates=candidates,
            user=self.user,
        )
        return {
            "fusion_run_id": str(run.id),
            "model_version": model.version if model else None,
            "customer": {"id": str(customer.id), "name": customer.name, "phone": customer.phone},
            "top_k": values["top_k"],
            "latency_ms": latency_ms,
            "channel_counts": {channel: len(rows) for channel, rows in channel_results.items()},
            "candidates": candidates,
        }

    def dashboard(self):
        runs = RecommendationFusionRun.objects.filter(workspace_id=self.workspace_id).select_related(
            "customer", "model_version"
        )[:20]
        return {
            "config": self.get_config(),
            "summary": {
                "fusion_run_count": RecommendationFusionRun.objects.filter(workspace_id=self.workspace_id).count(),
                "active_channel_count": len(self._config().enabled_channels or RECALL_CHANNELS),
                "latest_latency_ms": runs[0].latency_ms if runs else None,
            },
            "recent_runs": [serialize_fusion_run(row) for row in runs],
        }
