from rest_framework.request import Request
from rest_framework.views import APIView

from application.service_answer_review import handle_review, page_reviews
from common import result
from common.auth import TokenAuth
from common.auth.authentication import has_permissions
from common.constants.permission_constants import PermissionConstants, RoleConstants
from common.log.log import log


SERVICE_REVIEW_READ_PERMISSIONS = (
    PermissionConstants.APPLICATION_CHAT_LOG_READ.get_workspace_permission(),
    RoleConstants.ADMIN,
    RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
)
SERVICE_REVIEW_HANDLE_PERMISSIONS = (
    PermissionConstants.APPLICATION_CHAT_LOG_ANNOTATION.get_workspace_permission(),
    RoleConstants.ADMIN,
    RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
)


class ServiceAnswerReviewView(APIView):
    authentication_classes = [TokenAuth]

    class Page(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*SERVICE_REVIEW_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str, current_page: int, page_size: int):
            return result.success(
                page_reviews(workspace_id, current_page, page_size, request.query_params.get("status", "PENDING"))
            )

    class Handle(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*SERVICE_REVIEW_HANDLE_PERMISSIONS)
        @log(menu="服务助手复核", operate="处理服务助手回答复核")
        def post(self, request: Request, workspace_id: str, review_id: str):
            return result.success(
                handle_review(
                    workspace_id,
                    review_id,
                    request.data.get("action"),
                    request.data.get("note"),
                    request.user,
                )
            )
