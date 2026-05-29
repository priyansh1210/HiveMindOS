from collections import defaultdict
from uuid import UUID

from fastapi import APIRouter, HTTPException

from database.client import get_supabase
from database.models import TaskMetrics

router = APIRouter()


@router.get("/tasks", response_model=TaskMetrics)
async def task_metrics(company_id: UUID | None = None):
    client = get_supabase()
    if client is None:
        raise HTTPException(503, "Supabase not configured")
    query = client.table("tasks").select("status")
    if company_id is not None:
        query = query.eq("company_id", str(company_id))
    rows = (query.execute().data) or []

    counts = {"pending": 0, "planning": 0, "in_progress": 0, "completed": 0, "failed": 0}
    for row in rows:
        status = row.get("status")
        if status in counts:
            counts[status] += 1

    total = len(rows)
    completed = counts["completed"]
    completion_rate = (completed / total) if total else 0.0

    return TaskMetrics(
        total_tasks=total,
        pending=counts["pending"] + counts["planning"],
        in_progress=counts["in_progress"],
        completed=completed,
        failed=counts["failed"],
        completion_rate=completion_rate,
    )


@router.get("/agents")
async def agent_metrics(company_id: UUID | None = None):
    """Per-agent stats derived from the messages table.

    Activity_log isn't currently populated by the orchestrator, so we surface
    what we have: messages sent (outbound) and distinct tasks the agent touched.
    """
    client = get_supabase()
    if client is None:
        raise HTTPException(503, "Supabase not configured")

    agents_q = client.table("agents").select("id,name,role,color")
    if company_id is not None:
        agents_q = agents_q.eq("company_id", str(company_id))
    agents_rows = (agents_q.execute().data) or []

    msgs_rows = (
        client.table("messages")
        .select("from_agent,task_id")
        .execute()
        .data
    ) or []

    sent: dict[str, int] = defaultdict(int)
    tasks_touched: dict[str, set[str]] = defaultdict(set)
    for m in msgs_rows:
        role = m.get("from_agent")
        if not role:
            continue
        sent[role] += 1
        tid = m.get("task_id")
        if tid:
            tasks_touched[role].add(str(tid))

    out = []
    for a in agents_rows:
        role = a.get("role")
        out.append(
            {
                "agent_id": a.get("id"),
                "agent_name": a.get("name"),
                "role": role,
                "color": a.get("color"),
                "messages_sent": sent.get(role, 0),
                "tasks_touched": len(tasks_touched.get(role, set())),
            }
        )

    out.sort(key=lambda r: r["messages_sent"], reverse=True)
    return out


@router.get("/activity")
async def recent_activity(limit: int = 50):
    client = get_supabase()
    if client is None:
        raise HTTPException(503, "Supabase not configured")
    res = (
        client.table("activity_log")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []
