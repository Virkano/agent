from types import SimpleNamespace
import json

from django.test import TestCase
from rest_framework.test import APIClient

from application.models import Application, Chat, ChatRecord, ServiceAnswerReview, ServiceAnswerReviewAction
from application.service_answer_review import capture_pending_review, handle_review, page_reviews
from common.constants.permission_constants import PermissionConstants
from common.exception.app_exception import AppApiException
from users.models import User


class ServiceAnswerReviewTests(TestCase):
    def setUp(self):
        self.application = Application.objects.create(workspace_id="review-a", name="服务助手复核测试")
        self.chat = Chat.objects.create(application=self.application, abstract="测试对话")
        self.record = ChatRecord.objects.create(
            chat=self.chat,
            problem_text="资料有什么？",
            answer_text="当前答复需要人工复核，暂时无法直接展示。请联系人工客服。",
            index=1,
            details={"chat_step": {"compliance": {
                "manual_review_status": "PENDING",
                "risk_types": ["SENSITIVE_CONTENT"],
                "action": "BLOCKED",
                "reference_count": 1,
                "rule_version": "service-answer-v1",
            }}},
        )

    def test_capture_is_idempotent_and_keeps_only_metadata(self):
        first = capture_pending_review(self.record, "review-a")
        second = capture_pending_review(self.record, "review-a")
        self.assertEqual(first.id, second.id)
        self.assertEqual(ServiceAnswerReview.objects.filter(record=self.record).count(), 1)
        self.assertNotIn("资料有什么", str(first.__dict__))

    def test_queue_is_scoped_and_exposes_safe_review_context(self):
        capture_pending_review(self.record, "review-a")
        page = page_reviews("review-a", 1, 20)
        self.assertEqual(page["total"], 1)
        self.assertEqual(page["records"][0]["delivered_answer"], self.record.answer_text)
        self.assertEqual(page["records"][0]["user_question"], self.record.problem_text)
        self.assertEqual(page["records"][0]["application_name"], self.application.name)
        self.assertEqual(page["records"][0]["risk_details"][0]["label"], "命中敏感内容规则")
        self.assertNotIn("details", page["records"][0])
        self.assertEqual(page_reviews("review-b", 1, 20)["total"], 0)

    def test_queue_redacts_personal_data_in_user_question(self):
        self.record.problem_text = "请联系 13800138000 或 test@example.com，证件号 110101199001011234"
        self.record.save(update_fields=["problem_text"])
        capture_pending_review(self.record, "review-a")
        item = page_reviews("review-a", 1, 20)["records"][0]
        self.assertEqual(
            item["user_question"],
            "请联系 [手机号已脱敏] 或 [邮箱已脱敏]，证件号 [证件号已脱敏]",
        )

    def test_handle_adds_fact_and_rejects_cross_workspace_or_repeat(self):
        review = capture_pending_review(self.record, "review-a")
        reviewer = SimpleNamespace(pk="reviewer-1", username="tester")
        with self.assertRaises(AppApiException):
            handle_review("review-b", str(review.id), "CONFIRMED", "已确认", reviewer)
        result = handle_review("review-a", str(review.id), "CONFIRMED", "人工核实", reviewer)
        self.assertEqual(result["status"], "CONFIRMED")
        event = ServiceAnswerReviewAction.objects.get(review=review)
        self.assertEqual((event.previous_status, event.current_status, event.revision), ("PENDING", "CONFIRMED", 1))
        with self.assertRaises(AppApiException):
            handle_review("review-a", str(review.id), "DISMISSED", "重复操作", reviewer)

    def test_api_accepts_reviewer_permissions_and_returns_safe_review_context(self):
        review = capture_pending_review(self.record, "review-a")
        user = User.objects.create(username="reviewer", nick_name="reviewer", password="x", role="USER")
        client = APIClient()
        prefix = "/admin/api/workspace/review-a/service-answer-review"
        client.force_authenticate(user=user, token=SimpleNamespace(role_list=[], permission_list=[]))
        denied = client.get(f"{prefix}/1/20")
        self.assertEqual(denied.status_code, 403)
        client.force_authenticate(
            user=user,
            token=SimpleNamespace(
                role_list=[],
                permission_list=[
                    f"{PermissionConstants.APPLICATION_CHAT_LOG_READ.value}:/WORKSPACE/review-a",
                    f"{PermissionConstants.APPLICATION_CHAT_LOG_ANNOTATION.value}:/WORKSPACE/review-a",
                ],
            ),
        )
        response = client.get(f"{prefix}/1/20")
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)["data"]
        self.assertEqual(payload["total"], 1)
        self.assertEqual(payload["records"][0]["user_question"], self.record.problem_text)
        self.assertNotIn("details", payload["records"][0])
        handled = client.post(
            f"{prefix}/{review.id}/handle", {"action": "DISMISSED", "note": "已核实"}, format="json"
        )
        self.assertEqual(handled.status_code, 200)
        self.assertEqual(json.loads(handled.content)["data"]["status"], "DISMISSED")

    def test_workspace_manager_can_still_read_and_handle_review(self):
        review = capture_pending_review(self.record, "review-a")
        user = User.objects.create(username="manager", nick_name="manager", password="x", role="USER")
        client = APIClient()
        client.force_authenticate(
            user=user,
            token=SimpleNamespace(role_list=["WORKSPACE_MANAGE:/WORKSPACE/review-a"], permission_list=[]),
        )
        prefix = "/admin/api/workspace/review-a/service-answer-review"
        self.assertEqual(client.get(f"{prefix}/1/20").status_code, 200)
        response = client.post(
            f"{prefix}/{review.id}/handle", {"action": "CONFIRMED", "note": "管理员复核"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
