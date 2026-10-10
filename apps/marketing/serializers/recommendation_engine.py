# coding=utf-8
import hashlib
import math
import re
import time

from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from rest_framework import serializers

from common.exception.app_exception import AppApiException
from marketing.models import (
    MarketingCampaign,
    MarketingCampaignApprovalStatus,
    MarketingCampaignStatus,
    MarketingCustomer,
    RecommendationFeatureSnapshot,
    RecommendationFeatureType,
    RecommendationInferenceLog,
    RecommendationItemEmbedding,
    RecommendationModelStatus,
    RecommendationModelVersion,
    RecommendationTrainingRun,
    RecommendationTrainingStatus,
)


class RecommendationFeatureBuildSerializer(serializers.Serializer):
    input_dim = serializers.IntegerField(min_value=16, max_value=512, default=64)


class RecommendationTrainSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True, max_length=128)
    snapshot_version = serializers.IntegerField(required=False, min_value=1)
    embedding_dim = serializers.IntegerField(min_value=4, max_value=64, default=16)
    epochs = serializers.IntegerField(min_value=1, max_value=300, default=40)
    learning_rate = serializers.FloatField(min_value=0.0001, max_value=1, default=0.03)
    auto_publish = serializers.BooleanField(default=True)


class RecommendationInferSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField()
    top_k = serializers.IntegerField(min_value=1, max_value=50, default=5)
    model_version_id = serializers.UUIDField(required=False)


def _to_number(value):
    matched = re.search(r"\d+(?:\.\d+)?", str(value or ""))
    return float(matched.group()) if matched else 0.0


def _normalise_token(value):
    return re.sub(r"\s+", "", str(value or "").strip().lower())


def _hash_vector(tokens, input_dim):
    vector = [0.0] * input_dim
    for token in sorted(set(filter(None, tokens))):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % input_dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [round(value / norm, 8) for value in vector]


def _user_payload(customer):
    return {
        "customer_id": str(customer.id),
        "task_id": str(customer.task_id),
        "province": customer.province,
        "current_plan": customer.current_plan,
        "monthly_data_usage": _to_number(customer.monthly_data_usage),
        "monthly_call_usage": _to_number(customer.monthly_call_usage),
        "status": customer.status,
        "intent": customer.intent,
    }


def _user_tokens(payload):
    data_usage = float(payload.get("monthly_data_usage") or 0)
    call_usage = float(payload.get("monthly_call_usage") or 0)
    return [
        f"province:{_normalise_token(payload.get('province'))}",
        f"plan:{_normalise_token(payload.get('current_plan'))}",
        f"data_bucket:{int(data_usage // 10)}",
        f"call_bucket:{int(call_usage // 100)}",
        f"status:{payload.get('status') or ''}",
        f"intent:{_normalise_token(payload.get('intent'))}",
        "bias:user",
    ]


def _item_payload(campaign):
    return {
        "campaign_id": str(campaign.id),
        "campaign_version": campaign.version,
        "code": campaign.code,
        "name": campaign.name,
        "provinces": campaign.provinces or [],
        "plan_keywords": campaign.plan_keywords or [],
        "min_data_usage_gb": campaign.min_data_usage_gb,
        "min_call_usage_minutes": campaign.min_call_usage_minutes,
        "priority": campaign.priority,
        "benefit": campaign.benefit,
        "description": campaign.description,
    }


def _item_tokens(payload):
    tokens = [
        f"code:{_normalise_token(payload.get('code'))}",
        f"priority_bucket:{int((payload.get('priority') or 0) // 100)}",
        f"data_bucket:{int((payload.get('min_data_usage_gb') or 0) // 10)}",
        f"call_bucket:{int((payload.get('min_call_usage_minutes') or 0) // 100)}",
        "bias:item",
    ]
    tokens.extend(f"province:{_normalise_token(value)}" for value in payload.get("provinces") or [])
    tokens.extend(f"plan:{_normalise_token(value)}" for value in payload.get("plan_keywords") or [])
    text = _normalise_token(f"{payload.get('name', '')}{payload.get('benefit', '')}{payload.get('description', '')}")
    tokens.extend(f"text:{text[index:index + 2]}" for index in range(max(0, len(text) - 1)))
    return tokens


def _matches_campaign(user_payload, item_payload):
    province = str(user_payload.get("province") or "")
    current_plan = str(user_payload.get("current_plan") or "")
    provinces = [str(value) for value in item_payload.get("provinces") or []]
    plan_keywords = [str(value) for value in item_payload.get("plan_keywords") or []]
    if provinces and province not in provinces:
        return False
    if plan_keywords and not any(keyword in current_plan for keyword in plan_keywords):
        return False
    if float(user_payload.get("monthly_data_usage") or 0) < float(item_payload.get("min_data_usage_gb") or 0):
        return False
    return float(user_payload.get("monthly_call_usage") or 0) >= float(
        item_payload.get("min_call_usage_minutes") or 0
    )


def _round_vector(vector):
    return [round(float(value), 8) for value in vector]


def serialize_training_run(row):
    return {
        "id": str(row.id),
        "name": row.name,
        "snapshot_version": row.snapshot_version,
        "status": row.status,
        "status_label": row.get_status_display(),
        "input_dim": row.input_dim,
        "embedding_dim": row.embedding_dim,
        "epochs": row.epochs,
        "learning_rate": row.learning_rate,
        "user_count": row.user_count,
        "item_count": row.item_count,
        "sample_count": row.sample_count,
        "positive_count": row.positive_count,
        "initial_loss": row.initial_loss,
        "final_loss": row.final_loss,
        "metrics": row.metrics or {},
        "error_message": row.error_message,
        "started_at": row.started_at,
        "finished_at": row.finished_at,
        "create_time": row.create_time,
    }


def serialize_model_version(row):
    return {
        "id": str(row.id),
        "version": row.version,
        "name": row.name,
        "status": row.status,
        "status_label": row.get_status_display(),
        "training_run_id": str(row.training_run_id),
        "snapshot_version": row.snapshot_version,
        "embedding_dim": row.embedding_dim,
        "metrics": row.metrics or {},
        "published_at": row.published_at,
        "item_embedding_count": getattr(row, "item_embedding_count", None) or row.item_embeddings.count(),
        "create_time": row.create_time,
    }


class RecommendationEngineService:
    def __init__(self, workspace_id, user=None):
        self.workspace_id = workspace_id
        self.user = user

    def _customers(self):
        return MarketingCustomer.objects.filter(workspace_id=self.workspace_id).select_related("task")

    def _campaigns(self):
        return MarketingCampaign.objects.filter(
            workspace_id=self.workspace_id,
            status=MarketingCampaignStatus.ACTIVE,
            approval_status=MarketingCampaignApprovalStatus.APPROVED,
        ).order_by("priority", "name")

    def build_feature_snapshot(self, data=None):
        serializer = RecommendationFeatureBuildSerializer(data=data or {})
        serializer.is_valid(raise_exception=True)
        input_dim = serializer.validated_data["input_dim"]
        customers = list(self._customers())
        campaigns = list(self._campaigns())
        if not customers:
            raise AppApiException(400, "当前工作空间没有营销客户，无法生成用户特征")
        if not campaigns:
            raise AppApiException(400, "当前工作空间没有已上线且审批通过的营销活动，无法生成物料特征")
        snapshot_version = (
            RecommendationFeatureSnapshot.objects.filter(workspace_id=self.workspace_id).aggregate(
                maximum=Max("snapshot_version")
            )["maximum"]
            or 0
        ) + 1
        rows = []
        for customer in customers:
            payload = _user_payload(customer)
            rows.append(
                RecommendationFeatureSnapshot(
                    workspace_id=self.workspace_id,
                    snapshot_version=snapshot_version,
                    feature_type=RecommendationFeatureType.USER,
                    source_id=str(customer.id),
                    source_name=customer.name or customer.phone or str(customer.id),
                    feature_payload=payload,
                    input_vector=_hash_vector(_user_tokens(payload), input_dim),
                    user=self.user,
                )
            )
        for campaign in campaigns:
            payload = _item_payload(campaign)
            rows.append(
                RecommendationFeatureSnapshot(
                    workspace_id=self.workspace_id,
                    snapshot_version=snapshot_version,
                    feature_type=RecommendationFeatureType.ITEM,
                    source_id=str(campaign.id),
                    source_name=campaign.name,
                    feature_payload=payload,
                    input_vector=_hash_vector(_item_tokens(payload), input_dim),
                    user=self.user,
                )
            )
        RecommendationFeatureSnapshot.objects.bulk_create(rows)
        return {
            "snapshot_version": snapshot_version,
            "input_dim": input_dim,
            "user_count": len(customers),
            "item_count": len(campaigns),
            "feature_count": len(rows),
        }

    def _snapshot_rows(self, snapshot_version):
        rows = RecommendationFeatureSnapshot.objects.filter(
            workspace_id=self.workspace_id,
            snapshot_version=snapshot_version,
        )
        users = list(rows.filter(feature_type=RecommendationFeatureType.USER).order_by("source_id"))
        items = list(rows.filter(feature_type=RecommendationFeatureType.ITEM).order_by("source_id"))
        if not users or not items:
            raise AppApiException(400, "特征快照缺少用户或物料数据")
        input_dim = len(users[0].input_vector)
        if input_dim == 0 or any(len(row.input_vector) != input_dim for row in [*users, *items]):
            raise AppApiException(400, "特征快照向量维度不一致")
        return users, items, input_dim

    def train(self, data):
        serializer = RecommendationTrainSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        snapshot_version = values.get("snapshot_version")
        if snapshot_version is None:
            snapshot_version = RecommendationFeatureSnapshot.objects.filter(workspace_id=self.workspace_id).aggregate(
                maximum=Max("snapshot_version")
            )["maximum"]
        if snapshot_version is None:
            snapshot_version = self.build_feature_snapshot({})["snapshot_version"]
        users, items, input_dim = self._snapshot_rows(snapshot_version)
        run = RecommendationTrainingRun.objects.create(
            workspace_id=self.workspace_id,
            name=values.get("name") or f"双塔基线训练-v{snapshot_version}",
            snapshot_version=snapshot_version,
            status=RecommendationTrainingStatus.RUNNING,
            input_dim=input_dim,
            embedding_dim=values["embedding_dim"],
            epochs=values["epochs"],
            learning_rate=values["learning_rate"],
            user_count=len(users),
            item_count=len(items),
            sample_count=len(users) * len(items),
            started_at=timezone.now(),
            user=self.user,
        )
        try:
            artifact, metrics, item_vectors = self._fit_two_tower(run, users, items)
            with transaction.atomic():
                version_number = (
                    RecommendationModelVersion.objects.filter(workspace_id=self.workspace_id).aggregate(
                        maximum=Max("version")
                    )["maximum"]
                    or 0
                ) + 1
                run.status = RecommendationTrainingStatus.SUCCESS
                run.initial_loss = metrics["initial_loss"]
                run.final_loss = metrics["final_loss"]
                run.positive_count = metrics["positive_count"]
                run.metrics = metrics
                run.model_artifact = artifact
                run.finished_at = timezone.now()
                run.save()
                model_version = RecommendationModelVersion.objects.create(
                    workspace_id=self.workspace_id,
                    version=version_number,
                    name=run.name,
                    training_run=run,
                    snapshot_version=snapshot_version,
                    embedding_dim=run.embedding_dim,
                    metrics=metrics,
                    model_artifact=artifact,
                    user=self.user,
                )
                item_by_id = {row.source_id: row for row in items}
                campaigns = {str(row.id): row for row in self._campaigns().filter(id__in=item_by_id)}
                embedding_rows = []
                for source_id, vector in item_vectors.items():
                    if source_id not in campaigns:
                        continue
                    embedding_rows.append(
                        RecommendationItemEmbedding(
                            workspace_id=self.workspace_id,
                            model_version=model_version,
                            campaign=campaigns[source_id],
                            feature_snapshot=item_by_id[source_id],
                            vector=vector,
                            vector_norm=round(math.sqrt(sum(value * value for value in vector)), 8),
                        )
                    )
                RecommendationItemEmbedding.objects.bulk_create(embedding_rows)
                if values["auto_publish"]:
                    self._publish_locked(model_version)
            return {
                "training_run": serialize_training_run(run),
                "model_version": serialize_model_version(model_version),
            }
        except AppApiException:
            raise
        except Exception as exc:
            run.status = RecommendationTrainingStatus.FAILED
            run.error_message = str(exc)[:2000]
            run.finished_at = timezone.now()
            run.save(update_fields=["status", "error_message", "finished_at", "update_time"])
            raise AppApiException(500, f"双塔训练失败：{exc}")

    @staticmethod
    def _fit_two_tower(run, users, items):
        import torch
        from torch import nn
        from torch.nn import functional as functional

        torch.manual_seed(20260912)
        user_inputs = torch.tensor([row.input_vector for row in users], dtype=torch.float32)
        item_inputs = torch.tensor([row.input_vector for row in items], dtype=torch.float32)
        pair_users = []
        pair_items = []
        labels = []
        for user_index, user_row in enumerate(users):
            for item_index, item_row in enumerate(items):
                pair_users.append(user_index)
                pair_items.append(item_index)
                labels.append(float(_matches_campaign(user_row.feature_payload, item_row.feature_payload)))
        pair_users_tensor = torch.tensor(pair_users, dtype=torch.long)
        pair_items_tensor = torch.tensor(pair_items, dtype=torch.long)
        labels_tensor = torch.tensor(labels, dtype=torch.float32)
        user_tower = nn.Linear(run.input_dim, run.embedding_dim, bias=False)
        item_tower = nn.Linear(run.input_dim, run.embedding_dim, bias=False)
        optimiser = torch.optim.Adam([*user_tower.parameters(), *item_tower.parameters()], lr=run.learning_rate)
        loss_function = nn.BCEWithLogitsLoss()
        initial_loss = None
        final_loss = None
        for _ in range(run.epochs):
            optimiser.zero_grad()
            user_vectors = functional.normalize(user_tower(user_inputs), dim=1)
            item_vectors = functional.normalize(item_tower(item_inputs), dim=1)
            logits = (user_vectors[pair_users_tensor] * item_vectors[pair_items_tensor]).sum(dim=1) * 5
            loss = loss_function(logits, labels_tensor)
            if initial_loss is None:
                initial_loss = float(loss.detach())
            loss.backward()
            optimiser.step()
            final_loss = float(loss.detach())
        with torch.no_grad():
            trained_users = functional.normalize(user_tower(user_inputs), dim=1)
            trained_items = functional.normalize(item_tower(item_inputs), dim=1)
            logits = (trained_users[pair_users_tensor] * trained_items[pair_items_tensor]).sum(dim=1) * 5
            probabilities = torch.sigmoid(logits)
            predictions = (probabilities >= 0.5).float()
            accuracy = float((predictions == labels_tensor).float().mean())
        artifact = {
            "algorithm": "hashed-linear-two-tower-v1",
            "input_dim": run.input_dim,
            "embedding_dim": run.embedding_dim,
            "user_weight": [_round_vector(row) for row in user_tower.weight.detach().tolist()],
            "item_weight": [_round_vector(row) for row in item_tower.weight.detach().tolist()],
        }
        metrics = {
            "initial_loss": round(initial_loss or 0, 6),
            "final_loss": round(final_loss or 0, 6),
            "loss_reduction": round((initial_loss or 0) - (final_loss or 0), 6),
            "accuracy": round(accuracy, 6),
            "positive_count": int(sum(labels)),
            "positive_rate": round(sum(labels) / len(labels), 6) if labels else 0,
        }
        vectors = {
            item.source_id: _round_vector(trained_items[index].tolist()) for index, item in enumerate(items)
        }
        return artifact, metrics, vectors

    def _publish_locked(self, model_version):
        RecommendationModelVersion.objects.filter(
            workspace_id=self.workspace_id,
            status=RecommendationModelStatus.PUBLISHED,
        ).exclude(id=model_version.id).update(status=RecommendationModelStatus.ARCHIVED)
        model_version.status = RecommendationModelStatus.PUBLISHED
        model_version.published_at = timezone.now()
        model_version.save(update_fields=["status", "published_at", "update_time"])

    @transaction.atomic
    def publish(self, model_version_id):
        model_version = RecommendationModelVersion.objects.select_for_update().filter(
            workspace_id=self.workspace_id,
            id=model_version_id,
        ).first()
        if model_version is None:
            raise AppApiException(404, "推荐模型版本不存在")
        self._publish_locked(model_version)
        return serialize_model_version(model_version)

    def recommend(self, data):
        serializer = RecommendationInferSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        customer = self._customers().filter(id=values["customer_id"]).first()
        if customer is None:
            raise AppApiException(404, "营销客户不存在")
        versions = RecommendationModelVersion.objects.filter(workspace_id=self.workspace_id)
        model_version_id = values.get("model_version_id")
        if model_version_id:
            model_version = versions.filter(id=model_version_id).first()
        else:
            model_version = versions.filter(status=RecommendationModelStatus.PUBLISHED).order_by("-version").first()
        if model_version is None:
            raise AppApiException(400, "尚未发布双塔模型，请先完成训练并发布")
        started = time.perf_counter()
        payload = _user_payload(customer)
        artifact = model_version.model_artifact or {}
        input_dim = int(artifact.get("input_dim") or 0)
        if not input_dim or not artifact.get("user_weight"):
            raise AppApiException(400, "模型产物不完整，无法推理")
        input_vector = _hash_vector(_user_tokens(payload), input_dim)
        user_vector = self._project(input_vector, artifact["user_weight"])
        candidates = []
        embeddings = model_version.item_embeddings.select_related("campaign").filter(
            campaign__status=MarketingCampaignStatus.ACTIVE,
            campaign__approval_status=MarketingCampaignApprovalStatus.APPROVED,
        )
        for embedding in embeddings:
            similarity = sum(left * right for left, right in zip(user_vector, embedding.vector, strict=True))
            score = 1 / (1 + math.exp(-similarity * 5))
            candidates.append(
                {
                    "campaign_id": str(embedding.campaign_id),
                    "campaign_name": embedding.campaign.name,
                    "campaign_code": embedding.campaign.code,
                    "score": round(score, 6),
                    "similarity": round(similarity, 6),
                    "benefit": embedding.campaign.benefit,
                    "reasons": self._explain(customer, embedding.campaign),
                }
            )
        candidates.sort(key=lambda row: (-row["score"], row["campaign_name"]))
        candidates = candidates[: values["top_k"]]
        latency_ms = max(1, round((time.perf_counter() - started) * 1000))
        inference = RecommendationInferenceLog.objects.create(
            workspace_id=self.workspace_id,
            model_version=model_version,
            customer=customer,
            top_k=values["top_k"],
            latency_ms=latency_ms,
            user_snapshot=payload,
            candidates=candidates,
            user=self.user,
        )
        return {
            "inference_id": str(inference.id),
            "model_version": model_version.version,
            "customer": {"id": str(customer.id), "name": customer.name, "phone": customer.phone},
            "top_k": values["top_k"],
            "latency_ms": latency_ms,
            "candidates": candidates,
        }

    @staticmethod
    def _project(input_vector, weight):
        output = [sum(value * row[index] for index, value in enumerate(input_vector)) for row in weight]
        norm = math.sqrt(sum(value * value for value in output)) or 1.0
        return [value / norm for value in output]

    @staticmethod
    def _explain(customer, campaign):
        reasons = []
        if not campaign.provinces or customer.province in campaign.provinces:
            reasons.append("地域条件匹配")
        if not campaign.plan_keywords or any(keyword in customer.current_plan for keyword in campaign.plan_keywords):
            reasons.append("当前套餐匹配")
        if _to_number(customer.monthly_data_usage) >= campaign.min_data_usage_gb:
            reasons.append("流量使用特征匹配")
        if _to_number(customer.monthly_call_usage) >= campaign.min_call_usage_minutes:
            reasons.append("通话使用特征匹配")
        return reasons or ["双塔向量相似"]

    def dashboard(self):
        latest_snapshot = RecommendationFeatureSnapshot.objects.filter(workspace_id=self.workspace_id).aggregate(
            maximum=Max("snapshot_version")
        )["maximum"]
        snapshot_rows = RecommendationFeatureSnapshot.objects.filter(
            workspace_id=self.workspace_id,
            snapshot_version=latest_snapshot,
        )
        training_runs = RecommendationTrainingRun.objects.filter(workspace_id=self.workspace_id)[:20]
        versions = RecommendationModelVersion.objects.filter(workspace_id=self.workspace_id).prefetch_related(
            "item_embeddings"
        )[:20]
        published = next((row for row in versions if row.status == RecommendationModelStatus.PUBLISHED), None)
        item_embeddings = []
        if published:
            item_embeddings = [
                {
                    "id": str(row.id),
                    "campaign_id": str(row.campaign_id),
                    "campaign_name": row.campaign.name,
                    "dimension": len(row.vector),
                    "vector_norm": row.vector_norm,
                    "update_time": row.update_time,
                }
                for row in published.item_embeddings.select_related("campaign")
            ]
        customers = [
            {
                "id": str(row.id),
                "name": row.name or row.phone or str(row.id),
                "phone": row.phone,
                "province": row.province,
                "current_plan": row.current_plan,
            }
            for row in self._customers().order_by("name", "phone")[:100]
        ]
        return {
            "summary": {
                "snapshot_version": latest_snapshot,
                "user_feature_count": snapshot_rows.filter(feature_type=RecommendationFeatureType.USER).count(),
                "item_feature_count": snapshot_rows.filter(feature_type=RecommendationFeatureType.ITEM).count(),
                "successful_run_count": RecommendationTrainingRun.objects.filter(
                    workspace_id=self.workspace_id,
                    status=RecommendationTrainingStatus.SUCCESS,
                ).count(),
                "model_version_count": RecommendationModelVersion.objects.filter(
                    workspace_id=self.workspace_id
                ).count(),
                "published_version": published.version if published else None,
                "inference_count": RecommendationInferenceLog.objects.filter(workspace_id=self.workspace_id).count(),
            },
            "training_runs": [serialize_training_run(row) for row in training_runs],
            "model_versions": [serialize_model_version(row) for row in versions],
            "item_embeddings": item_embeddings,
            "customers": customers,
        }
