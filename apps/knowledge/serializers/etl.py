# coding=utf-8
import hashlib
from collections import Counter

from common.exception.app_exception import AppApiException
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from rest_framework import serializers

from knowledge.models import (
    Document,
    Embedding,
    Knowledge,
    KnowledgeEtlRun,
    KnowledgeEtlRunStatus,
    KnowledgeEtlRunTrigger,
    KnowledgeEtlStage,
    KnowledgeEtlStageRun,
    KnowledgeEtlStageStatus,
    KnowledgeIndexReleaseAction,
    KnowledgeIndexReleaseRecord,
    KnowledgeIndexVersion,
    KnowledgeIndexVersionStatus,
    Paragraph,
)


class KnowledgeEtlRunSerializer(serializers.Serializer):
    document_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=False,
        max_length=100,
    )
    min_paragraph_count = serializers.IntegerField(required=False, min_value=1, max_value=100000, default=1)
    min_embedding_coverage = serializers.FloatField(required=False, min_value=0, max_value=1, default=0.8)

    def validate_document_ids(self, value):
        return list(dict.fromkeys(str(item) for item in value))


class KnowledgeIndexReleaseSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=512, default="")


def _user_name(user):
    if not user:
        return "系统"
    return user.nick_name or user.username


def serialize_etl_stage(row):
    return {
        "id": str(row.id),
        "stage": row.stage,
        "stage_label": row.get_stage_display(),
        "sequence": row.sequence,
        "status": row.status,
        "status_label": row.get_status_display(),
        "input_snapshot": row.input_snapshot,
        "output_snapshot": row.output_snapshot,
        "error_message": row.error_message,
        "started_at": row.started_at,
        "finished_at": row.finished_at,
    }


def serialize_index_version(row):
    return {
        "id": str(row.id),
        "version": row.version,
        "version_label": f"v{row.version}",
        "status": row.status,
        "status_label": row.get_status_display(),
        "source_run_id": str(row.source_run_id),
        "source_run_number": row.source_run.run_number,
        "document_ids": row.document_ids,
        "document_count": row.document_count,
        "paragraph_count": row.paragraph_count,
        "embedding_count": row.embedding_count,
        "embedding_model_id": row.embedding_model_id_snapshot or None,
        "embedding_model_name": row.embedding_model_name,
        "content_digest": row.content_digest,
        "quality_result": row.quality_result,
        "published_at": row.published_at,
        "create_time": row.create_time,
    }


def serialize_etl_run(row, include_stages=False):
    data = {
        "id": str(row.id),
        "run_number": row.run_number,
        "trigger": row.trigger,
        "trigger_label": row.get_trigger_display(),
        "status": row.status,
        "status_label": row.get_status_display(),
        "current_stage": row.current_stage,
        "current_stage_label": row.get_current_stage_display(),
        "document_ids": row.document_ids,
        "config_snapshot": row.config_snapshot,
        "quality_result": row.quality_result,
        "error_message": row.error_message,
        "retry_of_id": str(row.retry_of_id) if row.retry_of_id else None,
        "operator_name": row.operator_name,
        "started_at": row.started_at,
        "finished_at": row.finished_at,
        "create_time": row.create_time,
        "index_version": serialize_index_version(row.index_version) if hasattr(row, "index_version") else None,
    }
    if include_stages:
        data["stages"] = [serialize_etl_stage(item) for item in row.stage_runs.all()]
    return data


def serialize_release(row):
    return {
        "id": str(row.id),
        "action": row.action,
        "action_label": row.get_action_display(),
        "from_version_id": str(row.from_version_id) if row.from_version_id else None,
        "from_version_label": f"v{row.from_version.version}" if row.from_version else "无",
        "target_version_id": str(row.target_version_id),
        "target_version_label": f"v{row.target_version.version}",
        "reason": row.reason,
        "operator_name": row.operator_name,
        "create_time": row.create_time,
    }


class KnowledgeEtlService:
    stage_order = [
        KnowledgeEtlStage.PARSE,
        KnowledgeEtlStage.CLEAN,
        KnowledgeEtlStage.SPLIT,
        KnowledgeEtlStage.VECTORIZE,
        KnowledgeEtlStage.QUALITY,
        KnowledgeEtlStage.VERSION,
    ]

    def __init__(self, workspace_id, knowledge_id, user=None):
        self.workspace_id = workspace_id
        self.knowledge_id = knowledge_id
        self.user = user
        self.knowledge = self._get_knowledge()

    def _get_knowledge(self):
        row = Knowledge.objects.filter(workspace_id=self.workspace_id, id=self.knowledge_id).first()
        if row is None:
            raise AppApiException(404, "知识库不存在")
        return row

    def _runs(self):
        return (
            KnowledgeEtlRun.objects.filter(workspace_id=self.workspace_id, knowledge_id=self.knowledge_id)
            .select_related("operator", "retry_of")
            .prefetch_related("stage_runs", "index_version__source_run")
        )

    def _versions(self):
        return KnowledgeIndexVersion.objects.filter(
            workspace_id=self.workspace_id,
            knowledge_id=self.knowledge_id,
        ).select_related("source_run")

    def _releases(self):
        return KnowledgeIndexReleaseRecord.objects.filter(
            workspace_id=self.workspace_id,
            knowledge_id=self.knowledge_id,
        ).select_related("from_version", "target_version")

    def dashboard(self):
        documents = list(
            Document.objects.filter(knowledge=self.knowledge, is_active=True)
            .order_by("name")
            .values("id", "name", "char_length", "status")
        )
        document_ids = [item["id"] for item in documents]
        paragraph_counts = Counter(
            Paragraph.objects.filter(document_id__in=document_ids, is_active=True)
            .values_list("document_id", flat=True)
        )
        embedded_counts = Counter(
            Embedding.objects.filter(document_id__in=document_ids, is_active=True)
            .values_list("document_id", flat=True)
        )
        document_rows = [
            {
                "id": str(item["id"]),
                "name": item["name"],
                "char_length": item["char_length"],
                "status": item["status"],
                "paragraph_count": paragraph_counts[item["id"]],
                "embedding_count": embedded_counts[item["id"]],
            }
            for item in documents
        ]
        runs = list(self._runs()[:30])
        versions = list(self._versions()[:30])
        releases = list(self._releases()[:30])
        published = next((item for item in versions if item.status == KnowledgeIndexVersionStatus.PUBLISHED), None)
        return {
            "knowledge": {"id": str(self.knowledge.id), "name": self.knowledge.name},
            "summary": {
                "document_count": len(document_rows),
                "run_count": self._runs().count(),
                "failed_run_count": self._runs().filter(status=KnowledgeEtlRunStatus.FAILED).count(),
                "candidate_count": self._versions().filter(status=KnowledgeIndexVersionStatus.CANDIDATE).count(),
                "published_version": f"v{published.version}" if published else "",
            },
            "documents": document_rows,
            "runs": [serialize_etl_run(item) for item in runs],
            "versions": [serialize_index_version(item) for item in versions],
            "releases": [serialize_release(item) for item in releases],
        }

    def get_run(self, run_id):
        row = self._runs().filter(id=run_id).first()
        if row is None:
            raise AppApiException(404, "ETL运行不存在")
        return serialize_etl_run(row, include_stages=True)

    @transaction.atomic
    def _create_run(self, data, trigger, retry_of=None):
        knowledge = Knowledge.objects.select_for_update().filter(
            workspace_id=self.workspace_id,
            id=self.knowledge_id,
        ).first()
        if knowledge is None:
            raise AppApiException(404, "知识库不存在")
        serializer = KnowledgeEtlRunSerializer(data=data or {})
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        active_documents = Document.objects.filter(knowledge=knowledge, is_active=True)
        document_ids = values.get("document_ids")
        if document_ids:
            actual_ids = {str(item) for item in active_documents.filter(id__in=document_ids).values_list("id", flat=True)}
            missing = [item for item in document_ids if item not in actual_ids]
            if missing:
                raise AppApiException(400, "所选文档不存在、已停用或不属于当前知识库")
        else:
            document_ids = [str(item) for item in active_documents.values_list("id", flat=True)]
        if not document_ids:
            raise AppApiException(400, "当前知识库没有可处理的文档")
        unfinished = KnowledgeEtlRun.objects.filter(
            knowledge=knowledge,
            status__in=[KnowledgeEtlRunStatus.PENDING, KnowledgeEtlRunStatus.RUNNING],
        ).exists()
        if unfinished:
            raise AppApiException(409, "当前知识库已有执行中的 ETL 任务")
        run_number = (
            KnowledgeEtlRun.objects.filter(knowledge=knowledge).aggregate(max_number=Max("run_number"))["max_number"]
            or 0
        ) + 1
        config = {
            "min_paragraph_count": values["min_paragraph_count"],
            "min_embedding_coverage": values["min_embedding_coverage"],
        }
        row = KnowledgeEtlRun.objects.create(
            workspace_id=self.workspace_id,
            knowledge=knowledge,
            run_number=run_number,
            trigger=trigger,
            document_ids=document_ids,
            config_snapshot=config,
            retry_of=retry_of,
            operator=self.user,
            operator_name=_user_name(self.user),
        )
        KnowledgeEtlStageRun.objects.bulk_create(
            [
                KnowledgeEtlStageRun(
                    workspace_id=self.workspace_id,
                    etl_run=row,
                    stage=stage,
                    sequence=index,
                )
                for index, stage in enumerate(self.stage_order, start=1)
            ]
        )
        return row.id

    def start_run(self, data=None):
        run_id = self._create_run(data or {}, KnowledgeEtlRunTrigger.MANUAL)
        self._execute_run(run_id)
        return self.get_run(run_id)

    def retry_run(self, run_id):
        source = self._runs().filter(id=run_id).first()
        if source is None:
            raise AppApiException(404, "ETL运行不存在")
        if source.status != KnowledgeEtlRunStatus.FAILED:
            raise AppApiException(400, "只有失败的 ETL 运行可以重试")
        payload = {**source.config_snapshot, "document_ids": source.document_ids}
        retry_id = self._create_run(payload, KnowledgeEtlRunTrigger.RETRY, retry_of=source)
        self._execute_run(retry_id)
        return self.get_run(retry_id)

    def _set_stage(self, run, stage, status, input_snapshot=None, output_snapshot=None, error_message=""):
        now = timezone.now()
        stage_run = KnowledgeEtlStageRun.objects.get(etl_run=run, stage=stage)
        stage_run.status = status
        if input_snapshot is not None:
            stage_run.input_snapshot = input_snapshot
        if output_snapshot is not None:
            stage_run.output_snapshot = output_snapshot
        stage_run.error_message = error_message
        if status == KnowledgeEtlStageStatus.RUNNING and stage_run.started_at is None:
            stage_run.started_at = now
        if status in {
            KnowledgeEtlStageStatus.SUCCESS,
            KnowledgeEtlStageStatus.FAILED,
            KnowledgeEtlStageStatus.SKIPPED,
        }:
            stage_run.started_at = stage_run.started_at or now
            stage_run.finished_at = now
        stage_run.save()
        run.current_stage = stage
        run.save(update_fields=["current_stage", "update_time"])

    def _fail_run(self, run, stage, message, output_snapshot=None):
        self._set_stage(
            run,
            stage,
            KnowledgeEtlStageStatus.FAILED,
            output_snapshot=output_snapshot,
            error_message=message,
        )
        start = self.stage_order.index(stage) + 1
        for remaining_stage in self.stage_order[start:]:
            self._set_stage(run, remaining_stage, KnowledgeEtlStageStatus.SKIPPED)
        run.status = KnowledgeEtlRunStatus.FAILED
        run.error_message = message
        run.finished_at = timezone.now()
        run.save(update_fields=["status", "error_message", "finished_at", "update_time"])

    def _execute_run(self, run_id):
        run = KnowledgeEtlRun.objects.select_related("knowledge").get(id=run_id)
        run.status = KnowledgeEtlRunStatus.RUNNING
        run.started_at = timezone.now()
        run.error_message = ""
        run.save(update_fields=["status", "started_at", "error_message", "update_time"])
        try:
            documents = list(
                Document.objects.filter(
                    knowledge=run.knowledge,
                    id__in=run.document_ids,
                    is_active=True,
                ).order_by("id")
            )
            self._set_stage(
                run,
                KnowledgeEtlStage.PARSE,
                KnowledgeEtlStageStatus.RUNNING,
                input_snapshot={"document_ids": run.document_ids},
            )
            if len(documents) != len(run.document_ids):
                self._fail_run(run, KnowledgeEtlStage.PARSE, "部分文档已删除、停用或不属于当前知识库")
                return
            self._set_stage(
                run,
                KnowledgeEtlStage.PARSE,
                KnowledgeEtlStageStatus.SUCCESS,
                output_snapshot={
                    "document_count": len(documents),
                    "total_char_length": sum(item.char_length for item in documents),
                    "documents": [{"id": str(item.id), "name": item.name} for item in documents],
                },
            )

            self._set_stage(run, KnowledgeEtlStage.CLEAN, KnowledgeEtlStageStatus.RUNNING)
            paragraphs = list(
                Paragraph.objects.filter(
                    knowledge=run.knowledge,
                    document_id__in=run.document_ids,
                    is_active=True,
                )
                .order_by("document_id", "position", "id")
                .only("id", "document_id", "content", "position")
            )
            nonempty_paragraphs = [item for item in paragraphs if item.content.strip()]
            clean_output = {
                "source_paragraph_count": len(paragraphs),
                "nonempty_paragraph_count": len(nonempty_paragraphs),
                "empty_paragraph_count": len(paragraphs) - len(nonempty_paragraphs),
            }
            if not nonempty_paragraphs:
                self._fail_run(run, KnowledgeEtlStage.CLEAN, "清洗后没有可用文本段落", clean_output)
                return
            self._set_stage(
                run,
                KnowledgeEtlStage.CLEAN,
                KnowledgeEtlStageStatus.SUCCESS,
                output_snapshot=clean_output,
            )

            self._set_stage(run, KnowledgeEtlStage.SPLIT, KnowledgeEtlStageStatus.RUNNING)
            per_document = Counter(str(item.document_id) for item in nonempty_paragraphs)
            split_output = {
                "paragraph_count": len(nonempty_paragraphs),
                "paragraphs_by_document": dict(per_document),
            }
            self._set_stage(
                run,
                KnowledgeEtlStage.SPLIT,
                KnowledgeEtlStageStatus.SUCCESS,
                output_snapshot=split_output,
            )

            self._set_stage(run, KnowledgeEtlStage.VECTORIZE, KnowledgeEtlStageStatus.RUNNING)
            embeddings = Embedding.objects.filter(
                knowledge=run.knowledge,
                document_id__in=run.document_ids,
                is_active=True,
            )
            embedding_count = embeddings.count()
            embedded_paragraph_ids = set(str(item) for item in embeddings.values_list("paragraph_id", flat=True).distinct())
            expected_paragraph_ids = {str(item.id) for item in nonempty_paragraphs}
            embedded_paragraph_count = len(expected_paragraph_ids & embedded_paragraph_ids)
            vector_output = {
                "embedding_count": embedding_count,
                "embedded_paragraph_count": embedded_paragraph_count,
                "missing_paragraph_count": len(expected_paragraph_ids) - embedded_paragraph_count,
            }
            self._set_stage(
                run,
                KnowledgeEtlStage.VECTORIZE,
                KnowledgeEtlStageStatus.SUCCESS,
                output_snapshot=vector_output,
            )

            self._set_stage(run, KnowledgeEtlStage.QUALITY, KnowledgeEtlStageStatus.RUNNING)
            coverage = embedded_paragraph_count / len(nonempty_paragraphs)
            min_paragraph_count = run.config_snapshot["min_paragraph_count"]
            min_embedding_coverage = run.config_snapshot["min_embedding_coverage"]
            checks = [
                {
                    "key": "paragraph_count",
                    "label": "有效段落数",
                    "actual": len(nonempty_paragraphs),
                    "threshold": min_paragraph_count,
                    "passed": len(nonempty_paragraphs) >= min_paragraph_count,
                },
                {
                    "key": "embedding_coverage",
                    "label": "向量覆盖率",
                    "actual": round(coverage, 4),
                    "threshold": min_embedding_coverage,
                    "passed": coverage >= min_embedding_coverage,
                },
            ]
            quality_result = {
                "passed": all(item["passed"] for item in checks),
                "score": round(sum(1 for item in checks if item["passed"]) * 100 / len(checks), 2),
                "checks": checks,
                **clean_output,
                **vector_output,
            }
            run.quality_result = quality_result
            run.save(update_fields=["quality_result", "update_time"])
            if not quality_result["passed"]:
                failed_labels = "、".join(item["label"] for item in checks if not item["passed"])
                self._fail_run(run, KnowledgeEtlStage.QUALITY, f"质量门禁未通过：{failed_labels}", quality_result)
                return
            self._set_stage(
                run,
                KnowledgeEtlStage.QUALITY,
                KnowledgeEtlStageStatus.SUCCESS,
                output_snapshot=quality_result,
            )

            self._set_stage(run, KnowledgeEtlStage.VERSION, KnowledgeEtlStageStatus.RUNNING)
            digest = hashlib.sha256()
            digest.update("|".join(sorted(run.document_ids)).encode())
            for paragraph in nonempty_paragraphs:
                digest.update(str(paragraph.id).encode())
                digest.update(paragraph.content.encode())
            with transaction.atomic():
                Knowledge.objects.select_for_update().get(id=run.knowledge_id)
                version_number = (
                    KnowledgeIndexVersion.objects.filter(knowledge=run.knowledge)
                    .aggregate(max_number=Max("version"))["max_number"]
                    or 0
                ) + 1
                knowledge = Knowledge.objects.select_related("embedding_model").get(id=run.knowledge_id)
                version = KnowledgeIndexVersion.objects.create(
                    workspace_id=self.workspace_id,
                    knowledge=run.knowledge,
                    version=version_number,
                    source_run=run,
                    document_ids=run.document_ids,
                    document_count=len(documents),
                    paragraph_count=len(nonempty_paragraphs),
                    embedding_count=embedding_count,
                    embedding_model_id_snapshot=str(knowledge.embedding_model_id) if knowledge.embedding_model_id else "",
                    embedding_model_name=knowledge.embedding_model.name if knowledge.embedding_model else "",
                    content_digest=digest.hexdigest(),
                    quality_result=quality_result,
                )
            self._set_stage(
                run,
                KnowledgeEtlStage.VERSION,
                KnowledgeEtlStageStatus.SUCCESS,
                output_snapshot={
                    "index_version_id": str(version.id),
                    "version": version.version,
                    "content_digest": version.content_digest,
                },
            )
            run.status = KnowledgeEtlRunStatus.WAITING_RELEASE
            run.finished_at = timezone.now()
            run.save(update_fields=["status", "finished_at", "update_time"])
        except Exception as exc:
            self._fail_run(run, run.current_stage, str(exc))

    @transaction.atomic
    def publish_run(self, run_id, data=None):
        payload = KnowledgeIndexReleaseSerializer(data=data or {})
        payload.is_valid(raise_exception=True)
        run = KnowledgeEtlRun.objects.select_for_update().filter(
            workspace_id=self.workspace_id,
            knowledge_id=self.knowledge_id,
            id=run_id,
        ).first()
        if run is None:
            raise AppApiException(404, "ETL运行不存在")
        if run.status != KnowledgeEtlRunStatus.WAITING_RELEASE:
            raise AppApiException(400, "只有通过质量门禁的候选版本可以发布")
        version = KnowledgeIndexVersion.objects.select_for_update().filter(source_run=run).first()
        if version is None or version.status != KnowledgeIndexVersionStatus.CANDIDATE:
            raise AppApiException(400, "候选索引版本不存在或状态已变化")
        current = KnowledgeIndexVersion.objects.select_for_update().filter(
            workspace_id=self.workspace_id,
            knowledge_id=self.knowledge_id,
            status=KnowledgeIndexVersionStatus.PUBLISHED,
        ).first()
        if current:
            current.status = KnowledgeIndexVersionStatus.ARCHIVED
            current.save(update_fields=["status", "update_time"])
        now = timezone.now()
        version.status = KnowledgeIndexVersionStatus.PUBLISHED
        version.published_at = now
        version.save(update_fields=["status", "published_at", "update_time"])
        run.status = KnowledgeEtlRunStatus.SUCCESS
        run.finished_at = now
        run.save(update_fields=["status", "finished_at", "update_time"])
        KnowledgeIndexReleaseRecord.objects.create(
            workspace_id=self.workspace_id,
            knowledge_id=self.knowledge_id,
            action=KnowledgeIndexReleaseAction.PUBLISH,
            from_version=current,
            target_version=version,
            reason=payload.validated_data["reason"],
            operator=self.user,
            operator_name=_user_name(self.user),
        )
        return self.get_run(run.id)

    @transaction.atomic
    def rollback_version(self, version_id, data=None):
        payload = KnowledgeIndexReleaseSerializer(data=data or {})
        payload.is_valid(raise_exception=True)
        target = KnowledgeIndexVersion.objects.select_for_update().filter(
            workspace_id=self.workspace_id,
            knowledge_id=self.knowledge_id,
            id=version_id,
        ).first()
        if target is None:
            raise AppApiException(404, "索引版本不存在")
        if target.status != KnowledgeIndexVersionStatus.ARCHIVED:
            raise AppApiException(400, "只能回滚到历史版本")
        current = KnowledgeIndexVersion.objects.select_for_update().filter(
            workspace_id=self.workspace_id,
            knowledge_id=self.knowledge_id,
            status=KnowledgeIndexVersionStatus.PUBLISHED,
        ).first()
        if current is None:
            raise AppApiException(400, "当前没有已发布版本")
        current.status = KnowledgeIndexVersionStatus.ARCHIVED
        current.save(update_fields=["status", "update_time"])
        target.status = KnowledgeIndexVersionStatus.PUBLISHED
        target.published_at = timezone.now()
        target.save(update_fields=["status", "published_at", "update_time"])
        KnowledgeIndexReleaseRecord.objects.create(
            workspace_id=self.workspace_id,
            knowledge_id=self.knowledge_id,
            action=KnowledgeIndexReleaseAction.ROLLBACK,
            from_version=current,
            target_version=target,
            reason=payload.validated_data["reason"],
            operator=self.user,
            operator_name=_user_name(self.user),
        )
        return serialize_index_version(target)
