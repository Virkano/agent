import csv
import json
from io import StringIO

from common import result
from common.auth import TokenAuth
from common.auth.authentication import has_permissions
from common.constants.permission_constants import (
    CompareConstants,
    PermissionConstants,
    RoleConstants,
    ViewPermission,
)
from common.log.log import log
from django.http import HttpResponse
from rest_framework.request import Request
from rest_framework.views import APIView

from knowledge.serializers.evaluation import CASE_CSV_HEADERS, KnowledgeEvaluationService, SEARCH_MODE_LABELS


def _service(request, workspace_id, knowledge_id):
    return KnowledgeEvaluationService(workspace_id, knowledge_id, request.user)


def _read_permissions(view):
    return has_permissions(
        PermissionConstants.KNOWLEDGE_HIT_TEST.get_workspace_knowledge_permission(),
        PermissionConstants.KNOWLEDGE_HIT_TEST.get_workspace_permission_workspace_manage_role(),
        RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
        ViewPermission(
            [RoleConstants.USER.get_workspace_role()],
            [PermissionConstants.KNOWLEDGE.get_workspace_knowledge_permission()],
            CompareConstants.AND,
        ),
    )(view)


def _edit_permissions(view):
    return has_permissions(
        PermissionConstants.KNOWLEDGE_EDIT.get_workspace_knowledge_permission(),
        PermissionConstants.KNOWLEDGE_EDIT.get_workspace_permission_workspace_manage_role(),
        RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
        ViewPermission(
            [RoleConstants.USER.get_workspace_role()],
            [PermissionConstants.KNOWLEDGE.get_workspace_knowledge_permission()],
            CompareConstants.AND,
        ),
    )(view)


class KnowledgeEvaluationDashboardView(APIView):
    authentication_classes = [TokenAuth]

    @_read_permissions
    def get(self, request: Request, workspace_id: str, knowledge_id: str):
        return result.success(_service(request, workspace_id, knowledge_id).dashboard())


class KnowledgeEvaluationOptionsView(APIView):
    authentication_classes = [TokenAuth]

    @_read_permissions
    def get(self, request: Request, workspace_id: str, knowledge_id: str):
        return result.success(
            _service(request, workspace_id, knowledge_id).options(request.query_params.get("document_id"))
        )


class KnowledgeEvaluationCaseView(APIView):
    authentication_classes = [TokenAuth]

    @_edit_permissions
    @log(menu="知识库检索评估", operate="新增评估问题")
    def post(self, request: Request, workspace_id: str, knowledge_id: str):
        return result.success(_service(request, workspace_id, knowledge_id).create_case(request.data))


class KnowledgeEvaluationCaseOperateView(APIView):
    authentication_classes = [TokenAuth]

    @_edit_permissions
    @log(menu="知识库检索评估", operate="编辑评估问题")
    def put(self, request: Request, workspace_id: str, knowledge_id: str, case_id: str):
        return result.success(_service(request, workspace_id, knowledge_id).update_case(case_id, request.data))

    @_edit_permissions
    @log(menu="知识库检索评估", operate="删除评估问题")
    def delete(self, request: Request, workspace_id: str, knowledge_id: str, case_id: str):
        return result.success(_service(request, workspace_id, knowledge_id).delete_case(case_id))


def _case_csv_response(rows, file_name):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(CASE_CSV_HEADERS)
    for row in rows:
        writer.writerow(
            [
                row.question,
                row.expected_document.name if row.expected_document else "",
                row.expected_paragraph.title if row.expected_paragraph else "",
                row.expected_answer,
                "是" if row.enabled else "否",
            ]
        )
    response = HttpResponse(output.getvalue().encode("utf-8-sig"), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{file_name}"'
    return response


class KnowledgeEvaluationCaseTemplateView(APIView):
    authentication_classes = [TokenAuth]

    @_read_permissions
    @log(menu="知识库检索评估", operate="下载评估问题模板")
    def get(self, request: Request, workspace_id: str, knowledge_id: str):
        _service(request, workspace_id, knowledge_id)
        return _case_csv_response([], "knowledge-evaluation-case-template.csv")


class KnowledgeEvaluationCaseImportView(APIView):
    authentication_classes = [TokenAuth]

    @_edit_permissions
    @log(menu="知识库检索评估", operate="导入评估问题")
    def post(self, request: Request, workspace_id: str, knowledge_id: str):
        return result.success(
            _service(request, workspace_id, knowledge_id).import_cases(request.FILES.get("file"))
        )


class KnowledgeEvaluationCaseExportView(APIView):
    authentication_classes = [TokenAuth]

    @_read_permissions
    @log(menu="知识库检索评估", operate="导出评估问题")
    def get(self, request: Request, workspace_id: str, knowledge_id: str):
        rows = _service(request, workspace_id, knowledge_id).case_rows()
        return _case_csv_response(rows, "knowledge-evaluation-cases.csv")


class KnowledgeEvaluationRunView(APIView):
    authentication_classes = [TokenAuth]

    @_read_permissions
    @log(menu="知识库检索评估", operate="执行检索评估")
    def post(self, request: Request, workspace_id: str, knowledge_id: str):
        return result.success(_service(request, workspace_id, knowledge_id).run(request.data))


class KnowledgeEvaluationRunDetailView(APIView):
    authentication_classes = [TokenAuth]

    @_read_permissions
    def get(self, request: Request, workspace_id: str, knowledge_id: str, run_id: str):
        return result.success(_service(request, workspace_id, knowledge_id).detail(run_id))


class KnowledgeEvaluationExportView(APIView):
    authentication_classes = [TokenAuth]

    @_read_permissions
    @log(menu="知识库检索评估", operate="导出检索评估结果")
    def get(self, request: Request, workspace_id: str, knowledge_id: str, run_id: str):
        run, rows = _service(request, workspace_id, knowledge_id).export_rows(run_id)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "问题",
                "检索模式",
                "是否命中",
                "期望文档",
                "期望排名",
                "耗时（毫秒）",
                "最高分",
                "错误",
                "召回结果",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.question,
                    SEARCH_MODE_LABELS.get(row.mode, row.mode),
                    "是" if row.hit else "否",
                    row.expected_document_name,
                    row.expected_rank or "",
                    row.latency_ms,
                    row.top_score,
                    row.error_message,
                    json.dumps(row.matches, ensure_ascii=False),
                ]
            )
        response = HttpResponse(output.getvalue().encode("utf-8-sig"), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="knowledge-evaluation-{run.id}.csv"'
        return response
