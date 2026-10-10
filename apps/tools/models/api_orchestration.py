import uuid_utils.compat as uuid
from django.db import models

from common.mixins.app_model_mixin import AppModelMixin
from users.models import User


class ApiAssetAuthScheme(models.TextChoices):
    NONE = "NONE", "无需鉴权"
    API_KEY = "API_KEY", "API Key"
    JWT = "JWT", "JWT"
    OAUTH2 = "OAUTH2", "OAuth2"
    SIGNATURE = "SIGNATURE", "签名"


class ApiAssetEnvironment(models.TextChoices):
    TEST = "TEST", "测试"
    GRAY = "GRAY", "灰度"
    PRODUCTION = "PRODUCTION", "生产"


class ApiVersionStatus(models.TextChoices):
    DRAFT = "DRAFT", "草稿"
    PUBLISHED = "PUBLISHED", "已发布"
    ARCHIVED = "ARCHIVED", "已归档"


class ApiInvocationStatus(models.TextChoices):
    SUCCESS = "SUCCESS", "调用成功"
    AUTH_FAILED = "AUTH_FAILED", "鉴权失败"
    SCHEMA_FAILED = "SCHEMA_FAILED", "Schema 校验失败"
    RESPONSE_FAILED = "RESPONSE_FAILED", "返回校验失败"
    TIMEOUT = "TIMEOUT", "调用超时"
    RETRY_EXHAUSTED = "RETRY_EXHAUSTED", "重试耗尽"
    CIRCUIT_OPEN = "CIRCUIT_OPEN", "熔断拒绝"


class ApiCircuitState(models.TextChoices):
    CLOSED = "CLOSED", "已关闭"
    OPEN = "OPEN", "已打开"


class ApiAdapterMode(models.TextChoices):
    MOCK = "MOCK", "晓搭 Mock"
    GATEWAY = "GATEWAY", "晓搭网关"


class ApiOrchestrationAsset(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    asset_key = models.CharField(max_length=64)
    name = models.CharField(max_length=160)
    description = models.CharField(max_length=512, blank=True, default="")
    icon = models.CharField(max_length=64, blank=True, default="Connection")
    auth_scheme = models.CharField(
        max_length=20,
        choices=ApiAssetAuthScheme.choices,
        default=ApiAssetAuthScheme.API_KEY,
    )
    auth_reference = models.CharField(max_length=160, blank=True, default="")
    ip_allowlist = models.JSONField(default=list)
    enabled = models.BooleanField(default=False, db_index=True)
    published_version_no = models.PositiveIntegerField(null=True, blank=True)
    circuit_state = models.CharField(
        max_length=16,
        choices=ApiCircuitState.choices,
        default=ApiCircuitState.CLOSED,
        db_index=True,
    )
    consecutive_failures = models.PositiveIntegerField(default=0)
    circuit_opened_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_constraint=False)

    class Meta:
        db_table = "api_orchestration_asset"
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "asset_key"], name="uniq_api_asset_workspace_key"
            )
        ]
        ordering = ["asset_key"]


class ApiOrchestrationVersion(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    asset = models.ForeignKey(
        ApiOrchestrationAsset,
        on_delete=models.CASCADE,
        related_name="versions",
    )
    version_no = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=ApiVersionStatus.choices,
        default=ApiVersionStatus.DRAFT,
        db_index=True,
    )
    environment = models.CharField(
        max_length=20,
        choices=ApiAssetEnvironment.choices,
        default=ApiAssetEnvironment.TEST,
    )
    protocol = models.CharField(max_length=32, default="XIADA_MOCK")
    method = models.CharField(max_length=12, default="POST")
    endpoint_path = models.CharField(max_length=256)
    input_schema = models.JSONField(default=dict)
    output_schema = models.JSONField(default=dict)
    request_mapping = models.JSONField(default=dict)
    response_mapping = models.JSONField(default=dict)
    openapi_snapshot = models.JSONField(default=dict)
    parameter_bindings = models.JSONField(default=list)
    adapter_mode = models.CharField(
        max_length=16,
        choices=ApiAdapterMode.choices,
        default=ApiAdapterMode.MOCK,
    )
    gateway_base_url = models.CharField(max_length=512, blank=True, default="")
    required_scopes = models.JSONField(default=list)
    timeout_ms = models.PositiveIntegerField(default=3000)
    max_retries = models.PositiveSmallIntegerField(default=2)
    circuit_failure_threshold = models.PositiveSmallIntegerField(default=3)
    circuit_recovery_seconds = models.PositiveIntegerField(default=60)
    mock_response = models.JSONField(default=dict)
    config_snapshot = models.JSONField(default=dict)
    published_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_constraint=False)

    class Meta:
        db_table = "api_orchestration_version"
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "asset", "version_no"],
                name="uniq_api_asset_version",
            )
        ]
        ordering = ["-version_no"]


class ApiInvocationAudit(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    asset = models.ForeignKey(ApiOrchestrationAsset, on_delete=models.CASCADE)
    version = models.ForeignKey(ApiOrchestrationVersion, on_delete=models.PROTECT)
    request_id = models.CharField(max_length=128)
    status = models.CharField(max_length=24, choices=ApiInvocationStatus.choices, db_index=True)
    auth_scheme = models.CharField(max_length=20, choices=ApiAssetAuthScheme.choices)
    auth_result = models.BooleanField(default=False)
    schema_result = models.BooleanField(default=False)
    request_snapshot = models.JSONField(default=dict)
    response_snapshot = models.JSONField(default=dict)
    error_message = models.CharField(max_length=512, blank=True, default="")
    duration_ms = models.PositiveIntegerField(default=0)
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_constraint=False)

    class Meta:
        db_table = "api_invocation_audit"
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "request_id"], name="uniq_api_invocation_request"
            )
        ]
        ordering = ["-create_time"]


class ApiGovernanceEvent(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    workspace_id = models.CharField(max_length=64, default="default", db_index=True)
    asset = models.ForeignKey(
        ApiOrchestrationAsset,
        on_delete=models.CASCADE,
        related_name="governance_events",
    )
    version = models.ForeignKey(
        ApiOrchestrationVersion,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    event_type = models.CharField(max_length=40, db_index=True)
    event_snapshot = models.JSONField(default=dict)
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_constraint=False)

    class Meta:
        db_table = "api_governance_event"
        ordering = ["-create_time"]
