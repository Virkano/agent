from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("marketing", "0005_marketingtouchbatch_execution")]
    operations = [
        migrations.AddField(
            model_name="marketingtouchbatch",
            name="approval_status",
            field=models.CharField(
                choices=[("PENDING", "待审批"), ("APPROVED", "已通过"), ("REJECTED", "已驳回")],
                db_index=True,
                default="APPROVED",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="marketingtouchbatch", name="approval_note", field=models.TextField(blank=True, default="")
        ),
        migrations.AddField(
            model_name="marketingtouchbatch",
            name="approver_name",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="marketingtouchbatch", name="approved_at", field=models.DateTimeField(blank=True, null=True)
        ),
    ]
