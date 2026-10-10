from rest_framework.request import Request
from rest_framework.views import APIView

from common import result
from common.auth import TokenAuth
from common.auth.authentication import WorkspacePermissionMixin
from common.auth.workspace_permissions import workspace_menu_permissions
from common.constants.permission_constants import PermissionConstants
from common.log.log import log
from common.utils.common import query_params_to_single_dict
from marketing.serializers import (
    MarketingQualityPolicyService,
    MarketingQualityReviewService,
    MarketingQualityRuleEffectService,
)


class MarketingQualityPermissionAPIView(WorkspacePermissionMixin, APIView):
    required_workspace_permissions = workspace_menu_permissions(PermissionConstants.MARKETING_QUALITY_READ)


class MarketingQualityReviewView(MarketingQualityPermissionAPIView):
    authentication_classes = [TokenAuth]

    class Page(MarketingQualityPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str, current_page: int, page_size: int):
            return result.success(
                MarketingQualityReviewService(workspace_id, request.user).page(
                    current_page,
                    page_size,
                    query_params_to_single_dict(request.query_params),
                )
            )

    class Handle(MarketingQualityPermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="对话质检", operate="处理质检记录")
        def post(self, request: Request, workspace_id: str, review_id: str):
            return result.success(
                MarketingQualityReviewService(workspace_id, request.user).handle(review_id, request.data)
            )

    class Policy(MarketingQualityPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str):
            return result.success(MarketingQualityPolicyService(workspace_id, request.user).get())

        @log(menu="对话质检", operate="更新质检策略")
        def put(self, request: Request, workspace_id: str):
            return result.success(MarketingQualityPolicyService(workspace_id, request.user).update(request.data))

    class PreflightPage(MarketingQualityPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str, current_page: int, page_size: int):
            return result.success(
                MarketingQualityPolicyService(workspace_id, request.user).page(
                    current_page,
                    page_size,
                    query_params_to_single_dict(request.query_params),
                )
            )

    class RuleEffect(MarketingQualityPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str):
            return result.success(
                MarketingQualityRuleEffectService(workspace_id, request.user).analyze(
                    query_params_to_single_dict(request.query_params)
                )
            )
