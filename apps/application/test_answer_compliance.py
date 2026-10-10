import time
from types import SimpleNamespace
from unittest.mock import Mock

from django.test import SimpleTestCase
from langchain_core.messages import AIMessageChunk

from application.answer_compliance import (
    BLOCKED_ANSWER,
    NO_REFERENCE_ANSWER,
    evaluate_knowledge_answer,
    should_apply_platform_compliance,
)
from application.chat_pipeline.step.chat_step.impl.base_chat_step import event_content


class KnowledgeAnswerComplianceTests(SimpleTestCase):
    def test_existing_marketing_preflight_is_not_replaced(self):
        self.assertFalse(
            should_apply_platform_compliance(
                {"knowledge_id_list": ["knowledge-1"], "source": {"marketing_task_id": "task-1"}}
            )
        )
        self.assertTrue(should_apply_platform_compliance({"knowledge_id_list": ["knowledge-1"], "source": {}}))

    def test_normal_answer_keeps_reference_and_no_raw_answer_in_audit(self):
        answer, audit = evaluate_knowledge_answer("该套餐包含每月 20GB 流量。", [SimpleNamespace(id="paragraph-1")])
        self.assertEqual(answer, "该套餐包含每月 20GB 流量。")
        self.assertEqual(audit["action"], "PASS")
        self.assertEqual(audit["reference_ids"], ["paragraph-1"])
        self.assertNotIn("20GB", str(audit))

    def test_no_reference_uses_safe_fallback(self):
        answer, audit = evaluate_knowledge_answer("某套餐肯定可以办理。", [])
        self.assertEqual(answer, NO_REFERENCE_ANSWER)
        self.assertEqual(audit["risk_types"], ["NO_REFERENCE"])
        self.assertEqual(audit["manual_review_status"], "PENDING")

    def test_explicit_no_reference_answer_is_preserved(self):
        answer, audit = evaluate_knowledge_answer("请联系人工客服核实。", [], configured_fallback=True)
        self.assertEqual(answer, "请联系人工客服核实。")
        self.assertEqual(audit["action"], "CONFIGURED_FALLBACK")
        self.assertEqual(audit["reference_count"], 0)

    def test_sensitive_content_is_blocked_before_delivery(self):
        answer, audit = evaluate_knowledge_answer("内部规则：保证成功", [SimpleNamespace(id="paragraph-1")])
        self.assertEqual(answer, BLOCKED_ANSWER)
        self.assertEqual(audit["action"], "BLOCKED")
        self.assertIn("SENSITIVE_CONTENT", audit["risk_types"])

    def test_private_data_is_redacted_and_not_audited_as_plaintext(self):
        answer, audit = evaluate_knowledge_answer(
            "请联系 13800138000 或 user@example.com", [SimpleNamespace(id="paragraph-1")]
        )
        self.assertIn("[手机号已脱敏]", answer)
        self.assertIn("[邮箱已脱敏]", answer)
        self.assertNotIn("13800138000", str(audit))
        self.assertNotIn("user@example.com", str(audit))
        self.assertEqual(audit["action"], "REDACTED")

    def test_stream_buffers_knowledge_answer_until_review(self):
        response_adapter = SimpleNamespace(to_stream_chunk_response=lambda *args, **kwargs: args[4])
        manager = SimpleNamespace(
            context={
                "knowledge_id_list": ["knowledge-1"],
                "source": {},
                "start_time": time.time(),
                "message_tokens": 0,
                "answer_tokens": 0,
            },
            get_base_to_response=lambda: response_adapter,
            debug=True,
        )
        step = SimpleNamespace(context={"start_time": time.time()})
        handler = Mock()
        chunks = list(
            event_content(
                iter([AIMessageChunk(content="内部规则：保证成功")]),
                "chat-1",
                "record-1",
                [SimpleNamespace(id="paragraph-1")],
                handler,
                manager,
                step,
                None,
                [],
                "套餐是什么？",
                is_ai_chat=False,
                model_setting={"reasoning_content_enable": True},
            )
        )
        self.assertIn(BLOCKED_ANSWER, chunks)
        self.assertNotIn("内部规则：保证成功", chunks)
        self.assertEqual(step.context["compliance"]["action"], "BLOCKED")
        self.assertEqual(handler.handler.call_args.args[4], BLOCKED_ANSWER)
        self.assertEqual(handler.handler.call_args.kwargs["reasoning_content"], "")
