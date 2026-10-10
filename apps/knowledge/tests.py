from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from common.exception.app_exception import AppApiException
from django.test import TestCase
from models_provider.models import Model
from users.models import User

from knowledge.models import (
    Document,
    Knowledge,
    KnowledgeEvaluationCase,
    KnowledgeEvaluationResult,
    KnowledgeEvaluationRunStatus,
    Paragraph,
)
from knowledge.serializers.evaluation import KnowledgeEvaluationService


class KnowledgeEvaluationTests(TestCase):
    def setUp(self):
        self.workspace_id = "knowledge-evaluation-workspace"
        self.user = User.objects.create(
            username="knowledge_evaluation_user",
            nick_name="知识评估员",
            password="x",
            role="USER",
        )
        self.knowledge = Knowledge.objects.create(
            workspace_id=self.workspace_id,
            name="套餐政策知识库",
            desc="用于检索评估",
            user=self.user,
        )
        self.document = Document.objects.create(
            knowledge=self.knowledge,
            name="299 套餐说明",
            char_length=100,
            user=self.user,
        )
        self.paragraph = Paragraph.objects.create(
            knowledge=self.knowledge,
            document=self.document,
            title="套餐权益",
            content="299 元套餐包含千兆宽带和大流量权益。",
            position=1,
        )
        self.service = KnowledgeEvaluationService(
            self.workspace_id,
            str(self.knowledge.id),
            self.user,
        )

    def _create_case(self):
        return self.service.create_case(
            {
                "question": "299 元套餐有什么权益？",
                "expected_document_id": str(self.document.id),
                "expected_paragraph_id": str(self.paragraph.id),
                "expected_answer": "千兆宽带",
            }
        )

    def test_case_crud_validates_knowledge_scope(self):
        created = self._create_case()
        self.assertEqual(created["expected_document_name"], self.document.name)
        self.assertEqual(KnowledgeEvaluationCase.objects.count(), 1)

        updated = self.service.update_case(
            created["id"],
            {"question": "请介绍 299 元套餐", "enabled": False},
        )
        self.assertEqual(updated["question"], "请介绍 299 元套餐")
        self.assertFalse(updated["enabled"])

        other_knowledge = Knowledge.objects.create(
            workspace_id="another-workspace",
            name="其他知识库",
            desc="越权目标",
            user=self.user,
        )
        other_document = Document.objects.create(
            knowledge=other_knowledge,
            name="其他文档",
            char_length=10,
            user=self.user,
        )
        with self.assertRaises(AppApiException) as invalid_target:
            self.service.update_case(created["id"], {"expected_document_id": str(other_document.id)})
        self.assertEqual(invalid_target.exception.code, 400)

        self.assertTrue(self.service.delete_case(created["id"]))
        self.assertEqual(KnowledgeEvaluationCase.objects.count(), 0)

    def test_case_csv_import_skips_duplicates_and_validates_atomically(self):
        csv_content = (
            "问题,期望文档,期望段落,期望答案,启用\n"
            "299 元套餐有什么权益？,299 套餐说明,套餐权益,,是\n"
            "套餐是否包含千兆宽带？,,,千兆宽带,否\n"
        ).encode("utf-8-sig")
        result = self.service.import_cases(
            SimpleUploadedFile("evaluation-cases.csv", csv_content, content_type="text/csv")
        )
        self.assertEqual(result["total_count"], 2)
        self.assertEqual(result["imported_count"], 2)
        self.assertEqual(result["skipped_count"], 0)
        self.assertEqual(KnowledgeEvaluationCase.objects.count(), 2)
        self.assertFalse(KnowledgeEvaluationCase.objects.get(question="套餐是否包含千兆宽带？").enabled)

        duplicate_result = self.service.import_cases(
            SimpleUploadedFile("evaluation-cases.csv", csv_content, content_type="text/csv")
        )
        self.assertEqual(duplicate_result["imported_count"], 0)
        self.assertEqual(duplicate_result["skipped_count"], 2)
        self.assertEqual(len(self.service.case_rows()), 2)

        invalid_content = (
            "问题,期望文档,期望段落,期望答案,启用\n"
            "这条本来可以导入,,,千兆宽带,是\n"
            "缺少文档的段落目标,,套餐权益,,是\n"
        ).encode("utf-8-sig")
        with self.assertRaises(AppApiException):
            self.service.import_cases(
                SimpleUploadedFile("invalid.csv", invalid_content, content_type="text/csv")
            )
        self.assertEqual(KnowledgeEvaluationCase.objects.count(), 2)

    def test_evaluation_run_compares_modes_and_calculates_metrics(self):
        case = self._create_case()
        expected = {
            "paragraph_id": str(self.paragraph.id),
            "paragraph_title": self.paragraph.title,
            "content": self.paragraph.content,
            "document_id": str(self.document.id),
            "document_name": self.document.name,
            "vector_score": 0.91,
            "comprehensive_score": 0.91,
            "reranker_score": None,
        }
        distractor = {**expected, "paragraph_id": "distractor", "document_id": "distractor", "content": "无关内容"}

        def retrieve(_question, mode, *_args):
            if mode == "keywords":
                return []
            if mode == "embedding":
                return [distractor, expected]
            return [expected]

        with patch.object(self.service, "_retrieve", side_effect=retrieve):
            run = self.service.run(
                {
                    "search_modes": ["embedding", "keywords", "blend"],
                    "top_number": 5,
                    "similarity": 0,
                }
            )

        self.assertEqual(run["status"], KnowledgeEvaluationRunStatus.SUCCESS)
        self.assertEqual(run["summary"]["case_count"], 1)
        self.assertEqual(run["summary"]["best_mode"], "blend")
        metrics = {item["mode"]: item for item in run["summary"]["mode_metrics"]}
        self.assertEqual(metrics["blend"]["hit_rate"], 100)
        self.assertEqual(metrics["embedding"]["mrr"], 0.5)
        self.assertEqual(metrics["keywords"]["no_answer_rate"], 100)
        self.assertEqual(KnowledgeEvaluationResult.objects.count(), 3)

        self.service.delete_case(case["id"])
        retained_result = KnowledgeEvaluationResult.objects.first()
        self.assertIsNone(retained_result.case_id)
        retained_run = self.service.detail(run["id"])
        self.assertEqual(len(retained_run["results"]), 3)
        self.assertEqual(retained_run["results"][0]["question"], "299 元套餐有什么权益？")

    def test_evaluation_run_keeps_partial_failure_and_dashboard_history(self):
        self._create_case()

        def retrieve(_question, mode, *_args):
            if mode == "embedding":
                raise RuntimeError("向量模型暂不可用")
            return []

        with patch.object(self.service, "_retrieve", side_effect=retrieve):
            run = self.service.run(
                {
                    "search_modes": ["embedding", "keywords"],
                    "top_number": 3,
                    "similarity": 0,
                }
            )

        self.assertEqual(run["status"], KnowledgeEvaluationRunStatus.PARTIAL)
        self.assertEqual(run["summary"]["error_count"], 1)
        failed = next(item for item in run["results"] if item["mode"] == "embedding")
        self.assertIn("向量模型暂不可用", failed["error_message"])

        with patch.object(self.service, "_dependency_health", return_value=[]):
            dashboard = self.service.dashboard()
        self.assertEqual(dashboard["case_summary"]["enabled_count"], 1)
        self.assertEqual(dashboard["latest_run"]["id"], run["id"])
        self.assertEqual(dashboard["documents"][0]["id"], str(self.document.id))

    def test_evaluation_run_loads_selected_reranker_model(self):
        self._create_case()
        model = Model.objects.create(
            name="评估重排模型",
            status="SUCCESS",
            model_type="RERANKER",
            model_name="test-reranker",
            provider="test-provider",
            credential="unused-in-test",
            workspace_id=self.workspace_id,
        )
        expected = {
            "paragraph_id": str(self.paragraph.id),
            "paragraph_title": self.paragraph.title,
            "content": self.paragraph.content,
            "document_id": str(self.document.id),
            "document_name": self.document.name,
            "vector_score": 0.91,
            "comprehensive_score": 0.91,
            "reranker_score": 0.98,
        }
        reranker = object()

        with (
            patch(
                "knowledge.serializers.evaluation.get_model_instance_by_model_workspace_id",
                return_value=reranker,
            ) as load_model,
            patch.object(self.service, "_retrieve", return_value=[expected]) as retrieve,
        ):
            run = self.service.run(
                {
                    "search_modes": ["reranker"],
                    "top_number": 5,
                    "similarity": 0,
                    "reranker_model_id": str(model.id),
                }
            )

        load_model.assert_called_once_with(str(model.id), self.workspace_id, top_n=5)
        self.assertIs(retrieve.call_args.args[-1], reranker)
        self.assertEqual(run["status"], KnowledgeEvaluationRunStatus.SUCCESS)
        self.assertEqual(run["summary"]["best_mode"], "reranker")
        self.assertEqual(run["results"][0]["top_score"], 0.98)
