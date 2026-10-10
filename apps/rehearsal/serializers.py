import csv
import hashlib
import json
import math
import random
import re
from collections import Counter
from datetime import timedelta
from io import StringIO

from django.db import transaction
from django.db.models import Count, Max, Min, Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import serializers

from common.exception.app_exception import AppApiException

from .models import (
    AlertAction,
    AlertSeverity,
    AlertStatus,
    AuxiliarySimulationStatus,
    CapabilityCallStatus,
    CapabilityMockKind,
    ComplaintBatchStatus,
    ComplaintDataSource,
    ComplaintSeverity,
    ComplaintStatus,
    ComplaintValidationStatus,
    DataDistribution,
    DataModelBuildStrategy,
    DataModelLoadStatus,
    DataModelQualityStatus,
    DataSimulationKind,
    DataSimulationStatus,
    FaultConfigurationAction,
    FaultConfigurationStatus,
    FaultReportAction,
    FaultReportLevel,
    FaultReportStatus,
    FaultReportTemplateStatus,
    RandomFactorCategory,
    RandomFactorDistribution,
    RehearsalComplaint,
    RehearsalComplaintBatch,
    RehearsalComplaintTemplate,
    RehearsalCustomerScope,
    RehearsalDataBatch,
    RehearsalDataModel,
    RehearsalDataModelLoad,
    RehearsalDataModelVersion,
    RehearsalDataPoint,
    RehearsalDataTemplate,
    RehearsalEventType,
    RehearsalFaultConfiguration,
    RehearsalFaultConfigurationEvent,
    RehearsalFaultReport,
    RehearsalFaultReportEvent,
    RehearsalFaultReportTemplate,
    RehearsalInstance,
    RehearsalInstanceAction,
    RehearsalInstanceEvent,
    RehearsalInstanceStatus,
    RehearsalAlert,
    RehearsalAlertEvent,
    RehearsalAlertTemplate,
    RehearsalAuxiliarySimulation,
    RehearsalCapabilityCall,
    RehearsalCapabilityMock,
    RehearsalProcessEvent,
    RehearsalProcessRun,
    RehearsalProcessStep,
    RehearsalProcessTemplate,
    RehearsalScenario,
    RehearsalScenarioStatus,
    RehearsalSceneEvent,
    RehearsalSceneLibrary,
    RehearsalSceneLibraryEvent,
    RehearsalSceneReplay,
    RehearsalSceneRun,
    RehearsalSceneScript,
    RehearsalSceneStep,
    RehearsalTracebackSnapshot,
    RehearsalWorkOrder,
    RehearsalWorkOrderEvent,
    ProcessRunAction,
    ProcessRunStatus,
    ProcessStepStatus,
    SceneRunAction,
    SceneRunStatus,
    SceneStepStatus,
    SceneLibraryAction,
    SceneLibraryStatus,
    SceneLibraryVisibility,
    SceneReplayStatus,
    TracebackScope,
    TracebackStatus,
    WorkOrderAction,
    WorkOrderPriority,
    WorkOrderStatus,
)


SIMULATION_RECORD_KIND_LABELS = {
    "INSTANCE": "预演实例",
    "COMPLAINT_BATCH": "申告批次",
    "DATA_BATCH": "趋势数据",
    "PROCESS_RUN": "处置流程",
    "SCENE_RUN": "场景执行",
    "ALERT": "模拟告警",
    "TRACEBACK": "动态回溯",
    "CAPABILITY_CALL": "能力调用",
    "FAULT_REPORT": "故障上报",
    "AUXILIARY_SIMULATION": "辅助模拟",
}

SIMULATION_RECORD_STATE_LABELS = {
    "PENDING": "待执行",
    "RUNNING": "执行中",
    "SUCCEEDED": "已完成",
    "ATTENTION": "需关注",
    "FAILED": "已失败",
}


PUBLIC_TEMPLATE = {
    "code": "PUBLIC-COMPLAINT-V1",
    "name": "公众客户申告模板",
    "customer_type": RehearsalCustomerScope.PUBLIC,
    "profile_schema": {
        "customer_ref": "PUB-{sequence}",
        "customer_name": "模拟公众客户{sequence}",
        "customer_segment": ["融合套餐", "移动客户", "宽带客户"],
    },
    "complaint_schema": {"channels": ["10000号", "在线客服", "营业厅"]},
    "categories": ["宽带中断", "套餐资费", "移动网络", "业务办理"],
    "content_patterns": [
        "模拟客户反馈{category}问题，请尽快核查处理。",
        "模拟客户多次咨询{category}，希望获得明确进度。",
    ],
}

ENTERPRISE_TEMPLATE = {
    "code": "ENTERPRISE-COMPLAINT-V1",
    "name": "政企客户申告模板",
    "customer_type": RehearsalCustomerScope.ENTERPRISE,
    "profile_schema": {
        "customer_ref": "ENT-{sequence}",
        "customer_name": "模拟政企客户{sequence}",
        "customer_segment": ["政企专线", "云网客户", "行业客户"],
    },
    "complaint_schema": {"channels": ["客户经理", "政企热线", "服务台"]},
    "categories": ["专线质量", "云资源访问", "网络时延", "业务连续性"],
    "content_patterns": [
        "模拟政企客户反馈{category}异常，要求按 SLA 快速响应。",
        "模拟重要客户发现{category}波动，请启动协同处置。",
    ],
}

PUBLIC_PROCESS_TEMPLATE = {
    "code": "PUBLIC-DISPOSAL-V1",
    "name": "公众客户申告处置流程",
    "description": "模拟公众客户申告从受理定位到客户回访的标准处置过程。",
    "customer_scope": RehearsalCustomerScope.PUBLIC,
    "auto_advance": False,
    "steps": [
        {
            "code": "ACCEPT",
            "name": "受理与定位",
            "description": "汇总申告范围并完成初步故障定位。",
            "owner_role": "客服调度",
            "planned_minutes": 10,
        },
        {
            "code": "DIAGNOSE",
            "name": "网络检测",
            "description": "执行线路、设备和区域影响检测。",
            "owner_role": "网络运维",
            "planned_minutes": 20,
        },
        {
            "code": "DISPOSE",
            "name": "处置实施",
            "description": "按定位结果执行恢复或业务调整。",
            "owner_role": "现场处置",
            "planned_minutes": 30,
        },
        {
            "code": "FOLLOW_UP",
            "name": "客户回访",
            "description": "验证恢复结果并记录客户反馈。",
            "owner_role": "客服专员",
            "planned_minutes": 15,
        },
    ],
}

ENTERPRISE_PROCESS_TEMPLATE = {
    "code": "ENTERPRISE-DISPOSAL-V1",
    "name": "政企客户协同处置流程",
    "description": "模拟重点客户故障的 SLA 研判、多专业协同与恢复验证。",
    "customer_scope": RehearsalCustomerScope.ENTERPRISE,
    "auto_advance": True,
    "steps": [
        {
            "code": "KEY_ACCEPT",
            "name": "重点客户受理",
            "description": "识别客户等级、业务范围和影响面。",
            "owner_role": "政企服务台",
            "planned_minutes": 5,
        },
        {
            "code": "SLA_ASSESS",
            "name": "SLA 研判",
            "description": "核对服务等级并确定响应优先级。",
            "owner_role": "客户经理",
            "planned_minutes": 10,
        },
        {
            "code": "COLLABORATE",
            "name": "多专业协同",
            "description": "组织云网、线路和现场团队联合处置。",
            "owner_role": "协同调度",
            "planned_minutes": 30,
        },
        {
            "code": "VERIFY",
            "name": "恢复验证",
            "description": "验证关键业务恢复和链路稳定性。",
            "owner_role": "网络运维",
            "planned_minutes": 15,
        },
        {
            "code": "ENTERPRISE_FOLLOW_UP",
            "name": "客户回访",
            "description": "同步处置结论并完成服务闭环。",
            "owner_role": "客户经理",
            "planned_minutes": 15,
        },
    ],
}

NETWORK_METRIC_TEMPLATE = {
    "code": "NETWORK-METRIC-V1",
    "name": "网络指标趋势模板",
    "description": "模拟网络负载、平均时延和告警数量的连续时序变化。",
    "kind": DataSimulationKind.METRIC,
    "default_tags": ["网络质量", "容量"],
    "default_rules": [
        {
            "code": "NETWORK_LOAD",
            "name": "网络负载",
            "unit": "%",
            "min_value": 35,
            "max_value": 95,
            "start_value": 48,
            "end_value": 82,
            "distribution": DataDistribution.WAVE,
            "decimals": 1,
        },
        {
            "code": "LATENCY_MS",
            "name": "平均时延",
            "unit": "ms",
            "min_value": 8,
            "max_value": 120,
            "start_value": 18,
            "end_value": 68,
            "distribution": DataDistribution.LINEAR,
            "decimals": 1,
        },
        {
            "code": "ALARM_COUNT",
            "name": "告警数量",
            "unit": "个",
            "min_value": 0,
            "max_value": 30,
            "start_value": 2,
            "end_value": 18,
            "distribution": DataDistribution.STEP,
            "decimals": 0,
        },
    ],
}

SENTIMENT_TREND_TEMPLATE = {
    "code": "SENTIMENT-TREND-V1",
    "name": "客户舆情趋势模板",
    "description": "模拟舆情声量、情感得分和负向占比的时间变化。",
    "kind": DataSimulationKind.SENTIMENT,
    "default_tags": ["客户舆情", "服务感知"],
    "default_rules": [
        {
            "code": "MENTION_VOLUME",
            "name": "舆情声量",
            "unit": "条",
            "min_value": 10,
            "max_value": 240,
            "start_value": 35,
            "end_value": 160,
            "distribution": DataDistribution.WAVE,
            "decimals": 0,
        },
        {
            "code": "SENTIMENT_SCORE",
            "name": "情感得分",
            "unit": "分",
            "min_value": -1,
            "max_value": 1,
            "start_value": 0.35,
            "end_value": -0.45,
            "distribution": DataDistribution.LINEAR,
            "decimals": 2,
        },
        {
            "code": "NEGATIVE_RATIO",
            "name": "负向占比",
            "unit": "%",
            "min_value": 0,
            "max_value": 100,
            "start_value": 18,
            "end_value": 67,
            "distribution": DataDistribution.STEP,
            "decimals": 1,
        },
    ],
}

NETWORK_FAULT_SCENE_SCRIPT = {
    "code": "NETWORK-FAULT-SCENE-V1",
    "name": "网络故障场景预演剧本",
    "description": "将模拟申告、网络指标与处置流程注入同一场景，完成异常研判、处置和恢复验证。",
    "steps": [
        {
            "code": "VERIFY_INJECTION",
            "name": "校验注入数据",
            "description": "核对申告、指标趋势和处置流程是否完整关联到当前实例。",
            "expected_result": "所有选定模拟数据均可追溯且实例归属一致。",
        },
        {
            "code": "ASSESS_IMPACT",
            "name": "研判故障影响",
            "description": "结合客户申告和指标变化判断影响范围、客户类型与风险等级。",
            "expected_result": "形成清晰的影响范围和风险判断。",
        },
        {
            "code": "EXECUTE_DISPOSAL",
            "name": "执行协同处置",
            "description": "按关联处置流程完成故障定位、调度和恢复动作。",
            "expected_result": "关键处置步骤已执行并留下过程记录。",
        },
        {
            "code": "VERIFY_RECOVERY",
            "name": "验证业务恢复",
            "description": "复核指标趋势、告警变化和客户侧服务恢复情况。",
            "expected_result": "确认核心指标和客户感知恢复到可接受范围。",
        },
        {
            "code": "CLOSE_SCENE",
            "name": "总结与转工单",
            "description": "沉淀预演结论，对遗留问题创建人工工单并明确责任人。",
            "expected_result": "形成场景总结，遗留问题具备人工闭环入口。",
        },
    ],
}

NETWORK_ALERT_TEMPLATE = {
    "code": "NETWORK-ALERT-V1",
    "name": "网络质量告警模拟模板",
    "description": "模拟网络时延、丢包和负载异常的上报、确认与恢复过程。",
    "default_severity": AlertSeverity.HIGH,
    "rules": [
        {
            "code": "LATENCY_HIGH",
            "name": "网络时延超阈值",
            "metric_code": "LATENCY_MS",
            "metric_name": "平均时延",
            "operator": "GT",
            "threshold": 100,
            "unit": "ms",
            "resource_type": "网络设备",
        },
        {
            "code": "PACKET_LOSS_HIGH",
            "name": "网络丢包率超阈值",
            "metric_code": "PACKET_LOSS",
            "metric_name": "丢包率",
            "operator": "GT",
            "threshold": 5,
            "unit": "%",
            "resource_type": "网络链路",
        },
    ],
}

DEFAULT_CAPABILITY_MOCKS = (
    {
        "code": "QUERY-RESOURCE-STATUS-V1",
        "name": "资源状态查询 API",
        "description": "模拟查询网络资源当前状态、负载和告警摘要。",
        "kind": CapabilityMockKind.API,
        "method": "GET",
        "endpoint": "/mock/network/resources/{resource_id}/status",
        "request_schema": {
            "required": ["resource_id"],
            "properties": {"resource_id": {"type": "string"}, "include_metrics": {"type": "boolean"}},
        },
        "response_template": {
            "available": True,
            "health": "DEGRADED",
            "active_alerts": 2,
            "message": "模拟资源状态已返回",
        },
        "failure_template": {"code": "RESOURCE_UNAVAILABLE", "message": "模拟资源暂不可用"},
        "default_status": CapabilityCallStatus.SUCCEEDED,
        "default_latency_ms": 86,
    },
    {
        "code": "ISOLATE-FAULT-NODE-V1",
        "name": "故障节点隔离原子能力",
        "description": "在隔离沙盒中模拟节点摘流、旁路切换和处置回执。",
        "kind": CapabilityMockKind.ATOMIC,
        "method": "POST",
        "endpoint": "atomic://network/isolate-fault-node",
        "request_schema": {
            "required": ["node_id", "strategy"],
            "properties": {"node_id": {"type": "string"}, "strategy": {"type": "string"}},
        },
        "response_template": {
            "accepted": True,
            "isolation_state": "ISOLATED",
            "rollback_ready": True,
            "message": "模拟隔离动作执行完成",
        },
        "failure_template": {"code": "ISOLATION_REJECTED", "message": "模拟隔离动作被拒绝"},
        "default_status": CapabilityCallStatus.SUCCEEDED,
        "default_latency_ms": 240,
    },
)

DEFAULT_FAULT_CONFIGURATION = {
    "request_id": "catalog:fault-configuration:network-core:v1",
    "code": "NETWORK-CORE-FAULT",
    "name": "核心网络节点故障模拟配置",
    "description": "覆盖核心节点告警、处置超时、全天候窗口、拓扑隔离与应急预案的默认预演配置。",
    "alert_rules": [
        {
            "code": "CORE_LATENCY_CRITICAL",
            "name": "核心链路时延严重异常",
            "severity": AlertSeverity.CRITICAL,
            "metric_code": "LATENCY_MS",
            "operator": "GTE",
            "threshold": 120,
            "unit": "ms",
        },
        {
            "code": "CORE_PACKET_LOSS_HIGH",
            "name": "核心链路丢包异常",
            "severity": AlertSeverity.HIGH,
            "metric_code": "PACKET_LOSS",
            "operator": "GTE",
            "threshold": 5,
            "unit": "%",
        },
    ],
    "timeout_policy": {
        "overall_seconds": 900,
        "step_seconds": 300,
        "on_timeout": "ESCALATE_AND_SWITCH",
        "retry_limit": 1,
    },
    "active_window": {
        "timezone": "Asia/Shanghai",
        "weekdays": [1, 2, 3, 4, 5, 6, 7],
        "start": "00:00",
        "end": "23:59",
    },
    "topology_snapshot": {
        "version": "TOPOLOGY-CORE-2026.09",
        "nodes": [
            {"id": "GW-01", "name": "业务网关", "type": "GATEWAY", "zone": "东区", "state": "HEALTHY"},
            {"id": "CORE-01", "name": "核心节点 A", "type": "CORE", "zone": "中心区", "state": "FAULT"},
            {"id": "CORE-02", "name": "核心节点 B", "type": "CORE", "zone": "中心区", "state": "STANDBY"},
            {"id": "ACCESS-01", "name": "接入节点", "type": "ACCESS", "zone": "南区", "state": "DEGRADED"},
        ],
        "links": [
            {"source": "GW-01", "target": "CORE-01", "state": "DEGRADED"},
            {"source": "GW-01", "target": "CORE-02", "state": "STANDBY"},
            {"source": "CORE-01", "target": "ACCESS-01", "state": "INTERRUPTED"},
            {"source": "CORE-02", "target": "ACCESS-01", "state": "AVAILABLE"},
        ],
    },
    "emergency_plan": {
        "code": "PLAN-CORE-ISOLATE-SWITCH",
        "name": "核心节点隔离与旁路切换预案",
        "owner": "网络运维战情室",
        "steps": [
            {"code": "CONFIRM", "name": "确认故障节点", "owner_role": "监控席", "target_minutes": 3},
            {"code": "ISOLATE", "name": "摘流并隔离节点", "owner_role": "核心网运维", "target_minutes": 5},
            {"code": "SWITCH", "name": "切换备用链路", "owner_role": "调度席", "target_minutes": 5},
            {"code": "VERIFY", "name": "核验业务恢复", "owner_role": "业务验证席", "target_minutes": 10},
        ],
    },
}

DEFAULT_FAULT_REPORT_TEMPLATE = {
    "request_id": "catalog:fault-report-template:network-core:v1",
    "code": "NETWORK-CORE-FAULT-REPORT",
    "name": "核心网络故障分阶段上报模板",
    "description": "覆盖首次上报、影响确认、处置进展和恢复确认的故障上报时限与责任角色。",
    "default_level": FaultReportLevel.LEVEL_2,
    "stage_definitions": [
        {
            "code": "INITIAL_REPORT",
            "name": "首次上报",
            "duration_minutes": 5,
            "owner_role": "监控席",
            "required_fields": ["title", "description", "impact_scope"],
        },
        {
            "code": "IMPACT_CONFIRM",
            "name": "影响确认",
            "duration_minutes": 10,
            "owner_role": "故障指挥",
            "required_fields": ["impact_scope"],
        },
        {
            "code": "DISPOSAL_PROGRESS",
            "name": "处置进展",
            "duration_minutes": 15,
            "owner_role": "核心网运维",
            "required_fields": [],
        },
        {
            "code": "RECOVERY_CONFIRM",
            "name": "恢复确认",
            "duration_minutes": 20,
            "owner_role": "业务验证席",
            "required_fields": [],
        },
    ],
    "required_fields": ["title", "description", "impact_scope"],
}

RANDOM_FACTOR_CATALOG = [
    {
        "code": "NETWORK_JITTER",
        "name": "网络抖动",
        "category": RandomFactorCategory.NETWORK,
        "unit": "ms",
        "min_value": 20,
        "max_value": 100,
        "distribution": RandomFactorDistribution.NORMAL,
        "trigger_probability": 0.8,
    },
    {
        "code": "PACKET_LOSS",
        "name": "随机丢包",
        "category": RandomFactorCategory.NETWORK,
        "unit": "%",
        "min_value": 0.1,
        "max_value": 5,
        "distribution": RandomFactorDistribution.UNIFORM,
        "trigger_probability": 0.3,
    },
    {
        "code": "PROPAGATION_DELAY",
        "name": "故障传播延迟",
        "category": RandomFactorCategory.FAULT,
        "unit": "s",
        "min_value": 30,
        "max_value": 300,
        "distribution": RandomFactorDistribution.UNIFORM,
        "trigger_probability": 0.65,
    },
    {
        "code": "FAULT_SPREAD",
        "name": "故障扩散范围",
        "category": RandomFactorCategory.FAULT,
        "unit": "区域",
        "min_value": 1,
        "max_value": 4,
        "distribution": RandomFactorDistribution.UNIFORM,
        "trigger_probability": 0.45,
    },
    {
        "code": "TRAFFIC_PEAK",
        "name": "随机流量峰值",
        "category": RandomFactorCategory.TRAFFIC,
        "unit": "倍",
        "min_value": 1.5,
        "max_value": 3,
        "distribution": RandomFactorDistribution.NORMAL,
        "trigger_probability": 0.7,
    },
    {
        "code": "TRAFFIC_FREQUENCY",
        "name": "流量波动频率",
        "category": RandomFactorCategory.TRAFFIC,
        "unit": "分钟",
        "min_value": 5,
        "max_value": 15,
        "distribution": RandomFactorDistribution.UNIFORM,
        "trigger_probability": 0.9,
    },
]

IMPORT_FIELDS = (
    "occurred_at",
    "customer_type",
    "customer_ref",
    "customer_name",
    "contact",
    "customer_segment",
    "region",
    "channel",
    "category",
    "severity",
    "title",
    "content",
)
REQUIRED_IMPORT_FIELDS = {
    "occurred_at",
    "customer_type",
    "customer_ref",
    "category",
    "severity",
    "title",
    "content",
}


class ScenarioCreateSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=128)
    description = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")
    customer_scope = serializers.ChoiceField(
        choices=RehearsalCustomerScope.choices,
        default=RehearsalCustomerScope.MIXED,
    )
    configuration = serializers.JSONField(required=False, default=dict)


class InstanceCreateSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=160)
    scenario_id = serializers.UUIDField()
    name = serializers.CharField(max_length=128)
    code = serializers.CharField(required=False, allow_blank=True, max_length=64, default="")
    planned_start_at = serializers.DateTimeField(required=False, allow_null=True)
    parameters = serializers.JSONField(required=False, default=dict)


class ComplaintGenerateSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=160)
    template_id = serializers.UUIDField()
    count = serializers.IntegerField(min_value=1, max_value=500)
    start_at = serializers.DateTimeField()
    interval_minutes = serializers.IntegerField(min_value=1, max_value=1440, default=5)


class InstanceOperateSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=RehearsalInstanceAction.choices)
    note = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")


class ProcessTemplateCreateSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=128)
    description = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")
    customer_scope = serializers.ChoiceField(choices=RehearsalCustomerScope.choices)
    auto_advance = serializers.BooleanField(default=False)
    steps = serializers.ListField(child=serializers.DictField(), min_length=1, max_length=20)

    def validate_steps(self, value):
        normalized = []
        seen_codes = set()
        for index, item in enumerate(value, start=1):
            code = str(item.get("code", "")).strip().upper()
            name = str(item.get("name", "")).strip()
            if not code or not name:
                raise serializers.ValidationError(f"第 {index} 个步骤缺少 code 或 name")
            if code in seen_codes:
                raise serializers.ValidationError(f"步骤编号 {code} 重复")
            try:
                planned_minutes = int(item.get("planned_minutes", 30))
            except (TypeError, ValueError) as exc:
                raise serializers.ValidationError(f"第 {index} 个步骤计划时长必须为整数") from exc
            if not 1 <= planned_minutes <= 10080:
                raise serializers.ValidationError(f"第 {index} 个步骤计划时长应在 1 至 10080 分钟之间")
            seen_codes.add(code)
            normalized.append(
                {
                    "code": code[:64],
                    "name": name[:128],
                    "description": str(item.get("description", "")).strip()[:500],
                    "owner_role": str(item.get("owner_role", "处置人员")).strip()[:64] or "处置人员",
                    "planned_minutes": planned_minutes,
                }
            )
        return normalized


class ProcessRunCreateSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=160)
    template_id = serializers.UUIDField()
    name = serializers.CharField(required=False, allow_blank=True, max_length=128, default="")
    auto_advance = serializers.BooleanField(required=False, allow_null=True, default=None)


class ProcessRunOperateSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=ProcessRunAction.choices)
    note = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")


def normalize_scene_steps(value):
    normalized = []
    seen_codes = set()
    for index, item in enumerate(value, start=1):
        code = str(item.get("code", "")).strip().upper()
        name = str(item.get("name", "")).strip()
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", code):
            raise serializers.ValidationError(f"第 {index} 个步骤 code 需以字母开头且只含大写字母、数字或下划线")
        if not name:
            raise serializers.ValidationError(f"第 {index} 个步骤缺少 name")
        if code in seen_codes:
            raise serializers.ValidationError(f"步骤编号 {code} 重复")
        seen_codes.add(code)
        normalized.append(
            {
                "code": code,
                "name": name[:128],
                "description": str(item.get("description", "")).strip()[:500],
                "expected_result": str(item.get("expected_result", "")).strip()[:500],
            }
        )
    return normalized


class SceneScriptCreateSerializer(serializers.Serializer):
    scenario_id = serializers.UUIDField()
    code = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=128)
    description = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")
    steps = serializers.ListField(child=serializers.DictField(), min_length=1, max_length=20)

    def validate_steps(self, value):
        return normalize_scene_steps(value)


class SceneRunCreateSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=160)
    script_id = serializers.UUIDField()
    name = serializers.CharField(required=False, allow_blank=True, max_length=128, default="")
    complaint_batch_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, max_length=10, default=list
    )
    data_batch_ids = serializers.ListField(child=serializers.UUIDField(), required=False, max_length=10, default=list)
    process_run_ids = serializers.ListField(child=serializers.UUIDField(), required=False, max_length=10, default=list)

    def validate(self, attrs):
        if not any(attrs.get(field) for field in ("complaint_batch_ids", "data_batch_ids", "process_run_ids")):
            raise serializers.ValidationError("至少选择一个申告批次、模拟数据批次或处置流程作为场景注入数据")
        return attrs


class SceneRunOperateSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=SceneRunAction.choices)
    note = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")
    output = serializers.JSONField(required=False, default=dict)

    def validate_output(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("步骤输出必须为对象")
        return value


class SceneLibraryCreateSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=160)
    scenario_id = serializers.UUIDField()
    script_id = serializers.UUIDField()
    code = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=128)
    description = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")
    default_instance_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    process_template_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    data_model_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    visibility = serializers.ChoiceField(
        choices=SceneLibraryVisibility.choices,
        default=SceneLibraryVisibility.WORKSPACE,
    )
    permission_roles = serializers.ListField(
        child=serializers.CharField(max_length=64),
        required=False,
        allow_empty=True,
        default=list,
    )
    configuration = serializers.JSONField(required=False, default=dict)

    def validate_permission_roles(self, value):
        roles = [str(item).strip().upper() for item in value if str(item).strip()]
        return list(dict.fromkeys(roles))

    def validate_configuration(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("场景库配置必须为对象")
        return value


class SceneLibraryCloneSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=160)
    name = serializers.CharField(required=False, allow_blank=True, max_length=128, default="")
    description = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")
    default_instance_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    process_template_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    data_model_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    visibility = serializers.ChoiceField(
        choices=SceneLibraryVisibility.choices,
        required=False,
        allow_blank=False,
    )
    permission_roles = serializers.ListField(
        child=serializers.CharField(max_length=64),
        required=False,
        allow_empty=True,
    )
    steps = serializers.ListField(child=serializers.DictField(), required=False, min_length=1, max_length=20)
    configuration = serializers.JSONField(required=False)
    note = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")

    def validate_permission_roles(self, value):
        roles = [str(item).strip().upper() for item in value if str(item).strip()]
        return list(dict.fromkeys(roles))

    def validate_steps(self, value):
        return normalize_scene_steps(value)

    def validate_configuration(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("场景库配置必须为对象")
        return value


class SceneLibraryOperateSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=[
            (SceneLibraryAction.PUBLISHED, SceneLibraryAction.PUBLISHED.label),
            (SceneLibraryAction.ARCHIVED, SceneLibraryAction.ARCHIVED.label),
        ]
    )
    note = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")


class SceneLibraryRunSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=160)
    instance_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    name = serializers.CharField(required=False, allow_blank=True, max_length=128, default="")
    include_latest_complaint_batch = serializers.BooleanField(required=False, default=True)
    include_latest_data_batch = serializers.BooleanField(required=False, default=True)
    include_latest_process_run = serializers.BooleanField(required=False, default=True)


class WorkOrderCreateSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=160)
    title = serializers.CharField(max_length=160)
    description = serializers.CharField(required=False, allow_blank=True, max_length=1000, default="")
    priority = serializers.ChoiceField(choices=WorkOrderPriority.choices, default=WorkOrderPriority.MEDIUM)
    assignee = serializers.CharField(required=False, allow_blank=True, max_length=128, default="")


class WorkOrderOperateSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=WorkOrderAction.choices)
    note = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")
    resolution = serializers.CharField(required=False, allow_blank=True, max_length=1000, default="")
    assignee = serializers.CharField(required=False, allow_blank=True, max_length=128, default="")


def normalize_alert_rules(value):
    normalized = []
    seen_codes = set()
    for index, item in enumerate(value, start=1):
        code = str(item.get("code", "")).strip().upper()
        name = str(item.get("name", "")).strip()
        metric_code = str(item.get("metric_code", "")).strip().upper()
        operator = str(item.get("operator", "GT")).strip().upper()
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", code):
            raise serializers.ValidationError(f"第 {index} 条告警规则 code 格式不正确")
        if code in seen_codes:
            raise serializers.ValidationError(f"告警规则编号 {code} 重复")
        if not name or not re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", metric_code):
            raise serializers.ValidationError(f"第 {index} 条告警规则缺少名称或指标编号")
        if operator not in {"GT", "GTE", "LT", "LTE", "EQ"}:
            raise serializers.ValidationError(f"第 {index} 条告警规则比较符不支持")
        try:
            threshold = float(item.get("threshold"))
        except (TypeError, ValueError) as exc:
            raise serializers.ValidationError(f"第 {index} 条告警规则阈值格式不正确") from exc
        if not math.isfinite(threshold):
            raise serializers.ValidationError(f"第 {index} 条告警规则阈值必须为有限数值")
        seen_codes.add(code)
        normalized.append(
            {
                "code": code,
                "name": name[:128],
                "metric_code": metric_code,
                "metric_name": str(item.get("metric_name", "")).strip()[:128] or name[:128],
                "operator": operator,
                "threshold": threshold,
                "unit": str(item.get("unit", "")).strip()[:24],
                "resource_type": str(item.get("resource_type", "网络设备")).strip()[:64] or "网络设备",
            }
        )
    return normalized


class AlertTemplateCreateSerializer(serializers.Serializer):
    scenario_id = serializers.UUIDField()
    code = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=128)
    description = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")
    default_severity = serializers.ChoiceField(choices=AlertSeverity.choices, default=AlertSeverity.HIGH)
    rules = serializers.ListField(child=serializers.DictField(), min_length=1, max_length=20)

    def validate_rules(self, value):
        return normalize_alert_rules(value)


class AlertCreateSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=160)
    template_id = serializers.UUIDField()
    rule_code = serializers.CharField(required=False, allow_blank=True, max_length=64, default="")
    scene_run_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    data_batch_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    title = serializers.CharField(required=False, allow_blank=True, max_length=160, default="")
    description = serializers.CharField(required=False, allow_blank=True, max_length=1000, default="")
    severity = serializers.ChoiceField(choices=AlertSeverity.choices, required=False, allow_null=True, default=None)
    source_system = serializers.CharField(required=False, allow_blank=True, max_length=64, default="预演模拟器")
    resource_type = serializers.CharField(required=False, allow_blank=True, max_length=64, default="")
    resource_id = serializers.CharField(required=False, allow_blank=True, max_length=128, default="")
    resource_name = serializers.CharField(required=False, allow_blank=True, max_length=160, default="")
    metric_code = serializers.CharField(required=False, allow_blank=True, max_length=64, default="")
    metric_name = serializers.CharField(required=False, allow_blank=True, max_length=128, default="")
    metric_value = serializers.FloatField(required=False, allow_null=True, default=None)
    threshold = serializers.FloatField(required=False, allow_null=True, default=None)
    occurred_at = serializers.DateTimeField(required=False, default=timezone.now)
    context = serializers.JSONField(required=False, default=dict)

    def validate_context(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("告警上下文必须为对象")
        return value


class AlertOperateSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=AlertAction.choices)
    note = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")
    event_at = serializers.DateTimeField(required=False, default=timezone.now)
    metric_value = serializers.FloatField(required=False, allow_null=True, default=None)
    detail = serializers.JSONField(required=False, default=dict)

    def validate_detail(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("告警操作详情必须为对象")
        return value


def normalize_data_rules(value):
    normalized = []
    seen_codes = set()
    for index, item in enumerate(value, start=1):
        code = str(item.get("code", "")).strip().upper()
        name = str(item.get("name", "")).strip()
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{0,31}", code):
            raise serializers.ValidationError(f"第 {index} 个字段 code 需以字母开头且只含大写字母、数字或下划线")
        if not name:
            raise serializers.ValidationError(f"第 {index} 个字段缺少 name")
        if code in seen_codes:
            raise serializers.ValidationError(f"字段编号 {code} 重复")
        try:
            minimum = float(item.get("min_value"))
            maximum = float(item.get("max_value"))
            start = float(item.get("start_value", minimum))
            end = float(item.get("end_value", maximum))
            decimals = int(item.get("decimals", 1))
        except (TypeError, ValueError) as exc:
            raise serializers.ValidationError(f"第 {index} 个字段的数值范围或精度格式不正确") from exc
        if not all(math.isfinite(number) for number in (minimum, maximum, start, end)):
            raise serializers.ValidationError(f"第 {index} 个字段只能使用有限数值")
        if minimum >= maximum:
            raise serializers.ValidationError(f"第 {index} 个字段的最小值必须小于最大值")
        if not minimum <= start <= maximum or not minimum <= end <= maximum:
            raise serializers.ValidationError(f"第 {index} 个字段的起止值必须位于最小值和最大值之间")
        if not 0 <= decimals <= 4:
            raise serializers.ValidationError(f"第 {index} 个字段的小数位应在 0 至 4 之间")
        distribution = str(item.get("distribution", DataDistribution.LINEAR)).upper()
        if distribution not in DataDistribution.values:
            raise serializers.ValidationError(f"第 {index} 个字段的分布类型不受支持")
        seen_codes.add(code)
        normalized.append(
            {
                "code": code,
                "name": name[:64],
                "unit": str(item.get("unit", "")).strip()[:16],
                "min_value": minimum,
                "max_value": maximum,
                "start_value": start,
                "end_value": end,
                "distribution": distribution,
                "decimals": decimals,
            }
        )
    return normalized


class DataTemplateCreateSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=128)
    description = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")
    kind = serializers.ChoiceField(choices=DataSimulationKind.choices)
    default_rules = serializers.ListField(child=serializers.DictField(), min_length=1, max_length=8)
    default_tags = serializers.ListField(
        child=serializers.CharField(max_length=24),
        required=False,
        max_length=8,
        default=list,
    )

    def validate_default_rules(self, value):
        return normalize_data_rules(value)

    def validate_default_tags(self, value):
        return list(dict.fromkeys(item.strip() for item in value if item.strip()))


class DataSimulationGenerateSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=160)
    template_id = serializers.UUIDField()
    name = serializers.CharField(required=False, allow_blank=True, max_length=128, default="")
    count = serializers.IntegerField(min_value=3, max_value=500)
    start_at = serializers.DateTimeField()
    interval_minutes = serializers.IntegerField(min_value=1, max_value=1440, default=5)
    rules = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        min_length=1,
        max_length=8,
    )
    tags = serializers.ListField(
        child=serializers.CharField(max_length=24),
        required=False,
        max_length=8,
        default=list,
    )

    def validate_rules(self, value):
        return normalize_data_rules(value)

    def validate_tags(self, value):
        return list(dict.fromkeys(item.strip() for item in value if item.strip()))


class DataModelBuildSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=160)
    name = serializers.CharField(required=False, allow_blank=True, max_length=128, default="")
    description = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")
    build_strategy = serializers.ChoiceField(
        choices=DataModelBuildStrategy.choices,
        default=DataModelBuildStrategy.FULL_INSTANCE,
    )
    transformer_code = serializers.CharField(required=False, allow_blank=True, max_length=64, default="CANONICAL_V1")
    scene_run_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    source_scope = serializers.DictField(required=False, default=dict)

    def validate_transformer_code(self, value):
        code = (value or "CANONICAL_V1").strip().upper()
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", code):
            raise serializers.ValidationError("转换器编号需以字母开头且只含大写字母、数字或下划线")
        return code


class DataModelLoadSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=160)
    note = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")
    transformer_code = serializers.CharField(required=False, allow_blank=True, max_length=64, default="")
    source_scope = serializers.DictField(required=False, default=dict)

    def validate_transformer_code(self, value):
        if not value:
            return ""
        code = value.strip().upper()
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", code):
            raise serializers.ValidationError("转换器编号需以字母开头且只含大写字母、数字或下划线")
        return code


TRACEBACK_KIND_CHOICES = (
    ("COMPLAINT", "客户申告"),
    ("METRIC", "指标趋势"),
    ("SENTIMENT", "舆情趋势"),
    ("PROCESS", "处置操作"),
    ("SCENE", "场景执行"),
    ("ALERT", "模拟告警"),
    ("WORK_ORDER", "人工工单"),
)


class TracebackCreateSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=160)
    name = serializers.CharField(required=False, allow_blank=True, max_length=128, default="")
    description = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")
    scope = serializers.ChoiceField(choices=TracebackScope.choices, default=TracebackScope.FULL_INSTANCE)
    scene_run_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    data_model_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    kind_scope = serializers.ListField(
        child=serializers.ChoiceField(choices=TRACEBACK_KIND_CHOICES),
        required=False,
        allow_empty=True,
        max_length=7,
        default=list,
    )
    window_start = serializers.DateTimeField(required=False, allow_null=True, default=None)
    window_end = serializers.DateTimeField(required=False, allow_null=True, default=None)

    def validate_kind_scope(self, value):
        return list(dict.fromkeys(value or []))

    def validate(self, attrs):
        window_start = attrs.get("window_start")
        window_end = attrs.get("window_end")
        if window_start and window_end and window_start > window_end:
            raise serializers.ValidationError("回溯开始时间不能晚于结束时间")
        return attrs


class SceneReplayCreateSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=160)
    name = serializers.CharField(required=False, allow_blank=True, max_length=128, default="")
    description = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")
    scene_run_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    window_start = serializers.DateTimeField(required=False, allow_null=True, default=None)
    window_end = serializers.DateTimeField(required=False, allow_null=True, default=None)

    def validate(self, attrs):
        window_start = attrs.get("window_start")
        window_end = attrs.get("window_end")
        if window_start and window_end and window_start > window_end:
            raise serializers.ValidationError("回放开始时间不能晚于结束时间")
        return attrs


def normalize_fault_report_attachments(value):
    normalized = []
    seen_references = set()
    for index, item in enumerate(value or [], start=1):
        if not isinstance(item, dict):
            raise serializers.ValidationError(f"第 {index} 个附件引用必须为对象")
        reference_id = str(item.get("reference_id") or "").strip()
        file_name = str(item.get("file_name") or "").strip()
        if not reference_id or not file_name:
            raise serializers.ValidationError(f"第 {index} 个附件缺少引用编号或文件名")
        if reference_id in seen_references:
            raise serializers.ValidationError(f"附件引用编号重复：{reference_id}")
        try:
            file_size = int(item.get("file_size") or 0)
        except (TypeError, ValueError) as exc:
            raise serializers.ValidationError(f"第 {index} 个附件大小必须为整数") from exc
        if file_size < 0 or file_size > 50 * 1024 * 1024:
            raise serializers.ValidationError(f"第 {index} 个附件大小必须在 0～50MB 之间")
        seen_references.add(reference_id)
        normalized.append(
            {
                "reference_id": reference_id[:160],
                "file_name": file_name[:255],
                "content_type": str(item.get("content_type") or "application/octet-stream")[:128],
                "file_size": file_size,
                "note": str(item.get("note") or "")[:500],
            }
        )
    return normalized


class FaultReportTemplateCreateSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=160)
    scenario_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    code = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=128)
    description = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")
    default_level = serializers.ChoiceField(
        choices=FaultReportLevel.choices,
        default=FaultReportLevel.LEVEL_3,
    )
    stage_definitions = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        max_length=12,
    )
    required_fields = serializers.ListField(
        child=serializers.CharField(max_length=64),
        required=False,
        allow_empty=True,
        max_length=20,
        default=list,
    )

    def validate_code(self, value):
        normalized = value.strip().upper()
        if not re.fullmatch(r"[A-Z0-9_-]+", normalized):
            raise serializers.ValidationError("模板编号仅支持大写字母、数字、下划线和中划线")
        return normalized

    def validate_stage_definitions(self, value):
        normalized = []
        seen_codes = set()
        for index, item in enumerate(value, start=1):
            code = str(item.get("code") or "").strip().upper()
            name = str(item.get("name") or "").strip()
            owner_role = str(item.get("owner_role") or "").strip()
            if not code or not name or not owner_role:
                raise serializers.ValidationError(f"第 {index} 个上报阶段缺少编号、名称或责任角色")
            if not re.fullmatch(r"[A-Z0-9_-]+", code):
                raise serializers.ValidationError(f"第 {index} 个上报阶段编号格式不正确")
            if code in seen_codes:
                raise serializers.ValidationError(f"上报阶段编号重复：{code}")
            try:
                duration_minutes = int(item.get("duration_minutes") or 0)
            except (TypeError, ValueError) as exc:
                raise serializers.ValidationError(f"第 {index} 个阶段时限必须为整数") from exc
            if duration_minutes < 1 or duration_minutes > 1440:
                raise serializers.ValidationError(f"第 {index} 个阶段时限必须在 1～1440 分钟之间")
            seen_codes.add(code)
            normalized.append(
                {
                    "sequence_no": index,
                    "code": code,
                    "name": name[:128],
                    "duration_minutes": duration_minutes,
                    "owner_role": owner_role[:128],
                    "required_fields": list(dict.fromkeys(item.get("required_fields") or [])),
                }
            )
        return normalized

    def validate_required_fields(self, value):
        return list(dict.fromkeys(item.strip() for item in value if item.strip()))


class FaultReportCreateSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=160)
    template_id = serializers.UUIDField()
    scene_run_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    title = serializers.CharField(max_length=160)
    description = serializers.CharField(required=False, allow_blank=True, max_length=1000, default="")
    impact_scope = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")
    level = serializers.ChoiceField(choices=FaultReportLevel.choices, required=False, allow_null=True, default=None)
    occurred_at = serializers.DateTimeField(required=False, default=timezone.now)
    attachments = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True,
        max_length=20,
        default=list,
    )

    def validate_attachments(self, value):
        return normalize_fault_report_attachments(value)


class FaultReportOperateSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=[choice for choice in FaultReportAction.choices if choice[0] != FaultReportAction.CREATED]
    )
    note = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")
    level = serializers.ChoiceField(choices=FaultReportLevel.choices, required=False, allow_null=True, default=None)
    attachments = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True,
        max_length=20,
        default=list,
    )
    event_at = serializers.DateTimeField(required=False, default=timezone.now)

    def validate_attachments(self, value):
        return normalize_fault_report_attachments(value)


class AuxiliarySimulationCreateSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=160)
    name = serializers.CharField(required=False, allow_blank=True, max_length=160, default="")
    seed = serializers.IntegerField(min_value=0, max_value=4294967295)
    duration_minutes = serializers.IntegerField(min_value=5, max_value=720, default=60)
    factors = serializers.ListField(child=serializers.DictField(), min_length=1, max_length=12)

    def validate_factors(self, value):
        catalog = {item["code"]: item for item in RANDOM_FACTOR_CATALOG}
        normalized = []
        seen = set()
        for index, item in enumerate(value, start=1):
            code = str(item.get("code") or "").strip().upper()
            definition = catalog.get(code)
            if definition is None:
                raise serializers.ValidationError(f"第 {index} 个随机因子不在支持目录中")
            if code in seen:
                raise serializers.ValidationError(f"随机因子重复：{code}")
            distribution = str(item.get("distribution") or definition["distribution"]).upper()
            if distribution not in RandomFactorDistribution.values:
                raise serializers.ValidationError(f"第 {index} 个随机因子的分布规则不支持")
            try:
                minimum = float(item.get("min_value", definition["min_value"]))
                maximum = float(item.get("max_value", definition["max_value"]))
                probability = float(item.get("trigger_probability", definition["trigger_probability"]))
            except (TypeError, ValueError) as exc:
                raise serializers.ValidationError(f"第 {index} 个随机因子参数必须为数值") from exc
            if not all(math.isfinite(number) for number in (minimum, maximum, probability)):
                raise serializers.ValidationError(f"第 {index} 个随机因子参数必须为有限数值")
            if minimum < 0 or maximum <= minimum:
                raise serializers.ValidationError(f"第 {index} 个随机因子取值范围无效")
            if not 0 <= probability <= 1:
                raise serializers.ValidationError(f"第 {index} 个随机因子触发概率应在 0～1 之间")
            seen.add(code)
            normalized.append(
                {
                    **definition,
                    "min_value": minimum,
                    "max_value": maximum,
                    "distribution": distribution,
                    "trigger_probability": probability,
                }
            )
        return normalized


class CapabilityMockCreateSerializer(serializers.Serializer):
    scenario_id = serializers.UUIDField()
    code = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=128)
    description = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")
    kind = serializers.ChoiceField(choices=CapabilityMockKind.choices)
    method = serializers.CharField(required=False, max_length=12, default="POST")
    endpoint = serializers.CharField(max_length=255)
    request_schema = serializers.JSONField(required=False, default=dict)
    response_template = serializers.JSONField(required=False, default=dict)
    failure_template = serializers.JSONField(required=False, default=dict)
    default_status = serializers.ChoiceField(
        choices=CapabilityCallStatus.choices,
        default=CapabilityCallStatus.SUCCEEDED,
    )
    default_latency_ms = serializers.IntegerField(min_value=0, max_value=120000, default=120)

    def validate_code(self, value):
        code = value.strip().upper()
        if not re.fullmatch(r"[A-Z][A-Z0-9-]{0,63}", code):
            raise serializers.ValidationError("能力编号需以字母开头且只含大写字母、数字或短横线")
        return code

    def validate_method(self, value):
        method = value.strip().upper()
        if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
            raise serializers.ValidationError("仅支持 GET、POST、PUT、PATCH 或 DELETE")
        return method

    def validate(self, attrs):
        if not isinstance(attrs.get("request_schema"), dict):
            raise serializers.ValidationError("请求 Schema 必须是 JSON 对象")
        if not isinstance(attrs.get("response_template"), dict):
            raise serializers.ValidationError("成功响应模板必须是 JSON 对象")
        if not isinstance(attrs.get("failure_template"), dict):
            raise serializers.ValidationError("失败响应模板必须是 JSON 对象")
        return attrs


class CapabilityCallSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=160)
    capability_id = serializers.UUIDField()
    request_payload = serializers.JSONField(required=False, default=dict)
    expected_status = serializers.ChoiceField(
        choices=CapabilityCallStatus.choices,
        required=False,
        allow_null=True,
        default=None,
    )
    latency_ms = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=120000, default=None)
    warroom_group = serializers.CharField(required=False, allow_blank=True, max_length=64, default="默认战情室")

    def validate_request_payload(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("请求参数必须是 JSON 对象")
        return value


class CapabilityReplaySerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=160)
    expected_status = serializers.ChoiceField(
        choices=CapabilityCallStatus.choices,
        required=False,
        allow_null=True,
        default=None,
    )
    latency_ms = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=120000, default=None)
    warroom_group = serializers.CharField(required=False, allow_blank=True, max_length=64, default="")


class FaultConfigurationCreateSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=160)
    scenario_id = serializers.UUIDField()
    code = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=128)
    description = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")
    alert_rules = serializers.JSONField(required=False, default=list)
    timeout_policy = serializers.JSONField(required=False, default=dict)
    active_window = serializers.JSONField(required=False, default=dict)
    topology_snapshot = serializers.JSONField(required=False, default=dict)
    emergency_plan = serializers.JSONField(required=False, default=dict)

    def validate_code(self, value):
        code = value.strip().upper()
        if not re.fullmatch(r"[A-Z][A-Z0-9-]{0,63}", code):
            raise serializers.ValidationError("配置编号需以字母开头且只含大写字母、数字或短横线")
        return code

    def validate(self, attrs):
        expected = {
            "alert_rules": list,
            "timeout_policy": dict,
            "active_window": dict,
            "topology_snapshot": dict,
            "emergency_plan": dict,
        }
        for field, value_type in expected.items():
            if not isinstance(attrs.get(field), value_type):
                raise serializers.ValidationError({field: "配置 JSON 结构不正确"})
        return attrs


class FaultConfigurationCloneSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=160)
    name = serializers.CharField(required=False, allow_blank=True, max_length=128, default="")
    description = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")
    alert_rules = serializers.JSONField(required=False)
    timeout_policy = serializers.JSONField(required=False)
    active_window = serializers.JSONField(required=False)
    topology_snapshot = serializers.JSONField(required=False)
    emergency_plan = serializers.JSONField(required=False)
    note = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")

    def validate(self, attrs):
        expected = {
            "alert_rules": list,
            "timeout_policy": dict,
            "active_window": dict,
            "topology_snapshot": dict,
            "emergency_plan": dict,
        }
        for field, value_type in expected.items():
            if field in attrs and not isinstance(attrs[field], value_type):
                raise serializers.ValidationError({field: "配置 JSON 结构不正确"})
        return attrs


class FaultConfigurationNoteSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")


class FaultConfigurationApplySerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=160)
    configuration_id = serializers.UUIDField()
    note = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")


def serialize_scenario(row):
    return {
        "id": str(row.id),
        "code": row.code,
        "name": row.name,
        "description": row.description,
        "customer_scope": row.customer_scope,
        "customer_scope_label": row.get_customer_scope_display(),
        "version": row.version,
        "status": row.status,
        "status_label": row.get_status_display(),
        "configuration": row.configuration,
        "create_time": row.create_time,
        "update_time": row.update_time,
    }


def serialize_template(row):
    return {
        "id": str(row.id),
        "code": row.code,
        "name": row.name,
        "customer_type": row.customer_type,
        "customer_type_label": row.get_customer_type_display(),
        "version": row.version,
        "enabled": row.enabled,
        "profile_schema": row.profile_schema,
        "complaint_schema": row.complaint_schema,
        "categories": row.categories,
        "content_patterns": row.content_patterns,
        "update_time": row.update_time,
    }


def serialize_batch(row):
    return {
        "id": str(row.id),
        "instance_id": str(row.instance_id),
        "template_id": str(row.template_id) if row.template_id else None,
        "template_name": row.template.name if row.template_id else "人工导入",
        "request_id": row.request_id,
        "source": row.source,
        "source_label": row.get_source_display(),
        "status": row.status,
        "status_label": row.get_status_display(),
        "version": row.version,
        "filename": row.filename,
        "total_count": row.total_count,
        "valid_count": row.valid_count,
        "invalid_count": row.invalid_count,
        "time_start": row.time_start,
        "time_end": row.time_end,
        "error_summary": row.error_summary,
        "create_time": row.create_time,
    }


def serialize_complaint(row):
    return {
        "id": str(row.id),
        "instance_id": str(row.instance_id),
        "batch_id": str(row.batch_id),
        "sequence_no": row.sequence_no,
        "source": row.batch.source,
        "source_label": row.batch.get_source_display(),
        "customer_type": row.customer_type,
        "customer_type_label": row.get_customer_type_display(),
        "customer_ref": row.customer_ref,
        "customer_name": row.customer_name,
        "contact_masked": row.contact_masked,
        "customer_segment": row.customer_segment,
        "occurred_at": row.occurred_at,
        "region": row.region,
        "channel": row.channel,
        "category": row.category,
        "severity": row.severity,
        "severity_label": row.get_severity_display(),
        "status": row.status,
        "status_label": row.get_status_display(),
        "title": row.title,
        "content": row.content,
        "validation_status": row.validation_status,
        "validation_status_label": row.get_validation_status_display(),
        "validation_errors": row.validation_errors,
    }


def serialize_event(row):
    return {
        "id": str(row.id),
        "sequence_no": row.sequence_no,
        "event_type": row.event_type,
        "event_type_label": row.get_event_type_display(),
        "previous_status": row.previous_status,
        "previous_status_label": row.get_previous_status_display(),
        "current_status": row.current_status,
        "current_status_label": row.get_current_status_display(),
        "detail": row.detail,
        "operator_name": row.operator.nick_name if row.operator_id else "系统",
        "create_time": row.create_time,
    }


def serialize_instance(row, *, include_detail=False):
    data = {
        "id": str(row.id),
        "scenario_id": str(row.scenario_id),
        "scenario_name": row.scenario.name,
        "request_id": row.request_id,
        "code": row.code,
        "name": row.name,
        "status": row.status,
        "status_label": row.get_status_display(),
        "planned_start_at": row.planned_start_at,
        "started_at": row.started_at,
        "completed_at": row.completed_at,
        "fault_configuration_id": str(row.fault_configuration_id) if row.fault_configuration_id else None,
        "fault_configuration_name": row.fault_configuration.name if row.fault_configuration_id else "",
        "fault_configuration_version": row.fault_configuration.version if row.fault_configuration_id else None,
        "fault_configuration_snapshot": row.fault_configuration_snapshot,
        "parameters": row.parameters,
        "summary": row.summary,
        "complaint_count": getattr(row, "complaint_count", 0),
        "invalid_count": getattr(row, "invalid_count", 0),
        "batch_count": getattr(row, "batch_count", 0),
        "data_batch_count": getattr(row, "data_batch_count", 0),
        "data_model_count": getattr(row, "data_model_count", 0),
        "traceback_count": getattr(row, "traceback_count", 0),
        "scene_replay_count": getattr(row, "scene_replay_count", 0),
        "fault_report_count": getattr(row, "fault_report_count", 0),
        "auxiliary_simulation_count": getattr(row, "auxiliary_simulation_count", 0),
        "scene_library_count": getattr(row, "scene_library_count", 0),
        "scene_run_count": getattr(row, "scene_run_count", 0),
        "alert_count": getattr(row, "alert_count", 0),
        "capability_call_count": getattr(row, "capability_call_count", 0),
        "create_time": row.create_time,
        "update_time": row.update_time,
    }
    if include_detail:
        data["batches"] = [serialize_batch(item) for item in row.batches.all()]
        data["events"] = [serialize_event(item) for item in row.events.all()]
        data["process_runs"] = [serialize_process_run(item) for item in row.process_runs.all()]
        data["data_batches"] = [serialize_data_batch(item) for item in row.data_batches.all()]
        data["data_models"] = [serialize_data_model(item) for item in row.data_models.all()]
        data["tracebacks"] = [serialize_traceback_snapshot(item) for item in row.traceback_snapshots.all()]
        data["scene_replays"] = [serialize_scene_replay(item) for item in row.scene_replays.all()]
        data["fault_reports"] = [serialize_fault_report(item) for item in row.fault_reports.all()]
        data["auxiliary_simulations"] = [
            serialize_auxiliary_simulation(item) for item in row.auxiliary_simulations.all()
        ]
        data["scene_libraries"] = [serialize_scene_library(item) for item in row.scene_libraries.all()]
        data["scene_runs"] = [serialize_scene_run(item) for item in row.scene_runs.all()]
        data["alerts"] = [serialize_alert(item) for item in row.alerts.all()]
        data["capability_calls"] = [serialize_capability_call(item) for item in row.capability_calls.all()]
        data["fault_configuration"] = (
            serialize_fault_configuration(row.fault_configuration) if row.fault_configuration_id else None
        )
    return data


def serialize_process_template(row):
    return {
        "id": str(row.id),
        "code": row.code,
        "name": row.name,
        "description": row.description,
        "customer_scope": row.customer_scope,
        "customer_scope_label": row.get_customer_scope_display(),
        "version": row.version,
        "enabled": row.enabled,
        "auto_advance": row.auto_advance,
        "steps": row.steps,
        "step_count": len(row.steps),
        "update_time": row.update_time,
    }


def serialize_process_step(row):
    return {
        "id": str(row.id),
        "sequence_no": row.sequence_no,
        "code": row.code,
        "name": row.name,
        "description": row.description,
        "owner_role": row.owner_role,
        "planned_minutes": row.planned_minutes,
        "status": row.status,
        "status_label": row.get_status_display(),
        "started_at": row.started_at,
        "completed_at": row.completed_at,
        "duration_seconds": row.duration_seconds,
        "note": row.note,
        "output_snapshot": row.output_snapshot,
    }


def serialize_process_event(row):
    action_label = {"GENERATED": "生成流程", **dict(ProcessRunAction.choices)}.get(row.action, row.action)
    return {
        "id": str(row.id),
        "sequence_no": row.sequence_no,
        "action": row.action,
        "action_label": action_label,
        "step_id": str(row.step_id) if row.step_id else None,
        "step_name": row.step.name if row.step_id else "",
        "previous_status": row.previous_status,
        "previous_status_label": dict(ProcessRunStatus.choices).get(row.previous_status, row.previous_status),
        "current_status": row.current_status,
        "current_status_label": dict(ProcessRunStatus.choices).get(row.current_status, row.current_status),
        "detail": row.detail,
        "operator_name": row.operator.nick_name if row.operator_id else "系统",
        "create_time": row.create_time,
    }


def serialize_process_run(row, *, include_detail=False):
    snapshot_steps = row.template_snapshot.get("steps", []) if row.template_snapshot else []
    current_step_name = next(
        (item.get("name", "") for item in snapshot_steps if item.get("code") == row.current_step_code),
        "",
    )
    data = {
        "id": str(row.id),
        "instance_id": str(row.instance_id),
        "instance_code": row.instance.code,
        "instance_name": row.instance.name,
        "template_id": str(row.template_id),
        "template_name": row.template.name,
        "template_version": row.template.version,
        "request_id": row.request_id,
        "code": row.code,
        "name": row.name,
        "status": row.status,
        "status_label": row.get_status_display(),
        "auto_advance": row.auto_advance,
        "current_step_index": row.current_step_index,
        "current_step_code": row.current_step_code,
        "current_step_name": current_step_name,
        "total_steps": row.total_steps,
        "completed_steps": row.completed_steps,
        "progress_percent": row.progress_percent,
        "blocked_reason": row.blocked_reason,
        "started_at": row.started_at,
        "completed_at": row.completed_at,
        "template_snapshot": row.template_snapshot,
        "summary": row.summary,
        "create_time": row.create_time,
        "update_time": row.update_time,
    }
    if include_detail:
        data["steps"] = [serialize_process_step(item) for item in row.steps.all()]
        data["events"] = [serialize_process_event(item) for item in row.events.all()]
    return data


def serialize_data_template(row):
    return {
        "id": str(row.id),
        "code": row.code,
        "name": row.name,
        "description": row.description,
        "kind": row.kind,
        "kind_label": row.get_kind_display(),
        "version": row.version,
        "enabled": row.enabled,
        "default_rules": row.default_rules,
        "default_tags": row.default_tags,
        "field_count": len(row.default_rules),
        "update_time": row.update_time,
    }


def serialize_data_point(row):
    return {
        "id": str(row.id),
        "batch_id": str(row.batch_id),
        "sequence_no": row.sequence_no,
        "occurred_at": row.occurred_at,
        "values": row.values,
        "tags": row.tags,
        "narrative": row.narrative,
    }


def serialize_data_batch(row, *, include_detail=False):
    data = {
        "id": str(row.id),
        "instance_id": str(row.instance_id),
        "instance_code": row.instance.code,
        "instance_name": row.instance.name,
        "template_id": str(row.template_id),
        "template_name": row.template.name,
        "template_version": row.template.version,
        "request_id": row.request_id,
        "code": row.code,
        "name": row.name,
        "kind": row.kind,
        "kind_label": row.get_kind_display(),
        "status": row.status,
        "status_label": row.get_status_display(),
        "version": row.version,
        "point_count": row.point_count,
        "interval_minutes": row.interval_minutes,
        "time_start": row.time_start,
        "time_end": row.time_end,
        "rules_snapshot": row.rules_snapshot,
        "tags": row.tags,
        "summary": row.summary,
        "create_time": row.create_time,
        "update_time": row.update_time,
    }
    if include_detail:
        data["points"] = [serialize_data_point(item) for item in row.points.all()]
    return data


def serialize_data_model_version(row):
    return {
        "id": str(row.id),
        "data_model_id": str(row.data_model_id),
        "version": row.version,
        "build_strategy": row.build_strategy,
        "build_strategy_label": row.get_build_strategy_display(),
        "transformer_code": row.transformer_code,
        "source_counts": row.source_counts,
        "entity_schema": row.entity_schema,
        "snapshot": row.snapshot,
        "quality_report": row.quality_report,
        "lineage": row.lineage,
        "checksum": row.checksum,
        "loaded_at": row.loaded_at,
        "create_time": row.create_time,
        "update_time": row.update_time,
    }


def serialize_data_model_load(row):
    return {
        "id": str(row.id),
        "data_model_id": str(row.data_model_id),
        "version_id": str(row.version_id) if row.version_id else None,
        "version": row.version.version if row.version_id else 0,
        "request_id": row.request_id,
        "status": row.status,
        "status_label": row.get_status_display(),
        "source_counts": row.source_counts,
        "note": row.note,
        "message": row.message,
        "started_at": row.started_at,
        "completed_at": row.completed_at,
        "operator_name": row.operator.nick_name if row.operator_id else "系统",
        "create_time": row.create_time,
    }


def serialize_data_model(row, *, include_detail=False):
    data = {
        "id": str(row.id),
        "instance_id": str(row.instance_id),
        "instance_code": row.instance.code,
        "instance_name": row.instance.name,
        "scenario_id": str(row.scenario_id),
        "scenario_name": row.scenario.name,
        "scene_run_id": str(row.scene_run_id) if row.scene_run_id else None,
        "scene_run_name": row.scene_run.name if row.scene_run_id else "",
        "request_id": row.request_id,
        "code": row.code,
        "name": row.name,
        "description": row.description,
        "build_strategy": row.build_strategy,
        "build_strategy_label": row.get_build_strategy_display(),
        "transformer_code": row.transformer_code,
        "version_count": row.version_count,
        "current_version": row.current_version,
        "quality_status": row.quality_status,
        "quality_status_label": row.get_quality_status_display(),
        "source_scope": row.source_scope,
        "summary": row.summary,
        "lineage": row.lineage,
        "version_total": getattr(row, "version_total", row.version_count),
        "load_total": getattr(row, "load_total", 0),
        "create_time": row.create_time,
        "update_time": row.update_time,
    }
    if include_detail:
        data["versions"] = [serialize_data_model_version(item) for item in row.versions.all()]
        data["loads"] = [serialize_data_model_load(item) for item in row.loads.all()]
    return data


def serialize_traceback_snapshot(row, *, include_detail=False):
    data = {
        "id": str(row.id),
        "instance_id": str(row.instance_id),
        "instance_code": row.instance.code,
        "instance_name": row.instance.name,
        "scenario_id": str(row.scenario_id),
        "scenario_name": row.scenario.name,
        "scene_run_id": str(row.scene_run_id) if row.scene_run_id else None,
        "scene_run_name": row.scene_run.name if row.scene_run_id else "",
        "data_model_id": str(row.data_model_id) if row.data_model_id else None,
        "data_model_name": row.data_model.name if row.data_model_id else "",
        "request_id": row.request_id,
        "code": row.code,
        "name": row.name,
        "description": row.description,
        "scope": row.scope,
        "scope_label": row.get_scope_display(),
        "status": row.status,
        "status_label": row.get_status_display(),
        "kind_scope": row.kind_scope,
        "window_start": row.window_start,
        "window_end": row.window_end,
        "total_events": row.total_events,
        "kind_counts": row.kind_counts,
        "pivot_counts": row.pivot_counts,
        "summary": row.summary,
        "checksum": row.checksum,
        "generated_at": row.generated_at,
        "create_time": row.create_time,
        "update_time": row.update_time,
    }
    if include_detail:
        data["snapshot"] = row.snapshot
        data["items"] = (row.snapshot or {}).get("items", [])
        data["nodes"] = (row.snapshot or {}).get("nodes", [])
        data["transitions"] = (row.snapshot or {}).get("transitions", [])
        data["deltas"] = (row.snapshot or {}).get("deltas", [])
    return data


def serialize_scene_script(row):
    return {
        "id": str(row.id),
        "scenario_id": str(row.scenario_id),
        "scenario_name": row.scenario.name,
        "code": row.code,
        "name": row.name,
        "description": row.description,
        "version": row.version,
        "enabled": row.enabled,
        "steps": row.steps,
        "step_count": len(row.steps),
        "create_time": row.create_time,
        "update_time": row.update_time,
    }


def serialize_scene_library_event(row):
    return {
        "id": str(row.id),
        "sequence_no": row.sequence_no,
        "action": row.action,
        "action_label": row.get_action_display(),
        "previous_status": row.previous_status,
        "previous_status_label": dict(SceneLibraryStatus.choices).get(row.previous_status, row.previous_status),
        "current_status": row.current_status,
        "current_status_label": dict(SceneLibraryStatus.choices).get(row.current_status, row.current_status),
        "detail": row.detail,
        "operator_name": row.operator.nick_name if row.operator_id else "系统",
        "create_time": row.create_time,
    }


def serialize_scene_library(row, *, include_detail=False):
    data = {
        "id": str(row.id),
        "scenario_id": str(row.scenario_id),
        "scenario_name": row.scenario.name,
        "script_id": str(row.script_id),
        "script_code": row.script.code,
        "script_name": row.script.name,
        "script_version": row.script.version,
        "default_instance_id": str(row.default_instance_id) if row.default_instance_id else None,
        "default_instance_code": row.default_instance.code if row.default_instance_id else "",
        "default_instance_name": row.default_instance.name if row.default_instance_id else "",
        "process_template_id": str(row.process_template_id) if row.process_template_id else None,
        "process_template_name": row.process_template.name if row.process_template_id else "",
        "data_model_id": str(row.data_model_id) if row.data_model_id else None,
        "data_model_name": row.data_model.name if row.data_model_id else "",
        "source_library_id": str(row.source_library_id) if row.source_library_id else None,
        "request_id": row.request_id,
        "code": row.code,
        "name": row.name,
        "description": row.description,
        "version": row.version,
        "status": row.status,
        "status_label": row.get_status_display(),
        "visibility": row.visibility,
        "visibility_label": row.get_visibility_display(),
        "permission_roles": row.permission_roles,
        "linked_config": row.linked_config,
        "run_count": row.run_count,
        "last_run_at": row.last_run_at,
        "event_count": getattr(row, "event_count", 0),
        "create_time": row.create_time,
        "update_time": row.update_time,
    }
    if include_detail:
        data["script"] = serialize_scene_script(row.script)
        data["events"] = [serialize_scene_library_event(item) for item in row.events.all()]
        data["scene_runs"] = [serialize_scene_run(item) for item in row.scene_runs.all()]
    return data


def serialize_scene_step(row):
    return {
        "id": str(row.id),
        "sequence_no": row.sequence_no,
        "code": row.code,
        "name": row.name,
        "description": row.description,
        "expected_result": row.expected_result,
        "status": row.status,
        "status_label": row.get_status_display(),
        "started_at": row.started_at,
        "completed_at": row.completed_at,
        "duration_seconds": row.duration_seconds,
        "note": row.note,
        "output_snapshot": row.output_snapshot,
    }


def serialize_scene_event(row):
    action_label = {"CREATED": "创建执行", **dict(SceneRunAction.choices)}.get(row.action, row.action)
    return {
        "id": str(row.id),
        "sequence_no": row.sequence_no,
        "action": row.action,
        "action_label": action_label,
        "step_id": str(row.step_id) if row.step_id else None,
        "step_name": row.step.name if row.step_id else "",
        "previous_status": row.previous_status,
        "previous_status_label": dict(SceneRunStatus.choices).get(row.previous_status, row.previous_status),
        "current_status": row.current_status,
        "current_status_label": dict(SceneRunStatus.choices).get(row.current_status, row.current_status),
        "detail": row.detail,
        "operator_name": row.operator.nick_name if row.operator_id else "系统",
        "create_time": row.create_time,
    }


def serialize_work_order_event(row):
    action_label = {"CREATED": "创建工单", **dict(WorkOrderAction.choices)}.get(row.action, row.action)
    return {
        "id": str(row.id),
        "sequence_no": row.sequence_no,
        "action": row.action,
        "action_label": action_label,
        "previous_status": row.previous_status,
        "previous_status_label": dict(WorkOrderStatus.choices).get(row.previous_status, row.previous_status),
        "current_status": row.current_status,
        "current_status_label": dict(WorkOrderStatus.choices).get(row.current_status, row.current_status),
        "detail": row.detail,
        "operator_name": row.operator.nick_name if row.operator_id else "系统",
        "create_time": row.create_time,
    }


def serialize_work_order(row, *, include_detail=False):
    data = {
        "id": str(row.id),
        "scene_run_id": str(row.scene_run_id),
        "scene_run_code": row.scene_run.code,
        "scene_run_name": row.scene_run.name,
        "request_id": row.request_id,
        "code": row.code,
        "title": row.title,
        "description": row.description,
        "priority": row.priority,
        "priority_label": row.get_priority_display(),
        "status": row.status,
        "status_label": row.get_status_display(),
        "assignee": row.assignee,
        "resolution": row.resolution,
        "accepted_at": row.accepted_at,
        "resolved_at": row.resolved_at,
        "closed_at": row.closed_at,
        "create_time": row.create_time,
        "update_time": row.update_time,
    }
    if include_detail:
        data["events"] = [serialize_work_order_event(item) for item in row.events.all()]
    return data


def serialize_alert_template(row):
    return {
        "id": str(row.id),
        "scenario_id": str(row.scenario_id),
        "scenario_name": row.scenario.name,
        "code": row.code,
        "name": row.name,
        "description": row.description,
        "version": row.version,
        "enabled": row.enabled,
        "default_severity": row.default_severity,
        "default_severity_label": row.get_default_severity_display(),
        "rules": row.rules,
        "rule_count": len(row.rules),
        "create_time": row.create_time,
        "update_time": row.update_time,
    }


def serialize_alert_event(row):
    action_label = {"CREATED": "配置告警", **dict(AlertAction.choices)}.get(row.action, row.action)
    return {
        "id": str(row.id),
        "sequence_no": row.sequence_no,
        "action": row.action,
        "action_label": action_label,
        "previous_status": row.previous_status,
        "previous_status_label": dict(AlertStatus.choices).get(row.previous_status, row.previous_status),
        "current_status": row.current_status,
        "current_status_label": dict(AlertStatus.choices).get(row.current_status, row.current_status),
        "occurred_at": row.occurred_at,
        "detail": row.detail,
        "operator_name": row.operator.nick_name if row.operator_id else "系统",
        "create_time": row.create_time,
    }


def serialize_alert(row, *, include_detail=False):
    duration_seconds = 0
    if row.reported_at:
        end_at = row.recovered_at or timezone.now()
        duration_seconds = max(int((end_at - row.reported_at).total_seconds()), 0)
    data = {
        "id": str(row.id),
        "instance_id": str(row.instance_id),
        "instance_code": row.instance.code,
        "instance_name": row.instance.name,
        "template_id": str(row.template_id),
        "template_name": row.template.name,
        "template_version": row.template.version,
        "scene_run_id": str(row.scene_run_id) if row.scene_run_id else None,
        "scene_run_name": row.scene_run.name if row.scene_run_id else "",
        "data_batch_id": str(row.data_batch_id) if row.data_batch_id else None,
        "data_batch_name": row.data_batch.name if row.data_batch_id else "",
        "request_id": row.request_id,
        "code": row.code,
        "title": row.title,
        "description": row.description,
        "severity": row.severity,
        "severity_label": row.get_severity_display(),
        "status": row.status,
        "status_label": row.get_status_display(),
        "source_system": row.source_system,
        "resource_type": row.resource_type,
        "resource_id": row.resource_id,
        "resource_name": row.resource_name,
        "metric_code": row.metric_code,
        "metric_name": row.metric_name,
        "metric_value": row.metric_value,
        "threshold": row.threshold,
        "occurred_at": row.occurred_at,
        "reported_at": row.reported_at,
        "acknowledged_at": row.acknowledged_at,
        "recovered_at": row.recovered_at,
        "duration_seconds": duration_seconds,
        "template_snapshot": row.template_snapshot,
        "context": row.context,
        "event_count": getattr(row, "event_count", 0),
        "create_time": row.create_time,
        "update_time": row.update_time,
    }
    if include_detail:
        data["events"] = [serialize_alert_event(item) for item in row.events.all()]
    return data


def serialize_capability_mock(row):
    return {
        "id": str(row.id),
        "scenario_id": str(row.scenario_id),
        "scenario_name": row.scenario.name,
        "code": row.code,
        "name": row.name,
        "description": row.description,
        "kind": row.kind,
        "kind_label": row.get_kind_display(),
        "version": row.version,
        "enabled": row.enabled,
        "method": row.method,
        "endpoint": row.endpoint,
        "request_schema": row.request_schema,
        "response_template": row.response_template,
        "failure_template": row.failure_template,
        "default_status": row.default_status,
        "default_status_label": row.get_default_status_display(),
        "default_latency_ms": row.default_latency_ms,
        "create_time": row.create_time,
        "update_time": row.update_time,
    }


def serialize_capability_call(row, *, include_detail=False):
    data = {
        "id": str(row.id),
        "instance_id": str(row.instance_id),
        "instance_code": row.instance.code,
        "instance_name": row.instance.name,
        "capability_id": str(row.capability_id),
        "capability_code": row.capability.code,
        "capability_name": row.capability.name,
        "capability_kind": row.capability.kind,
        "capability_kind_label": row.capability.get_kind_display(),
        "request_id": row.request_id,
        "call_no": row.call_no,
        "status": row.status,
        "status_label": row.get_status_display(),
        "source": row.source,
        "warroom_group": row.warroom_group,
        "http_status": row.http_status,
        "latency_ms": row.latency_ms,
        "error_message": row.error_message,
        "started_at": row.started_at,
        "finished_at": row.finished_at,
        "replay_of_id": str(row.replay_of_id) if row.replay_of_id else None,
        "create_time": row.create_time,
        "update_time": row.update_time,
    }
    if include_detail:
        data["request_payload"] = row.request_payload
        data["response_payload"] = row.response_payload
        data["capability_snapshot"] = row.capability_snapshot
        data["capability"] = serialize_capability_mock(row.capability)
        data["replays"] = [serialize_capability_call(item) for item in row.replays.all()]
    return data


def serialize_fault_configuration_event(row):
    return {
        "id": str(row.id),
        "sequence_no": row.sequence_no,
        "action": row.action,
        "action_label": row.get_action_display(),
        "instance_id": str(row.instance_id) if row.instance_id else None,
        "instance_name": row.instance.name if row.instance_id else "",
        "previous_status": row.previous_status,
        "previous_status_label": dict(FaultConfigurationStatus.choices).get(
            row.previous_status, row.previous_status
        ),
        "current_status": row.current_status,
        "current_status_label": dict(FaultConfigurationStatus.choices).get(
            row.current_status, row.current_status
        ),
        "detail": row.detail,
        "operator_name": row.operator.nick_name if row.operator_id else "系统",
        "create_time": row.create_time,
    }


def serialize_fault_configuration(row, *, include_detail=False):
    topology = row.topology_snapshot or {}
    plan = row.emergency_plan or {}
    data = {
        "id": str(row.id),
        "scenario_id": str(row.scenario_id),
        "scenario_name": row.scenario.name,
        "source_configuration_id": str(row.source_configuration_id) if row.source_configuration_id else None,
        "request_id": row.request_id,
        "code": row.code,
        "name": row.name,
        "description": row.description,
        "version": row.version,
        "status": row.status,
        "status_label": row.get_status_display(),
        "alert_rules": row.alert_rules,
        "timeout_policy": row.timeout_policy,
        "active_window": row.active_window,
        "topology_snapshot": topology,
        "emergency_plan": plan,
        "validation_report": row.validation_report,
        "validated_at": row.validated_at,
        "published_at": row.published_at,
        "alert_rule_count": len(row.alert_rules or []),
        "topology_node_count": len(topology.get("nodes", [])),
        "topology_link_count": len(topology.get("links", [])),
        "plan_step_count": len(plan.get("steps", [])),
        "bound_instance_count": getattr(row, "bound_instance_count", 0),
        "event_count": getattr(row, "event_count", 0),
        "create_time": row.create_time,
        "update_time": row.update_time,
    }
    if include_detail:
        data["events"] = [serialize_fault_configuration_event(item) for item in row.events.all()]
        data["bound_instances"] = [
            {
                "id": str(item.id),
                "code": item.code,
                "name": item.name,
                "status": item.status,
                "status_label": item.get_status_display(),
            }
            for item in row.bound_instances.all()
        ]
    return data


def serialize_scene_replay(row, *, include_detail=False):
    data = {
        "id": str(row.id),
        "instance_id": str(row.instance_id),
        "instance_code": row.instance.code,
        "instance_name": row.instance.name,
        "scene_run_id": str(row.scene_run_id) if row.scene_run_id else None,
        "scene_run_name": row.scene_run.name if row.scene_run_id else "",
        "fault_configuration_id": str(row.fault_configuration_id) if row.fault_configuration_id else None,
        "fault_configuration_name": row.fault_configuration.name if row.fault_configuration_id else "",
        "fault_configuration_version": row.fault_configuration.version if row.fault_configuration_id else None,
        "request_id": row.request_id,
        "code": row.code,
        "name": row.name,
        "description": row.description,
        "status": row.status,
        "status_label": row.get_status_display(),
        "window_start": row.window_start,
        "window_end": row.window_end,
        "traffic_frame_count": len(row.traffic_frames or []),
        "node_trace_count": len(row.node_traces or []),
        "changed_node_count": (row.summary or {}).get("changed_node_count", 0),
        "changed_link_count": (row.summary or {}).get("changed_link_count", 0),
        "average_latency_ms": (row.summary or {}).get("average_latency_ms", 0),
        "summary": row.summary,
        "checksum": row.checksum,
        "generated_at": row.generated_at,
        "create_time": row.create_time,
        "update_time": row.update_time,
    }
    if include_detail:
        data.update(
            {
                "traffic_frames": row.traffic_frames,
                "topology_before": row.topology_before,
                "topology_after": row.topology_after,
                "node_traces": row.node_traces,
                "mirror_comparison": row.mirror_comparison,
            }
        )
    return data


def serialize_fault_report_template(row):
    return {
        "id": str(row.id),
        "scenario_id": str(row.scenario_id) if row.scenario_id else None,
        "scenario_name": row.scenario.name if row.scenario_id else "全部场景",
        "request_id": row.request_id,
        "code": row.code,
        "name": row.name,
        "description": row.description,
        "version": row.version,
        "status": row.status,
        "status_label": row.get_status_display(),
        "default_level": row.default_level,
        "default_level_label": row.get_default_level_display(),
        "stage_definitions": row.stage_definitions,
        "stage_count": len(row.stage_definitions or []),
        "required_fields": row.required_fields,
        "report_count": getattr(row, "report_count", 0),
        "create_time": row.create_time,
        "update_time": row.update_time,
    }


def fault_report_allowed_actions(row):
    if row.status == FaultReportStatus.DRAFT:
        return [FaultReportAction.SUBMITTED, FaultReportAction.ESCALATED, FaultReportAction.ATTACHMENT_ADDED]
    if row.status == FaultReportStatus.REPORTED:
        return [
            FaultReportAction.ACCEPTED,
            FaultReportAction.ESCALATED,
            FaultReportAction.ATTACHMENT_ADDED,
            FaultReportAction.RECOVERED,
        ]
    if row.status == FaultReportStatus.PROCESSING:
        actions = [FaultReportAction.ESCALATED, FaultReportAction.ATTACHMENT_ADDED, FaultReportAction.RECOVERED]
        stages = (row.template_snapshot or {}).get("stage_definitions", [])
        current_index = next(
            (index for index, item in enumerate(stages) if item.get("code") == row.current_stage_code),
            0,
        )
        if current_index < len(stages) - 1:
            actions.insert(0, FaultReportAction.STAGE_ADVANCED)
        return actions
    if row.status == FaultReportStatus.RECOVERED:
        return [FaultReportAction.ATTACHMENT_ADDED, FaultReportAction.CLOSED]
    return []


def serialize_fault_report_event(row):
    return {
        "id": str(row.id),
        "sequence_no": row.sequence_no,
        "action": row.action,
        "action_label": row.get_action_display(),
        "previous_status": row.previous_status,
        "previous_status_label": dict(FaultReportStatus.choices).get(row.previous_status, row.previous_status),
        "current_status": row.current_status,
        "current_status_label": dict(FaultReportStatus.choices).get(row.current_status, row.current_status),
        "previous_stage_code": row.previous_stage_code,
        "current_stage_code": row.current_stage_code,
        "detail": row.detail,
        "operator_name": row.operator.nick_name if row.operator_id else "系统",
        "create_time": row.create_time,
    }


def serialize_fault_report(row, *, include_detail=False):
    stages = (row.template_snapshot or {}).get("stage_definitions", [])
    current_index = next(
        (index for index, item in enumerate(stages) if item.get("code") == row.current_stage_code),
        0,
    )
    active = row.status in (FaultReportStatus.DRAFT, FaultReportStatus.REPORTED, FaultReportStatus.PROCESSING)
    raw_remaining_seconds = int((row.stage_deadline_at - timezone.now()).total_seconds())
    progress_percent = {
        FaultReportStatus.DRAFT: 10,
        FaultReportStatus.REPORTED: 25,
        FaultReportStatus.RECOVERED: 90,
        FaultReportStatus.CLOSED: 100,
    }.get(
        row.status,
        min(80, 35 + round((current_index / max(len(stages) - 1, 1)) * 45)),
    )
    data = {
        "id": str(row.id),
        "instance_id": str(row.instance_id),
        "instance_code": row.instance.code,
        "instance_name": row.instance.name,
        "template_id": str(row.template_id) if row.template_id else None,
        "template_name": row.template.name if row.template_id else (row.template_snapshot or {}).get("name", ""),
        "template_version": (row.template_snapshot or {}).get("version"),
        "scene_run_id": str(row.scene_run_id) if row.scene_run_id else None,
        "scene_run_name": row.scene_run.name if row.scene_run_id else "",
        "request_id": row.request_id,
        "code": row.code,
        "title": row.title,
        "description": row.description,
        "impact_scope": row.impact_scope,
        "level": row.level,
        "level_label": row.get_level_display(),
        "status": row.status,
        "status_label": row.get_status_display(),
        "current_stage_code": row.current_stage_code,
        "current_stage_name": row.current_stage_name,
        "stage_index": current_index + 1,
        "stage_count": len(stages),
        "stage_owner_role": (stages[current_index] or {}).get("owner_role", "") if stages else "",
        "progress_percent": progress_percent,
        "occurred_at": row.occurred_at,
        "reported_at": row.reported_at,
        "accepted_at": row.accepted_at,
        "recovered_at": row.recovered_at,
        "closed_at": row.closed_at,
        "stage_started_at": row.stage_started_at,
        "stage_deadline_at": row.stage_deadline_at,
        "remaining_seconds": max(raw_remaining_seconds, 0) if active else 0,
        "overdue_seconds": abs(min(raw_remaining_seconds, 0)) if active else 0,
        "is_overdue": active and raw_remaining_seconds < 0,
        "attachments": row.attachments,
        "attachment_count": len(row.attachments or []),
        "template_snapshot": row.template_snapshot,
        "summary": row.summary,
        "event_count": getattr(row, "event_count", 0),
        "allowed_actions": fault_report_allowed_actions(row),
        "create_time": row.create_time,
        "update_time": row.update_time,
    }
    if include_detail:
        data["events"] = [serialize_fault_report_event(item) for item in row.events.all()]
    return data


def serialize_auxiliary_simulation(row, *, include_detail=False):
    result = row.result_snapshot or {}
    data = {
        "id": str(row.id),
        "instance_id": str(row.instance_id),
        "instance_code": row.instance.code,
        "instance_name": row.instance.name,
        "scenario_name": row.instance.scenario.name,
        "request_id": row.request_id,
        "code": row.code,
        "name": row.name,
        "seed": row.seed,
        "duration_minutes": row.duration_minutes,
        "status": row.status,
        "status_label": row.get_status_display(),
        "factor_snapshot": row.factor_snapshot,
        "factor_count": len(row.factor_snapshot or []),
        "triggered_factor_count": sum(1 for item in row.factor_snapshot or [] if item.get("triggered")),
        "anomaly_count": len(result.get("anomalies", [])),
        "summary": result.get("summary", {}),
        "statistics": result.get("statistics", []),
        "impact_analysis": result.get("impact_analysis", []),
        "checksum": row.checksum,
        "started_at": row.started_at,
        "completed_at": row.completed_at,
        "create_time": row.create_time,
        "update_time": row.update_time,
    }
    if include_detail:
        data["result_snapshot"] = result
        data["points"] = result.get("points", [])
        data["anomalies"] = result.get("anomalies", [])
        data["key_moments"] = result.get("key_moments", [])
    return data


def serialize_scene_run(row, *, include_detail=False):
    snapshot_steps = row.script_snapshot.get("steps", []) if row.script_snapshot else []
    current_step_name = next(
        (item.get("name", "") for item in snapshot_steps if item.get("code") == row.current_step_code),
        "",
    )
    data = {
        "id": str(row.id),
        "instance_id": str(row.instance_id),
        "instance_code": row.instance.code,
        "instance_name": row.instance.name,
        "script_id": str(row.script_id),
        "script_name": row.script.name,
        "script_version": row.script.version,
        "library_id": str(row.library_id) if row.library_id else None,
        "library_name": row.library.name if row.library_id else "",
        "library_version": row.library.version if row.library_id else None,
        "request_id": row.request_id,
        "code": row.code,
        "name": row.name,
        "status": row.status,
        "status_label": row.get_status_display(),
        "current_step_index": row.current_step_index,
        "current_step_code": row.current_step_code,
        "current_step_name": current_step_name,
        "total_steps": row.total_steps,
        "completed_steps": row.completed_steps,
        "progress_percent": row.progress_percent,
        "script_snapshot": row.script_snapshot,
        "injected_snapshot": row.injected_snapshot,
        "started_at": row.started_at,
        "completed_at": row.completed_at,
        "summary": row.summary,
        "work_order_count": getattr(row, "work_order_count", 0),
        "alert_count": getattr(row, "alert_count", 0),
        "create_time": row.create_time,
        "update_time": row.update_time,
    }
    if include_detail:
        data["steps"] = [serialize_scene_step(item) for item in row.steps.all()]
        data["events"] = [serialize_scene_event(item) for item in row.events.all()]
        data["work_orders"] = [serialize_work_order(item) for item in row.work_orders.all()]
        data["alerts"] = [serialize_alert(item) for item in row.alerts.all()]
    return data


class RehearsalService:
    def __init__(self, workspace_id, user=None):
        self.workspace_id = workspace_id
        self.user = user

    def ensure_default_catalog(self):
        scenario, _ = RehearsalScenario.objects.get_or_create(
            workspace_id=self.workspace_id,
            code="CUSTOMER-COMPLAINT-SIM-V1",
            version=1,
            defaults={
                "name": "客户申告时序预演",
                "description": "统一承载公众与政企客户申告数据生成、导入和时序回放。",
                "customer_scope": RehearsalCustomerScope.MIXED,
                "status": RehearsalScenarioStatus.READY,
                "configuration": {"capability": "X18", "timeline_mode": "SEQUENCE"},
                "created_by": self.user,
            },
        )
        templates = []
        for definition in (PUBLIC_TEMPLATE, ENTERPRISE_TEMPLATE):
            template, _ = RehearsalComplaintTemplate.objects.get_or_create(
                workspace_id=self.workspace_id,
                code=definition["code"],
                version=1,
                defaults={**definition, "created_by": self.user},
            )
            templates.append(template)
        for definition in (PUBLIC_PROCESS_TEMPLATE, ENTERPRISE_PROCESS_TEMPLATE):
            RehearsalProcessTemplate.objects.get_or_create(
                workspace_id=self.workspace_id,
                code=definition["code"],
                version=1,
                defaults={**definition, "created_by": self.user},
            )
        for definition in (NETWORK_METRIC_TEMPLATE, SENTIMENT_TREND_TEMPLATE):
            RehearsalDataTemplate.objects.get_or_create(
                workspace_id=self.workspace_id,
                code=definition["code"],
                version=1,
                defaults={**definition, "created_by": self.user},
            )
        scene_script, _ = RehearsalSceneScript.objects.get_or_create(
            workspace_id=self.workspace_id,
            code=NETWORK_FAULT_SCENE_SCRIPT["code"],
            version=1,
            defaults={
                **NETWORK_FAULT_SCENE_SCRIPT,
                "scenario": scenario,
                "created_by": self.user,
            },
        )
        RehearsalAlertTemplate.objects.get_or_create(
            workspace_id=self.workspace_id,
            code=NETWORK_ALERT_TEMPLATE["code"],
            version=1,
            defaults={
                **NETWORK_ALERT_TEMPLATE,
                "scenario": scenario,
                "created_by": self.user,
            },
        )
        for definition in DEFAULT_CAPABILITY_MOCKS:
            RehearsalCapabilityMock.objects.get_or_create(
                workspace_id=self.workspace_id,
                code=definition["code"],
                version=1,
                defaults={
                    **definition,
                    "scenario": scenario,
                    "created_by": self.user,
                },
            )
        fault_configuration, fault_configuration_created = RehearsalFaultConfiguration.objects.get_or_create(
            workspace_id=self.workspace_id,
            code=DEFAULT_FAULT_CONFIGURATION["code"],
            version=1,
            defaults={
                **DEFAULT_FAULT_CONFIGURATION,
                "scenario": scenario,
                "status": FaultConfigurationStatus.READY,
                "validation_report": {
                    "status": "PASSED",
                    "passed": True,
                    "check_count": 5,
                    "error_count": 0,
                    "errors": [],
                },
                "validated_at": timezone.now(),
                "published_at": timezone.now(),
                "created_by": self.user,
            },
        )
        if fault_configuration_created:
            self._record_fault_configuration_event(
                fault_configuration,
                FaultConfigurationAction.CREATED,
                FaultConfigurationStatus.READY,
                detail={"catalog": True, "version": fault_configuration.version},
            )
        RehearsalFaultReportTemplate.objects.get_or_create(
            workspace_id=self.workspace_id,
            code=DEFAULT_FAULT_REPORT_TEMPLATE["code"],
            version=1,
            defaults={
                **DEFAULT_FAULT_REPORT_TEMPLATE,
                "scenario": scenario,
                "status": FaultReportTemplateStatus.READY,
                "created_by": self.user,
            },
        )
        scene_library, scene_library_created = RehearsalSceneLibrary.objects.get_or_create(
            workspace_id=self.workspace_id,
            code="NETWORK-FAULT-LIB-V1",
            version=1,
            defaults={
                "scenario": scenario,
                "script": scene_script,
                "request_id": "catalog:scene-library:network-fault:v1",
                "name": "网络故障预演场景库",
                "description": "面向网络质量波动的可复用预演场景库，默认绑定网络故障剧本，支持克隆版本和关联实例执行。",
                "status": SceneLibraryStatus.READY,
                "visibility": SceneLibraryVisibility.WORKSPACE,
                "permission_roles": ["WORKSPACE_MANAGE"],
                "linked_config": self._scene_library_linked_config(
                    scene_script,
                    None,
                    None,
                    None,
                    {
                        "capability": "X24",
                        "catalog": "NETWORK_FAULT",
                        "cloneable": True,
                    },
                ),
                "created_by": self.user,
            },
        )
        if scene_library_created:
            self._record_scene_library_event(
                scene_library,
                SceneLibraryAction.CREATED,
                SceneLibraryStatus.READY,
                detail={"catalog": True, "script_code": scene_script.code, "version": scene_library.version},
            )
        return scenario, templates

    def _instance_queryset(self):
        return (
            RehearsalInstance.objects.filter(workspace_id=self.workspace_id)
            .select_related("scenario", "created_by", "fault_configuration")
            .annotate(
                complaint_count=Count(
                    "complaints",
                    filter=Q(complaints__validation_status=ComplaintValidationStatus.VALID),
                    distinct=True,
                ),
                invalid_count=Count(
                    "complaints",
                    filter=Q(complaints__validation_status=ComplaintValidationStatus.INVALID),
                    distinct=True,
                ),
                batch_count=Count("batches", distinct=True),
                data_batch_count=Count("data_batches", distinct=True),
                data_model_count=Count("data_models", distinct=True),
                traceback_count=Count("traceback_snapshots", distinct=True),
                scene_replay_count=Count("scene_replays", distinct=True),
                fault_report_count=Count("fault_reports", distinct=True),
                auxiliary_simulation_count=Count("auxiliary_simulations", distinct=True),
                scene_library_count=Count("scene_libraries", distinct=True),
                scene_run_count=Count("scene_runs", distinct=True),
                alert_count=Count("alerts", distinct=True),
                capability_call_count=Count("capability_calls", distinct=True),
            )
        )

    def _get_instance(self, instance_id, *, lock=False):
        queryset = RehearsalInstance.objects.filter(workspace_id=self.workspace_id)
        if lock:
            queryset = queryset.select_for_update()
        row = queryset.filter(id=instance_id).first()
        if row is None:
            raise AppApiException(404, "预演实例不存在")
        return row

    def _get_batch(self, batch_id):
        row = (
            RehearsalComplaintBatch.objects.filter(workspace_id=self.workspace_id)
            .select_related("instance", "template")
            .filter(id=batch_id)
            .first()
        )
        if row is None:
            raise AppApiException(404, "申告数据批次不存在")
        return row

    def _process_run_queryset(self):
        return RehearsalProcessRun.objects.filter(workspace_id=self.workspace_id).select_related(
            "instance", "template", "created_by"
        )

    def _get_process_run(self, run_id, *, lock=False):
        queryset = RehearsalProcessRun.objects.filter(workspace_id=self.workspace_id)
        if lock:
            queryset = queryset.select_for_update()
        row = queryset.filter(id=run_id).first()
        if row is None:
            raise AppApiException(404, "处置流程不存在")
        return row

    def _data_batch_queryset(self):
        return RehearsalDataBatch.objects.filter(workspace_id=self.workspace_id).select_related(
            "instance", "template", "created_by"
        )

    def _get_data_batch(self, batch_id):
        row = self._data_batch_queryset().filter(id=batch_id).first()
        if row is None:
            raise AppApiException(404, "模拟数据批次不存在")
        return row

    def _data_model_queryset(self):
        return (
            RehearsalDataModel.objects.filter(workspace_id=self.workspace_id)
            .select_related("instance", "scenario", "scene_run", "created_by")
            .annotate(
                version_total=Count("versions", distinct=True),
                load_total=Count("loads", distinct=True),
            )
        )

    def _get_data_model(self, model_id, *, lock=False):
        queryset = RehearsalDataModel.objects.filter(workspace_id=self.workspace_id)
        if lock:
            queryset = queryset.select_for_update()
        row = queryset.filter(id=model_id).first()
        if row is None:
            raise AppApiException(404, "预演数据模型不存在")
        return row

    def _traceback_queryset(self):
        return RehearsalTracebackSnapshot.objects.filter(workspace_id=self.workspace_id).select_related(
            "instance", "scenario", "scene_run", "data_model", "created_by"
        )

    def _get_traceback(self, traceback_id, *, lock=False):
        queryset = RehearsalTracebackSnapshot.objects.filter(workspace_id=self.workspace_id)
        if lock:
            queryset = queryset.select_for_update()
        row = queryset.select_related("instance", "scenario", "scene_run", "data_model").filter(id=traceback_id).first()
        if row is None:
            raise AppApiException(404, "数据动态回溯快照不存在")
        return row

    def _scene_run_queryset(self):
        return (
            RehearsalSceneRun.objects.filter(workspace_id=self.workspace_id)
            .select_related("instance", "script", "library", "created_by")
            .annotate(
                work_order_count=Count("work_orders", distinct=True),
                alert_count=Count("alerts", distinct=True),
            )
        )

    def _scene_library_queryset(self):
        return (
            RehearsalSceneLibrary.objects.filter(workspace_id=self.workspace_id)
            .select_related(
                "scenario",
                "script",
                "default_instance",
                "process_template",
                "data_model",
                "source_library",
                "created_by",
            )
            .annotate(event_count=Count("events", distinct=True))
        )

    def _get_scene_library(self, library_id, *, lock=False):
        queryset = RehearsalSceneLibrary.objects.filter(workspace_id=self.workspace_id)
        if lock:
            queryset = queryset.select_for_update()
        row = queryset.filter(id=library_id).first()
        if row is None:
            raise AppApiException(404, "预演场景库不存在")
        return row

    def _get_scene_run(self, run_id, *, lock=False):
        queryset = RehearsalSceneRun.objects.filter(workspace_id=self.workspace_id)
        if lock:
            queryset = queryset.select_for_update()
        row = queryset.filter(id=run_id).first()
        if row is None:
            raise AppApiException(404, "场景执行不存在")
        return row

    def _work_order_queryset(self):
        return RehearsalWorkOrder.objects.filter(workspace_id=self.workspace_id).select_related(
            "scene_run", "scene_run__instance", "created_by"
        )

    def _get_work_order(self, order_id, *, lock=False):
        queryset = RehearsalWorkOrder.objects.filter(workspace_id=self.workspace_id)
        if lock:
            queryset = queryset.select_for_update()
        row = queryset.filter(id=order_id).first()
        if row is None:
            raise AppApiException(404, "场景工单不存在")
        return row

    def _alert_queryset(self):
        return (
            RehearsalAlert.objects.filter(workspace_id=self.workspace_id)
            .select_related("instance", "template", "scene_run", "data_batch", "created_by")
            .annotate(event_count=Count("events", distinct=True))
        )

    def _get_alert(self, alert_id, *, lock=False):
        queryset = RehearsalAlert.objects.filter(workspace_id=self.workspace_id)
        if lock:
            queryset = queryset.select_for_update()
        row = queryset.filter(id=alert_id).first()
        if row is None:
            raise AppApiException(404, "模拟告警不存在")
        return row

    def _capability_mock_queryset(self):
        return RehearsalCapabilityMock.objects.filter(workspace_id=self.workspace_id).select_related(
            "scenario", "created_by"
        )

    def _get_capability_mock(self, capability_id):
        row = self._capability_mock_queryset().filter(id=capability_id).first()
        if row is None:
            raise AppApiException(404, "模拟能力不存在")
        return row

    def _capability_call_queryset(self):
        return RehearsalCapabilityCall.objects.filter(workspace_id=self.workspace_id).select_related(
            "instance", "capability", "capability__scenario", "replay_of", "created_by"
        )

    def _get_capability_call(self, call_id):
        row = self._capability_call_queryset().filter(id=call_id).first()
        if row is None:
            raise AppApiException(404, "能力调用记录不存在")
        return row

    def _fault_configuration_queryset(self):
        return (
            RehearsalFaultConfiguration.objects.filter(workspace_id=self.workspace_id)
            .select_related("scenario", "source_configuration", "created_by")
            .annotate(
                bound_instance_count=Count("bound_instances", distinct=True),
                event_count=Count("events", distinct=True),
            )
        )

    def _get_fault_configuration(self, configuration_id, *, lock=False):
        queryset = RehearsalFaultConfiguration.objects.filter(workspace_id=self.workspace_id)
        if lock:
            queryset = queryset.select_for_update()
        row = queryset.filter(id=configuration_id).first()
        if row is None:
            raise AppApiException(404, "故障模拟配置不存在")
        return row

    def _scene_replay_queryset(self):
        return RehearsalSceneReplay.objects.filter(workspace_id=self.workspace_id).select_related(
            "instance", "scene_run", "fault_configuration", "created_by"
        )

    def _get_scene_replay(self, replay_id):
        row = self._scene_replay_queryset().filter(id=replay_id).first()
        if row is None:
            raise AppApiException(404, "场景动态回溯不存在")
        return row

    def _fault_report_template_queryset(self):
        return (
            RehearsalFaultReportTemplate.objects.filter(workspace_id=self.workspace_id)
            .select_related("scenario", "created_by")
            .annotate(report_count=Count("reports", distinct=True))
        )

    def _get_fault_report_template(self, template_id):
        row = self._fault_report_template_queryset().filter(id=template_id).first()
        if row is None:
            raise AppApiException(404, "故障上报模板不存在")
        return row

    def _fault_report_queryset(self):
        return (
            RehearsalFaultReport.objects.filter(workspace_id=self.workspace_id)
            .select_related("instance", "template", "scene_run", "created_by")
            .annotate(event_count=Count("events", distinct=True))
        )

    def _get_fault_report(self, report_id, *, lock=False):
        queryset = RehearsalFaultReport.objects.filter(workspace_id=self.workspace_id)
        if lock:
            queryset = queryset.select_for_update()
        row = queryset.filter(id=report_id).first()
        if row is None:
            raise AppApiException(404, "故障上报记录不存在")
        return row

    def _auxiliary_simulation_queryset(self):
        return RehearsalAuxiliarySimulation.objects.filter(workspace_id=self.workspace_id).select_related(
            "instance", "instance__scenario", "created_by"
        )

    def _get_auxiliary_simulation(self, simulation_id):
        row = self._auxiliary_simulation_queryset().filter(id=simulation_id).first()
        if row is None:
            raise AppApiException(404, "辅助模拟批次不存在")
        return row

    def _record_event(self, instance, event_type, previous_status, detail=None):
        sequence = (
            RehearsalInstanceEvent.objects.filter(instance=instance).aggregate(value=Max("sequence_no"))["value"] or 0
        ) + 1
        return RehearsalInstanceEvent.objects.create(
            workspace_id=self.workspace_id,
            instance=instance,
            sequence_no=sequence,
            event_type=event_type,
            previous_status=previous_status,
            current_status=instance.status,
            detail=detail or {},
            operator=self.user,
        )

    def _refresh_summary(self, instance):
        complaints = RehearsalComplaint.objects.filter(instance=instance)
        instance.summary = {
            "batch_count": RehearsalComplaintBatch.objects.filter(instance=instance).count(),
            "data_batch_count": RehearsalDataBatch.objects.filter(instance=instance).count(),
            "data_point_count": RehearsalDataPoint.objects.filter(instance=instance).count(),
            "data_model_count": RehearsalDataModel.objects.filter(instance=instance).count(),
            "traceback_count": RehearsalTracebackSnapshot.objects.filter(instance=instance).count(),
            "scene_library_count": RehearsalSceneLibrary.objects.filter(default_instance=instance).count(),
            "scene_run_count": RehearsalSceneRun.objects.filter(instance=instance).count(),
            "work_order_count": RehearsalWorkOrder.objects.filter(scene_run__instance=instance).count(),
            "alert_count": RehearsalAlert.objects.filter(instance=instance).count(),
            "capability_call_count": RehearsalCapabilityCall.objects.filter(instance=instance).count(),
            "fault_configuration_count": 1 if instance.fault_configuration_id else 0,
            "scene_replay_count": RehearsalSceneReplay.objects.filter(instance=instance).count(),
            "fault_report_count": RehearsalFaultReport.objects.filter(instance=instance).count(),
            "auxiliary_simulation_count": RehearsalAuxiliarySimulation.objects.filter(instance=instance).count(),
            "active_alert_count": RehearsalAlert.objects.filter(
                instance=instance,
                status__in=(AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED),
            ).count(),
            "complaint_count": complaints.filter(validation_status=ComplaintValidationStatus.VALID).count(),
            "invalid_count": complaints.filter(validation_status=ComplaintValidationStatus.INVALID).count(),
            "public_count": complaints.filter(
                validation_status=ComplaintValidationStatus.VALID,
                customer_type=RehearsalCustomerScope.PUBLIC,
            ).count(),
            "enterprise_count": complaints.filter(
                validation_status=ComplaintValidationStatus.VALID,
                customer_type=RehearsalCustomerScope.ENTERPRISE,
            ).count(),
        }
        instance.save(update_fields=["summary", "update_time"])

    def dashboard(self):
        self.ensure_default_catalog()
        instances = self._instance_queryset()
        complaints = RehearsalComplaint.objects.filter(workspace_id=self.workspace_id)
        valid_complaints = complaints.filter(validation_status=ComplaintValidationStatus.VALID)
        templates = RehearsalComplaintTemplate.objects.filter(
            workspace_id=self.workspace_id,
            enabled=True,
        )
        scenarios = RehearsalScenario.objects.filter(
            workspace_id=self.workspace_id,
        ).exclude(status=RehearsalScenarioStatus.ARCHIVED)
        process_templates = RehearsalProcessTemplate.objects.filter(
            workspace_id=self.workspace_id,
            enabled=True,
        )
        process_runs = self._process_run_queryset()
        data_templates = RehearsalDataTemplate.objects.filter(
            workspace_id=self.workspace_id,
            enabled=True,
        )
        data_batches = self._data_batch_queryset()
        data_points = RehearsalDataPoint.objects.filter(workspace_id=self.workspace_id)
        data_models = self._data_model_queryset()
        data_model_versions = RehearsalDataModelVersion.objects.filter(workspace_id=self.workspace_id)
        tracebacks = self._traceback_queryset()
        scene_scripts = RehearsalSceneScript.objects.filter(
            workspace_id=self.workspace_id,
            enabled=True,
        ).select_related("scenario")
        scene_libraries = self._scene_library_queryset()
        scene_runs = self._scene_run_queryset()
        work_orders = self._work_order_queryset()
        alert_templates = RehearsalAlertTemplate.objects.filter(
            workspace_id=self.workspace_id,
            enabled=True,
        ).select_related("scenario")
        alerts = self._alert_queryset()
        capability_mocks = self._capability_mock_queryset().filter(enabled=True)
        capability_calls = self._capability_call_queryset()
        fault_configurations = self._fault_configuration_queryset()
        scene_replays = self._scene_replay_queryset()
        fault_report_templates = self._fault_report_template_queryset()
        fault_reports = self._fault_report_queryset()
        auxiliary_simulations = self._auxiliary_simulation_queryset()
        tag_counts = Counter(tag for tags in data_batches.values_list("tags", flat=True) for tag in (tags or []))
        latest_complaints = valid_complaints.select_related("batch").order_by("-occurred_at", "-create_time")[:12]
        return {
            "summary": {
                "scenario_count": scenarios.count(),
                "instance_count": instances.count(),
                "running_count": instances.filter(status=RehearsalInstanceStatus.RUNNING).count(),
                "ready_count": instances.filter(status=RehearsalInstanceStatus.READY).count(),
                "complaint_count": valid_complaints.count(),
                "invalid_count": complaints.filter(validation_status=ComplaintValidationStatus.INVALID).count(),
                "batch_count": RehearsalComplaintBatch.objects.filter(workspace_id=self.workspace_id).count(),
                "process_run_count": process_runs.count(),
                "process_running_count": process_runs.filter(status=ProcessRunStatus.RUNNING).count(),
                "process_blocked_count": process_runs.filter(status=ProcessRunStatus.BLOCKED).count(),
                "process_completed_count": process_runs.filter(status=ProcessRunStatus.COMPLETED).count(),
                "data_batch_count": data_batches.count(),
                "data_point_count": data_points.count(),
                "metric_batch_count": data_batches.filter(kind=DataSimulationKind.METRIC).count(),
                "sentiment_batch_count": data_batches.filter(kind=DataSimulationKind.SENTIMENT).count(),
                "data_model_count": data_models.count(),
                "data_model_version_count": data_model_versions.count(),
                "data_model_warn_count": data_models.filter(quality_status=DataModelQualityStatus.WARN).count(),
                "traceback_count": tracebacks.count(),
                "traceback_ready_count": tracebacks.filter(status=TracebackStatus.READY).count(),
                "simulation_record_count": (
                    instances.count()
                    + RehearsalComplaintBatch.objects.filter(workspace_id=self.workspace_id).count()
                    + process_runs.count()
                    + data_batches.count()
                    + scene_runs.count()
                    + alerts.count()
                    + tracebacks.count()
                    + capability_calls.count()
                    + fault_reports.count()
                    + auxiliary_simulations.count()
                ),
                "capability_mock_count": capability_mocks.count(),
                "capability_call_count": capability_calls.count(),
                "capability_call_succeeded_count": capability_calls.filter(
                    status=CapabilityCallStatus.SUCCEEDED
                ).count(),
                "capability_call_failed_count": capability_calls.filter(
                    status__in=(CapabilityCallStatus.FAILED, CapabilityCallStatus.TIMEOUT)
                ).count(),
                "fault_configuration_count": fault_configurations.count(),
                "fault_configuration_ready_count": fault_configurations.filter(
                    status=FaultConfigurationStatus.READY
                ).count(),
                "fault_configuration_draft_count": fault_configurations.filter(
                    status=FaultConfigurationStatus.DRAFT
                ).count(),
                "fault_configuration_bound_count": instances.exclude(fault_configuration_id=None).count(),
                "scene_replay_count": scene_replays.count(),
                "scene_replay_ready_count": scene_replays.filter(status=SceneReplayStatus.READY).count(),
                "scene_replay_frame_count": sum(
                    len(frames or []) for frames in scene_replays.values_list("traffic_frames", flat=True)
                ),
                "fault_report_template_count": fault_report_templates.filter(
                    status=FaultReportTemplateStatus.READY
                ).count(),
                "fault_report_count": fault_reports.count(),
                "fault_report_active_count": fault_reports.filter(
                    status__in=(FaultReportStatus.REPORTED, FaultReportStatus.PROCESSING)
                ).count(),
                "fault_report_overdue_count": fault_reports.filter(
                    status__in=(FaultReportStatus.DRAFT, FaultReportStatus.REPORTED, FaultReportStatus.PROCESSING),
                    stage_deadline_at__lt=timezone.now(),
                ).count(),
                "auxiliary_simulation_count": auxiliary_simulations.count(),
                "auxiliary_simulation_attention_count": auxiliary_simulations.filter(
                    status=AuxiliarySimulationStatus.ATTENTION
                ).count(),
                "scene_run_count": scene_runs.count(),
                "scene_library_count": scene_libraries.count(),
                "scene_library_ready_count": scene_libraries.filter(status=SceneLibraryStatus.READY).count(),
                "scene_running_count": scene_runs.filter(status=SceneRunStatus.RUNNING).count(),
                "scene_completed_count": scene_runs.filter(status=SceneRunStatus.COMPLETED).count(),
                "work_order_count": work_orders.count(),
                "work_order_open_count": work_orders.filter(
                    status__in=(WorkOrderStatus.OPEN, WorkOrderStatus.PROCESSING)
                ).count(),
                "alert_count": alerts.count(),
                "alert_pending_count": alerts.filter(status=AlertStatus.PENDING).count(),
                "alert_active_count": alerts.filter(
                    status__in=(AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED)
                ).count(),
                "alert_recovered_count": alerts.filter(status=AlertStatus.RECOVERED).count(),
            },
            "customer_counts": {
                value: valid_complaints.filter(customer_type=value).count()
                for value in (RehearsalCustomerScope.PUBLIC, RehearsalCustomerScope.ENTERPRISE)
            },
            "severity_counts": {
                value: valid_complaints.filter(severity=value).count() for value in ComplaintSeverity.values
            },
            "scenarios": [serialize_scenario(row) for row in scenarios],
            "templates": [serialize_template(row) for row in templates],
            "process_templates": [serialize_process_template(row) for row in process_templates],
            "process_runs": [serialize_process_run(row) for row in process_runs[:30]],
            "data_templates": [serialize_data_template(row) for row in data_templates],
            "data_batches": [serialize_data_batch(row) for row in data_batches[:30]],
            "data_tag_counts": [{"name": name, "count": count} for name, count in tag_counts.most_common(12)],
            "data_models": [serialize_data_model(row) for row in data_models[:30]],
            "tracebacks": [serialize_traceback_snapshot(row) for row in tracebacks[:30]],
            "scene_scripts": [serialize_scene_script(row) for row in scene_scripts],
            "scene_libraries": [serialize_scene_library(row) for row in scene_libraries[:30]],
            "scene_runs": [serialize_scene_run(row) for row in scene_runs[:30]],
            "work_orders": [serialize_work_order(row) for row in work_orders[:30]],
            "alert_templates": [serialize_alert_template(row) for row in alert_templates],
            "alerts": [serialize_alert(row) for row in alerts[:30]],
            "capability_mocks": [serialize_capability_mock(row) for row in capability_mocks],
            "capability_calls": [serialize_capability_call(row) for row in capability_calls[:30]],
            "fault_configurations": [
                serialize_fault_configuration(row) for row in fault_configurations[:30]
            ],
            "scene_replays": [serialize_scene_replay(row) for row in scene_replays[:30]],
            "fault_report_templates": [
                serialize_fault_report_template(row) for row in fault_report_templates[:30]
            ],
            "fault_reports": [serialize_fault_report(row) for row in fault_reports[:30]],
            "random_factor_catalog": RANDOM_FACTOR_CATALOG,
            "auxiliary_simulations": [
                serialize_auxiliary_simulation(row) for row in auxiliary_simulations[:30]
            ],
            "instances": [serialize_instance(row) for row in instances[:30]],
            "latest_complaints": [serialize_complaint(row) for row in latest_complaints],
        }

    def create_scenario(self, data):
        serializer = ScenarioCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        if RehearsalScenario.objects.filter(
            workspace_id=self.workspace_id,
            code=values["code"].strip(),
            version=1,
        ).exists():
            raise AppApiException(400, "预演场景编号已经存在")
        row = RehearsalScenario.objects.create(
            workspace_id=self.workspace_id,
            code=values["code"].strip(),
            name=values["name"].strip(),
            description=values["description"].strip(),
            customer_scope=values["customer_scope"],
            configuration=values["configuration"],
            created_by=self.user,
        )
        return serialize_scenario(row)

    @transaction.atomic
    def create_instance(self, data):
        serializer = InstanceCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        existing = self._instance_queryset().filter(request_id=values["request_id"].strip()).first()
        if existing:
            return {"created": False, "instance": serialize_instance(existing)}
        scenario = RehearsalScenario.objects.filter(
            workspace_id=self.workspace_id,
            id=values["scenario_id"],
            status=RehearsalScenarioStatus.READY,
        ).first()
        if scenario is None:
            raise AppApiException(400, "请选择可预演的场景")
        digest = hashlib.sha1(values["request_id"].encode()).hexdigest()[:6].upper()
        code = values["code"].strip() or f"SIM-{timezone.localtime():%Y%m%d}-{digest}"
        if RehearsalInstance.objects.filter(workspace_id=self.workspace_id, code=code).exists():
            raise AppApiException(400, "预演实例编号已经存在")
        row = RehearsalInstance.objects.create(
            workspace_id=self.workspace_id,
            scenario=scenario,
            request_id=values["request_id"].strip(),
            code=code,
            name=values["name"].strip(),
            planned_start_at=values.get("planned_start_at"),
            parameters=values["parameters"],
            created_by=self.user,
        )
        self._record_event(row, RehearsalEventType.CREATED, RehearsalInstanceStatus.DRAFT)
        return {"created": True, "instance": serialize_instance(self._instance_queryset().get(id=row.id))}

    def instance_detail(self, instance_id):
        row = (
            self._instance_queryset()
            .prefetch_related(
                "events__operator",
                "batches__template",
                "process_runs__template",
                "data_batches__template",
                "data_models__scenario",
                "data_models__scene_run",
                "traceback_snapshots__scenario",
                "traceback_snapshots__scene_run",
                "traceback_snapshots__data_model",
                "scene_replays__scene_run",
                "scene_replays__fault_configuration",
                "fault_reports__template",
                "fault_reports__scene_run",
                "auxiliary_simulations",
                "scene_libraries__scenario",
                "scene_libraries__script",
                "scene_libraries__process_template",
                "scene_libraries__data_model",
                "scene_runs__script",
                "alerts__template",
                "alerts__scene_run",
                "alerts__data_batch",
            )
            .filter(id=instance_id)
            .first()
        )
        if row is None:
            raise AppApiException(404, "预演实例不存在")
        return serialize_instance(row, include_detail=True)

    def _next_batch_version(self, instance):
        return (
            RehearsalComplaintBatch.objects.filter(instance=instance).aggregate(value=Max("version"))["value"] or 0
        ) + 1

    @transaction.atomic
    def generate_complaints(self, instance_id, data):
        serializer = ComplaintGenerateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        instance = self._get_instance(instance_id, lock=True)
        if instance.status not in (RehearsalInstanceStatus.DRAFT, RehearsalInstanceStatus.READY):
            raise AppApiException(400, "只有数据准备中或待启动实例可以生成申告")
        existing = (
            RehearsalComplaintBatch.objects.filter(
                workspace_id=self.workspace_id,
                request_id=values["request_id"].strip(),
            )
            .select_related("instance", "template")
            .first()
        )
        if existing:
            if existing.instance_id != instance.id:
                raise AppApiException(400, "数据批次幂等键已被其他预演实例使用")
            return {"created": False, "batch": serialize_batch(existing)}
        template = RehearsalComplaintTemplate.objects.filter(
            workspace_id=self.workspace_id,
            id=values["template_id"],
            enabled=True,
            customer_type__in=(RehearsalCustomerScope.PUBLIC, RehearsalCustomerScope.ENTERPRISE),
        ).first()
        if template is None:
            raise AppApiException(400, "申告模板不存在或已停用")
        start_at = values["start_at"]
        interval = values["interval_minutes"]
        count = values["count"]
        batch = RehearsalComplaintBatch.objects.create(
            workspace_id=self.workspace_id,
            instance=instance,
            template=template,
            request_id=values["request_id"].strip(),
            source=ComplaintDataSource.GENERATED,
            status=ComplaintBatchStatus.READY,
            version=self._next_batch_version(instance),
            total_count=count,
            valid_count=count,
            time_start=start_at,
            time_end=start_at + timedelta(minutes=interval * (count - 1)),
            created_by=self.user,
        )
        rng = random.Random(values["request_id"])
        severities = list(ComplaintSeverity.values)
        segments = template.profile_schema.get("customer_segment") or ["模拟客户"]
        channels = template.complaint_schema.get("channels") or ["模拟渠道"]
        categories = template.categories or ["服务质量"]
        patterns = template.content_patterns or ["模拟客户反馈{category}问题。"]
        rows = []
        for index in range(count):
            sequence = index + 1
            category = rng.choice(categories)
            severity = rng.choices(severities, weights=(35, 35, 22, 8), k=1)[0]
            is_public = template.customer_type == RehearsalCustomerScope.PUBLIC
            rows.append(
                RehearsalComplaint(
                    workspace_id=self.workspace_id,
                    instance=instance,
                    batch=batch,
                    sequence_no=sequence,
                    customer_type=template.customer_type,
                    customer_ref=f"{'PUB' if is_public else 'ENT'}-{sequence:06d}",
                    customer_name=f"模拟{'公众' if is_public else '政企'}客户{sequence:03d}",
                    contact_masked=(f"138****{sequence % 10000:04d}" if is_public else f"010-****{sequence:04d}"),
                    customer_segment=rng.choice(segments),
                    occurred_at=start_at + timedelta(minutes=interval * index),
                    region=rng.choice(["东区", "南区", "西区", "北区"]),
                    channel=rng.choice(channels),
                    category=category,
                    severity=severity,
                    status=ComplaintStatus.OPEN,
                    title=f"{category}模拟申告-{sequence:03d}",
                    content=rng.choice(patterns).format(category=category),
                    validation_status=ComplaintValidationStatus.VALID,
                    raw_data={"generated": True, "template_version": template.version},
                )
            )
        RehearsalComplaint.objects.bulk_create(rows)
        self._refresh_summary(instance)
        self._record_event(
            instance,
            RehearsalEventType.DATA_GENERATED,
            instance.status,
            {"batch_id": str(batch.id), "count": count, "template": template.code},
        )
        return {"created": True, "batch": serialize_batch(batch)}

    @staticmethod
    def _mask_contact(value):
        value = (value or "").strip()
        if not value or "*" in value:
            return value
        digits = "".join(char for char in value if char.isdigit())
        if len(digits) >= 7:
            return f"{digits[:3]}****{digits[-4:]}"
        return "****"

    @staticmethod
    def _parse_import_row(raw):
        errors = []
        customer_type = (raw.get("customer_type") or "").strip().upper()
        if customer_type not in (RehearsalCustomerScope.PUBLIC, RehearsalCustomerScope.ENTERPRISE):
            errors.append("customer_type 仅支持 PUBLIC 或 ENTERPRISE")
        severity = (raw.get("severity") or "").strip().upper()
        if severity not in ComplaintSeverity.values:
            errors.append("severity 仅支持 LOW/MEDIUM/HIGH/CRITICAL")
        occurred_at_text = (raw.get("occurred_at") or "").strip()
        occurred_at = parse_datetime(occurred_at_text)
        if occurred_at is None:
            errors.append("occurred_at 必须为 ISO 日期时间")
        elif timezone.is_naive(occurred_at):
            occurred_at = timezone.make_aware(occurred_at)
        for field in ("customer_ref", "category", "title", "content"):
            if not (raw.get(field) or "").strip():
                errors.append(f"{field} 不能为空")
        contact = (raw.get("contact") or "").strip()
        if contact and "*" not in contact:
            errors.append("contact 必须为脱敏值")
        sanitized = {key: (raw.get(key) or "").strip() for key in IMPORT_FIELDS}
        sanitized["contact"] = RehearsalService._mask_contact(contact)
        return {
            "customer_type": customer_type or RehearsalCustomerScope.PUBLIC,
            "customer_ref": sanitized["customer_ref"],
            "customer_name": sanitized["customer_name"],
            "contact_masked": sanitized["contact"],
            "customer_segment": sanitized["customer_segment"],
            "occurred_at": occurred_at,
            "region": sanitized["region"],
            "channel": sanitized["channel"],
            "category": sanitized["category"],
            "severity": severity or ComplaintSeverity.LOW,
            "title": sanitized["title"],
            "content": sanitized["content"],
            "validation_errors": errors,
            "raw_data": sanitized,
        }

    @transaction.atomic
    def import_complaints(self, instance_id, request_id, uploaded_file):
        instance = self._get_instance(instance_id, lock=True)
        if instance.status not in (RehearsalInstanceStatus.DRAFT, RehearsalInstanceStatus.READY):
            raise AppApiException(400, "只有数据准备中或待启动实例可以导入申告")
        request_id = (request_id or "").strip()
        if not request_id:
            raise AppApiException(400, "request_id 不能为空")
        existing = (
            RehearsalComplaintBatch.objects.filter(
                workspace_id=self.workspace_id,
                request_id=request_id,
            )
            .select_related("instance", "template")
            .first()
        )
        if existing:
            if existing.instance_id != instance.id:
                raise AppApiException(400, "数据批次幂等键已被其他预演实例使用")
            return {"created": False, "batch": serialize_batch(existing)}
        if uploaded_file is None:
            raise AppApiException(400, "请选择 CSV 文件")
        if uploaded_file.size > 5 * 1024 * 1024:
            raise AppApiException(400, "CSV 文件不能超过 5MB")
        try:
            content = uploaded_file.read().decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise AppApiException(400, "CSV 必须使用 UTF-8 编码") from exc
        reader = csv.DictReader(StringIO(content))
        headers = set(reader.fieldnames or [])
        missing_headers = sorted(REQUIRED_IMPORT_FIELDS - headers)
        if missing_headers:
            raise AppApiException(400, f"CSV 缺少字段：{', '.join(missing_headers)}")
        raw_rows = list(reader)
        if not raw_rows:
            raise AppApiException(400, "CSV 中没有申告数据")
        if len(raw_rows) > 1000:
            raise AppApiException(400, "单次最多导入 1000 条申告")
        parsed_rows = [self._parse_import_row(raw) for raw in raw_rows]
        invalid_count = sum(bool(item["validation_errors"]) for item in parsed_rows)
        valid_count = len(parsed_rows) - invalid_count
        error_counter = Counter(error for item in parsed_rows for error in item["validation_errors"])
        batch_status = (
            ComplaintBatchStatus.READY
            if invalid_count == 0
            else ComplaintBatchStatus.FAILED
            if valid_count == 0
            else ComplaintBatchStatus.PARTIAL
        )
        valid_times = [item["occurred_at"] for item in parsed_rows if item["occurred_at"]]
        batch = RehearsalComplaintBatch.objects.create(
            workspace_id=self.workspace_id,
            instance=instance,
            request_id=request_id,
            source=ComplaintDataSource.IMPORTED,
            status=batch_status,
            version=self._next_batch_version(instance),
            filename=uploaded_file.name[:255],
            total_count=len(parsed_rows),
            valid_count=valid_count,
            invalid_count=invalid_count,
            time_start=min(valid_times) if valid_times else None,
            time_end=max(valid_times) if valid_times else None,
            error_summary=dict(error_counter),
            created_by=self.user,
        )
        RehearsalComplaint.objects.bulk_create(
            [
                RehearsalComplaint(
                    workspace_id=self.workspace_id,
                    instance=instance,
                    batch=batch,
                    sequence_no=index,
                    customer_type=item["customer_type"],
                    customer_ref=item["customer_ref"],
                    customer_name=item["customer_name"],
                    contact_masked=item["contact_masked"],
                    customer_segment=item["customer_segment"],
                    occurred_at=item["occurred_at"],
                    region=item["region"],
                    channel=item["channel"],
                    category=item["category"],
                    severity=item["severity"],
                    status=ComplaintStatus.OPEN,
                    title=item["title"],
                    content=item["content"],
                    validation_status=(
                        ComplaintValidationStatus.INVALID
                        if item["validation_errors"]
                        else ComplaintValidationStatus.VALID
                    ),
                    validation_errors=item["validation_errors"],
                    raw_data=item["raw_data"],
                )
                for index, item in enumerate(parsed_rows, start=1)
            ]
        )
        self._refresh_summary(instance)
        self._record_event(
            instance,
            RehearsalEventType.DATA_IMPORTED,
            instance.status,
            {
                "batch_id": str(batch.id),
                "filename": batch.filename,
                "valid_count": valid_count,
                "invalid_count": invalid_count,
            },
        )
        return {"created": True, "batch": serialize_batch(batch)}

    @transaction.atomic
    def operate_instance(self, instance_id, data):
        serializer = InstanceOperateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        instance = self._get_instance(instance_id, lock=True)
        previous = instance.status
        action = values["action"]
        now = timezone.now()
        event_type = RehearsalEventType.PREPARED
        if action == RehearsalInstanceAction.PREPARE:
            if instance.status != RehearsalInstanceStatus.DRAFT:
                raise AppApiException(400, "只有数据准备中的实例可以完成准备")
            if not RehearsalComplaint.objects.filter(
                instance=instance,
                validation_status=ComplaintValidationStatus.VALID,
            ).exists():
                raise AppApiException(400, "至少需要一条校验通过的申告数据")
            instance.status = RehearsalInstanceStatus.READY
        elif action == RehearsalInstanceAction.START:
            if instance.status != RehearsalInstanceStatus.READY:
                raise AppApiException(400, "只有待启动实例可以开始预演")
            instance.status = RehearsalInstanceStatus.RUNNING
            instance.started_at = now
            event_type = RehearsalEventType.STARTED
        elif action == RehearsalInstanceAction.COMPLETE:
            if instance.status != RehearsalInstanceStatus.RUNNING:
                raise AppApiException(400, "只有预演中的实例可以完成")
            instance.status = RehearsalInstanceStatus.COMPLETED
            instance.completed_at = now
            event_type = RehearsalEventType.COMPLETED
        else:
            if instance.status not in (
                RehearsalInstanceStatus.DRAFT,
                RehearsalInstanceStatus.READY,
                RehearsalInstanceStatus.RUNNING,
            ):
                raise AppApiException(400, "当前实例已经结束，不能取消")
            instance.status = RehearsalInstanceStatus.CANCELLED
            instance.completed_at = now
            event_type = RehearsalEventType.CANCELLED
        instance.save(update_fields=["status", "started_at", "completed_at", "update_time"])
        event = self._record_event(
            instance,
            event_type,
            previous,
            {"note": values["note"].strip()},
        )
        return {
            "instance": serialize_instance(self._instance_queryset().get(id=instance.id)),
            "event": serialize_event(event),
        }

    def create_process_template(self, data):
        serializer = ProcessTemplateCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        code = values["code"].strip().upper()
        if RehearsalProcessTemplate.objects.filter(
            workspace_id=self.workspace_id,
            code=code,
            version=1,
        ).exists():
            raise AppApiException(400, "处置流程模板编号已经存在")
        row = RehearsalProcessTemplate.objects.create(
            workspace_id=self.workspace_id,
            code=code,
            name=values["name"].strip(),
            description=values["description"].strip(),
            customer_scope=values["customer_scope"],
            auto_advance=values["auto_advance"],
            steps=values["steps"],
            created_by=self.user,
        )
        return serialize_process_template(row)

    def create_data_template(self, data):
        serializer = DataTemplateCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        code = values["code"].strip().upper()
        if RehearsalDataTemplate.objects.filter(
            workspace_id=self.workspace_id,
            code=code,
            version=1,
        ).exists():
            raise AppApiException(400, "模拟数据模板编号已经存在")
        row = RehearsalDataTemplate.objects.create(
            workspace_id=self.workspace_id,
            code=code,
            name=values["name"].strip(),
            description=values["description"].strip(),
            kind=values["kind"],
            default_rules=values["default_rules"],
            default_tags=values["default_tags"],
            created_by=self.user,
        )
        return serialize_data_template(row)

    @staticmethod
    def _simulate_value(rule, index, count, rng):
        progress = index / max(count - 1, 1)
        minimum = rule["min_value"]
        maximum = rule["max_value"]
        start = rule["start_value"]
        end = rule["end_value"]
        span = maximum - minimum
        distribution = rule["distribution"]
        if distribution == DataDistribution.RANDOM:
            value = rng.uniform(minimum, maximum)
        elif distribution == DataDistribution.WAVE:
            baseline = start + (end - start) * progress
            value = baseline + math.sin(progress * math.pi * 4) * span * 0.12 + rng.uniform(-span * 0.025, span * 0.025)
        elif distribution == DataDistribution.STEP:
            value = (start if progress < 0.5 else end) + rng.uniform(-span * 0.025, span * 0.025)
        else:
            value = start + (end - start) * progress + rng.uniform(-span * 0.015, span * 0.015)
        value = max(minimum, min(maximum, value))
        decimals = rule["decimals"]
        return int(round(value)) if decimals == 0 else round(value, decimals)

    @staticmethod
    def _data_point_narrative(kind, sequence_no, values):
        if kind == DataSimulationKind.SENTIMENT:
            score = values.get("SENTIMENT_SCORE", 0)
            label = "负向舆情升温" if score <= -0.25 else "正向反馈增加" if score >= 0.25 else "舆情整体平稳"
            return f"{label} · 时序点 {sequence_no:03d}"
        return f"网络指标时序点 {sequence_no:03d}"

    @staticmethod
    def _data_summary(rules, value_rows):
        fields = {}
        for rule in rules:
            series = [row[rule["code"]] for row in value_rows]
            delta = series[-1] - series[0]
            tolerance = max((rule["max_value"] - rule["min_value"]) * 0.01, 10 ** (-rule["decimals"]))
            fields[rule["code"]] = {
                "name": rule["name"],
                "unit": rule["unit"],
                "minimum": min(series),
                "maximum": max(series),
                "average": round(sum(series) / len(series), rule["decimals"]),
                "latest": series[-1],
                "delta": round(delta, rule["decimals"]),
                "trend": "UP" if delta > tolerance else "DOWN" if delta < -tolerance else "FLAT",
                "distribution": rule["distribution"],
            }
        return {"fields": fields, "field_count": len(rules)}

    def _next_data_batch_version(self, instance):
        return (RehearsalDataBatch.objects.filter(instance=instance).aggregate(value=Max("version"))["value"] or 0) + 1

    @transaction.atomic
    def generate_simulation_data(self, instance_id, data):
        serializer = DataSimulationGenerateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        request_id = values["request_id"].strip()
        existing = self._data_batch_queryset().filter(request_id=request_id).first()
        if existing:
            if str(existing.instance_id) != str(instance_id):
                raise AppApiException(400, "模拟数据批次幂等键已被其他预演实例使用")
            return {"created": False, "batch": serialize_data_batch(existing)}
        instance = self._get_instance(instance_id, lock=True)
        if instance.status not in (
            RehearsalInstanceStatus.DRAFT,
            RehearsalInstanceStatus.READY,
            RehearsalInstanceStatus.RUNNING,
        ):
            raise AppApiException(400, "只有活动中的预演实例可以生成模拟数据")
        template = RehearsalDataTemplate.objects.filter(
            workspace_id=self.workspace_id,
            id=values["template_id"],
            enabled=True,
        ).first()
        if template is None:
            raise AppApiException(400, "请选择可用的模拟数据模板")
        rules = values.get("rules") or normalize_data_rules(template.default_rules)
        tags = list(dict.fromkeys([*(template.default_tags or []), *values["tags"]]))[:8]
        count = values["count"]
        start_at = values["start_at"]
        interval = values["interval_minutes"]
        end_at = start_at + timedelta(minutes=interval * (count - 1))
        digest = hashlib.sha1(request_id.encode()).hexdigest()[:6].upper()
        batch = RehearsalDataBatch.objects.create(
            workspace_id=self.workspace_id,
            instance=instance,
            template=template,
            request_id=request_id,
            code=f"DATA-{timezone.localtime():%Y%m%d}-{digest}",
            name=values["name"].strip() or f"{instance.name} · {template.name}",
            kind=template.kind,
            status=DataSimulationStatus.READY,
            version=self._next_data_batch_version(instance),
            point_count=count,
            interval_minutes=interval,
            time_start=start_at,
            time_end=end_at,
            rules_snapshot=rules,
            tags=tags,
            created_by=self.user,
        )
        rng = random.Random(request_id)
        value_rows = [
            {rule["code"]: self._simulate_value(rule, index, count, rng) for rule in rules} for index in range(count)
        ]
        points = []
        for index, point_values in enumerate(value_rows, start=1):
            point_tags = list(tags)
            if template.kind == DataSimulationKind.SENTIMENT:
                score = point_values.get("SENTIMENT_SCORE", 0)
                point_tags.append("负向" if score <= -0.25 else "正向" if score >= 0.25 else "中性")
            points.append(
                RehearsalDataPoint(
                    workspace_id=self.workspace_id,
                    instance=instance,
                    batch=batch,
                    sequence_no=index,
                    occurred_at=start_at + timedelta(minutes=interval * (index - 1)),
                    values=point_values,
                    tags=list(dict.fromkeys(point_tags)),
                    narrative=self._data_point_narrative(template.kind, index, point_values),
                )
            )
        RehearsalDataPoint.objects.bulk_create(points)
        batch.summary = self._data_summary(rules, value_rows)
        batch.save(update_fields=["summary", "update_time"])
        self._refresh_summary(instance)
        self._record_event(
            instance,
            RehearsalEventType.DATA_SIMULATED,
            instance.status,
            {
                "batch_id": str(batch.id),
                "kind": batch.kind,
                "point_count": count,
                "field_codes": [rule["code"] for rule in rules],
                "tags": tags,
            },
        )
        return {"created": True, "batch": serialize_data_batch(self._data_batch_queryset().get(id=batch.id))}

    @staticmethod
    def _datetime_value(value):
        return value.isoformat() if value else None

    @staticmethod
    def _data_model_schema():
        return {
            "customer_profile": ["customer_ref", "customer_name", "customer_segment", "region"],
            "complaint": ["category", "severity", "status", "occurred_at", "content"],
            "metric_point": ["batch_code", "occurred_at", "values", "tags"],
            "process_step": ["run_code", "step_code", "owner_role", "status", "duration_seconds"],
            "scene_step": ["scene_code", "step_code", "status", "output_snapshot"],
            "work_order": ["scene_run_code", "priority", "status", "assignee", "resolution"],
            "alert": ["code", "severity", "status", "resource_name", "metric_value", "threshold"],
        }

    def _data_model_source_counts(self, instance):
        return {
            "complaint_batches": RehearsalComplaintBatch.objects.filter(instance=instance).count(),
            "complaints": RehearsalComplaint.objects.filter(instance=instance).count(),
            "valid_complaints": RehearsalComplaint.objects.filter(
                instance=instance,
                validation_status=ComplaintValidationStatus.VALID,
            ).count(),
            "data_batches": RehearsalDataBatch.objects.filter(instance=instance).count(),
            "data_points": RehearsalDataPoint.objects.filter(instance=instance).count(),
            "process_runs": RehearsalProcessRun.objects.filter(instance=instance).count(),
            "process_steps": RehearsalProcessStep.objects.filter(run__instance=instance).count(),
            "scene_runs": RehearsalSceneRun.objects.filter(instance=instance).count(),
            "scene_steps": RehearsalSceneStep.objects.filter(run__instance=instance).count(),
            "work_orders": RehearsalWorkOrder.objects.filter(scene_run__instance=instance).count(),
            "alerts": RehearsalAlert.objects.filter(instance=instance).count(),
            "alert_events": RehearsalAlertEvent.objects.filter(alert__instance=instance).count(),
            "orphan_alerts": RehearsalAlert.objects.filter(
                instance=instance,
                scene_run__isnull=True,
                data_batch__isnull=True,
            ).count(),
        }

    def _data_model_quality_report(self, counts, model):
        checks = [
            {
                "code": "HAS_VALID_COMPLAINTS",
                "name": "有效申告",
                "passed": counts["valid_complaints"] > 0,
                "severity": "ERROR",
                "message": "至少需要一条有效申告才能支撑预演数据模型",
            },
            {
                "code": "HAS_OPERATION_SIGNAL",
                "name": "处置信号",
                "passed": counts["data_points"] > 0 or counts["process_runs"] > 0 or counts["alerts"] > 0,
                "severity": "WARN",
                "message": "建议补充时序、流程或告警数据，提升模型可回溯性",
            },
            {
                "code": "SCENE_ASSOCIATED",
                "name": "场景关联",
                "passed": model.build_strategy != DataModelBuildStrategy.SCENE_LINKED or bool(model.scene_run_id),
                "severity": "ERROR",
                "message": "场景关联构建策略需要绑定一个场景执行",
            },
            {
                "code": "ALERT_LINEAGE",
                "name": "告警血缘",
                "passed": counts["orphan_alerts"] == 0,
                "severity": "WARN",
                "message": "存在未关联场景或时序批次的告警",
            },
        ]
        failed_errors = [item for item in checks if not item["passed"] and item["severity"] == "ERROR"]
        failed_warnings = [item for item in checks if not item["passed"] and item["severity"] == "WARN"]
        if failed_errors:
            status = DataModelQualityStatus.FAIL
        elif failed_warnings:
            status = DataModelQualityStatus.WARN
        else:
            status = DataModelQualityStatus.PASS
        score = round((len([item for item in checks if item["passed"]]) / len(checks)) * 100)
        return {
            "status": status,
            "status_label": dict(DataModelQualityStatus.choices).get(status, status),
            "score": score,
            "checks": checks,
        }

    def _data_model_lineage(self, instance):
        complaint_batches = RehearsalComplaintBatch.objects.filter(instance=instance).select_related("template")[:20]
        data_batches = RehearsalDataBatch.objects.filter(instance=instance).select_related("template")[:20]
        process_runs = RehearsalProcessRun.objects.filter(instance=instance).select_related("template")[:20]
        scene_runs = RehearsalSceneRun.objects.filter(instance=instance).select_related("script")[:20]
        alerts = RehearsalAlert.objects.filter(instance=instance).select_related("template", "scene_run", "data_batch")[
            :20
        ]
        sources = [
            *[
                {
                    "source_type": "COMPLAINT_BATCH",
                    "source_id": str(row.id),
                    "code": f"BATCH-V{row.version}",
                    "name": row.filename or row.template.name if row.template_id else "人工导入申告",
                    "count": row.valid_count,
                }
                for row in complaint_batches
            ],
            *[
                {
                    "source_type": "DATA_BATCH",
                    "source_id": str(row.id),
                    "code": row.code,
                    "name": row.name,
                    "count": row.point_count,
                }
                for row in data_batches
            ],
            *[
                {
                    "source_type": "PROCESS_RUN",
                    "source_id": str(row.id),
                    "code": row.code,
                    "name": row.name,
                    "count": row.total_steps,
                }
                for row in process_runs
            ],
            *[
                {
                    "source_type": "SCENE_RUN",
                    "source_id": str(row.id),
                    "code": row.code,
                    "name": row.name,
                    "count": row.total_steps,
                }
                for row in scene_runs
            ],
            *[
                {
                    "source_type": "ALERT",
                    "source_id": str(row.id),
                    "code": row.code,
                    "name": row.title,
                    "count": getattr(row, "event_count", 0),
                }
                for row in alerts
            ],
        ]
        relations = [
            {
                "from": str(row.id),
                "from_type": "ALERT",
                "to": str(row.scene_run_id or row.data_batch_id or row.instance_id),
                "to_type": "SCENE_RUN" if row.scene_run_id else "DATA_BATCH" if row.data_batch_id else "INSTANCE",
                "relation": "DERIVED_FROM",
            }
            for row in alerts
        ]
        return {"sources": sources, "relations": relations}

    def _data_model_snapshot(self, model, counts, quality_report, transformer_code, source_scope):
        instance = model.instance
        latest_complaints = (
            RehearsalComplaint.objects.filter(
                instance=instance,
                validation_status=ComplaintValidationStatus.VALID,
            )
            .order_by("-occurred_at", "-create_time")[:8]
        )
        data_batches = RehearsalDataBatch.objects.filter(instance=instance).select_related("template")[:8]
        process_runs = RehearsalProcessRun.objects.filter(instance=instance).select_related("template")[:8]
        scene_runs = RehearsalSceneRun.objects.filter(instance=instance).select_related("script")[:8]
        alerts = RehearsalAlert.objects.filter(instance=instance).select_related("template", "scene_run", "data_batch")[
            :8
        ]
        scene_link = {}
        if model.scene_run_id:
            scene_link = {
                "id": str(model.scene_run_id),
                "code": model.scene_run.code,
                "name": model.scene_run.name,
                "status": model.scene_run.status,
                "injected_snapshot": model.scene_run.injected_snapshot,
            }
        return {
            "model": {
                "code": model.code,
                "name": model.name,
                "build_strategy": model.build_strategy,
                "transformer_code": transformer_code,
                "source_scope": source_scope,
            },
            "instance": {
                "id": str(instance.id),
                "code": instance.code,
                "name": instance.name,
                "status": instance.status,
                "scenario_id": str(instance.scenario_id),
                "scenario_name": instance.scenario.name,
            },
            "scene_link": scene_link,
            "source_counts": counts,
            "quality": quality_report,
            "samples": {
                "complaints": [
                    {
                        "id": str(row.id),
                        "title": row.title,
                        "category": row.category,
                        "severity": row.severity,
                        "occurred_at": self._datetime_value(row.occurred_at),
                    }
                    for row in latest_complaints
                ],
                "data_batches": [
                    {
                        "id": str(row.id),
                        "code": row.code,
                        "name": row.name,
                        "kind": row.kind,
                        "point_count": row.point_count,
                        "fields": [item.get("code") for item in row.rules_snapshot],
                    }
                    for row in data_batches
                ],
                "process_runs": [
                    {
                        "id": str(row.id),
                        "code": row.code,
                        "name": row.name,
                        "status": row.status,
                        "progress_percent": row.progress_percent,
                    }
                    for row in process_runs
                ],
                "scene_runs": [
                    {
                        "id": str(row.id),
                        "code": row.code,
                        "name": row.name,
                        "status": row.status,
                        "progress_percent": row.progress_percent,
                    }
                    for row in scene_runs
                ],
                "alerts": [
                    {
                        "id": str(row.id),
                        "code": row.code,
                        "title": row.title,
                        "severity": row.severity,
                        "status": row.status,
                        "scene_run_id": str(row.scene_run_id) if row.scene_run_id else None,
                        "data_batch_id": str(row.data_batch_id) if row.data_batch_id else None,
                    }
                    for row in alerts
                ],
            },
        }

    def _create_data_model_version(self, model, request_id, transformer_code, source_scope, note=""):
        existing_load = (
            RehearsalDataModelLoad.objects.filter(workspace_id=self.workspace_id, request_id=request_id)
            .select_related("data_model", "version", "operator")
            .first()
        )
        if existing_load:
            if existing_load.data_model_id != model.id:
                raise AppApiException(400, "数据模型加载幂等键已被其他模型使用")
            return existing_load.version, existing_load, False
        counts = self._data_model_source_counts(model.instance)
        quality_report = self._data_model_quality_report(counts, model)
        lineage = self._data_model_lineage(model.instance)
        snapshot = self._data_model_snapshot(model, counts, quality_report, transformer_code, source_scope)
        checksum = hashlib.sha1(
            json.dumps(snapshot, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        version_no = (
            RehearsalDataModelVersion.objects.filter(data_model=model).aggregate(value=Max("version"))["value"] or 0
        ) + 1
        now = timezone.now()
        version = RehearsalDataModelVersion.objects.create(
            workspace_id=self.workspace_id,
            data_model=model,
            version=version_no,
            build_strategy=model.build_strategy,
            transformer_code=transformer_code,
            source_counts=counts,
            entity_schema=self._data_model_schema(),
            snapshot=snapshot,
            quality_report=quality_report,
            lineage=lineage,
            checksum=checksum,
            loaded_at=now,
            created_by=self.user,
        )
        load_status = {
            DataModelQualityStatus.PASS: DataModelLoadStatus.LOADED,
            DataModelQualityStatus.WARN: DataModelLoadStatus.PARTIAL,
            DataModelQualityStatus.FAIL: DataModelLoadStatus.FAILED,
        }[quality_report["status"]]
        load = RehearsalDataModelLoad.objects.create(
            workspace_id=self.workspace_id,
            data_model=model,
            version=version,
            request_id=request_id,
            status=load_status,
            source_counts=counts,
            note=note.strip(),
            message=quality_report["status_label"],
            completed_at=now,
            operator=self.user,
        )
        model.transformer_code = transformer_code
        model.version_count = version_no
        model.current_version = version_no
        model.quality_status = quality_report["status"]
        model.source_scope = source_scope
        model.summary = {
            "source_counts": counts,
            "quality_score": quality_report["score"],
            "quality_status": quality_report["status"],
            "latest_checksum": checksum,
            "loaded_at": self._datetime_value(now),
        }
        model.lineage = lineage
        model.save(
            update_fields=[
                "transformer_code",
                "version_count",
                "current_version",
                "quality_status",
                "source_scope",
                "summary",
                "lineage",
                "update_time",
            ]
        )
        self._refresh_summary(model.instance)
        return version, load, True

    @transaction.atomic
    def create_data_model(self, instance_id, data):
        serializer = DataModelBuildSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        request_id = values["request_id"].strip()
        existing = self._data_model_queryset().filter(request_id=request_id).first()
        if existing:
            return {"created": False, "data_model": serialize_data_model(existing)}
        instance = self._get_instance(instance_id, lock=True)
        scene_run = None
        if values["scene_run_id"]:
            scene_run = RehearsalSceneRun.objects.filter(
                workspace_id=self.workspace_id,
                instance=instance,
                id=values["scene_run_id"],
            ).first()
            if scene_run is None:
                raise AppApiException(400, "关联场景执行不存在或不属于当前预演实例")
        if values["build_strategy"] == DataModelBuildStrategy.SCENE_LINKED and scene_run is None:
            raise AppApiException(400, "场景关联构建策略需要选择一个场景执行")
        digest = hashlib.sha1(request_id.encode()).hexdigest()[:6].upper()
        model = RehearsalDataModel.objects.create(
            workspace_id=self.workspace_id,
            instance=instance,
            scenario=instance.scenario,
            scene_run=scene_run,
            request_id=request_id,
            code=f"DM-{timezone.localtime():%Y%m%d}-{digest}",
            name=values["name"].strip() or f"{instance.name} · 预演数据模型",
            description=values["description"].strip(),
            build_strategy=values["build_strategy"],
            transformer_code=values["transformer_code"],
            source_scope=values["source_scope"],
            created_by=self.user,
        )
        version, load, _ = self._create_data_model_version(
            model,
            request_id,
            values["transformer_code"],
            values["source_scope"],
            "首次构建",
        )
        return {
            "created": True,
            "data_model": self.data_model_detail(model.id),
            "version": serialize_data_model_version(version),
            "load": serialize_data_model_load(load),
        }

    @transaction.atomic
    def load_data_model(self, model_id, data):
        serializer = DataModelLoadSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        model = self._get_data_model(model_id, lock=True)
        source_scope = {**(model.source_scope or {}), **values["source_scope"]}
        transformer_code = values["transformer_code"] or model.transformer_code
        version, load, created = self._create_data_model_version(
            model,
            values["request_id"].strip(),
            transformer_code,
            source_scope,
            values["note"],
        )
        return {
            "created": created,
            "data_model": self.data_model_detail(model.id),
            "version": serialize_data_model_version(version) if version else None,
            "load": serialize_data_model_load(load),
        }

    def data_model_detail(self, model_id):
        row = (
            self._data_model_queryset()
            .prefetch_related("versions", "loads__version", "loads__operator")
            .filter(id=model_id)
            .first()
        )
        if row is None:
            raise AppApiException(404, "预演数据模型不存在")
        return serialize_data_model(row, include_detail=True)

    def list_data_models(self, params=None):
        params = params or {}
        queryset = self._data_model_queryset()
        if params.get("instance_id"):
            queryset = queryset.filter(instance_id=params["instance_id"])
        if params.get("scenario_id"):
            queryset = queryset.filter(scenario_id=params["scenario_id"])
        if params.get("scene_run_id"):
            queryset = queryset.filter(scene_run_id=params["scene_run_id"])
        if params.get("build_strategy"):
            queryset = queryset.filter(build_strategy=params["build_strategy"])
        if params.get("quality_status"):
            queryset = queryset.filter(quality_status=params["quality_status"])
        keyword = (params.get("keyword") or "").strip()
        if keyword:
            queryset = queryset.filter(
                Q(code__icontains=keyword)
                | Q(name__icontains=keyword)
                | Q(instance__name__icontains=keyword)
                | Q(transformer_code__icontains=keyword)
            )
        try:
            page = max(int(params.get("page", 1)), 1)
            page_size = min(max(int(params.get("page_size", 20)), 1), 200)
        except (TypeError, ValueError) as exc:
            raise AppApiException(400, "分页参数必须为整数") from exc
        total = queryset.count()
        start = (page - 1) * page_size
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [serialize_data_model(row) for row in queryset[start : start + page_size]],
        }

    def _record_process_event(self, run, action, previous_status, *, step=None, detail=None):
        sequence = (RehearsalProcessEvent.objects.filter(run=run).aggregate(value=Max("sequence_no"))["value"] or 0) + 1
        return RehearsalProcessEvent.objects.create(
            workspace_id=self.workspace_id,
            run=run,
            step=step,
            sequence_no=sequence,
            action=action,
            previous_status=previous_status,
            current_status=run.status,
            detail=detail or {},
            operator=self.user,
        )

    def _refresh_process_run(self, run):
        steps = RehearsalProcessStep.objects.filter(run=run)
        finished_count = steps.filter(status__in=(ProcessStepStatus.COMPLETED, ProcessStepStatus.SKIPPED)).count()
        status_counts = {item["status"]: item["count"] for item in steps.values("status").annotate(count=Count("id"))}
        run.completed_steps = finished_count
        run.progress_percent = round(finished_count * 100 / run.total_steps) if run.total_steps else 0
        run.summary = {
            "status_counts": status_counts,
            "planned_minutes": sum(steps.values_list("planned_minutes", flat=True)),
            "actual_seconds": sum(steps.values_list("duration_seconds", flat=True)),
        }
        run.save(update_fields=["completed_steps", "progress_percent", "summary", "update_time"])

    @transaction.atomic
    def create_process_run(self, instance_id, data):
        serializer = ProcessRunCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        request_id = values["request_id"].strip()
        existing = self._process_run_queryset().filter(request_id=request_id).first()
        if existing:
            return {"created": False, "run": serialize_process_run(existing)}
        instance = self._get_instance(instance_id, lock=True)
        if instance.status not in (RehearsalInstanceStatus.READY, RehearsalInstanceStatus.RUNNING):
            raise AppApiException(400, "只有待启动或预演中的实例可以生成处置流程")
        if not RehearsalComplaint.objects.filter(
            instance=instance,
            validation_status=ComplaintValidationStatus.VALID,
        ).exists():
            raise AppApiException(400, "生成处置流程前至少需要一条有效申告")
        template = RehearsalProcessTemplate.objects.filter(
            workspace_id=self.workspace_id,
            id=values["template_id"],
            enabled=True,
        ).first()
        if template is None:
            raise AppApiException(400, "请选择可用的处置流程模板")
        digest = hashlib.sha1(request_id.encode()).hexdigest()[:6].upper()
        code = f"PROC-{timezone.localtime():%Y%m%d}-{digest}"
        run = RehearsalProcessRun.objects.create(
            workspace_id=self.workspace_id,
            instance=instance,
            template=template,
            request_id=request_id,
            code=code,
            name=values["name"].strip() or f"{instance.name} · {template.name}",
            auto_advance=template.auto_advance if values["auto_advance"] is None else values["auto_advance"],
            total_steps=len(template.steps),
            template_snapshot={
                "id": str(template.id),
                "code": template.code,
                "name": template.name,
                "version": template.version,
                "steps": template.steps,
            },
            created_by=self.user,
        )
        RehearsalProcessStep.objects.bulk_create(
            [
                RehearsalProcessStep(
                    workspace_id=self.workspace_id,
                    run=run,
                    sequence_no=index,
                    code=item["code"],
                    name=item["name"],
                    description=item.get("description", ""),
                    owner_role=item.get("owner_role", "处置人员"),
                    planned_minutes=item.get("planned_minutes", 30),
                )
                for index, item in enumerate(template.steps, start=1)
            ]
        )
        self._refresh_process_run(run)
        self._record_process_event(
            run,
            "GENERATED",
            ProcessRunStatus.PENDING,
            detail={"template_code": template.code, "total_steps": run.total_steps},
        )
        return {"created": True, "run": serialize_process_run(self._process_run_queryset().get(id=run.id))}

    @staticmethod
    def _current_process_step(run):
        if not run.current_step_index:
            return None
        return RehearsalProcessStep.objects.filter(run=run, sequence_no=run.current_step_index).first()

    @staticmethod
    def _finish_process_step(step, status, note, now):
        step.status = status
        step.completed_at = now
        step.note = note
        if step.started_at:
            step.duration_seconds = max(int((now - step.started_at).total_seconds()), 0)
        step.save(update_fields=["status", "completed_at", "note", "duration_seconds", "update_time"])

    def _advance_process(self, run, now):
        next_step = RehearsalProcessStep.objects.filter(run=run, status=ProcessStepStatus.PENDING).first()
        if next_step is None:
            run.status = ProcessRunStatus.COMPLETED
            run.current_step_code = ""
            run.completed_at = now
            run.progress_percent = 100
            run.save(update_fields=["status", "current_step_code", "completed_at", "progress_percent", "update_time"])
            return None
        next_step.status = ProcessStepStatus.RUNNING
        next_step.started_at = now
        next_step.save(update_fields=["status", "started_at", "update_time"])
        run.status = ProcessRunStatus.RUNNING
        run.current_step_index = next_step.sequence_no
        run.current_step_code = next_step.code
        run.blocked_reason = ""
        run.save(
            update_fields=[
                "status",
                "current_step_index",
                "current_step_code",
                "blocked_reason",
                "update_time",
            ]
        )
        return next_step

    @transaction.atomic
    def operate_process_run(self, run_id, data):
        serializer = ProcessRunOperateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        run = self._get_process_run(run_id, lock=True)
        previous = run.status
        action = values["action"]
        note = values["note"].strip()
        reason = values["reason"].strip()
        now = timezone.now()
        step = self._current_process_step(run)

        if action == ProcessRunAction.START:
            if run.status != ProcessRunStatus.PENDING:
                raise AppApiException(400, "只有待执行流程可以启动")
            run.started_at = now
            run.save(update_fields=["started_at", "update_time"])
            step = self._advance_process(run, now)
        elif action in (ProcessRunAction.COMPLETE_STEP, ProcessRunAction.AUTO_ADVANCE):
            if run.status != ProcessRunStatus.RUNNING or step is None or step.status != ProcessStepStatus.RUNNING:
                raise AppApiException(400, "当前没有可完成的执行中步骤")
            if action == ProcessRunAction.AUTO_ADVANCE and not run.auto_advance:
                raise AppApiException(400, "当前流程未启用自动推进")
            self._finish_process_step(step, ProcessStepStatus.COMPLETED, note, now)
            self._advance_process(run, now)
        elif action == ProcessRunAction.BLOCK:
            if run.status != ProcessRunStatus.RUNNING or step is None or step.status != ProcessStepStatus.RUNNING:
                raise AppApiException(400, "当前没有可阻塞的执行中步骤")
            if not reason:
                raise AppApiException(400, "阻塞流程时必须填写原因")
            step.status = ProcessStepStatus.BLOCKED
            step.note = reason
            step.save(update_fields=["status", "note", "update_time"])
            run.status = ProcessRunStatus.BLOCKED
            run.blocked_reason = reason
            run.save(update_fields=["status", "blocked_reason", "update_time"])
        elif action == ProcessRunAction.RESUME:
            if run.status != ProcessRunStatus.BLOCKED or step is None or step.status != ProcessStepStatus.BLOCKED:
                raise AppApiException(400, "只有已阻塞的当前步骤可以恢复")
            step.status = ProcessStepStatus.RUNNING
            step.note = note
            step.save(update_fields=["status", "note", "update_time"])
            run.status = ProcessRunStatus.RUNNING
            run.blocked_reason = ""
            run.save(update_fields=["status", "blocked_reason", "update_time"])
        elif action == ProcessRunAction.SKIP:
            if run.status != ProcessRunStatus.RUNNING or step is None or step.status != ProcessStepStatus.RUNNING:
                raise AppApiException(400, "当前没有可跳过的执行中步骤")
            self._finish_process_step(step, ProcessStepStatus.SKIPPED, note, now)
            self._advance_process(run, now)
        elif action == ProcessRunAction.FAIL:
            if run.status not in (ProcessRunStatus.RUNNING, ProcessRunStatus.BLOCKED) or step is None:
                raise AppApiException(400, "当前流程不能标记失败")
            self._finish_process_step(step, ProcessStepStatus.FAILED, reason or note, now)
            run.status = ProcessRunStatus.FAILED
            run.completed_at = now
            run.blocked_reason = reason
            run.save(update_fields=["status", "completed_at", "blocked_reason", "update_time"])
        else:
            if run.status in (ProcessRunStatus.COMPLETED, ProcessRunStatus.CANCELLED, ProcessRunStatus.FAILED):
                raise AppApiException(400, "当前流程已经结束，不能取消")
            if step and step.status in (ProcessStepStatus.RUNNING, ProcessStepStatus.BLOCKED):
                self._finish_process_step(step, ProcessStepStatus.SKIPPED, note or "流程已取消", now)
            run.status = ProcessRunStatus.CANCELLED
            run.completed_at = now
            run.save(update_fields=["status", "completed_at", "update_time"])

        self._refresh_process_run(run)
        event = self._record_process_event(
            run,
            action,
            previous,
            step=step,
            detail={"note": note, "reason": reason, "next_step_code": run.current_step_code},
        )
        return {
            "run": self.process_run_detail(run.id),
            "event": serialize_process_event(
                RehearsalProcessEvent.objects.select_related("step", "operator").get(id=event.id)
            ),
        }

    def process_run_detail(self, run_id):
        row = (
            self._process_run_queryset()
            .prefetch_related("steps", "events__step", "events__operator")
            .filter(id=run_id)
            .first()
        )
        if row is None:
            raise AppApiException(404, "处置流程不存在")
        return serialize_process_run(row, include_detail=True)

    def process_run_queryset(self, params=None):
        params = params or {}
        queryset = self._process_run_queryset()
        if params.get("instance_id"):
            queryset = queryset.filter(instance_id=params["instance_id"])
        if params.get("template_id"):
            queryset = queryset.filter(template_id=params["template_id"])
        if params.get("status"):
            queryset = queryset.filter(status=params["status"])
        if params.get("auto_advance") in ("true", "false"):
            queryset = queryset.filter(auto_advance=params["auto_advance"] == "true")
        keyword = (params.get("keyword") or "").strip()
        if keyword:
            queryset = queryset.filter(
                Q(code__icontains=keyword)
                | Q(name__icontains=keyword)
                | Q(instance__code__icontains=keyword)
                | Q(instance__name__icontains=keyword)
            )
        return queryset.order_by("-update_time")

    def list_process_runs(self, params=None):
        params = params or {}
        try:
            page = max(int(params.get("page", 1)), 1)
            page_size = min(max(int(params.get("page_size", 20)), 1), 200)
        except (TypeError, ValueError) as exc:
            raise AppApiException(400, "分页参数必须为整数") from exc
        queryset = self.process_run_queryset(params)
        total = queryset.count()
        start = (page - 1) * page_size
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [serialize_process_run(row) for row in queryset[start : start + page_size]],
        }

    def data_batch_queryset(self, params=None, *, include_points=False):
        params = params or {}
        queryset = self._data_batch_queryset()
        if include_points:
            queryset = queryset.prefetch_related("points")
        if params.get("batch_id"):
            queryset = queryset.filter(id=params["batch_id"])
        if params.get("instance_id"):
            queryset = queryset.filter(instance_id=params["instance_id"])
        if params.get("template_id"):
            queryset = queryset.filter(template_id=params["template_id"])
        if params.get("kind"):
            queryset = queryset.filter(kind=params["kind"])
        if params.get("status"):
            queryset = queryset.filter(status=params["status"])
        if params.get("tag"):
            queryset = queryset.filter(tags__contains=[params["tag"]])
        if params.get("date_from"):
            queryset = queryset.filter(time_end__date__gte=params["date_from"])
        if params.get("date_to"):
            queryset = queryset.filter(time_start__date__lte=params["date_to"])
        keyword = (params.get("keyword") or "").strip()
        if keyword:
            queryset = queryset.filter(
                Q(code__icontains=keyword)
                | Q(name__icontains=keyword)
                | Q(instance__code__icontains=keyword)
                | Q(instance__name__icontains=keyword)
            )
        return queryset.order_by("-update_time")

    def list_data_batches(self, params=None):
        params = params or {}
        try:
            page = max(int(params.get("page", 1)), 1)
            page_size = min(max(int(params.get("page_size", 20)), 1), 200)
        except (TypeError, ValueError) as exc:
            raise AppApiException(400, "分页参数必须为整数") from exc
        queryset = self.data_batch_queryset(params)
        total = queryset.count()
        start = (page - 1) * page_size
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [serialize_data_batch(row) for row in queryset[start : start + page_size]],
        }

    def data_batch_detail(self, batch_id):
        row = self._data_batch_queryset().prefetch_related("points").filter(id=batch_id).first()
        if row is None:
            raise AppApiException(404, "模拟数据批次不存在")
        return serialize_data_batch(row, include_detail=True)

    @transaction.atomic
    def create_scene_script(self, data):
        serializer = SceneScriptCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        scenario = RehearsalScenario.objects.filter(
            workspace_id=self.workspace_id,
            id=values["scenario_id"],
        ).exclude(status=RehearsalScenarioStatus.ARCHIVED).first()
        if scenario is None:
            raise AppApiException(400, "请选择可用的预演场景")
        code = values["code"].strip().upper()
        latest_version = (
            RehearsalSceneScript.objects.filter(workspace_id=self.workspace_id, code=code)
            .aggregate(value=Max("version"))["value"]
            or 0
        )
        row = RehearsalSceneScript.objects.create(
            workspace_id=self.workspace_id,
            scenario=scenario,
            code=code,
            name=values["name"].strip(),
            description=values["description"].strip(),
            version=latest_version + 1,
            steps=values["steps"],
            created_by=self.user,
        )
        return serialize_scene_script(row)

    def _resolve_scene_library_instance(self, scenario, instance_id, fallback=None):
        if instance_id is None:
            return fallback
        row = RehearsalInstance.objects.filter(workspace_id=self.workspace_id, id=instance_id).first()
        if row is None:
            raise AppApiException(400, "绑定的预演实例不存在")
        if row.scenario_id != scenario.id:
            raise AppApiException(400, "绑定的预演实例与场景库所属场景不一致")
        return row

    def _resolve_scene_library_process_template(self, template_id, fallback=None):
        if template_id is None:
            return fallback
        row = RehearsalProcessTemplate.objects.filter(
            workspace_id=self.workspace_id,
            id=template_id,
            enabled=True,
        ).first()
        if row is None:
            raise AppApiException(400, "绑定的处置流程模板不存在或已停用")
        return row

    def _resolve_scene_library_data_model(self, scenario, model_id, fallback=None):
        if model_id is None:
            return fallback
        row = RehearsalDataModel.objects.filter(workspace_id=self.workspace_id, id=model_id).first()
        if row is None:
            raise AppApiException(400, "绑定的预演数据模型不存在")
        if row.scenario_id != scenario.id:
            raise AppApiException(400, "绑定的预演数据模型与场景库所属场景不一致")
        return row

    @staticmethod
    def _scene_library_linked_config(script, default_instance, process_template, data_model, configuration):
        return {
            "script": {
                "id": str(script.id),
                "code": script.code,
                "name": script.name,
                "version": script.version,
                "step_count": len(script.steps),
                "steps": script.steps,
            },
            "default_instance": {
                "id": str(default_instance.id),
                "code": default_instance.code,
                "name": default_instance.name,
                "status": default_instance.status,
            }
            if default_instance
            else None,
            "process_template": {
                "id": str(process_template.id),
                "code": process_template.code,
                "name": process_template.name,
                "version": process_template.version,
                "step_count": len(process_template.steps),
            }
            if process_template
            else None,
            "data_model": {
                "id": str(data_model.id),
                "code": data_model.code,
                "name": data_model.name,
                "current_version": data_model.current_version,
                "quality_status": data_model.quality_status,
            }
            if data_model
            else None,
            "configuration": configuration or {},
        }

    def _record_scene_library_event(self, library, action, previous_status, detail=None):
        sequence = (
            RehearsalSceneLibraryEvent.objects.filter(library=library).aggregate(value=Max("sequence_no"))["value"] or 0
        ) + 1
        return RehearsalSceneLibraryEvent.objects.create(
            workspace_id=self.workspace_id,
            library=library,
            sequence_no=sequence,
            action=action,
            previous_status=previous_status,
            current_status=library.status,
            detail=detail or {},
            operator=self.user,
        )

    @transaction.atomic
    def create_scene_library(self, data):
        serializer = SceneLibraryCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        request_id = values["request_id"].strip()
        existing = self._scene_library_queryset().filter(request_id=request_id).first()
        if existing:
            return {"created": False, "library": serialize_scene_library(existing)}
        scenario = RehearsalScenario.objects.filter(
            workspace_id=self.workspace_id,
            id=values["scenario_id"],
        ).exclude(status=RehearsalScenarioStatus.ARCHIVED).first()
        if scenario is None:
            raise AppApiException(400, "请选择可用的预演场景")
        script = RehearsalSceneScript.objects.filter(
            workspace_id=self.workspace_id,
            id=values["script_id"],
            enabled=True,
        ).select_related("scenario").first()
        if script is None:
            raise AppApiException(400, "请选择可用的场景剧本")
        if script.scenario_id != scenario.id:
            raise AppApiException(400, "场景剧本与场景库所属场景不一致")
        default_instance = self._resolve_scene_library_instance(scenario, values.get("default_instance_id"))
        process_template = self._resolve_scene_library_process_template(values.get("process_template_id"))
        data_model = self._resolve_scene_library_data_model(scenario, values.get("data_model_id"))
        code = values["code"].strip().upper()
        latest_version = (
            RehearsalSceneLibrary.objects.filter(workspace_id=self.workspace_id, code=code)
            .aggregate(value=Max("version"))["value"]
            or 0
        )
        roles = values.get("permission_roles") or ["WORKSPACE_MANAGE"]
        row = RehearsalSceneLibrary.objects.create(
            workspace_id=self.workspace_id,
            scenario=scenario,
            script=script,
            default_instance=default_instance,
            process_template=process_template,
            data_model=data_model,
            request_id=request_id,
            code=code,
            name=values["name"].strip(),
            description=values["description"].strip(),
            version=latest_version + 1,
            visibility=values["visibility"],
            permission_roles=roles,
            linked_config=self._scene_library_linked_config(
                script,
                default_instance,
                process_template,
                data_model,
                values["configuration"],
            ),
            created_by=self.user,
        )
        self._record_scene_library_event(
            row,
            SceneLibraryAction.CREATED,
            SceneLibraryStatus.READY,
            detail={"script_code": script.code, "version": row.version},
        )
        return {"created": True, "library": serialize_scene_library(self._scene_library_queryset().get(id=row.id))}

    @transaction.atomic
    def clone_scene_library(self, library_id, data):
        serializer = SceneLibraryCloneSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        request_id = values["request_id"].strip()
        existing = self._scene_library_queryset().filter(request_id=request_id).first()
        if existing:
            return {"created": False, "library": serialize_scene_library(existing)}
        source = self._get_scene_library(library_id)
        if source.status == SceneLibraryStatus.ARCHIVED:
            raise AppApiException(400, "已归档场景库不能克隆")
        source = self._scene_library_queryset().get(id=source.id)
        steps = values.get("steps") or source.script.steps
        latest_script_version = (
            RehearsalSceneScript.objects.filter(workspace_id=self.workspace_id, code=source.script.code)
            .aggregate(value=Max("version"))["value"]
            or source.script.version
        )
        script = RehearsalSceneScript.objects.create(
            workspace_id=self.workspace_id,
            scenario=source.scenario,
            code=source.script.code,
            name=values.get("name") or source.script.name,
            description=values.get("description") or source.script.description,
            version=latest_script_version + 1,
            steps=steps,
            created_by=self.user,
        )
        default_instance = self._resolve_scene_library_instance(
            source.scenario,
            values.get("default_instance_id"),
            fallback=source.default_instance,
        )
        process_template = self._resolve_scene_library_process_template(
            values.get("process_template_id"),
            fallback=source.process_template,
        )
        data_model = self._resolve_scene_library_data_model(
            source.scenario,
            values.get("data_model_id"),
            fallback=source.data_model,
        )
        latest_library_version = (
            RehearsalSceneLibrary.objects.filter(workspace_id=self.workspace_id, code=source.code)
            .aggregate(value=Max("version"))["value"]
            or source.version
        )
        configuration = values.get("configuration", source.linked_config.get("configuration", {}))
        row = RehearsalSceneLibrary.objects.create(
            workspace_id=self.workspace_id,
            scenario=source.scenario,
            script=script,
            default_instance=default_instance,
            process_template=process_template,
            data_model=data_model,
            source_library=source,
            request_id=request_id,
            code=source.code,
            name=(values.get("name") or source.name).strip(),
            description=(values.get("description") or source.description).strip(),
            version=latest_library_version + 1,
            status=SceneLibraryStatus.READY,
            visibility=values.get("visibility", source.visibility),
            permission_roles=values.get("permission_roles", source.permission_roles or ["WORKSPACE_MANAGE"]),
            linked_config=self._scene_library_linked_config(script, default_instance, process_template, data_model, configuration),
            created_by=self.user,
        )
        self._record_scene_library_event(
            row,
            SceneLibraryAction.CLONED,
            SceneLibraryStatus.READY,
            detail={"source_library_id": str(source.id), "note": values.get("note", "")},
        )
        return {"created": True, "library": serialize_scene_library(self._scene_library_queryset().get(id=row.id))}

    @transaction.atomic
    def operate_scene_library(self, library_id, data):
        serializer = SceneLibraryOperateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        row = self._get_scene_library(library_id, lock=True)
        previous = row.status
        if values["action"] == SceneLibraryAction.PUBLISHED:
            row.status = SceneLibraryStatus.READY
        else:
            row.status = SceneLibraryStatus.ARCHIVED
        row.save(update_fields=["status", "update_time"])
        event = self._record_scene_library_event(
            row,
            values["action"],
            previous,
            detail={"note": values["note"].strip()},
        )
        return {
            "library": serialize_scene_library(self._scene_library_queryset().get(id=row.id)),
            "event": serialize_scene_library_event(RehearsalSceneLibraryEvent.objects.select_related("operator").get(id=event.id)),
        }

    def scene_library_detail(self, library_id):
        row = (
            self._scene_library_queryset()
            .prefetch_related(
                "events__operator",
                "scene_runs__instance",
                "scene_runs__script",
                "scene_runs__library",
            )
            .filter(id=library_id)
            .first()
        )
        if row is None:
            raise AppApiException(404, "预演场景库不存在")
        return serialize_scene_library(row, include_detail=True)

    def scene_library_queryset(self, params=None):
        params = params or {}
        queryset = self._scene_library_queryset()
        if params.get("scenario_id"):
            queryset = queryset.filter(scenario_id=params["scenario_id"])
        if params.get("script_id"):
            queryset = queryset.filter(script_id=params["script_id"])
        if params.get("status"):
            queryset = queryset.filter(status=params["status"])
        if params.get("visibility"):
            queryset = queryset.filter(visibility=params["visibility"])
        keyword = (params.get("keyword") or "").strip()
        if keyword:
            queryset = queryset.filter(
                Q(code__icontains=keyword)
                | Q(name__icontains=keyword)
                | Q(description__icontains=keyword)
                | Q(script__name__icontains=keyword)
                | Q(default_instance__name__icontains=keyword)
            )
        return queryset.order_by("code", "-version")

    def list_scene_libraries(self, params=None):
        params = params or {}
        try:
            page = max(int(params.get("page", 1)), 1)
            page_size = min(max(int(params.get("page_size", 20)), 1), 200)
        except (TypeError, ValueError) as exc:
            raise AppApiException(400, "分页参数必须为整数") from exc
        queryset = self.scene_library_queryset(params)
        total = queryset.count()
        start = (page - 1) * page_size
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [serialize_scene_library(row) for row in queryset[start : start + page_size]],
        }

    def _latest_scene_library_run_ids(self, instance, values):
        complaint_batch_ids = []
        data_batch_ids = []
        process_run_ids = []
        if values["include_latest_complaint_batch"]:
            batch = (
                RehearsalComplaintBatch.objects.filter(
                    workspace_id=self.workspace_id,
                    instance=instance,
                    status__in=(ComplaintBatchStatus.READY, ComplaintBatchStatus.PARTIAL),
                    valid_count__gt=0,
                )
                .order_by("-create_time")
                .first()
            )
            if batch:
                complaint_batch_ids.append(batch.id)
        if values["include_latest_data_batch"]:
            batch = (
                RehearsalDataBatch.objects.filter(
                    workspace_id=self.workspace_id,
                    instance=instance,
                    status=DataSimulationStatus.READY,
                )
                .order_by("-create_time")
                .first()
            )
            if batch:
                data_batch_ids.append(batch.id)
        if values["include_latest_process_run"]:
            run = (
                RehearsalProcessRun.objects.filter(workspace_id=self.workspace_id, instance=instance)
                .order_by("-create_time")
                .first()
            )
            if run:
                process_run_ids.append(run.id)
        return complaint_batch_ids, data_batch_ids, process_run_ids

    @transaction.atomic
    def create_scene_run_from_library(self, library_id, data):
        serializer = SceneLibraryRunSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        library = self._get_scene_library(library_id, lock=True)
        if library.status != SceneLibraryStatus.READY:
            raise AppApiException(400, "只有可复用场景库可以创建执行")
        instance = self._resolve_scene_library_instance(
            library.scenario,
            values.get("instance_id"),
            fallback=library.default_instance,
        )
        if instance is None:
            raise AppApiException(400, "请先绑定默认预演实例或在请求中指定实例")
        complaint_batch_ids, data_batch_ids, process_run_ids = self._latest_scene_library_run_ids(instance, values)
        if not any((complaint_batch_ids, data_batch_ids, process_run_ids)):
            raise AppApiException(400, "绑定实例没有可注入的申告、时序或处置流程数据")
        result = self.create_scene_run(
            str(instance.id),
            {
                "request_id": values["request_id"],
                "script_id": str(library.script_id),
                "name": values["name"].strip() or f"{library.name} · {instance.name}",
                "complaint_batch_ids": complaint_batch_ids,
                "data_batch_ids": data_batch_ids,
                "process_run_ids": process_run_ids,
            },
        )
        run = self._get_scene_run(result["run"]["id"], lock=True)
        if result["created"] and run.library_id is None:
            run.library = library
            run.save(update_fields=["library", "update_time"])
            library.run_count += 1
            library.last_run_at = timezone.now()
            library.save(update_fields=["run_count", "last_run_at", "update_time"])
            self._record_scene_library_event(
                library,
                SceneLibraryAction.RUN_CREATED,
                library.status,
                detail={
                    "scene_run_id": str(run.id),
                    "instance_id": str(instance.id),
                    "injected": {
                        "complaint_batches": len(complaint_batch_ids),
                        "data_batches": len(data_batch_ids),
                        "process_runs": len(process_run_ids),
                    },
                },
            )
        return {"created": result["created"], "run": self.scene_run_detail(run.id)}

    def _resolve_scene_injections(self, instance, values):
        definitions = (
            (
                "complaint_batches",
                "complaint_batch_ids",
                RehearsalComplaintBatch.objects.filter(workspace_id=self.workspace_id, instance=instance),
            ),
            (
                "data_batches",
                "data_batch_ids",
                RehearsalDataBatch.objects.filter(workspace_id=self.workspace_id, instance=instance),
            ),
            (
                "process_runs",
                "process_run_ids",
                RehearsalProcessRun.objects.filter(workspace_id=self.workspace_id, instance=instance),
            ),
        )
        resolved = {}
        for output_key, input_key, queryset in definitions:
            requested_ids = list(dict.fromkeys(values.get(input_key, [])))
            rows = list(queryset.filter(id__in=requested_ids))
            if len(rows) != len(requested_ids):
                raise AppApiException(400, "场景注入数据不存在或不属于当前预演实例")
            if output_key == "complaint_batches":
                resolved[output_key] = [
                    {
                        "id": str(row.id),
                        "source": row.source,
                        "status": row.status,
                        "valid_count": row.valid_count,
                        "invalid_count": row.invalid_count,
                    }
                    for row in rows
                ]
            elif output_key == "data_batches":
                resolved[output_key] = [
                    {
                        "id": str(row.id),
                        "code": row.code,
                        "name": row.name,
                        "kind": row.kind,
                        "status": row.status,
                        "point_count": row.point_count,
                    }
                    for row in rows
                ]
            else:
                resolved[output_key] = [
                    {
                        "id": str(row.id),
                        "code": row.code,
                        "name": row.name,
                        "status": row.status,
                        "progress_percent": row.progress_percent,
                    }
                    for row in rows
                ]
        resolved["totals"] = {
            "complaint_batches": len(resolved["complaint_batches"]),
            "complaints": sum(item["valid_count"] for item in resolved["complaint_batches"]),
            "data_batches": len(resolved["data_batches"]),
            "data_points": sum(item["point_count"] for item in resolved["data_batches"]),
            "process_runs": len(resolved["process_runs"]),
        }
        return resolved

    @transaction.atomic
    def create_scene_run(self, instance_id, data):
        serializer = SceneRunCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        request_id = values["request_id"].strip()
        existing = self._scene_run_queryset().filter(request_id=request_id).first()
        if existing:
            if str(existing.instance_id) != str(instance_id):
                raise AppApiException(400, "场景执行幂等键已被其他预演实例使用")
            return {"created": False, "run": serialize_scene_run(existing)}
        instance = self._get_instance(instance_id, lock=True)
        if instance.status not in (
            RehearsalInstanceStatus.DRAFT,
            RehearsalInstanceStatus.READY,
            RehearsalInstanceStatus.RUNNING,
        ):
            raise AppApiException(400, "只有活动中的预演实例可以创建场景执行")
        script = RehearsalSceneScript.objects.filter(
            workspace_id=self.workspace_id,
            id=values["script_id"],
            enabled=True,
        ).first()
        if script is None:
            raise AppApiException(400, "请选择可用的场景剧本")
        if script.scenario_id != instance.scenario_id:
            raise AppApiException(400, "场景剧本与预演实例所属场景不一致")
        injected_snapshot = self._resolve_scene_injections(instance, values)
        digest = hashlib.sha1(request_id.encode()).hexdigest()[:6].upper()
        run = RehearsalSceneRun.objects.create(
            workspace_id=self.workspace_id,
            instance=instance,
            script=script,
            request_id=request_id,
            code=f"SCENE-{timezone.localtime():%Y%m%d}-{digest}",
            name=values["name"].strip() or f"{instance.name} · {script.name}",
            total_steps=len(script.steps),
            script_snapshot={
                "id": str(script.id),
                "code": script.code,
                "name": script.name,
                "version": script.version,
                "steps": script.steps,
            },
            injected_snapshot=injected_snapshot,
            created_by=self.user,
        )
        RehearsalSceneStep.objects.bulk_create(
            [
                RehearsalSceneStep(
                    workspace_id=self.workspace_id,
                    run=run,
                    sequence_no=index,
                    code=item["code"],
                    name=item["name"],
                    description=item.get("description", ""),
                    expected_result=item.get("expected_result", ""),
                )
                for index, item in enumerate(script.steps, start=1)
            ]
        )
        self._refresh_scene_run(run)
        self._record_scene_event(
            run,
            "CREATED",
            SceneRunStatus.PENDING,
            detail={"script_code": script.code, "injected_totals": injected_snapshot["totals"]},
        )
        self._refresh_summary(instance)
        return {"created": True, "run": serialize_scene_run(self._scene_run_queryset().get(id=run.id))}

    def _record_scene_event(self, run, action, previous_status, *, step=None, detail=None):
        sequence = (RehearsalSceneEvent.objects.filter(run=run).aggregate(value=Max("sequence_no"))["value"] or 0) + 1
        return RehearsalSceneEvent.objects.create(
            workspace_id=self.workspace_id,
            run=run,
            step=step,
            sequence_no=sequence,
            action=action,
            previous_status=previous_status,
            current_status=run.status,
            detail=detail or {},
            operator=self.user,
        )

    def _refresh_scene_run(self, run):
        steps = RehearsalSceneStep.objects.filter(run=run)
        completed = steps.filter(status__in=(SceneStepStatus.COMPLETED, SceneStepStatus.SKIPPED)).count()
        status_counts = {item["status"]: item["count"] for item in steps.values("status").annotate(count=Count("id"))}
        run.completed_steps = completed
        run.progress_percent = round(completed * 100 / run.total_steps) if run.total_steps else 0
        if run.status == SceneRunStatus.COMPLETED:
            run.progress_percent = 100
        summary = {
            "status_counts": status_counts,
            "injected_totals": run.injected_snapshot.get("totals", {}),
        }
        if run.status in (SceneRunStatus.COMPLETED, SceneRunStatus.CANCELLED, SceneRunStatus.FAILED):
            conclusion = {
                SceneRunStatus.COMPLETED: "场景步骤已执行完毕，可复核结论或创建人工工单处理遗留事项。",
                SceneRunStatus.CANCELLED: "场景执行已取消，请检查取消原因后决定是否重新发起。",
                SceneRunStatus.FAILED: "场景执行失败，建议创建高优先级人工工单跟踪处置。",
            }[run.status]
            summary.update(
                {
                    "conclusion": conclusion,
                    "recommendation": "复核步骤输出与注入数据，对未闭环事项创建人工工单。",
                    "generated_at": timezone.now().isoformat(),
                }
            )
        run.summary = summary
        run.save(update_fields=["completed_steps", "progress_percent", "summary", "update_time"])

    @staticmethod
    def _current_scene_step(run):
        if not run.current_step_index:
            return None
        return RehearsalSceneStep.objects.filter(run=run, sequence_no=run.current_step_index).first()

    @staticmethod
    def _finish_scene_step(step, status, note, output, now):
        step.status = status
        step.completed_at = now
        step.note = note
        step.output_snapshot = output
        if step.started_at:
            step.duration_seconds = max(int((now - step.started_at).total_seconds()), 0)
        step.save(
            update_fields=[
                "status",
                "completed_at",
                "note",
                "output_snapshot",
                "duration_seconds",
                "update_time",
            ]
        )

    def _advance_scene(self, run, now):
        next_step = RehearsalSceneStep.objects.filter(run=run, status=SceneStepStatus.PENDING).first()
        if next_step is None:
            run.status = SceneRunStatus.COMPLETED
            run.current_step_code = ""
            run.completed_at = now
            run.save(update_fields=["status", "current_step_code", "completed_at", "update_time"])
            return None
        next_step.status = SceneStepStatus.RUNNING
        next_step.started_at = now
        next_step.save(update_fields=["status", "started_at", "update_time"])
        run.status = SceneRunStatus.RUNNING
        run.current_step_index = next_step.sequence_no
        run.current_step_code = next_step.code
        run.save(update_fields=["status", "current_step_index", "current_step_code", "update_time"])
        return next_step

    @transaction.atomic
    def operate_scene_run(self, run_id, data):
        serializer = SceneRunOperateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        run = self._get_scene_run(run_id, lock=True)
        previous = run.status
        action = values["action"]
        note = values["note"].strip()
        reason = values["reason"].strip()
        output = values["output"]
        now = timezone.now()
        step = self._current_scene_step(run)
        if action == SceneRunAction.START:
            if run.status != SceneRunStatus.PENDING:
                raise AppApiException(400, "只有待执行场景可以启动")
            run.started_at = now
            run.save(update_fields=["started_at", "update_time"])
            step = self._advance_scene(run, now)
        elif action in (SceneRunAction.COMPLETE_STEP, SceneRunAction.SKIP_STEP):
            if run.status != SceneRunStatus.RUNNING or step is None or step.status != SceneStepStatus.RUNNING:
                raise AppApiException(400, "当前没有可处理的执行中步骤")
            target_status = (
                SceneStepStatus.COMPLETED if action == SceneRunAction.COMPLETE_STEP else SceneStepStatus.SKIPPED
            )
            self._finish_scene_step(step, target_status, note, output, now)
            self._advance_scene(run, now)
        elif action == SceneRunAction.FAIL:
            if run.status != SceneRunStatus.RUNNING or step is None:
                raise AppApiException(400, "当前场景不能标记失败")
            if not reason:
                raise AppApiException(400, "标记场景失败时必须填写原因")
            self._finish_scene_step(step, SceneStepStatus.FAILED, reason, output, now)
            run.status = SceneRunStatus.FAILED
            run.completed_at = now
            run.save(update_fields=["status", "completed_at", "update_time"])
        else:
            if run.status in (SceneRunStatus.COMPLETED, SceneRunStatus.CANCELLED, SceneRunStatus.FAILED):
                raise AppApiException(400, "当前场景已经结束，不能取消")
            if step and step.status == SceneStepStatus.RUNNING:
                self._finish_scene_step(step, SceneStepStatus.SKIPPED, note or "场景已取消", output, now)
            run.status = SceneRunStatus.CANCELLED
            run.completed_at = now
            run.save(update_fields=["status", "completed_at", "update_time"])
        self._refresh_scene_run(run)
        event = self._record_scene_event(
            run,
            action,
            previous,
            step=step,
            detail={"note": note, "reason": reason, "output": output, "next_step_code": run.current_step_code},
        )
        return {
            "run": self.scene_run_detail(run.id),
            "event": serialize_scene_event(RehearsalSceneEvent.objects.select_related("step", "operator").get(id=event.id)),
        }

    def scene_run_detail(self, run_id):
        row = (
            self._scene_run_queryset()
            .prefetch_related(
                "steps",
                "events__step",
                "events__operator",
                "work_orders__scene_run",
                "alerts__template",
                "alerts__scene_run",
                "alerts__data_batch",
            )
            .filter(id=run_id)
            .first()
        )
        if row is None:
            raise AppApiException(404, "场景执行不存在")
        return serialize_scene_run(row, include_detail=True)

    def scene_run_queryset(self, params=None):
        params = params or {}
        queryset = self._scene_run_queryset()
        if params.get("instance_id"):
            queryset = queryset.filter(instance_id=params["instance_id"])
        if params.get("script_id"):
            queryset = queryset.filter(script_id=params["script_id"])
        if params.get("status"):
            queryset = queryset.filter(status=params["status"])
        keyword = (params.get("keyword") or "").strip()
        if keyword:
            queryset = queryset.filter(
                Q(code__icontains=keyword)
                | Q(name__icontains=keyword)
                | Q(instance__code__icontains=keyword)
                | Q(instance__name__icontains=keyword)
            )
        return queryset.order_by("-update_time")

    def list_scene_runs(self, params=None):
        params = params or {}
        try:
            page = max(int(params.get("page", 1)), 1)
            page_size = min(max(int(params.get("page_size", 20)), 1), 200)
        except (TypeError, ValueError) as exc:
            raise AppApiException(400, "分页参数必须为整数") from exc
        queryset = self.scene_run_queryset(params)
        total = queryset.count()
        start = (page - 1) * page_size
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [serialize_scene_run(row) for row in queryset[start : start + page_size]],
        }

    def _record_work_order_event(self, order, action, previous_status, detail=None):
        sequence = (
            RehearsalWorkOrderEvent.objects.filter(work_order=order).aggregate(value=Max("sequence_no"))["value"] or 0
        ) + 1
        return RehearsalWorkOrderEvent.objects.create(
            workspace_id=self.workspace_id,
            work_order=order,
            sequence_no=sequence,
            action=action,
            previous_status=previous_status,
            current_status=order.status,
            detail=detail or {},
            operator=self.user,
        )

    @transaction.atomic
    def create_work_order(self, run_id, data):
        serializer = WorkOrderCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        request_id = values["request_id"].strip()
        existing = self._work_order_queryset().filter(request_id=request_id).first()
        if existing:
            if str(existing.scene_run_id) != str(run_id):
                raise AppApiException(400, "场景工单幂等键已被其他场景执行使用")
            return {"created": False, "work_order": serialize_work_order(existing)}
        run = self._get_scene_run(run_id, lock=True)
        digest = hashlib.sha1(request_id.encode()).hexdigest()[:6].upper()
        order = RehearsalWorkOrder.objects.create(
            workspace_id=self.workspace_id,
            scene_run=run,
            request_id=request_id,
            code=f"WO-{timezone.localtime():%Y%m%d}-{digest}",
            title=values["title"].strip(),
            description=values["description"].strip(),
            priority=values["priority"],
            assignee=values["assignee"].strip(),
            created_by=self.user,
        )
        self._record_work_order_event(
            order,
            "CREATED",
            WorkOrderStatus.OPEN,
            {"priority": order.priority, "assignee": order.assignee},
        )
        return {"created": True, "work_order": serialize_work_order(self._work_order_queryset().get(id=order.id))}

    @transaction.atomic
    def operate_work_order(self, order_id, data):
        serializer = WorkOrderOperateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        order = self._get_work_order(order_id, lock=True)
        previous = order.status
        action = values["action"]
        note = values["note"].strip()
        resolution = values["resolution"].strip()
        assignee = values["assignee"].strip()
        now = timezone.now()
        if action == WorkOrderAction.ACCEPT:
            if order.status != WorkOrderStatus.OPEN:
                raise AppApiException(400, "只有待受理工单可以受理")
            order.status = WorkOrderStatus.PROCESSING
            order.accepted_at = now
            if assignee:
                order.assignee = assignee
        elif action == WorkOrderAction.RESOLVE:
            if order.status != WorkOrderStatus.PROCESSING:
                raise AppApiException(400, "只有处理中工单可以解决")
            if not resolution:
                raise AppApiException(400, "解决工单时必须填写解决结果")
            order.status = WorkOrderStatus.RESOLVED
            order.resolution = resolution
            order.resolved_at = now
        elif action == WorkOrderAction.CLOSE:
            if order.status != WorkOrderStatus.RESOLVED:
                raise AppApiException(400, "只有已解决工单可以关闭")
            order.status = WorkOrderStatus.CLOSED
            order.closed_at = now
        else:
            if order.status not in (WorkOrderStatus.RESOLVED, WorkOrderStatus.CLOSED):
                raise AppApiException(400, "只有已解决或已关闭工单可以重新打开")
            order.status = WorkOrderStatus.OPEN
            order.resolution = ""
            order.accepted_at = None
            order.resolved_at = None
            order.closed_at = None
            if assignee:
                order.assignee = assignee
        order.save(
            update_fields=[
                "status",
                "assignee",
                "resolution",
                "accepted_at",
                "resolved_at",
                "closed_at",
                "update_time",
            ]
        )
        event = self._record_work_order_event(
            order,
            action,
            previous,
            {"note": note, "resolution": resolution, "assignee": order.assignee},
        )
        return {
            "work_order": self.work_order_detail(order.id),
            "event": serialize_work_order_event(
                RehearsalWorkOrderEvent.objects.select_related("operator").get(id=event.id)
            ),
        }

    def work_order_detail(self, order_id):
        row = self._work_order_queryset().prefetch_related("events__operator").filter(id=order_id).first()
        if row is None:
            raise AppApiException(404, "场景工单不存在")
        return serialize_work_order(row, include_detail=True)

    def list_work_orders(self, params=None):
        params = params or {}
        queryset = self._work_order_queryset()
        if params.get("scene_run_id"):
            queryset = queryset.filter(scene_run_id=params["scene_run_id"])
        if params.get("status"):
            queryset = queryset.filter(status=params["status"])
        if params.get("priority"):
            queryset = queryset.filter(priority=params["priority"])
        keyword = (params.get("keyword") or "").strip()
        if keyword:
            queryset = queryset.filter(
                Q(code__icontains=keyword)
                | Q(title__icontains=keyword)
                | Q(description__icontains=keyword)
                | Q(assignee__icontains=keyword)
            )
        try:
            page = max(int(params.get("page", 1)), 1)
            page_size = min(max(int(params.get("page_size", 20)), 1), 200)
        except (TypeError, ValueError) as exc:
            raise AppApiException(400, "分页参数必须为整数") from exc
        total = queryset.count()
        start = (page - 1) * page_size
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [serialize_work_order(row) for row in queryset[start : start + page_size]],
        }

    def list_alert_templates(self):
        rows = RehearsalAlertTemplate.objects.filter(
            workspace_id=self.workspace_id,
            enabled=True,
        ).select_related("scenario")
        return [serialize_alert_template(row) for row in rows]

    @transaction.atomic
    def create_alert_template(self, data):
        serializer = AlertTemplateCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        scenario = RehearsalScenario.objects.filter(
            workspace_id=self.workspace_id,
            id=values["scenario_id"],
        ).exclude(status=RehearsalScenarioStatus.ARCHIVED).first()
        if scenario is None:
            raise AppApiException(400, "请选择可用的预演场景")
        code = values["code"].strip().upper()
        latest_version = (
            RehearsalAlertTemplate.objects.filter(
                workspace_id=self.workspace_id,
                code=code,
            ).aggregate(value=Max("version"))["value"]
            or 0
        )
        row = RehearsalAlertTemplate.objects.create(
            workspace_id=self.workspace_id,
            scenario=scenario,
            code=code,
            name=values["name"].strip(),
            description=values["description"].strip(),
            version=latest_version + 1,
            default_severity=values["default_severity"],
            rules=values["rules"],
            created_by=self.user,
        )
        return serialize_alert_template(row)

    def _record_alert_event(self, alert, action, previous_status, occurred_at, detail=None):
        sequence = (
            RehearsalAlertEvent.objects.filter(alert=alert).aggregate(value=Max("sequence_no"))["value"] or 0
        ) + 1
        return RehearsalAlertEvent.objects.create(
            workspace_id=self.workspace_id,
            alert=alert,
            sequence_no=sequence,
            action=action,
            previous_status=previous_status,
            current_status=alert.status,
            occurred_at=occurred_at,
            detail=detail or {},
            operator=self.user,
        )

    @transaction.atomic
    def create_alert(self, instance_id, data):
        serializer = AlertCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        request_id = values["request_id"].strip()
        existing = self._alert_queryset().filter(request_id=request_id).first()
        if existing:
            if str(existing.instance_id) != str(instance_id):
                raise AppApiException(400, "告警幂等键已被其他预演实例使用")
            return {"created": False, "alert": serialize_alert(existing)}
        instance = self._get_instance(instance_id, lock=True)
        if instance.status in (
            RehearsalInstanceStatus.COMPLETED,
            RehearsalInstanceStatus.CANCELLED,
            RehearsalInstanceStatus.FAILED,
        ):
            raise AppApiException(400, "已经结束的预演实例不能配置新告警")
        template = RehearsalAlertTemplate.objects.filter(
            workspace_id=self.workspace_id,
            id=values["template_id"],
            enabled=True,
        ).first()
        if template is None or template.scenario_id != instance.scenario_id:
            raise AppApiException(400, "告警模板与预演实例所属场景不一致")
        scene_run = None
        if values.get("scene_run_id"):
            scene_run = self._scene_run_queryset().filter(id=values["scene_run_id"]).first()
            if scene_run is None or scene_run.instance_id != instance.id:
                raise AppApiException(400, "关联场景执行不属于当前预演实例")
        data_batch = None
        if values.get("data_batch_id"):
            data_batch = self._data_batch_queryset().filter(id=values["data_batch_id"]).first()
            if data_batch is None or data_batch.instance_id != instance.id:
                raise AppApiException(400, "关联趋势批次不属于当前预演实例")
        rule_code = values["rule_code"].strip().upper()
        selected_rule = next((item for item in template.rules if item.get("code") == rule_code), None)
        if rule_code and selected_rule is None:
            raise AppApiException(400, "所选告警规则不属于当前模板")
        selected_rule = selected_rule or (template.rules[0] if template.rules else {})
        digest = hashlib.sha1(request_id.encode()).hexdigest()[:6].upper()
        metric_code = values["metric_code"].strip().upper() or selected_rule.get("metric_code", "")
        metric_name = values["metric_name"].strip() or selected_rule.get("metric_name", "")
        alert = RehearsalAlert.objects.create(
            workspace_id=self.workspace_id,
            instance=instance,
            template=template,
            scene_run=scene_run,
            data_batch=data_batch,
            request_id=request_id,
            code=f"ALERT-{timezone.localtime():%Y%m%d}-{digest}",
            title=values["title"].strip() or selected_rule.get("name", template.name),
            description=values["description"].strip(),
            severity=values.get("severity") or template.default_severity,
            source_system=values["source_system"].strip() or "预演模拟器",
            resource_type=values["resource_type"].strip() or selected_rule.get("resource_type", "网络设备"),
            resource_id=values["resource_id"].strip(),
            resource_name=values["resource_name"].strip(),
            metric_code=metric_code,
            metric_name=metric_name,
            metric_value=values.get("metric_value"),
            threshold=values.get("threshold")
            if values.get("threshold") is not None
            else selected_rule.get("threshold"),
            occurred_at=values["occurred_at"],
            template_snapshot={
                "id": str(template.id),
                "code": template.code,
                "name": template.name,
                "version": template.version,
                "rule": selected_rule,
            },
            context=values["context"],
            created_by=self.user,
        )
        self._record_alert_event(
            alert,
            "CREATED",
            AlertStatus.PENDING,
            alert.occurred_at,
            {
                "metric_code": alert.metric_code,
                "metric_value": alert.metric_value,
                "threshold": alert.threshold,
            },
        )
        self._refresh_summary(instance)
        return {"created": True, "alert": serialize_alert(self._alert_queryset().get(id=alert.id))}

    @transaction.atomic
    def operate_alert(self, alert_id, data):
        serializer = AlertOperateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        alert = self._get_alert(alert_id, lock=True)
        previous = alert.status
        action = values["action"]
        event_at = values["event_at"]
        latest_event = RehearsalAlertEvent.objects.filter(alert=alert).order_by("-occurred_at", "-sequence_no").first()
        if event_at < alert.occurred_at or (latest_event and event_at < latest_event.occurred_at):
            raise AppApiException(400, "告警操作时间不能早于告警发生时间或上一事件")
        if action == AlertAction.REPORT:
            if alert.status != AlertStatus.PENDING:
                raise AppApiException(400, "只有待上报告警可以上报")
            alert.status = AlertStatus.ACTIVE
            alert.reported_at = event_at
        elif action == AlertAction.ACKNOWLEDGE:
            if alert.status != AlertStatus.ACTIVE:
                raise AppApiException(400, "只有活动告警可以确认")
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = event_at
        else:
            if alert.status not in (AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED):
                raise AppApiException(400, "只有活动或已确认告警可以恢复")
            alert.status = AlertStatus.RECOVERED
            alert.recovered_at = event_at
        if values.get("metric_value") is not None:
            alert.metric_value = values["metric_value"]
        alert.save(
            update_fields=[
                "status",
                "metric_value",
                "reported_at",
                "acknowledged_at",
                "recovered_at",
                "update_time",
            ]
        )
        event = self._record_alert_event(
            alert,
            action,
            previous,
            event_at,
            {
                **values["detail"],
                "note": values["note"].strip(),
                "metric_value": alert.metric_value,
            },
        )
        self._refresh_summary(alert.instance)
        return {
            "alert": self.alert_detail(alert.id),
            "event": serialize_alert_event(RehearsalAlertEvent.objects.select_related("operator").get(id=event.id)),
        }

    def alert_detail(self, alert_id):
        row = self._alert_queryset().prefetch_related("events__operator").filter(id=alert_id).first()
        if row is None:
            raise AppApiException(404, "模拟告警不存在")
        return serialize_alert(row, include_detail=True)

    def list_alerts(self, params=None):
        params = params or {}
        queryset = self._alert_queryset()
        if params.get("instance_id"):
            queryset = queryset.filter(instance_id=params["instance_id"])
        if params.get("template_id"):
            queryset = queryset.filter(template_id=params["template_id"])
        if params.get("scene_run_id"):
            queryset = queryset.filter(scene_run_id=params["scene_run_id"])
        if params.get("status"):
            queryset = queryset.filter(status=params["status"])
        if params.get("severity"):
            queryset = queryset.filter(severity=params["severity"])
        if params.get("date_from"):
            queryset = queryset.filter(occurred_at__date__gte=params["date_from"])
        if params.get("date_to"):
            queryset = queryset.filter(occurred_at__date__lte=params["date_to"])
        keyword = (params.get("keyword") or "").strip()
        if keyword:
            queryset = queryset.filter(
                Q(code__icontains=keyword)
                | Q(title__icontains=keyword)
                | Q(resource_id__icontains=keyword)
                | Q(resource_name__icontains=keyword)
                | Q(metric_name__icontains=keyword)
            )
        try:
            page = max(int(params.get("page", 1)), 1)
            page_size = min(max(int(params.get("page_size", 20)), 1), 200)
        except (TypeError, ValueError) as exc:
            raise AppApiException(400, "分页参数必须为整数") from exc
        total = queryset.count()
        start = (page - 1) * page_size
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [serialize_alert(row) for row in queryset[start : start + page_size]],
        }

    @staticmethod
    def _traceback_kind_label(kind):
        return dict(TRACEBACK_KIND_CHOICES).get(kind, kind)

    def _response_timeline_item(self, item):
        return {**item, "occurred_at": self._datetime_value(item["occurred_at"])}

    def _build_instance_timeline_items(self, instance):
        items = []
        complaints = RehearsalComplaint.objects.filter(
            workspace_id=self.workspace_id,
            instance=instance,
            validation_status=ComplaintValidationStatus.VALID,
        ).order_by("occurred_at")[:200]
        for row in complaints:
            items.append(
                {
                    "kind": "COMPLAINT",
                    "kind_label": "客户申告",
                    "occurred_at": row.occurred_at,
                    "title": row.title,
                    "subtitle": f"{row.customer_name} · {row.get_severity_display()}",
                    "status": row.status,
                    "reference_id": str(row.id),
                    "detail": {"category": row.category, "region": row.region},
                }
            )
        points = RehearsalDataPoint.objects.filter(
            workspace_id=self.workspace_id,
            instance=instance,
        ).select_related("batch").order_by("occurred_at")[:200]
        for row in points:
            kind = row.batch.kind
            items.append(
                {
                    "kind": kind,
                    "kind_label": row.batch.get_kind_display(),
                    "occurred_at": row.occurred_at,
                    "title": row.narrative or f"{row.batch.name} · 第 {row.sequence_no} 点",
                    "subtitle": " / ".join(f"{key}={value}" for key, value in list(row.values.items())[:3]),
                    "status": row.batch.status,
                    "reference_id": str(row.id),
                    "detail": {"batch_id": str(row.batch_id), "values": row.values},
                }
            )
        process_events = RehearsalProcessEvent.objects.filter(
            workspace_id=self.workspace_id,
            run__instance=instance,
        ).select_related("run", "step").order_by("create_time")[:200]
        for row in process_events:
            items.append(
                {
                    "kind": "PROCESS",
                    "kind_label": "处置操作",
                    "occurred_at": row.create_time,
                    "title": f"{serialize_process_event(row)['action_label']} · {row.step.name if row.step_id else row.run.name}",
                    "subtitle": f"{row.get_previous_status_display()} → {row.get_current_status_display()}",
                    "status": row.current_status,
                    "reference_id": str(row.id),
                    "detail": row.detail,
                }
            )
        scene_events = RehearsalSceneEvent.objects.filter(
            workspace_id=self.workspace_id,
            run__instance=instance,
        ).select_related("run", "step").order_by("create_time")[:200]
        for row in scene_events:
            items.append(
                {
                    "kind": "SCENE",
                    "kind_label": "场景执行",
                    "occurred_at": row.create_time,
                    "title": f"{serialize_scene_event(row)['action_label']} · {row.step.name if row.step_id else row.run.name}",
                    "subtitle": f"{row.get_previous_status_display()} → {row.get_current_status_display()}",
                    "status": row.current_status,
                    "reference_id": str(row.id),
                    "detail": row.detail,
                }
            )
        work_order_events = RehearsalWorkOrderEvent.objects.filter(
            workspace_id=self.workspace_id,
            work_order__scene_run__instance=instance,
        ).select_related("work_order", "work_order__scene_run").order_by("create_time")[:200]
        for row in work_order_events:
            event = serialize_work_order_event(row)
            items.append(
                {
                    "kind": "WORK_ORDER",
                    "kind_label": "人工工单",
                    "occurred_at": row.create_time,
                    "title": f"{event['action_label']} · {row.work_order.title}",
                    "subtitle": f"{event['previous_status_label']} → {event['current_status_label']}",
                    "status": row.current_status,
                    "reference_id": str(row.work_order_id),
                    "detail": {**row.detail, "work_order_code": row.work_order.code},
                }
            )
        alert_events = RehearsalAlertEvent.objects.filter(
            workspace_id=self.workspace_id,
            alert__instance=instance,
        ).select_related("alert").order_by("occurred_at", "sequence_no")[:200]
        for row in alert_events:
            items.append(
                {
                    "kind": "ALERT",
                    "kind_label": "模拟告警",
                    "occurred_at": row.occurred_at,
                    "title": f"{serialize_alert_event(row)['action_label']} · {row.alert.title}",
                    "subtitle": f"{row.get_previous_status_display()} → {row.get_current_status_display()}",
                    "status": row.current_status,
                    "reference_id": str(row.alert_id),
                    "detail": {**row.detail, "severity": row.alert.severity, "alert_code": row.alert.code},
                }
            )
        items.sort(key=lambda item: (item["occurred_at"], item["kind"], item["reference_id"]))
        return items

    def instance_timeline(self, instance_id):
        instance = self._get_instance(instance_id)
        items = self._build_instance_timeline_items(instance)
        return {
            "instance": {"id": str(instance.id), "code": instance.code, "name": instance.name},
            "total": len(items),
            "kind_counts": dict(Counter(item["kind"] for item in items)),
            "items": [self._response_timeline_item(item) for item in items[:500]],
        }

    def _infer_traceback_window(self, instance, scope, window_start=None, window_end=None, scene_run=None):
        if scope == TracebackScope.FULL_INSTANCE:
            return window_start, window_end
        if scope == TracebackScope.CUSTOM:
            return window_start, window_end
        if window_start and window_end:
            return window_start, window_end
        alert_window = RehearsalAlert.objects.filter(workspace_id=self.workspace_id, instance=instance).aggregate(
            start=Min("occurred_at"),
            reported=Max("reported_at"),
            acknowledged=Max("acknowledged_at"),
            recovered=Max("recovered_at"),
            end=Max("occurred_at"),
        )
        if alert_window["start"]:
            inferred_start = window_start or alert_window["start"] - timedelta(minutes=30)
            inferred_end = (
                window_end
                or alert_window["recovered"]
                or alert_window["acknowledged"]
                or alert_window["reported"]
                or alert_window["end"]
            )
            return inferred_start, inferred_end + timedelta(minutes=30)
        if scene_run and scene_run.started_at:
            inferred_start = window_start or scene_run.started_at - timedelta(minutes=15)
            inferred_end = window_end or scene_run.completed_at or timezone.now()
            return inferred_start, inferred_end + timedelta(minutes=15)
        return window_start, window_end

    def _filter_traceback_items(self, items, kind_scope, window_start=None, window_end=None):
        selected_kinds = set(kind_scope or [])
        filtered = []
        for item in items:
            if selected_kinds and item["kind"] not in selected_kinds:
                continue
            if window_start and item["occurred_at"] < window_start:
                continue
            if window_end and item["occurred_at"] > window_end:
                continue
            filtered.append(item)
        return filtered

    def _traceback_nodes(self, items):
        nodes = []
        for kind in dict(TRACEBACK_KIND_CHOICES):
            group = [item for item in items if item["kind"] == kind]
            if not group:
                continue
            status_counts = Counter(item.get("status") or "UNKNOWN" for item in group)
            nodes.append(
                {
                    "kind": kind,
                    "kind_label": self._traceback_kind_label(kind),
                    "count": len(group),
                    "first_at": self._datetime_value(group[0]["occurred_at"]),
                    "last_at": self._datetime_value(group[-1]["occurred_at"]),
                    "first_title": group[0]["title"],
                    "last_title": group[-1]["title"],
                    "status_counts": dict(status_counts),
                }
            )
        return nodes

    def _traceback_transitions(self, items):
        transitions = Counter()
        for previous, current in zip(items, items[1:]):
            transitions[(previous["kind"], current["kind"])] += 1
        return [
            {
                "from_kind": source,
                "from_label": self._traceback_kind_label(source),
                "to_kind": target,
                "to_label": self._traceback_kind_label(target),
                "count": count,
            }
            for (source, target), count in transitions.most_common()
        ]

    @staticmethod
    def _numeric_value(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _traceback_deltas(self, items):
        series = {}
        for item in items:
            if item["kind"] not in (DataSimulationKind.METRIC, DataSimulationKind.SENTIMENT):
                continue
            for key, value in (item.get("detail") or {}).get("values", {}).items():
                number = self._numeric_value(value)
                if number is None:
                    continue
                series.setdefault(key, []).append((item["occurred_at"], number))
        deltas = []
        for key, values in series.items():
            if len(values) < 2:
                continue
            values.sort(key=lambda item: item[0])
            first_at, first_value = values[0]
            last_at, last_value = values[-1]
            deltas.append(
                {
                    "field": key,
                    "first_value": first_value,
                    "last_value": last_value,
                    "delta": round(last_value - first_value, 4),
                    "first_at": self._datetime_value(first_at),
                    "last_at": self._datetime_value(last_at),
                }
            )
        return sorted(deltas, key=lambda item: abs(item["delta"]), reverse=True)[:12]

    def _build_traceback_snapshot(self, instance, items, *, scope, kind_scope, window_start, window_end):
        serial_items = [self._response_timeline_item(item) for item in items]
        kind_counts = dict(Counter(item["kind"] for item in items))
        status_counts = dict(Counter(item.get("status") or "UNKNOWN" for item in items))
        first_event = items[0] if items else None
        last_event = items[-1] if items else None
        duration_minutes = 0
        if first_event and last_event:
            duration_minutes = max(int((last_event["occurred_at"] - first_event["occurred_at"]).total_seconds() // 60), 0)
        nodes = self._traceback_nodes(items)
        transitions = self._traceback_transitions(items)
        deltas = self._traceback_deltas(items)
        dominant_kind = max(kind_counts.items(), key=lambda item: item[1])[0] if kind_counts else ""
        summary = {
            "instance_code": instance.code,
            "scope": scope,
            "scope_label": dict(TracebackScope.choices).get(scope, scope),
            "kind_scope": kind_scope,
            "window_start": self._datetime_value(window_start),
            "window_end": self._datetime_value(window_end),
            "first_event_at": self._datetime_value(first_event["occurred_at"]) if first_event else None,
            "last_event_at": self._datetime_value(last_event["occurred_at"]) if last_event else None,
            "duration_minutes": duration_minutes,
            "dominant_kind": dominant_kind,
            "dominant_kind_label": self._traceback_kind_label(dominant_kind) if dominant_kind else "",
            "root_signal": first_event["title"] if first_event else "",
            "latest_signal": last_event["title"] if last_event else "",
            "node_count": len(nodes),
            "transition_count": len(transitions),
            "delta_count": len(deltas),
        }
        snapshot = {
            "instance": {"id": str(instance.id), "code": instance.code, "name": instance.name},
            "filters": {
                "scope": scope,
                "kind_scope": kind_scope,
                "window_start": self._datetime_value(window_start),
                "window_end": self._datetime_value(window_end),
            },
            "items": serial_items,
            "nodes": nodes,
            "transitions": transitions,
            "deltas": deltas,
        }
        return {
            "summary": summary,
            "snapshot": snapshot,
            "kind_counts": kind_counts,
            "pivot_counts": {"status_counts": status_counts, "node_counts": {item["kind"]: item["count"] for item in nodes}},
        }

    @transaction.atomic
    def create_traceback(self, instance_id, data):
        serializer = TracebackCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        request_id = values["request_id"].strip()
        existing = self._traceback_queryset().filter(request_id=request_id).first()
        if existing:
            return {"created": False, "traceback": self.traceback_detail(existing.id)}
        instance = self._get_instance(instance_id)
        scene_run = None
        if values["scene_run_id"]:
            scene_run = RehearsalSceneRun.objects.filter(
                workspace_id=self.workspace_id,
                instance=instance,
                id=values["scene_run_id"],
            ).first()
            if scene_run is None:
                raise AppApiException(400, "关联场景执行不存在或不属于当前预演实例")
        data_model = None
        if values["data_model_id"]:
            data_model = RehearsalDataModel.objects.filter(
                workspace_id=self.workspace_id,
                instance=instance,
                id=values["data_model_id"],
            ).first()
            if data_model is None:
                raise AppApiException(400, "关联预演数据模型不存在或不属于当前预演实例")
        kind_scope = values["kind_scope"] or [kind for kind, _ in TRACEBACK_KIND_CHOICES]
        window_start, window_end = self._infer_traceback_window(
            instance,
            values["scope"],
            values["window_start"],
            values["window_end"],
            scene_run,
        )
        source_items = self._build_instance_timeline_items(instance)
        items = self._filter_traceback_items(source_items, kind_scope, window_start, window_end)[:500]
        payload = self._build_traceback_snapshot(
            instance,
            items,
            scope=values["scope"],
            kind_scope=kind_scope,
            window_start=window_start,
            window_end=window_end,
        )
        checksum = hashlib.sha1(
            json.dumps(payload["snapshot"], ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        digest = hashlib.sha1(request_id.encode()).hexdigest()[:6].upper()
        row = RehearsalTracebackSnapshot.objects.create(
            workspace_id=self.workspace_id,
            instance=instance,
            scenario=instance.scenario,
            scene_run=scene_run,
            data_model=data_model,
            request_id=request_id,
            code=f"TB-{timezone.localtime():%Y%m%d}-{digest}",
            name=values["name"].strip() or f"{instance.name} · 数据动态回溯",
            description=values["description"].strip(),
            scope=values["scope"],
            status=TracebackStatus.READY if items else TracebackStatus.EMPTY,
            kind_scope=kind_scope,
            window_start=window_start,
            window_end=window_end,
            total_events=len(items),
            kind_counts=payload["kind_counts"],
            pivot_counts=payload["pivot_counts"],
            summary=payload["summary"],
            snapshot=payload["snapshot"],
            checksum=checksum,
            generated_at=timezone.now(),
            created_by=self.user,
        )
        self._refresh_summary(instance)
        return {"created": True, "traceback": self.traceback_detail(row.id)}

    def traceback_queryset(self, params=None):
        params = params or {}
        queryset = self._traceback_queryset()
        if params.get("instance_id"):
            queryset = queryset.filter(instance_id=params["instance_id"])
        if params.get("scenario_id"):
            queryset = queryset.filter(scenario_id=params["scenario_id"])
        if params.get("scene_run_id"):
            queryset = queryset.filter(scene_run_id=params["scene_run_id"])
        if params.get("data_model_id"):
            queryset = queryset.filter(data_model_id=params["data_model_id"])
        if params.get("scope"):
            queryset = queryset.filter(scope=params["scope"])
        if params.get("status"):
            queryset = queryset.filter(status=params["status"])
        if params.get("kind"):
            queryset = queryset.filter(kind_counts__has_key=params["kind"])
        if params.get("date_from"):
            queryset = queryset.filter(generated_at__date__gte=params["date_from"])
        if params.get("date_to"):
            queryset = queryset.filter(generated_at__date__lte=params["date_to"])
        keyword = (params.get("keyword") or "").strip()
        if keyword:
            queryset = queryset.filter(
                Q(code__icontains=keyword)
                | Q(name__icontains=keyword)
                | Q(description__icontains=keyword)
                | Q(instance__name__icontains=keyword)
                | Q(instance__code__icontains=keyword)
            )
        return queryset

    def list_tracebacks(self, params=None):
        params = params or {}
        try:
            page = max(int(params.get("page", 1)), 1)
            page_size = min(max(int(params.get("page_size", 20)), 1), 200)
        except (TypeError, ValueError) as exc:
            raise AppApiException(400, "分页参数必须为整数") from exc
        queryset = self.traceback_queryset(params)
        total = queryset.count()
        start = (page - 1) * page_size
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [serialize_traceback_snapshot(row) for row in queryset[start : start + page_size]],
        }

    def traceback_detail(self, traceback_id):
        return serialize_traceback_snapshot(self._get_traceback(traceback_id), include_detail=True)

    def list_capability_mocks(self, params=None):
        params = params or {}
        queryset = self._capability_mock_queryset()
        if params.get("scenario_id"):
            queryset = queryset.filter(scenario_id=params["scenario_id"])
        if params.get("kind"):
            queryset = queryset.filter(kind=params["kind"])
        if params.get("enabled") not in (None, ""):
            queryset = queryset.filter(enabled=str(params["enabled"]).lower() in {"1", "true", "yes"})
        keyword = (params.get("keyword") or "").strip()
        if keyword:
            queryset = queryset.filter(
                Q(code__icontains=keyword)
                | Q(name__icontains=keyword)
                | Q(description__icontains=keyword)
                | Q(endpoint__icontains=keyword)
            )
        return [serialize_capability_mock(row) for row in queryset]

    def create_capability_mock(self, data):
        serializer = CapabilityMockCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        scenario = RehearsalScenario.objects.filter(
            workspace_id=self.workspace_id,
            id=values["scenario_id"],
        ).exclude(status=RehearsalScenarioStatus.ARCHIVED).first()
        if scenario is None:
            raise AppApiException(400, "请选择当前工作空间内未归档的预演场景")
        latest_version = (
            RehearsalCapabilityMock.objects.filter(
                workspace_id=self.workspace_id,
                code=values["code"],
            ).aggregate(value=Max("version"))["value"]
            or 0
        )
        row = RehearsalCapabilityMock.objects.create(
            workspace_id=self.workspace_id,
            scenario=scenario,
            code=values["code"],
            name=values["name"].strip(),
            description=values["description"].strip(),
            kind=values["kind"],
            version=latest_version + 1,
            method=values["method"],
            endpoint=values["endpoint"].strip(),
            request_schema=values["request_schema"],
            response_template=values["response_template"],
            failure_template=values["failure_template"],
            default_status=values["default_status"],
            default_latency_ms=values["default_latency_ms"],
            created_by=self.user,
        )
        return serialize_capability_mock(row)

    @staticmethod
    def _capability_snapshot(capability):
        return {
            "id": str(capability.id),
            "code": capability.code,
            "name": capability.name,
            "kind": capability.kind,
            "version": capability.version,
            "method": capability.method,
            "endpoint": capability.endpoint,
            "request_schema": capability.request_schema,
            "response_template": capability.response_template,
            "failure_template": capability.failure_template,
        }

    @staticmethod
    def _validate_capability_payload(capability, payload):
        required = (capability.request_schema or {}).get("required", [])
        missing = [field for field in required if field not in payload or payload[field] in (None, "")]
        if missing:
            raise AppApiException(400, f"请求参数缺少必填字段：{', '.join(missing)}")

    @transaction.atomic
    def _execute_capability_call(
        self,
        instance_id,
        *,
        request_id,
        capability_id,
        request_payload,
        expected_status=None,
        latency_ms=None,
        warroom_group="默认战情室",
        source="SANDBOX",
        replay_of=None,
    ):
        existing = self._capability_call_queryset().filter(request_id=request_id).first()
        if existing:
            return {"created": False, "call": serialize_capability_call(existing, include_detail=True)}
        instance = self._get_instance(instance_id, lock=True)
        capability = self._get_capability_mock(capability_id)
        if not capability.enabled:
            raise AppApiException(400, "该模拟能力已停用")
        if capability.scenario_id != instance.scenario_id:
            raise AppApiException(400, "模拟能力与当前预演实例场景不匹配")
        self._validate_capability_payload(capability, request_payload)
        call_no = (
            RehearsalCapabilityCall.objects.filter(instance=instance, capability=capability).aggregate(
                value=Max("call_no")
            )["value"]
            or 0
        ) + 1
        call_status = expected_status or capability.default_status
        simulated_latency = capability.default_latency_ms if latency_ms is None else latency_ms
        started_at = timezone.now()
        finished_at = started_at + timedelta(milliseconds=simulated_latency)
        response_payload = json.loads(json.dumps(capability.response_template, ensure_ascii=False))
        error_message = ""
        http_status = 200
        if call_status == CapabilityCallStatus.FAILED:
            response_payload = json.loads(json.dumps(capability.failure_template, ensure_ascii=False))
            error_message = response_payload.get("message", "模拟能力调用失败")
            http_status = 500
        elif call_status == CapabilityCallStatus.TIMEOUT:
            response_payload = {
                "code": "SIMULATION_TIMEOUT",
                "message": "能力调用超过模拟超时阈值",
                "timeout_ms": simulated_latency,
            }
            error_message = response_payload["message"]
            http_status = 504
        response_payload["_simulation"] = {
            "request_id": request_id,
            "source": source,
            "capability_code": capability.code,
            "call_no": call_no,
        }
        row = RehearsalCapabilityCall.objects.create(
            workspace_id=self.workspace_id,
            instance=instance,
            capability=capability,
            replay_of=replay_of,
            request_id=request_id,
            call_no=call_no,
            status=call_status,
            source=source,
            warroom_group=warroom_group.strip() or "默认战情室",
            request_payload=request_payload,
            response_payload=response_payload,
            capability_snapshot=self._capability_snapshot(capability),
            http_status=http_status,
            latency_ms=simulated_latency,
            error_message=error_message,
            started_at=started_at,
            finished_at=finished_at,
            created_by=self.user,
        )
        self._record_event(
            instance,
            RehearsalEventType.CAPABILITY_CALLED,
            instance.status,
            {
                "call_id": str(row.id),
                "capability_code": capability.code,
                "capability_name": capability.name,
                "call_no": call_no,
                "status": call_status,
                "warroom_group": row.warroom_group,
                "source": source,
            },
        )
        self._refresh_summary(instance)
        return {"created": True, "call": serialize_capability_call(self._get_capability_call(row.id), include_detail=True)}

    def invoke_capability(self, instance_id, data):
        serializer = CapabilityCallSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        return self._execute_capability_call(
            instance_id,
            request_id=values["request_id"].strip(),
            capability_id=values["capability_id"],
            request_payload=values["request_payload"],
            expected_status=values["expected_status"],
            latency_ms=values["latency_ms"],
            warroom_group=values["warroom_group"],
        )

    def capability_call_queryset(self, params=None):
        params = params or {}
        queryset = self._capability_call_queryset()
        if params.get("instance_id"):
            queryset = queryset.filter(instance_id=params["instance_id"])
        if params.get("capability_id"):
            queryset = queryset.filter(capability_id=params["capability_id"])
        if params.get("kind"):
            queryset = queryset.filter(capability__kind=params["kind"])
        if params.get("status"):
            queryset = queryset.filter(status=params["status"])
        if params.get("warroom_group"):
            queryset = queryset.filter(warroom_group=params["warroom_group"])
        if params.get("date_from"):
            queryset = queryset.filter(started_at__date__gte=params["date_from"])
        if params.get("date_to"):
            queryset = queryset.filter(started_at__date__lte=params["date_to"])
        keyword = (params.get("keyword") or "").strip()
        if keyword:
            queryset = queryset.filter(
                Q(request_id__icontains=keyword)
                | Q(capability__code__icontains=keyword)
                | Q(capability__name__icontains=keyword)
                | Q(instance__code__icontains=keyword)
                | Q(instance__name__icontains=keyword)
                | Q(warroom_group__icontains=keyword)
                | Q(error_message__icontains=keyword)
            )
        return queryset

    def list_capability_calls(self, params=None):
        params = params or {}
        try:
            page = max(int(params.get("page", 1)), 1)
            page_size = min(max(int(params.get("page_size", 20)), 1), 200)
        except (TypeError, ValueError) as exc:
            raise AppApiException(400, "分页参数必须为整数") from exc
        queryset = self.capability_call_queryset(params)
        total = queryset.count()
        start = (page - 1) * page_size
        latency_values = list(queryset.values_list("latency_ms", flat=True))
        warroom_rows = queryset.values("warroom_group").annotate(
            total=Count("id"),
            succeeded=Count("id", filter=Q(status=CapabilityCallStatus.SUCCEEDED)),
            attention=Count(
                "id",
                filter=Q(status__in=(CapabilityCallStatus.FAILED, CapabilityCallStatus.TIMEOUT)),
            ),
        ).order_by("-attention", "-total", "warroom_group")
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "summary": {
                "total": total,
                "succeeded": queryset.filter(status=CapabilityCallStatus.SUCCEEDED).count(),
                "failed": queryset.filter(status=CapabilityCallStatus.FAILED).count(),
                "timeout": queryset.filter(status=CapabilityCallStatus.TIMEOUT).count(),
                "average_latency_ms": round(sum(latency_values) / len(latency_values)) if latency_values else 0,
            },
            "warrooms": list(warroom_rows),
            "items": [serialize_capability_call(row) for row in queryset[start : start + page_size]],
        }

    def capability_call_detail(self, call_id):
        return serialize_capability_call(self._get_capability_call(call_id), include_detail=True)

    def replay_capability_call(self, call_id, data):
        serializer = CapabilityReplaySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        original = self._get_capability_call(call_id)
        return self._execute_capability_call(
            original.instance_id,
            request_id=values["request_id"].strip(),
            capability_id=original.capability_id,
            request_payload=original.request_payload,
            expected_status=values["expected_status"],
            latency_ms=values["latency_ms"],
            warroom_group=values["warroom_group"] or original.warroom_group,
            source="REPLAY",
            replay_of=original,
        )

    @staticmethod
    def _fault_configuration_snapshot(configuration):
        return {
            "id": str(configuration.id),
            "code": configuration.code,
            "name": configuration.name,
            "version": configuration.version,
            "scenario_id": str(configuration.scenario_id),
            "status": configuration.status,
            "alert_rules": configuration.alert_rules,
            "timeout_policy": configuration.timeout_policy,
            "active_window": configuration.active_window,
            "topology_snapshot": configuration.topology_snapshot,
            "emergency_plan": configuration.emergency_plan,
            "validation_report": configuration.validation_report,
            "validated_at": configuration.validated_at.isoformat() if configuration.validated_at else None,
        }

    @staticmethod
    def _fault_configuration_checks(configuration):
        checks = []
        alert_rules = configuration.alert_rules or []
        alert_codes = [str(item.get("code", "")).strip().upper() for item in alert_rules if isinstance(item, dict)]
        alert_rule_valid = bool(alert_rules) and len(alert_codes) == len(alert_rules) and all(
            code
            and item.get("severity") in AlertSeverity.values
            and str(item.get("operator", "")).upper() in {"GT", "GTE", "LT", "LTE", "EQ"}
            and item.get("threshold") is not None
            for code, item in zip(alert_codes, alert_rules, strict=False)
        ) and len(alert_codes) == len(set(alert_codes))
        checks.append(
            {
                "code": "ALERT_RULES",
                "name": "告警规则",
                "passed": alert_rule_valid,
                "message": "告警规则编号、等级、比较符和阈值完整" if alert_rule_valid else "至少配置一条编号唯一且字段完整的告警规则",
            }
        )

        timeout_policy = configuration.timeout_policy or {}
        overall_seconds = timeout_policy.get("overall_seconds")
        step_seconds = timeout_policy.get("step_seconds")
        timeout_valid = (
            isinstance(overall_seconds, int)
            and isinstance(step_seconds, int)
            and 1 <= step_seconds <= overall_seconds <= 86400
            and timeout_policy.get("on_timeout") in {"ESCALATE", "SWITCH", "ESCALATE_AND_SWITCH", "ABORT"}
        )
        checks.append(
            {
                "code": "TIMEOUT_POLICY",
                "name": "超时策略",
                "passed": timeout_valid,
                "message": "步骤和整体超时范围有效" if timeout_valid else "超时需满足 1 ≤ 步骤 ≤ 整体 ≤ 86400 秒并设置处置动作",
            }
        )

        active_window = configuration.active_window or {}
        start = str(active_window.get("start", ""))
        end = str(active_window.get("end", ""))
        weekdays = active_window.get("weekdays", [])
        window_valid = (
            bool(re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", start))
            and bool(re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", end))
            and start != end
            and isinstance(weekdays, list)
            and bool(weekdays)
            and all(isinstance(day, int) and 1 <= day <= 7 for day in weekdays)
            and len(weekdays) == len(set(weekdays))
            and bool(str(active_window.get("timezone", "")).strip())
        )
        checks.append(
            {
                "code": "ACTIVE_WINDOW",
                "name": "运行时段",
                "passed": window_valid,
                "message": "运行时段、星期和时区有效" if window_valid else "运行时段需包含有效时区、星期及不同的 HH:MM 起止时间",
            }
        )

        topology = configuration.topology_snapshot or {}
        nodes = topology.get("nodes", [])
        links = topology.get("links", [])
        node_ids = [str(item.get("id", "")).strip() for item in nodes if isinstance(item, dict)]
        node_set = set(node_ids)
        topology_valid = (
            bool(nodes)
            and len(node_ids) == len(nodes)
            and len(node_ids) == len(node_set)
            and all(node_ids)
            and isinstance(links, list)
            and all(
                isinstance(item, dict)
                and item.get("source") in node_set
                and item.get("target") in node_set
                and item.get("source") != item.get("target")
                for item in links
            )
        )
        checks.append(
            {
                "code": "TOPOLOGY",
                "name": "拓扑快照",
                "passed": topology_valid,
                "message": "拓扑节点唯一且链路端点可解析" if topology_valid else "拓扑至少包含一个唯一节点，所有链路必须引用已存在的不同节点",
            }
        )

        emergency_plan = configuration.emergency_plan or {}
        plan_steps = emergency_plan.get("steps", [])
        step_codes = [str(item.get("code", "")).strip().upper() for item in plan_steps if isinstance(item, dict)]
        plan_valid = (
            bool(str(emergency_plan.get("code", "")).strip())
            and bool(str(emergency_plan.get("name", "")).strip())
            and bool(plan_steps)
            and len(step_codes) == len(plan_steps)
            and all(step_codes)
            and len(step_codes) == len(set(step_codes))
            and all(str(item.get("name", "")).strip() for item in plan_steps)
        )
        checks.append(
            {
                "code": "EMERGENCY_PLAN",
                "name": "应急预案",
                "passed": plan_valid,
                "message": "应急预案和步骤快照完整" if plan_valid else "应急预案需包含编号、名称及编号唯一的处置步骤",
            }
        )
        return checks

    def _record_fault_configuration_event(
        self,
        configuration,
        action,
        previous_status,
        *,
        instance=None,
        detail=None,
    ):
        sequence = (
            RehearsalFaultConfigurationEvent.objects.filter(configuration=configuration).aggregate(
                value=Max("sequence_no")
            )["value"]
            or 0
        ) + 1
        return RehearsalFaultConfigurationEvent.objects.create(
            workspace_id=self.workspace_id,
            configuration=configuration,
            instance=instance,
            sequence_no=sequence,
            action=action,
            previous_status=previous_status,
            current_status=configuration.status,
            detail=detail or {},
            operator=self.user,
        )

    @transaction.atomic
    def create_fault_configuration(self, data):
        serializer = FaultConfigurationCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        request_id = values["request_id"].strip()
        existing = self._fault_configuration_queryset().filter(request_id=request_id).first()
        if existing:
            return {"created": False, "configuration": serialize_fault_configuration(existing)}
        scenario = RehearsalScenario.objects.filter(
            workspace_id=self.workspace_id,
            id=values["scenario_id"],
        ).exclude(status=RehearsalScenarioStatus.ARCHIVED).first()
        if scenario is None:
            raise AppApiException(400, "请选择当前工作空间内未归档的预演场景")
        latest_version = (
            RehearsalFaultConfiguration.objects.filter(
                workspace_id=self.workspace_id,
                code=values["code"],
            ).aggregate(value=Max("version"))["value"]
            or 0
        )
        row = RehearsalFaultConfiguration.objects.create(
            workspace_id=self.workspace_id,
            scenario=scenario,
            request_id=request_id,
            code=values["code"],
            name=values["name"].strip(),
            description=values["description"].strip(),
            version=latest_version + 1,
            alert_rules=values["alert_rules"],
            timeout_policy=values["timeout_policy"],
            active_window=values["active_window"],
            topology_snapshot=values["topology_snapshot"],
            emergency_plan=values["emergency_plan"],
            validation_report={"status": "PENDING", "passed": False, "errors": []},
            created_by=self.user,
        )
        self._record_fault_configuration_event(
            row,
            FaultConfigurationAction.CREATED,
            FaultConfigurationStatus.DRAFT,
            detail={"version": row.version},
        )
        validated = self.validate_fault_configuration(row.id, {"note": "创建后自动校验"})
        return {"created": True, "configuration": validated["configuration"]}

    @transaction.atomic
    def clone_fault_configuration(self, configuration_id, data):
        serializer = FaultConfigurationCloneSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        request_id = values["request_id"].strip()
        existing = self._fault_configuration_queryset().filter(request_id=request_id).first()
        if existing:
            return {"created": False, "configuration": serialize_fault_configuration(existing)}
        source = self._get_fault_configuration(configuration_id)
        if source.status == FaultConfigurationStatus.ARCHIVED:
            raise AppApiException(400, "已归档故障模拟配置不能克隆")
        latest_version = (
            RehearsalFaultConfiguration.objects.filter(
                workspace_id=self.workspace_id,
                code=source.code,
            ).aggregate(value=Max("version"))["value"]
            or source.version
        )
        row = RehearsalFaultConfiguration.objects.create(
            workspace_id=self.workspace_id,
            scenario=source.scenario,
            source_configuration=source,
            request_id=request_id,
            code=source.code,
            name=(values.get("name") or source.name).strip(),
            description=(values.get("description") or source.description).strip(),
            version=latest_version + 1,
            alert_rules=values.get("alert_rules", source.alert_rules),
            timeout_policy=values.get("timeout_policy", source.timeout_policy),
            active_window=values.get("active_window", source.active_window),
            topology_snapshot=values.get("topology_snapshot", source.topology_snapshot),
            emergency_plan=values.get("emergency_plan", source.emergency_plan),
            validation_report={"status": "PENDING", "passed": False, "errors": []},
            created_by=self.user,
        )
        self._record_fault_configuration_event(
            row,
            FaultConfigurationAction.CLONED,
            FaultConfigurationStatus.DRAFT,
            detail={"source_configuration_id": str(source.id), "note": values["note"].strip()},
        )
        validated = self.validate_fault_configuration(row.id, {"note": "克隆后自动校验"})
        return {"created": True, "configuration": validated["configuration"]}

    @transaction.atomic
    def validate_fault_configuration(self, configuration_id, data=None):
        serializer = FaultConfigurationNoteSerializer(data=data or {})
        serializer.is_valid(raise_exception=True)
        row = self._get_fault_configuration(configuration_id, lock=True)
        if row.status == FaultConfigurationStatus.ARCHIVED:
            raise AppApiException(400, "已归档故障模拟配置不能重新校验")
        previous = row.status
        checks = self._fault_configuration_checks(row)
        errors = [item["message"] for item in checks if not item["passed"]]
        passed = not errors
        validated_at = timezone.now()
        row.status = FaultConfigurationStatus.READY if passed else FaultConfigurationStatus.DRAFT
        row.validated_at = validated_at
        if passed and row.published_at is None:
            row.published_at = validated_at
        row.validation_report = {
            "status": "PASSED" if passed else "FAILED",
            "passed": passed,
            "check_count": len(checks),
            "error_count": len(errors),
            "checks": checks,
            "errors": errors,
        }
        row.save(
            update_fields=["status", "validated_at", "published_at", "validation_report", "update_time"]
        )
        event = self._record_fault_configuration_event(
            row,
            FaultConfigurationAction.VALIDATED,
            previous,
            detail={"passed": passed, "error_count": len(errors), "note": serializer.validated_data["note"].strip()},
        )
        return {
            "configuration": serialize_fault_configuration(self._fault_configuration_queryset().get(id=row.id)),
            "event": serialize_fault_configuration_event(
                RehearsalFaultConfigurationEvent.objects.select_related("operator", "instance").get(id=event.id)
            ),
        }

    @transaction.atomic
    def archive_fault_configuration(self, configuration_id, data=None):
        serializer = FaultConfigurationNoteSerializer(data=data or {})
        serializer.is_valid(raise_exception=True)
        row = self._get_fault_configuration(configuration_id, lock=True)
        previous = row.status
        row.status = FaultConfigurationStatus.ARCHIVED
        row.save(update_fields=["status", "update_time"])
        event = self._record_fault_configuration_event(
            row,
            FaultConfigurationAction.ARCHIVED,
            previous,
            detail={"note": serializer.validated_data["note"].strip()},
        )
        return {
            "configuration": serialize_fault_configuration(self._fault_configuration_queryset().get(id=row.id)),
            "event": serialize_fault_configuration_event(
                RehearsalFaultConfigurationEvent.objects.select_related("operator", "instance").get(id=event.id)
            ),
        }

    @transaction.atomic
    def apply_fault_configuration(self, instance_id, data):
        serializer = FaultConfigurationApplySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        instance = self._get_instance(instance_id, lock=True)
        request_id = values["request_id"].strip()
        current_snapshot = instance.fault_configuration_snapshot or {}
        if current_snapshot.get("request_id") == request_id:
            return {"created": False, "instance": serialize_instance(self._instance_queryset().get(id=instance.id))}
        if instance.status in (
            RehearsalInstanceStatus.COMPLETED,
            RehearsalInstanceStatus.CANCELLED,
            RehearsalInstanceStatus.FAILED,
        ):
            raise AppApiException(400, "已经结束的预演实例不能应用故障模拟配置")
        configuration = RehearsalFaultConfiguration.objects.filter(
            workspace_id=self.workspace_id,
            id=values["configuration_id"],
        ).select_related("scenario").first()
        if configuration is None:
            raise AppApiException(404, "故障模拟配置不存在")
        if configuration.status != FaultConfigurationStatus.READY:
            raise AppApiException(400, "只有校验通过的故障模拟配置可以应用")
        if configuration.scenario_id != instance.scenario_id:
            raise AppApiException(400, "故障模拟配置与预演实例所属场景不一致")
        snapshot = self._fault_configuration_snapshot(configuration)
        snapshot["request_id"] = request_id
        snapshot["applied_at"] = timezone.now().isoformat()
        snapshot["note"] = values["note"].strip()
        instance.fault_configuration = configuration
        instance.fault_configuration_snapshot = snapshot
        instance.save(
            update_fields=["fault_configuration", "fault_configuration_snapshot", "update_time"]
        )
        self._record_fault_configuration_event(
            configuration,
            FaultConfigurationAction.APPLIED,
            configuration.status,
            instance=instance,
            detail={"request_id": request_id, "note": values["note"].strip()},
        )
        self._record_event(
            instance,
            RehearsalEventType.FAULT_CONFIGURATION_APPLIED,
            instance.status,
            {
                "configuration_id": str(configuration.id),
                "configuration_code": configuration.code,
                "configuration_version": configuration.version,
                "request_id": request_id,
            },
        )
        self._refresh_summary(instance)
        return {"created": True, "instance": serialize_instance(self._instance_queryset().get(id=instance.id))}

    def fault_configuration_queryset(self, params=None):
        params = params or {}
        queryset = self._fault_configuration_queryset()
        if params.get("scenario_id"):
            queryset = queryset.filter(scenario_id=params["scenario_id"])
        if params.get("status"):
            queryset = queryset.filter(status=params["status"])
        if params.get("bound") not in (None, ""):
            if str(params["bound"]).lower() in {"1", "true", "yes"}:
                queryset = queryset.filter(bound_instances__isnull=False).distinct()
            else:
                queryset = queryset.filter(bound_instances__isnull=True)
        keyword = (params.get("keyword") or "").strip()
        if keyword:
            queryset = queryset.filter(
                Q(code__icontains=keyword)
                | Q(name__icontains=keyword)
                | Q(description__icontains=keyword)
                | Q(scenario__name__icontains=keyword)
            )
        return queryset.order_by("code", "-version")

    def list_fault_configurations(self, params=None):
        params = params or {}
        try:
            page = max(int(params.get("page", 1)), 1)
            page_size = min(max(int(params.get("page_size", 20)), 1), 200)
        except (TypeError, ValueError) as exc:
            raise AppApiException(400, "分页参数必须为整数") from exc
        queryset = self.fault_configuration_queryset(params)
        total = queryset.count()
        start = (page - 1) * page_size
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "summary": {
                "total": total,
                "ready": queryset.filter(status=FaultConfigurationStatus.READY).count(),
                "draft": queryset.filter(status=FaultConfigurationStatus.DRAFT).count(),
                "archived": queryset.filter(status=FaultConfigurationStatus.ARCHIVED).count(),
                "bound_instances": RehearsalInstance.objects.filter(
                    workspace_id=self.workspace_id,
                    fault_configuration__in=queryset,
                ).count(),
            },
            "items": [serialize_fault_configuration(row) for row in queryset[start : start + page_size]],
        }

    def fault_configuration_detail(self, configuration_id):
        row = (
            self._fault_configuration_queryset()
            .prefetch_related("events__operator", "events__instance", "bound_instances")
            .filter(id=configuration_id)
            .first()
        )
        if row is None:
            raise AppApiException(404, "故障模拟配置不存在")
        return serialize_fault_configuration(row, include_detail=True)

    @staticmethod
    def _scene_replay_frame_nodes(payload, topology_nodes, fallback_index=0):
        node_ids = [str(item.get("id")) for item in topology_nodes if item.get("id")]
        source = str(
            payload.get("source_node")
            or payload.get("source_id")
            or payload.get("source")
            or (node_ids[fallback_index % len(node_ids)] if node_ids else "ORCHESTRATOR")
        )
        target = str(
            payload.get("target_node")
            or payload.get("node_id")
            or payload.get("resource_id")
            or payload.get("target")
            or (node_ids[(fallback_index + 1) % len(node_ids)] if len(node_ids) > 1 else source)
        )
        if source not in node_ids and node_ids:
            source = node_ids[fallback_index % len(node_ids)]
        if target not in node_ids and node_ids:
            target = node_ids[(fallback_index + 1) % len(node_ids)] if len(node_ids) > 1 else node_ids[0]
        return source, target

    def _build_scene_replay_frames(self, instance, topology_nodes, scene_run=None, window_start=None, window_end=None):
        frames = []

        def allowed(occurred_at):
            return not ((window_start and occurred_at < window_start) or (window_end and occurred_at > window_end))

        calls = self._capability_call_queryset().filter(instance=instance).order_by("started_at", "call_no")[:300]
        for index, row in enumerate(calls):
            if not allowed(row.started_at):
                continue
            source, target = self._scene_replay_frame_nodes(row.request_payload or {}, topology_nodes, index)
            frames.append(
                {
                    "sequence_no": len(frames) + 1,
                    "occurred_at": self._datetime_value(row.started_at),
                    "channel": "TRAFFIC",
                    "channel_label": "能力流量",
                    "source_node": source,
                    "target_node": target,
                    "protocol": (row.capability_snapshot or {}).get("method", "POST"),
                    "title": f"{row.capability.name} · {row.get_status_display()}",
                    "status": row.status,
                    "status_label": row.get_status_display(),
                    "latency_ms": row.latency_ms,
                    "reference_id": str(row.id),
                    "payload_summary": {
                        "http_status": row.http_status,
                        "source": row.source,
                        "warroom_group": row.warroom_group,
                    },
                }
            )

        alerts = self._alert_queryset().filter(instance=instance).order_by("occurred_at")[:200]
        for index, row in enumerate(alerts, len(frames)):
            if scene_run and row.scene_run_id and row.scene_run_id != scene_run.id:
                continue
            occurred_at = row.reported_at or row.occurred_at
            if not allowed(occurred_at):
                continue
            source, target = self._scene_replay_frame_nodes(
                {"source_node": "MONITOR", "resource_id": row.resource_id}, topology_nodes, index
            )
            frames.append(
                {
                    "sequence_no": len(frames) + 1,
                    "occurred_at": self._datetime_value(occurred_at),
                    "channel": "ALERT",
                    "channel_label": "告警信号",
                    "source_node": source,
                    "target_node": target,
                    "protocol": "EVENT",
                    "title": row.title,
                    "status": row.status,
                    "status_label": row.get_status_display(),
                    "latency_ms": 0,
                    "reference_id": str(row.id),
                    "payload_summary": {
                        "severity": row.severity,
                        "metric_code": row.metric_code,
                        "metric_value": row.metric_value,
                    },
                }
            )

        if scene_run:
            events = RehearsalSceneEvent.objects.filter(
                workspace_id=self.workspace_id, run=scene_run
            ).select_related("run", "step").order_by("create_time", "sequence_no")[:200]
            for index, row in enumerate(events, len(frames)):
                if not allowed(row.create_time):
                    continue
                source, target = self._scene_replay_frame_nodes(
                    {"source_node": "ORCHESTRATOR", "target_node": row.step.code if row.step_id else ""},
                    topology_nodes,
                    index,
                )
                frames.append(
                    {
                        "sequence_no": len(frames) + 1,
                        "occurred_at": self._datetime_value(row.create_time),
                        "channel": "CONTROL",
                        "channel_label": "场景控制",
                        "source_node": source,
                        "target_node": target,
                        "protocol": "EVENT",
                        "title": f"{row.get_action_display()} · {row.step.name if row.step_id else row.run.name}",
                        "status": row.current_status,
                        "status_label": row.get_current_status_display(),
                        "latency_ms": 0,
                        "reference_id": str(row.id),
                        "payload_summary": row.detail,
                    }
                )

        frames.sort(key=lambda item: (item["occurred_at"], item["channel"], item["reference_id"]))
        for index, frame in enumerate(frames, 1):
            frame["sequence_no"] = index
        return frames[:500]

    @staticmethod
    def _scene_replay_after_state(before_state, frames):
        statuses = {str(item.get("status", "")).upper() for item in frames}
        if statuses & {CapabilityCallStatus.TIMEOUT, CapabilityCallStatus.FAILED, AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED, SceneRunStatus.FAILED}:
            return "DEGRADED"
        if statuses & {AlertStatus.RECOVERED}:
            return "RECOVERED"
        if statuses & {CapabilityCallStatus.SUCCEEDED, SceneRunStatus.COMPLETED}:
            return "ACTIVE"
        return before_state or "UNKNOWN"

    def _build_scene_replay_mirror(self, topology, frames):
        topology_before = json.loads(json.dumps(topology or {}, ensure_ascii=False))
        before_nodes = topology_before.get("nodes", [])
        before_links = topology_before.get("links", [])
        node_traces = []
        after_nodes = []
        for node in before_nodes:
            node_id = str(node.get("id", ""))
            related = [
                frame for frame in frames if frame["source_node"] == node_id or frame["target_node"] == node_id
            ]
            before_state = str(node.get("state") or "UNKNOWN")
            after_state = self._scene_replay_after_state(before_state, related)
            after_nodes.append({**node, "state": after_state})
            node_traces.append(
                {
                    "node_id": node_id,
                    "node_name": node.get("name") or node_id,
                    "node_type": node.get("type", "UNKNOWN"),
                    "before_state": before_state,
                    "after_state": after_state,
                    "changed": before_state != after_state,
                    "traffic_count": len(related),
                    "attention_count": sum(
                        item["status"]
                        in (
                            CapabilityCallStatus.FAILED,
                            CapabilityCallStatus.TIMEOUT,
                            AlertStatus.ACTIVE,
                            AlertStatus.ACKNOWLEDGED,
                            SceneRunStatus.FAILED,
                        )
                        for item in related
                    ),
                    "frames": related,
                }
            )
        state_map = {str(item.get("id")): item.get("state", "UNKNOWN") for item in after_nodes}
        after_links = []
        link_deltas = []
        for link in before_links:
            before_state = str(link.get("state") or "UNKNOWN")
            endpoint_states = {state_map.get(str(link.get("source"))), state_map.get(str(link.get("target")))}
            after_state = "DEGRADED" if "DEGRADED" in endpoint_states else before_state
            after_link = {**link, "state": after_state}
            after_links.append(after_link)
            if before_state != after_state:
                link_deltas.append(
                    {
                        "source": link.get("source"),
                        "target": link.get("target"),
                        "before_state": before_state,
                        "after_state": after_state,
                    }
                )
        topology_after = {**topology_before, "nodes": after_nodes, "links": after_links}
        node_deltas = [item for item in node_traces if item["changed"]]
        mirror = {
            "node_deltas": node_deltas,
            "link_deltas": link_deltas,
            "before": {"node_count": len(before_nodes), "link_count": len(before_links)},
            "after": {
                "node_count": len(after_nodes),
                "link_count": len(after_links),
                "degraded_node_count": sum(item.get("state") == "DEGRADED" for item in after_nodes),
            },
        }
        return topology_before, topology_after, node_traces, mirror

    @transaction.atomic
    def create_scene_replay(self, instance_id, data):
        serializer = SceneReplayCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        request_id = values["request_id"].strip()
        existing = self._scene_replay_queryset().filter(request_id=request_id).first()
        if existing:
            return {"created": False, "replay": self.scene_replay_detail(existing.id)}
        instance = self._get_instance(instance_id)
        snapshot = instance.fault_configuration_snapshot or {}
        topology = snapshot.get("topology_snapshot") or {}
        if not topology.get("nodes"):
            raise AppApiException(400, "请先为预演实例应用包含拓扑快照的故障模拟配置")
        scene_run = None
        if values["scene_run_id"]:
            scene_run = RehearsalSceneRun.objects.filter(
                workspace_id=self.workspace_id,
                instance=instance,
                id=values["scene_run_id"],
            ).first()
            if scene_run is None:
                raise AppApiException(400, "关联场景执行不存在或不属于当前预演实例")
        window_start = values["window_start"] or (scene_run.started_at if scene_run else None)
        window_end = values["window_end"] or (scene_run.completed_at if scene_run else None)
        frames = self._build_scene_replay_frames(
            instance,
            topology.get("nodes", []),
            scene_run,
            window_start,
            window_end,
        )
        topology_before, topology_after, node_traces, mirror = self._build_scene_replay_mirror(topology, frames)
        latencies = [item["latency_ms"] for item in frames if item["latency_ms"] > 0]
        summary = {
            "traffic_frame_count": len(frames),
            "traffic_channel_counts": dict(Counter(item["channel"] for item in frames)),
            "attention_frame_count": sum(
                item["status"]
                in (
                    CapabilityCallStatus.FAILED,
                    CapabilityCallStatus.TIMEOUT,
                    AlertStatus.ACTIVE,
                    AlertStatus.ACKNOWLEDGED,
                    SceneRunStatus.FAILED,
                )
                for item in frames
            ),
            "average_latency_ms": round(sum(latencies) / len(latencies)) if latencies else 0,
            "node_count": len(node_traces),
            "changed_node_count": len(mirror["node_deltas"]),
            "changed_link_count": len(mirror["link_deltas"]),
            "topology_version": topology.get("version", ""),
            "fault_configuration_code": snapshot.get("code", ""),
            "fault_configuration_version": snapshot.get("version"),
        }
        immutable_payload = {
            "traffic_frames": frames,
            "topology_before": topology_before,
            "topology_after": topology_after,
            "node_traces": node_traces,
            "mirror_comparison": mirror,
            "summary": summary,
        }
        checksum = hashlib.sha256(
            json.dumps(immutable_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        digest = hashlib.sha1(request_id.encode()).hexdigest()[:6].upper()
        row = RehearsalSceneReplay.objects.create(
            workspace_id=self.workspace_id,
            instance=instance,
            scene_run=scene_run,
            fault_configuration=instance.fault_configuration,
            request_id=request_id,
            code=f"SR-{timezone.localtime():%Y%m%d}-{digest}",
            name=values["name"].strip() or f"{instance.name} · 场景动态回溯",
            description=values["description"].strip(),
            status=SceneReplayStatus.READY if frames else SceneReplayStatus.EMPTY,
            window_start=window_start,
            window_end=window_end,
            traffic_frames=frames,
            topology_before=topology_before,
            topology_after=topology_after,
            node_traces=node_traces,
            mirror_comparison=mirror,
            summary=summary,
            checksum=checksum,
            generated_at=timezone.now(),
            created_by=self.user,
        )
        self._refresh_summary(instance)
        return {"created": True, "replay": self.scene_replay_detail(row.id)}

    def scene_replay_queryset(self, params=None):
        params = params or {}
        queryset = self._scene_replay_queryset()
        if params.get("instance_id"):
            queryset = queryset.filter(instance_id=params["instance_id"])
        if params.get("scene_run_id"):
            queryset = queryset.filter(scene_run_id=params["scene_run_id"])
        if params.get("status"):
            queryset = queryset.filter(status=params["status"])
        if params.get("node_id"):
            queryset = queryset.filter(node_traces__contains=[{"node_id": str(params["node_id"])}])
        keyword = (params.get("keyword") or "").strip()
        if keyword:
            queryset = queryset.filter(
                Q(code__icontains=keyword)
                | Q(name__icontains=keyword)
                | Q(description__icontains=keyword)
                | Q(instance__code__icontains=keyword)
                | Q(instance__name__icontains=keyword)
                | Q(scene_run__name__icontains=keyword)
            )
        return queryset.order_by("-generated_at", "-update_time")

    def list_scene_replays(self, params=None):
        params = params or {}
        try:
            page = max(int(params.get("page", 1)), 1)
            page_size = min(max(int(params.get("page_size", 20)), 1), 200)
        except (TypeError, ValueError) as exc:
            raise AppApiException(400, "分页参数必须为整数") from exc
        queryset = self.scene_replay_queryset(params)
        total = queryset.count()
        start = (page - 1) * page_size
        summaries = list(queryset.values_list("summary", flat=True))
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "summary": {
                "total": total,
                "ready": queryset.filter(status=SceneReplayStatus.READY).count(),
                "empty": queryset.filter(status=SceneReplayStatus.EMPTY).count(),
                "traffic_frames": sum((item or {}).get("traffic_frame_count", 0) for item in summaries),
                "changed_nodes": sum((item or {}).get("changed_node_count", 0) for item in summaries),
                "average_latency_ms": round(
                    sum((item or {}).get("average_latency_ms", 0) for item in summaries) / len(summaries)
                ) if summaries else 0,
            },
            "items": [serialize_scene_replay(row) for row in queryset[start : start + page_size]],
        }

    def scene_replay_detail(self, replay_id):
        return serialize_scene_replay(self._get_scene_replay(replay_id), include_detail=True)

    def fault_report_template_queryset(self, params=None):
        params = params or {}
        queryset = self._fault_report_template_queryset()
        if params.get("scenario_id"):
            queryset = queryset.filter(Q(scenario_id=params["scenario_id"]) | Q(scenario_id=None))
        if params.get("status"):
            queryset = queryset.filter(status=str(params["status"]).upper())
        keyword = (params.get("keyword") or "").strip()
        if keyword:
            queryset = queryset.filter(
                Q(code__icontains=keyword) | Q(name__icontains=keyword) | Q(description__icontains=keyword)
            )
        return queryset.order_by("code", "-version")

    def list_fault_report_templates(self, params=None):
        return [serialize_fault_report_template(row) for row in self.fault_report_template_queryset(params)]

    @transaction.atomic
    def create_fault_report_template(self, data):
        serializer = FaultReportTemplateCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        request_id = values["request_id"].strip()
        existing = self._fault_report_template_queryset().filter(request_id=request_id).first()
        if existing:
            return {"created": False, "template": serialize_fault_report_template(existing)}
        scenario = None
        if values["scenario_id"]:
            scenario = RehearsalScenario.objects.filter(
                workspace_id=self.workspace_id,
                id=values["scenario_id"],
            ).exclude(status=RehearsalScenarioStatus.ARCHIVED).first()
            if scenario is None:
                raise AppApiException(400, "关联预演场景不存在或已归档")
        version = (
            RehearsalFaultReportTemplate.objects.filter(
                workspace_id=self.workspace_id,
                code=values["code"],
            ).aggregate(value=Max("version"))["value"]
            or 0
        ) + 1
        row = RehearsalFaultReportTemplate.objects.create(
            workspace_id=self.workspace_id,
            scenario=scenario,
            request_id=request_id,
            code=values["code"],
            name=values["name"].strip(),
            description=values["description"].strip(),
            version=version,
            status=FaultReportTemplateStatus.READY,
            default_level=values["default_level"],
            stage_definitions=values["stage_definitions"],
            required_fields=values["required_fields"],
            created_by=self.user,
        )
        return {"created": True, "template": serialize_fault_report_template(row)}

    @staticmethod
    def _fault_report_template_snapshot(template):
        return {
            "id": str(template.id),
            "code": template.code,
            "name": template.name,
            "version": template.version,
            "default_level": template.default_level,
            "stage_definitions": template.stage_definitions,
            "required_fields": template.required_fields,
        }

    @staticmethod
    def _fault_report_stage(snapshot, stage_code=None):
        stages = snapshot.get("stage_definitions", [])
        if not stages:
            raise AppApiException(400, "故障上报模板没有可用阶段")
        if not stage_code:
            return 0, stages[0]
        for index, item in enumerate(stages):
            if item.get("code") == stage_code:
                return index, item
        raise AppApiException(400, "当前上报阶段不在模板快照中")

    @staticmethod
    def _fault_report_attachments_with_audit(attachments, operator, event_at):
        operator_name = operator.nick_name if operator else "系统"
        return [
            {
                **item,
                "added_at": event_at.isoformat(),
                "added_by": operator_name,
            }
            for item in attachments
        ]

    def _record_fault_report_event(
        self,
        report,
        action,
        previous_status,
        previous_stage_code,
        detail=None,
    ):
        sequence_no = (
            RehearsalFaultReportEvent.objects.filter(report=report).aggregate(value=Max("sequence_no"))["value"]
            or 0
        ) + 1
        return RehearsalFaultReportEvent.objects.create(
            workspace_id=self.workspace_id,
            report=report,
            sequence_no=sequence_no,
            action=action,
            previous_status=previous_status,
            current_status=report.status,
            previous_stage_code=previous_stage_code,
            current_stage_code=report.current_stage_code,
            detail=detail or {},
            operator=self.user,
        )

    def _refresh_fault_report_summary(self, report):
        stages = (report.template_snapshot or {}).get("stage_definitions", [])
        current_index, _ = self._fault_report_stage(report.template_snapshot, report.current_stage_code)
        report.summary = {
            "stage_count": len(stages),
            "current_stage_index": current_index + 1,
            "progress_percent": {
                FaultReportStatus.DRAFT: 10,
                FaultReportStatus.REPORTED: 25,
                FaultReportStatus.RECOVERED: 90,
                FaultReportStatus.CLOSED: 100,
            }.get(
                report.status,
                min(80, 35 + round((current_index / max(len(stages) - 1, 1)) * 45)),
            ),
            "event_count": RehearsalFaultReportEvent.objects.filter(report=report).count(),
            "attachment_count": len(report.attachments or []),
            "fault_configuration_code": (report.instance.fault_configuration_snapshot or {}).get("code", ""),
            "fault_configuration_version": (report.instance.fault_configuration_snapshot or {}).get("version"),
        }
        report.save(update_fields=["summary", "update_time"])

    @transaction.atomic
    def create_fault_report(self, instance_id, data):
        serializer = FaultReportCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        request_id = values["request_id"].strip()
        existing = self._fault_report_queryset().filter(request_id=request_id).first()
        if existing:
            return {"created": False, "report": self.fault_report_detail(existing.id)}
        instance = self._get_instance(instance_id)
        if not (instance.fault_configuration_snapshot or {}).get("topology_snapshot"):
            raise AppApiException(400, "请先为预演实例应用故障模拟配置")
        template = self._get_fault_report_template(values["template_id"])
        if template.status != FaultReportTemplateStatus.READY:
            raise AppApiException(400, "请选择可使用的故障上报模板")
        if template.scenario_id and template.scenario_id != instance.scenario_id:
            raise AppApiException(400, "故障上报模板与预演实例场景不匹配")
        field_values = {
            "title": values["title"].strip(),
            "description": values["description"].strip(),
            "impact_scope": values["impact_scope"].strip(),
        }
        missing_fields = [field for field in template.required_fields if not field_values.get(field)]
        if missing_fields:
            raise AppApiException(400, f"缺少模板必填字段：{', '.join(missing_fields)}")
        scene_run = None
        if values["scene_run_id"]:
            scene_run = RehearsalSceneRun.objects.filter(
                workspace_id=self.workspace_id,
                instance=instance,
                id=values["scene_run_id"],
            ).first()
            if scene_run is None:
                raise AppApiException(400, "关联场景执行不存在或不属于当前预演实例")
        snapshot = self._fault_report_template_snapshot(template)
        _, first_stage = self._fault_report_stage(snapshot)
        event_at = timezone.now()
        attachments = self._fault_report_attachments_with_audit(values["attachments"], self.user, event_at)
        digest = hashlib.sha1(request_id.encode()).hexdigest()[:6].upper()
        row = RehearsalFaultReport.objects.create(
            workspace_id=self.workspace_id,
            instance=instance,
            template=template,
            scene_run=scene_run,
            request_id=request_id,
            code=f"FR-{timezone.localtime():%Y%m%d}-{digest}",
            title=field_values["title"],
            description=field_values["description"],
            impact_scope=field_values["impact_scope"],
            level=values["level"] or template.default_level,
            status=FaultReportStatus.DRAFT,
            current_stage_code=first_stage["code"],
            current_stage_name=first_stage["name"],
            occurred_at=values["occurred_at"],
            stage_started_at=event_at,
            stage_deadline_at=event_at + timedelta(minutes=first_stage["duration_minutes"]),
            attachments=attachments,
            template_snapshot=snapshot,
            created_by=self.user,
        )
        self._record_fault_report_event(
            row,
            FaultReportAction.CREATED,
            FaultReportStatus.DRAFT,
            "",
            {
                "level": row.level,
                "stage_name": row.current_stage_name,
                "deadline_at": row.stage_deadline_at.isoformat(),
                "attachment_count": len(attachments),
            },
        )
        self._record_event(
            instance,
            RehearsalEventType.FAULT_REPORT_UPDATED,
            instance.status,
            {"report_id": str(row.id), "report_code": row.code, "action": FaultReportAction.CREATED},
        )
        self._refresh_fault_report_summary(row)
        self._refresh_summary(instance)
        return {"created": True, "report": self.fault_report_detail(row.id)}

    def fault_report_queryset(self, params=None):
        params = params or {}
        queryset = self._fault_report_queryset()
        if params.get("instance_id"):
            queryset = queryset.filter(instance_id=params["instance_id"])
        if params.get("template_id"):
            queryset = queryset.filter(template_id=params["template_id"])
        if params.get("status"):
            queryset = queryset.filter(status=str(params["status"]).upper())
        if params.get("level"):
            queryset = queryset.filter(level=str(params["level"]).upper())
        if str(params.get("overdue") or "").lower() in ("1", "true", "yes"):
            queryset = queryset.filter(
                status__in=(FaultReportStatus.DRAFT, FaultReportStatus.REPORTED, FaultReportStatus.PROCESSING),
                stage_deadline_at__lt=timezone.now(),
            )
        keyword = (params.get("keyword") or "").strip()
        if keyword:
            queryset = queryset.filter(
                Q(code__icontains=keyword)
                | Q(title__icontains=keyword)
                | Q(description__icontains=keyword)
                | Q(impact_scope__icontains=keyword)
                | Q(instance__code__icontains=keyword)
                | Q(instance__name__icontains=keyword)
            )
        return queryset.order_by("-occurred_at", "-create_time")

    def list_fault_reports(self, params=None):
        params = params or {}
        try:
            page = max(int(params.get("page", 1)), 1)
            page_size = min(max(int(params.get("page_size", 20)), 1), 200)
        except (TypeError, ValueError) as exc:
            raise AppApiException(400, "分页参数必须为整数") from exc
        queryset = self.fault_report_queryset(params)
        total = queryset.count()
        start = (page - 1) * page_size
        now = timezone.now()
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "summary": {
                "total": total,
                "draft": queryset.filter(status=FaultReportStatus.DRAFT).count(),
                "active": queryset.filter(
                    status__in=(FaultReportStatus.REPORTED, FaultReportStatus.PROCESSING)
                ).count(),
                "recovered": queryset.filter(status=FaultReportStatus.RECOVERED).count(),
                "closed": queryset.filter(status=FaultReportStatus.CLOSED).count(),
                "overdue": queryset.filter(
                    status__in=(FaultReportStatus.DRAFT, FaultReportStatus.REPORTED, FaultReportStatus.PROCESSING),
                    stage_deadline_at__lt=now,
                ).count(),
                "attachments": sum(len(value or []) for value in queryset.values_list("attachments", flat=True)),
            },
            "items": [serialize_fault_report(row) for row in queryset[start : start + page_size]],
        }

    def fault_report_detail(self, report_id):
        row = (
            self._fault_report_queryset()
            .prefetch_related("events__operator")
            .filter(id=report_id)
            .first()
        )
        if row is None:
            raise AppApiException(404, "故障上报记录不存在")
        return serialize_fault_report(row, include_detail=True)

    @transaction.atomic
    def operate_fault_report(self, report_id, data):
        serializer = FaultReportOperateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        row = self._get_fault_report(report_id, lock=True)
        action = values["action"]
        if action not in fault_report_allowed_actions(row):
            raise AppApiException(400, "当前故障上报状态不允许执行该操作")
        if action in (
            FaultReportAction.STAGE_ADVANCED,
            FaultReportAction.ESCALATED,
            FaultReportAction.RECOVERED,
            FaultReportAction.CLOSED,
        ) and not values["note"].strip():
            raise AppApiException(400, "该操作必须填写说明")
        event_at = values["event_at"]
        previous_status = row.status
        previous_stage_code = row.current_stage_code
        detail = {"note": values["note"].strip(), "event_at": event_at.isoformat()}
        current_index, current_stage = self._fault_report_stage(row.template_snapshot, row.current_stage_code)

        if action == FaultReportAction.SUBMITTED:
            row.status = FaultReportStatus.REPORTED
            row.reported_at = event_at
        elif action == FaultReportAction.ACCEPTED:
            row.status = FaultReportStatus.PROCESSING
            row.accepted_at = event_at
            row.stage_started_at = event_at
            row.stage_deadline_at = event_at + timedelta(minutes=current_stage["duration_minutes"])
        elif action == FaultReportAction.STAGE_ADVANCED:
            stages = row.template_snapshot.get("stage_definitions", [])
            if current_index >= len(stages) - 1:
                raise AppApiException(400, "当前已是最后一个上报阶段")
            next_stage = stages[current_index + 1]
            row.current_stage_code = next_stage["code"]
            row.current_stage_name = next_stage["name"]
            row.stage_started_at = event_at
            row.stage_deadline_at = event_at + timedelta(minutes=next_stage["duration_minutes"])
            detail["next_stage_name"] = next_stage["name"]
            detail["deadline_at"] = row.stage_deadline_at.isoformat()
        elif action == FaultReportAction.ESCALATED:
            target_level = values["level"]
            if not target_level:
                raise AppApiException(400, "升级故障必须选择目标等级")
            level_order = {
                FaultReportLevel.LEVEL_1: 1,
                FaultReportLevel.LEVEL_2: 2,
                FaultReportLevel.LEVEL_3: 3,
                FaultReportLevel.LEVEL_4: 4,
            }
            if level_order[target_level] >= level_order[row.level]:
                raise AppApiException(400, "目标等级必须高于当前故障等级")
            detail.update({"previous_level": row.level, "current_level": target_level})
            row.level = target_level
        elif action == FaultReportAction.ATTACHMENT_ADDED:
            if not values["attachments"]:
                raise AppApiException(400, "请至少添加一个附件引用")
            existing_references = {item.get("reference_id") for item in row.attachments or []}
            duplicate_references = [
                item["reference_id"] for item in values["attachments"] if item["reference_id"] in existing_references
            ]
            if duplicate_references:
                raise AppApiException(400, f"附件引用已经存在：{', '.join(duplicate_references)}")
            added = self._fault_report_attachments_with_audit(values["attachments"], self.user, event_at)
            row.attachments = [*(row.attachments or []), *added]
            detail["attachments"] = added
        elif action == FaultReportAction.RECOVERED:
            row.status = FaultReportStatus.RECOVERED
            row.recovered_at = event_at
        elif action == FaultReportAction.CLOSED:
            row.status = FaultReportStatus.CLOSED
            row.closed_at = event_at

        row.save()
        self._record_fault_report_event(
            row,
            action,
            previous_status,
            previous_stage_code,
            detail,
        )
        self._record_event(
            row.instance,
            RehearsalEventType.FAULT_REPORT_UPDATED,
            row.instance.status,
            {
                "report_id": str(row.id),
                "report_code": row.code,
                "action": action,
                "status": row.status,
                "stage_code": row.current_stage_code,
            },
        )
        self._refresh_fault_report_summary(row)
        self._refresh_summary(row.instance)
        return {"report": self.fault_report_detail(row.id)}

    @staticmethod
    def _sample_random_factor(rng, factor):
        minimum = factor["min_value"]
        maximum = factor["max_value"]
        if factor["distribution"] == RandomFactorDistribution.NORMAL:
            value = rng.gauss((minimum + maximum) / 2, (maximum - minimum) / 6)
            return round(min(maximum, max(minimum, value)), 4)
        return round(rng.uniform(minimum, maximum), 4)

    @staticmethod
    def _metric_statistics(points, code, baseline):
        values = [float(item[code]) for item in points]
        mean = sum(values) / len(values) if values else 0
        variance = sum((value - mean) ** 2 for value in values) / len(values) if values else 0
        delta_percent = ((mean - baseline) / baseline * 100) if baseline else 0
        return {
            "code": code,
            "baseline": round(baseline, 4),
            "mean": round(mean, 4),
            "peak": round(max(values) if values else 0, 4),
            "variance": round(variance, 4),
            "delta_percent": round(delta_percent, 2),
        }

    def _build_auxiliary_result(self, instance, seed, duration_minutes, factors, started_at):
        rng = random.Random(seed)
        snapshots = []
        for factor in factors:
            triggered = rng.random() <= factor["trigger_probability"]
            value = self._sample_random_factor(rng, factor) if triggered else 0
            trigger_minute = rng.randint(1, max(1, duration_minutes // 2)) if triggered else None
            snapshots.append(
                {
                    **factor,
                    "triggered": triggered,
                    "sampled_value": value,
                    "trigger_minute": trigger_minute,
                }
            )

        factor_map = {item["code"]: item for item in snapshots if item["triggered"]}
        base_complaints = max(1.0, RehearsalComplaint.objects.filter(instance=instance).count() / max(duration_minutes, 1))
        baseline = {
            "latency_ms": 45.0,
            "packet_loss_pct": 0.05,
            "traffic_multiplier": 1.0,
            "complaint_count": base_complaints,
            "ticket_backlog": float(RehearsalWorkOrder.objects.filter(scene_run__instance=instance).count()),
            "timeout_rate_pct": 5.0,
        }
        points = []
        anomalies = []
        for minute in range(duration_minutes + 1):
            wave = 0.55 + 0.45 * math.sin((minute / max(duration_minutes, 1)) * math.pi)

            def active(code):
                item = factor_map.get(code)
                return item if item and minute >= item["trigger_minute"] else None

            jitter = active("NETWORK_JITTER")
            loss = active("PACKET_LOSS")
            propagation = active("PROPAGATION_DELAY")
            spread = active("FAULT_SPREAD")
            traffic = active("TRAFFIC_PEAK")
            frequency = active("TRAFFIC_FREQUENCY")
            frequency_wave = 1.0
            if frequency:
                period = max(frequency["sampled_value"], 1)
                frequency_wave = 0.55 + 0.45 * abs(math.sin(minute * math.pi / period))
            noise = rng.uniform(-0.025, 0.025)
            traffic_multiplier = baseline["traffic_multiplier"]
            if traffic:
                traffic_multiplier += (traffic["sampled_value"] - 1) * wave * frequency_wave
            latency = baseline["latency_ms"] + (jitter["sampled_value"] * wave if jitter else 0)
            packet_loss = baseline["packet_loss_pct"] + (loss["sampled_value"] * wave if loss else 0)
            spread_value = spread["sampled_value"] if spread else 1
            complaint_count = baseline["complaint_count"] * traffic_multiplier * (1 + packet_loss / 7) * spread_value
            timeout_rate = baseline["timeout_rate_pct"] + packet_loss * 2.2
            if propagation:
                timeout_rate += propagation["sampled_value"] / 18
            ticket_backlog = baseline["ticket_backlog"] + complaint_count * (timeout_rate / 100) * 1.8
            point = {
                "minute": minute,
                "occurred_at": (started_at + timedelta(minutes=minute)).isoformat(),
                "latency_ms": round(max(0, latency * (1 + noise)), 2),
                "packet_loss_pct": round(max(0, packet_loss * (1 + noise)), 3),
                "traffic_multiplier": round(max(1, traffic_multiplier * (1 + noise)), 3),
                "complaint_count": round(max(0, complaint_count * (1 + noise)), 2),
                "ticket_backlog": round(max(0, ticket_backlog * (1 + noise)), 2),
                "timeout_rate_pct": round(min(100, max(0, timeout_rate * (1 + noise))), 2),
            }
            points.append(point)
            reasons = []
            if point["packet_loss_pct"] >= 3:
                reasons.append(f"丢包率升至 {point['packet_loss_pct']}%")
            if point["latency_ms"] >= 110:
                reasons.append(f"网络时延升至 {point['latency_ms']}ms")
            if point["traffic_multiplier"] >= 2.5:
                reasons.append(f"流量峰值达到 {point['traffic_multiplier']} 倍")
            if point["timeout_rate_pct"] >= 20:
                reasons.append(f"工单响应超时率升至 {point['timeout_rate_pct']}%")
            if reasons and (not anomalies or minute - anomalies[-1]["minute"] >= 5):
                anomalies.append({"minute": minute, "occurred_at": point["occurred_at"], "reasons": reasons})

        metric_labels = {
            "latency_ms": "网络时延(ms)",
            "packet_loss_pct": "丢包率(%)",
            "traffic_multiplier": "流量倍率",
            "complaint_count": "申告量",
            "ticket_backlog": "工单积压",
            "timeout_rate_pct": "响应超时率(%)",
        }
        statistics = []
        for code, label in metric_labels.items():
            statistic = self._metric_statistics(points, code, baseline[code])
            statistic["name"] = label
            statistics.append(statistic)
        impact_analysis = []
        for item in snapshots:
            if not item["triggered"]:
                impact_analysis.append(f"{item['name']}未命中 {round(item['trigger_probability'] * 100)}% 触发概率，本批次未生效。")
            elif item["category"] == RandomFactorCategory.NETWORK:
                impact_analysis.append(
                    f"{item['name']}在第 {item['trigger_minute']} 分钟触发，采样强度 {item['sampled_value']}{item['unit']}，推高网络质量波动。"
                )
            elif item["category"] == RandomFactorCategory.FAULT:
                impact_analysis.append(
                    f"{item['name']}在第 {item['trigger_minute']} 分钟触发，采样强度 {item['sampled_value']}{item['unit']}，增加故障处置压力。"
                )
            else:
                impact_analysis.append(
                    f"{item['name']}在第 {item['trigger_minute']} 分钟触发，采样强度 {item['sampled_value']}{item['unit']}，带来业务流量与申告峰值。"
                )
        peak_point = max(points, key=lambda item: item["timeout_rate_pct"] + item["packet_loss_pct"] * 5)
        result = {
            "summary": {
                "point_count": len(points),
                "triggered_factor_count": len(factor_map),
                "anomaly_count": len(anomalies),
                "conclusion": (
                    f"组合随机因子命中 {len(factor_map)}/{len(snapshots)} 项，识别 {len(anomalies)} 个异常窗口；"
                    f"峰值响应超时率 {max(item['timeout_rate_pct'] for item in points)}%。"
                ),
            },
            "statistics": statistics,
            "impact_analysis": impact_analysis,
            "anomalies": anomalies,
            "key_moments": [
                {"minute": 0, "label": "模拟开始", "occurred_at": points[0]["occurred_at"]},
                {"minute": peak_point["minute"], "label": "影响峰值", "occurred_at": peak_point["occurred_at"]},
                {"minute": duration_minutes, "label": "模拟结束", "occurred_at": points[-1]["occurred_at"]},
            ],
            "points": points,
            "baseline": baseline,
        }
        return snapshots, result

    @transaction.atomic
    def create_auxiliary_simulation(self, instance_id, data):
        serializer = AuxiliarySimulationCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        request_id = values["request_id"].strip()
        existing = self._auxiliary_simulation_queryset().filter(request_id=request_id).first()
        if existing:
            return {"created": False, "simulation": self.auxiliary_simulation_detail(existing.id)}
        instance = self._get_instance(instance_id)
        started_at = timezone.now()
        factor_snapshot, result_snapshot = self._build_auxiliary_result(
            instance,
            values["seed"],
            values["duration_minutes"],
            values["factors"],
            started_at,
        )
        canonical = {
            "seed": values["seed"],
            "duration_minutes": values["duration_minutes"],
            "factors": factor_snapshot,
            "points": [{key: value for key, value in point.items() if key != "occurred_at"} for point in result_snapshot["points"]],
        }
        checksum = hashlib.sha256(json.dumps(canonical, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        digest = hashlib.sha1(request_id.encode()).hexdigest()[:6].upper()
        row = RehearsalAuxiliarySimulation.objects.create(
            workspace_id=self.workspace_id,
            instance=instance,
            request_id=request_id,
            code=f"AUX-{timezone.localtime():%Y%m%d}-{digest}",
            name=values["name"].strip() or f"{instance.name} · 随机因子组合模拟",
            seed=values["seed"],
            duration_minutes=values["duration_minutes"],
            status=(AuxiliarySimulationStatus.ATTENTION if result_snapshot["anomalies"] else AuxiliarySimulationStatus.COMPLETED),
            factor_snapshot=factor_snapshot,
            result_snapshot=result_snapshot,
            checksum=checksum,
            started_at=started_at,
            completed_at=started_at + timedelta(minutes=values["duration_minutes"]),
            created_by=self.user,
        )
        self._record_event(
            instance,
            RehearsalEventType.AUXILIARY_SIMULATED,
            instance.status,
            {
                "simulation_id": str(row.id),
                "simulation_code": row.code,
                "seed": row.seed,
                "factor_count": len(factor_snapshot),
                "triggered_factor_count": result_snapshot["summary"]["triggered_factor_count"],
                "anomaly_count": result_snapshot["summary"]["anomaly_count"],
                "checksum": checksum,
            },
        )
        self._refresh_summary(instance)
        return {"created": True, "simulation": self.auxiliary_simulation_detail(row.id)}

    def auxiliary_simulation_queryset(self, params=None):
        params = params or {}
        queryset = self._auxiliary_simulation_queryset()
        if params.get("instance_id"):
            queryset = queryset.filter(instance_id=params["instance_id"])
        if params.get("status"):
            queryset = queryset.filter(status=str(params["status"]).upper())
        if params.get("seed") not in (None, ""):
            queryset = queryset.filter(seed=params["seed"])
        keyword = (params.get("keyword") or "").strip()
        if keyword:
            queryset = queryset.filter(
                Q(code__icontains=keyword) | Q(name__icontains=keyword) | Q(instance__name__icontains=keyword)
            )
        return queryset.order_by("-started_at", "-create_time")

    def list_auxiliary_simulations(self, params=None):
        params = params or {}
        try:
            page = max(int(params.get("page", 1)), 1)
            page_size = min(max(int(params.get("page_size", 20)), 1), 200)
        except (TypeError, ValueError) as exc:
            raise AppApiException(400, "分页参数必须为整数") from exc
        queryset = self.auxiliary_simulation_queryset(params)
        total = queryset.count()
        start = (page - 1) * page_size
        rows = list(queryset)
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "summary": {
                "total": total,
                "attention": sum(row.status == AuxiliarySimulationStatus.ATTENTION for row in rows),
                "factor_count": sum(len(row.factor_snapshot or []) for row in rows),
                "triggered_factor_count": sum(
                    sum(1 for item in row.factor_snapshot or [] if item.get("triggered")) for row in rows
                ),
                "anomaly_count": sum(len((row.result_snapshot or {}).get("anomalies", [])) for row in rows),
            },
            "items": [serialize_auxiliary_simulation(row) for row in rows[start : start + page_size]],
        }

    def auxiliary_simulation_detail(self, simulation_id):
        return serialize_auxiliary_simulation(self._get_auxiliary_simulation(simulation_id), include_detail=True)

    @staticmethod
    def _simulation_record_duration(started_at, completed_at):
        if not started_at:
            return 0
        end_at = completed_at or timezone.now()
        return max(int((end_at - started_at).total_seconds()), 0)

    @staticmethod
    def _simulation_record_state(kind, status):
        state_maps = {
            "INSTANCE": {
                RehearsalInstanceStatus.DRAFT: "PENDING",
                RehearsalInstanceStatus.READY: "PENDING",
                RehearsalInstanceStatus.RUNNING: "RUNNING",
                RehearsalInstanceStatus.COMPLETED: "SUCCEEDED",
                RehearsalInstanceStatus.CANCELLED: "ATTENTION",
                RehearsalInstanceStatus.FAILED: "FAILED",
            },
            "COMPLAINT_BATCH": {
                ComplaintBatchStatus.READY: "SUCCEEDED",
                ComplaintBatchStatus.PARTIAL: "ATTENTION",
                ComplaintBatchStatus.FAILED: "FAILED",
            },
            "DATA_BATCH": {
                DataSimulationStatus.READY: "SUCCEEDED",
                DataSimulationStatus.FAILED: "FAILED",
            },
            "PROCESS_RUN": {
                ProcessRunStatus.PENDING: "PENDING",
                ProcessRunStatus.RUNNING: "RUNNING",
                ProcessRunStatus.BLOCKED: "ATTENTION",
                ProcessRunStatus.COMPLETED: "SUCCEEDED",
                ProcessRunStatus.CANCELLED: "ATTENTION",
                ProcessRunStatus.FAILED: "FAILED",
            },
            "SCENE_RUN": {
                SceneRunStatus.PENDING: "PENDING",
                SceneRunStatus.RUNNING: "RUNNING",
                SceneRunStatus.COMPLETED: "SUCCEEDED",
                SceneRunStatus.CANCELLED: "ATTENTION",
                SceneRunStatus.FAILED: "FAILED",
            },
            "ALERT": {
                AlertStatus.PENDING: "PENDING",
                AlertStatus.ACTIVE: "RUNNING",
                AlertStatus.ACKNOWLEDGED: "ATTENTION",
                AlertStatus.RECOVERED: "SUCCEEDED",
            },
            "TRACEBACK": {
                TracebackStatus.READY: "SUCCEEDED",
                TracebackStatus.EMPTY: "ATTENTION",
                TracebackStatus.ARCHIVED: "SUCCEEDED",
            },
            "CAPABILITY_CALL": {
                CapabilityCallStatus.SUCCEEDED: "SUCCEEDED",
                CapabilityCallStatus.FAILED: "FAILED",
                CapabilityCallStatus.TIMEOUT: "ATTENTION",
            },
            "FAULT_REPORT": {
                FaultReportStatus.DRAFT: "PENDING",
                FaultReportStatus.REPORTED: "RUNNING",
                FaultReportStatus.PROCESSING: "RUNNING",
                FaultReportStatus.RECOVERED: "SUCCEEDED",
                FaultReportStatus.CLOSED: "SUCCEEDED",
            },
            "AUXILIARY_SIMULATION": {
                AuxiliarySimulationStatus.COMPLETED: "SUCCEEDED",
                AuxiliarySimulationStatus.ATTENTION: "ATTENTION",
            },
        }
        return state_maps.get(kind, {}).get(status, "ATTENTION")

    def _simulation_record_item(
        self,
        *,
        kind,
        row,
        instance,
        name,
        status,
        status_label,
        progress_percent,
        result_summary,
        event_count,
        started_at,
        completed_at,
    ):
        state = self._simulation_record_state(kind, status)
        return {
            "record_key": f"{kind}:{row.id}",
            "kind": kind,
            "kind_label": SIMULATION_RECORD_KIND_LABELS[kind],
            "resource_id": str(row.id),
            "instance_id": str(instance.id),
            "instance_code": instance.code,
            "instance_name": instance.name,
            "code": getattr(row, "code", f"BATCH-{str(row.id)[:8].upper()}"),
            "name": name,
            "status": status,
            "status_label": status_label,
            "state": state,
            "state_label": SIMULATION_RECORD_STATE_LABELS[state],
            "progress_percent": max(0, min(int(progress_percent), 100)),
            "occurrence_no": 0,
            "result_summary": result_summary,
            "event_count": event_count,
            "started_at": started_at,
            "completed_at": completed_at,
            "duration_seconds": self._simulation_record_duration(started_at, completed_at),
            "create_time": row.create_time,
            "update_time": row.update_time,
            "_sort_at": completed_at or started_at or row.update_time or row.create_time,
        }

    def _build_simulation_records(self):
        records = []
        instances = self._instance_queryset().annotate(record_event_count=Count("events", distinct=True))
        for row in instances:
            progress = {
                RehearsalInstanceStatus.DRAFT: 10,
                RehearsalInstanceStatus.READY: 35,
                RehearsalInstanceStatus.RUNNING: 70,
                RehearsalInstanceStatus.COMPLETED: 100,
                RehearsalInstanceStatus.CANCELLED: 100,
                RehearsalInstanceStatus.FAILED: 100,
            }.get(row.status, 0)
            records.append(
                self._simulation_record_item(
                    kind="INSTANCE",
                    row=row,
                    instance=row,
                    name=row.name,
                    status=row.status,
                    status_label=row.get_status_display(),
                    progress_percent=progress,
                    result_summary=(
                        f"{row.complaint_count} 条有效申告 · {row.process_runs.count()} 个流程 · "
                        f"{row.scene_run_count} 次场景执行"
                    ),
                    event_count=row.record_event_count,
                    started_at=row.started_at,
                    completed_at=row.completed_at,
                )
            )

        complaint_batches = RehearsalComplaintBatch.objects.filter(workspace_id=self.workspace_id).select_related(
            "instance", "template"
        )
        for row in complaint_batches:
            progress = round((row.valid_count / row.total_count) * 100) if row.total_count else 0
            records.append(
                self._simulation_record_item(
                    kind="COMPLAINT_BATCH",
                    row=row,
                    instance=row.instance,
                    name=row.template.name if row.template_id else row.filename or "人工导入申告批次",
                    status=row.status,
                    status_label=row.get_status_display(),
                    progress_percent=progress,
                    result_summary=f"{row.valid_count} 条有效 · {row.invalid_count} 条异常",
                    event_count=row.total_count,
                    started_at=row.time_start or row.create_time,
                    completed_at=row.time_end or row.update_time,
                )
            )

        for row in self._data_batch_queryset():
            records.append(
                self._simulation_record_item(
                    kind="DATA_BATCH",
                    row=row,
                    instance=row.instance,
                    name=row.name,
                    status=row.status,
                    status_label=row.get_status_display(),
                    progress_percent=100 if row.status == DataSimulationStatus.READY else 0,
                    result_summary=f"{row.get_kind_display()} · {row.point_count} 个时序点 · V{row.version}",
                    event_count=row.point_count,
                    started_at=row.time_start,
                    completed_at=row.time_end,
                )
            )

        process_runs = self._process_run_queryset().annotate(record_event_count=Count("events", distinct=True))
        for row in process_runs:
            records.append(
                self._simulation_record_item(
                    kind="PROCESS_RUN",
                    row=row,
                    instance=row.instance,
                    name=row.name,
                    status=row.status,
                    status_label=row.get_status_display(),
                    progress_percent=row.progress_percent,
                    result_summary=f"{row.completed_steps}/{row.total_steps} 步完成"
                    + (f" · {row.blocked_reason}" if row.blocked_reason else ""),
                    event_count=row.record_event_count,
                    started_at=row.started_at,
                    completed_at=row.completed_at,
                )
            )

        scene_runs = self._scene_run_queryset().annotate(record_event_count=Count("events", distinct=True))
        for row in scene_runs:
            records.append(
                self._simulation_record_item(
                    kind="SCENE_RUN",
                    row=row,
                    instance=row.instance,
                    name=row.name,
                    status=row.status,
                    status_label=row.get_status_display(),
                    progress_percent=row.progress_percent,
                    result_summary=(
                        f"{row.completed_steps}/{row.total_steps} 步完成 · "
                        f"{row.work_order_count} 张工单 · {row.alert_count} 条告警"
                    ),
                    event_count=row.record_event_count,
                    started_at=row.started_at,
                    completed_at=row.completed_at,
                )
            )

        for row in self._alert_queryset():
            progress = {
                AlertStatus.PENDING: 20,
                AlertStatus.ACTIVE: 45,
                AlertStatus.ACKNOWLEDGED: 75,
                AlertStatus.RECOVERED: 100,
            }.get(row.status, 0)
            result = f"{row.get_severity_display()} · {row.resource_name or row.resource_id or '未指定网元'}"
            if row.metric_value is not None:
                result += f" · {row.metric_name or row.metric_code or '指标'}={row.metric_value}"
            records.append(
                self._simulation_record_item(
                    kind="ALERT",
                    row=row,
                    instance=row.instance,
                    name=row.title,
                    status=row.status,
                    status_label=row.get_status_display(),
                    progress_percent=progress,
                    result_summary=result,
                    event_count=row.event_count,
                    started_at=row.reported_at or row.occurred_at,
                    completed_at=row.recovered_at,
                )
            )

        for row in self._traceback_queryset():
            records.append(
                self._simulation_record_item(
                    kind="TRACEBACK",
                    row=row,
                    instance=row.instance,
                    name=row.name,
                    status=row.status,
                    status_label=row.get_status_display(),
                    progress_percent=100 if row.status != TracebackStatus.EMPTY else 0,
                    result_summary=(
                        f"{row.total_events} 个事实 · {(row.summary or {}).get('node_count', 0)} 个节点 · "
                        f"{(row.summary or {}).get('transition_count', 0)} 组转移"
                    ),
                    event_count=row.total_events,
                    started_at=row.window_start or row.generated_at,
                    completed_at=row.window_end or row.generated_at,
                )
            )

        for row in self._capability_call_queryset():
            records.append(
                self._simulation_record_item(
                    kind="CAPABILITY_CALL",
                    row=row,
                    instance=row.instance,
                    name=row.capability.name,
                    status=row.status,
                    status_label=row.get_status_display(),
                    progress_percent=100,
                    result_summary=(
                        f"{row.capability.get_kind_display()} · HTTP {row.http_status} · "
                        f"{row.latency_ms}ms · {row.warroom_group}"
                    ),
                    event_count=1,
                    started_at=row.started_at,
                    completed_at=row.finished_at,
                )
            )

        for row in self._fault_report_queryset():
            report_data = serialize_fault_report(row)
            records.append(
                self._simulation_record_item(
                    kind="FAULT_REPORT",
                    row=row,
                    instance=row.instance,
                    name=row.title,
                    status=row.status,
                    status_label=row.get_status_display(),
                    progress_percent=report_data["progress_percent"],
                    result_summary=(
                        f"{row.get_level_display()} · {row.current_stage_name} · "
                        f"{len(row.attachments or [])} 个附件"
                    ),
                    event_count=row.event_count,
                    started_at=row.reported_at or row.occurred_at,
                    completed_at=row.closed_at or row.recovered_at,
                )
            )

        for row in self._auxiliary_simulation_queryset():
            summary = (row.result_snapshot or {}).get("summary", {})
            records.append(
                self._simulation_record_item(
                    kind="AUXILIARY_SIMULATION",
                    row=row,
                    instance=row.instance,
                    name=row.name,
                    status=row.status,
                    status_label=row.get_status_display(),
                    progress_percent=100,
                    result_summary=(
                        f"种子 {row.seed} · {summary.get('triggered_factor_count', 0)}/{len(row.factor_snapshot or [])} "
                        f"项命中 · {summary.get('anomaly_count', 0)} 个异常窗口"
                    ),
                    event_count=len((row.result_snapshot or {}).get("key_moments", [])),
                    started_at=row.started_at,
                    completed_at=row.completed_at,
                )
            )

        counters = Counter()
        for record in sorted(records, key=lambda item: item["create_time"]):
            counter_key = (record["instance_id"], record["kind"])
            counters[counter_key] += 1
            record["occurrence_no"] = counters[counter_key]
        return records

    def simulation_records(self, params=None):
        params = params or {}
        records = self._build_simulation_records()
        if params.get("instance_id"):
            records = [item for item in records if item["instance_id"] == str(params["instance_id"])]
        if params.get("kind"):
            records = [item for item in records if item["kind"] == str(params["kind"]).upper()]
        if params.get("state"):
            records = [item for item in records if item["state"] == str(params["state"]).upper()]
        if params.get("date_from"):
            records = [
                item for item in records if item["_sort_at"].date().isoformat() >= str(params["date_from"])
            ]
        if params.get("date_to"):
            records = [
                item for item in records if item["_sort_at"].date().isoformat() <= str(params["date_to"])
            ]
        keyword = (params.get("keyword") or "").strip().lower()
        if keyword:
            records = [
                item
                for item in records
                if keyword
                in " ".join(
                    (
                        item["code"],
                        item["name"],
                        item["instance_code"],
                        item["instance_name"],
                        item["result_summary"],
                    )
                ).lower()
            ]
        return sorted(records, key=lambda item: item["_sort_at"], reverse=True)

    def list_simulation_records(self, params=None):
        params = params or {}
        try:
            page = max(int(params.get("page", 1)), 1)
            page_size = min(max(int(params.get("page_size", 20)), 1), 200)
        except (TypeError, ValueError) as exc:
            raise AppApiException(400, "分页参数必须为整数") from exc
        records = self.simulation_records(params)
        state_counts = Counter(item["state"] for item in records)
        kind_counts = Counter(item["kind"] for item in records)
        durations = [item["duration_seconds"] for item in records if item["duration_seconds"] > 0]
        total = len(records)
        start = (page - 1) * page_size
        items = records[start : start + page_size]
        for item in items:
            item.pop("_sort_at", None)
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "summary": {
                "total": total,
                "pending": state_counts["PENDING"],
                "running": state_counts["RUNNING"],
                "succeeded": state_counts["SUCCEEDED"],
                "attention": state_counts["ATTENTION"],
                "failed": state_counts["FAILED"],
                "average_duration_seconds": round(sum(durations) / len(durations)) if durations else 0,
                "kind_counts": dict(kind_counts),
            },
            "items": items,
        }

    def simulation_record_detail(self, kind, record_id):
        normalized_kind = str(kind).upper()
        if normalized_kind not in SIMULATION_RECORD_KIND_LABELS:
            raise AppApiException(400, "不支持的模拟记录类型")
        record = next(
            (
                item
                for item in self._build_simulation_records()
                if item["kind"] == normalized_kind and item["resource_id"] == str(record_id)
            ),
            None,
        )
        if record is None:
            raise AppApiException(404, "模拟记录不存在")
        record.pop("_sort_at", None)

        if normalized_kind == "INSTANCE":
            payload = self.instance_detail(record_id)
            activity = [
                {
                    "sequence_no": item["sequence_no"],
                    "label": item["event_type_label"],
                    "status_label": item["current_status_label"],
                    "occurred_at": item["create_time"],
                    "detail": item["detail"],
                }
                for item in payload.get("events", [])
            ]
        elif normalized_kind == "COMPLAINT_BATCH":
            row = self._get_batch(record_id)
            payload = serialize_batch(row)
            payload["complaints"] = [serialize_complaint(item) for item in row.complaints.all()[:200]]
            activity = [
                {
                    "sequence_no": item["sequence_no"],
                    "label": item["title"],
                    "status_label": item["validation_status_label"],
                    "occurred_at": item["occurred_at"],
                    "detail": {"category": item["category"], "severity": item["severity_label"]},
                }
                for item in payload["complaints"]
            ]
        elif normalized_kind == "DATA_BATCH":
            payload = self.data_batch_detail(record_id)
            activity = [
                {
                    "sequence_no": item["sequence_no"],
                    "label": item["narrative"] or f"时序点 {item['sequence_no']}",
                    "status_label": payload["status_label"],
                    "occurred_at": item["occurred_at"],
                    "detail": item["values"],
                }
                for item in payload.get("points", [])[:200]
            ]
        elif normalized_kind == "PROCESS_RUN":
            payload = self.process_run_detail(record_id)
            activity = [
                {
                    "sequence_no": item["sequence_no"],
                    "label": item["action_label"],
                    "status_label": item["current_status_label"],
                    "occurred_at": item["create_time"],
                    "detail": item["detail"],
                }
                for item in payload.get("events", [])
            ]
        elif normalized_kind == "SCENE_RUN":
            payload = self.scene_run_detail(record_id)
            activity = [
                {
                    "sequence_no": item["sequence_no"],
                    "label": item["action_label"],
                    "status_label": item["current_status_label"],
                    "occurred_at": item["create_time"],
                    "detail": item["detail"],
                }
                for item in payload.get("events", [])
            ]
        elif normalized_kind == "ALERT":
            payload = self.alert_detail(record_id)
            activity = [
                {
                    "sequence_no": item["sequence_no"],
                    "label": item["action_label"],
                    "status_label": item["current_status_label"],
                    "occurred_at": item["occurred_at"],
                    "detail": item["detail"],
                }
                for item in payload.get("events", [])
            ]
        elif normalized_kind == "TRACEBACK":
            payload = self.traceback_detail(record_id)
            activity = [
                {
                    "sequence_no": index,
                    "label": item["title"],
                    "status_label": item["status"],
                    "occurred_at": item["occurred_at"],
                    "detail": item["detail"],
                }
                for index, item in enumerate(payload.get("items", []), 1)
            ]
        elif normalized_kind == "CAPABILITY_CALL":
            payload = self.capability_call_detail(record_id)
            activity = [
                {
                    "sequence_no": 1,
                    "label": "发起模拟调用",
                    "status_label": payload["status_label"],
                    "occurred_at": payload["started_at"],
                    "detail": payload["request_payload"],
                },
                {
                    "sequence_no": 2,
                    "label": "生成模拟响应",
                    "status_label": payload["status_label"],
                    "occurred_at": payload["finished_at"],
                    "detail": payload["response_payload"],
                },
            ]
        elif normalized_kind == "FAULT_REPORT":
            payload = self.fault_report_detail(record_id)
            activity = [
                {
                    "sequence_no": item["sequence_no"],
                    "label": item["action_label"],
                    "status_label": item["current_status_label"],
                    "occurred_at": item["create_time"],
                    "detail": item["detail"],
                }
                for item in payload.get("events", [])
            ]
        else:
            payload = self.auxiliary_simulation_detail(record_id)
            activity = [
                {
                    "sequence_no": index,
                    "label": item["label"],
                    "status_label": payload["status_label"],
                    "occurred_at": item["occurred_at"],
                    "detail": {"minute": item["minute"]},
                }
                for index, item in enumerate(payload.get("key_moments", []), 1)
            ]
        return {"record": record, "activity_count": len(activity), "activity": activity, "detail": payload}

    def complaint_queryset(self, params=None):
        params = params or {}
        queryset = RehearsalComplaint.objects.filter(workspace_id=self.workspace_id).select_related("instance", "batch")
        if params.get("instance_id"):
            queryset = queryset.filter(instance_id=params["instance_id"])
        if params.get("customer_type"):
            queryset = queryset.filter(customer_type=params["customer_type"])
        if params.get("severity"):
            queryset = queryset.filter(severity=params["severity"])
        if params.get("status"):
            queryset = queryset.filter(status=params["status"])
        if params.get("validation_status"):
            queryset = queryset.filter(validation_status=params["validation_status"])
        if params.get("source"):
            queryset = queryset.filter(batch__source=params["source"])
        if params.get("date_from"):
            queryset = queryset.filter(occurred_at__date__gte=params["date_from"])
        if params.get("date_to"):
            queryset = queryset.filter(occurred_at__date__lte=params["date_to"])
        keyword = (params.get("keyword") or "").strip()
        if keyword:
            queryset = queryset.filter(
                Q(customer_ref__icontains=keyword)
                | Q(customer_name__icontains=keyword)
                | Q(title__icontains=keyword)
                | Q(content__icontains=keyword)
            )
        return queryset.order_by("-occurred_at", "-create_time")

    def list_complaints(self, params=None):
        params = params or {}
        try:
            page = max(int(params.get("page", 1)), 1)
            page_size = min(max(int(params.get("page_size", 50)), 1), 500)
        except (TypeError, ValueError) as exc:
            raise AppApiException(400, "分页参数必须为整数") from exc
        queryset = self.complaint_queryset(params)
        total = queryset.count()
        start = (page - 1) * page_size
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [serialize_complaint(row) for row in queryset[start : start + page_size]],
        }

    def batch_detail(self, batch_id):
        return serialize_batch(self._get_batch(batch_id))
