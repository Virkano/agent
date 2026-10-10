from rest_framework.request import Request
from rest_framework.views import APIView

from common import result
from common.auth import TokenAuth
from common.auth.authentication import WorkspacePermissionMixin
from common.auth.workspace_permissions import workspace_menu_permissions
from common.constants.permission_constants import PermissionConstants
from common.utils.common import query_params_to_single_dict
from marketing.serializers import MarketingOperationsService


class MarketingOperationsPermissionAPIView(WorkspacePermissionMixin, APIView):
    required_workspace_permissions = workspace_menu_permissions(PermissionConstants.MARKETING_OPERATIONS_READ)


class MarketingOperationsView(MarketingOperationsPermissionAPIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, workspace_id: str):
        return result.success(
            MarketingOperationsService(workspace_id, request.user).overview(
                query_params_to_single_dict(request.query_params)
            )
        )
