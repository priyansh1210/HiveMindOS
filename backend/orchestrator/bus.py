"""MessageBus — the single channel through which every agent message flows.

Responsibilities:
  1. Persist each message to Supabase `messages` (source of truth).
  2. Push each message to the WebSocket broadcaster (live dashboard feed).
  3. Maintain a fast in-memory cache so executors can build per-agent inboxes
     without hitting the DB on every subtask.

Status transitions for agents/tasks are also routed through here so the
dashboard sees one coherent event stream.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from database.client import get_supabase
from routers.websocket import broadcaster


class MessageBus:
    def __init__(self) -> None:
        # Cache holds messages keyed by task_id (str) for inbox lookups.
        self._cache: dict[str, list[dict[str, Any]]] = {}

    # ------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------
    async def send(
        self,
        *,
        task_id: UUID | str,
        from_agent: str,
        to_agent: str,
        message_type: str,
        content: str,
        data: Optional[dict[str, Any]] = None,
        priority: str = "medium",
    ) -> dict[str, Any]:
        record = {
            "task_id": str(task_id),
            "from_agent": from_agent,
            "to_agent": to_agent,
            "message_type": message_type,
            "content": content,
            "data": data,
            "priority": priority,
        }

        stored = await self._persist(record)
        self._cache.setdefault(str(task_id), []).append(stored)

        await broadcaster.broadcast("message", stored)
        return stored

    async def _persist(self, record: dict[str, Any]) -> dict[str, Any]:
        client = get_supabase()
        if client is None:
            return {
                **record,
                "id": str(uuid4()),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        res = client.table("messages").insert(record).execute()
        return (res.data and res.data[0]) or record

    # ------------------------------------------------------------
    # Inbox lookup
    # ------------------------------------------------------------
    def inbox_for(
        self,
        *,
        task_id: UUID | str,
        agent_role: str,
    ) -> list[str]:
        """Return a list of rendered messages this agent should see for the task."""
        messages = self._cache.get(str(task_id), [])
        lines: list[str] = []
        for msg in messages:
            to = msg.get("to_agent")
            if to not in (agent_role, "all"):
                continue
            if msg.get("from_agent") == agent_role:
                continue
            sender = msg.get("from_agent", "unknown")
            content = msg.get("content", "")
            mtype = msg.get("message_type", "info")
            lines.append(f"[{mtype}] {sender} → {to}: {content}")
        return lines

    def messages_for_task(self, task_id: UUID | str) -> list[dict[str, Any]]:
        return list(self._cache.get(str(task_id), []))

    # ------------------------------------------------------------
    # Status broadcasts (tasks + agents)
    # ------------------------------------------------------------
    async def update_task_status(
        self,
        *,
        task_id: UUID | str,
        status: str,
        plan: Optional[dict[str, Any]] = None,
        result: Optional[dict[str, Any]] = None,
        completed: bool = False,
    ) -> None:
        client = get_supabase()
        payload: dict[str, Any] = {"status": status}
        if plan is not None:
            payload["plan"] = plan
        if result is not None:
            payload["result"] = result
        if completed:
            payload["completed_at"] = datetime.now(timezone.utc).isoformat()

        if client is not None:
            client.table("tasks").update(payload).eq("id", str(task_id)).execute()

        await broadcaster.broadcast(
            "task_status",
            {"task_id": str(task_id), **payload},
        )

    async def update_agent_status(
        self,
        *,
        agent_role: str,
        status: str,
        company_id: Optional[UUID | str] = None,
    ) -> None:
        client = get_supabase()
        if client is not None:
            query = client.table("agents").update({"status": status}).eq("role", agent_role)
            if company_id is not None:
                query = query.eq("company_id", str(company_id))
            query.execute()

        await broadcaster.broadcast(
            "agent_status",
            {"role": agent_role, "status": status},
        )


_bus: Optional[MessageBus] = None


def get_bus() -> MessageBus:
    global _bus
    if _bus is None:
        _bus = MessageBus()
    return _bus
