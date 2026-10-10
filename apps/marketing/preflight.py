import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from application.models.application_chat import ChatRecord
from common.utils.logger import telecom_ai_logger
from marketing.models import (
    MarketingAnswerPreflightRecord,
    MarketingAnswerQualityStatus,
    MarketingCustomer,
    MarketingPreflightAction,
    MarketingQualityPolicy,
    MarketingQualityPolicyMode,
    MarketingTask,
)
from marketing.quality import RULE_VERSION, evaluate_marketing_answer


DEFAULT_POLICY_MODE = MarketingQualityPolicyMode.SHADOW
PREFLIGHT_EVALUATION_TIMEOUT_SECONDS = 0.3
INTERCEPTED_CUSTOMER_ANSWER = (
    "这个问题涉及具体资费或办理规则，我暂时无法确认准确结果。为避免给您错误信息，建议由当地人工客服进一步核实后再办理。"
)
_EVALUATION_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="marketing-quality")


def get_workspace_quality_policy(workspace_id):
    policy = MarketingQualityPolicy.objects.filter(workspace_id=workspace_id).first()
    return {
        "mode": policy.mode if policy else DEFAULT_POLICY_MODE,
        "rule_version": policy.rule_version if policy else RULE_VERSION,
        "intercept_rule_types": list(policy.intercept_rule_types or []) if policy else [],
        "updated_by_name": policy.updated_by_name if policy else "",
        "update_time": policy.update_time if policy else None,
    }


def should_buffer_marketing_preflight(source):
    """Only interception mode buffers a marketing answer before customer delivery."""

    source = source if isinstance(source, dict) else {}
    task_id = source.get("marketing_task_id")
    if not task_id:
        return False
    task = MarketingTask.objects.filter(id=task_id).only("workspace_id").first()
    if task is None:
        return False
    return get_workspace_quality_policy(task.workspace_id)["mode"] == MarketingQualityPolicyMode.INTERCEPT


def _evaluate_with_timeout(problem_text, final_answer, source, details, previous_answer):
    future = _EVALUATION_EXECUTOR.submit(
        evaluate_marketing_answer,
        problem_text,
        final_answer,
        source=source,
        details=details,
        previous_answer=previous_answer,
    )
    return future.result(timeout=PREFLIGHT_EVALUATION_TIMEOUT_SECONDS)


def prepare_marketing_preflight(
    problem_text,
    generated_answer,
    final_answer,
    source,
    chat_id=None,
    paragraph_count=0,
):
    """Evaluate one marketing answer and return the policy-selected delivery snapshot."""

    started_at = time.perf_counter()
    source = source if isinstance(source, dict) else {}
    task_id = source.get("marketing_task_id")
    if not task_id:
        return None
    task = MarketingTask.objects.filter(id=task_id).first()
    if task is None:
        return None
    policy = get_workspace_quality_policy(task.workspace_id)
    if policy["mode"] == MarketingQualityPolicyMode.OFF:
        return None

    customer = None
    customer_id = source.get("marketing_customer_id")
    if customer_id:
        customer = MarketingCustomer.objects.filter(
            id=customer_id,
            task_id=task.id,
            workspace_id=task.workspace_id,
        ).first()
    previous_answer = ""
    if chat_id:
        previous_record = ChatRecord.objects.filter(chat_id=chat_id).order_by("-index", "-create_time").first()
        previous_answer = previous_record.answer_text if previous_record else ""
    details = {"paragraph_list": [None] * max(int(paragraph_count or 0), 0)}
    base_snapshot = {
        "workspace_id": task.workspace_id,
        "task_id": task.id,
        "customer_id": customer.id if customer else None,
        "policy_mode": policy["mode"],
        "generated_answer": str(generated_answer or ""),
        "final_answer": str(final_answer or ""),
    }
    try:
        result = _evaluate_with_timeout(problem_text, final_answer, source, details, previous_answer)
    except FutureTimeoutError:
        telecom_ai_logger.warning("Marketing preflight timed out for task %s", task.id)
        return {
            **base_snapshot,
            "action": MarketingPreflightAction.BYPASSED,
            "status": MarketingAnswerQualityStatus.REVIEW,
            "score": 0,
            "risk_types": [],
            "reasons": ["发送前质检超时，已按可用性策略旁路"],
            "suggestion": "检查质检服务耗时，恢复后再启用灰度拦截。",
            "evidence": {"bypass_reason": "TIMEOUT"},
            "rule_version": policy["rule_version"],
            "evaluation_ms": max(0, round((time.perf_counter() - started_at) * 1000)),
        }
    except Exception:
        telecom_ai_logger.exception("Marketing preflight evaluation failed for task %s", task.id)
        return {
            **base_snapshot,
            "action": MarketingPreflightAction.BYPASSED,
            "status": MarketingAnswerQualityStatus.REVIEW,
            "score": 0,
            "risk_types": [],
            "reasons": ["发送前质检异常，已按可用性策略旁路"],
            "suggestion": "检查质检服务日志，恢复后再启用灰度拦截。",
            "evidence": {"bypass_reason": "ERROR"},
            "rule_version": policy["rule_version"],
            "evaluation_ms": max(0, round((time.perf_counter() - started_at) * 1000)),
        }
    intercepted_risk_types = [
        risk_type
        for risk_type in result["risk_types"]
        if policy["mode"] == MarketingQualityPolicyMode.INTERCEPT and risk_type in policy["intercept_rule_types"]
    ]
    delivered_answer = INTERCEPTED_CUSTOMER_ANSWER if intercepted_risk_types else str(final_answer or "")
    evidence = {
        **result["evidence"],
        "configured_intercept_rule_types": policy["intercept_rule_types"],
        "intercepted_risk_types": intercepted_risk_types,
    }
    return {
        **base_snapshot,
        "action": (
            MarketingPreflightAction.INTERCEPTED
            if intercepted_risk_types
            else (
                MarketingPreflightAction.SAFEGUARD_REWRITTEN
                if str(generated_answer or "") != str(final_answer or "")
                else MarketingPreflightAction.OBSERVED
            )
        ),
        "final_answer": delivered_answer,
        **result,
        "evidence": evidence,
        "evaluation_ms": max(0, round((time.perf_counter() - started_at) * 1000)),
    }


def save_marketing_preflight(record_id, snapshot):
    if not snapshot:
        return None
    try:
        record = ChatRecord.objects.filter(id=record_id).first()
        if record is None:
            return None
        preflight, _ = MarketingAnswerPreflightRecord.objects.update_or_create(
            record_id=record.id,
            defaults=snapshot,
        )
        return preflight
    except Exception:
        telecom_ai_logger.exception("Marketing shadow preflight save failed for chat record %s", record_id)
        return None
