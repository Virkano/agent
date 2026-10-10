import json
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from marketing.models import MarketingNotification
from models_provider.models import LifecycleModelVersion, LifecycleModelVersionStatus
from users.models import User

from .models import MonitoringAlertStatus, MonitoringMetricStatus, PlatformMonitoringAlert, PlatformMonitoringRule
from .serializers import PlatformMonitoringService, _metric


class PlatformMonitoringServiceTests(TestCase):
    def setUp(self):
        self.workspace_id = "default"
        self.user = User.objects.create(
            username="platform_monitoring_user",
            nick_name="平台监控管理员",
            password="x",
            role="ADMIN",
        )
        self.service = PlatformMonitoringService(self.workspace_id, self.user)

    @staticmethod
    def healthy_resource_metrics():
        return [
            _metric("backend_available", 1),
            _metric("database_available", 1),
            _metric("redis_available", 1),
            _metric("ollama_available", 1),
            _metric("vector_service_available", 1),
        ]

    @patch.object(PlatformMonitoringService, "_collect_resource_metrics", side_effect=healthy_resource_metrics)
    def test_collect_builds_four_dimension_dashboard_and_default_rules(self, _resource):
        dashboard = self.service.collect()

        self.assertEqual(dashboard["latest_run"]["status"], "SUCCESS")
        self.assertEqual(dashboard["summary"]["metric_count"], 17)
        self.assertEqual({item["scope"] for item in dashboard["scopes"]}, {"MODEL", "DATA", "KNOWLEDGE", "RESOURCE"})
        self.assertEqual(PlatformMonitoringRule.objects.filter(workspace_id=self.workspace_id).count(), 10)
        rule = PlatformMonitoringRule.objects.filter(workspace_id=self.workspace_id).first()
        updated = self.service.save_rule({"enabled": False}, str(rule.id))
        self.assertFalse(updated["enabled"])

    @patch.object(PlatformMonitoringService, "_collect_resource_metrics", side_effect=healthy_resource_metrics)
    def test_rule_creates_alert_rollback_task_and_global_bell_notification(self, _resource):
        rule = self.service.save_rule(
            {
                "name": "发布模型缺失验收规则",
                "metric_key": "published_model_count",
                "operator": "LT",
                "warning_threshold": 1,
                "critical_threshold": 0.5,
                "auto_action": "CREATE_ROLLBACK_TASK",
            }
        )

        dashboard = self.service.collect()

        alert = PlatformMonitoringAlert.objects.get(rule_id=rule["id"])
        self.assertEqual(alert.severity, MonitoringMetricStatus.CRITICAL)
        self.assertEqual(alert.response_status, "TASK_CREATED")
        self.assertEqual(dashboard["summary"]["active_alert_count"], 1)
        notice = MarketingNotification.objects.get(
            source_type="PLATFORM_ALERT",
            source_id=str(alert.id),
            user=self.user,
        )
        self.assertEqual(notice.target_route, f"/platform-monitoring?alert_id={alert.id}")

    @patch.object(PlatformMonitoringService, "_collect_resource_metrics", side_effect=healthy_resource_metrics)
    def test_recovered_metric_resolves_existing_alert(self, _resource):
        rule = self.service.save_rule(
            {
                "name": "发布模型恢复验收规则",
                "metric_key": "published_model_count",
                "operator": "LT",
                "warning_threshold": 1,
                "critical_threshold": 0.5,
            }
        )
        self.service.collect()
        LifecycleModelVersion.objects.create(
            workspace_id=self.workspace_id,
            registry_name="monitoring-recovery-model",
            version=1,
            status=LifecycleModelVersionStatus.PUBLISHED,
        )

        dashboard = self.service.collect()

        alert = PlatformMonitoringAlert.objects.get(rule_id=rule["id"])
        self.assertEqual(alert.status, MonitoringAlertStatus.RESOLVED)
        self.assertEqual(dashboard["summary"]["active_alert_count"], 0)

    @patch.object(PlatformMonitoringService, "_collect_resource_metrics", side_effect=healthy_resource_metrics)
    def test_alert_can_be_acknowledged_and_resolved(self, _resource):
        rule = self.service.save_rule(
            {
                "name": "告警处置验收规则",
                "metric_key": "published_model_count",
                "operator": "LT",
                "warning_threshold": 1,
            }
        )
        self.service.collect()
        alert = PlatformMonitoringAlert.objects.get(rule_id=rule["id"])

        acknowledged = self.service.operate_alert(str(alert.id), "ACKNOWLEDGE")
        resolved = self.service.operate_alert(str(alert.id), "RESOLVE")

        self.assertEqual(acknowledged["status"], MonitoringAlertStatus.ACKNOWLEDGED)
        self.assertEqual(resolved["status"], MonitoringAlertStatus.RESOLVED)


class PlatformMonitoringApiTests(TestCase):
    def setUp(self):
        self.workspace_id = "monitoring-api-workspace"
        self.user = User.objects.create(
            username="platform_monitoring_api_user",
            nick_name="平台监控接口管理员",
            password="x",
            role="WORKSPACE_MANAGE",
        )
        self.client = APIClient()
        auth = SimpleNamespace(
            role_list=[f"WORKSPACE_MANAGE:/WORKSPACE/{self.workspace_id}"],
            permission_list=[],
        )
        self.client.force_authenticate(user=self.user, token=auth)

    @patch.object(PlatformMonitoringService, "_collect_resource_metrics", side_effect=PlatformMonitoringServiceTests.healthy_resource_metrics)
    def test_collect_and_dashboard_api(self, _resource):
        collect_response = self.client.post(
            f"/admin/api/workspace/{self.workspace_id}/platform-monitoring/collect",
            data={},
            format="json",
        )
        dashboard_response = self.client.get(
            f"/admin/api/workspace/{self.workspace_id}/platform-monitoring/dashboard"
        )

        collect_payload = json.loads(collect_response.content)
        dashboard_payload = json.loads(dashboard_response.content)
        self.assertEqual(collect_response.status_code, 200)
        self.assertEqual(collect_payload["code"], 200)
        self.assertEqual(collect_payload["data"]["summary"]["metric_count"], 17)
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertEqual(dashboard_payload["data"]["latest_run"]["status"], "SUCCESS")
