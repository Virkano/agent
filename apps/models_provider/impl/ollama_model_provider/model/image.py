from typing import Dict
from models_provider.base_model_provider import TelecomAIBaseModel
from models_provider.impl.base_chat_open_ai import BaseChatOpenAI
from models_provider.impl.ollama_model_provider.endpoint import resolve_ollama_base_url


class OllamaImage(TelecomAIBaseModel, BaseChatOpenAI):

    @staticmethod
    def is_cache_model():
        return False

    @staticmethod
    def new_instance(model_type, model_name, model_credential: Dict[str, object], **model_kwargs):
        base_url = resolve_ollama_base_url(model_credential.get('api_base', ''))
        base_url = base_url if base_url.endswith('/v1') else (base_url + '/v1')
        optional_params = TelecomAIBaseModel.filter_optional_params(model_kwargs)
        return OllamaImage(
            model_name=model_name,
            openai_api_base=base_url,
            openai_api_key=model_credential.get('api_key'),
            # stream_options={"include_usage": True},
            streaming=True,
            stream_usage=True,
            **optional_params,
        )
