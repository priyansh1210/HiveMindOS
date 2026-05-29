"""Run the three blueprint demo scenarios sequentially and dump their flows.

Usage (from backend/, venv active):
    python scripts/run_demo_scenarios.py
"""

import asyncio
import json
import time
import urllib.request
from typing import Any


SCENARIOS = [
    (
        "marketing",
        "Launch a summer marketing campaign for our new product, budget under $20K",
    ),
    (
        "onboarding",
        "Onboard Priya as a senior frontend engineer starting next Monday",
    ),
    (
        "escalation",
        "Handle an angry enterprise customer threatening to churn over a 3-day outage",
    ),
]


def post_task(prompt: str) -> dict[str, Any]:
    req = urllib.request.Request(
        "http://localhost:8000/api/tasks",
        data=json.dumps({"prompt": prompt}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def get_task(task_id: str) -> dict[str, Any]:
    with urllib.request.urlopen(f"http://localhost:8000/api/tasks/{task_id}") as r:
        return json.loads(r.read())


def get_messages(task_id: str) -> list[dict[str, Any]]:
    with urllib.request.urlopen(
        f"http://localhost:8000/api/messages?task_id={task_id}"
    ) as r:
        return json.loads(r.read())


async def run_one(name: str, prompt: str) -> dict[str, Any]:
    print(f"\n=== Scenario: {name} ===")
    print(f"  prompt: {prompt}")
    started = time.time()
    task = post_task(prompt)
    tid = task["id"]
    print(f"  task id: {tid}")

    # Poll until completed/failed (max 6 min)
    for _ in range(120):
        await asyncio.sleep(3)
        t = get_task(tid)
        status = t.get("status")
        if status in ("completed", "failed"):
            elapsed = time.time() - started
            print(f"  status: {status} after {elapsed:.1f}s")
            msgs = get_messages(tid)
            msgs = sorted(msgs, key=lambda m: m["created_at"])
            print(f"  messages: {len(msgs)}")
            roles = sorted({m["from_agent"] for m in msgs if m["from_agent"] not in ("user", "orchestrator")})
            print(f"  agents involved: {roles}")
            plan = t.get("plan") or {}
            subtasks = plan.get("subtasks", []) if isinstance(plan, dict) else []
            print(f"  subtasks planned: {len(subtasks)}")
            return {
                "name": name,
                "task_id": tid,
                "status": status,
                "elapsed_s": elapsed,
                "title": t.get("title"),
                "messages": msgs,
                "subtask_count": len(subtasks),
                "agents_involved": roles,
                "summary": (t.get("result") or {}).get("summary", "") if isinstance(t.get("result"), dict) else "",
                "error": (t.get("result") or {}).get("error") if isinstance(t.get("result"), dict) else None,
            }
    return {"name": name, "task_id": tid, "status": "timeout"}


async def main():
    results = []
    for name, prompt in SCENARIOS:
        r = await run_one(name, prompt)
        results.append(r)
        # Cooldown so we don't slam Gemini TPM limits between runs.
        await asyncio.sleep(5)

    out_path = "scripts/demo_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
