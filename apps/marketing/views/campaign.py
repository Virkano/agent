from urllib.parse import quote

from django.http import HttpResponse
from rest_framework.request import Request
from rest_framework.views import APIView

from common import result
from common.auth import TokenAuth
from common.auth.authentication import WorkspacePermissionMixin
from common.auth.workspace_permissions import workspace_menu_permissions
from common.constants.permission_constants import PermissionConstants
from common.log.log import log
from common.utils.common import query_params_to_single_dict
from marketing.exporting import build_campaign_effect_workbook
from marketing.serializers.campaign import MarketingCampaignService


class MarketingCampaignPermissionAPIView(WorkspacePermissionMixin, APIView):
    required_workspace_permissions = workspace_menu_permissions(PermissionConstants.MARKETING_CAMPAIGN_READ)


class MarketingCampaignView(MarketingCampaignPermissionAPIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, workspace_id: str):
        params = query_params_to_single_dict(request.query_params)
        return result.success(MarketingCampaignService(workspace_id, request.user).list(params))

    @log(menu="营销活动库", operate="新增营销活动")
    def post(self, request: Request, workspace_id: str):
        return result.success(MarketingCampaignService(workspace_id, request.user).create(request.data))

    class Page(MarketingCampaignPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str, current_page: int, page_size: int):
            params = query_params_to_single_dict(request.query_params)
            service = MarketingCampaignService(workspace_id, request.user)
            return result.success(service.page(current_page, page_size, params))

    class Operate(MarketingCampaignPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str, campaign_id: str):
            return result.success(MarketingCampaignService(workspace_id, request.user).get(campaign_id))

        @log(menu="营销活动库", operate="编辑营销活动")
        def put(self, request: Request, workspace_id: str, campaign_id: str):
            return result.success(
                MarketingCampaignService(workspace_id, request.user).update(campaign_id, request.data)
            )

        @log(menu="营销活动库", operate="删除营销活动")
        def delete(self, request: Request, workspace_id: str, campaign_id: str):
            return result.success(MarketingCampaignService(workspace_id, request.user).delete(campaign_id))

    class Submit(MarketingCampaignPermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="营销活动库", operate="提交营销活动审批")
        def post(self, request: Request, workspace_id: str, campaign_id: str):
            return result.success(MarketingCampaignService(workspace_id, request.user).submit(campaign_id))

    class Approval(MarketingCampaignPermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="营销活动库", operate="审批营销活动")
        def post(self, request: Request, workspace_id: str, campaign_id: str):
            return result.success(
                MarketingCampaignService(workspace_id, request.user).approve(campaign_id, request.data)
            )

    class Effect(MarketingCampaignPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str, campaign_id: str):
            return result.success(MarketingCampaignService(workspace_id, request.user).effect(campaign_id))

    class EffectExport(MarketingCampaignPermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="营销活动库", operate="导出营销活动复盘")
        def get(self, request: Request, workspace_id: str, campaign_id: str):
            effect = MarketingCampaignService(workspace_id, request.user).effect(campaign_id)
            output = build_campaign_effect_workbook(effect)
            file_name = f"{effect['campaign']['name']}-活动复盘.xlsx"
            response = HttpResponse(
                output.getvalue(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = f"attachment; filename*=UTF-8''{quote(file_name)}"
            return response

    class RecommendationAction(MarketingCampaignPermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="营销活动库", operate="执行活动推荐")
        def post(self, request: Request, workspace_id: str, campaign_id: str):
            return result.success(
                MarketingCampaignService(workspace_id, request.user).execute_recommendation(campaign_id, request.data)
            )

    class Versions(MarketingCampaignPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str, campaign_id: str):
            return result.success(MarketingCampaignService(workspace_id, request.user).versions(campaign_id))

    class Restore(MarketingCampaignPermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="营销活动库", operate="恢复营销活动历史版本")
        def post(self, request: Request, workspace_id: str, campaign_id: str, version: int):
            return result.success(MarketingCampaignService(workspace_id, request.user).restore(campaign_id, version))
