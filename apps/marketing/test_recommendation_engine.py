import json
from types import SimpleNamespace

from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from marketing.models import (
    MarketingCampaign,
    MarketingCampaignApprovalStatus,
    MarketingCampaignStatus,
    MarketingCustomer,
    MarketingScenario,
    MarketingTask,
    MarketingTouchBatch,
    MarketingTouchExecution,
    MarketingTouchExecutionResult,
    RecommendationFeatureSnapshot,
    RecommendationFeedbackEvent,
    RecommendationFeedbackType,
    RecommendationFusionConfig,
    RecommendationFusionRun,
    RecommendationInferenceLog,
    RecommendationIncrementalRun,
    RecommendationIncrementalStatus,
    RecommendationItemEmbedding,
    RecommendationModelStatus,
    RecommendationModelVersion,
    RecommendationRankingRun,
    RecommendationRankingStatus,
    RecommendationRankingVersion,
    RecommendationTrainingStatus,
)
from marketing.serializers.recommendation_engine import RecommendationEngineService
from marketing.serializers.recommendation_effect import RecommendationEffectService
from marketing.serializers.recommendation_fusion import RecommendationFusionService
from marketing.serializers.recommendation_incremental import RecommendationIncrementalService
from marketing.serializers.recommendation_ranking import DEFAULT_RANKING_WEIGHTS, RecommendationRankingService
from trigger.event_orchestration import EventOrchestrationService
from trigger.models import EventFlowRun, FlowRunStatus, StandardEvent
from users.models import User


class RecommendationEngineFixture(TestCase):
    def setUp(self):
        self.workspace_id = "recommendation-engine-test"
        self.user = User.objects.create(
            username="recommendation_engine_user",
            nick_name="推荐引擎管理员",
            password="x",
            role="ADMIN",
        )
        scenario = MarketingScenario.objects.create(
            workspace_id=self.workspace_id,
            name="双塔推荐验收场景",
            user=self.user,
        )
        task = MarketingTask.objects.create(
            workspace_id=self.workspace_id,
            name="双塔推荐验收任务",
            scenario=scenario,
            user=self.user,
        )
        self.beijing_customer = MarketingCustomer.objects.create(
            workspace_id=self.workspace_id,
            task=task,
            name="北京高流量客户",
            phone="customer-bj",
            province="北京",
            current_plan="畅享套餐",
            monthly_data_usage="60GB",
            monthly_call_usage="300分钟",
            status="INTENT",
            intent="高意向",
        )
        MarketingCustomer.objects.create(
            workspace_id=self.workspace_id,
            task=task,
            name="上海基础客户",
            phone="customer-sh",
            province="上海",
            current_plan="基础套餐",
            monthly_data_usage="8GB",
            monthly_call_usage="60分钟",
        )
        self.beijing_campaign = MarketingCampaign.objects.create(
            workspace_id=self.workspace_id,
            user=self.user,
            name="北京畅享升级包",
            code="BJ-UPGRADE",
            status=MarketingCampaignStatus.ACTIVE,
            approval_status=MarketingCampaignApprovalStatus.APPROVED,
            benefit="每月增加 30GB 流量",
            provinces=["北京"],
            plan_keywords=["畅享"],
            min_data_usage_gb=20,
            min_call_usage_minutes=100,
            priority=10,
        )
        MarketingCampaign.objects.create(
            workspace_id=self.workspace_id,
            user=self.user,
            name="上海基础关怀包",
            code="SH-CARE",
            status=MarketingCampaignStatus.ACTIVE,
            approval_status=MarketingCampaignApprovalStatus.APPROVED,
            benefit="基础套餐专属关怀权益",
            provinces=["上海"],
            plan_keywords=["基础"],
            priority=20,
        )
        self.service = RecommendationEngineService(self.workspace_id, self.user)

    def build_and_train(self, auto_publish=True):
        snapshot = self.service.build_feature_snapshot({"input_dim": 32})
        return self.service.train(
            {
                "name": f"验收双塔-v{snapshot['snapshot_version']}",
                "snapshot_version": snapshot["snapshot_version"],
                "embedding_dim": 8,
                "epochs": 30,
                "learning_rate": 0.05,
                "auto_publish": auto_publish,
            }
        )


class RecommendationEngineServiceTests(RecommendationEngineFixture):
    def test_feature_snapshot_contains_user_and_item_towers(self):
        result = self.service.build_feature_snapshot({"input_dim": 32})

        self.assertEqual(result["user_count"], 2)
        self.assertEqual(result["item_count"], 2)
        self.assertEqual(result["feature_count"], 4)
        self.assertEqual(
            {len(row.input_vector) for row in RecommendationFeatureSnapshot.objects.all()},
            {32},
        )

    def test_train_creates_real_model_version_and_item_embeddings(self):
        result = self.build_and_train()

        run = result["training_run"]
        version = result["model_version"]
        self.assertEqual(run["status"], RecommendationTrainingStatus.SUCCESS)
        self.assertLess(run["final_loss"], run["initial_loss"])
        self.assertEqual(version["status"], RecommendationModelStatus.PUBLISHED)
        self.assertEqual(version["item_embedding_count"], 2)
        self.assertEqual(RecommendationItemEmbedding.objects.count(), 2)

    def test_topk_inference_uses_published_model_and_records_result(self):
        self.build_and_train()

        result = self.service.recommend({"customer_id": str(self.beijing_customer.id), "top_k": 2})

        self.assertEqual(len(result["candidates"]), 2)
        self.assertEqual(result["candidates"][0]["campaign_id"], str(self.beijing_campaign.id))
        self.assertGreaterEqual(result["candidates"][0]["score"], result["candidates"][1]["score"])
        self.assertEqual(RecommendationInferenceLog.objects.count(), 1)

    def test_manual_publish_archives_previous_version(self):
        first = self.build_and_train()
        second = self.build_and_train(auto_publish=False)

        self.service.publish(second["model_version"]["id"])

        first_version = RecommendationModelVersion.objects.get(id=first["model_version"]["id"])
        second_version = RecommendationModelVersion.objects.get(id=second["model_version"]["id"])
        self.assertEqual(first_version.status, RecommendationModelStatus.ARCHIVED)
        self.assertEqual(second_version.status, RecommendationModelStatus.PUBLISHED)


class RecommendationEngineApiTests(RecommendationEngineFixture):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        auth = SimpleNamespace(
            role_list=[f"WORKSPACE_MANAGE:/WORKSPACE/{self.workspace_id}"],
            permission_list=[],
        )
        self.client.force_authenticate(user=self.user, token=auth)

    def test_snapshot_train_dashboard_and_infer_api(self):
        prefix = f"/admin/api/workspace/{self.workspace_id}/marketing/recommendation"
        snapshot_response = self.client.post(f"{prefix}/feature-snapshot", {"input_dim": 32}, format="json")
        snapshot_payload = json.loads(snapshot_response.content)["data"]
        train_response = self.client.post(
            f"{prefix}/train",
            {
                "name": "接口双塔训练",
                "snapshot_version": snapshot_payload["snapshot_version"],
                "embedding_dim": 8,
                "epochs": 20,
                "learning_rate": 0.05,
                "auto_publish": True,
            },
            format="json",
        )
        dashboard_response = self.client.get(f"{prefix}/dashboard")
        infer_response = self.client.post(
            f"{prefix}/infer",
            {"customer_id": str(self.beijing_customer.id), "top_k": 1},
            format="json",
        )

        self.assertEqual(snapshot_response.status_code, 200)
        self.assertEqual(train_response.status_code, 200)
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertEqual(infer_response.status_code, 200)
        dashboard = json.loads(dashboard_response.content)["data"]
        inference = json.loads(infer_response.content)["data"]
        self.assertEqual(dashboard["summary"]["published_version"], 1)
        self.assertEqual(inference["model_version"], 1)
        self.assertEqual(len(inference["candidates"]), 1)


class RecommendationFusionServiceTests(RecommendationEngineFixture):
    def setUp(self):
        super().setUp()
        self.fusion_service = RecommendationFusionService(self.workspace_id, self.user)

    def test_default_config_exposes_all_six_channels(self):
        config = self.fusion_service.get_config()

        self.assertEqual(len(config["enabled_channels"]), 6)
        self.assertAlmostEqual(sum(config["weights"].values()), 1)
        self.assertEqual(RecommendationFusionConfig.objects.count(), 1)

    def test_fusion_works_without_published_two_tower_model(self):
        result = self.fusion_service.infer({"customer_id": str(self.beijing_customer.id), "top_k": 5})

        self.assertIsNone(result["model_version"])
        self.assertGreater(len(result["candidates"]), 0)
        self.assertEqual(result["candidates"][0]["campaign_id"], str(self.beijing_campaign.id))
        self.assertIn("RULE", {row["channel"] for row in result["candidates"][0]["source_details"]})
        self.assertEqual(RecommendationFusionRun.objects.count(), 1)

    def test_six_channel_fusion_deduplicates_and_explains_sources(self):
        self.build_and_train()
        peer = MarketingCustomer.objects.create(
            workspace_id=self.workspace_id,
            task=self.beijing_customer.task,
            name="北京相似客户",
            phone="customer-bj-peer",
            province="北京",
            current_plan="畅享套餐",
            monthly_data_usage="45GB",
            monthly_call_usage="220分钟",
            status="INTENT",
            intent="高意向",
        )
        self.service.recommend({"customer_id": str(peer.id), "top_k": 2})

        result = self.fusion_service.infer({"customer_id": str(self.beijing_customer.id), "top_k": 5})

        campaign_ids = [row["campaign_id"] for row in result["candidates"]]
        self.assertEqual(len(campaign_ids), len(set(campaign_ids)))
        top_candidate = result["candidates"][0]
        source_channels = {row["channel"] for row in top_candidate["source_details"]}
        self.assertIn("TWO_TOWER", source_channels)
        self.assertIn("COLLABORATIVE", source_channels)
        self.assertGreaterEqual(top_candidate["source_count"], 4)
        self.assertAlmostEqual(
            top_candidate["score"],
            sum(row["contribution"] for row in top_candidate["source_details"]),
            places=5,
        )

    def test_weight_configuration_changes_fusion_contribution(self):
        config = self.fusion_service.save_config(
            {
                "weights": {
                    "TWO_TOWER": 0,
                    "RULE": 1,
                    "COLLABORATIVE": 0,
                    "CONTENT": 0,
                    "HOT": 0,
                    "REGION": 0,
                },
                "enabled_channels": ["RULE"],
                "candidate_pool_size": 20,
            }
        )
        result = self.fusion_service.infer({"customer_id": str(self.beijing_customer.id), "top_k": 5})

        self.assertEqual(config["enabled_channels"], ["RULE"])
        self.assertEqual(result["candidates"][0]["source_count"], 1)
        self.assertEqual(result["candidates"][0]["source_details"][0]["channel"], "RULE")
        self.assertEqual(result["candidates"][0]["score"], 1)


class RecommendationFusionApiTests(RecommendationEngineFixture):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        auth = SimpleNamespace(
            role_list=[f"WORKSPACE_MANAGE:/WORKSPACE/{self.workspace_id}"],
            permission_list=[],
        )
        self.client.force_authenticate(user=self.user, token=auth)

    def test_config_dashboard_and_fusion_infer_api(self):
        prefix = f"/admin/api/workspace/{self.workspace_id}/marketing/recommendation"
        config_response = self.client.put(
            f"{prefix}/fusion-config",
            {
                "weights": {
                    "TWO_TOWER": 0.3,
                    "RULE": 0.3,
                    "COLLABORATIVE": 0.1,
                    "CONTENT": 0.1,
                    "HOT": 0.1,
                    "REGION": 0.1,
                },
                "enabled_channels": ["TWO_TOWER", "RULE", "COLLABORATIVE", "CONTENT", "HOT", "REGION"],
                "candidate_pool_size": 30,
            },
            format="json",
        )
        infer_response = self.client.post(
            f"{prefix}/fusion-infer",
            {"customer_id": str(self.beijing_customer.id), "top_k": 3},
            format="json",
        )
        dashboard_response = self.client.get(f"{prefix}/fusion-dashboard")

        self.assertEqual(config_response.status_code, 200)
        self.assertEqual(infer_response.status_code, 200)
        self.assertEqual(dashboard_response.status_code, 200)
        dashboard = json.loads(dashboard_response.content)["data"]
        inference = json.loads(infer_response.content)["data"]
        self.assertEqual(dashboard["summary"]["fusion_run_count"], 1)
        self.assertEqual(inference["channel_counts"]["RULE"], 1)
        self.assertGreater(len(inference["candidates"]), 0)


class RecommendationRankingServiceTests(RecommendationEngineFixture):
    def setUp(self):
        super().setUp()
        self.ranking_service = RecommendationRankingService(self.workspace_id, self.user)

    def test_dashboard_creates_explainable_published_baseline(self):
        dashboard = self.ranking_service.dashboard()

        self.assertEqual(dashboard["summary"]["published_version"], 1)
        self.assertEqual(len(dashboard["feature_schema"]), 7)
        self.assertAlmostEqual(sum(dashboard["versions"][0]["feature_weights"].values()), 1)
        self.assertEqual(RecommendationRankingVersion.objects.count(), 1)

    def test_ranking_returns_topn_and_feature_contributions(self):
        result = self.ranking_service.infer(
            {"customer_id": str(self.beijing_customer.id), "top_n": 1, "candidate_pool_size": 10}
        )

        self.assertEqual(len(result["candidates"]), 1)
        candidate = result["candidates"][0]
        self.assertEqual(candidate["rank"], 1)
        self.assertEqual(candidate["campaign_id"], str(self.beijing_campaign.id))
        self.assertEqual(len(candidate["feature_details"]), 7)
        self.assertAlmostEqual(
            candidate["rank_score"],
            sum(row["contribution"] for row in candidate["feature_details"]),
            places=5,
        )
        self.assertEqual(RecommendationRankingRun.objects.count(), 1)
        self.assertEqual(RecommendationFusionRun.objects.count(), 1)
        exposure = RecommendationFeedbackEvent.objects.get(event_type=RecommendationFeedbackType.EXPOSED)
        self.assertEqual(exposure.campaign_id, self.beijing_campaign.id)
        self.assertEqual(len(exposure.feature_snapshot), 7)
        self.assertFalse(StandardEvent.objects.filter(workspace_id=self.workspace_id).exists())

    def test_published_exposure_flow_receives_top_ranked_event_once(self):
        EventOrchestrationService(self.workspace_id, self.user).create_flow({
            "code": "RECOMMENDATION_REVIEW",
            "name": "推荐曝光复核",
            "event_type": "marketing.recommendation.exposed",
            "source_types": ["SYSTEM"],
            "event_schema": {"required": ["task_id", "customer_id", "ranking_run_id", "feedback_id"]},
            "nodes": [{"code": "REVIEW", "name": "人工复核", "node_type": "MANUAL"}],
            "publish": True,
        })
        result = self.ranking_service.infer({
            "customer_id": str(self.beijing_customer.id),
            "top_n": 2,
            "candidate_pool_size": 10,
        })
        event = StandardEvent.objects.get(workspace_id=self.workspace_id)
        self.assertEqual(event.payload_snapshot["ranking_run_id"], result["ranking_run_id"])
        self.assertEqual(event.payload_snapshot["customer_id"], str(self.beijing_customer.id))
        self.assertEqual(
            event.payload_snapshot["feedback_id"],
            str(RecommendationFeedbackEvent.objects.get(
                ranking_run_id=result["ranking_run_id"],
                campaign_id=result["candidates"][0]["campaign_id"],
                event_type=RecommendationFeedbackType.EXPOSED,
            ).id),
        )
        self.assertEqual(EventFlowRun.objects.get(standard_event=event).status, FlowRunStatus.WAITING)
        from marketing.recommendation_events import publish_top_exposure

        replay = publish_top_exposure(RecommendationRankingRun.objects.get(id=result["ranking_run_id"]), self.user)
        self.assertFalse(replay["created"])
        self.assertEqual(StandardEvent.objects.filter(workspace_id=self.workspace_id).count(), 1)

    def test_invalid_exposure_contract_rolls_back_ranking_and_feedback(self):
        EventOrchestrationService(self.workspace_id, self.user).create_flow({
            "code": "RECOMMENDATION_INVALID_CONTRACT",
            "name": "非法推荐契约验收",
            "event_type": "marketing.recommendation.exposed",
            "source_types": ["SYSTEM"],
            "event_schema": {"required": ["unavailable_field"]},
            "nodes": [{"code": "REVIEW", "name": "人工复核", "node_type": "MANUAL"}],
            "publish": True,
        })
        with self.assertRaises(ValidationError):
            self.ranking_service.infer({
                "customer_id": str(self.beijing_customer.id),
                "top_n": 1,
                "candidate_pool_size": 10,
            })
        self.assertFalse(RecommendationRankingRun.objects.filter(workspace_id=self.workspace_id).exists())
        self.assertFalse(RecommendationFeedbackEvent.objects.filter(workspace_id=self.workspace_id).exists())
        self.assertFalse(StandardEvent.objects.filter(workspace_id=self.workspace_id).exists())

    def test_feature_weight_version_can_publish_and_archive_previous(self):
        self.ranking_service.dashboard()
        weights = {**DEFAULT_RANKING_WEIGHTS, "RECALL_SCORE": 0.8, "BUSINESS_MATCH": 0.3}
        created = self.ranking_service.create_version(
            {"name": "业务增强精排-v2", "feature_weights": weights, "auto_publish": True}
        )

        self.assertEqual(created["version"], 2)
        self.assertEqual(created["status"], RecommendationRankingStatus.PUBLISHED)
        self.assertEqual(
            RecommendationRankingVersion.objects.get(version=1).status,
            RecommendationRankingStatus.ARCHIVED,
        )

    def test_ranking_can_preview_draft_version(self):
        created = self.ranking_service.create_version(
            {"name": "召回优先草稿", "feature_weights": DEFAULT_RANKING_WEIGHTS}
        )
        result = self.ranking_service.infer(
            {
                "customer_id": str(self.beijing_customer.id),
                "top_n": 2,
                "candidate_pool_size": 10,
                "ranking_version_id": created["id"],
            }
        )

        self.assertEqual(created["status"], RecommendationRankingStatus.DRAFT)
        self.assertEqual(result["ranking_version"], 2)
        self.assertGreater(result["candidate_count"], 0)


class RecommendationRankingApiTests(RecommendationEngineFixture):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        auth = SimpleNamespace(
            role_list=[f"WORKSPACE_MANAGE:/WORKSPACE/{self.workspace_id}"],
            permission_list=[],
        )
        self.client.force_authenticate(user=self.user, token=auth)

    def test_version_publish_dashboard_and_ranking_api(self):
        prefix = f"/admin/api/workspace/{self.workspace_id}/marketing/recommendation"
        version_response = self.client.post(
            f"{prefix}/ranking-version",
            {
                "name": "接口精排-v2",
                "feature_weights": DEFAULT_RANKING_WEIGHTS,
                "auto_publish": True,
            },
            format="json",
        )
        infer_response = self.client.post(
            f"{prefix}/ranking-infer",
            {"customer_id": str(self.beijing_customer.id), "top_n": 1, "candidate_pool_size": 10},
            format="json",
        )
        dashboard_response = self.client.get(f"{prefix}/ranking-dashboard")

        self.assertEqual(version_response.status_code, 200)
        self.assertEqual(infer_response.status_code, 200)
        self.assertEqual(dashboard_response.status_code, 200)
        dashboard = json.loads(dashboard_response.content)["data"]
        inference = json.loads(infer_response.content)["data"]
        self.assertEqual(dashboard["summary"]["published_version"], 2)
        self.assertEqual(dashboard["summary"]["ranking_run_count"], 1)
        self.assertEqual(inference["ranking_version"], 2)
        self.assertEqual(len(inference["candidates"]), 1)


class RecommendationIncrementalServiceTests(RecommendationEngineFixture):
    def setUp(self):
        super().setUp()
        self.ranking_service = RecommendationRankingService(self.workspace_id, self.user)
        self.incremental_service = RecommendationIncrementalService(self.workspace_id, self.user)
        self.ranking_result = self.ranking_service.infer(
            {"customer_id": str(self.beijing_customer.id), "top_n": 2, "candidate_pool_size": 10}
        )

    def record_pair(self):
        candidates = self.ranking_result["candidates"]
        positive = self.incremental_service.record_feedback(
            {
                "ranking_run_id": self.ranking_result["ranking_run_id"],
                "campaign_id": candidates[0]["campaign_id"],
                "event_type": RecommendationFeedbackType.CLICKED,
                "event_key": "test:clicked",
            }
        )
        negative = self.incremental_service.record_feedback(
            {
                "ranking_run_id": self.ranking_result["ranking_run_id"],
                "campaign_id": candidates[1]["campaign_id"],
                "event_type": RecommendationFeedbackType.NEGATIVE,
                "event_key": "test:negative",
            }
        )
        return positive, negative

    def test_feedback_is_idempotent_and_keeps_feature_snapshot(self):
        positive, _ = self.record_pair()
        duplicated = self.incremental_service.record_feedback(
            {
                "ranking_run_id": self.ranking_result["ranking_run_id"],
                "campaign_id": self.ranking_result["candidates"][0]["campaign_id"],
                "event_type": RecommendationFeedbackType.CLICKED,
                "event_key": "test:clicked",
            }
        )

        self.assertTrue(positive["created"])
        self.assertFalse(duplicated["created"])
        self.assertEqual(positive["feature_snapshot"], duplicated["feature_snapshot"])
        self.assertEqual(RecommendationFeedbackEvent.objects.filter(label__gt=0).count(), 1)

    def test_incremental_train_creates_version_and_metric_comparison(self):
        self.record_pair()

        result = self.incremental_service.train(
            {"name": "反馈增量验收-v2", "learning_rate": 0.25, "minimum_samples": 2, "auto_publish": True}
        )

        run = result["run"]
        version = result["generated_version"]
        self.assertEqual(run["status"], RecommendationIncrementalStatus.SUCCESS)
        self.assertEqual(run["sample_count"], 2)
        self.assertEqual(version["version"], 2)
        self.assertAlmostEqual(sum(version["feature_weights"].values()), 1, places=5)
        self.assertIn("learned_pairwise_accuracy", run["metrics"])
        self.assertEqual(RecommendationIncrementalRun.objects.count(), 1)

    def test_sync_imports_touch_intent_once(self):
        batch = MarketingTouchBatch.objects.create(
            workspace_id=self.workspace_id,
            task=self.beijing_customer.task,
            user=self.user,
            name="增量学习触达批次",
        )
        touch = MarketingTouchExecution.objects.create(
            workspace_id=self.workspace_id,
            batch=batch,
            customer=self.beijing_customer,
            user=self.user,
            result=MarketingTouchExecutionResult.INTENT,
        )

        first = self.incremental_service.sync_business_feedback()
        second = self.incremental_service.sync_business_feedback()

        self.assertEqual(first["created_by_type"][RecommendationFeedbackType.CLICKED], 1)
        self.assertEqual(second["created_count"], 0)
        self.assertTrue(
            RecommendationFeedbackEvent.objects.filter(source_type="TOUCH_EXECUTION", source_id=str(touch.id)).exists()
        )


class RecommendationIncrementalApiTests(RecommendationEngineFixture):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        auth = SimpleNamespace(
            role_list=[f"WORKSPACE_MANAGE:/WORKSPACE/{self.workspace_id}"],
            permission_list=[],
        )
        self.client.force_authenticate(user=self.user, token=auth)

    def test_feedback_dashboard_sync_and_train_api(self):
        prefix = f"/admin/api/workspace/{self.workspace_id}/marketing/recommendation"
        ranking_response = self.client.post(
            f"{prefix}/ranking-infer",
            {"customer_id": str(self.beijing_customer.id), "top_n": 2, "candidate_pool_size": 10},
            format="json",
        )
        ranking = json.loads(ranking_response.content)["data"]
        for event_type, candidate in zip(
            [RecommendationFeedbackType.CLICKED, RecommendationFeedbackType.NEGATIVE],
            ranking["candidates"],
            strict=True,
        ):
            feedback_response = self.client.post(
                f"{prefix}/feedback",
                {
                    "ranking_run_id": ranking["ranking_run_id"],
                    "campaign_id": candidate["campaign_id"],
                    "event_type": event_type,
                },
                format="json",
            )
            self.assertEqual(feedback_response.status_code, 200)
        sync_response = self.client.post(f"{prefix}/incremental-sync", {}, format="json")
        train_response = self.client.post(
            f"{prefix}/incremental-train",
            {"name": "接口反馈增量-v2", "minimum_samples": 2, "auto_publish": False},
            format="json",
        )
        dashboard_response = self.client.get(f"{prefix}/incremental-dashboard")

        self.assertEqual(ranking_response.status_code, 200)
        self.assertEqual(sync_response.status_code, 200)
        self.assertEqual(train_response.status_code, 200)
        self.assertEqual(dashboard_response.status_code, 200)
        dashboard = json.loads(dashboard_response.content)["data"]
        trained = json.loads(train_response.content)["data"]
        self.assertEqual(dashboard["summary"]["labeled_sample_count"], 2)
        self.assertEqual(dashboard["summary"]["incremental_run_count"], 1)
        self.assertEqual(trained["generated_version"]["status"], RecommendationRankingStatus.DRAFT)


class RecommendationEffectServiceTests(RecommendationEngineFixture):
    def setUp(self):
        super().setUp()
        ranking = RecommendationRankingService(self.workspace_id, self.user).infer(
            {"customer_id": str(self.beijing_customer.id), "top_n": 2, "candidate_pool_size": 10}
        )
        feedback_service = RecommendationIncrementalService(self.workspace_id, self.user)
        for event_type, candidate in zip(
            [
                RecommendationFeedbackType.CLICKED,
                RecommendationFeedbackType.CONVERTED,
                RecommendationFeedbackType.NEGATIVE,
            ],
            [ranking["candidates"][0], ranking["candidates"][0], ranking["candidates"][1]],
            strict=True,
        ):
            feedback_service.record_feedback(
                {
                    "ranking_run_id": ranking["ranking_run_id"],
                    "campaign_id": candidate["campaign_id"],
                    "event_type": event_type,
                }
            )

    def test_effect_dashboard_calculates_funnel_quality_and_latency(self):
        dashboard = RecommendationEffectService(self.workspace_id).dashboard({"days": 30})

        summary = dashboard["summary"]
        self.assertEqual(summary["exposure_count"], 2)
        self.assertEqual(summary["click_count"], 1)
        self.assertEqual(summary["conversion_count"], 1)
        self.assertEqual(summary["negative_count"], 1)
        self.assertEqual(summary["ctr"], 0.5)
        self.assertEqual(summary["cvr"], 0.5)
        self.assertEqual(summary["coverage_rate"], 1)
        self.assertEqual(summary["diversity_score"], 1)
        self.assertGreaterEqual(dashboard["latency"]["total_avg_ms"], 2)
        self.assertEqual(dashboard["version_performance"][0]["version"], 1)
        self.assertEqual(dashboard["campaign_performance"][0]["campaign_name"], self.beijing_campaign.name)
        self.assertEqual(dashboard["daily_trend"][-1]["exposure_count"], 2)


class RecommendationEffectApiTests(RecommendationEngineFixture):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        auth = SimpleNamespace(
            role_list=[f"WORKSPACE_MANAGE:/WORKSPACE/{self.workspace_id}"],
            permission_list=[],
        )
        self.client.force_authenticate(user=self.user, token=auth)

    def test_effect_dashboard_api_supports_period_filter(self):
        RecommendationRankingService(self.workspace_id, self.user).infer(
            {"customer_id": str(self.beijing_customer.id), "top_n": 2, "candidate_pool_size": 10}
        )

        response = self.client.get(
            f"/admin/api/workspace/{self.workspace_id}/marketing/recommendation/effect-dashboard",
            {"days": 7},
        )

        self.assertEqual(response.status_code, 200)
        dashboard = json.loads(response.content)["data"]
        self.assertEqual(dashboard["period"]["days"], 7)
        self.assertEqual(dashboard["summary"]["exposure_count"], 2)
        self.assertEqual(len(dashboard["daily_trend"]), 7)
