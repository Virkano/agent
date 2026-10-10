# coding=utf-8
from rest_framework.request import Request
from rest_framework.views import APIView

from common import result
from common.auth import TokenAuth
from common.auth.authentication import has_permissions
from common.constants.permission_constants import PermissionConstants, RoleConstants
from common.log.log import log
from common.utils.common import query_params_to_single_dict
from models_provider.serializers.pipeline import ModelPipelineService


class ModelPipelineView(APIView):
    authentication_classes = [TokenAuth]

    class Pipeline(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(
            PermissionConstants.MODEL_READ.get_workspace_permission(),
            PermissionConstants.MODEL_READ.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
            RoleConstants.USER.get_workspace_role(),
        )
        def get(self, request: Request, workspace_id: str):
            filters = query_params_to_single_dict(request.query_params)
            return result.success(ModelPipelineService(workspace_id, request.user).list_pipelines(filters))

        @has_permissions(
            PermissionConstants.MODEL_CREATE.get_workspace_permission(),
            PermissionConstants.MODEL_CREATE.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
        )
        @log(menu="模型训练流水线", operate="创建训练流水线")
        def post(self, request: Request, workspace_id: str):
            return result.success(ModelPipelineService(workspace_id, request.user).create_pipeline(request.data))

    class PipelineOperate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(
            PermissionConstants.MODEL_READ.get_workspace_permission(),
            PermissionConstants.MODEL_READ.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
            RoleConstants.USER.get_workspace_role(),
        )
        def get(self, request: Request, workspace_id: str, pipeline_id: str):
            return result.success(ModelPipelineService(workspace_id, request.user).get_pipeline(pipeline_id))

        @has_permissions(
            PermissionConstants.MODEL_EDIT.get_workspace_permission(),
            PermissionConstants.MODEL_EDIT.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
        )
        @log(menu="模型训练流水线", operate="更新训练流水线")
        def put(self, request: Request, workspace_id: str, pipeline_id: str):
            service = ModelPipelineService(workspace_id, request.user)
            return result.success(service.update_pipeline(pipeline_id, request.data))

        @has_permissions(
            PermissionConstants.MODEL_DELETE.get_workspace_permission(),
            PermissionConstants.MODEL_DELETE.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
        )
        @log(menu="模型训练流水线", operate="删除训练流水线")
        def delete(self, request: Request, workspace_id: str, pipeline_id: str):
            return result.success(ModelPipelineService(workspace_id, request.user).delete_pipeline(pipeline_id))

    class RunList(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(
            PermissionConstants.MODEL_READ.get_workspace_permission(),
            PermissionConstants.MODEL_READ.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
            RoleConstants.USER.get_workspace_role(),
        )
        def get(self, request: Request, workspace_id: str):
            filters = query_params_to_single_dict(request.query_params)
            return result.success(ModelPipelineService(workspace_id, request.user).list_runs(filters))

    class Run(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(
            PermissionConstants.MODEL_EDIT.get_workspace_permission(),
            PermissionConstants.MODEL_EDIT.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
        )
        @log(menu="模型训练流水线", operate="启动训练流水线")
        def post(self, request: Request, workspace_id: str, pipeline_id: str):
            return result.success(ModelPipelineService(workspace_id, request.user).start_run(pipeline_id, request.data))

    class RunOperate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(
            PermissionConstants.MODEL_READ.get_workspace_permission(),
            PermissionConstants.MODEL_READ.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
            RoleConstants.USER.get_workspace_role(),
        )
        def get(self, request: Request, workspace_id: str, run_id: str):
            return result.success(ModelPipelineService(workspace_id, request.user).get_run(run_id))

    class Approve(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(
            PermissionConstants.MODEL_EDIT.get_workspace_permission(),
            PermissionConstants.MODEL_EDIT.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
        )
        @log(menu="模型训练流水线", operate="审批流水线运行")
        def post(self, request: Request, workspace_id: str, run_id: str):
            return result.success(ModelPipelineService(workspace_id, request.user).approve_run(run_id, request.data))

    class Retry(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(
            PermissionConstants.MODEL_EDIT.get_workspace_permission(),
            PermissionConstants.MODEL_EDIT.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
        )
        @log(menu="模型训练流水线", operate="重试流水线运行")
        def post(self, request: Request, workspace_id: str, run_id: str):
            return result.success(ModelPipelineService(workspace_id, request.user).retry_run(run_id))
