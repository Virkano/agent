# coding=utf-8
"""
    @project: dianxin
    @project: dianxin
    @file： tokenizer_manage_config.py
    @date：2024/4/28 10:17
    @desc:
"""

import os
from pathlib import Path

from telecom_ai_agent.env import get_env


class MKTokenizer:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def encode(self, text):
        return self.tokenizer.encode(text).ids


class TokenizerManage:
    tokenizer = None

    @staticmethod
    def get_tokenizer():
        from tokenizers import Tokenizer
        if TokenizerManage.tokenizer is not None:
            return MKTokenizer(TokenizerManage.tokenizer)

        model_path = Path(
            get_env(
                "TELECOM_AI_TOKENIZER_MODEL_PATH",
                os.path.join("/opt/telecom_ai_agent-app", "model", "tokenizer", "models--bert-base-cased"),
            )
        )
        tokenizer_file = TokenizerManage._get_tokenizer_file(model_path)
        TokenizerManage.tokenizer = Tokenizer.from_file(str(tokenizer_file))
        return MKTokenizer(TokenizerManage.tokenizer)

    @staticmethod
    def _get_tokenizer_file(model_path: Path) -> Path:
        ref_path = model_path / "refs" / "main"
        if ref_path.exists():
            snapshot = ref_path.read_text(encoding="utf-8").strip()
            tokenizer_file = model_path / "snapshots" / snapshot / "tokenizer.json"
            if tokenizer_file.exists():
                return tokenizer_file

        tokenizer_file = model_path / "tokenizer.json"
        if tokenizer_file.exists():
            return tokenizer_file

        from huggingface_hub import hf_hub_download

        model_path.mkdir(parents=True, exist_ok=True)
        return Path(
            hf_hub_download(
                repo_id="bert-base-cased",
                filename="tokenizer.json",
                cache_dir=str(model_path.parent),
            )
        )
