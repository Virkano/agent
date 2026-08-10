import uuid_utils.compat as uuid
from django.db import migrations, models
import django.db.models.deletion


def seed_defaults(apps, schema_editor):
    User = apps.get_model('users', 'User')
    Workspace = apps.get_model('xpack_lite', 'Workspace')
    RoleSetting = apps.get_model('xpack_lite', 'RoleSetting')
    WorkspaceUserRoleMapping = apps.get_model('xpack_lite', 'WorkspaceUserRoleMapping')

    admin_user = User.objects.filter(username='admin').first()
    Workspace.objects.get_or_create(
        id='default',
        defaults={'name': '默认空间', 'create_user_id': admin_user.id if admin_user else None},
    )
    roles = [
        ('ADMIN', '系统管理员', 'ADMIN'),
        ('WORKSPACE_MANAGE', '工作空间管理员', 'WORKSPACE_MANAGE'),
        ('USER', '普通用户', 'USER'),
    ]
    for role_id, role_name, role_type in roles:
        RoleSetting.objects.get_or_create(
            id=role_id,
            defaults={
                'role_name': role_name,
                'type': role_type,
                'internal': True,
                'create_user_id': admin_user.id if admin_user else None,
            },
        )
    if admin_user:
        for role_id in ['ADMIN', 'WORKSPACE_MANAGE', 'USER']:
            WorkspaceUserRoleMapping.objects.get_or_create(
                workspace_id='default',
                role_id=role_id,
                user_id=admin_user.id,
                defaults={'id': uuid.uuid7()},
            )


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
        ('system_manage', '0005_resourcemapping'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatAuthSetting',
            fields=[
                ('auth_type', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=64)),
                ('enabled', models.BooleanField(default=False)),
                ('config', models.JSONField(default=dict)),
                ('create_time', models.DateTimeField(auto_now_add=True, db_index=True, null=True)),
                ('update_time', models.DateTimeField(auto_now=True, null=True)),
            ],
            options={'db_table': 'chat_auth_setting'},
        ),
        migrations.CreateModel(
            name='Workspace',
            fields=[
                ('id', models.CharField(default=uuid.uuid7, editable=False, max_length=128, primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=64, unique=True)),
                ('create_time', models.DateTimeField(auto_now_add=True, db_index=True, null=True)),
                ('update_time', models.DateTimeField(auto_now=True, null=True)),
                ('create_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='users.user')),
            ],
            options={'db_table': 'workspace'},
        ),
        migrations.CreateModel(
            name='RoleSetting',
            fields=[
                ('id', models.CharField(max_length=128, primary_key=True, serialize=False)),
                ('role_name', models.CharField(db_index=True, max_length=64)),
                ('type', models.CharField(db_index=True, max_length=64)),
                ('internal', models.BooleanField(db_index=True, default=False)),
                ('create_time', models.DateTimeField(auto_now_add=True, db_index=True, null=True)),
                ('update_time', models.DateTimeField(auto_now=True, null=True)),
                ('create_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='users.user')),
            ],
            options={'db_table': 'role_setting'},
        ),
        migrations.CreateModel(
            name='RolePermissionMapping',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid7, editable=False, max_length=128, primary_key=True, serialize=False)),
                ('permission_id', models.CharField(db_index=True, max_length=256)),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='permission_mappings', to='xpack_lite.rolesetting')),
            ],
            options={'db_table': 'role_permission', 'unique_together': {('role', 'permission_id')}},
        ),
        migrations.CreateModel(
            name='WorkspaceUserRoleMapping',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid7, editable=False, max_length=128, primary_key=True, serialize=False)),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='userrolerelation', related_query_name='userrolerelation', to='xpack_lite.rolesetting')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
                ('workspace', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='xpack_lite.workspace')),
            ],
            options={'db_table': 'user_role_relation', 'unique_together': {('workspace', 'role', 'user')}},
        ),
        migrations.RunPython(seed_defaults, migrations.RunPython.noop),
    ]
