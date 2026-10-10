# coding=utf-8
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
from rest_framework.request import Request
from rest_framework.views import APIView

from knowledge.serializers.etl import KnowledgeEtlService


def _service(request, workspace_id, knowledge_id):
    return KnowledgeEtlService(workspace_id, knowledge_id, request.user)


def _read_permissions(view):
    return has_permissions(
        PermissionConstants.KNOWLEDGE_DOCUMENT_READ.get_workspace_knowledge_permission(),
        PermissionConstants.KNOWLEDGE_DOCUMENT_READ.get_workspace_permission_workspace_manage_role(),
        RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
        ViewPermission(
            [RoleConstants.USER.get_workspace_role()],
            [PermissionConstants.KNOWLEDGE.get_workspace_knowledge_permission()],
            CompareConstants.AND,
        ),
    )(view)


def _edit_permissions(view):
    return has_permissions(
        PermissionConstants.KNOWLEDGE_DOCUMENT_EDIT.get_workspace_knowledge_permission(),
        PermissionConstants.KNOWLEDGE_DOCUMENT_EDIT.get_workspace_permission_workspace_manage_role(),
        RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
        ViewPermission(
            [RoleConstants.USER.get_workspace_role()],
            [PermissionConstants.KNOWLEDGE.get_workspace_knowledge_permission()],
            CompareConstants.AND,
        ),
    )(view)


class KnowledgeEtlDashboardView(APIView):
    authentication_classes = [TokenAuth]

    @_read_permissions
    def get(self, request: Request, workspace_id: str, knowledge_id: str):
        return result.success(_service(request, workspace_id, knowledge_id).dashboard())


class KnowledgeEtlRunView(APIView):
    authentication_classes = [TokenAuth]

    @_edit_permissions
    @log(menu="知识库 ETL", operate="启动知识处理任务")
    def post(self, request: Request, workspace_id: str, knowledge_id: str):
        return result.success(_service(request, workspace_id, knowledge_id).start_run(request.data))


class KnowledgeEtlRunDetailView(APIView):
    authentication_classes = [TokenAuth]

    @_read_permissions
    def get(self, request: Request, workspace_id: str, knowledge_id: str, run_id: str):
        return result.success(_service(request, workspace_id, knowledge_id).get_run(run_id))


class KnowledgeEtlRunRetryView(APIView):
    authentication_classes = [TokenAuth]

    @_edit_permissions
    @log(menu="知识库 ETL", operate="重试知识处理任务")
    def post(self, request: Request, workspace_id: str, knowledge_id: str, run_id: str):
        return result.success(_service(request, workspace_id, knowledge_id).retry_run(run_id))


class KnowledgeEtlRunPublishView(APIView):
    authentication_classes = [TokenAuth]

    @_edit_permissions
    @log(menu="知识库 ETL", operate="发布知识索引版本")
    def post(self, request: Request, workspace_id: str, knowledge_id: str, run_id: str):
        return result.success(_service(request, workspace_id, knowledge_id).publish_run(run_id, request.data))


class KnowledgeIndexVersionRollbackView(APIView):
    authentication_classes = [TokenAuth]

    @_edit_permissions
    @log(menu="知识库 ETL", operate="回滚知识索引版本")
    def post(self, request: Request, workspace_id: str, knowledge_id: str, version_id: str):
        return result.success(_service(request, workspace_id, knowledge_id).rollback_version(version_id, request.data))
