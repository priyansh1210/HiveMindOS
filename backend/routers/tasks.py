from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException

from database.client import get_supabase
from database.models import Task, TaskUserInput
from orchestrator.engine import get_orchestrator

router = APIRouter()


@router.get("", response_model=list[Task])
async def list_tasks(company_id: UUID | None = None, limit: int = 50):
    client = get_supabase()
    if client is None:
        raise HTTPException(503, "Supabase not configured")
    query = client.table("tasks").select("*")
    if company_id is not None:
        query = query.eq("company_id", str(company_id))
    res = query.order("created_at", desc=True).limit(limit).execute()
    return res.data or []


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: UUID):
    client = get_supabase()
    if client is None:
        raise HTTPException(503, "Supabase not configured")
    res = client.table("tasks").select("*").eq("id", str(task_id)).single().execute()
    if not res.data:
        raise HTTPException(404, "Task not found")
    return res.data


@router.get("/{task_id}/messages")
async def get_task_messages(task_id: UUID, limit: int = 200):
    client = get_supabase()
    if client is None:
        raise HTTPException(503, "Supabase not configured")
    res = (
        client.table("messages")
        .select("*")
        .eq("task_id", str(task_id))
        .order("created_at")
        .limit(limit)
        .execute()
    )
    return res.data or []


@router.post("", response_model=Task, status_code=201)
async def create_task(payload: TaskUserInput, background: BackgroundTasks):
    """Submit a natural-language prompt — the orchestrator plans and executes
    it in the background. The route returns immediately with the new task row;
    the client should subscribe to /ws (or poll /api/tasks/{id}) for progress.
    """
    client = get_supabase()
    if client is None:
        raise HTTPException(503, "Supabase not configured")

    company_id = payload.company_id
    if company_id is None:
        company_res = client.table("companies").select("id").limit(1).execute()
        if not company_res.data:
            raise HTTPException(400, "No company found — run database/seed.sql first")
        company_id = company_res.data[0]["id"]

    res = (
        client.table("tasks")
        .insert(
            {
                "company_id": str(company_id),
                "title": payload.prompt[:120],
                "description": payload.prompt,
                "status": "pending",
            }
        )
        .execute()
    )
    task = res.data[0]

    orchestrator = get_orchestrator()
    background.add_task(
        orchestrator.run,
        task_id=UUID(task["id"]),
        user_request=payload.prompt,
        company_id=UUID(str(company_id)) if company_id else None,
    )

    return task
