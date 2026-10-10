import uuid_utils.compat as uuid
from django.db import models

from common.mixins.app_model_mixin import AppModelMixin


class MasterDataAccessEvent(AppModelMixin):
    """Append-only application fact for direct master-data read endpoints."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, db_index=True)
    actor_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    resource_model = models.CharField(max_length=96, db_index=True)
    action = models.CharField(max_length=16)
    outcome = models.CharField(max_length=16, db_index=True)
    route_template = models.CharField(max_length=512)
    scope_hash = models.CharField(max_length=64, blank=True, default="")
    query_keys = models.JSONField(default=list)

    class Meta:
        db_table = "master_data_access_event"
        ordering = ["-create_time"]
