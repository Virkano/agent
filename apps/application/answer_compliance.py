"""Coarse V1 guard for knowledge-backed customer answers."""

import hashlib
import re


RULE_VERSION = "service-answer-v1"
NO_REFERENCE_ANSWER = "当前没有检索到可核实的资料，暂时无法给出确定答复。请补充问题或联系人工客服核实。"
BLOCKED_ANSWER = "当前答复需要人工复核，暂时无法直接展示。请联系人工客服。"
SENSITIVE_MARKERS = (
    "系统提示词",
    "内部规则",
    "管理员口令",
    "API密钥",
    "保证成功",
    "永久优惠",
)
PHONE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])")
ID_NUMBER = re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")


def should_apply_platform_compliance(context):
    """Marketing conversations keep their existing configurable preflight."""
    if not isinstance(context, dict):
        return False
    source = context.get("source")
    return bool(context.get("knowledge_id_list")) and not (
        isinstance(source, dict) and source.get("marketing_task_id")
    )


def _sha256(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def runtime_failure_audit():
    return {
        "rule_version": RULE_VERSION,
        "action": "BLOCKED",
        "risk_types": ["RUNTIME_ERROR"],
        "manual_review_status": "PENDING",
        "reference_count": 0,
        "reference_ids": [],
    }


def evaluate_knowledge_answer(answer_text, paragraph_list, *, configured_fallback=False):
    """Return customer text and metadata-only audit; never retain matched secrets."""
    generated = str(answer_text or "")
    references = [str(item.id) for item in (paragraph_list or []) if getattr(item, "id", None) is not None]
    risk_types = []
    if not references and not configured_fallback:
        risk_types.append("NO_REFERENCE")
    if any(marker.casefold() in generated.casefold() for marker in SENSITIVE_MARKERS):
        risk_types.append("SENSITIVE_CONTENT")
    if PHONE.search(generated) or EMAIL.search(generated) or ID_NUMBER.search(generated):
        risk_types.append("PRIVATE_DATA")

    if "SENSITIVE_CONTENT" in risk_types:
        delivered = BLOCKED_ANSWER
        action = "BLOCKED"
    elif "NO_REFERENCE" in risk_types:
        delivered = NO_REFERENCE_ANSWER
        action = "FALLBACK"
    else:
        delivered = generated
        delivered = PHONE.sub("[手机号已脱敏]", delivered)
        delivered = EMAIL.sub("[邮箱已脱敏]", delivered)
        delivered = ID_NUMBER.sub("[证件号已脱敏]", delivered)
        action = "REDACTED" if delivered != generated else ("CONFIGURED_FALLBACK" if not references else "PASS")

    return delivered, {
        "rule_version": RULE_VERSION,
        "action": action,
        "risk_types": risk_types,
        "manual_review_status": "PENDING" if risk_types else "NOT_REQUIRED",
        "reference_count": len(references),
        "reference_ids": references[:20],
        "generated_sha256": _sha256(generated),
        "delivered_sha256": _sha256(delivered),
    }
