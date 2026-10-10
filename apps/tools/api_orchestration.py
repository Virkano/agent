import copy
import time
from datetime import datetime

import uuid_utils.compat as uuid
from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from rest_framework import serializers

from common.exception.app_exception import AppApiException
from tools.models import (
    ApiAssetAuthScheme,
    ApiAssetEnvironment,
    ApiAdapterMode,
    ApiCircuitState,
    ApiGovernanceEvent,
    ApiInvocationAudit,
    ApiInvocationStatus,
    ApiOrchestrationAsset,
    ApiOrchestrationVersion,
    ApiVersionStatus,
)


class ApiAssetWriteSerializer(serializers.Serializer):
    asset_key = serializers.RegexField(r"^[a-z][a-z0-9_]{2,63}$")
    name = serializers.CharField(max_length=160)
    description = serializers.CharField(required=False, allow_blank=True, default="", max_length=512)
    icon = serializers.CharField(required=False, allow_blank=True, default="Connection", max_length=64)
    auth_scheme = serializers.ChoiceField(choices=ApiAssetAuthScheme.choices, default=ApiAssetAuthScheme.API_KEY)
    auth_reference = serializers.CharField(required=False, allow_blank=True, default="", max_length=160)
    ip_allowlist = serializers.ListField(child=serializers.IPAddressField(), required=False, default=list)
    environment = serializers.ChoiceField(choices=ApiAssetEnvironment.choices, default=ApiAssetEnvironment.TEST)
    method = serializers.ChoiceField(choices=("GET", "POST", "PUT", "PATCH", "DELETE"), default="POST")
    endpoint_path = serializers.CharField(max_length=256)
    input_schema = serializers.DictField()
    output_schema = serializers.DictField()
    request_mapping = serializers.DictField(required=False, default=dict)
    response_mapping = serializers.DictField(required=False, default=dict)
    openapi_snapshot = serializers.DictField(required=False, default=dict)
    parameter_bindings = serializers.ListField(
        child=serializers.DictField(), required=False, default=list
    )
    adapter_mode = serializers.ChoiceField(
        choices=ApiAdapterMode.choices, default=ApiAdapterMode.MOCK
    )
    gateway_base_url = serializers.URLField(
        required=False, allow_blank=True, default="", max_length=512
    )
    required_scopes = serializers.ListField(
        child=serializers.CharField(max_length=100), required=False, default=list
    )
    timeout_ms = serializers.IntegerField(min_value=100, max_value=120000, default=3000)
    max_retries = serializers.IntegerField(min_value=0, max_value=5, default=2)
    circuit_failure_threshold = serializers.IntegerField(min_value=1, max_value=20, default=3)
    circuit_recovery_seconds = serializers.IntegerField(min_value=1, max_value=3600, default=60)
    mock_response = serializers.DictField(required=False, default=dict)

    def validate_endpoint_path(self, value):
        if not value.startswith("/"):
            raise serializers.ValidationError("接口路径必须以 / 开头")
        return value

    def validate(self, attrs):
        for field in ("input_schema", "output_schema"):
            errors = validate_schema_definition(attrs[field])
            if errors:
                raise serializers.ValidationError({field: errors})
        binding_errors = validate_parameter_bindings(
            attrs["parameter_bindings"], attrs["input_schema"]
        )
        if binding_errors:
            raise serializers.ValidationError({"parameter_bindings": binding_errors})
        if attrs["auth_scheme"] != ApiAssetAuthScheme.NONE and not attrs["auth_reference"]:
            raise serializers.ValidationError({"auth_reference": "鉴权方式启用时必须填写凭证引用"})
        if attrs["adapter_mode"] == ApiAdapterMode.GATEWAY and not attrs["gateway_base_url"]:
            raise serializers.ValidationError({"gateway_base_url": "网关模式必须填写晓搭网关地址"})
        if (
            attrs["environment"] != ApiAssetEnvironment.TEST
            and attrs["gateway_base_url"]
            and not attrs["gateway_base_url"].startswith("https://")
        ):
            raise serializers.ValidationError({"gateway_base_url": "灰度和生产环境必须使用 HTTPS"})
        return attrs


class ApiMockInvokeSerializer(serializers.Serializer):
    request_id = serializers.CharField(required=False, allow_blank=True, max_length=128)
    payload = serializers.DictField(default=dict)
    auth_context = serializers.DictField(required=False, default=dict)
    source_context = serializers.DictField(required=False, default=dict)
    simulated_failures = serializers.IntegerField(min_value=0, max_value=10, default=0)
    simulated_latency_ms = serializers.IntegerField(min_value=0, max_value=180000, default=0)


class ApiPublishSerializer(serializers.Serializer):
    breaking_change_confirmed = serializers.BooleanField(default=False)
    change_ticket = serializers.CharField(
        required=False, allow_blank=True, default="", max_length=128
    )


class ApiEnabledSerializer(serializers.Serializer):
    enabled = serializers.BooleanField()
    reason = serializers.CharField(required=False, allow_blank=True, default="", max_length=256)


class OpenApiImportSerializer(serializers.Serializer):
    document = serializers.DictField()
    path = serializers.CharField(required=False, allow_blank=True, max_length=256)
    method = serializers.CharField(required=False, allow_blank=True, max_length=12)


PARAMETER_SOURCE_TYPES = {"REQUEST", "CONTEXT", "CONSTANT", "PREVIOUS_OUTPUT"}


def validate_parameter_bindings(bindings, input_schema):
    errors = []
    properties = input_schema.get("properties", {})
    targets = []
    for index, binding in enumerate(bindings):
        prefix = f"第 {index + 1} 项"
        target = binding.get("target")
        source_type = binding.get("source_type")
        if not isinstance(target, str) or not target:
            errors.append(f"{prefix}: target 不能为空")
            continue
        targets.append(target)
        if target not in properties:
            errors.append(f"{prefix}: target {target} 未在输入 Schema 中声明")
        if source_type not in PARAMETER_SOURCE_TYPES:
            errors.append(f"{prefix}: source_type 不受支持")
        if source_type != "CONSTANT" and not binding.get("source_path"):
            errors.append(f"{prefix}: 非常量来源必须填写 source_path")
        depends_on = binding.get("depends_on", [])
        if not isinstance(depends_on, list) or not all(
            isinstance(item, str) for item in depends_on
        ):
            errors.append(f"{prefix}: depends_on 必须是字符串数组")
    if len(targets) != len(set(targets)):
        errors.append("target 不得重复")
    target_set = set(targets)
    dependencies = {}
    for binding in bindings:
        target = binding.get("target")
        if not isinstance(target, str) or not target:
            continue
        depends_on = binding.get("depends_on", [])
        if not isinstance(depends_on, list):
            continue
        unknown = [item for item in depends_on if item not in target_set]
        if unknown:
            errors.append(f"{target}: depends_on 包含未知目标 {', '.join(unknown)}")
        if target in depends_on:
            errors.append(f"{target}: 不得依赖自身")
        dependencies[target] = [item for item in depends_on if item in target_set]
    if _has_dependency_cycle(dependencies):
        errors.append("参数依赖存在环路")
    return errors


def _has_dependency_cycle(dependencies):
    visiting = set()
    visited = set()

    def visit(node):
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(dependency) for dependency in dependencies.get(node, [])):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in dependencies)


def _read_path(source, path):
    value = source
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return False, None
        value = value[part]
    return True, value


def resolve_parameter_bindings(bindings, payload, source_context):
    if not bindings:
        return dict(payload), [], {}
    resolved = {}
    pending = {item["target"]: item for item in bindings}
    source_summary = {}
    errors = []
    while pending:
        ready = [
            item
            for item in pending.values()
            if all(dependency not in pending for dependency in item.get("depends_on", []))
        ]
        if not ready:
            errors.append("参数依赖无法解析")
            break
        for binding in ready:
            target = binding["target"]
            pending.pop(target)
            missing_dependencies = [
                dependency
                for dependency in binding.get("depends_on", [])
                if dependency not in resolved
            ]
            if missing_dependencies:
                errors.append(f"{target}: 依赖参数缺失 {', '.join(missing_dependencies)}")
                continue
            source_type = binding["source_type"]
            source_summary[target] = source_type
            if source_type == "CONSTANT":
                found, value = "source_value" in binding, binding.get("source_value")
            else:
                sources = {
                    "REQUEST": payload,
                    "CONTEXT": source_context,
                    "PREVIOUS_OUTPUT": source_context.get("previous_output", {}),
                }
                found, value = _read_path(sources[source_type], binding["source_path"])
            if found:
                resolved[target] = value
            elif binding.get("required", False):
                errors.append(f"{target}: 参数来源未提供")
    return resolved, errors, source_summary


def validate_schema_definition(schema):
    errors = []
    if schema.get("type") != "object":
        errors.append("根节点 type 必须是 object")
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        errors.append("properties 必须是对象")
        properties = {}
    required = schema.get("required", [])
    if not isinstance(required, list):
        errors.append("required 必须是数组")
    elif any(item not in properties for item in required):
        errors.append("required 字段必须在 properties 中声明")
    allowed_types = {"string", "number", "integer", "boolean", "object", "array"}
    for key, definition in properties.items():
        if not isinstance(definition, dict) or definition.get("type") not in allowed_types:
            errors.append(f"properties.{key}.type 不受支持")
    return errors


def validate_payload(schema, payload):
    errors = []
    for key in schema.get("required", []):
        if key not in payload:
            errors.append(f"{key}: 缺少必填字段")
    checks = {
        "string": lambda value: isinstance(value, str),
        "number": lambda value: isinstance(value, (int, float)) and not isinstance(value, bool),
        "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
        "boolean": lambda value: isinstance(value, bool),
        "object": lambda value: isinstance(value, dict),
        "array": lambda value: isinstance(value, list),
    }
    for key, value in payload.items():
        definition = schema.get("properties", {}).get(key)
        if definition is None:
            if schema.get("additionalProperties") is False:
                errors.append(f"{key}: 不允许的字段")
            continue
        expected_type = definition.get("type")
        if expected_type in checks and not checks[expected_type](value):
            errors.append(f"{key}: 应为 {expected_type}")
    return errors


def _resolve_openapi_schema(value, document, seen=None):
    if not isinstance(value, dict):
        return value
    seen = seen or set()
    reference = value.get("$ref")
    if reference:
        if not reference.startswith("#/") or reference in seen:
            raise AppApiException(400, f"不支持或循环的 OpenAPI 引用: {reference}")
        target = document
        for part in reference[2:].split("/"):
            if not isinstance(target, dict) or part not in target:
                raise AppApiException(400, f"OpenAPI 引用不存在: {reference}")
            target = target[part]
        return _resolve_openapi_schema(target, document, seen | {reference})
    result = {}
    for key, item in value.items():
        if key == "properties" and isinstance(item, dict):
            result[key] = {
                name: _resolve_openapi_schema(schema, document, seen)
                for name, schema in item.items()
            }
        elif key == "items":
            result[key] = _resolve_openapi_schema(item, document, seen)
        elif isinstance(item, (dict, list)):
            result[key] = copy.deepcopy(item)
        else:
            result[key] = item
    return result


def _openapi_json_schema(content, document):
    if not isinstance(content, dict):
        return None
    media = content.get("application/json") or next(iter(content.values()), None)
    if not isinstance(media, dict) or not isinstance(media.get("schema"), dict):
        return None
    return _resolve_openapi_schema(media["schema"], document)


def parse_openapi_document(data):
    serializer = OpenApiImportSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    values = serializer.validated_data
    document = values["document"]
    if not (str(document.get("openapi", "")).startswith("3.")):
        raise AppApiException(400, "仅支持 OpenAPI 3.x 文档")
    paths = document.get("paths")
    if not isinstance(paths, dict) or not paths:
        raise AppApiException(400, "OpenAPI paths 不能为空")
    requested_path = values.get("path")
    requested_method = values.get("method", "").lower()
    chosen_path = None
    chosen_method = None
    operation = None
    supported = ("get", "post", "put", "patch", "delete")
    for path, path_item in paths.items():
        if requested_path and path != requested_path:
            continue
        if not isinstance(path_item, dict):
            continue
        methods = (requested_method,) if requested_method else supported
        for method in methods:
            if method in supported and isinstance(path_item.get(method), dict):
                chosen_path, chosen_method, operation = path, method, path_item[method]
                break
        if operation is not None:
            break
    if operation is None:
        raise AppApiException(400, "未找到指定或可导入的 OpenAPI 操作")
    path_item = paths[chosen_path]
    properties = {}
    required = []
    parameters = [
        *path_item.get("parameters", []),
        *operation.get("parameters", []),
    ]
    for parameter in parameters:
        if not isinstance(parameter, dict) or not parameter.get("name"):
            continue
        name = parameter["name"]
        schema = _resolve_openapi_schema(parameter.get("schema", {"type": "string"}), document)
        properties[name] = schema
        if parameter.get("required") and name not in required:
            required.append(name)
    request_body = operation.get("requestBody", {})
    body_schema = _openapi_json_schema(request_body.get("content", {}), document)
    if body_schema:
        if body_schema.get("type") != "object":
            raise AppApiException(400, "OpenAPI 请求体根节点必须是 object")
        properties.update(body_schema.get("properties", {}))
        required.extend(item for item in body_schema.get("required", []) if item not in required)
    input_schema = {
        "type": "object",
        "required": required,
        "additionalProperties": False,
        "properties": properties,
    }
    responses = operation.get("responses", {})
    response = responses.get("200") or responses.get("201") or responses.get("default")
    output_schema = _openapi_json_schema(
        response.get("content", {}) if isinstance(response, dict) else {}, document
    )
    if output_schema is None:
        output_schema = {"type": "object", "properties": {}}
    for label, schema in (("输入", input_schema), ("输出", output_schema)):
        errors = validate_schema_definition(schema)
        if errors:
            raise AppApiException(400, f"{label} Schema 不受支持: {'；'.join(errors)}")
    bindings = [
        {
            "target": name,
            "source_type": "REQUEST",
            "source_path": name,
            "required": name in required,
            "depends_on": [],
        }
        for name in properties
    ]
    return {
        "method": chosen_method.upper(),
        "endpoint_path": chosen_path,
        "input_schema": input_schema,
        "output_schema": output_schema,
        "parameter_bindings": bindings,
        "openapi_snapshot": document,
        "summary": {
            "title": document.get("info", {}).get("title", ""),
            "version": document.get("info", {}).get("version", ""),
            "operation_id": operation.get("operationId", ""),
        },
    }


def _schema_diff(base, target):
    base_properties = base.get("properties", {})
    target_properties = target.get("properties", {})
    base_names = set(base_properties)
    target_names = set(target_properties)
    return {
        "added": sorted(target_names - base_names),
        "removed": sorted(base_names - target_names),
        "type_changed": [
            {
                "field": name,
                "from": base_properties[name].get("type"),
                "to": target_properties[name].get("type"),
            }
            for name in sorted(base_names & target_names)
            if base_properties[name].get("type") != target_properties[name].get("type")
        ],
        "required_added": sorted(
            set(target.get("required", [])) - set(base.get("required", []))
        ),
        "required_removed": sorted(
            set(base.get("required", [])) - set(target.get("required", []))
        ),
    }


def validate_invocation_auth(asset, version, auth_context):
    if version.environment != ApiAssetEnvironment.TEST and asset.ip_allowlist:
        if auth_context.get("source_ip") not in asset.ip_allowlist:
            return False, "来源 IP 不在白名单中"
    if asset.auth_scheme == ApiAssetAuthScheme.NONE:
        return True, ""
    if not auth_context.get("validated"):
        return False, "上游鉴权证明未通过"
    if auth_context.get("scheme") != asset.auth_scheme:
        return False, "鉴权方式与接口配置不一致"
    if version.environment != ApiAssetEnvironment.TEST:
        if auth_context.get("credential_reference") != asset.auth_reference:
            return False, "凭证引用与接口配置不一致"
    if asset.auth_scheme in (ApiAssetAuthScheme.JWT, ApiAssetAuthScheme.OAUTH2):
        expires_at = auth_context.get("expires_at")
        if version.environment != ApiAssetEnvironment.TEST and expires_at is None:
            return False, "令牌缺少有效期证明"
        if expires_at is not None:
            try:
                if isinstance(expires_at, (int, float)):
                    expired = expires_at <= timezone.now().timestamp()
                else:
                    parsed = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
                    expired = parsed.timestamp() <= timezone.now().timestamp()
            except (TypeError, ValueError):
                return False, "令牌有效期格式无效"
            if expired:
                return False, "令牌已过期"
        missing_scopes = set(version.required_scopes) - set(auth_context.get("scopes", []))
        if missing_scopes:
            return False, f"令牌缺少权限: {', '.join(sorted(missing_scopes))}"
    if asset.auth_scheme == ApiAssetAuthScheme.SIGNATURE:
        if not auth_context.get("signature_valid"):
            return False, "签名校验未通过"
        if not auth_context.get("timestamp_valid"):
            return False, "签名时间窗校验未通过"
        if auth_context.get("nonce_replayed"):
            return False, "签名随机数已被使用"
    return True, ""


def serialize_version(row):
    return {
        "id": str(row.id),
        "version_no": row.version_no,
        "status": row.status,
        "status_label": row.get_status_display(),
        "environment": row.environment,
        "environment_label": row.get_environment_display(),
        "protocol": row.protocol,
        "method": row.method,
        "endpoint_path": row.endpoint_path,
        "input_schema": row.input_schema,
        "output_schema": row.output_schema,
        "request_mapping": row.request_mapping,
        "response_mapping": row.response_mapping,
        "openapi_snapshot": row.openapi_snapshot,
        "parameter_bindings": row.parameter_bindings,
        "adapter_mode": row.adapter_mode,
        "adapter_mode_label": row.get_adapter_mode_display(),
        "gateway_base_url": row.gateway_base_url,
        "required_scopes": row.required_scopes,
        "timeout_ms": row.timeout_ms,
        "max_retries": row.max_retries,
        "circuit_failure_threshold": row.circuit_failure_threshold,
        "circuit_recovery_seconds": row.circuit_recovery_seconds,
        "mock_response": row.mock_response,
        "published_at": row.published_at,
        "create_time": row.create_time,
    }


def serialize_asset(row, include_versions=False):
    payload = {
        "id": str(row.id),
        "asset_key": row.asset_key,
        "name": row.name,
        "description": row.description,
        "icon": row.icon,
        "auth_scheme": row.auth_scheme,
        "auth_scheme_label": row.get_auth_scheme_display(),
        "auth_reference": row.auth_reference,
        "ip_allowlist": row.ip_allowlist,
        "enabled": row.enabled,
        "published_version_no": row.published_version_no,
        "circuit_state": row.circuit_state,
        "circuit_state_label": row.get_circuit_state_display(),
        "consecutive_failures": row.consecutive_failures,
        "circuit_opened_at": row.circuit_opened_at,
        "version_count": getattr(row, "version_count", row.versions.count()),
        "update_time": row.update_time,
    }
    if include_versions:
        payload["versions"] = [serialize_version(version) for version in row.versions.all()]
        payload["governance_events"] = [
            serialize_governance_event(event)
            for event in row.governance_events.select_related("version", "operator")[:50]
        ]
    return payload


def serialize_governance_event(row):
    return {
        "id": str(row.id),
        "event_type": row.event_type,
        "version_no": row.version.version_no if row.version else None,
        "event_snapshot": row.event_snapshot,
        "operator_name": (
            row.operator.nick_name or row.operator.username if row.operator else "系统"
        ),
        "create_time": row.create_time,
    }


def serialize_audit(row):
    return {
        "id": str(row.id),
        "asset_id": str(row.asset_id),
        "asset_name": row.asset.name,
        "version_no": row.version.version_no,
        "request_id": row.request_id,
        "status": row.status,
        "status_label": row.get_status_display(),
        "auth_scheme": row.auth_scheme,
        "auth_result": row.auth_result,
        "schema_result": row.schema_result,
        "request_snapshot": row.request_snapshot,
        "response_snapshot": row.response_snapshot,
        "error_message": row.error_message,
        "duration_ms": row.duration_ms,
        "operator_name": (
            row.operator.nick_name or row.operator.username if row.operator else "系统"
        ),
        "create_time": row.create_time,
    }


class ApiOrchestrationService:
    def __init__(self, workspace_id, user):
        self.workspace_id = workspace_id
        self.user = user

    def _assets(self):
        return ApiOrchestrationAsset.objects.filter(workspace_id=self.workspace_id)

    def _asset(self, asset_id):
        row = self._assets().filter(id=asset_id).first()
        if row is None:
            raise AppApiException(404, "接口资产不存在")
        return row

    def dashboard(self):
        assets = self._assets().annotate(version_count=Count("versions"))
        audits = ApiInvocationAudit.objects.filter(workspace_id=self.workspace_id).select_related(
            "asset", "version", "operator"
        )
        status_counts = {item["status"]: item["count"] for item in audits.values("status").annotate(count=Count("id"))}
        return {
            "summary": {
                "asset_count": assets.count(),
                "published_count": assets.filter(enabled=True, published_version_no__isnull=False).count(),
                "version_count": ApiOrchestrationVersion.objects.filter(workspace_id=self.workspace_id).count(),
                "invocation_count": audits.count(),
                "success_count": status_counts.get(ApiInvocationStatus.SUCCESS, 0),
                "failure_count": audits.exclude(status=ApiInvocationStatus.SUCCESS).count(),
                "circuit_open_count": assets.filter(
                    circuit_state=ApiCircuitState.OPEN
                ).count(),
            },
            "assets": [serialize_asset(row) for row in assets],
            "recent_audits": [serialize_audit(row) for row in audits[:30]],
        }

    @transaction.atomic
    def save_asset(self, data, asset_id=None):
        serializer = ApiAssetWriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        if asset_id:
            asset = ApiOrchestrationAsset.objects.select_for_update().filter(
                workspace_id=self.workspace_id, id=asset_id
            ).first()
            if asset is None:
                raise AppApiException(404, "接口资产不存在")
            if self._assets().exclude(id=asset.id).filter(asset_key=values["asset_key"]).exists():
                raise AppApiException(400, "接口标识已存在")
        else:
            if self._assets().filter(asset_key=values["asset_key"]).exists():
                raise AppApiException(400, "接口标识已存在")
            asset = ApiOrchestrationAsset(workspace_id=self.workspace_id, created_by=self.user)
        for field in ("asset_key", "name", "description", "icon", "auth_scheme", "auth_reference", "ip_allowlist"):
            setattr(asset, field, values[field])
        asset.save()
        version_no = (
            ApiOrchestrationVersion.objects.filter(workspace_id=self.workspace_id, asset=asset)
            .aggregate(value=Count("id"))["value"]
            + 1
        )
        snapshot = {
            key: values[key]
            for key in (
                "environment", "method", "endpoint_path", "input_schema", "output_schema",
                "request_mapping", "response_mapping", "openapi_snapshot",
                "parameter_bindings", "adapter_mode", "gateway_base_url",
                "required_scopes", "timeout_ms", "max_retries",
                "circuit_failure_threshold", "circuit_recovery_seconds", "mock_response",
            )
        }
        version = ApiOrchestrationVersion.objects.create(
            workspace_id=self.workspace_id,
            asset=asset,
            version_no=version_no,
            created_by=self.user,
            config_snapshot=snapshot,
            **snapshot,
        )
        payload = serialize_asset(asset, include_versions=True)
        payload["draft_version"] = serialize_version(version)
        return payload

    def detail(self, asset_id):
        return serialize_asset(self._asset(asset_id), include_versions=True)

    def _record_event(self, asset, event_type, snapshot, version=None):
        return ApiGovernanceEvent.objects.create(
            workspace_id=self.workspace_id,
            asset=asset,
            version=version,
            event_type=event_type,
            event_snapshot=snapshot,
            operator=self.user,
        )

    def import_openapi(self, data):
        return parse_openapi_document(data)

    def compare_versions(self, asset_id, base_version_id, target_version_id):
        asset = self._asset(asset_id)
        versions = {
            str(row.id): row
            for row in ApiOrchestrationVersion.objects.filter(
                workspace_id=self.workspace_id,
                asset=asset,
                id__in=[base_version_id, target_version_id],
            )
        }
        base = versions.get(str(base_version_id))
        target = versions.get(str(target_version_id))
        if base is None or target is None:
            raise AppApiException(404, "待比较的接口版本不存在")
        tracked_fields = (
            "environment",
            "method",
            "endpoint_path",
            "request_mapping",
            "response_mapping",
            "parameter_bindings",
            "mock_response",
            "openapi_snapshot",
        )
        changed_fields = [
            field for field in tracked_fields if getattr(base, field) != getattr(target, field)
        ]
        input_diff = _schema_diff(base.input_schema, target.input_schema)
        output_diff = _schema_diff(base.output_schema, target.output_schema)
        if any(input_diff.values()):
            changed_fields.append("input_schema")
        if any(output_diff.values()):
            changed_fields.append("output_schema")
        breaking_changes = []
        if base.method != target.method:
            breaking_changes.append(f"请求方法由 {base.method} 变为 {target.method}")
        if base.endpoint_path != target.endpoint_path:
            breaking_changes.append(
                f"接口路径由 {base.endpoint_path} 变为 {target.endpoint_path}"
            )
        breaking_changes.extend(
            f"输入新增必填字段: {name}" for name in input_diff["required_added"]
        )
        breaking_changes.extend(
            f"输入字段类型变化: {item['field']} ({item['from']} → {item['to']})"
            for item in input_diff["type_changed"]
        )
        breaking_changes.extend(
            f"输出字段被移除: {name}" for name in output_diff["removed"]
        )
        breaking_changes.extend(
            f"输出字段类型变化: {item['field']} ({item['from']} → {item['to']})"
            for item in output_diff["type_changed"]
        )
        return {
            "base_version": serialize_version(base),
            "target_version": serialize_version(target),
            "changed_fields": changed_fields,
            "input_schema_diff": input_diff,
            "output_schema_diff": output_diff,
            "breaking_changes": breaking_changes,
            "breaking_count": len(breaking_changes),
            "compatible": not breaking_changes,
        }

    @transaction.atomic
    def publish(self, asset_id, version_id, data=None):
        serializer = ApiPublishSerializer(data=data or {})
        serializer.is_valid(raise_exception=True)
        publish_options = serializer.validated_data
        asset = ApiOrchestrationAsset.objects.select_for_update().filter(
            workspace_id=self.workspace_id, id=asset_id
        ).first()
        if asset is None:
            raise AppApiException(404, "接口资产不存在")
        version = ApiOrchestrationVersion.objects.filter(
            workspace_id=self.workspace_id, asset=asset, id=version_id
        ).first()
        if version is None:
            raise AppApiException(404, "接口版本不存在")
        if version.status == ApiVersionStatus.PUBLISHED:
            return self.detail(str(asset.id))
        if version.status != ApiVersionStatus.DRAFT:
            raise AppApiException(400, "仅草稿版本可以发布")
        earlier_versions = ApiOrchestrationVersion.objects.filter(
            workspace_id=self.workspace_id,
            asset=asset,
            version_no__lt=version.version_no,
        )
        if version.environment == ApiAssetEnvironment.GRAY and not earlier_versions.filter(
            environment=ApiAssetEnvironment.TEST,
            status__in=[ApiVersionStatus.PUBLISHED, ApiVersionStatus.ARCHIVED],
        ).exists():
            raise AppApiException(400, "灰度发布前必须存在已发布过的测试版本")
        if version.environment == ApiAssetEnvironment.PRODUCTION:
            if not earlier_versions.filter(
                environment=ApiAssetEnvironment.GRAY,
                status__in=[ApiVersionStatus.PUBLISHED, ApiVersionStatus.ARCHIVED],
            ).exists():
                raise AppApiException(400, "生产发布前必须存在已发布过的灰度版本")
            if not version.openapi_snapshot:
                raise AppApiException(400, "生产发布必须绑定 OpenAPI 契约快照")
            if not asset.ip_allowlist:
                raise AppApiException(400, "生产发布必须配置 IP 白名单")
            if version.adapter_mode == ApiAdapterMode.GATEWAY and not version.gateway_base_url.startswith(
                "https://"
            ):
                raise AppApiException(400, "生产网关地址必须使用 HTTPS")
            current = ApiOrchestrationVersion.objects.filter(
                workspace_id=self.workspace_id,
                asset=asset,
                status=ApiVersionStatus.PUBLISHED,
            ).first()
            if current:
                comparison = self.compare_versions(
                    str(asset.id), str(current.id), str(version.id)
                )
                if comparison["breaking_count"] and not publish_options[
                    "breaking_change_confirmed"
                ]:
                    raise AppApiException(400, "生产版本包含破坏性变更，必须显式确认")
                if comparison["breaking_count"] and not publish_options["change_ticket"]:
                    raise AppApiException(400, "确认生产破坏性变更时必须填写变更单号")
        ApiOrchestrationVersion.objects.filter(
            workspace_id=self.workspace_id,
            asset=asset,
            status=ApiVersionStatus.PUBLISHED,
        ).exclude(id=version.id).update(status=ApiVersionStatus.ARCHIVED)
        version.status = ApiVersionStatus.PUBLISHED
        version.published_at = timezone.now()
        version.save(update_fields=["status", "published_at", "update_time"])
        asset.published_version_no = version.version_no
        asset.enabled = True
        asset.save(update_fields=["published_version_no", "enabled", "update_time"])
        self._record_event(
            asset,
            "VERSION_PUBLISHED",
            {
                "environment": version.environment,
                "adapter_mode": version.adapter_mode,
                "breaking_change_confirmed": publish_options["breaking_change_confirmed"],
                "change_ticket": publish_options["change_ticket"],
            },
            version,
        )
        return self.detail(str(asset.id))

    @transaction.atomic
    def set_enabled(self, asset_id, data):
        serializer = ApiEnabledSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        asset = ApiOrchestrationAsset.objects.select_for_update().filter(
            workspace_id=self.workspace_id, id=asset_id
        ).first()
        if asset is None:
            raise AppApiException(404, "接口资产不存在")
        if values["enabled"] and asset.published_version_no is None:
            raise AppApiException(400, "没有发布版本的接口不能启用")
        asset.enabled = values["enabled"]
        asset.save(update_fields=["enabled", "update_time"])
        self._record_event(
            asset,
            "ASSET_ENABLED" if asset.enabled else "ASSET_DISABLED",
            {"enabled": asset.enabled, "reason": values["reason"]},
        )
        return self.detail(str(asset.id))

    @transaction.atomic
    def rollback(self, asset_id, version_id):
        asset = ApiOrchestrationAsset.objects.select_for_update().filter(
            workspace_id=self.workspace_id, id=asset_id
        ).first()
        if asset is None:
            raise AppApiException(404, "接口资产不存在")
        target = ApiOrchestrationVersion.objects.filter(
            workspace_id=self.workspace_id, asset=asset, id=version_id
        ).first()
        if target is None:
            raise AppApiException(404, "目标版本不存在")
        latest = ApiOrchestrationVersion.objects.filter(asset=asset).order_by("-version_no").first()
        snapshot = target.config_snapshot.copy()
        rollback_version = ApiOrchestrationVersion.objects.create(
            workspace_id=self.workspace_id,
            asset=asset,
            version_no=(latest.version_no if latest else 0) + 1,
            created_by=self.user,
            config_snapshot=snapshot,
            **snapshot,
        )
        return self.publish(
            str(asset.id),
            str(rollback_version.id),
            {"breaking_change_confirmed": True, "change_ticket": "ROLLBACK"},
        )

    def _published_version(self, asset):
        if not asset.enabled or asset.published_version_no is None:
            raise AppApiException(400, "接口资产尚未发布或已停用")
        return ApiOrchestrationVersion.objects.filter(
            workspace_id=self.workspace_id,
            asset=asset,
            version_no=asset.published_version_no,
            status=ApiVersionStatus.PUBLISHED,
        ).first()

    @transaction.atomic
    def mock_invoke(self, asset_id, data):
        serializer = ApiMockInvokeSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        asset = ApiOrchestrationAsset.objects.select_for_update().filter(
            workspace_id=self.workspace_id, id=asset_id
        ).first()
        if asset is None:
            raise AppApiException(404, "接口资产不存在")
        version = self._published_version(asset)
        request_id = values.get("request_id") or f"XIADA-{str(uuid.uuid7()).replace('-', '')[-16:]}"
        if ApiInvocationAudit.objects.filter(workspace_id=self.workspace_id, request_id=request_id).exists():
            raise AppApiException(400, "请求号已存在")
        started = time.perf_counter()
        if asset.circuit_state == ApiCircuitState.OPEN and asset.circuit_opened_at:
            elapsed = (timezone.now() - asset.circuit_opened_at).total_seconds()
            if elapsed >= version.circuit_recovery_seconds:
                asset.circuit_state = ApiCircuitState.CLOSED
                asset.consecutive_failures = 0
                asset.circuit_opened_at = None
                asset.save(
                    update_fields=[
                        "circuit_state",
                        "consecutive_failures",
                        "circuit_opened_at",
                        "update_time",
                    ]
                )
                self._record_event(
                    asset,
                    "CIRCUIT_RECOVERED",
                    {"recovery_seconds": version.circuit_recovery_seconds},
                    version,
                )
            else:
                audit = ApiInvocationAudit.objects.create(
                    workspace_id=self.workspace_id,
                    asset=asset,
                    version=version,
                    request_id=request_id,
                    status=ApiInvocationStatus.CIRCUIT_OPEN,
                    auth_scheme=asset.auth_scheme,
                    auth_result=False,
                    schema_result=False,
                    request_snapshot={
                        "protocol": version.protocol,
                        "toolCode": asset.asset_key,
                        "version": version.version_no,
                        "attempts": 0,
                    },
                    response_snapshot={},
                    error_message="熔断器已打开，请在恢复窗口后重试",
                    duration_ms=max(1, int((time.perf_counter() - started) * 1000)),
                    operator=self.user,
                )
                return serialize_audit(audit)
        auth_result, auth_error = validate_invocation_auth(
            asset, version, values["auth_context"]
        )
        errors = [] if auth_result else [auth_error]
        resolved_payload, resolution_errors, source_summary = resolve_parameter_bindings(
            version.parameter_bindings,
            values["payload"],
            values["source_context"],
        )
        schema_errors = (
            resolution_errors + validate_payload(version.input_schema, resolved_payload)
            if auth_result
            else []
        )
        status = ApiInvocationStatus.SUCCESS
        response = {}
        attempts = 0
        if not auth_result:
            status = ApiInvocationStatus.AUTH_FAILED
        elif schema_errors:
            status = ApiInvocationStatus.SCHEMA_FAILED
            errors = schema_errors
        else:
            attempts = min(values["simulated_failures"], version.max_retries) + 1
            if values["simulated_latency_ms"] > version.timeout_ms:
                attempts = version.max_retries + 1
                status = ApiInvocationStatus.TIMEOUT
                errors = [
                    f"调用耗时 {values['simulated_latency_ms']}ms 超过 {version.timeout_ms}ms，"
                    f"已尝试 {attempts} 次"
                ]
            elif values["simulated_failures"] > version.max_retries:
                attempts = version.max_retries + 1
                status = ApiInvocationStatus.RETRY_EXHAUSTED
                errors = [f"瞬时失败超过最大重试次数 {version.max_retries}"]
            else:
                response = {
                    "requestId": request_id,
                    "code": "SUCCESS",
                    "data": version.mock_response,
                }
                output_errors = validate_payload(version.output_schema, response["data"])
                if output_errors:
                    status = ApiInvocationStatus.RESPONSE_FAILED
                    errors = output_errors
        resilience_failed = status in (
            ApiInvocationStatus.TIMEOUT,
            ApiInvocationStatus.RETRY_EXHAUSTED,
            ApiInvocationStatus.RESPONSE_FAILED,
        )
        if resilience_failed:
            asset.consecutive_failures += 1
            if asset.consecutive_failures >= version.circuit_failure_threshold:
                asset.circuit_state = ApiCircuitState.OPEN
                asset.circuit_opened_at = timezone.now()
                self._record_event(
                    asset,
                    "CIRCUIT_OPENED",
                    {
                        "failure_count": asset.consecutive_failures,
                        "threshold": version.circuit_failure_threshold,
                        "last_status": status,
                    },
                    version,
                )
            asset.save(
                update_fields=[
                    "consecutive_failures",
                    "circuit_state",
                    "circuit_opened_at",
                    "update_time",
                ]
            )
        elif status == ApiInvocationStatus.SUCCESS and asset.consecutive_failures:
            asset.consecutive_failures = 0
            asset.save(update_fields=["consecutive_failures", "update_time"])
        audit = ApiInvocationAudit.objects.create(
            workspace_id=self.workspace_id,
            asset=asset,
            version=version,
            request_id=request_id,
            status=status,
            auth_scheme=asset.auth_scheme,
            auth_result=auth_result,
            schema_result=auth_result and not schema_errors,
            request_snapshot={
                "protocol": version.protocol,
                "toolCode": asset.asset_key,
                "version": version.version_no,
                "params": resolved_payload,
                "parameterSources": source_summary,
                "attempts": attempts,
                "timeoutMs": version.timeout_ms,
                "adapterMode": version.adapter_mode,
            },
            response_snapshot=response,
            error_message="；".join(errors),
            duration_ms=max(1, int((time.perf_counter() - started) * 1000)),
            operator=self.user,
        )
        return serialize_audit(audit)

    @transaction.atomic
    def bootstrap_demo(self):
        asset = self._assets().filter(asset_key="customer_recommendation").first()
        if asset is None:
            payload = self.save_asset(
                {
                    "asset_key": "customer_recommendation",
                    "name": "客户产品推荐",
                    "description": "晓搭协议 Mock：根据客户标识返回推荐产品",
                    "auth_scheme": ApiAssetAuthScheme.API_KEY,
                    "auth_reference": "system-api-key:m05-demo",
                    "ip_allowlist": ["127.0.0.1"],
                    "environment": ApiAssetEnvironment.TEST,
                    "method": "POST",
                    "endpoint_path": "/xiaoda/v1/customer/recommendation",
                    "input_schema": {
                        "type": "object",
                        "required": ["customer_id"],
                        "additionalProperties": False,
                        "properties": {"customer_id": {"type": "string"}},
                    },
                    "output_schema": {
                        "type": "object",
                        "required": ["recommendations"],
                        "properties": {"recommendations": {"type": "array"}},
                    },
                    "request_mapping": {"customerId": "customer_id"},
                    "response_mapping": {"items": "recommendations"},
                    "mock_response": {
                        "recommendations": [
                            {"product_code": "P-5G-001", "name": "5G 畅享套餐", "score": 0.92}
                        ]
                    },
                }
            )
            asset = self._asset(payload["id"])
            self.publish(str(asset.id), payload["draft_version"]["id"])
        elif asset.published_version_no is None:
            latest = asset.versions.first()
            self.publish(str(asset.id), str(latest.id))
        self.mock_invoke(
            str(asset.id),
            {"payload": {"customer_id": "C-DEMO-001"}, "auth_context": {"validated": True, "scheme": "API_KEY"}},
        )
        self.mock_invoke(
            str(asset.id),
            {"payload": {"customer_id": "C-DEMO-002"}, "auth_context": {"validated": False}},
        )
        self.mock_invoke(
            str(asset.id),
            {"payload": {}, "auth_context": {"validated": True, "scheme": "API_KEY"}},
        )
        return self.dashboard()
