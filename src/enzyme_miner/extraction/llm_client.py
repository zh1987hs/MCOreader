import json
import logging
import os
from dataclasses import dataclass
from typing import Any

import requests

LOGGER = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    provider: str
    model: str
    temperature: float = 0.0
    max_tokens: int = 1200
    api_key: str | None = None
    api_base: str | None = None
    api_key_header: str = "Authorization"
    api_key_prefix: str = "Bearer"


def call_openai(prompt: str, config: LLMConfig) -> str:
    api_key = config.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    api_base = config.api_base or "https://api.openai.com/v1"
    payload = {
        "model": config.model,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "messages": [
            {"role": "system", "content": "You are a precise information extraction system."},
            {"role": "user", "content": prompt},
        ],
    }
    headers = {config.api_key_header: f"{config.api_key_prefix} {api_key}", "Content-Type": "application/json"}
    response = requests.post(f"{api_base}/chat/completions", headers=headers, data=json.dumps(payload), timeout=60)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def call_llm(prompt: str, config: LLMConfig) -> str:
    provider = config.provider.lower()
    if provider in {"openai", "openai_compatible"}:
        return call_openai(prompt, config)
    raise ValueError(f"Unsupported provider: {config.provider}")
