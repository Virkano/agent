import csv
import json
import re
import time
from collections import defaultdict
from io import StringIO
from urllib.parse import urljoin

import requests
from common.config.embedding_config import VectorStore
from common.exception.app_exception import AppApiException
from common.utils.rsa_util import rsa_long_decrypt
from django.db import transaction
from django.utils import timezone
from langchain_core.documents import Document as LangChainDocument
from models_provider.models import Model
from models_provider.tools import get_model_instance_by_model_workspace_id
from rest_framework import serializers

from knowledge.models import (
    Document,
    Embedding,
    Knowledge,
    KnowledgeEvaluationCase,
    KnowledgeEvaluationResult,
    KnowledgeEvaluationRun,
    KnowledgeEvaluationRunStatus,
    Paragraph,
    SearchMode,
)
from knowledge.serializers.common import get_embedding_model_by_knowledge_id


SEARCH_MODE_LABELS = {
    "embedding": "向量检索",
    "keywords": "关键词检索",
    "blend": "混合检索",
    "reranker": "混合检索 + 重排",
}

CASE_CSV_HEADERS = ["问题", "期望文档", "期望段落", "期望答案", "启用"]
CASE_IMPORT_MAX_FILE_SIZE = 2 * 1024 * 1024
CASE_IMPORT_MAX_ROWS = 500
CASE_ENABLED_VALUES = {"1", "true", "yes", "y", "是", "启用"}
CASE_DISABLED_VALUES = {"0", "false", "no", "n", "否", "停用"}


class EvaluationCaseSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=1000)
    expected_document_id = serializers.UUIDField(required=False, allow_null=True)
    expected_paragraph_id = serializers.UUIDField(required=False, allow_null=True)
    expected_answer = serializers.CharField(required=False, allow_blank=True, max_length=10000)
    enabled = serializers.BooleanField(required=False, default=True)

    def validate(self, attrs):
        if not any(
            [
                attrs.get("expected_document_id"),
                attrs.get("expected_paragraph_id"),
                attrs.get("expected_answer", "").strip(),
            ]
        ):
            raise serializers.ValidationError("期望文档、期望段落和期望答案至少填写一项")
        return attrs


class EvaluationCaseUpdateSerializer(serializers.Serializer):
    question = serializers.CharField(required=False, max_length=1000)
    expected_document_id = serializers.UUIDField(required=False, allow_null=True)
    expected_paragraph_id = serializers.UUIDField(required=False, allow_null=True)
    expected_answer = serializers.CharField(required=False, allow_blank=True, max_length=10000)
    enabled = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("至少需要修改一个字段")
        return attrs


class EvaluationRunSerializer(serializers.Serializer):
    search_modes = serializers.ListField(
        child=serializers.ChoiceField(choices=tuple(SEARCH_MODE_LABELS)),
        allow_empty=False,
        max_length=4,
        default=["embedding", "keywords", "blend"],
    )
    top_number = serializers.IntegerField(min_value=1, max_value=50, default=5)
    similarity = serializers.FloatField(min_value=0, max_value=2, default=0)
    reranker_model_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        attrs["search_modes"] = list(dict.fromkeys(attrs["search_modes"]))
        if "reranker" in attrs["search_modes"] and not attrs.get("reranker_model_id"):
            raise serializers.ValidationError({"reranker_model_id": "选择重排模式时必须指定重排模型"})
        return attrs


def _user_name(user):
    if not user:
        return "系统"
    return user.nick_name or user.username


def _percentage(numerator, denominator):
    return round(numerator * 100 / denominator, 2) if denominator else 0


def _normalize_text(value):
    return re.sub(r"\s+", "", (value or "").lower())


def _read_case_csv(uploaded_file):
    if uploaded_file is None:
        raise AppApiException(400, "请选择要导入的 CSV 文件")
    file_name = str(getattr(uploaded_file, "name", "")).strip()
    if not file_name.lower().endswith(".csv"):
        raise AppApiException(400, "评估样本仅支持 CSV 文件")
    if getattr(uploaded_file, "size", 0) > CASE_IMPORT_MAX_FILE_SIZE:
        raise AppApiException(400, "评估样本文件不能超过 2MB")
    content = uploaded_file.read()
    if not content:
        raise AppApiException(400, "导入文件为空")
    text = None
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            text = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise AppApiException(400, "CSV 文件编码不支持，请使用 UTF-8 或 GB18030")
    reader = csv.DictReader(StringIO(text))
    headers = [str(header or "").strip() for header in (reader.fieldnames or [])]
    if "问题" not in headers:
        raise AppApiException(400, "CSV 文件缺少“问题”列，请先下载最新模板")
    rows = []
    for row_number, source in enumerate(reader, start=2):
        row = {str(key or "").strip(): str(value or "").strip() for key, value in source.items()}
        if any(row.values()):
            rows.append((row_number, row))
    if not rows:
        raise AppApiException(400, "CSV 文件至少需要一条评估样本")
    if len(rows) > CASE_IMPORT_MAX_ROWS:
        raise AppApiException(400, f"一次最多导入 {CASE_IMPORT_MAX_ROWS} 条评估样本")
    return rows


def _parse_case_enabled(value, row_number):
    normalized = str(value or "").strip().lower()
    if not normalized:
        return True
    if normalized in CASE_ENABLED_VALUES:
        return True
    if normalized in CASE_DISABLED_VALUES:
        return False
    raise AppApiException(400, f"第 {row_number} 行“启用”只能填写是/否、true/false 或 1/0")


def serialize_case(row):
    return {
        "id": str(row.id),
        "question": row.question,
        "expected_document_id": str(row.expected_document_id) if row.expected_document_id else None,
        "expected_document_name": row.expected_document.name if row.expected_document else "",
        "expected_paragraph_id": str(row.expected_paragraph_id) if row.expected_paragraph_id else None,
        "expected_paragraph_title": row.expected_paragraph.title if row.expected_paragraph else "",
        "expected_paragraph_content": row.expected_paragraph.content if row.expected_paragraph else "",
        "expected_answer": row.expected_answer,
        "enabled": row.enabled,
        "update_time": row.update_time,
    }


def serialize_run(row, include_results=False):
    data = {
        "id": str(row.id),
        "status": row.status,
        "status_label": row.get_status_display(),
        "search_modes": row.search_modes,
        "top_number": row.top_number,
        "similarity": row.similarity,
        "reranker_model_id": str(row.reranker_model_id) if row.reranker_model_id else None,
        "reranker_model_name": row.reranker_model.name if row.reranker_model else "",
        "summary": row.summary,
        "error_message": row.error_message,
        "started_at": row.started_at,
        "finished_at": row.finished_at,
        "user_name": row.user_name,
        "create_time": row.create_time,
    }
    if include_results:
        data["results"] = [serialize_result(item) for item in row.results.all()]
    return data


def serialize_result(row):
    return {
        "id": str(row.id),
        "case_id": str(row.case_id) if row.case_id else None,
        "mode": row.mode,
        "mode_label": SEARCH_MODE_LABELS.get(row.mode, row.mode),
        "question": row.question,
        "expected_document_id": row.expected_document_id_snapshot,
        "expected_document_name": row.expected_document_name,
        "expected_paragraph_id": row.expected_paragraph_id_snapshot,
        "expected_answer": row.expected_answer,
        "hit": row.hit,
        "expected_rank": row.expected_rank,
        "latency_ms": row.latency_ms,
        "top_score": row.top_score,
        "matches": row.matches,
        "error_message": row.error_message,
    }


class KnowledgeEvaluationService:
    def __init__(self, workspace_id, knowledge_id, user=None):
        self.workspace_id = workspace_id
        self.knowledge_id = knowledge_id
        self.user = user
        self.knowledge = self._get_knowledge()

    def _get_knowledge(self):
        knowledge = Knowledge.objects.filter(id=self.knowledge_id, workspace_id=self.workspace_id).first()
        if knowledge is None:
            raise AppApiException(404, "知识库不存在")
        return knowledge

    def _case_queryset(self):
        return (
            KnowledgeEvaluationCase.objects.filter(
                workspace_id=self.workspace_id,
                knowledge=self.knowledge,
            )
            .select_related("expected_document", "expected_paragraph")
            .order_by("-update_time")
        )

    def _run_queryset(self):
        return (
            KnowledgeEvaluationRun.objects.filter(
                workspace_id=self.workspace_id,
                knowledge=self.knowledge,
            )
            .select_related("reranker_model")
            .order_by("-create_time")
        )

    def _resolve_targets(self, values, current=None):
        document_id = values.get(
            "expected_document_id",
            current.expected_document_id if current else None,
        )
        paragraph_id = values.get(
            "expected_paragraph_id",
            current.expected_paragraph_id if current else None,
        )
        document = None
        paragraph = None
        if paragraph_id:
            paragraph = Paragraph.objects.select_related("document").filter(
                id=paragraph_id,
                knowledge=self.knowledge,
            ).first()
            if paragraph is None:
                raise AppApiException(400, "期望段落不属于当前知识库")
            if document_id and str(paragraph.document_id) != str(document_id):
                raise AppApiException(400, "期望段落不属于所选文档")
            document = paragraph.document
        elif document_id:
            document = Document.objects.filter(id=document_id, knowledge=self.knowledge).first()
            if document is None:
                raise AppApiException(400, "期望文档不属于当前知识库")
        return document, paragraph

    def create_case(self, data):
        serializer = EvaluationCaseSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        document, paragraph = self._resolve_targets(values)
        row = KnowledgeEvaluationCase.objects.create(
            workspace_id=self.workspace_id,
            knowledge=self.knowledge,
            question=values["question"].strip(),
            expected_document=document,
            expected_paragraph=paragraph,
            expected_answer=values.get("expected_answer", "").strip(),
            enabled=values.get("enabled", True),
            user=self.user,
        )
        return serialize_case(row)

    def update_case(self, case_id, data):
        serializer = EvaluationCaseUpdateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        row = self._case_queryset().filter(id=case_id).first()
        if row is None:
            raise AppApiException(404, "评估样本不存在")
        merged = {
            "expected_document_id": values.get("expected_document_id", row.expected_document_id),
            "expected_paragraph_id": values.get("expected_paragraph_id", row.expected_paragraph_id),
            "expected_answer": values.get("expected_answer", row.expected_answer),
        }
        if not any([merged["expected_document_id"], merged["expected_paragraph_id"], merged["expected_answer"].strip()]):
            raise AppApiException(400, "期望文档、期望段落和期望答案至少保留一项")
        document, paragraph = self._resolve_targets(values, row)
        row.expected_document = document
        row.expected_paragraph = paragraph
        for field in ("question", "expected_answer", "enabled"):
            if field in values:
                value = values[field]
                setattr(row, field, value.strip() if isinstance(value, str) else value)
        row.user = self.user
        row.save()
        return serialize_case(row)

    def delete_case(self, case_id):
        deleted, _ = self._case_queryset().filter(id=case_id).delete()
        if not deleted:
            raise AppApiException(404, "评估样本不存在")
        return True

    def import_cases(self, uploaded_file):
        source_rows = _read_case_csv(uploaded_file)
        documents_by_name = defaultdict(list)
        for document in Document.objects.filter(knowledge=self.knowledge, is_active=True).only("id", "name"):
            documents_by_name[document.name.strip()].append(document)
        paragraphs_by_target = defaultdict(list)
        for paragraph in (
            Paragraph.objects.filter(knowledge=self.knowledge, is_active=True)
            .select_related("document")
            .only("id", "title", "document_id", "document__name")
        ):
            paragraphs_by_target[(paragraph.document.name.strip(), paragraph.title.strip())].append(paragraph)

        existing_questions = {
            _normalize_text(question)
            for question in self._case_queryset().values_list("question", flat=True)
        }
        seen_questions = set(existing_questions)
        prepared_rows = []
        skipped_count = 0
        for row_number, source in source_rows:
            question = source.get("问题", "").strip()
            document_name = source.get("期望文档", "").strip()
            paragraph_title = source.get("期望段落", "").strip()
            expected_answer = source.get("期望答案", "").strip()
            if not question:
                raise AppApiException(400, f"第 {row_number} 行“问题”不能为空")
            if len(question) > 1000:
                raise AppApiException(400, f"第 {row_number} 行“问题”不能超过 1000 个字符")
            if len(expected_answer) > 10000:
                raise AppApiException(400, f"第 {row_number} 行“期望答案”不能超过 10000 个字符")
            if paragraph_title and not document_name:
                raise AppApiException(400, f"第 {row_number} 行填写期望段落时必须同时填写期望文档")
            if not any([document_name, paragraph_title, expected_answer]):
                raise AppApiException(400, f"第 {row_number} 行至少填写期望文档、期望段落或期望答案之一")

            document = None
            paragraph = None
            if document_name:
                documents = documents_by_name.get(document_name, [])
                if not documents:
                    raise AppApiException(400, f"第 {row_number} 行期望文档“{document_name}”不存在或已禁用")
                if len(documents) > 1:
                    raise AppApiException(400, f"第 {row_number} 行期望文档“{document_name}”名称不唯一")
                document = documents[0]
            if paragraph_title:
                paragraphs = paragraphs_by_target.get((document_name, paragraph_title), [])
                if not paragraphs:
                    raise AppApiException(
                        400,
                        f"第 {row_number} 行期望段落“{paragraph_title}”不属于文档“{document_name}”或已禁用",
                    )
                if len(paragraphs) > 1:
                    raise AppApiException(
                        400,
                        f"第 {row_number} 行文档“{document_name}”内的段落“{paragraph_title}”名称不唯一",
                    )
                paragraph = paragraphs[0]

            normalized_question = _normalize_text(question)
            if normalized_question in seen_questions:
                skipped_count += 1
                continue
            seen_questions.add(normalized_question)
            prepared_rows.append(
                {
                    "question": question,
                    "expected_document": document,
                    "expected_paragraph": paragraph,
                    "expected_answer": expected_answer,
                    "enabled": _parse_case_enabled(source.get("启用", ""), row_number),
                }
            )

        with transaction.atomic():
            created_rows = [
                KnowledgeEvaluationCase.objects.create(
                    workspace_id=self.workspace_id,
                    knowledge=self.knowledge,
                    user=self.user,
                    **values,
                )
                for values in prepared_rows
            ]
        return {
            "total_count": len(source_rows),
            "imported_count": len(created_rows),
            "skipped_count": skipped_count,
            "cases": [serialize_case(row) for row in created_rows],
        }

    def case_rows(self):
        return list(self._case_queryset())

    def options(self, document_id=None):
        documents = list(
            Document.objects.filter(knowledge=self.knowledge, is_active=True)
            .order_by("name")
            .values("id", "name")
        )
        paragraphs = []
        if document_id:
            if not any(str(item["id"]) == str(document_id) for item in documents):
                raise AppApiException(400, "文档不属于当前知识库或已禁用")
            paragraphs = [
                {
                    "id": str(row.id),
                    "title": row.title,
                    "content": row.content[:240],
                }
                for row in Paragraph.objects.filter(
                    knowledge=self.knowledge,
                    document_id=document_id,
                    is_active=True,
                ).order_by("position", "create_time")[:1000]
            ]
        return {
            "documents": [{"id": str(item["id"]), "name": item["name"]} for item in documents],
            "paragraphs": paragraphs,
        }

    def _reranker_models(self):
        rows = Model.objects.filter(
            model_type="RERANKER",
            status="SUCCESS",
            workspace_id__in=[self.workspace_id, "default", "None"],
        ).order_by("name")
        return [
            {
                "id": str(row.id),
                "name": row.name,
                "model_name": row.model_name,
                "provider": row.provider,
            }
            for row in rows
        ]

    def _dependency_health(self):
        paragraph_count = Paragraph.objects.filter(knowledge=self.knowledge, is_active=True).count()
        embedding_count = Embedding.objects.filter(knowledge_id=self.knowledge_id, is_active=True).count()
        checks = [
            {
                "key": "vector_store",
                "name": "向量索引",
                "status": "HEALTHY" if embedding_count else "WARNING",
                "detail": f"{embedding_count} 条有效向量 / {paragraph_count} 个启用段落",
            }
        ]
        embedding_started = time.perf_counter()
        try:
            embedding_model = get_embedding_model_by_knowledge_id(self.knowledge_id)
            vector = embedding_model.embed_query("知识库检索评估健康检查")
            elapsed = round((time.perf_counter() - embedding_started) * 1000)
            checks.append(
                {
                    "key": "embedding_model",
                    "name": "向量模型",
                    "status": "HEALTHY" if vector else "WARNING",
                    "detail": f"{self.knowledge.embedding_model.name if self.knowledge.embedding_model else '未命名模型'} · {len(vector or [])} 维 · {elapsed} ms",
                }
            )
        except Exception as exc:
            checks.append(
                {
                    "key": "embedding_model",
                    "name": "向量模型",
                    "status": "ERROR",
                    "detail": str(exc)[:240],
                }
            )

        ollama_models = Model.objects.filter(
            provider="model_ollama_provider",
            status="SUCCESS",
            workspace_id__in=[self.workspace_id, "default", "None"],
        ).order_by("create_time")
        if not ollama_models.exists():
            checks.append(
                {
                    "key": "ollama",
                    "name": "Ollama",
                    "status": "NOT_CONFIGURED",
                    "detail": "当前工作空间没有配置 Ollama 模型",
                }
            )
        else:
            try:
                credential = json.loads(rsa_long_decrypt(ollama_models.first().credential))
                api_base = credential.get("api_base", "http://127.0.0.1:11434")
                response = requests.get(urljoin(api_base.rstrip("/") + "/", "api/tags"), timeout=2)
                response.raise_for_status()
                model_count = len(response.json().get("models", []))
                checks.append(
                    {
                        "key": "ollama",
                        "name": "Ollama",
                        "status": "HEALTHY",
                        "detail": f"服务在线 · 已加载 {model_count} 个模型",
                    }
                )
            except Exception as exc:
                checks.append(
                    {
                        "key": "ollama",
                        "name": "Ollama",
                        "status": "ERROR",
                        "detail": str(exc)[:240],
                    }
                )
        return checks

    def dashboard(self):
        cases = list(self._case_queryset())
        runs = list(self._run_queryset()[:10])
        options = self.options()
        return {
            "knowledge": {
                "id": str(self.knowledge.id),
                "name": self.knowledge.name,
                "description": self.knowledge.desc,
            },
            "case_summary": {
                "total_count": len(cases),
                "enabled_count": sum(item.enabled for item in cases),
                "document_target_count": sum(bool(item.expected_document_id) for item in cases),
                "paragraph_target_count": sum(bool(item.expected_paragraph_id) for item in cases),
                "answer_target_count": sum(bool(item.expected_answer.strip()) for item in cases),
            },
            "cases": [serialize_case(item) for item in cases],
            "runs": [serialize_run(item) for item in runs],
            "latest_run": serialize_run(runs[0]) if runs else None,
            "documents": options["documents"],
            "reranker_models": self._reranker_models(),
            "dependency_health": self._dependency_health(),
            "mode_labels": SEARCH_MODE_LABELS,
        }

    def _retrieve(self, question, mode, top_number, similarity, reranker_model=None):
        vector = VectorStore.get_embedding_vector()
        embedding_model = get_embedding_model_by_knowledge_id(self.knowledge_id)
        excluded_documents = [
            str(value)
            for value in Document.objects.filter(knowledge=self.knowledge, is_active=False).values_list("id", flat=True)
        ]
        base_mode = "blend" if mode == "reranker" else mode
        candidate_count = min(50, max(top_number * 3, 10)) if mode == "reranker" else top_number
        hits = vector.hit_test(
            question,
            [self.knowledge_id],
            excluded_documents,
            candidate_count,
            similarity,
            SearchMode(base_mode),
            embedding_model,
        ) or []
        hit_by_paragraph = {str(item.get("paragraph_id")): item for item in hits}
        paragraph_rows = Paragraph.objects.filter(id__in=hit_by_paragraph).select_related("document")
        paragraph_by_id = {str(item.id): item for item in paragraph_rows}
        matches = []
        for hit in hits:
            paragraph = paragraph_by_id.get(str(hit.get("paragraph_id")))
            if paragraph is None:
                continue
            score = hit.get("comprehensive_score", hit.get("similarity", 0)) or 0
            matches.append(
                {
                    "paragraph_id": str(paragraph.id),
                    "paragraph_title": paragraph.title,
                    "content": paragraph.content,
                    "document_id": str(paragraph.document_id),
                    "document_name": paragraph.document.name,
                    "vector_score": round(float(hit.get("similarity", 0) or 0), 6),
                    "comprehensive_score": round(float(score), 6),
                    "reranker_score": None,
                }
            )
        if mode != "reranker" or not reranker_model or not matches:
            return matches[:top_number]

        source_by_content = defaultdict(list)
        documents = []
        for match in matches:
            source_by_content[match["content"]].append(match)
            documents.append(LangChainDocument(page_content=match["content"]))
        reranked_documents = reranker_model.compress_documents(documents, question)
        reranked_matches = []
        for document in reranked_documents:
            source_rows = source_by_content.get(document.page_content) or []
            if not source_rows:
                continue
            source = dict(source_rows.pop(0))
            source["reranker_score"] = round(float(document.metadata.get("relevance_score", 0) or 0), 6)
            reranked_matches.append(source)
        return reranked_matches[:top_number]

    @staticmethod
    def _evaluate_case(case, matches):
        expected_rank = None
        for index, match in enumerate(matches, start=1):
            paragraph_hit = case.expected_paragraph_id and str(case.expected_paragraph_id) == match["paragraph_id"]
            document_hit = (
                not case.expected_paragraph_id
                and case.expected_document_id
                and str(case.expected_document_id) == match["document_id"]
            )
            answer_hit = False
            if not case.expected_paragraph_id and not case.expected_document_id and case.expected_answer.strip():
                answer_hit = _normalize_text(case.expected_answer) in _normalize_text(match["content"])
            if paragraph_hit or document_hit or answer_hit:
                expected_rank = index
                break
        return expected_rank is not None, expected_rank

    @staticmethod
    def _build_summary(results, case_count):
        by_mode = defaultdict(list)
        for row in results:
            by_mode[row.mode].append(row)
        mode_metrics = []
        for mode, rows in by_mode.items():
            hit_count = sum(item.hit for item in rows)
            no_answer_count = sum(not item.matches and not item.error_message for item in rows)
            failed_count = sum(bool(item.error_message) for item in rows)
            reciprocal_rank = sum(1 / item.expected_rank for item in rows if item.expected_rank)
            mode_metrics.append(
                {
                    "mode": mode,
                    "mode_label": SEARCH_MODE_LABELS.get(mode, mode),
                    "case_count": case_count,
                    "hit_count": hit_count,
                    "hit_rate": _percentage(hit_count, case_count),
                    "recall_at_k": _percentage(hit_count, case_count),
                    "mrr": round(reciprocal_rank / case_count, 4) if case_count else 0,
                    "no_answer_count": no_answer_count,
                    "no_answer_rate": _percentage(no_answer_count, case_count),
                    "failed_count": failed_count,
                    "avg_latency_ms": round(sum(item.latency_ms for item in rows) / len(rows)) if rows else 0,
                }
            )
        mode_metrics.sort(
            key=lambda item: (-item["hit_rate"], -item["mrr"], item["avg_latency_ms"])
        )
        return {
            "case_count": case_count,
            "mode_count": len(mode_metrics),
            "result_count": len(results),
            "error_count": sum(bool(item.error_message) for item in results),
            "best_mode": mode_metrics[0]["mode"] if mode_metrics else "",
            "best_mode_label": mode_metrics[0]["mode_label"] if mode_metrics else "",
            "best_hit_rate": mode_metrics[0]["hit_rate"] if mode_metrics else 0,
            "mode_metrics": mode_metrics,
        }

    def run(self, data):
        serializer = EvaluationRunSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        cases = list(self._case_queryset().filter(enabled=True))
        if not cases:
            raise AppApiException(400, "请先创建并启用至少一个评估样本")
        reranker_model_row = None
        reranker_model = None
        if values.get("reranker_model_id"):
            reranker_model_row = Model.objects.filter(
                id=values["reranker_model_id"],
                model_type="RERANKER",
                status="SUCCESS",
                workspace_id__in=[self.workspace_id, "default", "None"],
            ).first()
            if reranker_model_row is None:
                raise AppApiException(400, "重排模型不存在或不可用")
            reranker_model = get_model_instance_by_model_workspace_id(
                str(reranker_model_row.id),
                self.workspace_id,
                top_n=values["top_number"],
            )
        now = timezone.now()
        run = KnowledgeEvaluationRun.objects.create(
            workspace_id=self.workspace_id,
            knowledge=self.knowledge,
            status=KnowledgeEvaluationRunStatus.RUNNING,
            search_modes=values["search_modes"],
            top_number=values["top_number"],
            similarity=values["similarity"],
            reranker_model=reranker_model_row,
            started_at=now,
            user=self.user,
            user_name=_user_name(self.user),
        )
        created_results = []
        errors = []
        for case in cases:
            for mode in values["search_modes"]:
                started = time.perf_counter()
                matches = []
                error_message = ""
                hit = False
                expected_rank = None
                try:
                    matches = self._retrieve(
                        case.question,
                        mode,
                        values["top_number"],
                        values["similarity"],
                        reranker_model,
                    )
                    hit, expected_rank = self._evaluate_case(case, matches)
                except Exception as exc:
                    error_message = str(exc)[:2000]
                    errors.append(f"{SEARCH_MODE_LABELS.get(mode, mode)}：{error_message}")
                latency_ms = max(0, round((time.perf_counter() - started) * 1000))
                top_score = 0
                if matches:
                    top_score = matches[0].get("reranker_score")
                    if top_score is None:
                        top_score = matches[0].get("comprehensive_score", 0)
                created_results.append(
                    KnowledgeEvaluationResult.objects.create(
                        workspace_id=self.workspace_id,
                        run=run,
                        case=case,
                        mode=mode,
                        question=case.question,
                        expected_document_id_snapshot=str(case.expected_document_id or ""),
                        expected_document_name=case.expected_document.name if case.expected_document else "",
                        expected_paragraph_id_snapshot=str(case.expected_paragraph_id or ""),
                        expected_answer=case.expected_answer,
                        hit=hit,
                        expected_rank=expected_rank,
                        latency_ms=latency_ms,
                        top_score=float(top_score or 0),
                        matches=matches,
                        error_message=error_message,
                    )
                )
        summary = self._build_summary(created_results, len(cases))
        if summary["error_count"] == len(created_results):
            status = KnowledgeEvaluationRunStatus.FAILED
        elif summary["error_count"]:
            status = KnowledgeEvaluationRunStatus.PARTIAL
        else:
            status = KnowledgeEvaluationRunStatus.SUCCESS
        run.status = status
        run.summary = summary
        run.error_message = "\n".join(dict.fromkeys(errors))[:10000]
        run.finished_at = timezone.now()
        run.save(update_fields=["status", "summary", "error_message", "finished_at", "update_time"])
        return self.detail(str(run.id))

    def detail(self, run_id):
        row = self._run_queryset().prefetch_related("results").filter(id=run_id).first()
        if row is None:
            raise AppApiException(404, "评估记录不存在")
        return serialize_run(row, include_results=True)

    def export_rows(self, run_id):
        run = self._run_queryset().filter(id=run_id).first()
        if run is None:
            raise AppApiException(404, "评估记录不存在")
        return run, list(run.results.order_by("mode", "question"))
