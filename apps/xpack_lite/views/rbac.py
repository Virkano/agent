import uuid_utils.compat as uuid
from django.db import transaction
from django.db.models import Count, Q
from rest_framework.request import Request
from rest_framework.views import APIView

from common.auth.authenticate import TokenAuth
from common.constants.permission_constants import (
    Group,
    PermissionConstants,
    Permission_Label,
    RoleConstants,
)
from common.exception.app_exception import AppApiException
from common.result import result
from common.utils.common import password_encrypt
from system_manage.models.chat_user import (
    ChatUser,
    ResourceChatUserAuthorize,
    ResourceChatUserGroupAuthorize,
    UserGroup,
    UserGroupRelation,
)
from users.models import User
from xpack_lite.models import ChatAuthSetting, RolePermissionMapping, RoleSetting, Workspace, WorkspaceUserRoleMapping
from xpack_lite.services import (
    chat_user_to_dict,
    get_current_user_manageable_workspaces,
    get_workspace_list_by_user,
    ensure_workspace_root_folders,
    invalidate_user_auth_cache,
    is_admin,
    is_workspace_manager,
    page_result,
    role_to_dict,
    search_chat_users,
    search_users,
)

PERMISSION_NAME_ZH_CN = {
    'SYSTEM_SETTING': '系统设置',
    'USER_MANAGEMENT': '用户管理',
    'ROLE': '角色',
    'WORKSPACE': '工作空间',
    'RESOURCE_APPLICATION': '资源管理-智能体',
    'RESOURCE_KNOWLEDGE': '资源管理-知识库',
    'RESOURCE_TOOL': '资源管理-工具',
    'RESOURCE_MODEL': '资源管理-模型',
    'RESOURCE_PERMISSION': '资源授权',
    'SHARED_KNOWLEDGE': '共享资源-知识库',
    'SHARED_MODEL': '共享资源-模型',
    'SHARED_TOOL': '共享资源-工具',
    'OPERATION_LOG': '操作日志',
    'SYSTEM_MANAGEMENT': '系统管理',
    'APPLICATION': '智能体',
    'KNOWLEDGE': '知识库',
    'MODEL': '模型',
    'TOOL': '工具',
    'TRIGGER': '触发器',
    'OTHER': '其他',
    'READ': '查看',
    'READ+EDIT': '编辑',
    'READ+CREATE': '创建',
    'READ+DELETE': '删除',
    'READ+IMPORT': '导入',
    'READ+EXPORT': '导出',
    'READ+PUBLISH': '发布',
    'READ+SYNC': '同步',
    'READ+GENERATE': '生成问题',
    'READ+ADD_MEMBER': '添加成员',
    'READ+REMOVE_MEMBER': '移除成员',
    'READ+VECTOR': '向量化',
    'READ+MIGRATE': '迁移',
    'READ+RELATE': '关联分段',
    'READ+USER_GROUP': '用户组',
    'READ+ANNOTATION': '标注',
    'READ+CLEAR_POLICY': '清除策略',
    'READ+EMBED': '嵌入第三方',
    'READ+ACCESS': '访问限制',
    'READ+DISPLAY': '显示设置',
    'READ+API_KEY': 'API Key',
    'READ+PUBLIC_ACCESS': '公共访问链接',
    'READ+Q_WEIXIN': '企业微信',
    'READ+FEISHU': '飞书',
    'READ+DD': '钉钉',
    'READ+WEIXIN_PUBLIC_ACCOUNT': '微信公众号',
    'READ+ADD_KNOWLEDGE': '添加到知识库',
    'READ+TO_CHAT': '去对话',
    'READ+SETTING': '管理',
    'READ+DOWNLOAD': '下载原文档',
    'READ+COPY': '复制',
    'READ+AUTH': '资源授权',
    'READ+TAG': '标签设置',
    'READ+REPLACE': '替换原文档',
    'READ+UPDATE': '更新 License',
    'READ+RELATE_VIEW': '查看关联资源',
    'READ+RECORD': '查看执行记录',
    'READ+TRIGGER_READ': '查看触发器',
    'READ+TRIGGER_CREATE': '创建触发器',
    'READ+TRIGGER_EDIT': '编辑触发器',
    'READ+TRIGGER_DELETE': '删除触发器',
    'READ+BATCH_DELETE': '批量删除',
    'READ+BATCH_MOVE': '批量移动',
    'READ+TOKEN': '分词索引',
    'READ+TO_WORKSPACE': '授权到工作空间',
    'EMAIL_SETTING': '邮箱设置',
    'KNOWLEDGE_DOCUMENT': '文档',
    'KNOWLEDGE_PROBLEM': '问题',
    'APPLICATION_OVERVIEW': '概览',
    'APPLICATION_ACCESS': '应用接入',
    'APPLICATION_CHAT_USER': '对话用户',
    'APPLICATION_CHAT_LOG': '对话日志',
    'KNOWLEDGE_CHAT_USER': '对话用户',
    'LOGIN_AUTH': '登录认证',
    'DISPLAY_SETTINGS': '显示设置',
    'SYSTEM_API_KEY': '系统 API Key',
    'APPEARANCE_SETTINGS': '外观设置',
    'CHAT_USER': '对话用户',
    'USER_GROUP': '用户组',
    'CHAT_USER_AUTH': '对话用户认证',
    'OVERVIEW': '概览',
    'HOMEPAGE': '首页',
    'SYSTEM_TOOL': '工具',
    'SYSTEM_MODEL': '模型',
    'SYSTEM_KNOWLEDGE': '知识库',
    'SYSTEM_KNOWLEDGE_DOCUMENT': '文档',
    'SYSTEM_KNOWLEDGE_TERMBASE': '问题',
    'SYSTEM_KNOWLEDGE_WORKFLOW': '工作流',
    'SYSTEM_KNOWLEDGE_TAG': '标签',
    'SYSTEM_KNOWLEDGE_PROBLEM': '问题',
    'SYSTEM_KNOWLEDGE_HIT_TEST': '命中测试',
    'SYSTEM_KNOWLEDGE_CHAT_USER': '对话用户',
    'SYSTEM_RESOURCE_TOOL': '工具',
    'SYSTEM_RESOURCE_MODEL': '模型',
    'SYSTEM_RESOURCE_KNOWLEDGE': '知识库',
    'SYSTEM_RESOURCE_KNOWLEDGE_DOCUMENT': '文档',
    'SYSTEM_RESOURCE_KNOWLEDGE_TERMBASE': '问题',
    'SYSTEM_RESOURCE_KNOWLEDGE_WORKFLOW': '工作流',
    'SYSTEM_RES_KNOWLEDGE_TAG': '标签',
    'SYSTEM_RESOURCE_KNOWLEDGE_PROBLEM': '问题',
    'SYSTEM_RESOURCE_KNOWLEDGE_HIT_TEST': '命中测试',
    'SYSTEM_RESOURCE_KNOWLEDGE_CHAT_USER': '对话用户',
    'WORKSPACE_USER_GROUP': '用户组',
    'WORKSPACE_CHAT_USER': '对话用户',
    'WORKSPACE_WORKSPACE': '工作空间',
    'WORKSPACE_ROLE': '角色',
    'APPLICATION_WORKSPACE_USER_RESOURCE_PERMISSION': '智能体',
    'KNOWLEDGE_WORKSPACE_USER_RESOURCE_PERMISSION': '知识库',
    'MODEL_WORKSPACE_USER_RESOURCE_PERMISSION': '模型',
    'TOOL_WORKSPACE_USER_RESOURCE_PERMISSION': '工具',
    'SYSTEM_RESOURCE_APPLICATION': '智能体',
    'SYSTEM_RESOURCE_APPLICATION_OVERVIEW': '概览',
    'SYSTEM_RESOURCE_APPLICATION_ACCESS': '应用接入',
    'SYSTEM_RESOURCE_APPLICATION_CHAT_USER': '对话用户',
    'SYSTEM_RESOURCE_APPLICATION_CHAT_LOG': '对话日志',
    'APPLICATION_FOLDER': '文件夹',
    'KNOWLEDGE_FOLDER': '文件夹',
    'TOOL_FOLDER': '文件夹',
    'Folder': '文件夹',
    'Application': '智能体',
    'Knowledge': '知识库',
    'Document': '文档',
    'Problem': '问题',
    'Model': '模型',
    'Tool': '工具',
    'Workflow': '工作流',
    'Termbase': '问题',
    'Tag': '标签',
    'Hit-Test': '命中测试',
    'Dialogue users': '对话用户',
    'Conversation log': '对话日志',
    'Application Access': '应用接入',
    'Read': '查看',
    'Edit': '编辑',
    'Create': '创建',
    'Delete': '删除',
    'Import': '导入',
    'Export': '导出',
    'Publish': '发布',
    'Sync': '同步',
    'Generate': '生成问题',
    'Vector': '向量化',
    'resource authorization': '资源授权',
    'View related resources': '查看关联资源',
    'Read Trigger': '查看触发器',
    'Create Trigger': '创建触发器',
    'Edit Trigger': '编辑触发器',
    'Delete Trigger': '删除触发器',
    'Read execute record': '查看执行记录',
    'Token Index': '分词索引',
}


def _permission_name(value):
    label = str(Permission_Label.get(value, value))
    return PERMISSION_NAME_ZH_CN.get(value, PERMISSION_NAME_ZH_CN.get(label, label))


def _require_admin(request):
    if not is_admin(request.user.id):
        raise AppApiException(403, 'No permission to access')


def _require_workspace_manager(request, workspace_id):
    if not is_workspace_manager(request.user.id, workspace_id):
        raise AppApiException(403, 'No permission to access')


def _workspace_resource_exists(workspace_id):
    checks = []
    for dotted, field in [
        ('application.models.Application', 'workspace_id'),
        ('knowledge.models.Knowledge', 'workspace_id'),
        ('tools.models.Tool', 'workspace_id'),
        ('models_provider.models.Model', 'workspace_id'),
    ]:
        try:
            module_path, class_name = dotted.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            model = getattr(module, class_name)
            checks.append(model.objects.filter(**{field: workspace_id}).exists())
        except Exception:
            checks.append(False)
    return any(checks)


def _serialize_workspace_member(relation):
    return {
        'user_relation_id': str(relation.id),
        'user_id': str(relation.user_id),
        'username': relation.user.username,
        'nick_name': relation.user.nick_name,
        'role_id': relation.role_id,
        'role_name': relation.role.role_name,
    }


class WorkspaceListView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request):
        workspace_queryset = Workspace.objects.order_by('create_time')
        if not is_admin(request.user.id):
            manageable_ids = [row['id'] for row in get_current_user_manageable_workspaces(request.user)]
            workspace_queryset = workspace_queryset.filter(id__in=manageable_ids)
        user_counts = WorkspaceUserRoleMapping.objects.values('workspace_id').annotate(count=Count('user_id', distinct=True))
        count_map = {row['workspace_id']: row['count'] for row in user_counts}
        data = [
            {'id': workspace.id, 'name': workspace.name, 'user_count': count_map.get(workspace.id, 0)}
            for workspace in workspace_queryset
        ]
        return result.success(data)

    def post(self, request: Request):
        _require_admin(request)
        name = (request.data or {}).get('name')
        workspace_id = (request.data or {}).get('id')
        if not name or len(name) > 64:
            raise AppApiException(500, 'Workspace name must be 1-64 characters')
        if workspace_id:
            workspace = Workspace.objects.filter(id=workspace_id).first()
            if not workspace:
                raise AppApiException(500, 'Workspace does not exist')
            if Workspace.objects.filter(name=name).exclude(id=workspace_id).exists():
                raise AppApiException(500, 'Workspace name already exists')
            workspace.name = name
            workspace.save()
        else:
            if Workspace.objects.filter(name=name).exists():
                raise AppApiException(500, 'Workspace name already exists')
            workspace = Workspace.objects.create(id=str(uuid.uuid7()), name=name, create_user=request.user)
            ensure_workspace_root_folders(workspace, request.user)
        return result.success({'id': workspace.id, 'name': workspace.name})


class WorkspaceOperateView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, workspace_id):
        _require_admin(request)
        return result.success({'exists': _workspace_resource_exists(workspace_id)})

    def delete(self, request: Request, workspace_id):
        _require_admin(request)
        if workspace_id == 'default':
            raise AppApiException(500, 'Default workspace cannot be deleted')
        if _workspace_resource_exists(workspace_id):
            raise AppApiException(500, 'Workspace has resources and cannot be deleted')
        Workspace.objects.filter(id=workspace_id).delete()
        return result.success(True)


class WorkspaceByUserView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request):
        return result.success(get_workspace_list_by_user(request.user.id))


class CurrentUserWorkspaceView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request):
        return result.success(get_workspace_list_by_user(request.user.id))


class WorkspaceMemberView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, workspace_id, current_page=None, page_size=None):
        _require_workspace_manager(request, workspace_id)
        queryset = WorkspaceUserRoleMapping.objects.select_related('user', 'role').filter(workspace_id=workspace_id)
        username = request.query_params.get('username')
        nick_name = request.query_params.get('nick_name')
        if username:
            queryset = queryset.filter(user__username__icontains=username)
        if nick_name:
            queryset = queryset.filter(user__nick_name__icontains=nick_name)
        queryset = queryset.order_by('user__username', 'role_id')
        if current_page and page_size:
            return result.success(page_result(queryset, current_page, page_size, _serialize_workspace_member))
        return result.success([_serialize_workspace_member(row) for row in queryset[:200]])

    @transaction.atomic
    def post(self, request: Request, workspace_id):
        _require_workspace_manager(request, workspace_id)
        payload = request.data if isinstance(request.data, list) else [request.data]
        for item in payload:
            for user_id in item.get('user_ids', []):
                for role_id in item.get('role_ids', []):
                    WorkspaceUserRoleMapping.objects.get_or_create(
                        workspace_id=workspace_id,
                        role_id=role_id,
                        user_id=user_id,
                        defaults={'id': uuid.uuid7()},
                    )
                    invalidate_user_auth_cache(user_id)
        return result.success(True)


class WorkspaceMemberRemoveView(APIView):
    authentication_classes = [TokenAuth]

    def post(self, request: Request, workspace_id, user_relation_id):
        _require_workspace_manager(request, workspace_id)
        relation = WorkspaceUserRoleMapping.objects.filter(id=user_relation_id, workspace_id=workspace_id).first()
        if not relation:
            return result.success(True)
        if relation.role_id == RoleConstants.ADMIN.name and str(relation.user_id) == 'f0dd8f71-e4ee-11ee-8c84-a8a1595801ab':
            raise AppApiException(500, 'Built-in administrator cannot be removed')
        user_id = relation.user_id
        relation.delete()
        invalidate_user_auth_cache(user_id)
        return result.success(True)


class RoleListView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request):
        roles = RoleSetting.objects.order_by('internal', 'create_time')
        if not is_admin(request.user.id):
            roles = roles.exclude(type=RoleConstants.ADMIN.name)
        internal = [role_to_dict(role) for role in roles.filter(internal=True)]
        custom = [role_to_dict(role) for role in roles.filter(internal=False)]
        return result.success({'internal_role': internal, 'custom_role': custom})

    def post(self, request: Request):
        _require_admin(request)
        role_id = request.data.get('role_id')
        role_name = request.data.get('role_name')
        role_type = request.data.get('role_type')
        if not role_name:
            raise AppApiException(500, 'Role name is required')
        if role_id:
            role = RoleSetting.objects.filter(id=role_id, internal=False).first()
            if not role:
                raise AppApiException(500, 'Role does not exist or is internal')
            role.role_name = role_name
            role.save()
        else:
            if role_type not in [RoleConstants.ADMIN.name, RoleConstants.WORKSPACE_MANAGE.name, RoleConstants.USER.name]:
                raise AppApiException(500, 'Invalid inherited role')
            role = RoleSetting.objects.create(
                id=str(uuid.uuid7()),
                role_name=role_name,
                type=role_type,
                internal=False,
                create_user=request.user,
            )
        return result.success(role_to_dict(role))


class RoleOperateView(APIView):
    authentication_classes = [TokenAuth]

    def delete(self, request: Request, role_id):
        _require_admin(request)
        role = RoleSetting.objects.filter(id=role_id, internal=False).first()
        if not role:
            raise AppApiException(500, 'Role does not exist or is internal')
        user_ids = list(WorkspaceUserRoleMapping.objects.filter(role_id=role_id).values_list('user_id', flat=True))
        role.delete()
        for user_id in user_ids:
            invalidate_user_auth_cache(user_id)
        return result.success(True)


class CurrentUserRoleListView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request):
        roles = RoleSetting.objects.all()
        if not is_admin(request.user.id):
            roles = roles.filter(type=RoleConstants.USER.name)
        return result.success([{'id': role.id, 'name': role.role_name, 'role_name': role.role_name, 'type': role.type} for role in roles])


def _role_permission_tree(role_id=None, template_role_type=None):
    enabled = set()
    if role_id:
        enabled = set(RolePermissionMapping.objects.filter(role_id=role_id).values_list('permission_id', flat=True))
    elif template_role_type:
        for permission in PermissionConstants:
            if any(role.value.name == template_role_type for role in permission.value.role_list):
                enabled.add(str(permission.value))
    modules = {}
    for permission in PermissionConstants:
        p = permission.value
        if not p.is_ee:
            continue
        parent_groups = p.parent_group or []
        if not parent_groups:
            continue
        parent = parent_groups[0].value
        group = p.group.value
        modules.setdefault(parent, {})
        modules[parent].setdefault(group, [])
        modules[parent][group].append({'id': str(p), 'name': _permission_name(p.operate.value), 'enable': str(p) in enabled})
    return [
        {
            'id': parent,
            'name': _permission_name(parent),
            'children': [
                {
                    'id': group,
                    'name': _permission_name(group),
                    'permission': permissions,
                    'enable': all(item['enable'] for item in permissions),
                }
                for group, permissions in children.items()
            ],
        }
        for parent, children in modules.items()
    ]


class RolePermissionView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, role_id):
        return result.success(_role_permission_tree(role_id=role_id))

    @transaction.atomic
    def post(self, request: Request, role_id):
        _require_admin(request)
        role = RoleSetting.objects.filter(id=role_id, internal=False).first()
        if not role:
            raise AppApiException(500, 'Role does not exist or is internal')
        enabled_ids = [item.get('id') for item in request.data if item.get('enable')]
        RolePermissionMapping.objects.filter(role_id=role_id).delete()
        RolePermissionMapping.objects.bulk_create([
            RolePermissionMapping(role_id=role_id, permission_id=permission_id)
            for permission_id in enabled_ids
        ], ignore_conflicts=True)
        for user_id in WorkspaceUserRoleMapping.objects.filter(role_id=role_id).values_list('user_id', flat=True):
            invalidate_user_auth_cache(user_id)
        return result.success(True)


class RoleTemplateView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, role_type):
        return result.success(_role_permission_tree(template_role_type=role_type))


class RoleMemberView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, role_id, current_page, page_size):
        role = RoleSetting.objects.filter(id=role_id).first()
        if not role:
            raise AppApiException(500, 'Role does not exist')
        queryset = WorkspaceUserRoleMapping.objects.select_related('user', 'workspace').filter(role_id=role_id)
        if not is_admin(request.user.id):
            manageable_ids = [w['id'] for w in get_current_user_manageable_workspaces(request.user)]
            queryset = queryset.filter(workspace_id__in=manageable_ids)
        username = request.query_params.get('username')
        nick_name = request.query_params.get('nick_name')
        if username:
            queryset = queryset.filter(user__username__icontains=username)
        if nick_name:
            queryset = queryset.filter(user__nick_name__icontains=nick_name)

        def serialize(row):
            return {
                'user_relation_id': str(row.id),
                'user_id': str(row.user_id),
                'username': row.user.username,
                'nick_name': row.user.nick_name,
                'workspace_id': row.workspace_id,
                'workspace_name': '' if row.workspace_id == 'None' else row.workspace.name,
            }

        return result.success(page_result(queryset.order_by('user__username'), current_page, page_size, serialize))


class RoleMemberAddView(APIView):
    authentication_classes = [TokenAuth]

    @transaction.atomic
    def post(self, request: Request, role_id):
        role = RoleSetting.objects.filter(id=role_id).first()
        if not role:
            raise AppApiException(500, 'Role does not exist')
        members = request.data.get('members', [])
        for item in members:
            for user_id in item.get('user_ids', []):
                for workspace_id in item.get('workspace_ids', ['None']):
                    if role.type != RoleConstants.ADMIN.name:
                        _require_workspace_manager(request, workspace_id)
                    else:
                        _require_admin(request)
                    WorkspaceUserRoleMapping.objects.get_or_create(
                        workspace_id=workspace_id,
                        role_id=role_id,
                        user_id=user_id,
                        defaults={'id': uuid.uuid7()},
                    )
                    invalidate_user_auth_cache(user_id)
        return result.success(True)


class RoleMemberRemoveView(APIView):
    authentication_classes = [TokenAuth]

    def delete(self, request: Request, role_id, user_relation_id):
        relation = WorkspaceUserRoleMapping.objects.filter(id=user_relation_id, role_id=role_id).first()
        if not relation:
            return result.success(True)
        if relation.role.type == RoleConstants.ADMIN.name:
            _require_admin(request)
        else:
            _require_workspace_manager(request, relation.workspace_id)
        user_id = relation.user_id
        relation.delete()
        invalidate_user_auth_cache(user_id)
        return result.success(True)


class ChatUserManageView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, current_page=None, page_size=None):
        queryset = search_chat_users(request.query_params)
        if current_page and page_size:
            return result.success(page_result(queryset, current_page, page_size, chat_user_to_dict))
        return result.success([chat_user_to_dict(row) for row in queryset[:200]])

    @transaction.atomic
    def post(self, request: Request):
        username = request.data.get('username')
        nick_name = request.data.get('nick_name')
        password = request.data.get('password')
        if not username or not nick_name or not password:
            raise AppApiException(500, 'Username, nickname and password are required')
        chat_user = ChatUser.objects.create(
            username=username,
            nick_name=nick_name,
            email=request.data.get('email'),
            phone=request.data.get('phone', ''),
            password=password_encrypt(password),
            source=request.data.get('source', 'LOCAL'),
            is_active=request.data.get('is_active', True),
        )
        _set_chat_user_groups(chat_user.id, request.data.get('user_group_ids', []), replace=True)
        return result.success(chat_user_to_dict(chat_user))


class ChatUserListView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request):
        return result.success([chat_user_to_dict(row) for row in search_chat_users(request.query_params)[:200]])


class ChatUserOperateView(APIView):
    authentication_classes = [TokenAuth]

    def put(self, request: Request, user_id):
        chat_user = ChatUser.objects.filter(id=user_id).first()
        if not chat_user:
            raise AppApiException(500, 'Chat user does not exist')
        for field in ['email', 'phone', 'nick_name', 'is_active']:
            if field in request.data:
                setattr(chat_user, field, request.data.get(field))
        chat_user.save()
        if 'user_group_ids' in request.data:
            _set_chat_user_groups(chat_user.id, request.data.get('user_group_ids', []), replace=True)
        return result.success(chat_user_to_dict(chat_user))

    def delete(self, request: Request, user_id):
        ChatUser.objects.filter(id=user_id).delete()
        return result.success(True)


class ChatUserPasswordView(APIView):
    authentication_classes = [TokenAuth]

    def put(self, request: Request, user_id):
        password = request.data.get('password')
        re_password = request.data.get('re_password')
        if password != re_password:
            raise AppApiException(500, 'Passwords do not match')
        ChatUser.objects.filter(id=user_id).update(password=password_encrypt(password))
        return result.success(True)


class ChatUserBatchDeleteView(APIView):
    authentication_classes = [TokenAuth]

    def post(self, request: Request):
        ChatUser.objects.filter(id__in=request.data).delete()
        return result.success(True)


def _set_chat_user_groups(user_id, group_ids, replace=False):
    if replace:
        UserGroupRelation.objects.filter(user_id=user_id).delete()
    for group_id in group_ids:
        UserGroupRelation.objects.get_or_create(user_id=user_id, group_id=group_id, defaults={'id': uuid.uuid7()})


class ChatUserBatchGroupView(APIView):
    authentication_classes = [TokenAuth]

    def post(self, request: Request):
        user_ids = request.data.get('ids') or request.data.get('user_ids') or []
        group_ids = request.data.get('user_group_ids') or []
        replace = not request.data.get('is_append', True)
        for user_id in user_ids:
            _set_chat_user_groups(user_id, group_ids, replace=replace)
        return result.success(True)


class ChatUserSyncView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request):
        return result.success([{'label': '系统用户', 'value': 'system'}])

    def post(self, request: Request, sync_type):
        _require_admin(request)
        if sync_type != 'system':
            raise AppApiException(500, 'Unsupported sync type')
        user_ids = request.data.get('user_ids') if isinstance(request.data, dict) else []
        if not user_ids:
            raise AppApiException(500, 'Please select users to import')
        default_group = UserGroup.objects.order_by('name').first()
        success_count = 0
        conflict_usernames = []
        for user in User.objects.filter(id__in=user_ids, is_active=True):
            chat_user = ChatUser.objects.filter(username=user.username).first()
            if chat_user is not None and chat_user.source != 'SYSTEM':
                conflict_usernames.append(user.username)
                continue
            if chat_user is None:
                chat_user = ChatUser.objects.create(
                    username=user.username,
                    nick_name=user.nick_name,
                    email=user.email,
                    phone=user.phone,
                    password=user.password,
                    source='SYSTEM',
                    is_active=user.is_active,
                )
                success_count += 1
            else:
                chat_user.nick_name = user.nick_name
                chat_user.email = user.email
                chat_user.phone = user.phone
                chat_user.password = user.password
                chat_user.is_active = user.is_active
                chat_user.save(update_fields=['nick_name', 'email', 'phone', 'password', 'is_active'])
                success_count += 1
            if default_group:
                UserGroupRelation.objects.get_or_create(user=chat_user, group=default_group, defaults={'id': uuid.uuid7()})
        return result.success({
            'success_count': success_count,
            'conflict_users': [{'type': 'username', 'users': conflict_usernames}] if conflict_usernames else [],
        })


class UserGroupView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request):
        return result.success(list(UserGroup.objects.order_by('name').values('id', 'name')))

    def post(self, request: Request):
        name = request.data.get('name')
        group_id = request.data.get('id')
        if not name:
            raise AppApiException(500, 'Group name is required')
        if group_id:
            group = UserGroup.objects.filter(id=group_id).first()
            if not group:
                raise AppApiException(500, 'Group does not exist')
            group.name = name
            group.save()
        else:
            group = UserGroup.objects.create(id=str(uuid.uuid7()), name=name)
        return result.success({'id': group.id, 'name': group.name})


class UserGroupOperateView(APIView):
    authentication_classes = [TokenAuth]

    def delete(self, request: Request, user_group_id):
        UserGroup.objects.filter(id=user_group_id).delete()
        return result.success(True)


class UserGroupMemberView(APIView):
    authentication_classes = [TokenAuth]

    def post(self, request: Request, user_group_id):
        ids = request.data.get('ids') or request.data.get('user_ids') or []
        for user_id in ids:
            UserGroupRelation.objects.get_or_create(user_id=user_id, group_id=user_group_id, defaults={'id': uuid.uuid7()})
        return result.success(True)

    def get(self, request: Request, user_group_id, current_page, page_size):
        queryset = UserGroupRelation.objects.select_related('user').filter(group_id=user_group_id)
        username = request.query_params.get('username')
        nick_name = request.query_params.get('nick_name')
        if username:
            queryset = queryset.filter(user__username__icontains=username)
        if nick_name:
            queryset = queryset.filter(user__nick_name__icontains=nick_name)

        def serialize(row):
            data = chat_user_to_dict(row.user)
            data['user_group_relation_id'] = str(row.id)
            return data

        return result.success(page_result(queryset.order_by('user__username'), current_page, page_size, serialize))


class UserGroupMemberRemoveView(APIView):
    authentication_classes = [TokenAuth]

    def post(self, request: Request, user_group_id):
        ids = request.data.get('ids') or request.data.get('user_group_relation_ids') or []
        UserGroupRelation.objects.filter(id__in=ids, group_id=user_group_id).delete()
        return result.success(True)


class ResourceUserGroupAuthorizeView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, workspace_id, resource_type, resource_id):
        _require_workspace_manager(request, workspace_id)
        auth_map = {
            str(row.user_group_id): row.is_auth
            for row in ResourceChatUserGroupAuthorize.objects.filter(
                workspace_id=workspace_id,
                resource_type=resource_type,
                resource_id=resource_id,
            )
        }
        return result.success([
            {'id': str(group.id), 'name': group.name, 'is_auth': auth_map.get(str(group.id), False)}
            for group in UserGroup.objects.order_by('name')
        ])

    def put(self, request: Request, workspace_id, resource_type, resource_id):
        _require_workspace_manager(request, workspace_id)
        for item in request.data:
            ResourceChatUserGroupAuthorize.objects.update_or_create(
                user_group_id=item.get('user_group_id'),
                resource_id=resource_id,
                resource_type=resource_type,
                defaults={'workspace_id': workspace_id, 'is_auth': item.get('is_auth', False)},
            )
        return result.success(True)


class ResourceUserAuthorizeView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, workspace_id, resource_type, resource_id, user_group_id, current_page, page_size):
        _require_workspace_manager(request, workspace_id)
        group_relations = UserGroupRelation.objects.select_related('user').filter(group_id=user_group_id)
        user_auth = {
            str(row.user_id): row.is_auth
            for row in ResourceChatUserAuthorize.objects.filter(
                workspace_id=workspace_id,
                user_group_id=user_group_id,
                resource_id=resource_id,
                resource_type=resource_type,
            )
        }

        def serialize(row):
            data = chat_user_to_dict(row.user)
            data['is_auth'] = user_auth.get(str(row.user_id), False)
            return data

        return result.success(page_result(group_relations.order_by('user__username'), current_page, page_size, serialize))

    def put(self, request: Request, workspace_id, resource_type, resource_id, user_group_id):
        _require_workspace_manager(request, workspace_id)
        for item in request.data:
            ResourceChatUserAuthorize.objects.update_or_create(
                user_group_id=user_group_id,
                user_id=item.get('chat_user_id'),
                resource_id=resource_id,
                resource_type=resource_type,
                defaults={'workspace_id': workspace_id, 'is_auth': item.get('is_auth', False)},
            )
        return result.success(True)


class ChatAuthSettingView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request):
        data = []
        for auth_type, name in [('ldap', 'LDAP'), ('cas', 'CAS'), ('oidc', 'OIDC'), ('oauth2', 'OAuth2'), ('scan', '扫码登录')]:
            row, _ = ChatAuthSetting.objects.get_or_create(auth_type=auth_type, defaults={'name': name, 'enabled': False})
            data.append({'auth_type': row.auth_type, 'name': row.name, 'enabled': row.enabled, 'config': row.config})
        return result.success(data)
