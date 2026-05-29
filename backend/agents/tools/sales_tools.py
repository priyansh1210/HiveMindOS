from .base import ToolRegistry, tool
from ._helpers import llm_tool


@tool(
    name="research_competitor",
    description="Generate competitive analysis for a named competitor.",
    args={"company_name": {"type": "str", "description": "Competitor company name"}},
)
async def research_competitor(company_name: str) -> dict:
    return await llm_tool(
        system="You are a market analyst. Output: Strengths (3), Weaknesses (3), "
        "Pricing (rough estimate), Market Position (1 line).",
        user=f"Competitor: {company_name}",
        max_tokens=500,
    )


@tool(
    name="generate_pitch",
    description="Draft a sales pitch outline for a product and audience.",
    args={
        "product": {"type": "str", "description": "Product name"},
        "audience": {"type": "str", "description": "Target audience (e.g. 'mid-market CTOs')"},
    },
)
async def generate_pitch(product: str, audience: str) -> dict:
    return await llm_tool(
        system="You are a sales strategist. Output a pitch outline: Hook, "
        "Problem, Solution, Differentiator, Proof, CTA — one line each.",
        user=f"Product: {product}. Audience: {audience}.",
        max_tokens=400,
    )


@tool(
    name="create_proposal",
    description="Draft a deal proposal summary for a prospect.",
    args={
        "prospect": {"type": "str", "description": "Prospect company"},
        "deal_size": {"type": "str", "description": "Approximate deal size, e.g. '$50K'"},
    },
)
async def create_proposal(prospect: str, deal_size: str) -> dict:
    return await llm_tool(
        system="You are a sales lead. Output a proposal summary: Scope, "
        "Deliverables (3 bullets), Pricing, Timeline, Next Steps.",
        user=f"Prospect: {prospect}. Deal size: {deal_size}.",
        max_tokens=500,
    )


@tool(
    name="forecast_revenue",
    description="Forecast revenue for a period given pipeline assumptions.",
    args={
        "period": {"type": "str", "description": "Period (e.g. 'Q3 2026')"},
        "assumptions": {"type": "str", "description": "Key assumptions or pipeline notes"},
    },
)
async def forecast_revenue(period: str, assumptions: str) -> dict:
    return await llm_tool(
        system="You are a sales ops analyst. Output a revenue forecast with "
        "low/base/high scenarios, a 1-line rationale, and 2 risks.",
        user=f"Period: {period}. Assumptions: {assumptions}",
        max_tokens=400,
    )


@tool(
    name="draft_outreach_email",
    description="Draft a personalized cold outreach email.",
    args={
        "recipient": {"type": "str", "description": "Recipient name or role + company"},
        "context": {"type": "str", "description": "Context / hook to reference"},
    },
)
async def draft_outreach_email(recipient: str, context: str) -> dict:
    return await llm_tool(
        system="You are a sales rep. Write a short cold email: subject line + "
        "3-paragraph body. Keep it under 120 words and end with a clear ask.",
        user=f"Recipient: {recipient}. Context: {context}",
        max_tokens=400,
    )


def build_sales_tools() -> ToolRegistry:
    registry = ToolRegistry()
    for t in (
        research_competitor,
        generate_pitch,
        create_proposal,
        forecast_revenue,
        draft_outreach_email,
    ):
        registry.register(t)
    return registry
