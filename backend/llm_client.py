"""LLM client abstraction — routes requests across Gemini Pro, Gemini Flash, and Groq.

Roles:
    "orchestrator" → Gemini 2.5 Pro (smartest, 25 req/day free tier)
    "agent"        → Gemini 2.5 Flash (fast, 500 req/day free tier)
    "fallback"     → Groq Llama 3.3 70B (very fast, ~14k req/day)

On Gemini quota/rate errors, callers can request role="fallback" to retry on Groq.
"""

from __future__ import annotations

import asyncio
from typing import Literal, Optional

import google.generativeai as genai
from groq import AsyncGroq

from config import get_settings


Role = Literal["orchestrator", "agent", "fallback"]


_gemini_lock = asyncio.Lock()


def _gemini_keys() -> list[str]:
    settings = get_settings()
    keys = [k for k in (settings.gemini_api_key, settings.gemini_api_key_2) if k]
    if not keys:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Get one free at https://aistudio.google.com/apikey"
        )
    return keys


_groq_client: Optional[AsyncGroq] = None


def _get_groq_client() -> AsyncGroq:
    global _groq_client
    if _groq_client is not None:
        return _groq_client
    settings = get_settings()
    if not settings.groq_api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Get one free at https://console.groq.com"
        )
    # max_retries=1 so we fail fast on rate limits instead of silently retrying
    # for minutes inside the SDK.
    _groq_client = AsyncGroq(api_key=settings.groq_api_key, max_retries=1)
    return _groq_client


DEFAULT_TIMEOUT_SECS = 45


async def call_llm(
    prompt: str,
    system_prompt: str = "",
    role: Role = "agent",
    *,
    temperature: float = 0.7,
    max_tokens: int = 1024,
    json_mode: bool = False,
    timeout: float = DEFAULT_TIMEOUT_SECS,
) -> str:
    """Single-shot LLM call. Returns the model's text response."""
    settings = get_settings()

    async def _gemini(api_key: str):
        model_name = (
            settings.gemini_orchestrator_model
            if role == "orchestrator"
            else settings.gemini_agent_model
        )
        return await _call_gemini(
            prompt=prompt,
            system_prompt=system_prompt,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
            api_key=api_key,
        )

    async def _groq():
        return await _call_groq(
            prompt=prompt,
            system_prompt=system_prompt,
            model=settings.groq_fallback_model,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
        )

    if role == "fallback":
        return await asyncio.wait_for(_groq(), timeout=timeout)

    # Try each configured Gemini key in turn, then fall back to Groq.
    last_gemini_exc: Optional[Exception] = None
    for key in _gemini_keys():
        try:
            return await asyncio.wait_for(_gemini(key), timeout=timeout)
        except Exception as exc:
            last_gemini_exc = exc
            print(
                f"[llm_client] Gemini key …{key[-6:]} ({role}) failed: "
                f"{type(exc).__name__}: {str(exc)[:180]}",
                flush=True,
            )
            continue

    if settings.groq_api_key:
        try:
            return await asyncio.wait_for(_groq(), timeout=timeout)
        except Exception as groq_exc:
            raise RuntimeError(
                f"All providers failed. Last Gemini: "
                f"{type(last_gemini_exc).__name__}: {last_gemini_exc}. "
                f"Groq: {type(groq_exc).__name__}: {groq_exc}"
            ) from groq_exc
    raise last_gemini_exc  # type: ignore[misc]


async def _call_gemini(
    *,
    prompt: str,
    system_prompt: str,
    model_name: str,
    temperature: float,
    max_tokens: int,
    json_mode: bool,
    api_key: str,
) -> str:
    generation_config: dict = {
        "temperature": temperature,
        "max_output_tokens": max_tokens,
    }
    if json_mode:
        generation_config["response_mime_type"] = "application/json"

    # The Gemini SDK uses module-level config, so we must serialize calls to
    # avoid one async task swapping keys mid-flight for another.
    async with _gemini_lock:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name,
            system_instruction=system_prompt or None,
            generation_config=generation_config,
        )
        response = await asyncio.to_thread(model.generate_content, prompt)
    return (response.text or "").strip()


async def _call_groq(
    *,
    prompt: str,
    system_prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
    json_mode: bool,
) -> str:
    client = _get_groq_client()
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    kwargs: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = await client.chat.completions.create(**kwargs)
    return (response.choices[0].message.content or "").strip()
