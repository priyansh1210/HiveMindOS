"""Planner — decompose a user request into a typed multi-agent plan.

Uses Gemini 2.5 Pro (orchestrator role) in JSON mode for structured output.
Falls back gracefully if the model returns malformed JSON.
"""

from __future__ import annotations

import json
import re
from typing import Optional

from database.models import SubTask, TaskPlan
from llm_client import call_llm


PLANNER_SYSTEM_PROMPT = """Decompose a business request into 3-5 subtasks for specialist agents.

AGENTS: hr, sales, finance, support, ops

Output ONLY this JSON shape (no prose, no markdown):
{
  "task_title": "Short title",
  "subtasks": [
    {"id": 1, "description": "Direct instruction to the agent", "assigned_to": "sales",
     "depends_on": [], "priority": "high"}
  ],
  "execution_order": "mixed"
}

Rules: ids unique, priorities low|medium|high|urgent, depends_on lists prior ids only when output is actually needed.
"""


JSON_BLOCK_PATTERN = re.compile(r"\{.*\}", re.DOTALL)


class PlannerError(RuntimeError):
    pass


class Planner:
    async def plan(self, user_request: str) -> TaskPlan:
        # Use Flash (agent tier) by default — 500 req/day vs Pro's 25/day, and
        # JSON-mode plan quality is more than sufficient for our schema.
        raw = await call_llm(
            prompt=f"USER REQUEST:\n{user_request}",
            system_prompt=PLANNER_SYSTEM_PROMPT,
            role="agent",
            temperature=0.4,
            max_tokens=700,
            json_mode=True,
        )

        plan = _try_parse_plan(raw)
        if plan is not None:
            return plan

        # One retry: ask the model to fix its own output as strict JSON.
        repair_prompt = (
            "Your previous output could not be parsed as JSON. Reissue it as "
            "strict JSON matching the required schema. Do not include "
            "markdown fencing.\n\nPREVIOUS OUTPUT:\n" + raw
        )
        raw2 = await call_llm(
            prompt=repair_prompt,
            system_prompt=PLANNER_SYSTEM_PROMPT,
            role="agent",
            temperature=0.2,
            max_tokens=700,
            json_mode=True,
        )
        plan = _try_parse_plan(raw2)
        if plan is not None:
            return plan

        raise PlannerError(f"Planner failed to produce valid JSON. Last output:\n{raw2}")


def _try_parse_plan(raw: str) -> Optional[TaskPlan]:
    text = raw.strip()
    if not text:
        return None

    # JSON-mode normally returns clean JSON, but be defensive.
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = JSON_BLOCK_PATTERN.search(text)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

    try:
        subtasks = [SubTask(**s) for s in data.get("subtasks", [])]
        if not subtasks:
            return None
        return TaskPlan(
            task_title=data.get("task_title", "Untitled task"),
            subtasks=subtasks,
            execution_order=data.get("execution_order", "mixed"),
        )
    except Exception:  # noqa: BLE001
        return None
