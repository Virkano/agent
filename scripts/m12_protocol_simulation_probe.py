"""Link the M12 recommendation scenario to IVR, Xiaoda Mock and rehearsal facts.

Run from the repository root after loading .env.local:
    ./.venv/bin/python apps/manage.py shell -c \
        'from scripts.m12_protocol_simulation_probe import run; run()'
"""

import logging

from scripts.m12_linkage_inventory import DEMO_WORKSPACE_ID


SCENARIO_REF = "M12-RECOMMENDATION-REVIEW-V1"
ACCEPTANCE_NOTE = "M12验收模拟：仅验证协议和状态链，不代表真实客户、电话线路或外部网关调用"


def _operator(workspace_id):
    from trigger.models import EventFlowRun
    from users.models import User
    from xpack_lite.models import WorkspaceUserRoleMapping

    flow = EventFlowRun.objects.filter(
        workspace_id=workspace_id,
        standard_event__event_id__startswith="ranking:",
    ).select_related("flow_version__created_by").order_by("-create_time").first()
    if flow and flow.flow_version.created_by:
        return flow.flow_version.created_by
    mapping = WorkspaceUserRoleMapping.objects.filter(
        workspace_id=workspace_id,
        user__is_active=True,
    ).select_related("user").first()
    if mapping:
        return mapping.user
    operator = User.objects.filter(is_active=True).order_by("date_joined").first()
    if operator is None:
        raise RuntimeError("No active acceptance operator is available")
    return operator


def _scenario_context(workspace_id):
    from marketing.models import RecommendationRankingRun

    ranking = RecommendationRankingRun.objects.filter(
        workspace_id=workspace_id,
    ).select_related("customer__task").order_by("-create_time").first()
    if ranking is None:
        raise RuntimeError("Run the M12 recommendation probe first")
    return ranking, {
        "scenario_ref": SCENARIO_REF,
        "marketing_task_id": str(ranking.customer.task_id),
        "marketing_customer_id": str(ranking.customer_id),
        "ranking_run_id": str(ranking.id),
        "acceptance_simulated": True,
    }


def _replay_ivr(workspace_id, operator, context):
    from marketing.models import IvrEventType, IvrSessionStatus, IvrTransport
    from marketing.serializers.ivr import IvrProtocolSimulatorService

    service = IvrProtocolSimulatorService(workspace_id, operator)
    external_session_id = f"{SCENARIO_REF}:{context['ranking_run_id']}"
    created = service.create_session(
        {
            "external_session_id": external_session_id,
            "transport": IvrTransport.WEBSOCKET_REPLAY,
            "caller_label": "M12验收模拟客户",
            "metadata": {**context, "acceptance_note": ACCEPTANCE_NOTE},
        }
    )
    session_id = created["session"]["id"]
    if created["session"]["status"] not in (IvrSessionStatus.ENDED, IvrSessionStatus.FAILED):
        service.process_audio(
            session_id,
            {
                "request_id": f"{SCENARIO_REF}:ivr:audio",
                "chunk_index": 0,
                "duration_ms": 1200,
                "transcript_hint": "请确认本次推荐复核已经完成",
                "is_final": True,
            },
        )
        service.record_event(
            session_id,
            {
                "request_id": f"{SCENARIO_REF}:ivr:end",
                "event_type": IvrEventType.SESSION_ENDED,
                "payload": {"scenario_ref": SCENARIO_REF, "acceptance_simulated": True},
            },
        )
    detail = service.get(session_id)
    if detail["status"] != IvrSessionStatus.ENDED:
        raise RuntimeError("IVR contract replay did not reach ENDED")
    if detail["metadata"].get("scenario_ref") != SCENARIO_REF:
        raise RuntimeError("IVR scenario correlation is missing")
    return detail


def _invoke_xiaoda(workspace_id, operator, context):
    from tools.api_orchestration import ApiOrchestrationService
    from tools.models import ApiInvocationAudit, ApiInvocationStatus, ApiOrchestrationAsset

    service = ApiOrchestrationService(workspace_id, operator)
    asset = ApiOrchestrationAsset.objects.filter(
        workspace_id=workspace_id,
        asset_key="m12_recommendation_review",
    ).first()
    if asset is None:
        created = service.save_asset(
            {
                "asset_key": "m12_recommendation_review",
                "name": "M12推荐复核结果查询",
                "description": ACCEPTANCE_NOTE,
                "auth_scheme": "API_KEY",
                "auth_reference": "system-api-key:m12-acceptance-reference",
                "ip_allowlist": ["127.0.0.1"],
                "environment": "TEST",
                "method": "POST",
                "endpoint_path": "/xiaoda/mock/v1/recommendation-review",
                "input_schema": {
                    "type": "object",
                    "required": ["scenario_ref", "customer_id", "ranking_run_id"],
                    "additionalProperties": False,
                    "properties": {
                        "scenario_ref": {"type": "string"},
                        "customer_id": {"type": "string"},
                        "ranking_run_id": {"type": "string"},
                    },
                },
                "output_schema": {
                    "type": "object",
                    "required": ["review_status", "acceptance_simulated"],
                    "additionalProperties": False,
                    "properties": {
                        "review_status": {"type": "string"},
                        "acceptance_simulated": {"type": "boolean"},
                    },
                },
                "mock_response": {
                    "review_status": "COMPLETED",
                    "acceptance_simulated": True,
                },
            }
        )
        asset = ApiOrchestrationAsset.objects.get(id=created["id"])
        service.publish(str(asset.id), created["draft_version"]["id"])
    request_id = f"{SCENARIO_REF}:xiaoda:success"
    audit = ApiInvocationAudit.objects.filter(
        workspace_id=workspace_id,
        request_id=request_id,
    ).first()
    if audit is None:
        result = service.mock_invoke(
            str(asset.id),
            {
                "request_id": request_id,
                "payload": {
                    "scenario_ref": SCENARIO_REF,
                    "customer_id": context["marketing_customer_id"],
                    "ranking_run_id": context["ranking_run_id"],
                },
                "auth_context": {"validated": True, "scheme": "API_KEY"},
            },
        )
        audit = ApiInvocationAudit.objects.get(id=result["id"])
    if audit.status != ApiInvocationStatus.SUCCESS:
        raise RuntimeError("Xiaoda Mock invocation did not succeed")
    if (audit.request_snapshot.get("params") or {}).get("scenario_ref") != SCENARIO_REF:
        raise RuntimeError("Xiaoda scenario correlation is missing")
    return audit


def _run_rehearsal(workspace_id, operator, context, ivr_detail, xiaoda_audit):
    from django.utils import timezone

    from rehearsal.models import (
        RehearsalComplaintTemplate,
        RehearsalCustomerScope,
        RehearsalInstance,
        RehearsalInstanceStatus,
        RehearsalScenario,
    )
    from rehearsal.serializers import RehearsalService

    service = RehearsalService(workspace_id, operator)
    service.ensure_default_catalog()
    scenario = RehearsalScenario.objects.filter(
        workspace_id=workspace_id,
        code=SCENARIO_REF,
        version=1,
    ).first()
    if scenario is None:
        result = service.create_scenario(
            {
                "code": SCENARIO_REF,
                "name": "M12推荐复核跨协议验收场景",
                "description": ACCEPTANCE_NOTE,
                "customer_scope": RehearsalCustomerScope.PUBLIC,
                "configuration": context,
            }
        )
        scenario = RehearsalScenario.objects.get(id=result["id"])
    request_id = f"{SCENARIO_REF}:rehearsal:instance"
    instance_result = service.create_instance(
        {
            "request_id": request_id,
            "scenario_id": str(scenario.id),
            "code": "M12-RECOMMENDATION-REVIEW",
            "name": "M12推荐复核跨协议验收实例",
            "parameters": {
                **context,
                "ivr_session_id": ivr_detail["id"],
                "xiaoda_invocation_id": str(xiaoda_audit.id),
                "acceptance_note": ACCEPTANCE_NOTE,
            },
        }
    )
    instance = RehearsalInstance.objects.get(id=instance_result["instance"]["id"])
    if instance.status == RehearsalInstanceStatus.DRAFT:
        template = RehearsalComplaintTemplate.objects.filter(
            workspace_id=workspace_id,
            code="PUBLIC-COMPLAINT-V1",
            enabled=True,
        ).first()
        if template is None:
            raise RuntimeError("Default rehearsal complaint template is missing")
        service.generate_complaints(
            str(instance.id),
            {
                "request_id": f"{SCENARIO_REF}:rehearsal:complaints",
                "template_id": str(template.id),
                "count": 1,
                "start_at": timezone.now(),
                "interval_minutes": 5,
            },
        )
        service.operate_instance(str(instance.id), {"action": "PREPARE", "note": ACCEPTANCE_NOTE})
        instance.refresh_from_db()
    if instance.status == RehearsalInstanceStatus.READY:
        service.operate_instance(str(instance.id), {"action": "START", "note": ACCEPTANCE_NOTE})
        instance.refresh_from_db()
    if instance.status == RehearsalInstanceStatus.RUNNING:
        service.operate_instance(str(instance.id), {"action": "COMPLETE", "note": ACCEPTANCE_NOTE})
        instance.refresh_from_db()
    if instance.status != RehearsalInstanceStatus.COMPLETED:
        raise RuntimeError("Rehearsal instance did not reach COMPLETED")
    if instance.parameters.get("scenario_ref") != SCENARIO_REF:
        raise RuntimeError("Rehearsal scenario correlation is missing")
    return service.instance_detail(str(instance.id))


def run(workspace_id=DEMO_WORKSPACE_ID):
    logging.disable(logging.DEBUG)
    operator = _operator(workspace_id)
    _ranking, context = _scenario_context(workspace_id)
    ivr_detail = _replay_ivr(workspace_id, operator, context)
    xiaoda_audit = _invoke_xiaoda(workspace_id, operator, context)
    rehearsal = _run_rehearsal(
        workspace_id,
        operator,
        context,
        ivr_detail,
        xiaoda_audit,
    )
    print(
        {
            "workspace_id": workspace_id,
            "scenario_ref": SCENARIO_REF,
            "task_id": context["marketing_task_id"],
            "customer_id": context["marketing_customer_id"],
            "ranking_run_id": context["ranking_run_id"],
            "ivr_session_id": ivr_detail["id"],
            "ivr_status": ivr_detail["status"],
            "ivr_protocol": "CONTRACT_REPLAY",
            "xiaoda_invocation_id": str(xiaoda_audit.id),
            "xiaoda_status": xiaoda_audit.status,
            "xiaoda_adapter": "MOCK",
            "rehearsal_instance_id": rehearsal["id"],
            "rehearsal_status": rehearsal["status"],
            "rehearsal_event_count": len(rehearsal["events"]),
            "acceptance_simulated": True,
        }
    )
