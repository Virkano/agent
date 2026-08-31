import uuid_utils.compat as uuid
from django.db import migrations


DINGTALK_USER_GROUP_ID = 'dingtalk'
DINGTALK_USER_GROUP_NAME = '钉钉用户组'
APPLICATION_RESOURCE_TYPE = 'APPLICATION'


def seed_dingtalk_chat_user_group(apps, schema_editor):
    ChatUser = apps.get_model('system_manage', 'ChatUser')
    UserGroup = apps.get_model('system_manage', 'UserGroup')
    UserGroupRelation = apps.get_model('system_manage', 'UserGroupRelation')
    ResourceChatUserGroupAuthorize = apps.get_model('system_manage', 'ResourceChatUserGroupAuthorize')
    ChatExternalAccount = apps.get_model('xpack_lite', 'ChatExternalAccount')
    Application = apps.get_model('application', 'Application')

    group, _ = UserGroup.objects.get_or_create(
        id=DINGTALK_USER_GROUP_ID,
        defaults={'name': DINGTALK_USER_GROUP_NAME},
    )

    dingtalk_user_ids = set(
        str(user_id)
        for user_id in ChatExternalAccount.objects.filter(platform='dingtalk').values_list('chat_user_id', flat=True)
    )
    dingtalk_user_ids.update(
        str(user_id)
        for user_id in ChatUser.objects.filter(source='dingtalk').values_list('id', flat=True)
    )
    for user_id in dingtalk_user_ids:
        UserGroupRelation.objects.get_or_create(
            user_id=user_id,
            group=group,
            defaults={'id': uuid.uuid7()},
        )

    for application in Application.objects.all().iterator():
        ResourceChatUserGroupAuthorize.objects.update_or_create(
            user_group=group,
            resource_id=application.id,
            resource_type=APPLICATION_RESOURCE_TYPE,
            defaults={'workspace_id': application.workspace_id or 'default', 'is_auth': True},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0014_applicationversion_knowledge_ids'),
        ('xpack_lite', '0006_chat_external_account'),
    ]

    operations = [
        migrations.RunPython(seed_dingtalk_chat_user_group, migrations.RunPython.noop),
    ]
