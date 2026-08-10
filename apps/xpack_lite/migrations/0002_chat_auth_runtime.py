import uuid_utils.compat as uuid
from django.db import migrations, models
import django.db.models.deletion


def seed_chat_runtime(apps, schema_editor):
    Application = apps.get_model('application', 'Application')
    ApplicationSetting = apps.get_model('xpack_lite', 'ApplicationSetting')
    ChatPlatform = apps.get_model('xpack_lite', 'ChatPlatform')
    UserGroup = apps.get_model('system_manage', 'UserGroup')

    UserGroup.objects.get_or_create(id='default', defaults={'name': '默认用户组'})
    ChatPlatform.objects.update_or_create(
        auth_type='LOCAL',
        defaults={'name': '本地账号', 'is_active': True, 'is_valid': True, 'config': {}},
    )
    for application in Application.objects.all():
        ApplicationSetting.objects.get_or_create(application_id=application.id, defaults={'id': str(uuid.uuid7())})


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0001_initial'),
        ('system_manage', '0001_initial'),
        ('xpack_lite', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatPlatform',
            fields=[
                ('id', models.CharField(default=uuid.uuid7, editable=False, max_length=128, primary_key=True, serialize=False)),
                ('auth_type', models.CharField(db_index=True, max_length=64, unique=True)),
                ('name', models.CharField(max_length=150)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('is_valid', models.BooleanField(db_index=True, default=True)),
                ('config', models.JSONField(default=dict)),
            ],
            options={'db_table': 'chat_platform'},
        ),
        migrations.CreateModel(
            name='ApplicationSetting',
            fields=[
                ('id', models.CharField(default=uuid.uuid7, editable=False, max_length=128, primary_key=True, serialize=False)),
                ('show_history', models.BooleanField(default=True)),
                ('draggable', models.BooleanField(default=False)),
                ('show_guide', models.BooleanField(default=True)),
                ('avatar', models.CharField(blank=True, default='', max_length=1024)),
                ('show_avatar', models.BooleanField(default=True)),
                ('float_icon', models.CharField(blank=True, default='', max_length=1024)),
                ('disclaimer', models.BooleanField(default=False)),
                ('disclaimer_value', models.TextField(blank=True, default='')),
                ('custom_theme', models.JSONField(default=dict)),
                ('user_avatar', models.CharField(blank=True, default='', max_length=1024)),
                ('show_user_avatar', models.BooleanField(default=True)),
                ('show_share', models.BooleanField(default=True)),
                ('float_location', models.JSONField(default=dict)),
                ('chat_background', models.CharField(blank=True, default='', max_length=1024)),
                ('application', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='local_xpack_setting', to='application.application')),
            ],
            options={'db_table': 'application_setting'},
        ),
        migrations.RunPython(seed_chat_runtime, migrations.RunPython.noop),
    ]
