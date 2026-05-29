from .base import BaseAgent
from .tools.sales_tools import build_sales_tools


class SalesAgent(BaseAgent):
    role = "sales"
    name = "Sales Agent"
    color = "#34d399"

    def __init__(self, company_context: str = "") -> None:
        super().__init__(company_context=company_context, tools=build_sales_tools())

    def base_system_prompt(self) -> str:
        return (
            "You are the Sales Agent. You are energetic, data-driven, and "
            "persuasive. You handle leads, proposals, competitor analysis, "
            "and pipeline management. You think in opportunities, numbers, "
            "and next steps."
        )
