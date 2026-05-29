from .base import ToolRegistry, tool
from ._helpers import llm_tool


@tool(
    name="estimate_budget",
    description="Produce a budget estimate with line items for a project.",
    args={
        "project": {"type": "str", "description": "Project name / description"},
        "scope": {"type": "str", "description": "Scope notes (channels, duration, headcount)"},
    },
)
async def estimate_budget(project: str, scope: str) -> dict:
    return await llm_tool(
        system="You are a finance analyst. Output a budget table with 4-6 line "
        "items (category, cost, % of total) plus a Total and a 1-line rationale.",
        user=f"Project: {project}. Scope: {scope}",
        max_tokens=500,
    )


@tool(
    name="calculate_roi",
    description="Calculate expected ROI for an investment.",
    args={
        "investment": {"type": "str", "description": "Investment amount and what it's for"},
        "expected_return": {"type": "str", "description": "Expected return assumptions"},
    },
)
async def calculate_roi(investment: str, expected_return: str) -> dict:
    return await llm_tool(
        system="You are a finance analyst. Show: net return, ROI %, payback "
        "period, and 2 sensitivities (best/worst case).",
        user=f"Investment: {investment}. Expected return: {expected_return}",
        max_tokens=350,
    )


@tool(
    name="generate_invoice",
    description="Generate an invoice line-item summary for a customer.",
    args={
        "customer": {"type": "str", "description": "Customer name"},
        "items": {"type": "str", "description": "Items billed (free-form)"},
    },
)
async def generate_invoice(customer: str, items: str) -> dict:
    return await llm_tool(
        system="You are an accounts assistant. Output an invoice summary: "
        "customer, line items (description, qty, unit price, total), subtotal, "
        "tax estimate, grand total, due date 30 days out.",
        user=f"Customer: {customer}. Items: {items}",
        max_tokens=400,
    )


@tool(
    name="expense_analysis",
    description="Analyze a category of expenses for trends or anomalies.",
    args={
        "category": {"type": "str", "description": "Expense category"},
        "period": {"type": "str", "description": "Time period"},
    },
)
async def expense_analysis(category: str, period: str) -> dict:
    return await llm_tool(
        system="You are a finance analyst. Output: total spend, % change vs "
        "prior period, top 3 line items, 1 anomaly, 1 recommendation.",
        user=f"Category: {category}. Period: {period}",
        max_tokens=400,
    )


@tool(
    name="financial_forecast",
    description="Produce a short-horizon financial forecast.",
    args={
        "horizon": {"type": "str", "description": "Horizon (e.g. 'next 2 quarters')"},
        "assumptions": {"type": "str", "description": "Key assumptions"},
    },
)
async def financial_forecast(horizon: str, assumptions: str) -> dict:
    return await llm_tool(
        system="You are a finance analyst. Output revenue, costs, EBITDA for "
        "the horizon, plus 2 risks and 1 upside.",
        user=f"Horizon: {horizon}. Assumptions: {assumptions}",
        max_tokens=450,
    )


def build_finance_tools() -> ToolRegistry:
    registry = ToolRegistry()
    for t in (
        estimate_budget,
        calculate_roi,
        generate_invoice,
        expense_analysis,
        financial_forecast,
    ):
        registry.register(t)
    return registry
