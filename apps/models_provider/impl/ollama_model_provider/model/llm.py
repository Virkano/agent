# coding=utf-8
"""
    @project: dianxin
    @project: dianxin
    @file： llm.py
    @date：2024/3/6 11:48
    @desc:
"""
from typing import List, Dict
from langchain_core.messages import BaseMessage, get_buffer_string
from langchain_ollama.chat_models import ChatOllama


from common.config.tokenizer_manage_config import TokenizerManage
from models_provider.base_model_provider import TelecomAIBaseModel
from models_provider.impl.ollama_model_provider.endpoint import resolve_ollama_base_url


class OllamaChatModel(TelecomAIBaseModel, ChatOllama):
    @staticmethod
    def is_cache_model():
        return False

    @staticmethod
    def new_instance(model_type, model_name, model_credential: Dict[str, object], **model_kwargs):
        base_url = resolve_ollama_base_url(model_credential.get('api_base', ''))
        optional_params = TelecomAIBaseModel.filter_optional_params(model_kwargs)

        return OllamaChatModel(model=model_name, base_url=base_url,
                               stream=True, **optional_params)

    def get_num_tokens_from_messages(self, messages: List[BaseMessage]) -> int:
        tokenizer = TokenizerManage.get_tokenizer()
        return sum([len(tokenizer.encode(get_buffer_string([m]))) for m in messages])

    def get_num_tokens(self, text: str) -> int:
        tokenizer = TokenizerManage.get_tokenizer()
        return len(tokenizer.encode(text))
