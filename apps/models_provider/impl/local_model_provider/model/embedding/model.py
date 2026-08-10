# coding=utf-8
"""
    @project: MaxKB
    @Author：虎虎
    @file： model.py
    @date：2025/11/5 15:26
    @desc:
"""
import hashlib
import math
from typing import Dict, List

from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings

from common.utils.logger import maxkb_logger
from models_provider.base_model_provider import MaxKBBaseModel

max_retries = 3
LOCAL_HASH_EMBEDDING_MODEL = "maxkb-local-hash-embedding"


class LocalHashEmbedding(MaxKBBaseModel, Embeddings):
    dimension = 384

    @staticmethod
    def new_instance(model_type, model_name, model_credential: Dict[str, object], **model_kwargs):
        return LocalHashEmbedding()

    def _embed(self, text: str) -> List[float]:
        text = text or ""
        tokens = [text[index:index + 2] for index in range(max(len(text) - 1, 1))]
        vector = [0.0] * self.dimension

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(text) for text in texts]


class LocalEmbedding(MaxKBBaseModel, HuggingFaceEmbeddings):
    @staticmethod
    def is_cache_model():
        return True

    @staticmethod
    def new_instance(model_type, model_name, model_credential: Dict[str, object], **model_kwargs):
        if model_name == LOCAL_HASH_EMBEDDING_MODEL:
            return LocalHashEmbedding()

        for attempt in range(max_retries):
            try:
                embedding = LocalEmbedding(model_name=model_name, cache_folder=model_credential.get('cache_folder'),
                                           model_kwargs={'device': model_credential.get('device')},
                                           encode_kwargs={'normalize_embeddings': True}
                                           )
                # 测试一下是否真的能用
                embedding.embed_query("test")
                return embedding
            except Exception as e:
                if 'meta tensor' in str(e).lower() and attempt < max_retries - 1:
                    maxkb_logger.warning(
                        f"Test failed with meta tensor error, retrying... (attempt {attempt + 1}/{max_retries})")
                    import time
                    time.sleep(1)
                    continue
                raise e
