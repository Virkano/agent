# coding=utf-8
from collections import defaultdict

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from common.exception.app_exception import AppApiException
from marketing.models import (
    MarketingCampaign,
    MarketingConversionOutcome,
    MarketingConversionRecord,
    MarketingTouchExecution,
    MarketingTouchExecutionResult,
    RecommendationFeedbackEvent,
    RecommendationFeedbackType,
    RecommendationIncrementalRun,
    RecommendationIncrementalStatus,
    RecommendationRankingRun,
    RecommendationRankingVersion,
)
from marketing.serializers.recommendation_ranking import (
    DEFAULT_RANKING_WEIGHTS,
    RANKING_FEATURES,
    RecommendationRankingService,
    serialize_ranking_version,
)


FEEDBACK_LABELS = {
    RecommendationFeedbackType.EXPOSED: 0.0,
    RecommendationFeedbackType.CLICKED: 0.6,
    RecommendationFeedbackType.CONVERTED: 1.0,
    RecommendationFeedbackType.NEGATIVE: -1.0,
}


class RecommendationFeedbackSerializer(serializers.Serializer):
    ranking_run_id = serializers.UUIDField()
    campaign_id = serializers.UUIDField()
    event_type = serializers.ChoiceField(choices=RecommendationFeedbackType.choices)
    source_type = serializers.CharField(required=False, default="MANUAL", max_length=32)
    source_id = serializers.CharField(required=False, allow_blank=True, default="", max_length=64)
    event_key = serializers.CharField(required=False, allow_blank=True, default="", max_length=160)
    metadata = serializers.DictField(required=False, default=dict)
    occurred_at = serializers.DateTimeField(required=False, default=timezone.now)


class RecommendationIncrementalTrainSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True, max_length=128)
    base_ranking_version_id = serializers.UUIDField(required=False)
    learning_rate = serializers.FloatField(min_value=0.01, max_value=1, default=0.25)
    minimum_samples = serializers.IntegerField(min_value=2, max_value=10000, default=2)
    auto_publish = serializers.BooleanField(default=True)


def serialize_feedback_event(row):
    return {
        "id": str(row.id),
        "customer": {
            "id": str(row.customer_id) if row.customer_id else None,
            "name": row.customer.name if row.customer else "已删除客户",
        },
        "campaign": {
            "id": str(row.campaign_id) if row.campaign_id else None,
            "name": row.campaign.name if row.campaign else "已删除活动",
        },
        "ranking_run_id": str(row.ranking_run_id) if row.ranking_run_id else None,
        "event_type": row.event_type,
        "event_type_label": row.get_event_type_display(),
        "label": row.label,
        "source_type": row.source_type,
        "source_id": row.source_id,
        "feature_snapshot": row.feature_snapshot or {},
        "metadata": row.metadata or {},
        "occurred_at": row.occurred_at,
    }


def serialize_incremental_run(row):
    return {
        "id": str(row.id),
        "name": row.name,
        "status": row.status,
        "status_label": row.get_status_display(),
        "base_ranking_version": row.base_ranking_version.version if row.base_ranking_version else None,
        "generated_ranking_version": (row.generated_ranking_version.version if row.generated_ranking_version else None),
        "generated_status": row.generated_ranking_version.status if row.generated_ranking_version else None,
        "learning_rate": row.learning_rate,
        "sample_count": row.sample_count,
        "positive_count": row.positive_count,
        "negative_count": row.negative_count,
        "weight_delta": row.weight_delta or {},
        "metrics": row.metrics or {},
        "error_message": row.error_message,
        "started_at": row.started_at,
        "finished_at": row.finished_at,
        "create_time": row.create_time,
    }


class RecommendationIncrementalService:
    def __init__(self, workspace_id, user=None):
        self.workspace_id = workspace_id
        self.user = user

    @staticmethod
    def _feature_snapshot(candidate):
        return {
            row["feature"]: float(row.get("value") or 0)
            for row in candidate.get("feature_details") or []
            if row.get("feature") in RANKING_FEATURES
        }

    @staticmethod
    def _candidate(run, campaign_id):
        return next(
            (row for row in run.ranked_candidates or [] if str(row.get("campaign_id")) == str(campaign_id)),
            None,
        )

    def _create_event(
        self,
        *,
        run,
        campaign,
        event_type,
        source_type,
        source_id="",
        event_key="",
        metadata=None,
        occurred_at=None,
    ):
        if event_key:
            existing = RecommendationFeedbackEvent.objects.filter(
                workspace_id=self.workspace_id,
                event_key=event_key,
            ).first()
            if existing:
                return existing, False
        candidate = self._candidate(run, campaign.id)
        if candidate is None:
            raise AppApiException(400, "该活动不在指定精排运行结果中")
        event = RecommendationFeedbackEvent.objects.create(
            workspace_id=self.workspace_id,
            customer=run.customer,
            campaign=campaign,
            ranking_run=run,
            event_type=event_type,
            label=FEEDBACK_LABELS[event_type],
            source_type=source_type,
            source_id=source_id,
            event_key=event_key,
            feature_snapshot=self._feature_snapshot(candidate),
            metadata=metadata or {},
            occurred_at=occurred_at or timezone.now(),
            user=self.user,
        )
        return event, True

    @transaction.atomic
    def record_feedback(self, data):
        serializer = RecommendationFeedbackSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        run = (
            RecommendationRankingRun.objects.select_related("customer")
            .filter(
                workspace_id=self.workspace_id,
                id=values["ranking_run_id"],
            )
            .first()
        )
        if run is None:
            raise AppApiException(404, "精排运行不存在")
        campaign = MarketingCampaign.objects.filter(
            workspace_id=self.workspace_id,
            id=values["campaign_id"],
        ).first()
        if campaign is None:
            raise AppApiException(404, "营销活动不存在")
        event, created = self._create_event(
            run=run,
            campaign=campaign,
            event_type=values["event_type"],
            source_type=values["source_type"],
            source_id=values["source_id"],
            event_key=values["event_key"],
            metadata=values["metadata"],
            occurred_at=values["occurred_at"],
        )
        return {**serialize_feedback_event(event), "created": created}

    def _latest_run(self, customer_id, campaign_id=None):
        runs = RecommendationRankingRun.objects.filter(
            workspace_id=self.workspace_id,
            customer_id=customer_id,
        ).order_by("-create_time")
        for run in runs[:100]:
            if not campaign_id or self._candidate(run, campaign_id):
                return run
        return None

    @transaction.atomic
    def sync_business_feedback(self):
        created_counts = defaultdict(int)
        campaigns = {str(row.id): row for row in MarketingCampaign.objects.filter(workspace_id=self.workspace_id)}
        for run in RecommendationRankingRun.objects.filter(workspace_id=self.workspace_id).select_related("customer"):
            for candidate in run.ranked_candidates or []:
                campaign = campaigns.get(str(candidate.get("campaign_id")))
                if campaign is None:
                    continue
                _, created = self._create_event(
                    run=run,
                    campaign=campaign,
                    event_type=RecommendationFeedbackType.EXPOSED,
                    source_type="RANKING_RUN",
                    source_id=str(run.id),
                    event_key=f"ranking:{run.id}:exposed:{campaign.id}",
                    occurred_at=run.create_time,
                )
                created_counts[RecommendationFeedbackType.EXPOSED] += int(created)

        touch_mapping = {
            MarketingTouchExecutionResult.INTENT: RecommendationFeedbackType.CLICKED,
            MarketingTouchExecutionResult.REJECTED: RecommendationFeedbackType.NEGATIVE,
        }
        touches = MarketingTouchExecution.objects.filter(
            workspace_id=self.workspace_id,
            result__in=touch_mapping,
        ).order_by("create_time")
        for touch in touches:
            run = self._latest_run(touch.customer_id)
            if run is None or not run.ranked_candidates:
                continue
            campaign = campaigns.get(str(run.ranked_candidates[0].get("campaign_id")))
            if campaign is None:
                continue
            event_type = touch_mapping[touch.result]
            _, created = self._create_event(
                run=run,
                campaign=campaign,
                event_type=event_type,
                source_type="TOUCH_EXECUTION",
                source_id=str(touch.id),
                event_key=f"touch:{touch.id}:{event_type}",
                metadata={"touch_result": touch.result},
                occurred_at=touch.create_time,
            )
            created_counts[event_type] += int(created)

        conversions = MarketingConversionRecord.objects.filter(workspace_id=self.workspace_id).order_by("create_time")
        for conversion in conversions:
            matching_campaign = next(
                (
                    campaign
                    for campaign in campaigns.values()
                    if conversion.product_name
                    and (campaign.name in conversion.product_name or campaign.code in conversion.product_name)
                ),
                None,
            )
            run = self._latest_run(conversion.customer_id, matching_campaign.id if matching_campaign else None)
            if run is None or not run.ranked_candidates:
                continue
            campaign = matching_campaign or campaigns.get(str(run.ranked_candidates[0].get("campaign_id")))
            if campaign is None or self._candidate(run, campaign.id) is None:
                continue
            event_type = (
                RecommendationFeedbackType.CONVERTED
                if conversion.outcome == MarketingConversionOutcome.CONVERTED
                else RecommendationFeedbackType.NEGATIVE
            )
            _, created = self._create_event(
                run=run,
                campaign=campaign,
                event_type=event_type,
                source_type="CONVERSION_RECORD",
                source_id=str(conversion.id),
                event_key=f"conversion:{conversion.id}:{event_type}",
                metadata={"outcome": conversion.outcome, "product_name": conversion.product_name},
                occurred_at=conversion.create_time,
            )
            created_counts[event_type] += int(created)
        return {
            "created_count": sum(created_counts.values()),
            "created_by_type": {event: created_counts[event] for event in RecommendationFeedbackType.values},
            "total_event_count": RecommendationFeedbackEvent.objects.filter(workspace_id=self.workspace_id).count(),
        }

    def _resolve_base_version(self, version_id=None):
        ranking_service = RecommendationRankingService(self.workspace_id, self.user)
        return ranking_service._resolve_version(version_id)

    @staticmethod
    def _score(weights, features):
        total = sum(weights.values()) or 1
        return (
            sum(float(weights.get(feature) or 0) * float(features.get(feature) or 0) for feature in RANKING_FEATURES)
            / total
        )

    @classmethod
    def _pairwise_accuracy(cls, weights, positives, negatives):
        pairs = [(positive, negative) for positive in positives for negative in negatives]
        if not pairs:
            return 0.5
        wins = 0.0
        for positive, negative in pairs:
            left = cls._score(weights, positive.feature_snapshot or {})
            right = cls._score(weights, negative.feature_snapshot or {})
            wins += 1 if left > right else 0.5 if left == right else 0
        return round(wins / len(pairs), 6)

    def train(self, data):
        serializer = RecommendationIncrementalTrainSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        base_version = self._resolve_base_version(values.get("base_ranking_version_id"))
        now = timezone.now()
        run = RecommendationIncrementalRun.objects.create(
            workspace_id=self.workspace_id,
            name=values.get("name") or f"增量精排训练-v{base_version.version + 1}",
            status=RecommendationIncrementalStatus.RUNNING,
            base_ranking_version=base_version,
            learning_rate=values["learning_rate"],
            started_at=now,
            user=self.user,
        )
        samples = [
            row
            for row in (
                RecommendationFeedbackEvent.objects.filter(workspace_id=self.workspace_id)
                .exclude(label=0)
                .order_by("occurred_at")
            )
            if row.feature_snapshot
        ]
        positives = [row for row in samples if row.label > 0]
        negatives = [row for row in samples if row.label < 0]
        if len(samples) < values["minimum_samples"] or not positives or not negatives:
            message = "增量训练至少需要一条正反馈和一条负反馈，并满足最小样本数"
            run.status = RecommendationIncrementalStatus.FAILED
            run.sample_count = len(samples)
            run.positive_count = len(positives)
            run.negative_count = len(negatives)
            run.error_message = message
            run.finished_at = timezone.now()
            run.save()
            raise AppApiException(400, message)

        base_weights = {**DEFAULT_RANKING_WEIGHTS, **(base_version.feature_weights or {})}
        raw_weights = {}
        signal_by_feature = {}
        for feature in RANKING_FEATURES:
            positive_mean = sum(float(row.feature_snapshot.get(feature) or 0) * row.label for row in positives) / sum(
                row.label for row in positives
            )
            negative_mean = sum(float(row.feature_snapshot.get(feature) or 0) for row in negatives) / len(negatives)
            signal = positive_mean - negative_mean
            signal_by_feature[feature] = round(signal, 6)
            raw_weights[feature] = max(0.001, base_weights[feature] * (1 + values["learning_rate"] * signal))
        weight_total = sum(raw_weights.values())
        proposed_weights = {feature: raw_weights[feature] / weight_total for feature in RANKING_FEATURES}
        ranking_service = RecommendationRankingService(self.workspace_id, self.user)
        generated = ranking_service.create_version(
            {
                "name": f"{run.name}-策略",
                "feature_weights": proposed_weights,
                "auto_publish": False,
            }
        )
        generated_version = RecommendationRankingVersion.objects.get(id=generated["id"])
        learned_weights = {**DEFAULT_RANKING_WEIGHTS, **(generated_version.feature_weights or {})}
        weight_delta = {
            feature: round(learned_weights[feature] - base_weights[feature] / sum(base_weights.values()), 6)
            for feature in RANKING_FEATURES
        }
        base_accuracy = self._pairwise_accuracy(base_weights, positives, negatives)
        learned_accuracy = self._pairwise_accuracy(learned_weights, positives, negatives)
        should_publish = values["auto_publish"] and learned_accuracy >= base_accuracy
        metrics = {
            "baseline": "incremental_feedback_weighting_v1",
            "base_pairwise_accuracy": base_accuracy,
            "learned_pairwise_accuracy": learned_accuracy,
            "accuracy_delta": round(learned_accuracy - base_accuracy, 6),
            "feature_signals": signal_by_feature,
            "auto_publish_requested": values["auto_publish"],
            "published": should_publish,
        }
        generated_version.metrics = metrics
        generated_version.save(update_fields=["metrics", "update_time"])
        if should_publish:
            ranking_service.publish(str(generated_version.id))
            generated_version.refresh_from_db()

        run.status = RecommendationIncrementalStatus.SUCCESS
        run.generated_ranking_version = generated_version
        run.sample_count = len(samples)
        run.positive_count = len(positives)
        run.negative_count = len(negatives)
        run.event_snapshot = [
            {
                "event_id": str(row.id),
                "event_type": row.event_type,
                "label": row.label,
                "customer_id": str(row.customer_id) if row.customer_id else None,
                "campaign_id": str(row.campaign_id) if row.campaign_id else None,
                "feature_snapshot": row.feature_snapshot,
            }
            for row in samples
        ]
        run.weight_delta = weight_delta
        run.metrics = metrics
        run.finished_at = timezone.now()
        run.save()
        return {
            "run": serialize_incremental_run(run),
            "generated_version": serialize_ranking_version(generated_version),
        }

    def dashboard(self):
        events = RecommendationFeedbackEvent.objects.filter(workspace_id=self.workspace_id).select_related(
            "customer", "campaign", "ranking_run"
        )
        runs = RecommendationIncrementalRun.objects.filter(workspace_id=self.workspace_id).select_related(
            "base_ranking_version", "generated_ranking_version"
        )[:20]
        by_type = {event: events.filter(event_type=event).count() for event in RecommendationFeedbackType.values}
        return {
            "summary": {
                "feedback_count": events.count(),
                "labeled_sample_count": events.exclude(label=0).count(),
                "positive_count": events.filter(label__gt=0).count(),
                "negative_count": events.filter(label__lt=0).count(),
                "incremental_run_count": RecommendationIncrementalRun.objects.filter(
                    workspace_id=self.workspace_id
                ).count(),
                "latest_generated_version": runs[0].generated_ranking_version.version
                if runs and runs[0].generated_ranking_version
                else None,
            },
            "feedback_by_type": by_type,
            "event_types": [
                {"value": value, "label": label, "training_label": FEEDBACK_LABELS[value]}
                for value, label in RecommendationFeedbackType.choices
            ],
            "recent_events": [serialize_feedback_event(row) for row in events[:30]],
            "recent_runs": [serialize_incremental_run(row) for row in runs],
        }
