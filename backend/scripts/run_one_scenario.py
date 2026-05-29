"""Run a single demo scenario by name. Use after Gemini RPM has cooled off.

Usage:
    python scripts/run_one_scenario.py onboarding
"""

import asyncio
import json
import sys
import time
import urllib.request


PROMPTS = {
    "marketing": "Launch a summer marketing campaign for our new product, budget under $20K",
    "onboarding": "Onboard Priya as a senior frontend engineer starting next Monday",
    "escalation": "Handle an angry enterprise customer threatening to churn over a 3-day outage",
}


def post(prompt: str):
    req = urllib.request.Request(
        "http://localhost:8000/api/tasks",
        data=json.dumps({"prompt": prompt}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def get(tid):
    with urllib.request.urlopen(f"http://localhost:8000/api/tasks/{tid}") as r:
        return json.loads(r.read())


def msgs(tid):
    with urllib.request.urlopen(
        f"http://localhost:8000/api/messages?task_id={tid}"
    ) as r:
        return json.loads(r.read())


async def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "onboarding"
    prompt = PROMPTS[name]
    print(f"Scenario: {name}\nPrompt: {prompt}\n")
    t0 = time.time()
    task = post(prompt)
    tid = task["id"]
    print(f"task id: {tid}")
    for _ in range(150):
        await asyncio.sleep(2)
        t = get(tid)
        if t["status"] in ("completed", "failed"):
            break
    elapsed = time.time() - t0
    ms = sorted(msgs(tid), key=lambda m: m["created_at"])
    roles = sorted({m["from_agent"] for m in ms if m["from_agent"] not in ("user", "orchestrator")})
    print(f"\nstatus: {t['status']}  elapsed: {elapsed:.1f}s")
    print(f"messages: {len(ms)}  agents involved: {roles}")
    summary = (t.get("result") or {}).get("summary", "")
    print(f"\nsummary head:\n{summary[:600]}\n")
    print("--- messages ---")
    for m in ms:
        print(f"  {m['from_agent']} -> {m['to_agent']} [{m['message_type']}]: {(m.get('content') or '')[:150]}")


if __name__ == "__main__":
    asyncio.run(main())
