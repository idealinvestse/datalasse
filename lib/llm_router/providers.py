"""Providers: OpenAI-compat for OpenRouter and Groq + full mock support.

Reuses concepts from moss-router (providers.js) and groq_client.py (lazy openai, base_url).
MOCK=1 or INTERNAL_ROUTER_MOCK=1 : never touches net, zero cost.
"""
from __future__ import annotations

import os
import time
from typing import Any

MOCK_ENV = os.getenv("MOCK", "") == "1" or os.getenv("INTERNAL_ROUTER_MOCK", "") == "1"

def _is_mock() -> bool:
    return MOCK_ENV

_OPENAI_CLIENTS: dict[str, Any] = {}
_HAS_OPENAI = False

try:
    from openai import OpenAI
    _HAS_OPENAI = True
except Exception:
    OpenAI = None  # type: ignore
    _HAS_OPENAI = False

def get_openai_client(provider: str, cfg: dict[str, Any]) -> Any:
    """Return (cached per-provider) OpenAI client configured for provider."""
    if _is_mock() or not _HAS_OPENAI:
        return None
    if provider in _OPENAI_CLIENTS:
        return _OPENAI_CLIENTS[provider]
    pcfg = cfg.get("providers", {}).get(provider, {})
    base = pcfg.get("base_url")
    key_env = pcfg.get("api_key_env", "")
    api_key = os.getenv(key_env) or ("sk-mock" if _is_mock() else None)
    if not api_key and not _is_mock():
        api_key = "sk-mock"
    cli = OpenAI(api_key=api_key, base_url=base, timeout=60)
    _OPENAI_CLIENTS[provider] = cli
    return cli


def call_provider(
    provider: str,
    model: str,
    messages: list[dict[str, str]],
    max_tokens: int,
    cfg: dict[str, Any],
    extra_headers: dict | None = None,
    temperature: float = 0.2,
) -> dict[str, Any]:
    """Execute chat. Returns {'content': str, 'usage': dict, 'raw_model': , 'provider': , 'latency_ms': }"""
    start = time.time()
    if _is_mock():
        prompt_len = sum(len(m.get("content", "")) for m in messages)
        pt = max(5, prompt_len // 4)
        ct = max(3, pt // 3)
        content = f"[MOCK:{provider}/{model}] response for {messages[-1]['content'][:60]}..."
        return {
            "content": content,
            "usage": {"prompt_tokens": pt, "completion_tokens": ct},
            "raw_model": model,
            "provider": provider,
            "latency_ms": int((time.time() - start) * 1000),
        }

    # Strip openrouter/ prefix for OR (matches research-goal + plan)
    eff_model = model
    if provider == "openrouter" and model.startswith("openrouter/"):
        eff_model = model[len("openrouter/"):]

    client = get_openai_client(provider, cfg)
    if client is None:
        # fallback mock if no openai or no key in real
        return {
            "content": f"[FALLBACK-MOCK no-client] {provider}/{eff_model}",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            "raw_model": eff_model,
            "provider": provider,
            "latency_ms": 10,
        }

    pcfg = cfg.get("providers", {}).get(provider, {})
    headers = dict(pcfg.get("default_headers", {}))
    if extra_headers:
        headers.update(extra_headers)

    try:
        resp = client.chat.completions.create(
            model=eff_model,
            messages=messages,  # type: ignore
            max_tokens=max_tokens,
            temperature=temperature,
            extra_headers=headers or None,
        )
        choice = resp.choices[0]
        content = choice.message.content or ""
        usage = resp.usage
        u = {"prompt_tokens": getattr(usage, "prompt_tokens", 0), "completion_tokens": getattr(usage, "completion_tokens", 0)} if usage else {"prompt_tokens": 0, "completion_tokens": 0}
        return {
            "content": content,
            "usage": u,
            "raw_model": getattr(resp, "model", eff_model),
            "provider": provider,
            "latency_ms": int((time.time() - start) * 1000),
        }
    except Exception as e:
        # surface for escalation
        raise RuntimeError(f"provider {provider} model {eff_model} failed: {e}") from e
