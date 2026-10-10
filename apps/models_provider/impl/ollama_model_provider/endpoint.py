"""Resolve the Ollama endpoint for host/container deployment."""

import os
from urllib.parse import ParseResult, urlparse


def resolve_ollama_base_url(configured_url: str) -> str:
    url = os.getenv("JB_OLLAMA_BASE_URL") or os.getenv("TELECOM_AI_OLLAMA_BASE_URL") or configured_url
    parsed = urlparse(url)
    result = ParseResult(
        scheme=parsed.scheme,
        netloc=parsed.netloc,
        path=parsed.path,
        params="",
        query="",
        fragment="",
    ).geturl()
    return result[:-1] if result.endswith("/") else result
