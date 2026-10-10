# coding=utf-8
"""
@project: dianxin
@project: dianxin
@file： base_chat_step.py
@date：2024/1/9 18:25
@desc: 对话step Base实现
"""

import json
import time
import traceback
from typing import List

import uuid_utils.compat as uuid
from application.chat_pipeline.I_base_chat_pipeline import ParagraphPipelineModel
from application.chat_pipeline.pipeline_manage import PipelineManage
from application.chat_pipeline.step.chat_step.i_chat_step import IChatStep, PostResponseHandler
from application.answer_compliance import (
    BLOCKED_ANSWER,
    evaluate_knowledge_answer,
    runtime_failure_audit,
    should_apply_platform_compliance,
)
from application.flow.tools import Reasoning, get_tools, mcp_response_generator
from application.long_term_memory import extract_long_term_memory
from application.models import (
    Application,
    ApplicationAccessToken,
    ApplicationApiKey,
    ApplicationChatUserStats,
    ApplicationLongTermMemory,
    ChatUserType,
)
from common.exception.app_exception import AppApiException
from common.utils.logger import telecom_ai_logger
from common.utils.rsa_util import rsa_long_decrypt
from common.utils.shared_resource_auth import filter_authorized_ids, get_runtime_user_id
from common.utils.tool_code import ToolExecutor
from django.db.models import QuerySet
from django.http import StreamingHttpResponse
from django.utils.translation import gettext as _
from langchain.chat_models.base import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, HumanMessage, SystemMessage
from models_provider.tools import get_model_instance_by_model_workspace_id
from rest_framework import status
from tools.models import Tool, ToolType


def add_access_num(chat_user_id=None, chat_user_type=None, application_id=None):
    if [ChatUserType.ANONYMOUS_USER.value, ChatUserType.CHAT_USER.value].__contains__(
        chat_user_type
    ) and application_id is not None:
        application_public_access_client = (
            QuerySet(ApplicationChatUserStats)
            .filter(chat_user_id=chat_user_id, chat_user_type=chat_user_type, application_id=application_id)
            .first()
        )
        if application_public_access_client is not None:
            application_public_access_client.access_num = application_public_access_client.access_num + 1
            application_public_access_client.intraday_access_num = (
                application_public_access_client.intraday_access_num + 1
            )
            application_public_access_client.save()


def write_context(step, manage, request_token, response_token, all_text):
    step.context["message_tokens"] = request_token
    step.context["answer_tokens"] = response_token
    current_time = time.time()
    step.context["answer_text"] = all_text
    step.context["run_time"] = current_time - step.context["start_time"]
    manage.context["run_time"] = current_time - manage.context["start_time"]
    manage.context["message_tokens"] = manage.context["message_tokens"] + request_token
    manage.context["answer_tokens"] = manage.context["answer_tokens"] + response_token


def get_marketing_customer_safe_answer(problem_text: str, source: dict | None, answer_text: str):
    """Prevent a weak local model from making unverified fee commitments to a marketing customer."""
    if not isinstance(source, dict) or not source.get("marketing_task_id") or not source.get("marketing_customer_id"):
        return answer_text

    question = problem_text or ""
    if not any(word in question for word in ["贵", "费用", "多少钱", "加钱", "额外", "月费", "价格", "资费"]):
        return answer_text

    if any(word in question for word in ["贵", "多少钱", "价格", "资费"]):
        return (
            "是否划算要结合您当地可办理的方案和月费变化来判断。"
            "办理前会先向您确认月费变化、优惠期限和合约期，确认清楚后再由您决定是否办理。"
        )
    return (
        "套餐升级是否会增加费用，要以您当地实际可办理的方案为准。"
        "办理前会先向您确认月费变化、优惠期限和合约期，确认清楚后再由您决定是否办理。"
    )


def get_marketing_runtime_fallback(problem_text: str, source: dict | None):
    """Return customer-facing text when a dependency fails during a marketing chat."""
    if not isinstance(source, dict) or not source.get("marketing_task_id"):
        return None
    safe_answer = get_marketing_customer_safe_answer(problem_text, source, "")
    if safe_answer:
        return safe_answer
    return "暂时无法查询最新的本地办理信息，请稍后重试；如需立即确认，可联系当地营业厅或人工客服。"


def get_marketing_customer_answer(problem_text: str, source: dict | None, answer_text: str):
    """Apply customer-safe pricing first, then a configured recommendation."""
    safe_answer = get_marketing_customer_safe_answer(problem_text, source, answer_text)
    if safe_answer != answer_text:
        return safe_answer
    from marketing.recommendation import get_customer_recommendation_answer

    return get_customer_recommendation_answer(problem_text, source, answer_text)


def needs_marketing_customer_review(problem_text: str, source: dict | None):
    if not isinstance(source, dict) or not source.get("marketing_task_id") or not source.get("marketing_customer_id"):
        return False
    question = problem_text or ""
    if any(word in question for word in ["贵", "费用", "多少钱", "加钱", "额外", "月费", "价格", "资费"]):
        return True
    from marketing.recommendation import RECOMMENDATION_QUESTION_KEYWORDS

    recommendation = source.get("marketing_recommendation")
    return (
        isinstance(recommendation, dict)
        and recommendation.get("status") == "MATCHED"
        and any(word in question for word in RECOMMENDATION_QUESTION_KEYWORDS)
    )


def prepare_marketing_answer_preflight(
    problem_text: str,
    generated_answer: str,
    final_answer: str,
    source: dict | None,
    chat_id=None,
    paragraph_count=0,
):
    """Run the optional marketing shadow check without making chat availability depend on it."""
    try:
        from marketing.preflight import prepare_marketing_preflight

        return prepare_marketing_preflight(
            problem_text,
            generated_answer,
            final_answer,
            source,
            chat_id=chat_id,
            paragraph_count=paragraph_count,
        )
    except Exception:
        telecom_ai_logger.exception("Marketing shadow preflight evaluation failed for chat %s", chat_id)
        return None


def should_buffer_marketing_answer_preflight(source: dict | None):
    try:
        from marketing.preflight import should_buffer_marketing_preflight

        return should_buffer_marketing_preflight(source)
    except Exception:
        telecom_ai_logger.exception("Marketing preflight policy lookup failed")
        return False


def save_marketing_answer_preflight(chat_record_id, snapshot):
    try:
        from marketing.preflight import save_marketing_preflight

        return save_marketing_preflight(chat_record_id, snapshot)
    except Exception:
        telecom_ai_logger.exception("Marketing shadow preflight persistence failed for chat record %s", chat_record_id)
        return None


def event_content(
    response,
    chat_id,
    chat_record_id,
    paragraph_list: List[ParagraphPipelineModel],
    post_response_handler: PostResponseHandler,
    manage,
    step,
    chat_model,
    message_list: List[BaseMessage],
    problem_text: str,
    padding_problem_text: str = None,
    chat_user_id=None,
    chat_user_type=None,
    is_ai_chat: bool = None,
    model_setting=None,
):
    if model_setting is None:
        model_setting = {}
    reasoning_content_enable = model_setting.get("reasoning_content_enable", False)
    reasoning_content_start = model_setting.get("reasoning_content_start", "<think>")
    reasoning_content_end = model_setting.get("reasoning_content_end", "</think>")
    reasoning = Reasoning(reasoning_content_start, reasoning_content_end)
    all_text = ""
    reasoning_content = ""
    knowledge_enabled = should_apply_platform_compliance(manage.context)
    marketing_review_before_send = needs_marketing_customer_review(
        problem_text, manage.context.get("source")
    ) or should_buffer_marketing_answer_preflight(manage.context.get("source"))
    review_before_send = knowledge_enabled or marketing_review_before_send
    try:
        response_reasoning_content = False
        for chunk in response:
            reasoning_chunk = reasoning.get_reasoning_content(chunk)
            content_chunk = reasoning_chunk.get("content")
            if "reasoning_content" in chunk.additional_kwargs:
                response_reasoning_content = True
                reasoning_content_chunk = chunk.additional_kwargs.get("reasoning_content", "")
            else:
                reasoning_content_chunk = reasoning_chunk.get("reasoning_content")
            content_chunk = reasoning._normalize_content(content_chunk)
            all_text += content_chunk
            if reasoning_content_chunk is None:
                reasoning_content_chunk = ""
            reasoning_content += reasoning_content_chunk
            if not review_before_send:
                yield manage.get_base_to_response().to_stream_chunk_response(
                    chat_id,
                    str(chat_record_id),
                    "ai-chat-node",
                    [],
                    content_chunk,
                    False,
                    0,
                    0,
                    {
                        "node_is_end": False,
                        "view_type": "many_view",
                        "node_type": "ai-chat-node",
                        "real_node_id": "ai-chat-node",
                        "reasoning_content": reasoning_content_chunk if reasoning_content_enable else "",
                    },
                )
        reasoning_chunk = reasoning.get_end_reasoning_content()
        all_text += reasoning_chunk.get("content")
        reasoning_content_chunk = ""
        if not response_reasoning_content:
            reasoning_content_chunk = reasoning_chunk.get("reasoning_content")
        if not review_before_send:
            yield manage.get_base_to_response().to_stream_chunk_response(
                chat_id,
                str(chat_record_id),
                "ai-chat-node",
                [],
                reasoning_chunk.get("content"),
                False,
                0,
                0,
                {
                    "node_is_end": False,
                    "view_type": "many_view",
                    "node_type": "ai-chat-node",
                    "real_node_id": "ai-chat-node",
                    "reasoning_content": reasoning_content_chunk if reasoning_content_enable else "",
                },
            )
        # 获取token
        if is_ai_chat:
            try:
                request_token = chat_model.get_num_tokens_from_messages(message_list)
                response_token = chat_model.get_num_tokens(all_text)
            except Exception:
                request_token = 0
                response_token = 0
        else:
            request_token = 0
            response_token = 0
        generated_text = all_text
        if marketing_review_before_send:
            all_text = get_marketing_customer_answer(problem_text, manage.context.get("source"), all_text)
        preflight_snapshot = prepare_marketing_answer_preflight(
            problem_text,
            generated_text,
            all_text,
            manage.context.get("source"),
            chat_id=chat_id,
            paragraph_count=len(paragraph_list or []),
        )
        if preflight_snapshot:
            all_text = preflight_snapshot.get("final_answer", all_text)
        if knowledge_enabled:
            no_reference_setting = manage.context.get("no_references_setting") or {}
            all_text, step.context["compliance"] = evaluate_knowledge_answer(
                all_text,
                paragraph_list,
                configured_fallback=no_reference_setting.get("status") == "designated_answer",
            )
            if preflight_snapshot:
                preflight_snapshot["final_answer"] = all_text
        if review_before_send:
            yield manage.get_base_to_response().to_stream_chunk_response(
                chat_id,
                str(chat_record_id),
                "ai-chat-node",
                [],
                all_text,
                False,
                0,
                0,
                {
                    "node_is_end": False,
                    "view_type": "many_view",
                    "node_type": "ai-chat-node",
                    "real_node_id": "ai-chat-node",
                    "reasoning_content": "",
                },
            )
        write_context(step, manage, request_token, response_token, all_text)
        post_response_handler.handler(
            chat_id,
            chat_record_id,
            paragraph_list,
            problem_text,
            all_text,
            manage,
            step,
            padding_problem_text,
            reasoning_content=reasoning_content if reasoning_content_enable and not knowledge_enabled else "",
        )
        save_marketing_answer_preflight(chat_record_id, preflight_snapshot)
        yield manage.get_base_to_response().to_stream_chunk_response(
            chat_id,
            str(chat_record_id),
            "ai-chat-node",
            [],
            "",
            True,
            request_token,
            response_token,
            {"node_is_end": True, "view_type": "many_view", "node_type": "ai-chat-node"},
        )
        if not manage.debug:
            add_access_num(chat_user_id, chat_user_type, manage.context.get("application_id"))
    except BaseException as e:
        if isinstance(e, GeneratorExit):
            telecom_ai_logger.error("Generator was closed (client disconnected)")
        else:
            telecom_ai_logger.error(f"{str(e)}:{traceback.format_exc()}")
            if knowledge_enabled:
                all_text = BLOCKED_ANSWER
                step.context["compliance"] = runtime_failure_audit()
            else:
                all_text = get_marketing_runtime_fallback(problem_text, manage.context.get("source")) or (
                    "Exception:" + str(e)
                )
        write_context(step, manage, 0, 0, all_text)
        post_response_handler.handler(
            chat_id,
            chat_record_id,
            paragraph_list,
            problem_text,
            all_text,
            manage,
            step,
            padding_problem_text,
            reasoning_content=reasoning_content if reasoning_content_enable and not knowledge_enabled else "",
        )
        if not manage.debug:
            add_access_num(chat_user_id, chat_user_type, manage.context.get("application_id"))
        yield manage.get_base_to_response().to_stream_chunk_response(
            chat_id,
            str(chat_record_id),
            "ai-chat-node",
            [],
            all_text,
            False,
            0,
            0,
            {
                "node_is_end": False,
                "view_type": "many_view",
                "node_type": "ai-chat-node",
                "real_node_id": "ai-chat-node",
                "reasoning_content": "",
            },
        )


class BaseChatStep(IChatStep):
    def execute(
        self,
        message_list: List[BaseMessage],
        chat_id,
        problem_text,
        post_response_handler: PostResponseHandler,
        model_id: str = None,
        workspace_id: str = None,
        paragraph_list=None,
        manage: PipelineManage = None,
        padding_problem_text: str = None,
        stream: bool = True,
        chat_user_id=None,
        chat_user_type=None,
        no_references_setting=None,
        model_params_setting=None,
        model_setting=None,
        mcp_tool_ids=None,
        mcp_servers="",
        mcp_source="referencing",
        tool_ids=None,
        application_ids=None,
        skill_tool_ids=None,
        mcp_output_enable=True,
        **kwargs,
    ):
        chat_model = (
            get_model_instance_by_model_workspace_id(model_id, workspace_id, **(model_params_setting or {}))
            if model_id is not None
            else None
        )
        if stream:
            return self.execute_stream(
                message_list,
                chat_id,
                problem_text,
                post_response_handler,
                chat_model,
                paragraph_list,
                manage,
                padding_problem_text,
                chat_user_id,
                chat_user_type,
                no_references_setting,
                model_setting,
                mcp_tool_ids,
                mcp_servers,
                mcp_source,
                tool_ids,
                application_ids,
                skill_tool_ids,
                workspace_id,
                mcp_output_enable,
            )
        else:
            return self.execute_block(
                message_list,
                chat_id,
                problem_text,
                post_response_handler,
                chat_model,
                paragraph_list,
                manage,
                padding_problem_text,
                chat_user_id,
                chat_user_type,
                no_references_setting,
                model_setting,
                mcp_tool_ids,
                mcp_servers,
                mcp_source,
                tool_ids,
                application_ids,
                skill_tool_ids,
                workspace_id,
                mcp_output_enable,
            )

    def get_details(self, manage, **kwargs):
        # 提取长期记忆
        extract_long_term_memory.apply_async(
            args=(
                manage.context.get("workspace_id"),
                manage.context.get("application_id"),
                manage.context.get("chat_user_id"),
            ),
            countdown=1,
        )
        return {
            "status": self.status,
            "err_message": self.err_message,
            "step_type": "chat_step",
            "run_time": self.context.get("run_time") or 0,
            "model_id": str(manage.context["model_id"]),
            "message_list": self.reset_message_list(
                self.context["step_args"].get("message_list"), self.context.get("answer_text")
            ),
            "message_tokens": self.context.get("message_tokens"),
            "answer_tokens": self.context.get("answer_tokens"),
            "cost": 0,
            "compliance": self.context.get("compliance"),
        }

    @staticmethod
    def reset_message_list(message_list: List[BaseMessage], answer_text):
        result = [
            {
                "role": "user"
                if isinstance(message, HumanMessage)
                else ("system" if isinstance(message, SystemMessage) else "ai"),
                "content": message.content,
            }
            for message in message_list
        ]
        result.append({"role": "ai", "content": answer_text})
        return result

    def _handle_mcp_request(
        self,
        mcp_source,
        mcp_servers,
        mcp_tool_ids,
        tool_ids,
        application_ids,
        skill_tool_ids,
        mcp_output_enable,
        chat_model,
        system_prompt,
        message_list,
        agent_id,
        chat_id,
        workspace_id,
        runtime_user_id=None,
    ):

        mcp_servers_config = {}

        # 迁移过来mcp_source是None
        if mcp_source is None:
            mcp_source = "custom"
        # 兼容老数据
        if not mcp_tool_ids:
            mcp_tool_ids = []
        if mcp_source == "custom" and mcp_servers:
            mcp_servers_config = json.loads(mcp_servers)
        elif mcp_tool_ids:
            mcp_tools = QuerySet(Tool).filter(id__in=mcp_tool_ids).values()
            for mcp_tool in mcp_tools:
                if mcp_tool and mcp_tool["is_active"]:
                    mcp_servers_config = {**mcp_servers_config, **json.loads(mcp_tool["code"])}
        # 校验代码是否包括禁止的关键字
        ToolExecutor().validate_mcp_transport(json.dumps(mcp_servers_config))

        tool_init_params = {}
        tools = get_tools("APPLICATION", agent_id, tool_ids, workspace_id, runtime_user_id)
        if tool_ids and len(tool_ids) > 0:  # 如果有工具ID，则将其转换为MCP
            self.context["tool_ids"] = tool_ids
            for tool_id in tool_ids:
                tool = QuerySet(Tool).filter(id=tool_id, tool_type=ToolType.CUSTOM).first()
                if tool is None or tool.is_active is False:
                    continue
                executor = ToolExecutor()
                init_params_default_value = {i["field"]: i.get("default_value") for i in tool.init_field_list}
                if tool.init_params is not None:
                    tool_init_params = init_params_default_value | json.loads(rsa_long_decrypt(tool.init_params))
                else:
                    tool_init_params = init_params_default_value
                tool_config = executor.get_tool_mcp_config(tool, tool_init_params)

                mcp_servers_config[str(tool.id)] = tool_config

        if application_ids and len(application_ids) > 0:
            self.context["application_ids"] = application_ids
            for application_id in application_ids:
                app = QuerySet(Application).filter(id=application_id, is_publish=True).first()
                if app is None:
                    continue
                app_key = QuerySet(ApplicationApiKey).filter(application_id=application_id, is_active=True).first()
                if app_key is not None:
                    api_key = app_key.secret_key
                    application_access_token = (
                        QuerySet(ApplicationAccessToken).filter(application_id=app_key.application_id).first()
                    )
                    if application_access_token is not None and application_access_token.authentication:
                        raise AppApiException(
                            500,
                            _("Agent 【{name}】 access token authentication is not supported for agent tool").format(
                                name=app.name
                            ),
                        )
                else:
                    raise AppApiException(
                        500, _("Agent Key is required for agent tool 【{name}】").format(name=app.name)
                    )
                executor = ToolExecutor()
                app_config = executor.get_app_mcp_config(api_key)
                mcp_servers_config[app.name] = app_config

        if skill_tool_ids and len(skill_tool_ids) > 0:
            self.context["skill_tool_ids"] = skill_tool_ids
            skill_file_items = []

            for tool_id in skill_tool_ids:
                tool = QuerySet(Tool).filter(id=tool_id, is_active=True).first()
                if tool is None or tool.is_active is False:
                    continue
                init_params_default_value = {i["field"]: i.get("default_value") for i in tool.init_field_list}
                if tool.init_params is not None:
                    params = init_params_default_value | json.loads(rsa_long_decrypt(tool.init_params))
                else:
                    params = init_params_default_value

                skill_file_items.append({"tool_id": str(tool.id), "file_id": tool.code, "params": params})
            mcp_servers_config["skills"] = skill_file_items

        if len(mcp_servers_config) > 0 or len(tools) > 0:
            source_id = agent_id
            source_type = "APPLICATION"
            return mcp_response_generator(
                chat_model,
                system_prompt,
                message_list,
                json.dumps(mcp_servers_config),
                mcp_output_enable,
                tool_init_params,
                source_id,
                source_type,
                chat_id,
                tools,
            )

        return None

    def get_stream_result(
        self,
        message_list: List[BaseMessage],
        chat_model: BaseChatModel = None,
        paragraph_list=None,
        no_references_setting=None,
        problem_text=None,
        mcp_tool_ids=None,
        mcp_servers="",
        mcp_source="referencing",
        tool_ids=None,
        application_ids=None,
        skill_tool_ids=None,
        workspace_id=None,
        mcp_output_enable=True,
        agent_id=None,
        chat_id=None,
        chat_user_id=None,
        chat_user_type=None,
    ):
        if paragraph_list is None:
            paragraph_list = []
        directly_return_chunk_list = [
            AIMessageChunk(content=paragraph.content)
            for paragraph in paragraph_list
            if (
                paragraph.hit_handling_method == "directly_return"
                and paragraph.similarity >= paragraph.directly_return_similarity
            )
        ]
        if directly_return_chunk_list is not None and len(directly_return_chunk_list) > 0:
            return iter(directly_return_chunk_list), False
        elif len(paragraph_list) == 0 and no_references_setting.get("status") == "designated_answer":
            return iter(
                [AIMessageChunk(content=no_references_setting.get("value").replace("{question}", problem_text))]
            ), False
        if chat_model is None:
            return iter(
                [
                    AIMessageChunk(
                        _(
                            "Sorry, the AI model is not configured. Please go to the application to set up the AI model first."
                        )
                    )
                ]
            ), False
        else:
            user_system_prompt = None
            filtered_message_list = []
            long_term_memory = (
                QuerySet(ApplicationLongTermMemory).filter(chat_user_id=chat_user_id, application_id=agent_id).first()
            )
            if long_term_memory is not None:
                memory = long_term_memory.memory
            else:
                memory = ""

            # print(chat_user_id, chat_user_type)
            for msg in message_list:
                if isinstance(msg, SystemMessage):
                    if isinstance(msg.content, str):
                        user_system_prompt = msg.content.replace("{memory}", memory)
                        msg.content = user_system_prompt
                    elif isinstance(msg.content, list):
                        user_system_prompt = "".join(
                            item.get("text", "") if isinstance(item, dict) else str(item) for item in msg.content
                        )
                    else:
                        user_system_prompt = str(msg.content)
                else:
                    filtered_message_list.append(msg)
            runtime_user_id = get_runtime_user_id(chat_user_id=chat_user_id, chat_user_type=chat_user_type)
            # 过滤tool_id
            all_tool_ids = list(set((mcp_tool_ids or []) + (tool_ids or []) + (skill_tool_ids or [])))
            authorized_set = set(filter_authorized_ids("tool", all_tool_ids, workspace_id, user_id=runtime_user_id))

            mcp_tool_ids = [i for i in (mcp_tool_ids or []) if i in authorized_set]
            tool_ids = [i for i in (tool_ids or []) if i in authorized_set]
            skill_tool_ids = [i for i in (skill_tool_ids or []) if i in authorized_set]
            # 处理 MCP 请求
            mcp_result = self._handle_mcp_request(
                mcp_source,
                mcp_servers,
                mcp_tool_ids,
                tool_ids,
                application_ids,
                skill_tool_ids,
                mcp_output_enable,
                chat_model,
                user_system_prompt,
                filtered_message_list,
                agent_id,
                chat_id,
                workspace_id,
                runtime_user_id,
            )
            if mcp_result:
                return mcp_result, True
            return chat_model.stream(message_list), True

    def execute_stream(
        self,
        message_list: List[BaseMessage],
        chat_id,
        problem_text,
        post_response_handler: PostResponseHandler,
        chat_model: BaseChatModel = None,
        paragraph_list=None,
        manage: PipelineManage = None,
        padding_problem_text: str = None,
        chat_user_id=None,
        chat_user_type=None,
        no_references_setting=None,
        model_setting=None,
        mcp_tool_ids=None,
        mcp_servers="",
        mcp_source="referencing",
        tool_ids=None,
        application_ids=None,
        skill_tool_ids=None,
        workspace_id=None,
        mcp_output_enable=True,
    ):
        chat_result, is_ai_chat = self.get_stream_result(
            message_list,
            chat_model,
            paragraph_list,
            no_references_setting,
            problem_text,
            mcp_tool_ids,
            mcp_servers,
            mcp_source,
            tool_ids,
            application_ids,
            skill_tool_ids,
            workspace_id,
            mcp_output_enable,
            manage.context.get("application_id"),
            chat_id,
            chat_user_id,
            chat_user_type,
        )
        chat_record_id = (
            self.context.get("step_args", {}).get("chat_record_id")
            if self.context.get("step_args", {}).get("chat_record_id")
            else uuid.uuid7()
        )
        r = StreamingHttpResponse(
            streaming_content=event_content(
                chat_result,
                chat_id,
                chat_record_id,
                paragraph_list,
                post_response_handler,
                manage,
                self,
                chat_model,
                message_list,
                problem_text,
                padding_problem_text,
                chat_user_id,
                chat_user_type,
                is_ai_chat,
                model_setting,
            ),
            content_type="text/event-stream;charset=utf-8",
        )

        r["Cache-Control"] = "no-cache"
        return r

    def get_block_result(
        self,
        message_list: List[BaseMessage],
        chat_model: BaseChatModel = None,
        paragraph_list=None,
        no_references_setting=None,
        problem_text=None,
        mcp_tool_ids=None,
        mcp_servers="",
        mcp_source="referencing",
        tool_ids=None,
        application_ids=None,
        skill_tool_ids=None,
        workspace_id=None,
        mcp_output_enable=True,
        application_id=None,
        chat_id=None,
        chat_user_id=None,
        chat_user_type=None,
    ):
        if paragraph_list is None:
            paragraph_list = []
        directly_return_chunk_list = [
            AIMessageChunk(content=paragraph.content)
            for paragraph in paragraph_list
            if (
                paragraph.hit_handling_method == "directly_return"
                and paragraph.similarity >= paragraph.directly_return_similarity
            )
        ]
        if directly_return_chunk_list is not None and len(directly_return_chunk_list) > 0:
            return directly_return_chunk_list[0], False
        elif len(paragraph_list) == 0 and no_references_setting.get("status") == "designated_answer":
            return AIMessage(no_references_setting.get("value").replace("{question}", problem_text)), False
        if chat_model is None:
            return AIMessage(
                _("Sorry, the AI model is not configured. Please go to the application to set up the AI model first.")
            ), False
        else:
            runtime_user_id = get_runtime_user_id(chat_user_id=chat_user_id, chat_user_type=chat_user_type)
            # 过滤tool_id
            all_tool_ids = list(set((mcp_tool_ids or []) + (tool_ids or []) + (skill_tool_ids or [])))
            authorized_set = set(filter_authorized_ids("tool", all_tool_ids, workspace_id, user_id=runtime_user_id))

            mcp_tool_ids = [i for i in (mcp_tool_ids or []) if i in authorized_set]
            tool_ids = [i for i in (tool_ids or []) if i in authorized_set]
            skill_tool_ids = [i for i in (skill_tool_ids or []) if i in authorized_set]
            # 处理 MCP 请求
            mcp_result = self._handle_mcp_request(
                mcp_source,
                mcp_servers,
                mcp_tool_ids,
                tool_ids,
                application_ids,
                skill_tool_ids,
                mcp_output_enable,
                chat_model,
                "",
                message_list,
                application_id,
                chat_id,
                workspace_id,
                runtime_user_id,
            )
            if mcp_result:
                return mcp_result, True
            return chat_model.invoke(message_list), True

    def execute_block(
        self,
        message_list: List[BaseMessage],
        chat_id,
        problem_text,
        post_response_handler: PostResponseHandler,
        chat_model: BaseChatModel = None,
        paragraph_list=None,
        manage: PipelineManage = None,
        padding_problem_text: str = None,
        chat_user_id=None,
        chat_user_type=None,
        no_references_setting=None,
        model_setting=None,
        mcp_tool_ids=None,
        mcp_servers="",
        mcp_source="referencing",
        tool_ids=None,
        application_ids=None,
        skill_tool_ids=None,
        workspace_id=None,
        mcp_output_enable=True,
    ):
        reasoning_content_enable = model_setting.get("reasoning_content_enable", False)
        reasoning_content_start = model_setting.get("reasoning_content_start", "<think>")
        reasoning_content_end = model_setting.get("reasoning_content_end", "</think>")
        reasoning = Reasoning(reasoning_content_start, reasoning_content_end)
        chat_record_id = uuid.uuid7()
        # 调用模型
        try:
            chat_result, is_ai_chat = self.get_block_result(
                message_list,
                chat_model,
                paragraph_list,
                no_references_setting,
                problem_text,
                mcp_tool_ids,
                mcp_servers,
                mcp_source,
                tool_ids,
                application_ids,
                skill_tool_ids,
                workspace_id,
                mcp_output_enable,
                manage.context.get("application_id"),
                chat_id,
                chat_user_id,
                chat_user_type,
            )
            if is_ai_chat:
                request_token = chat_model.get_num_tokens_from_messages(message_list)
                response_token = chat_model.get_num_tokens(chat_result.content)
            else:
                request_token = 0
                response_token = 0
            reasoning_result = reasoning.get_reasoning_content(chat_result)
            reasoning_result_end = reasoning.get_end_reasoning_content()
            generated_content = reasoning_result.get("content") + reasoning_result_end.get("content")
            content = get_marketing_customer_safe_answer(
                problem_text,
                manage.context.get("source"),
                generated_content,
            )
            preflight_snapshot = prepare_marketing_answer_preflight(
                problem_text,
                generated_content,
                content,
                manage.context.get("source"),
                chat_id=chat_id,
                paragraph_count=len(paragraph_list or []),
            )
            if preflight_snapshot:
                content = preflight_snapshot.get("final_answer", content)
            knowledge_enabled = should_apply_platform_compliance(manage.context)
            if knowledge_enabled:
                no_reference_setting = manage.context.get("no_references_setting") or {}
                content, self.context["compliance"] = evaluate_knowledge_answer(
                    content,
                    paragraph_list,
                    configured_fallback=no_reference_setting.get("status") == "designated_answer",
                )
                if preflight_snapshot:
                    preflight_snapshot["final_answer"] = content
            write_context(self, manage, request_token, response_token, content)
            if "reasoning_content" in chat_result.response_metadata:
                reasoning_content = chat_result.response_metadata.get("reasoning_content", "") or ""
            else:
                reasoning_content = (reasoning_result.get("reasoning_content") or "") + (
                    reasoning_result_end.get("reasoning_content") or ""
                )
            if knowledge_enabled:
                reasoning_content = ""
            post_response_handler.handler(
                chat_id,
                chat_record_id,
                paragraph_list,
                problem_text,
                content,
                manage,
                self,
                padding_problem_text,
                reasoning_content=reasoning_content,
            )
            save_marketing_answer_preflight(chat_record_id, preflight_snapshot)
            if not manage.debug:
                add_access_num(chat_user_id, chat_user_type, manage.context.get("application_id"))
            return manage.get_base_to_response().to_block_response(
                str(chat_id),
                str(chat_record_id),
                content,
                True,
                request_token,
                response_token,
                {
                    "reasoning_content": reasoning_content if reasoning_content_enable else "",
                    "answer_list": [
                        {"content": content, "reasoning_content": reasoning_content if reasoning_content_enable else ""}
                    ],
                },
            )
        except Exception as e:
            if should_apply_platform_compliance(manage.context):
                all_text = BLOCKED_ANSWER
                self.context["compliance"] = runtime_failure_audit()
            else:
                all_text = get_marketing_runtime_fallback(problem_text, manage.context.get("source")) or (
                    "Exception:" + str(e)
                )
            write_context(self, manage, 0, 0, all_text)
            post_response_handler.handler(
                chat_id,
                chat_record_id,
                paragraph_list,
                problem_text,
                all_text,
                manage,
                self,
                padding_problem_text,
                reasoning_content="",
            )
            if not manage.debug:
                add_access_num(chat_user_id, chat_user_type, manage.context.get("application_id"))
            fallback_status = (
                status.HTTP_200_OK
                if get_marketing_runtime_fallback(problem_text, manage.context.get("source"))
                else status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            return manage.get_base_to_response().to_block_response(
                str(chat_id), str(chat_record_id), all_text, True, 0, 0, _status=fallback_status
            )
