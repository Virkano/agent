"""Deterministic, metadata-only inventory of registered data and HTTP assets."""

import hashlib
import json
import re

from django.apps import apps
from django.urls import URLPattern, URLResolver, get_resolver


# Owner roles are accountable placeholders until named owners are approved.
DOMAIN_POLICIES = {
    "application": ("智能体应用", "智能体平台主管角色", "L3"),
    "chat": ("对话服务", "智能体平台主管角色", "L3"),
    "knowledge": ("知识库", "知识平台主管角色", "L3"),
    "marketing": ("营销运营", "营销业务负责人角色", "L3"),
    "models_provider": ("模型平台", "模型平台主管角色", "L3"),
    "platform_monitoring": ("指标预警", "运维监控负责人角色", "L2"),
    "rehearsal": ("故障预演", "网络运维负责人角色", "L3"),
    "system_manage": ("系统治理", "平台安全负责人角色", "L4"),
    "tools": ("工具与 API", "集成平台主管角色", "L3"),
    "trigger": ("事件编排", "集成平台主管角色", "L3"),
    "users": ("身份与权限", "平台安全负责人角色", "L4"),
    "xpack_lite": ("工作空间权限", "平台安全负责人角色", "L4"),
    "common": ("共享平台", "平台架构负责人角色", "L3"),
    "oss": ("文件服务", "平台架构负责人角色", "L3"),
    "homepage": ("门户", "平台架构负责人角色", "L2"),
    "folders": ("目录", "知识平台主管角色", "L3"),
}
FRAMEWORK_APPS = {"contenttypes", "django_apscheduler", "django_celery_beat"}
MASTER_DATA_MODELS = {"users.User", "marketing.MarketingCustomer"}
INTERFACE_LAYERS = {
    "users": "PLATFORM",
    "system_manage": "PLATFORM",
    "xpack_lite": "PLATFORM",
    "common": "PLATFORM",
    "homepage": "PLATFORM",
    "chat": "CHANNEL",
    "oss": "CHANNEL",
    "tools": "ORCHESTRATION",
    "trigger": "ORCHESTRATION",
}
SENSITIVE_NAME = re.compile(
    r"password|secret|token|credential|api_key|phone|email|mobile|id_card|customer|address|"
    r"payload|snapshot|content|body|prompt|message|raw_data",
    re.IGNORECASE,
)
HTTP_METHODS = ("get", "post", "put", "patch", "delete")


def _policy(app_label):
    return DOMAIN_POLICIES.get(app_label, ("待归属", "待指定", "UNCLASSIFIED"))


def _model_entries():
    entries = []
    for model in apps.get_models():
        meta = model._meta
        if meta.app_label in FRAMEWORK_APPS or meta.proxy:
            continue
        domain, owner_role, classification = _policy(meta.app_label)
        field_names = sorted(field.name for field in meta.concrete_fields)
        sensitive_fields = [name for name in field_names if SENSITIVE_NAME.search(name)]
        if sensitive_fields and classification == "L2":
            classification = "L3"
        label = meta.label
        entries.append({
            "model": label,
            "table": meta.db_table,
            "domain": domain,
            "owner_role": owner_role,
            "classification": classification,
            "field_count": len(field_names),
            "sensitive_field_names": sensitive_fields,
            "master_data": label in MASTER_DATA_MODELS,
            "storage": "PostgreSQL",
            "proposed_lake_dataset": f"telecom_ai.{meta.app_label}.{meta.db_table}",
            "lake_mapping_status": "PROPOSED_NOT_CONNECTED",
            "read_access_audit_status": "DIRECT_API_PARTIAL" if label in MASTER_DATA_MODELS else "NOT_ASSESSED",
            "read_access_audit_evidence": "system_manage.MasterDataAccessEvent" if label in MASTER_DATA_MODELS else "",
            "source": f"{model.__module__}.{model.__name__}",
        })
    return sorted(entries, key=lambda item: item["model"])


def _route_entries():
    entries = []

    def visit(patterns, prefix=""):
        for pattern in patterns:
            route = prefix + str(pattern.pattern)
            if isinstance(pattern, URLResolver):
                visit(pattern.url_patterns, route)
                continue
            if not isinstance(pattern, URLPattern) or not route.startswith(("admin/api/", "chat/api/")):
                continue
            callback = pattern.callback
            view = getattr(callback, "cls", None) or getattr(callback, "view_class", None)
            module = view.__module__ if view else callback.__module__
            app_label = module.split(".", 1)[0]
            domain, owner_role, _ = _policy(app_label)
            methods = sorted(method.upper() for method in HTTP_METHODS if view and hasattr(view, method))
            entries.append({
                "route": "/" + route,
                "surface": "ADMIN" if route.startswith("admin/api/") else "CHAT",
                "methods": methods or ["UNRESOLVED"],
                "view": f"{module}.{view.__name__ if view else callback.__name__}",
                "domain": domain,
                "owner_role": owner_role,
                "interface_layer": INTERFACE_LAYERS.get(app_label, "BUSINESS_SERVICE"),
                "openapi_review_status": "NOT_VERIFIED",
                "eop_registration_status": "PENDING",
                "dcoos_compatibility_status": "PENDING",
            })

    visit(get_resolver().url_patterns)
    return sorted(entries, key=lambda item: (item["route"], item["view"]))


def build_inventory():
    models = _model_entries()
    routes = _route_entries()
    payload = {
        "schema_version": 1,
        "classification_policy": {
            "L2": "内部数据",
            "L3": "敏感业务数据；字段级名称提示需人工复核",
            "L4": "受限身份或安全数据",
        },
        "limitations": [
            "仅扫描 Django 已注册模型和 API URL 元数据，不读取业务记录或凭证值",
            "负责人为岗位角色，尚未绑定真实责任人",
            "字段分级仅做保守初筛；JSON 内容、对象文件和实际权限需人工复核",
            "EOP 注册、DCOOS 兼容、入湖映射与主数据读取审计均未自动认定完成",
        ],
        "models": models,
        "api_routes": routes,
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    payload["sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return payload


def validate_inventory(inventory):
    issues = []
    model_labels = {entry["model"] for entry in inventory["models"]}
    for label in sorted(MASTER_DATA_MODELS - model_labels):
        issues.append(f"Master data model is not registered: {label}")
    for entry in inventory["models"]:
        if entry["classification"] == "UNCLASSIFIED" or entry["owner_role"] == "待指定":
            issues.append(f"Model ownership/classification unresolved: {entry['model']}")
    for entry in inventory["api_routes"]:
        if entry["owner_role"] == "待指定":
            issues.append(f"API ownership unresolved: {entry['route']} ({entry['view']})")
    if not inventory["models"] or not inventory["api_routes"]:
        issues.append("Model or API inventory is empty")
    return issues
