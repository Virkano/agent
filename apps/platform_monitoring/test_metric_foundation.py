import json
from types import SimpleNamespace

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from datetime import timedelta

from marketing.models import MarketingNotification
from trigger.event_orchestration import EventOrchestrationService
from trigger.models import FlowRunStatus
from users.models import User

from .business_metric_collectors import collect_recommendation_review_metrics
from .metric_foundation import MetricFoundationService
from .models import (
    MetricAlertIncident,
    MetricAlertRuleVersion,
    MetricCollectionBatch,
    MetricComplianceStatus,
    MetricDataSource,
    MetricDefinition,
    MetricDispatchEventAction,
    MetricDispatchOrder,
    MetricDispatchOrderEvent,
    MetricDynamicBaseline,
    MetricTheme,
    MetricWorkOrderStatus,
)


class MetricFoundationServiceTests(TestCase):
    def setUp(self):
        self.workspace_id = "metric-foundation-test"
        self.user = User.objects.create(
            username="metric_foundation_user",
            nick_name="指标值班员",
            password="x",
            role="WORKSPACE_MANAGE",
        )
        self.service = MetricFoundationService(self.workspace_id, self.user)

    def test_bootstrap_builds_eight_themes_dynamic_baseline_and_dispatch(self):
        result = self.service.bootstrap_demo()

        self.assertEqual(MetricDefinition.objects.filter(workspace_id=self.workspace_id).count(), 8)
        self.assertEqual(
            set(MetricDefinition.objects.filter(workspace_id=self.workspace_id).values_list("theme", flat=True)),
            set(MetricTheme.values),
        )
        self.assertGreater(MetricDynamicBaseline.objects.filter(workspace_id=self.workspace_id).count(), 0)
        incident = MetricAlertIncident.objects.get(workspace_id=self.workspace_id)
        order = MetricDispatchOrder.objects.get(workspace_id=self.workspace_id, incident=incident)
        self.assertEqual(incident.config_version, 1)
        self.assertEqual(order.status, MetricWorkOrderStatus.ASSIGNED)
        self.assertEqual(order.assignee, self.user)
        self.assertEqual(result["overview"]["summary"]["theme_count"], 8)
        self.assertTrue(
            MarketingNotification.objects.filter(
                workspace_id=self.workspace_id,
                source_type="METRIC_DISPATCH_ORDER",
                source_id=str(order.id),
                user=self.user,
            ).exists()
        )

    def test_rule_versions_are_immutable_and_failed_compliance_rule_does_not_fire(self):
        definition = self.service.save_definition(
            {
                "metric_key": "delivery_delay_hours",
                "name": "交付延期时长",
                "theme": MetricTheme.DELIVERY,
                "unit": "小时",
                "dimensions_schema": ["device"],
            }
        )
        rule = self.service.save_rule(
            {
                "definition_id": definition["id"],
                "name": "无效动态规则",
                "mode": "DYNAMIC",
                "direction": "ABOVE",
                "warning_deviation": 3,
                "critical_deviation": 2,
                "baseline_window": 3,
            }
        )
        updated = self.service.save_rule({"critical_deviation": 4}, rule["id"])

        versions = MetricAlertRuleVersion.objects.filter(rule_id=rule["id"]).order_by("version")
        self.assertEqual(rule["compliance_status"], MetricComplianceStatus.FAILED)
        self.assertEqual(updated["compliance_status"], MetricComplianceStatus.PASSED)
        self.assertEqual(list(versions.values_list("version", flat=True)), [1, 2])
        self.assertEqual(versions.first().config_snapshot["critical_deviation"], 2)

    def test_import_keeps_row_errors_and_order_closes_through_state_machine(self):
        bootstrap = self.service.bootstrap_demo()
        result = self.service.import_batch(
            {
                "batch_no": "PARTIAL-001",
                "rows": [
                    {
                        "metric_key": "network_availability",
                        "value": 99.9,
                        "dimensions": {
                            "device": "核心路由器-01",
                            "network_element": "NE-HZ-001",
                            "time_slot": "全天",
                        },
                    },
                    {"metric_key": "unknown_metric", "value": 1},
                ],
            }
        )
        order_id = bootstrap["overview"]["orders"][0]["id"]

        claimed = self.service.operate_order(order_id, "CLAIM")
        processing = self.service.operate_order(order_id, "START")
        resolved = self.service.operate_order(order_id, "RESOLVE")
        closed = self.service.operate_order(order_id, "CLOSE")

        self.assertEqual(result["status"], "PARTIAL")
        self.assertEqual(result["accepted_rows"], 1)
        self.assertEqual(result["rejected_rows"], 1)
        self.assertEqual(claimed["status"], "CLAIMED")
        self.assertEqual(processing["status"], "PROCESSING")
        self.assertEqual(resolved["status"], "RESOLVED")
        self.assertEqual(closed["status"], "CLOSED")
        self.assertEqual(MetricCollectionBatch.objects.get(batch_no="PARTIAL-001").error_rows[0]["row"], 2)
        self.assertEqual(
            list(
                MetricDispatchOrderEvent.objects.filter(order_id=order_id).values_list("action", flat=True)
            ),
            ["CREATED", "CLAIMED", "STARTED", "RESOLVED", "CLOSED"],
        )

    def test_recommendation_review_collector_is_idempotent_and_resolves(self):
        definition = self.service.save_definition({
            "metric_key": "m12_recommendation_review_pending",
            "name": "推荐待人工复核节点数",
            "theme": "DELIVERY",
            "unit": "个",
            "dimensions_schema": ["task_id", "ranking_run_id", "flow_run_id"],
        })
        self.service.save_rule({
            "definition_id": definition["id"],
            "name": "推荐待人工复核预警",
            "mode": "STATIC",
            "direction": "ABOVE",
            "warning_threshold": 0,
            "critical_threshold": 5,
        })
        orchestration = EventOrchestrationService(self.workspace_id, self.user)
        orchestration.create_flow({
            "code": "RECOMMENDATION_REVIEW_METRIC",
            "name": "推荐曝光复核指标",
            "event_type": "marketing.recommendation.exposed",
            "source_types": ["SYSTEM"],
            "event_schema": {"required": ["task_id", "ranking_run_id"]},
            "nodes": [{"code": "REVIEW", "name": "人工复核", "node_type": "MANUAL"}],
            "publish": True,
        })
        received = orchestration.receive_event({
            "event_id": "RECOMMENDATION-METRIC-001",
            "idempotency_key": "RECOMMENDATION-METRIC-001",
            "source_type": "SYSTEM",
            "event_type": "marketing.recommendation.exposed",
            "payload": {"task_id": "TASK-001", "ranking_run_id": "RANKING-001"},
        })
        run_id = received["runs"][0]["id"]

        first = collect_recommendation_review_metrics()
        replay = collect_recommendation_review_metrics()

        self.assertEqual(first["created_count"], 1)
        self.assertEqual(replay["created_count"], 0)
        self.assertEqual(replay["reused_count"], 1)
        self.assertEqual(MetricCollectionBatch.objects.filter(workspace_id=self.workspace_id).count(), 1)
        incident = MetricAlertIncident.objects.get(workspace_id=self.workspace_id)
        self.assertEqual(incident.observed_value, 1)
        self.assertEqual(MetricDispatchOrder.objects.filter(incident=incident).count(), 1)

        detail = orchestration.run_detail(run_id)
        review = next(row for row in detail["nodes"] if row["node_code"] == "REVIEW")
        completed = orchestration.operate_node(
            run_id, review["id"], {"action": "APPROVE", "note": "验收通过"}
        )
        resolved = collect_recommendation_review_metrics()

        self.assertEqual(completed["status"], FlowRunStatus.SUCCEEDED)
        self.assertEqual(resolved["created_count"], 1)
        self.assertEqual(MetricCollectionBatch.objects.filter(workspace_id=self.workspace_id).count(), 2)
        incident.refresh_from_db()
        self.assertEqual(incident.status, "RESOLVED")
        self.assertEqual(incident.observed_value, 1)
        self.assertEqual(MetricDispatchOrder.objects.filter(incident=incident).count(), 1)

    def test_configuration_duty_calendar_and_manual_order_events(self):
        source = self.service.save_source(
            {
                "source_key": "network_api",
                "name": "综合网管接口",
                "source_type": "API",
                "config_snapshot": {"endpoint": "/metrics/network", "schedule": "*/5 * * * *"},
            }
        )
        updated_source = self.service.save_source({"name": "综合网管指标接口"}, source["id"])
        now = timezone.now()
        shift = self.service.save_duty_shift(
            {
                "name": "白班",
                "starts_at": now - timedelta(hours=12),
                "ends_at": now + timedelta(hours=8),
                "assignee_id": str(self.user.id),
            }
        )

        self.assertEqual(updated_source["name"], "综合网管指标接口")
        self.assertEqual(MetricDataSource.objects.get(id=source["id"]).config_snapshot["endpoint"], "/metrics/network")
        with self.assertRaises(Exception):
            self.service.save_source(
                {
                    "source_key": "unsafe_source",
                    "name": "不得落库的敏感配置",
                    "source_type": "DATABASE",
                    "config_snapshot": {"connection": {"password": "not-persisted"}},
                }
            )
        self.assertEqual(self.service.list_duty_shifts()[0]["id"], shift["id"])
        with self.assertRaises(Exception):
            self.service.save_duty_shift(
                {
                    "name": "重叠班次",
                    "starts_at": now - timedelta(hours=1),
                    "ends_at": now + timedelta(hours=2),
                    "assignee_id": str(self.user.id),
                }
            )

        self.service.bootstrap_demo()
        order = MetricDispatchOrder.objects.filter(workspace_id=self.workspace_id).first()
        self.service.operate_order(str(order.id), {"action": "TRANSFER", "assignee_id": str(self.user.id), "note": "交接复核"})
        self.service.operate_order(str(order.id), {"action": "COMMENT", "note": "已核对上游采集链路"})
        actions = list(order.events.values_list("action", flat=True))
        self.assertIn(MetricDispatchEventAction.TRANSFERRED, actions)
        self.assertIn(MetricDispatchEventAction.COMMENTED, actions)
        self.assertEqual(self.service.list_order_events(str(order.id))[-1]["note"], "已核对上游采集链路")

    def test_eight_theme_analytics_filters_and_observation_drilldown(self):
        self.service.bootstrap_demo()
        definition = MetricDefinition.objects.get(
            workspace_id=self.workspace_id,
            metric_key="fault_recovery_minutes",
        )
        analytics = self.service.metric_analytics(
            {
                "theme": MetricTheme.TROUBLESHOOTING,
                "definition_id": str(definition.id),
                "device": "核心路由器-01",
                "network_element": "NE-HZ-001",
                "time_slot": "全天",
            }
        )

        self.assertEqual(len(analytics["theme_stats"]), 8)
        self.assertTrue(all(item["observation_count"] >= 6 for item in analytics["theme_stats"]))
        self.assertEqual(analytics["summary"]["observation_count"], 6)
        self.assertEqual(analytics["summary"]["alert_count"], 1)
        self.assertGreater(sum(point["baseline_mean"] is not None for point in analytics["points"]), 0)
        alert_point = next(point for point in analytics["points"] if point["alert"])
        detail = self.service.observation_detail(alert_point["id"])

        self.assertEqual(detail["observation"]["definition"]["metric_key"], "fault_recovery_minutes")
        self.assertEqual(detail["batch"]["accepted_rows"], 48)
        self.assertEqual(len(detail["incidents"]), 1)
        self.assertEqual(len(detail["incidents"][0]["orders"]), 1)
        self.assertEqual(detail["incidents"][0]["orders"][0]["events"][0]["action"], "CREATED")

    def test_reopened_incident_creates_a_new_dispatch_order(self):
        self.service.bootstrap_demo()
        definition = self.service.save_definition(
            {
                "metric_key": "security_gap_count",
                "name": "安全缺口数",
                "theme": MetricTheme.SECURITY,
                "unit": "项",
            }
        )
        self.service.save_rule(
            {
                "definition_id": definition["id"],
                "name": "安全缺口固定阈值",
                "mode": "STATIC",
                "direction": "ABOVE",
                "warning_threshold": 3,
                "critical_threshold": 5,
            }
        )
        self.service.import_batch(
            {"batch_no": "REOPEN-001", "rows": [{"metric_key": "security_gap_count", "value": 8}]}
        )
        first_order = MetricDispatchOrder.objects.filter(
            workspace_id=self.workspace_id,
            incident__rule__name="安全缺口固定阈值",
        ).get()
        for action in ("CLAIM", "START", "RESOLVE", "CLOSE"):
            self.service.operate_order(str(first_order.id), action)
        self.service.import_batch(
            {"batch_no": "REOPEN-002", "rows": [{"metric_key": "security_gap_count", "value": 9}]}
        )

        orders = MetricDispatchOrder.objects.filter(
            workspace_id=self.workspace_id,
            incident__rule__name="安全缺口固定阈值",
        ).order_by("create_time")
        self.assertEqual(orders.count(), 2)
        self.assertEqual(orders.first().status, MetricWorkOrderStatus.CLOSED)
        self.assertEqual(orders.last().status, MetricWorkOrderStatus.ASSIGNED)


class MetricFoundationApiTests(TestCase):
    def setUp(self):
        self.workspace_id = "metric-foundation-api"
        self.user = User.objects.create(
            username="metric_foundation_api_user",
            nick_name="指标接口管理员",
            password="x",
            role="WORKSPACE_MANAGE",
        )
        self.client = APIClient()
        self.client.force_authenticate(
            user=self.user,
            token=SimpleNamespace(
                role_list=[f"WORKSPACE_MANAGE:/WORKSPACE/{self.workspace_id}"],
                permission_list=[],
            ),
        )

    def test_bootstrap_and_overview_api(self):
        bootstrap_response = self.client.post(
            f"/admin/api/workspace/{self.workspace_id}/metric-foundation/bootstrap",
            data={},
            format="json",
        )
        overview_response = self.client.get(
            f"/admin/api/workspace/{self.workspace_id}/metric-foundation/overview"
        )

        bootstrap_payload = json.loads(bootstrap_response.content)
        overview_payload = json.loads(overview_response.content)
        self.assertEqual(bootstrap_response.status_code, 200)
        self.assertEqual(bootstrap_payload["code"], 200)
        self.assertEqual(overview_response.status_code, 200)
        self.assertEqual(overview_payload["data"]["summary"]["definition_count"], 8)
        self.assertEqual(overview_payload["data"]["summary"]["theme_count"], 8)

    def test_configuration_and_event_api(self):
        source_response = self.client.post(
            f"/admin/api/workspace/{self.workspace_id}/metric-foundation/source",
            data={
                "source_key": "manual_file",
                "name": "人工文件导入",
                "source_type": "MANUAL",
                "config_snapshot": {"format": "JSON"},
            },
            format="json",
        )
        bootstrap_response = self.client.post(
            f"/admin/api/workspace/{self.workspace_id}/metric-foundation/bootstrap",
            data={},
            format="json",
        )
        order_id = json.loads(bootstrap_response.content)["data"]["overview"]["orders"][0]["id"]
        comment_response = self.client.post(
            f"/admin/api/workspace/{self.workspace_id}/metric-foundation/order/{order_id}/operate",
            data={"action": "COMMENT", "note": "接口验收备注"},
            format="json",
        )
        event_response = self.client.get(
            f"/admin/api/workspace/{self.workspace_id}/metric-foundation/order/{order_id}/events"
        )

        self.assertEqual(source_response.status_code, 200)
        self.assertEqual(comment_response.status_code, 200)
        events = json.loads(event_response.content)["data"]
        self.assertEqual(events[-1]["action"], "COMMENTED")
        self.assertEqual(events[-1]["note"], "接口验收备注")

    def test_analytics_and_observation_detail_api(self):
        self.client.post(
            f"/admin/api/workspace/{self.workspace_id}/metric-foundation/bootstrap",
            data={},
            format="json",
        )
        definition = MetricDefinition.objects.get(
            workspace_id=self.workspace_id,
            metric_key="fault_recovery_minutes",
        )
        analytics_response = self.client.get(
            f"/admin/api/workspace/{self.workspace_id}/metric-foundation/analytics",
            {"definition_id": str(definition.id), "device": "核心路由器-01"},
        )
        analytics = json.loads(analytics_response.content)["data"]
        observation_id = analytics["points"][-1]["id"]
        detail_response = self.client.get(
            f"/admin/api/workspace/{self.workspace_id}/metric-foundation/observation/{observation_id}"
        )
        detail = json.loads(detail_response.content)["data"]

        self.assertEqual(analytics_response.status_code, 200)
        self.assertEqual(len(analytics["points"]), 6)
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail["observation"]["id"], observation_id)
