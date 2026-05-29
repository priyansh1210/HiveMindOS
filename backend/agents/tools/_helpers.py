"""Shared helper for LLM-backed "fake" tools.

Per the hackathon blueprint, most tools just generate realistic-looking output
via an LLM call rather than hitting real APIs. This helper standardizes that
so each tool stays a 3-line wrapper.
"""

from __future__ import annotations

from typing import Any

from llm_client import call_llm


async def llm_tool(
    system: str,
    user: str,
    *,
    max_tokens: int = 600,
    temperature: float = 0.7,
) -> dict[str, Any]:
    """Run a focused LLM call and wrap the text in a result envelope."""
    text = await call_llm(
        prompt=user,
        system_prompt=system,
        role="agent",
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return {"result": text}
