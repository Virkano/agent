# coding=utf-8
from rest_framework.request import Request
from rest_framework.views import APIView

from common import result
from common.auth import TokenAuth
from common.auth.authentication import has_permissions
from common.constants.permission_constants import PermissionConstants, RoleConstants
from common.log.log import log
from common.utils.common import query_params_to_single_dict
from models_provider.serializers.lifecycle import ModelLifecycleService


class ModelLifecycleView(APIView):
    authentication_classes = [TokenAuth]

    class Overview(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(
            PermissionConstants.MODEL_READ.get_workspace_permission(),
            PermissionConstants.MODEL_READ.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
            RoleConstants.USER.get_workspace_role(),
        )
        def get(self, request: Request, workspace_id: str):
            return result.success(ModelLifecycleService(workspace_id, request.user).overview())

    class Experiment(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(
            PermissionConstants.MODEL_READ.get_workspace_permission(),
            PermissionConstants.MODEL_READ.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
            RoleConstants.USER.get_workspace_role(),
        )
        def get(self, request: Request, workspace_id: str):
            return result.success(
                ModelLifecycleService(workspace_id, request.user).list_experiments(
                    query_params_to_single_dict(request.query_params)
                )
            )

        @has_permissions(
            PermissionConstants.MODEL_CREATE.get_workspace_permission(),
            PermissionConstants.MODEL_CREATE.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
        )
        @log(menu="模型生命周期", operate="创建模型实验")
        def post(self, request: Request, workspace_id: str):
            return result.success(ModelLifecycleService(workspace_id, request.user).create_experiment(request.data))

    class ExperimentOperate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(
            PermissionConstants.MODEL_READ.get_workspace_permission(),
            PermissionConstants.MODEL_READ.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
            RoleConstants.USER.get_workspace_role(),
        )
        def get(self, request: Request, workspace_id: str, experiment_id: str):
            return result.success(ModelLifecycleService(workspace_id, request.user).get_experiment(experiment_id))

        @has_permissions(
            PermissionConstants.MODEL_EDIT.get_workspace_permission(),
            PermissionConstants.MODEL_EDIT.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
        )
        @log(menu="模型生命周期", operate="更新模型实验")
        def put(self, request: Request, workspace_id: str, experiment_id: str):
            return result.success(
                ModelLifecycleService(workspace_id, request.user).update_experiment(experiment_id, request.data)
            )

        @has_permissions(
            PermissionConstants.MODEL_DELETE.get_workspace_permission(),
            PermissionConstants.MODEL_DELETE.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
        )
        @log(menu="模型生命周期", operate="删除模型实验")
        def delete(self, request: Request, workspace_id: str, experiment_id: str):
            return result.success(ModelLifecycleService(workspace_id, request.user).delete_experiment(experiment_id))

    class Version(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(
            PermissionConstants.MODEL_READ.get_workspace_permission(),
            PermissionConstants.MODEL_READ.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
            RoleConstants.USER.get_workspace_role(),
        )
        def get(self, request: Request, workspace_id: str):
            return result.success(
                ModelLifecycleService(workspace_id, request.user).list_versions(
                    query_params_to_single_dict(request.query_params)
                )
            )

        @has_permissions(
            PermissionConstants.MODEL_CREATE.get_workspace_permission(),
            PermissionConstants.MODEL_CREATE.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
        )
        @log(menu="模型生命周期", operate="注册模型版本")
        def post(self, request: Request, workspace_id: str):
            return result.success(ModelLifecycleService(workspace_id, request.user).create_version(request.data))

    class VersionOperate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(
            PermissionConstants.MODEL_READ.get_workspace_permission(),
            PermissionConstants.MODEL_READ.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
            RoleConstants.USER.get_workspace_role(),
        )
        def get(self, request: Request, workspace_id: str, version_id: str):
            return result.success(ModelLifecycleService(workspace_id, request.user).get_version(version_id))

        @has_permissions(
            PermissionConstants.MODEL_EDIT.get_workspace_permission(),
            PermissionConstants.MODEL_EDIT.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
        )
        @log(menu="模型生命周期", operate="更新模型版本")
        def put(self, request: Request, workspace_id: str, version_id: str):
            return result.success(
                ModelLifecycleService(workspace_id, request.user).update_version(version_id, request.data)
            )

        @has_permissions(
            PermissionConstants.MODEL_DELETE.get_workspace_permission(),
            PermissionConstants.MODEL_DELETE.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
        )
        @log(menu="模型生命周期", operate="删除模型版本")
        def delete(self, request: Request, workspace_id: str, version_id: str):
            return result.success(ModelLifecycleService(workspace_id, request.user).delete_version(version_id))

    class Evaluate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(
            PermissionConstants.MODEL_EDIT.get_workspace_permission(),
            PermissionConstants.MODEL_EDIT.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
        )
        @log(menu="模型生命周期", operate="评估模型版本")
        def post(self, request: Request, workspace_id: str, version_id: str):
            return result.success(
                ModelLifecycleService(workspace_id, request.user).evaluate_version(version_id, request.data)
            )

    class Publish(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(
            PermissionConstants.MODEL_EDIT.get_workspace_permission(),
            PermissionConstants.MODEL_EDIT.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
        )
        @log(menu="模型生命周期", operate="发布模型版本")
        def post(self, request: Request, workspace_id: str, version_id: str):
            return result.success(
                ModelLifecycleService(workspace_id, request.user).publish_version(version_id, request.data)
            )

    class Rollback(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(
            PermissionConstants.MODEL_EDIT.get_workspace_permission(),
            PermissionConstants.MODEL_EDIT.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
        )
        @log(menu="模型生命周期", operate="回滚模型版本")
        def post(self, request: Request, workspace_id: str, version_id: str):
            return result.success(
                ModelLifecycleService(workspace_id, request.user).rollback_version(version_id, request.data)
            )

    class Release(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(
            PermissionConstants.MODEL_READ.get_workspace_permission(),
            PermissionConstants.MODEL_READ.get_workspace_permission_workspace_manage_role(),
            RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
            RoleConstants.USER.get_workspace_role(),
        )
        def get(self, request: Request, workspace_id: str):
            registry_name = request.query_params.get("registry_name")
            return result.success(
                ModelLifecycleService(workspace_id, request.user).list_releases(registry_name)
            )
