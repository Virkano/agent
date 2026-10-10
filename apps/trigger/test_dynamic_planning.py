import json
from datetime import timedelta
from types import SimpleNamespace

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from users.models import User

from .event_orchestration import EventOrchestrationService
from .models import (
    DispatchTask,
    DispatchTaskStatus,
    EventFlowNodeAttempt,
    EventFlowNodeRun,
    FlowNodeRunStatus,
    FlowRunEventType,
    FlowRunStatus,
    NodeAttemptStatus,
)
from .resource_coordination import ResourceCoordinationService


class DynamicPlanningFixture(TestCase):
    def setUp(self):
        self.workspace_id = "dynamic-planning-test"
        self.user = User.objects.create(
            username="dynamic_planner",
            nick_name="动态路径管理员",
            password="x",
            role="WORKSPACE_MANAGE",
        )
        self.coordinator = ResourceCoordinationService(self.workspace_id, self.user)
        self.service = EventOrchestrationService(self.workspace_id, self.user)
        self.pool = self.coordinator.create_pool(
            {
                "code": "DYNAMIC_WORKER",
                "name": "动态执行资源池",
                "resource_type": "WORKER",
                "capacity": 4,
                "max_units_per_task": 1,
                "lease_timeout_seconds": 300,
            }
        )

    def flow_payload(self, code="DYNAMIC_FLOW"):
        pool_id = self.pool["id"]
        return {
            "code": code,
            "name": "故障动态处置流",
            "event_type": "network.dynamic.incident",
            "source_types": ["SYSTEM"],
            "event_schema": {"required": ["alarm_id", "severity"]},
            "publish": True,
            "nodes": [
                {
                    "code": "PRIMARY",
                    "name": "主模型研判",
                    "node_type": "AGENT",
                    "resource_pool_id": pool_id,
                    "max_retries": 1,
                    "timeout_seconds": 30,
                    "failure_strategy": "FALLBACK",
                    "fallback_node_code": "RULE_FALLBACK",
                    "recovery_action": "RELEASE_AND_REROUTE",
                },
                {
                    "code": "RULE_FALLBACK",
                    "name": "规则引擎降级",
                    "node_type": "TOOL",
                    "resource_pool_id": pool_id,
                    "dependencies": ["PRIMARY"],
                    "activation_mode": "FALLBACK_ONLY",
                },
                {
                    "code": "REPORT",
                    "name": "汇总处置报告",
                    "node_type": "REPORT",
                    "resource_pool_id": pool_id,
                    "dependencies": ["PRIMARY", "RULE_FALLBACK"],
                    "dependency_mode": "ANY_SUCCESS",
                },
                {
                    "code": "CRITICAL_ALERT",
                    "name": "重大告警通知",
                    "node_type": "NOTIFICATION",
                    "resource_pool_id": pool_id,
                    "dependencies": ["REPORT"],
                    "condition": {
                        "source": "EVENT_PAYLOAD",
                        "path": "severity",
                        "operator": "EQ",
                        "value": "critical",
                    },
                },
            ],
        }

    @staticmethod
    def event_payload(suffix="001", severity="critical"):
        return {
            "event_id": f"DYNAMIC-EVT-{suffix}",
            "idempotency_key": f"dynamic-event-{suffix}",
            "source_type": "SYSTEM",
            "event_type": "network.dynamic.incident",
            "subject": f"动态路径事件 {suffix}",
            "payload": {"alarm_id": f"ALARM-{suffix}", "severity": severity},
        }

    @staticmethod
    def node(detail, code):
        return next(item for item in detail["nodes"] if item["node_code"] == code)


class DynamicPlanningServiceTests(DynamicPlanningFixture):
    def test_retry_exhausted_activates_fallback_and_run_succeeds(self):
        self.service.create_flow(self.flow_payload())
        received = self.service.receive_event(self.event_payload())
        run_id = received["runs"][0]["id"]
        detail = self.service.run_detail(run_id)

        primary = self.node(detail, "PRIMARY")
        detail = self.service.operate_node(
            run_id, primary["id"], {"action": "FAIL", "note": "模型暂时不可用"}
        )
        primary = self.node(detail, "PRIMARY")
        self.assertEqual(primary["status"], FlowNodeRunStatus.RUNNING)
        self.assertEqual(primary["active_attempt_no"], 2)

        detail = self.service.operate_node(
            run_id, primary["id"], {"action": "FAIL", "note": "重试仍然失败"}
        )
        self.assertEqual(self.node(detail, "PRIMARY")["status"], FlowNodeRunStatus.FAILED)
        self.assertTrue(self.node(detail, "PRIMARY")["failure_handled"])
        self.assertEqual(
            self.node(detail, "RULE_FALLBACK")["status"], FlowNodeRunStatus.RUNNING
        )

        detail = self.service.operate_node(
            run_id,
            self.node(detail, "RULE_FALLBACK")["id"],
            {"action": "SUCCEED", "output": {"route": "rules"}},
        )
        detail = self.service.operate_node(
            run_id,
            self.node(detail, "REPORT")["id"],
            {"action": "SUCCEED"},
        )
        detail = self.service.operate_node(
            run_id,
            self.node(detail, "CRITICAL_ALERT")["id"],
            {"action": "SUCCEED"},
        )
        self.assertEqual(detail["status"], FlowRunStatus.SUCCEEDED)
        self.assertEqual(detail["completed_node_count"], 4)
        self.assertEqual(
            EventFlowNodeAttempt.objects.filter(run_id=run_id, node_run__node_code="PRIMARY").count(),
            2,
        )
        event_types = {item["event_type"] for item in detail["events"]}
        self.assertIn(FlowRunEventType.NODE_RETRYING, event_types)
        self.assertIn(FlowRunEventType.NODE_FALLBACK, event_types)
        self.assertIn(FlowRunEventType.NODE_RECOVERED, event_types)

    def test_condition_skips_alert_and_primary_success_skips_fallback(self):
        self.service.create_flow(self.flow_payload(code="CONDITION_FLOW"))
        received = self.service.receive_event(self.event_payload("LOW", severity="warning"))
        run_id = received["runs"][0]["id"]
        detail = self.service.run_detail(run_id)
        detail = self.service.operate_node(
            run_id, self.node(detail, "PRIMARY")["id"], {"action": "SUCCEED"}
        )
        self.assertEqual(
            self.node(detail, "RULE_FALLBACK")["status"], FlowNodeRunStatus.SKIPPED
        )
        detail = self.service.operate_node(
            run_id, self.node(detail, "REPORT")["id"], {"action": "SUCCEED"}
        )
        self.assertEqual(
            self.node(detail, "CRITICAL_ALERT")["status"], FlowNodeRunStatus.SKIPPED
        )
        self.assertEqual(detail["status"], FlowRunStatus.SUCCEEDED)

    def test_timeout_releases_resource_and_enters_next_attempt(self):
        self.service.create_flow(self.flow_payload(code="TIMEOUT_FLOW"))
        received = self.service.receive_event(self.event_payload("TIMEOUT"))
        run_id = received["runs"][0]["id"]
        node = EventFlowNodeRun.objects.get(run_id=run_id, node_code="PRIMARY")
        first_task_id = node.dispatch_task_id
        stale_time = timezone.now() - timedelta(seconds=60)
        EventFlowNodeRun.objects.filter(id=node.id).update(started_at=stale_time)

        detail = self.service.advance_run(run_id)
        primary = self.node(detail, "PRIMARY")
        self.assertEqual(primary["status"], FlowNodeRunStatus.RUNNING)
        self.assertEqual(primary["active_attempt_no"], 2)
        self.assertEqual(
            DispatchTask.objects.get(id=first_task_id).status, DispatchTaskStatus.FAILED
        )
        first_attempt = EventFlowNodeAttempt.objects.get(node_run_id=node.id, attempt_no=1)
        self.assertEqual(first_attempt.status, NodeAttemptStatus.TIMED_OUT)
        self.assertIn(
            FlowRunEventType.NODE_TIMED_OUT,
            {item["event_type"] for item in detail["events"]},
        )


class DynamicPlanningApiTests(DynamicPlanningFixture):
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

    def test_failed_run_can_replay_idempotently_with_original_version(self):
        self.service.create_flow(self.flow_payload())
        event = self.service.receive_event(self.event_payload("REPLAY"))
        original_id = event["runs"][0]["id"]
        detail = self.service.run_detail(original_id)
        primary = EventFlowNodeRun.objects.get(run_id=original_id, node_code="PRIMARY")
        primary.max_retries = 0
        primary.failure_strategy = "FAIL_RUN"
        primary.save(update_fields=["max_retries", "failure_strategy", "update_time"])
        self.service.operate_node(
            original_id, self.node(detail, "PRIMARY")["id"], {"action": "FAIL"}
        )
        self.assertEqual(EventFlowNodeRun.objects.get(id=primary.id).run.status, FlowRunStatus.FAILED)

        payload = {"idempotency_key": "replay-request-001"}
        first = self.response_data(
            self.client.post(f"{self.prefix}/run/{original_id}/replay", payload, format="json")
        )
        second = self.response_data(
            self.client.post(f"{self.prefix}/run/{original_id}/replay", payload, format="json")
        )
        self.assertTrue(first["created"])
        self.assertFalse(second["created"])
        replay = first["runs"][0]
        self.assertEqual(replay["replay_of_id"], original_id)
        self.assertNotEqual(replay["trace_id"], self.service.run_detail(original_id)["trace_id"])
        self.assertEqual(replay["flow_version"], 1)
