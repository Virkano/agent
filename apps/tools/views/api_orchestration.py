from rest_framework.request import Request
from rest_framework.views import APIView

from common import result
from common.auth import TokenAuth
from common.auth.authentication import has_permissions
from common.auth.workspace_permissions import workspace_menu_permissions
from common.constants.permission_constants import PermissionConstants
from common.exception.app_exception import AppApiException
from common.log.log import log
from tools.api_orchestration import ApiOrchestrationService


API_READ_PERMISSIONS = workspace_menu_permissions(PermissionConstants.API_ORCHESTRATION_READ)
API_WRITE_PERMISSIONS = API_READ_PERMISSIONS


class ApiOrchestrationView(APIView):
    authentication_classes = [TokenAuth]

    class Dashboard(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*API_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            return result.success(ApiOrchestrationService(workspace_id, request.user).dashboard())

    class Asset(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*API_WRITE_PERMISSIONS)
        @log(menu="API 编排与晓搭", operate="新增 API 资产版本")
        def post(self, request: Request, workspace_id: str):
            return result.success(ApiOrchestrationService(workspace_id, request.user).save_asset(request.data))

    class OpenApiImport(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*API_WRITE_PERMISSIONS)
        @log(menu="API 编排与晓搭", operate="导入 OpenAPI 契约")
        def post(self, request: Request, workspace_id: str):
            return result.success(
                ApiOrchestrationService(workspace_id, request.user).import_openapi(request.data)
            )

    class AssetOperate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*API_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str, asset_id: str):
            return result.success(ApiOrchestrationService(workspace_id, request.user).detail(asset_id))

        @has_permissions(*API_WRITE_PERMISSIONS)
        @log(menu="API 编排与晓搭", operate="更新 API 资产版本")
        def put(self, request: Request, workspace_id: str, asset_id: str):
            return result.success(
                ApiOrchestrationService(workspace_id, request.user).save_asset(request.data, asset_id)
            )

    class Publish(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*API_WRITE_PERMISSIONS)
        @log(menu="API 编排与晓搭", operate="发布 API 资产版本")
        def post(self, request: Request, workspace_id: str, asset_id: str, version_id: str):
            return result.success(
                ApiOrchestrationService(workspace_id, request.user).publish(
                    asset_id, version_id, request.data
                )
            )

    class Enabled(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*API_WRITE_PERMISSIONS)
        @log(menu="API 编排与晓搭", operate="启用或停用 API 资产")
        def post(self, request: Request, workspace_id: str, asset_id: str):
            return result.success(
                ApiOrchestrationService(workspace_id, request.user).set_enabled(
                    asset_id, request.data
                )
            )

    class Rollback(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*API_WRITE_PERMISSIONS)
        @log(menu="API 编排与晓搭", operate="回滚 API 资产版本")
        def post(self, request: Request, workspace_id: str, asset_id: str, version_id: str):
            return result.success(
                ApiOrchestrationService(workspace_id, request.user).rollback(asset_id, version_id)
            )

    class VersionCompare(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*API_READ_PERMISSIONS)
        def get(
            self,
            request: Request,
            workspace_id: str,
            asset_id: str,
            version_id: str,
        ):
            target_version_id = request.query_params.get("target_version_id")
            if not target_version_id:
                raise AppApiException(400, "target_version_id 不能为空")
            return result.success(
                ApiOrchestrationService(workspace_id, request.user).compare_versions(
                    asset_id, version_id, target_version_id
                )
            )

    class MockInvoke(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*API_WRITE_PERMISSIONS)
        @log(menu="API 编排与晓搭", operate="调用晓搭模拟接口")
        def post(self, request: Request, workspace_id: str, asset_id: str):
            return result.success(
                ApiOrchestrationService(workspace_id, request.user).mock_invoke(asset_id, request.data)
            )

    class Bootstrap(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*API_WRITE_PERMISSIONS)
        @log(menu="API 编排与晓搭", operate="初始化 API 编排演示数据")
        def post(self, request: Request, workspace_id: str):
            return result.success(ApiOrchestrationService(workspace_id, request.user).bootstrap_demo())
