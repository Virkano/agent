# coding=utf-8
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from common.exception.app_exception import AppApiException
from marketing.models import (
    ChangeConfirmation,
    ChangeConfirmationDecision,
    ChangeConfirmationStatus,
    ChangeOperation,
    ChangeOperationStatus,
    ChangeOperationType,
    ChangeRiskAssessment,
    ChangeRiskLevel,
    IvrSession,
)


class ChangeOperationCreateSerializer(serializers.Serializer):
    code = serializers.CharField(required=False, allow_blank=True, max_length=96)
    name = serializers.CharField(max_length=160)
    operation_type = serializers.ChoiceField(
        choices=ChangeOperationType.choices,
        default=ChangeOperationType.CONFIG_CHANGE,
    )
    description = serializers.CharField(required=False, allow_blank=True, max_length=4000)
    planned_start_at = serializers.DateTimeField(required=False, allow_null=True)
    ivr_session_id = serializers.UUIDField(required=False, allow_null=True)


class ChangeRiskEvaluateSerializer(serializers.Serializer):
    instruction_complete = serializers.BooleanField(default=True)
    business_logic_passed = serializers.BooleanField(default=True)
    consistency_passed = serializers.BooleanField(default=True)
    affected_customer_count = serializers.IntegerField(default=0, min_value=0, max_value=100000000)
    cross_system_change = serializers.BooleanField(default=False)
    rollback_plan_ready = serializers.BooleanField(default=True)
    emergency_change = serializers.BooleanField(default=False)
    customer_notice_ready = serializers.BooleanField(default=True)


class ChangeConfirmationSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=160)
    decision = serializers.ChoiceField(choices=ChangeConfirmationDecision.choices)
    comment = serializers.CharField(required=False, allow_blank=True, max_length=4000)

    def validate(self, attrs):
        if attrs["decision"] == ChangeConfirmationDecision.REJECT and not attrs.get("comment", "").strip():
            raise serializers.ValidationError({"comment": "驳回高风险变更时必须填写原因"})
        return attrs


def serialize_change_assessment(row):
    return {
        "id": str(row.id),
        "revision": row.revision,
        "risk_level": row.risk_level,
        "risk_level_label": row.get_risk_level_display(),
        "risk_score": row.risk_score,
        "input_snapshot": row.input_snapshot or {},
        "reasons": row.reasons or [],
        "evaluator_name": row.user.nick_name if row.user else "",
        "create_time": row.create_time,
    }


def serialize_change_confirmation(row):
    return {
        "id": str(row.id),
        "assessment_id": str(row.assessment_id),
        "request_id": row.request_id,
        "decision": row.decision,
        "decision_label": row.get_decision_display(),
        "comment": row.comment,
        "risk_level": row.risk_level,
        "risk_score": row.risk_score,
        "confirmer_name": row.confirmer.nick_name if row.confirmer else "",
        "create_time": row.create_time,
    }


def serialize_change_operation(row, *, include_history=False):
    data = {
        "id": str(row.id),
        "code": row.code,
        "name": row.name,
        "operation_type": row.operation_type,
        "operation_type_label": row.get_operation_type_display(),
        "description": row.description,
        "planned_start_at": row.planned_start_at,
        "ivr_session_id": str(row.ivr_session_id) if row.ivr_session_id else None,
        "ivr_session_external_id": row.ivr_session.external_session_id if row.ivr_session else "",
        "status": row.status,
        "status_label": row.get_status_display(),
        "risk_level": row.risk_level,
        "risk_level_label": row.get_risk_level_display(),
        "risk_score": row.risk_score,
        "risk_revision": row.risk_revision,
        "risk_snapshot": row.risk_snapshot or {},
        "risk_reasons": row.risk_reasons or [],
        "confirmation_status": row.confirmation_status,
        "confirmation_status_label": row.get_confirmation_status_display(),
        "evaluated_at": row.evaluated_at,
        "decided_at": row.decided_at,
        "creator_name": row.user.nick_name if row.user else "",
        "create_time": row.create_time,
        "update_time": row.update_time,
    }
    if include_history:
        data["assessments"] = [serialize_change_assessment(item) for item in row.assessments.all()]
        data["confirmations"] = [serialize_change_confirmation(item) for item in row.confirmations.all()]
    return data


class ChangeOperationRiskService:
    def __init__(self, workspace_id, user=None):
        self.workspace_id = workspace_id
        self.user = user

    def _queryset(self):
        return ChangeOperation.objects.filter(workspace_id=self.workspace_id).select_related("ivr_session", "user")

    def _get(self, operation_id, *, lock=False):
        queryset = ChangeOperation.objects.filter(workspace_id=self.workspace_id)
        if lock:
            queryset = queryset.select_for_update()
        operation = queryset.filter(id=operation_id).first()
        if operation is None:
            raise AppApiException(404, "变更操作不存在")
        return operation

    def _linked_session(self, session_id):
        if not session_id:
            return None
        session = IvrSession.objects.filter(workspace_id=self.workspace_id, id=session_id).first()
        if session is None:
            raise AppApiException(400, "关联的 IVR 会话不存在或不属于当前工作空间")
        return session

    @staticmethod
    def _calculate_risk(values):
        score = 0
        reasons = []

        def add(factor, label, severity, points, message):
            nonlocal score
            score += points
            reasons.append(
                {
                    "factor": factor,
                    "label": label,
                    "severity": severity,
                    "points": points,
                    "message": message,
                }
            )

        if not values["instruction_complete"]:
            add("INSTRUCTION", "指令完整性", "WARNING", 20, "操作指令或执行步骤不完整")
        if not values["business_logic_passed"]:
            add("BUSINESS_LOGIC", "业务逻辑", "CRITICAL", 45, "业务规则校验未通过")
        if not values["consistency_passed"]:
            add("CONSISTENCY", "一致性", "CRITICAL", 45, "跨数据或配置一致性校验未通过")

        affected_count = values["affected_customer_count"]
        if affected_count >= 10000:
            add("IMPACT_SCOPE", "影响范围", "CRITICAL", 35, f"预计影响 {affected_count} 个客户")
        elif affected_count >= 1000:
            add("IMPACT_SCOPE", "影响范围", "WARNING", 20, f"预计影响 {affected_count} 个客户")
        elif affected_count >= 100:
            add("IMPACT_SCOPE", "影响范围", "NOTICE", 10, f"预计影响 {affected_count} 个客户")

        if values["cross_system_change"]:
            add("CROSS_SYSTEM", "跨系统变更", "WARNING", 15, "操作涉及多个业务系统")
        if not values["rollback_plan_ready"]:
            points = 30 if values["cross_system_change"] else 15
            add("ROLLBACK", "回退保障", "CRITICAL" if points == 30 else "WARNING", points, "回退方案未就绪")
        if values["emergency_change"]:
            add("EMERGENCY", "紧急变更", "WARNING", 20, "紧急操作缺少常规观察窗口")
        if not values["customer_notice_ready"]:
            add("CUSTOMER_NOTICE", "客户告知", "NOTICE", 10, "客户影响告知尚未就绪")

        critical = any(item["severity"] == "CRITICAL" for item in reasons)
        score = min(score, 100)
        if critical or score >= 60:
            risk_level = ChangeRiskLevel.RED
        elif score >= 20:
            risk_level = ChangeRiskLevel.YELLOW
        else:
            risk_level = ChangeRiskLevel.GREEN
        if not reasons:
            reasons.append(
                {
                    "factor": "ALL_CHECKS",
                    "label": "核心校验",
                    "severity": "PASS",
                    "points": 0,
                    "message": "指令、业务逻辑、一致性和复合因素均通过",
                }
            )
        return risk_level, score, reasons

    @transaction.atomic
    def create(self, data):
        serializer = ChangeOperationCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        code = values.get("code", "").strip() or f"CHANGE-{timezone.now():%Y%m%d%H%M%S%f}"
        existing = self._queryset().filter(code=code).first()
        if existing:
            return {"created": False, "operation": serialize_change_operation(existing)}
        operation = ChangeOperation.objects.create(
            workspace_id=self.workspace_id,
            code=code,
            name=values["name"].strip(),
            operation_type=values["operation_type"],
            description=values.get("description", "").strip(),
            planned_start_at=values.get("planned_start_at"),
            ivr_session=self._linked_session(values.get("ivr_session_id")),
            user=self.user,
        )
        return {"created": True, "operation": serialize_change_operation(operation)}

    @transaction.atomic
    def evaluate(self, operation_id, data):
        serializer = ChangeRiskEvaluateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        operation = self._get(operation_id, lock=True)
        risk_level, risk_score, reasons = self._calculate_risk(values)
        revision = operation.risk_revision + 1
        assessment = ChangeRiskAssessment.objects.create(
            workspace_id=self.workspace_id,
            operation=operation,
            revision=revision,
            risk_level=risk_level,
            risk_score=risk_score,
            input_snapshot=values,
            reasons=reasons,
            user=self.user,
        )
        operation.risk_level = risk_level
        operation.risk_score = risk_score
        operation.risk_revision = revision
        operation.risk_snapshot = values
        operation.risk_reasons = reasons
        operation.evaluated_at = timezone.now()
        operation.decided_at = None
        if risk_level == ChangeRiskLevel.RED:
            operation.status = ChangeOperationStatus.CONFIRMATION_PENDING
            operation.confirmation_status = ChangeConfirmationStatus.PENDING
        elif risk_level == ChangeRiskLevel.GREEN:
            operation.status = ChangeOperationStatus.APPROVED
            operation.confirmation_status = ChangeConfirmationStatus.NOT_REQUIRED
        else:
            operation.status = ChangeOperationStatus.RISK_EVALUATED
            operation.confirmation_status = ChangeConfirmationStatus.NOT_REQUIRED
        operation.save(
            update_fields=[
                "risk_level",
                "risk_score",
                "risk_revision",
                "risk_snapshot",
                "risk_reasons",
                "evaluated_at",
                "decided_at",
                "status",
                "confirmation_status",
                "update_time",
            ]
        )
        return {
            "operation": serialize_change_operation(self._queryset().get(id=operation.id)),
            "assessment": serialize_change_assessment(assessment),
            "requires_confirmation": risk_level == ChangeRiskLevel.RED,
        }

    @transaction.atomic
    def confirm(self, operation_id, data):
        serializer = ChangeConfirmationSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        existing = (
            ChangeConfirmation.objects.filter(
                workspace_id=self.workspace_id,
                request_id=values["request_id"],
            )
            .select_related("assessment", "confirmer")
            .first()
        )
        if existing:
            if str(existing.operation_id) != str(operation_id):
                raise AppApiException(400, "确认请求幂等键已被其他变更操作使用")
            return {
                "created": False,
                "operation": self.detail(existing.operation_id),
                "confirmation": serialize_change_confirmation(existing),
            }
        operation = self._get(operation_id, lock=True)
        if operation.confirmation_status != ChangeConfirmationStatus.PENDING:
            raise AppApiException(400, "当前变更操作没有待处理的高风险确认")
        assessment = ChangeRiskAssessment.objects.filter(
            operation=operation,
            revision=operation.risk_revision,
        ).first()
        if assessment is None or assessment.risk_level != ChangeRiskLevel.RED:
            raise AppApiException(400, "高风险评估快照不存在，不能确认")
        confirmation = ChangeConfirmation.objects.create(
            workspace_id=self.workspace_id,
            operation=operation,
            assessment=assessment,
            request_id=values["request_id"],
            decision=values["decision"],
            comment=values.get("comment", "").strip(),
            risk_level=assessment.risk_level,
            risk_score=assessment.risk_score,
            confirmer=self.user,
        )
        if values["decision"] == ChangeConfirmationDecision.APPROVE:
            operation.status = ChangeOperationStatus.APPROVED
            operation.confirmation_status = ChangeConfirmationStatus.APPROVED
        else:
            operation.status = ChangeOperationStatus.REJECTED
            operation.confirmation_status = ChangeConfirmationStatus.REJECTED
        operation.decided_at = timezone.now()
        operation.save(update_fields=["status", "confirmation_status", "decided_at", "update_time"])
        return {
            "created": True,
            "operation": serialize_change_operation(self._queryset().get(id=operation.id)),
            "confirmation": serialize_change_confirmation(confirmation),
        }

    def detail(self, operation_id):
        operation = (
            self._queryset()
            .prefetch_related("assessments__user", "confirmations__assessment", "confirmations__confirmer")
            .filter(id=operation_id)
            .first()
        )
        if operation is None:
            raise AppApiException(404, "变更操作不存在")
        return serialize_change_operation(operation, include_history=True)

    def dashboard(self):
        queryset = ChangeOperation.objects.filter(workspace_id=self.workspace_id)
        operations = list(self._queryset().order_by("-update_time")[:30])
        return {
            "summary": {
                "operation_count": queryset.count(),
                "red_count": queryset.filter(risk_level=ChangeRiskLevel.RED, risk_revision__gt=0).count(),
                "pending_confirmation_count": queryset.filter(
                    confirmation_status=ChangeConfirmationStatus.PENDING
                ).count(),
                "approved_count": queryset.filter(status=ChangeOperationStatus.APPROVED).count(),
            },
            "risk_counts": {
                value: queryset.filter(risk_level=value, risk_revision__gt=0).count()
                for value in ChangeRiskLevel.values
            },
            "operations": [serialize_change_operation(item) for item in operations],
            "risk_rules": {
                "red": "存在关键校验失败或风险分达到 60",
                "yellow": "风险分达到 20 且无关键校验失败",
                "green": "风险分低于 20",
                "confirmation": "红灯变更必须人工确认后才能放行或驳回",
            },
        }
