from django.db import migrations


DINGTALK_USER_GROUP_ID = 'dingtalk'
DINGTALK_USER_GROUP_NAME = '钉钉用户组'
APPLICATION_RESOURCE_TYPE = 'APPLICATION'
KNOWLEDGE_RESOURCE_TYPE = 'KNOWLEDGE'


def seed_dingtalk_knowledge_authorization(apps, schema_editor):
    UserGroup = apps.get_model('system_manage', 'UserGroup')
    ResourceChatUserGroupAuthorize = apps.get_model('system_manage', 'ResourceChatUserGroupAuthorize')
    ResourceMapping = apps.get_model('system_manage', 'ResourceMapping')
    Application = apps.get_model('application', 'Application')
    Knowledge = apps.get_model('knowledge', 'Knowledge')

    group, _ = UserGroup.objects.get_or_create(
        id=DINGTALK_USER_GROUP_ID,
        defaults={'name': DINGTALK_USER_GROUP_NAME},
    )
    app_workspace_map = {
        str(row.id): row.workspace_id
        for row in Application.objects.only('id', 'workspace_id')
    }
    knowledge_workspace_map = {
        str(row.id): row.workspace_id
        for row in Knowledge.objects.only('id', 'workspace_id')
    }

    mappings = ResourceMapping.objects.filter(
        source_type=APPLICATION_RESOURCE_TYPE,
        target_type=KNOWLEDGE_RESOURCE_TYPE,
    ).values_list('source_id', 'target_id')
    for application_id, knowledge_id in mappings.iterator():
        ResourceChatUserGroupAuthorize.objects.update_or_create(
            user_group=group,
            resource_id=knowledge_id,
            resource_type=KNOWLEDGE_RESOURCE_TYPE,
            defaults={
                'workspace_id': knowledge_workspace_map.get(str(knowledge_id))
                or app_workspace_map.get(str(application_id))
                or 'default',
                'is_auth': True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('xpack_lite', '0007_seed_dingtalk_chat_user_group'),
    ]

    operations = [
        migrations.RunPython(seed_dingtalk_knowledge_authorization, migrations.RunPython.noop),
    ]
