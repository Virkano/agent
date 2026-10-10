# coding=utf-8
"""Lightweight, auditable marketing-customer conversation insights.

The result is deliberately based on the customer's own message instead of a
small local model.  This makes the marketing funnel deterministic and avoids
turning an unverified model inference into a customer or operator fact.
"""

from collections import Counter

from django.utils import timezone

from marketing.models import MarketingCustomer, MarketingCustomerStatus


OBJECTION_RULES = {
    "费用": ("贵", "费用", "多少钱", "月费", "价格", "资费", "加钱", "额外"),
    "合约": ("合约", "合约期", "违约", "到期", "绑定"),
    "流量": ("流量不够", "超流量", "限速", "流量"),
    "服务": ("信号", "网速", "服务", "客服", "办理不了"),
}
MANUAL_KEYWORDS = ("人工", "投诉", "申诉", "退订", "销户", "扣费", "账单", "诈骗", "举报", "号码异常")
NO_INTENT_KEYWORDS = ("不需要", "不想", "不要", "不办", "不用了", "没兴趣", "拒绝", "算了")
INTENT_KEYWORDS = ("帮我办理", "我要办理", "可以办理", "现在办理", "帮我开通", "我要升级", "帮我升级")


def analyze_customer_message(problem_text: str) -> dict:
    """Return a concise customer-state signal from one customer message."""
    text = (problem_text or "").strip()
    objection_tags = [tag for tag, keywords in OBJECTION_RULES.items() if any(word in text for word in keywords)]

    if any(word in text for word in MANUAL_KEYWORDS):
        return {
            "status": MarketingCustomerStatus.MANUAL,
            "intent": "需人工跟进",
            "objection_tags": objection_tags,
            "requires_manual_follow_up": True,
        }
    if any(word in text for word in NO_INTENT_KEYWORDS):
        return {
            "status": MarketingCustomerStatus.NO_INTENT,
            "intent": "明确无意向",
            "objection_tags": objection_tags,
            "requires_manual_follow_up": False,
        }
    if any(word in text for word in INTENT_KEYWORDS):
        return {
            "status": MarketingCustomerStatus.INTENT,
            "intent": "明确办理意向",
            "objection_tags": objection_tags,
            "requires_manual_follow_up": False,
        }
    return {
        "status": MarketingCustomerStatus.CONSULTED,
        "intent": "待跟进" if objection_tags else "已咨询",
        "objection_tags": objection_tags,
        "requires_manual_follow_up": False,
    }


def update_customer_conversation_insight(
    source: dict | None, problem_text: str, chat_id, chat_record_id
) -> dict | None:
    """Persist one auditable signal for a marketing customer conversation.

    A customer intentionally set to manual follow-up is never overwritten by
    subsequent automatic analysis.  Operator remarks are also left untouched.
    """
    if not isinstance(source, dict):
        return None
    task_id = source.get("marketing_task_id")
    customer_id = source.get("marketing_customer_id")
    if not task_id or not customer_id:
        return None

    customer = MarketingCustomer.objects.filter(id=customer_id, task_id=task_id).first()
    if customer is None:
        return None

    result = analyze_customer_message(problem_text)
    insight = {
        **result,
        "problem_text": (problem_text or "")[:500],
        "chat_id": str(chat_id),
        "chat_record_id": str(chat_record_id),
        "analyzed_at": timezone.now().isoformat(),
    }
    config = dict(customer.config or {})
    history = list(config.get("marketing_insight_history") or [])[-19:]
    history.append(insight)
    config["marketing_insight"] = insight
    config["marketing_insight_history"] = history

    update_fields = ["config", "update_time"]
    customer.config = config
    if customer.status != MarketingCustomerStatus.MANUAL:
        customer.status = result["status"]
        customer.intent = result["intent"]
        update_fields.extend(["status", "intent"])
    customer.save(update_fields=update_fields)
    return insight


def summarize_customer_insights(customers) -> dict:
    """Build task-level, customer-visible operations metrics."""
    objection_counts = Counter()
    auto_insight_customer_count = 0
    follow_up_record_count = 0
    for customer in customers:
        config = customer.config if isinstance(customer.config, dict) else {}
        insight = config.get("marketing_insight") if isinstance(config.get("marketing_insight"), dict) else {}
        if insight:
            auto_insight_customer_count += 1
            objection_counts.update(insight.get("objection_tags") or [])
        follow_up_record_count += len(config.get("marketing_follow_up_history") or [])
    return {
        "auto_insight_customer_count": auto_insight_customer_count,
        "follow_up_record_count": follow_up_record_count,
        "objection_summary": [{"tag": tag, "count": count} for tag, count in objection_counts.most_common()],
    }
