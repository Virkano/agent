from common.database_model_manage.handle.base_handle import IBaseModelHandle
from system_manage.models.chat_user import ChatUser, UserGroup, UserGroupRelation
from xpack_lite.models import (
    ApplicationSetting,
    ChatPlatform,
    RolePermissionMapping,
    RoleSetting,
    SharedResourceWorkspaceAuthorization,
    Workspace,
    WorkspaceUserRoleMapping,
)
from xpack_lite.services import (
    ensure_xpack_defaults,
    get_authorized_knowledge,
    get_authorized_model,
    get_authorized_tool,
    get_knowledge_list_of_authorized,
    get_workspace_list_by_user,
    is_auth_chat_user,
    local_license_is_valid,
)


class LocalXpackModelHandle(IBaseModelHandle):
    def get_model_dict(self):
        ensure_xpack_defaults()
        return {
            'workspace_model': Workspace,
            'role_model': RoleSetting,
            'role_permission_mapping_model': RolePermissionMapping,
            'workspace_user_role_mapping': WorkspaceUserRoleMapping,
            'chat_user': ChatUser,
            'user_group': UserGroup,
            'user_group_relation': UserGroupRelation,
            'application_setting': ApplicationSetting,
            'chat_platform': ChatPlatform,
            'knowledge_workspace_authorization': SharedResourceWorkspaceAuthorization,
            'shared_resource_workspace_authorization': SharedResourceWorkspaceAuthorization,
            'get_authorized_knowledge': get_authorized_knowledge,
            'get_authorized_model': get_authorized_model,
            'get_authorized_tool': get_authorized_tool,
            'get_workspace_list_by_user': get_workspace_list_by_user,
            'get_knowledge_list_of_authorized': get_knowledge_list_of_authorized,
            'is_auth_chat_user': is_auth_chat_user,
            'license_is_valid': local_license_is_valid,
        }
