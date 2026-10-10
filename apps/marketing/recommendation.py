# coding=utf-8
"""Deterministic marketing recommendation selection for customer chats."""

import re
from datetime import date

from common.exception.app_exception import AppApiException


RECOMMENDATION_QUESTION_KEYWORDS = ("套餐", "升级", "流量", "推荐", "活动", "办理", "合适", "有什么")
FEE_QUESTION_KEYWORDS = ("贵", "费用", "多少钱", "加钱", "额外", "月费", "价格", "资费")


def _to_number(value) -> float:
    matched = re.search(r"\d+(?:\.\d+)?", str(value or ""))
    return float(matched.group()) if matched else 0


def _as_text_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _as_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        raise AppApiException(400, "营销活动生效日期必须为 YYYY-MM-DD")


def _is_effective(offer: dict, on_date: date) -> bool:
    start_date = _as_date(offer.get("effective_start"))
    end_date = _as_date(offer.get("effective_end"))
    return (start_date is None or start_date <= on_date) and (end_date is None or on_date <= end_date)


def _matches_offer(offer: dict, customer: dict) -> bool:
    plan = str(customer.get("plan") or "")
    province = str(customer.get("province") or "")
    plan_keywords = _as_text_list(offer.get("plan_keywords"))
    provinces = _as_text_list(offer.get("provinces"))
    if plan_keywords and not any(keyword in plan for keyword in plan_keywords):
        return False
    if provinces and province not in provinces:
        return False
    if _to_number(customer.get("data_usage")) < _to_number(offer.get("min_data_usage_gb")):
        return False
    return _to_number(customer.get("call_usage")) >= _to_number(offer.get("min_call_usage_minutes"))


def validate_recommendation_policy(policy: dict | None) -> dict:
    """Validate a strategy before a scenario is saved."""
    policy = policy if isinstance(policy, dict) else {}
    if not policy or not policy.get("enabled"):
        return {"enabled": False, "offer_count": 0}
    offers = policy.get("offers")
    if not isinstance(offers, list) or not offers:
        raise AppApiException(400, "启用推荐策略时至少需要配置一个活动")
    names = set()
    priority_group_pairs = set()
    for index, raw_offer in enumerate(offers):
        offer = raw_offer if isinstance(raw_offer, dict) else {}
        name = str(offer.get("name") or "").strip()
        if not name or not str(offer.get("benefit") or "").strip():
            raise AppApiException(400, f"活动 {index + 1} 请填写活动名称和客户可见权益")
        if not str(offer.get("fee_note") or "").strip() or not str(offer.get("contract_note") or "").strip():
            raise AppApiException(400, f"活动 {index + 1} 请填写费用边界和合约边界")
        if name in names:
            raise AppApiException(400, "活动名称不能重复")
        names.add(name)
        try:
            priority = int(offer.get("priority", 100))
        except (TypeError, ValueError):
            raise AppApiException(400, f"活动 {index + 1} 的优先级必须为整数")
        if priority < 1:
            raise AppApiException(400, f"活动 {index + 1} 的优先级必须大于 0")
        start_date = _as_date(offer.get("effective_start"))
        end_date = _as_date(offer.get("effective_end"))
        if start_date and end_date and end_date < start_date:
            raise AppApiException(400, f"活动 {index + 1} 的结束日期不能早于开始日期")
        exclusive_group = str(offer.get("exclusive_group") or "").strip()
        if exclusive_group:
            pair = (exclusive_group, priority)
            if pair in priority_group_pairs:
                raise AppApiException(400, f"互斥组“{exclusive_group}”内不能使用相同优先级")
            priority_group_pairs.add(pair)
    return {"enabled": True, "offer_count": len(offers)}


def select_recommendation(policy: dict | None, customer: dict | None, on_date: date | None = None) -> dict:
    """Select the highest-priority effective administrator-configured offer.

    The caller stores the selected result in the chat source so historical
    records remain explainable even if the scenario configuration changes.
    """
    policy = policy if isinstance(policy, dict) else {}
    customer = customer if isinstance(customer, dict) else {}
    if not policy.get("enabled"):
        return {"status": "DISABLED"}

    effective_date = on_date or date.today()
    offers = [raw_offer for raw_offer in policy.get("offers") or [] if isinstance(raw_offer, dict)]
    offers = sorted(enumerate(offers), key=lambda row: (int(row[1].get("priority", 100)), row[0]))
    for index, offer in offers:
        if not offer.get("name") or not _is_effective(offer, effective_date) or not _matches_offer(offer, customer):
            continue
        return {
            "status": "MATCHED",
            "offer_id": str(offer.get("id") or f"offer-{index + 1}"),
            "offer_name": str(offer.get("name")),
            "benefit": str(offer.get("benefit") or ""),
            "fee_note": str(offer.get("fee_note") or "以当地实际可办理方案为准。"),
            "contract_note": str(offer.get("contract_note") or "办理前会确认优惠期限和合约期。"),
            "priority": int(offer.get("priority", 100)),
            "exclusive_group": str(offer.get("exclusive_group") or ""),
        }
    return {"status": "NO_MATCH"}


def get_recommendation_context(source: dict | None) -> str:
    recommendation = source.get("marketing_recommendation") if isinstance(source, dict) else None
    if not isinstance(recommendation, dict):
        return ""
    if recommendation.get("status") == "MATCHED":
        return (
            "已匹配到管理员配置的营销活动："
            f"{recommendation.get('offer_name')}。客户可见权益：{recommendation.get('benefit') or '以当地可办方案为准'}。"
            f"费用边界：{recommendation.get('fee_note')} 合约边界：{recommendation.get('contract_note')}。\n"
            "只能围绕此活动回答；不得编造其他活动、金额或承诺。客户询问套餐升级、流量、活动或办理时，应直接、自然地说明该活动和下一步核实方式。"
        )
    if recommendation.get("status") == "NO_MATCH":
        return "当前客户未命中已配置活动，不得承诺优惠、金额或可办理资格；只可说明会核实当地可办方案。"
    return ""


def get_customer_recommendation_answer(problem_text: str, source: dict | None, answer_text: str) -> str:
    """Use a configured offer as the customer-facing decision for relevant questions.

    The knowledge retrieval and model response still run before this guard.  It
    only replaces weak-model wording with the administrator-approved offer.
    """
    if not isinstance(source, dict) or not source.get("marketing_customer_id"):
        return answer_text
    question = problem_text or ""
    if any(keyword in question for keyword in FEE_QUESTION_KEYWORDS):
        return answer_text
    if not any(keyword in question for keyword in RECOMMENDATION_QUESTION_KEYWORDS):
        return answer_text
    recommendation = source.get("marketing_recommendation")
    if not isinstance(recommendation, dict) or recommendation.get("status") != "MATCHED":
        return answer_text
    benefit = recommendation.get("benefit") or "可优先核实当地可办权益"
    fee_note = recommendation.get("fee_note") or "费用以当地实际可办理方案为准。"
    contract_note = recommendation.get("contract_note") or "办理前会确认优惠期限和合约期。"
    parts = [
        f"结合您当前套餐和近期使用情况，建议您优先了解“{recommendation.get('offer_name')}”",
        benefit,
        fee_note,
        contract_note,
    ]
    return "".join(f"{str(part).strip().rstrip('。；;')}。" for part in parts if str(part).strip())
