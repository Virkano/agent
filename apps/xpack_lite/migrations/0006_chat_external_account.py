import uuid_utils.compat as uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('system_manage', '0001_initial'),
        ('xpack_lite', '0005_shared_resource_workspace_authorization'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatExternalAccount',
            fields=[
                ('id', models.CharField(default=uuid.uuid7, editable=False, max_length=128, primary_key=True, serialize=False)),
                ('platform', models.CharField(db_index=True, max_length=64)),
                ('external_id', models.CharField(db_index=True, max_length=150)),
                ('union_id', models.CharField(blank=True, db_index=True, default='', max_length=150)),
                ('open_id', models.CharField(blank=True, db_index=True, default='', max_length=150)),
                ('profile', models.JSONField(default=dict)),
                ('create_time', models.DateTimeField(auto_now_add=True, db_index=True, null=True)),
                ('update_time', models.DateTimeField(auto_now=True, null=True)),
                ('chat_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='external_accounts', to='system_manage.chatuser')),
            ],
            options={
                'db_table': 'chat_external_account',
                'unique_together': {('platform', 'external_id')},
            },
        ),
    ]
