import json
from types import SimpleNamespace

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from common.exception.app_exception import AppApiException
from marketing.change_quality_exports import build_change_quality_csv, build_change_quality_pdf
from marketing.models import (
    ChangeControlActionRecord,
    ChangeControlStatus,
    ChangeOperationCommunication,
    ChangeQualityReport,
    MarketingNotification,
)
from marketing.serializers import ChangeOperationControlService, ChangeOperationRiskService
from users.models import User


class ChangeOperationControlFixture(TestCase):
    def setUp(self):
        self.workspace_id = "change-control-test"
        self.user = User.objects.create(
            username="change_control_user",
            nick_name="变更管控管理员",
            password="x",
            role="ADMIN",
        )
        self.risk_service = ChangeOperationRiskService(self.workspace_id, self.user)
        self.service = ChangeOperationControlService(self.workspace_id, self.user)

    def create_evaluated_operation(self, *, code="CHANGE-CONTROL-001", risk=None):
        created = self.risk_service.create(
            {
                "code": code,
                "name": "核心网络割接",
                "operation_type": "NETWORK_CUTOVER",
            }
        )["operation"]
        self.risk_service.evaluate(created["id"], risk or {})
        return created["id"]

    def create_and_send_communication(self, operation_id, *, phase, suffix, kind="CONTROL_REMINDER"):
        created = self.service.create_communication(
            operation_id,
            {
                "request_id": f"communication:{suffix}",
                "kind": kind,
                "phase": phase,
                "audience": "OPERATOR",
                "channel": "IN_APP",
                "subject": f"{phase} 管控提醒",
                "content": "请按变更窗口完成核验并反馈。",
            },
        )["communication"]
        self.service.update_communication_status(created["id"], {"status": "SENT"})
        return created


class ChangeOperationControlServiceTests(ChangeOperationControlFixture):
    def test_control_lifecycle_requires_before_and_during_communications(self):
        operation_id = self.create_evaluated_operation()

        with self.assertRaises(AppApiException):
            self.service.control(operation_id, {"action": "START"})

        self.create_and_send_communication(operation_id, phase="BEFORE", suffix="before")
        started = self.service.control(operation_id, {"action": "START", "note": "窗口已开启"})
        self.assertEqual(started["operation"]["control_status"], ChangeControlStatus.IN_PROGRESS)

        with self.assertRaises(AppApiException):
            self.service.control(operation_id, {"action": "COMPLETE"})

        during = self.create_and_send_communication(
            operation_id,
            phase="DURING",
            suffix="during",
            kind="CUTOVER_NOTICE",
        )
        acknowledged = self.service.update_communication_status(during["id"], {"status": "ACKNOWLEDGED"})
        completed = self.service.control(operation_id, {"action": "COMPLETE", "note": "指标恢复正常"})

        self.assertEqual(acknowledged["communication"]["status"], "ACKNOWLEDGED")
        self.assertEqual(completed["operation"]["control_status"], ChangeControlStatus.COMPLETED)
        self.assertEqual(ChangeControlActionRecord.objects.filter(operation_id=operation_id).count(), 2)
        self.assertEqual(MarketingNotification.objects.filter(workspace_id=self.workspace_id).count(), 2)

    def test_communication_idempotency_and_transition_rules(self):
        operation_id = self.create_evaluated_operation()
        payload = {
            "request_id": "communication:idempotent",
            "kind": "CONTROL_REMINDER",
            "phase": "BEFORE",
            "audience": "OPERATOR",
            "channel": "IN_APP",
            "subject": "变更前提醒",
            "content": "执行前确认回退方案。",
        }
        first = self.service.create_communication(operation_id, payload)
        duplicate = self.service.create_communication(operation_id, payload)
        sent = self.service.update_communication_status(first["communication"]["id"], {"status": "SENT"})
        duplicate_sent = self.service.update_communication_status(first["communication"]["id"], {"status": "SENT"})

        self.assertTrue(first["created"])
        self.assertFalse(duplicate["created"])
        self.assertTrue(sent["changed"])
        self.assertFalse(duplicate_sent["changed"])
        self.assertEqual(ChangeOperationCommunication.objects.count(), 1)
        self.service.update_communication_status(first["communication"]["id"], {"status": "ACKNOWLEDGED"})
        with self.assertRaises(AppApiException):
            self.service.update_communication_status(
                first["communication"]["id"],
                {"status": "FAILED", "failure_reason": "终态不能变更"},
            )

    def test_quality_report_snapshot_drilldown_and_exports(self):
        operation_id = self.create_evaluated_operation()
        self.create_and_send_communication(operation_id, phase="BEFORE", suffix="report-before")
        self.service.control(operation_id, {"action": "START"})
        self.create_and_send_communication(operation_id, phase="DURING", suffix="report-during")
        self.service.control(operation_id, {"action": "COMPLETE"})
        today = timezone.localdate()

        report_data = self.service.generate_report(
            {"period_start": today.isoformat(), "period_end": today.isoformat(), "title": "变更质量日报"}
        )
        report = ChangeQualityReport.objects.get(id=report_data["id"])
        drilldown = self.service.report_drilldown(report.id, today.isoformat())
        csv_content = build_change_quality_csv(report)
        pdf_content = build_change_quality_pdf(report)

        self.assertEqual(report.metrics["operation_count"], 1)
        self.assertEqual(report.metrics["completed_count"], 1)
        self.assertEqual(report.metrics["communication_coverage_rate"], 100.0)
        self.assertEqual(drilldown["summary"]["completed_count"], 1)
        self.assertTrue(csv_content.startswith(b"\xef\xbb\xbf"))
        self.assertIn("变更质量日报".encode(), csv_content)
        self.assertTrue(pdf_content.startswith(b"%PDF"))
        self.assertGreater(len(pdf_content), 10000)


class ChangeOperationControlApiTests(ChangeOperationControlFixture):
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

    def test_api_communication_control_report_and_export(self):
        operation_id = self.create_evaluated_operation()
        prefix = f"/admin/api/workspace/{self.workspace_id}/marketing/ivr/change"
        communication = self.response_data(
            self.client.post(
                f"{prefix}/operation/{operation_id}/communication",
                {
                    "request_id": "communication:api:before",
                    "kind": "CONTROL_REMINDER",
                    "phase": "BEFORE",
                    "audience": "OPERATOR",
                    "channel": "IN_APP",
                    "subject": "API 变更前提醒",
                    "content": "请完成割接前核验。",
                },
                format="json",
            )
        )["communication"]
        self.response_data(
            self.client.post(
                f"{prefix}/communication/{communication['id']}/status",
                {"status": "SENT"},
                format="json",
            )
        )
        started = self.response_data(
            self.client.post(
                f"{prefix}/operation/{operation_id}/control",
                {"action": "START", "note": "API 开始"},
                format="json",
            )
        )
        today = timezone.localdate().isoformat()
        report = self.response_data(
            self.client.post(
                f"{prefix}/quality/report",
                {"period_start": today, "period_end": today},
                format="json",
            )
        )
        dashboard = self.response_data(self.client.get(f"{prefix}/control/dashboard"))
        drilldown = self.response_data(
            self.client.get(f"{prefix}/quality/report/{report['id']}/drilldown", {"date": today})
        )
        csv_response = self.client.get(f"{prefix}/quality/report/{report['id']}/export/csv")
        pdf_response = self.client.get(f"{prefix}/quality/report/{report['id']}/export/pdf")

        self.assertEqual(started["operation"]["control_status"], ChangeControlStatus.IN_PROGRESS)
        self.assertEqual(dashboard["summary"]["in_progress_count"], 1)
        self.assertEqual(drilldown["summary"]["operation_count"], 1)
        self.assertEqual(csv_response.status_code, 200)
        self.assertEqual(csv_response["Content-Type"], "text/csv; charset=utf-8")
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")
