import uuid_utils.compat as uuid
import django.contrib.postgres.fields
import django.db.models.deletion
from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        ('xpack_lite', '0003_platform_display_setting'),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemApiKey',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid7, editable=False, max_length=128, primary_key=True, serialize=False)),
                ('secret_key', models.CharField(db_index=True, max_length=1024, unique=True)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('allow_cross_domain', models.BooleanField(default=False)),
                ('cross_domain_list', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=128), default=list, size=None)),
                ('expire_time', models.DateTimeField(default=timezone.now)),
                ('is_permanent', models.BooleanField(default=True)),
                ('create_time', models.DateTimeField(auto_now_add=True, db_index=True, null=True)),
                ('update_time', models.DateTimeField(auto_now=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='system_api_keys', to='users.user')),
            ],
            options={
                'db_table': 'system_api_key',
            },
        ),
    ]
