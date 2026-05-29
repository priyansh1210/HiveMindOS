"""Quick 'can I demo right now?' probe. Run from backend/ with venv active.

Two green checks = safe to run live. Any red = use Flow B (pre-cached TaskDetail).
"""

import asyncio
from llm_client import call_llm


async def probe(role: str, label: str) -> None:
    try:
        r = await call_llm(
            "Reply with the single word OK.",
            "Be terse.",
            role=role,
            max_tokens=8,
            timeout=15,
        )
        print(f"  {label}: OK  ({r[:30]})")
    except Exception as e:
        print(f"  {label}: FAIL  {type(e).__name__}: {str(e)[:140]}")


async def main():
    print("Quota probe (do not run during a live demo!):")
    await probe("agent", "Gemini Flash")
    await probe("fallback", "Groq Llama 3.3 70B")


if __name__ == "__main__":
    asyncio.run(main())
