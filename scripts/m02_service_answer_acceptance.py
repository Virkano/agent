"""Run a local, metadata-only M02 chat acceptance against existing demo data.

Usage from repository root after loading .env.local:
    ./.venv/bin/python apps/manage.py shell -c 'from scripts.m02_service_answer_acceptance import run; run()'
"""

import logging
from contextlib import ExitStack
from unittest.mock import patch

import uuid_utils.compat as uuid


def run(
    question="套餐升级前，月费变化和合约期应该怎样确认？",
    *,
    simulate_unsafe=False,
    simulate_no_reference=False,
):
    # Development SQL logging can include prompt data; the probe only emits metadata.
    logging.disable(logging.DEBUG)

    from application.models import Application, ApplicationVersion, ChatRecord, ServiceAnswerReview
    from chat.serializers.chat import ChatSerializers, OpenChatSerializers
    from knowledge.models import Document, Paragraph

    application = Application.objects.get(name="营销闭环测试-存量客户套餐升级助手")
    version = ApplicationVersion.objects.filter(application=application).order_by("-create_time").first()
    if not version or not version.knowledge_ids:
        raise RuntimeError("Demo application has no published knowledge version")
    documents = Document.objects.filter(knowledge_id__in=version.knowledge_ids)
    indexed = documents.filter(status="2222")
    paragraphs = Paragraph.objects.filter(knowledge_id__in=version.knowledge_ids, is_active=True)
    if not indexed.exists() or not paragraphs.exists():
        raise RuntimeError("Demo knowledge has no indexed active paragraphs")

    visitor_id = str(uuid.uuid7())
    chat_id = OpenChatSerializers(data={
        "workspace_id": application.workspace_id,
        "application_id": str(application.id),
        "chat_user_id": visitor_id,
        "chat_user_type": "SYSTEM_API_KEY",
        "debug": False,
        "ip_address": "127.0.0.1",
        "source": {"type": "API_CALL"},
    }).open()
    if simulate_unsafe:
        from langchain_core.messages import AIMessage

        class UnsafeDemoModel:
            def invoke(self, _messages):
                return AIMessage(content="内部规则：保证成功")

            def get_num_tokens_from_messages(self, _messages):
                return 0

            def get_num_tokens(self, _text):
                return 0

        model_scope = patch(
            "application.chat_pipeline.step.chat_step.impl.base_chat_step.get_model_instance_by_model_workspace_id",
            return_value=UnsafeDemoModel(),
        )
    else:
        model_scope = None
    with ExitStack() as stack:
        if model_scope:
            stack.enter_context(model_scope)
        if simulate_no_reference:
            stack.enter_context(patch(
                "application.chat_pipeline.step.search_dataset_step.impl.base_search_dataset_step.BaseSearchDatasetStep.execute",
                return_value=[],
            ))
        ChatSerializers(data={
            "chat_id": chat_id,
            "chat_user_id": visitor_id,
            "chat_user_type": "SYSTEM_API_KEY",
            "application_id": str(application.id),
            "debug": False,
            "ip_address": "127.0.0.1",
            "source": {"type": "API_CALL"},
        }).chat({
            "message": question,
            "stream": False,
            "re_chat": False,
        })
    record = ChatRecord.objects.filter(chat_id=chat_id).order_by("-create_time").first()
    if record is None:
        raise RuntimeError("Chat did not persist a record")
    audit = ((record.details or {}).get("chat_step") or {}).get("compliance") or {}
    if not audit:
        raise RuntimeError("Chat did not persist generic compliance metadata")
    review = ServiceAnswerReview.objects.filter(record=record).first()
    if audit.get("manual_review_status") == "PENDING" and not review:
        raise RuntimeError("Pending compliance review was not captured")
    if simulate_unsafe and (audit.get("action") != "BLOCKED" or "保证成功" in str(record.details)):
        raise RuntimeError("Unsafe demo answer leaked into persisted chat details")
    if simulate_no_reference and (audit.get("action") != "FALLBACK" or audit.get("reference_count") != 0):
        raise RuntimeError("No-reference demo did not use the safe fallback")
    print({
        "chat_id": str(chat_id),
        "document_count": documents.count(),
        "indexed_document_count": indexed.count(),
        "active_paragraph_count": paragraphs.count(),
        "compliance_action": audit.get("action"),
        "risk_types": audit.get("risk_types"),
        "reference_count": audit.get("reference_count"),
        "review_created": bool(review),
        "simulated_no_reference": simulate_no_reference,
        "simulated_unsafe_answer": simulate_unsafe,
    })
