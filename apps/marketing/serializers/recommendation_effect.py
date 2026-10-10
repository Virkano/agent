# coding=utf-8
import math
from collections import defaultdict
from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from marketing.models import (
    MarketingCampaign,
    MarketingCampaignApprovalStatus,
    MarketingCampaignStatus,
    RecommendationFeedbackEvent,
    RecommendationFeedbackType,
    RecommendationRankingRun,
    RecommendationRankingStatus,
)


EVENT_COUNTER_FIELDS = {
    RecommendationFeedbackType.EXPOSED: "exposure_count",
    RecommendationFeedbackType.CLICKED: "click_count",
    RecommendationFeedbackType.CONVERTED: "conversion_count",
    RecommendationFeedbackType.NEGATIVE: "negative_count",
}


class RecommendationEffectQuerySerializer(serializers.Serializer):
    days = serializers.ChoiceField(choices=(7, 30, 90), default=30)


def _rate(numerator, denominator):
    return round(numerator / denominator, 6) if denominator else 0.0


def _average(values):
    return round(sum(values) / len(values), 3) if values else 0.0


def _percentile(values, percentile):
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, math.ceil(len(ordered) * percentile) - 1)
    return round(float(ordered[index]), 3)


class RecommendationEffectService:
    def __init__(self, workspace_id):
        self.workspace_id = workspace_id

    @staticmethod
    def _campaign_tags(campaign):
        if campaign is None:
            return set()
        return {
            *{f"province:{value}" for value in campaign.provinces or []},
            *{f"plan:{value}" for value in campaign.plan_keywords or []},
        }

    @classmethod
    def _run_diversity(cls, run, campaigns):
        candidate_ids = [str(row.get("campaign_id")) for row in run.ranked_candidates or []]
        tag_sets = [cls._campaign_tags(campaigns.get(campaign_id)) for campaign_id in candidate_ids]
        pairs = [(left, right) for index, left in enumerate(tag_sets) for right in tag_sets[index + 1 :]]
        if not pairs:
            return 0.0
        distances = []
        for left, right in pairs:
            union = left | right
            distances.append(1 - len(left & right) / len(union) if union else 0.0)
        return _average(distances)

    @staticmethod
    def _event_counts(events):
        counts = {event_type: 0 for event_type in RecommendationFeedbackType.values}
        for event in events:
            counts[event.event_type] += 1
        return counts

    def dashboard(self, query_params):
        serializer = RecommendationEffectQuerySerializer(data=query_params)
        serializer.is_valid(raise_exception=True)
        days = int(serializer.validated_data["days"])
        now = timezone.now()
        start_at = now - timedelta(days=days)
        events = list(
            RecommendationFeedbackEvent.objects.filter(
                workspace_id=self.workspace_id,
                occurred_at__gte=start_at,
            ).select_related("campaign", "customer", "ranking_run__ranking_version")
        )
        runs = list(
            RecommendationRankingRun.objects.filter(
                workspace_id=self.workspace_id,
                create_time__gte=start_at,
            ).select_related("ranking_version", "fusion_run")
        )
        campaigns = {str(row.id): row for row in MarketingCampaign.objects.filter(workspace_id=self.workspace_id)}
        active_campaign_count = MarketingCampaign.objects.filter(
            workspace_id=self.workspace_id,
            status=MarketingCampaignStatus.ACTIVE,
            approval_status=MarketingCampaignApprovalStatus.APPROVED,
        ).count()
        counts = self._event_counts(events)
        exposure_count = counts[RecommendationFeedbackType.EXPOSED]
        click_count = counts[RecommendationFeedbackType.CLICKED]
        conversion_count = counts[RecommendationFeedbackType.CONVERTED]
        negative_count = counts[RecommendationFeedbackType.NEGATIVE]
        exposed_campaign_ids = {
            str(event.campaign_id)
            for event in events
            if event.event_type == RecommendationFeedbackType.EXPOSED and event.campaign_id
        }
        run_diversities = [self._run_diversity(run, campaigns) for run in runs if run.ranked_candidates]
        ranking_latencies = [run.latency_ms for run in runs]
        fusion_latencies = [run.fusion_run.latency_ms if run.fusion_run else 0 for run in runs]
        total_latencies = [
            ranking + fusion for ranking, fusion in zip(ranking_latencies, fusion_latencies, strict=True)
        ]

        daily = {}
        today = timezone.localdate()
        for offset in range(days - 1, -1, -1):
            date = today - timedelta(days=offset)
            daily[date.isoformat()] = {
                "date": date.isoformat(),
                "exposure_count": 0,
                "click_count": 0,
                "conversion_count": 0,
                "negative_count": 0,
            }
        for event in events:
            date_key = timezone.localtime(event.occurred_at).date().isoformat()
            row = daily.get(date_key)
            if row is None:
                continue
            row[EVENT_COUNTER_FIELDS[event.event_type]] += 1
        trend = []
        for row in daily.values():
            row["ctr"] = _rate(row["click_count"], row["exposure_count"])
            row["cvr"] = _rate(row["conversion_count"], row["exposure_count"])
            trend.append(row)

        version_groups = defaultdict(
            lambda: {
                "run_count": 0,
                "ranking_latencies": [],
                "total_latencies": [],
                "diversities": [],
                "events": [],
            }
        )
        for run in runs:
            version_key = str(run.ranking_version_id) if run.ranking_version_id else "unversioned"
            group = version_groups[version_key]
            group["version"] = run.ranking_version.version if run.ranking_version else None
            group["name"] = run.ranking_version.name if run.ranking_version else "未绑定版本"
            group["status"] = run.ranking_version.status if run.ranking_version else None
            group["run_count"] += 1
            group["ranking_latencies"].append(run.latency_ms)
            group["total_latencies"].append(run.latency_ms + (run.fusion_run.latency_ms if run.fusion_run else 0))
            group["diversities"].append(self._run_diversity(run, campaigns))
        for event in events:
            version_key = (
                str(event.ranking_run.ranking_version_id)
                if event.ranking_run and event.ranking_run.ranking_version_id
                else "unversioned"
            )
            version_groups[version_key]["events"].append(event)

        version_performance = []
        for group in version_groups.values():
            group_counts = self._event_counts(group["events"])
            group_exposures = group_counts[RecommendationFeedbackType.EXPOSED]
            group_campaigns = {
                str(event.campaign_id)
                for event in group["events"]
                if event.event_type == RecommendationFeedbackType.EXPOSED and event.campaign_id
            }
            version_performance.append(
                {
                    "version": group.get("version"),
                    "name": group.get("name", "未绑定版本"),
                    "status": group.get("status"),
                    "is_published": group.get("status") == RecommendationRankingStatus.PUBLISHED,
                    "run_count": group["run_count"],
                    "exposure_count": group_exposures,
                    "click_count": group_counts[RecommendationFeedbackType.CLICKED],
                    "conversion_count": group_counts[RecommendationFeedbackType.CONVERTED],
                    "negative_count": group_counts[RecommendationFeedbackType.NEGATIVE],
                    "ctr": _rate(group_counts[RecommendationFeedbackType.CLICKED], group_exposures),
                    "cvr": _rate(group_counts[RecommendationFeedbackType.CONVERTED], group_exposures),
                    "negative_rate": _rate(group_counts[RecommendationFeedbackType.NEGATIVE], group_exposures),
                    "coverage_rate": _rate(len(group_campaigns), active_campaign_count),
                    "diversity_score": _average(group["diversities"]),
                    "ranking_avg_ms": _average(group["ranking_latencies"]),
                    "total_avg_ms": _average(group["total_latencies"]),
                }
            )
        version_performance.sort(key=lambda row: row["version"] or 0, reverse=True)

        campaign_groups = defaultdict(list)
        for event in events:
            if event.campaign_id:
                campaign_groups[str(event.campaign_id)].append(event)
        campaign_performance = []
        for campaign_id, campaign_events in campaign_groups.items():
            campaign = campaigns.get(campaign_id)
            campaign_counts = self._event_counts(campaign_events)
            campaign_exposures = campaign_counts[RecommendationFeedbackType.EXPOSED]
            campaign_performance.append(
                {
                    "campaign_id": campaign_id,
                    "campaign_name": campaign.name if campaign else "已删除活动",
                    "exposure_count": campaign_exposures,
                    "click_count": campaign_counts[RecommendationFeedbackType.CLICKED],
                    "conversion_count": campaign_counts[RecommendationFeedbackType.CONVERTED],
                    "negative_count": campaign_counts[RecommendationFeedbackType.NEGATIVE],
                    "ctr": _rate(campaign_counts[RecommendationFeedbackType.CLICKED], campaign_exposures),
                    "cvr": _rate(campaign_counts[RecommendationFeedbackType.CONVERTED], campaign_exposures),
                }
            )
        campaign_performance.sort(
            key=lambda row: (
                -row["conversion_count"],
                -row["click_count"],
                -row["exposure_count"],
                row["campaign_name"],
            )
        )

        return {
            "period": {"days": days, "start_at": start_at, "end_at": now},
            "summary": {
                "exposure_count": exposure_count,
                "click_count": click_count,
                "conversion_count": conversion_count,
                "negative_count": negative_count,
                "ctr": _rate(click_count, exposure_count),
                "cvr": _rate(conversion_count, exposure_count),
                "negative_rate": _rate(negative_count, exposure_count),
                "coverage_rate": _rate(len(exposed_campaign_ids), active_campaign_count),
                "diversity_score": _average(run_diversities),
                "unique_customer_count": len({event.customer_id for event in events if event.customer_id}),
                "active_campaign_count": active_campaign_count,
                "ranking_run_count": len(runs),
            },
            "latency": {
                "ranking_avg_ms": _average(ranking_latencies),
                "fusion_avg_ms": _average(fusion_latencies),
                "total_avg_ms": _average(total_latencies),
                "p95_total_ms": _percentile(total_latencies, 0.95),
            },
            "funnel": [
                {"stage": "EXPOSED", "label": "曝光", "count": exposure_count},
                {"stage": "CLICKED", "label": "点击", "count": click_count},
                {"stage": "CONVERTED", "label": "转化", "count": conversion_count},
                {"stage": "NEGATIVE", "label": "负反馈", "count": negative_count},
            ],
            "daily_trend": trend,
            "version_performance": version_performance,
            "campaign_performance": campaign_performance[:20],
        }
