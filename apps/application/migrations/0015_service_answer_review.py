import uuid_utils.compat as uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("application", "0014_applicationversion_knowledge_ids")]

    operations = [
        migrations.CreateModel(
            name="ServiceAnswerReview",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid7, editable=False, primary_key=True, serialize=False)),
                ("workspace_id", models.CharField(db_index=True, max_length=128)),
                ("status", models.CharField(choices=[("PENDING", "待复核"), ("CONFIRMED", "确认问题"), ("DISMISSED", "排除问题")], default="PENDING", max_length=16)),
                ("risk_types", models.JSONField(default=list)),
                ("delivery_action", models.CharField(max_length=32)),
                ("reference_count", models.PositiveIntegerField(default=0)),
                ("rule_version", models.CharField(max_length=64)),
                ("revision", models.PositiveIntegerField(default=0)),
                ("create_time", models.DateTimeField(auto_now_add=True)),
                ("update_time", models.DateTimeField(auto_now=True)),
                ("record", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="service_answer_review", to="application.chatrecord")),
            ],
            options={"db_table": "service_answer_review"},
        ),
        migrations.CreateModel(
            name="ServiceAnswerReviewAction",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid7, editable=False, primary_key=True, serialize=False)),
                ("revision", models.PositiveIntegerField()),
                ("previous_status", models.CharField(max_length=16)),
                ("current_status", models.CharField(max_length=16)),
                ("reviewer_id", models.CharField(max_length=128)),
                ("reviewer_name", models.CharField(max_length=128)),
                ("note", models.TextField()),
                ("create_time", models.DateTimeField(auto_now_add=True)),
                ("review", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="actions", to="application.serviceanswerreview")),
            ],
            options={"db_table": "service_answer_review_action"},
        ),
        migrations.AddIndex(
            model_name="serviceanswerreview",
            index=models.Index(fields=["workspace_id", "status", "create_time"], name="service_review_queue"),
        ),
        migrations.AddConstraint(
            model_name="serviceanswerreviewaction",
            constraint=models.UniqueConstraint(fields=("review", "revision"), name="service_review_action_revision"),
        ),
    ]
