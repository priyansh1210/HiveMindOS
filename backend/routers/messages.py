from uuid import UUID

from fastapi import APIRouter, HTTPException

from database.client import get_supabase
from database.models import Message

router = APIRouter()


@router.get("", response_model=list[Message])
async def list_messages(
    task_id: UUID | None = None,
    from_agent: str | None = None,
    to_agent: str | None = None,
    limit: int = 100,
):
    client = get_supabase()
    if client is None:
        raise HTTPException(503, "Supabase not configured")
    query = client.table("messages").select("*")
    if task_id is not None:
        query = query.eq("task_id", str(task_id))
    if from_agent is not None:
        query = query.eq("from_agent", from_agent)
    if to_agent is not None:
        query = query.eq("to_agent", to_agent)
    res = query.order("created_at", desc=True).limit(limit).execute()
    return res.data or []
