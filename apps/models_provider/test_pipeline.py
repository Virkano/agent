# coding=utf-8
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from common.exception.app_exception import AppApiException
from models_provider.models import (
    LifecycleModelVersionStatus,
    ModelPipelineRun,
    ModelPipelineRunStatus,
    ModelPipelineRunTrigger,
    ModelPipelineStageStatus,
    ModelReleaseRecord,
    ModelTrainingPipeline,
)
from models_provider.serializers.pipeline import ModelPipelineService, run_due_training_pipelines
from users.models import User
from models_provider import pipeline_jobs


class ModelPipelineServiceTests(TestCase):
    workspace_id = "pipeline-test"

    def setUp(self):
        self.user = User.objects.create(
            username="pipeline-tester",
            nick_name="模型流水线测试员",
            password="test-password",
            role="USER",
        )
        self.service = ModelPipelineService(self.workspace_id, self.user)

    def create_pipeline(self, **overrides):
        data = {
            "name": "客服意图自动训练",
            "description": "M08-02 验收流水线",
            "registry_name": "客服意图模型",
            "dataset_name": "客服意图训练集",
            "dataset_version": "2026.09",
            "parameters": {"epochs": 3},
            "evaluation_metrics": {"accuracy": 0.95, "latency_ms": 80},
            "thresholds": {"accuracy": {"min": 0.9}, "latency_ms": {"max": 100}},
            "approval_mode": "AUTO",
            "auto_deploy": True,
        }
        data.update(overrides)
        return self.service.create_pipeline(data)

    def test_auto_pipeline_runs_all_stages_and_publishes_version(self):
        pipeline = self.create_pipeline()

        run = self.service.start_run(pipeline["id"])

        self.assertEqual(run["status"], ModelPipelineRunStatus.SUCCESS)
        self.assertEqual(run["trigger"], ModelPipelineRunTrigger.MANUAL)
        self.assertEqual([stage["status"] for stage in run["stages"]], ["SUCCESS"] * 5)
        self.assertEqual(run["model_version_label"], "v1")
        self.assertEqual(ModelReleaseRecord.objects.filter(target_version_id=run["model_version_id"]).count(), 1)
        self.assertEqual(
            ModelPipelineRun.objects.get(id=run["id"]).model_version.status,
            LifecycleModelVersionStatus.PUBLISHED,
        )

    def test_manual_approval_can_publish_or_reject(self):
        pipeline = self.create_pipeline(approval_mode="MANUAL")
        waiting = self.service.start_run(pipeline["id"])
        self.assertEqual(waiting["status"], ModelPipelineRunStatus.WAITING_APPROVAL)
        self.assertEqual(waiting["stages"][3]["status"], ModelPipelineStageStatus.PENDING)

        approved = self.service.approve_run(waiting["id"], {"action": "APPROVE", "comment": "准入通过"})
        self.assertEqual(approved["status"], ModelPipelineRunStatus.SUCCESS)
        self.assertEqual(approved["stages"][3]["status"], ModelPipelineStageStatus.SUCCESS)

        second = self.service.start_run(pipeline["id"])
        rejected = self.service.approve_run(second["id"], {"action": "REJECT", "comment": "等待更多样本"})
        self.assertEqual(rejected["status"], ModelPipelineRunStatus.REJECTED)
        self.assertEqual(rejected["stages"][4]["status"], ModelPipelineStageStatus.SKIPPED)

    def test_failed_evaluation_skips_approval_and_deployment(self):
        pipeline = self.create_pipeline(evaluation_metrics={"accuracy": 0.5, "latency_ms": 80})

        run = self.service.start_run(pipeline["id"])

        self.assertEqual(run["status"], ModelPipelineRunStatus.FAILED)
        self.assertIn("准入门槛", run["error_message"])
        self.assertEqual(run["stages"][2]["status"], ModelPipelineStageStatus.SUCCESS)
        self.assertEqual(run["stages"][3]["status"], ModelPipelineStageStatus.SKIPPED)
        self.assertEqual(ModelReleaseRecord.objects.filter(target_version_id=run["model_version_id"]).count(), 0)

    def test_failed_run_can_retry_with_new_metrics(self):
        pipeline = self.create_pipeline(evaluation_metrics={"accuracy": 0.5, "latency_ms": 80})
        failed = self.service.start_run(pipeline["id"])

        retried = self.service.start_run(
            pipeline["id"],
            {"evaluation_metrics": {"accuracy": 0.96, "latency_ms": 75}},
            ModelPipelineRunTrigger.RETRY,
        )

        self.assertEqual(retried["run_number"], 2)
        self.assertEqual(retried["trigger"], ModelPipelineRunTrigger.RETRY)
        self.assertEqual(retried["status"], ModelPipelineRunStatus.SUCCESS)
        self.assertEqual(failed["run_number"], 1)

    def test_schedule_validation_and_due_execution(self):
        with self.assertRaises(Exception):
            self.create_pipeline(name="无效调度", schedule_enabled=True, cron_expression="invalid")
        pipeline = self.create_pipeline(
            name="定时重训流水线",
            schedule_enabled=True,
            cron_expression="*/5 * * * *",
        )
        ModelTrainingPipeline.objects.filter(id=pipeline["id"]).update(
            next_run_at=timezone.now() - timedelta(minutes=1)
        )

        results = run_due_training_pipelines()

        matching = [item for item in results if item["pipeline_id"] == pipeline["id"]]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["trigger"], ModelPipelineRunTrigger.SCHEDULED)
        self.assertEqual(matching[0]["status"], ModelPipelineRunStatus.SUCCESS)
        self.assertGreater(ModelTrainingPipeline.objects.get(id=pipeline["id"]).next_run_at, timezone.now())

    def test_workspace_isolation_and_run_history_protect_pipeline(self):
        pipeline = self.create_pipeline()
        self.service.start_run(pipeline["id"])
        other = ModelPipelineService("other-workspace", self.user)

        with self.assertRaises(AppApiException):
            other.get_pipeline(pipeline["id"])
        with self.assertRaises(AppApiException):
            self.service.delete_pipeline(pipeline["id"])

    @patch("models_provider.pipeline_jobs.scheduler")
    @patch("models_provider.pipeline_jobs.RedisLock")
    def test_scheduler_registration_uses_project_lock_contract(self, lock_class, scheduler):
        lock = lock_class.return_value
        lock.try_lock.return_value = True
        scheduler.get_job.return_value = None

        pipeline_jobs.run()

        lock.try_lock.assert_called_once_with(pipeline_jobs.LOCK_KEY, timeout=60)
        scheduler.add_job.assert_called_once()
        self.assertEqual(scheduler.add_job.call_args.kwargs["id"], pipeline_jobs.JOB_ID)
        lock.un_lock.assert_called_once_with(pipeline_jobs.LOCK_KEY)
