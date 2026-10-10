import uuid_utils.compat as uuid
from django.core.cache import cache
from django.db.models import Q

from common.constants.cache_version import Cache_Version
from common.constants.permission_constants import PermissionConstants, RoleConstants, WorkspaceGroup
from application.models import Application, ApplicationFolder
from common.constants.permission_constants import Group
from knowledge.models import Knowledge, KnowledgeFolder
from system_manage.models.chat_user import (
    ChatUser,
    ResourceChatUserAuthorize,
    ResourceChatUserGroupAuthorize,
    UserGroup,
    UserGroupRelation,
)
from tools.models import ToolFolder
from users.models import User
from xpack_lite.models import (
    ApplicationSetting,
    ChatPlatform,
    PlatformDisplaySetting,
    RolePermissionMapping,
    RoleSetting,
    SharedResourceWorkspaceAuthorization,
    Workspace,
    WorkspaceUserRoleMapping,
)


BUILTIN_ROLES = (
    (RoleConstants.ADMIN.name, '系统管理员', RoleConstants.ADMIN.name),
    (RoleConstants.WORKSPACE_MANAGE.name, '工作空间管理员', RoleConstants.WORKSPACE_MANAGE.name),
    (RoleConstants.USER.name, '普通用户', RoleConstants.USER.name),
)

DEFAULT_DISPLAY_SETTING = {
    'theme': '#3370FF',
    'icon': '',
    'loginLogo': '',
    'loginImage': '',
    'title': '电信智能体',
    'slogan': '开箱即用、灵活编排的企业级智能体平台',
    'showUserManual': False,
    'userManualUrl': '',
    'showForum': False,
    'forumUrl': '',
    'showProject': False,
    'projectUrl': '',
}


def local_xpack_enabled():
    return True


def local_license_is_valid():
    return True


def _get_authorized_shared_resource(queryset, workspace_id, resource_type):
    if workspace_id in (None, '', 'None'):
        return queryset

    resource_ids = [str(resource_id) for resource_id in queryset.values_list('id', flat=True)]
    auth_rows = SharedResourceWorkspaceAuthorization.objects.filter(
        resource_type=resource_type,
        id__in=resource_ids,
    )
    allowed_ids = []
    for row in auth_rows:
        workspace_ids = [str(workspace_id) for workspace_id in (row.workspace_id_list or [])]
        current_workspace_id = str(workspace_id)
        if row.authentication_type == 'WHITE_LIST':
            is_allowed = current_workspace_id in workspace_ids
        else:
            is_allowed = current_workspace_id not in workspace_ids
        if is_allowed:
            allowed_ids.append(row.id)
    return queryset.filter(id__in=allowed_ids)


def get_authorized_tool(queryset, workspace_id):
    return _get_authorized_shared_resource(queryset, workspace_id, Group.TOOL.value)


def get_authorized_knowledge(queryset, workspace_id):
    return _get_authorized_shared_resource(queryset, workspace_id, Group.KNOWLEDGE.value)


def get_authorized_model(queryset, workspace_id):
    return _get_authorized_shared_resource(queryset, workspace_id, Group.MODEL.value)


def invalidate_user_auth_cache(user_id):
    permission_version, permission_get_key = Cache_Version.PERMISSION_LIST.value
    cache.delete(permission_get_key(str(user_id)), version=permission_version)
    role_version, role_get_key = Cache_Version.ROLE_LIST.value
    cache.delete(role_get_key(str(user_id)), version=role_version)


def ensure_xpack_defaults():
    admin_user = User.objects.filter(username='admin').first()
    default_workspace, _ = Workspace.objects.get_or_create(
        id='default',
        defaults={'name': '默认空间', 'create_user_id': admin_user.id if admin_user else None},
    )
    if default_workspace.name == 'default':
        default_workspace.name = '默认空间'
        default_workspace.save(update_fields=['name'])
    ensure_workspace_root_folders(default_workspace, admin_user)
    for role_id, role_name, role_type in BUILTIN_ROLES:
        role, created = RoleSetting.objects.get_or_create(
            id=role_id,
            defaults={
                'role_name': role_name,
                'type': role_type,
                'internal': True,
                'create_user_id': admin_user.id if admin_user else None,
            },
        )
        if not created:
            changed_fields = []
            for field, value in {'role_name': role_name, 'type': role_type, 'internal': True}.items():
                if getattr(role, field) != value:
                    setattr(role, field, value)
                    changed_fields.append(field)
            if admin_user and role.create_user_id != admin_user.id:
                role.create_user_id = admin_user.id
                changed_fields.append('create_user')
            if changed_fields:
                role.save(update_fields=changed_fields)
    seed_builtin_role_permissions()
    UserGroup.objects.get_or_create(id='default', defaults={'name': '默认用户组'})
    chat_platform, created = ChatPlatform.objects.get_or_create(
        auth_type='LOCAL',
        defaults={'name': '本地账号', 'is_active': True, 'is_valid': True},
    )
    if not created and (chat_platform.name != '本地账号' or not chat_platform.is_active or not chat_platform.is_valid):
        chat_platform.name = '本地账号'
        chat_platform.is_active = True
        chat_platform.is_valid = True
        chat_platform.save(update_fields=['name', 'is_active', 'is_valid'])
    PlatformDisplaySetting.objects.get_or_create(id='default', defaults={'meta': DEFAULT_DISPLAY_SETTING})
    for application in Application.objects.all():
        ApplicationSetting.objects.get_or_create(application=application)
    if admin_user:
        for role_id in [RoleConstants.ADMIN.name, RoleConstants.WORKSPACE_MANAGE.name, RoleConstants.USER.name]:
            WorkspaceUserRoleMapping.objects.get_or_create(
                workspace_id='default',
                role_id=role_id,
                user_id=admin_user.id,
                defaults={'id': uuid.uuid7()},
            )
    for workspace in Workspace.objects.all():
        ensure_workspace_root_folders(workspace, admin_user or workspace.create_user)
        if admin_user:
            WorkspaceUserRoleMapping.objects.get_or_create(
                workspace_id=workspace.id,
                role_id=RoleConstants.WORKSPACE_MANAGE.name,
                user_id=admin_user.id,
                defaults={'id': uuid.uuid7()},
            )
    if admin_user:
        invalidate_user_auth_cache(admin_user.id)


def ensure_workspace_root_folders(workspace, user=None):
    user_id = user.id if user else None
    for folder_model in [ApplicationFolder, KnowledgeFolder, ToolFolder]:
        folder_model.objects.get_or_create(
            id=workspace.id,
            defaults={
                'name': '根目录',
                'user_id': user_id,
                'workspace_id': workspace.id,
            },
        )


def seed_builtin_role_permissions():
    permission_rows = []
    for permission in PermissionConstants:
        permission_id = str(permission.value)
        for role in permission.value.role_list:
            permission_rows.append((role.value.name, permission_id))
        if _is_workspace_manage_default_permission(permission):
            permission_rows.append((RoleConstants.WORKSPACE_MANAGE.name, permission_id))
    existing = set(
        RolePermissionMapping.objects.filter(
            role_id__in=[r[0] for r in BUILTIN_ROLES],
        ).values_list('role_id', 'permission_id')
    )
    bulk = [
        RolePermissionMapping(role_id=role_id, permission_id=permission_id)
        for role_id, permission_id in permission_rows
        if (role_id, permission_id) not in existing
    ]
    if bulk:
        RolePermissionMapping.objects.bulk_create(bulk, ignore_conflicts=True)


def _is_workspace_manage_default_permission(permission):
    permission_value = permission.value
    parent_groups = permission_value.parent_group or []
    return permission_value.is_ee and any(isinstance(group, WorkspaceGroup) for group in parent_groups)


def get_workspace_list_by_user(user_id):
    if is_admin(user_id):
        return list(Workspace.objects.order_by('create_time').values('id', 'name'))
    workspace_ids = WorkspaceUserRoleMapping.objects.filter(user_id=user_id).values('workspace_id')
    return list(Workspace.objects.filter(id__in=workspace_ids).order_by('create_time').values('id', 'name'))


def get_current_user_manageable_workspaces(user):
    if is_admin(user.id):
        return list(Workspace.objects.order_by('create_time').values('id', 'name'))
    workspace_ids = WorkspaceUserRoleMapping.objects.filter(
        user_id=user.id,
        role__type=RoleConstants.WORKSPACE_MANAGE.name,
    ).values('workspace_id')
    return list(Workspace.objects.filter(id__in=workspace_ids).order_by('create_time').values('id', 'name'))


def is_admin(user_id):
    return WorkspaceUserRoleMapping.objects.filter(user_id=user_id, role_id=RoleConstants.ADMIN.name).exists()


def is_workspace_manager(user_id, workspace_id):
    return is_admin(user_id) or WorkspaceUserRoleMapping.objects.filter(
        user_id=user_id,
        workspace_id=workspace_id,
        role__type=RoleConstants.WORKSPACE_MANAGE.name,
    ).exists()


def role_to_dict(role):
    return {
        'id': role.id,
        'role_name': role.role_name,
        'type': role.type,
        'create_user': str(role.create_user_id or ''),
        'internal': role.internal,
        'user_count': WorkspaceUserRoleMapping.objects.filter(role_id=role.id).values('user_id').distinct().count(),
    }


def chat_user_to_dict(chat_user):
    group_relations = UserGroupRelation.objects.select_related('group').filter(user_id=chat_user.id)
    return {
        'id': str(chat_user.id),
        'email': chat_user.email,
        'phone': chat_user.phone,
        'nick_name': chat_user.nick_name,
        'username': chat_user.username,
        'source': chat_user.source,
        'is_active': chat_user.is_active,
        'create_time': chat_user.create_time,
        'update_time': chat_user.update_time,
        'user_group_ids': [str(r.group_id) for r in group_relations],
        'user_group_names': [r.group.name for r in group_relations],
    }


def page_result(queryset, current_page, page_size, serializer):
    current_page = int(current_page)
    page_size = int(page_size)
    total = queryset.count()
    start = (current_page - 1) * page_size
    records = [serializer(row) for row in queryset[start:start + page_size]]
    return {'total': total, 'records': records, 'current': current_page, 'size': page_size}


def search_users(params):
    queryset = User.objects.all().order_by('-create_time')
    username = params.get('username')
    nick_name = params.get('nick_name')
    if username:
        queryset = queryset.filter(username__icontains=username)
    if nick_name:
        queryset = queryset.filter(nick_name__icontains=nick_name)
    return queryset


def search_chat_users(params):
    value = params.get('username_or_nickname') or params.get('username') or params.get('nick_name')
    queryset = ChatUser.objects.all().order_by('-create_time')
    if value:
        queryset = queryset.filter(Q(username__icontains=value) | Q(nick_name__icontains=value))
    return queryset


def get_knowledge_list_of_authorized(chat_user_id, knowledge_id_list):
    return _get_authorized_resource_ids(chat_user_id, knowledge_id_list, Group.KNOWLEDGE.value)


def is_auth_chat_user(chat_user_id, application_id):
    return len(_get_authorized_resource_ids(chat_user_id, [application_id], Group.APPLICATION.value)) > 0


def _get_resource_workspace_ids(resource_ids, resource_type):
    """Map resources to workspaces so chat-user authorization cannot cross workspaces."""
    resource_ids = [str(resource_id) for resource_id in (resource_ids or [])]
    if resource_type == Group.APPLICATION.value:
        rows = Application.objects.filter(id__in=resource_ids).values('id', 'workspace_id')
    elif resource_type == Group.KNOWLEDGE.value:
        rows = Knowledge.objects.filter(id__in=resource_ids).values('id', 'workspace_id')
    else:
        return {}
    return {str(row['id']): row['workspace_id'] or 'default' for row in rows}


def _get_authorized_resource_ids(chat_user_id, resource_id_list, resource_type):
    resource_ids = [str(resource_id) for resource_id in (resource_id_list or [])]
    if not chat_user_id or not resource_ids:
        return []
    workspace_map = _get_resource_workspace_ids(resource_ids, resource_type)
    if not workspace_map:
        return []
    workspace_ids = set(workspace_map.values())
    relation_group_ids = list(
        UserGroupRelation.objects.filter(user_id=chat_user_id).values_list('group_id', flat=True)
    )
    explicit_query = ResourceChatUserAuthorize.objects.filter(
        user_id=chat_user_id,
        resource_type=resource_type,
        resource_id__in=resource_ids,
        workspace_id__in=workspace_ids,
    )
    if not relation_group_ids:
        return []
    explicit_query = explicit_query.filter(user_group_id__in=relation_group_ids)

    explicitly_allowed_ids = set(
        str(resource_id)
        for resource_id in explicit_query.filter(is_auth=True).values_list('resource_id', flat=True)
    )
    explicitly_denied_ids = set(
        str(resource_id)
        for resource_id in explicit_query.filter(is_auth=False).values_list('resource_id', flat=True)
    )
    group_auth_rows = ResourceChatUserGroupAuthorize.objects.filter(
        user_group_id__in=relation_group_ids,
        resource_type=resource_type,
        resource_id__in=resource_ids,
        workspace_id__in=workspace_ids,
        is_auth=True,
    )
    group_authorized_ids = {str(row.resource_id) for row in group_auth_rows}
    return [
        resource_id
        for resource_id in resource_ids
        if (resource_id in explicitly_allowed_ids
            or (resource_id in group_authorized_ids and resource_id not in explicitly_denied_ids))
    ]
