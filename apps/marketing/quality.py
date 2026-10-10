import re
from difflib import SequenceMatcher

from application.models.application_chat import ChatRecord
from marketing.models import (
    MarketingAnswerQualityReview,
    MarketingAnswerQualityStatus,
    MarketingCustomer,
    MarketingTask,
)


RULE_VERSION = "marketing-quality-v1"
MARKETING_QUESTION_KEYWORDS = (
    "套餐",
    "流量",
    "通话",
    "费用",
    "资费",
    "优惠",
    "合约",
    "升级",
    "办理",
    "活动",
)
OFF_TOPIC_TECHNICAL_KEYWORDS = (
    "mysql",
    "数据库升级",
    "软件升级",
    "安装新版本",
    "diffstat",
    "mysqlbackup",
    "unbake",
)
INTERNAL_EXPOSURE_MARKERS = (
    "建议坐席话术",
    "确认用户诉求",
    "给出合规话术",
    "风险提醒/转人工条件",
    "是否需要转人工判断",
    "总结建议",
    "内部规则",
    "系统提示词",
)
UNVERIFIED_COMMITMENT_MARKERS = (
    "保证办理",
    "保证成功",
    "一定可以办理",
    "立即生效",
    "永久优惠",
    "绝对免费",
    "零费用",
)
PROVINCES = (
    "北京",
    "天津",
    "河北",
    "山西",
    "内蒙古",
    "辽宁",
    "吉林",
    "黑龙江",
    "上海",
    "江苏",
    "浙江",
    "安徽",
    "福建",
    "江西",
    "山东",
    "河南",
    "湖北",
    "湖南",
    "广东",
    "广西",
    "海南",
    "重庆",
    "四川",
    "贵州",
    "云南",
    "西藏",
    "陕西",
    "甘肃",
    "青海",
    "宁夏",
    "新疆",
)
MONEY_PATTERN = re.compile(r"(?<!\d)(\d{1,5}(?:\.\d{1,2})?)\s*(?:元|块钱)")
NORMALIZE_PATTERN = re.compile(r"[^0-9a-zA-Z\u4e00-\u9fff]+")

RISK_DEFINITIONS = {
    "RUNTIME_ERROR": (100, True, "回答包含系统运行错误信息", "立即转人工并排查模型或工具调用日志。"),
    "OFF_TOPIC": (60, True, "套餐营销问题被回答成数据库或软件操作内容", "停止展示该回答，转人工并检查知识库召回。"),
    "INTERNAL_EXPOSURE": (
        60,
        True,
        "回答向客户暴露了坐席话术或内部处理步骤",
        "改写为直接面向客户的答复，移除内部标签和流程。",
    ),
    "UNVERIFIED_PRICE": (
        50,
        True,
        "回答包含活动、客户问题和套餐上下文中均未确认的金额",
        "不得展示未配置金额，应引用活动库或转人工核实。",
    ),
    "UNVERIFIED_COMMITMENT": (
        50,
        True,
        "回答作出了活动配置中没有的确定性办理承诺",
        "改为条件式说明，并在办理前核实资费、优惠期和合约期。",
    ),
    "PROVINCE_MISMATCH": (
        60,
        True,
        "回答提及的省份与当前客户归属省份不一致",
        "停止展示异地政策，按客户归属地重新检索或转人工。",
    ),
    "REPEATED_ANSWER": (
        25,
        False,
        "回答与上一轮高度重复或在本轮重复相同段落",
        "结合客户追问补充新信息，避免重复整段模板。",
    ),
    "MISSING_MATCHED_BENEFIT": (
        20,
        False,
        "已命中活动，但回答没有体现该活动名称或已配置权益",
        "基于命中活动的客户可见权益重新组织回答。",
    ),
    "MISSING_REFERENCE": (
        15,
        False,
        "营销问题没有命中活动，也没有可追溯的知识库引用",
        "补充知识库依据；无依据时明确说明并转人工核实。",
    ),
    "EMPTY_OR_TOO_SHORT": (30, False, "回答为空或过短，无法解决客户问题", "补充与客户问题直接相关的可执行信息。"),
}


def _normalize(value):
    return NORMALIZE_PATTERN.sub("", str(value or "")).lower()


def _source_for(record):
    record_source = record.source if isinstance(record.source, dict) else {}
    chat_source = record.chat.source if record.chat_id and isinstance(record.chat.source, dict) else {}
    return {**chat_source, **record_source}


def _count_knowledge_references(value):
    if isinstance(value, dict):
        count = 0
        for key, child in value.items():
            if key == "paragraph_list" and isinstance(child, list):
                count += len(child)
            else:
                count += _count_knowledge_references(child)
        return count
    if isinstance(value, list):
        return sum(_count_knowledge_references(item) for item in value)
    return 0


def _policy_fragment_found(answer, recommendation):
    normalized_answer = _normalize(answer)
    for key in ("offer_name", "benefit", "fee_note", "contract_note"):
        text = _normalize(recommendation.get(key))
        if not text:
            continue
        if text in normalized_answer:
            return True
        fragment_length = min(max(len(text) // 3, 6), 12)
        if any(
            text[index : index + fragment_length] in normalized_answer
            for index in range(0, max(len(text) - fragment_length + 1, 1), max(fragment_length // 2, 1))
        ):
            return True
    return False


def _has_repetition(answer, previous_answer):
    parts = [_normalize(part) for part in re.split(r"[。！？!?\n]+", answer or "")]
    meaningful_parts = [part for part in parts if len(part) >= 8]
    if len(meaningful_parts) != len(set(meaningful_parts)):
        return True
    current = _normalize(answer)
    previous = _normalize(previous_answer)
    return bool(len(current) >= 30 and len(previous) >= 30 and SequenceMatcher(None, current, previous).ratio() >= 0.92)


def evaluate_marketing_answer(problem_text, answer_text, source=None, details=None, previous_answer=""):
    source = source if isinstance(source, dict) else {}
    details = details if isinstance(details, dict) else {}
    problem_text = str(problem_text or "")
    answer_text = str(answer_text or "")
    lowered_answer = answer_text.lower()
    recommendation = (
        source.get("marketing_recommendation") if isinstance(source.get("marketing_recommendation"), dict) else {}
    )
    matched_campaign = recommendation.get("status") == "MATCHED"
    reference_count = _count_knowledge_references(details)
    is_marketing_question = any(keyword in problem_text for keyword in MARKETING_QUESTION_KEYWORDS)
    risk_types = []

    def add_risk(risk_type):
        if risk_type not in risk_types:
            risk_types.append(risk_type)

    if "expecting value" in lowered_answer or "traceback" in lowered_answer:
        add_risk("RUNTIME_ERROR")
    if is_marketing_question and any(keyword in lowered_answer for keyword in OFF_TOPIC_TECHNICAL_KEYWORDS):
        add_risk("OFF_TOPIC")
    if any(marker in answer_text for marker in INTERNAL_EXPOSURE_MARKERS):
        add_risk("INTERNAL_EXPOSURE")

    allowed_text = " ".join(
        str(value or "")
        for value in (
            problem_text,
            source.get("marketing_customer_plan"),
            source.get("marketing_customer_data_usage"),
            source.get("marketing_customer_call_usage"),
            recommendation.get("offer_name"),
            recommendation.get("benefit"),
            recommendation.get("fee_note"),
            recommendation.get("contract_note"),
        )
    )
    allowed_amounts = set(MONEY_PATTERN.findall(allowed_text))
    answer_amounts = set(MONEY_PATTERN.findall(answer_text))
    if answer_amounts - allowed_amounts:
        add_risk("UNVERIFIED_PRICE")
    if any(marker in answer_text and marker not in allowed_text for marker in UNVERIFIED_COMMITMENT_MARKERS):
        add_risk("UNVERIFIED_COMMITMENT")

    customer_province = str(source.get("marketing_customer_province") or "").strip()
    mentioned_provinces = {province for province in PROVINCES if province in answer_text}
    if customer_province and any(province != customer_province for province in mentioned_provinces):
        add_risk("PROVINCE_MISMATCH")
    if _has_repetition(answer_text, previous_answer):
        add_risk("REPEATED_ANSWER")
    if matched_campaign and not _policy_fragment_found(answer_text, recommendation):
        add_risk("MISSING_MATCHED_BENEFIT")
    if is_marketing_question and not matched_campaign and reference_count == 0:
        add_risk("MISSING_REFERENCE")
    if len(_normalize(answer_text)) < 12:
        add_risk("EMPTY_OR_TOO_SHORT")

    score = max(0, 100 - sum(RISK_DEFINITIONS[risk_type][0] for risk_type in risk_types))
    if any(RISK_DEFINITIONS[risk_type][1] for risk_type in risk_types):
        status = MarketingAnswerQualityStatus.HIGH_RISK
    elif risk_types:
        status = MarketingAnswerQualityStatus.REVIEW
    else:
        status = MarketingAnswerQualityStatus.PASS
    reasons = [RISK_DEFINITIONS[risk_type][2] for risk_type in risk_types]
    suggestions = list(dict.fromkeys(RISK_DEFINITIONS[risk_type][3] for risk_type in risk_types))
    evidence_source = "CAMPAIGN" if matched_campaign else ("KNOWLEDGE" if reference_count else "NONE")
    return {
        "status": status,
        "score": score,
        "risk_types": risk_types,
        "reasons": reasons,
        "suggestion": " ".join(suggestions),
        "evidence": {
            "source_type": evidence_source,
            "knowledge_reference_count": reference_count,
            "matched_offer_id": recommendation.get("offer_id") if matched_campaign else None,
            "matched_offer_name": recommendation.get("offer_name") if matched_campaign else "",
            "unverified_amounts": sorted(answer_amounts - allowed_amounts),
        },
        "rule_version": RULE_VERSION,
    }


def audit_and_save_quality_review(record, previous_answer=None):
    source = _source_for(record)
    task_id = source.get("marketing_task_id")
    if not task_id:
        return None
    task = MarketingTask.objects.filter(id=task_id).first()
    if task is None:
        return None
    customer = None
    customer_id = source.get("marketing_customer_id")
    if customer_id:
        customer = MarketingCustomer.objects.filter(
            id=customer_id,
            task_id=task.id,
            workspace_id=task.workspace_id,
        ).first()
    if previous_answer is None:
        previous_record = (
            ChatRecord.objects.filter(chat_id=record.chat_id, index__lt=record.index)
            .order_by("-index", "-create_time")
            .first()
        )
        previous_answer = previous_record.answer_text if previous_record else ""
    result = evaluate_marketing_answer(
        record.problem_text,
        record.answer_text,
        source=source,
        details=record.details,
        previous_answer=previous_answer,
    )
    review, _ = MarketingAnswerQualityReview.objects.update_or_create(
        record_id=record.id,
        defaults={
            "workspace_id": task.workspace_id,
            "task_id": task.id,
            "customer_id": customer.id if customer else None,
            **result,
        },
    )
    return review


def ensure_quality_reviews(records):
    records = list(records)
    if not records:
        return {}
    existing = {
        str(review.record_id): review
        for review in MarketingAnswerQualityReview.objects.filter(record_id__in=[record.id for record in records])
    }
    previous_answers = {}
    for record in sorted(records, key=lambda row: (str(row.chat_id), row.index, row.create_time)):
        record_key = str(record.id)
        review = existing.get(record_key)
        if review is None or review.rule_version != RULE_VERSION:
            review = audit_and_save_quality_review(
                record,
                previous_answer=previous_answers.get(str(record.chat_id), ""),
            )
            if review:
                existing[record_key] = review
        previous_answers[str(record.chat_id)] = record.answer_text or ""
    return existing


def serialize_quality_review(review):
    if review is None:
        return None
    return {
        "id": str(review.id),
        "status": review.status,
        "score": review.score,
        "risk_types": review.risk_types or [],
        "reasons": review.reasons or [],
        "suggestion": review.suggestion,
        "evidence": review.evidence or {},
        "rule_version": review.rule_version,
        "manual_status": review.manual_status,
        "reviewer_name": review.reviewer_name,
        "reviewed_at": review.reviewed_at,
        "review_note": review.review_note,
        "revised_answer": review.revised_answer,
        "manual_revision": review.manual_revision,
        "create_time": review.create_time,
        "update_time": review.update_time,
    }
