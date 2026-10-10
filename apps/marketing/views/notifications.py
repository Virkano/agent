from rest_framework.request import Request
from rest_framework.views import APIView

from common import result
from common.auth import TokenAuth
from common.auth.authentication import WorkspacePermissionMixin
from common.auth.workspace_permissions import workspace_menu_permissions
from common.constants.permission_constants import PermissionConstants
from common.log.log import log
from common.utils.common import query_params_to_single_dict
from marketing.serializers import MarketingNotificationService


class MarketingOperationsPermissionAPIView(WorkspacePermissionMixin, APIView):
    required_workspace_permissions = workspace_menu_permissions(PermissionConstants.MARKETING_OPERATIONS_READ)


class MarketingNotificationView(MarketingOperationsPermissionAPIView):
    authentication_classes = [TokenAuth]

    class Page(MarketingOperationsPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str, current_page: int, page_size: int):
            return result.success(
                MarketingNotificationService(workspace_id, request.user).page(
                    current_page,
                    page_size,
                    query_params_to_single_dict(request.query_params),
                )
            )

    class UnreadCount(MarketingOperationsPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str):
            return result.success(
                {"unread_count": MarketingNotificationService(workspace_id, request.user).unread_count()}
            )

    class Read(MarketingOperationsPermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="营销运营监控", operate="标记通知已读")
        def post(self, request: Request, workspace_id: str, notification_id: str):
            return result.success(
                MarketingNotificationService(workspace_id, request.user).mark_read(notification_id)
            )

    class ReadAll(MarketingOperationsPermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="营销运营监控", operate="全部通知标记已读")
        def post(self, request: Request, workspace_id: str):
            return result.success(MarketingNotificationService(workspace_id, request.user).mark_all_read())
