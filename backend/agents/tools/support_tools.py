from database.client import get_supabase

from .base import ToolRegistry, tool
from ._helpers import llm_tool


@tool(
    name="search_knowledge_base",
    description="Search the company knowledge base for relevant articles.",
    args={"query": {"type": "str", "description": "What you're looking for"}},
)
async def search_knowledge_base(query: str) -> dict:
    # Real KB lookup when Supabase is configured; otherwise simulate.
    client = get_supabase()
    if client is not None:
        # Naive ILIKE search — good enough for the demo without embeddings.
        like = f"%{query}%"
        res = (
            client.table("knowledge")
            .select("title,category,content")
            .or_(f"title.ilike.{like},content.ilike.{like}")
            .limit(3)
            .execute()
        )
        if res.data:
            return {"result": res.data, "source": "supabase"}

    return await llm_tool(
        system="You are a knowledge base. Return 2 plausible KB articles "
        "(title + 2-sentence summary each) matching the query.",
        user=query,
        max_tokens=350,
    )


@tool(
    name="create_ticket",
    description="Open a support ticket for a customer issue.",
    args={
        "customer": {"type": "str", "description": "Customer name or ID"},
        "issue": {"type": "str", "description": "Short issue description"},
    },
)
async def create_ticket(customer: str, issue: str) -> dict:
    return await llm_tool(
        system="You are a support system. Return a ticket record: id (TKT-xxxx), "
        "customer, issue summary, severity (low/medium/high), category, SLA.",
        user=f"Customer: {customer}. Issue: {issue}",
        max_tokens=300,
    )


@tool(
    name="draft_response",
    description="Draft a customer-facing response to an issue.",
    args={"issue": {"type": "str", "description": "The customer's reported issue"}},
)
async def draft_response(issue: str) -> dict:
    return await llm_tool(
        system="You are a support rep. Write a warm, concise reply that "
        "acknowledges the issue, gives a workaround if possible, and sets "
        "expectation for next steps. Under 100 words.",
        user=issue,
        max_tokens=300,
    )


@tool(
    name="escalate_issue",
    description="Escalate a ticket to the right team with rationale.",
    args={
        "ticket_id": {"type": "str", "description": "Ticket ID"},
        "reason": {"type": "str", "description": "Why this needs escalation"},
    },
)
async def escalate_issue(ticket_id: str, reason: str) -> dict:
    return await llm_tool(
        system="You are an escalations manager. Output: target team, priority, "
        "1-paragraph rationale, and 2 questions to answer next.",
        user=f"Ticket: {ticket_id}. Reason: {reason}",
        max_tokens=300,
    )


@tool(
    name="sentiment_analysis",
    description="Classify the sentiment and urgency of a customer message.",
    args={"message": {"type": "str", "description": "The customer's message"}},
)
async def sentiment_analysis(message: str) -> dict:
    return await llm_tool(
        system="You are a sentiment classifier. Output sentiment "
        "(positive/neutral/negative/angry), urgency (low/medium/high), "
        "and 1 line explaining your read.",
        user=message,
        max_tokens=200,
    )


def build_support_tools() -> ToolRegistry:
    registry = ToolRegistry()
    for t in (
        search_knowledge_base,
        create_ticket,
        draft_response,
        escalate_issue,
        sentiment_analysis,
    ):
        registry.register(t)
    return registry
