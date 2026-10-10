# coding=utf-8
from django.test import Client, TestCase

from common.exception.app_exception import AppApiException
from models_provider.models import (
    LifecycleModelVersion,
    LifecycleModelVersionStatus,
    ModelEvaluationRun,
    ModelEvaluationStatus,
    ModelExperiment,
    ModelExperimentStatus,
    ModelReleaseAction,
    ModelReleaseRecord,
)
from models_provider.serializers.lifecycle import ModelLifecycleService
from users.models import User


class ModelLifecycleServiceTests(TestCase):
    workspace_id = "lifecycle-test"

    def setUp(self):
        self.user = User.objects.create(
            username="lifecycle-tester",
            nick_name="模型生命周期测试员",
            password="test-password",
            role="USER",
        )
        self.service = ModelLifecycleService(self.workspace_id, self.user)

    def create_completed_experiment(self, name="基线实验"):
        experiment = self.service.create_experiment(
            {
                "name": name,
                "dataset_name": "评估样本集",
                "dataset_version": "2026.09",
                "parameters": {"temperature": 0.1},
                "tags": {"stage": "candidate"},
            }
        )
        self.service.update_experiment(experiment["id"], {"status": ModelExperimentStatus.RUNNING})
        return self.service.update_experiment(experiment["id"], {"status": ModelExperimentStatus.SUCCESS})

    def create_version(self, experiment, registry_name="客服意图模型"):
        return self.service.create_version(
            {
                "registry_name": registry_name,
                "experiment_id": experiment["id"],
                "artifact_uri": "s3://model-artifacts/customer-intent",
                "artifact_digest": "sha256:test",
                "metrics": {"training_accuracy": 0.95},
            }
        )

    def evaluate_passed(self, version):
        return self.service.evaluate_version(
            version["id"],
            {
                "dataset_name": "发布准入集",
                "dataset_version": "v1",
                "metrics": {"accuracy": 0.93, "latency_ms": 88},
                "thresholds": {"accuracy": {"min": 0.9}, "latency_ms": {"max": 100}},
                "summary": "满足首版发布门槛",
            },
        )

    def test_experiment_state_transition_and_workspace_isolation(self):
        experiment = self.service.create_experiment({"name": "状态流转实验"})
        self.assertEqual(experiment["status"], ModelExperimentStatus.DRAFT)

        running = self.service.update_experiment(experiment["id"], {"status": ModelExperimentStatus.RUNNING})
        self.assertIsNotNone(running["started_at"])
        completed = self.service.update_experiment(experiment["id"], {"status": ModelExperimentStatus.SUCCESS})
        self.assertIsNotNone(completed["finished_at"])

        other_service = ModelLifecycleService("other-workspace", self.user)
        with self.assertRaises(AppApiException) as missing:
            other_service.get_experiment(experiment["id"])
        self.assertEqual(missing.exception.code, 404)

        with self.assertRaises(AppApiException):
            self.service.update_experiment(experiment["id"], {"status": ModelExperimentStatus.RUNNING})

    def test_duplicate_experiment_name_returns_business_error_without_breaking_transaction(self):
        self.service.create_experiment({"name": "不可重名实验"})
        with self.assertRaises(AppApiException) as duplicate:
            self.service.create_experiment({"name": "不可重名实验"})
        self.assertEqual(duplicate.exception.code, 400)
        self.assertEqual(ModelExperiment.objects.filter(workspace_id=self.workspace_id).count(), 1)

    def test_only_completed_experiment_can_register_sequential_versions(self):
        draft = self.service.create_experiment({"name": "未完成实验"})
        with self.assertRaises(AppApiException):
            self.create_version(draft)

        completed = self.create_completed_experiment("版本来源实验")
        version_one = self.create_version(completed)
        version_two = self.create_version(completed)
        self.assertEqual(version_one["version"], 1)
        self.assertEqual(version_two["version"], 2)
        self.assertEqual(version_one["dataset_version"], "2026.09")
        self.assertEqual(version_one["parameters"], {"temperature": 0.1})

    def test_evaluation_checks_minimum_and_maximum_thresholds(self):
        version = self.create_version(self.create_completed_experiment())
        result = self.evaluate_passed(version)
        self.assertEqual(result["evaluation"]["status"], ModelEvaluationStatus.PASSED)
        self.assertEqual(result["version"]["status"], LifecycleModelVersionStatus.APPROVED)

        failed = self.service.evaluate_version(
            version["id"],
            {
                "dataset_name": "发布准入集",
                "metrics": {"accuracy": 0.89, "latency_ms": 101},
                "thresholds": {"accuracy": 0.9, "latency_ms": {"max": 100}},
            },
        )
        self.assertEqual(failed["evaluation"]["status"], ModelEvaluationStatus.FAILED)
        self.assertEqual(failed["version"]["status"], LifecycleModelVersionStatus.REJECTED)
        self.assertEqual(ModelEvaluationRun.objects.filter(model_version_id=version["id"]).count(), 2)

    def test_failed_evaluation_blocks_publish(self):
        version = self.create_version(self.create_completed_experiment())
        self.service.evaluate_version(
            version["id"],
            {
                "dataset_name": "发布准入集",
                "metrics": {"accuracy": 0.5},
                "thresholds": {"accuracy": 0.9},
            },
        )
        with self.assertRaises(AppApiException) as blocked:
            self.service.publish_version(version["id"], {"reason": "尝试发布失败版本"})
        self.assertEqual(blocked.exception.code, 400)
        self.assertEqual(ModelReleaseRecord.objects.count(), 0)

    def test_publish_new_version_and_rollback_keep_auditable_records(self):
        experiment = self.create_completed_experiment()
        version_one = self.create_version(experiment)
        version_two = self.create_version(experiment)
        self.evaluate_passed(version_one)
        self.evaluate_passed(version_two)

        first_publish = self.service.publish_version(version_one["id"], {"reason": "首次上线"})
        self.assertEqual(first_publish["release"]["action"], ModelReleaseAction.PUBLISH)

        second_publish = self.service.publish_version(version_two["id"], {"reason": "效果提升"})
        self.assertEqual(second_publish["release"]["from_version"], 1)
        version_one_row = LifecycleModelVersion.objects.get(id=version_one["id"])
        self.assertEqual(version_one_row.status, LifecycleModelVersionStatus.ARCHIVED)

        rollback = self.service.rollback_version(version_one["id"], {"reason": "线上指标回落"})
        self.assertEqual(rollback["release"]["action"], ModelReleaseAction.ROLLBACK)
        self.assertEqual(rollback["release"]["from_version"], 2)
        self.assertEqual(rollback["release"]["target_version"], 1)
        self.assertEqual(
            list(ModelReleaseRecord.objects.values_list("action", flat=True)),
            [ModelReleaseAction.ROLLBACK, ModelReleaseAction.PUBLISH, ModelReleaseAction.PUBLISH],
        )
        self.assertEqual(
            LifecycleModelVersion.objects.get(id=version_two["id"]).status,
            LifecycleModelVersionStatus.ARCHIVED,
        )

    def test_delete_guards_keep_lifecycle_history(self):
        experiment = self.create_completed_experiment()
        version = self.create_version(experiment)
        self.evaluate_passed(version)

        with self.assertRaises(AppApiException):
            self.service.delete_version(version["id"])
        with self.assertRaises(AppApiException):
            self.service.delete_experiment(experiment["id"])

    def test_overview_is_workspace_scoped(self):
        version = self.create_version(self.create_completed_experiment())
        self.evaluate_passed(version)
        self.service.publish_version(version["id"], {"reason": "首版发布"})

        overview = self.service.overview()
        self.assertEqual(overview["experiment_total"], 1)
        self.assertEqual(overview["version_total"], 1)
        self.assertEqual(overview["published_total"], 1)
        self.assertEqual(len(overview["recent_releases"]), 1)
        self.assertEqual(ModelLifecycleService("other-workspace", self.user).overview()["version_total"], 0)

    def test_lifecycle_endpoint_requires_authentication(self):
        response = Client().get(f"/admin/api/workspace/{self.workspace_id}/model-lifecycle/overview")
        self.assertEqual(response.status_code, 401)
