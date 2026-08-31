# Generated for Telecom AI Agent branding.

from django.db import migrations


DEFAULT_EMBEDDING_MODEL_ID = '42f63a3d-427e-11ef-b3ec-a8a1595801ab'


def rename_default_embedding_model(apps, schema_editor):
    Model = apps.get_model('models_provider', 'Model')
    Model.objects.filter(
        id=DEFAULT_EMBEDDING_MODEL_ID,
        name='telecom_ai_agent-embedding',
        model_name='telecom_ai_agent-local-hash-embedding',
    ).update(name='telecom-ai-embedding', model_name='telecom-ai-local-hash-embedding')


def restore_default_embedding_model(apps, schema_editor):
    Model = apps.get_model('models_provider', 'Model')
    Model.objects.filter(
        id=DEFAULT_EMBEDDING_MODEL_ID,
        name='telecom-ai-embedding',
        model_name='telecom-ai-local-hash-embedding',
    ).update(name='telecom_ai_agent-embedding', model_name='telecom_ai_agent-local-hash-embedding')


class Migration(migrations.Migration):
    dependencies = [
        ('models_provider', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(rename_default_embedding_model, restore_default_embedding_model),
    ]
