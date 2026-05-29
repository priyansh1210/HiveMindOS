"""Orchestrator — plan + execute a user task end-to-end.

Flow:
  1. Planner decomposes the user prompt into typed subtasks.
  2. Engine executes subtasks respecting `depends_on`, in parallel when possible.
  3. When an agent emits `→ @other_role: ...` mentions, those become new
     dynamically-spawned subtasks routed to that role.
  4. Every agent invocation produces a `response` message on the bus, and every
     mention produces a `request` message. Both persist to Supabase and stream
     to the WebSocket broadcaster.

Hard caps prevent runaway delegation: MAX_SUBTASKS and MAX_ROUNDS.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

from agents.registry import get_registry
from database.models import SubTask, TaskPlan

from .bus import MessageBus, get_bus
from .planner import Planner, PlannerError


MAX_SUBTASKS = 10
MAX_ROUNDS = 6
MAX_DYNAMIC_PER_AGENT = 2  # how many mentions one source agent may spawn in a task


@dataclass
class SubtaskResult:
    subtask_id: int
    assigned_to: str
    description: str
    response: str
    tool_calls: list[dict] = field(default_factory=list)
    duration_ms: int = 0
    error: Optional[str] = None


@dataclass
class TaskExecutionResult:
    task_title: str
    plan: TaskPlan
    subtask_results: list[SubtaskResult] = field(default_factory=list)
    final_summary: str = ""
    error: Optional[str] = None


class Orchestrator:
    def __init__(self, bus: Optional[MessageBus] = None) -> None:
        self.bus = bus or get_bus()
        self.planner = Planner()
        self.registry = get_registry()

    # ----------------------------------------------------------------
    # Public entry point
    # ----------------------------------------------------------------
    async def run(
        self,
        *,
        task_id: UUID,
        user_request: str,
        company_id: Optional[UUID] = None,
    ) -> TaskExecutionResult:
        # Fresh state per task — don't leak memory from prior runs.
        for agent in self.registry.all().values():
            agent.reset()

        # Surface the user request itself on the bus so the dashboard shows it.
        await self.bus.send(
            task_id=task_id,
            from_agent="user",
            to_agent="orchestrator",
            message_type="user",
            content=user_request,
            priority="high",
        )

        # --- Planning phase ---
        await self.bus.update_task_status(task_id=task_id, status="planning")
        try:
            plan = await self.planner.plan(user_request)
        except Exception as exc:  # noqa: BLE001 — planner must never hang the task
            err = f"{type(exc).__name__}: {exc}"
            await self.bus.send(
                task_id=task_id,
                from_agent="orchestrator",
                to_agent="user",
                message_type="info",
                content=f"Planning failed: {err}",
                priority="urgent",
            )
            await self.bus.update_task_status(
                task_id=task_id,
                status="failed",
                result={"error": err},
                completed=True,
            )
            return TaskExecutionResult(
                task_title="Planning failed",
                plan=TaskPlan(task_title="failed", subtasks=[]),
                error=err,
            )

        await self.bus.send(
            task_id=task_id,
            from_agent="orchestrator",
            to_agent="all",
            message_type="broadcast",
            content=f"Planned {len(plan.subtasks)} subtasks for: {plan.task_title}",
            data={"plan": plan.model_dump()},
        )
        await self.bus.update_task_status(
            task_id=task_id, status="in_progress", plan=plan.model_dump()
        )

        # --- Execution phase ---
        execution = TaskExecutionResult(task_title=plan.task_title, plan=plan)
        queue: list[SubTask] = list(plan.subtasks)
        completed: dict[int, SubtaskResult] = {}
        next_id = max((s.id for s in queue), default=0) + 1
        rounds = 0

        # Dedupe + caps to prevent agents pinging each other in circles.
        spawned_by: dict[str, int] = {}
        routed_keys: set[tuple[str, str, str]] = set()

        while queue and rounds < MAX_ROUNDS:
            rounds += 1
            ready = [
                s for s in queue
                if all(dep in completed for dep in s.depends_on)
            ]
            if not ready:
                # Cyclic / unsatisfiable dependency — abort gracefully.
                execution.error = "Dependency deadlock; some subtasks were skipped."
                break

            # Remove the ready ones from the queue before running.
            for s in ready:
                queue.remove(s)

            # Run independent ready subtasks concurrently.
            results = await asyncio.gather(
                *(self._run_subtask(task_id=task_id, subtask=s, company_id=company_id) for s in ready),
                return_exceptions=False,
            )

            for subtask, result in zip(ready, results):
                completed[subtask.id] = result
                execution.subtask_results.append(result)

                # Handle dynamic delegation — mentions become new subtasks.
                agent = self.registry.get(subtask.assigned_to)
                if agent is None:
                    continue

                last_run = getattr(agent, "_last_run", None)
                if not last_run:
                    continue

                for mention in last_run.mentions:
                    if len(completed) + len(queue) >= MAX_SUBTASKS:
                        break
                    if self.registry.get(mention.to_agent) is None:
                        continue
                    if spawned_by.get(subtask.assigned_to, 0) >= MAX_DYNAMIC_PER_AGENT:
                        continue
                    # Dedupe near-identical asks (same source/target/topic).
                    topic_key = mention.content.lower().strip()[:60]
                    key = (subtask.assigned_to, mention.to_agent, topic_key)
                    if key in routed_keys:
                        continue
                    routed_keys.add(key)
                    spawned_by[subtask.assigned_to] = spawned_by.get(subtask.assigned_to, 0) + 1

                    await self.bus.send(
                        task_id=task_id,
                        from_agent=subtask.assigned_to,
                        to_agent=mention.to_agent,
                        message_type="request",
                        content=mention.content,
                    )
                    queue.append(
                        SubTask(
                            id=next_id,
                            description=mention.content,
                            assigned_to=mention.to_agent,
                            depends_on=[],
                            priority="medium",
                        )
                    )
                    next_id += 1

        # --- Summary phase ---
        summary = self._build_summary(execution)
        execution.final_summary = summary

        await self.bus.send(
            task_id=task_id,
            from_agent="orchestrator",
            to_agent="user",
            message_type="response",
            content=summary,
            data={"subtask_count": len(execution.subtask_results)},
            priority="high",
        )

        await self.bus.update_task_status(
            task_id=task_id,
            status="failed" if execution.error else "completed",
            result={
                "task_title": execution.task_title,
                "summary": summary,
                "subtask_count": len(execution.subtask_results),
                "error": execution.error,
            },
            completed=True,
        )

        return execution

    # ----------------------------------------------------------------
    # Subtask execution
    # ----------------------------------------------------------------
    async def _run_subtask(
        self,
        *,
        task_id: UUID,
        subtask: SubTask,
        company_id: Optional[UUID] = None,
    ) -> SubtaskResult:
        agent = self.registry.get(subtask.assigned_to)
        if agent is None:
            await self.bus.send(
                task_id=task_id,
                from_agent="orchestrator",
                to_agent="user",
                message_type="info",
                content=f"Unknown agent role '{subtask.assigned_to}' — skipping subtask.",
                priority="high",
            )
            return SubtaskResult(
                subtask_id=subtask.id,
                assigned_to=subtask.assigned_to,
                description=subtask.description,
                response="",
                error=f"Unknown agent role: {subtask.assigned_to}",
            )

        await self.bus.update_agent_status(
            agent_role=subtask.assigned_to, status="working", company_id=company_id
        )

        inbox = self.bus.inbox_for(task_id=task_id, agent_role=subtask.assigned_to)
        try:
            run = await agent.run(subtask.description, inbox=inbox)
        except Exception as exc:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            await self.bus.update_agent_status(
                agent_role=subtask.assigned_to, status="idle", company_id=company_id
            )
            return SubtaskResult(
                subtask_id=subtask.id,
                assigned_to=subtask.assigned_to,
                description=subtask.description,
                response="",
                error=f"{type(exc).__name__}: {exc}",
            )

        # Stash the latest run on the agent so the engine can pull mentions
        # without re-parsing. This is fine because subtasks per agent are
        # serialized inside one task run (we await each in order).
        agent._last_run = run  # type: ignore[attr-defined]

        await self.bus.send(
            task_id=task_id,
            from_agent=subtask.assigned_to,
            to_agent="all",
            message_type="response",
            content=run.response,
            data={
                "subtask_id": subtask.id,
                "tools": [tc.name for tc in run.tool_calls],
            },
        )

        await self.bus.update_agent_status(
            agent_role=subtask.assigned_to, status="idle", company_id=company_id
        )

        return SubtaskResult(
            subtask_id=subtask.id,
            assigned_to=subtask.assigned_to,
            description=subtask.description,
            response=run.response,
            tool_calls=[
                {"name": tc.name, "args": tc.args, "error": tc.error}
                for tc in run.tool_calls
            ],
            duration_ms=run.total_duration_ms,
        )

    # ----------------------------------------------------------------
    # Summary
    # ----------------------------------------------------------------
    @staticmethod
    def _build_summary(execution: TaskExecutionResult) -> str:
        lines = [f"Completed: {execution.task_title}"]
        for r in execution.subtask_results:
            status = "OK" if not r.error else "FAIL"
            tools_used = ", ".join(tc["name"] for tc in r.tool_calls) or "none"
            lines.append(
                f"  {status} [{r.assigned_to}] {r.description.strip()[:80]}"
                f"  (tools: {tools_used})"
            )
            if r.error:
                lines.append(f"       ERROR: {r.error}")
        if execution.error:
            lines.append(f"\nNotes: {execution.error}")
        return "\n".join(lines)


_orchestrator: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator
