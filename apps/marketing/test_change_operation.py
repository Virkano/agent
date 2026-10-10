import json
from types import SimpleNamespace

from django.test import TestCase
from rest_framework.test import APIClient

from common.exception.app_exception import AppApiException
from marketing.models import (
    ChangeConfirmation,
    ChangeConfirmationStatus,
    ChangeOperation,
    ChangeOperationStatus,
    ChangeRiskAssessment,
    ChangeRiskLevel,
)
from marketing.serializers import ChangeOperationRiskService
from users.models import User


class ChangeOperationRiskFixture(TestCase):
    def setUp(self):
        self.workspace_id = "change-operation-test"
        self.user = User.objects.create(
            username="change_operation_user",
            nick_name="变更确认管理员",
            password="x",
            role="ADMIN",
        )
        self.service = ChangeOperationRiskService(self.workspace_id, self.user)

    def create_operation(self, **overrides):
        data = {
            "code": "CHANGE-TEST-001",
            "name": "核心套餐配置变更",
            "operation_type": "CONFIG_CHANGE",
            "description": "验证红黄绿风险判定",
        }
        data.update(overrides)
        return self.service.create(data)["operation"]


class ChangeOperationRiskServiceTests(ChangeOperationRiskFixture):
    def test_green_operation_is_automatically_approved(self):
        operation = self.create_operation()

        result = self.service.evaluate(operation["id"], {})

        self.assertEqual(result["assessment"]["risk_level"], ChangeRiskLevel.GREEN)
        self.assertEqual(result["assessment"]["risk_score"], 0)
        self.assertFalse(result["requires_confirmation"])
        self.assertEqual(result["operation"]["status"], ChangeOperationStatus.APPROVED)
        self.assertEqual(result["operation"]["confirmation_status"], ChangeConfirmationStatus.NOT_REQUIRED)

    def test_critical_consistency_failure_requires_confirmation_and_is_idempotent(self):
        operation = self.create_operation()
        evaluated = self.service.evaluate(
            operation["id"],
            {
                "consistency_passed": False,
                "affected_customer_count": 100,
            },
        )

        first = self.service.confirm(
            operation["id"],
            {
                "request_id": "confirm:test:001",
                "decision": "APPROVE",
                "comment": "已核验回退窗口，同意执行",
            },
        )
        duplicate = self.service.confirm(
            operation["id"],
            {
                "request_id": "confirm:test:001",
                "decision": "APPROVE",
                "comment": "已核验回退窗口，同意执行",
            },
        )

        self.assertEqual(evaluated["assessment"]["risk_level"], ChangeRiskLevel.RED)
        self.assertTrue(evaluated["requires_confirmation"])
        self.assertEqual(first["operation"]["status"], ChangeOperationStatus.APPROVED)
        self.assertTrue(first["created"])
        self.assertFalse(duplicate["created"])
        self.assertEqual(ChangeConfirmation.objects.count(), 1)

        another = self.create_operation(code="CHANGE-TEST-002")
        self.service.evaluate(another["id"], {"consistency_passed": False})
        with self.assertRaises(AppApiException):
            self.service.confirm(
                another["id"],
                {
                    "request_id": "confirm:test:001",
                    "decision": "APPROVE",
                    "comment": "不能复用其他变更的确认键",
                },
            )

    def test_reevaluation_preserves_assessment_history(self):
        operation = self.create_operation()
        self.service.evaluate(operation["id"], {"business_logic_passed": False})

        second = self.service.evaluate(operation["id"], {"instruction_complete": False})
        detail = self.service.detail(operation["id"])

        self.assertEqual(second["assessment"]["revision"], 2)
        self.assertEqual(second["assessment"]["risk_level"], ChangeRiskLevel.YELLOW)
        self.assertEqual(detail["status"], ChangeOperationStatus.RISK_EVALUATED)
        self.assertEqual(len(detail["assessments"]), 2)
        self.assertEqual(ChangeRiskAssessment.objects.filter(operation_id=operation["id"]).count(), 2)


class ChangeOperationRiskApiTests(ChangeOperationRiskFixture):
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

    @staticmethod
    def response_data(response):
        assert response.status_code == 200, response.content
        return json.loads(response.content)["data"]

    def test_api_red_risk_rejection_full_chain(self):
        prefix = f"/admin/api/workspace/{self.workspace_id}/marketing/ivr/change"
        created = self.response_data(
            self.client.post(
                f"{prefix}/operation",
                {
                    "code": "CHANGE-API-001",
                    "name": "跨系统割接",
                    "operation_type": "NETWORK_CUTOVER",
                },
                format="json",
            )
        )
        operation_id = created["operation"]["id"]
        evaluated = self.response_data(
            self.client.post(
                f"{prefix}/operation/{operation_id}/evaluate",
                {
                    "cross_system_change": True,
                    "rollback_plan_ready": False,
                    "emergency_change": True,
                    "affected_customer_count": 12000,
                },
                format="json",
            )
        )
        confirmed = self.response_data(
            self.client.post(
                f"{prefix}/operation/{operation_id}/confirm",
                {
                    "request_id": "confirm:api:reject:001",
                    "decision": "REJECT",
                    "comment": "回退方案未就绪，禁止执行",
                },
                format="json",
            )
        )
        detail = self.response_data(self.client.get(f"{prefix}/operation/{operation_id}"))
        dashboard = self.response_data(self.client.get(f"{prefix}/dashboard"))

        self.assertTrue(created["created"])
        self.assertEqual(evaluated["assessment"]["risk_level"], ChangeRiskLevel.RED)
        self.assertEqual(evaluated["assessment"]["risk_score"], 100)
        self.assertEqual(confirmed["operation"]["status"], ChangeOperationStatus.REJECTED)
        self.assertEqual(detail["confirmations"][0]["comment"], "回退方案未就绪，禁止执行")
        self.assertEqual(dashboard["summary"]["red_count"], 1)
        self.assertEqual(dashboard["summary"]["pending_confirmation_count"], 0)
        self.assertEqual(ChangeOperation.objects.count(), 1)
