# coding=utf-8
from rest_framework.request import Request
from rest_framework.views import APIView

from common import result
from common.auth import TokenAuth
from common.auth.authentication import WorkspacePermissionMixin
from common.auth.workspace_permissions import workspace_menu_permissions
from common.constants.permission_constants import PermissionConstants
from common.log.log import log
from common.utils.common import query_params_to_single_dict
from marketing.serializers import MarketingScenarioService


class MarketingScenarioPermissionAPIView(WorkspacePermissionMixin, APIView):
    required_workspace_permissions = workspace_menu_permissions(PermissionConstants.MARKETING_SCENARIO_READ)


class MarketingScenarioView(MarketingScenarioPermissionAPIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, workspace_id: str):
        return result.success(
            MarketingScenarioService(workspace_id, request.user).list(query_params_to_single_dict(request.query_params))
        )

    @log(menu="营销场景", operate="新增营销场景")
    def post(self, request: Request, workspace_id: str):
        return result.success(MarketingScenarioService(workspace_id, request.user).create(request.data))

    class Page(MarketingScenarioPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str, current_page: int, page_size: int):
            return result.success(
                MarketingScenarioService(workspace_id, request.user).page(
                    current_page, page_size, query_params_to_single_dict(request.query_params)
                )
            )

    class Operate(MarketingScenarioPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str, scenario_id: str):
            return result.success(MarketingScenarioService(workspace_id, request.user).get(scenario_id))

        @log(menu="营销场景", operate="编辑营销场景")
        def put(self, request: Request, workspace_id: str, scenario_id: str):
            return result.success(
                MarketingScenarioService(workspace_id, request.user).update(scenario_id, request.data)
            )

        @log(menu="营销场景", operate="删除营销场景")
        def delete(self, request: Request, workspace_id: str, scenario_id: str):
            return result.success(MarketingScenarioService(workspace_id, request.user).delete(scenario_id))

    class RecommendationSimulate(MarketingScenarioPermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="营销场景", operate="执行推荐模拟")
        def post(self, request: Request, workspace_id: str, scenario_id: str):
            return result.success(
                MarketingScenarioService(workspace_id, request.user).simulate_recommendation(scenario_id, request.data)
            )
