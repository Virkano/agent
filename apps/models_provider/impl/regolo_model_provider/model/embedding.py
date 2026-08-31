# coding=utf-8
"""
    @project: dianxin
    @project: dianxin
    @file： embedding.py
    @date：2024/7/12 17:44
    @desc:
"""
from typing import Dict

from langchain_openai import OpenAIEmbeddings

from models_provider.base_model_provider import TelecomAIBaseModel


class RegoloEmbeddingModel(TelecomAIBaseModel, OpenAIEmbeddings):
    @staticmethod
    def new_instance(model_type, model_name, model_credential: Dict[str, object], **model_kwargs):
        return RegoloEmbeddingModel(
            api_key=model_credential.get('api_key'),
            model=model_name,
            openai_api_base=model_credential.get('api_base') or "https://api.regolo.ai/v1",
        )
