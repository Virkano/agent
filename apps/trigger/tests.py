import json
from datetime import timedelta
from types import SimpleNamespace

from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from users.models import User

from .models import DispatchResourceLease, DispatchTask, DispatchTaskStatus, ResourceLeaseStatus
from .resource_coordination import ResourceCoordinationService


class ResourceCoordinationFixture(TestCase):
    def setUp(self):
        self.workspace_id = "dispatch-test"
        self.user = User.objects.create(
            username="dispatch_admin",
            nick_name="调度管理员",
            password="x",
            role="WORKSPACE_MANAGE",
        )
        self.service = ResourceCoordinationService(self.workspace_id, self.user)

    def create_pool(self, code="AGENT_CORE", capacity=1, max_units=1, timeout=300):
        return self.service.create_pool(
            {
                "code": code,
                "name": f"{code} 资源池",
                "resource_type": "AGENT",
                "capacity": capacity,
                "max_units_per_task": max_units,
                "lease_timeout_seconds": timeout,
                "description": "资源协调验收池",
            }
        )

    def submit(self, pool_id, suffix, priority=50, units=1, mutex_keys=None):
        return self.service.submit_task(
            pool_id,
            {
                "request_id": f"request:{suffix}",
                "idempotency_key": f"idempotency:{suffix}",
                "name": f"调度任务 {suffix}",
                "source": "SYSTEM",
                "source_reference": f"event:{suffix}",
                "priority": priority,
                "required_units": units,
                "mutex_keys": mutex_keys or [],
                "payload": {"suffix": suffix},
            },
        )


class ResourceCoordinationServiceTests(ResourceCoordinationFixture):
    def test_priority_queue_allocates_high_priority_first(self):
        pool = self.create_pool()
        blocker = self.submit(pool["id"], "blocker", priority=10)["task"]
        low = self.submit(pool["id"], "low", priority=20)["task"]
        high = self.submit(pool["id"], "high", priority=90)["task"]

        self.assertEqual(blocker["status"], DispatchTaskStatus.RUNNING)
        self.assertEqual(low["status"], DispatchTaskStatus.QUEUED)
        self.assertEqual(high["status"], DispatchTaskStatus.QUEUED)

        result = self.service.operate_task(blocker["id"], {"action": "SUCCEED", "note": "释放配额"})
        self.assertIn(high["id"], result["allocated_task_ids"])
        self.assertEqual(self.service.task_detail(high["id"])["status"], DispatchTaskStatus.RUNNING)
        self.assertEqual(self.service.task_detail(low["id"])["status"], DispatchTaskStatus.QUEUED)

    def test_mutex_conflict_and_idempotency(self):
        pool = self.create_pool(code="MODEL_POOL", capacity=2, max_units=2)
        first = self.submit(pool["id"], "mutex-a", mutex_keys=["model:billing"])["task"]
        second = self.submit(pool["id"], "mutex-b", priority=80, mutex_keys=["model:billing"])["task"]
        replay = self.submit(pool["id"], "mutex-b", priority=80, mutex_keys=["model:billing"])

        self.assertEqual(first["status"], DispatchTaskStatus.RUNNING)
        self.assertEqual(second["status"], DispatchTaskStatus.QUEUED)
        self.assertIn("互斥资源冲突", second["queue_reason"])
        self.assertFalse(replay["created"])
        self.assertEqual(DispatchTask.objects.filter(workspace_id=self.workspace_id).count(), 2)

        self.service.operate_task(first["id"], {"action": "SUCCEED"})
        self.assertEqual(self.service.task_detail(second["id"])["status"], DispatchTaskStatus.RUNNING)

    def test_quota_validation_and_expired_lease_reclaim(self):
        pool = self.create_pool(code="WORKER_POOL", timeout=30)
        with self.assertRaises(ValidationError):
            self.submit(pool["id"], "too-large", units=2)

        running = self.submit(pool["id"], "running", priority=20)["task"]
        waiting = self.submit(pool["id"], "waiting", priority=90)["task"]
        lease = DispatchResourceLease.objects.get(task_id=running["id"])
        lease.expires_at = timezone.now() - timedelta(seconds=1)
        lease.save(update_fields=["expires_at", "update_time"])

        result = self.service.reclaim_pool(pool["id"])
        self.assertIn(str(lease.id), result["expired_lease_ids"])
        self.assertIn(waiting["id"], result["allocated_task_ids"])
        self.assertEqual(self.service.task_detail(running["id"])["status"], DispatchTaskStatus.FAILED)
        self.assertEqual(
            DispatchResourceLease.objects.get(id=lease.id).status,
            ResourceLeaseStatus.EXPIRED,
        )


class ResourceCoordinationApiTests(ResourceCoordinationFixture):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.client.force_authenticate(
            user=self.user,
            token=SimpleNamespace(
                role_list=[f"WORKSPACE_MANAGE:/WORKSPACE/{self.workspace_id}"],
                permission_list=[],
            ),
        )
        self.prefix = f"/admin/api/workspace/{self.workspace_id}/resource-coordination"

    @staticmethod
    def response_data(response):
        assert response.status_code == 200, response.content
        return json.loads(response.content)["data"]

    def test_api_pool_submit_query_operate_and_dashboard(self):
        pool = self.response_data(
            self.client.post(
                f"{self.prefix}/pool",
                {
                    "code": "API_AGENT_POOL",
                    "name": "API 智能体池",
                    "resource_type": "AGENT",
                    "capacity": 2,
                    "max_units_per_task": 1,
                    "lease_timeout_seconds": 120,
                },
                format="json",
            )
        )
        task = self.response_data(
            self.client.post(
                f"{self.prefix}/pool/{pool['id']}/task",
                {
                    "request_id": "api:task:1",
                    "idempotency_key": "api:idempotency:1",
                    "name": "API 调度任务",
                    "source": "WEBHOOK",
                    "priority": 88,
                    "required_units": 1,
                    "mutex_keys": ["customer:001"],
                },
                format="json",
            )
        )["task"]

        self.assertEqual(task["status"], DispatchTaskStatus.RUNNING)
        task_list = self.response_data(self.client.get(f"{self.prefix}/task", {"status": "RUNNING"}))
        self.assertEqual([item["id"] for item in task_list], [task["id"]])
        detail = self.response_data(self.client.get(f"{self.prefix}/task/{task['id']}"))
        self.assertEqual(len(detail["events"]), 2)
        operated = self.response_data(
            self.client.post(
                f"{self.prefix}/task/{task['id']}/operate",
                {"action": "SUCCEED", "note": "API 验收完成"},
                format="json",
            )
        )
        self.assertEqual(operated["task"]["status"], DispatchTaskStatus.SUCCEEDED)
        dashboard = self.response_data(self.client.get(f"{self.prefix}/dashboard"))
        self.assertEqual(dashboard["summary"]["pool_count"], 1)
        self.assertEqual(dashboard["summary"]["succeeded_task_count"], 1)
