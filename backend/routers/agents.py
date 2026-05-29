from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.registry import get_registry
from database.client import get_supabase
from database.models import Agent, AgentStatusUpdate

router = APIRouter()


# ============================================================
# Live-agent endpoints (in-process registry — no DB required)
# ============================================================
class InvokePayload(BaseModel):
    prompt: str
    reset_memory: bool = False


@router.get("/roles")
async def list_roles():
    """Roles available in the live in-process agent registry."""
    registry = get_registry()
    return [
        {
            "role": agent.role,
            "name": agent.name,
            "color": agent.color,
            "tools": agent.tools.names(),
            "memory_size": len(agent.memory),
        }
        for agent in registry.all().values()
    ]


@router.post("/roles/{role}/invoke")
async def invoke_agent(role: str, payload: InvokePayload):
    """Send a prompt to a specific agent and get its response."""
    agent = get_registry().get(role)
    if agent is None:
        raise HTTPException(404, f"Unknown agent role: {role}")
    if payload.reset_memory:
        agent.reset()

    run = await agent.run(payload.prompt)
    return {
        "agent": agent.role,
        "response": run.response,
        "tool_calls": [
            {
                "name": tc.name,
                "args": tc.args,
                "duration_ms": tc.duration_ms,
                "error": tc.error,
            }
            for tc in run.tool_calls
        ],
        "mentions": [
            {"to_agent": m.to_agent, "content": m.content} for m in run.mentions
        ],
        "turns": run.turns,
        "duration_ms": run.total_duration_ms,
        "memory_size": len(agent.memory),
    }


@router.post("/roles/{role}/reset", status_code=204)
async def reset_agent(role: str):
    agent = get_registry().get(role)
    if agent is None:
        raise HTTPException(404, f"Unknown agent role: {role}")
    agent.reset()
    return None


# ============================================================
# DB-backed endpoints
# ============================================================
@router.get("", response_model=list[Agent])
async def list_agents(company_id: UUID | None = None):
    client = get_supabase()
    if client is None:
        raise HTTPException(503, "Supabase not configured")
    query = client.table("agents").select("*")
    if company_id is not None:
        query = query.eq("company_id", str(company_id))
    res = query.order("created_at").execute()
    return res.data or []


@router.get("/{agent_id}", response_model=Agent)
async def get_agent(agent_id: UUID):
    client = get_supabase()
    if client is None:
        raise HTTPException(503, "Supabase not configured")
    res = client.table("agents").select("*").eq("id", str(agent_id)).single().execute()
    if not res.data:
        raise HTTPException(404, "Agent not found")
    return res.data


@router.patch("/{agent_id}/status", response_model=Agent)
async def update_agent_status(agent_id: UUID, payload: AgentStatusUpdate):
    client = get_supabase()
    if client is None:
        raise HTTPException(503, "Supabase not configured")
    res = (
        client.table("agents")
        .update({"status": payload.status})
        .eq("id", str(agent_id))
        .execute()
    )
    if not res.data:
        raise HTTPException(404, "Agent not found")
    return res.data[0]
