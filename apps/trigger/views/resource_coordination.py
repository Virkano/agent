from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.views import APIView

from common import result
from common.auth import TokenAuth
from common.auth.authentication import has_permissions
from common.auth.workspace_permissions import workspace_menu_permissions
from common.constants.permission_constants import PermissionConstants
from common.log.log import log
from trigger.resource_coordination import ResourceCoordinationService


RESOURCE_COORDINATION_PERMISSIONS = workspace_menu_permissions(
    PermissionConstants.RESOURCE_COORDINATION_READ
)


def _service(request, workspace_id):
    return ResourceCoordinationService(workspace_id, request.user)


class ResourceCoordinationDashboardView(APIView):
    authentication_classes = [TokenAuth]

    @extend_schema(methods=["GET"], summary=_("Resource coordination dashboard"), tags=[_("Trigger")])
    @has_permissions(*RESOURCE_COORDINATION_PERMISSIONS)
    def get(self, request: Request, workspace_id: str):
        return result.success(_service(request, workspace_id).dashboard())


class ResourcePoolView(APIView):
    authentication_classes = [TokenAuth]

    @extend_schema(methods=["GET"], summary=_("List dispatch resource pools"), tags=[_("Trigger")])
    @has_permissions(*RESOURCE_COORDINATION_PERMISSIONS)
    def get(self, request: Request, workspace_id: str):
        return result.success(_service(request, workspace_id).pools())

    @extend_schema(methods=["POST"], summary=_("Create dispatch resource pool"), tags=[_("Trigger")])
    @has_permissions(*RESOURCE_COORDINATION_PERMISSIONS)
    @log(menu="资源协调中心", operate="创建调度资源池")
    def post(self, request: Request, workspace_id: str):
        return result.success(_service(request, workspace_id).create_pool(request.data))


class DispatchTaskView(APIView):
    authentication_classes = [TokenAuth]

    @extend_schema(methods=["GET"], summary=_("List coordinated tasks"), tags=[_("Trigger")])
    @has_permissions(*RESOURCE_COORDINATION_PERMISSIONS)
    def get(self, request: Request, workspace_id: str):
        return result.success(_service(request, workspace_id).tasks(request.query_params))


class DispatchTaskSubmitView(APIView):
    authentication_classes = [TokenAuth]

    @extend_schema(methods=["POST"], summary=_("Submit coordinated task"), tags=[_("Trigger")])
    @has_permissions(*RESOURCE_COORDINATION_PERMISSIONS)
    @log(menu="资源协调中心", operate="提交协调任务")
    def post(self, request: Request, workspace_id: str, pool_id: str):
        return result.success(_service(request, workspace_id).submit_task(pool_id, request.data))


class DispatchTaskDetailView(APIView):
    authentication_classes = [TokenAuth]

    @extend_schema(methods=["GET"], summary=_("Get coordinated task details"), tags=[_("Trigger")])
    @has_permissions(*RESOURCE_COORDINATION_PERMISSIONS)
    def get(self, request: Request, workspace_id: str, task_id: str):
        return result.success(_service(request, workspace_id).task_detail(task_id))


class DispatchTaskOperateView(APIView):
    authentication_classes = [TokenAuth]

    @extend_schema(methods=["POST"], summary=_("Operate coordinated task"), tags=[_("Trigger")])
    @has_permissions(*RESOURCE_COORDINATION_PERMISSIONS)
    @log(menu="资源协调中心", operate="操作协调任务")
    def post(self, request: Request, workspace_id: str, task_id: str):
        return result.success(_service(request, workspace_id).operate_task(task_id, request.data))


class ResourcePoolReclaimView(APIView):
    authentication_classes = [TokenAuth]

    @extend_schema(methods=["POST"], summary=_("Reclaim expired resource leases"), tags=[_("Trigger")])
    @has_permissions(*RESOURCE_COORDINATION_PERMISSIONS)
    @log(menu="资源协调中心", operate="回收过期资源租约")
    def post(self, request: Request, workspace_id: str, pool_id: str):
        return result.success(_service(request, workspace_id).reclaim_pool(pool_id))
