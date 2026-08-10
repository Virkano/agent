from django.db import migrations, models


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


def seed_platform_display_setting(apps, schema_editor):
    PlatformDisplaySetting = apps.get_model('xpack_lite', 'PlatformDisplaySetting')
    PlatformDisplaySetting.objects.get_or_create(id='default', defaults={'meta': DEFAULT_DISPLAY_SETTING})


class Migration(migrations.Migration):

    dependencies = [
        ('xpack_lite', '0002_chat_auth_runtime'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlatformDisplaySetting',
            fields=[
                ('id', models.CharField(default='default', editable=False, max_length=64, primary_key=True, serialize=False)),
                ('meta', models.JSONField(default=dict)),
                ('create_time', models.DateTimeField(auto_now_add=True, db_index=True, null=True)),
                ('update_time', models.DateTimeField(auto_now=True, null=True)),
            ],
            options={'db_table': 'platform_display_setting'},
        ),
        migrations.RunPython(seed_platform_display_setting, migrations.RunPython.noop),
    ]
