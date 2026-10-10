from common.exception.app_exception import AppApiException
from django.test import TestCase
from users.models import User

from knowledge.models import (
    Document,
    Embedding,
    Knowledge,
    KnowledgeEtlRunStatus,
    KnowledgeEtlStageStatus,
    KnowledgeIndexReleaseAction,
    KnowledgeIndexReleaseRecord,
    KnowledgeIndexVersion,
    KnowledgeIndexVersionStatus,
    Paragraph,
    SourceType,
)
from knowledge.serializers.etl import KnowledgeEtlService


class KnowledgeEtlServiceTests(TestCase):
    def setUp(self):
        self.workspace_id = "knowledge-etl-workspace"
        self.user = User.objects.create(
            username="knowledge_etl_user",
            nick_name="知识工程师",
            password="x",
            role="USER",
        )
        self.knowledge = Knowledge.objects.create(
            workspace_id=self.workspace_id,
            name="智能客服知识库",
            desc="用于 ETL 版本验收",
            user=self.user,
        )
        self.document = Document.objects.create(
            knowledge=self.knowledge,
            name="套餐办理手册.md",
            char_length=64,
            user=self.user,
        )
        self.paragraph = self._create_paragraph("办理说明", "用户可以通过营业厅或线上渠道办理套餐。", 1)
        self.service = KnowledgeEtlService(self.workspace_id, str(self.knowledge.id), self.user)

    def _create_paragraph(self, title, content, position):
        paragraph = Paragraph.objects.create(
            knowledge=self.knowledge,
            document=self.document,
            title=title,
            content=content,
            position=position,
        )
        Embedding.objects.create(
            id=f"etl-embedding-{paragraph.id}",
            source_id=str(paragraph.id),
            source_type=SourceType.PARAGRAPH,
            knowledge=self.knowledge,
            document=self.document,
            paragraph=paragraph,
            embedding=[0.1, 0.2, 0.3],
        )
        return paragraph

    def test_run_builds_candidate_version_and_all_stage_snapshots(self):
        run = self.service.start_run({"document_ids": [str(self.document.id)]})

        self.assertEqual(run["status"], KnowledgeEtlRunStatus.WAITING_RELEASE)
        self.assertEqual(len(run["stages"]), 6)
        self.assertTrue(all(item["status"] == KnowledgeEtlStageStatus.SUCCESS for item in run["stages"]))
        self.assertTrue(run["quality_result"]["passed"])
        self.assertEqual(run["quality_result"]["embedded_paragraph_count"], 1)
        self.assertEqual(run["index_version"]["status"], KnowledgeIndexVersionStatus.CANDIDATE)
        self.assertEqual(run["index_version"]["paragraph_count"], 1)
        self.assertEqual(len(run["index_version"]["content_digest"]), 64)

    def test_publish_switches_version_and_rollback_is_traceable(self):
        first = self.service.start_run({})
        published_first = self.service.publish_run(first["id"], {"reason": "首版上线"})
        first_version_id = published_first["index_version"]["id"]
        self.assertEqual(published_first["status"], KnowledgeEtlRunStatus.SUCCESS)
        self.assertEqual(published_first["index_version"]["status"], KnowledgeIndexVersionStatus.PUBLISHED)

        self._create_paragraph("变更说明", "套餐变更在次月生效。", 2)
        second = self.service.start_run({})
        published_second = self.service.publish_run(second["id"], {"reason": "补充变更规则"})
        self.assertEqual(published_second["index_version"]["version"], 2)
        self.assertEqual(
            KnowledgeIndexVersion.objects.get(id=first_version_id).status,
            KnowledgeIndexVersionStatus.ARCHIVED,
        )

        rolled_back = self.service.rollback_version(first_version_id, {"reason": "验收回滚"})
        self.assertEqual(rolled_back["status"], KnowledgeIndexVersionStatus.PUBLISHED)
        self.assertEqual(
            KnowledgeIndexVersion.objects.get(id=published_second["index_version"]["id"]).status,
            KnowledgeIndexVersionStatus.ARCHIVED,
        )
        actions = list(
            KnowledgeIndexReleaseRecord.objects.filter(knowledge=self.knowledge)
            .order_by("create_time")
            .values_list("action", flat=True)
        )
        self.assertEqual(
            actions,
            [
                KnowledgeIndexReleaseAction.PUBLISH,
                KnowledgeIndexReleaseAction.PUBLISH,
                KnowledgeIndexReleaseAction.ROLLBACK,
            ],
        )

    def test_quality_failure_can_retry_after_data_is_fixed(self):
        failed = self.service.start_run({"min_paragraph_count": 2})
        self.assertEqual(failed["status"], KnowledgeEtlRunStatus.FAILED)
        self.assertIn("有效段落数", failed["error_message"])
        self.assertIsNone(failed["index_version"])
        self.assertEqual(failed["stages"][-1]["status"], KnowledgeEtlStageStatus.SKIPPED)

        self._create_paragraph("生效时间", "新套餐通常在次月一日生效。", 2)
        retry = self.service.retry_run(failed["id"])
        self.assertEqual(retry["status"], KnowledgeEtlRunStatus.WAITING_RELEASE)
        self.assertEqual(retry["trigger"], "RETRY")
        self.assertEqual(retry["retry_of_id"], failed["id"])

    def test_document_scope_rejects_cross_workspace_target(self):
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
        with self.assertRaises(AppApiException) as error:
            self.service.start_run({"document_ids": [str(other_document.id)]})
        self.assertEqual(error.exception.code, 400)

    def test_dashboard_reports_documents_runs_versions_and_releases(self):
        run = self.service.start_run({})
        self.service.publish_run(run["id"], {})

        dashboard = self.service.dashboard()
        self.assertEqual(dashboard["summary"]["document_count"], 1)
        self.assertEqual(dashboard["summary"]["run_count"], 1)
        self.assertEqual(dashboard["summary"]["published_version"], "v1")
        self.assertEqual(dashboard["documents"][0]["paragraph_count"], 1)
        self.assertEqual(len(dashboard["runs"]), 1)
        self.assertEqual(len(dashboard["versions"]), 1)
        self.assertEqual(len(dashboard["releases"]), 1)
