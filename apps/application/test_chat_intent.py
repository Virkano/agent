from types import SimpleNamespace
from unittest.mock import Mock

from django.test import SimpleTestCase

from application.chat_intent import route_conversation_control_message
from application.chat_pipeline.step.search_dataset_step.impl.base_search_dataset_step import BaseSearchDatasetStep


class ConversationControlIntentTests(SimpleTestCase):
    def test_pure_greeting_is_routed_without_business_inference(self):
        route = route_conversation_control_message("你好！")

        self.assertEqual(route.intent, "greeting")
        self.assertIn("套餐升级服务助手", route.answer)
        self.assertNotIn("确认", route.answer)
        self.assertNotIn("资源", route.answer)

    def test_greeting_with_business_question_is_not_swallowed(self):
        self.assertIsNone(route_conversation_control_message("你好，请问套餐什么时候生效？"))

    def test_search_step_skips_retrieval_for_pure_greeting(self):
        step = BaseSearchDatasetStep()
        step.context["step_args"] = {"problem_text": "您好"}
        step.execute = Mock(side_effect=AssertionError("greeting must not access the vector store"))
        manage = SimpleNamespace(
            context={"no_references_setting": {"status": "ai_questioning", "value": "{question}"}}
        )

        step._run(manage)

        step.execute.assert_not_called()
        self.assertEqual(manage.context["paragraph_list"], [])
        self.assertEqual(manage.context["conversation_intent"], "greeting")
        self.assertEqual(manage.context["no_references_setting"]["status"], "designated_answer")
        self.assertTrue(step.context["retrieval_skipped"])

    def test_thanks_and_goodbye_have_stable_routes(self):
        self.assertEqual(route_conversation_control_message("谢谢您").intent, "thanks")
        self.assertEqual(route_conversation_control_message("拜拜～").intent, "goodbye")
