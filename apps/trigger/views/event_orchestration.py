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
from trigger.event_orchestration import EventOrchestrationService


EVENT_ORCHESTRATION_PERMISSIONS = workspace_menu_permissions(
    PermissionConstants.EVENT_ORCHESTRATION_READ
)


def _service(request, workspace_id):
    return EventOrchestrationService(workspace_id, request.user)


class EventOrchestrationDashboardView(APIView):
    authentication_classes = [TokenAuth]

    @extend_schema(methods=["GET"], summary=_("Event orchestration dashboard"), tags=[_("Trigger")])
    @has_permissions(*EVENT_ORCHESTRATION_PERMISSIONS)
    def get(self, request: Request, workspace_id: str):
        return result.success(_service(request, workspace_id).dashboard())


class EventFlowView(APIView):
    authentication_classes = [TokenAuth]

    @extend_schema(methods=["GET"], summary=_("List event flow versions"), tags=[_("Trigger")])
    @has_permissions(*EVENT_ORCHESTRATION_PERMISSIONS)
    def get(self, request: Request, workspace_id: str):
        return result.success(_service(request, workspace_id).flows())

    @extend_schema(methods=["POST"], summary=_("Create event flow version"), tags=[_("Trigger")])
    @has_permissions(*EVENT_ORCHESTRATION_PERMISSIONS)
    @log(menu="事件任务编排", operate="创建事件流程版本")
    def post(self, request: Request, workspace_id: str):
        return result.success(_service(request, workspace_id).create_flow(request.data))


class EventFlowDetailView(APIView):
    authentication_classes = [TokenAuth]

    @extend_schema(methods=["GET"], summary=_("Get event flow version"), tags=[_("Trigger")])
    @has_permissions(*EVENT_ORCHESTRATION_PERMISSIONS)
    def get(self, request: Request, workspace_id: str, flow_id: str):
        return result.success(_service(request, workspace_id).flow_detail(flow_id))


class EventFlowPublishView(APIView):
    authentication_classes = [TokenAuth]

    @extend_schema(methods=["POST"], summary=_("Publish event flow version"), tags=[_("Trigger")])
    @has_permissions(*EVENT_ORCHESTRATION_PERMISSIONS)
    @log(menu="事件任务编排", operate="发布事件流程版本")
    def post(self, request: Request, workspace_id: str, flow_id: str):
        return result.success(_service(request, workspace_id).publish_flow(flow_id))


class StandardEventReceiveView(APIView):
    authentication_classes = [TokenAuth]

    @extend_schema(methods=["POST"], summary=_("Receive a standard event"), tags=[_("Trigger")])
    @has_permissions(*EVENT_ORCHESTRATION_PERMISSIONS)
    @log(menu="事件任务编排", operate="接收标准事件")
    def post(self, request: Request, workspace_id: str):
        return result.success(_service(request, workspace_id).receive_event(request.data))


class EventFlowRunView(APIView):
    authentication_classes = [TokenAuth]

    @extend_schema(methods=["GET"], summary=_("List event flow runs"), tags=[_("Trigger")])
    @has_permissions(*EVENT_ORCHESTRATION_PERMISSIONS)
    def get(self, request: Request, workspace_id: str):
        return result.success(_service(request, workspace_id).runs())


class EventFlowRunDetailView(APIView):
    authentication_classes = [TokenAuth]

    @extend_schema(methods=["GET"], summary=_("Get event flow run"), tags=[_("Trigger")])
    @has_permissions(*EVENT_ORCHESTRATION_PERMISSIONS)
    def get(self, request: Request, workspace_id: str, run_id: str):
        return result.success(_service(request, workspace_id).run_detail(run_id))


class EventFlowRunAdvanceView(APIView):
    authentication_classes = [TokenAuth]

    @extend_schema(methods=["POST"], summary=_("Advance an event flow run"), tags=[_("Trigger")])
    @has_permissions(*EVENT_ORCHESTRATION_PERMISSIONS)
    @log(menu="事件任务编排", operate="推进事件流程运行")
    def post(self, request: Request, workspace_id: str, run_id: str):
        return result.success(_service(request, workspace_id).advance_run(run_id))


class EventFlowRunReplayView(APIView):
    authentication_classes = [TokenAuth]

    @extend_schema(methods=["POST"], summary=_("Replay an event flow run"), tags=[_("Trigger")])
    @has_permissions(*EVENT_ORCHESTRATION_PERMISSIONS)
    @log(menu="事件任务编排", operate="重放事件流程运行")
    def post(self, request: Request, workspace_id: str, run_id: str):
        return result.success(_service(request, workspace_id).replay_run(run_id, request.data))


class EventFlowNodeOperateView(APIView):
    authentication_classes = [TokenAuth]

    @extend_schema(methods=["POST"], summary=_("Operate an event flow node"), tags=[_("Trigger")])
    @has_permissions(*EVENT_ORCHESTRATION_PERMISSIONS)
    @log(menu="事件任务编排", operate="操作事件流程节点")
    def post(self, request: Request, workspace_id: str, run_id: str, node_id: str):
        return result.success(
            _service(request, workspace_id).operate_node(run_id, node_id, request.data)
        )
