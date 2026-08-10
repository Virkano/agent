import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xpack_lite', '0004_system_api_key'),
    ]

    operations = [
        migrations.CreateModel(
            name='SharedResourceWorkspaceAuthorization',
            fields=[
                ('id', models.CharField(max_length=128, primary_key=True, serialize=False)),
                ('resource_type', models.CharField(db_index=True, max_length=32)),
                ('authentication_type', models.CharField(default='WHITE_LIST', max_length=32)),
                ('workspace_id_list', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=128), default=list, size=None)),
                ('create_time', models.DateTimeField(auto_now_add=True, db_index=True, null=True)),
                ('update_time', models.DateTimeField(auto_now=True, null=True)),
            ],
            options={
                'db_table': 'shared_resource_workspace_authorization',
            },
        ),
    ]
