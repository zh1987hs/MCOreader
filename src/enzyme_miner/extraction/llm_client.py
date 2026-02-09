import json
import logging
import os
import time
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
    max_retries: int = 2
    retry_backoff_s: float = 2.0
    api_key: str | None = None
    api_base: str | None = None
    api_key_header: str = "Authorization"
    api_key_prefix: str = "Bearer"
    response_json_path: str | None = None
    response_format: str | None = None


def call_openai(prompt: str, config: LLMConfig) -> str:
    model = _normalize_model(config.model)
    if not model:
        raise RuntimeError("LLM model name is empty after normalization.")
    api_key = config.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    api_base = config.api_base or "https://api.openai.com/v1"
    payload = {
        "model": model,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "messages": [
            {"role": "system", "content": "You are a precise information extraction system."},
            {"role": "user", "content": prompt},
        ],
    }
    if config.response_format:
        payload["response_format"] = {"type": config.response_format}
    headers = {config.api_key_header: f"{config.api_key_prefix} {api_key}", "Content-Type": "application/json"}
    url = f"{api_base}/chat/completions"
    last_error: Exception | None = None
    for attempt in range(config.max_retries + 1):
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
            if response.status_code in {429, 500, 502, 503, 504} and attempt < config.max_retries:
                _sleep_before_retry(attempt, response.status_code, config.retry_backoff_s)
                continue
            response.raise_for_status()
            data = response.json()
            content = _safe_extract_content(data, response.text)
            if config.response_json_path:
                return _safe_extract_json_path(data, config.response_json_path, content)
            return content
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            last_error = exc
            if attempt < config.max_retries:
                _sleep_before_retry(attempt, "network_error", config.retry_backoff_s)
                continue
            raise
        except json.JSONDecodeError as exc:
            last_error = exc
            if attempt < config.max_retries:
                _sleep_before_retry(attempt, "invalid_json", config.retry_backoff_s)
                continue
            raise
        except requests.HTTPError as exc:
            last_error = exc
            raise
    if last_error:
        raise last_error
    raise RuntimeError("LLM request failed with no response.")


def _normalize_model(model: str) -> str:
    normalized = model.strip()
    if normalized.endswith(":"):
        normalized = normalized.rstrip(":").strip()
    if normalized != model:
        LOGGER.warning("Normalized LLM model name from %r to %r.", model, normalized)
    return normalized


def _sleep_before_retry(attempt: int, reason: object, base_delay: float) -> None:
    delay = base_delay * (2**attempt)
    LOGGER.warning("Retrying LLM request after %.1fs due to %s.", delay, reason)
    time.sleep(delay)


def _safe_extract_content(data: dict[str, Any], fallback: str) -> str:
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        LOGGER.warning("Failed to extract message content from LLM response: %s", exc)
    return fallback


def _safe_extract_json_path(data: dict[str, Any], path: str, fallback: str) -> str:
    try:
        return _extract_json_path(data, path)
    except (KeyError, IndexError, TypeError) as exc:
        LOGGER.warning("Failed to extract response_json_path %r: %s", path, exc)
        return fallback


def _extract_json_path(data: dict[str, Any], path: str) -> str:
    current: Any = data
    for part in path.split("."):
        if part.isdigit():
            current = current[int(part)]
        else:
            current = current[part]
    if isinstance(current, (dict, list)):
        return json.dumps(current, ensure_ascii=False)
    return str(current)


def call_llm(prompt: str, config: LLMConfig) -> str:
    provider = config.provider.lower()
    if provider in {"openai", "openai_compatible"}:
        return call_openai(prompt, config)
    raise ValueError(f"Unsupported provider: {config.provider}")
