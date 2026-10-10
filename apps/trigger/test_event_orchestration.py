import json
from types import SimpleNamespace

from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from users.models import User

from .event_orchestration import EventOrchestrationService
from .models import (
    EventFlowRun,
    FlowNodeRunStatus,
    FlowRunStatus,
    FlowVersionStatus,
    StandardEvent,
)
from .resource_coordination import ResourceCoordinationService


class EventOrchestrationFixture(TestCase):
    def setUp(self):
        self.workspace_id = "event-orchestration-test"
        self.user = User.objects.create(
            username="event_admin",
            nick_name="事件编排管理员",
            password="x",
            role="WORKSPACE_MANAGE",
        )
        self.coordinator = ResourceCoordinationService(self.workspace_id, self.user)
        self.service = EventOrchestrationService(self.workspace_id, self.user)

    def create_pool(self, code="EVENT_WORKER", capacity=2):
        return self.coordinator.create_pool(
            {
                "code": code,
                "name": f"{code} 资源池",
                "resource_type": "WORKER",
                "capacity": capacity,
                "max_units_per_task": 1,
                "lease_timeout_seconds": 300,
                "description": "事件编排测试池",
            }
        )

    def flow_payload(self, pool_id, code="INCIDENT_FLOW", publish=True):
        return {
            "code": code,
            "name": "故障分析编排",
            "description": "标准事件驱动的分析、报告与人工确认链路",
            "event_type": "network.incident.detected",
            "source_types": ["SYSTEM", "WEBHOOK"],
            "event_schema": {"required": ["alarm_id"]},
            "publish": publish,
            "nodes": [
                {
                    "code": "QUERY",
                    "name": "查询上下文",
                    "node_type": "DATA_QUERY",
                    "resource_pool_id": pool_id,
                    "dependencies": [],
                    "priority": 80,
                },
                {
                    "code": "ANALYZE",
                    "name": "智能体研判",
                    "node_type": "AGENT",
                    "resource_pool_id": pool_id,
                    "dependencies": ["QUERY"],
                    "priority": 90,
                },
                {
                    "code": "REPORT",
                    "name": "生成报告",
                    "node_type": "REPORT",
                    "resource_pool_id": pool_id,
                    "dependencies": ["ANALYZE"],
                    "priority": 70,
                },
                {
                    "code": "ALERT",
                    "name": "发送告警",
                    "node_type": "NOTIFICATION",
                    "resource_pool_id": pool_id,
                    "dependencies": ["ANALYZE"],
                    "priority": 70,
                },
                {
                    "code": "REVIEW",
                    "name": "人工复核",
                    "node_type": "MANUAL",
                    "dependencies": ["REPORT", "ALERT"],
                },
            ],
        }

    @staticmethod
    def event_payload(suffix="001"):
        return {
            "event_id": f"EVT-{suffix}",
            "idempotency_key": f"event-idempotency-{suffix}",
            "source_type": "SYSTEM",
            "event_type": "network.incident.detected",
            "subject": f"核心网告警 {suffix}",
            "payload": {"alarm_id": f"ALARM-{suffix}", "severity": "critical"},
        }

    def node(self, detail, code):
        return next(item for item in detail["nodes"] if item["node_code"] == code)


class EventOrchestrationServiceTests(EventOrchestrationFixture):
    def test_flow_version_publish_archives_previous_and_rejects_cycle(self):
        pool = self.create_pool()
        first = self.service.create_flow(self.flow_payload(pool["id"]))
        second_payload = self.flow_payload(pool["id"], publish=True)
        second_payload["name"] = "故障分析编排 V2"
        second = self.service.create_flow(second_payload)

        self.assertEqual(first["version_no"], 1)
        self.assertEqual(second["version_no"], 2)
        self.assertEqual(self.service.flow_detail(first["id"])["status"], FlowVersionStatus.ARCHIVED)
        self.assertEqual(second["status"], FlowVersionStatus.PUBLISHED)

        invalid = self.flow_payload(pool["id"], code="CYCLE_FLOW", publish=False)
        invalid["nodes"] = [
            {
                "code": "A_NODE",
                "name": "A",
                "node_type": "TOOL",
                "resource_pool_id": pool["id"],
                "dependencies": ["B_NODE"],
            },
            {
                "code": "B_NODE",
                "name": "B",
                "node_type": "TOOL",
                "resource_pool_id": pool["id"],
                "dependencies": ["A_NODE"],
            },
        ]
        with self.assertRaises(ValidationError):
            self.service.create_flow(invalid)

    def test_event_idempotency_payload_gate_and_parallel_dag(self):
        pool = self.create_pool(capacity=2)
        self.service.create_flow(self.flow_payload(pool["id"]))

        missing = self.event_payload("MISSING")
        missing["payload"] = {"severity": "critical"}
        with self.assertRaises(ValidationError):
            self.service.receive_event(missing)
        self.assertFalse(StandardEvent.objects.filter(event_id="EVT-MISSING").exists())

        received = self.service.receive_event(self.event_payload())
        replay = self.service.receive_event(self.event_payload())
        self.assertTrue(received["created"])
        self.assertFalse(replay["created"])
        self.assertEqual(StandardEvent.objects.filter(workspace_id=self.workspace_id).count(), 1)

        run_id = received["runs"][0]["id"]
        detail = self.service.run_detail(run_id)
        self.assertEqual(self.node(detail, "QUERY")["status"], FlowNodeRunStatus.RUNNING)

        detail = self.service.operate_node(
            run_id, self.node(detail, "QUERY")["id"], {"action": "SUCCEED"}
        )
        self.assertEqual(self.node(detail, "ANALYZE")["status"], FlowNodeRunStatus.RUNNING)
        detail = self.service.operate_node(
            run_id, self.node(detail, "ANALYZE")["id"], {"action": "SUCCEED"}
        )
        self.assertEqual(self.node(detail, "REPORT")["status"], FlowNodeRunStatus.RUNNING)
        self.assertEqual(self.node(detail, "ALERT")["status"], FlowNodeRunStatus.RUNNING)

        detail = self.service.operate_node(
            run_id, self.node(detail, "REPORT")["id"], {"action": "SUCCEED"}
        )
        detail = self.service.operate_node(
            run_id, self.node(detail, "ALERT")["id"], {"action": "SUCCEED"}
        )
        self.assertEqual(self.node(detail, "REVIEW")["status"], FlowNodeRunStatus.WAITING_MANUAL)
        detail = self.service.operate_node(
            run_id,
            self.node(detail, "REVIEW")["id"],
            {"action": "APPROVE", "note": "复核通过"},
        )
        self.assertEqual(detail["status"], FlowRunStatus.SUCCEEDED)
        self.assertEqual([event["sequence_no"] for event in detail["events"]], list(range(1, 17)))

    def test_waiting_resource_is_synchronized_after_capacity_release(self):
        pool = self.create_pool(capacity=1)
        blocker = self.coordinator.submit_task(
            pool["id"],
            {
                "request_id": "blocker-request",
                "idempotency_key": "blocker-idempotency",
                "name": "占用执行器",
                "source": "SYSTEM",
                "priority": 10,
                "required_units": 1,
            },
        )["task"]
        self.service.create_flow(self.flow_payload(pool["id"]))
        received = self.service.receive_event(self.event_payload("WAIT"))
        run_id = received["runs"][0]["id"]
        detail = self.service.run_detail(run_id)
        self.assertEqual(self.node(detail, "QUERY")["status"], FlowNodeRunStatus.WAITING_RESOURCE)

        self.coordinator.operate_task(blocker["id"], {"action": "SUCCEED"})
        detail = self.service.advance_run(run_id)
        self.assertEqual(self.node(detail, "QUERY")["status"], FlowNodeRunStatus.RUNNING)
        self.assertEqual(detail["status"], FlowRunStatus.RUNNING)


class EventOrchestrationApiTests(EventOrchestrationFixture):
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
        self.prefix = f"/admin/api/workspace/{self.workspace_id}/event-orchestration"

    @staticmethod
    def response_data(response):
        assert response.status_code == 200, response.content
        return json.loads(response.content)["data"]

    def test_api_create_receive_operate_and_dashboard(self):
        pool = self.create_pool(capacity=2)
        flow = self.response_data(
            self.client.post(f"{self.prefix}/flow", self.flow_payload(pool["id"]), format="json")
        )
        self.assertEqual(flow["status"], FlowVersionStatus.PUBLISHED)
        event = self.response_data(
            self.client.post(f"{self.prefix}/event", self.event_payload("API"), format="json")
        )
        run_id = event["runs"][0]["id"]
        detail = self.response_data(self.client.get(f"{self.prefix}/run/{run_id}"))
        query = self.node(detail, "QUERY")
        detail = self.response_data(
            self.client.post(
                f"{self.prefix}/run/{run_id}/node/{query['id']}/operate",
                {"action": "SUCCEED", "output": {"rows": 12}},
                format="json",
            )
        )
        self.assertEqual(self.node(detail, "ANALYZE")["status"], FlowNodeRunStatus.RUNNING)
        dashboard = self.response_data(self.client.get(f"{self.prefix}/dashboard"))
        self.assertEqual(dashboard["summary"]["published_flow_count"], 1)
        self.assertEqual(dashboard["summary"]["event_count"], 1)
        self.assertEqual(EventFlowRun.objects.get(id=run_id).status, FlowRunStatus.RUNNING)
