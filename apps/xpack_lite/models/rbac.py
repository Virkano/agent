import uuid_utils.compat as uuid
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

from application.models import Application
from system_manage.models.chat_user import ChatUser
from users.models import User


class Workspace(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False)
    name = models.CharField(max_length=64, unique=True, db_index=True)
    create_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    create_time = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
    update_time = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        db_table = 'workspace'


class RoleSetting(models.Model):
    id = models.CharField(primary_key=True, max_length=128)
    role_name = models.CharField(max_length=64, db_index=True)
    type = models.CharField(max_length=64, db_index=True)
    internal = models.BooleanField(default=False, db_index=True)
    create_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    create_time = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
    update_time = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        db_table = 'role_setting'


class RolePermissionMapping(models.Model):
    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False)
    role = models.ForeignKey(RoleSetting, on_delete=models.CASCADE, related_name='permission_mappings')
    permission_id = models.CharField(max_length=256, db_index=True)

    class Meta:
        db_table = 'role_permission'
        unique_together = ('role', 'permission_id')


class WorkspaceUserRoleMapping(models.Model):
    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    role = models.ForeignKey(
        RoleSetting,
        on_delete=models.CASCADE,
        related_name='userrolerelation',
        related_query_name='userrolerelation',
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = 'user_role_relation'
        unique_together = ('workspace', 'role', 'user')


class ChatAuthSetting(models.Model):
    auth_type = models.CharField(primary_key=True, max_length=64)
    name = models.CharField(max_length=64)
    enabled = models.BooleanField(default=False)
    config = models.JSONField(default=dict)
    create_time = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
    update_time = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        db_table = 'chat_auth_setting'


class ChatPlatform(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False)
    auth_type = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True, db_index=True)
    is_valid = models.BooleanField(default=True, db_index=True)
    config = models.JSONField(default=dict)

    class Meta:
        db_table = 'chat_platform'


class ChatExternalAccount(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False)
    chat_user = models.ForeignKey(ChatUser, on_delete=models.CASCADE, related_name='external_accounts')
    platform = models.CharField(max_length=64, db_index=True)
    external_id = models.CharField(max_length=150, db_index=True)
    union_id = models.CharField(max_length=150, default='', blank=True, db_index=True)
    open_id = models.CharField(max_length=150, default='', blank=True, db_index=True)
    profile = models.JSONField(default=dict)
    create_time = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
    update_time = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        db_table = 'chat_external_account'
        unique_together = ('platform', 'external_id')


class ApplicationSetting(models.Model):
    id = models.CharField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False)
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='local_xpack_setting')
    show_history = models.BooleanField(default=True)
    draggable = models.BooleanField(default=False)
    show_guide = models.BooleanField(default=True)
    avatar = models.CharField(max_length=1024, default='', blank=True)
    show_avatar = models.BooleanField(default=True)
    float_icon = models.CharField(max_length=1024, default='', blank=True)
    disclaimer = models.BooleanField(default=False)
    disclaimer_value = models.TextField(default='', blank=True)
    custom_theme = models.JSONField(default=dict)
    user_avatar = models.CharField(max_length=1024, default='', blank=True)
    show_user_avatar = models.BooleanField(default=True)
    show_share = models.BooleanField(default=True)
    float_location = models.JSONField(default=dict)
    chat_background = models.CharField(max_length=1024, default='', blank=True)

    class Meta:
        db_table = 'application_setting'


class PlatformDisplaySetting(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default='default', editable=False)
    meta = models.JSONField(default=dict)
    create_time = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
    update_time = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        db_table = 'platform_display_setting'


class SystemApiKey(models.Model):
    id = models.UUIDField(primary_key=True, max_length=128, default=uuid.uuid7, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='system_api_keys')
    secret_key = models.CharField(max_length=1024, unique=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    allow_cross_domain = models.BooleanField(default=False)
    cross_domain_list = ArrayField(
        base_field=models.CharField(max_length=128, blank=True),
        default=list,
    )
    expire_time = models.DateTimeField(default=timezone.now)
    is_permanent = models.BooleanField(default=True)
    create_time = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
    update_time = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        db_table = 'system_api_key'


class SharedResourceWorkspaceAuthorization(models.Model):
    id = models.CharField(primary_key=True, max_length=128)
    resource_type = models.CharField(max_length=32, db_index=True)
    authentication_type = models.CharField(max_length=32, default='WHITE_LIST')
    workspace_id_list = ArrayField(
        base_field=models.CharField(max_length=128, blank=True),
        default=list,
    )
    create_time = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
    update_time = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        db_table = 'shared_resource_workspace_authorization'
