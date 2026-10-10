"""Deterministic routing for short conversational control messages.

Knowledge retrieval is useful for business questions, but it is actively harmful
for a standalone greeting: a low similarity threshold can turn an unrelated
paragraph into a fabricated business state.  Keep this router deliberately
small and high precision.  Messages that contain an actual question continue
through the normal retrieval and LLM pipeline.
"""

import re
from dataclasses import dataclass


_IGNORABLE_CHARACTERS = re.compile(r"[\s\u3000,，。.!！?？~～、;；:：'\"“”‘’]+")


@dataclass(frozen=True)
class ConversationRoute:
    intent: str
    answer: str


_ROUTES = {
    "greeting": (
        {
            "你好",
            "您好",
            "你好啊",
            "您好啊",
            "嗨",
            "哈喽",
            "哈啰",
            "在吗",
            "早上好",
            "上午好",
            "下午好",
            "晚上好",
            "hello",
            "hi",
        },
        "您好！我是中国电信套餐升级服务助手，请问您想了解套餐、流量、宽带还是办理规则？",
    ),
    "thanks": (
        {"谢谢", "谢谢你", "谢谢您", "感谢", "感谢你", "感谢您", "多谢", "好的谢谢"},
        "不客气，很高兴能帮到您。如果还有套餐或办理方面的问题，可以继续告诉我。",
    ),
    "goodbye": (
        {"再见", "拜拜", "先这样", "不用了", "没问题了", "bye", "goodbye"},
        "好的，感谢您的咨询，祝您生活愉快！",
    ),
}


def _normalize(text: str) -> str:
    return _IGNORABLE_CHARACTERS.sub("", str(text or "")).casefold()


def route_conversation_control_message(text: str) -> ConversationRoute | None:
    """Route only a pure greeting/thanks/goodbye; never swallow a business query."""
    normalized = _normalize(text)
    if not normalized:
        return None
    for intent, (utterances, answer) in _ROUTES.items():
        if normalized in utterances:
            return ConversationRoute(intent=intent, answer=answer)
    return None
